from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.capture import capture_source
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.knowledge import (
    analyze_gaps,
    analyze_project_argument,
    curate_note_candidate,
    curate_note_link,
    emit_note_candidates,
    frame_project_paper,
    write_project_argument_canvas,
    write_project_export,
)
from memoria_vault.runtime.operations import compile_source_digest
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.search_index import rebuild_checked_qmd_source
from memoria_vault.runtime.trusted_writer import mark_checked, observe_pi_edit_from_head
from memoria_vault.runtime.vaultio import read_frontmatter

ROOT = Path(__file__).resolve().parent.parent


def workspace(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "vault-template/.memoria/schemas", tmp_path / ".memoria/schemas")
    shutil.copytree(ROOT / "vault-template/.memoria/config", tmp_path / ".memoria/config")
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


def _fake_qmd_query(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    npm_root = tmp_path / "npm-global"
    npm_bin = npm_root / "bin"
    npm_bin.mkdir(parents=True)
    npm = bin_dir / "npm"
    npm.write_text(f"#!{sys.executable}\nprint({str(npm_root)!r})\n", encoding="utf-8")
    qmd = npm_bin / "qmd"
    qmd.write_text(
        f"#!{sys.executable}\n"
        "import json\n"
        "print(json.dumps([\n"
        "    {'file': 'qmd://memoria-checked/works/source-alpha.md', 'score': 8}\n"
        "]))\n",
        encoding="utf-8",
    )
    npm.chmod(0o755)
    qmd.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")


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
    assert fm["source_id"] == "catalog/sources/source-alpha"
    assert fm["evidence_set"] == ["catalog/sources/source-alpha"]
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
    assert committed == {state.JOURNAL_HEAD_REL, note_rel}


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
        "source_id": "catalog/sources/pdf-source",
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
        reason="PI approved",
        machine="curator",
    )

    note_rel = notes["note_paths"][0]
    assert result["note_path"] == note_rel
    assert result["status"] == "accepted"
    assert "status" not in read_frontmatter(vault / note_rel)
    assert state.note_curation_status(vault, note_rel) == "accepted"
    assert "The body stays intact." in (vault / note_rel).read_text(encoding="utf-8")
    event = list(iter_jsonl(vault / "journal/curator.jsonl"))[-1]
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
        vault / "knowledge/notes/already.md",
        "type: note\ncheck_status: checked\ntitle: Already\n",
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
    assert committed == {state.JOURNAL_HEAD_REL, "knowledge/notes/source.md"}


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
        if parent.name in {"catalog", "knowledge", "capabilities"}:
            return parent.parent
    return path.parent


