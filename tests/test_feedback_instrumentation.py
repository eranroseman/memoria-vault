"""I1-skeleton: server-side disposition + read-observation events, feedback flag."""

from __future__ import annotations

import json
import uuid
from dataclasses import replace
from pathlib import Path

import pytest

from memoria_vault.runtime import state, worker
from memoria_vault.runtime.feedback import feedback_production_enabled
from memoria_vault.runtime.operations import record_empirical_event
from tests.helpers import call_with_context, git, init_cli_workspace, operation_context


def _events_with_schema(vault: Path, schema: str) -> list[dict]:
    with state.connect(vault) as conn:
        rows = conn.execute("SELECT payload_json FROM event_log ORDER BY event_id").fetchall()
    payloads = [json.loads(row["payload_json"]) for row in rows]
    return [p for p in payloads if p.get("schema") == schema]


def _journal_lines(vault: Path) -> dict[str, list[str]]:
    """Every per-machine journal file's raw lines — the writer's own file artifact."""
    return {
        path.name: path.read_text(encoding="utf-8").splitlines()
        for path in sorted((vault / ".memoria/journal").glob("*.jsonl"))
    }


@pytest.mark.parametrize(
    ("outcome", "decision"),
    [("apply", "accept"), ("reject", "reject"), ("defer", "defer")],
)
def test_resolve_attention_emits_disposition(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], outcome: str, decision: str
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    request = worker.enqueue_operation(
        workspace,
        "resolve-attention",
        actor="pi",
        idempotency_key=f"pi-resolve-{outcome}",
        payload={"target_id": "inbox/attention/pi.md", "outcome": outcome, "reason": "PI decision"},
    )

    result = worker.run_request(workspace, request["job_id"], machine="PI laptop")

    assert result["status"] == "done"
    dispositions = _events_with_schema(workspace, "disposition.v1")
    assert len(dispositions) == 1
    assert dispositions[0]["decision"] == decision
    assert dispositions[0]["item_type"] == "attention"
    assert dispositions[0]["item_id"] == "inbox/attention/pi.md"
    assert dispositions[0]["actor"] == "pi"
    # request_id is the join key beta.1 client events will reconcile against.
    assert dispositions[0]["request_id"] == request["job_id"]


def test_acknowledge_attention_emits_no_disposition(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    request = worker.enqueue_operation(
        workspace,
        "acknowledge-attention",
        actor="pi",
        idempotency_key="pi-ack",
        payload={"target_id": "inbox/attention/pi.md", "reason": "ack"},
    )

    worker.run_request(workspace, request["job_id"], machine="PI laptop")

    assert _events_with_schema(workspace, "disposition.v1") == []


def test_feedback_flag_defaults_false_when_absent(tmp_path: Path) -> None:
    assert feedback_production_enabled(tmp_path) is False


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("production_enabled: true\n", True),
        ("production_enabled: false\n", False),
        # A quoted string is not a boolean, so it must not enable (the reader
        # accepts only a real YAML boolean `true`). `yes`/`on` are YAML booleans
        # and legitimately enable, so they are not the interesting case here.
        ('production_enabled: "true"\n', False),
        ("other: 1\n", False),
        ("", False),
        ("- not a map\n", False),
    ],
)
def test_feedback_flag_reads_explicit_true_only(tmp_path: Path, body: str, expected: bool) -> None:
    config = tmp_path / ".memoria/config"
    config.mkdir(parents=True, exist_ok=True)
    (config / "feedback.yaml").write_text(body, encoding="utf-8")
    assert feedback_production_enabled(tmp_path) is expected


