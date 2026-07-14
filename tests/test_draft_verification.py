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
    render_project_draft_export_markdown as _render_project_draft_export_markdown,
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


def render_project_draft_export_markdown(vault: Path, *args, **kwargs):
    return call_with_context(_render_project_draft_export_markdown, vault, *args, **kwargs)


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


def test_draft_renderer_and_writer_neutralize_exported_beacons(tmp_path: Path) -> None:
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
        body=(
            "![draft](http://beacon.example/draft.png) "
            "<script>signal()</script> http://beacon.example/bare"
        ),
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA2 — Support\n")
    compose_project_draft(vault, "project-alpha")

    applied = (vault / "projects/project-alpha/draft.md").read_text(encoding="utf-8")
    rendered = render_project_draft_export_markdown(vault, "project-alpha")
    written = write_project_export(vault, "project-alpha", draft=True)

    for content in (applied, rendered["content"], written["content"]):
        assert "![draft]" not in content
        assert "<script>" not in content
        assert "](http://beacon.example" not in content
        assert "`http://beacon.example/draft.png`" in content
        assert "`http://beacon.example/bare`" in content


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


def test_draft_text_drift_overrides_pi_disposition_and_refuses_export(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    _project(vault)
    write_checked_concept(
        vault,
        "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\nid: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
        "note",
        body="The PI accepts this exact claim text.",
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — Thesis\n")
    composed = compose_project_draft(vault, "project-alpha")
    evidence_id = composed["evidence_markers"][0]["id"]
    [bound] = state.evidence_sets(vault)
    resolve_evidence_review(vault, evidence_id, decision="accept", reason="PI accepted")

    assert verify_project_draft(vault, "project-alpha")["ready"] is True
    write_project_export(vault, "project-alpha", draft=True)

    draft = vault / "projects/project-alpha/draft.md"
    draft.write_text(
        draft.read_text(encoding="utf-8").replace(
            "The PI accepts this exact claim text.",
            "The claim text changed after PI acceptance.",
        ),
        encoding="utf-8",
    )
    state.rebuild_evidence_sets_from_markers(vault)
    verification = verify_project_draft(vault, "project-alpha")

    assert verification["ready"] is False
    assert verification["findings"] == [
        {
            "kind": "evidence-text-drift",
            "severity": "high",
            "evidence_id": evidence_id,
            "block_ref": bound["block_ref"],
            "reason": "anchored block text differs from its stored binding",
        }
    ]
    with pytest.raises(ValueError, match="evidence-text-drift"):
        write_project_export(vault, "project-alpha", draft=True)


def test_relocated_evidence_marker_refuses_export_with_unbound_text(tmp_path: Path) -> None:
    draft, evidence_id = _compose_source_backed_draft(
        tmp_path,
        body="Original source-backed claim.",
    )
    [bound] = state.evidence_sets(tmp_path)

    assert verify_project_draft(tmp_path, "project-alpha")["ready"] is True
    assert (
        "[@source-alpha]" in write_project_export(tmp_path, "project-alpha", draft=True)["content"]
    )

    original = draft.read_text(encoding="utf-8")
    marker_start = f"%%ev: {evidence_id} "
    _before, marker_and_rest = original.split(marker_start, 1)
    marker = marker_start + marker_and_rest.split("%%", 1)[0] + "%%"
    anchor = f" ^blk-{evidence_id.removeprefix('ev-')}"
    draft.write_text(
        original.replace(f"{anchor} {marker}", anchor).rstrip()
        + f"\n\nChanged unsupported claim. {marker}\n",
        encoding="utf-8",
    )

    verification = verify_project_draft(tmp_path, "project-alpha")

    assert verification["ready"] is False
    assert verification["findings"] == [
        {
            "kind": "evidence-text-unbound",
            "severity": "high",
            "evidence_id": evidence_id,
            "block_ref": bound["block_ref"],
            "reason": "anchored block text cannot be resolved",
        }
    ]
    with pytest.raises(ValueError, match="evidence-text-unbound"):
        write_project_export(tmp_path, "project-alpha", draft=True)


def test_even_escaped_inline_code_controls_refuse_export(tmp_path: Path) -> None:
    draft, evidence_id = _compose_source_backed_draft(
        tmp_path,
        body="Original source-backed claim.",
    )
    original = draft.read_text(encoding="utf-8")
    marker_start = f"%%ev: {evidence_id} "
    _before, marker_and_rest = original.split(marker_start, 1)
    marker = marker_start + marker_and_rest.split("%%", 1)[0] + "%%"
    anchor = f"^blk-{evidence_id.removeprefix('ev-')}"
    draft.write_text(
        f"Source note: `notes/support.md`\n\nUnsupported claim. {'\\' * 2}` {anchor} {marker} `\n",
        encoding="utf-8",
    )
    with state.connect(tmp_path) as conn:
        conn.execute("DELETE FROM evidence_sets")
    state.rebuild_evidence_sets_from_markers(tmp_path)
    [bound] = state.evidence_sets(tmp_path)

    verification = verify_project_draft(tmp_path, "project-alpha")

    assert verification["ready"] is False
    assert verification["findings"] == [
        {
            "kind": "evidence-text-unbound",
            "severity": "high",
            "evidence_id": evidence_id,
            "block_ref": bound["block_ref"],
            "reason": "stored block-text binding is missing",
        }
    ]
    with pytest.raises(ValueError, match="evidence-text-unbound"):
        write_project_export(tmp_path, "project-alpha", draft=True)


def test_backslash_before_inline_code_closer_controls_refuse_export(tmp_path: Path) -> None:
    draft, evidence_id = _compose_source_backed_draft(
        tmp_path,
        body="Original source-backed claim.",
    )
    original = draft.read_text(encoding="utf-8")
    marker_start = f"%%ev: {evidence_id} "
    _before, marker_and_rest = original.split(marker_start, 1)
    marker = marker_start + marker_and_rest.split("%%", 1)[0] + "%%"
    anchor = f"^blk-{evidence_id.removeprefix('ev-')}"
    escaped_closer = "\\" + "`"
    draft.write_text(
        "Source note: `notes/support.md`\n\n"
        f"Unsupported claim. ` {anchor} {marker} {escaped_closer}\n",
        encoding="utf-8",
    )
    with state.connect(tmp_path) as conn:
        conn.execute("DELETE FROM evidence_sets")
    state.rebuild_evidence_sets_from_markers(tmp_path)
    [bound] = state.evidence_sets(tmp_path)

    verification = verify_project_draft(tmp_path, "project-alpha")

    assert verification["ready"] is False
    assert verification["findings"] == [
        {
            "kind": "evidence-text-unbound",
            "severity": "high",
            "evidence_id": evidence_id,
            "block_ref": bound["block_ref"],
            "reason": "stored block-text binding is missing",
        }
    ]
    with pytest.raises(ValueError, match="evidence-text-unbound"):
        write_project_export(tmp_path, "project-alpha", draft=True)


def test_heading_and_following_paragraph_cannot_share_evidence_binding(
    tmp_path: Path,
) -> None:
    draft, evidence_id = _compose_source_backed_draft(
        tmp_path,
        body="Original source-backed claim.",
    )
    original = draft.read_text(encoding="utf-8")
    marker_start = f"%%ev: {evidence_id} "
    _before, marker_and_rest = original.split(marker_start, 1)
    marker = marker_start + marker_and_rest.split("%%", 1)[0] + "%%"
    anchor = f"^blk-{evidence_id.removeprefix('ev-')}"
    draft.write_text(
        f"# Supported claim {anchor} {marker}\n"
        "Changed unsupported claim.\n\n"
        "Source note: `notes/support.md`\n",
        encoding="utf-8",
    )
    with state.connect(tmp_path) as conn:
        conn.execute("DELETE FROM evidence_sets")
    state.rebuild_evidence_sets_from_markers(tmp_path)
    [bound] = state.evidence_sets(tmp_path)

    assert verify_project_draft(tmp_path, "project-alpha")["ready"] is True
    assert (
        "[@source-alpha]" in write_project_export(tmp_path, "project-alpha", draft=True)["content"]
    )

    draft.write_text(
        f"# Supported claim {anchor} \n"
        f"Changed unsupported claim. {marker}\n\n"
        "Source note: `notes/support.md`\n",
        encoding="utf-8",
    )
    verification = verify_project_draft(tmp_path, "project-alpha")

    assert verification["ready"] is False
    assert verification["findings"] == [
        {
            "kind": "evidence-text-unbound",
            "severity": "high",
            "evidence_id": evidence_id,
            "block_ref": bound["block_ref"],
            "reason": "anchored block text cannot be resolved",
        }
    ]
    with pytest.raises(ValueError, match="evidence-text-unbound"):
        write_project_export(tmp_path, "project-alpha", draft=True)


def test_unresolvable_evidence_anchor_refuses_export(tmp_path: Path) -> None:
    draft, evidence_id = _compose_source_backed_draft(
        tmp_path,
        body="This claim loses its block anchor.",
    )
    [bound] = state.evidence_sets(tmp_path)
    anchor = f" ^blk-{evidence_id.removeprefix('ev-')}"
    draft.write_text(
        draft.read_text(encoding="utf-8").replace(anchor, ""),
        encoding="utf-8",
    )

    verification = verify_project_draft(tmp_path, "project-alpha")

    assert verification["ready"] is False
    assert verification["findings"] == [
        {
            "kind": "evidence-text-unbound",
            "severity": "high",
            "evidence_id": evidence_id,
            "block_ref": bound["block_ref"],
            "reason": "anchored block text cannot be resolved",
        }
    ]
    with pytest.raises(ValueError, match="evidence-text-unbound"):
        write_project_export(tmp_path, "project-alpha", draft=True)


def test_missing_stored_evidence_binding_refuses_export(tmp_path: Path) -> None:
    _draft, evidence_id = _compose_source_backed_draft(
        tmp_path,
        body="This claim has a resolvable block but no stored binding.",
    )
    [bound] = state.evidence_sets(tmp_path)
    with state.connect(tmp_path) as conn:
        conn.execute(
            "UPDATE evidence_sets SET block_text_sha256 = NULL WHERE id = ?",
            (evidence_id,),
        )

    verification = verify_project_draft(tmp_path, "project-alpha")

    assert verification["ready"] is False
    assert verification["findings"] == [
        {
            "kind": "evidence-text-unbound",
            "severity": "high",
            "evidence_id": evidence_id,
            "block_ref": bound["block_ref"],
            "reason": "stored block-text binding is missing",
        }
    ]
    with pytest.raises(ValueError, match="evidence-text-unbound"):
        write_project_export(tmp_path, "project-alpha", draft=True)


def test_evidence_review_rejects_non_pi_actor_without_clearing_draft_gate(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    _project(vault)
    write_checked_concept(
        vault,
        "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\nid: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
        "note",
        body="This implicit claim still needs PI review.",
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — Thesis\n")
    result = compose_project_draft(vault, "project-alpha")
    evidence_id = result["evidence_markers"][0]["id"]

    with pytest.raises(ValueError, match="resolve-evidence-review requires PI actor authority"):
        resolve_evidence_review(
            vault,
            evidence_id,
            decision="accept",
            reason="agent attempted disposition",
            actor="agent",
        )

    verification = verify_project_draft(vault, "project-alpha")

    assert verification["ready"] is False
    assert {finding["kind"] for finding in verification["findings"]} == {
        "evidence-incomplete",
        "review-required",
    }


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


def _compose_source_backed_draft(vault: Path, *, body: str) -> tuple[Path, str]:
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
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FA2\n"
        "work_id: catalog/sources/source-alpha\n",
        "note",
        body=body,
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA2 — Support\n")
    composed = compose_project_draft(vault, "project-alpha")
    return (
        vault / "projects/project-alpha/draft.md",
        composed["evidence_markers"][0]["id"],
    )
