"""Policy audit and hash helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path

from memoria_vault.runtime.jsonl import append_jsonl

EMPTY_SHA256 = "sha256:" + hashlib.sha256(b"").hexdigest()

AUDIT_RELPATH = "system/logs/audit.jsonl"
AUDIT_SCHEMA_VERSION = 2
REVIEW_MODE = "blocking"


def sha256_bytes(data: bytes) -> str:
    """Return ``sha256:<64-hex>`` for ``data``."""
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    """Return ``sha256:<64-hex>`` for ``path``; missing files hash as empty."""
    if not path.exists():
        return EMPTY_SHA256
    return sha256_bytes(path.read_bytes())


def append_audit(vault: Path, entry: dict) -> None:
    """Append one stamped JSON object to ``system/logs/audit.jsonl``."""
    stamped = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "review_mode": REVIEW_MODE,
        **entry,
    }
    append_jsonl(vault / AUDIT_RELPATH, [stamped])
