from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.capture import (
    capture_source as _capture_source,
)
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.projections import (
    write_tracked_projections as _write_tracked_projections,
)
from memoria_vault.runtime.search_index import answer_query as _answer_query
from memoria_vault.runtime.subsystems.lib.edges import LINK_RELATIONS, concept_edge_path_records
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
    git,
    mark_file_status,
    work_text,
    write_note,
)
from tests.helpers import (
    capture_bibtex_source_checked as _capture_bibtex_source,
)
from tests.helpers import (
    worker_workspace as workspace,
)

pytestmark = pytest.mark.runtime


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


def note_text() -> str:
    return "---\ntype: note\ntitle: Worker note\ntags: []\nlinks: {}\n---\nBody.\n"


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
        actor="pi",
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
        csl_json={"memoria": {"research_area": ["catalog-only"]}},
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


def _frame_paper_payload(**extra: object) -> dict:
    payload: dict = {
        "project_path": "project-alpha",
        "target": "Journal of Testable Systems",
        "audience": "local-first tool builders",
        "research_question": "Can Memoria support standalone CLI research?",
        "central_contribution": "A checked CLI loop can produce usable evidence.",
        "gap_statement": "Existing PKM loops lack local checked export.",
        "claim_evidence_map": {"CLI loop works": "notes/support.md"},
        "figure_plan": {"Figure 1": "CLI loop stages"},
        "limitations": "Single-corpus dogfood run.",
    }
    payload.update(extra)
    return payload


def _framable_project(vault: Path) -> str:
    project_rel = "projects/project-alpha/project.md"
    project = vault / project_rel
    project.parent.mkdir(parents=True, exist_ok=True)
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
    return project_rel


def dispositions(vault: Path) -> list[dict]:
    return state.read_event_log(vault, event_types=["disposition"])


def test_curate_note_link_worker_branch_threads_proposal_ref(tmp_path: Path) -> None:
    """The dispatch branch reads `proposal_ref` off the payload, or the gate is unreachable.

    The engine-level pair in `test_knowledge.py` proves `curate_note_link`; this
    one proves the worker actually hands it the payload field, which is the only
    route a real caller has.
    """
    vault = workspace(tmp_path)
    write_note(vault, "support", "checked", "Support body.")
    write_note(vault, "thesis", "checked", "Thesis body.")
    write_note(vault, "aside", "checked", "Aside body.")

    enqueue_operation(
        vault,
        "curate-note-link",
        payload={
            "source_note_path": "notes/support.md",
            "target_path": "notes/thesis.md",
            "link_type": "supports",
            "proposal_ref": "inbox/candidate-link-x.md",
        },
        idempotency_key="link-proposed",
        actor="pi",
    )
    proposed = run_next_job(vault, machine="test-machine")
    enqueue_operation(
        vault,
        "curate-note-link",
        payload={
            "source_note_path": "notes/support.md",
            "target_path": "notes/aside.md",
            "link_type": "supports",
        },
        idempotency_key="link-original",
        actor="pi",
    )
    original = run_next_job(vault, machine="test-machine")

    assert proposed is not None and proposed["status"] == "done"
    assert original is not None and original["status"] == "done"
    rows = dispositions(vault)
    assert [(row["decision"], row["item_type"], row["item_id"]) for row in rows] == [
        ("accept", "edge-proposal", "inbox/candidate-link-x.md")
    ]


