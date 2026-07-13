"""Workspace backup, restore, and backup-health contracts."""

from __future__ import annotations

import json
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
