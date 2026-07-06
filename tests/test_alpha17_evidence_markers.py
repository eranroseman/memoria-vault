from __future__ import annotations

import pytest

from memoria_vault.runtime.evidence import (
    BlockRef,
    EvidenceMarker,
    SourceSpanRef,
    evidence_ids_in_text,
    evidence_ref_kind,
    extract_evidence_markers,
    mint_evidence_id,
    parse_block_ref,
    parse_evidence_marker,
    parse_source_span_ref,
    serialize_evidence_marker,
)


def test_evidence_marker_round_trips_canonical_form() -> None:
    marker = EvidenceMarker(
        evidence_id="ev-deadbeef",
        evidence_type="multi-span",
        state="complete",
        review_required=True,
        items=("source-alpha#^p0001", "ev-feedcafe"),
    )

    text = serialize_evidence_marker(marker)

    assert text == (
        "%%ev: ev-deadbeef type=multi-span state=complete "
        "review=true items=source-alpha#^p0001|ev-feedcafe%%"
    )
    assert parse_evidence_marker(text) == marker


def test_extract_evidence_markers_from_draft_text() -> None:
    text = (
        "Claim one. %%ev: ev-11111111 type=single-span state=complete "
        "review=false items=work-a#^p0001%%\n"
        "Claim two. %%ev: ev-22222222 type=implicit state=evidence-incomplete "
        "review=true items=%%"
    )

    markers = extract_evidence_markers(text)

    assert [marker.evidence_id for marker in markers] == ["ev-11111111", "ev-22222222"]
    assert evidence_ids_in_text(text) == {"ev-11111111", "ev-22222222"}


def test_evidence_ref_validation_accepts_source_spans_and_nested_evidence_sets() -> None:
    assert parse_source_span_ref("source-alpha#^p0001") == SourceSpanRef("source-alpha", "p0001")
    assert evidence_ref_kind("ev-deadbeef") == "evidence-set"
    assert evidence_ref_kind("source-alpha#^p0001") == "source-span"


def test_evidence_ref_validation_rejects_citekey_shaped_span() -> None:
    with pytest.raises(ValueError, match="invalid source-span ref"):
        evidence_ref_kind("@smith2024#^p0001")


def test_block_refs_are_local_workspace_refs() -> None:
    assert parse_block_ref("notes/claim.md#^blk-abc123") == BlockRef("notes/claim.md", "abc123")
    with pytest.raises(ValueError, match="invalid block ref path"):
        parse_block_ref("../notes/claim.md#^blk-abc123")


def test_mint_evidence_id_retries_on_collision() -> None:
    tokens = iter(["deadbeef", "feedcafe"])

    assert mint_evidence_id({"ev-deadbeef"}, token_factory=lambda: next(tokens)) == "ev-feedcafe"
