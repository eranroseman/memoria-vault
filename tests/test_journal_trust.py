"""Journal-chain, export-reconciliation, and authoritative-read contracts."""

from __future__ import annotations

import json
from contextlib import contextmanager

import pytest

from memoria_vault import cli
from memoria_vault.cli import main
from memoria_vault.runtime import state, trusted_writer
from memoria_vault.runtime.jsonl import append_jsonl, iter_jsonl
from tests.helpers import init_cli_workspace, operation_context


def _seed_events(vault, count: int = 3) -> None:
    for index in range(count):
        trusted_writer.append_explicit_journal_event(
            vault,
            {
                "event": "run",
                "run_id": f"journal-run-{index}",
                "status": "started",
            },
            actor="operation",
            machine="journal-test",
        )
    state.write_journal_head_anchor(vault)


def _event_count(vault) -> int:
    with state.connect(vault) as conn:
        return int(conn.execute("SELECT COUNT(*) FROM event_log").fetchone()[0])


def test_verify_accepts_empty_chain_without_anchor(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    (vault / state.JOURNAL_HEAD_REL).unlink(missing_ok=True)

    report = state.verify_journal_chain(vault)

    assert report["ok"] is True
    assert report["events"] == 0
    assert report["tip"] == "GENESIS"
    assert report["anchor"] == ""


def test_verify_accepts_empty_chain_with_genesis_anchor(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    state.write_journal_head_anchor(vault)

    report = state.verify_journal_chain(vault)

    assert report["ok"] is True
    assert report["events"] == 0
    assert report["tip"] == "GENESIS"
    assert report["anchor"] == "GENESIS"


def test_verify_passes_on_healthy_chain(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    _seed_events(vault)

    report = state.verify_journal_chain(vault)

    assert report == {
        "ok": True,
        "events": 3,
        "tip": state.journal_head(vault),
        "anchor": state.journal_head(vault),
        "error": "",
    }


def test_verify_fails_on_tampered_payload(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    _seed_events(vault)
    with state.connect(vault) as conn:
        conn.execute("DROP TRIGGER event_log_no_update")
        conn.execute("UPDATE event_log SET payload_json = '{}' WHERE event_id = 2")

    report = state.verify_journal_chain(vault)

    assert report["ok"] is False
    assert "event 2" in report["error"]


def test_verify_fails_on_tampered_prev_hash(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    _seed_events(vault)
    with state.connect(vault) as conn:
        conn.execute("DROP TRIGGER event_log_no_update")
        conn.execute(
            "UPDATE event_log SET prev_hash = ? WHERE event_id = 2",
            ("sha256:forged-prev-hash",),
        )

    report = state.verify_journal_chain(vault)

    assert report["ok"] is False
    assert "event 2" in report["error"]


def test_verify_rejects_rehashed_chain_that_drops_committed_anchor(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    _seed_events(vault, count=2)
    trusted_writer.commit_explicit_writer_changes(
        vault,
        "anchor journal",
        [],
        actor="operation",
        machine="journal-test",
    )

    forged_events = []
    previous = "GENESIS"
    with state.connect(vault) as conn:
        conn.execute("DROP TRIGGER event_log_no_update")
        rows = conn.execute(
            """
            SELECT event_id, timestamp, event_type, machine, payload_json
            FROM event_log
            ORDER BY event_id
            """
        ).fetchall()
        for row in rows:
            event = json.loads(str(row["payload_json"]))
            event["run_id"] = f"forged-{row['event_id']}"
            payload = json.dumps(
                event,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            row_hash = state._journal_hash(
                int(row["event_id"]),
                str(row["timestamp"]),
                str(row["event_type"]),
                str(row["machine"]),
                payload,
                previous,
            )
            conn.execute(
                """
                UPDATE event_log
                SET payload_json = ?, prev_hash = ?, row_hash = ?
                WHERE event_id = ?
                """,
                (payload, previous, row_hash, row["event_id"]),
            )
            forged_events.append(event)
            previous = row_hash

    (vault / ".memoria/journal/journal-test.jsonl").write_text(
        "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in forged_events),
        encoding="utf-8",
    )
    (vault / state.JOURNAL_HEAD_REL).write_text(previous + "\n", encoding="utf-8")

    report = state.verify_journal_chain(vault)

    assert report["ok"] is False
    assert "committed" in report["error"]


def test_verify_rejects_event_type_that_conflicts_with_payload(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    _seed_events(vault, count=1)
    with state.connect(vault) as conn:
        conn.execute("DROP TRIGGER event_log_no_update")
        row = conn.execute(
            """
            SELECT event_id, timestamp, machine, payload_json, prev_hash
            FROM event_log
            """
        ).fetchone()
        row_hash = state._journal_hash(
            int(row["event_id"]),
            str(row["timestamp"]),
            "forged-type",
            str(row["machine"]),
            str(row["payload_json"]),
            str(row["prev_hash"]),
        )
        conn.execute(
            "UPDATE event_log SET event_type = ?, row_hash = ? WHERE event_id = ?",
            ("forged-type", row_hash, row["event_id"]),
        )
    (vault / state.JOURNAL_HEAD_REL).write_text(row_hash + "\n", encoding="utf-8")

    report = state.verify_journal_chain(vault)

    assert report["ok"] is False
    assert "event type" in report["error"]


def test_verify_fails_on_broken_anchor(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    _seed_events(vault)
    (vault / state.JOURNAL_HEAD_REL).write_text("bogus\n", encoding="utf-8")

    report = state.verify_journal_chain(vault)

    assert report["ok"] is False
    assert "anchor" in report["error"]


def test_verify_fails_when_nonempty_chain_has_no_anchor(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    _seed_events(vault)
    (vault / state.JOURNAL_HEAD_REL).unlink()

    report = state.verify_journal_chain(vault)

    assert report["ok"] is False
    assert "missing" in report["error"]


def test_journal_verify_cli_reports_health_and_failure(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    _seed_events(vault)

    assert main(["journal", "verify", "--workspace", str(vault), "--json"]) == 0
    healthy = json.loads(capsys.readouterr().out)
    assert healthy["ok"] is True
    assert healthy["events"] == 3

    (vault / state.JOURNAL_HEAD_REL).write_text("bogus\n", encoding="utf-8")
    assert main(["journal", "verify", "--workspace", str(vault), "--json"]) == 1
    failed = json.loads(capsys.readouterr().out)
    assert failed["ok"] is False
    assert "anchor" in failed["error"]


def test_workspace_scan_fails_before_mutation_on_broken_journal(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    _seed_events(vault)
    before = _event_count(vault)
    (vault / state.JOURNAL_HEAD_REL).write_text("bogus\n", encoding="utf-8")

    assert main(["workspace", "scan", "--workspace", str(vault), "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)

    assert payload["ok"] is False
    assert payload["journal"]["ok"] is False
    assert _event_count(vault) == before


def test_append_is_authoritative_before_jsonl_and_advances_anchor(tmp_path, capsys, monkeypatch):
    vault = init_cli_workspace(tmp_path, capsys)
    before = _event_count(vault)

    def crash_jsonl(*_args, **_kwargs):
        raise RuntimeError("jsonl append crashed")

    monkeypatch.setattr(trusted_writer, "append_jsonl", crash_jsonl)

    with pytest.raises(RuntimeError, match="jsonl append crashed"):
        trusted_writer.append_explicit_journal_event(
            vault,
            {"event": "run", "run_id": "db-first", "status": "started"},
            actor="operation",
            machine="journal-test",
        )

    assert _event_count(vault) == before + 1
    assert state.journal_head(vault) == state.journal_head_anchor(vault)
    assert (vault / state.JOURNAL_HEAD_REL).read_text(
        encoding="utf-8"
    ).strip() == state.journal_head(vault)


def test_mediated_append_keeps_context_when_jsonl_crashes(tmp_path, capsys, monkeypatch):
    vault = init_cli_workspace(tmp_path, capsys)
    context = operation_context(
        vault,
        actor="agent",
        operation_id="journal-mediated-test",
        machine="agent-machine",
        run_id="agent-run",
    )

    def crash_jsonl(*_args, **_kwargs):
        raise RuntimeError("jsonl append crashed")

    monkeypatch.setattr(trusted_writer, "append_jsonl", crash_jsonl)

    with pytest.raises(RuntimeError, match="jsonl append crashed"):
        trusted_writer.append_journal_event(
            vault,
            {"event": "run", "status": "started"},
            context=context,
        )

    with state.connect(vault) as conn:
        row = conn.execute(
            "SELECT payload_json FROM event_log ORDER BY event_id DESC LIMIT 1"
        ).fetchone()
    event = json.loads(str(row["payload_json"]))
    assert {
        key: event[key] for key in ("actor", "run_id", "request_id", "operation", "machine")
    } == {
        "actor": "agent",
        "run_id": "agent-run",
        "request_id": context.request_id,
        "operation": "journal-mediated-test",
        "machine": "agent-machine",
    }
    assert state.journal_head(vault) == state.journal_head_anchor(vault)


def test_reconcile_reemits_db_only_event_to_recorded_machine(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    event = {
        "event": "run",
        "run_id": "only-db",
        "status": "started",
        "timestamp": "2026-07-12T00:00:00+00:00",
        "actor": "operation",
        "machine": "journal-test",
    }
    state._append_journal_row(vault, event, machine="journal-test")
    state.write_journal_head_anchor(vault)

    assert trusted_writer.reconcile_journal_export(vault) == 1
    assert list(iter_jsonl(vault / ".memoria/journal/journal-test.jsonl")) == [event]
    assert trusted_writer.reconcile_journal_export(vault) == 0


def test_reconcile_preserves_duplicate_payload_counts(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    event = trusted_writer.append_explicit_journal_event(
        vault,
        {"event": "run", "run_id": "duplicate", "status": "started"},
        actor="operation",
        machine="journal-test",
    )
    state._append_journal_row(vault, event, machine="journal-test")
    state.write_journal_head_anchor(vault)

    assert trusted_writer.reconcile_journal_export(vault) == 1
    assert trusted_writer.reconcile_journal_export(vault) == 0
    assert list(iter_jsonl(vault / ".memoria/journal/journal-test.jsonl")) == [event, event]


def test_verify_rejects_jsonl_only_event(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    _seed_events(vault, count=1)
    append_jsonl(
        vault / ".memoria/journal/journal-test.jsonl",
        [
            {
                "event": "run",
                "run_id": "forged-export-only",
                "status": "started",
                "timestamp": "2026-07-12T00:00:00+00:00",
                "actor": "operation",
                "machine": "journal-test",
            }
        ],
    )

    report = state.verify_journal_chain(vault)

    assert report["ok"] is False
    assert "JSONL" in report["error"]


def test_verify_rejects_malformed_jsonl(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    _seed_events(vault, count=1)
    path = vault / ".memoria/journal/journal-test.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write("not-json\n")

    report = state.verify_journal_chain(vault)

    assert report["ok"] is False
    assert "invalid JSONL" in report["error"]


def test_verify_rejects_jsonl_event_in_wrong_machine_file(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    _seed_events(vault, count=1)
    event = next(iter_jsonl(vault / ".memoria/journal/journal-test.jsonl"))
    append_jsonl(vault / ".memoria/journal/other-machine.jsonl", [event])

    report = state.verify_journal_chain(vault)

    assert report["ok"] is False
    assert "machine mismatch" in report["error"]


def test_reconcile_rejects_jsonl_only_rows_before_repair(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    db_only = {
        "event": "run",
        "run_id": "needs-repair",
        "status": "started",
        "timestamp": "2026-07-12T00:00:00+00:00",
        "actor": "operation",
        "machine": "journal-test",
    }
    jsonl_only = {
        **db_only,
        "run_id": "forged-export-only",
    }
    state._append_journal_row(vault, db_only, machine="journal-test")
    state.write_journal_head_anchor(vault)
    append_jsonl(vault / ".memoria/journal/journal-test.jsonl", [jsonl_only])

    with pytest.raises(ValueError, match="JSONL export contains"):
        trusted_writer.reconcile_journal_export(vault)

    assert list(iter_jsonl(vault / ".memoria/journal/journal-test.jsonl")) == [jsonl_only]


def test_workspace_scan_repairs_db_only_jsonl_before_other_work(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    event = {
        "event": "run",
        "run_id": "scan-repair",
        "status": "started",
        "timestamp": "2026-07-12T00:00:00+00:00",
        "actor": "operation",
        "machine": "journal-test",
    }
    state._append_journal_row(vault, event, machine="journal-test")
    state.write_journal_head_anchor(vault)

    assert main(["workspace", "scan", "--workspace", str(vault), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["journal_reconciled"] == 1
    assert event in list(iter_jsonl(vault / ".memoria/journal/journal-test.jsonl"))


def test_workspace_scan_repairs_partial_final_jsonl_line(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    _seed_events(vault, count=1)
    path = vault / ".memoria/journal/journal-test.jsonl"
    complete = path.read_bytes()
    path.write_bytes(complete[:-4])

    assert main(["workspace", "scan", "--workspace", str(vault), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["journal_reconciled"] == 1
    assert len(list(iter_jsonl(path))) == 1
    assert state.verify_journal_chain(vault)["ok"] is True


def test_workspace_scan_serializes_journal_verify_and_reconcile(tmp_path, capsys, monkeypatch):
    vault = init_cli_workspace(tmp_path, capsys)
    lock_held = False
    real_lock = cli._workspace_lock
    real_verify = state.verify_journal_chain
    real_reconcile = trusted_writer.reconcile_journal_export

    @contextmanager
    def observed_lock(workspace):
        nonlocal lock_held
        with real_lock(workspace):
            lock_held = True
            try:
                yield
            finally:
                lock_held = False

    def verify(workspace):
        assert lock_held
        return real_verify(workspace)

    def reconcile(workspace):
        assert lock_held
        return real_reconcile(workspace)

    monkeypatch.setattr(cli, "_workspace_lock", observed_lock)
    monkeypatch.setattr(state, "verify_journal_chain", verify)
    monkeypatch.setattr(trusted_writer, "reconcile_journal_export", reconcile)

    assert main(["workspace", "scan", "--workspace", str(vault), "--json"]) == 0
