from __future__ import annotations

from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.knowledge import (
    compose_project_draft,
    resolve_evidence_review,
    verify_project_draft,
    write_project_export,
)
from memoria_vault.runtime.policy.audit import sha256_file


def test_verified_source_backed_draft_exports_without_internal_markers(tmp_path: Path) -> None:
    vault = tmp_path
    state.upsert_catalog_record(
        vault,
        source_id="source-alpha",
        title="Alpha Source",
        check_status="checked",
        content_path=".memoria/blobs/source-content/source-alpha.md",
    )
    _source_span(vault, "source-alpha")
    _project(vault)
    _checked(
        vault,
        "notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Support\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FA2\nsource_id: catalog/sources/source-alpha\n",
        "note",
        body="This source-backed claim can be exported.",
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA2 — Support\n")
    compose_project_draft(vault, "project-alpha")

    verification = verify_project_draft(vault, "project-alpha")
    exported = write_project_export(vault, "project-alpha", draft=True)

    assert verification["ready"] is True
    assert verification["findings"] == []
    assert "This source-backed claim can be exported." in exported["content"]
    assert "[@source-alpha]" in exported["content"]
    assert "%%ev:" not in exported["content"]
    assert "^blk-" not in exported["content"]


def test_unclean_draft_refuses_export_with_evidence_reason(tmp_path: Path) -> None:
    vault = tmp_path
    _project(vault)
    _checked(
        vault,
        "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\nid: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
        "note",
        body="This implicit claim needs review.",
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — Thesis\n")
    compose_project_draft(vault, "project-alpha")

    verification = verify_project_draft(vault, "project-alpha")

    assert verification["ready"] is False
    assert {finding["kind"] for finding in verification["findings"]} == {
        "evidence-incomplete",
        "review-required",
    }
    with pytest.raises(ValueError, match="project draft is not export-ready"):
        write_project_export(vault, "project-alpha", draft=True)


def test_draft_verification_flags_broken_structural_reference(tmp_path: Path) -> None:
    vault = tmp_path
    state.upsert_catalog_record(
        vault,
        source_id="source-alpha",
        title="Alpha Source",
        check_status="checked",
        content_path=".memoria/blobs/source-content/source-alpha.md",
    )
    _source_span(vault, "source-alpha")
    _project(vault)
    _checked(
        vault,
        "notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Support\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FA2\nsource_id: catalog/sources/source-alpha\n",
        "note",
        body="This source-backed claim has a structural reference.",
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA2 — Support\n")
    compose_project_draft(vault, "project-alpha")
    draft = vault / "projects/project-alpha/draft.md"
    draft.write_text(
        draft.read_text(encoding="utf-8").replace(
            "Source note: `notes/support.md`",
            "Source note: `notes/missing.md`",
        ),
        encoding="utf-8",
    )

    verification = verify_project_draft(vault, "project-alpha")

    assert verification["ready"] is False
    assert verification["findings"] == [
        {
            "kind": "broken-structural-reference",
            "severity": "high",
            "reference": "notes/missing.md",
        }
    ]
    with pytest.raises(ValueError, match="broken-structural-reference"):
        write_project_export(vault, "project-alpha", draft=True)


def test_draft_verification_flags_deterministic_number_mismatch(tmp_path: Path) -> None:
    vault = tmp_path
    state.upsert_catalog_record(
        vault,
        source_id="source-alpha",
        title="Alpha Source",
        check_status="checked",
        content_path=".memoria/blobs/source-content/source-alpha.md",
    )
    _source_span(vault, "source-alpha")
    _project(vault)
    _checked(
        vault,
        "notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Support\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FA2\nsource_id: catalog/sources/source-alpha\n",
        "note",
        body="This source-backed claim has a deterministic slice count.",
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA2 — Support\n")
    compose_project_draft(vault, "project-alpha")
    draft = vault / "projects/project-alpha/draft.md"
    draft.write_text(
        draft.read_text(encoding="utf-8").replace(
            "Slice includes 1 checked notes.",
            "Slice includes 2 checked notes.",
        ),
        encoding="utf-8",
    )

    verification = verify_project_draft(vault, "project-alpha")

    assert verification["ready"] is False
    assert verification["findings"] == [
        {
            "kind": "deterministic-number-mismatch",
            "severity": "high",
            "number": "slice_checked_note_count",
            "expected": 1,
            "observed": 2,
        }
    ]


def test_draft_verification_routes_analysis_code_numbers_to_incomplete(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    state.upsert_catalog_record(
        vault,
        source_id="source-alpha",
        title="Alpha Source",
        check_status="checked",
        content_path=".memoria/blobs/source-content/source-alpha.md",
    )
    _source_span(vault, "source-alpha")
    _project(vault)
    _checked(
        vault,
        "notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Support\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FA2\nsource_id: catalog/sources/source-alpha\n",
        "note",
        body="This source-backed claim is clean until analysis code is cited.",
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA2 — Support\n")
    compose_project_draft(vault, "project-alpha")
    draft = vault / "projects/project-alpha/draft.md"
    draft.write_text(
        draft.read_text(encoding="utf-8").rstrip() + "\n\nThe effect size is analysis-computed.\n",
        encoding="utf-8",
    )

    verification = verify_project_draft(vault, "project-alpha")

    assert verification["ready"] is False
    assert verification["findings"] == [
        {"kind": "analysis-number-evidence-incomplete", "severity": "high"}
    ]


def test_evidence_review_disposition_clears_draft_gate(tmp_path: Path) -> None:
    vault = tmp_path
    _project(vault)
    _checked(
        vault,
        "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\nid: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
        "note",
        body="This implicit claim was manually accepted.",
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — Thesis\n")
    result = compose_project_draft(vault, "project-alpha")
    evidence_id = result["evidence_markers"][0]["id"]

    resolve_evidence_review(vault, evidence_id, decision="accept", reason="PI accepted")
    verification = verify_project_draft(vault, "project-alpha")

    assert verification["ready"] is True
    assert verification["findings"] == []


def _project(vault: Path) -> None:
    _checked(
        vault,
        "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n",
        "project",
    )


def _outline(vault: Path, content: str) -> None:
    path = vault / "projects/project-alpha/outline.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _checked(
    vault: Path,
    rel: str,
    frontmatter: str,
    concept_type: str,
    *,
    body: str = "Body.",
) -> None:
    path = vault / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}---\n{body}\n", encoding="utf-8")
    state.record_observed_file_edit(
        vault,
        output_id=rel,
        concept_type=concept_type,
        output_sha256=sha256_file(path),
    )
    state.set_concept_verdict(vault, rel, "checked")


def _source_span(vault: Path, source_id: str) -> None:
    path = vault / f".memoria/blobs/source-content/{source_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{source_id} source span. ^p0001\n", encoding="utf-8")
