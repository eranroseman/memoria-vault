#!/usr/bin/env python3
"""Audit-log detector family for the Memoria Linter."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Finding:
    detector: str
    severity: str
    path: str
    message: str
    timestamp: str = ""


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ""

def audit_unpaired_writes(vault: Path, max_age_h: float = 1.0) -> list[Finding]:
    """A mutating allow in the audit chain whose write never completed.

    Every mutating allow / allow_with_log record carries a before_hash and is
    paired by a `write_complete` record (same path + task_id) once the worker's
    write lands (policy_hook post_tool_call -> complete_write). An unpaired
    record older than `max_age_h` means the reversibility chain has a hole --
    the write either failed silently or completed without its after_hash, so
    the prior state can no longer be pinned. Report-only, like every detector."""
    from datetime import datetime, timezone

    log = vault / "system" / "logs" / "audit.jsonl"
    if not log.is_file():
        return []
    mutating = {"write", "append", "move", "delete", "mkdir", "auto_fix"}
    pending: dict[tuple[str, str], dict] = {}      # (path, task_id) -> pre-record
    for line in read(log).splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        key = (e.get("path", ""), e.get("task_id", ""))
        if e.get("decision") == "write_complete":
            pending.pop(key, None)
        elif (e.get("decision") in ("allow", "allow_with_log")
                and e.get("action") in mutating and e.get("before_hash")):
            pending[key] = e
    now = datetime.now(timezone.utc)
    out = []
    for (path, task_id), e in sorted(pending.items()):
        try:
            ts = datetime.fromisoformat(str(e.get("timestamp", "")).replace("Z", "+00:00"))
        except ValueError:
            continue
        age_h = (now - ts).total_seconds() / 3600
        if age_h > max_age_h:
            out.append(Finding("audit-unpaired-writes", "MEDIUM", path,
                               f"mutating allow ({e.get('action')}, task {task_id}) has no "
                               f"paired write_complete after {age_h:.1f}h -- the audit "
                               f"chain cannot pin this write's after-state"))
    return out


def vault_hash_drift(vault: Path) -> list[Finding]:
    """A file's on-disk state no longer matches its last audited write.

    Walks `system/logs/audit.jsonl` (append-only forever, ADR-25 -- so one walk
    covers the full history; there are no rotated files to stitch) and keeps the
    *latest* `write_complete` record per path (last write wins). Each recorded
    `after_hash` is then compared to the current on-disk SHA-256, using the same
    ``sha256:<64-hex>`` convention as policy_mcp.sha256_file: a missing file
    hashes as the empty byte string. That convention makes deletes fall out
    naturally -- a completed delete records the empty hash as its after_hash,
    and an absent file hashes to the same value, so a deleted-and-still-absent
    path matches and is skipped. (A zero-byte file is indistinguishable from an
    absent one -- both hash empty -- an accepted blind spot of the convention.)

    Any mismatch is CRITICAL: the file was edited outside the audited write
    path, so the audit trail no longer pins its state. A legitimate human edit
    in Obsidian surfaces here too, by design -- the finding tells the PI the
    trail lost its pin, not that the edit was malicious. Malformed log lines
    are skipped, mirroring audit_unpaired_writes."""
    import hashlib

    empty = "sha256:" + hashlib.sha256(b"").hexdigest()
    log = vault / "system" / "logs" / "audit.jsonl"
    if not log.is_file():
        return []
    latest: dict[str, dict] = {}                   # path -> last write_complete
    for line in read(log).splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(e, dict) or e.get("decision") != "write_complete":
            continue
        path, after = e.get("path"), e.get("after_hash")
        if isinstance(path, str) and path and isinstance(after, str) and after:
            latest[path] = e
    out = []
    for path, e in sorted(latest.items()):
        f = vault / path
        try:
            current = ("sha256:" + hashlib.sha256(f.read_bytes()).hexdigest()
                       if f.exists() else empty)
        except OSError as exc:
            out.append(Finding("vault-hash-drift", "CRITICAL", path,
                               f"cannot hash audited file: {exc}"))
            continue
        if current != e["after_hash"]:
            state = "missing" if current == empty else "edited"
            out.append(Finding("vault-hash-drift", "CRITICAL", path,
                               f"on-disk state ({state}) no longer matches the last "
                               f"audited after_hash ({e.get('action')}, task "
                               f"{e.get('task_id')}, {e.get('timestamp')}) -- "
                               f"out-of-band change; the audit trail no longer "
                               f"pins this file's state"))
    return out
def audit_log_size(vault: Path, max_mb: float = 50.0) -> list[Finding]:
    """Advisory size check on the append-only-forever audit log (ADR-25).

    audit.jsonl is never rotated -- rotation would complicate the per-write
    pairing reads (audit_unpaired_writes), the hash-drift walk (vault_hash_drift),
    and the session digests for no benefit at single-researcher write volume.
    Unbounded growth is surfaced here instead of staying silent: a LOW advisory
    fires once the log exceeds a generous 50 MB threshold."""
    log = vault / "system" / "logs" / "audit.jsonl"
    if not log.is_file():
        return []
    size_mb = log.stat().st_size / (1024 * 1024)
    if size_mb <= max_mb:
        return []
    return [Finding("audit-log-size", "LOW", "system/logs/audit.jsonl",
                    f"audit log is {size_mb:.0f} MB (advisory threshold {max_mb:.0f} MB) "
                    f"-- append-only forever by design (ADR-25), so growth is "
                    f"surfaced here, never rotated away")]
