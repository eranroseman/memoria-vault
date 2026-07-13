"""Operation provenance context and actor flows."""

import inspect
import json
from collections.abc import Callable
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import Any

import pytest

from memoria_vault.runtime import state, trusted_writer, worker
from memoria_vault.runtime.jsonl import iter_jsonl
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


def _saved_operation_context(
    vault: Path,
    *,
    provenance: dict[str, Any] | None = None,
) -> OperationContext:
    context = OperationContext(
        actor="agent",
        run_id="run-1",
        request_id="request-1",
        operation_id="create-concept",
        machine="agent_machine",
    )
    envelope = state.request_envelope(
        request_id=context.request_id,
        operation_id=context.operation_id,
        actor=context.actor,
        provenance=provenance or {},
    )
    state.save_request(
        vault,
        envelope,
        {
            "job_id": context.request_id,
            "kind": "operation",
            "operation_id": context.operation_id,
            "bound_context": {
                "actor": context.actor,
                "run_id": context.run_id,
                "request_id": context.request_id,
                "operation_id": context.operation_id,
                "machine": context.machine,
            },
        },
    )
    return context


def _event_log_payloads(vault: Path) -> list[dict[str, Any]]:
    with state.connect(vault) as conn:
        rows = conn.execute("SELECT payload_json FROM event_log ORDER BY event_id").fetchall()
    return [json.loads(row["payload_json"]) for row in rows]


def _note_content(title: str) -> str:
    return (
        "---\n"
        "type: note\n"
        f"title: {title}\n"
        "mode: claim\n"
        f"claim_text: {title}\n"
        "tags: []\n"
        "links: {}\n"
        "---\n\n"
        f"{title}.\n"
    )


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


def test_context_journal_metadata_comes_from_context_and_saved_request(tmp_path: Path) -> None:
    context = _saved_operation_context(
        tmp_path,
        provenance={"agent_identity": "codex", "surface": "mcp"},
    )

    row = trusted_writer.append_journal_event(
        tmp_path,
        {"event": "derived", "output_id": "notes/context.md"},
        context=context,
    )

    assert row == {
        "event": "derived",
        "output_id": "notes/context.md",
        "actor": "agent",
        "run_id": "run-1",
        "request_id": "request-1",
        "operation": "create-concept",
        "machine": "agent_machine",
        "request_provenance": {"agent_identity": "codex", "surface": "mcp"},
        "timestamp": row["timestamp"],
    }
    jsonl_rows = list(iter_jsonl(tmp_path / ".memoria/journal/agent_machine.jsonl"))
    assert jsonl_rows == [row]
    assert _event_log_payloads(tmp_path) == [row]
    with state.connect(tmp_path) as conn:
        assert conn.execute("SELECT machine FROM event_log").fetchone()["machine"] == row["machine"]


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("actor", None),
        ("run_id", ""),
        ("request_id", "other-request"),
        ("operation", None),
        ("machine", "other_machine"),
    ],
)
def test_context_journal_reserved_metadata_conflict_changes_neither_store(
    tmp_path: Path,
    key: str,
    value: Any,
) -> None:
    context = _saved_operation_context(tmp_path)

    with pytest.raises(ValueError, match=key):
        trusted_writer.append_journal_event(
            tmp_path,
            {"event": "derived", key: value},
            context=context,
        )

    assert not list((tmp_path / ".memoria/journal").glob("*.jsonl"))
    assert _event_log_payloads(tmp_path) == []


def test_context_journal_request_provenance_conflict_changes_neither_store(
    tmp_path: Path,
) -> None:
    context = _saved_operation_context(tmp_path, provenance={"agent_identity": "codex"})

    with pytest.raises(ValueError, match="request_provenance"):
        trusted_writer.append_journal_event(
            tmp_path,
            {"event": "derived", "request_provenance": None},
            context=context,
        )

    assert not list((tmp_path / ".memoria/journal").glob("*.jsonl"))
    assert _event_log_payloads(tmp_path) == []