def test_analyze_gaps_names_mismatches_and_seed_terms(tmp_path: Path) -> None:
    _md(
        tmp_path / "catalog/sources/source-alpha/source.md",
        "type: source\ncheck_status: checked\ntitle: Alpha\ndescription: Alpha\ntags: [sleep]\n",
    )
    _md(
        tmp_path / "knowledge/works/source-alpha.md",
        "type: work\ncheck_status: checked\ntitle: Alpha digest\n"
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
        path = tmp_path / f"knowledge/notes/candidate-{idx}.md"
        _md(
            path,
            f"type: note\ncheck_status: checked\ntitle: Candidate {idx}\ntags: [candidate-only]\n",
        )
        state.append_journal_event(
            tmp_path,
            {
                "event": "derived",
                "operation": "propose-note-candidates",
                "output_id": path.relative_to(tmp_path).as_posix(),
            },
        )

    result = analyze_gaps(tmp_path, seed_terms=["new area"], dense_threshold=2)

    gaps = {gap["topic"]: gap for gap in result["gaps"]}
    assert set(gaps) == {"sleep", "warrant", "new area"}
    assert gaps["sleep"]["gap_type"] == "undigested"
    assert gaps["sleep"]["source_count"] == 1
    assert gaps["sleep"]["digest_count"] == 1
    assert gaps["sleep"]["note_count"] == 0
    _assert_gap_contract(gaps["sleep"], "undigested")
    assert gaps["warrant"]["gap_type"] == "under-warranted"
    assert gaps["warrant"]["note_count"] == 2
    _assert_gap_contract(gaps["warrant"], "under-warranted")
    assert gaps["new area"]["gap_type"] == "new-topic"
    _assert_gap_contract(gaps["new area"], "new-topic")
    assert result["summary"]["total"] == 3
    assert result["summary"]["by_severity"]["high"] == 2
    assert result["saturation"]["ready"] is False
    assert result["checked_topics"] == 5


def test_analyze_gaps_counts_checked_sqlite_catalog_source_terms(tmp_path: Path) -> None:
    state.upsert_catalog_record(
        tmp_path,
        source_id="db-alpha",
        title="DB Alpha",
        text_status="full-text",
        check_status="checked",
        csl_json={"memoria": {"topics": ["catalog-only"]}},
    )
    state.upsert_catalog_record(
        tmp_path,
        source_id="db-archived",
        title="DB Archived",
        text_status="full-text",
        check_status="checked",
        csl_json={"memoria": {"topics": ["archived-only"], "standing": "archived"}},
    )
    state.upsert_catalog_record(
        tmp_path,
        source_id="db-unchecked",
        title="DB Unchecked",
        text_status="full-text",
        check_status="unchecked",
        csl_json={"memoria": {"topics": ["unchecked-only"]}},
    )
    state.replace_work_graph_edges(
        tmp_path,
        "db-alpha",
        [
            {
                "relation_type": "topic",
                "target_id": "https://openalex.org/T1",
                "source_provider": "openalex",
                "raw": {"subfield": {"display_name": "Graph-only Topic"}},
            },
            {
                "relation_type": "keyword",
                "target_id": "https://openalex.org/K1",
                "target_title": "Graph-only Keyword",
                "source_provider": "openalex",
            },
        ],
    )
    state.replace_work_graph_edges(
        tmp_path,
        "db-archived",
        [
            {
                "relation_type": "topic",
                "target_id": "https://openalex.org/T2",
                "source_provider": "openalex",
                "raw": {"subfield": {"display_name": "Archived graph"}},
            }
        ],
    )

    result = analyze_gaps(tmp_path, dense_threshold=1)

    gaps = {gap["topic"]: gap for gap in result["gaps"]}
    assert set(gaps) == {"Graph-only Keyword", "Graph-only Topic", "catalog-only"}
    assert gaps["catalog-only"]["gap_type"] == "undigested"
    assert gaps["catalog-only"]["source_count"] == 1
    assert gaps["catalog-only"]["digest_count"] == 0
    assert gaps["catalog-only"]["note_count"] == 0
    assert gaps["Graph-only Topic"]["gap_type"] == "undigested"
    assert gaps["Graph-only Topic"]["source_count"] == 1
    assert gaps["Graph-only Topic"]["digest_count"] == 0
    assert gaps["Graph-only Topic"]["note_count"] == 0
    assert gaps["Graph-only Keyword"]["gap_type"] == "undigested"
    assert gaps["Graph-only Keyword"]["source_count"] == 1
    assert gaps["Graph-only Keyword"]["digest_count"] == 0
    assert gaps["Graph-only Keyword"]["note_count"] == 0


def test_analyze_gaps_uses_qmd_graph_for_discovery_candidates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = workspace(tmp_path / "vault")
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "rare alpha full text for qmd-backed gap analysis",
        machine="capture-machine",
    )
    state.replace_work_graph_edges(
        vault,
        "source-alpha",
        [
            {
                "relation_type": "references",
                "target_id": "https://openalex.org/W999",
                "target_title": "Beta Work",
                "target_doi": "10.1000/beta",
                "source_provider": "openalex",
            }
        ],
    )
    rebuild_checked_qmd_source(vault)
    _fake_qmd_query(tmp_path, monkeypatch)

    result = analyze_gaps(
        vault,
        seed_terms=["rare alpha"],
        dense_threshold=1,
        machine="gap-machine",
    )

    gap = {row["topic"]: row for row in result["gaps"]}["rare alpha"]
    assert gap["gap_type"] == "undigested"
    _assert_gap_contract(gap, "undigested")
    assert gap["retrieval_engine"] == "qmd"
    assert gap["retrieval_sources"][0]["path"] == "works/source-alpha.md"
    citation_gap = {row["topic"]: row for row in result["gaps"]}[
        "Citation neighborhood: Alpha Source"
    ]
    _assert_gap_contract(citation_gap, "citation-neighborhood")
    assert citation_gap["candidate_work_ids"] == ["https://openalex.org/W999"]
    assert result["citation_neighborhood_gap_count"] == 1
    assert result["discovery_candidate_paths"] == [
        "inbox/candidate-work-source-alpha-references-https___openalex.org_W999.md"
    ]
    candidate = vault / result["discovery_candidate_paths"][0]
    fm = read_frontmatter(candidate)
    assert fm["attention_kind"] == "candidate"
    assert fm["raised_by"] == "analyze-gaps"
    assert fm["discovered_work_id"] == "https://openalex.org/W999"
    assert "check_status" not in fm
    assert state.catalog_source(vault, "https://openalex.org/W999") is None
    committed = set(
        git(vault, "show", "--name-only", "--format=", result["discovery_commit"]).splitlines()
    )
    assert committed == {
        "inbox/candidate-work-source-alpha-references-https___openalex.org_W999.md",
        state.JOURNAL_HEAD_REL,
    }


