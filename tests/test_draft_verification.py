from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from memoria_vault.runtime import knowledge, state
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
from memoria_vault.runtime.time import parse_iso
from memoria_vault.runtime.trusted_writer import append_explicit_journal_event, append_journal_event
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
        citekey="source-alpha",
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
        citekey="source-alpha",
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
        write_project_export(vault, "project-alpha", allow_unready=True, draft=True)


def test_draft_verification_flags_broken_structural_reference(tmp_path: Path) -> None:
    vault = tmp_path
    state.upsert_catalog_record(
        vault,
        work_id="source-alpha",
        citekey="source-alpha",
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
        citekey="source-alpha",
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


@pytest.mark.parametrize(
    "analysis_reference",
    ["analysis-computed", "analysis code", "code-grounds"],
)
def test_draft_verification_routes_analysis_number_references_to_incomplete(
    tmp_path: Path,
    analysis_reference: str,
) -> None:
    vault = tmp_path
    state.upsert_catalog_record(
        vault,
        work_id="source-alpha",
        citekey="source-alpha",
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
        body="This source-backed claim is clean until its evidence is cited.",
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA2 — Support\n")
    compose_project_draft(vault, "project-alpha")
    draft = vault / "projects/project-alpha/draft.md"
    draft.write_text(
        draft.read_text(encoding="utf-8").rstrip()
        + f"\n\nThe effect size is {analysis_reference}.\n",
        encoding="utf-8",
    )

    verification = verify_project_draft(vault, "project-alpha")

    assert verification["ready"] is False
    assert verification["findings"] == [
        {"kind": "analysis-number-evidence-incomplete", "severity": "high"}
    ]


def test_draft_with_zero_evidence_sets_reports_no_evidence_set_finding(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    _project(vault)
    draft = vault / "projects/project-alpha/draft.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(
        "---\ntype: draft\nproject: projects/project-alpha/project.md\n---\n\n"
        "# Alpha project\n\nA claim with no evidence marker at all.\n",
        encoding="utf-8",
    )

    verification = verify_project_draft(vault, "project-alpha")

    assert verification["ready"] is False
    assert verification["ok"] is False
    assert [finding["kind"] for finding in verification["findings"]] == [
        "no-evidence-set",
        "missing-structural-reference",
    ]
    assert verification["missing"] == [
        "no-evidence-set",
        "missing-structural-reference",
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


def _compose_implicit_draft(vault: Path, *, body: str) -> str:
    """Compose project-alpha around one checked note with no evidence items."""
    _project(vault)
    write_checked_concept(
        vault,
        "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\nid: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
        "note",
        body=body,
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — Thesis\n")
    return compose_project_draft(vault, "project-alpha")["evidence_markers"][0]["id"]


def test_reject_disposition_keeps_export_hold(tmp_path: Path) -> None:
    evidence_id = _compose_implicit_draft(
        tmp_path, body="This rejected implicit claim must stay blocked."
    )

    resolve_evidence_review(
        tmp_path,
        evidence_id,
        decision="reject",
        reason="grounds do not support the claim",
    )

    verification = verify_project_draft(tmp_path, "project-alpha")

    assert verification["ready"] is False
    assert "evidence-incomplete" in {finding["kind"] for finding in verification["findings"]}


def test_reject_after_accept_reblocks_export(tmp_path: Path) -> None:
    evidence_id = _compose_implicit_draft(
        tmp_path, body="This claim was accepted, then the PI reversed."
    )

    resolve_evidence_review(tmp_path, evidence_id, decision="accept", reason="PI accepted")
    assert verify_project_draft(tmp_path, "project-alpha")["ready"] is True

    resolve_evidence_review(tmp_path, evidence_id, decision="reject", reason="PI reversed")
    verification = verify_project_draft(tmp_path, "project-alpha")

    assert verification["ready"] is False


def test_accept_after_reject_clears_export_hold(tmp_path: Path) -> None:
    evidence_id = _compose_implicit_draft(
        tmp_path, body="This rejected claim was later accepted by the PI."
    )

    resolve_evidence_review(tmp_path, evidence_id, decision="reject", reason="PI rejected")
    assert verify_project_draft(tmp_path, "project-alpha")["ready"] is False

    resolve_evidence_review(tmp_path, evidence_id, decision="accept", reason="PI accepted")

    assert verify_project_draft(tmp_path, "project-alpha")["ready"] is True


def test_latest_legacy_digestless_disposition_voids_prior_accept(tmp_path: Path) -> None:
    evidence_id = _compose_implicit_draft(
        tmp_path, body="A legacy disposition must not revive an older acceptance."
    )

    resolve_evidence_review(tmp_path, evidence_id, decision="accept", reason="PI accepted")
    assert verify_project_draft(tmp_path, "project-alpha")["ready"] is True

    append_explicit_journal_event(
        tmp_path,
        {
            "event": "resolved",
            "operation": "resolve-evidence-review",
            "evidence_id": evidence_id,
            "decision": "accept",
            "reason": "legacy digestless acceptance",
        },
        actor="pi",
        machine="test-machine",
    )

    assert evidence_id not in knowledge._disposed_evidence_digests(tmp_path)
    assert verify_project_draft(tmp_path, "project-alpha")["ready"] is False


def test_defer_disposition_keeps_hold_and_records_utc_day_suppression(tmp_path: Path) -> None:
    evidence_id = _compose_implicit_draft(
        tmp_path, body="This implicit claim is deferred until tomorrow."
    )

    event = resolve_evidence_review(tmp_path, evidence_id, decision="defer", reason="revisit")
    verification = verify_project_draft(tmp_path, "project-alpha")

    moment = parse_iso(event["timestamp"])
    assert moment is not None
    expected_day = (moment.date() + timedelta(days=1)).isoformat()
    assert event["suppressed_until"] == f"{expected_day}T00:00:00Z"
    assert verification["ready"] is False
    assert "evidence-incomplete" in {finding["kind"] for finding in verification["findings"]}


def test_defer_disposition_uses_utc_day_at_offset_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    timestamp = "2026-07-17T23:30:00-02:00"
    evidence_id = _compose_implicit_draft(
        tmp_path, body="This deferred claim crosses a UTC-day boundary."
    )
    calls = 0

    def now_once() -> str:
        nonlocal calls
        calls += 1
        if calls > 1:
            raise AssertionError("one disposition action must use one timestamp")
        return timestamp

    monkeypatch.setattr(knowledge, "now_iso", now_once)

    event = resolve_evidence_review(tmp_path, evidence_id, decision="defer", reason="revisit")

    with state.connect(tmp_path) as conn:
        disposition = conn.execute(
            "SELECT payload_json FROM event_log WHERE event_type = 'disposition'"
        ).fetchone()

    assert calls == 1
    assert event["timestamp"] == timestamp
    assert event["suppressed_until"] == "2026-07-19T00:00:00Z"
    assert json.loads(disposition["payload_json"])["timestamp"] == timestamp


def test_edit_disposition_records_deep_link_and_keeps_hold(tmp_path: Path) -> None:
    evidence_id = _compose_implicit_draft(
        tmp_path, body="This implicit claim needs its marker fixed."
    )

    event = resolve_evidence_review(tmp_path, evidence_id, decision="edit", reason="fix marker")
    verification = verify_project_draft(tmp_path, "project-alpha")

    anchor = evidence_id.removeprefix("ev-")
    assert event["edit_target"] == {
        "draft_path": "projects/project-alpha/draft.md",
        "block_ref": f"projects/project-alpha/draft.md#^blk-{anchor}",
    }
    assert verification["ready"] is False


@pytest.mark.parametrize("decision", ["defer", "edit"])
def test_defer_or_edit_after_accept_reblocks_export(tmp_path: Path, decision: str) -> None:
    evidence_id = _compose_implicit_draft(
        tmp_path, body="A later non-accept decision must revoke clearance."
    )

    resolve_evidence_review(tmp_path, evidence_id, decision="accept", reason="PI accepted")
    assert verify_project_draft(tmp_path, "project-alpha")["ready"] is True

    resolve_evidence_review(tmp_path, evidence_id, decision=decision, reason="PI changed course")

    assert evidence_id not in knowledge._disposed_evidence_digests(tmp_path)
    assert verify_project_draft(tmp_path, "project-alpha")["ready"] is False


def test_unknown_decision_names_all_four(tmp_path: Path) -> None:
    evidence_id = _compose_implicit_draft(tmp_path, body="Guard message names the seam decisions.")

    with pytest.raises(ValueError, match="accept, reject, edit, or defer"):
        resolve_evidence_review(tmp_path, evidence_id, decision="override", reason="nope")


def test_accept_disposition_journals_optional_warrant(tmp_path: Path) -> None:
    vault = tmp_path
    evidence_id = _compose_implicit_draft(
        vault, body="This accepted claim carries a stated warrant."
    )

    event = resolve_evidence_review(
        vault,
        evidence_id,
        decision="accept",
        reason="PI accepted",
        warrant="The cited spans jointly entail the claim.",
    )
    bare = resolve_evidence_review(vault, evidence_id, decision="accept", reason="again")

    assert event["warrant"] == "The cited spans jointly entail the claim."
    assert "warrant" not in bare


@pytest.mark.parametrize("decision", ["reject", "edit", "defer"])
def test_warrant_refused_on_non_accept_decisions(tmp_path: Path, decision: str) -> None:
    vault = tmp_path
    evidence_id = _compose_implicit_draft(vault, body="A warrant cannot ride a rejection.")

    with pytest.raises(ValueError, match="warrant text rides only the accept decision"):
        resolve_evidence_review(
            vault,
            evidence_id,
            decision=decision,
            reason="no",
            warrant="This should be refused.",
        )


def test_evidence_items_digest_preserves_nonempty_item_order() -> None:
    items = ["source-alpha#^p0001", "source-beta#^p0002"]

    digest = knowledge._evidence_items_sha256(items)

    assert digest == hashlib.sha256(b"source-alpha#^p0001|source-beta#^p0002").hexdigest()
    assert digest != knowledge._evidence_items_sha256(list(reversed(items)))


def test_disposition_event_records_empty_items_digest(tmp_path: Path) -> None:
    vault = tmp_path
    _project(vault)
    write_checked_concept(
        vault,
        "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\nid: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
        "note",
        body="This implicit claim gets a content-bound disposition.",
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — Thesis\n")
    result = compose_project_draft(vault, "project-alpha")
    evidence_id = result["evidence_markers"][0]["id"]

    event = resolve_evidence_review(vault, evidence_id, decision="accept", reason="PI accepted")

    assert event["items_sha256"] == hashlib.sha256(b"").hexdigest()


def test_editing_items_voids_prior_disposition(tmp_path: Path) -> None:
    vault = tmp_path
    _project(vault)
    write_checked_concept(
        vault,
        "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\nid: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
        "note",
        body="This implicit claim was accepted, then its grounds changed.",
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — Thesis\n")
    result = compose_project_draft(vault, "project-alpha")
    evidence_id = result["evidence_markers"][0]["id"]
    resolve_evidence_review(vault, evidence_id, decision="accept", reason="PI accepted")
    assert verify_project_draft(vault, "project-alpha")["ready"] is True

    draft = vault / "projects/project-alpha/draft.md"
    draft.write_text(
        draft.read_text(encoding="utf-8").replace(
            "items=%%",
            "items=source-missing#^p0001%%",
        ),
        encoding="utf-8",
    )
    verification = verify_project_draft(vault, "project-alpha")

    assert verification["ready"] is False
    assert "evidence-incomplete" in {finding["kind"] for finding in verification["findings"]}


def test_disposition_requires_matching_evidence_record(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown evidence id"):
        resolve_evidence_review(tmp_path, "ev-deadbeef", decision="accept", reason="none")


def test_legacy_digestless_disposition_is_inert(tmp_path: Path) -> None:
    vault = tmp_path
    _project(vault)
    write_checked_concept(
        vault,
        "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\nid: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
        "note",
        body="This implicit claim has a legacy disposition without an items digest.",
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — Thesis\n")
    result = compose_project_draft(vault, "project-alpha")
    evidence_id = result["evidence_markers"][0]["id"]
    append_explicit_journal_event(
        vault,
        {
            "event": "resolved",
            "operation": "resolve-evidence-review",
            "evidence_id": evidence_id,
            "decision": "accept",
            "reason": "legacy PI acceptance",
        },
        actor="pi",
        machine="test-machine",
    )

    verification = verify_project_draft(vault, "project-alpha")

    assert verification["ready"] is False
    assert {finding["kind"] for finding in verification["findings"]} == {
        "evidence-incomplete",
        "review-required",
    }


def test_latest_digest_bound_reject_disposition_reblocks_export(tmp_path: Path) -> None:
    vault = tmp_path
    _project(vault)
    write_checked_concept(
        vault,
        "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\nid: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
        "note",
        body="This implicit claim has two PI dispositions for different grounds.",
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — Thesis\n")
    result = compose_project_draft(vault, "project-alpha")
    evidence_id = result["evidence_markers"][0]["id"]
    first = resolve_evidence_review(vault, evidence_id, decision="accept", reason="PI accepted")

    draft = vault / "projects/project-alpha/draft.md"
    draft.write_text(
        draft.read_text(encoding="utf-8").replace(
            "items=%%",
            "items=source-missing#^p0001%%",
        ),
        encoding="utf-8",
    )
    state.rebuild_evidence_sets_from_markers(vault)
    second = resolve_evidence_review(vault, evidence_id, decision="reject", reason="PI rejected")

    assert second["items_sha256"] == hashlib.sha256(b"source-missing#^p0001").hexdigest()
    assert evidence_id not in knowledge._disposed_evidence_digests(vault)
    assert verify_project_draft(vault, "project-alpha")["ready"] is False

    draft.write_text(
        draft.read_text(encoding="utf-8").replace(
            "items=source-missing#^p0001%%",
            "items=%%",
        ),
        encoding="utf-8",
    )
    verification = verify_project_draft(vault, "project-alpha")

    assert first["items_sha256"] == hashlib.sha256(b"").hexdigest()
    assert verification["ready"] is False
    assert "evidence-incomplete" in {finding["kind"] for finding in verification["findings"]}


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


def test_reintroduced_evidence_id_refuses_export_when_its_text_changed(tmp_path: Path) -> None:
    draft, evidence_id = _compose_source_backed_draft(
        tmp_path,
        body="Original source-backed claim.",
    )
    original = draft.read_text(encoding="utf-8")
    marker_start = f"%%ev: {evidence_id} "
    _before, marker_and_rest = original.split(marker_start, 1)
    marker = marker_start + marker_and_rest.split("%%", 1)[0] + "%%"
    anchor = f"^blk-{evidence_id.removeprefix('ev-')}"

    draft.write_text(original.replace(f"{anchor} {marker}", ""), encoding="utf-8")
    state.rebuild_evidence_sets_from_markers(tmp_path)
    assert state.evidence_sets(tmp_path) == []

    draft.write_text(
        original.replace("Original source-backed claim.", "Changed source-backed claim."),
        encoding="utf-8",
    )
    verification = verify_project_draft(tmp_path, "project-alpha")

    assert verification["ready"] is False
    assert verification["findings"][0]["kind"] == "evidence-text-drift"
    with pytest.raises(ValueError, match="evidence-text-drift"):
        write_project_export(tmp_path, "project-alpha", draft=True)


def test_first_binding_journals_one_evidence_minted_event(tmp_path: Path) -> None:
    _compose_source_backed_draft(tmp_path, body="A minted claim enters the journal.")
    [bound] = state.evidence_sets(tmp_path)

    events = state.read_event_log(tmp_path, event_types=["evidence-minted"])

    assert [
        (event["evidence_id"], event["block_ref"], event["block_text_sha256"]) for event in events
    ] == [(bound["id"], bound["block_ref"], bound["block_text_sha256"])]

    verify_project_draft(tmp_path, "project-alpha")
    events_after = state.read_event_log(tmp_path, event_types=["evidence-minted"])

    assert len(events_after) == 1


def test_mint_journal_failure_rolls_back_binding_and_active_sets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = tmp_path
    state.upsert_catalog_record(
        vault,
        work_id="source-alpha",
        citekey="source-alpha",
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
        body="A claim whose mint event must be atomic with its binding.",
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA2 — Support\n")

    def fail_journal_insert(*_args, **_kwargs) -> None:
        raise RuntimeError("mint journal insert failed")

    monkeypatch.setattr(state, "_insert_journal_row_conn", fail_journal_insert, raising=False)

    with pytest.raises(RuntimeError, match="mint journal insert failed"):
        compose_project_draft(vault, "project-alpha")

    assert state.evidence_sets(vault) == []
    with state.connect(vault) as conn:
        assert conn.execute("SELECT COUNT(*) FROM evidence_bindings").fetchone()[0] == 0
    assert state.read_event_log(vault, event_types=["evidence-minted"]) == []

    monkeypatch.undo()
    verify_project_draft(vault, "project-alpha")

    [bound] = state.evidence_sets(vault)
    assert [
        (event["evidence_id"], event["block_ref"], event["block_text_sha256"])
        for event in state.read_event_log(vault, event_types=["evidence-minted"])
    ] == [(bound["id"], bound["block_ref"], bound["block_text_sha256"])]


def test_lost_bindings_ledger_rebuilds_from_journal_and_tamper_stays_detected(
    tmp_path: Path,
) -> None:
    draft, _evidence_id = _compose_source_backed_draft(
        tmp_path, body="The journal preserves this exact claim text."
    )
    [bound] = state.evidence_sets(tmp_path)
    assert bound["block_text_sha256"]

    with state.connect(tmp_path) as conn:
        conn.execute("DROP TABLE evidence_bindings")

    result = state.rebuild_evidence_bindings_from_journal(tmp_path)

    assert result == {"replayed": 1, "inserted": 1}
    with state.connect(tmp_path) as conn:
        restored = conn.execute("SELECT id, block_text_sha256 FROM evidence_bindings").fetchall()
    assert [(row["id"], row["block_text_sha256"]) for row in restored] == [
        (bound["id"], bound["block_text_sha256"])
    ]

    draft.write_text(
        draft.read_text(encoding="utf-8").replace(
            "The journal preserves this exact claim text.",
            "Tampered claim text after ledger loss.",
        ),
        encoding="utf-8",
    )
    verification = verify_project_draft(tmp_path, "project-alpha")

    assert verification["ready"] is False
    assert any(finding["kind"] == "evidence-text-drift" for finding in verification["findings"])


def test_bindings_ledger_recovery_refuses_a_broken_journal_chain(tmp_path: Path) -> None:
    _compose_source_backed_draft(tmp_path, body="A chain-protected source-backed claim.")
    [bound] = state.evidence_sets(tmp_path)
    assert bound["block_text_sha256"]

    with state.connect(tmp_path) as conn:
        conn.execute("DROP TABLE evidence_bindings")
        conn.execute("DROP TRIGGER event_log_no_update")
        conn.execute(
            "UPDATE event_log SET payload_json = replace(payload_json, ?, ?) "
            "WHERE event_type = 'evidence-minted'",
            (bound["block_text_sha256"], "sha256:" + "0" * 64),
        )

    assert state.verify_journal_chain(tmp_path)["ok"] is False
    with pytest.raises(ValueError, match="journal chain"):
        state.rebuild_evidence_bindings_from_journal(tmp_path)
    with state.connect(tmp_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM evidence_bindings").fetchone()[0] == 0


def test_bindings_ledger_recovery_refuses_a_noncanonical_mint_event(tmp_path: Path) -> None:
    _compose_source_backed_draft(tmp_path, body="A canonical mint must have all fields.")
    context = operation_context(tmp_path, operation_id="replay-evidence-bindings")
    append_journal_event(
        tmp_path,
        {
            "event": "evidence-minted",
            "evidence_id": "ev-deadbeef",
            "block_ref": "#^blk-deadbeef",
            "block_text_sha256": None,
        },
        context=context,
    )
    assert state.verify_journal_chain(tmp_path)["ok"] is True

    with state.connect(tmp_path) as conn:
        conn.execute("DROP TABLE evidence_bindings")

    with pytest.raises(ValueError, match="invalid evidence-minted journal event"):
        state.rebuild_evidence_bindings_from_journal(tmp_path)
    with state.connect(tmp_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM evidence_bindings").fetchone()[0] == 0


def test_evidence_mint_payload_validator_rejects_a_nonstring_actor() -> None:
    event = {
        "event": "evidence-minted",
        "evidence_id": "ev-deadbeef",
        "block_ref": "projects/project-alpha/draft.md#^blk-deadbeef",
        "block_text_sha256": None,
        "actor": [],
        "request_provenance": {"surface": "pytest"},
        "run_id": "replay-run",
        "request_id": "replay-request",
        "operation": "replay-evidence-bindings",
        "machine": "test-machine",
        "timestamp": "2026-07-16T00:00:00Z",
    }

    with pytest.raises(ValueError, match="invalid evidence-minted journal event"):
        state._evidence_mint_event_binding(event)


def test_bindings_ledger_recovery_uses_first_mint_and_restores_immutability(
    tmp_path: Path,
) -> None:
    _compose_source_backed_draft(tmp_path, body="The original mint remains authoritative.")
    [bound] = state.evidence_sets(tmp_path)
    context = operation_context(tmp_path, operation_id="replay-evidence-bindings")
    append_journal_event(
        tmp_path,
        {
            "event": "evidence-minted",
            "evidence_id": bound["id"],
            "block_ref": bound["block_ref"],
            "block_text_sha256": "sha256:" + "f" * 64,
        },
        context=context,
    )
    assert state.verify_journal_chain(tmp_path)["ok"] is True

    with state.connect(tmp_path) as conn:
        conn.execute("DROP TABLE evidence_bindings")

    assert state.rebuild_evidence_bindings_from_journal(tmp_path) == {
        "replayed": 2,
        "inserted": 1,
    }
    with state.connect(tmp_path) as conn:
        assert (
            conn.execute(
                "SELECT block_text_sha256 FROM evidence_bindings WHERE id = ?", (bound["id"],)
            ).fetchone()[0]
            == bound["block_text_sha256"]
        )
        with pytest.raises(sqlite3.IntegrityError, match="evidence bindings are immutable"):
            conn.execute(
                "UPDATE evidence_bindings SET block_text_sha256 = NULL WHERE id = ?", (bound["id"],)
            )
        with pytest.raises(sqlite3.IntegrityError, match="evidence bindings are immutable"):
            conn.execute("DELETE FROM evidence_bindings WHERE id = ?", (bound["id"],))


def test_draft_export_uses_the_verified_draft_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    draft, _evidence_id = _compose_source_backed_draft(
        tmp_path,
        body="Verified source-backed claim.",
    )
    original = knowledge.read_project_draft
    reads = 0

    def swap_after_verification(*args, **kwargs):
        nonlocal reads
        reads += 1
        if reads == 2:
            draft.write_text(
                draft.read_text(encoding="utf-8").replace(
                    "Verified source-backed claim.",
                    "Unverified changed claim.",
                ),
                encoding="utf-8",
            )
        return original(*args, **kwargs)

    monkeypatch.setattr(knowledge, "read_project_draft", swap_after_verification)
    exported = write_project_export(tmp_path, "project-alpha", draft=True)

    assert reads == 1
    assert "Verified source-backed claim." in exported["content"]
    assert "Unverified changed claim." not in exported["content"]


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


@pytest.mark.parametrize(
    ("opening", "closing"),
    [
        ("<!-- ", " -->"),
        ("<script>", "</script>"),
        ("<span hidden>", "</span>"),
        ("<span hidden/>", "</span>"),
        ('<span hidden data="\\">', "</span>"),
        ("<span hidden data='\\'>", "</span>"),
        ("<?hidden ", " ?>"),
        ("---\nhidden: |\n  ", "\n---"),
        ('[hidden]: https://example.invalid "', '"'),
    ],
)
def test_hidden_marker_cannot_make_external_edit_export_ready(
    tmp_path: Path,
    opening: str,
    closing: str,
) -> None:
    draft, evidence_id = _compose_source_backed_draft(
        tmp_path,
        body="Original source-backed claim.",
    )
    original = draft.read_text(encoding="utf-8")
    marker_start = f"%%ev: {evidence_id} "
    _before, marker_and_rest = original.split(marker_start, 1)
    marker = marker_start + marker_and_rest.split("%%", 1)[0] + "%%"
    fresh_evidence_id = "ev-1234abcd"
    fresh_marker = marker.replace(evidence_id, fresh_evidence_id)
    fresh_anchor = f"^blk-{fresh_evidence_id.removeprefix('ev-')}"
    draft.write_text(
        f"{opening}Hidden claim. {fresh_anchor} {fresh_marker}{closing}\n\n"
        "Source note: `notes/support.md`\n",
        encoding="utf-8",
    )
    state.rebuild_evidence_sets_from_markers(tmp_path)

    verification = verify_project_draft(tmp_path, "project-alpha")

    assert state.evidence_sets(tmp_path) == []
    assert verification["ready"] is False
    assert knowledge.read_project_draft(tmp_path, "project-alpha")["evidence_markers"] == []
    with state.connect(tmp_path) as conn:
        assert (
            conn.execute(
                "SELECT id FROM evidence_bindings WHERE id = ?", (fresh_evidence_id,)
            ).fetchone()
            is None
        )
    with pytest.raises(ValueError, match="project draft is not export-ready"):
        write_project_export(tmp_path, "project-alpha", draft=True)


def test_hidden_existing_evidence_marker_remains_unbound(tmp_path: Path) -> None:
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
        f"<!-- Hidden claim. {anchor} {marker} -->\n\nSource note: `notes/support.md`\n",
        encoding="utf-8",
    )
    state.rebuild_evidence_sets_from_markers(tmp_path)

    [bound] = state.evidence_sets(tmp_path)
    verification = verify_project_draft(tmp_path, "project-alpha")

    assert bound["id"] == evidence_id
    assert verification["ready"] is False
    assert verification["findings"][0]["kind"] == "evidence-text-unbound"
    assert knowledge.read_project_draft(tmp_path, "project-alpha")["evidence_markers"] == []
    with pytest.raises(ValueError, match="evidence-text-unbound"):
        write_project_export(tmp_path, "project-alpha", draft=True)


@pytest.mark.parametrize("hidden_rel", ["", "notes/duplicate-marker.md"])
def test_duplicate_evidence_id_refuses_export(tmp_path: Path, hidden_rel: str) -> None:
    draft, evidence_id = _compose_source_backed_draft(
        tmp_path,
        body="Original source-backed claim.",
    )
    original = draft.read_text(encoding="utf-8")
    marker_start = f"%%ev: {evidence_id} "
    _before, marker_and_rest = original.split(marker_start, 1)
    marker = marker_start + marker_and_rest.split("%%", 1)[0] + "%%"
    anchor = f"^blk-{evidence_id.removeprefix('ev-')}"
    hidden = f"<!-- Hidden claim. {anchor} {marker} -->\n"
    if hidden_rel:
        duplicate = tmp_path / hidden_rel
        duplicate.parent.mkdir(parents=True, exist_ok=True)
        duplicate.write_text(hidden, encoding="utf-8")
    else:
        draft.write_text(original + "\n" + hidden, encoding="utf-8")

    verification = verify_project_draft(tmp_path, "project-alpha")

    assert verification["ready"] is False
    assert any(
        finding["kind"] == "evidence-id-duplicate" and finding["evidence_id"] == evidence_id
        for finding in verification["findings"]
    )
    with pytest.raises(ValueError, match="evidence-id-duplicate"):
        write_project_export(tmp_path, "project-alpha", draft=True)


def test_duplicate_evidence_id_uses_the_draft_block_ref_when_foreign_marker_sorts_first(
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
    foreign = tmp_path / "notes/duplicate-marker.md"
    foreign.parent.mkdir(parents=True, exist_ok=True)
    foreign.write_text(
        f"Foreign duplicate. {anchor} {marker}\n",
        encoding="utf-8",
    )

    verification = verify_project_draft(tmp_path, "project-alpha")

    duplicate = next(
        finding
        for finding in verification["findings"]
        if finding["kind"] == "evidence-id-duplicate"
    )
    assert duplicate["block_ref"] == f"projects/project-alpha/draft.md#{anchor}"


def test_hidden_duplicate_in_one_draft_blocks_that_draft_when_direct_elsewhere(
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
    other_id = "ev-1234abcd"
    other_marker = marker.replace(evidence_id, other_id)
    other_anchor = f"^blk-{other_id.removeprefix('ev-')}"
    hidden = f"<!-- Hidden claim. {anchor} {marker} -->\n"
    draft.write_text(
        original.replace(f"{anchor} {marker}", "")
        + f"\nValid second claim. {other_anchor} {other_marker}\n\n{hidden}",
        encoding="utf-8",
    )
    duplicate = tmp_path / "projects/project-beta/draft.md"
    duplicate.parent.mkdir(parents=True, exist_ok=True)
    duplicate.write_text(
        f"Foreign duplicate. {anchor} {marker}\n",
        encoding="utf-8",
    )

    verification = verify_project_draft(tmp_path, "project-alpha")

    assert verification["ready"] is False
    assert any(
        finding["kind"] == "evidence-id-duplicate" and finding["evidence_id"] == evidence_id
        for finding in verification["findings"]
    )
    with pytest.raises(ValueError, match="evidence-id-duplicate"):
        write_project_export(tmp_path, "project-alpha", draft=True)


def test_hidden_existing_id_moved_outside_draft_remains_unbound(tmp_path: Path) -> None:
    draft, evidence_id = _compose_source_backed_draft(
        tmp_path,
        body="Original source-backed claim.",
    )
    original = draft.read_text(encoding="utf-8")
    marker_start = f"%%ev: {evidence_id} "
    _before, marker_and_rest = original.split(marker_start, 1)
    marker = marker_start + marker_and_rest.split("%%", 1)[0] + "%%"
    anchor = f"^blk-{evidence_id.removeprefix('ev-')}"
    other_id = "ev-1234abcd"
    other_marker = marker.replace(evidence_id, other_id)
    other_anchor = f"^blk-{other_id.removeprefix('ev-')}"
    draft.write_text(
        original + f"\nValid second claim. {other_anchor} {other_marker}\n",
        encoding="utf-8",
    )
    assert verify_project_draft(tmp_path, "project-alpha")["ready"] is True

    draft.write_text(
        draft.read_text(encoding="utf-8").replace(f"{anchor} {marker}", ""),
        encoding="utf-8",
    )
    external = tmp_path / "notes/external-hidden.md"
    external.parent.mkdir(parents=True, exist_ok=True)
    external.write_text(
        f"<!-- Hidden claim. {anchor} {marker} -->\n",
        encoding="utf-8",
    )

    verification = verify_project_draft(tmp_path, "project-alpha")

    assert verification["ready"] is False
    assert any(
        finding["kind"] == "evidence-text-unbound" and finding["evidence_id"] == evidence_id
        for finding in verification["findings"]
    )
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
    fresh_evidence_id = "ev-1234abcd"
    fresh_marker = marker.replace(evidence_id, fresh_evidence_id)
    fresh_anchor = f"^blk-{fresh_evidence_id.removeprefix('ev-')}"
    draft.write_text(
        f"Supported claim. {fresh_anchor} {fresh_marker}\n\nSource note: `notes/support.md`\n",
        encoding="utf-8",
    )
    state.rebuild_evidence_sets_from_markers(tmp_path)
    [bound] = state.evidence_sets(tmp_path)

    assert verify_project_draft(tmp_path, "project-alpha")["ready"] is True
    assert (
        "[@source-alpha]" in write_project_export(tmp_path, "project-alpha", draft=True)["content"]
    )

    draft.write_text(
        f"# Supported claim {fresh_anchor}\n"
        f"Changed unsupported claim. {fresh_marker}\n\n"
        "Source note: `notes/support.md`\n",
        encoding="utf-8",
    )
    verification = verify_project_draft(tmp_path, "project-alpha")

    assert verification["ready"] is False
    assert verification["findings"] == [
        {
            "kind": "evidence-text-unbound",
            "severity": "high",
            "evidence_id": fresh_evidence_id,
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
    draft, evidence_id = _compose_source_backed_draft(
        tmp_path,
        body="This claim has a resolvable block but no stored binding.",
    )
    original = draft.read_text(encoding="utf-8")
    marker_start = f"%%ev: {evidence_id} "
    _before, marker_and_rest = original.split(marker_start, 1)
    marker = marker_start + marker_and_rest.split("%%", 1)[0] + "%%"
    anchor = f"^blk-{evidence_id.removeprefix('ev-')}"
    unbound_evidence_id = "ev-1234abcd"
    unbound_marker = marker.replace(evidence_id, unbound_evidence_id)
    unbound_anchor = f"^blk-{unbound_evidence_id.removeprefix('ev-')}"
    draft.write_text(
        original.replace(f"{anchor} {marker}", f"{unbound_anchor} {unbound_marker}"),
        encoding="utf-8",
    )
    with state.connect(tmp_path) as conn:
        conn.execute(
            "INSERT INTO evidence_bindings(id, block_text_sha256) VALUES (?, NULL)",
            (unbound_evidence_id,),
        )

    verification = verify_project_draft(tmp_path, "project-alpha")
    [bound] = state.evidence_sets(tmp_path)

    assert verification["ready"] is False
    assert verification["findings"] == [
        {
            "kind": "evidence-text-unbound",
            "severity": "high",
            "evidence_id": unbound_evidence_id,
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
        allow_unready=True,
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


@pytest.mark.parametrize("standing", ["retracted", "superseded"])
def test_stale_source_blocks_draft_and_pi_disposition_cannot_clear_it(
    tmp_path: Path, standing: str
) -> None:
    _draft, evidence_id = _compose_source_backed_draft(
        tmp_path,
        body="Claim over a source that later loses standing.",
    )
    [bound] = state.evidence_sets(tmp_path)
    assert verify_project_draft(tmp_path, "project-alpha")["ready"] is True

    _set_source_standing(tmp_path, "source-alpha", standing)
    verification = verify_project_draft(tmp_path, "project-alpha")

    assert verification["ready"] is False
    stale = [
        finding
        for finding in verification["findings"]
        if finding["kind"] == "evidence-source-stale"
    ]
    assert stale == [
        {
            "kind": "evidence-source-stale",
            "severity": "high",
            "evidence_id": evidence_id,
            "block_ref": bound["block_ref"],
            "work_id": "source-alpha",
            "path": [],
        }
    ]
    assert f"evidence-source-stale:{evidence_id}" in verification["missing"]

    resolve_evidence_review(
        tmp_path,
        evidence_id,
        decision="accept",
        reason="PI cannot clear staleness",
    )
    after = verify_project_draft(tmp_path, "project-alpha")

    assert after["ready"] is False
    assert any(finding["kind"] == "evidence-source-stale" for finding in after["findings"])
    with pytest.raises(ValueError, match="evidence-source-stale"):
        write_project_export(tmp_path, "project-alpha", draft=True)


def test_stale_taint_propagates_through_nested_sets_with_path(tmp_path: Path) -> None:
    vault = tmp_path
    state.upsert_catalog_record(
        vault,
        work_id="source-alpha",
        citekey="source-alpha",
        title="Alpha Source",
        check_status="checked",
        content_path=".memoria/blobs/source-content/source-alpha.md",
    )
    _source_span(vault, "source-alpha")
    _project(vault)
    draft = vault / "projects/project-alpha/draft.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(
        "---\ntype: draft\nproject: projects/project-alpha/project.md\n---\n\n"
        "# Alpha project\n\n"
        "Direct claim. ^blk-aaaa1111 %%ev: ev-aaaa1111 "
        "items=source-alpha#^p0001%%\n\n"
        "Nested claim. ^blk-bbbb2222 %%ev: ev-bbbb2222 items=ev-aaaa1111%%\n",
        encoding="utf-8",
    )
    _set_source_standing(vault, "source-alpha", "retracted")

    verification = verify_project_draft(vault, "project-alpha")

    stale = sorted(
        (finding["evidence_id"], finding["work_id"], finding["path"])
        for finding in verification["findings"]
        if finding["kind"] == "evidence-source-stale"
    )
    assert stale == [
        ("ev-aaaa1111", "source-alpha", []),
        ("ev-bbbb2222", "source-alpha", ["ev-aaaa1111"]),
    ]
    assert verification["ready"] is False


def test_stale_taint_reaches_a_nested_set_outside_the_draft(tmp_path: Path) -> None:
    vault = tmp_path
    state.upsert_catalog_record(
        vault,
        work_id="source-alpha",
        citekey="source-alpha",
        title="Alpha Source",
        check_status="checked",
        content_path=".memoria/blobs/source-content/source-alpha.md",
    )
    _source_span(vault, "source-alpha")
    _project(vault)
    external = vault / "notes/external-grounds.md"
    external.parent.mkdir(parents=True, exist_ok=True)
    external.write_text(
        "External grounds. ^blk-aaaa1111 %%ev: ev-aaaa1111 items=source-alpha#^p0001%%\n",
        encoding="utf-8",
    )
    draft = vault / "projects/project-alpha/draft.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(
        "---\ntype: draft\nproject: projects/project-alpha/project.md\n---\n\n"
        "# Alpha project\n\n"
        "Nested claim. ^blk-bbbb2222 %%ev: ev-bbbb2222 items=ev-aaaa1111%%\n",
        encoding="utf-8",
    )
    _set_source_standing(vault, "source-alpha", "retracted")

    verification = verify_project_draft(vault, "project-alpha")

    stale = [
        finding
        for finding in verification["findings"]
        if finding["kind"] == "evidence-source-stale"
    ]
    assert stale == [
        {
            "kind": "evidence-source-stale",
            "severity": "high",
            "evidence_id": "ev-bbbb2222",
            "block_ref": "projects/project-alpha/draft.md#^blk-bbbb2222",
            "work_id": "source-alpha",
            "path": ["ev-aaaa1111"],
        }
    ]


def test_archived_source_is_advisory_and_never_blocks_export(tmp_path: Path) -> None:
    _draft, evidence_id = _compose_source_backed_draft(
        tmp_path,
        body="Claim over an archived source.",
    )
    [bound] = state.evidence_sets(tmp_path)
    _set_source_standing(tmp_path, "source-alpha", "archived")

    verification = verify_project_draft(tmp_path, "project-alpha")

    assert verification["ready"] is True
    assert verification["ok"] is True
    assert verification["missing"] == []
    assert verification["findings"] == [
        {
            "kind": "evidence-source-archived",
            "severity": "medium",
            "evidence_id": evidence_id,
            "block_ref": bound["block_ref"],
            "work_id": "source-alpha",
            "path": [],
        }
    ]
    exported = write_project_export(tmp_path, "project-alpha", draft=True)
    assert "%%ev:" not in exported["content"]


def test_unset_standing_is_current_and_raises_no_standing_finding(tmp_path: Path) -> None:
    _compose_source_backed_draft(
        tmp_path,
        body="Claim over a source without standing.",
    )

    verification = verify_project_draft(tmp_path, "project-alpha")

    assert verification["ready"] is True
    assert verification["ok"] is True
    assert verification["missing"] == []
    assert not any(
        finding["kind"].startswith("evidence-source-") for finding in verification["findings"]
    )


def test_advisory_before_stale_truncation_keeps_stale_readiness_and_missing(
    tmp_path: Path,
) -> None:
    draft, evidence_id = _compose_source_backed_draft(
        tmp_path,
        body="Claim over sources with distinct standing.",
    )
    _set_source_standing(tmp_path, "source-beta", "retracted")
    _source_span(tmp_path, "source-beta")
    draft.write_text(
        draft.read_text(encoding="utf-8").replace(
            "items=source-alpha#^p0001%%",
            "items=source-alpha#^p0001|source-beta#^p0001%%",
        ),
        encoding="utf-8",
    )
    state.rebuild_evidence_sets_from_markers(tmp_path)
    resolve_evidence_review(
        tmp_path,
        evidence_id,
        decision="accept",
        reason="PI accepts the multi-source grounds shape",
    )
    _set_source_standing(tmp_path, "source-alpha", "archived")

    verification = verify_project_draft(tmp_path, "project-alpha", max_findings=1)

    assert [finding["kind"] for finding in verification["findings"]] == ["evidence-source-archived"]
    assert verification["ready"] is False
    assert verification["ok"] is False
    assert verification["missing"] == [f"evidence-source-stale:{evidence_id}"]


def test_archived_advisory_is_excluded_from_blocking_export_reason(tmp_path: Path) -> None:
    draft, _evidence_id = _compose_source_backed_draft(
        tmp_path,
        body="Claim over an archived source with a separate export problem.",
    )
    _set_source_standing(tmp_path, "source-alpha", "archived")
    draft.write_text(
        draft.read_text(encoding="utf-8").replace(
            "Source note: `notes/support.md`",
            "Source note: `notes/missing.md`",
        ),
        encoding="utf-8",
    )

    verification = verify_project_draft(tmp_path, "project-alpha")

    assert verification["ready"] is False
    assert [finding["kind"] for finding in verification["findings"]] == [
        "evidence-source-archived",
        "broken-structural-reference",
    ]
    assert verification["missing"] == ["broken-structural-reference"]
    with pytest.raises(ValueError, match="broken-structural-reference") as error:
        write_project_export(tmp_path, "project-alpha", draft=True)
    assert "evidence-source-archived" not in str(error.value)


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


def _set_source_standing(vault: Path, work_id: str, standing: str) -> None:
    state.upsert_catalog_record(
        vault,
        work_id=work_id,
        citekey=work_id,
        title=f"{work_id} title",
        check_status="checked",
        content_path=f".memoria/blobs/source-content/{work_id}.md",
        csl_json={"memoria": {"standing": standing}},
    )


def _compose_source_backed_draft(vault: Path, *, body: str) -> tuple[Path, str]:
    state.upsert_catalog_record(
        vault,
        work_id="source-alpha",
        citekey="source-alpha",
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


def test_every_disposition_emits_disposition_v1_event(tmp_path: Path) -> None:
    vault = tmp_path
    evidence_id = _compose_implicit_draft(
        vault, body="Each seam action lands one disposition.v1 event."
    )

    for decision in ("defer", "edit", "reject", "accept"):
        resolve_evidence_review(
            vault, evidence_id, decision=decision, reason=f"PI chose {decision}"
        )

    with state.connect(vault) as conn:
        rows = conn.execute(
            "SELECT payload_json FROM event_log WHERE event_type = 'disposition' ORDER BY event_id"
        ).fetchall()
    payloads = [json.loads(row["payload_json"]) for row in rows]

    assert [payload["decision"] for payload in payloads] == [
        "defer",
        "edit",
        "reject",
        "accept",
    ]
    assert {payload["schema"] for payload in payloads} == {"disposition.v1"}
    assert {payload["item_type"] for payload in payloads} == {"evidence-set"}
    assert {payload["item_id"] for payload in payloads} == {evidence_id}

    with state.connect(vault) as conn:
        paired_rows = conn.execute(
            """
            SELECT event_type, timestamp, machine, payload_json
            FROM event_log
            WHERE event_type IN ('resolved', 'disposition')
            ORDER BY event_id
            """
        ).fetchall()

    assert len(paired_rows) == 8
    for decision, offset in zip(("defer", "edit", "reject", "accept"), range(0, 8, 2), strict=True):
        resolved, disposition = paired_rows[offset : offset + 2]
        resolved_payload = json.loads(resolved["payload_json"])
        disposition_payload = json.loads(disposition["payload_json"])

        assert [resolved["event_type"], disposition["event_type"]] == ["resolved", "disposition"]
        assert resolved["timestamp"] == disposition["timestamp"]
        assert resolved_payload["timestamp"] == disposition_payload["timestamp"]
        assert resolved_payload["timestamp"] == resolved["timestamp"]
        assert [resolved_payload["decision"], disposition_payload["decision"]] == [
            decision,
            decision,
        ]
        assert [resolved_payload["actor"], disposition_payload["actor"]] == ["pi", "pi"]
        assert [resolved_payload["machine"], disposition_payload["machine"]] == [
            "test-machine",
            "test-machine",
        ]
        assert [resolved["machine"], disposition["machine"]] == [
            "test-machine",
            "test-machine",
        ]
