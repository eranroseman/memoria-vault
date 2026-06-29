from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.vaultio import read_frontmatter
from memoria_vault.runtime.worker import enqueue_operation, enqueue_trusted_write, run_next_job

ROOT = Path(__file__).resolve().parent.parent


def workspace(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "vault-template/.memoria/schemas", tmp_path / ".memoria/schemas")
    shutil.copytree(ROOT / "vault-template/capabilities", tmp_path / "capabilities")
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "cycle@example.invalid")
    git(tmp_path, "config", "user.name", "Alpha Cycle")
    return tmp_path


def git(vault: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=vault,
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.returncode:
        raise AssertionError(proc.stderr or proc.stdout)
    return proc.stdout.strip()


def run_operation(
    vault: Path,
    operation_id: str,
    payload: dict | None = None,
    *,
    key: str,
) -> dict:
    enqueue_operation(vault, operation_id, payload=payload or {}, idempotency_key=key)
    done = run_next_job(vault, machine="cycle-machine")
    assert done is not None
    assert done["status"] == "done"
    return done


def run_trusted_write(vault: Path, target: str, content: str, *, key: str) -> dict:
    enqueue_trusted_write(vault, target, content, idempotency_key=key)
    done = run_next_job(vault, machine="cycle-machine")
    assert done is not None
    assert done["status"] == "done"
    return done


def test_basic_knowledge_cycle_runs_through_worker_queue(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    run_trusted_write(
        vault,
        "knowledge/notes/thesis.md",
        (
            "---\n"
            "type: note\n"
            "check_status: checked\n"
            "title: Thesis\n"
            "status: accepted\n"
            "tags: [Memory Consolidation]\n"
            "---\n"
            "Sleep-dependent memory consolidation needs supporting evidence.\n"
        ),
        key="seed-thesis",
    )
    run_trusted_write(
        vault,
        "knowledge/projects/project-alpha.md",
        (
            "---\n"
            "type: project\n"
            "check_status: checked\n"
            "title: Sleep memory project\n"
            "description: A disposable alpha.11 cycle project.\n"
            "thesis: knowledge/notes/thesis.md\n"
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
                "The result is relevant to the alpha.11 project."
            ),
        },
        key="capture-source",
    )
    assert capture["source_path"] == "catalog/sources/doi-10.1000_cycle.2026/source.md"
    source_frontmatter = read_frontmatter(vault / capture["source_path"])
    assert source_frontmatter["check_status"] == "checked"
    assert source_frontmatter["source_id"] == "doi-10.1000_cycle.2026"
    assert source_frontmatter["citekey"] == "cycle2026"
    assert source_frontmatter["identifiers"] == {"doi": "10.1000/cycle.2026"}
    assert source_frontmatter["csl_json"]["DOI"] == "10.1000/cycle.2026"
    assert Path(source_frontmatter["content_path"]).is_relative_to(
        "catalog/sources/doi-10.1000_cycle.2026"
    )
    assert Path(source_frontmatter["raw_copy_path"]).is_relative_to(
        "catalog/sources/doi-10.1000_cycle.2026/raw"
    )

    run_operation(
        vault,
        "record-copi-interview",
        {
            "source_id": "doi-10.1000_cycle.2026",
            "response": "The PI cares about recall evidence for the thesis.",
            "project_id": "knowledge/projects/project-alpha.md",
        },
        key="record-interview",
    )
    digest = run_operation(
        vault,
        "compile-source-digest",
        {
            "source_id": "doi-10.1000_cycle.2026",
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
    assert digest["digest_path"] == "knowledge/digests/doi-10.1000_cycle.2026.md"
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
                    "evidence_set": [capture["source_path"]],
                    "annotation_ref": {
                        "source_path": capture["source_path"],
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
    assert note_frontmatter["status"] == "candidate"
    assert note_frontmatter["annotation_ref"] == {
        "source_path": capture["source_path"],
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
            "target_path": "knowledge/notes/thesis.md",
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

    manifest = run_operation(vault, "rebuild-checked-qmd-source", key="rebuild-qmd")
    indexed_paths = {row["path"] for row in manifest["documents"]}
    assert capture["source_path"] in indexed_paths
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
        event for path in sorted((vault / "journal").glob("*.jsonl")) for event in iter_jsonl(path)
    ]
    assert any(event.get("event") == "model_call" for event in events)
    assert any(event.get("operation") == "curate-note-link" for event in events)
    assert all(
        read_frontmatter(vault / path)["check_status"] == "checked" for path in indexed_paths
    )

    rollback = run_operation(
        vault,
        "cascade-rollback",
        {
            "target_id": capture["source_path"],
            "reason": "cycle source rollback proof",
        },
        key="rollback-cycle",
    )
    reverted = set(rollback["rollback"]["reverted"])
    assert digest["digest_path"] in reverted
    assert note_path in reverted
    assert (vault / capture["source_path"]).is_file()
    assert not (vault / digest["digest_path"]).exists()
    assert not (vault / note_path).exists()
    assert (
        read_frontmatter(vault / ".memoria/quarantine" / digest["digest_path"])["check_status"]
        == "quarantined"
    )
    assert (
        read_frontmatter(vault / ".memoria/quarantine" / note_path)["check_status"] == "quarantined"
    )
