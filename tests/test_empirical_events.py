from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from memoria_vault.engine import api as engine_api
from memoria_vault.engine.empirical_events import (
    validate_disposition_event,
    validate_empirical_event,
    validate_read_event,
)
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


def test_disposition_event_accepts_valid_payload() -> None:
    event = validate_disposition_event(
        {"decision": "accept", "item_type": "attention", "item_id": "inbox/attention/x.md"}
    )
    assert event == {
        "decision": "accept",
        "item_type": "attention",
        "item_id": "inbox/attention/x.md",
    }


def test_disposition_event_rejects_bad_decision() -> None:
    with pytest.raises(ValueError, match="decision must be one of"):
        validate_disposition_event({"decision": "maybe", "item_type": "attention", "item_id": "x"})


def test_disposition_event_rejects_unknown_field() -> None:
    with pytest.raises(ValueError, match="unsupported fields"):
        validate_disposition_event(
            {"decision": "accept", "item_type": "attention", "item_id": "x", "rating": 5}
        )


def test_disposition_event_requires_all_fields() -> None:
    with pytest.raises(ValueError, match="missing required fields"):
        validate_disposition_event({"decision": "accept"})


def test_read_event_accepts_valid_payload() -> None:
    assert validate_read_event({"workflow": "ask", "staleness_hit": True}) == {
        "workflow": "ask",
        "staleness_hit": True,
    }


def test_read_event_requires_workflow_and_staleness_hit() -> None:
    with pytest.raises(ValueError, match="missing required fields"):
        validate_read_event({"workflow": "ask"})


def test_read_event_rejects_non_bool_staleness_hit() -> None:
    with pytest.raises(ValueError, match="staleness_hit must be a boolean"):
        validate_read_event({"workflow": "ask", "staleness_hit": "yes"})


def test_empirical_event_accepts_loudness_and_staleness_hit() -> None:
    event = validate_empirical_event(
        _event(
            event_type="session.stopped",
            outcome="stopped",
            duration_s=1,
            loudness="alert",
            staleness_hit=True,
        )
    )
    assert event["loudness"] == "alert"
    assert event["staleness_hit"] is True


def test_empirical_event_rejects_bad_loudness() -> None:
    event = _event(event_type="session.stopped", outcome="stopped", duration_s=1, loudness="loud")
    with pytest.raises(ValueError, match="loudness must be one of"):
        validate_empirical_event(event)


def test_empirical_event_rejects_non_bool_staleness_hit() -> None:
    event = _event(
        event_type="session.stopped", outcome="stopped", duration_s=1, staleness_hit="yes"
    )
    with pytest.raises(ValueError, match="staleness_hit must be a boolean"):
        validate_empirical_event(event)


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
        "output": "telemetry_event_ref.v1",
    }
    assert policy["allowed_tools"] == ["trusted_writer"]
    # The sink moved to `telemetry_events` (T.3), so the manifest no longer grants
    # this operation the journal write scope it stopped using. A stale grant here is
    # not inert: `require_policy_path` reads `allowed_paths` as the permission list.
    assert ".memoria/journal/" not in policy["allowed_paths"]


def test_empirical_event_operation_records_one_telemetry_row_and_no_journal_row(
    tmp_path: Path,
) -> None:
    """T.3: the door contract is unchanged; the sink is `telemetry_events`.

    This is the same coverage the journal-sink version carried — replay idempotency,
    the echoed client `event_id`, and the privacy allowlist on what is actually
    stored — re-pointed at the surviving producer, plus the writer-side proof that
    the journal gained nothing (no `event_log` row, no JSONL line, no commit).
    """
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
    assert first["result"]["telemetry_id"]
    assert {"journal_event_id", "commit", "schema"}.isdisjoint(first["result"])
    with state.connect(vault) as conn:
        rows = conn.execute(
            "SELECT event_id, event_type, session_id, surface, payload_json FROM telemetry_events"
        ).fetchall()
        journal_rows = conn.execute("SELECT COUNT(*) AS count FROM event_log").fetchone()["count"]
    assert len(rows) == 1
    assert rows[0]["event_id"] == first["result"]["telemetry_id"]
    assert rows[0]["event_type"] == "empirical_event.v1"
    assert rows[0]["session_id"] == event["session_id"]
    assert rows[0]["surface"] == event["surface"]
    stored = json.loads(rows[0]["payload_json"])
    assert stored["event_id"] == event["event_id"]
    assert {"body", "content", "text", "path", "uri"}.isdisjoint(stored)
    # Writer-side journal proof. The old sink built the whole journal apparatus from
    # nothing in this bare vault, so its total absence is the assertion: not one
    # `event_log` row of any type, no per-machine JSONL, no tracked anchor, no commit.
    assert journal_rows == 0
    assert not (vault / ".memoria/journal").exists()
    assert not (vault / state.JOURNAL_HEAD_REL).exists()
    assert engine_api.read_journal(vault, operation="empirical-event-record")["events"] == []
    assert git(vault, "rev-list", "--all", "--count") == "0"


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
        actor="pi",
    )

    assert result["ok"] is False
    assert "requires idempotency_key=empirical-event:" in result["result"]["error"]
    assert list(iter_jsonl(vault / ".memoria/journal/test-machine.jsonl")) == []


