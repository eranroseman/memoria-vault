"""Strict empirical-use event schema for local data collection."""

from __future__ import annotations

import uuid
from typing import Any

from memoria_vault.runtime.time import parse_iso

EMPIRICAL_EVENT_SCHEMA = "empirical_event.v1"
JOURNAL_EVENT_REF_SCHEMA = "journal_event_ref.v1"
EMPIRICAL_EVENT_RECORD_OPERATION = "empirical-event-record"
DISPOSITION_EVENT_SCHEMA = "disposition.v1"
READ_EVENT_SCHEMA = "read-observed.v1"
EDGE_WRITE_EVENT_SCHEMA = "edge-write.v1"

SURFACES = frozenset({"cli", "rest", "mcp", "obsidian", "vscode", "manual"})
WORKFLOWS = frozenset(
    {
        "ask",
        "attention",
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

LOUDNESS = frozenset({"quiet", "notice", "alert", "block"})

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
        "loudness",
        "staleness_hit",
    }
)
ENUM_FIELDS = {
    "surface": SURFACES,
    "workflow": WORKFLOWS,
    "decision": DECISIONS,
    "outcome": OUTCOMES,
    "reason_code": REASON_CODES,
    "loudness": LOUDNESS,
}
OPAQUE_ID_FIELDS = frozenset({"session_id", "project_id", "item_id"})
DISPOSITION_REQUIRED_FIELDS = frozenset({"decision", "item_type", "item_id"})
READ_REQUIRED_FIELDS = frozenset({"workflow", "staleness_hit"})
EDGE_WRITE_REQUIRED_FIELDS = frozenset({"relation_type", "write_path"})
# The two seams that mint a concept edge: the PI's typed link and the single-row
# upsert behind `confirm-tension`. A third write path is a schema change here.
EDGE_WRITE_PATHS = frozenset({"curate-note-link", "insert-concept-edge"})
IMPORT_RUN_EVENT_SCHEMA = "import-run.v1"
IMPORT_RUN_FORMATS = frozenset({"bibtex", "csl"})
IMPORT_RUN_COUNT_FIELDS = (
    "entries_total",
    "admitted",
    "skipped",
    "failed",
    "duplicates_flagged",
)
IMPORT_RUN_TIMING_FIELDS = ("duration_s", "index_refresh_s")
IMPORT_RUN_REQUIRED_FIELDS = frozenset(
    {"run_id", "format", *IMPORT_RUN_COUNT_FIELDS, *IMPORT_RUN_TIMING_FIELDS}
)


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
        elif field == "staleness_hit":
            event[field] = _bool_field(field, value)
        else:
            event[field] = _string_field(field, value)

    for field, allowed_values in ENUM_FIELDS.items():
        if field in event and event[field] not in allowed_values:
            allowed_text = ", ".join(sorted(allowed_values))
            raise ValueError(f"{field} must be one of: {allowed_text}")
    for field in OPAQUE_ID_FIELDS:
        if field in event:
            _reject_pathlike(field, event[field])
    return event


