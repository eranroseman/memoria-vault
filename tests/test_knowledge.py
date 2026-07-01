from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from memoria_vault.runtime.capture import capture_source
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.knowledge import (
    analyze_gaps,
    analyze_project_argument,
    curate_note_candidate,
    curate_note_link,
    emit_note_candidates,
    write_project_argument_canvas,
)
from memoria_vault.runtime.operations import compile_source_digest
from memoria_vault.runtime.trusted_writer import mark_checked, observe_pi_edit_from_head
from memoria_vault.runtime.vaultio import read_frontmatter

ROOT = Path(__file__).resolve().parent.parent


def workspace(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "vault-template/.memoria/schemas", tmp_path / ".memoria/schemas")
    shutil.copytree(ROOT / "vault-template/capabilities", tmp_path / "capabilities")
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "knowledge@example.invalid")
    git(tmp_path, "config", "user.name", "Knowledge")
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


def test_emit_note_candidates_promotes_checked_candidate_notes(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Alpha content about framing, methods, outcomes, gaps, and impact.",
        machine="capture-machine",
    )
    compile_source_digest(
        vault,
        "source-alpha",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="digest-machine",
    )

    result = emit_note_candidates(
        vault,
        "source-alpha",
        [
            {
                "title": "Framing changes the question",
                "description": "A candidate note from the source digest.",
                "body": "The source reframes the problem before measuring outcomes.",
                "claim_text": "Framing changes which outcomes matter.",
                "tags": ["Framing"],
            }
        ],
        machine="note-machine",
        run_id="notes-alpha",
    )

    [note_rel] = result["note_paths"]
    note = vault / note_rel
    fm = read_frontmatter(note)
    assert fm["type"] == "note"
    assert fm["check_status"] == "checked"
    assert fm["status"] == "candidate"
    assert fm["source_id"] == "catalog/sources/source-alpha"
    assert fm["evidence_set"] == ["catalog/sources/source-alpha/source.md"]
    assert fm["claim_text"] == "Framing changes which outcomes matter."

    events = list(iter_jsonl(vault / "journal/note-machine.jsonl"))
    assert [event["event"] for event in events] == [
        "run",
        "model_call",
        "derived",
        "check-fired",
        "run",
    ]
    assert events[1]["runner"] == "pydantic-ai"
    assert events[-1]["outputs"] == [note_rel]
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {"journal/note-machine.jsonl", note_rel}


