"""Backup and restore the workspace stores that Git cannot rebuild."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.time import now_iso
from memoria_vault.runtime.vaultio import write_bytes_durable, write_text_durable

BACKUP_FORMAT = "memoria-workspace-backup"
BACKUP_VERSION = 1
MANIFEST_NAME = "manifest.json"
BLOBS_REL = ".memoria/blobs"
LAST_BACKUP_REL = ".memoria/config/last-backup"


def create_backup(
    vault: Path,
    target: Path,
    *,
    actor: str,
    machine: str,
) -> dict[str, Any]:
    """Publish one coherent, manifest-bound backup snapshot."""
    _require_pi_maintenance(actor, machine)
    vault = Path(vault).resolve()
    raw_target = Path(target).expanduser()
    if raw_target.is_symlink():
        return _failure("backup target must not be a symlink")
    target = raw_target.resolve(strict=False)
    if _paths_overlap(vault, target):
        return _failure("backup target and live vault must not overlap")
    target_error = _replaceable_target_error(target)
    if target_error:
        return _failure(target_error)

    from memoria_vault.runtime.trusted_writer import reconcile_journal_export

    with state.workspace_lock(vault):
        journal = state.verify_journal_chain(vault)
        if not journal["ok"]:
            return _failure(f"journal verification failed: {journal['error']}")
        try:
            reconcile_journal_export(vault)
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            return _failure(f"journal reconciliation failed: {exc}")
        journal = state.verify_journal_chain(vault)
        if not journal["ok"]:
            return _failure(f"journal verification failed after reconciliation: {journal['error']}")

        target.parent.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix=f".{target.name}.stage-", dir=target.parent))
        try:
            database = stage / "memoria.sqlite"
            _snapshot_database(vault / state.DB_REL, database)
            database_sha256 = _file_sha256(database)

            source_blobs = vault / BLOBS_REL
            source_inventory = blob_inventory(source_blobs)
            _copy_blob_tree(source_blobs, stage / "blobs", source_inventory["entries"])
            staged_inventory = blob_inventory(stage / "blobs")
            if staged_inventory != source_inventory:
                raise RuntimeError("blob store changed while the backup was being copied")

            anchor_path = vault / state.JOURNAL_HEAD_REL
            has_anchor = anchor_path.is_file()
            if anchor_path.is_symlink():
                raise ValueError("journal-head must not be a symlink")
            anchor = ""
            if has_anchor:
                anchor_bytes = anchor_path.read_bytes()
                anchor = anchor_bytes.decode("utf-8").strip()
                write_bytes_durable(stage / "journal-head", anchor_bytes)

            created_at = now_iso()
            manifest = {
                "format": BACKUP_FORMAT,
                "version": BACKUP_VERSION,
                "created_at": created_at,
                "database": {
                    "path": "memoria.sqlite",
                    "sha256": database_sha256,
                },
                "blobs": {
                    "path": "blobs",
                    "files": source_inventory["files"],
                    "sha256": source_inventory["sha256"],
                },
                "journal_head": {
                    "path": "journal-head" if has_anchor else None,
                    "value": anchor if has_anchor else None,
                },
            }
            write_text_durable(
                stage / MANIFEST_NAME,
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            )
            _publish_backup_directory(stage, target)
            stage = None

            stamp = {
                "format": BACKUP_FORMAT,
                "version": BACKUP_VERSION,
                "created_at": created_at,
                "target": str(target),
                "blob_files": source_inventory["files"],
                "blob_sha256": source_inventory["sha256"],
            }
            write_text_durable(
                vault / LAST_BACKUP_REL,
                json.dumps(stamp, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                create_parent=True,
            )
        except BaseException:
            if stage is not None:
                shutil.rmtree(stage, ignore_errors=True)
            raise

    return {
        "ok": True,
        "target": str(target),
        "db": True,
        "blobs": source_inventory["files"],
        "blob_sha256": source_inventory["sha256"],
        "journal_head": has_anchor,
    }


def blob_inventory(root: Path) -> dict[str, Any]:
    """Return a deterministic content inventory for one blob tree."""
    root = Path(root)
    entries: list[dict[str, Any]] = []
    if root.is_symlink():
        raise ValueError("blob root must not be a symlink")
    if root.exists() and not root.is_dir():
        raise ValueError("blob root must be a directory")
    if root.is_dir():
        for path in sorted(root.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"blob tree contains a symlink: {path.relative_to(root)}")
            if path.is_dir():
                continue
            if not path.is_file():
                raise ValueError(f"blob tree contains a non-file: {path.relative_to(root)}")
            entries.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "size": path.stat().st_size,
                    "sha256": _file_sha256(path),
                }
            )
    encoded = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "files": len(entries),
        "sha256": "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
        "entries": entries,
    }


def _require_pi_maintenance(actor: str, machine: str) -> None:
    if actor != "pi":
        raise ValueError("workspace maintenance requires PI actor authority")
    if not isinstance(machine, str) or not machine.strip():
        raise ValueError("workspace maintenance machine must be nonblank")


def _paths_overlap(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def _failure(error: str) -> dict[str, Any]:
    return {"ok": False, "error": error}


def _replaceable_target_error(target: Path) -> str:
    if not os.path.lexists(target):
        return ""
    if target.is_symlink() or not target.is_dir():
        return "existing backup target is not a recognized Memoria backup directory"
    if _read_manifest(target) is None:
        return "existing target is not a recognized Memoria backup"
    return ""


def _read_manifest(root: Path) -> dict[str, Any] | None:
    path = root / MANIFEST_NAME
    if path.is_symlink() or not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict):
        return None
    if value.get("format") != BACKUP_FORMAT or value.get("version") != BACKUP_VERSION:
        return None
    return value


def _snapshot_database(source: Path, target: Path) -> None:
    if source.is_symlink() or not source.is_file():
        raise ValueError(f"workspace database is missing or invalid: {source}")
    source_uri = f"file:{source.as_posix()}?mode=ro"
    with sqlite3.connect(source_uri, uri=True) as src, sqlite3.connect(target) as dst:
        src.backup(dst)
    _fsync_file(target)


def _copy_blob_tree(
    source: Path,
    target: Path,
    entries: list[dict[str, Any]],
) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        rel = Path(str(entry["path"]))
        src = source / rel
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst, follow_symlinks=False)
        _fsync_file(dst)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def _publish_backup_directory(stage: Path, target: Path) -> None:
    target_error = _replaceable_target_error(target)
    if target_error:
        raise ValueError(target_error)
    if not os.path.lexists(target):
        os.replace(stage, target)
        return

    rollback = Path(tempfile.mkdtemp(prefix=f".{target.name}.rollback-", dir=target.parent))
    rollback.rmdir()
    os.replace(target, rollback)
    try:
        os.replace(stage, target)
    except BaseException:
        os.replace(rollback, target)
        raise
    shutil.rmtree(rollback)
