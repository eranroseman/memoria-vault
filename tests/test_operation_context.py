"""Operation provenance context and actor flows."""

import json
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from memoria_vault.runtime import state, worker
from memoria_vault.runtime.trusted_writer import OperationContext, operation_context_from_job
from tests.helpers import init_cli_workspace


def _operation_job(
    *,
    actor: Any = "agent",
    request_id: Any = "request-1",
    operation_id: Any = "create-concept",
    run_id: Any = None,
) -> dict[str, Any]:
    args = {} if run_id is None else {"run_id": run_id}
    return {
        "job_id": request_id,
        "kind": "operation",
        "operation_id": operation_id,
        "request_envelope": {
            "request_id": request_id,
            "operation_id": operation_id,
            "actor": actor,
            "args": args,
        },
    }


def test_operation_context_is_frozen_and_slotted() -> None:
    context = OperationContext("agent", "run-1", "request-1", "create-concept", "machine")

    assert not hasattr(context, "__dict__")
    with pytest.raises(FrozenInstanceError):
        context.actor = "pi"  # type: ignore[misc]


@pytest.mark.parametrize("envelope", [None, "not-a-mapping", []])
def test_context_rejects_missing_or_non_mapping_envelope(envelope: Any) -> None:
    job = _operation_job()
    job["request_envelope"] = envelope

    with pytest.raises(ValueError, match="request envelope"):
        operation_context_from_job(job, "machine")


@pytest.mark.parametrize("actor", [None, "", " ", "review-agent"])
def test_context_rejects_missing_blank_or_unknown_actor(actor: Any) -> None:
    job = _operation_job(actor=actor)

    with pytest.raises(ValueError, match="actor"):
        operation_context_from_job(job, "machine")


@pytest.mark.parametrize(
    ("location", "key", "value"),
    [
        ("job", "job_id", ""),
        ("job", "job_id", 1),
        ("job", "operation_id", " "),
        ("job", "operation_id", 1),
        ("envelope", "request_id", ""),
        ("envelope", "request_id", 1),
        ("envelope", "operation_id", " "),
        ("envelope", "operation_id", 1),
    ],
)
def test_context_rejects_blank_or_non_string_identifiers(
    location: str, key: str, value: Any
) -> None:
    job = _operation_job()
    target = job if location == "job" else job["request_envelope"]
    target[key] = value

    with pytest.raises(ValueError, match=r"identifier|request|operation"):
        operation_context_from_job(job, "machine")


def test_context_rejects_request_id_mismatch() -> None:
    job = _operation_job()
    job["request_envelope"]["request_id"] = "other-request"

    with pytest.raises(ValueError, match=r"request.*match"):
        operation_context_from_job(job, "machine")


@pytest.mark.parametrize(
    "job",
    [
        {
            **_operation_job(),
            "operation_id": "other-operation",
        },
        {
            "job_id": "request-1",
            "kind": "trusted_write",
            "operation": "trusted-write",
            "request_envelope": {
                "request_id": "request-1",
                "operation_id": "other-operation",
                "actor": "operation",
                "args": {},
            },
        },
    ],
)
def test_context_rejects_operation_id_mismatch(job: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match=r"operation.*match"):
        operation_context_from_job(job, "machine")


def test_context_uses_explicit_run_id() -> None:
    context = operation_context_from_job(_operation_job(run_id="run-2"), "machine")

    assert context.run_id == "run-2"


@pytest.mark.parametrize("run_id", [None, "", " "])
def test_context_falls_back_to_request_id_for_missing_or_blank_run_id(run_id: Any) -> None:
    context = operation_context_from_job(_operation_job(run_id=run_id), "machine")

    assert context.run_id == "request-1"


@pytest.mark.parametrize("run_id", [1, [], {}])
def test_context_rejects_non_string_run_id(run_id: Any) -> None:
    with pytest.raises(ValueError, match="run_id"):
        operation_context_from_job(_operation_job(run_id=run_id), "machine")


