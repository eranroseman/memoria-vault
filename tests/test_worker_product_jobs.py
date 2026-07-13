from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.capture import (
    capture_bibtex_source as _capture_bibtex_source,
)
from memoria_vault.runtime.capture import (
    capture_source as _capture_source,
)
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.projections import (
    write_tracked_projections as _write_tracked_projections,
)
from memoria_vault.runtime.search_index import answer_query as _answer_query
from memoria_vault.runtime.trusted_writer import (
    commit_writer_changes as _commit_writer_changes,
)
from memoria_vault.runtime.trusted_writer import (
    mark_checked as _mark_checked,
)
from memoria_vault.runtime.trusted_writer import (
    observe_pi_edit,
)
from memoria_vault.runtime.vaultio import read_frontmatter
from memoria_vault.runtime.worker import (
    enqueue_integrity_sweep,
    enqueue_operation,
    enqueue_trusted_write,
    run_integrity_sweep,
    run_next_job,
)
from tests.helpers import (
    WORKSPACE_SEED,
    call_with_context,
    copy_memoria_dirs,
    git,
    init_git,
    mark_file_status,
)


def capture_source(vault: Path, *args, **kwargs):
    return call_with_context(_capture_source, vault, *args, **kwargs)


def capture_bibtex_source(vault: Path, *args, **kwargs):
    return call_with_context(_capture_bibtex_source, vault, *args, **kwargs)


def mark_checked(vault: Path, *args, **kwargs):
    return call_with_context(_mark_checked, vault, *args, **kwargs)


def commit_writer_changes(vault: Path, *args, **kwargs):
    return call_with_context(_commit_writer_changes, vault, *args, **kwargs)


def write_tracked_projections(vault: Path, *args, **kwargs):
    return call_with_context(_write_tracked_projections, vault, *args, **kwargs)


def answer_query(vault: Path, *args, **kwargs):
    return call_with_context(_answer_query, vault, *args, **kwargs)


def workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas", "config")
    init_git(tmp_path, "worker@example.invalid", "Alpha Worker")
    git(tmp_path, "add", ".memoria/schemas", ".memoria/config")
    git(tmp_path, "commit", "-m", "seed worker workspace")
    return tmp_path


def note_text(status: str = "checked") -> str:
    return "---\ntype: note\ntitle: Worker note\ntags: []\nlinks: {}\n---\nBody.\n"


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


