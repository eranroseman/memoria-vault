"""I1-skeleton: server-side disposition + read-observation events, feedback flag."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_vault.runtime import state, worker
from memoria_vault.runtime.feedback import feedback_production_enabled
from tests.helpers import init_cli_workspace


def _events_with_schema(vault: Path, schema: str) -> list[dict]:
    with state.connect(vault) as conn:
        rows = conn.execute("SELECT payload_json FROM event_log ORDER BY event_id").fetchall()
    payloads = [json.loads(row["payload_json"]) for row in rows]
    return [p for p in payloads if p.get("schema") == schema]


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


def test_doctor_bundle_surfaces_feedback_flag(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    from memoria_vault import cli

    capsys.readouterr()
    cli.main(["doctor", "bundle", "--workspace", str(workspace), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["feedback"] == {"production_enabled": False}
