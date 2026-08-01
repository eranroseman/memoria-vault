"""Non-chained telemetry sink (I1 spec §1): analytics-only events, never the journal."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.time import now_iso

# Native flow events: no client schema, so `record_telemetry_event` validates them
# field-for-field itself. Later sections add entries here rather than a second registry.
NATIVE_EVENT_FIELDS = {
    "attention-admitted": frozenset({"card_path", "kind", "loudness", "raised_by"}),
    "producer-run-skipped": frozenset({"producer", "reason"}),
}


def record_telemetry_event(vault: Path, event_type: str, payload: dict[str, Any]) -> str:
    """Validate and insert one analytics-only event. No journal append, no git effect."""
    event = _validated(event_type, payload)
    event_id = uuid.uuid4().hex
    with state.connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO telemetry_events
                (event_id, ts, event_type, session_id, surface, payload_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                now_iso(),
                event_type,
                event.get("session_id"),
                event.get("surface"),
                json.dumps(event, sort_keys=True),
            ),
        )
    return event_id


def _validated(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    from memoria_vault.engine import empirical_events as schemas

    if event_type == schemas.EMPIRICAL_EVENT_SCHEMA:
        return schemas.validate_empirical_event(payload)
    if event_type == schemas.READ_EVENT_SCHEMA:
        return schemas.validate_read_event(payload)
    if event_type == "edge-write.v1" and hasattr(schemas, "validate_edge_write_event"):
        return schemas.validate_edge_write_event(payload)
    fields = NATIVE_EVENT_FIELDS.get(event_type)
    if fields is None:
        raise ValueError(f"unknown telemetry event type: {event_type}")
    unknown = sorted(set(payload) - fields)
    if unknown:
        raise ValueError(f"{event_type} contains unsupported fields: {', '.join(unknown)}")
    missing = sorted(field for field in fields if not str(payload.get(field) or "").strip())
    if missing:
        raise ValueError(f"{event_type} missing required fields: {', '.join(missing)}")
    return {field: str(payload[field]).strip() for field in fields}
