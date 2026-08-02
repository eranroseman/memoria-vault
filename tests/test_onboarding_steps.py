"""Contract tests for onboarding-step telemetry (O1 spec §5): an observer, never a gate."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.onboarding_steps import (
    ONBOARDING_STEPS,
    emit_onboarding_step,
    emit_onboarding_step_once,
    has_onboarding_step,
)


def test_onboarding_step_is_a_registered_all_string_native_type() -> None:
    from memoria_vault.runtime.telemetry import NATIVE_EVENT_FIELDS

    assert NATIVE_EVENT_FIELDS["onboarding-step"] == frozenset({"step"})


def test_onboarding_steps_roster_is_the_spec_five() -> None:
    # Literals, and nothing derived from ONBOARDING_STEPS: a test that iterates the
    # roster still passes after the roster loses an entry.
    assert ONBOARDING_STEPS == {
        "init-done",
        "onboard-done",
        "project-framed",
        "seed-installed",
        "first-answer",
    }


def test_emit_onboarding_step_records_one_server_side_row(tmp_path: Path) -> None:
    event_id = emit_onboarding_step(tmp_path, "init-done")

    assert event_id
    with state.connect(tmp_path) as conn:
        row = conn.execute(
            "SELECT event_type, session_id, surface, payload_json FROM telemetry_events"
            " WHERE event_id = ?",
            (event_id,),
        ).fetchone()
    assert row["event_type"] == "onboarding-step"
    # NULL here is the real producer state, not an unfixtured default: an onboarding
    # step is recorded server-side with no client envelope. The producer of non-NULL
    # session_id/surface is a client-submitted empirical event, fixtured by
    # tests/test_telemetry_events.py::
    # test_record_telemetry_event_keeps_client_session_and_surface_for_empirical_events.
    assert row["session_id"] is None  # spec §5: server-side, session_id NULL
    assert row["surface"] is None
    assert json.loads(row["payload_json"]) == {"step": "init-done"}
    assert has_onboarding_step(tmp_path, "init-done") is True
    assert has_onboarding_step(tmp_path, "first-answer") is False


def test_emit_onboarding_step_records_every_step_under_its_own_name(tmp_path: Path) -> None:
    # Each step name is written through, so a helper that hardcoded one step (or
    # dropped the payload) cannot pass. Literal list, not a loop over ONBOARDING_STEPS.
    for step in ("init-done", "onboard-done", "project-framed", "seed-installed", "first-answer"):
        assert emit_onboarding_step(tmp_path, step)

    with state.connect(tmp_path) as conn:
        payloads = [
            json.loads(row["payload_json"])
            for row in conn.execute(
                "SELECT payload_json FROM telemetry_events WHERE event_type = 'onboarding-step'"
                " ORDER BY payload_json"
            )
        ]
    assert payloads == [
        {"step": "first-answer"},
        {"step": "init-done"},
        {"step": "onboard-done"},
        {"step": "project-framed"},
        {"step": "seed-installed"},
    ]
    assert has_onboarding_step(tmp_path, "seed-installed") is True


def test_emit_onboarding_step_appends_nothing_to_the_journal(tmp_path: Path) -> None:
    # Proved at the writer, not at the reader: verify_journal_chain cannot see a
    # telemetry row either way, so only the event_log count shows this emitter does
    # not also journal.
    emit_onboarding_step(tmp_path, "init-done")

    with state.connect(tmp_path) as conn:
        journal = conn.execute("SELECT COUNT(*) FROM event_log").fetchone()[0]
        telemetry = conn.execute("SELECT COUNT(*) FROM telemetry_events").fetchone()[0]
    assert journal == 0
    assert telemetry == 1
    assert state.verify_journal_chain(tmp_path)["events"] == 0


def test_emit_onboarding_step_rejects_unknown_steps(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown onboarding step"):
        emit_onboarding_step(tmp_path, "made-up-step")
    with pytest.raises(ValueError, match="unknown onboarding step"):
        has_onboarding_step(tmp_path, "made-up-step")
    with pytest.raises(ValueError, match="unknown onboarding step"):
        emit_onboarding_step_once(tmp_path, "made-up-step")

    # A programmer error at the call site never reaches the sink.
    with state.connect(tmp_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM telemetry_events").fetchone()[0] == 0


def _disable_the_telemetry_sink(vault: Path) -> None:
    """Make every telemetry insert fail for real, at the sink.

    `DROP TABLE telemetry_events` is NOT a durable arrangement: `state._init`
    re-runs the whole of `schema.sql` (all `CREATE ... IF NOT EXISTS`) on every
    `state.connect`, so the next connection puts the table straight back and the
    emit succeeds. A `BEFORE INSERT` trigger survives that re-run, refuses only
    writes to this one table, and leaves reads and the rest of the vault working
    — the shape of a sink that is present but refusing.
    """
    with state.connect(vault) as conn:
        conn.execute(
            "CREATE TRIGGER telemetry_sink_offline BEFORE INSERT ON telemetry_events"
            " BEGIN SELECT RAISE(ABORT, 'telemetry sink offline'); END"
        )


def test_emit_onboarding_step_no_ops_when_the_sink_refuses_the_insert(tmp_path: Path) -> None:
    _disable_the_telemetry_sink(tmp_path)

    # The failure is produced, not mocked: the real insert raises.
    with state.connect(tmp_path) as conn, pytest.raises(sqlite3.DatabaseError):
        conn.execute(
            "INSERT INTO telemetry_events (event_id, ts, event_type, payload_json)"
            " VALUES ('probe', 'ts', 'onboarding-step', '{}')"
        )

    assert emit_onboarding_step(tmp_path, "init-done") is None  # observer, never a gate
    assert emit_onboarding_step_once(tmp_path, "init-done") is None
    # Reads still work here, so the False is the honest "no row", not a swallowed error.
    assert has_onboarding_step(tmp_path, "init-done") is False


def test_onboarding_step_reads_no_op_on_an_unreadable_database(tmp_path: Path) -> None:
    emit_onboarding_step(tmp_path, "init-done")
    assert has_onboarding_step(tmp_path, "init-done") is True
    database = state.db_path(tmp_path)
    for suffix in ("-wal", "-shm"):
        sidecar = database.with_name(database.name + suffix)
        sidecar.unlink(missing_ok=True)
    database.write_bytes(b"not a database at all\n")

    # A corrupt vault DB is the read-side sink failure; the prior True above shows
    # the False below is the guard firing, not an empty table.
    assert has_onboarding_step(tmp_path, "init-done") is False
    assert emit_onboarding_step(tmp_path, "init-done") is None


def test_emit_onboarding_step_no_ops_without_the_telemetry_module(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(sys.modules, "memoria_vault.runtime.telemetry", None)

    assert emit_onboarding_step(tmp_path, "init-done") is None


def test_emit_onboarding_step_once_skips_when_a_prior_row_exists(tmp_path: Path) -> None:
    first = emit_onboarding_step_once(tmp_path, "project-framed")
    second = emit_onboarding_step_once(tmp_path, "project-framed")

    assert first
    assert second is None
    with state.connect(tmp_path) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM telemetry_events WHERE event_type = 'onboarding-step'"
        ).fetchone()[0]
    assert count == 1


def test_emit_onboarding_step_once_dedupes_per_step_not_per_event_type(tmp_path: Path) -> None:
    # A prior row for a *different* step must not suppress this one, or the five
    # steps collapse into one and every §5 delta disappears.
    assert emit_onboarding_step_once(tmp_path, "init-done")
    assert emit_onboarding_step_once(tmp_path, "seed-installed")

    with state.connect(tmp_path) as conn:
        steps = sorted(
            json.loads(row["payload_json"])["step"]
            for row in conn.execute("SELECT payload_json FROM telemetry_events")
        )
    assert steps == ["init-done", "seed-installed"]


def test_emit_onboarding_step_repeats_without_the_once_guard(tmp_path: Path) -> None:
    # The plain emitter is an honest observer of real re-runs (spec-gap resolution 4);
    # only emit_onboarding_step_once dedupes.
    first = emit_onboarding_step(tmp_path, "init-done")
    second = emit_onboarding_step(tmp_path, "init-done")

    assert first != second
    with state.connect(tmp_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM telemetry_events").fetchone()[0]
    assert count == 2
