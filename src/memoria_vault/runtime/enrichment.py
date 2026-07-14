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
    derive_work_aspect_rows,
    render_references_bib,
)
from memoria_vault.runtime.content_security import neutralize_untrusted_markdown
from memoria_vault.runtime.integrity import record_integrity_check
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.trusted_writer import (
    OperationContext,
    append_journal_event,
    commit_writer_changes,
    validate_operation_context,
)
from memoria_vault.runtime.vaultio import frontmatter_doc, write_text_durable

PROVIDER_CONFIG = ".memoria/config/providers.yaml"


def load_provider_config(vault: Path) -> dict[str, Any]:
    path = Path(vault) / PROVIDER_CONFIG
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{PROVIDER_CONFIG} must be a map")
    return data


def provider_allowlist_issues(config: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    from memoria_vault.runtime.operations import network_allowed

    providers = config.get("providers") if isinstance(config.get("providers"), dict) else {}
    issues = []
    for name, spec in sorted(providers.items()):
        if not isinstance(spec, dict) or not spec.get("enabled", True):
            continue
        base_url = str(spec.get("base_url") or "").strip()
        if base_url and not network_allowed(policy, base_url):
            issues.append(f"{name} base_url not allowed: {base_url}")
    return issues


def enrich_source(
    vault: Path,
    work_id: str,
    *,
    context: OperationContext,
    policy: dict[str, Any],
    provider_payloads: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validate_operation_context(vault, context)
    vault = Path(vault)
    source = state.catalog_source(vault, work_id)
    if source is None:
        raise ValueError(f"unknown catalog source: {work_id}")
    doi = _doi(source)
    if not doi:
        raise ValueError("enrich-source requires a DOI catalog identifier")

    config = load_provider_config(vault)
    issues = provider_allowlist_issues(config, policy)
    if issues:
        raise PermissionError("; ".join(issues))
    run_id = context.run_id
    fixture_payloads = provider_payloads if isinstance(provider_payloads, dict) else {}
    required = _required_providers(config, "doi")
    optional = _optional_providers(config, "doi", fixture_payloads)
    state.start_enrichment_run(
        vault,
        run_id=run_id,
        work_id=source["work_id"],
        required_provider_policy={"branch": "doi", "required": required, "optional": optional},
        request_id=context.request_id,
    )
    append_journal_event(
        vault,
        {"event": "run", "workflow": "enrich-source", "status": "started"},
        context=context,
    )

    payloads: dict[str, dict[str, Any]] = {}
    payload_hashes: dict[str, str] = {}
    missing: list[str] = []
    optional_missing: list[str] = []
    for provider in [*required, *optional]:
        try:
            payload, latency_ms = _provider_payload(
                vault, config, policy, provider, doi, fixture_payloads
            )
        except RuntimeError as exc:
            if provider in required:
                missing.append(f"{provider}: {exc}")
            else:
                optional_missing.append(f"{provider}: {exc}")
            continue
        payloads[provider] = payload
        raw_hash, raw_path = _write_provider_blob(vault, provider, payload)
        payload_hashes[provider] = raw_hash
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
                "provider": provider,
                "endpoint": _provider_endpoint(config, provider, doi),
                "request": {"doi": doi},
                "response_hash": raw_hash,
                "status": "ok",
                "latency_ms": latency_ms,
            },
            context=context,
        )

    if missing:
        reason = "missing required provider: " + "; ".join(missing)
        state.finish_enrichment_run(vault, run_id, "needs_human")
        finding = record_integrity_check(
            vault,
            f"catalog/sources/{source['work_id']}",
            check="source-enrichment",
            status="failed",
            reason=reason,
            shadow=False,
            context=context,
        )
        attention_path = _write_attention_flag(
            vault,
            source,
            check="source-enrichment",
            finding=reason,
            evidence="Required DOI provider payloads did not all resolve."
            + _provider_hash_evidence(payload_hashes),
        )
        commit = commit_writer_changes(
            vault,
            f"flag source enrichment {source['work_id']}",
            [attention_path],
            context=context,
        )
        return {
            "run_id": run_id,
            "enrichment_status": "needs_human",
            "finding": finding,
            "attention_path": attention_path,
            "commit": commit,
        }

    canonical = _merge_doi_source(source, payloads, payload_hashes)
    state.replace_external_ids(vault, canonical["external_ids"])
    state.replace_field_provenance(vault, source["work_id"], canonical["provenance"])
    graph_edges = _first_order_work_graph(source["work_id"], payloads)
    state.replace_work_graph_edges(vault, source["work_id"], graph_edges)
    text_status = str(source.get("text_status") or "metadata-only")
    content_hash = str(source.get("normalized_text_sha256") or "")
    content_path = str(source.get("content_path") or "")
    if text_status != "full-text":
        acquired_text = _fixture_full_text(payloads, fixture_payloads)
        if not acquired_text:
            acquired_text = _fetch_discovered_full_text(policy, payloads)
        if acquired_text:
            content_hash, content_path = _write_acquired_text_blob(
                vault, source["work_id"], acquired_text
            )
            text_status = "full-text"
    blocked_status = _blocked_status(canonical)
    full_text_block = "" if text_status == "full-text" else "full-text acquisition failed"
    check_status = "unchecked" if blocked_status else "checked"
    if full_text_block:
        check_status = "unchecked"
    provider_coverage = _provider_coverage(canonical)
    state.upsert_catalog_record(
        vault,
        work_id=source["work_id"],
        title=canonical["title"],
        description=source.get("description", ""),
        concept_path=source["concept_path"],
        doi=doi,
        resource=canonical["resource"],
        identifiers=canonical["identifiers"],
        citekey=source.get("citekey") or canonical["csl_json"].get("id") or "",
        csl_json=canonical["csl_json"],
        provider_coverage=provider_coverage,
        text_status=text_status,
        check_status=check_status,
        content_hash=content_hash,
        raw_hash=source.get("raw_text_sha256", ""),
        content_path=content_path,
        raw_path=source.get("raw_path", ""),
    )
    state.replace_work_aspects(
        vault,
        source["work_id"],
        derive_work_aspect_rows(
            canonical["csl_json"],
            _source_content_text(vault, content_path),
            check_status=check_status,
        ),
    )

    if blocked_status:
        state.finish_enrichment_run(vault, run_id, blocked_status)
        check = "source-retraction" if blocked_status == "contested" else "source-enrichment"
        finding = record_integrity_check(
            vault,
            f"catalog/sources/{source['work_id']}",
            check=check,
            status="failed",
            reason=canonical["block_reason"],
            shadow=False,
            context=context,
        )
        attention_path = _write_attention_flag(
            vault,
            source,
            check=check,
            finding=canonical["block_reason"],
            evidence="Provider evidence blocked checked promotion."
            + _provider_hash_evidence(payload_hashes),
        )
        commit = commit_writer_changes(
            vault,
            f"flag source enrichment {source['work_id']}",
            [attention_path],
            context=context,
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
            f"catalog/sources/{source['work_id']}",
            check="source-full-text",
            status="failed",
            reason=full_text_block,
            shadow=False,
            context=context,
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
            f"flag source full text {source['work_id']}",
            [attention_path],
            context=context,
        )
        return {
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
    references_path = "bibliography.bib"
    references_text = render_references_bib(vault)
    write_text_durable(vault / references_path, references_text, create_parent=True)
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
            "workflow": "enrich-source",
            "status": "done",
            "outputs": [references_path, *candidate_paths],
        },
        context=context,
    )
    commit = commit_writer_changes(
        vault,
        f"enrich source {source['work_id']}",
        [references_path, *candidate_paths],
        context=context,
    )
    state.finish_enrichment_run(vault, run_id, "enriched")
    return {
        "run_id": run_id,
        "enrichment_status": "enriched",
        "references_path": references_path,
        "content_path": content_path,
        "discovery_candidate_paths": candidate_paths,
        "text_status": text_status,
        "optional_provider_failures": optional_missing,
        "commit": commit,
    }


