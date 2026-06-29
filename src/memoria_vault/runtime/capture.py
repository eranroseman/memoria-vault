"""Minimal alpha.11 source capture pipeline."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse
from urllib.request import urlopen

from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.trusted_writer import (
    append_journal_event,
    commit_writer_changes,
    normalize_promotion_checks,
    promote_checked,
    stage_concept,
)
from memoria_vault.runtime.vaultio import read_frontmatter


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
    metadata_status: str = "partial",
    citekey: str = "",
    machine: str | None = None,
    run_id: str | None = None,
    workflow: str = "capture_source",
    required_checks: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Capture one source into catalog files through the trusted writer."""
    vault = Path(vault)
    promotion_checks = normalize_promotion_checks(required_checks)
    source_id = _source_id(source_id)
    if not title.strip() or not description.strip():
        raise ValueError("title and description are required")
    if not content_text.strip():
        raise ValueError("content_text is required")
    run_id = run_id or f"capture:{source_id}"

    started = append_journal_event(
        vault,
        {
            "event": "run",
            "run_id": run_id,
            "workflow": workflow,
            "status": "started",
        },
        machine=machine,
    )

    root = vault / "catalog" / "sources" / source_id
    raw_path = root / "raw" / safe_filename(raw_filename or "source.txt")
    content_path = root / "content.md"
    raw_sha = _write_immutable(
        raw_path, raw_bytes if raw_bytes is not None else content_text.encode()
    )
    content_sha = _write_immutable(content_path, content_text.strip().encode() + b"\n")
    raw_rel = raw_path.relative_to(vault).as_posix()
    content_rel = content_path.relative_to(vault).as_posix()
    source_rel = f"catalog/sources/{source_id}/source.md"
    inputs = [
        {"id": raw_rel, "sha256": raw_sha},
        {"id": content_rel, "sha256": content_sha},
    ]
    frontmatter: dict[str, Any] = {
        "type": "source",
        "check_status": "unchecked",
        "title": title,
        "description": description,
        "source_id": source_id,
        "item_type": item_type,
        "raw_copy_path": raw_rel,
        "content_path": content_rel,
        "raw_text_sha256": raw_sha,
        "normalized_text_sha256": content_sha,
        "metadata_status": metadata_status,
    }
    if resource:
        frontmatter["resource"] = resource
    if citekey:
        frontmatter["citekey"] = citekey
    if identifiers:
        frontmatter["identifiers"] = identifiers
    if csl_json:
        frontmatter["csl_json"] = csl_json
    frontmatter = _source_frontmatter(vault, source_rel, frontmatter)
    entity_specs = _source_entity_specs(vault, frontmatter.get("csl_json") or {}, source_rel)
    if entity_links := _source_entity_links(entity_specs):
        frontmatter["links"] = entity_links
    frontmatter = _source_frontmatter(vault, source_rel, frontmatter)

    entity_stages = [
        stage_concept(
            vault,
            spec["path"],
            _entity_text(spec["frontmatter"], spec["title"], source_rel),
            inputs=inputs,
            operation=workflow,
            run_id=run_id,
            machine=machine,
        )
        for spec in entity_specs
    ]

    stage = stage_concept(
        vault,
        source_rel,
        _concept_text(frontmatter, title, content_rel),
        inputs=inputs,
        operation=workflow,
        run_id=run_id,
        machine=machine,
    )
    entity_checks = [
        promote_checked(vault, spec["path"], checks=promotion_checks, machine=machine)
        for spec in entity_specs
    ]
    check = promote_checked(vault, source_rel, checks=promotion_checks, machine=machine)
    finished = append_journal_event(
        vault,
        {
            "event": "run",
            "run_id": run_id,
            "workflow": workflow,
            "status": "done",
            "outputs": [source_rel, content_rel, *(spec["path"] for spec in entity_specs)],
            "raw": raw_rel,
        },
        machine=machine,
    )
    commit = commit_writer_changes(
        vault,
        f"capture source {source_id}",
        [source_rel, content_rel, *(spec["path"] for spec in entity_specs)],
        machine=machine,
    )
    return {
        "run_id": run_id,
        "source_path": source_rel,
        "content_path": content_rel,
        "raw_path": raw_rel,
        "raw_sha256": raw_sha,
        "content_sha256": content_sha,
        "started": started,
        "derived": stage,
        "entity_derived": entity_stages,
        "entity_checked": entity_checks,
        "entity_paths": [spec["path"] for spec in entity_specs],
        "checked": check,
        "finished": finished,
        "commit": commit,
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
    required_checks: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Capture one source from a local BibTeX entry."""
    entry = parse_bibtex_entry(bibtex)
    fields = entry["fields"]
    citekey = entry["citekey"]
    title = fields.get("title") or citekey
    doi = fields.get("doi", "")
    resource = fields.get("url") or (f"https://doi.org/{doi}" if doi else "")
    text = content_text or fields.get("abstract") or title
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
        metadata_status="partial",
        citekey=citekey,
        machine=machine,
        run_id=run_id or f"capture-bibtex:{citekey}",
        workflow="capture_bibtex_source",
        required_checks=required_checks,
    )


def capture_zotero_source(
    vault: Path,
    item: dict[str, Any],
    *,
    content_text: str | None = None,
    source_id: str | None = None,
    description: str | None = None,
    raw_filename: str | None = None,
    machine: str | None = None,
    run_id: str | None = None,
    required_checks: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Capture one Zotero Local API item snapshot."""
    data = item.get("data")
    if not isinstance(data, dict):
        raise ValueError("Zotero item must include a data object")
    key = str(item.get("key") or data.get("key") or "").strip()
    if not key:
        raise ValueError("Zotero item key is required")

    title = str(data.get("title") or key).strip()
    item_type = _zotero_item_type(str(data.get("itemType") or ""))
    abstract = str(data.get("abstractNote") or "").strip()
    citekey = _zotero_citekey(data)
    stable_id = source_id or f"zotero-{key.lower()}"
    raw_text = json.dumps(item, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    identifiers = _zotero_identifiers(data)
    csl_json = _zotero_csl_json(key, data)
    return capture_source(
        vault,
        stable_id,
        title,
        description or abstract or f"Zotero {data.get('itemType') or 'item'} source.",
        content_text or abstract or title,
        raw_bytes=raw_text.encode(),
        raw_filename=raw_filename or f"{safe_filename(stable_id)}.zotero.json",
        resource=_zotero_resource(item, data, identifiers),
        item_type=item_type,
        identifiers=identifiers or None,
        csl_json=csl_json,
        metadata_status="partial",
        citekey=citekey,
        machine=machine,
        run_id=run_id or f"capture-zotero:{key}",
        workflow="capture_zotero_source",
        required_checks=required_checks,
    )


def capture_zotero_local_source(
    vault: Path,
    item_key: str,
    *,
    local_api_base: str = "http://localhost:23119/api/users/0",
    timeout: float = 5.0,
    content_text: str | None = None,
    source_id: str | None = None,
    description: str | None = None,
    raw_filename: str | None = None,
    machine: str | None = None,
    run_id: str | None = None,
    required_checks: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Fetch one Zotero Local API item by key, then capture its JSON snapshot."""
    key = item_key.strip()
    if not key:
        raise ValueError("Zotero item key is required")
    item = _zotero_local_item(key, local_api_base=local_api_base, timeout=timeout)
    return capture_zotero_source(
        vault,
        item,
        content_text=content_text,
        source_id=source_id,
        description=description,
        raw_filename=raw_filename,
        machine=machine,
        run_id=run_id,
        required_checks=required_checks,
    )


def capture_url_source(
    vault: Path,
    url: str,
    *,
    title: str | None = None,
    description: str | None = None,
    timeout: float = 10.0,
    machine: str | None = None,
    run_id: str | None = None,
    required_checks: Iterable[str] | None = None,
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
        metadata_status="partial",
        machine=machine,
        run_id=run_id or f"capture-url:{resource}",
        workflow="capture_url_source",
        required_checks=required_checks,
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
    metadata_status: str = "partial",
    citekey: str = "",
    machine: str | None = None,
    run_id: str | None = None,
    required_checks: Iterable[str] | None = None,
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
        metadata_status=metadata_status,
        citekey=citekey,
        machine=machine,
        run_id=run_id or f"capture-pdf:{_source_id(source_id)}",
        workflow="capture_pdf_source",
        required_checks=required_checks,
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


def render_references_bib(vault: Path) -> str:
    """Render checked source Concepts as the generated references.bib projection."""
    entries = []
    for path in sorted((Path(vault) / "catalog" / "sources").glob("*/source.md")):
        frontmatter = read_frontmatter(path)
        if frontmatter.get("type") != "source" or frontmatter.get("check_status") != "checked":
            continue
        if not frontmatter.get("citekey"):
            continue
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
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
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
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(data)
    return sha256_file(path)


def _concept_text(frontmatter: dict[str, Any], title: str, content_rel: str) -> str:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - packaged deployments install PyYAML.
        raise RuntimeError("capture requires PyYAML to write source frontmatter") from exc

    rendered = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{rendered}\n---\n# {title}\n\nContent: `{content_rel}`\n"


def _source_frontmatter(vault: Path, source_rel: str, incoming: dict[str, Any]) -> dict[str, Any]:
    source_path = vault / source_rel
    if not source_path.is_file():
        return incoming
    existing = dict(read_frontmatter(source_path))
    if existing.get("type") != "source":
        raise ValueError(f"{source_rel} already exists as {existing.get('type')}, not source")
    if str(existing.get("source_id") or "") != str(incoming.get("source_id") or ""):
        raise ValueError(f"{source_rel} source_id does not match recapture")

    merged = {**existing, **incoming}
    merged["check_status"] = "unchecked"
    merged["metadata_status"] = _best_metadata_status(
        str(existing.get("metadata_status") or ""),
        str(incoming.get("metadata_status") or ""),
    )
    if identifiers := _merge_mapping(existing.get("identifiers"), incoming.get("identifiers")):
        merged["identifiers"] = identifiers
    if csl_json := _merge_mapping(existing.get("csl_json"), incoming.get("csl_json")):
        merged["csl_json"] = csl_json
    if links := _merge_link_mapping(existing.get("links"), incoming.get("links")):
        merged["links"] = links
    return merged


def _merge_mapping(old: Any, new: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for source in (old, new):
        if not isinstance(source, dict):
            continue
        merged.update({str(key): value for key, value in source.items() if value not in ("", None)})
    return merged


def _merge_link_mapping(old: Any, new: Any) -> dict[str, list[str]]:
    merged: dict[str, list[str]] = {}
    for source in (old, new):
        if not isinstance(source, dict):
            continue
        for key, values in source.items():
            if not isinstance(values, list):
                continue
            target = merged.setdefault(str(key), [])
            for value in values:
                if isinstance(value, str) and value not in target:
                    target.append(value)
    return merged


def _best_metadata_status(old: str, new: str) -> str:
    rank = {"": 0, "not-indexed": 1, "unverified": 2, "partial": 3, "verified": 4}
    return new if rank.get(new, 0) >= rank.get(old, 0) else old


def _entity_text(frontmatter: dict[str, Any], title: str, source_rel: str) -> str:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - packaged deployments install PyYAML.
        raise RuntimeError("capture requires PyYAML to write entity frontmatter") from exc

    rendered = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()
    links = frontmatter.get("links") if isinstance(frontmatter.get("links"), dict) else {}
    sources = [source for source in links.get("sources", [source_rel]) if isinstance(source, str)]
    source_lines = "\n".join(f"- `{source}`" for source in sources)
    return f"---\n{rendered}\n---\n# {title}\n\nSources:\n{source_lines}\n"


def _source_entity_specs(
    vault: Path, csl_json: dict[str, Any], source_rel: str
) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    seen: set[str] = set()
    authors = csl_json.get("author")
    if isinstance(authors, list):
        for author in authors:
            if not isinstance(author, dict):
                continue
            if name := _csl_author_name(author):
                _add_entity_spec(
                    vault,
                    specs,
                    seen,
                    "person",
                    name,
                    source_rel,
                    external_ids=_csl_author_external_ids(author),
                )
    if venue := str(csl_json.get("container-title") or "").strip():
        _add_entity_spec(
            vault,
            specs,
            seen,
            "venue",
            venue,
            source_rel,
            external_ids=_csl_venue_external_ids(csl_json),
        )
    return specs


def _add_entity_spec(
    vault: Path,
    specs: list[dict[str, Any]],
    seen: set[str],
    kind: str,
    name: str,
    source_rel: str,
    external_ids: dict[str, Any] | None = None,
) -> None:
    slug = _entity_slug(name)
    path = f"catalog/entities/{kind}-{slug}.md"
    if path in seen:
        return
    seen.add(path)
    frontmatter = _entity_frontmatter(vault, path, kind, name, source_rel, external_ids or {})
    specs.append(
        {
            "path": path,
            "title": str(frontmatter.get("title") or name),
            "frontmatter": frontmatter,
        }
    )


def _entity_frontmatter(
    vault: Path,
    path: str,
    kind: str,
    name: str,
    source_rel: str,
    external_ids: dict[str, Any],
) -> dict[str, Any]:
    entity_path = vault / path
    if entity_path.is_file():
        frontmatter = dict(read_frontmatter(entity_path))
        if frontmatter.get("type") != kind:
            raise ValueError(f"{path} already exists as {frontmatter.get('type')}, not {kind}")
    else:
        frontmatter = {
            "type": kind,
            "title": name,
            "description": f"Catalog {kind} derived from source metadata.",
            "canonical_name": name,
        }
    frontmatter["check_status"] = "unchecked"
    _merge_entity_external_ids(frontmatter, external_ids)
    links = frontmatter.get("links") if isinstance(frontmatter.get("links"), dict) else {}
    sources = [source for source in links.get("sources", []) if isinstance(source, str)]
    if source_rel not in sources:
        sources.append(source_rel)
    frontmatter["links"] = {**links, "sources": sources}
    return frontmatter


def _merge_entity_external_ids(frontmatter: dict[str, Any], incoming: dict[str, Any]) -> None:
    incoming_ids = {
        str(key): str(value).strip() for key, value in incoming.items() if str(value).strip()
    }
    if not incoming_ids:
        return
    existing = (
        dict(frontmatter["external_ids"])
        if isinstance(frontmatter.get("external_ids"), dict)
        else {}
    )
    conflicts = []
    for key, value in incoming_ids.items():
        if key not in existing:
            existing[key] = value
            continue
        if str(existing[key]).strip() != value:
            conflicts.append(
                {
                    "field": key,
                    "existing": str(existing[key]).strip(),
                    "incoming": value,
                }
            )
    frontmatter["external_ids"] = existing
    if conflicts:
        metadata = (
            dict(frontmatter["metadata"]) if isinstance(frontmatter.get("metadata"), dict) else {}
        )
        prior = metadata.get("identity_conflicts")
        rows = [row for row in prior if isinstance(row, dict)] if isinstance(prior, list) else []
        for conflict in conflicts:
            if conflict not in rows:
                rows.append(conflict)
        metadata["identity_status"] = "ambiguous"
        metadata["identity_conflicts"] = rows
        frontmatter["metadata"] = metadata


def _source_entity_links(specs: list[dict[str, Any]]) -> dict[str, list[str]]:
    links: dict[str, list[str]] = {}
    authors = [spec["path"] for spec in specs if spec["frontmatter"]["type"] == "person"]
    venues = [spec["path"] for spec in specs if spec["frontmatter"]["type"] == "venue"]
    if authors:
        links["authors"] = authors
    if venues:
        links["venues"] = venues
    return links


def _csl_author_name(author: dict[str, Any]) -> str:
    if literal := str(author.get("literal") or "").strip():
        return literal
    family = str(author.get("family") or "").strip()
    given = str(author.get("given") or "").strip()
    if family and given:
        return f"{given} {family}"
    return family


def _csl_author_external_ids(author: dict[str, Any]) -> dict[str, str]:
    ids: dict[str, str] = {}
    for key in ("ORCID", "orcid"):
        value = str(author.get(key) or "").strip()
        if value:
            ids["orcid"] = _normalized_orcid(value)
            break
    return ids


def _csl_venue_external_ids(csl_json: dict[str, Any]) -> dict[str, str]:
    ids: dict[str, str] = {}
    for key in ("ISSN", "issn", "ISSN-L", "issn-l"):
        value = str(csl_json.get(key) or "").strip()
        if value:
            ids[key.casefold()] = value
    return ids


def _normalized_orcid(value: str) -> str:
    return re.sub(r"^https?://orcid\.org/", "", value.strip(), flags=re.IGNORECASE)


def _entity_slug(name: str) -> str:
    slug = safe_filename(re.sub(r"\s+", "-", name.casefold())).strip("._-")
    if not slug:
        raise ValueError("entity canonical_name is required")
    return slug


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
    return csl


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


def _zotero_citekey(data: dict[str, Any]) -> str:
    for key in ("citationKey", "citekey", "bibtexKey"):
        if value := str(data.get(key) or "").strip():
            return value
    extra = str(data.get("extra") or "")
    match = re.search(r"(?im)^\s*(?:citation key|citekey|bibtex)\s*:\s*(\S+)", extra)
    return match.group(1) if match else ""


def _zotero_local_item(
    item_key: str,
    *,
    local_api_base: str,
    timeout: float,
) -> dict[str, Any]:
    url = f"{local_api_base.rstrip('/')}/items/{quote(item_key, safe='')}"
    try:
        item = _read_zotero_json(url, timeout)
    except OSError as exc:
        raise RuntimeError(f"Zotero Local API fetch failed for item {item_key}") from exc
    if not isinstance(item, dict):
        raise ValueError("Zotero Local API item response must be an object")
    return item


def _read_zotero_json(url: str, timeout: float) -> Any:
    with urlopen(url, timeout=timeout) as response:
        return json.load(response)


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


def _zotero_identifiers(data: dict[str, Any]) -> dict[str, str]:
    fields = {
        "doi": "DOI",
        "isbn": "ISBN",
        "issn": "ISSN",
        "pmid": "PMID",
        "pmcid": "PMCID",
        "arxiv": "arXiv",
    }
    return {
        key: value for key, field in fields.items() if (value := str(data.get(field) or "").strip())
    }


def _zotero_resource(
    item: dict[str, Any], data: dict[str, Any], identifiers: dict[str, str]
) -> str:
    if url := str(data.get("url") or "").strip():
        return url
    if doi := identifiers.get("doi"):
        return f"https://doi.org/{doi}"
    links = item.get("links")
    alternate = links.get("alternate") if isinstance(links, dict) else None
    if isinstance(alternate, dict) and alternate.get("href"):
        return str(alternate["href"])
    key = str(item.get("key") or data.get("key") or "").strip()
    return f"zotero://select/library/items/{key}" if key else ""


def _zotero_csl_json(key: str, data: dict[str, Any]) -> dict[str, Any]:
    csl: dict[str, Any] = {
        "id": _zotero_citekey(data) or key,
        "type": _zotero_csl_type(str(data.get("itemType") or "")),
        "title": str(data.get("title") or key),
    }
    creators = data.get("creators")
    if isinstance(creators, list):
        authors = [_zotero_creator(creator) for creator in creators if isinstance(creator, dict)]
        if authors:
            csl["author"] = authors
    if year := _zotero_year(str(data.get("date") or "")):
        csl["issued"] = {"date-parts": [[int(year)]]}
    if container := str(
        data.get("publicationTitle")
        or data.get("bookTitle")
        or data.get("proceedingsTitle")
        or data.get("conferenceName")
        or ""
    ).strip():
        csl["container-title"] = container
    if doi := str(data.get("DOI") or "").strip():
        csl["DOI"] = doi
    if url := str(data.get("url") or "").strip():
        csl["URL"] = url
    if abstract := str(data.get("abstractNote") or "").strip():
        csl["abstract"] = abstract
    return csl


def _zotero_creator(creator: dict[str, Any]) -> dict[str, str]:
    if name := str(creator.get("name") or "").strip():
        return {"literal": name}
    family = str(creator.get("lastName") or "").strip()
    given = str(creator.get("firstName") or "").strip()
    if family and given:
        return {"family": family, "given": given}
    if family:
        return {"family": family}
    return {"literal": given}


def _zotero_year(date: str) -> str:
    match = re.search(r"\b(1[5-9]\d{2}|20\d{2}|21\d{2})\b", date)
    return match.group(1) if match else ""


def _zotero_item_type(item_type: str) -> str:
    if item_type in {"book", "bookSection"}:
        return "book"
    if item_type in {"webpage", "blogPost", "forumPost"}:
        return "webpage"
    if item_type == "dataset":
        return "dataset"
    if item_type == "computerProgram":
        return "software"
    if item_type in {"report", "thesis"}:
        return "report"
    return "article"


def _zotero_csl_type(item_type: str) -> str:
    if item_type == "book":
        return "book"
    if item_type in {"conferencePaper", "presentation"}:
        return "paper-conference"
    if item_type in {"webpage", "blogPost", "forumPost"}:
        return "webpage"
    if item_type == "dataset":
        return "dataset"
    if item_type == "computerProgram":
        return "software"
    if item_type in {"report", "thesis"}:
        return "report"
    return "article-journal"


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
