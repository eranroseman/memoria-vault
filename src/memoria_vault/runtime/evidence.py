"""Evidence-set marker and anchor primitives for draft verification."""

from __future__ import annotations

import re
import secrets
from collections.abc import Callable, Iterable
from dataclasses import dataclass

_EV_ID_RE = re.compile(r"^ev-[0-9a-f]{8}$")
_EV_MARKER_RE = re.compile(r"%%ev:\s*(?P<body>.*?)%%")
_SOURCE_SPAN_RE = re.compile(r"^(?P<work_id>[A-Za-z0-9][A-Za-z0-9._-]*)#\^p(?P<page>\d{4,})$")
_CODE_GROUNDS_RE = re.compile(
    r"^code-grounds:(?P<run_id>[A-Za-z0-9._:-]+):(?P<artifact_id>[A-Za-z0-9._-]+):"
    r"(?P<output_sha256>sha256:[0-9a-f]{64})$"
)


@dataclass(frozen=True)
class SourceSpanRef:
    work_id: str
    page: str


@dataclass(frozen=True)
class CodeGroundsRef:
    run_id: str
    artifact_id: str
    output_sha256: str


@dataclass(frozen=True)
class EvidenceMarker:
    evidence_id: str
    items: tuple[str, ...]


def parse_source_span_ref(ref: str) -> SourceSpanRef:
    value = ref.strip()
    match = _SOURCE_SPAN_RE.fullmatch(value)
    if not match:
        raise ValueError(f"invalid source-span ref: {ref!r}")
    return SourceSpanRef(match.group("work_id"), f"p{match.group('page')}")


def parse_code_grounds_ref(ref: str) -> CodeGroundsRef:
    value = ref.strip()
    match = _CODE_GROUNDS_RE.fullmatch(value)
    if not match:
        raise ValueError(f"invalid code-grounds ref: {ref!r}")
    return CodeGroundsRef(
        match.group("run_id"),
        match.group("artifact_id"),
        match.group("output_sha256"),
    )


def evidence_ref_kind(ref: str) -> str:
    value = ref.strip()
    if _CODE_GROUNDS_RE.fullmatch(value):
        return "code-grounds"
    if _EV_ID_RE.fullmatch(value):
        return "evidence-set"
    parse_source_span_ref(value)
    return "source-span"


def parse_evidence_marker(marker: str) -> EvidenceMarker:
    value = marker.strip()
    match = _EV_MARKER_RE.fullmatch(value)
    if not match:
        raise ValueError(f"invalid evidence marker: {marker!r}")
    parts = match.group("body").split()
    if not parts or not _EV_ID_RE.fullmatch(parts[0]):
        raise ValueError(f"invalid evidence marker id: {marker!r}")

    items: tuple[str, ...] = ()
    has_items_field = False
    for part in parts[1:]:
        if "=" not in part:
            raise ValueError(f"invalid evidence marker field: {part!r}")
        key, raw = part.split("=", 1)
        if key != "items":
            raise ValueError(f"unknown evidence marker field: {key!r}")
        if has_items_field:
            raise ValueError("duplicate evidence marker field: 'items'")
        has_items_field = True
        if raw:
            items = tuple(raw.split("|"))
            if any(not item for item in items):
                raise ValueError("empty evidence marker item")

    for item in items:
        evidence_ref_kind(item)

    return EvidenceMarker(evidence_id=parts[0], items=items)


def serialize_evidence_marker(marker: EvidenceMarker) -> str:
    if not _EV_ID_RE.fullmatch(marker.evidence_id):
        raise ValueError(f"invalid evidence id: {marker.evidence_id!r}")
    for item in marker.items:
        evidence_ref_kind(item)
    return f"%%ev: {marker.evidence_id} items={'|'.join(marker.items)}%%"


def extract_evidence_markers(text: str) -> list[EvidenceMarker]:
    return [parse_evidence_marker(match.group(0)) for match in _EV_MARKER_RE.finditer(text)]


def evidence_ids_in_text(text: str) -> set[str]:
    return {marker.evidence_id for marker in extract_evidence_markers(text)}


def mint_evidence_id(
    existing_ids: Iterable[str] = (),
    *,
    token_factory: Callable[[], str] | None = None,
) -> str:
    existing = set(existing_ids)
    make_token = token_factory or (lambda: secrets.token_hex(4))
    for _ in range(1024):
        token = make_token().lower().removeprefix("ev-")
        candidate = f"ev-{token[:8]}"
        if _EV_ID_RE.fullmatch(candidate) and candidate not in existing:
            return candidate
    raise RuntimeError("could not mint a unique evidence id")