def test_analyze_gaps_proposes_candidates_from_sqlite_source_gaps_without_qmd(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path / "vault")
    state.upsert_catalog_record(
        vault,
        source_id="db-alpha",
        title="DB Alpha",
        text_status="full-text",
        check_status="checked",
        csl_json={"memoria": {"topics": ["catalog-only"]}},
    )
    state.replace_work_graph_edges(
        vault,
        "db-alpha",
        [
            {
                "relation_type": "related",
                "target_id": "https://openalex.org/W777",
                "target_title": "Gamma Work",
                "target_doi": "10.1000/gamma",
                "source_provider": "openalex",
            }
        ],
    )

    result = analyze_gaps(vault, dense_threshold=1, machine="gap-machine")

    gap = {row["topic"]: row for row in result["gaps"]}["catalog-only"]
    _assert_gap_contract(gap, "undigested")
    assert gap["source_ids"] == ["db-alpha"]
    assert gap["discovery_candidate_paths"] == [
        "inbox/candidate-work-db-alpha-related-https___openalex.org_W777.md"
    ]
    citation_gap = {row["topic"]: row for row in result["gaps"]}["Citation neighborhood: DB Alpha"]
    _assert_gap_contract(citation_gap, "citation-neighborhood")
    assert citation_gap["candidate_work_ids"] == ["https://openalex.org/W777"]
    assert result["citation_neighborhood_gap_count"] == 1
    assert result["discovery_candidate_paths"] == gap["discovery_candidate_paths"]
    candidate = vault / result["discovery_candidate_paths"][0]
    fm = read_frontmatter(candidate)
    assert fm["raised_by"] == "analyze-gaps"
    assert fm["discovered_work_id"] == "https://openalex.org/W777"
    assert "check_status" not in fm
    assert state.catalog_source(vault, "https://openalex.org/W777") is None


def test_analyze_gaps_reports_missing_full_text(tmp_path: Path) -> None:
    vault = workspace(tmp_path / "vault")
    state.upsert_catalog_record(
        vault,
        source_id="unchecked-metadata",
        title="Unchecked Metadata",
        text_status="metadata-only",
        check_status="unchecked",
    )
    state.upsert_catalog_record(
        vault,
        source_id="metadata-only",
        title="Metadata Only",
        text_status="metadata-only",
        check_status="checked",
    )

    result = analyze_gaps(vault, machine="gap-machine")

    assert result["full_text_gap_count"] == 1
    gap = result["gaps"][0]
    _assert_gap_contract(gap, "full-text-missing")
    assert gap["source_id"] == "metadata-only"
    assert "unchecked-metadata" not in json.dumps(result["gaps"])
    assert result["full_text_attention_paths"] == ["inbox/flag-gap-full-text-metadata-only.md"]
    attention = vault / result["full_text_attention_paths"][0]
    fm = read_frontmatter(attention)
    assert fm["attention_kind"] == "flag"
    assert fm["raised_by"] == "analyze-gaps"
    assert fm["target"] == "catalog/sources/metadata-only"
    committed = set(
        git(
            vault,
            "show",
            "--name-only",
            "--format=",
            result["full_text_attention_commit"],
        ).splitlines()
    )
    assert committed == {
        "inbox/flag-gap-full-text-metadata-only.md",
        state.JOURNAL_HEAD_REL,
    }


