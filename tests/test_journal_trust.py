"""Journal-chain, export-reconciliation, and authoritative-read contracts."""

from __future__ import annotations

import json

from memoria_vault.cli import main
from memoria_vault.runtime import state, trusted_writer
from tests.helpers import init_cli_workspace


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