def replay_enrichment_run(vault: Path, run_id: str) -> dict[str, Any]:
    vault = Path(vault)
    with state.connect(vault) as conn:
        run = conn.execute(
            "SELECT work_id FROM enrichment_runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        rows = conn.execute(
            """
            SELECT provider, raw_hash, raw_path
            FROM provider_payloads
            WHERE run_id = ?
            ORDER BY provider
            """,
            (run_id,),
        ).fetchall()
    if run is None:
        raise RuntimeError(f"unknown enrichment run: {run_id}")
    source = state.catalog_source(vault, str(run["work_id"]))
    if source is None:
        raise RuntimeError(f"unknown catalog source: {run['work_id']}")
    payloads = {str(row["provider"]): _read_provider_blob(vault, dict(row)) for row in rows}
    if not payloads:
        raise RuntimeError(f"no provider payload blobs recorded for run: {run_id}")
    return {
        "work_id": source["work_id"],
        "provider_payloads": payloads,
        "normalized": {
            provider: _normalize_provider(provider, payload)
            for provider, payload in sorted(payloads.items())
        },
        "canonical": _merge_doi_source(
            source,
            payloads,
            {str(row["provider"]): str(row["raw_hash"]) for row in rows},
        ),
        "graph_edges": _first_order_work_graph(source["work_id"], payloads),
    }


