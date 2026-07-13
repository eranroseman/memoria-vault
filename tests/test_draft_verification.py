from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.knowledge import analyze_gaps as _analyze_gaps
from memoria_vault.runtime.knowledge import (
    compose_project_draft as _compose_project_draft,
)
from memoria_vault.runtime.knowledge import (
    resolve_evidence_review as _resolve_evidence_review,
)
from memoria_vault.runtime.knowledge import (
    verify_project_draft as _verify_project_draft,
)
from memoria_vault.runtime.knowledge import (
    write_project_export as _write_project_export,
)
from tests.helpers import call_with_context, operation_context, write_checked_concept


def compose_project_draft(vault: Path, *args, **kwargs):
    return call_with_context(_compose_project_draft, vault, *args, **kwargs)


def analyze_gaps(vault: Path, *args, **kwargs):
    return call_with_context(_analyze_gaps, vault, *args, **kwargs)


def resolve_evidence_review(vault: Path, *args, **kwargs):
    kwargs.setdefault("actor", "pi")
    kwargs.setdefault("machine", "test-machine")
    return _resolve_evidence_review(vault, *args, **kwargs)


def verify_project_draft(vault: Path, *args, **kwargs):
    return call_with_context(_verify_project_draft, vault, *args, **kwargs)


def write_project_export(vault: Path, *args, **kwargs):
    return call_with_context(_write_project_export, vault, *args, **kwargs)


def test_compose_rejects_forged_context_before_draft_or_evidence_mutation(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    _project(vault)
    write_checked_concept(
        vault,
        "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\nid: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
        "note",
        body="A claim that must not be composed under forged provenance.",
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — Thesis\n")
    context = operation_context(vault, operation_id="compose-project-draft")
    forged = replace(context, actor="integrity")

    with pytest.raises(ValueError, match="context"):
        _compose_project_draft(vault, "project-alpha", context=forged)

    assert not (vault / "projects/project-alpha/draft.md").exists()
    assert state.evidence_sets(vault) == []


def test_verify_rejects_forged_context_before_evidence_rebuild(tmp_path: Path) -> None:
    vault = tmp_path
    _project(vault)
    write_checked_concept(
        vault,
        "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\nid: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
        "note",
        body="A claim with an evidence marker.",
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — Thesis\n")
    compose_project_draft(vault, "project-alpha", run_id="compose-run")
    before = state.evidence_sets(vault)
    context = operation_context(vault, operation_id="verify-project-draft")
    forged = replace(context, run_id="forged-run")

    with pytest.raises(ValueError, match="context"):
        _verify_project_draft(vault, "project-alpha", context=forged)

    assert state.evidence_sets(vault) == before


def test_verified_source_backed_draft_exports_without_internal_markers(tmp_path: Path) -> None:
    vault = tmp_path
    state.upsert_catalog_record(
        vault,
        work_id="source-alpha",
        title="Alpha Source",
        check_status="checked",
        content_path=".memoria/blobs/source-content/source-alpha.md",
    )
    _source_span(vault, "source-alpha")
    _project(vault)
    write_checked_concept(
        vault,
        "notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Support\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FA2\nwork_id: catalog/sources/source-alpha\n",
        "note",
        body="This source-backed claim can be exported.",
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA2 — Support\n")
    compose_project_draft(vault, "project-alpha")

    verification = verify_project_draft(
        vault,
        "project-alpha",
        run_id="verify-project-request-run",
    )
    exported = write_project_export(vault, "project-alpha", draft=True)

    assert verification["ready"] is True
    assert verification["findings"] == []
    assert {row["run_id"] for row in verification["evidence_sets"]} == {
        "verify-project-request-run"
    }
    assert "This source-backed claim can be exported." in exported["content"]
    assert "[@source-alpha]" in exported["content"]
    assert "%%ev:" not in exported["content"]
    assert "^blk-" not in exported["content"]


def test_unclean_draft_refuses_export_with_evidence_reason(tmp_path: Path) -> None:
    vault = tmp_path
    _project(vault)
    write_checked_concept(
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
        work_id="source-alpha",
        title="Alpha Source",
        check_status="checked",
        content_path=".memoria/blobs/source-content/source-alpha.md",
    )
    _source_span(vault, "source-alpha")
    _project(vault)
    write_checked_concept(
        vault,
        "notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Support\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FA2\nwork_id: catalog/sources/source-alpha\n",
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
        work_id="source-alpha",
        title="Alpha Source",
        check_status="checked",
        content_path=".memoria/blobs/source-content/source-alpha.md",
    )
    _source_span(vault, "source-alpha")
    _project(vault)
    write_checked_concept(
        vault,
        "notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Support\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FA2\nwork_id: catalog/sources/source-alpha\n",
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
        work_id="source-alpha",
        title="Alpha Source",
        check_status="checked",
        content_path=".memoria/blobs/source-content/source-alpha.md",
    )
    _source_span(vault, "source-alpha")
    _project(vault)
    write_checked_concept(
        vault,
        "notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Support\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FA2\nwork_id: catalog/sources/source-alpha\n",
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
    write_checked_concept(
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


def test_regular_export_with_existing_draft_uses_export_context_for_readiness(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    _project(vault)
    write_checked_concept(
        vault,
        "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\nid: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
        "note",
        body="This implicit claim remains visible in the regular export.",
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — Thesis\n")
    compose_project_draft(vault, "project-alpha")

    exported = write_project_export(
        vault,
        "project-alpha",
        run_id="export-project-request-run",
    )

    assert exported["readiness"]["ready"] is False
    assert {row["run_id"] for row in state.evidence_sets(vault)} == {"export-project-request-run"}


def test_gap_analysis_with_existing_draft_uses_analysis_context_for_readiness(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    _project(vault)
    write_checked_concept(
        vault,
        "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\nid: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
        "note",
        body="This implicit claim contributes a paper-readiness gap.",
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — Thesis\n")
    compose_project_draft(vault, "project-alpha")

    result = analyze_gaps(
        vault,
        project_path="project-alpha",
        run_id="analyze-gaps-request-run",
    )

    assert result["paper_readiness_gap_count"] == 1
    assert {row["run_id"] for row in state.evidence_sets(vault)} == {"analyze-gaps-request-run"}


def _project(vault: Path) -> None:
    write_checked_concept(
        vault,
        "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n",
        "project",
    )


def _outline(vault: Path, content: str) -> None:
    path = vault / "projects/project-alpha/outline.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _source_span(vault: Path, work_id: str) -> None:
    path = vault / f".memoria/blobs/source-content/{work_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{work_id} source span. ^p0001\n", encoding="utf-8")