def test_context_journal_rejects_non_mapping_request_provenance_before_mutation(
    tmp_path: Path,
) -> None:
    context = OperationContext(
        actor="agent",
        run_id="run-1",
        request_id="request-1",
        operation_id="create-concept",
        machine="agent_machine",
    )
    envelope = state.request_envelope(
        request_id=context.request_id,
        operation_id=context.operation_id,
        actor=context.actor,
    )
    envelope["provenance"] = None
    state.save_request(
        tmp_path,
        envelope,
        {
            "job_id": context.request_id,
            "kind": "operation",
            "operation_id": context.operation_id,
            "bound_context": {
                "actor": context.actor,
                "run_id": context.run_id,
                "request_id": context.request_id,
                "operation_id": context.operation_id,
                "machine": context.machine,
            },
        },
    )

    with pytest.raises(ValueError, match=r"provenance.*mapping"):
        trusted_writer.append_journal_event(
            tmp_path,
            {"event": "derived"},
            context=context,
        )

    assert not list((tmp_path / ".memoria/journal").glob("*.jsonl"))
    assert _event_log_payloads(tmp_path) == []


@pytest.mark.parametrize(
    ("actor", "machine", "match"),
    [
        ("bogus", "agent machine", "actor"),
        ("pi", "", "machine"),
        ("pi", " ", "machine"),
    ],
)
def test_explicit_journal_rejects_invalid_actor_or_blank_machine_without_mutation(
    tmp_path: Path,
    actor: str,
    machine: str,
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        trusted_writer.append_explicit_journal_event(
            tmp_path,
            {"event": "manual"},
            actor=actor,
            machine=machine,
        )

    assert not list((tmp_path / ".memoria/journal").glob("*.jsonl"))
    assert _event_log_payloads(tmp_path) == []


@pytest.mark.parametrize(
    ("key", "value"),
    [("actor", None), ("actor", "agent"), ("machine", None), ("machine", "other")],
)
def test_explicit_journal_metadata_conflict_changes_neither_store(
    tmp_path: Path,
    key: str,
    value: Any,
) -> None:
    with pytest.raises(ValueError, match=key):
        trusted_writer.append_explicit_journal_event(
            tmp_path,
            {"event": "manual", key: value},
            actor="pi",
            machine="PI laptop",
        )

    assert not list((tmp_path / ".memoria/journal").glob("*.jsonl"))
    assert _event_log_payloads(tmp_path) == []


def test_explicit_journal_machine_is_normalized_once_across_both_stores(
    tmp_path: Path,
) -> None:
    row = trusted_writer.append_explicit_journal_event(
        tmp_path,
        {"event": "manual"},
        actor="pi",
        machine="PI laptop",
    )

    assert row["actor"] == "pi"
    assert row["machine"] == "PI_laptop"
    assert list(iter_jsonl(tmp_path / ".memoria/journal/PI_laptop.jsonl")) == [row]
    assert _event_log_payloads(tmp_path) == [row]
    with state.connect(tmp_path) as conn:
        assert conn.execute("SELECT machine FROM event_log").fetchone()["machine"] == "PI_laptop"


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


def test_worker_binds_exact_context_to_running_request_before_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queued = worker.enqueue_operation(
        tmp_path,
        "test-bound-context",
        payload={"run_id": "bound-run"},
        idempotency_key="bound-request",
        actor="agent",
    )
    seen: dict[str, Any] = {}

    def inspect_dispatch(
        vault: Path, job: dict[str, Any], context: OperationContext
    ) -> dict[str, Any]:
        persisted = state.request_job(vault, context.request_id)
        assert persisted is not None
        assert persisted["status"] == "running"
        assert persisted["bound_context"] == trusted_writer.operation_context_record(context)
        seen["bound_context"] = persisted["bound_context"]
        return {}

    monkeypatch.setattr(worker, "_run_job", inspect_dispatch)

    result = worker.run_request(tmp_path, queued["job_id"], machine="agent laptop")

    assert result["status"] == "done"
    assert seen["bound_context"] == {
        "actor": "agent",
        "run_id": "bound-run",
        "request_id": "bound-request",
        "operation_id": "test-bound-context",
        "machine": "agent_laptop",
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("actor", "integrity"),
        ("run_id", "forged-run"),
        ("request_id", "missing-request"),
        ("operation_id", "forged-operation"),
        ("machine", "forged-machine"),
    ],
)
def test_forged_or_nonexistent_context_rejected_without_journal_mutation(
    tmp_path: Path,
    field: str,
    value: str,
) -> None:
    context = _saved_operation_context(tmp_path)
    forged = replace(context, **{field: value})

    with pytest.raises(ValueError, match=r"context|request"):
        trusted_writer.append_journal_event(
            tmp_path,
            {"event": "derived", "output_id": "notes/forged.md"},
            context=forged,
        )

    assert not list((tmp_path / ".memoria/journal").glob("*.jsonl"))
    assert _event_log_payloads(tmp_path) == []


