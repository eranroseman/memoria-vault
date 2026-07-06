"""Evidence-set marker and anchor primitives for draft verification."""

from __future__ import annotations

import re
import secrets
from collections.abc import Callable, Iterable
from dataclasses import dataclass

EVIDENCE_TYPES = frozenset({"single-span", "multi-span", "multi-hop", "implicit"})
EVIDENCE_STATES = frozenset({"complete", "evidence-incomplete"})

_EV_ID_RE = re.compile(r"^ev-[0-9a-f]{8}$")
_EV_MARKER_RE = re.compile(r"%%ev:\s*(?P<body>.*?)%%")
_SOURCE_SPAN_RE = re.compile(r"^(?P<work_id>[A-Za-z0-9][A-Za-z0-9._-]*)#\^p(?P<page>\d{4,})$")
_BLOCK_REF_RE = re.compile(r"^(?P<path>[^#\n\r]+)#\^blk-(?P<block_id>[A-Za-z0-9][A-Za-z0-9_-]*)$")


@dataclass(frozen=True)
class SourceSpanRef:
    work_id: str
    page: str


@dataclass(frozen=True)
class BlockRef:
    path: str
    block_id: str


@dataclass(frozen=True)
class EvidenceMarker:
    evidence_id: str
    evidence_type: str
    state: str
    review_required: bool
    items: tuple[str, ...]


def parse_source_span_ref(ref: str) -> SourceSpanRef:
    value = ref.strip()
    match = _SOURCE_SPAN_RE.fullmatch(value)
    if not match:
        raise ValueError(f"invalid source-span ref: {ref!r}")
    return SourceSpanRef(match.group("work_id"), f"p{match.group('page')}")


def parse_block_ref(ref: str) -> BlockRef:
    value = ref.strip()
    match = _BLOCK_REF_RE.fullmatch(value)
    if not match:
        raise ValueError(f"invalid block ref: {ref!r}")
    path = match.group("path").replace("\\", "/").strip()
    parts = [part for part in path.split("/") if part and part != "."]
    if not path or path.startswith("/") or ".." in parts:
        raise ValueError(f"invalid block ref path: {ref!r}")
    return BlockRef(path, match.group("block_id"))


def evidence_ref_kind(ref: str) -> str:
    value = ref.strip()
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

    fields: dict[str, str] = {}
    for part in parts[1:]:
        if "=" not in part:
            raise ValueError(f"invalid evidence marker field: {part!r}")
        key, raw = part.split("=", 1)
        fields[key] = raw

    unknown = set(fields) - {"type", "state", "review", "items"}
    if unknown:
        raise ValueError(f"unknown evidence marker field(s): {sorted(unknown)}")

    evidence_type = fields.get("type", "")
    state = fields.get("state", "")
    if evidence_type not in EVIDENCE_TYPES:
        raise ValueError(f"invalid evidence type: {evidence_type!r}")
    if state not in EVIDENCE_STATES:
        raise ValueError(f"invalid evidence state: {state!r}")

    items = tuple(item for item in fields.get("items", "").split("|") if item)
    for item in items:
        evidence_ref_kind(item)

    return EvidenceMarker(
        evidence_id=parts[0],
        evidence_type=evidence_type,
        state=state,
        review_required=_parse_review(fields.get("review", "")),
        items=items,
    )


def serialize_evidence_marker(marker: EvidenceMarker) -> str:
    if not _EV_ID_RE.fullmatch(marker.evidence_id):
        raise ValueError(f"invalid evidence id: {marker.evidence_id!r}")
    if marker.evidence_type not in EVIDENCE_TYPES:
        raise ValueError(f"invalid evidence type: {marker.evidence_type!r}")
    if marker.state not in EVIDENCE_STATES:
        raise ValueError(f"invalid evidence state: {marker.state!r}")
    for item in marker.items:
        evidence_ref_kind(item)
    review = "true" if marker.review_required else "false"
    items = "|".join(marker.items)
    return (
        f"%%ev: {marker.evidence_id} type={marker.evidence_type} "
        f"state={marker.state} review={review} items={items}%%"
    )


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


def _parse_review(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "required", "yes", "1"}:
        return True
    if normalized in {"false", "clear", "none", "no", "0"}:
        return False
    raise ValueError(f"invalid evidence review flag: {value!r}")