def test_workflows_roster_includes_attention() -> None:
    from memoria_vault.engine.empirical_events import WORKFLOWS, validate_read_event

    assert "attention" in WORKFLOWS
    event = validate_read_event({"workflow": "attention", "staleness_hit": True})
    assert event == {"workflow": "attention", "staleness_hit": True}


@pytest.mark.parametrize("write_path", ["curate-note-link", "insert-concept-edge"])
def test_edge_write_event_accepts_every_roster_relation_on_both_write_paths(
    write_path: str,
) -> None:
    """The `relation_type` enum IS `EDGE_RELATIONS` -- not a second hand-kept roster."""
    from memoria_vault.engine.empirical_events import validate_edge_write_event
    from memoria_vault.runtime.subsystems.lib.edges import EDGE_RELATIONS

    roster = sorted(EDGE_RELATIONS)

    # `tension` is the discriminator: it is in EDGE_RELATIONS and out of
    # LINK_RELATIONS, so a validator keyed to the narrower roster fails here.
    assert "tension" in roster
    assert [
        validate_edge_write_event({"relation_type": relation, "write_path": write_path})
        for relation in roster
    ] == [{"relation_type": relation, "write_path": write_path} for relation in roster]


def test_edge_write_event_normalizes_surrounding_whitespace_before_the_enum_check() -> None:
    """Strip then check: a padded roster verb is the same write, not an off-roster one."""
    from memoria_vault.engine.empirical_events import validate_edge_write_event

    assert validate_edge_write_event(
        {"relation_type": "  tension\n", "write_path": " insert-concept-edge "}
    ) == {"relation_type": "tension", "write_path": "insert-concept-edge"}


def test_edge_write_event_rejects_an_off_roster_relation() -> None:
    from memoria_vault.engine.empirical_events import validate_edge_write_event

    # `backing` is a Toulmin term the seven-relation roster deliberately omits.
    with pytest.raises(ValueError, match="relation_type must be one of"):
        validate_edge_write_event({"relation_type": "backing", "write_path": "curate-note-link"})


def test_edge_write_event_rejects_an_unknown_write_path() -> None:
    from memoria_vault.engine.empirical_events import validate_edge_write_event

    with pytest.raises(ValueError, match="write_path must be one of"):
        validate_edge_write_event({"relation_type": "supports", "write_path": "vim"})


@pytest.mark.parametrize(
    ("payload", "missing"),
    [
        ({"relation_type": "supports"}, "write_path"),
        ({"write_path": "curate-note-link"}, "relation_type"),
        ({"relation_type": "  ", "write_path": "curate-note-link"}, "relation_type"),
    ],
)
def test_edge_write_event_rejects_a_missing_field(payload: dict, missing: str) -> None:
    """Both fields are required, so each one's absence must be named on its own."""
    from memoria_vault.engine.empirical_events import validate_edge_write_event

    with pytest.raises(ValueError, match=f"missing required fields: {missing}$"):
        validate_edge_write_event(payload)


def test_edge_write_event_rejects_extra_fields_and_non_objects() -> None:
    """The field set is closed: a counter row carries no endpoint and no free text."""
    from memoria_vault.engine.empirical_events import validate_edge_write_event

    with pytest.raises(ValueError, match="unsupported fields: source_path, warrant"):
        validate_edge_write_event(
            {
                "relation_type": "supports",
                "write_path": "curate-note-link",
                "source_path": "notes/a.md",
                "warrant": "licensing text",
            }
        )
    with pytest.raises(ValueError, match="must be an object"):
        validate_edge_write_event([("relation_type", "supports")])  # type: ignore[arg-type]


def _import_run_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "run_id": "import-20260717-a1b2",
        "format": "bibtex",
        "entries_total": 13,
        "admitted": 9,
        "skipped": 1,
        "failed": 2,
        "duplicates_flagged": 1,
        "duration_s": 41.5,
        "index_refresh_s": 3.2,
    }
    row.update(overrides)
    return row


