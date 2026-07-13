"""tests/test_schema_v9.py — v9 schema contract."""

import hashlib
import sqlite3

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.trusted_writer import OperationContext


def _conn(tmp_path):
    vault = tmp_path / "vault"
    (vault / ".memoria").mkdir(parents=True)
    return state.connect(vault)


def _record_derivation(vault, *, input_id, output_id="concepts/output.md", actor):
    payload_text = "---\ntype: note\n---\n\nOutput.\n"
    state.record_file_output(
        vault,
        output_id=output_id,
        concept_type="note",
        check_status="unchecked",
        output_sha256="sha256:" + hashlib.sha256(payload_text.encode()).hexdigest(),
        staging_id=f".memoria/staging/{output_id}",
        payload_text=payload_text,
        context=OperationContext(
            actor=actor,
            run_id="schema-test",
            request_id="schema-test",
            operation_id="schema-test",
            machine="schema-test",
        ),
        inputs=[{"id": input_id}],
    )


def test_user_version_is_9(tmp_path):
    with _conn(tmp_path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 9


def test_operation_requests_actor_accepts_agent_and_rejects_bogus(tmp_path):
    with _conn(tmp_path) as conn:
        conn.execute(
            "INSERT INTO operation_requests"
            "(request_id, operation_id, actor, status, created_at, job_json)"
            " VALUES ('r1', 'op', 'agent', 'pending', 't', '{}')"
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO operation_requests"
                "(request_id, operation_id, actor, status, created_at, job_json)"
                " VALUES ('r2', 'op', 'bogus', 'pending', 't', '{}')"
            )


def test_operation_requests_actor_has_no_default(tmp_path):
    with _conn(tmp_path) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO operation_requests"
                "(request_id, operation_id, status, created_at, job_json)"
                " VALUES ('r3', 'op', 'pending', 't', '{}')"
            )


def test_derivations_actor_accepts_agent(tmp_path):
    with _conn(tmp_path) as conn:
        conn.execute(
            "INSERT INTO derivations(input_id, output_id, actor) VALUES ('a', 'b', 'agent')"
        )


def test_record_file_output_keeps_latest_derivation_actor(tmp_path):
    vault = tmp_path / "vault"
    _record_derivation(vault, input_id="sources/input.md", actor="pi")
    _record_derivation(vault, input_id="sources/input.md", actor="agent")

    with state.connect(vault) as conn:
        rows = conn.execute(
            "SELECT actor FROM derivations WHERE input_id = ? AND output_id = ?",
            ("sources/input.md", "concepts/output.md"),
        ).fetchall()

    assert [row["actor"] for row in rows] == ["agent"]


def test_record_file_output_rejects_invalid_actor_on_new_derivation(tmp_path):
    vault = tmp_path / "vault"

    with pytest.raises(sqlite3.IntegrityError):
        _record_derivation(vault, input_id="sources/input.md", actor="bogus")


def test_failed_derivation_actor_update_preserves_valid_actor(tmp_path):
    vault = tmp_path / "vault"
    _record_derivation(vault, input_id="sources/input.md", actor="pi")

    with pytest.raises(sqlite3.IntegrityError):
        _record_derivation(vault, input_id="sources/input.md", actor="bogus")

    with state.connect(vault) as conn:
        actor = conn.execute(
            "SELECT actor FROM derivations WHERE input_id = ? AND output_id = ?",
            ("sources/input.md", "concepts/output.md"),
        ).fetchone()["actor"]

    assert actor == "pi"


def test_event_log_indexes_exist(tmp_path):
    with _conn(tmp_path) as conn:
        names = {
            row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        }
    assert "idx_event_log_event_type" in names
    assert "idx_event_log_timestamp" in names


def test_request_envelope_requires_actor():
    with pytest.raises(TypeError):
        state.request_envelope(request_id="r", operation_id="op")


def test_request_envelope_rejects_blank_and_bogus_actor():
    for bad in ("", "  ", "claude"):
        with pytest.raises(ValueError):
            state.request_envelope(request_id="r", operation_id="op", actor=bad)


def test_request_envelope_accepts_vocabulary():
    for good in ("pi", "agent", "operation", "integrity"):
        env = state.request_envelope(request_id="r", operation_id="op", actor=good)
        assert env["actor"] == good