def test_emit_note_candidates_preserves_pdf_annotation_selector(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "pdf-source",
        "PDF Source",
        "A fixture PDF source.",
        "The PDF reports an anchored finding on page 3.",
        raw_bytes=b"%PDF-1.4 fixture bytes\n",
        raw_filename="paper.pdf",
        machine="capture-machine",
    )
    compile_source_digest(
        vault,
        "pdf-source",
        ["Anchored finding", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="digest-machine",
    )
    annotation_ref = {
        "source_id": "catalog/sources/pdf-source/source.md",
        "raw_copy_path": "catalog/sources/pdf-source/raw/paper.pdf",
        "page": 3,
        "text_quote": "anchored finding",
        "bbox": [72, 144, 300, 180],
    }

    result = emit_note_candidates(
        vault,
        "pdf-source",
        [
            {
                "title": "PDF anchored finding",
                "description": "A note with page/span/bbox provenance.",
                "body": "The PDF reports an anchored finding on page 3.",
                "claim_text": "The PDF reports an anchored finding.",
                "quote": "anchored finding",
                "annotation_ref": annotation_ref,
            }
        ],
        machine="note-machine",
    )

    [note_rel] = result["note_paths"]
    note_fm = read_frontmatter(vault / note_rel)
    source_fm = read_frontmatter(vault / "catalog/sources/pdf-source/source.md")
    assert source_fm["raw_copy_path"] == "catalog/sources/pdf-source/raw/paper.pdf"
    assert note_fm["annotation_ref"] == annotation_ref
    assert note_fm["quote"] == "anchored finding"


def test_curate_note_candidate_accepts_checked_candidate_with_journal(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Alpha content about framing, methods, outcomes, gaps, and impact.",
        machine="capture-machine",
    )
    compile_source_digest(
        vault,
        "source-alpha",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="digest-machine",
    )
    notes = emit_note_candidates(
        vault,
        "source-alpha",
        [{"title": "Curated candidate", "body": "The body stays intact."}],
        machine="note-machine",
    )

    result = curate_note_candidate(
        vault,
        notes["note_paths"][0],
        "accepted",
        reason="PI approved",
        machine="curator",
    )

    note_rel = notes["note_paths"][0]
    assert result["note_path"] == note_rel
    assert result["status"] == "accepted"
    assert read_frontmatter(vault / note_rel)["status"] == "accepted"
    assert "The body stays intact." in (vault / note_rel).read_text(encoding="utf-8")
    event = list(iter_jsonl(vault / "journal/curator.jsonl"))[-1]
    assert event["event"] == "resolved"
    assert event["operation"] == "curate-note-candidate"
    assert event["target_id"] == note_rel
    assert event["resolution"] == "accepted"
    assert event["reason"] == "PI approved"
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {"journal/curator.jsonl", note_rel}


def test_pi_can_edit_candidate_text_before_accepting(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Alpha content about framing, methods, outcomes, gaps, and impact.",
        machine="capture-machine",
    )
    compile_source_digest(
        vault,
        "source-alpha",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="digest-machine",
    )
    notes = emit_note_candidates(
        vault,
        "source-alpha",
        [{"title": "Editable candidate", "body": "Machine draft."}],
        machine="note-machine",
    )
    note_rel = notes["note_paths"][0]
    note = vault / note_rel

    note.write_text(
        note.read_text(encoding="utf-8").replace("Machine draft.", "PI-edited claim."),
        encoding="utf-8",
    )
    observed = observe_pi_edit_from_head(vault, note_rel, machine="pi-machine")
    check = mark_checked(vault, note_rel, machine="pi-machine")
    result = curate_note_candidate(
        vault,
        note_rel,
        "accepted",
        reason="PI edited then accepted",
        machine="curator",
    )

    assert observed["actor"] == "pi"
    assert check["status"] == "passed"
    assert result["status"] == "accepted"
    assert read_frontmatter(note)["status"] == "accepted"
    assert "PI-edited claim." in note.read_text(encoding="utf-8")


def test_curate_note_candidate_rejects_non_candidate_status(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    _md(
        vault / "knowledge/notes/already.md",
        "type: note\ncheck_status: checked\ntitle: Already\nstatus: accepted\n",
    )

    try:
        curate_note_candidate(vault, "already", "rejected", machine="curator")
    except ValueError as exc:
        assert "not a candidate note" in str(exc)
    else:
        raise AssertionError("curating an accepted note should fail")


def test_curate_note_link_records_typed_link_on_checked_note(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    _md(
        vault / "knowledge/notes/source.md",
        "type: note\ncheck_status: checked\ntitle: Source\nstatus: accepted\n",
    )
    _md(
        vault / "knowledge/notes/target.md",
        "type: note\ncheck_status: checked\ntitle: Target\nstatus: accepted\n",
    )

    result = curate_note_link(
        vault,
        "source",
        "supports",
        "target",
        reason="PI linked claims",
        machine="curator",
    )

    source_fm = read_frontmatter(vault / "knowledge/notes/source.md")
    assert source_fm["links"] == {"supports": ["knowledge/notes/target.md"]}
    assert result["source_note_path"] == "knowledge/notes/source.md"
    assert result["target_path"] == "knowledge/notes/target.md"
    assert result["link_type"] == "supports"
    assert result["changed"] is True
    event = list(iter_jsonl(vault / "journal/curator.jsonl"))[-1]
    assert event["event"] == "resolved"
    assert event["operation"] == "curate-note-link"
    assert event["linked_id"] == "knowledge/notes/target.md"
    assert event["reason"] == "PI linked claims"
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {"journal/curator.jsonl", "knowledge/notes/source.md"}


def _md(path: Path, frontmatter: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}---\nBody.\n", encoding="utf-8")


def test_analyze_gaps_names_mismatches_and_seed_terms(tmp_path: Path) -> None:
    _md(
        tmp_path / "catalog/sources/source-alpha/source.md",
        "type: source\ncheck_status: checked\ntitle: Alpha\ndescription: Alpha\ntags: [sleep]\n",
    )
    _md(
        tmp_path / "knowledge/digests/source-alpha.md",
        "type: digest\ncheck_status: checked\ntitle: Alpha digest\n"
        "description: Alpha\nsource_id: catalog/sources/source-alpha\ntags: [sleep]\n",
    )
    for idx in range(2):
        _md(
            tmp_path / f"knowledge/notes/warrant-{idx}.md",
            f"type: note\ncheck_status: checked\ntitle: Warrant {idx}\ntags: [warrant]\n",
        )
    _md(
        tmp_path / "catalog/sources/balanced/source.md",
        "type: source\ncheck_status: checked\ntitle: Balanced\ndescription: Balanced\n"
        "tags: [balanced]\n",
    )
    _md(
        tmp_path / "knowledge/notes/balanced.md",
        "type: note\ncheck_status: checked\ntitle: Balanced note\ntags: [balanced]\n",
    )
    _md(
        tmp_path / "catalog/sources/thin/source.md",
        "type: source\ncheck_status: checked\ntitle: Thin\ndescription: Thin\ntags: [thin]\n",
    )
    _md(
        tmp_path / "catalog/sources/unchecked/source.md",
        "type: source\ncheck_status: unchecked\ntitle: Unchecked\ndescription: Unchecked\n"
        "tags: [unchecked-only]\n",
    )
    _md(
        tmp_path / "catalog/sources/retracted/source.md",
        "type: source\ncheck_status: checked\ntitle: Retracted\ndescription: Retracted\n"
        "lifecycle: retracted\ntags: [stale-only]\n",
    )
    for idx in range(2):
        _md(
            tmp_path / f"knowledge/notes/candidate-{idx}.md",
            f"type: note\ncheck_status: checked\ntitle: Candidate {idx}\n"
            "status: candidate\ntags: [candidate-only]\n",
        )

    result = analyze_gaps(tmp_path, seed_terms=["new area"], dense_threshold=2)

    gaps = {gap["topic"]: gap for gap in result["gaps"]}
    assert set(gaps) == {"sleep", "warrant", "new area"}
    assert gaps["sleep"]["gap_type"] == "undigested"
    assert gaps["sleep"]["source_count"] == 1
    assert gaps["sleep"]["digest_count"] == 1
    assert gaps["sleep"]["note_count"] == 0
    assert gaps["warrant"]["gap_type"] == "under-warranted"
    assert gaps["warrant"]["note_count"] == 2
    assert gaps["new area"]["gap_type"] == "new-topic"
    assert result["checked_topics"] == 5


def test_analyze_project_argument_reads_checked_note_links(tmp_path: Path) -> None:
    _md(
        tmp_path / "knowledge/projects/project-alpha.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n"
        "description: Project\nthesis: knowledge/notes/thesis.md\n",
    )
    _md(
        tmp_path / "knowledge/notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\nstatus: accepted\n",
    )
    _md(
        tmp_path / "knowledge/notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Support\nstatus: accepted\n"
        "links:\n  supports:\n    - knowledge/notes/thesis.md\n",
    )
    _md(
        tmp_path / "knowledge/notes/refute.md",
        "type: note\ncheck_status: checked\ntitle: Refute\nstatus: accepted\n"
        "links:\n  contradicts:\n    - knowledge/notes/thesis.md\n",
    )
    _md(
        tmp_path / "knowledge/notes/candidate.md",
        "type: note\ncheck_status: checked\ntitle: Candidate\nstatus: candidate\n"
        "links:\n  supports:\n    - knowledge/notes/thesis.md\n",
    )

    result = analyze_project_argument(tmp_path, "project-alpha")

    assert result["project_path"] == "knowledge/projects/project-alpha.md"
    assert result["thesis_path"] == "knowledge/notes/thesis.md"
    assert result["argument_stage"] == "developing"
    assert result["relation_count"] == 2
    assert result["supports_count"] == 1
    assert result["contradicts_count"] == 1
    assert result["extends_count"] == 0
    assert result["evidence_saturation"] == "unsaturated"
    assert result["displayed_confidence"] == "below-threshold"
    assert result["saturation_conditions"] == {
        "mature_graph": False,
        "has_support": True,
        "has_refutation": True,
    }
    assert {node["path"] for node in result["nodes"]} == {
        "knowledge/notes/thesis.md",
        "knowledge/notes/support.md",
        "knowledge/notes/refute.md",
    }
    assert result["findings"] == [{"kind": "thin-argument", "severity": "medium"}]
    assert [row["kind"] for row in result["gap_findings"]] == ["conflict"]
    assert [row["kind"] for row in result["advisories"]] == ["structural"]


def test_write_project_argument_canvas_projects_checked_note_links(tmp_path: Path) -> None:
    _md(
        tmp_path / "knowledge/projects/project-alpha.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n"
        "description: Project\nthesis: knowledge/notes/thesis.md\n",
    )
    _md(
        tmp_path / "knowledge/notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\nstatus: accepted\n",
    )
    _md(
        tmp_path / "knowledge/notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Support\nstatus: accepted\n"
        "links:\n  supports:\n    - knowledge/notes/thesis.md\n",
    )

    result = write_project_argument_canvas(tmp_path, "project-alpha")

    assert result["canvas_path"] == "knowledge/projects/project-alpha/argument.canvas"
    assert result["node_count"] == 2
    assert result["edge_count"] == 1
    canvas = json.loads((tmp_path / result["canvas_path"]).read_text(encoding="utf-8"))
    assert {node["file"] for node in canvas["nodes"]} == {
        "knowledge/notes/thesis.md",
        "knowledge/notes/support.md",
    }
    assert canvas["edges"][0]["label"] == "supports"
