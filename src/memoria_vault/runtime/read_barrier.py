"""Checked-file consumption guard."""

from __future__ import annotations

import hashlib
from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.policy.audit import EMPTY_SHA256, sha256_file
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.worker import enqueue_operation


def is_consumable_checked_file(vault: Path, relpath: str) -> bool:
    vault = Path(vault)
    rel = normalize_path(relpath)
    if state.concept_check_status(vault, rel) != "checked":
        return False
    record = state.output_record(vault, rel)
    if not record or record["store"] != "file" or record["check_status"] != "checked":
        _enqueue_scan(vault, rel, "missing checked output record", EMPTY_SHA256)
        return False
    target = normalize_path(str(record["target_path"] or rel))
    path = vault / target
    expected = str(record["output_sha256"] or "")
    current = sha256_file(path) if path.is_file() else EMPTY_SHA256
    if record["materialization_status"] != "materialized" or current != expected:
        _enqueue_scan(vault, rel, "checked file changed before consumption", current)
        return False
    return True


def _enqueue_scan(vault: Path, relpath: str, reason: str, current_hash: str) -> None:
    digest = hashlib.sha256(f"{relpath}:{reason}:{current_hash}".encode()).hexdigest()[:16]
    enqueue_operation(
        vault,
        "observe-pi-edits",
        payload={"reason": reason, "target_path": relpath},
        idempotency_key=f"read-guard-scan-{digest}",
        schedule_id="read-guard",
        actor="integrity",
    )
