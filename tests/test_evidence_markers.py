from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from memoria_vault.runtime import evidence
from memoria_vault.runtime.evidence import (
    EvidenceMarker,
    SourceSpanRef,
    evidence_ids_in_text,
    evidence_ref_kind,
    extract_evidence_markers,
    mint_evidence_id,
    parse_evidence_marker,
    parse_source_span_ref,
    serialize_evidence_marker,
)

pytestmark = pytest.mark.unit


def test_evidence_marker_v2_has_only_id_and_items_fields() -> None:
    marker = EvidenceMarker(evidence_id="ev-deadbeef", items=())

    assert tuple(marker.__dataclass_fields__) == ("evidence_id", "items")
    with pytest.raises(FrozenInstanceError):
        marker.items = ("source-alpha#^p0001",)  # type: ignore[misc]


def test_evidence_marker_round_trips_canonical_v2_form() -> None:
    marker = EvidenceMarker(
        evidence_id="ev-deadbeef",
        items=("source-alpha#^p0001", "ev-feedcafe"),
    )

    text = serialize_evidence_marker(marker)

    assert text == "%%ev: ev-deadbeef items=source-alpha#^p0001|ev-feedcafe%%"
    assert parse_evidence_marker(text) == marker


def test_serializer_emits_items_for_an_empty_marker() -> None:
    assert (
        serialize_evidence_marker(EvidenceMarker("ev-deadbeef", ())) == "%%ev: ev-deadbeef items=%%"
    )


def test_empty_and_omitted_items_both_parse_as_no_items() -> None:
    assert parse_evidence_marker("%%ev: ev-deadbeef items=%%").items == ()
    assert parse_evidence_marker("%%ev: ev-deadbeef%%").items == ()


@pytest.mark.parametrize(
    "field",
    [
        "type=single-span",
        "state=complete",
        "review=false",
        "unrecognized=value",
    ],
)
def test_parser_rejects_retired_and_unknown_fields_individually(field: str) -> None:
    with pytest.raises(ValueError, match="unknown evidence marker field"):
        parse_evidence_marker(f"%%ev: ev-deadbeef {field} items=source-alpha#^p0001%%")


@pytest.mark.parametrize(
    "marker",
    [
        "%%ev: ev-deadbeef items=work-a#^p0001 items=work-b#^p0002%%",
        "%%ev: ev-deadbeef items= items=work-a#^p0001%%",
        "%%ev: ev-deadbeef items=work-a#^p0001 items=%%",
        "%%ev: ev-deadbeef items= items=%%",
    ],
)
def test_parser_rejects_duplicate_items_fields(marker: str) -> None:
    with pytest.raises(ValueError, match="duplicate evidence marker field"):
        parse_evidence_marker(marker)


def test_parser_rejects_a_trailing_token_without_an_equals_sign() -> None:
    with pytest.raises(ValueError, match="invalid evidence marker field"):
        parse_evidence_marker("%%ev: ev-deadbeef items=work-a#^p0001 trailing%%")


@pytest.mark.parametrize(
    "items",
    [
        "work-a#^p0001||ev-feedcafe",
        "|work-a#^p0001",
        "work-a#^p0001|",
    ],
)
def test_parser_rejects_empty_pipe_components(items: str) -> None:
    with pytest.raises(ValueError, match="empty evidence marker item"):
        parse_evidence_marker(f"%%ev: ev-deadbeef items={items}%%")


def test_parser_preserves_ordered_duplicate_nonempty_items() -> None:
    assert parse_evidence_marker(
        "%%ev: ev-deadbeef items=ev-feedcafe|work-a#^p0001|ev-feedcafe%%"
    ).items == ("ev-feedcafe", "work-a#^p0001", "ev-feedcafe")


def test_evidence_marker_accepts_code_grounds_items() -> None:
    item = "code-grounds:run-1:analysis:sha256:" + "0" * 64
    marker = EvidenceMarker("ev-deadbeef", (item,))

    assert parse_evidence_marker(f"%%ev: ev-deadbeef items={item}%%") == marker
    assert serialize_evidence_marker(marker) == f"%%ev: ev-deadbeef items={item}%%"


def test_marker_parser_fails_closed_on_an_unclassifiable_item() -> None:
    with pytest.raises(ValueError, match="invalid source-span ref"):
        parse_evidence_marker("%%ev: ev-deadbeef items=@smith2024#^p0001%%")


def test_extract_evidence_markers_from_draft_text() -> None:
    text = (
        "Claim one. %%ev: ev-11111111 items=work-a#^p0001%%\nClaim two. %%ev: ev-22222222 items=%%"
    )

    markers = extract_evidence_markers(text)

    assert [marker.evidence_id for marker in markers] == ["ev-11111111", "ev-22222222"]
    assert evidence_ids_in_text(text) == {"ev-11111111", "ev-22222222"}


def test_evidence_ref_validation_accepts_source_spans_and_nested_evidence_sets() -> None:
    assert parse_source_span_ref("source-alpha#^p0001") == SourceSpanRef("source-alpha", "p0001")
    assert evidence_ref_kind("ev-deadbeef") == "evidence-set"
    assert evidence_ref_kind("source-alpha#^p0001") == "source-span"


def test_code_grounds_refs_validate_and_retired_refs_fail_closed() -> None:
    ref = "code-grounds:run-1:analysis:sha256:" + "0" * 64

    assert evidence.parse_code_grounds_ref(ref) == evidence.CodeGroundsRef(
        run_id="run-1",
        artifact_id="analysis",
        output_sha256="sha256:" + "0" * 64,
    )
    assert evidence_ref_kind(ref) == "code-grounds"
    with pytest.raises(ValueError, match="invalid code-grounds ref"):
        evidence.parse_code_grounds_ref(ref.replace("code-grounds", "code-warrant"))
    with pytest.raises(ValueError, match="invalid source-span ref"):
        evidence_ref_kind(ref.replace("code-grounds", "code-warrant"))


def test_evidence_ref_validation_rejects_citekey_shaped_span() -> None:
    with pytest.raises(ValueError, match="invalid source-span ref"):
        evidence_ref_kind("@smith2024#^p0001")


def test_mint_evidence_id_retries_on_collision() -> None:
    tokens = iter(["deadbeef", "feedcafe"])

    assert mint_evidence_id({"ev-deadbeef"}, token_factory=lambda: next(tokens)) == "ev-feedcafe"