def test_frame_paper_with_proposal_ref_emits_one_frame_proposal_accept(tmp_path: Path) -> None:
    """I1 spec §2 contract 4: framing a machine-proposed frame is PI judgment."""
    vault = workspace(tmp_path)
    _framable_project(vault)

    enqueue_operation(
        vault,
        "frame-paper",
        payload=_frame_paper_payload(proposal_ref="  inbox/candidate-frame-y.md  "),
        idempotency_key="frame-paper-proposed",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done is not None and done["status"] == "done"
    rows = dispositions(vault)
    assert len(rows) == 1
    assert rows[0]["decision"] == "accept"
    assert rows[0]["item_type"] == "frame-proposal"
    assert rows[0]["item_id"] == "inbox/candidate-frame-y.md"


def test_frame_paper_without_proposal_ref_emits_nothing(tmp_path: Path) -> None:
    """PI-original framing records no disposition — absent and blank alike."""
    vault = workspace(tmp_path)
    _framable_project(vault)

    enqueue_operation(
        vault,
        "frame-paper",
        payload=_frame_paper_payload(),
        idempotency_key="frame-paper-original",
        actor="pi",
    )
    first = run_next_job(vault, machine="test-machine")
    enqueue_operation(
        vault,
        "frame-paper",
        payload=_frame_paper_payload(proposal_ref="   "),
        idempotency_key="frame-paper-blank",
        actor="pi",
    )
    second = run_next_job(vault, machine="test-machine")

    assert first is not None and first["status"] == "done"
    assert second is not None and second["status"] == "done"
    assert dispositions(vault) == []


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


def test_worker_rejects_unparseable_answer_query_trace_flag(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    queued = enqueue_operation(
        vault,
        "answer-query",
        payload={"query": "alpha", "trace": "perhaps"},
        idempotency_key="answer-query-invalid-trace",
        actor="pi",
    )

    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "failed"
    assert "trace must be a boolean" in done["error"]


def test_worker_accepts_false_answer_query_trace_flag_without_trace(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    write_note(vault, "checked", "checked", "alpha beta")
    queued = enqueue_operation(
        vault,
        "answer-query",
        payload={"query": "alpha", "trace": "false"},
        idempotency_key="answer-query-false-trace",
        actor="pi",
    )

    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert "trace" not in done


@pytest.mark.parametrize(
    ("allow_unready", "error"),
    [
        ("false", "project is not export-ready"),
        ("perhaps", "allow_unready must be a boolean"),
    ],
)
def test_worker_does_not_fail_open_for_untyped_export_readiness_opt_out(
    tmp_path: Path, allow_unready: str, error: str
) -> None:
    vault = workspace(tmp_path)
    project = vault / "projects/project-alpha/project.md"
    project.parent.mkdir(parents=True)
    project.write_text(
        "---\n"
        "type: project\n"
        "check_status: checked\n"
        "title: Alpha project\n"
        "description: Project\n"
        "thesis: notes/thesis.md\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    mark_file_status(vault, "projects/project-alpha/project.md", "project")
    write_note(vault, "thesis", "checked", "A checked thesis.")

    queued = enqueue_operation(
        vault,
        "export-project",
        payload={"project_path": "project-alpha", "allow_unready": allow_unready},
        idempotency_key=f"export-project-{allow_unready}",
        actor="operation",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "failed"
    assert error in done["error"]


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
    pi_depth_two_rel = "notes/pi-depth-two.md"

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

    pi_depth_two_path = vault / pi_depth_two_rel
    pi_depth_two_path.write_text(note_text(), encoding="utf-8")
    depth_two_prior_sha = sha256_file(pi_depth_two_path)
    pi_depth_two_path.write_text(note_text() + "\nPI two hops down.\n", encoding="utf-8")
    observe_pi_edit(
        vault,
        pi_depth_two_rel,
        depth_two_prior_sha,
        inputs=[{"id": direct_rel, "sha256": sha256_file(vault / direct_rel)}],
        machine="pi-machine",
    )
    mark_checked(vault, pi_depth_two_rel, machine="pi-machine")
    commit_writer_changes(
        vault, "observe pi downstream", [pi_rel, pi_depth_two_rel], machine="pi-machine"
    )

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
    # Epistemic marks are origin-blind (EDGES section 7): a PI-authored descendant
    # takes the mark its depth earns, exactly like a machine-derived one. Depth 1
    # demotes; depth 2+ goes stale.
    assert state.concept_check_status(vault, pi_rel) == "unchecked"
    assert state.concept_check_status(vault, depth_two_rel) == "checked"
    assert state.concept_flags(vault, depth_two_rel)["stale"]["trigger_id"] == source_rel
    assert state.concept_check_status(vault, pi_depth_two_rel) == "checked"
    assert state.concept_flags(vault, pi_depth_two_rel)["stale"]["trigger_id"] == source_rel

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
        event.get("check") == "scan-demotion-propagation"
        and event.get("target_id") == pi_rel
        and event.get("route") == "act"
        for event in event_log
    )
    assert any(
        event.get("check") == "scan-demotion-stale"
        and event.get("target_id") == pi_depth_two_rel
        and event.get("route") == "log"
        for event in event_log
    )
    assert not any(event.get("check") == "cascade-rollback" for event in event_log)


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


def test_mark_checked_emits_accept_disposition_with_the_target_doc_type(tmp_path: Path) -> None:
    """I1 spec §2: promoting machine-staged content to checked is PI judgment on it.

    Two concept types, never one: `item_type` is the *target's* frontmatter
    `type`, and a single-type fixture cannot tell that from a hardcoded "note".
    """
    vault = workspace(tmp_path)
    enqueue_trusted_write(
        vault, "notes/pi.md", note_text(), idempotency_key="write-note", actor="operation"
    )
    run_next_job(vault, machine="test-machine")
    enqueue_trusted_write(
        vault,
        "hubs/pi.md",
        "---\ntype: hub\ntitle: Worker hub\ntag: worker\ntags: []\nlinks: {}\n---\nBody.\n",
        idempotency_key="write-hub",
        actor="operation",
    )
    run_next_job(vault, machine="test-machine")

    for rel, key in (("notes/pi.md", "mark-note"), ("hubs/pi.md", "mark-hub")):
        enqueue_operation(
            vault,
            "mark-checked",
            payload={"target_path": rel},
            idempotency_key=key,
            actor="pi",
        )
        done = run_next_job(vault, machine="test-machine")
        assert done is not None and done["status"] == "done", done

    rows = dispositions(vault)
    assert {row["item_id"]: row["item_type"] for row in rows} == {
        "notes/pi.md": "note",
        "hubs/pi.md": "hub",
    }
    assert {row["decision"] for row in rows} == {"accept"}


def test_mark_checked_disposition_survives_an_unnormalized_target_path(tmp_path: Path) -> None:
    """The payload path is caller text; the recorded `item_id` is the canonical one.

    `mark_checked` normalizes before it writes, so a disposition keyed off the
    raw payload string would file the same document under two different ids.
    """
    vault = workspace(tmp_path)
    enqueue_trusted_write(
        vault, "notes/pi.md", note_text(), idempotency_key="write-note", actor="operation"
    )
    run_next_job(vault, machine="test-machine")

    enqueue_operation(
        vault,
        "mark-checked",
        payload={"target_path": "./notes/pi.md"},
        idempotency_key="mark-unnormalized",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done is not None and done["status"] == "done", done
    assert [row["item_id"] for row in dispositions(vault)] == ["notes/pi.md"]


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


def _seed_work(vault: Path, work_id: str, **fields: object) -> None:
    state.upsert_catalog_record(
        vault,
        work_id=work_id,
        title="Original",
        description="Original description",
        check_status="checked",
        **fields,
    )


def _run_update_work(vault: Path, key: str, payload: dict) -> dict:
    enqueue_operation(vault, "update-work", payload=payload, idempotency_key=key, actor="pi")
    done = run_next_job(vault, machine="test-machine")
    assert done is not None and done["status"] == "done", done
    return done


def test_update_work_overwriting_a_machine_enriched_value_is_an_edit(tmp_path: Path) -> None:
    """I1 spec §2: correcting what enrich-source wrote is PI judgment over machine output.

    Overwriting a previously non-empty `identifiers`/`csl_json` value is a
    correction; filling a previously empty one is completion. That distinction
    is the precision signal, and it needs the *before* value to exist.
    """
    vault = workspace(tmp_path)
    _seed_work(
        vault,
        "alpha",
        identifiers={"doi": "10.1000/machine"},
        csl_json={"title": "Original", "DOI": "10.1000/machine"},
    )

    _run_update_work(vault, "correct-doi", {"work_id": "alpha", "doi": "10.1000/corrected"})

    rows = dispositions(vault)
    assert [(row["decision"], row["item_type"], row["item_id"]) for row in rows] == [
        ("edit", "work", "alpha")
    ]


def test_update_work_correction_is_seen_through_identifiers_alone(tmp_path: Path) -> None:
    """`identifiers`' before-state is load-bearing on its own, not a spare wheel.

    A DOI update writes `identifiers["doi"]` and `csl_json["DOI"]` together, so
    a fixture carrying both prior values passes even with the `identifiers`
    before-state thrown away. Capture can leave a DOI in `identifiers` while the
    provider payload behind `csl_json` carries none — then only the identifiers
    pair sees a prior value, and the csl side is a completion.
    """
    vault = workspace(tmp_path)
    _seed_work(
        vault,
        "zeta",
        identifiers={"doi": "10.1000/machine"},
        csl_json={"title": "Original"},
    )

    _run_update_work(vault, "correct-identifier", {"work_id": "zeta", "doi": "10.1000/pi"})

    assert [row["decision"] for row in dispositions(vault)] == ["edit"]


def test_update_work_correction_is_seen_through_csl_json_alone(tmp_path: Path) -> None:
    """`csl_json`'s before-state is load-bearing on its own, not a spare wheel.

    A DOI correction moves `identifiers` *and* `csl_json` together, so a test
    that only ever corrects a DOI passes even if the `csl_json` before-state is
    thrown away. `resource` moves `csl_json["URL"]` and nothing else.
    """
    vault = workspace(tmp_path)
    _seed_work(
        vault,
        "epsilon",
        identifiers={},
        csl_json={"title": "Original", "URL": "https://example.invalid/machine"},
        resource="https://example.invalid/machine",
    )

    _run_update_work(
        vault, "correct-url", {"work_id": "epsilon", "resource": "https://example.invalid/pi"}
    )

    assert [row["decision"] for row in dispositions(vault)] == ["edit"]


def test_update_work_filling_an_empty_value_is_completion_not_an_edit(tmp_path: Path) -> None:
    """No prior machine value means nothing was corrected — completion is silent."""
    vault = workspace(tmp_path)
    _seed_work(vault, "beta", identifiers={}, csl_json={"title": "Original"})

    _run_update_work(vault, "fill-doi", {"work_id": "beta", "doi": "10.1000/first"})

    assert dispositions(vault) == []


def test_update_work_restating_the_same_value_is_not_an_edit(tmp_path: Path) -> None:
    """A no-op rewrite of an enriched value corrects nothing."""
    vault = workspace(tmp_path)
    _seed_work(
        vault,
        "gamma",
        identifiers={"doi": "10.1000/machine"},
        csl_json={"title": "Original", "DOI": "10.1000/machine"},
    )

    _run_update_work(vault, "restate-doi", {"work_id": "gamma", "doi": "10.1000/machine"})
    _run_update_work(vault, "retitle-only", {"work_id": "gamma", "title": "Retitled"})

    assert dispositions(vault) == []


def test_update_work_memoria_block_changes_are_never_machine_corrections(tmp_path: Path) -> None:
    """`csl_json.memoria` has no machine author, so rewriting it corrects nobody.

    `worker.py` is the only writer of that block (standing, research_area,
    methodology): none of it comes from enrich-source or import. Comparing it
    would fire an `edit` on every second standing change a PI ever makes.
    """
    vault = workspace(tmp_path)
    _seed_work(
        vault,
        "delta",
        csl_json={"title": "Original", "memoria": {"standing": "current", "topics": ["legacy"]}},
    )

    _run_update_work(vault, "restand", {"work_id": "delta", "standing": "archived"})
    _run_update_work(vault, "remethod", {"work_id": "delta", "methodology": ["rct"]})

    assert dispositions(vault) == []
    assert state.catalog_source(vault, "delta")["csl_json"]["memoria"]["standing"] == "archived"


def test_update_work_preserves_unrecognized_topics_from_catalog_row(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    state.upsert_catalog_record(
        vault,
        work_id="legacy",
        title="Pre-F4 Work",
        csl_json={"memoria": {"topics": ["legacy-topic"], "standing": "current"}},
        check_status="checked",
    )

    enqueue_operation(
        vault,
        "update-work",
        payload={"work_id": "legacy", "methodology": ["rct"]},
        idempotency_key="preserve-catalog-work",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done is not None
    assert done["status"] == "done"
    assert done["work"]["csl_json"]["memoria"] == {
        "topics": ["legacy-topic"],
        "standing": "current",
        "methodology": ["rct"],
    }
    assert state.catalog_source(vault, "legacy")["csl_json"]["memoria"] == {
        "topics": ["legacy-topic"],
        "standing": "current",
        "methodology": ["rct"],
    }


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


@pytest.mark.parametrize("relation", sorted(LINK_RELATIONS))
def test_worker_runs_each_served_curate_note_link(tmp_path: Path, relation: str) -> None:
    """The queued worker path completes the same verbs the direct path does."""
    vault = workspace(tmp_path)
    source = write_note(vault, "source", "checked", "Source body.")
    target = write_note(vault, "target", "checked", "Target body.")
    queued = enqueue_operation(
        vault,
        "curate-note-link",
        payload={
            "source_note_path": source.relative_to(vault).as_posix(),
            "link_type": relation,
            "target_path": target.relative_to(vault).as_posix(),
        },
        idempotency_key=f"served-link-{relation}",
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None and done["status"] == "done", done
    assert done["link_type"] == relation
    assert read_frontmatter(source)["links"] == {relation: ["notes/target.md"]}


def test_worker_curate_note_link_carries_warrant_to_the_edge(tmp_path: Path) -> None:
    """The queued path wires `payload.warrant` through; without it no edge is written."""
    vault = workspace(tmp_path)
    source = write_note(vault, "source", "checked", "Source body.")
    write_note(vault, "target", "checked", "Target body.")
    payload = {
        "source_note_path": source.relative_to(vault).as_posix(),
        "link_type": "supports",
        "target_path": "notes/target.md",
    }
    enqueue_operation(
        vault, "curate-note-link", payload=payload, idempotency_key="link-no-warrant", actor="pi"
    )
    bare = run_next_job(vault, machine="test-machine")
    enqueue_operation(
        vault,
        "curate-note-link",
        payload={**payload, "warrant": "the trial licenses this step"},
        idempotency_key="link-warrant",
        actor="pi",
    )
    warranted = run_next_job(vault, machine="test-machine")

    assert bare is not None and bare["status"] == "done", bare
    assert warranted is not None and warranted["status"] == "done", warranted
    assert [
        record["attributes"] for record in concept_edge_path_records(vault, checked_only=False)
    ] == [{"warrant": "the trial licenses this step"}]


def test_worker_rejects_tension_curate_note_link(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    source = write_note(vault, "source", "checked", "Source body.")
    target = write_note(vault, "target", "checked", "Target body.")
    enqueue_operation(
        vault,
        "curate-note-link",
        payload={
            "source_note_path": source.relative_to(vault).as_posix(),
            "link_type": "tension",
            "target_path": target.relative_to(vault).as_posix(),
        },
        idempotency_key="served-link-tension",
        actor="pi",
    )
    failed = run_next_job(vault, machine="test-machine")

    assert failed is not None and failed["status"] == "failed"
    assert "link_type must be one of" in str(failed["error"])


def _retractable_work(vault: Path, work_id: str) -> None:
    state.upsert_catalog_record(
        vault,
        work_id=work_id,
        title="Retractable",
        description="Soon retracted.",
        csl_json={"title": "Retractable"},
        check_status="checked",
    )


def _ground_claim_in(vault: Path, work_id: str, note: str, evidence_id: str) -> None:
    write_note(vault, note, "checked", f"Claim grounded in {work_id}.")
    state.replace_evidence_sets(
        vault,
        [
            {
                "id": evidence_id,
                "block_ref": f"notes/{note}.md#^blk-33333333",
                "items": [f"{work_id}#^p0001"],
                "type": "single-span",
                "state": "complete",
                "review_required": False,
                "bind": False,
            }
        ],
    )


def _update_standing(vault: Path, work_id: str, standing: str, key: str) -> dict:
    enqueue_operation(
        vault,
        "update-work",
        payload={"work_id": work_id, "standing": standing},
        idempotency_key=key,
        actor="pi",
    )
    done = run_next_job(vault, machine="test-machine")
    assert done is not None and done["status"] == "done", done
    return done


def test_update_work_standing_retraction_sweeps_grounded_claims(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    _retractable_work(vault, "w9")
    _ground_claim_in(vault, "w9", "grounded", "ev-33333333")

    done = _update_standing(vault, "w9", "retracted", "retract-w9")

    assert done["propagation"]["trigger"] == "standing-changed"
    assert done["propagation"]["target_id"] == "catalog/sources/w9"
    assert done["propagation"]["marked"] == {"notes/grounded.md": "grounds-lost"}
    frontmatter = read_frontmatter(vault / "notes/grounded.md")
    assert frontmatter["stale"] is True
    assert frontmatter["consequence"] == "grounds-lost"
    assert state.concept_consequence(vault, "notes/grounded.md") == "grounds-lost"


def test_update_work_supersession_sweeps_too(tmp_path: Path) -> None:
    """`superseded` is the standing set's second member, not a copy of the first."""
    vault = workspace(tmp_path)
    _retractable_work(vault, "w11")
    _ground_claim_in(vault, "w11", "superseded-claim", "ev-44444444")

    done = _update_standing(vault, "w11", "superseded", "supersede-w11")

    assert done["propagation"]["marked"] == {"notes/superseded-claim.md": "grounds-lost"}


def test_update_work_archiving_does_not_sweep(tmp_path: Path) -> None:
    """Shelving is not falsification: `archived` is outside the standing set."""
    vault = workspace(tmp_path)
    _retractable_work(vault, "w10")
    _ground_claim_in(vault, "w10", "shelved-claim", "ev-55555555")

    done = _update_standing(vault, "w10", "archived", "archive-w10")

    assert done["propagation"] == {}
    assert read_frontmatter(vault / "notes/shelved-claim.md").get("stale") is None


def test_update_work_restating_a_standing_is_not_a_transition(tmp_path: Path) -> None:
    """Already retracted: the sweep fired once, and re-issuing it is not a second fall."""
    vault = workspace(tmp_path)
    _retractable_work(vault, "w12")
    _ground_claim_in(vault, "w12", "twice-claim", "ev-66666666")
    first = _update_standing(vault, "w12", "retracted", "retract-w12-once")

    again = _update_standing(vault, "w12", "retracted", "retract-w12-twice")

    assert first["propagation"]["marked"] == {"notes/twice-claim.md": "grounds-lost"}
    assert again["propagation"] == {}


def test_worker_runs_fork_project_canvas_operation_jobs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    for name, body in {
        "thesis": "type: note\ntitle: Thesis\ntags: []\nstatus: accepted\n",
        "support": (
            "type: note\ntitle: Support\ntags: []\nstatus: accepted\n"
            "links:\n  supports:\n    - notes/thesis.md\n"
        ),
    }.items():
        note = vault / f"notes/{name}.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(f"---\n{body}---\nBody.\n", encoding="utf-8")
        mark_file_status(vault, note.relative_to(vault).as_posix())
    project = vault / "projects/project-alpha/project.md"
    project.parent.mkdir(parents=True, exist_ok=True)
    project.write_text(
        "---\ntype: project\ntitle: Alpha project\nthesis: notes/thesis.md\n---\nP.\n",
        encoding="utf-8",
    )
    mark_file_status(vault, "projects/project-alpha/project.md", "project")

    enqueue_operation(
        vault,
        "render-project-argument-canvas",
        payload={"project_path": "project-alpha"},
        idempotency_key="fork-setup-render",
        actor="pi",
    )
    rendered = run_next_job(vault, machine="test-machine")
    assert rendered is not None and rendered["status"] == "done"

    enqueue_operation(
        vault,
        "fork-project-canvas",
        payload={"project_path": "project-alpha", "name": "review"},
        idempotency_key="fork-canvas",
        # Not PI-protected: the plugin's fork command reaches the worker as an
        # ordinary agent enqueue, exactly like the render it forks from.
        actor="agent",
    )
    done = run_next_job(vault, machine="test-machine")

    assert done is not None
    assert done["status"] == "done"
    assert done["project_path"] == "projects/project-alpha/project.md"
    assert done["source_canvas_path"] == "projects/project-alpha/argument.canvas"
    assert done["scratch_canvas_path"] == "projects/project-alpha/scratch-review.canvas"
    assert done["commit"]
    scratch = json.loads((vault / done["scratch_canvas_path"]).read_text(encoding="utf-8"))
    generated = json.loads((vault / done["source_canvas_path"]).read_text(encoding="utf-8"))
    assert scratch["edges"] == generated["edges"]
    assert all(node["id"] != "memoria-banner" for node in scratch["nodes"])

    enqueue_operation(
        vault,
        "fork-project-canvas",
        payload={"name": "no-project"},
        idempotency_key="fork-canvas-no-project",
        actor="agent",
    )
    refused = run_next_job(vault, machine="test-machine")

    assert refused is not None
    assert refused["status"] == "failed"
    assert "fork-project-canvas requires project_path" in str(refused["error"])
