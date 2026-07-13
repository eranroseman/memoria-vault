from __future__ import annotations

import json
from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.vaultio import read_frontmatter
from memoria_vault.runtime.worker import (
    enqueue_operation,
    enqueue_trusted_write,
    run_next_job,
    run_request,
)
from tests.helpers import copy_memoria_dirs, init_git


def workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas", "config")
    init_git(tmp_path, "cycle@example.invalid", "Alpha Cycle")
    return tmp_path


def run_operation(
    vault: Path,
    operation_id: str,
    payload: dict | None = None,
    *,
    key: str,
) -> dict:
    job = enqueue_operation(
        vault, operation_id, payload=payload or {}, idempotency_key=key, actor="pi"
    )
    done = run_request(vault, str(job["job_id"]), machine="cycle-machine")
    assert done is not None
    assert done["status"] == "done"
    return done


def run_trusted_write(vault: Path, target: str, content: str, *, key: str) -> dict:
    enqueue_trusted_write(vault, target, content, idempotency_key=key, actor="operation")
    done = run_next_job(vault, machine="cycle-machine")
    assert done is not None
    assert done["status"] == "done"
    return done


def test_basic_knowledge_cycle_runs_through_worker_queue(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    run_trusted_write(
        vault,
        "notes/thesis.md",
        (
            "---\n"
            "type: note\n"
            "title: Thesis\n"
            "tags: [Memory Consolidation]\n"
            "links: {}\n"
            "---\n"
            "Sleep-dependent memory consolidation needs supporting evidence.\n"
        ),
        key="seed-thesis",
    )
    run_trusted_write(
        vault,
        "projects/project-alpha/project.md",
        (
            "---\n"
            "type: project\n"
            "title: Sleep memory project\n"
            "description: A disposable knowledge-cycle project.\n"
            "tags: []\n"
            "links: {}\n"
            "thesis: notes/thesis.md\n"
            "---\n"
            "Project framing.\n"
        ),
        key="open-project",
    )

    initial_gaps = run_operation(
        vault,
        "analyze-gaps",
        {"dense_threshold": 1},
        key="initial-gap-analysis",
    )
    assert {gap["topic"]: gap["gap_type"] for gap in initial_gaps["gaps"]}[
        "Memory Consolidation"
    ] == "under-warranted"

    bibtex = """@article{cycle2026,
      title = {Memory Consolidation in Sleep},
      author = {Ada, River},
      year = {2026},
      journal = {Journal of Testable Research},
      doi = {10.1000/cycle.2026},
      abstract = {Sleep memory consolidation improves recall in the fixture study.}
    }"""
    capture = run_operation(
        vault,
        "capture-bibtex-source",
        {
            "bibtex": bibtex,
            "content_text": (
                "Sleep memory consolidation improves recall in the fixture study. "
                "The result is relevant to the knowledge-cycle project."
            ),
        },
        key="capture-source",
    )
    work_id = capture["work_id"]
    source_ref = f"catalog/sources/{work_id}"
    assert work_id == "doi-10.1000_cycle.2026"
    assert capture["check_status"] == "unchecked"
    assert capture["enrichment_job"]["operation_id"] == "enrich-source"
    assert not (vault / source_ref).exists()
    source = state.catalog_source(vault, work_id)
    assert source is not None
    assert source["check_status"] == "unchecked"
    assert source["citekey"] == "cycle2026"
    assert source["identifiers"] == {"doi": "10.1000/cycle.2026"}
    assert source["csl_json"]["DOI"] == "10.1000/cycle.2026"
    assert source["content_path"].startswith(
        ".memoria/blobs/source-content/doi-10.1000_cycle.2026/"
    )
    assert source["raw_path"].startswith(
        ".memoria/blobs/source-content/doi-10.1000_cycle.2026/raw/"
    )
    state.upsert_catalog_record(
        vault,
        work_id=source["work_id"],
        concept_path=source["concept_path"],
        doi=source["identifiers"]["doi"],
        title=source["title"],
        description=source["description"],
        resource=source["resource"],
        identifiers=source["identifiers"],
        citekey=source["citekey"],
        csl_json=source["csl_json"],
        provider_coverage="full",
        text_status=source["text_status"],
        check_status="checked",
        content_hash=source["normalized_text_sha256"],
        raw_hash=source["raw_text_sha256"],
        content_path=source["content_path"],
        raw_path=source["raw_path"],
    )

    run_operation(
        vault,
        "record-copi-interview",
        {
            "work_id": "doi-10.1000_cycle.2026",
            "response": "The PI cares about recall evidence for the thesis.",
            "project_id": "projects/project-alpha/project.md",
        },
        key="record-interview",
    )
    digest = run_operation(
        vault,
        "compile-source-digest",
        {
            "work_id": "doi-10.1000_cycle.2026",
            "hub_topics": [
                "Memory Consolidation",
                "Sleep Methods",
                "Recall Outcome",
                "Evidence Gap",
                "Project Impact",
            ],
        },
        key="compile-digest",
    )
    assert digest["digest_path"] == "digests/doi-10.1000_cycle.2026.md"
    assert len(digest["hub_paths"]) == 5

    notes = run_operation(
        vault,
        "propose-note-candidates",
        {
            "digest_path": digest["digest_path"],
            "candidates": [
                {
                    "title": "Sleep supports memory consolidation",
                    "body": "The fixture source supports the project thesis about recall.",
                    "claim_text": "Sleep memory consolidation improves recall.",
                    "quote": "Sleep memory consolidation improves recall",
                    "evidence_set": [source_ref],
                    "annotation_ref": {
                        "source_path": source_ref,
                        "page": 1,
                        "quote": "Sleep memory consolidation improves recall",
                        "bbox": [10, 20, 120, 40],
                    },
                    "tags": ["Memory Consolidation"],
                }
            ],
        },
        key="propose-notes",
    )
    note_path = notes["note_paths"][0]
    note_frontmatter = read_frontmatter(vault / note_path)
    assert state.note_curation_status(vault, note_path) == "candidate"
    assert note_frontmatter["annotation_ref"] == {
        "source_path": source_ref,
        "page": 1,
        "quote": "Sleep memory consolidation improves recall",
        "bbox": [10, 20, 120, 40],
    }

    run_operation(
        vault,
        "curate-note-candidate",
        {"note_path": note_path, "status": "accepted", "reason": "PI accepted"},
        key="accept-note",
    )
    run_operation(
        vault,
        "curate-note-link",
        {
            "source_note_path": note_path,
            "target_path": "notes/thesis.md",
            "link_type": "supports",
            "reason": "PI linked support",
        },
        key="link-note",
    )

    final_gaps = run_operation(
        vault,
        "analyze-gaps",
        {"dense_threshold": 1},
        key="final-gap-analysis",
    )
    assert "Memory Consolidation" not in {gap["topic"] for gap in final_gaps["gaps"]}

    answer = run_operation(
        vault,
        "answer-query",
        {"query": "sleep recall memory consolidation", "k": 5},
        key="answer-query",
    )
    assert answer["sources"]
    assert answer["unknowns"] == []

    manifest = run_operation(vault, "rebuild-checked-search-index", key="rebuild-search")
    indexed_paths = {row["path"] for row in manifest["documents"]}
    assert f"fulltexts/{work_id}.md" in indexed_paths
    assert digest["digest_path"] in indexed_paths
    assert note_path in indexed_paths

    canvas = run_operation(
        vault,
        "render-project-argument-canvas",
        {"project_path": "project-alpha"},
        key="render-canvas",
    )
    canvas_data = json.loads((vault / canvas["canvas_path"]).read_text(encoding="utf-8"))
    assert canvas["edge_count"] == 1
    assert {edge["label"] for edge in canvas_data["edges"]} == {"supports"}

    events = [
        event
        for path in sorted((vault / ".memoria/journal").glob("*.jsonl"))
        for event in iter_jsonl(path)
    ]
    assert any(event.get("event") == "model_call" for event in events)
    assert any(event.get("operation") == "curate-note-link" for event in events)
    for path in indexed_paths:
        source_path = (
            (vault / path)
            if (vault / path).is_file()
            else (vault / ".memoria/index/search/checked" / path)
        )
        assert "check_status" not in read_frontmatter(source_path)
        if (vault / path).is_file():
            assert state.concept_check_status(vault, path) == "checked"

    rollback = run_operation(
        vault,
        "cascade-rollback",
        {
            "target_id": source_ref,
            "reason": "cycle source rollback proof",
        },
        key="rollback-cycle",
    )
    reverted = set(rollback["rollback"]["reverted"])
    needs_human = set(rollback["rollback"]["needs_human"])
    assert reverted == set()
    assert digest["digest_path"] in needs_human
    assert note_path in needs_human
    assert not (vault / source_ref).exists()
    assert (vault / digest["digest_path"]).exists()
    assert (vault / note_path).exists()
    assert state.concept_check_status(vault, digest["digest_path"]) == "checked"
    assert state.concept_check_status(vault, note_path) == "checked"
