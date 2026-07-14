from __future__ import annotations

import json
import multiprocessing
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.vaultio import read_frontmatter
from memoria_vault.runtime.worker import (
    _workspace_lock,
    enqueue_operation,
    enqueue_trusted_write,
    run_next_job,
    run_pending_jobs,
)
from memoria_vault.runtime.worker import (
    main as worker_main,
)
from tests.helpers import git, work_text, write_note
from tests.helpers import worker_workspace as workspace


def note_text() -> str:
    return "---\ntype: note\ntitle: Worker note\ntags: []\nlinks: {}\n---\nBody.\n"


def _claim_workspace_lock(vault: Path, started, acquired) -> None:
    started.put("started")
    with _workspace_lock(vault):
        acquired.put("acquired")


def test_worker_workspace_lock_serializes_processes(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    context = multiprocessing.get_context()
    started = context.Queue()
    acquired = context.Queue()
    process = context.Process(target=_claim_workspace_lock, args=(vault, started, acquired))
    try:
        with _workspace_lock(vault):
            process.start()
            assert started.get(timeout=2) == "started"
            with pytest.raises(queue.Empty):
                acquired.get(timeout=0.2)
        assert acquired.get(timeout=2) == "acquired"
        process.join(timeout=2)
        assert process.exitcode == 0
    finally:
        if process.is_alive():
            process.terminate()
            process.join(timeout=2)


def test_worker_runs_queued_trusted_write_through_writer_and_commits(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    queued = enqueue_trusted_write(
        vault,
        "notes/worker.md",
        note_text(),
        inputs=[{"id": "catalog/sources/source-a/source.md", "sha256": "sha256:abc"}],
        idempotency_key="write-worker",
        actor="operation",
    )

    assert queued["status"] == "pending"
    assert not (vault / "notes/worker.md").exists()

    done = run_next_job(vault, machine="test-machine")

    assert done is not None
    assert done["status"] == "done"
    assert done["outputs"] == ["notes/worker.md"]
    target = vault / "notes/worker.md"
    assert "check_status" not in read_frontmatter(target)
    assert state.concept_check_status(vault, "notes/worker.md") == "checked"
    assert not (vault / ".memoria/staging/notes/worker.md").exists()

    event_log = list(iter_jsonl(vault / ".memoria/journal/test-machine.jsonl"))
    assert [event["event"] for event in event_log] == ["derived", "check-fired"]
    committed = set(git(vault, "show", "--name-only", "--format=", done["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL, "notes/worker.md"}


def test_worker_create_concept_operation_materializes_unchecked(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    queued = enqueue_operation(
        vault,
        "create-concept",
        payload={
            "target_path": "notes/agent.md",
            "content": note_text(),
            "concept_type": "note",
        },
        idempotency_key="agent-create",
        output_intents=[{"id": "notes/agent.md", "kind": "note"}],
        primary_target="notes/agent.md",
        actor="agent",
    )

    done = run_next_job(vault, machine="test-machine")

    assert queued["status"] == "pending"
    assert done is not None
    assert done["status"] == "done"
    assert done["check_status"] == "unchecked"
    target = vault / "notes/agent.md"
    assert "check_status" not in read_frontmatter(target)
    assert state.concept_check_status(vault, "notes/agent.md") == "unchecked"
    committed = set(git(vault, "show", "--name-only", "--format=", done["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL, "notes/agent.md"}


def test_worker_create_concept_rejects_generic_work_bypass(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    enqueue_operation(
        vault,
        "create-concept",
        payload={
            "target_path": "digests/bypass.md",
            "content": work_text("bypass", "Bypass body."),
            "concept_type": "work",
        },
        idempotency_key="agent-create-work",
        output_intents=[{"id": "digests/bypass.md", "kind": "work"}],
        primary_target="digests/bypass.md",
        actor="agent",
    )

    failed = run_next_job(vault, machine="test-machine")

    assert failed is not None
    assert failed["status"] == "failed"
    assert "create-concept concept_type must be one of" in failed["error"]
    assert not (vault / "digests/bypass.md").exists()


def test_enqueue_trusted_write_is_idempotent_across_sqlite_states(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    first = enqueue_trusted_write(
        vault,
        "notes/worker.md",
        note_text(),
        idempotency_key="same-job",
        actor="operation",
    )
    second = enqueue_trusted_write(
        vault,
        "notes/worker.md",
        note_text(),
        idempotency_key="same-job",
        actor="operation",
    )

    assert first == second
    [done] = run_pending_jobs(vault, machine="test-machine")
    assert not (vault / ".memoria/queue").exists()
    after_done = enqueue_trusted_write(
        vault,
        "notes/worker.md",
        note_text(),
        idempotency_key="same-job",
        actor="operation",
    )
    assert after_done["status"] == "done"
    assert after_done["commit"] == done["commit"]


@pytest.mark.parametrize(
    "override",
    [
        {"actor": "agent"},
        {"operation_id": "surface-tensions"},
        {"payload": {"query": "beta"}},
        {"input_refs": []},
        {"output_intents": []},
        {"primary_target": "notes/other.md"},
        {"precondition_hashes": {"notes/input.md": "sha256:different"}},
        {"causal_refs": []},
        {"provenance": {"surface": "different"}},
        {"schedule_id": "different-schedule"},
    ],
)
def test_enqueue_operation_binds_idempotency_to_the_complete_request_identity(
    tmp_path: Path, override: dict[str, object]
) -> None:
    vault = workspace(tmp_path)
    base: dict[str, object] = {
        "operation_id": "answer-query",
        "payload": {"query": "alpha"},
        "idempotency_key": "bound-request",
        "input_refs": ["notes/input.md"],
        "output_intents": [{"id": "notes/output.md", "kind": "answer"}],
        "primary_target": "notes/output.md",
        "precondition_hashes": {"notes/input.md": "sha256:original"},
        "causal_refs": [{"id": "journal:original"}],
        "actor": "pi",
        "provenance": {"surface": "pytest"},
        "schedule_id": "original-schedule",
    }
    first = enqueue_operation(vault, **base)

    assert enqueue_operation(vault, **base) == first

    with pytest.raises(ValueError, match="idempotency key is already bound"):
        enqueue_operation(vault, **(base | override))
    assert state.request_job(vault, "bound-request") == first


def test_enqueue_trusted_write_rejects_reused_key_with_changed_request(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    first = enqueue_trusted_write(
        vault,
        "notes/original.md",
        note_text(),
        idempotency_key="bound-write",
        actor="operation",
    )

    with pytest.raises(ValueError, match="idempotency key is already bound"):
        enqueue_trusted_write(
            vault,
            "notes/original.md",
            note_text() + "Changed.\n",
            idempotency_key="bound-write",
            actor="operation",
        )

    assert state.request_job(vault, "bound-write") == first


def test_enqueue_request_rejects_reused_key_across_job_kinds(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    target = "notes/cross-kind.md"
    content = note_text()
    inputs = ["notes/input.md"]
    first = enqueue_trusted_write(
        vault,
        target,
        content,
        inputs=inputs,
        operation="trusted-write",
        run_id="cross-kind-run",
        idempotency_key="cross-kind",
        actor="agent",
    )

    with pytest.raises(ValueError, match="idempotency key is already bound"):
        enqueue_operation(
            vault,
            "trusted-write",
            payload={
                "target_path": target,
                "content": content,
                "inputs": inputs,
                "run_id": "cross-kind-run",
            },
            idempotency_key="cross-kind",
            input_refs=inputs,
            output_intents=[{"id": target, "kind": "trusted_write"}],
            primary_target=target,
            actor="agent",
            provenance={"surface": "worker"},
        )

    assert state.request_job(vault, "cross-kind") == first


def test_concurrent_conflicting_enqueues_commit_one_request_identity(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    with state.connect(vault):
        pass
    barrier = threading.Barrier(2)

    def enqueue(actor: str) -> tuple[str, str]:
        barrier.wait()
        try:
            job = enqueue_operation(
                vault,
                "answer-query",
                payload={"query": "alpha"},
                idempotency_key="concurrent-bound-request",
                actor=actor,
            )
        except ValueError as exc:
            return "conflict", str(exc)
        return "saved", str(job["request_envelope"]["actor"])

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(enqueue, ("pi", "agent")))

    assert sorted(status for status, _value in results) == ["conflict", "saved"]
    winner = next(value for status, value in results if status == "saved")
    with state.connect(vault) as conn:
        rows = conn.execute(
            "SELECT actor FROM operation_requests WHERE request_id = ?",
            ("concurrent-bound-request",),
        ).fetchall()
    assert [row["actor"] for row in rows] == [winner]


def test_request_identity_distinguishes_json_boolean_from_number(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    first = enqueue_operation(
        vault,
        "answer-query",
        payload={"enabled": True},
        idempotency_key="typed-request",
        actor="pi",
    )

    with pytest.raises(ValueError, match="idempotency key is already bound"):
        enqueue_operation(
            vault,
            "answer-query",
            payload={"enabled": 1},
            idempotency_key="typed-request",
            actor="pi",
        )

    assert state.request_job(vault, "typed-request") == first


def test_request_identity_normalizes_tuples_to_persisted_json_arrays(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    first = enqueue_operation(
        vault,
        "answer-query",
        payload={"terms": ("alpha", "beta")},
        idempotency_key="normalized-request",
        actor="pi",
    )
    retry = enqueue_operation(
        vault,
        "answer-query",
        payload={"terms": ("alpha", "beta")},
        idempotency_key="normalized-request",
        actor="pi",
    )

    assert retry == first
    assert retry["request_envelope"]["args"] == {"terms": ["alpha", "beta"]}


def test_claim_and_supersede_race_has_exactly_one_winner(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    source = enqueue_operation(
        vault,
        "answer-query",
        payload={"query": "original"},
        idempotency_key="race-source",
        actor="pi",
    )
    barrier = threading.Barrier(2)

    def claim() -> str:
        running = {**source, "status": "running", "started_at": state.now_iso()}
        barrier.wait()
        return "claimed" if state.claim_request(vault, "race-source", running) else "not-claimed"

    def supersede() -> str:
        barrier.wait()
        try:
            enqueue_operation(
                vault,
                "answer-query",
                payload={"query": "successor"},
                idempotency_key="race-successor",
                causal_refs=["race-source"],
                actor="pi",
                supersede_request_id="race-source",
            )
        except ValueError:
            return "supersede-conflict"
        return "superseded"

    with ThreadPoolExecutor(max_workers=2) as executor:
        claim_future = executor.submit(claim)
        supersede_future = executor.submit(supersede)
        claim_result = claim_future.result()
        supersede_result = supersede_future.result()

    assert (claim_result, supersede_result) in {
        ("claimed", "supersede-conflict"),
        ("not-claimed", "superseded"),
    }


def test_exact_retry_cannot_supersede_an_unrelated_pending_request(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    existing = enqueue_operation(
        vault,
        "answer-query",
        payload={"query": "existing"},
        idempotency_key="existing-request",
        actor="pi",
    )
    unrelated = enqueue_operation(
        vault,
        "answer-query",
        payload={"query": "unrelated"},
        idempotency_key="unrelated-request",
        actor="pi",
    )

    with pytest.raises(ValueError, match="idempotency key is already bound"):
        enqueue_operation(
            vault,
            "answer-query",
            payload={"query": "existing"},
            idempotency_key="existing-request",
            actor="pi",
            supersede_request_id="unrelated-request",
        )

    assert state.request_job(vault, "existing-request") == existing
    assert state.request_job(vault, "unrelated-request") == unrelated


def test_agent_and_self_supersession_are_rejected_without_mutation(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    source = enqueue_operation(
        vault,
        "answer-query",
        payload={"query": "source"},
        idempotency_key="protected-source",
        actor="pi",
    )

    with pytest.raises(ValueError, match="supersession requires PI actor authority"):
        enqueue_operation(
            vault,
            "answer-query",
            payload={"query": "agent successor"},
            idempotency_key="agent-successor",
            actor="agent",
            supersede_request_id="protected-source",
        )
    with pytest.raises(ValueError, match="cannot supersede itself"):
        enqueue_operation(
            vault,
            "answer-query",
            payload={"query": "source"},
            idempotency_key="protected-source",
            actor="pi",
            supersede_request_id="protected-source",
        )

    assert state.request_job(vault, "protected-source") == source
    assert state.request_job(vault, "agent-successor") is None


def test_worker_runs_prompt_operation_manifest_jobs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    write_note(vault, "claim", "checked", "Claim: Alpha reduces beta.")

    queued = enqueue_operation(
        vault,
        "analyze-claims",
        payload={"input_ref": "notes/claim.md"},
        idempotency_key="analyze-claims",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["output_path"] == "notes/analyze-claims-analyze-claims.md"
    assert done["staging_id"] == (".memoria/staging/notes/analyze-claims-analyze-claims.md")
    assert not (vault / done["staging_id"]).exists()
    materialized = vault / done["output_path"]
    fm = read_frontmatter(materialized)
    assert "check_status" not in fm
    assert state.concept_check_status(vault, done["output_path"]) == "unchecked"
    assert "status" not in fm
    assert "evidence_set" not in fm
    assert "citations" not in fm
    assert "Alpha reduces beta" in materialized.read_text(encoding="utf-8")
    committed = set(git(vault, "show", "--name-only", "--format=", done["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL, done["output_path"]}


def test_worker_cli_enqueues_operation_payload(tmp_path: Path, capsys) -> None:
    vault = workspace(tmp_path)

    rc = worker_main(
        [
            "enqueue-operation",
            "--vault",
            str(vault),
            "--operation-id",
            "answer-query",
            "--payload",
            '{"query":"alpha","k":1}',
            "--idempotency-key",
            "ask-alpha",
            "--actor",
            "agent",
        ]
    )

    assert rc == 0
    output = json.loads(capsys.readouterr().out)
    assert output["job_id"] == "ask-alpha"
    assert output["payload"] == {"query": "alpha", "k": 1}
    assert output["request_envelope"]["actor"] == "agent"


def test_worker_requires_valid_operation_policy_before_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = workspace(tmp_path)

    def reject_invalid_policy(_vault: Path, _operation_id: str) -> dict:
        raise ValueError("answer-query missing operation policy fields: runner")

    monkeypatch.setattr(
        "memoria_vault.runtime.operations.load_operation_policy",
        reject_invalid_policy,
    )

    enqueue_operation(
        vault,
        "answer-query",
        payload={"query": "alpha"},
        idempotency_key="unchecked-policy",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done is not None
    assert done["status"] == "failed"
    assert "answer-query missing operation policy fields: runner" in done["error"]


@pytest.mark.slow
def test_worker_marks_invalid_job_failed_without_bundle_write(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    enqueue_trusted_write(
        vault,
        "notes/bad.md",
        "---\ntype: note\ntags: []\nlinks: {}\n---\nBody.\n",
        idempotency_key="bad-job",
        actor="operation",
    )

    failed = run_next_job(vault, machine="test-machine")

    assert failed is not None
    assert failed["status"] == "failed"
    assert "missing required field: title" in failed["error"]
    assert not (vault / "notes/bad.md").exists()