def _required_providers(config: dict[str, Any], branch: str) -> list[str]:
    branches = config.get("branches") if isinstance(config.get("branches"), dict) else {}
    spec = branches.get(branch) if isinstance(branches.get(branch), dict) else {}
    providers = spec.get("required")
    if not isinstance(providers, list) or not all(isinstance(item, str) for item in providers):
        raise ValueError(f"{PROVIDER_CONFIG} branches.{branch}.required must be a string list")
    return providers


def _optional_providers(
    config: dict[str, Any], branch: str, fixture_payloads: dict[str, Any] | None = None
) -> list[str]:
    branches = config.get("branches") if isinstance(config.get("branches"), dict) else {}
    spec = branches.get(branch) if isinstance(branches.get(branch), dict) else {}
    providers = spec.get("optional", [])
    if not isinstance(providers, list) or not all(isinstance(item, str) for item in providers):
        raise ValueError(f"{PROVIDER_CONFIG} branches.{branch}.optional must be a string list")
    fixtures = fixture_payloads if isinstance(fixture_payloads, dict) else {}
    return [
        provider
        for provider in providers
        if provider in fixtures or _provider_default_on(config, provider)
    ]


def _provider_default_on(config: dict[str, Any], provider: str) -> bool:
    spec = _provider_spec(config, provider)
    gate = spec.get("default_on_when_keyed")
    if isinstance(gate, str):
        return bool(os.environ.get(gate))
    if isinstance(gate, list):
        return any(isinstance(name, str) and os.environ.get(name) for name in gate)
    return False


