"""Source capture and catalog staging helpers."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen

from memoria_vault.runtime import state
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.trusted_writer import (
    append_journal_event,
    commit_writer_changes,
)
from memoria_vault.runtime.vaultio import write_bytes_durable, write_text_durable

WORK_ASPECT_ORDER = ("context", "key_idea", "method", "outcome", "limitation", "assumption")
_ASPECT_HEADING_ALIASES = {
    "assumption": "assumption",
    "assumptions": "assumption",
    "background": "context",
    "context": "context",
    "key_idea": "key_idea",
    "key_ideas": "key_idea",
    "limitation": "limitation",
    "limitations": "limitation",
    "method": "method",
    "methods": "method",
    "outcome": "outcome",
    "outcomes": "outcome",
    "result": "outcome",
    "results": "outcome",
}


def source_requires_enrichment(
    *,
    identifiers: dict[str, Any] | None = None,
    csl_json: dict[str, Any] | None = None,
) -> bool:
    identifiers = identifiers if isinstance(identifiers, dict) else {}
    csl_json = csl_json if isinstance(csl_json, dict) else {}
    return bool(
        str(identifiers.get("doi") or identifiers.get("isbn") or "").strip()
        or str(csl_json.get("DOI") or csl_json.get("ISBN") or "").strip()
    )


def _normalize_text_status(value: str) -> str:
    status = str(value or "full-text").strip().lower()
    if status not in {"full-text", "abstract-only", "metadata-only"}:
        raise ValueError("text_status must be full-text, abstract-only, or metadata-only")
    return status


def _normalize_check_status(value: str) -> str:
    status = str(value or "unchecked").strip().lower()
    if status not in {"unchecked", "checked", "quarantined"}:
        raise ValueError("check_status must be unchecked, checked, or quarantined")
    return status


def _fallback_text_status(content_text: str | None, abstract: str | None) -> str:
    if content_text and content_text.strip():
        return "full-text"
    if abstract and abstract.strip():
        return "abstract-only"
    return "metadata-only"


def stage_catalog_source(
    vault: Path,
    source_id: str,
    title: str,
    description: str,
    content_text: str,
    *,
    raw_bytes: bytes | None = None,
    raw_filename: str = "source.txt",
    resource: str = "",
    item_type: str = "article",
    identifiers: dict[str, Any] | None = None,
    csl_json: dict[str, Any] | None = None,
    provider_coverage: str = "partial",
    text_status: str = "full-text",
    citekey: str = "",
    machine: str | None = None,
    run_id: str | None = None,
    workflow: str = "capture_source",
    check_status: str = "unchecked",
) -> dict[str, Any]:
    """Stage a source as a DB catalog row plus immutable blob payloads."""
    vault = Path(vault)
    source_id = _source_id(source_id)
    if not title.strip() or not description.strip():
        raise ValueError("title and description are required")
    if not content_text.strip():
        raise ValueError("content_text is required")
    text_status = _normalize_text_status(text_status)
    check_status = _normalize_check_status(check_status)
    existing = state.catalog_source(vault, source_id)
    if existing:
        identifiers = _merge_mapping(existing.get("identifiers"), identifiers)
        csl_json = _merge_mapping(existing.get("csl_json"), csl_json)
        provider_coverage = _best_provider_coverage(
            str(existing.get("provider_coverage") or ""),
            provider_coverage,
        )
        resource = resource or str(existing.get("resource") or "")
        citekey = citekey or str(existing.get("citekey") or "")
    run_id = run_id or f"capture:{source_id}"

    started = append_journal_event(
        vault,
        {"event": "run", "run_id": run_id, "workflow": workflow, "status": "started"},
        machine=machine,
    )
    root = vault / ".memoria/blobs/source-content" / source_id
    raw_path = root / "raw" / safe_filename(raw_filename or "source.txt")
    content_path = root / "content.txt"
    raw_sha = _write_immutable(
        raw_path, raw_bytes if raw_bytes is not None else content_text.encode()
    )
    content_sha = _write_immutable(content_path, content_text.strip().encode() + b"\n")
    raw_rel = raw_path.relative_to(vault).as_posix()
    content_rel = content_path.relative_to(vault).as_posix()
    state.upsert_catalog_record(
        vault,
        source_id=source_id,
        title=title,
        description=description,
        concept_path=f"catalog/sources/{source_id}",
        doi=str((identifiers or {}).get("doi") or (csl_json or {}).get("DOI") or "") or None,
        resource=resource,
        identifiers=identifiers,
        citekey=citekey,
        csl_json=csl_json,
        provider_coverage=provider_coverage,
        text_status=text_status,
        check_status=check_status,
        content_hash=content_sha,
        raw_hash=raw_sha,
        content_path=content_rel,
        raw_path=raw_rel,
    )
    state.replace_work_aspects(
        vault,
        source_id,
        derive_work_aspect_rows(csl_json, content_text, check_status=check_status),
    )
    if _has_reference_metadata(csl_json):
        _replace_import_reference_edges(vault, source_id, _reference_edges(csl_json))
    finished = append_journal_event(
        vault,
        {
            "event": "run",
            "run_id": run_id,
            "workflow": workflow,
            "status": "done",
            "source_id": source_id,
            "outputs": [content_rel, raw_rel],
            "raw": raw_rel,
        },
        machine=machine,
    )
    commit = commit_writer_changes(vault, f"stage source {source_id}", [], machine=machine)
    return {
        "run_id": run_id,
        "source_id": source_id,
        "source_path": f"catalog/sources/{source_id}",
        "content_path": content_rel,
        "raw_path": raw_rel,
        "raw_sha256": raw_sha,
        "content_sha256": content_sha,
        "text_status": text_status,
        "check_status": check_status,
        "started": started,
        "finished": finished,
        "commit": commit,
    }


def capture_source(
    vault: Path,
    source_id: str,
    title: str,
    description: str,
    content_text: str,
    *,
    raw_bytes: bytes | None = None,
    raw_filename: str = "source.txt",
    resource: str = "",
    item_type: str = "article",
    identifiers: dict[str, Any] | None = None,
    csl_json: dict[str, Any] | None = None,
    provider_coverage: str = "partial",
    text_status: str = "full-text",
    citekey: str = "",
    machine: str | None = None,
    run_id: str | None = None,
    workflow: str = "capture_source",
) -> dict[str, Any]:
    """Capture one source as a checked SQLite catalog row plus blob payloads."""
    return stage_catalog_source(
        vault,
        source_id,
        title,
        description,
        content_text,
        raw_bytes=raw_bytes,
        raw_filename=raw_filename,
        resource=resource,
        item_type=item_type,
        identifiers=identifiers,
        csl_json=csl_json,
        provider_coverage=provider_coverage,
        text_status=text_status,
        citekey=citekey,
        machine=machine,
        run_id=run_id,
        workflow=workflow,
        check_status="checked",
    )


def derive_work_aspect_rows(
    csl_json: dict[str, Any] | None,
    content_text: str,
    *,
    check_status: str = "unchecked",
) -> list[dict[str, str]]:
    csl_json = csl_json if isinstance(csl_json, dict) else {}
    rows: dict[str, dict[str, str]] = {}
    for aspect_type, aspect_text in _structured_aspects(csl_json).items():
        rows[aspect_type] = _aspect_row(aspect_type, aspect_text, check_status)
    for aspect_type, aspect_text in _markdown_aspects(content_text).items():
        rows.setdefault(aspect_type, _aspect_row(aspect_type, aspect_text, check_status))
    return [rows[aspect_type] for aspect_type in WORK_ASPECT_ORDER if aspect_type in rows]


def _structured_aspects(csl_json: dict[str, Any]) -> dict[str, str]:
    memoria = csl_json.get("memoria") if isinstance(csl_json.get("memoria"), dict) else {}
    raw = memoria.get("aspects") or memoria.get("_aspects") or csl_json.get("_aspects") or {}
    if not isinstance(raw, dict):
        return {}
    out = {}
    for key, value in raw.items():
        aspect_type = _aspect_type(str(key))
        text = str(value or "").strip()
        if aspect_type and text:
            out[aspect_type] = text
    return out


def _markdown_aspects(content_text: str) -> dict[str, str]:
    out = {}
    current = ""
    lines: list[str] = []

    def flush() -> None:
        if current and lines:
            text = " ".join(line.strip() for line in lines if line.strip())
            if text:
                out.setdefault(current, re.sub(r"\s+", " ", text).strip())

    for line in content_text.splitlines():
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", line)
        if match:
            flush()
            current = _aspect_type(match.group(1))
            lines = []
            continue
        if current:
            lines.append(line)
    flush()
    return out


def _aspect_type(value: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
    return _ASPECT_HEADING_ALIASES.get(key, "")


def _aspect_row(aspect_type: str, aspect_text: str, check_status: str) -> dict[str, str]:
    text = re.sub(r"\s+", " ", aspect_text).strip()
    return {
        "aspect_type": aspect_type,
        "aspect_text": text,
        "anchor_text": text[:200],
        "check_status": check_status,
        "source_provider": "deterministic",
    }


def capture_bibtex_source(
    vault: Path,
    bibtex: str,
    *,
    content_text: str | None = None,
    source_id: str | None = None,
    description: str | None = None,
    machine: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Capture one source from a local BibTeX entry."""
    entry = parse_bibtex_entry(bibtex)
    fields = entry["fields"]
    citekey = entry["citekey"]
    title = fields.get("title") or citekey
    doi = fields.get("doi", "")
    resource = fields.get("url") or (f"https://doi.org/{doi}" if doi else "")
    abstract = fields.get("abstract") or ""
    text = content_text or abstract or title
    identifiers = {
        key: value
        for key in ("doi", "isbn", "issn", "pmid", "pmcid", "arxiv")
        if (value := fields.get(key))
    }
    return capture_source(
        vault,
        source_id or _bibtex_default_source_id(fields, citekey),
        title,
        description or fields.get("abstract") or f"BibTeX {entry['entry_type']} source.",
        text,
        raw_bytes=bibtex.strip().encode() + b"\n",
        raw_filename=f"{safe_filename(citekey)}.bib",
        resource=resource,
        item_type=_item_type(entry["entry_type"]),
        identifiers=identifiers or None,
        csl_json=_csl_json(entry),
        provider_coverage="partial",
        text_status=_fallback_text_status(content_text, abstract),
        citekey=citekey,
        machine=machine,
        run_id=run_id or f"capture-bibtex:{citekey}",
        workflow="capture_bibtex_source",
    )


