"""Backup and restore the workspace stores that Git cannot rebuild."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import sqlite3
import subprocess
import tempfile
from collections.abc import Iterable
from contextlib import closing
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.time import now_iso
from memoria_vault.runtime.vaultio import write_bytes_durable, write_text_durable

BACKUP_FORMAT = "memoria-workspace-backup"
BACKUP_VERSION = 1
MANIFEST_NAME = "manifest.json"
BLOBS_REL = ".memoria/blobs"
LAST_BACKUP_REL = ".memoria/config/last-backup"
BACKUP_TRANSACTION_FORMAT = "memoria-backup-publication-transaction"
BACKUP_TRANSACTION_VERSION = 2
BACKUP_TRANSACTION_REL = ".memoria/backup-transaction.json"
BACKUP_TRANSACTION_PHASES = frozenset({"publishing", "published-cleanup", "rolled-back-cleanup"})
RESTORE_TRANSACTION_FORMAT = "memoria-restore-transaction"
RESTORE_TRANSACTION_VERSION = 2
RESTORE_TRANSACTION_REL = ".memoria/restore-transaction.json"
RESTORE_TRANSACTION_PHASES = frozenset({"swapping", "commit-cleanup", "rollback-cleanup"})
TRANSACTION_DIRECTORY_FORMAT = "memoria-transaction-directory"
TRANSACTION_DIRECTORY_VERSION = 1
TRANSACTION_DIRECTORY_IDENTITY = ".memoria-transaction-identity.json"


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
    runtime_error = _runtime_root_error(vault)
    if runtime_error:
        return _failure(runtime_error)
    raw_target = Path(target).expanduser()
    if _path_redirects(raw_target):
        return _failure("backup target must not be a symlink")
    target = raw_target.resolve(strict=False)
    if _paths_overlap(vault, target):
        return _failure("backup target and live vault must not overlap")
    target_error = _replaceable_target_error(target)
    if target_error:
        return _failure(target_error)

    from memoria_vault.runtime.trusted_writer import reconcile_journal_export

    with state.workspace_lock(vault):
        if _read_restore_transaction(vault) is not None:
            return _failure("interrupted restore requires memoria workspace recover")
        if _read_backup_transaction(vault) is not None:
            return _failure("interrupted backup requires memoria workspace recover")
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
        _fsync_directory(target.parent)
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
            _fsync_tree(stage)
            _publish_backup_directory(stage, target, vault)
            stage = None
        except BaseException:
            if stage is not None and not _backup_transaction_binds_stage(vault, stage):
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


def _write_local_backup_stamp(vault: Path, target: Path, manifest: dict[str, Any]) -> None:
    created_at = manifest.get("created_at")
    blobs = _manifest_section(manifest, "blobs")
    blob_files = blobs.get("files")
    if not isinstance(created_at, str) or not created_at.strip():
        raise ValueError("backup stamp creation timestamp is invalid")
    if not isinstance(blob_files, int) or blob_files < 0:
        raise ValueError("backup stamp blob file count is invalid")
    stamp = {
        "format": BACKUP_FORMAT,
        "version": BACKUP_VERSION,
        "created_at": created_at,
        "target": str(target),
        "blob_files": blob_files,
        "blob_sha256": _manifest_hash(blobs, "blob inventory"),
    }
    write_text_durable(
        vault / LAST_BACKUP_REL,
        json.dumps(stamp, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        create_parent=True,
    )


def restore_backup(
    vault: Path,
    source: Path,
    *,
    force: bool = False,
    actor: str,
    machine: str,
) -> dict[str, Any]:
    """Validate and atomically restore one manifest-bound backup."""
    _require_pi_maintenance(actor, machine)
    vault = Path(vault).resolve()
    runtime_error = _runtime_root_error(vault)
    if runtime_error:
        return _failure(runtime_error)
    raw_source = Path(source).expanduser()
    if _path_redirects(raw_source):
        return _failure("backup source must not be a symlink")
    source = raw_source.resolve(strict=False)
    if _paths_overlap(vault, source):
        return _failure("backup source and live vault must not overlap")
    manifest = _read_manifest(source)
    if manifest is None:
        return _failure(f"not a recognized Memoria backup: {source}")
    if (vault / state.DB_REL).exists() and not force:
        return _failure("live database is present; pass --force to replace it")

    stage = Path(tempfile.mkdtemp(prefix=f".{vault.name}.restore-stage-", dir=vault.parent))
    _fsync_directory(vault.parent)
    try:
        try:
            validated = _stage_restore_source(source, manifest, stage)
            _fsync_tree(stage)
        except (OSError, UnicodeError, ValueError, sqlite3.DatabaseError) as exc:
            return _failure(f"backup validation failed: {exc}")

        with state.workspace_lock(vault):
            if _read_restore_transaction(vault) is not None:
                return _failure("interrupted restore requires memoria workspace recover")
            if _read_backup_transaction(vault) is not None:
                return _failure("interrupted backup requires memoria workspace recover")
            if (vault / state.DB_REL).exists() and not force:
                return _failure("live database is present; pass --force to replace it")
            try:
                committed_anchor = _committed_journal_anchor(vault)
            except (OSError, ValueError) as exc:
                return _failure(f"committed journal-head lookup failed: {exc}")
            if committed_anchor not in {None, "GENESIS"}:
                if committed_anchor not in validated["row_hashes"]:
                    return _failure(
                        "backup predates the committed journal-head; restore the matching "
                        "Git revision before restoring this backup"
                    )
            journal = _install_restore_stage(vault, stage, source, manifest, actor, machine)
            stage = None
    finally:
        if stage is not None and not _restore_transaction_binds_stage(vault, stage):
            shutil.rmtree(stage, ignore_errors=True)

    return {
        "ok": True,
        "restored_from": str(source),
        "blobs": int(manifest["blobs"]["files"]),
        "blob_sha256": str(manifest["blobs"]["sha256"]),
        "journal": journal,
    }


def blob_inventory(root: Path) -> dict[str, Any]:
    """Return a deterministic content inventory for one blob tree."""
    root = Path(root)
    entries: list[dict[str, Any]] = []
    if _path_redirects(root):
        raise ValueError("blob root must not be a symlink")
    if root.exists() and not root.is_dir():
        raise ValueError("blob root must be a directory")
    if root.is_dir():
        for path in sorted(root.rglob("*")):
            if _path_redirects(path):
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


def local_backup_status(vault: Path) -> dict[str, Any]:
    """Validate the local-backup stamp against live and backed-up blobs."""
    vault = Path(vault)
    runtime_error = _runtime_root_error(vault)
    if runtime_error:
        return {
            "valid": False,
            "stamp_exists": False,
            "stamp_path": LAST_BACKUP_REL,
            "target": "",
            "blob_files": 0,
            "blob_sha256": "",
            "inventory_ok": False,
            "error": runtime_error,
        }
    try:
        current = blob_inventory(vault / BLOBS_REL)
    except (OSError, ValueError) as exc:
        return {
            "valid": False,
            "stamp_exists": (vault / LAST_BACKUP_REL).is_file(),
            "stamp_path": LAST_BACKUP_REL,
            "target": "",
            "blob_files": 0,
            "blob_sha256": "",
            "inventory_ok": False,
            "error": f"live blob inventory is invalid: {exc}",
        }

    base = {
        "valid": False,
        "stamp_exists": False,
        "stamp_path": LAST_BACKUP_REL,
        "target": "",
        "blob_files": current["files"],
        "blob_sha256": current["sha256"],
        "inventory_ok": True,
        "error": "",
    }
    stamp_path = vault / LAST_BACKUP_REL
    if stamp_path.is_symlink() or not stamp_path.is_file():
        return {**base, "error": "no valid local backup stamp"}
    try:
        stamp = json.loads(stamp_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {**base, "stamp_exists": True, "error": f"backup stamp is invalid: {exc}"}
    if not isinstance(stamp, dict):
        return {**base, "stamp_exists": True, "error": "backup stamp is not an object"}

    target_value = stamp.get("target")
    target = Path(target_value) if isinstance(target_value, str) and target_value else None
    stamped_files = stamp.get("blob_files")
    stamped_hash = stamp.get("blob_sha256")
    stamped = {
        **base,
        "stamp_exists": True,
        "target": str(target) if target is not None else "",
    }
    if stamp.get("format") != BACKUP_FORMAT or stamp.get("version") != BACKUP_VERSION:
        return {**stamped, "error": "backup stamp format is invalid"}
    if stamped_files != current["files"] or stamped_hash != current["sha256"]:
        return {**stamped, "error": "backup stamp does not match the current blob inventory"}
    if target is None or not target.is_absolute() or _path_redirects(target) or not target.is_dir():
        return {**stamped, "error": "stamped backup target is missing or invalid"}
    manifest = _read_manifest(target)
    if manifest is None:
        return {**stamped, "error": "stamped backup target is not a recognized backup"}
    try:
        database_spec = _manifest_section(manifest, "database")
        blobs_spec = _manifest_section(manifest, "blobs")
        expected_database_hash = _manifest_hash(database_spec, "database")
        expected_blob_hash = _manifest_hash(blobs_spec, "blob inventory")
        database = target / "memoria.sqlite"
        if database.is_symlink() or not database.is_file():
            raise ValueError("stamped backup target database is missing")
        if _file_sha256(database) != expected_database_hash:
            raise ValueError("stamped backup target database hash does not match")
        backed_up = blob_inventory(target / "blobs")
        if (
            backed_up["files"] != blobs_spec.get("files")
            or backed_up["sha256"] != expected_blob_hash
            or backed_up["files"] != current["files"]
            or backed_up["sha256"] != current["sha256"]
        ):
            raise ValueError("stamped backup target does not match the current blob inventory")
    except (OSError, ValueError) as exc:
        return {**stamped, "error": str(exc)}
    return {**stamped, "valid": True, "error": ""}


def recover_interrupted_restore(vault: Path) -> dict[str, Any]:
    """Restore the complete pre-restore component set recorded by an interrupted swap."""
    vault = Path(vault).resolve()
    runtime_error = _runtime_root_error(vault)
    if runtime_error:
        raise ValueError(runtime_error)

    with state.workspace_lock(vault):
        transaction = _read_restore_transaction(vault)
        if transaction is None:
            return {"recovered": False}
        phase = str(transaction["phase"])
        terminal = phase in {"commit-cleanup", "rollback-cleanup"}
        rollback = _restore_transaction_sibling(
            vault,
            transaction.get("rollback"),
            f".{vault.name}.restore-rollback-",
            "rollback",
            required=not terminal,
        )
        stage = _restore_transaction_sibling(
            vault,
            transaction.get("stage"),
            f".{vault.name}.restore-stage-",
            "stage",
            required=not terminal,
        )
        transaction_id = _transaction_id(transaction)
        originally_present = _restore_transaction_presence(transaction)
        for directory, role in ((rollback, "rollback"), (stage, "stage")):
            if os.path.lexists(directory):
                if terminal:
                    _validate_terminal_transaction_directory(
                        vault, directory, role, RESTORE_TRANSACTION_FORMAT, transaction_id
                    )
                else:
                    _validate_transaction_directory_identity(
                        vault, directory, role, RESTORE_TRANSACTION_FORMAT, transaction_id
                    )
        if not terminal:
            _preflight_restore_recovery_components(rollback, stage)
            for live_rel, rollback_rel, _staged_rel in reversed(_restore_components()):
                live = vault / live_rel
                saved = rollback / rollback_rel
                if os.path.lexists(saved):
                    if os.path.lexists(live):
                        _remove_path_durable(live)
                    live.parent.mkdir(parents=True, exist_ok=True)
                    _copy_recovery_component(saved, live)
                elif live_rel.as_posix() in originally_present:
                    if (
                        not os.path.lexists(live)
                        and live_rel not in _sqlite_disposable_components()
                    ):
                        raise ValueError(
                            f"original restore component has no live or rollback copy: {live_rel}"
                        )
                else:
                    _remove_path_durable(live)

        verify_journal = (
            Path(state.DB_REL).as_posix() in originally_present or phase == "commit-cleanup"
        )
        if verify_journal:
            database = vault / state.DB_REL
            if _path_redirects(database) or not database.is_file():
                raise ValueError("recovered restore database is missing")
            journal = state.verify_journal_chain(vault)
            if not journal["ok"]:
                raise ValueError(
                    f"recovered pre-restore journal verification failed: {journal['error']}"
                )
        else:
            journal = {"ok": True, "head": "", "skipped": "database was absent before restore"}
        if not terminal:
            phase = "rollback-cleanup"
            _set_restore_transaction_phase(vault, transaction, phase)
        _cleanup_transaction_directory(rollback)
        _cleanup_transaction_directory(stage)
        _remove_restore_transaction(vault)

    return {
        "recovered": True,
        "rollback": rollback.name,
        "outcome": "committed" if phase == "commit-cleanup" else "rolled_back",
        "journal": journal,
    }


def recover_interrupted_backup(vault: Path) -> dict[str, Any]:
    """Restore a complete backup target after an interrupted replacement."""
    vault = Path(vault).resolve()
    runtime_error = _runtime_root_error(vault)
    if runtime_error:
        raise ValueError(runtime_error)

    with state.workspace_lock(vault):
        transaction = _read_backup_transaction(vault)
        if transaction is None:
            return {"recovered": False}
        phase = str(transaction["phase"])
        previous_target = bool(transaction["previous_target"])
        target = _backup_transaction_target(vault, transaction.get("target"))
        rollback = _backup_transaction_sibling(
            target, transaction.get("rollback"), f".{target.name}.rollback-", "rollback"
        )
        stage = _backup_transaction_sibling(
            target, transaction.get("stage"), f".{target.name}.stage-", "stage"
        )
        transaction_id = _transaction_id(transaction)
        if phase == "publishing" and not previous_target:
            target_exists = os.path.lexists(target)
            rollback_exists = os.path.lexists(rollback)
            stage_exists = os.path.lexists(stage)
            if not target_exists and not rollback_exists and stage_exists:
                _validate_transaction_directory_identity(
                    vault, stage, "stage", BACKUP_TRANSACTION_FORMAT, transaction_id
                )
                _require_recognized_backup_target(stage)
                outcome = "rolled_back"
            elif target_exists and not rollback_exists and not stage_exists:
                _validate_transaction_directory_identity(
                    vault,
                    target,
                    "stage",
                    BACKUP_TRANSACTION_FORMAT,
                    transaction_id,
                    directory_name=stage.name,
                )
                _require_recognized_backup_target(target)
                outcome = "published"
            else:
                raise ValueError("backup transaction filesystem state is invalid")
            phase = f"{outcome.replace('_', '-')}-cleanup"
            _set_backup_transaction_phase(vault, transaction, phase)
        elif phase == "publishing":
            target_exists = os.path.lexists(target)
            rollback_exists = os.path.lexists(rollback)
            stage_exists = os.path.lexists(stage)
            if target_exists and stage_exists and not rollback_exists:
                _validate_transaction_directory_identity(
                    vault,
                    target,
                    "rollback",
                    BACKUP_TRANSACTION_FORMAT,
                    transaction_id,
                    directory_name=rollback.name,
                )
                _validate_transaction_directory_identity(
                    vault, stage, "stage", BACKUP_TRANSACTION_FORMAT, transaction_id
                )
                _require_recognized_backup_target(target)
                _require_recognized_backup_target(stage)
                outcome = "rolled_back"
            elif not target_exists and rollback_exists and stage_exists:
                _validate_transaction_directory_identity(
                    vault, rollback, "rollback", BACKUP_TRANSACTION_FORMAT, transaction_id
                )
                _validate_transaction_directory_identity(
                    vault, stage, "stage", BACKUP_TRANSACTION_FORMAT, transaction_id
                )
                _require_recognized_backup_target(rollback)
                _require_recognized_backup_target(stage)
                _replace_durable(rollback, target)
                _require_recognized_backup_target(target)
                outcome = "rolled_back"
            elif target_exists and rollback_exists and not stage_exists:
                _validate_transaction_directory_identity(
                    vault,
                    target,
                    "stage",
                    BACKUP_TRANSACTION_FORMAT,
                    transaction_id,
                    directory_name=stage.name,
                )
                _validate_transaction_directory_identity(
                    vault, rollback, "rollback", BACKUP_TRANSACTION_FORMAT, transaction_id
                )
                _require_recognized_backup_target(target)
                _require_recognized_backup_target(rollback)
                outcome = "published"
            else:
                raise ValueError("backup transaction filesystem state is invalid")
            phase = f"{outcome.replace('_', '-')}-cleanup"
            _set_backup_transaction_phase(vault, transaction, phase)
        else:
            outcome = "published" if phase == "published-cleanup" else "rolled_back"
            if outcome == "published" or previous_target:
                _require_recognized_backup_target(target)
                _validate_transaction_directory_identity(
                    vault,
                    target,
                    "stage" if outcome == "published" else "rollback",
                    BACKUP_TRANSACTION_FORMAT,
                    transaction_id,
                    directory_name=stage.name if outcome == "published" else rollback.name,
                )
            elif os.path.lexists(target):
                raise ValueError("backup transaction target must remain absent after rollback")
            for directory, role in ((rollback, "rollback"), (stage, "stage")):
                if os.path.lexists(directory):
                    _validate_terminal_transaction_directory(
                        vault, directory, role, BACKUP_TRANSACTION_FORMAT, transaction_id
                    )
        if outcome == "published":
            manifest = _read_manifest(target)
            if manifest is None:
                raise ValueError("published backup transaction target manifest is invalid")
            _write_local_backup_stamp(vault, target, manifest)
        _cleanup_transaction_directory(rollback)
        _cleanup_transaction_directory(stage)
        _remove_backup_transaction(vault)
        _remove_target_identity_after_marker(target)

    return {"recovered": True, "target": str(target), "outcome": outcome}


def _stage_restore_source(
    source: Path,
    manifest: dict[str, Any],
    stage: Path,
) -> dict[str, Any]:
    created_at = manifest.get("created_at")
    if not isinstance(created_at, str) or not created_at.strip():
        raise ValueError("backup creation timestamp is invalid")
    database_spec = _manifest_section(manifest, "database")
    blobs_spec = _manifest_section(manifest, "blobs")
    anchor_spec = _manifest_section(manifest, "journal_head")
    if database_spec.get("path") != "memoria.sqlite":
        raise ValueError("backup database path is invalid")
    if blobs_spec.get("path") != "blobs":
        raise ValueError("backup blob path is invalid")
    expected_database_hash = _manifest_hash(database_spec, "database")
    expected_blob_hash = _manifest_hash(blobs_spec, "blob inventory")
    expected_blob_files = blobs_spec.get("files")
    if not isinstance(expected_blob_files, int) or expected_blob_files < 0:
        raise ValueError("backup blob file count is invalid")

    source_database = source / "memoria.sqlite"
    if source_database.is_symlink() or not source_database.is_file():
        raise ValueError("backup database is missing or is not a regular file")
    if _file_sha256(source_database) != expected_database_hash:
        raise ValueError("backup database hash does not match its manifest")

    staged_database = stage / state.DB_REL
    staged_database.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_database, staged_database, follow_symlinks=False)
    _fsync_file(staged_database)
    if _file_sha256(staged_database) != expected_database_hash:
        raise ValueError("staged database hash does not match its manifest")
    _sqlite_quick_check(staged_database)

    source_blobs = source / "blobs"
    source_inventory = blob_inventory(source_blobs)
    if (
        source_inventory["files"] != expected_blob_files
        or source_inventory["sha256"] != expected_blob_hash
    ):
        raise ValueError("backup blob inventory does not match its manifest")
    staged_blobs = stage / BLOBS_REL
    _copy_blob_tree(source_blobs, staged_blobs, source_inventory["entries"])
    if blob_inventory(staged_blobs) != source_inventory:
        raise ValueError("staged blob inventory does not match its source")
    if blob_inventory(source_blobs) != source_inventory:
        raise ValueError("backup blob inventory changed while it was being copied")

    anchor_path = anchor_spec.get("path")
    anchor_value = anchor_spec.get("value")
    if anchor_path is None and anchor_value is None:
        pass
    elif anchor_path == "journal-head" and isinstance(anchor_value, str) and anchor_value:
        source_anchor = source / "journal-head"
        if source_anchor.is_symlink() or not source_anchor.is_file():
            raise ValueError("backup journal-head is missing or invalid")
        if source_anchor.read_text(encoding="utf-8").strip() != anchor_value:
            raise ValueError("backup journal-head does not match its manifest")
        write_bytes_durable(stage / state.JOURNAL_HEAD_REL, source_anchor.read_bytes())
    else:
        raise ValueError("backup journal-head manifest entry is invalid")

    clean_database = staged_database.with_name("memoria.restore.sqlite")
    _snapshot_database(staged_database, clean_database)
    os.replace(clean_database, staged_database)
    _remove_sqlite_sidecars(staged_database)
    _rebuild_journal_exports(stage)
    verification = state.verify_journal_chain(stage)
    if not verification["ok"]:
        raise ValueError(f"backup journal verification failed: {verification['error']}")
    _consolidate_database(staged_database)
    with closing(sqlite3.connect(staged_database)) as conn:
        row_hashes = {
            str(row[0]) for row in conn.execute("SELECT row_hash FROM event_log ORDER BY event_id")
        }
    return {"row_hashes": row_hashes, "journal": verification}


def _manifest_section(manifest: dict[str, Any], name: str) -> dict[str, Any]:
    section = manifest.get(name)
    if not isinstance(section, dict):
        raise ValueError(f"backup manifest {name} section is invalid")
    return section


def _manifest_hash(section: dict[str, Any], label: str) -> str:
    value = section.get("sha256")
    if not isinstance(value, str) or not value.startswith("sha256:") or len(value) != 71:
        raise ValueError(f"backup {label} hash is invalid")
    return value


def _sqlite_quick_check(path: Path) -> None:
    uri = path.resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as conn:
        rows = [str(row[0]) for row in conn.execute("PRAGMA quick_check")]
    if rows != ["ok"]:
        raise ValueError(f"backup database quick_check failed: {', '.join(rows)}")


def _rebuild_journal_exports(vault: Path) -> None:
    journal_root = vault / ".memoria/journal"
    journal_root.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[str]] = {}
    with closing(sqlite3.connect(vault / state.DB_REL)) as conn:
        rows = conn.execute(
            "SELECT machine, payload_json FROM event_log ORDER BY event_id"
        ).fetchall()
    for machine_value, payload_json in rows:
        machine = str(machine_value)
        event = json.loads(str(payload_json))
        if not isinstance(event, dict) or event.get("machine") != machine:
            raise ValueError("backup event_log machine does not match its payload")
        if not machine.strip() or safe_filename(machine) != machine:
            raise ValueError("backup event_log machine is not a canonical filename")
        grouped.setdefault(machine, []).append(json.dumps(event, ensure_ascii=False) + "\n")
    for machine, lines in grouped.items():
        write_text_durable(journal_root / f"{machine}.jsonl", "".join(lines))


def _committed_journal_anchor(vault: Path) -> str | None:
    git_dir = vault / ".git"
    if _path_redirects(git_dir) or not git_dir.is_dir():
        raise ValueError("workspace Git metadata must be a directory")
    if os.path.lexists(git_dir / "commondir"):
        raise ValueError("workspace Git common-directory indirection is not supported")
    env = {name: value for name, value in os.environ.items() if not name.startswith("GIT_")}
    git = [
        "git",
        f"--git-dir={git_dir}",
        f"--work-tree={vault}",
        "-c",
        f"core.hooksPath={os.devnull}",
        "-c",
        "core.fsmonitor=false",
    ]
    try:
        listed = subprocess.run(
            [*git, "ls-tree", "--name-only", "HEAD", "--", state.JOURNAL_HEAD_REL],
            cwd=vault,
            env=env,
            check=False,
            text=True,
            capture_output=True,
        )
    except OSError as exc:
        raise OSError(f"cannot execute Git: {exc}") from exc
    if listed.returncode:
        raise ValueError(listed.stderr.strip() or "Git could not inspect the committed anchor")
    if not listed.stdout.strip():
        return None
    try:
        shown = subprocess.run(
            [*git, "show", f"HEAD:{state.JOURNAL_HEAD_REL}"],
            cwd=vault,
            env=env,
            check=False,
            text=True,
            capture_output=True,
        )
    except OSError as exc:
        raise OSError(f"cannot execute Git: {exc}") from exc
    if shown.returncode:
        raise ValueError(shown.stderr.strip() or "Git could not read the committed anchor")
    anchor = shown.stdout.strip()
    if not anchor:
        raise ValueError("the committed journal-head is empty")
    return anchor


def _install_restore_stage(
    vault: Path,
    stage: Path,
    source: Path,
    manifest: dict[str, Any],
    actor: str,
    machine: str,
) -> dict[str, Any]:
    rollback = Path(tempfile.mkdtemp(prefix=f".{vault.name}.restore-rollback-", dir=vault.parent))
    _fsync_directory(vault.parent)
    try:
        _write_restore_transaction(vault, rollback, stage)
    except BaseException:
        if not _restore_transaction_binds_rollback(vault, rollback):
            _cleanup_directory(rollback)
        raise
    try:
        for live_rel, rollback_rel, _staged_rel in _restore_components():
            live = vault / live_rel
            if not os.path.lexists(live):
                continue
            saved = rollback / rollback_rel
            saved.parent.mkdir(parents=True, exist_ok=True)
            _replace_durable(live, saved)

        install_components = [
            (stage / state.DB_REL, vault / state.DB_REL),
            (stage / BLOBS_REL, vault / BLOBS_REL),
        ]
        staged_anchor = stage / state.JOURNAL_HEAD_REL
        if staged_anchor.is_file():
            install_components.append((staged_anchor, vault / state.JOURNAL_HEAD_REL))
        install_components.append((stage / ".memoria/journal", vault / ".memoria/journal"))
        for staged, live in install_components:
            live.parent.mkdir(parents=True, exist_ok=True)
            _replace_durable(staged, live)

        verification = state.verify_journal_chain(vault)
        if not verification["ok"]:
            raise ValueError(f"restored journal verification failed: {verification['error']}")
        from memoria_vault.runtime.trusted_writer import append_explicit_journal_event

        append_explicit_journal_event(
            vault,
            {
                "event": "workspace-restored",
                "restored_from": str(source),
                "backup_created_at": manifest["created_at"],
                "backup_blob_sha256": manifest["blobs"]["sha256"],
            },
            actor=actor,
            machine=machine,
        )
        final_verification = state.verify_journal_chain(vault)
        if not final_verification["ok"]:
            raise ValueError(
                f"restored journal failed after provenance append: {final_verification['error']}"
            )
        _write_local_backup_stamp(vault, source, manifest)
    except BaseException as restore_error:
        try:
            recover_interrupted_restore(vault)
        except BaseException as rollback_error:
            raise rollback_error from restore_error
        raise
    transaction = _read_restore_transaction(vault)
    if transaction is None:
        raise ValueError("restore transaction marker is missing after a successful swap")
    _set_restore_transaction_phase(vault, transaction, "commit-cleanup")
    _cleanup_transaction_directory(rollback)
    _cleanup_transaction_directory(stage)
    _remove_restore_transaction(vault)
    return final_verification


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path)


def _remove_sqlite_sidecars(database: Path) -> None:
    for suffix in ("-wal", "-shm"):
        _remove_path_durable(Path(f"{database}{suffix}"))


def _consolidate_database(database: Path) -> None:
    consolidated = database.with_name(f".{database.name}.consolidated")
    _snapshot_database(database, consolidated)
    _remove_sqlite_sidecars(database)
    os.replace(consolidated, database)
    _remove_sqlite_sidecars(consolidated)


def _require_pi_maintenance(actor: str, machine: str) -> None:
    if actor != "pi":
        raise ValueError("workspace maintenance requires PI actor authority")
    if not isinstance(machine, str) or not machine.strip():
        raise ValueError("workspace maintenance machine must be nonblank")


def _paths_overlap(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def _failure(error: str) -> dict[str, Any]:
    return {"ok": False, "error": error}


def _runtime_root_error(vault: Path) -> str:
    runtime_paths = (
        Path(".memoria"),
        Path(".memoria/locks"),
        Path(".memoria/locks/worker.lock"),
        Path(".memoria/config"),
        *(live_rel for live_rel, _rollback_rel, _staged_rel in _restore_components()),
    )
    for rel in runtime_paths:
        path = vault / rel
        if _path_redirects(path):
            return f"workspace runtime path must not be a symlink: {rel}"
    return ""


def _path_redirects(path: Path) -> bool:
    return path.is_symlink() or path.is_junction()


def validate_runtime_root(vault: Path) -> None:
    """Reject runtime paths that redirect maintenance outside the workspace."""
    error = _runtime_root_error(Path(vault))
    if error:
        raise ValueError(error)


def validate_maintenance_preconditions(vault: Path) -> None:
    """Refuse maintenance while runtime paths redirect or recovery is pending."""
    vault = Path(vault)
    validate_runtime_root(vault)
    if _read_restore_transaction(vault) is not None:
        raise ValueError("interrupted restore requires memoria workspace recover")
    if _read_backup_transaction(vault) is not None:
        raise ValueError("interrupted backup requires memoria workspace recover")


def validate_workspace_write_targets(vault: Path, relpaths: Iterable[str | Path]) -> None:
    """Reject a write target whose existing path redirects outside the workspace."""
    vault = Path(vault)
    for value in relpaths:
        rel = Path(value)
        if rel.is_absolute() or not rel.parts or ".." in rel.parts:
            raise ValueError(f"workspace write target must be relative: {value}")
        current = vault
        for index, part in enumerate(rel.parts):
            current /= part
            if _path_redirects(current):
                raise ValueError(
                    "workspace write target must not redirect through a symlink or junction: "
                    f"{rel.as_posix()}"
                )
            if index < len(rel.parts) - 1 and os.path.lexists(current) and not current.is_dir():
                raise ValueError(
                    f"workspace write target parent must be a directory: {rel.as_posix()}"
                )


def _write_backup_transaction(vault: Path, target: Path, rollback: Path, stage: Path) -> None:
    if rollback.parent != target.parent or stage.parent != target.parent:
        raise ValueError("backup transaction directories must be target siblings")
    previous_target = os.path.lexists(target) or os.path.lexists(rollback)
    candidates = [
        (directory, role, directory_name)
        for directory, role, directory_name in (
            (target, "rollback", rollback.name),
            (rollback, "rollback", rollback.name),
            (stage, "stage", stage.name),
        )
        if os.path.lexists(directory)
    ]
    for directory, role, _directory_name in candidates:
        if _path_redirects(directory) or not directory.is_dir():
            raise ValueError(f"backup transaction {role} directory is invalid")
    if not os.path.lexists(stage):
        raise ValueError("backup transaction stage directory is missing")
    transaction_id = secrets.token_hex(16)
    marker = vault / BACKUP_TRANSACTION_REL
    try:
        for directory, role, directory_name in candidates:
            _write_transaction_directory_identity(
                vault,
                directory,
                role,
                BACKUP_TRANSACTION_FORMAT,
                transaction_id,
                directory_name=directory_name,
            )
        value = {
            "format": BACKUP_TRANSACTION_FORMAT,
            "version": BACKUP_TRANSACTION_VERSION,
            "vault": str(vault),
            "target": str(target),
            "rollback": rollback.name,
            "stage": stage.name,
            "transaction_id": transaction_id,
            "phase": "publishing",
            "previous_target": previous_target,
        }
        write_text_durable(
            marker,
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
        _fsync_directory(marker.parent)
    except BaseException:
        if not os.path.lexists(marker):
            for directory, _role, _directory_name in reversed(candidates):
                _remove_transaction_directory_identity(directory)
        raise


def _read_backup_transaction(vault: Path) -> dict[str, Any] | None:
    path = vault / BACKUP_TRANSACTION_REL
    if not os.path.lexists(path):
        return None
    if path.is_symlink() or not path.is_file():
        raise ValueError("backup transaction marker must be a regular file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"backup transaction marker is invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("backup transaction marker must be an object")
    if value.get("format") == BACKUP_TRANSACTION_FORMAT and value.get("version") == 1:
        raise ValueError("legacy backup transaction marker identity is invalid")
    if (
        value.get("format") != BACKUP_TRANSACTION_FORMAT
        or value.get("version") != BACKUP_TRANSACTION_VERSION
        or value.get("vault") != str(vault)
        or value.get("phase") not in BACKUP_TRANSACTION_PHASES
        or not isinstance(value.get("previous_target"), bool)
    ):
        raise ValueError("backup transaction marker identity is invalid")
    return value


def _set_backup_transaction_phase(
    vault: Path, transaction: dict[str, Any], phase: str
) -> dict[str, Any]:
    if phase not in BACKUP_TRANSACTION_PHASES:
        raise ValueError("backup transaction phase is invalid")
    updated = {**transaction, "phase": phase}
    _write_transaction_marker(vault / BACKUP_TRANSACTION_REL, updated)
    return updated


def _backup_transaction_binds_stage(vault: Path, stage: Path) -> bool:
    try:
        transaction = _read_backup_transaction(vault)
    except ValueError:
        return True
    return transaction is not None and transaction.get("stage") == stage.name


def _backup_transaction_target(vault: Path, value: object) -> Path:
    if not isinstance(value, str):
        raise ValueError("backup transaction target is invalid")
    target = Path(value)
    if not target.is_absolute() or not target.name or _paths_overlap(vault, target):
        raise ValueError("backup transaction target is invalid")
    if target.parent.resolve(strict=False) != target.parent:
        raise ValueError("backup transaction target parent is invalid")
    return target


def _backup_transaction_sibling(target: Path, value: object, prefix: str, label: str) -> Path:
    if not isinstance(value, str) or Path(value).name != value or not value.startswith(prefix):
        raise ValueError(f"backup transaction {label} directory is invalid")
    path = target.parent / value
    if _path_redirects(path):
        raise ValueError(f"backup transaction {label} directory is invalid")
    return path


def _remove_backup_transaction(vault: Path) -> None:
    path = vault / BACKUP_TRANSACTION_REL
    if not os.path.lexists(path):
        return
    if path.is_symlink() or not path.is_file():
        raise ValueError("backup transaction marker is not removable")
    path.unlink()
    _fsync_directory(path.parent)


def _require_recognized_backup_target(target: Path) -> None:
    if _path_redirects(target) or not target.is_dir():
        raise ValueError("backup transaction target is missing or invalid")
    manifest = _read_manifest(target)
    if manifest is None or not _is_restorable_backup(target, manifest):
        raise ValueError("backup transaction target is not a recognized Memoria backup")


def _restore_components() -> tuple[tuple[Path, Path, Path | None], ...]:
    return (
        (Path(state.DB_REL), Path("memoria.sqlite"), Path(state.DB_REL)),
        (Path(f"{state.DB_REL}-wal"), Path("memoria.sqlite-wal"), None),
        (Path(f"{state.DB_REL}-shm"), Path("memoria.sqlite-shm"), None),
        (Path(f"{state.DB_REL}-journal"), Path("memoria.sqlite-journal"), None),
        (Path(BLOBS_REL), Path("blobs"), Path(BLOBS_REL)),
        (Path(state.JOURNAL_HEAD_REL), Path("journal-head"), Path(state.JOURNAL_HEAD_REL)),
        (Path(".memoria/journal"), Path("journal"), Path(".memoria/journal")),
        (Path(LAST_BACKUP_REL), Path("last-backup"), None),
    )


def _sqlite_disposable_components() -> frozenset[Path]:
    return frozenset({Path(f"{state.DB_REL}-shm")})


def _preflight_restore_recovery_components(rollback: Path, stage: Path) -> None:
    for _live_rel, rollback_rel, staged_rel in _restore_components():
        saved = rollback / rollback_rel
        staged = stage / staged_rel if staged_rel is not None else None
        if _path_redirects(saved):
            raise ValueError(f"restore rollback component must not be a symlink: {rollback_rel}")
        if staged is not None and _path_redirects(staged):
            raise ValueError(f"restore stage component must not be a symlink: {staged_rel}")


def _write_restore_transaction(vault: Path, rollback: Path, stage: Path) -> None:
    runtime_error = _runtime_root_error(vault)
    if runtime_error:
        raise ValueError(runtime_error)
    for role, directory in (("rollback", rollback), ("stage", stage)):
        if _path_redirects(directory):
            raise ValueError(f"restore transaction {role} directory must not be a symlink")
        if directory.parent != vault.parent:
            raise ValueError(f"restore transaction {role} directory must be a vault sibling")
        if not directory.is_dir():
            raise ValueError(f"restore transaction {role} directory is missing")
    present = [
        live_rel.as_posix()
        for live_rel, _rollback_rel, _staged_rel in _restore_components()
        if os.path.lexists(vault / live_rel)
    ]
    for live_rel, rollback_rel in (
        (Path(f"{state.DB_REL}-wal"), Path("memoria.sqlite-wal")),
        (Path(f"{state.DB_REL}-journal"), Path("memoria.sqlite-journal")),
    ):
        if live_rel.as_posix() not in present:
            continue
        live = vault / live_rel
        if _path_redirects(live) or not live.is_file():
            raise ValueError(f"restore component must be a regular file: {live_rel}")
        _copy_recovery_component(live, rollback / rollback_rel)

    transaction_id = secrets.token_hex(16)
    _write_transaction_directory_identity(
        vault, rollback, "rollback", RESTORE_TRANSACTION_FORMAT, transaction_id
    )
    _write_transaction_directory_identity(
        vault, stage, "stage", RESTORE_TRANSACTION_FORMAT, transaction_id
    )
    value = {
        "format": RESTORE_TRANSACTION_FORMAT,
        "version": RESTORE_TRANSACTION_VERSION,
        "vault": str(vault),
        "rollback": rollback.name,
        "stage": stage.name,
        "transaction_id": transaction_id,
        "phase": "swapping",
        "present": present,
    }
    marker = vault / RESTORE_TRANSACTION_REL
    write_text_durable(
        marker,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _fsync_directory(marker.parent)


def _read_restore_transaction(vault: Path) -> dict[str, Any] | None:
    path = vault / RESTORE_TRANSACTION_REL
    if not os.path.lexists(path):
        return None
    if path.is_symlink() or not path.is_file():
        raise ValueError("restore transaction marker must be a regular file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"restore transaction marker is invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("restore transaction marker must be an object")
    if value.get("format") == RESTORE_TRANSACTION_FORMAT and value.get("version") == 1:
        raise ValueError("legacy restore transaction marker identity is invalid")
    if (
        value.get("format") != RESTORE_TRANSACTION_FORMAT
        or value.get("version") != RESTORE_TRANSACTION_VERSION
        or value.get("vault") != str(vault)
        or value.get("phase") not in RESTORE_TRANSACTION_PHASES
    ):
        raise ValueError("restore transaction marker identity is invalid")
    return value


def _set_restore_transaction_phase(
    vault: Path, transaction: dict[str, Any], phase: str
) -> dict[str, Any]:
    if phase not in RESTORE_TRANSACTION_PHASES:
        raise ValueError("restore transaction phase is invalid")
    updated = {**transaction, "phase": phase}
    _write_transaction_marker(vault / RESTORE_TRANSACTION_REL, updated)
    return updated


def _restore_transaction_sibling(
    vault: Path,
    value: object,
    prefix: str,
    label: str,
    *,
    required: bool = True,
) -> Path:
    if not isinstance(value, str) or Path(value).name != value or not value.startswith(prefix):
        raise ValueError(f"restore transaction {label} directory is invalid")
    path = vault.parent / value
    if _path_redirects(path) or (os.path.lexists(path) and not path.is_dir()):
        raise ValueError(f"restore transaction {label} directory is missing or invalid")
    if required and not path.is_dir():
        raise ValueError(f"restore transaction {label} directory is missing or invalid")
    return path


def _restore_transaction_presence(transaction: dict[str, Any]) -> set[str]:
    value = transaction.get("present")
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("restore transaction original component list is invalid")
    present = set(value)
    allowed = {live_rel.as_posix() for live_rel, _rollback, _staged in _restore_components()}
    if len(present) != len(value) or not present <= allowed:
        raise ValueError("restore transaction original component list is invalid")
    return present


def _restore_transaction_binds_stage(vault: Path, stage: Path) -> bool:
    try:
        transaction = _read_restore_transaction(vault)
    except ValueError:
        return True
    return transaction is not None and transaction.get("stage") == stage.name


def _restore_transaction_binds_rollback(vault: Path, rollback: Path) -> bool:
    try:
        transaction = _read_restore_transaction(vault)
    except ValueError:
        return True
    return transaction is not None and transaction.get("rollback") == rollback.name


def _transaction_id(transaction: dict[str, Any]) -> str:
    value = transaction.get("transaction_id")
    if (
        not isinstance(value, str)
        or len(value) != 32
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError("transaction identity is invalid")
    return value


def _write_transaction_marker(path: Path, value: dict[str, Any]) -> None:
    write_text_durable(
        path,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _fsync_directory(path.parent)


def _write_transaction_directory_identity(
    vault: Path,
    directory: Path,
    role: str,
    transaction_format: str,
    transaction_id: str,
    *,
    directory_name: str | None = None,
) -> None:
    value = {
        "format": TRANSACTION_DIRECTORY_FORMAT,
        "version": TRANSACTION_DIRECTORY_VERSION,
        "transaction_format": transaction_format,
        "transaction_id": transaction_id,
        "vault": str(vault),
        "role": role,
        "directory": directory_name or directory.name,
    }
    write_text_durable(
        directory / TRANSACTION_DIRECTORY_IDENTITY,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _fsync_directory(directory)


def _validate_transaction_directory_identity(
    vault: Path,
    directory: Path,
    role: str,
    transaction_format: str,
    transaction_id: str,
    *,
    directory_name: str | None = None,
) -> None:
    path = directory / TRANSACTION_DIRECTORY_IDENTITY
    if _path_redirects(path) or not path.is_file():
        raise ValueError(f"transaction {role} directory identity is missing or invalid")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"transaction {role} directory identity is invalid: {exc}") from exc
    expected = {
        "format": TRANSACTION_DIRECTORY_FORMAT,
        "version": TRANSACTION_DIRECTORY_VERSION,
        "transaction_format": transaction_format,
        "transaction_id": transaction_id,
        "vault": str(vault),
        "role": role,
        "directory": directory_name or directory.name,
    }
    if value != expected:
        raise ValueError(f"transaction {role} directory identity does not match")


def _validate_terminal_transaction_directory(
    vault: Path,
    directory: Path,
    role: str,
    transaction_format: str,
    transaction_id: str,
) -> None:
    identity = directory / TRANSACTION_DIRECTORY_IDENTITY
    if os.path.lexists(identity):
        _validate_transaction_directory_identity(
            vault, directory, role, transaction_format, transaction_id
        )
        return
    if _path_redirects(directory) or not directory.is_dir() or any(directory.iterdir()):
        raise ValueError(f"transaction {role} cleanup directory is not empty")


def _remove_transaction_directory_identity(directory: Path) -> None:
    path = directory / TRANSACTION_DIRECTORY_IDENTITY
    if not os.path.lexists(path):
        return
    if _path_redirects(path) or not path.is_file():
        raise ValueError("transaction directory identity is not removable")
    path.unlink()
    _fsync_directory(directory)


def _remove_target_identity_after_marker(directory: Path) -> None:
    """Best-effort cleanup after recovery no longer needs the target binding."""
    try:
        _remove_transaction_directory_identity(directory)
    except (OSError, ValueError):
        pass


def _remove_restore_transaction(vault: Path) -> None:
    path = vault / RESTORE_TRANSACTION_REL
    if os.path.lexists(path):
        path.unlink()
        _fsync_directory(path.parent)


def _replace_durable(source: Path, destination: Path) -> None:
    os.replace(source, destination)
    _fsync_directory(destination.parent)
    if destination.parent != source.parent:
        _fsync_directory(source.parent)


def _remove_path_durable(path: Path) -> None:
    if not os.path.lexists(path):
        return
    _remove_path(path)
    _fsync_directory(path.parent)


def _copy_recovery_component(source: Path, destination: Path) -> None:
    if source.is_file():
        shutil.copy2(source, destination, follow_symlinks=False)
        _fsync_file(destination)
    elif source.is_dir():
        shutil.copytree(source, destination, symlinks=True)
        for path in sorted(destination.rglob("*"), reverse=True):
            if path.is_symlink():
                continue
            if path.is_file():
                _fsync_file(path)
            elif path.is_dir():
                _fsync_directory(path)
        _fsync_directory(destination)
    else:
        raise ValueError(f"restore rollback component is not a regular file or directory: {source}")
    _fsync_directory(destination.parent)


def _fsync_tree(root: Path) -> None:
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"durable tree root is missing or invalid: {root}")
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_symlink():
            raise ValueError(f"durable tree contains a symlink: {path}")
        if path.is_file():
            _fsync_file(path)
        elif path.is_dir():
            _fsync_directory(path)
    _fsync_directory(root)


def _cleanup_directory(path: Path) -> None:
    if _path_redirects(path):
        raise ValueError(f"recovery directory must not be a symlink: {path.name}")
    if path.is_dir():
        parent = path.parent
        shutil.rmtree(path)
        _fsync_directory(parent)


def _cleanup_transaction_directory(path: Path) -> None:
    if not os.path.lexists(path):
        return
    if _path_redirects(path) or not path.is_dir():
        raise ValueError(f"recovery directory must be a directory: {path.name}")
    identity = path / TRANSACTION_DIRECTORY_IDENTITY
    for child in list(path.iterdir()):
        if child == identity:
            continue
        _remove_path_durable(child)
    _remove_transaction_directory_identity(path)
    _cleanup_directory(path)


def _fsync_directory(path: Path) -> None:
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        if os.name == "nt":
            return
        raise
    try:
        os.fsync(fd)
    except OSError:
        if os.name != "nt":
            raise
    finally:
        os.close(fd)


def _replaceable_target_error(target: Path) -> str:
    if not os.path.lexists(target):
        return ""
    if target.is_symlink() or not target.is_dir():
        return "existing backup target is not a recognized Memoria backup directory"
    manifest = _read_manifest(target)
    if manifest is None or not _is_restorable_backup(target, manifest):
        return "existing target is not a recognized Memoria backup"
    return ""


def _is_restorable_backup(target: Path, manifest: dict[str, Any]) -> bool:
    stage = Path(tempfile.mkdtemp(prefix=f".{target.name}.validate-", dir=target.parent))
    try:
        _stage_restore_source(target, manifest, stage)
    except (OSError, UnicodeError, ValueError, sqlite3.DatabaseError):
        return False
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    return True


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
    source_uri = source.resolve().as_uri() + "?mode=ro"
    with (
        closing(sqlite3.connect(source_uri, uri=True)) as src,
        closing(sqlite3.connect(target)) as dst,
    ):
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


def _publish_backup_directory(stage: Path, target: Path, vault: Path) -> None:
    target_error = _replaceable_target_error(target)
    if target_error:
        raise ValueError(target_error)
    rollback = Path(tempfile.mkdtemp(prefix=f".{target.name}.rollback-", dir=target.parent))
    rollback.rmdir()
    _fsync_directory(target.parent)
    _write_backup_transaction(vault, target, rollback, stage)
    try:
        if os.path.lexists(target):
            _replace_durable(target, rollback)
        _replace_durable(stage, target)
        _complete_backup_publication(vault, target, rollback, stage)
    except BaseException as publish_error:
        try:
            recovery = recover_interrupted_backup(vault)
        except BaseException as recovery_error:
            raise recovery_error from publish_error
        if recovery["outcome"] == "published":
            return
        raise


def _complete_backup_publication(vault: Path, target: Path, rollback: Path, stage: Path) -> None:
    transaction = _read_backup_transaction(vault)
    if transaction is None or transaction.get("phase") != "publishing":
        raise ValueError("backup publication transaction is missing or invalid")
    transaction_id = _transaction_id(transaction)
    _validate_transaction_directory_identity(
        vault,
        target,
        "stage",
        BACKUP_TRANSACTION_FORMAT,
        transaction_id,
        directory_name=stage.name,
    )
    if bool(transaction["previous_target"]):
        _validate_transaction_directory_identity(
            vault, rollback, "rollback", BACKUP_TRANSACTION_FORMAT, transaction_id
        )
    elif os.path.lexists(rollback):
        raise ValueError("backup publication rollback directory must remain absent")
    _set_backup_transaction_phase(vault, transaction, "published-cleanup")
    manifest = _read_manifest(target)
    if manifest is None:
        raise ValueError("published backup transaction target manifest is invalid")
    _write_local_backup_stamp(vault, target, manifest)
    _cleanup_transaction_directory(rollback)
    _cleanup_transaction_directory(stage)
    _remove_backup_transaction(vault)
    _remove_target_identity_after_marker(target)
