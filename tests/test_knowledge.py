from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.capture import capture_source as _capture_source
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.knowledge import (
    curate_note_candidate as _curate_note_candidate,
)
from memoria_vault.runtime.knowledge import (
    curate_note_link as _curate_note_link,
)
from memoria_vault.runtime.knowledge import (
    emit_note_candidates as _emit_note_candidates,
)
from memoria_vault.runtime.operations import compile_source_digest as _compile_source_digest
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.trusted_writer import mark_checked as _mark_checked
from memoria_vault.runtime.trusted_writer import observe_pi_edit_from_head
from memoria_vault.runtime.vaultio import read_frontmatter
from tests.helpers import call_with_context, copy_memoria_dirs, git, init_git, operation_context


def _call(function, vault: Path, *args, **kwargs):
    return call_with_context(function, vault, *args, **kwargs)


def capture_source(vault: Path, *args, **kwargs):
    return _call(_capture_source, vault, *args, **kwargs)


def curate_note_candidate(vault: Path, *args, **kwargs):
    return _call(_curate_note_candidate, vault, *args, **kwargs)


def curate_note_link(vault: Path, *args, **kwargs):
    return _call(_curate_note_link, vault, *args, **kwargs)


def emit_note_candidates(vault: Path, *args, **kwargs):
    context = operation_context(
        vault,
        operation_id="propose-note-candidates",
        machine=str(kwargs.pop("machine", "test-machine") or "test-machine"),
        run_id=str(kwargs.pop("run_id", "test-run") or "test-run"),
    )
    return _emit_note_candidates(vault, *args, context=context, **kwargs)


def compile_source_digest(vault: Path, *args, **kwargs):
    return _call(_compile_source_digest, vault, *args, **kwargs)


def mark_checked(vault: Path, *args, **kwargs):
    return _call(_mark_checked, vault, *args, **kwargs)


def workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas", "config")
    init_git(tmp_path, "knowledge@example.invalid", "Knowledge")
    return tmp_path


def _assert_gap_contract(gap: dict[str, object], kind: str) -> None:
    assert gap["kind"] == kind
    assert gap["gap_type"] == kind
    assert gap["severity"] in {"high", "medium", "low"}
    assert gap["impact"] in {0, 1, 2}
    assert gap["confidence"] in {0, 1, 2}
    assert gap["actionability"] in {0, 1, 2}
    assert gap["score"] == gap["impact"] * gap["confidence"] * gap["actionability"]
    assert isinstance(gap["why"], str) and gap["why"]
    assert isinstance(gap["next_actions"], list)
    assert isinstance(gap["candidate_work_ids"], list)


def _checked(vault: Path, rel: str, concept_type: str) -> None:
    state.record_observed_file_edit(
        vault,
        output_id=rel,
        concept_type=concept_type,
        output_sha256=sha256_file(vault / rel),
    )
    state.set_concept_verdict(vault, rel, "checked")


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
    assert "check_status" not in fm
    assert state.concept_check_status(vault, note_rel) == "checked"
    assert "status" not in fm
    assert state.note_curation_status(vault, note_rel) == "candidate"
    assert fm["work_id"] == "catalog/sources/source-alpha"
    assert "evidence_set" not in fm
    assert "citations" not in fm
    assert fm["claim_text"] == "Framing changes which outcomes matter."

    events = list(iter_jsonl(vault / ".memoria/journal/note-machine.jsonl"))
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
    assert committed == {state.JOURNAL_HEAD_REL, note_rel}


def test_emit_note_candidates_neutralizes_every_model_derived_text_field(
    tmp_path: Path,
) -> None:
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
    candidates = [
        {
            "title": "![Candidate](http://beacon.example/title.png)",
            "description": '<img src="http://beacon.example/description.png">',
            "body": "Body http://beacon.example/body",
            "claim_text": "[claim](http://beacon.example/claim)",
            "quote": "![quote](http://beacon.example/quote.png)",
            "tags": ["[tag](http://beacon.example/tag)"],
            "annotation_ref": {
                "work_id": "catalog/sources/source-alpha",
                "text_quote": "http://beacon.example/annotation",
            },
        }
    ]

    result = emit_note_candidates(
        vault,
        "source-alpha",
        candidates,
        machine="note-machine",
    )

    [note_rel] = result["note_paths"]
    rendered = (vault / note_rel).read_text(encoding="utf-8")
    assert "![" not in rendered
    assert "<img" not in rendered
    assert "](http://beacon.example" not in rendered
    for url in (
        "http://beacon.example/title.png",
        "http://beacon.example/description.png",
        "http://beacon.example/body",
        "http://beacon.example/claim",
        "http://beacon.example/quote.png",
        "http://beacon.example/tag",
        "http://beacon.example/annotation",
    ):
        assert f"`{url}`" in rendered