def test_analyze_project_argument_reads_checked_note_links(tmp_path: Path) -> None:
    _md(
        tmp_path / "knowledge/projects/project-alpha.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n"
        "description: Project\nthesis: knowledge/notes/thesis.md\n",
    )
    _md(
        tmp_path / "knowledge/notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\n",
    )
    _md(
        tmp_path / "knowledge/notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Support\n"
        "links:\n  supports:\n    - knowledge/notes/thesis.md\n",
    )
    _md(
        tmp_path / "knowledge/notes/refute.md",
        "type: note\ncheck_status: checked\ntitle: Refute\n"
        "links:\n  contradicts:\n    - knowledge/notes/thesis.md\n",
    )
    candidate = tmp_path / "knowledge/notes/candidate.md"
    _md(
        candidate,
        "type: note\ncheck_status: checked\ntitle: Candidate\n"
        "links:\n  supports:\n    - knowledge/notes/thesis.md\n",
    )
    state.append_journal_event(
        tmp_path,
        {
            "event": "derived",
            "operation": "propose-note-candidates",
            "output_id": candidate.relative_to(tmp_path).as_posix(),
        },
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


def test_analyze_gaps_adds_project_argument_health(tmp_path: Path) -> None:
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

    result = analyze_gaps(tmp_path, project_path="project-alpha")

    assert result["project_path"] == "knowledge/projects/project-alpha.md"
    assert result["thesis_path"] == "knowledge/notes/thesis.md"
    assert result["argument_stage"] == "developing"
    assert result["argument_gap_count"] == 2
    assert result["paper_readiness_gap_count"] == 1
    gaps = {gap["finding_kind"]: gap for gap in result["gaps"] if "finding_kind" in gap}
    _assert_gap_contract(gaps["thin-argument"], "argument-unsupported")
    assert gaps["thin-argument"]["note_count"] == 3
    _assert_gap_contract(gaps["conflict"], "argument-fragile")
    assert gaps["conflict"]["advice"] == "resolve or preserve the contradiction"
    paper_gap = next(gap for gap in result["gaps"] if gap["kind"] == "paper-readiness")
    assert "target" in paper_gap["missing"]
    assert result["saturation"] == {
        "claims": 1,
        "saturated": 1,
        "unsupported": 0,
        "uncountered": 0,
        "ready": True,
        "claim_saturation": [
            {
                "claim": "knowledge/notes/thesis.md",
                "has_support": True,
                "has_counterpoint": True,
                "saturated": True,
            }
        ],
        "conditions": {
            "mature_graph": False,
            "has_support": True,
            "has_refutation": True,
        },
        "evidence_saturation": "unsaturated",
    }


def test_analyze_gaps_seeds_project_scope_and_thesis_terms(tmp_path: Path) -> None:
    _md(
        tmp_path / "knowledge/projects/project-alpha.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n"
        "description: Project\nthesis: knowledge/notes/thesis.md\n"
        "scope_topics: [sensemaking]\n"
        "facets:\n"
        "  methodology: [qualitative]\n",
    )
    _md(
        tmp_path / "knowledge/notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\nstatus: accepted\n"
        "keywords: [patient-generated-data]\n"
        "facets:\n"
        "  topics: [care coordination]\n",
    )

    result = analyze_gaps(tmp_path, project_path="project-alpha", dense_threshold=1)

    gaps = {gap["topic"]: gap for gap in result["gaps"]}
    assert gaps["sensemaking"]["gap_type"] == "new-topic"
    assert gaps["qualitative"]["gap_type"] == "new-topic"
    assert gaps["patient-generated-data"]["gap_type"] == "under-warranted"
    assert gaps["patient-generated-data"]["note_count"] == 1
    assert gaps["care coordination"]["gap_type"] == "under-warranted"


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


def test_write_project_export_renders_checked_project_markdown(tmp_path: Path) -> None:
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
        tmp_path / "knowledge/hubs/alpha-hub.md",
        "type: hub\ncheck_status: checked\ntitle: Alpha hub\n"
        "description: Curated project context\nproject: knowledge/projects/project-alpha.md\n",
    )
    (tmp_path / "references.bib").write_text("@article{alpha,title={Alpha}}\n", encoding="utf-8")

    result = write_project_export(
        tmp_path,
        "project-alpha",
        output_path="exports/project-alpha.md",
    )

    assert result["project_path"] == "knowledge/projects/project-alpha.md"
    assert result["format"] == "markdown"
    assert result["output_path"] == "exports/project-alpha.md"
    assert result["content"] == ""
    text = (tmp_path / result["output_path"]).read_text(encoding="utf-8")
    assert "# Alpha project" in text
    assert "## Argument Snapshot" in text
    assert "- Thesis: `knowledge/notes/thesis.md`" in text
    assert "- Support --supports--> Thesis" in text
    assert "- Alpha hub: `knowledge/hubs/alpha-hub.md` -- Curated project context" in text
    assert "```bibtex\n@article{alpha,title={Alpha}}\n```" in text