def _write_attention_flag(
    vault: Path,
    source: dict[str, Any],
    *,
    check: str,
    finding: str,
    evidence: str,
) -> str:
    work_id = str(source["work_id"])
    title = f"Enrichment blocked for {work_id}"
    target = f"catalog/sources/{work_id}"
    rel = normalize_path(
        f"inbox/flag-enrichment-{safe_filename(work_id)}-{safe_filename(check)}.md"
    )
    path = vault / rel
    if path.exists():
        return rel
    safe_finding = neutralize_untrusted_markdown(finding)
    safe_evidence = neutralize_untrusted_markdown(evidence)
    text = frontmatter_doc(
        {
            "title": title,
            "projection": "attention",
            "attention_kind": "flag",
            "attention_status": "open",
            "finding": safe_finding,
            "agent_recommendation": "issues-found",
            "target": target,
            "raised_by": "enrich-source",
            "loudness": "alert",
            "created": date.today().isoformat(),
        },
        f"# Finding\n\n{safe_finding}\n\n# Evidence\n\n{safe_evidence}\n",
    )
    write_text_durable(path, text, create_parent=True)
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
        f"{safe_filename(str(source['work_id']))}-"
        f"{safe_filename(str(edge['relation_type']))}-"
        f"{safe_filename(target_id)}.md"
    )
    path = vault / rel
    if path.exists():
        return rel
    safe_target_title = neutralize_untrusted_markdown(target_title)
    text = frontmatter_doc(
        {
            "title": f"Review discovered Work: {safe_target_title}",
            "projection": "attention",
            "attention_kind": "candidate",
            "attention_status": "open",
            "target": f"catalog/sources/{source['work_id']}",
            "discovered_work_id": target_id,
            "relation_type": str(edge["relation_type"]),
            "raised_by": raised_by,
            "loudness": "normal",
            "created": date.today().isoformat(),
        },
        (
            f"# Candidate Work\n\n{safe_target_title}\n\n# Evidence\n\n"
            f"{source['work_id']} {edge['relation_type']} this Work in provider metadata.\n"
        ),
    )
    write_text_durable(path, text, create_parent=True)
    return rel


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
    spec = _provider_spec(config, provider)
    timeout = float(spec.get("timeout_seconds") or 10)
    started = time.monotonic()
    headers = {"User-Agent": "memoria-vault/0.1 alpha16"}
    header_env = spec.get("header_env")
    if isinstance(header_env, dict):
        for header, env_name in header_env.items():
            value = os.environ.get(str(env_name or ""), "")
            if value:
                headers[str(header)] = value
    req = request.Request(endpoint, headers=headers)
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
    if not path.exists():
        write_text_durable(path, text, create_parent=True)
    return raw_hash, rel


def _provider_hash_evidence(payload_hashes: dict[str, str]) -> str:
    if not payload_hashes:
        return ""
    rows = "\n".join(
        f"- {provider}: {raw_hash}" for provider, raw_hash in sorted(payload_hashes.items())
    )
    return "\n\nProvider payload hashes:\n" + rows


def _read_provider_blob(vault: Path, row: dict[str, Any]) -> dict[str, Any]:
    rel = normalize_path(str(row["raw_path"]))
    path = vault / rel
    if not path.is_file():
        raise RuntimeError(f"provider payload blob missing: {rel}")
    text = path.read_text(encoding="utf-8")
    actual_hash = _hash_text(text)
    if actual_hash != row["raw_hash"]:
        raise RuntimeError(f"provider payload blob hash mismatch: {rel}")
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise RuntimeError(f"provider payload blob is not an object: {rel}")
    return payload


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
    from memoria_vault.runtime.operations import require_allowed_network

    for url in _discovered_full_text_urls(payloads):
        try:
            require_allowed_network(policy, url)
        except PermissionError:
            continue
        req = request.Request(url, headers={"User-Agent": "memoria-vault/0.1 alpha16"})
        try:
            with request.urlopen(req, timeout=20) as resp:
                raw = resp.read()
                content_type = _response_content_type(resp)
        except (OSError, error.HTTPError):
            continue
        try:
            text = _extract_full_text(url, raw, content_type)
        except (RuntimeError, ValueError):
            continue
        if text:
            return text
    return ""


def _discovered_full_text_urls(payloads: dict[str, dict[str, Any]]) -> list[str]:
    urls = []
    for location in _open_access_locations(payloads.get("unpaywall", {})):
        for key in ("url_for_pdf", "url_for_fulltext", "url_for_landing_page", "url"):
            _append_url(urls, location.get(key))
    openalex = payloads.get("openalex", {})
    open_access = openalex.get("open_access")
    if isinstance(open_access, dict):
        _append_url(urls, open_access.get("oa_url"))
    for location in _openalex_open_access_locations(openalex):
        for key in ("pdf_url", "landing_page_url"):
            _append_url(urls, location.get(key))
    crossref_links = _crossref_message(payloads.get("crossref", {})).get("link")
    if isinstance(crossref_links, list):
        for link in crossref_links:
            if isinstance(link, dict):
                _append_url(urls, link.get("URL") or link.get("url"))
    return urls