def test_emit_note_candidate_renders_composed_fenced_title_inert(tmp_path: Path) -> None:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("Pandoc is optional")
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "source-fenced-title",
        "Alpha Source",
        "A fixture source.",
        "Alpha content about framing, methods, outcomes, gaps, and impact.",
        machine="capture-machine",
    )
    compile_source_digest(
        vault,
        "source-fenced-title",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="digest-machine",
    )

    result = emit_note_candidates(
        vault,
        "source-fenced-title",
        [
            {
                "title": '```\n<img src="https://evil.example/candidate-title">\n```',
                "body": "Candidate body.",
            }
        ],
        machine="note-machine",
    )

    [note_rel] = result["note_paths"]
    rendered = subprocess.run(
        [pandoc, "-f", "commonmark", "-t", "html"],
        input=(vault / note_rel).read_text(encoding="utf-8"),
        text=True,
        capture_output=True,
        check=True,
    ).stdout

    assert "<img" not in rendered


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
        "work_id": "catalog/sources/pdf-source",
        "raw_copy_path": ".memoria/blobs/source-content/pdf-source/raw/paper.pdf",
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
        actor="pi",
        reason="PI approved",
        machine="curator",
    )

    note_rel = notes["note_paths"][0]
    assert result["note_path"] == note_rel
    assert result["status"] == "accepted"
    assert "status" not in read_frontmatter(vault / note_rel)
    assert state.note_curation_status(vault, note_rel) == "accepted"
    assert "The body stays intact." in (vault / note_rel).read_text(encoding="utf-8")
    event = list(iter_jsonl(vault / ".memoria/journal/curator.jsonl"))[-1]
    assert event["event"] == "resolved"
    assert event["operation"] == "curate-note-candidate"
    assert event["target_id"] == note_rel
    assert event["resolution"] == "accepted"
    assert event["reason"] == "PI approved"
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL}


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
        actor="pi",
        reason="PI edited then accepted",
        machine="curator",
    )

    assert observed["actor"] == "pi"
    assert check["status"] == "passed"
    assert result["status"] == "accepted"
    assert "status" not in read_frontmatter(note)
    assert state.note_curation_status(vault, note_rel) == "accepted"
    assert "PI-edited claim." in note.read_text(encoding="utf-8")


def test_curate_note_candidate_rejects_non_candidate_status(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    _md(
        vault / "notes/already.md",
        "type: note\ncheck_status: checked\ntitle: Already\n",
    )

    try:
        curate_note_candidate(vault, "already", "rejected", actor="pi", machine="curator")
    except ValueError as exc:
        assert "not a candidate note" in str(exc)
    else:
        raise AssertionError("curating an accepted note should fail")


def test_curate_note_link_records_typed_link_on_checked_note(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    _md(
        vault / "notes/source.md",
        "type: note\ncheck_status: checked\ntitle: Source\nstatus: accepted\n",
    )
    _md(
        vault / "notes/target.md",
        "type: note\ncheck_status: checked\ntitle: Target\nstatus: accepted\n",
    )

    result = curate_note_link(
        vault,
        "source",
        "supports",
        "target",
        actor="pi",
        reason="PI linked claims",
        machine="curator",
    )

    source_fm = read_frontmatter(vault / "notes/source.md")
    assert source_fm["links"] == {"supports": ["notes/target.md"]}
    assert result["source_note_path"] == "notes/source.md"
    assert result["target_path"] == "notes/target.md"
    assert result["link_type"] == "supports"
    assert result["changed"] is True
    event = list(iter_jsonl(vault / ".memoria/journal/curator.jsonl"))[-1]
    assert event["event"] == "resolved"
    assert event["operation"] == "curate-note-link"
    assert event["linked_id"] == "notes/target.md"
    assert event["reason"] == "PI linked claims"
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL, "notes/source.md"}


def _md(path: Path, frontmatter: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}---\nBody.\n", encoding="utf-8")
    fm = read_frontmatter(path)
    status = fm.get("check_status")
    if status in state.CHECK_STATUSES:
        vault = _vault_root(path)
        rel = path.relative_to(vault).as_posix()
        state.record_observed_file_edit(
            vault,
            output_id=rel,
            concept_type=str(fm.get("type") or "note"),
            output_sha256=sha256_file(path),
        )
        state.set_concept_verdict(vault, rel, str(status))


def _vault_root(path: Path) -> Path:
    for parent in path.parents:
        if parent.name in {
            "notes",
            "hubs",
            "projects",
            "digests",
            "fulltext",
            "capabilities",
        }:
            return parent.parent
    return path.parent


def _valid_paper_plan() -> dict[str, object]:
    return {
        "target": "Journal of Testable Systems",
        "audience": "local-first tool builders",
        "research_question": "Can Memoria support standalone CLI research?",
        "central_contribution": "A checked CLI loop can produce usable evidence.",
        "gap_statement": "Existing PKM loops lack local checked export.",
        "claim_evidence_map": {"CLI loop works": "notes/support.md"},
        "figure_plan": {"Figure 1": "CLI loop stages"},
        "limitations": "Single-corpus dogfood run.",
    }