def _valid_paper_plan() -> dict[str, object]:
    return {
        "target": "Journal of Testable Systems",
        "audience": "local-first tool builders",
        "research_question": "Can Memoria support standalone CLI research?",
        "central_contribution": "A checked CLI loop can produce usable evidence.",
        "gap_statement": "Existing PKM loops lack local checked export.",
        "claim_evidence_map": {"CLI loop works": "knowledge/notes/support.md"},
        "figure_plan": {"Figure 1": "CLI loop stages"},
        "limitations": "Single-corpus dogfood run.",
    }


def test_frame_project_paper_records_plan_and_leaves_project_unchecked(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    project = vault / "knowledge/projects/project-alpha.md"
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
    _checked(vault, "knowledge/projects/project-alpha.md", "project")

    result = frame_project_paper(
        vault,
        "project-alpha",
        paper_plan=_valid_paper_plan(),
        machine="frame-test",
        run_id="frame-run",
    )

    assert result["project_path"] == "knowledge/projects/project-alpha.md"
    assert result["check_status"] == "unchecked"
    frontmatter = read_frontmatter(project)
    assert frontmatter["paper_plan"]["research_question"].startswith("Can Memoria")
    assert frontmatter["outcome_frame"] == {
        "kind": "paper",
        "target": "Journal of Testable Systems",
        "audience": "local-first tool builders",
        "research_question": "Can Memoria support standalone CLI research?",
        "status": "framed",
    }
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL, "knowledge/projects/project-alpha.md"}


def test_ready_only_export_requires_paper_plan_and_checked_support(tmp_path: Path) -> None:
    vault = tmp_path
    _md(
        vault / "knowledge/projects/project-alpha.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n"
        "description: Project\nthesis: knowledge/notes/thesis.md\n",
    )
    _md(
        vault / "knowledge/notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\n",
    )
    with pytest.raises(ValueError, match="target"):
        write_project_export(vault, "project-alpha", ready_only=True)

    project = vault / "knowledge/projects/project-alpha.md"
    frontmatter, body = project.read_text(encoding="utf-8").split("---\n", 2)[1:]
    project.write_text(
        "---\n"
        + frontmatter
        + "paper_plan:\n"
        + "  target: Journal of Testable Systems\n"
        + "  audience: local-first tool builders\n"
        + "  research_question: Can Memoria support standalone CLI research?\n"
        + "  central_contribution: A checked CLI loop can produce usable evidence.\n"
        + "  gap_statement: Existing PKM loops lack local checked export.\n"
        + "  claim_evidence_map:\n"
        + "    CLI loop works: knowledge/notes/support.md\n"
        + "  figure_plan:\n"
        + "    Figure 1: CLI loop stages\n"
        + "  limitations: Single-corpus dogfood run.\n"
        + "---\n"
        + body,
        encoding="utf-8",
    )
    _checked(vault, "knowledge/projects/project-alpha.md", "project")
    _md(
        vault / "knowledge/notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Support\n"
        "links:\n  supports:\n    - knowledge/notes/thesis.md\n",
    )

    result = write_project_export(vault, "project-alpha", ready_only=True)

    assert result["readiness"]["ready"] is True
    assert result["readiness"]["status"] == "export-ready"
    assert "# Alpha project" in result["content"]
    assert "## Paper Plan" in result["content"]


def test_write_project_export_requires_pandoc_for_non_markdown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _md(
        tmp_path / "knowledge/projects/project-alpha.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n",
    )
    monkeypatch.setattr("memoria_vault.runtime.knowledge.shutil.which", lambda _name: None)

    with pytest.raises(RuntimeError, match="Pandoc is required"):
        write_project_export(
            tmp_path,
            "project-alpha",
            export_format="docx",
            output_path="exports/project-alpha.docx",
        )
