"""Multi-entry parsing and adapter normalization for `memoria work import`.

The shipped single-entry builders (`bibtex_capture_payload` /
`csl_capture_payload`, runtime/capture.py) parse exactly one entry and stay
untouched; these splitters cut a multi-entry file into per-entry chunks that
feed them. A BibTeX entry whose container never closes is returned as the
final chunk so the bulk driver can name the failure instead of dropping it.

The O2 section-4 adapter map is deliberately separate from capture.py's
``_item_type``. That shipped helper silently labels unknown types ``article``;
this module preserves that fallback while exposing whether it was mapped, so a
later integration seam can make the guess visible. For ``@misc``, repo-host
URLs win over DataCite dataset DOI prefixes, which win over ordinary URLs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from memoria_vault.runtime import state
from memoria_vault.runtime.capture import (
    bibtex_capture_payload,
    csl_capture_payload,
    parse_bibtex_entry,
)

_ENTRY_TYPE_MAP: dict[str, str] = {
    "article": "article",
    "book": "book",
    "webpage": "webpage",
    "software": "software",
    "dataset": "dataset",
    "report": "report",
    "inproceedings": "article",
    "incollection": "article",
    "conference": "article",
    "inbook": "book",
    "booklet": "book",
    "online": "webpage",
    "www": "webpage",
    "data": "dataset",
    "manual": "software",
    "techreport": "report",
    "phdthesis": "report",
    "mastersthesis": "report",
    "article-journal": "article",
    "paper-conference": "article",
    "chapter": "article",
    "thesis": "report",
    "post-weblog": "webpage",
}

_REPO_HOSTS = ("github.com", "gitlab.com", "codeberg.org")
_DATASET_DOI_PREFIXES = frozenset(
    {"10.5281", "10.5061", "10.6084", "10.7910", "10.17632", "10.3886", "10.15468", "10.24432"}
)
_DUPLICATE_IDENTIFIER_FIELDS = ("arxiv", "pmcid")
_BIBTEX_ENTRY_START = re.compile(r"@\s*[A-Za-z][A-Za-z0-9_-]*\s*[({]")


def split_bibtex_entries(text: str) -> list[str]:
    """Split BibTeX text on top-level @ boundaries, brace- and paren-aware."""
    entries: list[str] = []
    index = _next_bibtex_entry_start(text, 0)
    while index != -1:
        end = _entry_end(text, index)
        if end is None:
            entries.append(text[index:].strip())
            break
        entries.append(text[index : end + 1].strip())
        index = _next_bibtex_entry_start(text, end + 1)
    return entries


def _next_bibtex_entry_start(text: str, start: int) -> int:
    """Find a real entry opener, ignoring @ signs in percent comments."""
    in_comment = False
    for index in range(start, len(text)):
        char = text[index]
        if char == "\n":
            in_comment = False
        elif in_comment:
            continue
        elif char == "%":
            in_comment = True
        elif char == "@" and _BIBTEX_ENTRY_START.match(text, index):
            return index
    return -1


def _entry_end(text: str, start: int) -> int | None:
    """Index of the container close matching this entry's opener, or None.

    A second top-level ``@`` before any opener ends the (malformed) chunk
    just before it; an unclosed container returns None (tail chunk).
    """
    closer = ""
    depth = 0
    for index in range(start + 1, len(text)):
        char = text[index]
        if not closer:
            if char == "{":
                closer, depth = "}", 1
            elif char == "(":
                closer, depth = ")", 1
            elif char == "@":
                return index - 1
        elif char == "{" and closer == "}":
            depth += 1
        elif char == "(" and closer == ")":
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return index
    return None


def split_csl_entries(text: str) -> list[str]:
    """Split CSL-JSON: array -> per-item dumps; single object -> [text]."""
    data = json.loads(text)
    if isinstance(data, dict):
        return [text]
    if isinstance(data, list):
        items: list[str] = []
        for index, item in enumerate(data, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"CSL array item {index} must be a JSON object")
            items.append(json.dumps(item, ensure_ascii=False, sort_keys=True))
        return items
    raise ValueError("CSL import expects a JSON object or array of objects")


_CITEKEY = re.compile(r"@\s*[^({\s][^({]*[{(]\s*([^,\s{}()]+)")


def build_entry_payload(fmt: str, entry_text: str) -> dict[str, Any]:
    """Build one capture-source payload from one split entry chunk."""
    if fmt == "bibtex":
        return bibtex_capture_payload(entry_text)
    item = json.loads(entry_text)
    if not isinstance(item, dict):
        raise ValueError("CSL entry must be a JSON object")
    payload = csl_capture_payload(item, raw_text=entry_text)
    payload["identifiers"] = _normalized_entry_identifiers(item, payload["identifiers"])
    return payload


def parse_entry_fields(fmt: str, entry_text: str) -> dict[str, Any]:
    """Derive the flat adapter field map for one split entry chunk.

    BibTeX becomes ``{"type": entry_type, **fields}``; CSL is the parsed item.
    This is the shape ``entry_item_type`` / ``entry_type_mapped`` / ``entry_fetch``
    read, so the driver never re-implements either extraction.
    """
    if fmt == "bibtex":
        entry = parse_bibtex_entry(entry_text)
        return {"type": entry["entry_type"], **entry["fields"]}
    item = json.loads(entry_text)
    if not isinstance(item, dict):
        raise ValueError("CSL entry must be a JSON object")
    return item


def entry_ref(fmt: str, entry_text: str, index: int) -> str:
    """Name a failed entry: citekey / CSL id when recoverable, else the index."""
    if fmt == "bibtex":
        if match := _CITEKEY.match(entry_text.strip()):
            return match.group(1)
    else:
        try:
            item = json.loads(entry_text)
        except ValueError:
            item = None
        if isinstance(item, dict) and str(item.get("id") or "").strip():
            return str(item["id"])
    return f"entry-{index}"


def entry_fetch(entry_fields: dict[str, Any], identifiers: dict[str, Any]) -> dict[str, str] | None:
    """Synthesize only a fetch descriptor the policy-bound resolver supports."""
    identifiers = _normalized_entry_identifiers(entry_fields, identifiers)
    pmcid = str(identifiers.get("pmcid") or "").strip()
    if pmcid:
        if not pmcid.upper().startswith("PMC"):
            pmcid = f"PMC{pmcid}"
        return {
            "method": "pmc-oa",
            "url": f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id={pmcid}",
        }
    arxiv = str(identifiers.get("arxiv") or "").strip()
    if arxiv.lower().startswith("arxiv:"):
        arxiv = arxiv[len("arxiv:") :].strip()
    if arxiv:
        return {"method": "arxiv-pdf", "url": f"https://export.arxiv.org/pdf/{arxiv}"}
    url = _entry_url(entry_fields)
    if url.lower().endswith(".pdf"):
        return {"method": "pdf-url", "url": url}
    return None


def _normalized_entry_identifiers(
    entry_fields: dict[str, Any], identifiers: dict[str, Any]
) -> dict[str, Any]:
    """Preserve PMCID/arXiv identifiers from either BibTeX or CSL field casing."""
    normalized = dict(identifiers)
    supplied = {str(key).casefold(): value for key, value in identifiers.items()}
    fields = {str(key).casefold(): value for key, value in entry_fields.items()}
    for name in ("pmcid", "arxiv"):
        value = supplied.get(name) or fields.get(name)
        if text := str(value or "").strip():
            normalized[name] = text
    return normalized


def entry_capture_request(
    payload: dict[str, Any],
    fetch: dict[str, str] | None,
    *,
    mapped: bool = True,
) -> tuple[str, dict[str, Any]]:
    """Build one admission request without fetching or authorizing a URL."""
    item_type = str(payload.get("item_type") or "article")
    resource = str(payload.get("resource") or "").strip()
    if mapped and item_type == "webpage" and resource:
        return (
            "capture-url-source",
            {
                "url": resource,
                "title": str(payload.get("title") or ""),
                "description": str(payload.get("description") or ""),
            },
        )
    if not mapped or not isinstance(fetch, dict):
        return "capture-source", payload
    method = str(fetch.get("method") or "").strip()
    url = str(fetch.get("url") or "").strip()
    eligible = item_type == "article" or (item_type == "report" and method == "pdf-url")
    if not eligible or method not in {"pmc-oa", "pdf-url", "arxiv-pdf"} or not url:
        return "capture-source", payload
    work_id = str(payload.get("work_id") or "").strip()
    return (
        "capture-remote-pdf-source",
        {
            "fetch": {"method": method, "url": url},
            "capture": {
                "work_id": work_id,
                "title": str(payload.get("title") or work_id),
                "description": str(payload.get("description") or ""),
                "resource": resource or url,
                "item_type": item_type,
                "identifiers": payload.get("identifiers"),
                "csl_json": payload.get("csl_json"),
                "citekey": str(payload.get("citekey") or ""),
                "provider_coverage": str(payload.get("provider_coverage") or "partial"),
            },
        },
    )


def detect_identifier_collisions(
    vault: Path, work_id: str, identifiers: dict[str, Any]
) -> list[dict[str, str]]:
    """Return exact arXiv/PMCID matches in other catalog rows.

    The admitted work ID is already normalized by the capture seam, so the
    self-match exclusion is direct equality. This deliberately scans the full
    catalog at beta.1's 100-work ceiling; DOI remains owned by structural
    dedupe and its UNIQUE constraint, not a triage signal.
    """
    wanted = {
        field: str(identifiers.get(field) or "").strip() for field in _DUPLICATE_IDENTIFIER_FIELDS
    }
    if not any(wanted.values()):
        return []
    collisions: list[dict[str, str]] = []
    for row in state.catalog_sources(vault, checked_only=False):
        if row["work_id"] == work_id:
            continue
        other = row["identifiers"] if isinstance(row["identifiers"], dict) else {}
        for field, value in wanted.items():
            if value and value == str(other.get(field) or "").strip():
                collisions.append({"other_work_id": row["work_id"], "field": field})
    return collisions


def is_doi_collision_error(error: str) -> bool:
    """Whether a worker failure is the catalog DOI-UNIQUE edge."""
    return "catalog_sources.doi" in str(error)


def entry_item_type(entry_fields: dict[str, Any]) -> str:
    """Normalize a BibTeX or CSL entry onto the shipped item-type vocabulary."""
    return _resolve_item_type(entry_fields)[0]


def entry_type_mapped(entry_fields: dict[str, Any]) -> bool:
    """Whether ``entry_item_type`` was explicit or determined by an approved heuristic."""
    return _resolve_item_type(entry_fields)[1]


def _resolve_item_type(entry_fields: dict[str, Any]) -> tuple[str, bool]:
    raw_type = str(entry_fields.get("type") or "").strip().lower()
    if raw_type in _ENTRY_TYPE_MAP:
        return _ENTRY_TYPE_MAP[raw_type], True
    if raw_type == "misc":
        url = _entry_url(entry_fields)
        if _is_repo_host(url):
            return "software", True
        if _doi_prefix(entry_fields) in _DATASET_DOI_PREFIXES:
            return "dataset", True
        if url:
            return "webpage", True
    return "article", False


def _entry_url(entry_fields: dict[str, Any]) -> str:
    return str(entry_fields.get("url") or entry_fields.get("URL") or "").strip()


def _doi_prefix(entry_fields: dict[str, Any]) -> str:
    doi = str(entry_fields.get("doi") or entry_fields.get("DOI") or "").strip()
    return doi.partition("/")[0]


def _is_repo_host(url: str) -> bool:
    parsed = urlparse(url)
    if not parsed.hostname and not parsed.scheme and not url.startswith("//"):
        parsed = urlparse(f"//{url}")
    host = (parsed.hostname or "").lower()
    return any(host == repo or host.endswith(f".{repo}") for repo in _REPO_HOSTS)