def _append_url(urls: list[str], value: Any) -> None:
    url = str(value or "").strip()
    if url and url not in urls:
        urls.append(url)


def _open_access_locations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    locations = []
    best = payload.get("best_oa_location")
    if isinstance(best, dict):
        locations.append(best)
    oa_locations = payload.get("oa_locations")
    if isinstance(oa_locations, list):
        for location in oa_locations:
            if isinstance(location, dict) and location not in locations:
                locations.append(location)
    return locations


def _openalex_open_access_locations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    locations = []
    for key in ("best_oa_location", "primary_location"):
        location = payload.get(key)
        if isinstance(location, dict) and location.get("is_oa") is not False:
            locations.append(location)
    all_locations = payload.get("locations")
    if isinstance(all_locations, list):
        for location in all_locations:
            if (
                isinstance(location, dict)
                and location.get("is_oa") is not False
                and location not in locations
            ):
                locations.append(location)
    return locations


def _openalex_locations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    locations = []
    for key in ("primary_location", "best_oa_location"):
        location = payload.get(key)
        if isinstance(location, dict):
            locations.append(location)
    all_locations = payload.get("locations")
    if isinstance(all_locations, list):
        for location in all_locations:
            if isinstance(location, dict) and location not in locations:
                locations.append(location)
    return locations


def _response_content_type(resp: Any) -> str:
    return str(resp.headers.get("Content-Type") or "")


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
    for location in _open_access_locations(payload):
        if key in location:
            return location.get(key)
    return None


def _write_acquired_text_blob(vault: Path, work_id: str, text: str) -> tuple[str, str]:
    normalized = text.strip() + "\n"
    content_hash = _hash_text(normalized)
    rel = normalize_path(
        ".memoria/blobs/source-content/"
        f"{safe_filename(work_id)}/full-text/{content_hash.removeprefix('sha256:')}.txt"
    )
    path = vault / rel
    if not path.exists():
        write_text_durable(path, normalized, create_parent=True)
    return content_hash, rel


