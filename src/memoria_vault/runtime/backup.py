"""Backup and restore the workspace stores that Git cannot rebuild."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
from contextlib import closing
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
    raw_source = Path(source).expanduser()
    if raw_source.is_symlink():
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
    try:
        try:
            validated = _stage_restore_source(source, manifest, stage)
        except (OSError, UnicodeError, ValueError, sqlite3.DatabaseError) as exc:
            return _failure(f"backup validation failed: {exc}")

        with state.workspace_lock(vault):
            if (vault / state.DB_REL).exists() and not force:
                return _failure("live database is present; pass --force to replace it")
            committed_anchor = _committed_journal_anchor(vault)
            if committed_anchor not in {None, "", "GENESIS"}:
                if committed_anchor not in validated["row_hashes"]:
                    return _failure(
                        "backup predates the committed journal-head; restore the matching "
                        "Git revision before restoring this backup"
                    )
            journal = _install_restore_stage(vault, stage, source, manifest, actor, machine)
            stage = None
    finally:
        if stage is not None:
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
        grouped.setdefault(machine, []).append(json.dumps(event, ensure_ascii=False) + "\n")
    for machine, lines in grouped.items():
        write_text_durable(journal_root / f"{machine}.jsonl", "".join(lines))


def _committed_journal_anchor(vault: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "show", f"HEAD:{state.JOURNAL_HEAD_REL}"],
            cwd=vault,
            check=False,
            text=True,
            capture_output=True,
        )
    except OSError:
        return None
    return None if proc.returncode else proc.stdout.strip()


def _install_restore_stage(
    vault: Path,
    stage: Path,
    source: Path,
    manifest: dict[str, Any],
    actor: str,
    machine: str,
) -> dict[str, Any]:
    rollback = Path(tempfile.mkdtemp(prefix=f".{vault.name}.restore-rollback-", dir=vault.parent))
    components = (
        (Path(state.DB_REL), Path("memoria.sqlite")),
        (Path(f"{state.DB_REL}-wal"), Path("memoria.sqlite-wal")),
        (Path(f"{state.DB_REL}-shm"), Path("memoria.sqlite-shm")),
        (Path(BLOBS_REL), Path("blobs")),
        (Path(state.JOURNAL_HEAD_REL), Path("journal-head")),
        (Path(".memoria/journal"), Path("journal")),
    )
    installed: list[Path] = []
    moved: list[tuple[Path, Path]] = []
    try:
        for live_rel, rollback_rel in components:
            live = vault / live_rel
            if not os.path.lexists(live):
                continue
            saved = rollback / rollback_rel
            saved.parent.mkdir(parents=True, exist_ok=True)
            os.replace(live, saved)
            moved.append((live, saved))

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
            os.replace(staged, live)
            installed.append(live)

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
        stamp = {
            "format": BACKUP_FORMAT,
            "version": BACKUP_VERSION,
            "created_at": manifest["created_at"],
            "target": str(source),
            "blob_files": manifest["blobs"]["files"],
            "blob_sha256": manifest["blobs"]["sha256"],
        }
        write_text_durable(
            vault / LAST_BACKUP_REL,
            json.dumps(stamp, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            create_parent=True,
        )
    except BaseException:
        for path in reversed(installed):
            _remove_path(path)
        _remove_sqlite_sidecars(vault / state.DB_REL)
        for live, saved in reversed(moved):
            live.parent.mkdir(parents=True, exist_ok=True)
            if os.path.lexists(live):
                _remove_path(live)
            os.replace(saved, live)
        raise
    else:
        shutil.rmtree(rollback)
        shutil.rmtree(stage, ignore_errors=True)
    finally:
        if rollback.exists():
            shutil.rmtree(rollback, ignore_errors=True)
    return final_verification


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path)


def _remove_sqlite_sidecars(database: Path) -> None:
    for suffix in ("-wal", "-shm"):
        Path(f"{database}{suffix}").unlink(missing_ok=True)


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