def validate_disposition_event(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a normalized server-side disposition event or raise ``ValueError``."""
    if not isinstance(payload, dict):
        raise ValueError("disposition event payload must be an object")
    unknown = sorted(set(payload) - DISPOSITION_REQUIRED_FIELDS)
    if unknown:
        raise ValueError(f"disposition event contains unsupported fields: {', '.join(unknown)}")
    missing = sorted(field for field in DISPOSITION_REQUIRED_FIELDS if _missing(payload.get(field)))
    if missing:
        raise ValueError(f"disposition event missing required fields: {', '.join(missing)}")
    decision = _string_field("decision", payload["decision"])
    if decision not in DECISIONS:
        raise ValueError(f"decision must be one of: {', '.join(sorted(DECISIONS))}")
    return {
        "decision": decision,
        "item_type": _string_field("item_type", payload["item_type"]),
        "item_id": _string_field("item_id", payload["item_id"]),
    }


def validate_read_event(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a normalized server-side read-observation event or raise ``ValueError``."""
    if not isinstance(payload, dict):
        raise ValueError("read event payload must be an object")
    unknown = sorted(set(payload) - READ_REQUIRED_FIELDS)
    if unknown:
        raise ValueError(f"read event contains unsupported fields: {', '.join(unknown)}")
    missing = sorted(field for field in READ_REQUIRED_FIELDS if _missing(payload.get(field)))
    if missing:
        raise ValueError(f"read event missing required fields: {', '.join(missing)}")
    workflow = _string_field("workflow", payload["workflow"])
    if workflow not in WORKFLOWS:
        raise ValueError(f"workflow must be one of: {', '.join(sorted(WORKFLOWS))}")
    return {
        "workflow": workflow,
        "staleness_hit": _bool_field("staleness_hit", payload["staleness_hit"]),
    }


def validate_edge_write_event(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a normalized per-relation-type edge-write counter or raise ``ValueError``.

    Counts only: two closed enums and nothing else. No endpoint, no warrant text,
    no note path — this row is the I1 touch-budget denominator, so it must stay
    aggregable without carrying vault content into the analytics table.
    """
    from memoria_vault.runtime.vocabulary.edges import EDGE_RELATIONS

    if not isinstance(payload, dict):
        raise ValueError("edge-write event payload must be an object")
    unknown = sorted(set(payload) - EDGE_WRITE_REQUIRED_FIELDS)
    if unknown:
        raise ValueError(f"edge-write event contains unsupported fields: {', '.join(unknown)}")
    missing = sorted(field for field in EDGE_WRITE_REQUIRED_FIELDS if _missing(payload.get(field)))
    if missing:
        raise ValueError(f"edge-write event missing required fields: {', '.join(missing)}")
    relation_type = _string_field("relation_type", payload["relation_type"])
    if relation_type not in EDGE_RELATIONS:
        raise ValueError(f"relation_type must be one of: {', '.join(sorted(EDGE_RELATIONS))}")
    write_path = _string_field("write_path", payload["write_path"])
    if write_path not in EDGE_WRITE_PATHS:
        raise ValueError(f"write_path must be one of: {', '.join(sorted(EDGE_WRITE_PATHS))}")
    return {"relation_type": relation_type, "write_path": write_path}


def validate_import_run_event(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a normalized per-run bulk-import event or raise ``ValueError``.

    One row per import run (O2 spec section 6): analytics-only, routed to the
    telemetry table — never the journal. Counts are integers; timings are
    non-negative numerics (whole-index refresh time until LOOP.1 lands). The
    row carries nine fields and no retraction count: ``--enrich`` only queues
    ``enrich-source`` jobs, so retraction truth does not exist at command
    return (#1517).
    """
    if not isinstance(payload, dict):
        raise ValueError("import-run event payload must be an object")
    unknown = sorted(set(payload) - IMPORT_RUN_REQUIRED_FIELDS)
    if unknown:
        raise ValueError(f"import-run event contains unsupported fields: {', '.join(unknown)}")
    missing = sorted(field for field in IMPORT_RUN_REQUIRED_FIELDS if _missing(payload.get(field)))
    if missing:
        raise ValueError(f"import-run event missing required fields: {', '.join(missing)}")
    run_id = _string_field("run_id", payload["run_id"])
    _reject_pathlike("run_id", run_id)
    entry_format = _string_field("format", payload["format"])
    if entry_format not in IMPORT_RUN_FORMATS:
        raise ValueError(f"format must be one of: {', '.join(sorted(IMPORT_RUN_FORMATS))}")
    event: dict[str, Any] = {"run_id": run_id, "format": entry_format}
    for field in IMPORT_RUN_COUNT_FIELDS:
        event[field] = _count_field(field, payload[field])
    for field in IMPORT_RUN_TIMING_FIELDS:
        event[field] = _elapsed_field(field, payload[field])
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


def _count_field(field: str, value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    if value < 0:
        raise ValueError(f"{field} must be >= 0")
    return value


def _elapsed_field(field: str, value: Any) -> float | int:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ValueError(f"{field} must be numeric")
    if value < 0:
        raise ValueError(f"{field} must be >= 0")
    return value


def _bool_field(field: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a boolean")
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