def _source_content_text(vault: Path, content_path: str) -> str:
    if not content_path:
        return ""
    path = vault / normalize_path(content_path)
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _merge_doi_source(
    source: dict[str, Any],
    payloads: dict[str, dict[str, Any]],
    payload_hashes: dict[str, str] | None = None,
) -> dict[str, Any]:
    payload_hashes = dict(payload_hashes or {})
    crossref = _crossref_message(payloads["crossref"])
    openalex = payloads["openalex"]
    unpaywall = payloads["unpaywall"]
    doi = _doi(source)
    title = _first(crossref.get("title")) or str(source.get("title") or "")
    openalex_title = str(openalex.get("title") or "").strip()
    title_conflict = _title_conflict(title, openalex)
    csl_json = {
        "id": source.get("citekey") or source["work_id"],
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
    semantic_scholar = payloads.get("semanticscholar", {})
    semantic_scholar_id = str(semantic_scholar.get("paperId") or "").strip()
    if semantic_scholar_id:
        identifiers["semanticscholar"] = semantic_scholar_id
    tldr = semantic_scholar.get("tldr")
    if isinstance(tldr, dict) and str(tldr.get("text") or "").strip():
        csl_json["note"] = str(tldr["text"]).strip()
    provenance = [
        _provenance(
            "title",
            title,
            "crossref",
            evidence_payload_id=payload_hashes.get("crossref", ""),
            alternatives=[
                {
                    "provider": "openalex",
                    "value": openalex_title,
                    "evidence_payload_id": payload_hashes.get("openalex", ""),
                }
            ]
            if title_conflict
            else [],
            conflict_status="conflict" if title_conflict else "none",
        ),
        _provenance(
            "author",
            csl_json["author"],
            "crossref",
            evidence_payload_id=payload_hashes.get("crossref", ""),
        ),
        _provenance(
            "issued",
            csl_json["issued"],
            "crossref",
            evidence_payload_id=payload_hashes.get("crossref", ""),
        ),
        _provenance("DOI", doi, "crossref", evidence_payload_id=payload_hashes.get("crossref", "")),
        _provenance(
            "oa_location",
            unpaywall.get("best_oa_location") or {},
            "unpaywall",
            evidence_payload_id=payload_hashes.get("unpaywall", ""),
        ),
    ]
    external_ids = [
        _external_id("source", source["work_id"], "doi", doi, "crossref"),
        *(
            [_external_id("source", source["work_id"], "openalex", openalex_id, "openalex")]
            if openalex_id
            else []
        ),
        *(
            [
                _external_id(
                    "source",
                    source["work_id"],
                    "semanticscholar",
                    semantic_scholar_id,
                    "semanticscholar",
                )
            ]
            if semantic_scholar_id
            else []
        ),
        *_openalex_external_ids(openalex),
    ]
    block_reason = ""
    if _is_retracted(crossref):
        block_reason = "retracted or contested source"
    elif title_conflict:
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
    work_id: str, payloads: dict[str, dict[str, Any]]
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
    relations = crossref.get("relation")
    if isinstance(relations, dict):
        for relation_key, relation_rows in sorted(relations.items()):
            rows_for_relation = relation_rows if isinstance(relation_rows, list) else []
            for relation_row in rows_for_relation:
                if not isinstance(relation_row, dict):
                    continue
                relation_id = str(relation_row.get("id") or "").strip()
                if not relation_id:
                    continue
                id_type = str(relation_row.get("id-type") or "").strip().casefold()
                target_doi = relation_id if id_type == "doi" else ""
                target = f"doi:{target_doi.casefold()}" if target_doi else relation_id
                _add_graph_row(
                    rows,
                    "related",
                    target,
                    relation_id,
                    target_doi,
                    "crossref",
                    {"relation": relation_key, **relation_row},
                )

    openalex = payloads.get("openalex", {})
    authorships = openalex.get("authorships")
    if isinstance(authorships, list):
        for authorship in authorships:
            if not isinstance(authorship, dict):
                continue
            author = authorship.get("author")
            author_id = ""
            author_title = ""
            if isinstance(author, dict):
                author_title = str(author.get("display_name") or "").strip()
                author_id = str(
                    author.get("id") or author.get("orcid") or author_title or ""
                ).strip()
            if author_id:
                _add_graph_row(
                    rows,
                    "authorship",
                    author_id,
                    author_title or author_id,
                    "",
                    "openalex",
                    authorship,
                )
            institutions = authorship.get("institutions")
            if isinstance(institutions, list):
                for institution in institutions:
                    if not isinstance(institution, dict):
                        continue
                    title = str(institution.get("display_name") or "").strip()
                    target_id = str(
                        institution.get("id") or institution.get("ror") or title or ""
                    ).strip()
                    if not target_id:
                        continue
                    raw = dict(institution)
                    if author_id:
                        raw["author_id"] = author_id
                    if author_title:
                        raw["author_display_name"] = author_title
                    _add_graph_row(rows, "institution", target_id, title, "", "openalex", raw)

    for location in _openalex_locations(openalex):
        location_source = location.get("source")
        if not isinstance(location_source, dict):
            continue
        title = str(location_source.get("display_name") or "").strip()
        target_id = str(
            location_source.get("id")
            or location_source.get("issn_l")
            or _first(location_source.get("issn"))
            or title
            or ""
        ).strip()
        if not target_id:
            continue
        raw = dict(location_source)
        raw["location"] = {key: value for key, value in location.items() if key != "source"}
        _add_graph_row(rows, "published_in", target_id, title or target_id, "", "openalex", raw)

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
                    {"id": target_id, "source_work": work_id},
                )

    semantic_scholar = payloads.get("semanticscholar", {})
    for relation_type, field in (("references", "references"), ("related", "citations")):
        values = semantic_scholar.get(field)
        if not isinstance(values, list):
            continue
        for row in values:
            if not isinstance(row, dict):
                continue
            target_doi = _semantic_scholar_doi(row)
            paper_id = str(row.get("paperId") or "").strip()
            target_id = (
                f"doi:{target_doi.casefold()}" if target_doi else f"semanticscholar:{paper_id}"
            )
            if target_id == "semanticscholar:":
                continue
            title = str(row.get("title") or target_id).strip()
            _add_graph_row(
                rows,
                relation_type,
                target_id,
                title,
                target_doi,
                "semanticscholar",
                row,
            )

    topic_candidates = []
    if isinstance(openalex.get("primary_topic"), dict):
        topic_candidates.append(openalex["primary_topic"])
    topics = openalex.get("topics")
    if isinstance(topics, list):
        topic_candidates.extend(topic for topic in topics if isinstance(topic, dict))
    concepts = openalex.get("concepts")
    if isinstance(concepts, list):
        topic_candidates.extend(concept for concept in concepts if isinstance(concept, dict))
    mesh = openalex.get("mesh")
    if isinstance(mesh, list):
        topic_candidates.extend(_openalex_mesh_topics(mesh))
    sdgs = openalex.get("sustainable_development_goals")
    if isinstance(sdgs, list):
        topic_candidates.extend(sdg for sdg in sdgs if isinstance(sdg, dict))
    for topic in topic_candidates:
        title = str(topic.get("display_name") or topic.get("name") or "").strip()
        target_id = str(topic.get("id") or "").strip() or (f"topic:{title}" if title else "")
        if target_id:
            _add_graph_row(rows, "topic", target_id, title, "", "openalex", topic)

    keywords = openalex.get("keywords")
    if isinstance(keywords, list):
        for keyword in keywords:
            if not isinstance(keyword, dict):
                continue
            title = str(
                keyword.get("display_name") or keyword.get("name") or keyword.get("keyword") or ""
            ).strip()
            target_id = str(keyword.get("id") or "").strip() or (
                f"keyword:{title}" if title else ""
            )
            if target_id:
                _add_graph_row(rows, "keyword", target_id, title, "", "openalex", keyword)
    return list(rows.values())


