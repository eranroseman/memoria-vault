"""Strict empirical-use event schema for alpha.20 data collection."""

from __future__ import annotations

import uuid
from typing import Any

from memoria_vault.runtime.time import parse_iso

EMPIRICAL_EVENT_SCHEMA = "empirical_event.v1"
JOURNAL_EVENT_REF_SCHEMA = "journal_event_ref.v1"
EMPIRICAL_EVENT_RECORD_OPERATION = "empirical-event-record"

SURFACES = frozenset({"cli", "rest", "mcp", "obsidian", "vscode", "manual"})
WORKFLOWS = frozenset(
    {
        "ask",
        "capture",
        "gap",
        "evidence-review",
        "canvas",
        "draft",
        "srd",
        "export",
        "session",
        "connection",
        "operation",
    }
)
DECISIONS = frozenset({"accept", "reject", "edit", "defer", "override", "abandon"})
OUTCOMES = frozenset(
    {
        "connected",
        "queued",
        "flushed",
        "kept-artifact",
        "fallback",
        "exported",
        "blocked",
        "failed",
        "stopped",
    }
)
REASON_CODES = frozenset(
    {
        "useful",
        "not-useful",
        "too-slow",
        "missing-context",
        "wrong-scope",
        "duplicate",
        "confusing",
        "privacy",
        "offline",
        "external-tool",
        "other",
    }
)

BASE_REQUIRED_FIELDS = frozenset({"event_id", "event_type", "timestamp", "session_id", "surface"})
EVENT_REQUIRED_FIELDS = {
    "session.started": frozenset({"workflow"}),
    "session.stopped": frozenset({"workflow", "outcome", "duration_s"}),
    "http.connected": frozenset({"workflow", "outcome"}),
    "view.opened": frozenset({"workflow"}),
    "operation.queued": frozenset({"workflow", "outcome"}),
    "disposition.recorded": frozenset({"workflow", "decision", "reason_code"}),
    "fallback.recorded": frozenset({"workflow", "outcome", "reason_code"}),
    "export.attempted": frozenset({"workflow", "variant", "outcome", "reason_code"}),
}
ALLOWED_FIELDS = frozenset(
    {
        *BASE_REQUIRED_FIELDS,
        "workflow",
        "decision",
        "outcome",
        "reason_code",
        "duration_s",
        "project_id",
        "item_type",
        "item_id",
        "variant",
    }
)
ENUM_FIELDS = {
    "surface": SURFACES,
    "workflow": WORKFLOWS,
    "decision": DECISIONS,
    "outcome": OUTCOMES,
    "reason_code": REASON_CODES,
}
OPAQUE_ID_FIELDS = frozenset({"session_id", "project_id", "item_id"})


def validate_empirical_event(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a normalized empirical event or raise ``ValueError``."""
    if not isinstance(payload, dict):
        raise ValueError("empirical event payload must be an object")
    unknown = sorted(set(payload) - ALLOWED_FIELDS)
    if unknown:
        raise ValueError(f"empirical event contains unsupported fields: {', '.join(unknown)}")

    event_type = _required_string(payload, "event_type")
    if event_type not in EVENT_REQUIRED_FIELDS:
        allowed = ", ".join(sorted(EVENT_REQUIRED_FIELDS))
        raise ValueError(f"event_type must be one of: {allowed}")

    required = BASE_REQUIRED_FIELDS | EVENT_REQUIRED_FIELDS[event_type]
    missing = sorted(field for field in required if _missing(payload.get(field)))
    if missing:
        raise ValueError(f"empirical event missing required fields: {', '.join(missing)}")

    event: dict[str, Any] = {}
    for field in sorted(ALLOWED_FIELDS):
        if field not in payload:
            continue
        value = payload[field]
        if field == "duration_s":
            event[field] = _duration(value)
        elif field == "event_id":
            event[field] = _uuid_string(value)
        elif field == "timestamp":
            event[field] = _timestamp(value)
        else:
            event[field] = _string_field(field, value)

    for field, allowed in ENUM_FIELDS.items():
        if field in event and event[field] not in allowed:
            allowed_text = ", ".join(sorted(allowed))
            raise ValueError(f"{field} must be one of: {allowed_text}")
    for field in OPAQUE_ID_FIELDS:
        if field in event:
            _reject_pathlike(field, event[field])
    return event


def _missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _required_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value.strip()


def _string_field(field: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _uuid_string(value: Any) -> str:
    raw = _string_field("event_id", value)
    try:
        return str(uuid.UUID(raw))
    except ValueError as exc:
        raise ValueError("event_id must be a UUID") from exc


def _timestamp(value: Any) -> str:
    raw = _string_field("timestamp", value)
    parsed = parse_iso(raw)
    if parsed is None:
        raise ValueError("timestamp must be ISO-8601")
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return raw


def _duration(value: Any) -> float | int:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ValueError("duration_s must be numeric")
    if value <= 0:
        raise ValueError("duration_s must be positive")
    return value


def _reject_pathlike(field: str, value: str) -> None:
    if (
        "/" in value
        or "\\" in value
        or ".." in value
        or "://" in value
        or value.startswith(("~", ".", "file:"))
    ):
        raise ValueError(f"{field} must be an opaque id, not a path or URI")