def test_context_normalizes_explicit_and_platform_machine_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("memoria_vault.runtime.trusted_writer.platform.node", lambda: "host name")

    explicit = operation_context_from_job(_operation_job(), "agent machine")
    fallback = operation_context_from_job(_operation_job(), None)

    assert explicit.machine == "agent_machine"
    assert fallback.machine == "host_name"


def test_context_builder_failure_records_failed_request_without_mutation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    queued = worker.enqueue_operation(
        workspace,
        "create-concept",
        actor="agent",
        payload={
            "target_path": "notes/invalid-context.md",
            "content": "---\ntype: note\ntitle: Invalid context\ntags: []\nlinks: {}\n---\nBody.\n",
            "concept_type": "note",
        },
        idempotency_key="invalid-context",
    )
    queued["request_envelope"].pop("actor")

    failed = worker._run_claimed_job(workspace, queued, "agent machine")

    assert failed["status"] == "failed"
    assert "actor" in failed["error"]
    assert state.request_job(workspace, "invalid-context")["status"] == "failed"
    assert not (workspace / "notes/invalid-context.md").exists()
    assert not list((workspace / ".memoria/journal").glob("*.jsonl"))
    with state.connect(workspace) as conn:
        assert conn.execute("SELECT COUNT(*) FROM event_log").fetchone()[0] == 0


@pytest.mark.parametrize(
    "call",
    [
        lambda workspace: worker.enqueue_operation(workspace, "analyze-gaps"),
        lambda workspace: worker.enqueue_trusted_write(workspace, "notes/context.md", "content"),
        lambda workspace: __import__(
            "memoria_vault.engine.api", fromlist=["compose_draft"]
        ).compose_draft(workspace, "projects/p/project.md"),
        lambda workspace: __import__(
            "memoria_vault.engine.api", fromlist=["verify_draft"]
        ).verify_draft(workspace, "projects/p/project.md"),
        lambda workspace: __import__(
            "memoria_vault.engine.api", fromlist=["promote_draft_passage"]
        ).promote_draft_passage(
            workspace,
            "projects/p/project.md",
            title="Passage",
            passage="Text",
        ),
        lambda workspace: __import__(
            "memoria_vault.engine.api", fromlist=["run_operation"]
        ).run_operation(workspace, "analyze-gaps", {}),
        lambda workspace: __import__(
            "memoria_vault.engine.api", fromlist=["write_new_concept"]
        ).write_new_concept(
            workspace,
            "note",
            "Context",
            body="Body",
            tags=[],
            extra={"mode": "claim", "claim_text": "Body"},
        ),
        lambda workspace: __import__(
            "memoria_vault.engine.api", fromlist=["resolve_attention"]
        ).resolve_attention(
            workspace,
            "inbox/attention/context.md",
            outcome="apply",
            reason="Because",
        ),
    ],
)
def test_request_creation_interfaces_require_actor(
    tmp_path: Path,
    call: Callable[[Path], Any],
) -> None:
    with pytest.raises(TypeError, match="actor"):
        call(tmp_path)


def test_agent_enveloped_create_concept_lands_agent_actor(tmp_path, capsys) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    from memoria_vault.engine import api as engine_api

    engine_api.run_operation(
        workspace,
        "create-concept",
        {
            "target_path": "notes/actor-test.md",
            "content": (
                "---\ntype: note\ntitle: Actor test\nmode: claim\nclaim_text: x\n---\n\nBody.\n"
            ),
            "concept_type": "note",
        },
        actor="agent",
    )
    with state.connect(workspace) as conn:
        req = conn.execute(
            "SELECT actor FROM operation_requests WHERE operation_id='create-concept'"
        ).fetchone()
        assert req["actor"] == "agent"
        rows = conn.execute(
            "SELECT payload_json FROM event_log"
            " WHERE json_extract(payload_json,'$.operation')='create-concept'"
            "   AND json_extract(payload_json,'$.actor') IS NOT NULL"
        ).fetchall()
    actors = {json.loads(row["payload_json"]).get("actor") for row in rows}
    assert actors, "create-concept journaled no actor-bearing events"
    assert actors == {"agent"}