def _openalex_mesh_topics(rows: list[Any]) -> list[dict[str, Any]]:
    topics = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        title = str(row.get("descriptor_name") or "").strip()
        qualifier = str(row.get("qualifier_name") or "").strip()
        display = f"{title} / {qualifier}" if title and qualifier else title or qualifier
        target_id = str(row.get("descriptor_ui") or row.get("qualifier_ui") or "").strip()
        if display or target_id:
            topics.append(
                {**row, "id": f"mesh:{target_id}" if target_id else "", "display_name": display}
            )
    return topics


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
    if provider == "semanticscholar":
        return {
            "paperId": payload.get("paperId"),
            "title": payload.get("title"),
            "tldr": payload.get("tldr"),
        }
    return payload


def _semantic_scholar_doi(row: dict[str, Any]) -> str:
    external_ids = row.get("externalIds")
    if isinstance(external_ids, dict):
        return str(external_ids.get("DOI") or external_ids.get("doi") or "").strip()
    return ""


def _blocked_status(canonical: dict[str, Any]) -> str:
    if not canonical["block_reason"]:
        return ""
    if "retracted" in canonical["block_reason"] or "contested" in canonical["block_reason"]:
        return "contested"
    return "needs_human"


def _provider_coverage(canonical: dict[str, Any]) -> str:
    if canonical["block_reason"] and "retracted" not in canonical["block_reason"]:
        return "degraded"
    return "full"


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


def _provenance(
    field_path: str,
    value: Any,
    provider: str,
    *,
    evidence_payload_id: str = "",
    alternatives: list[dict[str, Any]] | None = None,
    conflict_status: str = "none",
) -> dict[str, Any]:
    return {
        "field_path": field_path,
        "value_hash": _hash_json(value),
        "winning_provider": provider,
        "evidence_payload_id": evidence_payload_id,
        "alternatives": alternatives or [],
        "conflict_status": conflict_status,
    }


def _first(value: Any) -> str:
    if isinstance(value, list) and value:
        return str(value[0] or "").strip()
    return str(value or "").strip()


def _unpaywall_license(payload: dict[str, Any]) -> str:
    return str(_location_value(payload, "license") or "").strip()


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