def bibtex_capture_payload(
    bibtex: str,
    *,
    content_text: str | None = None,
    source_id: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Build a capture-source payload from one BibTeX entry."""
    entry = parse_bibtex_entry(bibtex)
    fields = entry["fields"]
    citekey = entry["citekey"]
    title = fields.get("title") or citekey
    doi = fields.get("doi", "")
    resource = fields.get("url") or (f"https://doi.org/{doi}" if doi else "")
    abstract = fields.get("abstract") or ""
    identifiers = {
        key: value
        for key in ("doi", "isbn", "issn", "pmid", "pmcid", "arxiv")
        if (value := fields.get(key))
    }
    return {
        "source_id": source_id or _bibtex_default_source_id(fields, citekey),
        "title": title,
        "description": description or abstract or f"BibTeX {entry['entry_type']} source.",
        "content_text": content_text or abstract or title,
        "raw_text": bibtex.strip() + "\n",
        "raw_filename": f"{safe_filename(citekey)}.bib",
        "resource": resource,
        "item_type": _item_type(entry["entry_type"]),
        "identifiers": identifiers,
        "csl_json": _csl_json(entry),
        "provider_coverage": "partial",
        "text_status": _fallback_text_status(content_text, abstract),
        "citekey": citekey,
        "stage_only": True,
    }


def csl_capture_payload(
    csl_json: dict[str, Any],
    *,
    raw_text: str,
    content_text: str | None = None,
    source_id: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Build a capture-source payload from one CSL-JSON item."""
    title = str(csl_json.get("title") or csl_json.get("id") or "").strip()
    if not title:
        raise ValueError("CSL item requires title or id")
    doi = str(csl_json.get("DOI") or "").strip()
    isbn = str(csl_json.get("ISBN") or "").strip()
    url = str(csl_json.get("URL") or "").strip()
    abstract = str(csl_json.get("abstract") or "")
    identifiers = {key: value for key, value in {"doi": doi, "isbn": isbn}.items() if value}
    stable_id = source_id or str(csl_json.get("id") or doi or isbn or url or title)
    return {
        "source_id": stable_id,
        "title": title,
        "description": description or abstract or f"CSL {title} source.",
        "content_text": content_text or abstract or title,
        "raw_text": raw_text.strip() + "\n",
        "raw_filename": f"{safe_filename(stable_id)}.csl.json",
        "resource": url or (f"https://doi.org/{doi}" if doi else ""),
        "item_type": str(csl_json.get("type") or "article"),
        "identifiers": identifiers,
        "csl_json": csl_json,
        "provider_coverage": "partial",
        "text_status": _fallback_text_status(content_text, abstract),
        "citekey": str(csl_json.get("id") or ""),
        "stage_only": True,
    }


def capture_url_source(
    vault: Path,
    url: str,
    *,
    title: str | None = None,
    description: str | None = None,
    timeout: float = 10.0,
    machine: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Capture one URL snapshot with stdlib HTML text extraction."""
    resource = url.strip()
    if not resource:
        raise ValueError("url is required")
    raw_bytes = _read_url_bytes(resource, timeout)
    extracted_title, content_text = _html_text(raw_bytes)
    final_title = title or extracted_title or resource
    return capture_source(
        vault,
        _url_source_id(resource),
        final_title,
        description or f"URL snapshot captured from {resource}.",
        content_text,
        raw_bytes=raw_bytes,
        raw_filename=f"{safe_filename(_url_source_id(resource))}.html",
        resource=resource,
        item_type="webpage",
        csl_json={
            "id": _url_source_id(resource),
            "type": "webpage",
            "title": final_title,
            "URL": resource,
        },
        provider_coverage="partial",
        text_status="full-text",
        machine=machine,
        run_id=run_id or f"capture-url:{resource}",
        workflow="capture_url_source",
    )


def stage_url_source(
    vault: Path,
    url: str,
    *,
    title: str | None = None,
    description: str | None = None,
    timeout: float = 10.0,
    machine: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Stage one URL snapshot as an unchecked DB row plus text/blob payloads."""
    resource = url.strip()
    if not resource:
        raise ValueError("url is required")
    raw_bytes = _read_url_bytes(resource, timeout)
    extracted_title, content_text = _html_text(raw_bytes)
    final_title = title or extracted_title or resource
    source_id = _url_source_id(resource)
    return stage_catalog_source(
        vault,
        source_id,
        final_title,
        description or f"URL snapshot captured from {resource}.",
        content_text,
        raw_bytes=raw_bytes,
        raw_filename=f"{safe_filename(source_id)}.html",
        resource=resource,
        item_type="webpage",
        csl_json={
            "id": source_id,
            "type": "webpage",
            "title": final_title,
            "URL": resource,
        },
        provider_coverage="partial",
        text_status="full-text",
        machine=machine,
        run_id=run_id or f"capture-url:{resource}",
        workflow="capture_url_source",
    )


def capture_pdf_source(
    vault: Path,
    source_id: str,
    title: str,
    description: str,
    raw_bytes: bytes,
    *,
    raw_filename: str = "source.pdf",
    resource: str = "",
    item_type: str = "article",
    identifiers: dict[str, Any] | None = None,
    csl_json: dict[str, Any] | None = None,
    provider_coverage: str = "partial",
    citekey: str = "",
    machine: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Capture a PDF raw blob and extracted page text."""
    stable_source_id = _source_id(source_id)
    pdf_raw_filename = raw_filename or "source.pdf"
    pages = _extract_pdf_pages(raw_bytes)
    _validate_pdf_text_coherence(pages)
    content_text = _pdf_content_text(pages)
    return capture_source(
        vault,
        stable_source_id,
        title,
        description,
        content_text,
        raw_bytes=raw_bytes,
        raw_filename=pdf_raw_filename,
        resource=resource,
        item_type=item_type,
        identifiers=identifiers,
        csl_json=csl_json,
        provider_coverage=provider_coverage,
        text_status="full-text",
        citekey=citekey,
        machine=machine,
        run_id=run_id or f"capture-pdf:{_source_id(source_id)}",
        workflow="capture_pdf_source",
    )


def stage_pdf_source(
    vault: Path,
    source_id: str,
    title: str,
    description: str,
    raw_bytes: bytes,
    *,
    raw_filename: str = "source.pdf",
    resource: str = "",
    item_type: str = "article",
    identifiers: dict[str, Any] | None = None,
    csl_json: dict[str, Any] | None = None,
    provider_coverage: str = "partial",
    citekey: str = "",
    machine: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Stage a PDF raw blob and extracted text as an unchecked DB row."""
    stable_source_id = _source_id(source_id)
    pdf_raw_filename = raw_filename or "source.pdf"
    pages = _extract_pdf_pages(raw_bytes)
    _validate_pdf_text_coherence(pages)
    content_text = _pdf_content_text(pages)
    return stage_catalog_source(
        vault,
        stable_source_id,
        title,
        description,
        content_text,
        raw_bytes=raw_bytes,
        raw_filename=pdf_raw_filename,
        resource=resource,
        item_type=item_type,
        identifiers=identifiers,
        csl_json=csl_json,
        provider_coverage=provider_coverage,
        text_status="full-text",
        citekey=citekey,
        machine=machine,
        run_id=run_id or f"capture-pdf:{stable_source_id}",
        workflow="capture_pdf_source",
    )


def parse_bibtex_entry(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped.startswith("@"):
        raise ValueError("BibTeX entry must start with @")
    open_index = _first_container(stripped)
    entry_type = stripped[1:open_index].strip().lower()
    if not entry_type:
        raise ValueError("BibTeX entry type is required")
    close_index = _matching_container(stripped, open_index)
    body = stripped[open_index + 1 : close_index]
    citekey, fields = _split_citekey(body)
    return {
        "entry_type": entry_type,
        "citekey": citekey,
        "fields": _parse_bibtex_fields(fields),
    }


def parse_bibtex_entries(text: str) -> Iterator[dict[str, Any]]:
    index = 0
    while True:
        start = text.find("@", index)
        if start == -1:
            return
        open_index = _first_container(text[start:]) + start
        close_index = _matching_container(text, open_index)
        yield parse_bibtex_entry(text[start : close_index + 1])
        index = close_index + 1


def render_references_bib(vault: Path) -> str:
    """Render checked SQLite catalog Works as the generated references.bib projection."""
    entries = []
    sources = state.catalog_sources(vault)
    for frontmatter in sources:
        csl_json = (
            frontmatter.get("csl_json") if isinstance(frontmatter.get("csl_json"), dict) else {}
        )
        if frontmatter.get("citekey") or csl_json.get("id"):
            entries.append(_render_source_bibtex(frontmatter))
    return ("\n\n".join(entries) + "\n") if entries else ""


def write_references_bib(
    vault: Path,
    *,
    output_path: str = "references.bib",
    commit: bool = False,
    machine: str | None = None,
) -> dict[str, Any]:
    """Write the generated references.bib projection."""
    vault = Path(vault)
    output = vault / output_path
    text = render_references_bib(vault)
    old = output.read_text(encoding="utf-8") if output.exists() else None
    changed = old != text
    if changed:
        write_text_durable(output, text, create_parent=True)
    event = None
    commit_id = ""
    if commit:
        event = append_journal_event(
            vault,
            {
                "event": "run",
                "run_id": "projection:references.bib",
                "workflow": "generate_references_bib",
                "status": "done",
                "outputs": [output_path],
            },
            machine=machine,
        )
        commit_id = commit_writer_changes(
            vault,
            "regenerate references.bib",
            [output_path],
            machine=machine,
        )
    return {"path": output_path, "changed": changed, "event": event, "commit": commit_id}


def check_references_bib(vault: Path, *, output_path: str = "references.bib") -> bool:
    path = Path(vault) / output_path
    return path.is_file() and path.read_text(encoding="utf-8") == render_references_bib(vault)


def _has_bibliography_fields(frontmatter: dict[str, Any]) -> bool:
    return bool(
        str(frontmatter.get("citekey") or "").strip()
        or frontmatter.get("csl_json")
        or frontmatter.get("identifiers")
    )


def _source_id(value: str) -> str:
    source_id = safe_filename(value).strip("._-")
    if not source_id:
        raise ValueError("source_id is required")
    return source_id


def _bibtex_default_source_id(fields: dict[str, str], citekey: str) -> str:
    doi = fields.get("doi", "").strip().lower()
    if doi:
        return f"doi-{doi}"
    if url := fields.get("url", "").strip():
        return _url_source_id(url)
    return citekey


def _write_immutable(path: Path, data: bytes) -> str:
    if path.exists() and path.read_bytes() != data:
        raise FileExistsError(path)
    if not path.exists():
        write_bytes_durable(path, data, create_parent=True)
    return sha256_file(path)


def _merge_mapping(old: Any, new: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for source in (old, new):
        if not isinstance(source, dict):
            continue
        merged.update({str(key): value for key, value in source.items() if value not in ("", None)})
    return merged


def _best_provider_coverage(old: str, new: str) -> str:
    rank = {"": 0, "partial": 1, "degraded": 2, "full": 3}
    return new if rank.get(new, 0) >= rank.get(old, 0) else old


def _extract_pdf_pages(raw_bytes: bytes) -> list[dict[str, Any]]:
    try:
        import fitz
    except ImportError as exc:  # pragma: no cover - CI does not install the optional PDF parser.
        raise RuntimeError("PDF capture requires PyMuPDF from the vault MCP requirements") from exc

    pages = []
    with fitz.open(stream=raw_bytes, filetype="pdf") as doc:
        for page_number, page in enumerate(doc, start=1):
            text = "\n".join(
                line
                for line in (" ".join(row.split()) for row in page.get_text("text").splitlines())
                if line
            )
            pages.append(
                {
                    "page": page_number,
                    "text": text,
                }
            )
    if not any(page["text"].strip() for page in pages):
        raise ValueError("PDF parser produced no text")
    return pages


def _pdf_content_text(pages: list[dict[str, Any]]) -> str:
    rows = []
    for page in pages:
        text = str(page.get("text") or "").strip()
        if text:
            rows.append(f"## Page {page['page']}\n\n{text}")
    if not rows:
        raise ValueError("PDF parser produced no text")
    return "\n\n".join(rows)


def _validate_pdf_text_coherence(pages: list[dict[str, Any]]) -> None:
    text = "\n".join(str(page.get("text") or "") for page in pages)
    visible = [char for char in text if not char.isspace()]
    if not visible:
        raise ValueError("PDF parser produced no text")
    replacement_ratio = text.count("\ufffd") / len(visible)
    alnum_ratio = sum(1 for char in visible if char.isalnum()) / len(visible)
    if replacement_ratio > 0.02:
        raise ValueError("PDF parser output failed coherence check: replacement characters")
    if alnum_ratio < 0.3:
        raise ValueError("PDF parser output failed coherence check: low word content")


def _first_container(text: str) -> int:
    positions = [index for token in "{(" if (index := text.find(token)) != -1]
    if not positions:
        raise ValueError("BibTeX entry must use { ... } or ( ... )")
    return min(positions)


def _matching_container(text: str, open_index: int) -> int:
    opener = text[open_index]
    closer = "}" if opener == "{" else ")"
    depth = 0
    for index, char in enumerate(text[open_index:], start=open_index):
        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("BibTeX entry has an unclosed container")


def _split_citekey(body: str) -> tuple[str, str]:
    split_at = _top_level_comma(body)
    if split_at == -1:
        raise ValueError("BibTeX entry must include fields")
    citekey = body[:split_at].strip()
    if not citekey:
        raise ValueError("BibTeX citekey is required")
    return citekey, body[split_at + 1 :]


def _top_level_comma(text: str) -> int:
    depth = 0
    quote = False
    for index, char in enumerate(text):
        if char == '"' and (index == 0 or text[index - 1] != "\\"):
            quote = not quote
        elif not quote and char in "{(":
            depth += 1
        elif not quote and char in "})":
            depth -= 1
        elif char == "," and depth == 0 and not quote:
            return index
    return -1


def _parse_bibtex_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    index = 0
    while index < len(text):
        while index < len(text) and text[index] in " \t\r\n,":
            index += 1
        name_start = index
        while index < len(text) and (text[index].isalnum() or text[index] in "_-"):
            index += 1
        name = text[name_start:index].strip().lower()
        if not name:
            break
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text) or text[index] != "=":
            raise ValueError(f"BibTeX field {name!r} is missing =")
        index += 1
        while index < len(text) and text[index].isspace():
            index += 1
        value, index = _read_bibtex_value(text, index)
        fields[name] = _clean_bibtex_value(value)
    return fields


def _read_bibtex_value(text: str, index: int) -> tuple[str, int]:
    if index >= len(text):
        return "", index
    if text[index] in "{(":
        close = _matching_container(text, index)
        return text[index + 1 : close], close + 1
    if text[index] == '"':
        end = index + 1
        while end < len(text):
            if text[end] == '"' and text[end - 1] != "\\":
                return text[index + 1 : end], end + 1
            end += 1
        raise ValueError("BibTeX quoted value is unclosed")
    end = index
    while end < len(text) and text[end] != ",":
        end += 1
    return text[index:end], end


def _clean_bibtex_value(value: str) -> str:
    cleaned = value.replace("\n", " ").replace("\r", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = cleaned.replace("\\&", "&").replace("\\_", "_")
    return cleaned.replace("{", "").replace("}", "")


def _item_type(entry_type: str) -> str:
    if entry_type in {"book", "inbook", "booklet"}:
        return "book"
    if entry_type in {"online", "webpage", "www"}:
        return "webpage"
    if entry_type in {"dataset", "data"}:
        return "dataset"
    if entry_type in {"software", "manual"}:
        return "software"
    if entry_type in {"techreport", "report", "phdthesis", "mastersthesis"}:
        return "report"
    return "article"


def _csl_json(entry: dict[str, Any]) -> dict[str, Any]:
    fields = entry["fields"]
    csl: dict[str, Any] = {
        "id": entry["citekey"],
        "type": _csl_type(entry["entry_type"]),
        "title": fields.get("title", entry["citekey"]),
    }
    if author := fields.get("author"):
        csl["author"] = [_csl_author(name) for name in re.split(r"\s+and\s+", author)]
    if year := fields.get("year"):
        csl["issued"] = {"date-parts": [[int(year)]]} if year.isdigit() else {"raw": year}
    if container := fields.get("journal") or fields.get("booktitle"):
        csl["container-title"] = container
    if doi := fields.get("doi"):
        csl["DOI"] = doi
    if url := fields.get("url"):
        csl["URL"] = url
    if abstract := fields.get("abstract"):
        csl["abstract"] = abstract
    if references := fields.get("references") or fields.get("reference"):
        csl["references"] = references
    return csl


def _has_reference_metadata(csl_json: dict[str, Any] | None) -> bool:
    return isinstance(csl_json, dict) and ("references" in csl_json or "reference" in csl_json)


def _replace_import_reference_edges(
    vault: Path, source_id: str, import_edges: list[dict[str, Any]]
) -> None:
    with state.connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT relation_type, target_id, target_title, target_doi, source_provider, raw_json
            FROM work_graph_edges
            WHERE work_id = ?
              AND source_provider != 'import'
            ORDER BY relation_type, target_id
            """,
            (source_id,),
        ).fetchall()
    preserved = []
    for row in rows:
        edge = dict(row)
        try:
            raw = json.loads(str(edge.get("raw_json") or "{}"))
        except json.JSONDecodeError:
            raw = {}
        edge["raw"] = raw if isinstance(raw, dict) else {}
        preserved.append(edge)
    preserved_keys = {(edge["relation_type"], edge["target_id"]) for edge in preserved}
    new_edges = [
        edge
        for edge in import_edges
        if (edge["relation_type"], edge["target_id"]) not in preserved_keys
    ]
    state.replace_work_graph_edges(vault, source_id, [*preserved, *new_edges])


def _reference_edges(csl_json: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(csl_json, dict):
        return []
    refs = csl_json.get("references", csl_json.get("reference", []))
    if isinstance(refs, str):
        items: list[Any] = [part for part in re.split(r"[\n;]+", refs) if part.strip()]
    elif isinstance(refs, list):
        items = refs
    else:
        items = []
    edges = {}
    for item in items:
        edge = _reference_edge(item)
        if edge:
            edges[(edge["relation_type"], edge["target_id"])] = edge
    return [edges[key] for key in sorted(edges)]


def _reference_edge(item: Any) -> dict[str, Any] | None:
    raw = item if isinstance(item, dict) else {"value": str(item)}
    doi = _reference_doi(raw)
    target = f"doi:{doi.casefold()}" if doi else _reference_target(raw)
    if not target:
        return None
    title = _reference_title(raw) or target
    return {
        "relation_type": "references",
        "target_id": target,
        "target_title": title,
        "target_doi": doi,
        "source_provider": "import",
        "raw": raw,
    }


def _reference_doi(raw: dict[str, Any]) -> str:
    for key in ("DOI", "doi"):
        if doi := str(raw.get(key) or "").strip():
            return doi
    value = str(raw.get("value") or "")
    match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", value, flags=re.IGNORECASE)
    return match.group(0).rstrip(".,;") if match else ""


def _reference_target(raw: dict[str, Any]) -> str:
    for key in ("id", "ID", "URL", "url", "openalex"):
        if value := str(raw.get(key) or "").strip():
            return value
    value = str(raw.get("value") or "").strip()
    if value.startswith(("http://", "https://")):
        return value
    return ""


def _reference_title(raw: dict[str, Any]) -> str:
    for key in ("title", "article-title", "container-title", "unstructured", "value"):
        if value := str(raw.get(key) or "").strip():
            return value
    return ""


def _csl_type(entry_type: str) -> str:
    if entry_type in {"book", "inbook"}:
        return "book"
    if entry_type in {"inproceedings", "conference"}:
        return "paper-conference"
    if entry_type in {"online", "webpage", "www"}:
        return "webpage"
    if entry_type in {"dataset", "data"}:
        return "dataset"
    if entry_type in {"software", "manual"}:
        return "software"
    if entry_type in {"techreport", "report"}:
        return "report"
    return "article-journal"


def _csl_author(name: str) -> dict[str, str]:
    name = name.strip()
    if "," in name:
        family, given = [part.strip() for part in name.split(",", 1)]
        return {"family": family, "given": given}
    parts = name.split()
    if len(parts) > 1:
        return {"family": parts[-1], "given": " ".join(parts[:-1])}
    return {"literal": name}


def _read_url_bytes(url: str, timeout: float) -> bytes:
    with urlopen(url, timeout=timeout) as response:
        return response.read()


def _html_text(raw_bytes: bytes) -> tuple[str, str]:
    parser = _TextHTMLParser()
    parser.feed(raw_bytes.decode("utf-8", errors="replace"))
    text = "\n".join(part for part in parser.parts if part)
    if not text.strip():
        raise ValueError("URL capture produced no text")
    return parser.title.strip(), text


def _url_source_id(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc or "url"
    path = parsed.path.strip("/") or "index"
    return safe_filename(f"url-{host}-{path}".lower().replace("/", "-")).strip("._-")


class _TextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.title = ""
        self._skip = 0
        self._title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip += 1
        elif tag == "title":
            self._title = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip:
            self._skip -= 1
        elif tag == "title":
            self._title = False

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text or self._skip:
            return
        if self._title:
            self.title = f"{self.title} {text}".strip()
        else:
            self.parts.append(text)


def _render_source_bibtex(frontmatter: dict[str, Any]) -> str:
    csl = frontmatter.get("csl_json") if isinstance(frontmatter.get("csl_json"), dict) else {}
    citekey = str(frontmatter.get("citekey") or csl.get("id"))
    fields = {
        "title": str(csl.get("title") or frontmatter.get("title") or citekey),
        "author": _render_csl_authors(csl.get("author")),
        "year": _render_csl_year(csl.get("issued")),
        "journal": str(csl.get("container-title") or ""),
        "doi": str((frontmatter.get("identifiers") or {}).get("doi") or csl.get("DOI") or ""),
        "url": str(csl.get("URL") or frontmatter.get("resource") or ""),
        "abstract": str(csl.get("abstract") or ""),
    }
    rows = [(key, value) for key, value in fields.items() if value]
    rendered = [f"@{_bibtex_type(frontmatter, csl)}{{{citekey},"]
    rendered.extend(
        f"  {key} = {{{_bibtex_escape(value)}}}{',' if index < len(rows) - 1 else ''}"
        for index, (key, value) in enumerate(rows)
    )
    rendered.append("}")
    return "\n".join(rendered)


def _bibtex_type(frontmatter: dict[str, Any], csl: dict[str, Any]) -> str:
    csl_type = csl.get("type")
    item_type = frontmatter.get("item_type")
    if csl_type == "book" or item_type == "book":
        return "book"
    if csl_type == "paper-conference":
        return "inproceedings"
    if csl_type == "webpage" or item_type == "webpage":
        return "online"
    if csl_type == "dataset" or item_type == "dataset":
        return "dataset"
    if csl_type == "software" or item_type == "software":
        return "software"
    if csl_type == "report" or item_type == "report":
        return "techreport"
    return "article"


def _render_csl_authors(authors: Any) -> str:
    if not isinstance(authors, list):
        return ""
    rendered = []
    for author in authors:
        if not isinstance(author, dict):
            continue
        if author.get("literal"):
            rendered.append(str(author["literal"]))
        elif author.get("family") and author.get("given"):
            rendered.append(f"{author['family']}, {author['given']}")
        elif author.get("family"):
            rendered.append(str(author["family"]))
    return " and ".join(rendered)


def _render_csl_year(issued: Any) -> str:
    if not isinstance(issued, dict):
        return ""
    parts = issued.get("date-parts")
    if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0]:
        return str(parts[0][0])
    return str(issued.get("raw") or "")


def _bibtex_escape(value: str) -> str:
    return " ".join(value.replace("{", "").replace("}", "").split())
