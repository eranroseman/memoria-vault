"""Workspace backup, restore, and backup-health contracts."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from memoria_vault.cli import main
from memoria_vault.runtime import backup, state, trusted_writer
from tests.helpers import init_cli_workspace


def _seed(vault: Path) -> Path:
    blob = vault / ".memoria/blobs/source-content/w-1/raw/source.txt"
    blob.parent.mkdir(parents=True, exist_ok=True)
    blob.write_text("evidence bytes", encoding="utf-8")
    trusted_writer.append_explicit_journal_event(
        vault,
        {"event": "run", "run_id": "backup-seed", "status": "started"},
        actor="operation",
        machine="backup-test",
    )
    state.write_journal_head_anchor(vault)
    return blob


def _create(vault: Path, target: Path) -> dict[str, object]:
    return backup.create_backup(vault, target, actor="pi", machine="backup-test")


def _restore(vault: Path, source: Path, *, force: bool = True) -> dict[str, object]:
    return backup.restore_backup(
        vault,
        source,
        force=force,
        actor="pi",
        machine="restore-test",
    )


def _rewrite_backup_last_machine(source: Path, machine: str) -> None:
    database = source / "memoria.sqlite"
    with sqlite3.connect(database) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("DROP TRIGGER event_log_no_update")
        row = conn.execute(
            "SELECT event_id, timestamp, event_type, payload_json, prev_hash"
            " FROM event_log ORDER BY event_id DESC LIMIT 1"
        ).fetchone()
        assert row is not None
        event = json.loads(str(row["payload_json"]))
        event["machine"] = machine
        payload_json = state._json(event)
        row_hash = state._journal_hash(
            int(row["event_id"]),
            str(row["timestamp"]),
            str(row["event_type"]),
            machine,
            payload_json,
            str(row["prev_hash"]),
        )
        conn.execute(
            "UPDATE event_log SET machine = ?, payload_json = ?, row_hash = ? WHERE event_id = ?",
            (machine, payload_json, row_hash, int(row["event_id"])),
        )

    backup._consolidate_database(database)
    (source / "journal-head").write_text(row_hash + "\n", encoding="utf-8")
    manifest_path = source / backup.MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["database"]["sha256"] = backup._file_sha256(database)
    manifest["journal_head"]["value"] = row_hash
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_backup_snapshot_binds_db_blobs_and_anchor(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    target = tmp_path / "backup-1"

    report = _create(vault, target)
    manifest = json.loads((target / backup.MANIFEST_NAME).read_text(encoding="utf-8"))

    assert report["ok"] is True
    assert report["blobs"] == 1
    assert report["journal_head"] is True
    assert (target / "memoria.sqlite").is_file()
    assert (target / "blobs/source-content/w-1/raw/source.txt").read_text(
        encoding="utf-8"
    ) == "evidence bytes"
    assert (target / "journal-head").read_text(encoding="utf-8").strip() == state.journal_head(
        vault
    )
    assert manifest["format"] == backup.BACKUP_FORMAT
    assert manifest["version"] == backup.BACKUP_VERSION
    assert manifest["database"]["sha256"].startswith("sha256:")
    assert manifest["blobs"]["files"] == 1
    assert manifest["blobs"]["sha256"].startswith("sha256:")


@pytest.mark.parametrize("redirect_rel", [Path("."), Path("nested")])
def test_blob_inventory_rejects_windows_junctions(
    tmp_path: Path, monkeypatch, redirect_rel: Path
) -> None:
    root = tmp_path / "blobs"
    nested = root / "nested"
    nested.mkdir(parents=True)
    (nested / "content.txt").write_text("content", encoding="utf-8")
    redirected = root / redirect_rel
    real_is_junction = Path.is_junction

    def fake_is_junction(path: Path) -> bool:
        return Path(path) == redirected or real_is_junction(path)

    monkeypatch.setattr(Path, "is_junction", fake_is_junction)

    with pytest.raises(ValueError, match="symlink"):
        backup.blob_inventory(root)


def test_local_backup_status_rejects_junction_backup_target(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    target = tmp_path / "junction-backup-target"
    assert _create(vault, target)["ok"] is True
    real_is_junction = Path.is_junction

    def fake_is_junction(path: Path) -> bool:
        return Path(path) == target or real_is_junction(path)

    monkeypatch.setattr(Path, "is_junction", fake_is_junction)

    report = backup.local_backup_status(vault)

    assert report["valid"] is False
    assert report["error"] == "stamped backup target is missing or invalid"


def test_backup_and_restore_markers_are_ignored_local_machine_state(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)

    assert _create(vault, tmp_path / "ignored-stamp-backup")["ok"] is True

    for rel in (
        backup.LAST_BACKUP_REL,
        backup.BACKUP_TRANSACTION_REL,
        backup.RESTORE_TRANSACTION_REL,
    ):
        ignored = subprocess.run(["git", "check-ignore", "-q", rel], cwd=vault, check=False)
        assert ignored.returncode == 0


def test_backup_replaces_only_a_recognized_snapshot_without_merging(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    target = tmp_path / "backup-1"
    assert _create(vault, target)["ok"] is True
    (target / "stale-file").write_text("must disappear", encoding="utf-8")

    report = _create(vault, target)

    assert report["ok"] is True
    assert not (target / "stale-file").exists()
    assert not list(tmp_path.glob(".backup-1.stage-*"))
    assert not list(tmp_path.glob(".backup-1.rollback-*"))


def test_backup_publish_failure_restores_previous_recognized_snapshot(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    blob = _seed(vault)
    target = tmp_path / "backup-rollback"
    assert _create(vault, target)["ok"] is True
    previous_manifest = (target / backup.MANIFEST_NAME).read_bytes()
    blob.write_text("new evidence bytes", encoding="utf-8")
    real_replace = backup.os.replace

    def fail_stage_publish(source, destination):
        source_path = Path(source)
        destination_path = Path(destination)
        if source_path.name.startswith(f".{target.name}.stage-") and destination_path == target:
            raise OSError("injected stage publication failure")
        return real_replace(source, destination)

    monkeypatch.setattr(backup.os, "replace", fail_stage_publish)

    with pytest.raises(OSError, match="injected stage publication failure"):
        _create(vault, target)

    assert (target / backup.MANIFEST_NAME).read_bytes() == previous_manifest
    assert (target / "blobs/source-content/w-1/raw/source.txt").read_text(
        encoding="utf-8"
    ) == "evidence bytes"
    assert not (vault / backup.BACKUP_TRANSACTION_REL).exists()
    assert not list(tmp_path.glob(".backup-rollback.stage-*"))
    assert not list(tmp_path.glob(".backup-rollback.rollback-*"))


def test_backup_preserves_transaction_stage_when_publication_recovery_fails(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    blob = _seed(vault)
    target = tmp_path / "backup-recovery-material"
    assert _create(vault, target)["ok"] is True
    blob.write_text("new evidence bytes", encoding="utf-8")
    real_replace = backup._replace_durable

    def fail_stage_publish(source: Path, destination: Path) -> None:
        if Path(source).name.startswith(f".{target.name}.stage-") and Path(destination) == target:
            raise OSError("injected stage publication failure")
        real_replace(source, destination)

    def fail_recovery(_vault: Path) -> dict[str, object]:
        raise ValueError("injected backup recovery failure")

    monkeypatch.setattr(backup, "_replace_durable", fail_stage_publish)
    monkeypatch.setattr(backup, "recover_interrupted_backup", fail_recovery)

    with pytest.raises(ValueError, match="injected backup recovery failure"):
        _create(vault, target)

    assert (vault / backup.BACKUP_TRANSACTION_REL).is_file()
    assert len(list(tmp_path.glob(f".{target.name}.stage-*"))) == 1
    assert len(list(tmp_path.glob(f".{target.name}.rollback-*"))) == 1


def test_backup_reports_success_after_recovering_completed_publish_rename(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    blob = _seed(vault)
    target = tmp_path / "backup-post-rename-fsync"
    assert _create(vault, target)["ok"] is True
    blob.write_text("new evidence bytes", encoding="utf-8")
    real_fsync_directory = backup._fsync_directory
    failed = False

    def fail_once_after_publish(path: Path) -> None:
        nonlocal failed
        rollback_exists = bool(list(tmp_path.glob(f".{target.name}.rollback-*")))
        stage_exists = bool(list(tmp_path.glob(f".{target.name}.stage-*")))
        if (
            not failed
            and Path(path) == tmp_path
            and target.exists()
            and rollback_exists
            and not stage_exists
        ):
            failed = True
            raise OSError("injected post-publish directory fsync failure")
        real_fsync_directory(path)

    monkeypatch.setattr(backup, "_fsync_directory", fail_once_after_publish)

    report = _create(vault, target)

    assert failed is True
    assert report["ok"] is True
    assert (target / "blobs/source-content/w-1/raw/source.txt").read_text(
        encoding="utf-8"
    ) == "new evidence bytes"
    assert backup.local_backup_status(vault)["valid"] is True
    assert not (vault / backup.BACKUP_TRANSACTION_REL).exists()


def test_first_backup_reports_success_after_recovering_completed_publish_rename(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    target = tmp_path / "first-backup-post-rename-fsync"
    real_fsync_directory = backup._fsync_directory
    failed = False

    def fail_once_after_publish(path: Path) -> None:
        nonlocal failed
        if (
            not failed
            and Path(path) == tmp_path
            and target.is_dir()
            and (vault / backup.BACKUP_TRANSACTION_REL).is_file()
        ):
            failed = True
            raise OSError("injected first-publish directory fsync failure")
        real_fsync_directory(path)

    monkeypatch.setattr(backup, "_fsync_directory", fail_once_after_publish)

    report = _create(vault, target)

    assert failed is True
    assert report["ok"] is True
    assert backup.local_backup_status(vault)["valid"] is True
    assert not (vault / backup.BACKUP_TRANSACTION_REL).exists()


def test_published_backup_recovery_writes_stamp_before_removing_marker(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    target = tmp_path / "backup-stamp-interruption"
    stamp_path = vault / backup.LAST_BACKUP_REL
    real_write = backup.write_text_durable

    def fail_stamp(path: Path, text: str, **kwargs: object) -> None:
        if Path(path) == stamp_path:
            raise OSError("injected backup stamp interruption")
        real_write(path, text, **kwargs)

    monkeypatch.setattr(backup, "write_text_durable", fail_stamp)

    with pytest.raises(OSError, match="backup stamp interruption"):
        _create(vault, target)

    marker_path = vault / backup.BACKUP_TRANSACTION_REL
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    assert marker["phase"] == "published-cleanup"
    assert target.is_dir()
    assert not stamp_path.exists()

    monkeypatch.setattr(backup, "write_text_durable", real_write)
    report = backup.recover_interrupted_backup(vault)

    assert report["outcome"] == "published"
    assert backup.local_backup_status(vault)["valid"] is True
    assert not marker_path.exists()


def test_backup_refuses_arbitrary_existing_target(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    target = tmp_path / "not-a-backup"
    target.mkdir()
    sentinel = target / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    report = _create(vault, target)

    assert report["ok"] is False
    assert "recognized Memoria backup" in str(report["error"])
    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_backup_publication_uses_durable_rename(tmp_path: Path, monkeypatch) -> None:
    stage = tmp_path / "stage"
    stage.mkdir()
    target = tmp_path / "published"
    calls: list[tuple[Path, Path]] = []
    replace_durable = backup._replace_durable

    def record_replace(source: Path, destination: Path) -> None:
        calls.append((Path(source), Path(destination)))
        replace_durable(source, destination)

    monkeypatch.setattr(backup, "_replace_durable", record_replace)
    monkeypatch.setattr(backup, "_write_backup_transaction", lambda *_args: None)
    monkeypatch.setattr(
        backup,
        "recover_interrupted_backup",
        lambda _vault: {"recovered": True, "target": str(target), "outcome": "published"},
    )

    backup._publish_backup_directory(stage, target, tmp_path / "vault")

    assert calls == [(stage, target)]


def test_cross_directory_durable_rename_flushes_destination_before_source(
    tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "source" / "snapshot"
    destination = tmp_path / "destination" / "snapshot"
    source.parent.mkdir()
    destination.parent.mkdir()
    source.write_text("snapshot", encoding="utf-8")
    flushed: list[Path] = []
    monkeypatch.setattr(backup, "_fsync_directory", lambda path: flushed.append(Path(path)))

    backup._replace_durable(source, destination)

    assert flushed == [destination.parent, source.parent]


@pytest.mark.skipif(os.name == "nt", reason="directory fsync is not available on Windows")
def test_directory_fsync_failure_is_not_reported_as_durable(tmp_path: Path, monkeypatch) -> None:
    def fail_fsync(_fd: int) -> None:
        raise OSError("injected directory fsync failure")

    monkeypatch.setattr(backup.os, "fsync", fail_fsync)

    with pytest.raises(OSError, match="injected directory fsync failure"):
        backup._fsync_directory(tmp_path)


def test_backup_refuses_forged_manifest_target_without_deleting_contents(
    tmp_path: Path, capsys
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    target = tmp_path / "forged-backup"
    target.mkdir()
    (target / backup.MANIFEST_NAME).write_text(
        json.dumps({"format": backup.BACKUP_FORMAT, "version": backup.BACKUP_VERSION}),
        encoding="utf-8",
    )
    sentinel = target / "unrelated" / "keep.txt"
    sentinel.parent.mkdir()
    sentinel.write_text("keep", encoding="utf-8")

    report = _create(vault, target)

    assert report["ok"] is False
    assert "recognized Memoria backup" in str(report["error"])
    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_backup_refuses_symlink_target_without_touching_destination(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    destination = tmp_path / "destination"
    destination.mkdir()
    sentinel = destination / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    target = tmp_path / "backup-link"
    target.symlink_to(destination, target_is_directory=True)

    report = _create(vault, target)

    assert report["ok"] is False
    assert "symlink" in str(report["error"])
    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_backup_refuses_symlinked_memoria_root_without_reading_outside_vault(
    tmp_path: Path, capsys
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    outside_runtime = tmp_path / "outside-runtime"
    (vault / ".memoria").rename(outside_runtime)
    (vault / ".memoria").symlink_to(outside_runtime, target_is_directory=True)
    target = tmp_path / "escaped-backup"

    report = _create(vault, target)

    assert report["ok"] is False
    assert "symlink" in str(report["error"])
    assert not target.exists()


def test_backup_refuses_symlinked_runtime_config_without_writing_outside_vault(
    tmp_path: Path, capsys
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    outside_config = tmp_path / "outside-config"
    (vault / ".memoria/config").rename(outside_config)
    (vault / ".memoria/config").symlink_to(outside_config, target_is_directory=True)
    target = tmp_path / "escaped-config-backup"

    report = _create(vault, target)

    assert report["ok"] is False
    assert "symlink" in str(report["error"])
    assert not (outside_config / "last-backup").exists()


def test_restore_refuses_symlinked_live_database_before_transaction(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    source = tmp_path / "restore-source"
    assert _create(vault, source)["ok"] is True
    live_database = vault / state.DB_REL
    outside_database = tmp_path / "outside-live.sqlite"
    live_database.replace(outside_database)
    live_database.symlink_to(outside_database)

    report = _restore(vault, source)

    assert report["ok"] is False
    assert "symlink" in str(report["error"])
    assert live_database.is_symlink()
    assert outside_database.is_file()
    assert not (vault / backup.RESTORE_TRANSACTION_REL).exists()


def test_runtime_validation_rejects_windows_junctions(tmp_path: Path, capsys, monkeypatch) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    redirected = vault / backup.BLOBS_REL
    real_is_junction = Path.is_junction

    def fake_is_junction(path: Path) -> bool:
        return Path(path) == redirected or real_is_junction(path)

    monkeypatch.setattr(Path, "is_junction", fake_is_junction)

    with pytest.raises(ValueError, match="runtime path"):
        backup.validate_runtime_root(vault)


def test_backup_refuses_target_inside_live_vault(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    target = vault / "nested-backup"

    report = _create(vault, target)

    assert report["ok"] is False
    assert "overlap" in str(report["error"])
    assert not target.exists()


def test_backup_rejects_non_pi_actor_before_creating_target(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    target = tmp_path / "agent-backup"

    with pytest.raises(ValueError, match="PI actor authority"):
        backup.create_backup(vault, target, actor="agent", machine="backup-test")

    assert not target.exists()


def test_backup_refuses_unverified_journal_without_partial_target(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    (vault / state.JOURNAL_HEAD_REL).write_text("wrong-head\n", encoding="utf-8")
    target = tmp_path / "invalid-journal-backup"

    report = _create(vault, target)

    assert report["ok"] is False
    assert "journal" in str(report["error"])
    assert not target.exists()


def test_workspace_backup_cli_requires_pi_and_publishes_snapshot(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    target = tmp_path / "cli-backup"

    assert (
        main(
            [
                "workspace",
                "backup",
                str(target),
                "--workspace",
                str(vault),
                "--actor",
                "agent",
                "--json",
            ]
        )
        == 2
    )
    assert not target.exists()
    capsys.readouterr()

    assert (
        main(
            [
                "workspace",
                "backup",
                str(target),
                "--workspace",
                str(vault),
                "--json",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert Path(payload["target"]) == target.resolve()

    assert main(["workspace", "backup", str(target), "--workspace", str(vault)]) == 0
    assert capsys.readouterr().out == f"{target.resolve()}\n"


def test_restore_round_trip_rebuilds_exports_and_preserves_source(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    blob = _seed(vault)
    source = tmp_path / "round-trip-backup"
    assert _create(vault, source)["ok"] is True
    source_manifest = (source / backup.MANIFEST_NAME).read_bytes()
    source_database = (source / "memoria.sqlite").read_bytes()

    blob.write_text("newer live evidence", encoding="utf-8")
    trusted_writer.append_explicit_journal_event(
        vault,
        {"event": "run", "run_id": "after-backup", "status": "started"},
        actor="operation",
        machine="live-machine",
    )
    state.write_journal_head_anchor(vault)
    for export in (vault / ".memoria/journal").glob("*.jsonl"):
        export.unlink()
    Path(f"{vault / state.DB_REL}-wal").write_bytes(b"stale-wal")
    Path(f"{vault / state.DB_REL}-shm").write_bytes(b"stale-shm")
    Path(f"{vault / state.DB_REL}-journal").write_bytes(b"stale-journal")

    report = _restore(vault, source)

    assert report["ok"] is True
    wal = Path(f"{vault / state.DB_REL}-wal")
    shm = Path(f"{vault / state.DB_REL}-shm")
    journal = Path(f"{vault / state.DB_REL}-journal")
    assert not wal.exists() or wal.read_bytes() != b"stale-wal"
    assert not shm.exists() or shm.read_bytes() != b"stale-shm"
    assert not journal.exists() or journal.read_bytes() != b"stale-journal"
    assert blob.read_text(encoding="utf-8") == "evidence bytes"
    verification = state.verify_journal_chain(vault)
    assert verification["ok"] is True
    events = state.read_event_log(vault)
    assert events[-1]["event"] == "workspace-restored"
    assert events[-1]["actor"] == "pi"
    assert events[-1]["machine"] == "restore-test"
    assert list((vault / ".memoria/journal").glob("*.jsonl"))
    assert (source / backup.MANIFEST_NAME).read_bytes() == source_manifest
    assert (source / "memoria.sqlite").read_bytes() == source_database


def test_restore_refuses_symlinked_memoria_root_without_touching_outside_state(
    tmp_path: Path, capsys
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    source = tmp_path / "safe-backup"
    assert _create(vault, source)["ok"] is True
    outside_runtime = tmp_path / "outside-runtime"
    (vault / ".memoria").rename(outside_runtime)
    sentinel = outside_runtime / "blobs" / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    (vault / ".memoria").symlink_to(outside_runtime, target_is_directory=True)

    report = _restore(vault, source)

    assert report["ok"] is False
    assert "symlink" in str(report["error"])
    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_restore_refuses_live_database_without_force(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    blob = _seed(vault)
    source = tmp_path / "force-backup"
    assert _create(vault, source)["ok"] is True
    blob.write_text("live value", encoding="utf-8")

    report = _restore(vault, source, force=False)

    assert report["ok"] is False
    assert "force" in str(report["error"])
    assert blob.read_text(encoding="utf-8") == "live value"


def test_restore_rejects_non_pi_actor_before_touching_live_state(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    blob = _seed(vault)
    source = tmp_path / "actor-backup"
    assert _create(vault, source)["ok"] is True
    blob.write_text("live value", encoding="utf-8")

    with pytest.raises(ValueError, match="PI actor authority"):
        backup.restore_backup(
            vault,
            source,
            force=True,
            actor="agent",
            machine="restore-test",
        )

    assert blob.read_text(encoding="utf-8") == "live value"


def test_restore_validates_manifest_hash_before_touching_live_state(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    blob = _seed(vault)
    source = tmp_path / "corrupt-backup"
    assert _create(vault, source)["ok"] is True
    database = source / "memoria.sqlite"
    database.write_bytes(database.read_bytes() + b"corrupt")
    blob.write_text("live value", encoding="utf-8")
    live_head = state.journal_head(vault)

    report = _restore(vault, source)

    assert report["ok"] is False
    assert "database hash" in str(report["error"])
    assert blob.read_text(encoding="utf-8") == "live value"
    assert state.journal_head(vault) == live_head


def test_restore_rejects_noncanonical_export_machine_without_writing_outside_stage(
    tmp_path: Path, capsys
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    blob = _seed(vault)
    source = tmp_path / "crafted-machine-backup"
    assert _create(vault, source)["ok"] is True
    outside = tmp_path / "outside.jsonl"
    outside.write_text("keep\n", encoding="utf-8")
    _rewrite_backup_last_machine(source, str(outside.with_suffix("")))
    blob.write_text("live value", encoding="utf-8")

    report = _restore(vault, source)

    assert report["ok"] is False
    assert "machine" in str(report["error"])
    assert outside.read_text(encoding="utf-8") == "keep\n"
    assert blob.read_text(encoding="utf-8") == "live value"


@pytest.mark.parametrize("failure", ["nonzero", "oserror"])
def test_restore_fails_closed_when_committed_anchor_lookup_fails(
    tmp_path: Path, capsys, monkeypatch, failure: str
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    blob = _seed(vault)
    source = tmp_path / f"git-anchor-{failure}"
    assert _create(vault, source)["ok"] is True
    blob.write_text("live value", encoding="utf-8")

    def fail_git(*args, **kwargs):
        if failure == "oserror":
            raise OSError("git unavailable")
        return subprocess.CompletedProcess(args[0], 128, "", "git failed")

    monkeypatch.setattr(backup.subprocess, "run", fail_git)

    report = _restore(vault, source)

    assert report["ok"] is False
    assert "committed journal-head" in str(report["error"])
    assert blob.read_text(encoding="utf-8") == "live value"


def test_committed_anchor_ignores_git_environment_redirects(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    expected = subprocess.run(
        ["git", "show", f"HEAD:{state.JOURNAL_HEAD_REL}"],
        cwd=vault,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    outside = tmp_path / "outside-repository"
    outside.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=outside, check=True)
    subprocess.run(
        ["git", "config", "user.email", "outside@example.invalid"],
        cwd=outside,
        check=True,
    )
    subprocess.run(["git", "config", "user.name", "Outside"], cwd=outside, check=True)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-q", "-m", "outside"],
        cwd=outside,
        check=True,
    )
    monkeypatch.setenv("GIT_DIR", str(outside / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(outside))

    assert backup._committed_journal_anchor(vault) == expected


def test_committed_anchor_rejects_git_common_directory_indirection(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    (vault / ".git/commondir").write_text(str(tmp_path / "outside-git"), encoding="utf-8")

    with pytest.raises(ValueError, match="common-directory indirection"):
        backup._committed_journal_anchor(vault)


def test_restore_refuses_backup_older_than_committed_journal_anchor(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    source = tmp_path / "old-backup"
    assert _create(vault, source)["ok"] is True
    trusted_writer.append_explicit_journal_event(
        vault,
        {"event": "run", "run_id": "committed-later", "status": "started"},
        actor="operation",
        machine="backup-test",
    )
    state.write_journal_head_anchor(vault)
    subprocess.run(
        ["git", "config", "user.email", "backup-test@example.invalid"], cwd=vault, check=True
    )
    subprocess.run(["git", "config", "user.name", "Backup Test"], cwd=vault, check=True)
    subprocess.run(["git", "add", state.JOURNAL_HEAD_REL], cwd=vault, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "anchor newer journal"], cwd=vault, check=True)
    live_head = state.journal_head(vault)

    report = _restore(vault, source)

    assert report["ok"] is False
    assert "committed journal-head" in str(report["error"])
    assert state.journal_head(vault) == live_head


def test_restore_mid_swap_failure_rolls_back_every_live_component(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    blob = _seed(vault)
    source = tmp_path / "rollback-source"
    assert _create(vault, source)["ok"] is True
    blob.write_text("newer live evidence", encoding="utf-8")
    trusted_writer.append_explicit_journal_event(
        vault,
        {"event": "run", "run_id": "live-tip", "status": "started"},
        actor="operation",
        machine="live-machine",
    )
    state.write_journal_head_anchor(vault)
    live_head = state.journal_head(vault)
    real_replace = backup.os.replace

    def fail_journal_install(source_path, destination_path):
        source_value = Path(source_path)
        destination_value = Path(destination_path)
        if ".restore-stage-" in str(source_value) and destination_value.name == "journal":
            raise OSError("injected restore swap failure")
        return real_replace(source_path, destination_path)

    monkeypatch.setattr(backup.os, "replace", fail_journal_install)

    with pytest.raises(OSError, match="injected restore swap failure"):
        _restore(vault, source)

    assert blob.read_text(encoding="utf-8") == "newer live evidence"
    assert state.journal_head(vault) == live_head
    assert state.verify_journal_chain(vault)["ok"] is True
    assert not list(vault.parent.glob(f".{vault.name}.restore-stage-*"))
    assert not list(vault.parent.glob(f".{vault.name}.restore-rollback-*"))


def test_restore_failure_preserves_absent_live_database(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    source = tmp_path / "absent-live-database-source"
    assert _create(vault, source)["ok"] is True
    database = vault / state.DB_REL
    for path in (
        database,
        Path(f"{database}-wal"),
        Path(f"{database}-shm"),
        vault / backup.BLOBS_REL,
        vault / state.JOURNAL_HEAD_REL,
        vault / ".memoria/journal",
    ):
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)
    assert not database.exists()
    real_replace = backup._replace_durable

    def fail_journal_install(source_path: Path, destination_path: Path) -> None:
        if ".restore-stage-" in str(source_path) and Path(destination_path).name == "journal":
            raise OSError("injected restore swap failure")
        real_replace(source_path, destination_path)

    monkeypatch.setattr(backup, "_replace_durable", fail_journal_install)

    with pytest.raises(OSError, match="injected restore swap failure"):
        _restore(vault, source, force=False)

    assert not database.exists()
    assert not (vault / backup.RESTORE_TRANSACTION_REL).exists()


def test_workspace_recover_preserves_absent_database_after_restore_rollback(
    tmp_path: Path, capsys
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    database = vault / state.DB_REL
    for path in (
        database,
        Path(f"{database}-wal"),
        Path(f"{database}-shm"),
        Path(f"{database}-journal"),
        vault / backup.BLOBS_REL,
        vault / state.JOURNAL_HEAD_REL,
        vault / ".memoria/journal",
        vault / backup.LAST_BACKUP_REL,
    ):
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)
    rollback = tmp_path / f".{vault.name}.restore-rollback-empty"
    stage = tmp_path / f".{vault.name}.restore-stage-empty"
    rollback.mkdir()
    stage.mkdir()
    backup._write_restore_transaction(vault, rollback, stage)

    assert main(["workspace", "recover", "--workspace", str(vault), "--json"]) == 0

    assert not database.exists()
    assert not (vault / backup.RESTORE_TRANSACTION_REL).exists()


def test_restore_first_move_fsync_failure_preserves_original_wal(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    wal = Path(f"{vault / state.DB_REL}-wal")
    wal.write_bytes(b"original committed WAL bytes")
    stage = tmp_path / f".{vault.name}.restore-stage-fsync-failure"
    stage.mkdir()
    real_fsync_directory = backup._fsync_directory

    def fail_after_database_move(path: Path) -> None:
        candidate = Path(path)
        if ".restore-rollback-" in candidate.name and (candidate / "memoria.sqlite").exists():
            raise OSError("injected rollback-directory fsync failure")
        real_fsync_directory(candidate)

    monkeypatch.setattr(backup, "_fsync_directory", fail_after_database_move)
    monkeypatch.setattr(
        backup.state,
        "verify_journal_chain",
        lambda _vault: {"ok": True, "head": "test-head"},
    )

    with pytest.raises(OSError, match="injected rollback-directory fsync failure"):
        backup._install_restore_stage(
            vault,
            stage,
            tmp_path / "unused-source",
            {},
            "pi",
            "backup-test",
        )

    assert wal.read_bytes() == b"original committed WAL bytes"
    assert (vault / state.DB_REL).is_file()
    assert not (vault / backup.RESTORE_TRANSACTION_REL).exists()
    assert not list(vault.parent.glob(f".{vault.name}.restore-stage-*"))
    assert not list(vault.parent.glob(f".{vault.name}.restore-rollback-*"))


def test_workspace_recover_restores_live_components_after_interrupted_restore(
    tmp_path: Path, capsys
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    blob = _seed(vault)
    source = tmp_path / "interrupted-restore-source"
    assert _create(vault, source)["ok"] is True
    blob.write_text("newer live evidence", encoding="utf-8")
    trusted_writer.append_explicit_journal_event(
        vault,
        {"event": "run", "run_id": "live-tip", "status": "started"},
        actor="operation",
        machine="live-machine",
    )
    state.write_journal_head_anchor(vault)
    live_head = state.journal_head(vault)
    crash_script = tmp_path / "interrupt_restore.py"
    crash_script.write_text(
        "\n".join(
            (
                "import os",
                "from pathlib import Path",
                "from memoria_vault.cli import main",
                "from memoria_vault.runtime import backup, state",
                f"vault = Path({str(vault)!r})",
                f"source = Path({str(source)!r})",
                "database = vault / state.DB_REL",
                "real_replace = backup.os.replace",
                "def interrupt(source_path, destination_path):",
                "    real_replace(source_path, destination_path)",
                "    if '.restore-stage-' in str(source_path) and Path(destination_path) == database:",
                "        os._exit(87)",
                "backup.os.replace = interrupt",
                "main(['workspace', 'restore', str(source), '--workspace', str(vault), '--force', '--json'])",
                "raise SystemExit(1)",
                "",
            )
        ),
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src")}
    interrupted = subprocess.run(
        [sys.executable, str(crash_script)], env=env, check=False, capture_output=True, text=True
    )

    assert interrupted.returncode == 87
    assert main(["workspace", "recover", "--workspace", str(vault), "--json"]) == 0
    recovery = json.loads(capsys.readouterr().out)
    assert len(recovery["restore_rollbacks"]) == 1
    assert blob.read_text(encoding="utf-8") == "newer live evidence"
    assert state.journal_head(vault) == live_head
    assert state.verify_journal_chain(vault)["ok"] is True
    assert not (vault / backup.RESTORE_TRANSACTION_REL).exists()
    assert not list(vault.parent.glob(f".{vault.name}.restore-stage-*"))
    assert not list(vault.parent.glob(f".{vault.name}.restore-rollback-*"))


def test_workspace_recover_preserves_wal_when_restore_stops_after_marker(
    tmp_path: Path, capsys
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    source = tmp_path / "marker-crash-source"
    assert _create(vault, source)["ok"] is True
    expected_head = tmp_path / "expected-live-head"
    database_without_wal = tmp_path / "database-without-wal.sqlite"
    crash_script = tmp_path / "interrupt_after_restore_marker.py"
    crash_script.write_text(
        "\n".join(
            (
                "import os",
                "import shutil",
                "from pathlib import Path",
                "from memoria_vault.cli import main",
                "from memoria_vault.runtime import backup, state, trusted_writer",
                f"vault = Path({str(vault)!r})",
                f"source = Path({str(source)!r})",
                f"expected_head = Path({str(expected_head)!r})",
                f"database_without_wal = Path({str(database_without_wal)!r})",
                "real_connect = state.connect",
                "def no_auto_checkpoint(vault_path):",
                "    connection = real_connect(vault_path)",
                "    connection.execute('PRAGMA wal_autocheckpoint = 0')",
                "    return connection",
                "state.connect = no_auto_checkpoint",
                "keeper = state.connect(vault)",
                "keeper.execute('BEGIN')",
                "keeper.execute('SELECT COUNT(*) FROM event_log').fetchone()",
                "trusted_writer.append_explicit_journal_event(",
                "    vault,",
                "    {'event': 'run', 'run_id': 'marker-crash-live', 'status': 'started'},",
                "    actor='operation',",
                "    machine='live-machine',",
                ")",
                "expected_head.write_text((vault / state.JOURNAL_HEAD_REL).read_text(encoding='utf-8'), encoding='utf-8')",
                "shutil.copyfile(vault / state.DB_REL, database_without_wal)",
                "real_write = backup._write_restore_transaction",
                "def interrupt(vault_path, rollback, stage):",
                "    real_write(vault_path, rollback, stage)",
                "    os._exit(87)",
                "backup._write_restore_transaction = interrupt",
                "main(['workspace', 'restore', str(source), '--workspace', str(vault), '--force', '--json'])",
                "raise SystemExit(1)",
                "",
            )
        ),
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src")}
    interrupted = subprocess.run(
        [sys.executable, str(crash_script)], env=env, check=False, capture_output=True, text=True
    )

    assert interrupted.returncode == 87
    live_wal = Path(f"{vault / state.DB_REL}-wal")
    assert live_wal.is_file()
    assert (vault / backup.RESTORE_TRANSACTION_REL).is_file()
    rollback_dirs = list(vault.parent.glob(f".{vault.name}.restore-rollback-*"))
    assert len(rollback_dirs) == 1
    assert (rollback_dirs[0] / "memoria.sqlite-wal").is_file()
    with sqlite3.connect(database_without_wal) as conn:
        copied_payloads = [
            str(row[0]) for row in conn.execute("SELECT payload_json FROM event_log")
        ]
    assert not any("marker-crash-live" in payload for payload in copied_payloads)
    database_after_crash = tmp_path / "database-after-crash.sqlite"
    database_after_crash.write_bytes((vault / state.DB_REL).read_bytes())
    with sqlite3.connect(database_after_crash) as conn:
        post_crash_payloads = [
            str(row[0]) for row in conn.execute("SELECT payload_json FROM event_log")
        ]
    assert not any("marker-crash-live" in payload for payload in post_crash_payloads)
    assert main(["workspace", "recover", "--workspace", str(vault), "--json"]) == 0
    recovery = json.loads(capsys.readouterr().out)
    assert len(recovery["restore_rollbacks"]) == 1
    assert state.journal_head(vault) == expected_head.read_text(encoding="utf-8").strip()
    assert state.verify_journal_chain(vault)["ok"] is True
    with state.connect(vault) as conn:
        payloads = [str(row[0]) for row in conn.execute("SELECT payload_json FROM event_log")]
    assert any("marker-crash-live" in payload for payload in payloads)


def test_restore_recovery_preserves_original_component_not_yet_moved(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    wal = Path(f"{vault / state.DB_REL}-wal")
    wal.write_bytes(b"original committed WAL bytes")
    rollback = tmp_path / f".{vault.name}.restore-rollback-before-first-move"
    stage = tmp_path / f".{vault.name}.restore-stage-before-first-move"
    rollback.mkdir()
    stage.mkdir()
    backup._write_restore_transaction(vault, rollback, stage)
    monkeypatch.setattr(
        backup.state,
        "verify_journal_chain",
        lambda _vault: {"ok": True, "head": "test-head"},
    )

    backup.recover_interrupted_restore(vault)

    assert wal.read_bytes() == b"original committed WAL bytes"


def test_restore_recovery_refuses_a_missing_original_wal(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    wal = Path(f"{vault / state.DB_REL}-wal")
    wal.write_bytes(b"original committed WAL bytes")
    rollback = tmp_path / f".{vault.name}.restore-rollback-missing-wal"
    stage = tmp_path / f".{vault.name}.restore-stage-missing-wal"
    rollback.mkdir()
    stage.mkdir()
    backup._write_restore_transaction(vault, rollback, stage)
    wal.unlink()
    (rollback / "memoria.sqlite-wal").unlink()
    monkeypatch.setattr(
        backup.state,
        "verify_journal_chain",
        lambda _vault: {"ok": True, "head": "test-head"},
    )

    with pytest.raises(ValueError, match="original restore component"):
        backup.recover_interrupted_restore(vault)

    assert (vault / backup.RESTORE_TRANSACTION_REL).is_file()
    assert rollback.is_dir()
    assert stage.is_dir()


def test_workspace_recover_restores_previous_target_after_interrupted_backup_replacement(
    tmp_path: Path, capsys
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    blob = _seed(vault)
    target = tmp_path / "interrupted-backup-target"
    assert _create(vault, target)["ok"] is True
    previous_manifest = (target / backup.MANIFEST_NAME).read_text(encoding="utf-8")
    blob.write_text("newer live evidence", encoding="utf-8")
    crash_script = tmp_path / "interrupt_backup.py"
    crash_script.write_text(
        "\n".join(
            (
                "import os",
                "from pathlib import Path",
                "from memoria_vault.cli import main",
                "from memoria_vault.runtime import backup",
                f"vault = Path({str(vault)!r})",
                f"target = Path({str(target)!r})",
                "real_replace = backup.os.replace",
                "def interrupt(source_path, destination_path):",
                "    real_replace(source_path, destination_path)",
                "    if Path(source_path) == target and '.rollback-' in Path(destination_path).name:",
                "        os._exit(87)",
                "backup.os.replace = interrupt",
                "main(['workspace', 'backup', str(target), '--workspace', str(vault), '--json'])",
                "raise SystemExit(1)",
                "",
            )
        ),
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src")}
    interrupted = subprocess.run(
        [sys.executable, str(crash_script)], env=env, check=False, capture_output=True, text=True
    )

    assert interrupted.returncode == 87
    assert not target.exists()
    assert main(["workspace", "recover", "--workspace", str(vault), "--json"]) == 0
    assert (target / backup.MANIFEST_NAME).read_text(encoding="utf-8") == previous_manifest


def test_workspace_recover_writes_stamp_after_completed_backup_publish_crash(
    tmp_path: Path, capsys
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    blob = _seed(vault)
    target = tmp_path / "published-before-crash"
    assert _create(vault, target)["ok"] is True
    blob.write_text("newer live evidence", encoding="utf-8")
    crash_script = tmp_path / "interrupt_after_backup_publish.py"
    crash_script.write_text(
        "\n".join(
            (
                "import os",
                "from pathlib import Path",
                "from memoria_vault.cli import main",
                "from memoria_vault.runtime import backup",
                f"vault = Path({str(vault)!r})",
                f"target = Path({str(target)!r})",
                "real_replace = backup.os.replace",
                "def interrupt(source_path, destination_path):",
                "    real_replace(source_path, destination_path)",
                f"    if Path(source_path).name.startswith('.{target.name}.stage-') and Path(destination_path) == target:",
                "        os._exit(87)",
                "backup.os.replace = interrupt",
                "main(['workspace', 'backup', str(target), '--workspace', str(vault), '--json'])",
                "raise SystemExit(1)",
                "",
            )
        ),
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src")}
    interrupted = subprocess.run(
        [sys.executable, str(crash_script)], env=env, check=False, capture_output=True, text=True
    )

    assert interrupted.returncode == 87
    assert (target / "blobs/source-content/w-1/raw/source.txt").read_text(
        encoding="utf-8"
    ) == "newer live evidence"
    assert backup.local_backup_status(vault)["valid"] is False
    assert main(["workspace", "recover", "--workspace", str(vault), "--json"]) == 0
    assert backup.local_backup_status(vault)["valid"] is True


def test_workspace_recover_writes_stamp_after_first_backup_publish_crash(
    tmp_path: Path, capsys
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    target = tmp_path / "first-published-before-crash"
    crash_script = tmp_path / "interrupt_after_first_backup_publish.py"
    crash_script.write_text(
        "\n".join(
            (
                "import os",
                "from pathlib import Path",
                "from memoria_vault.cli import main",
                "from memoria_vault.runtime import backup",
                f"vault = Path({str(vault)!r})",
                f"target = Path({str(target)!r})",
                "real_replace = backup.os.replace",
                "def interrupt(source_path, destination_path):",
                "    real_replace(source_path, destination_path)",
                f"    if Path(source_path).name.startswith('.{target.name}.stage-') and Path(destination_path) == target:",
                "        os._exit(87)",
                "backup.os.replace = interrupt",
                "main(['workspace', 'backup', str(target), '--workspace', str(vault), '--json'])",
                "raise SystemExit(1)",
                "",
            )
        ),
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src")}
    interrupted = subprocess.run(
        [sys.executable, str(crash_script)], env=env, check=False, capture_output=True, text=True
    )

    assert interrupted.returncode == 87
    assert backup.local_backup_status(vault)["valid"] is False
    assert main(["workspace", "recover", "--workspace", str(vault), "--json"]) == 0
    assert backup.local_backup_status(vault)["valid"] is True


def test_restore_refuses_while_backup_publication_recovery_is_pending(
    tmp_path: Path, capsys
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    source = tmp_path / "restore-source"
    assert _create(vault, source)["ok"] is True
    target = tmp_path / "pending-target"
    rollback = tmp_path / ".pending-target.rollback-test"
    stage = tmp_path / ".pending-target.stage-test"
    assert _create(vault, stage)["ok"] is True
    backup._write_backup_transaction(vault, target, rollback, stage)

    report = _restore(vault, source)

    assert report["ok"] is False
    assert "interrupted backup" in str(report["error"])
    assert (vault / backup.BACKUP_TRANSACTION_REL).is_file()


def test_workspace_recover_preserves_originals_after_interrupted_in_process_rollback(
    tmp_path: Path, capsys
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    blob = _seed(vault)
    source = tmp_path / "rollback-crash-source"
    assert _create(vault, source)["ok"] is True
    blob.write_text("newer live evidence", encoding="utf-8")
    trusted_writer.append_explicit_journal_event(
        vault,
        {"event": "run", "run_id": "live-tip", "status": "started"},
        actor="operation",
        machine="live-machine",
    )
    state.write_journal_head_anchor(vault)
    live_head = state.journal_head(vault)
    crash_script = tmp_path / "interrupt_rollback.py"
    crash_script.write_text(
        "\n".join(
            (
                "import os",
                "from pathlib import Path",
                "from memoria_vault.cli import main",
                "from memoria_vault.runtime import backup",
                f"vault = Path({str(vault)!r})",
                f"source = Path({str(source)!r})",
                "real_replace = backup.os.replace",
                "real_copy = backup._copy_recovery_component",
                "def fail_journal_install(source_path, destination_path):",
                "    if '.restore-stage-' in str(source_path) and Path(destination_path).name == 'journal':",
                "        raise OSError('injected restore install failure')",
                "    return real_replace(source_path, destination_path)",
                "def interrupt_after_old_database_copy(source_path, destination_path):",
                "    real_copy(source_path, destination_path)",
                "    if '.restore-rollback-' in str(source_path) and Path(source_path).name == 'memoria.sqlite':",
                "        os._exit(87)",
                "backup.os.replace = fail_journal_install",
                "backup._copy_recovery_component = interrupt_after_old_database_copy",
                "main(['workspace', 'restore', str(source), '--workspace', str(vault), '--force', '--json'])",
                "raise SystemExit(1)",
                "",
            )
        ),
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).parents[1] / "src")}
    interrupted = subprocess.run(
        [sys.executable, str(crash_script)], env=env, check=False, capture_output=True, text=True
    )

    assert interrupted.returncode == 87
    assert main(["workspace", "recover", "--workspace", str(vault), "--json"]) == 0
    assert blob.read_text(encoding="utf-8") == "newer live evidence"
    assert state.journal_head(vault) == live_head
    assert state.verify_journal_chain(vault)["ok"] is True


def test_workspace_recover_rejects_transaction_sibling_escape(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    rollback = tmp_path / f".{vault.name}.restore-rollback-forged"
    stage = tmp_path / f".{vault.name}.restore-stage-forged"
    rollback.mkdir()
    stage.mkdir()
    backup._write_restore_transaction(vault, rollback, stage)
    marker = vault / backup.RESTORE_TRANSACTION_REL
    value = json.loads(marker.read_text(encoding="utf-8"))
    value["rollback"] = f"../.{vault.name}.restore-rollback-forged"
    marker.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ValueError, match="rollback directory"):
        backup.recover_interrupted_restore(vault)


def test_workspace_recover_rejects_restore_transaction_marker_directory(
    tmp_path: Path, capsys
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    rollback = tmp_path / f".{vault.name}.restore-rollback-marker-directory"
    stage = tmp_path / f".{vault.name}.restore-stage-marker-directory"
    rollback.mkdir()
    stage.mkdir()
    backup._write_restore_transaction(vault, rollback, stage)
    marker = vault / backup.RESTORE_TRANSACTION_REL
    marker.unlink()
    marker.mkdir()

    with pytest.raises(ValueError, match="marker"):
        backup.recover_interrupted_restore(vault)

    assert rollback.is_dir()
    assert stage.is_dir()


def test_workspace_recover_rejects_mismatched_restore_directory_identity(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    rollback = tmp_path / f".{vault.name}.restore-rollback-identity"
    stage = tmp_path / f".{vault.name}.restore-stage-identity"
    rollback.mkdir()
    stage.mkdir()
    backup._write_restore_transaction(vault, rollback, stage)
    marker_path = vault / backup.RESTORE_TRANSACTION_REL
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    marker["transaction_id"] = "a" * 32
    marker_path.write_text(json.dumps(marker), encoding="utf-8")
    identity_name = ".memoria-transaction-identity.json"
    for directory, role, transaction_id in (
        (rollback, "rollback", "b" * 32),
        (stage, "stage", "a" * 32),
    ):
        (directory / identity_name).write_text(
            json.dumps(
                {
                    "format": "memoria-transaction-directory",
                    "version": 1,
                    "transaction_id": transaction_id,
                    "vault": str(vault.resolve()),
                    "role": role,
                    "directory": directory.name,
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(
        backup.state,
        "verify_journal_chain",
        lambda _vault: {"ok": True, "head": "test-head"},
    )

    with pytest.raises(ValueError, match="identity"):
        backup.recover_interrupted_restore(vault)

    assert rollback.is_dir()
    assert stage.is_dir()


def test_workspace_recover_rejects_unbound_v1_restore_transaction(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    rollback = tmp_path / f".{vault.name}.restore-rollback-legacy-v1"
    stage = tmp_path / f".{vault.name}.restore-stage-legacy-v1"
    rollback.mkdir()
    stage.mkdir()
    rollback_sentinel = rollback / "legacy-sentinel"
    stage_sentinel = stage / "legacy-sentinel"
    rollback_sentinel.write_text("keep", encoding="utf-8")
    stage_sentinel.write_text("keep", encoding="utf-8")
    for live_rel, rollback_rel, _staged_rel in backup._restore_components():
        live = vault / live_rel
        saved = rollback / rollback_rel
        if live.is_dir():
            shutil.copytree(live, saved, symlinks=True)
        elif live.is_file():
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(live, saved, follow_symlinks=False)
    (vault / backup.RESTORE_TRANSACTION_REL).write_text(
        json.dumps(
            {
                "format": backup.RESTORE_TRANSACTION_FORMAT,
                "version": 1,
                "vault": str(vault.resolve()),
                "rollback": rollback.name,
                "stage": stage.name,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="identity"):
        backup.recover_interrupted_restore(vault)

    assert (vault / backup.RESTORE_TRANSACTION_REL).is_file()
    assert rollback_sentinel.read_text(encoding="utf-8") == "keep"
    assert stage_sentinel.read_text(encoding="utf-8") == "keep"


def test_workspace_recover_rejects_unbound_v1_backup_transaction(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    target = tmp_path / "legacy-backup-target"
    stage = tmp_path / ".legacy-backup-target.stage-legacy"
    rollback = tmp_path / ".legacy-backup-target.rollback-legacy"
    assert _create(vault, target)["ok"] is True
    original_manifest = (target / backup.MANIFEST_NAME).read_bytes()
    assert _create(vault, stage)["ok"] is True
    target.rename(rollback)
    (vault / backup.BACKUP_TRANSACTION_REL).write_text(
        json.dumps(
            {
                "format": backup.BACKUP_TRANSACTION_FORMAT,
                "version": 1,
                "vault": str(vault.resolve()),
                "target": str(target),
                "rollback": rollback.name,
                "stage": stage.name,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="identity"):
        backup.recover_interrupted_backup(vault)

    assert not target.exists()
    assert (rollback / backup.MANIFEST_NAME).read_bytes() == original_manifest
    assert (vault / backup.BACKUP_TRANSACTION_REL).is_file()
    assert stage.is_dir()


def test_workspace_recover_preserves_ambiguous_legacy_v1_recovery_material(
    tmp_path: Path, capsys
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    rollback = tmp_path / f".{vault.name}.restore-rollback-legacy-ambiguous"
    stage = tmp_path / f".{vault.name}.restore-stage-legacy-ambiguous"
    rollback.mkdir()
    stage.mkdir()
    sentinel = rollback / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    (vault / backup.RESTORE_TRANSACTION_REL).write_text(
        json.dumps(
            {
                "format": backup.RESTORE_TRANSACTION_FORMAT,
                "version": 1,
                "vault": str(vault.resolve()),
                "rollback": rollback.name,
                "stage": stage.name,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="identity"):
        backup.recover_interrupted_restore(vault)

    assert (vault / backup.RESTORE_TRANSACTION_REL).is_file()
    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert stage.is_dir()


def test_workspace_recover_does_not_mutate_before_legacy_ambiguity(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    rollback = tmp_path / f".{vault.name}.restore-rollback-legacy-partial"
    stage = tmp_path / f".{vault.name}.restore-stage-legacy-partial"
    rollback.mkdir()
    stage.mkdir()
    saved_journal = rollback / "journal"
    shutil.copytree(vault / ".memoria/journal", saved_journal)
    (saved_journal / "recovery-only.txt").write_text("must not install", encoding="utf-8")
    (vault / backup.RESTORE_TRANSACTION_REL).write_text(
        json.dumps(
            {
                "format": backup.RESTORE_TRANSACTION_FORMAT,
                "version": 1,
                "vault": str(vault.resolve()),
                "rollback": rollback.name,
                "stage": stage.name,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="legacy"):
        backup.recover_interrupted_restore(vault)

    assert not (vault / ".memoria/journal/recovery-only.txt").exists()
    assert (vault / backup.RESTORE_TRANSACTION_REL).is_file()
    assert saved_journal.is_dir()
    assert stage.is_dir()


def test_restore_transaction_writer_rejects_symlinked_recovery_directory(
    tmp_path: Path, capsys
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    outside = tmp_path / "outside-rollback"
    outside.mkdir()
    rollback = tmp_path / f".{vault.name}.restore-rollback-link"
    rollback.symlink_to(outside, target_is_directory=True)
    stage = tmp_path / f".{vault.name}.restore-stage-real"
    stage.mkdir()

    with pytest.raises(ValueError, match="symlink"):
        backup._write_restore_transaction(vault, rollback, stage)

    assert not (outside / backup.TRANSACTION_DIRECTORY_IDENTITY).exists()


def test_restore_preserves_bound_rollback_when_marker_publication_reports_failure(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    stage = tmp_path / f".{vault.name}.restore-stage-marker-failure"
    stage.mkdir()
    real_write_transaction = backup._write_restore_transaction

    def publish_then_fail(vault_path: Path, rollback: Path, stage_path: Path) -> None:
        real_write_transaction(vault_path, rollback, stage_path)
        raise OSError("injected post-marker failure")

    monkeypatch.setattr(backup, "_write_restore_transaction", publish_then_fail)

    with pytest.raises(OSError, match="injected post-marker failure"):
        backup._install_restore_stage(
            vault,
            stage,
            tmp_path / "unused-source",
            {},
            "pi",
            "backup-test",
        )

    marker_path = vault / backup.RESTORE_TRANSACTION_REL
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    assert (vault.parent / marker["rollback"]).is_dir()
    assert stage.is_dir()


def test_restore_transaction_writer_propagates_identity_directory_fsync_failure(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    rollback = tmp_path / f".{vault.name}.restore-rollback-fsync"
    stage = tmp_path / f".{vault.name}.restore-stage-fsync"
    rollback.mkdir()
    stage.mkdir()

    def fail_identity_fsync(path: Path) -> None:
        if Path(path) == rollback and (rollback / backup.TRANSACTION_DIRECTORY_IDENTITY).exists():
            raise OSError("injected identity directory fsync failure")

    monkeypatch.setattr(backup, "_fsync_directory", fail_identity_fsync)

    with pytest.raises(OSError, match="identity directory fsync failure"):
        backup._write_restore_transaction(vault, rollback, stage)

    assert not (vault / backup.RESTORE_TRANSACTION_REL).exists()


def test_restore_transaction_writer_propagates_marker_directory_fsync_failure(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    rollback = tmp_path / f".{vault.name}.restore-rollback-marker-fsync"
    stage = tmp_path / f".{vault.name}.restore-stage-marker-fsync"
    rollback.mkdir()
    stage.mkdir()
    marker = vault / backup.RESTORE_TRANSACTION_REL

    def fail_marker_fsync(path: Path) -> None:
        if Path(path) == marker.parent and marker.exists():
            raise OSError("injected marker directory fsync failure")

    monkeypatch.setattr(backup, "_fsync_directory", fail_marker_fsync)

    with pytest.raises(OSError, match="marker directory fsync failure"):
        backup._write_restore_transaction(vault, rollback, stage)

    assert marker.is_file()
    assert rollback.is_dir()
    assert stage.is_dir()


def test_backup_transaction_writer_propagates_marker_directory_fsync_failure(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    target = tmp_path / "marker-fsync-target"
    rollback = tmp_path / ".marker-fsync-target.rollback-bound"
    stage = tmp_path / ".marker-fsync-target.stage-bound"
    assert _create(vault, target)["ok"] is True
    assert _create(vault, stage)["ok"] is True
    marker = vault / backup.BACKUP_TRANSACTION_REL

    def fail_marker_fsync(path: Path) -> None:
        if Path(path) == marker.parent and marker.exists():
            raise OSError("injected marker directory fsync failure")

    monkeypatch.setattr(backup, "_fsync_directory", fail_marker_fsync)

    with pytest.raises(OSError, match="marker directory fsync failure"):
        backup._write_backup_transaction(vault, target, rollback, stage)

    assert marker.is_file()
    assert target.is_dir()
    assert stage.is_dir()


def test_workspace_recover_rejects_substituted_valid_backup_stage(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    target = tmp_path / "identity-bound-target"
    stage = tmp_path / ".identity-bound-target.stage-recorded"
    rollback = tmp_path / ".identity-bound-target.rollback-recorded"
    substitute = tmp_path / "valid-stage-substitute"
    assert _create(vault, target)["ok"] is True
    assert _create(vault, stage)["ok"] is True
    assert _create(vault, substitute)["ok"] is True
    backup._write_backup_transaction(vault, target, rollback, stage)
    held_stage = tmp_path / "held-original-stage"
    stage.rename(held_stage)
    substitute.rename(stage)

    with pytest.raises(ValueError, match="identity"):
        backup.recover_interrupted_backup(vault)

    assert (vault / backup.BACKUP_TRANSACTION_REL).is_file()
    assert (stage / backup.MANIFEST_NAME).is_file()
    assert (target / backup.MANIFEST_NAME).is_file()


def test_workspace_recover_rejects_substituted_published_backup_after_identity_cleanup(
    tmp_path: Path, capsys
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    blob = _seed(vault)
    target = tmp_path / "identity-bound-terminal-target"
    stage = tmp_path / ".identity-bound-terminal-target.stage-recorded"
    rollback = tmp_path / ".identity-bound-terminal-target.rollback-recorded"
    substitute = tmp_path / "identity-bound-terminal-substitute"
    assert _create(vault, target)["ok"] is True
    blob.write_text("replacement evidence bytes", encoding="utf-8")
    assert _create(vault, stage)["ok"] is True
    assert _create(vault, substitute)["ok"] is True
    backup._write_backup_transaction(vault, target, rollback, stage)
    target.rename(rollback)
    stage.rename(target)
    transaction = backup._read_backup_transaction(vault)
    assert transaction is not None
    backup._set_backup_transaction_phase(vault, transaction, "published-cleanup")
    (target / backup.TRANSACTION_DIRECTORY_IDENTITY).unlink()
    target.rename(tmp_path / "held-published-backup")
    substitute.rename(target)

    with pytest.raises(ValueError, match="identity"):
        backup.recover_interrupted_backup(vault)

    assert (vault / backup.BACKUP_TRANSACTION_REL).is_file()


def test_workspace_recover_rejects_substituted_valid_backup_rollback(
    tmp_path: Path, capsys
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    target = tmp_path / "identity-bound-target"
    stage = tmp_path / ".identity-bound-target.stage-recorded"
    rollback = tmp_path / ".identity-bound-target.rollback-recorded"
    substitute = tmp_path / "valid-rollback-substitute"
    assert _create(vault, target)["ok"] is True
    assert _create(vault, stage)["ok"] is True
    assert _create(vault, substitute)["ok"] is True
    backup._write_backup_transaction(vault, target, rollback, stage)
    target.rename(rollback)
    held_rollback = tmp_path / "held-original-rollback"
    rollback.rename(held_rollback)
    substitute.rename(rollback)

    with pytest.raises(ValueError, match="identity"):
        backup.recover_interrupted_backup(vault)

    assert (vault / backup.BACKUP_TRANSACTION_REL).is_file()
    assert (rollback / backup.MANIFEST_NAME).is_file()
    assert not target.exists()


def test_workspace_recover_rejects_unrecognized_backup_rollback(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    target = tmp_path / "missing-backup-target"
    rollback = tmp_path / ".missing-backup-target.rollback-forged"
    stage = tmp_path / ".missing-backup-target.stage-forged"
    assert _create(vault, rollback)["ok"] is True
    assert _create(vault, stage)["ok"] is True
    backup._write_backup_transaction(vault, target, rollback, stage)
    (rollback / backup.MANIFEST_NAME).unlink()
    sentinel = rollback / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(ValueError, match="recognized Memoria backup"):
        backup.recover_interrupted_backup(vault)

    assert not target.exists()
    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_workspace_recover_does_not_delete_unrecognized_backup_stage(
    tmp_path: Path, capsys
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    target = tmp_path / "complete-backup-target"
    assert _create(vault, target)["ok"] is True
    rollback = tmp_path / ".complete-backup-target.rollback-forged"
    stage = tmp_path / ".complete-backup-target.stage-forged"
    assert _create(vault, stage)["ok"] is True
    backup._write_backup_transaction(vault, target, rollback, stage)
    (stage / backup.MANIFEST_NAME).unlink()
    sentinel = stage / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(ValueError, match="recognized Memoria backup"):
        backup.recover_interrupted_backup(vault)

    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_workspace_recover_requires_pi_actor(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)

    assert (
        main(
            [
                "workspace",
                "recover",
                "--workspace",
                str(vault),
                "--actor",
                "agent",
                "--json",
            ]
        )
        == 2
    )


def test_workspace_recover_text_output_summarizes_recovery(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    capsys.readouterr()

    assert main(["workspace", "recover", "--workspace", str(vault)]) == 0

    output = capsys.readouterr().out.strip()
    assert output.startswith("workspace recovery:")
    assert "0 restore rollbacks" in output
    assert "0 backup targets" in output


def test_workspace_recover_rejects_symlinked_runtime_before_lock_creation(
    tmp_path: Path, capsys
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    outside_runtime = tmp_path / "outside-runtime"
    (vault / ".memoria").rename(outside_runtime)
    (vault / ".memoria").symlink_to(outside_runtime, target_is_directory=True)
    outside_lock = outside_runtime / "locks/worker.lock"
    outside_lock.unlink(missing_ok=True)

    assert main(["workspace", "recover", "--workspace", str(vault), "--json"]) == 2

    assert not outside_lock.exists()


def test_workspace_recover_rejects_redirected_worker_lock_before_open(
    tmp_path: Path, capsys
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    worker_lock = vault / ".memoria/locks/worker.lock"
    worker_lock.parent.mkdir(parents=True, exist_ok=True)
    worker_lock.unlink(missing_ok=True)
    outside_lock = tmp_path / "outside-worker.lock"
    worker_lock.symlink_to(outside_lock)

    assert main(["workspace", "recover", "--workspace", str(vault), "--json"]) == 2

    assert not outside_lock.exists()


@pytest.mark.parametrize("redirect_parent", [False, True])
def test_workspace_lock_rejects_redirected_lock_path(tmp_path: Path, redirect_parent: bool) -> None:
    vault = tmp_path / "workspace"
    runtime = vault / ".memoria"
    runtime.mkdir(parents=True)
    outside_locks = tmp_path / "outside-locks"
    outside_locks.mkdir()
    outside_lock = outside_locks / "worker.lock"
    if redirect_parent:
        (runtime / "locks").symlink_to(outside_locks, target_is_directory=True)
    else:
        locks = runtime / "locks"
        locks.mkdir()
        (locks / "worker.lock").symlink_to(outside_lock)

    with pytest.raises(
        ValueError, match="workspace lock path must not redirect through a symlink or junction"
    ):
        with state.workspace_lock(vault):
            pass

    assert not outside_lock.exists()


def test_workspace_lock_fails_closed_without_no_follow_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = tmp_path / "workspace"
    lock_path = vault / ".memoria/locks/worker.lock"
    lock_path.parent.mkdir(parents=True)
    outside_lock = tmp_path / "outside-worker.lock"
    real_open = Path.open

    def replace_lock_before_open(path: Path, *args, **kwargs):
        if Path(path) == lock_path:
            lock_path.symlink_to(outside_lock)
        return real_open(path, *args, **kwargs)

    monkeypatch.delattr(state.os, "O_NOFOLLOW")
    monkeypatch.setattr(Path, "open", replace_lock_before_open)

    with pytest.raises(ValueError, match="no-follow"):
        with state.workspace_lock(vault):
            pass

    assert not outside_lock.exists()


def test_workspace_lock_uses_native_safe_opener_on_windows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = tmp_path / "workspace"
    lock_path = vault / ".memoria/locks/worker.lock"
    real_os = state.os
    sentinel = object()

    class WindowsOS:
        name = "nt"

        def __getattr__(self, name: str):
            return getattr(real_os, name)

    monkeypatch.setattr(state, "os", WindowsOS())
    monkeypatch.setattr(
        state,
        "_open_workspace_lock_file_windows",
        lambda _vault, _lock_path: sentinel,
        raising=False,
    )

    opened = state._open_workspace_lock_file(vault, lock_path)
    try:
        assert opened is sentinel
    finally:
        if opened is not sentinel:
            opened.close()


@pytest.mark.skipif(os.name != "nt", reason="requires a native Windows handle backend")
def test_windows_workspace_lock_smoke_rejects_reparse_component(tmp_path: Path) -> None:
    vault = tmp_path / "workspace"
    vault.mkdir()
    lock_path = vault / ".memoria/locks/worker.lock"

    with state.workspace_lock(vault):
        assert lock_path.is_file()

    lock_path.unlink()
    locks = lock_path.parent
    locks.rmdir()
    outside_locks = tmp_path / "outside-locks"
    outside_locks.mkdir()
    created = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(locks), str(outside_locks)],
        capture_output=True,
        text=True,
        check=False,
    )
    if created.returncode:
        pytest.skip(f"Windows junction creation is unavailable: {created.stderr.strip()}")
    try:
        with pytest.raises(
            ValueError, match="workspace lock path must not redirect through a symlink or junction"
        ):
            with state.workspace_lock(vault):
                pass

        assert not (outside_locks / "worker.lock").exists()
    finally:
        locks.rmdir()


def test_workspace_recover_preserves_rollback_when_verification_fails(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    rollback = tmp_path / f".{vault.name}.restore-rollback-test"
    stage = tmp_path / f".{vault.name}.restore-stage-test"
    rollback.mkdir()
    stage.mkdir()
    saved_database = rollback / "memoria.sqlite"
    saved_database.write_bytes((vault / state.DB_REL).read_bytes())
    backup._write_restore_transaction(vault, rollback, stage)
    monkeypatch.setattr(
        backup.state,
        "verify_journal_chain",
        lambda _vault: {"ok": False, "error": "injected verification failure"},
    )

    with pytest.raises(ValueError, match="injected verification failure"):
        backup.recover_interrupted_restore(vault)

    assert saved_database.is_file()
    assert (vault / backup.RESTORE_TRANSACTION_REL).is_file()


def test_restore_recovery_resumes_identity_bound_terminal_cleanup(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    rollback = tmp_path / f".{vault.name}.restore-rollback-terminal"
    stage = tmp_path / f".{vault.name}.restore-stage-terminal"
    rollback.mkdir()
    stage.mkdir()
    backup._write_restore_transaction(vault, rollback, stage)
    monkeypatch.setattr(
        backup.state,
        "verify_journal_chain",
        lambda _vault: {"ok": True, "head": "test-head"},
    )
    real_cleanup = backup._cleanup_directory

    def interrupt_after_rollback_cleanup(path: Path) -> None:
        real_cleanup(path)
        if Path(path) == rollback:
            raise OSError("injected terminal cleanup interruption")

    monkeypatch.setattr(backup, "_cleanup_directory", interrupt_after_rollback_cleanup)

    with pytest.raises(OSError, match="terminal cleanup interruption"):
        backup.recover_interrupted_restore(vault)

    marker_path = vault / backup.RESTORE_TRANSACTION_REL
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    assert marker["phase"] == "rollback-cleanup"
    assert not rollback.exists()
    assert stage.is_dir()

    monkeypatch.setattr(backup, "_cleanup_directory", real_cleanup)
    report = backup.recover_interrupted_restore(vault)

    assert report["recovered"] is True
    assert not marker_path.exists()
    assert not stage.exists()


def test_backup_recovery_resumes_identity_bound_terminal_cleanup(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    target = tmp_path / "terminal-cleanup-target"
    rollback = tmp_path / ".terminal-cleanup-target.rollback-bound"
    stage = tmp_path / ".terminal-cleanup-target.stage-bound"
    assert _create(vault, target)["ok"] is True
    assert _create(vault, stage)["ok"] is True
    backup._write_backup_transaction(vault, target, rollback, stage)
    real_cleanup = backup._cleanup_directory

    def interrupt_after_stage_cleanup(path: Path) -> None:
        real_cleanup(path)
        if Path(path) == stage:
            raise OSError("injected terminal cleanup interruption")

    monkeypatch.setattr(backup, "_cleanup_directory", interrupt_after_stage_cleanup)

    with pytest.raises(OSError, match="terminal cleanup interruption"):
        backup.recover_interrupted_backup(vault)

    marker_path = vault / backup.BACKUP_TRANSACTION_REL
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    assert marker["phase"] == "rolled-back-cleanup"
    assert not stage.exists()
    assert target.is_dir()

    monkeypatch.setattr(backup, "_cleanup_directory", real_cleanup)
    report = backup.recover_interrupted_backup(vault)

    assert report["recovered"] is True
    assert report["outcome"] == "rolled_back"
    assert not marker_path.exists()
    assert not (target / backup.TRANSACTION_DIRECTORY_IDENTITY).exists()


def test_backup_recovery_removes_marker_before_target_identity(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    target = tmp_path / "marker-before-identity-target"
    rollback = tmp_path / ".marker-before-identity-target.rollback-test"
    stage = tmp_path / ".marker-before-identity-target.stage-test"
    assert _create(vault, target)["ok"] is True
    assert _create(vault, stage)["ok"] is True
    backup._write_backup_transaction(vault, target, rollback, stage)
    real_remove_marker = backup._remove_backup_transaction

    def remove_marker_after_identity_check(candidate: Path) -> None:
        assert (target / backup.TRANSACTION_DIRECTORY_IDENTITY).is_file()
        real_remove_marker(candidate)

    monkeypatch.setattr(backup, "_remove_backup_transaction", remove_marker_after_identity_check)

    report = backup.recover_interrupted_backup(vault)

    assert report["outcome"] == "rolled_back"
    assert not (vault / backup.BACKUP_TRANSACTION_REL).exists()
    assert not (target / backup.TRANSACTION_DIRECTORY_IDENTITY).exists()


def test_backup_publish_tolerates_post_marker_identity_cleanup_failure(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    target = tmp_path / "post-marker-cleanup-target"
    real_remove_identity = backup._remove_transaction_directory_identity

    def fail_target_identity_cleanup(directory: Path) -> None:
        if Path(directory) == target:
            raise OSError("injected target identity cleanup failure")
        real_remove_identity(directory)

    monkeypatch.setattr(
        backup,
        "_remove_transaction_directory_identity",
        fail_target_identity_cleanup,
    )

    report = _create(vault, target)

    assert report["ok"] is True
    assert not (vault / backup.BACKUP_TRANSACTION_REL).exists()
    assert (target / backup.TRANSACTION_DIRECTORY_IDENTITY).is_file()


def test_restore_recovery_resumes_after_identity_is_removed_from_empty_cleanup_dir(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    rollback = tmp_path / f".{vault.name}.restore-rollback-empty-terminal"
    stage = tmp_path / f".{vault.name}.restore-stage-empty-terminal"
    rollback.mkdir()
    stage.mkdir()
    backup._write_restore_transaction(vault, rollback, stage)
    monkeypatch.setattr(
        backup.state,
        "verify_journal_chain",
        lambda _vault: {"ok": True, "head": "test-head"},
    )
    real_cleanup = backup._cleanup_directory

    def interrupt_before_empty_directory_removal(path: Path) -> None:
        if Path(path) == rollback:
            raise OSError("injected empty-directory cleanup interruption")
        real_cleanup(path)

    monkeypatch.setattr(backup, "_cleanup_directory", interrupt_before_empty_directory_removal)

    with pytest.raises(OSError, match="empty-directory cleanup interruption"):
        backup.recover_interrupted_restore(vault)

    marker_path = vault / backup.RESTORE_TRANSACTION_REL
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    assert marker["phase"] == "rollback-cleanup"
    assert rollback.is_dir()
    assert not list(rollback.iterdir())

    monkeypatch.setattr(backup, "_cleanup_directory", real_cleanup)
    report = backup.recover_interrupted_restore(vault)

    assert report["recovered"] is True
    assert not marker_path.exists()
    assert not rollback.exists()
    assert not stage.exists()


def test_successful_restore_resumes_identity_bound_terminal_cleanup(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    blob = _seed(vault)
    source = tmp_path / "commit-cleanup-source"
    assert _create(vault, source)["ok"] is True
    blob.write_text("newer live evidence", encoding="utf-8")
    real_cleanup = backup._cleanup_directory

    def interrupt_after_rollback_cleanup(path: Path) -> None:
        real_cleanup(path)
        if ".restore-rollback-" in Path(path).name:
            raise OSError("injected commit cleanup interruption")

    monkeypatch.setattr(backup, "_cleanup_directory", interrupt_after_rollback_cleanup)

    with pytest.raises(OSError, match="commit cleanup interruption"):
        _restore(vault, source)

    marker_path = vault / backup.RESTORE_TRANSACTION_REL
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    assert marker["phase"] == "commit-cleanup"
    assert blob.read_text(encoding="utf-8") == "evidence bytes"

    monkeypatch.setattr(backup, "_cleanup_directory", real_cleanup)
    report = backup.recover_interrupted_restore(vault)

    assert report["outcome"] == "committed"
    assert blob.read_text(encoding="utf-8") == "evidence bytes"
    assert not marker_path.exists()


def test_restore_rollback_restores_previous_local_backup_stamp(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    blob = _seed(vault)
    source = tmp_path / "restore-stamp-source"
    assert _create(vault, source)["ok"] is True
    blob.write_text("newer live evidence", encoding="utf-8")
    coverage = tmp_path / "restore-stamp-coverage"
    assert _create(vault, coverage)["ok"] is True
    stamp_path = vault / backup.LAST_BACKUP_REL
    previous_stamp = stamp_path.read_bytes()
    real_set_phase = backup._set_restore_transaction_phase

    def interrupt_before_commit_cleanup(
        vault_path: Path, transaction: dict[str, object], phase: str
    ) -> dict[str, object]:
        if phase == "commit-cleanup":
            raise OSError("injected pre-commit-cleanup interruption")
        return real_set_phase(vault_path, transaction, phase)

    monkeypatch.setattr(backup, "_set_restore_transaction_phase", interrupt_before_commit_cleanup)

    with pytest.raises(OSError, match="pre-commit-cleanup interruption"):
        _restore(vault, source)

    assert json.loads(stamp_path.read_text(encoding="utf-8"))["target"] == str(source)
    monkeypatch.setattr(backup, "_set_restore_transaction_phase", real_set_phase)

    report = backup.recover_interrupted_restore(vault)

    assert report["outcome"] == "rolled_back"
    assert blob.read_text(encoding="utf-8") == "newer live evidence"
    assert stamp_path.read_bytes() == previous_stamp
    assert backup.local_backup_status(vault)["valid"] is True


def test_restore_preserves_recovery_material_when_rollback_itself_fails(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    blob = _seed(vault)
    source = tmp_path / "rollback-recovery-source"
    assert _create(vault, source)["ok"] is True
    blob.write_text("newer live evidence", encoding="utf-8")
    real_replace = backup.os.replace
    real_copy = backup._copy_recovery_component
    install_failed = False

    def fail_install(source_path, destination_path):
        nonlocal install_failed
        source_value = Path(source_path)
        destination_value = Path(destination_path)
        if ".restore-stage-" in str(source_value) and destination_value.name == "journal":
            install_failed = True
            raise OSError("injected restore install failure")
        return real_replace(source_path, destination_path)

    def fail_rollback(source_path, destination_path):
        if install_failed and ".restore-rollback-" in str(source_path):
            raise OSError("injected rollback failure")
        return real_copy(source_path, destination_path)

    monkeypatch.setattr(backup.os, "replace", fail_install)
    monkeypatch.setattr(backup, "_copy_recovery_component", fail_rollback)

    with pytest.raises(OSError, match="injected rollback failure"):
        _restore(vault, source)

    recovery_dirs = list(vault.parent.glob(f".{vault.name}.restore-rollback-*"))
    assert len(recovery_dirs) == 1
    assert (recovery_dirs[0] / "memoria.sqlite").is_file()
    assert (recovery_dirs[0] / "blobs/source-content/w-1/raw/source.txt").is_file()
    assert (vault / backup.RESTORE_TRANSACTION_REL).is_file()
    assert len(list(vault.parent.glob(f".{vault.name}.restore-stage-*"))) == 1


def test_restore_preserves_recovery_material_when_rollback_verification_fails(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    blob = _seed(vault)
    source = tmp_path / "rollback-verification-source"
    assert _create(vault, source)["ok"] is True
    blob.write_text("newer live evidence", encoding="utf-8")
    real_replace = backup.os.replace
    real_verify = backup.state.verify_journal_chain
    install_failed = False

    def fail_install(source_path, destination_path):
        nonlocal install_failed
        if ".restore-stage-" in str(source_path) and Path(destination_path).name == "journal":
            install_failed = True
            raise OSError("injected restore install failure")
        return real_replace(source_path, destination_path)

    def fail_rollback_verification(candidate: Path):
        report = real_verify(candidate)
        if install_failed and Path(candidate) == vault:
            return {"ok": False, "error": "injected rollback verification failure"}
        return report

    monkeypatch.setattr(backup.os, "replace", fail_install)
    monkeypatch.setattr(backup.state, "verify_journal_chain", fail_rollback_verification)

    with pytest.raises(ValueError, match="injected rollback verification failure"):
        _restore(vault, source)

    assert (vault / backup.RESTORE_TRANSACTION_REL).is_file()
    assert len(list(vault.parent.glob(f".{vault.name}.restore-rollback-*"))) == 1
    assert len(list(vault.parent.glob(f".{vault.name}.restore-stage-*"))) == 1


def test_workspace_restore_cli_requires_force_and_pi_authority(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    source = tmp_path / "cli-restore"
    assert _create(vault, source)["ok"] is True

    assert (
        main(
            [
                "workspace",
                "restore",
                str(source),
                "--workspace",
                str(vault),
                "--actor",
                "agent",
                "--force",
                "--json",
            ]
        )
        == 2
    )
    capsys.readouterr()
    assert (
        main(
            [
                "workspace",
                "restore",
                str(source),
                "--workspace",
                str(vault),
                "--json",
            ]
        )
        == 1
    )
    refusal = json.loads(capsys.readouterr().out)
    assert refusal["ok"] is False
    assert "force" in refusal["error"]

    assert (
        main(
            [
                "workspace",
                "restore",
                str(source),
                "--workspace",
                str(vault),
                "--force",
                "--json",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["ok"] is True

    assert (
        main(
            [
                "workspace",
                "restore",
                str(source),
                "--workspace",
                str(vault),
                "--force",
            ]
        )
        == 0
    )
    assert capsys.readouterr().out == f"{source.resolve()}\n"


def test_backup_report_requires_current_blob_inventory_coverage(tmp_path: Path, capsys) -> None:
    from memoria_vault.cli import _backup_report

    vault = init_cli_workspace(tmp_path, capsys)
    blob = _seed(vault)
    target = tmp_path / "doctor-backup"

    initial = _backup_report(vault)
    assert initial["ok"] is False
    assert initial["blob_sync"]["files"] == 1

    assert _create(vault, target)["ok"] is True
    covered = _backup_report(vault)
    assert covered["ok"] is True
    assert covered["local_backup"]["valid"] is True

    blob.write_text("changed after backup", encoding="utf-8")
    stale = _backup_report(vault)
    assert stale["ok"] is False
    assert stale["local_backup"]["valid"] is False
    assert "inventory" in stale["local_backup"]["error"]


def test_backup_report_rejects_stamp_when_backup_target_disappears(tmp_path: Path, capsys) -> None:
    from memoria_vault.cli import _backup_report

    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    target = tmp_path / "removed-backup"
    assert _create(vault, target)["ok"] is True
    for path in sorted(target.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()
    target.rmdir()

    report = _backup_report(vault)

    assert report["ok"] is False
    assert report["local_backup"]["valid"] is False
    assert "target" in report["local_backup"]["error"]


def test_backup_report_requires_blob_coverage_not_sqlite_only(tmp_path: Path, capsys) -> None:
    from memoria_vault.cli import _backup_report

    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    config = vault / ".memoria/config"
    config.mkdir(parents=True, exist_ok=True)
    (config / "litestream.yml").write_text("dbs: []\n", encoding="utf-8")

    sqlite_only = _backup_report(vault)
    assert sqlite_only["ok"] is False

    (config / "blob-sync.yaml").write_text("target: test\n", encoding="utf-8")
    blob_covered = _backup_report(vault)
    assert blob_covered["ok"] is True
    assert blob_covered["blob_sync"]["configured"] is True


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("blob-sync.yaml", ""),
        ("blob-sync.yaml", "target: [\n"),
        ("blob-sync.yaml", "target: '   '\n"),
        ("blob-sync.yaml", "enabled: false\ntarget: test\n"),
        ("blob-sync.yaml", "enabled: 0\ntarget: test\n"),
        ("blob-sync.yaml", "enabled: null\ntarget: test\n"),
        ("blob-sync.yaml", "enabled: 'false'\ntarget: test\n"),
        ("blob-sync.json", '{"enabled": false, "target": "test"}\n'),
    ],
)
def test_backup_report_rejects_nonfunctional_blob_coverage_config(
    tmp_path: Path, capsys, name: str, content: str
) -> None:
    from memoria_vault.cli import _backup_report

    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    config = vault / ".memoria/config" / name
    config.write_text(content, encoding="utf-8")

    report = _backup_report(vault)

    assert report["ok"] is False
    assert report["blob_sync"]["configured"] is False


def test_backup_report_rejects_symlinked_runtime_without_reading_outside_config(
    tmp_path: Path, capsys
) -> None:
    from memoria_vault.cli import _backup_report

    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    outside_runtime = tmp_path / "outside-runtime"
    (vault / ".memoria").rename(outside_runtime)
    (outside_runtime / "config/blob-sync.yaml").write_text(
        "enabled: true\ntarget: outside\n", encoding="utf-8"
    )
    (vault / ".memoria").symlink_to(outside_runtime, target_is_directory=True)

    report = _backup_report(vault)

    assert report["ok"] is False
    assert report["local_backup"]["inventory_ok"] is False
    assert report["blob_sync"]["configured"] is False


def test_backup_report_counts_files_not_directories(tmp_path: Path, capsys) -> None:
    from memoria_vault.cli import _backup_report

    vault = init_cli_workspace(tmp_path, capsys)
    (vault / ".memoria/blobs/empty/nested").mkdir(parents=True)

    report = _backup_report(vault)

    assert report["ok"] is True
    assert report["blob_sync"]["files"] == 0


def test_doctor_and_bundle_propagate_failed_backup_health(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)

    assert main(["doctor", "--workspace", str(vault), "--json"]) == 1
    doctor = json.loads(capsys.readouterr().out)
    assert doctor["ok"] is False
    assert doctor["backup"]["ok"] is False

    assert main(["doctor", "bundle", "--workspace", str(vault), "--json"]) == 1
    bundle = json.loads(capsys.readouterr().out)
    assert bundle["ok"] is False
    assert bundle["backup"]["ok"] is False
