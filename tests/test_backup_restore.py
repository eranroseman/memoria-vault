"""Workspace backup, restore, and backup-health contracts."""

from __future__ import annotations

import json
import sqlite3
import subprocess
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


def test_backup_stamp_is_ignored_local_machine_state(tmp_path: Path, capsys) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)

    assert _create(vault, tmp_path / "ignored-stamp-backup")["ok"] is True

    ignored = subprocess.run(
        ["git", "check-ignore", "-q", ".memoria/config/last-backup"],
        cwd=vault,
        check=False,
    )
    status = subprocess.run(
        ["git", "status", "--short", "--", ".memoria/config/last-backup"],
        cwd=vault,
        check=True,
        text=True,
        capture_output=True,
    )
    assert ignored.returncode == 0
    assert status.stdout == ""


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
    assert not list(tmp_path.glob(".backup-rollback.stage-*"))
    assert not list(tmp_path.glob(".backup-rollback.rollback-*"))


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

    report = _restore(vault, source)

    assert report["ok"] is True
    wal = Path(f"{vault / state.DB_REL}-wal")
    shm = Path(f"{vault / state.DB_REL}-shm")
    assert not wal.exists() or wal.read_bytes() != b"stale-wal"
    assert not shm.exists() or shm.read_bytes() != b"stale-shm"
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


def test_restore_preserves_recovery_material_when_rollback_itself_fails(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    vault = init_cli_workspace(tmp_path, capsys)
    blob = _seed(vault)
    source = tmp_path / "rollback-recovery-source"
    assert _create(vault, source)["ok"] is True
    blob.write_text("newer live evidence", encoding="utf-8")
    real_replace = backup.os.replace
    install_failed = False

    def fail_install_then_rollback(source_path, destination_path):
        nonlocal install_failed
        source_value = Path(source_path)
        destination_value = Path(destination_path)
        if ".restore-stage-" in str(source_value) and destination_value.name == "journal":
            install_failed = True
            raise OSError("injected restore install failure")
        if install_failed and ".restore-rollback-" in str(source_value):
            raise OSError("injected rollback failure")
        return real_replace(source_path, destination_path)

    monkeypatch.setattr(backup.os, "replace", fail_install_then_rollback)

    with pytest.raises(OSError, match="injected rollback failure"):
        _restore(vault, source)

    recovery_dirs = list(vault.parent.glob(f".{vault.name}.restore-rollback-*"))
    assert len(recovery_dirs) == 1
    assert (recovery_dirs[0] / "memoria.sqlite").is_file()
    assert (recovery_dirs[0] / "blobs/source-content/w-1/raw/source.txt").is_file()


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