def test_worker_runs_digest_and_note_construction_operation_jobs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Alpha content about framing, methods, outcomes, gaps, and impact.",
        machine="capture-machine",
    )

    digest_job = enqueue_operation(
        vault,
        "compile-source-digest",
        payload={
            "work_id": "source-alpha",
            "hub_topics": ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
            "run_id": "compile-alpha",
            "mode": "live",
        },
        idempotency_key="compile-alpha",
        actor="operation",
    )
    digest_done = run_next_job(vault, machine="test-machine")

    assert digest_job["kind"] == "operation"
    assert digest_done is not None
    assert digest_done["status"] == "done"
    assert digest_done["digest_path"] == "digests/source-alpha.md"
    assert "check_status" not in read_frontmatter(vault / digest_done["digest_path"])
    assert state.concept_check_status(vault, digest_done["digest_path"]) == "checked"
    events = list(iter_jsonl(vault / ".memoria/journal/test-machine.jsonl"))
    model_call = next(event for event in events if event["event"] == "model_call")
    assert model_call["mode"] == "live"
    assert model_call["provider"] == "gateway"
    assert set(digest_done["hub_paths"]) == {
        "hubs/framing.md",
        "hubs/methods.md",
        "hubs/outcomes.md",
        "hubs/gaps.md",
        "hubs/impact.md",
    }

    note_job = enqueue_operation(
        vault,
        "propose-note-candidates",
        payload={
            "digest_path": digest_done["digest_path"],
            "candidates": [
                {
                    "title": "Framing changes the question",
                    "body": "The source reframes the problem before measuring outcomes.",
                    "claim_text": "Framing changes which outcomes matter.",
                    "tags": ["Framing"],
                }
            ],
            "run_id": "notes-alpha",
        },
        idempotency_key="notes-alpha",
        actor="pi",
    )
    note_done = run_next_job(vault, machine="test-machine")

    assert note_job["kind"] == "operation"
    assert note_done is not None
    assert note_done["status"] == "done", note_done
    [note_rel] = note_done["note_paths"]
    note_fm = read_frontmatter(vault / note_rel)
    assert "check_status" not in note_fm
    assert state.concept_check_status(vault, note_rel) == "checked"
    assert "status" not in note_fm
    assert state.note_curation_status(vault, note_rel) == "candidate"
    assert note_fm["work_id"] == "catalog/sources/source-alpha"

    curate_job = enqueue_operation(
        vault,
        "curate-note-candidate",
        payload={"note_path": note_rel, "status": "accepted", "reason": "PI approved"},
        idempotency_key="curate-note-alpha",
        actor="operation",
    )
    curate_done = run_next_job(vault, machine="test-machine")

    assert curate_job["kind"] == "operation"
    assert curate_done is not None
    assert curate_done["status"] == "done"
    assert curate_done["note_path"] == note_rel
    assert curate_done["curation_status"] == "accepted"
    assert "status" not in read_frontmatter(vault / note_rel)
    assert state.note_curation_status(vault, note_rel) == "accepted"

    target_note = write_note(vault, "linked-target", "checked", "Target body.")
    link_job = enqueue_operation(
        vault,
        "curate-note-link",
        payload={
            "source_note_path": note_rel,
            "link_type": "supports",
            "target_path": target_note.relative_to(vault).as_posix(),
            "reason": "PI linked notes",
        },
        idempotency_key="link-note-alpha",
        actor="pi",
    )
    link_done = run_next_job(vault, machine="test-machine")

    assert link_job["kind"] == "operation"
    assert link_done is not None
    assert link_done["status"] == "done"
    assert link_done["source_note_path"] == note_rel
    assert link_done["target_path"] == "notes/linked-target.md"
    assert link_done["link_type"] == "supports"
    assert read_frontmatter(vault / note_rel)["links"] == {"supports": ["notes/linked-target.md"]}