def test_record_empirical_event_lands_in_telemetry_and_never_in_the_journal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The storage ruling proven at the *writer* (I1 spec §1, T.3).

    `test_telemetry_events.py` proves the reader side — a raw telemetry insert stays
    invisible to `verify_journal_chain`. That cannot see a writer that records to
    telemetry *and* also journals, so this drives the real writer and pins every
    journal-side artifact the old sink produced: the `event_log` row, the per-machine
    JSONL line, the tracked `.memoria/journal-head` anchor, and the commit.
    """
    workspace = init_cli_workspace(tmp_path, capsys)
    # Upper-cased on purpose: the response must echo the *validated* event, so this
    # also pins that the writer validates before it records rather than leaning on
    # `record_telemetry_event` to do it and returning the raw payload it was handed.
    raw_event_id = str(uuid.uuid4()).upper()
    event = {
        "event_id": raw_event_id,
        "event_type": "view.opened",
        "timestamp": "2026-07-16T00:00:00Z",
        "session_id": "session-alpha",
        "surface": "obsidian",
        "workflow": "attention",
    }
    normalized = {**event, "event_id": str(uuid.UUID(raw_event_id))}
    assert normalized["event_id"] != raw_event_id
    head_before = git(workspace, "rev-parse", "HEAD")
    status_before = git(workspace, "status", "--porcelain")
    anchor_before = (workspace / state.JOURNAL_HEAD_REL).read_bytes()
    journal_before = _journal_lines(workspace)
    with state.connect(workspace) as conn:
        log_before = conn.execute("SELECT COUNT(*) FROM event_log").fetchone()[0]

    result = call_with_context(record_empirical_event, workspace, dict(event))

    assert set(result) == {"event_id", "telemetry_id", "event", "outputs"}
    assert result["event_id"] == normalized["event_id"]
    assert result["telemetry_id"]
    assert result["event"] == normalized
    assert result["outputs"] == []
    with state.connect(workspace) as conn:
        log_after = conn.execute("SELECT COUNT(*) FROM event_log").fetchone()[0]
        empirical_rows = conn.execute(
            "SELECT COUNT(*) FROM event_log WHERE event_type = 'empirical-event'"
        ).fetchone()[0]
        telemetry = conn.execute(
            "SELECT event_id, event_type, session_id, surface, payload_json FROM telemetry_events"
            " WHERE event_type = 'empirical_event.v1'"
        ).fetchall()
    # Journal side: not one row, one line, one anchor byte, or one commit more.
    assert log_after == log_before
    assert empirical_rows == 0
    assert _journal_lines(workspace) == journal_before
    assert (workspace / state.JOURNAL_HEAD_REL).read_bytes() == anchor_before
    assert git(workspace, "rev-parse", "HEAD") == head_before
    assert git(workspace, "status", "--porcelain") == status_before
    assert state.verify_journal_chain(workspace)["ok"] is True
    # Telemetry side: exactly the one row, with the client's own columns kept. Scoped
    # to this event type -- `init_cli_workspace` also records O1's `init-done`
    # onboarding step, and a bare table count would conflate the two namespaces.
    assert len(telemetry) == 1
    assert telemetry[0]["event_id"] == result["telemetry_id"]
    assert telemetry[0]["event_type"] == "empirical_event.v1"
    assert telemetry[0]["session_id"] == "session-alpha"
    assert telemetry[0]["surface"] == "obsidian"
    assert json.loads(telemetry[0]["payload_json"]) == normalized


def test_record_empirical_event_rejects_a_forged_context_before_recording(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The telemetry sink is still behind the trusted-writer context check.

    Moving off the journal moved the sink out from behind `append_journal_event`'s own
    validation, so this is the only thing left proving a forged context cannot record.
    """
    workspace = init_cli_workspace(tmp_path, capsys)
    context = operation_context(workspace, operation_id="empirical-event-record")
    forged = replace(context, request_id="missing-request")
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "view.opened",
        "timestamp": "2026-07-16T00:00:00Z",
        "session_id": "session-alpha",
        "surface": "obsidian",
        "workflow": "attention",
    }

    with pytest.raises(ValueError, match=r"context|request"):
        record_empirical_event(workspace, event, context=forged)

    with state.connect(workspace) as conn:
        # Scoped to this writer's own event type: the workspace's `init-done`
        # onboarding step (O1 T.2) is a different producer and must not mask a
        # forged-context row landing here.
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM telemetry_events WHERE event_type = 'empirical_event.v1'"
            ).fetchone()[0]
            == 0
        )


def test_doctor_bundle_surfaces_feedback_flag(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    from memoria_vault import cli

    capsys.readouterr()
    cli.main(["doctor", "bundle", "--workspace", str(workspace), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["feedback"] == {"production_enabled": False}
