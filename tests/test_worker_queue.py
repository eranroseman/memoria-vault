from __future__ import annotations

import json
import multiprocessing
import queue
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.policy.audit import sha256_file
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
from tests.helpers import copy_memoria_dirs, git, init_git


def workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas", "config")
    init_git(tmp_path, "worker@example.invalid", "Alpha Worker")
    git(tmp_path, "add", ".memoria/schemas", ".memoria/config")
    git(tmp_path, "commit", "-m", "seed worker workspace")
    return tmp_path


def note_text(status: str = "checked") -> str:
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


def work_text(title: str, body: str) -> str:
    return (
        f"---\ntype: digest\ntitle: {title}\ntags: []\nlinks: {{}}\nwork_id: {title}\n---\n{body}\n"
    )


def write_note(vault: Path, name: str, status: str, body: str) -> Path:
    path = vault / "notes" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\ntype: note\ntitle: {name}\ntags: []\nlinks: {{}}\n---\n{body}\n",
        encoding="utf-8",
    )
    state.record_observed_file_edit(
        vault,
        output_id=path.relative_to(vault).as_posix(),
        concept_type="note",
        output_sha256=sha256_file(path),
    )
    state.set_concept_verdict(vault, path.relative_to(vault).as_posix(), status)
    return path


def test_worker_runs_queued_trusted_write_through_writer_and_commits(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    queued = enqueue_trusted_write(
        vault,
        "notes/worker.md",
        note_text(status="checked"),
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
            "content": note_text(status="unchecked"),
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
    assert not (vault / done["output_path"]).exists()
    staged = vault / done["staging_id"]
    fm = read_frontmatter(staged)
    assert "check_status" not in fm
    assert state.concept_check_status(vault, done["output_path"]) == "unchecked"
    assert "status" not in fm
    assert "evidence_set" not in fm
    assert "citations" not in fm
    assert "Alpha reduces beta" in staged.read_text(encoding="utf-8")
    committed = set(git(vault, "show", "--name-only", "--format=", done["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL, done["staging_id"]}


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