def test_stage_rejects_forged_context_before_file_or_database_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    context = _saved_operation_context(workspace)
    forged = replace(context, actor="integrity")

    with pytest.raises(ValueError, match="context"):
        trusted_writer.stage_concept(
            workspace,
            "notes/forged-stage.md",
            _note_content("Forged stage"),
            context=forged,
        )

    assert not (workspace / ".memoria/staging/notes/forged-stage.md").exists()
    with state.connect(workspace) as conn:
        assert conn.execute("SELECT COUNT(*) FROM outputs").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM derivations").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM event_log").fetchone()[0] == 0
    assert not list((workspace / ".memoria/journal").glob("*.jsonl"))


def test_materialize_rejects_nonexistent_context_before_move(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    context = _saved_operation_context(workspace)
    trusted_writer.stage_concept(
        workspace,
        "notes/materialize-boundary.md",
        _note_content("Materialize boundary"),
        context=context,
    )
    staging = workspace / ".memoria/staging/notes/materialize-boundary.md"
    missing = replace(context, request_id="missing-request")

    with pytest.raises(ValueError, match="request"):
        trusted_writer.materialize_unchecked(
            workspace,
            "notes/materialize-boundary.md",
            context=missing,
        )

    assert staging.is_file()
    assert not (workspace / "notes/materialize-boundary.md").exists()


def test_quarantine_rejects_nonexistent_context_before_move_or_state_change(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    target = workspace / "notes/quarantine-boundary.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_note_content("Quarantine boundary"), encoding="utf-8")
    missing = OperationContext(
        "integrity", "scan-run", "missing-request", "trace-integrity-scan", "scanner"
    )

    with pytest.raises(ValueError, match="request"):
        trusted_writer.quarantine_untraced(
            workspace,
            ["notes/quarantine-boundary.md"],
            context=missing,
        )

    assert target.is_file()
    assert not (workspace / ".memoria/quarantine/notes/quarantine-boundary.md").exists()
    with state.connect(workspace) as conn:
        assert conn.execute("SELECT COUNT(*) FROM event_log").fetchone()[0] == 0


def test_commit_rejects_nonexistent_context_before_git_or_anchor_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    target = workspace / "scratch.txt"
    target.write_text("uncommitted\n", encoding="utf-8")
    before_head = worker.subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=workspace,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    missing = OperationContext(
        "operation", "commit-run", "missing-request", "test-commit", "writer"
    )

    with pytest.raises(ValueError, match="request"):
        trusted_writer.commit_writer_changes(
            workspace,
            "must not commit",
            ["scratch.txt"],
            context=missing,
        )

    after_head = worker.subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=workspace,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    assert after_head == before_head
    assert target.is_file()


def test_projection_rejects_nonexistent_context_before_write(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from memoria_vault.runtime.projections import write_workspace_indexes

    workspace = init_cli_workspace(tmp_path, capsys)
    index = workspace / "index.md"
    index.write_text("sentinel\n", encoding="utf-8")
    missing = OperationContext(
        "operation", "projection-run", "missing-request", "projection", "writer"
    )

    with pytest.raises(ValueError, match="request"):
        write_workspace_indexes(workspace, context=missing)

    assert index.read_text(encoding="utf-8") == "sentinel\n"


def test_explicit_scan_propagation_rejects_blank_machine_at_entry(tmp_path: Path) -> None:
    from memoria_vault.runtime.integrity import propagate_scan_demotion_explicit

    with pytest.raises(ValueError, match="machine"):
        propagate_scan_demotion_explicit(
            tmp_path,
            "notes/source.md",
            reason="test",
            actor="integrity",
            machine=" ",
        )


def test_explicit_pi_observation_rejects_blank_machine_before_database_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    target = workspace / "notes/blank-machine.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_note_content("Blank machine"), encoding="utf-8")

    with pytest.raises(ValueError, match="machine"):
        trusted_writer.observe_pi_edit(
            workspace,
            "notes/blank-machine.md",
            "sha256:prior",
            machine=" ",
        )

    with state.connect(workspace) as conn:
        assert conn.execute("SELECT COUNT(*) FROM outputs").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM concept_verdicts").fetchone()[0] == 0
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


@pytest.mark.parametrize(
    ("function", "required", "forbidden"),
    [
        (trusted_writer.append_journal_event, {"context"}, {"actor", "machine"}),
        (trusted_writer.stage_concept, {"context"}, {"actor", "machine", "run_id", "operation"}),
        (trusted_writer.mark_checked, {"context"}, {"actor", "machine"}),
        (trusted_writer.promote_checked, {"context"}, {"actor", "machine"}),
        (trusted_writer.materialize_unchecked, {"context"}, {"actor", "machine"}),
        (trusted_writer.quarantine_untraced, {"context"}, {"actor", "machine"}),
        (trusted_writer.quarantine_untraced_from_status, {"context"}, {"actor", "machine"}),
        (trusted_writer.commit_writer_changes, {"context"}, {"actor", "machine"}),
    ],
)
def test_request_writer_interfaces_require_only_context_provenance(
    function: Callable[..., Any], required: set[str], forbidden: set[str]
) -> None:
    signature = inspect.signature(function)

    for name in required:
        parameter = signature.parameters[name]
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is inspect.Parameter.empty
    assert forbidden.isdisjoint(signature.parameters)


@pytest.mark.parametrize(
    ("function", "required"),
    [
        (trusted_writer.append_explicit_journal_event, {"actor", "machine"}),
        (trusted_writer.commit_explicit_writer_changes, {"actor", "machine"}),
        (trusted_writer.observe_pi_edit, {"machine"}),
        (trusted_writer.observe_pi_edit_from_head, {"machine"}),
        (trusted_writer.observe_pi_edits_explicit_from_status, {"actor", "machine"}),
    ],
)
def test_outside_envelope_writer_interfaces_require_explicit_provenance(
    function: Callable[..., Any], required: set[str]
) -> None:
    signature = inspect.signature(function)

    for name in required:
        parameter = signature.parameters[name]
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is inspect.Parameter.empty
    assert "context" not in signature.parameters


def _run_input_backed_create(
    workspace: Path,
    *,
    actor: str,
    request_id: str,
    title: str,
) -> dict[str, Any]:
    target = "notes/context-owned.md"
    queued = worker.enqueue_operation(
        workspace,
        "create-concept",
        actor=actor,
        idempotency_key=request_id,
        input_refs=[{"id": "catalog/sources/source-a/source.md", "role": "source"}],
        output_intents=[{"id": target, "kind": "concept"}],
        primary_target=target,
        payload={
            "target_path": target,
            "content": _note_content(title),
            "concept_type": "note",
            "run_id": f"run-{request_id}",
        },
    )
    return worker.run_request(workspace, queued["job_id"], machine="agent machine")


@pytest.mark.parametrize("actor", ["agent", "operation", "integrity"])
def test_create_concept_preserves_context_end_to_end(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    actor: str,
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    request_id = f"create-{actor}"

    result = _run_input_backed_create(
        workspace,
        actor=actor,
        request_id=request_id,
        title=f"Context {actor}",
    )

    assert result["status"] == "done"
    with state.connect(workspace) as conn:
        request = conn.execute(
            "SELECT actor FROM operation_requests WHERE request_id = ?", (request_id,)
        ).fetchone()
        derivations = conn.execute(
            "SELECT input_id, output_id, actor FROM derivations"
            " WHERE output_id = 'notes/context-owned.md'"
        ).fetchall()
        event_rows = conn.execute(
            "SELECT machine, payload_json FROM event_log"
            " WHERE json_extract(payload_json, '$.request_id') = ?",
            (request_id,),
        ).fetchall()
    assert request["actor"] == actor
    assert [tuple(row) for row in derivations] == [
        ("catalog/sources/source-a/source.md", "notes/context-owned.md", actor)
    ]
    assert event_rows
    for event_row in event_rows:
        event = json.loads(event_row["payload_json"])
        assert event["actor"] == actor
        assert event["run_id"] == f"run-{request_id}"
        assert event["request_id"] == request_id
        assert event["operation"] == "create-concept"
        assert event["machine"] == "agent_machine"
        assert event_row["machine"] == "agent_machine"
    journal = list(iter_jsonl(workspace / ".memoria/journal/agent_machine.jsonl"))
    assert [row for row in journal if row.get("request_id") == request_id] == [
        json.loads(row["payload_json"]) for row in event_rows
    ]


def test_repeated_edge_keeps_latest_actor_and_both_historical_events(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)

    first = _run_input_backed_create(
        workspace, actor="pi", request_id="repeat-pi", title="PI version"
    )
    second = _run_input_backed_create(
        workspace, actor="agent", request_id="repeat-agent", title="Agent version"
    )

    assert first["status"] == second["status"] == "done"
    with state.connect(workspace) as conn:
        derivations = conn.execute(
            "SELECT actor FROM derivations"
            " WHERE input_id = 'catalog/sources/source-a/source.md'"
            " AND output_id = 'notes/context-owned.md'"
        ).fetchall()
        events = conn.execute(
            "SELECT payload_json FROM event_log"
            " WHERE json_extract(payload_json, '$.event') = 'derived'"
            " AND json_extract(payload_json, '$.output_id') = 'notes/context-owned.md'"
            " ORDER BY event_id"
        ).fetchall()
    assert [row["actor"] for row in derivations] == ["agent"]
    history = [json.loads(row["payload_json"]) for row in events]
    assert [(row["request_id"], row["actor"]) for row in history] == [
        ("repeat-pi", "pi"),
        ("repeat-agent", "agent"),
    ]


@pytest.mark.parametrize("operation_id", ["acknowledge-attention", "resolve-attention"])
def test_attention_resolution_rejects_non_pi_before_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    operation_id: str,
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    target = "inbox/attention/non-pi.md"
    request = worker.enqueue_operation(
        workspace,
        operation_id,
        actor="agent",
        idempotency_key=f"agent-{operation_id}",
        payload={"target_id": target, "reason": "agent may not decide"},
    )

    result = worker.run_request(workspace, request["job_id"], machine="agent machine")

    assert result["status"] == "failed"
    assert "PI" in result["error"]
    assert not (workspace / target).exists()
    assert not [row for row in _event_log_payloads(workspace) if row.get("event") == "resolved"]


@pytest.mark.parametrize("operation_id", ["acknowledge-attention", "resolve-attention"])
def test_attention_resolution_accepts_pi_and_records_pi(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    operation_id: str,
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    request = worker.enqueue_operation(
        workspace,
        operation_id,
        actor="pi",
        idempotency_key=f"pi-{operation_id}",
        payload={"target_id": "inbox/attention/pi.md", "reason": "PI decision"},
    )

    result = worker.run_request(workspace, request["job_id"], machine="PI laptop")

    assert result["status"] == "done"
    assert result["resolution"]["actor"] == "pi"
    assert result["resolution"]["request_id"] == request["job_id"]


def test_scheduled_sweep_requests_declare_integrity_actor(tmp_path: Path) -> None:
    jobs = worker.enqueue_integrity_sweep(tmp_path, sweep_id="scheduled-actor")

    assert jobs
    assert {job["request_envelope"]["actor"] for job in jobs} == {"integrity"}
    with state.connect(tmp_path) as conn:
        actors = conn.execute(
            "SELECT DISTINCT actor FROM operation_requests WHERE schedule_id = ?",
            ("scheduled-actor",),
        ).fetchall()
    assert [row["actor"] for row in actors] == ["integrity"]


def test_read_barrier_scan_request_row_declares_integrity_actor(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from memoria_vault.runtime.read_barrier import is_consumable_checked_file

    workspace = init_cli_workspace(tmp_path, capsys)
    worker.enqueue_trusted_write(
        workspace,
        "notes/read-barrier.md",
        _note_content("Read barrier"),
        idempotency_key="read-barrier-write",
        actor="operation",
    )
    worker.run_next_job(workspace, machine="writer")
    path = workspace / "notes/read-barrier.md"
    path.write_text(path.read_text(encoding="utf-8") + "\nExternal edit.\n", encoding="utf-8")

    assert is_consumable_checked_file(workspace, "notes/read-barrier.md") is False

    with state.connect(workspace) as conn:
        row = conn.execute(
            """
            SELECT operation_id, actor, schedule_id
            FROM operation_requests
            WHERE schedule_id = 'read-guard'
            """
        ).fetchone()
    assert tuple(row) == ("observe-pi-edits", "integrity", "read-guard")


def test_observe_pi_edits_rejects_non_integrity_request_before_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    request = worker.enqueue_operation(
        workspace,
        "observe-pi-edits",
        idempotency_key="pi-scan-authority",
        actor="pi",
    )

    result = worker.run_request(workspace, request["job_id"], machine="scanner")

    assert result["status"] == "failed"
    assert "integrity" in result["error"]
    assert not list((workspace / ".memoria/journal").glob("*.jsonl"))
    with state.connect(workspace) as conn:
        assert conn.execute("SELECT COUNT(*) FROM event_log").fetchone()[0] == 0


def test_integrity_scan_keeps_nested_external_edit_actor_pi(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    worker.enqueue_trusted_write(
        workspace,
        "notes/nested-pi.md",
        _note_content("Nested PI"),
        idempotency_key="nested-pi-write",
        actor="operation",
    )
    worker.run_next_job(workspace, machine="writer")
    path = workspace / "notes/nested-pi.md"
    path.write_text(path.read_text(encoding="utf-8") + "\nPI edit.\n", encoding="utf-8")
    request = worker.enqueue_operation(
        workspace,
        "observe-pi-edits",
        idempotency_key="nested-pi-scan",
        actor="integrity",
    )

    result = worker.run_request(workspace, request["job_id"], machine="scanner")

    assert result["status"] == "done"
    with state.connect(workspace) as conn:
        request_actor = conn.execute(
            "SELECT actor FROM operation_requests WHERE request_id = 'nested-pi-scan'"
        ).fetchone()["actor"]
        payloads = [
            json.loads(row["payload_json"])
            for row in conn.execute(
                "SELECT payload_json FROM event_log WHERE event_type = 'observed_external_edit'"
            )
        ]
    assert request_actor == "integrity"
    assert len(payloads) == 1
    assert payloads[0]["actor"] == "pi"
    assert payloads[0]["operation"] == "observe-pi-edits"
