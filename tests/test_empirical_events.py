from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from memoria_vault.engine import api as engine_api
from memoria_vault.engine.empirical_events import validate_empirical_event
from memoria_vault.runtime import state
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.operations import load_operation_policy
from memoria_vault.runtime.time import now_iso
from tests.helpers import git, init_git


def _workspace(tmp_path: Path) -> Path:
    init_git(tmp_path, "empirical@example.invalid", "Empirical Events")
    return tmp_path


def _event(**overrides: object) -> dict[str, object]:
    event: dict[str, object] = {
        "event_id": str(uuid.uuid4()),
        "event_type": "disposition.recorded",
        "timestamp": now_iso(),
        "session_id": "session-alpha",
        "surface": "obsidian",
        "workflow": "evidence-review",
        "decision": "accept",
        "reason_code": "useful",
        "item_type": "attention",
        "item_id": "item-alpha",
    }
    event.update(overrides)
    return event


def test_empirical_event_validator_accepts_normalized_event() -> None:
    event_id = str(uuid.uuid4()).upper()

    event = validate_empirical_event(_event(event_id=event_id, timestamp="2026-07-08T12:00:00Z"))

    assert event["event_id"] == str(uuid.UUID(event_id))
    assert event["timestamp"] == "2026-07-08T12:00:00Z"
    assert event["surface"] == "obsidian"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("event_id", "not-a-uuid", "event_id must be a UUID"),
        ("timestamp", "not-a-time", "timestamp must be ISO-8601"),
        ("timestamp", "2026-07-08T12:00:00", "timestamp must include a timezone"),
        ("surface", "editor", "surface must be one of"),
        ("workflow", "raw-notes", "workflow must be one of"),
        ("decision", "maybe", "decision must be one of"),
        ("outcome", "maybe", "outcome must be one of"),
        ("reason_code", "because", "reason_code must be one of"),
    ],
)
def test_empirical_event_validator_rejects_invalid_fields(
    field: str, value: object, message: str
) -> None:
    event = _event(event_type="session.stopped", outcome="stopped", duration_s=1)
    event[field] = value

    with pytest.raises(ValueError, match=message):
        validate_empirical_event(event)


@pytest.mark.parametrize(
    "event",
    [
        {"event_type": "session.started"},
        {"event_type": "session.stopped", "workflow": "session", "outcome": "stopped"},
        {"event_type": "http.connected", "workflow": "connection"},
        {"event_type": "view.opened"},
        {"event_type": "operation.queued", "workflow": "operation"},
        {"event_type": "disposition.recorded", "workflow": "gap", "decision": "defer"},
        {"event_type": "fallback.recorded", "workflow": "ask", "outcome": "fallback"},
        {
            "event_type": "export.attempted",
            "workflow": "export",
            "variant": "markdown",
            "outcome": "exported",
        },
    ],
)
def test_empirical_event_validator_requires_event_type_fields(event: dict[str, object]) -> None:
    payload: dict[str, object] = {
        "event_id": str(uuid.uuid4()),
        "timestamp": now_iso(),
        "session_id": "session-alpha",
        "surface": "obsidian",
        **event,
    }

    with pytest.raises(ValueError, match="empirical event missing required fields"):
        validate_empirical_event(payload)


@pytest.mark.parametrize(
    "field",
    [
        "body",
        "content",
        "text",
        "note_text",
        "draft_text",
        "excerpt",
        "path",
        "uri",
        "source_path",
        "target_path",
        "absolute_path",
    ],
)
def test_empirical_event_validator_rejects_unknown_or_text_fields(field: str) -> None:
    payload = _event()
    payload[field] = "leak"

    with pytest.raises(ValueError, match="unsupported fields"):
        validate_empirical_event(payload)


@pytest.mark.parametrize("field", ["session_id", "project_id", "item_id"])
def test_empirical_event_validator_rejects_pathlike_identifiers(field: str) -> None:
    payload = _event(**{field: "notes/private.md"})

    with pytest.raises(ValueError, match="opaque id"):
        validate_empirical_event(payload)


def test_empirical_event_validator_requires_positive_duration() -> None:
    payload = _event(event_type="session.stopped", outcome="stopped", duration_s=0)

    with pytest.raises(ValueError, match="duration_s must be positive"):
        validate_empirical_event(payload)


def test_empirical_event_operation_manifest_uses_schema_ids() -> None:
    policy = load_operation_policy(Path(), "empirical-event-record")

    assert policy["operation_id"] == "empirical-event-record"
    assert policy["io_schema"] == {
        "input": "empirical_event.v1",
        "output": "journal_event_ref.v1",
    }
    assert policy["allowed_tools"] == ["trusted_writer"]
    assert ".memoria/journal/" in policy["allowed_paths"]


def test_empirical_event_operation_records_journal_event_once(tmp_path: Path) -> None:
    vault = _workspace(tmp_path)
    event = _event()
    key = f"empirical-event:{event['event_id']}"

    first = engine_api.run_operation(
        vault,
        "empirical-event-record",
        event,
        idempotency_key=key,
        actor="agent",
        machine="test-machine",
    )
    second = engine_api.run_operation(
        vault,
        "empirical-event-record",
        event,
        idempotency_key=key,
        actor="agent",
        machine="test-machine",
    )

    assert first["ok"] is True
    assert second["ok"] is True
    assert second["job"]["status"] == "done"
    assert first["result"]["event_id"] == event["event_id"]
    assert first["result"]["schema"] == "journal_event_ref.v1"
    rows = list(iter_jsonl(vault / ".memoria/journal/test-machine.jsonl"))
    assert len(rows) == 1
    assert rows[0]["operation"] == "empirical-event-record"
    assert rows[0]["schema"] == "empirical_event.v1"
    assert rows[0]["event_id"] == event["event_id"]
    assert rows[0]["actor"] == "agent"
    assert {"body", "content", "text", "path", "uri"}.isdisjoint(rows[0])
    listed = engine_api.read_journal(vault, operation="empirical-event-record")
    assert len(listed["events"]) == 1
    assert listed["events"][0]["event_id"] == first["result"]["journal_event_id"]
    assert listed["events"][0]["payload"]["event_id"] == event["event_id"]
    assert listed["events"][0]["payload"]["request_id"] == first["job"]["job_id"]
    with state.connect(vault) as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS count FROM event_log WHERE event_type = 'empirical-event'"
        ).fetchone()["count"]
    assert count == 1
    committed = set(
        git(vault, "show", "--name-only", "--format=", first["result"]["commit"]).splitlines()
    )
    assert committed == {state.JOURNAL_HEAD_REL}


@pytest.mark.parametrize("idempotency_key", [None, "wrong-key"])
def test_empirical_event_operation_requires_event_id_idempotency_key(
    tmp_path: Path, idempotency_key: str | None
) -> None:
    vault = _workspace(tmp_path)
    event = _event()

    result = engine_api.run_operation(
        vault,
        "empirical-event-record",
        event,
        idempotency_key=idempotency_key,
        machine="test-machine",
    )

    assert result["ok"] is False
    assert "requires idempotency_key=empirical-event:" in result["result"]["error"]
    assert list(iter_jsonl(vault / ".memoria/journal/test-machine.jsonl")) == []