def test_worker_records_copi_interview_operation_jobs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Alpha content about methods.",
        machine="capture-machine",
    )

    queued = enqueue_operation(
        vault,
        "record-copi-interview",
        payload={
            "work_id": "source-alpha",
            "prompt": "What matters?",
            "response": "The PI cares about the methods caveat.",
            "project_id": "projects/project-alpha/project.md",
        },
        idempotency_key="copi-interview-alpha",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["work_id"] == "source-alpha"
    assert done["turn_id"].startswith("journal:copi-interview:")
    events = list(iter_jsonl(vault / ".memoria/journal/test-machine.jsonl"))
    assert events[-1]["event"] == "copi-interview"
    assert events[-1]["work_id"] == "source-alpha"
    assert events[-1]["response"] == "The PI cares about the methods caveat."
    committed = set(git(vault, "show", "--name-only", "--format=", done["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL}


def test_worker_runs_gap_analysis_operation_jobs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    (vault / "catalog/sources/source-alpha").mkdir(parents=True)
    (vault / "catalog/sources/source-alpha/source.md").write_text(
        "---\n"
        "type: source\n"
        "check_status: checked\n"
        "title: Alpha\n"
        "description: Alpha\n"
        "tags: [sleep]\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    state.upsert_catalog_record(
        vault,
        work_id="db-alpha",
        title="DB Alpha",
        text_status="full-text",
        check_status="checked",
        csl_json={"memoria": {"topics": ["catalog-only"]}},
    )
    state.upsert_catalog_record(
        vault,
        work_id="metadata-only",
        title="Metadata Only",
        text_status="metadata-only",
        check_status="checked",
    )
    (vault / "digests").mkdir(parents=True)
    (vault / "digests/source-alpha.md").write_text(
        "---\n"
        "type: digest\n"
        "title: Alpha digest\n"
        "description: Alpha\n"
        "tags: [sleep]\n"
        "links: {}\n"
        "work_id: catalog/sources/source-alpha\n"
        "---\n"
        "Neural retrieval improves durable memory systems.\n"
        "Neural retrieval also changes review timing.\n",
        encoding="utf-8",
    )
    mark_file_status(vault, "digests/source-alpha.md", "digest")

    queued = enqueue_operation(
        vault,
        "analyze-gaps",
        payload={"seed_terms": ["new area"], "dense_threshold": 1},
        idempotency_key="gap-analysis",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    gaps = {gap["topic"]: gap for gap in done["gaps"]}
    assert done["gap_count"] == 4
    assert done["summary"]["total"] == 4
    assert done["saturation"]["ready"] is False
    assert done["full_text_attention_paths"] == ["inbox/flag-gap-full-text-metadata-only.md"]
    assert done["tag_candidate_paths"] == ["inbox/candidate-tag-neural-retrieval.md"]
    assert (vault / done["full_text_attention_paths"][0]).is_file()
    assert (vault / done["tag_candidate_paths"][0]).is_file()
    assert done["tag_candidates"][0]["phrase"] == "neural retrieval"
    assert gaps["catalog-only"]["gap_type"] == "undigested"
    assert gaps["catalog-only"]["kind"] == "undigested"
    assert gaps["catalog-only"]["severity"] == "high"
    assert gaps["catalog-only"]["source_count"] == 1
    assert gaps["Metadata Only"]["gap_type"] == "full-text-missing"
    assert gaps["Metadata Only"]["kind"] == "full-text-missing"
    assert gaps["Metadata Only"]["why"]
    assert gaps["Metadata Only"]["next_actions"]
    assert gaps["sleep"]["gap_type"] == "undigested"
    assert gaps["new area"]["gap_type"] == "new-topic"


def test_worker_runs_project_scoped_gap_analysis(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    (vault / "projects/project-alpha").mkdir(parents=True)
    (vault / "projects/project-alpha/project.md").write_text(
        "---\n"
        "type: project\n"
        "title: Alpha project\n"
        "tags: []\n"
        "links: {}\n"
        "thesis: notes/thesis.md\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    mark_file_status(vault, "projects/project-alpha/project.md", "project")
    for name, body in {
        "thesis": "type: note\ntitle: Thesis\ntags: []\nlinks: {}\nstatus: accepted\n",
        "support": (
            "type: note\ntitle: Support\ntags: []\nstatus: accepted\n"
            "links:\n  supports:\n    - notes/thesis.md\n"
        ),
        "refute": (
            "type: note\ntitle: Refute\ntags: []\nstatus: accepted\n"
            "links:\n  contradicts:\n    - notes/thesis.md\n"
        ),
    }.items():
        note = vault / f"notes/{name}.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(f"---\n{body}---\nBody.\n", encoding="utf-8")
        mark_file_status(vault, note.relative_to(vault).as_posix())

    queued = enqueue_operation(
        vault,
        "analyze-gaps",
        payload={"project_path": "project-alpha", "seed_terms": [], "dense_threshold": 2},
        idempotency_key="project-gap-analysis",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["project_path"] == "projects/project-alpha/project.md"
    assert done["thesis_path"] == "notes/thesis.md"
    assert done["argument_gap_count"] == 2
    assert done["paper_readiness_gap_count"] == 1
    assert {gap["finding_kind"] for gap in done["gaps"] if "finding_kind" in gap} == {
        "thin-argument",
        "conflict",
    }
    assert {gap["kind"] for gap in done["gaps"]} == {
        "argument-unsupported",
        "argument-fragile",
        "paper-readiness",
    }
    assert done["saturation"]["claims"] == 1
    assert done["saturation"]["ready"] is True


def test_worker_runs_frame_paper_operation(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    project_rel = "projects/project-alpha/project.md"
    project = vault / project_rel
    project.parent.mkdir(parents=True)
    project.write_text(
        "---\n"
        "type: project\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FAV\n"
        "title: Alpha project\n"
        "tags: []\n"
        "links: {}\n"
        "paper_plan: {}\n"
        "outcome_frame: {}\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    mark_file_status(vault, project_rel, "project")

    queued = enqueue_operation(
        vault,
        "frame-paper",
        payload={
            "project_path": "project-alpha",
            "target": "Journal of Testable Systems",
            "audience": "local-first tool builders",
            "research_question": "Can Memoria support standalone CLI research?",
            "central_contribution": "A checked CLI loop can produce usable evidence.",
            "gap_statement": "Existing PKM loops lack local checked export.",
            "claim_evidence_map": {"CLI loop works": "notes/support.md"},
            "figure_plan": {"Figure 1": "CLI loop stages"},
            "limitations": "Single-corpus dogfood run.",
        },
        idempotency_key="frame-paper",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["project_path"] == project_rel
    assert done["check_status"] == "unchecked"
    frontmatter = read_frontmatter(project)
    assert frontmatter["paper_plan"]["target"] == "Journal of Testable Systems"
    assert frontmatter["outcome_frame"]["status"] == "framed"


def test_worker_runs_project_argument_analysis_operation_jobs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    (vault / "projects/project-alpha").mkdir(parents=True)
    (vault / "projects/project-alpha/project.md").write_text(
        "---\n"
        "type: project\n"
        "title: Alpha project\n"
        "description: Project\n"
        "tags: []\n"
        "links: {}\n"
        "thesis: notes/thesis.md\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    mark_file_status(vault, "projects/project-alpha/project.md", "project")
    for name, body in {
        "thesis": "type: note\ntitle: Thesis\ntags: []\nlinks: {}\nstatus: accepted\n",
        "support": (
            "type: note\ntitle: Support\ntags: []\nstatus: accepted\n"
            "links:\n  supports:\n    - notes/thesis.md\n"
        ),
        "refute": (
            "type: note\ntitle: Refute\ntags: []\nstatus: accepted\n"
            "links:\n  contradicts:\n    - notes/thesis.md\n"
        ),
    }.items():
        note = vault / f"notes/{name}.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(f"---\n{body}---\nBody.\n", encoding="utf-8")
        mark_file_status(vault, note.relative_to(vault).as_posix())

    queued = enqueue_operation(
        vault,
        "analyze-project-argument",
        payload={"project_path": "project-alpha"},
        idempotency_key="project-argument",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["argument_stage"] == "developing"
    assert done["evidence_saturation"] == "unsaturated"
    assert done["saturation_conditions"] == {
        "mature_graph": False,
        "has_support": True,
        "has_refutation": True,
    }
    assert done["relation_count"] == 2
    assert done["supports_count"] == 1
    assert done["contradicts_count"] == 1
    assert [row["kind"] for row in done["gap_findings"]] == ["conflict"]
    assert [row["kind"] for row in done["advisories"]] == ["structural"]

    queued_canvas = enqueue_operation(
        vault,
        "render-project-argument-canvas",
        payload={"project_path": "project-alpha"},
        idempotency_key="project-argument-canvas",
        actor="pi",
    )
    canvas_done = run_next_job(vault, machine="test-machine")

    assert queued_canvas["kind"] == "operation"
    assert canvas_done is not None
    assert canvas_done["status"] == "done"
    assert canvas_done["canvas_path"] == "projects/project-alpha/argument.canvas"
    assert canvas_done["node_count"] == 3
    assert canvas_done["edge_count"] == 2
    canvas = json.loads((vault / canvas_done["canvas_path"]).read_text(encoding="utf-8"))
    assert {edge["label"] for edge in canvas["edges"]} == {"supports", "contradicts"}


def test_worker_runs_checked_search_index_rebuild_operation_jobs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    write_note(vault, "checked", "checked", "alpha beta")
    write_note(vault, "unchecked", "unchecked", "poison alpha")

    queued = enqueue_operation(
        vault,
        "rebuild-checked-search-index",
        idempotency_key="rebuild-search",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["document_count"] == 1
    assert [row["path"] for row in done["documents"]] == ["notes/checked.md"]
    assert (vault / ".memoria/index/search/checked/notes/checked.md").is_file()
    assert not (vault / ".memoria/index/search/checked/notes/unchecked.md").exists()


def test_worker_runs_answer_query_operation_jobs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    write_note(vault, "checked", "checked", "alpha beta")
    write_note(vault, "unchecked", "unchecked", "poison alpha")

    queued = enqueue_operation(
        vault,
        "answer-query",
        payload={"query": "alpha", "k": 3},
        idempotency_key="answer-query",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["engine"] == "bm25"
    assert done["unknowns"] == []
    assert [source["path"] for source in done["sources"]] == ["notes/checked.md"]


def test_worker_runs_seeded_error_verdict_in_disposable_fixture(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    eval_dir = vault / ".memoria/eval"
    eval_dir.mkdir(parents=True)
    shutil.copyfile(
        WORKSPACE_SEED / ".memoria/eval/alpha15-seeded-errors.json",
        eval_dir / "alpha15-seeded-errors.json",
    )

    queued = enqueue_operation(
        vault,
        "run-seeded-error-verdict",
        payload={"mode": "live", "target_operation_id": "compile-source-digest"},
        idempotency_key="seeded-verdict",
        actor="operation",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["passed"] is True
    assert done["mode"] == "live"
    assert done["provider"] == "gateway"
    assert done["operation_id"] == "compile-source-digest"
    assert done["non_sandbox_licensed"] is True
    assert done["verdict_key"].startswith("sha256:")
    assert done["metrics"]["expected_errors"] == 12
    assert done["metrics"]["detected_errors"] == 12
    assert done["metrics"]["residual_errors"] == 0
    assert not (vault / "catalog/sources/seed-source/source.md").exists()


def test_seeded_error_verdict_resolves_target_operation_runner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = workspace(tmp_path)
    eval_dir = vault / ".memoria/eval"
    eval_dir.mkdir(parents=True)
    shutil.copyfile(
        WORKSPACE_SEED / ".memoria/eval/alpha15-seeded-errors.json",
        eval_dir / "alpha15-seeded-errors.json",
    )
    resolved = []

    def fake_resolve(vault_path: Path, policy: dict, mode: str) -> dict[str, object]:
        resolved.append(policy["operation_id"])
        return {
            "mode": mode,
            "runner": "pydantic-ai",
            "provider": "gateway",
            "model": f"{policy['operation_id']}-model",
            "base_url": "https://model.test/v1",
            "key_env": None,
            "params": {"temperature": 0},
        }

    def fake_verdict(
        vault_path: Path,
        *,
        template_root: Path,
        bundle_path: Path,
        runner: dict,
        operation_id: str,
        context,
    ) -> dict[str, object]:
        return {
            "operation_id": operation_id,
            "mode": runner["mode"],
            "provider": runner["provider"],
            "model": runner["model"],
            "machine": context.machine,
        }

    monkeypatch.setattr("memoria_vault.runtime.operations.resolve_operation_runner", fake_resolve)
    monkeypatch.setattr(
        "memoria_vault.runtime.seeded_errors.run_seeded_error_verdict",
        fake_verdict,
    )

    enqueue_operation(
        vault,
        "run-seeded-error-verdict",
        payload={"mode": "live", "target_operation_id": "compile-source-digest"},
        idempotency_key="seeded-target-runner",
        actor="operation",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done is not None
    assert done["status"] == "done"
    assert resolved == ["compile-source-digest"]
    assert done["operation_id"] == "compile-source-digest"
    assert done["model"] == "compile-source-digest-model"
    assert done["machine"] == "test-machine"


def test_worker_seeded_error_verdict_requires_alpha15_bundle(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    eval_dir = vault / ".memoria/eval"
    eval_dir.mkdir(parents=True)
    (eval_dir / "alpha12-seeded-errors.json").write_text("{}", encoding="utf-8")

    enqueue_operation(
        vault,
        "run-seeded-error-verdict",
        payload={"mode": "test"},
        idempotency_key="seeded-no-removed-fallback",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done is not None
    assert done["status"] == "failed"
    assert ".memoria/eval/alpha15-seeded-errors.json" in done["error"]


def test_worker_runs_cascade_rollback_operation_jobs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    enqueue_trusted_write(
        vault,
        "notes/rollback.md",
        note_text(),
        idempotency_key="write-rollback",
        actor="operation",
    )
    run_next_job(vault, machine="test-machine")

    queued = enqueue_operation(
        vault,
        "cascade-rollback",
        payload={
            "target_id": "notes/rollback.md",
            "reason": "test rollback",
            "include_target": True,
        },
        idempotency_key="rollback-worker",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["reverted_count"] == 1
    assert done["needs_human_count"] == 0
    assert done["rollback"]["reverted"] == ["notes/rollback.md"]
    assert not (vault / "notes/rollback.md").exists()
    assert (vault / ".memoria/quarantine/notes/rollback.md").is_file()
    committed = set(git(vault, "show", "--name-only", "--format=", done["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL, "notes/rollback.md"}


def test_worker_runs_attention_resolution_operation_jobs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    queued = enqueue_operation(
        vault,
        "acknowledge-attention",
        payload={"target_id": "notes/attention.md", "reason": "PI saw it"},
        idempotency_key="ack-attention",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["resolution"]["event"] == "resolved"
    assert done["resolution"]["resolution"] == "acknowledged"
    assert done["resolution"]["outcome"] == "acknowledged"
    assert done["resolution"]["target_id"] == "notes/attention.md"
    assert done["resolution"]["actor"] == "pi"
    committed = set(git(vault, "show", "--name-only", "--format=", done["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL}


def test_worker_runs_observe_pi_edits_operation_jobs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    enqueue_trusted_write(
        vault,
        "notes/pi.md",
        note_text(),
        idempotency_key="write-pi",
        actor="operation",
    )
    run_next_job(vault, machine="test-machine")
    (vault / "notes/pi.md").write_text(note_text() + "\nPI edit.\n", encoding="utf-8")

    queued = enqueue_operation(
        vault,
        "observe-pi-edits",
        idempotency_key="observe-pi",
        actor="integrity",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["observed_count"] == 1
    assert done["paths"] == ["notes/pi.md"]
    assert "check_status" not in read_frontmatter(vault / "notes/pi.md")
    assert state.concept_check_status(vault, "notes/pi.md") == "unchecked"
    event_log = list(iter_jsonl(vault / ".memoria/journal/test-machine.jsonl"))
    assert event_log[-1]["event"] == "observed_external_edit"
    assert event_log[-1]["actor"] == "pi"
    with state.connect(vault) as conn:
        row = conn.execute(
            "SELECT check_status FROM outputs WHERE output_id = 'notes/pi.md'"
        ).fetchone()
        consumable = conn.execute(
            "SELECT output_id FROM consumable_outputs WHERE output_id = 'notes/pi.md'"
        ).fetchone()
    assert row["check_status"] == "unchecked"
    assert consumable is None
    committed = set(git(vault, "show", "--name-only", "--format=", done["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL, "notes/pi.md"}


def test_observe_pi_edits_propagates_scan_side_demotion(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    source_rel = "notes/source.md"
    direct_rel = "digests/direct.md"
    depth_two_rel = "digests/depth-two.md"
    pi_rel = "notes/pi-downstream.md"

    enqueue_trusted_write(
        vault, source_rel, note_text(), idempotency_key="write-source", actor="operation"
    )
    run_next_job(vault, machine="test-machine")
    enqueue_trusted_write(
        vault,
        direct_rel,
        work_text("direct", "Direct digest from source."),
        inputs=[{"id": source_rel, "sha256": sha256_file(vault / source_rel)}],
        idempotency_key="write-direct",
        actor="operation",
    )
    run_next_job(vault, machine="test-machine")
    enqueue_trusted_write(
        vault,
        depth_two_rel,
        work_text("depth-two", "Depth two keeps the depthtwomarker answer."),
        inputs=[{"id": direct_rel, "sha256": sha256_file(vault / direct_rel)}],
        idempotency_key="write-depth-two",
        actor="operation",
    )
    run_next_job(vault, machine="test-machine")

    pi_path = vault / pi_rel
    pi_path.parent.mkdir(parents=True, exist_ok=True)
    pi_path.write_text(note_text(), encoding="utf-8")
    prior_sha = sha256_file(pi_path)
    pi_path.write_text(note_text() + "\nPI downstream.\n", encoding="utf-8")
    observe_pi_edit(
        vault,
        pi_rel,
        prior_sha,
        inputs=[{"id": source_rel, "sha256": sha256_file(vault / source_rel)}],
        machine="pi-machine",
    )
    mark_checked(vault, pi_rel, machine="pi-machine")
    commit_writer_changes(vault, "observe pi downstream", [pi_rel], machine="pi-machine")

    source_path = vault / source_rel
    source_path.write_text(note_text() + "\nEdited source.\n", encoding="utf-8")
    enqueue_operation(
        vault,
        "observe-pi-edits",
        idempotency_key="observe-source-edit",
        actor="integrity",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done is not None
    assert done["status"] == "done"
    assert done["paths"] == [source_rel]
    assert state.concept_check_status(vault, source_rel) == "unchecked"
    assert state.concept_check_status(vault, direct_rel) == "unchecked"
    assert state.concept_check_status(vault, pi_rel) == "checked"
    assert state.concept_check_status(vault, depth_two_rel) == "checked"
    assert state.concept_flags(vault, depth_two_rel)["stale"]["trigger_id"] == source_rel

    answer = answer_query(vault, "depthtwomarker", include_stale=True)
    assert [source["path"] for source in answer["sources"]] == [depth_two_rel]
    assert answer["staleness"] == [{"path": depth_two_rel, "field": "stale", "value": True}]
    event_log = list(iter_jsonl(vault / ".memoria/journal/test-machine.jsonl"))
    assert any(
        event.get("check") == "scan-demotion-propagation"
        and event.get("target_id") == direct_rel
        and event.get("route") == "act"
        for event in event_log
    )
    assert any(
        event.get("check") == "cascade-rollback"
        and event.get("target_id") == pi_rel
        and event.get("route") == "ask"
        for event in event_log
    )


def test_observe_pi_edits_quarantines_changed_tracked_projection(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    write_tracked_projections(vault, commit=True, machine="test-machine")
    references = vault / "bibliography.bib"
    references.write_text(
        references.read_text(encoding="utf-8") + "\n% direct projection edit\n",
        encoding="utf-8",
    )

    enqueue_operation(
        vault,
        "observe-pi-edits",
        idempotency_key="observe-projection-edit",
        actor="integrity",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done is not None
    assert done["status"] == "done"
    assert done["observed_count"] == 0
    assert done["projection_quarantine_count"] == 1
    assert done["projection_paths"] == ["bibliography.bib"]
    assert "% direct projection edit" not in references.read_text(encoding="utf-8")
    assert (vault / ".memoria/quarantine/bibliography.bib").is_file()


def test_worker_runs_mark_checked_operation_jobs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    enqueue_trusted_write(
        vault,
        "notes/pi.md",
        note_text(),
        idempotency_key="write-pi",
        actor="operation",
    )
    run_next_job(vault, machine="test-machine")
    (vault / "notes/pi.md").write_text(note_text() + "\nPI edit.\n", encoding="utf-8")
    enqueue_operation(
        vault,
        "observe-pi-edits",
        idempotency_key="observe-pi",
        actor="integrity",
    )
    run_next_job(vault, machine="test-machine")

    queued = enqueue_operation(
        vault,
        "mark-checked",
        payload={"target_path": "notes/pi.md", "check": "memoria-runtime"},
        idempotency_key="mark-pi-checked",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["check"]["check"] == "memoria-runtime"
    assert done["check"]["status"] == "passed"
    assert "check_status" not in read_frontmatter(vault / "notes/pi.md")
    assert state.concept_check_status(vault, "notes/pi.md") == "checked"
    committed = set(git(vault, "show", "--name-only", "--format=", done["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL, "notes/pi.md"}


def test_worker_runs_update_work_operation_jobs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    state.upsert_catalog_record(
        vault,
        work_id="alpha",
        title="Original",
        description="Original description",
        identifiers={"doi": "10.1000/original"},
        csl_json={"title": "Original", "DOI": "10.1000/original"},
        check_status="checked",
    )

    queued = enqueue_operation(
        vault,
        "update-work",
        payload={
            "work_id": "alpha",
            "title": "Updated",
            "standing": "archived",
            "research_area": ["personal-informatics"],
        },
        idempotency_key="update-alpha",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["override_log"] == ".memoria/overrides.jsonl"
    assert "commit" in done
    assert done["work"]["title"] == "Updated"
    assert done["work"]["csl_json"]["memoria"]["standing"] == "archived"
    assert done["work"]["csl_json"]["memoria"]["research_area"] == ["personal-informatics"]
    with state.connect(vault) as conn:
        row = conn.execute(
            """
            SELECT payload_json
            FROM event_log
            WHERE event_type = 'work_updated'
            ORDER BY event_id DESC
            LIMIT 1
            """
        ).fetchone()
    event = json.loads(row["payload_json"])
    assert event["operation"] == "update-work"
    assert event["updates"]["title"] == "Updated"
    assert event["override_log"] == ".memoria/overrides.jsonl"
    [override] = list(iter_jsonl(vault / ".memoria/overrides.jsonl"))
    assert override["operation"] == "update-work"
    assert override["work_id"] == "alpha"
    assert override["updates"]["standing"] == "archived"
    committed = set(git(vault, "show", "--name-only", "--format=", done["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL, ".memoria/overrides.jsonl"}
    assert git(vault, "status", "--short", "--", ".memoria/overrides.jsonl") == ""


def test_worker_runs_references_bib_projection_operation_jobs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    capture_bibtex_source(
        vault,
        """@article{harness2026,
          title = {Harnessed Workflows for Durable Research},
          author = {Ada, River},
          year = {2026},
          journal = {Journal of Testable Systems}
        }""",
        machine="test-machine",
    )

    queued = enqueue_operation(
        vault,
        "regenerate-references-bib",
        idempotency_key="references-bib",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["changed"] is True
    assert done["output"] == "bibliography.bib"
    assert "@article{harness2026," in (vault / "bibliography.bib").read_text(encoding="utf-8")
    committed = set(git(vault, "show", "--name-only", "--format=", done["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL, "bibliography.bib"}


def test_scheduled_integrity_sweep_is_daily_idempotent(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    enqueue_trusted_write(
        vault,
        "notes/foreign.md",
        note_text(),
        idempotency_key="write-foreign-before-sweep",
        actor="operation",
    )
    run_next_job(vault, machine="test-machine")
    foreign = vault / "notes/foreign.md"
    foreign.write_text(note_text() + "\nForeign edit.\n", encoding="utf-8")

    enqueue_trusted_write(
        vault,
        "notes/bad-evidence.md",
        "---\n"
        "type: note\n"
        "title: Bad evidence\n"
        "tags: []\n"
        "links: {}\n"
        "work_id: catalog/sources/missing\n"
        "---\n"
        "# Bad evidence\n",
        idempotency_key="write-bad-evidence-before-sweep",
        actor="operation",
    )
    run_next_job(vault, machine="test-machine")

    result = run_integrity_sweep(
        vault,
        shadow=False,
        sweep_id="2026-06-29",
        machine="test-machine",
    )

    assert [job["job_id"] for job in result["jobs"]] == [
        "trace-integrity-scan-2026-06-29",
        "check-source-metadata-2026-06-29",
        "integrity-evidence-check-2026-06-29",
        "integrity-quote-anchor-check-2026-06-29",
        "integrity-claim-quote-check-2026-06-29",
        "integrity-prompt-injection-check-2026-06-29",
        "integrity-provenance-checkpoint-2026-06-29",
        "integrity-citation-survival-check-2026-06-29",
        "integrity-contradiction-check-2026-06-29",
        "integrity-link-target-check-2026-06-29",
    ]
    by_operation = {job["operation_id"]: job for job in result["results"]}
    assert by_operation["trace-integrity-scan"]["finding_count"] == 1
    assert not foreign.exists()
    assert "check_status" not in read_frontmatter(vault / ".memoria/quarantine/notes/foreign.md")
    assert state.concept_check_status(vault, "notes/foreign.md") == "quarantined"
    assert by_operation["integrity-evidence-check"]["finding_count"] == 1
    assert by_operation["integrity-evidence-check"]["findings"][0]["route"] == "ask"
    assert by_operation["integrity-quote-anchor-check"]["finding_count"] == 0
    assert by_operation["integrity-claim-quote-check"]["finding_count"] == 0
    assert by_operation["integrity-prompt-injection-check"]["finding_count"] == 0
    assert by_operation["integrity-citation-survival-check"]["finding_count"] == 0
    assert by_operation["integrity-provenance-checkpoint"]["finding_count"] == 0
    assert by_operation["integrity-contradiction-check"]["finding_count"] == 0
    assert by_operation["integrity-link-target-check"]["finding_count"] == 0

    again = enqueue_integrity_sweep(vault, shadow=False, sweep_id="2026-06-29")

    assert {job["status"] for job in again} == {"done"}

    replay = run_integrity_sweep(
        vault,
        shadow=False,
        sweep_id="2026-06-29",
        machine="test-machine",
    )

    assert {job["status"] for job in replay["jobs"]} == {"done"}
    assert replay["results"] == []
