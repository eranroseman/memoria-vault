"""Contract tests for the non-chained telemetry_events table and its writer."""

from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.time import now_iso

TELEMETRY_COLUMNS = ("event_id", "ts", "event_type", "session_id", "surface", "payload_json")


def _insert(conn: sqlite3.Connection, **values: str | None) -> None:
    columns = [name for name in TELEMETRY_COLUMNS if name in values]
    conn.execute(
        f"INSERT INTO telemetry_events ({', '.join(columns)})"
        f" VALUES ({', '.join('?' for _ in columns)})",
        tuple(values[name] for name in columns),
    )


def test_telemetry_events_table_lands_at_the_current_schema_version(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(telemetry_events)")}
        version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        indexes = {row[1] for row in conn.execute("PRAGMA index_list(telemetry_events)")}

    assert cols == {"event_id", "ts", "event_type", "session_id", "surface", "payload_json"}
    # Not a literal: the rung is whichever integer was free when this landed, and a
    # pinned number here is exactly what put an unrelated schema task on the critical
    # path. What has to hold is that a fresh install carries the table *and* the version.
    # `tests/test_schema_version.py` keeps the literal pin on both sides of that equality.
    assert version == state.SCHEMA_VERSION
    assert "idx_telemetry_type_ts" in indexes


def test_telemetry_index_covers_event_type_then_ts(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        columns = [
            row["name"]
            for row in conn.execute("PRAGMA index_info(idx_telemetry_type_ts)")
            # PRAGMA index_info yields (seqno, cid, name); seqno is already the order.
        ]

    assert columns == ["event_type", "ts"]


def test_telemetry_rows_round_trip_with_and_without_the_client_columns(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        _insert(
            conn,
            event_id="server-row",
            ts="2026-07-16T00:00:00+00:00",
            event_type="attention-admitted",
            payload_json='{"raised_by":"sweep"}',
        )
        _insert(
            conn,
            event_id="client-row",
            ts="2026-07-16T00:00:01+00:00",
            event_type="empirical_event.v1",
            session_id="s-1",
            surface="cli",
            payload_json='{"workflow":"ask"}',
        )

    with state.connect(tmp_path) as conn:
        rows = [
            tuple(row)
            for row in conn.execute(
                "SELECT event_id, ts, event_type, session_id, surface, payload_json"
                " FROM telemetry_events ORDER BY event_id"
            )
        ]

    assert rows == [
        (
            "client-row",
            "2026-07-16T00:00:01+00:00",
            "empirical_event.v1",
            "s-1",
            "cli",
            '{"workflow":"ask"}',
        ),
        (
            "server-row",
            "2026-07-16T00:00:00+00:00",
            "attention-admitted",
            None,
            None,
            '{"raised_by":"sweep"}',
        ),
    ]


def test_telemetry_events_enforces_primary_key_and_not_null_columns(tmp_path: Path) -> None:
    required = {
        "event_id": "e1",
        "ts": "2026-07-16T00:00:00+00:00",
        "event_type": "attention-admitted",
        "payload_json": "{}",
    }
    with state.connect(tmp_path) as conn:
        _insert(conn, **required)

        with pytest.raises(sqlite3.IntegrityError):
            _insert(conn, **{**required, "ts": "2026-07-16T00:00:02+00:00"})

        # `event_id` is deliberately absent: SQLite's `TEXT PRIMARY KEY` does not imply
        # NOT NULL on a rowid table, and cross-section contract 2 pins that DDL verbatim.
        # `record_telemetry_event` is the only writer and always mints a uuid4 hex.
        for column in ("ts", "event_type", "payload_json"):
            with pytest.raises(sqlite3.IntegrityError):
                _insert(conn, **{**required, "event_id": f"null-{column}", column: None})


def test_journal_verification_ignores_telemetry_rows(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        conn.execute(
            "INSERT INTO telemetry_events (event_id, ts, event_type, payload_json)"
            " VALUES (?, ?, ?, ?)",
            ("e1", "2026-07-16T00:00:00+00:00", "read-observed.v1", "{}"),
        )

    verdict = state.verify_journal_chain(tmp_path)

    assert verdict["ok"] is True
    assert verdict["events"] == 0


def _rows(vault: Path) -> list[sqlite3.Row]:
    with state.connect(vault) as conn:
        return conn.execute(
            "SELECT event_id, ts, event_type, session_id, surface, payload_json"
            " FROM telemetry_events ORDER BY ts, event_type"
        ).fetchall()


def test_native_event_fields_pins_both_registered_types_and_their_fields() -> None:
    from memoria_vault.runtime.telemetry import NATIVE_EVENT_FIELDS

    # Literals first, and no iteration over the registry anywhere in this test: a test
    # that derives its expectations from NATIVE_EVENT_FIELDS still passes when the
    # registry loses an entry. Later plans extend this dict; they extend these literals.
    assert set(NATIVE_EVENT_FIELDS) == {
        "attention-admitted",
        "onboarding-step",
        "producer-run-skipped",
    }
    assert NATIVE_EVENT_FIELDS["attention-admitted"] == frozenset(
        {"card_path", "kind", "loudness", "raised_by"}
    )
    # O1 T.1 extends this dict rather than starting a second registry; its own
    # field pin lives beside the helper in tests/test_onboarding_steps.py.
    assert NATIVE_EVENT_FIELDS["onboarding-step"] == frozenset({"step"})
    assert NATIVE_EVENT_FIELDS["producer-run-skipped"] == frozenset({"producer", "reason"})


def test_record_telemetry_event_inserts_validated_native_rows(tmp_path: Path, monkeypatch) -> None:
    from memoria_vault.runtime import telemetry
    from memoria_vault.runtime.telemetry import record_telemetry_event

    monkeypatch.setattr(telemetry, "now_iso", lambda: "2026-07-16T12:00:00Z")

    admitted_id = record_telemetry_event(
        tmp_path,
        "attention-admitted",
        {"card_path": "inbox/flag-x.md", "kind": "flag", "loudness": "alert", "raised_by": "sweep"},
    )
    # Padded values: the writer normalizes, so analytics group by "sweep", not " sweep ".
    skipped_id = record_telemetry_event(
        tmp_path, "producer-run-skipped", {"producer": " sweep ", "reason": "paused"}
    )

    rows = {row["event_type"]: row for row in _rows(tmp_path)}
    assert set(rows) == {"attention-admitted", "producer-run-skipped"}
    assert rows["attention-admitted"]["event_id"] == admitted_id
    assert rows["producer-run-skipped"]["event_id"] == skipped_id
    for row in rows.values():
        # Server-side rows never fabricate the client's columns.
        assert row["session_id"] is None
        assert row["surface"] is None
        assert row["ts"] == "2026-07-16T12:00:00Z"
    assert json.loads(rows["attention-admitted"]["payload_json"]) == {
        "card_path": "inbox/flag-x.md",
        "kind": "flag",
        "loudness": "alert",
        "raised_by": "sweep",
    }
    assert json.loads(rows["producer-run-skipped"]["payload_json"]) == {
        "producer": "sweep",
        "reason": "paused",
    }


def test_record_telemetry_event_mints_a_distinct_id_per_row(tmp_path: Path) -> None:
    from memoria_vault.runtime.telemetry import record_telemetry_event

    payload = {"producer": "sweep", "reason": "paused"}
    first = record_telemetry_event(tmp_path, "producer-run-skipped", dict(payload))
    second = record_telemetry_event(tmp_path, "producer-run-skipped", dict(payload))

    assert first != second
    assert {row["event_id"] for row in _rows(tmp_path)} == {first, second}


def test_record_telemetry_event_appends_nothing_to_the_journal(tmp_path: Path) -> None:
    from memoria_vault.runtime.telemetry import record_telemetry_event

    record_telemetry_event(
        tmp_path,
        "attention-admitted",
        {"card_path": "inbox/flag-x.md", "kind": "flag", "loudness": "alert", "raised_by": "sweep"},
    )

    # The storage ruling proven at the writer, not just at the reader: the raw-insert
    # test above shows verify_journal_chain cannot see telemetry rows, but only this
    # shows the writer does not also append one.
    with state.connect(tmp_path) as conn:
        journal = conn.execute("SELECT COUNT(*) FROM event_log").fetchone()[0]
    assert journal == 0
    assert state.verify_journal_chain(tmp_path)["events"] == 0
    assert len(_rows(tmp_path)) == 1


def test_record_telemetry_event_rejects_unknown_type_and_bad_fields(tmp_path: Path) -> None:
    from memoria_vault.runtime.telemetry import record_telemetry_event

    with pytest.raises(ValueError, match="unknown telemetry event type"):
        record_telemetry_event(tmp_path, "made-up.v1", {})
    with pytest.raises(ValueError, match="missing required fields"):
        record_telemetry_event(tmp_path, "producer-run-skipped", {"producer": "sweep"})
    # Present-but-blank is missing too, or a caller silences a producer with "".
    with pytest.raises(ValueError, match="missing required fields"):
        record_telemetry_event(
            tmp_path, "producer-run-skipped", {"producer": "sweep", "reason": " "}
        )
    with pytest.raises(ValueError, match="unsupported fields"):
        record_telemetry_event(
            tmp_path,
            "producer-run-skipped",
            {"producer": "sweep", "reason": "paused", "extra": "no"},
        )

    assert _rows(tmp_path) == []


def test_record_telemetry_event_routes_read_observed_through_its_validator(tmp_path: Path) -> None:
    from memoria_vault.runtime.telemetry import record_telemetry_event

    event_id = record_telemetry_event(
        tmp_path, "read-observed.v1", {"workflow": "attention", "staleness_hit": False}
    )
    assert event_id
    (row,) = _rows(tmp_path)
    assert row["event_type"] == "read-observed.v1"
    # The read validator's booleans survive as booleans, not as "False".
    assert json.loads(row["payload_json"]) == {"workflow": "attention", "staleness_hit": False}

    with pytest.raises(ValueError):
        record_telemetry_event(tmp_path, "read-observed.v1", {"workflow": "attention"})


def test_record_telemetry_event_keeps_client_session_and_surface_for_empirical_events(
    tmp_path: Path,
) -> None:
    from memoria_vault.runtime.telemetry import record_telemetry_event

    record_telemetry_event(
        tmp_path,
        "empirical_event.v1",
        {
            "event_id": str(uuid.uuid4()),
            "event_type": "view.opened",
            "timestamp": now_iso(),
            "session_id": "session-alpha",
            "surface": "obsidian",
            "workflow": "attention",
        },
    )

    (row,) = _rows(tmp_path)
    # Client-submitted events are the one producer of non-NULL session_id/surface;
    # without this the writer could drop both columns and every server-side test passes.
    assert row["session_id"] == "session-alpha"
    assert row["surface"] == "obsidian"


def test_edge_write_events_are_rejected_until_their_validator_lands(tmp_path: Path) -> None:
    from memoria_vault.engine import empirical_events
    from memoria_vault.runtime.telemetry import record_telemetry_event

    # The graph plan's ERP-D.6 adds `validate_edge_write_event` and owns flipping this
    # test; until then the hasattr guard must produce the honest error, not AttributeError.
    assert not hasattr(empirical_events, "validate_edge_write_event")
    with pytest.raises(ValueError, match="unknown telemetry event type"):
        record_telemetry_event(tmp_path, "edge-write.v1", {"edge_id": "e1"})
