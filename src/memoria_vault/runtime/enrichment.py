"""DOI catalog enrichment over the SQLite worker/state boundary."""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import date
from pathlib import Path
from typing import Any
from urllib import error, parse, request

import yaml

from memoria_vault.runtime import state
from memoria_vault.runtime.capture import (
    _extract_pdf_pages,
    _html_text,
    _pdf_content_text,
    _validate_pdf_text_coherence,
    render_references_bib,
)
from memoria_vault.runtime.integrity import record_integrity_check
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.trusted_writer import append_journal_event, commit_writer_changes

PROVIDER_CONFIG = ".memoria/config/providers.yaml"


def load_provider_config(vault: Path) -> dict[str, Any]:
    path = Path(vault) / PROVIDER_CONFIG
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{PROVIDER_CONFIG} must be a map")
    return data


def provider_allowlist_issues(config: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    allowed = [str(value).rstrip("/") + "/" for value in policy.get("allowed_network") or []]
    providers = config.get("providers") if isinstance(config.get("providers"), dict) else {}
    issues = []
    for name, spec in sorted(providers.items()):
        if not isinstance(spec, dict) or not spec.get("enabled", True):
            continue
        base_url = str(spec.get("base_url") or "").strip()
        if base_url and not any(base_url.startswith(prefix) for prefix in allowed):
            issues.append(f"{name} base_url not allowed: {base_url}")
    return issues


def enrich_source(
    vault: Path,
    source_id: str,
    *,
    policy: dict[str, Any],
    provider_payloads: dict[str, Any] | None = None,
    machine: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    vault = Path(vault)
    source = state.catalog_source(vault, source_id)
    if source is None:
        raise ValueError(f"unknown catalog source: {source_id}")
    doi = _doi(source)
    if not doi:
        raise ValueError("enrich-source requires a DOI catalog identifier")

    config = load_provider_config(vault)
    issues = provider_allowlist_issues(config, policy)
    if issues:
        raise PermissionError("; ".join(issues))
    required = _required_providers(config, "doi")
    run_id = run_id or f"enrich-source:{source['source_id']}:{_hash_text(doi)}"
    fixture_payloads = provider_payloads if isinstance(provider_payloads, dict) else {}
    state.start_enrichment_run(
        vault,
        run_id=run_id,
        source_id=source["source_id"],
        required_provider_policy={"branch": "doi", "required": required},
    )
    append_journal_event(
        vault,
        {"event": "run", "run_id": run_id, "workflow": "enrich-source", "status": "started"},
        machine=machine,
    )

    payloads: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for provider in required:
        try:
            payload, latency_ms = _provider_payload(
                vault, config, policy, provider, doi, fixture_payloads
            )
        except RuntimeError as exc:
            missing.append(f"{provider}: {exc}")
            continue
        payloads[provider] = payload
        raw_hash, raw_path = _write_provider_blob(vault, provider, payload)
        state.store_provider_payload(
            vault,
            run_id=run_id,
            provider=provider,
            request_key=doi,
            request_params_hash=_hash_json({"doi": doi}),
            status="ok",
            raw_hash=raw_hash,
            raw_path=raw_path,
            normalized=_normalize_provider(provider, payload),
            latency_ms=latency_ms,
        )
        append_journal_event(
            vault,
            {
                "event": "api_call",
                "run_id": run_id,
                "provider": provider,
                "endpoint": _provider_endpoint(config, provider, doi),
                "request": {"doi": doi},
                "response_hash": raw_hash,
                "status": "ok",
                "latency_ms": latency_ms,
            },
            machine=machine,
        )

    if missing:
        reason = "missing required provider: " + "; ".join(missing)
        state.finish_enrichment_run(vault, run_id, "needs_human")
        finding = record_integrity_check(
            vault,
            f"catalog/sources/{source['source_id']}",
            check="source-enrichment",
            status="failed",
            reason=reason,
            shadow=False,
            machine=machine,
        )
        attention_path = _write_attention_flag(
            vault,
            source,
            check="source-enrichment",
            finding=reason,
            evidence="Required DOI provider payloads did not all resolve.",
        )
        commit = commit_writer_changes(
            vault,
            f"flag source enrichment {source['source_id']}",
            [attention_path],
            machine=machine,
        )
        return {
            "run_id": run_id,
            "enrichment_status": "needs_human",
            "finding": finding,
            "attention_path": attention_path,
            "commit": commit,
        }

    canonical = _merge_doi_source(source, payloads)
    state.replace_external_ids(vault, canonical["external_ids"])
    state.replace_field_provenance(vault, source["source_id"], canonical["provenance"])
    graph_edges = _first_order_work_graph(source["source_id"], payloads)
    state.replace_work_graph_edges(vault, source["source_id"], graph_edges)
    text_status = str(source.get("text_status") or "metadata-only")
    content_hash = str(source.get("normalized_text_sha256") or "")
    content_path = str(source.get("content_path") or "")
    if text_status != "full-text":
        acquired_text = _fixture_full_text(payloads, fixture_payloads)
        if not acquired_text:
            acquired_text = _fetch_discovered_full_text(policy, payloads)
        if acquired_text:
            content_hash, content_path = _write_acquired_text_blob(
                vault, source["source_id"], acquired_text
            )
            text_status = "full-text"
    blocked_status = _blocked_status(canonical)
    full_text_block = "" if text_status == "full-text" else "full-text acquisition failed"
    check_status = "unchecked" if blocked_status else "checked"
    if full_text_block:
        check_status = "unchecked"
    metadata_status = "unverified" if blocked_status else "verified"
    state.upsert_catalog_record(
        vault,
        source_id=source["source_id"],
        title=canonical["title"],
        description=source.get("description", ""),
        concept_path=source["concept_path"],
        doi=doi,
        resource=canonical["resource"],
        identifiers=canonical["identifiers"],
        citekey=source.get("citekey") or canonical["csl_json"].get("id") or "",
        csl_json=canonical["csl_json"],
        metadata_status=metadata_status,
        text_status=text_status,
        check_status=check_status,
        content_hash=content_hash,
        raw_hash=source.get("raw_text_sha256", ""),
        content_path=content_path,
        raw_path=source.get("raw_path", ""),
    )

    if blocked_status:
        state.finish_enrichment_run(vault, run_id, blocked_status)
        check = "source-retraction" if blocked_status == "contested" else "source-enrichment"
        finding = record_integrity_check(
            vault,
            f"catalog/sources/{source['source_id']}",
            check=check,
            status="failed",
            reason=canonical["block_reason"],
            shadow=False,
            machine=machine,
        )
        attention_path = _write_attention_flag(
            vault,
            source,
            check=check,
            finding=canonical["block_reason"],
            evidence="Provider evidence blocked checked promotion.",
        )
        commit = commit_writer_changes(
            vault,
            f"flag source enrichment {source['source_id']}",
            [attention_path],
            machine=machine,
        )
        return {
            "run_id": run_id,
            "enrichment_status": blocked_status,
            "finding": finding,
            "attention_path": attention_path,
            "commit": commit,
        }

    if full_text_block:
        state.finish_enrichment_run(vault, run_id, "needs_human")
        finding = record_integrity_check(
            vault,
            f"catalog/sources/{source['source_id']}",
            check="source-full-text",
            status="failed",
            reason=full_text_block,
            shadow=False,
            machine=machine,
        )
        attention_path = _write_attention_flag(
            vault,
            source,
            check="source-full-text",
            finding=full_text_block,
            evidence="Required provider metadata resolved, but no digestible full text was acquired.",
        )
        commit = commit_writer_changes(
            vault,
            f"flag source full text {source['source_id']}",
            [attention_path],
            machine=machine,
        )
        return {
            "run_id": run_id,
            "enrichment_status": "needs_human",
            "finding": finding,
            "attention_path": attention_path,
            "commit": commit,
        }

    candidate_paths = [
        _write_discovery_candidate(vault, source, edge)
        for edge in graph_edges
        if edge["relation_type"] in {"references", "related"}
    ]
    references_path = "references.bib"
    references_text = render_references_bib(vault)
    (vault / references_path).write_text(references_text, encoding="utf-8")
    state.record_projection_output(
        vault,
        output_id=references_path,
        output_sha256=_hash_text(references_text),
        payload_text=references_text,
    )
    append_journal_event(
        vault,
        {
            "event": "run",
            "run_id": run_id,
            "workflow": "enrich-source",
            "status": "done",
            "outputs": [references_path, *candidate_paths],
        },
        machine=machine,
    )
    commit = commit_writer_changes(
        vault,
        f"enrich source {source['source_id']}",
        [references_path, *candidate_paths],
        machine=machine,
    )
    state.finish_enrichment_run(vault, run_id, "enriched")
    return {
        "run_id": run_id,
        "enrichment_status": "enriched",
        "references_path": references_path,
        "content_path": content_path,
        "discovery_candidate_paths": candidate_paths,
        "text_status": text_status,
        "commit": commit,
    }


def _required_providers(config: dict[str, Any], branch: str) -> list[str]:
    branches = config.get("branches") if isinstance(config.get("branches"), dict) else {}
    spec = branches.get(branch) if isinstance(branches.get(branch), dict) else {}
    providers = spec.get("required")
    if not isinstance(providers, list) or not all(isinstance(item, str) for item in providers):
        raise ValueError(f"{PROVIDER_CONFIG} branches.{branch}.required must be a string list")
    return providers


def _write_attention_flag(
    vault: Path,
    source: dict[str, Any],
    *,
    check: str,
    finding: str,
    evidence: str,
) -> str:
    source_id = str(source["source_id"])
    title = f"Enrichment blocked for {source_id}"
    target = f"catalog/sources/{source_id}"
    rel = normalize_path(
        f"inbox/flag-enrichment-{safe_filename(source_id)}-{safe_filename(check)}.md"
    )
    path = vault / rel
    if path.exists():
        return rel
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(
        [
            "---",
            f'title: "{_yaml_str(title)}"',
            "projection: attention",
            "attention_kind: flag",
            "attention_status: open",
            f'finding: "{_yaml_str(finding)}"',
            "agent_recommendation: issues-found",
            f'target: "{_yaml_str(target)}"',
            "raised_by: enrich-source",
            "loudness: alert",
            f"created: {date.today().isoformat()}",
            "---",
            "",
            "# Finding",
            "",
            finding,
            "",
            "# Evidence",
            "",
            evidence,
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")
    return rel


def _write_discovery_candidate(
    vault: Path,
    source: dict[str, Any],
    edge: dict[str, Any],
    *,
    raised_by: str = "enrich-source",
) -> str:
    target_id = str(edge["target_id"])
    target_title = str(edge.get("target_title") or target_id)
    rel = normalize_path(
        "inbox/candidate-work-"
        f"{safe_filename(str(source['source_id']))}-"
        f"{safe_filename(str(edge['relation_type']))}-"
        f"{safe_filename(target_id)}.md"
    )
    path = vault / rel
    if path.exists():
        return rel
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(
        [
            "---",
            f'title: "Review discovered Work: {_yaml_str(target_title)}"',
            "projection: attention",
            "attention_kind: candidate",
            "attention_status: open",
            f'target: "catalog/sources/{_yaml_str(str(source["source_id"]))}"',
            f'discovered_work_id: "{_yaml_str(target_id)}"',
            f'relation_type: "{_yaml_str(str(edge["relation_type"]))}"',
            f"raised_by: {_yaml_str(raised_by)}",
            "loudness: normal",
            f"created: {date.today().isoformat()}",
            "---",
            "",
            "# Candidate Work",
            "",
            target_title,
            "",
            "# Evidence",
            "",
            f"{source['source_id']} {edge['relation_type']} this Work in provider metadata.",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")
    return rel


def _yaml_str(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def _provider_payload(
    vault: Path,
    config: dict[str, Any],
    policy: dict[str, Any],
    provider: str,
    doi: str,
    fixture_payloads: dict[str, Any],
) -> tuple[dict[str, Any], int]:
    if provider in fixture_payloads:
        payload = fixture_payloads[provider]
        if not isinstance(payload, dict):
            raise RuntimeError("fixture payload must be an object")
        return payload, 0
    endpoint = _provider_endpoint(config, provider, doi)
    from memoria_vault.runtime.operations import require_allowed_network

    require_allowed_network(policy, endpoint)
    timeout = float(_provider_spec(config, provider).get("timeout_seconds") or 10)
    started = time.monotonic()
    req = request.Request(endpoint, headers={"User-Agent": "memoria-vault/0.1 alpha13"})
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (OSError, error.HTTPError, json.JSONDecodeError) as exc:
        raise RuntimeError(str(exc)) from exc
    if not isinstance(payload, dict):
        raise RuntimeError("provider returned non-object JSON")
    return payload, int((time.monotonic() - started) * 1000)


def _provider_endpoint(config: dict[str, Any], provider: str, doi: str) -> str:
    spec = _provider_spec(config, provider)
    template = str(spec.get("endpoint_template") or "").strip()
    if not template:
        raise ValueError(f"{PROVIDER_CONFIG} provider {provider} missing endpoint_template")
    email = os.environ.get(str(spec.get("email_env") or ""), "")
    endpoint = template.format(doi=parse.quote(doi, safe=""), email=parse.quote(email))
    return _append_env_query_params(endpoint, spec)


def _append_env_query_params(endpoint: str, spec: dict[str, Any]) -> str:
    query_params = spec.get("query_params")
    if not isinstance(query_params, dict):
        return endpoint
    parsed = parse.urlsplit(endpoint)
    pairs = parse.parse_qsl(parsed.query, keep_blank_values=True)
    for name, env_name in query_params.items():
        value = os.environ.get(str(env_name or ""), "")
        if value:
            pairs.append((str(name), value))
    query = parse.urlencode(pairs)
    return parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))


def _provider_spec(config: dict[str, Any], provider: str) -> dict[str, Any]:
    providers = config.get("providers") if isinstance(config.get("providers"), dict) else {}
    spec = providers.get(provider)
    if not isinstance(spec, dict):
        raise ValueError(f"{PROVIDER_CONFIG} missing provider: {provider}")
    return spec


def _write_provider_blob(vault: Path, provider: str, payload: dict[str, Any]) -> tuple[str, str]:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    raw_hash = _hash_text(text)
    rel = normalize_path(
        f".memoria/blobs/provider-payloads/{provider}/{raw_hash.removeprefix('sha256:')}.json"
    )
    path = vault / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(text, encoding="utf-8")
    return raw_hash, rel


def _fixture_full_text(
    payloads: dict[str, dict[str, Any]], fixture_payloads: dict[str, Any]
) -> str:
    for candidate in (
        fixture_payloads.get("full_text"),
        payloads.get("unpaywall", {}).get("full_text"),
        _location_value(payloads.get("unpaywall", {}), "full_text"),
        _location_value(payloads.get("unpaywall", {}), "text"),
    ):
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
        if isinstance(candidate, dict):
            text = str(candidate.get("text") or candidate.get("content") or "").strip()
            if text:
                return text
    return ""


def _fetch_discovered_full_text(policy: dict[str, Any], payloads: dict[str, dict[str, Any]]) -> str:
    url = _open_access_text_url(payloads.get("unpaywall", {}))
    if not url:
        return ""
    from memoria_vault.runtime.operations import require_allowed_network

    try:
        require_allowed_network(policy, url)
    except PermissionError:
        return ""
    req = request.Request(url, headers={"User-Agent": "memoria-vault/0.1 alpha14"})
    try:
        with request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
            content_type = _response_content_type(resp)
    except (OSError, error.HTTPError):
        return ""
    return _extract_full_text(url, raw, content_type)


def _open_access_text_url(payload: dict[str, Any]) -> str:
    location = payload.get("best_oa_location")
    if not isinstance(location, dict):
        return ""
    for key in ("url_for_pdf", "url_for_fulltext", "url_for_landing_page", "url"):
        url = str(location.get(key) or "").strip()
        if url:
            return url
    return ""


def _response_content_type(resp: Any) -> str:
    headers = getattr(resp, "headers", None)
    if hasattr(headers, "get"):
        return str(headers.get("Content-Type") or "")
    info = resp.info() if hasattr(resp, "info") else None
    return str(info.get("Content-Type") or "") if hasattr(info, "get") else ""


def _extract_full_text(url: str, raw: bytes, content_type: str) -> str:
    lower_type = content_type.casefold()
    path = parse.urlsplit(url).path.casefold()
    if "html" in lower_type or path.endswith((".html", ".htm")):
        return _html_text(raw)[1].strip()
    if "pdf" in lower_type or path.endswith(".pdf"):
        try:
            pages = _extract_pdf_pages(raw)
            _validate_pdf_text_coherence(pages)
            return _pdf_content_text(pages).strip()
        except (ImportError, RuntimeError, ValueError):
            return ""
    return raw.decode("utf-8", errors="replace").strip()


def _location_value(payload: dict[str, Any], key: str) -> Any:
    location = payload.get("best_oa_location")
    return location.get(key) if isinstance(location, dict) else None


def _write_acquired_text_blob(vault: Path, source_id: str, text: str) -> tuple[str, str]:
    normalized = text.strip() + "\n"
    content_hash = _hash_text(normalized)
    rel = normalize_path(
        ".memoria/blobs/source-content/"
        f"{safe_filename(source_id)}/full-text/{content_hash.removeprefix('sha256:')}.txt"
    )
    path = vault / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(normalized, encoding="utf-8")
    return content_hash, rel


def _merge_doi_source(
    source: dict[str, Any], payloads: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    crossref = _crossref_message(payloads["crossref"])
    openalex = payloads["openalex"]
    unpaywall = payloads["unpaywall"]
    doi = _doi(source)
    title = _first(crossref.get("title")) or str(source.get("title") or "")
    csl_json = {
        "id": source.get("citekey") or source["source_id"],
        "type": crossref.get("type") or "article-journal",
        "title": title,
        "author": _crossref_authors(crossref),
        "issued": crossref.get("issued") or {},
        "DOI": doi,
        "URL": crossref.get("URL") or f"https://doi.org/{doi}",
    }
    if container := _first(crossref.get("container-title")):
        csl_json["container-title"] = container
    if license_value := _unpaywall_license(unpaywall):
        csl_json["license"] = license_value
    identifiers = dict(source.get("identifiers") or {})
    identifiers["doi"] = doi
    if openalex_id := str(openalex.get("id") or "").strip():
        identifiers["openalex"] = openalex_id
    provenance = [
        _provenance("title", title, "crossref"),
        _provenance("author", csl_json["author"], "crossref"),
        _provenance("issued", csl_json["issued"], "crossref"),
        _provenance("DOI", doi, "crossref"),
        _provenance("oa_location", unpaywall.get("best_oa_location") or {}, "unpaywall"),
    ]
    external_ids = [
        _external_id("source", source["source_id"], "doi", doi, "crossref"),
        *(
            [_external_id("source", source["source_id"], "openalex", openalex_id, "openalex")]
            if openalex_id
            else []
        ),
        *_openalex_external_ids(openalex),
    ]
    block_reason = ""
    if _is_retracted(crossref):
        block_reason = "retracted or contested source"
    elif _title_conflict(title, openalex):
        block_reason = "high-authority title conflict"
    return {
        "title": title,
        "resource": csl_json["URL"],
        "identifiers": identifiers,
        "csl_json": csl_json,
        "provenance": provenance,
        "external_ids": external_ids,
        "block_reason": block_reason,
    }


def _first_order_work_graph(
    source_id: str, payloads: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    crossref = _crossref_message(payloads.get("crossref", {}))
    references = crossref.get("reference")
    if isinstance(references, list):
        for reference_row in references:
            if not isinstance(reference_row, dict):
                continue
            doi = str(reference_row.get("DOI") or reference_row.get("doi") or "").strip()
            target = f"doi:{doi.casefold()}" if doi else str(reference_row.get("key") or "").strip()
            if not target:
                continue
            title = str(
                reference_row.get("article-title")
                or reference_row.get("volume-title")
                or reference_row.get("unstructured")
                or target
            ).strip()
            _add_graph_row(
                rows,
                "references",
                target,
                title,
                doi,
                "crossref",
                reference_row,
            )

    openalex = payloads.get("openalex", {})
    for relation_type, field in (("references", "referenced_works"), ("related", "related_works")):
        values = openalex.get(field)
        if not isinstance(values, list):
            continue
        for target in values:
            target_id = str(target or "").strip()
            if target_id:
                _add_graph_row(
                    rows,
                    relation_type,
                    target_id,
                    target_id.rsplit("/", 1)[-1],
                    "",
                    "openalex",
                    {"id": target_id, "source_work": source_id},
                )

    topics = openalex.get("topics")
    if isinstance(topics, list):
        for topic in topics:
            if not isinstance(topic, dict):
                continue
            title = str(topic.get("display_name") or topic.get("name") or "").strip()
            target_id = str(topic.get("id") or "").strip() or (f"topic:{title}" if title else "")
            if target_id:
                _add_graph_row(rows, "topic", target_id, title, "", "openalex", topic)
    return list(rows.values())


def _add_graph_row(
    rows: dict[tuple[str, str], dict[str, Any]],
    relation_type: str,
    target_id: str,
    target_title: str,
    target_doi: str,
    source_provider: str,
    raw: dict[str, Any],
) -> None:
    rows.setdefault(
        (relation_type, target_id),
        {
            "relation_type": relation_type,
            "target_id": target_id,
            "target_title": target_title,
            "target_doi": target_doi,
            "source_provider": source_provider,
            "raw": raw,
        },
    )


def _normalize_provider(provider: str, payload: dict[str, Any]) -> dict[str, Any]:
    if provider == "crossref":
        message = _crossref_message(payload)
        return {"title": _first(message.get("title")), "doi": message.get("DOI")}
    if provider == "openalex":
        return {"title": payload.get("title"), "id": payload.get("id")}
    if provider == "unpaywall":
        return {"doi": payload.get("doi"), "best_oa_location": payload.get("best_oa_location")}
    return payload


def _blocked_status(canonical: dict[str, Any]) -> str:
    if not canonical["block_reason"]:
        return ""
    if "retracted" in canonical["block_reason"] or "contested" in canonical["block_reason"]:
        return "contested"
    return "needs_human"


def _doi(source: dict[str, Any]) -> str:
    identifiers = source.get("identifiers") if isinstance(source.get("identifiers"), dict) else {}
    csl_json = source.get("csl_json") if isinstance(source.get("csl_json"), dict) else {}
    return str(source.get("doi") or identifiers.get("doi") or csl_json.get("DOI") or "").strip()


def _crossref_message(payload: dict[str, Any]) -> dict[str, Any]:
    message = payload.get("message")
    return message if isinstance(message, dict) else payload


def _crossref_authors(message: dict[str, Any]) -> list[dict[str, Any]]:
    authors = message.get("author")
    if not isinstance(authors, list):
        return []
    rows = []
    for author in authors:
        if not isinstance(author, dict):
            continue
        row = {
            key: str(author.get(key) or "").strip()
            for key in ("given", "family", "literal", "ORCID")
            if str(author.get(key) or "").strip()
        }
        if row:
            rows.append(row)
    return rows


def _openalex_external_ids(payload: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    authorships = payload.get("authorships")
    if not isinstance(authorships, list):
        return rows
    for authorship in authorships:
        if not isinstance(authorship, dict):
            continue
        author = authorship.get("author")
        if isinstance(author, dict):
            owner_id = str(author.get("id") or author.get("display_name") or "").strip()
            if author.get("orcid") and owner_id:
                rows.append(
                    _external_id(
                        "person",
                        owner_id,
                        "orcid",
                        str(author["orcid"]).removeprefix("https://orcid.org/"),
                        "openalex",
                    )
                )
            if owner_id.startswith("https://openalex.org/"):
                rows.append(_external_id("person", owner_id, "openalex", owner_id, "openalex"))
        institutions = authorship.get("institutions")
        if isinstance(institutions, list):
            for institution in institutions:
                if not isinstance(institution, dict):
                    continue
                owner_id = str(institution.get("id") or institution.get("display_name") or "")
                value = str(institution.get("ror") or "").strip()
                if owner_id and value:
                    rows.append(_external_id("organization", owner_id, "ror", value, "openalex"))
    return rows


def _external_id(
    owner_type: str, owner_id: str, namespace: str, value: str, provider: str
) -> dict[str, str]:
    return {
        "owner_type": owner_type,
        "owner_id": owner_id,
        "namespace": namespace,
        "value": value,
        "source_provider": provider,
    }


def _provenance(field_path: str, value: Any, provider: str) -> dict[str, str]:
    return {
        "field_path": field_path,
        "value_hash": _hash_json(value),
        "winning_provider": provider,
    }


def _first(value: Any) -> str:
    if isinstance(value, list) and value:
        return str(value[0] or "").strip()
    return str(value or "").strip()


def _unpaywall_license(payload: dict[str, Any]) -> str:
    location = payload.get("best_oa_location")
    return str(location.get("license") or "").strip() if isinstance(location, dict) else ""


def _is_retracted(crossref: dict[str, Any]) -> bool:
    relation = crossref.get("relation")
    return isinstance(relation, dict) and any(
        "retract" in str(key).casefold() or "erratum" in str(key).casefold() for key in relation
    )


def _title_conflict(title: str, openalex: dict[str, Any]) -> bool:
    other = str(openalex.get("title") or "").strip()
    return bool(other and title and other.casefold() != title.casefold())


def _hash_json(value: Any) -> str:
    return _hash_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def _hash_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()