def test_validate_import_run_event_normalizes_one_row_per_run() -> None:
    from memoria_vault.engine.empirical_events import (
        IMPORT_RUN_EVENT_SCHEMA,
        validate_import_run_event,
    )

    assert IMPORT_RUN_EVENT_SCHEMA == "import-run.v1"
    event = validate_import_run_event(_import_run_row())
    assert event == _import_run_row()
    assert isinstance(event["entries_total"], int)
    assert isinstance(event["duration_s"], float)
    assert validate_import_run_event(_import_run_row(format="csl"))["format"] == "csl"


def test_validate_import_run_event_accepts_the_honest_zeros_of_a_no_op_run() -> None:
    # A re-run that admits nothing refreshes no index (O2 plan GAP 4) and flags no
    # duplicates. Every count and both timings must survive as literal zero: a
    # truthiness-based required-field check would call them missing and refuse the
    # only run shape the resume path can produce.
    from memoria_vault.engine.empirical_events import validate_import_run_event

    row = _import_run_row(
        entries_total=0,
        admitted=0,
        skipped=0,
        failed=0,
        duplicates_flagged=0,
        duration_s=0.0,
        index_refresh_s=0.0,
    )

    assert validate_import_run_event(row) == row


def test_validate_import_run_event_rejects_bad_shapes() -> None:
    from memoria_vault.engine.empirical_events import validate_import_run_event

    with pytest.raises(ValueError, match="admitted must be an integer"):
        validate_import_run_event(_import_run_row(admitted=True))
    with pytest.raises(ValueError, match="entries_total must be an integer"):
        validate_import_run_event(_import_run_row(entries_total=13.0))
    with pytest.raises(ValueError, match="failed must be >= 0"):
        validate_import_run_event(_import_run_row(failed=-1))
    with pytest.raises(ValueError, match="format must be one of"):
        validate_import_run_event(_import_run_row(format="ris"))
    with pytest.raises(ValueError, match="missing required fields: run_id"):
        validate_import_run_event(
            {key: value for key, value in _import_run_row().items() if key != "run_id"}
        )
    with pytest.raises(ValueError, match="unsupported fields: verdict"):
        validate_import_run_event(_import_run_row(verdict="clean"))
    with pytest.raises(ValueError, match="opaque id"):
        validate_import_run_event(_import_run_row(run_id="../escape"))
    with pytest.raises(ValueError, match="index_refresh_s must be numeric"):
        validate_import_run_event(_import_run_row(index_refresh_s="3.2"))
    with pytest.raises(ValueError, match="duration_s must be numeric"):
        validate_import_run_event(_import_run_row(duration_s=True))
    with pytest.raises(ValueError, match="index_refresh_s must be >= 0"):
        validate_import_run_event(_import_run_row(index_refresh_s=-0.1))
    with pytest.raises(ValueError, match="payload must be an object"):
        validate_import_run_event([("run_id", "x")])  # type: ignore[arg-type]


def test_validate_import_run_event_guards_every_count_and_timing_field() -> None:
    # Class-1 guard: one representative field proves nothing about a per-field loop.
    # Each name is checked alone so a truncated IMPORT_RUN_COUNT_FIELDS /
    # IMPORT_RUN_TIMING_FIELDS tuple cannot pass by riding a neighbour's assertion.
    from memoria_vault.engine.empirical_events import (
        IMPORT_RUN_COUNT_FIELDS,
        IMPORT_RUN_TIMING_FIELDS,
        validate_import_run_event,
    )

    assert IMPORT_RUN_COUNT_FIELDS == (
        "entries_total",
        "admitted",
        "skipped",
        "failed",
        "duplicates_flagged",
    )
    assert IMPORT_RUN_TIMING_FIELDS == ("duration_s", "index_refresh_s")

    for field in IMPORT_RUN_COUNT_FIELDS:
        with pytest.raises(ValueError, match=f"{field} must be an integer"):
            validate_import_run_event(_import_run_row(**{field: "3"}))
        with pytest.raises(ValueError, match=f"{field} must be >= 0"):
            validate_import_run_event(_import_run_row(**{field: -1}))
    for field in IMPORT_RUN_TIMING_FIELDS:
        with pytest.raises(ValueError, match=f"{field} must be numeric"):
            validate_import_run_event(_import_run_row(**{field: "3.2"}))
        with pytest.raises(ValueError, match=f"{field} must be >= 0"):
            validate_import_run_event(_import_run_row(**{field: -1}))
