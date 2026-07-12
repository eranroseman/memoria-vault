"""tests/test_schema_v9.py — v9 schema contract."""

import sqlite3

import pytest

from memoria_vault.runtime import state


def _conn(tmp_path):
    vault = tmp_path / "vault"
    (vault / ".memoria").mkdir(parents=True)
    return state.connect(vault)


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


def test_event_log_indexes_exist(tmp_path):
    with _conn(tmp_path) as conn:
        names = {
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        }
    assert "idx_event_log_event_type" in names
    assert "idx_event_log_timestamp" in names
