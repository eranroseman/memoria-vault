"""Workspace backup, restore, and backup-health contracts."""

from __future__ import annotations

import json
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
