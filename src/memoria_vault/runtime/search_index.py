"""Checked-only search-index helpers."""

from __future__ import annotations

import json
import math
import re
import shutil
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml

from memoria_vault.runtime import indexing, state
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.read_barrier import is_consumable_checked_file
from memoria_vault.runtime.vaultio import iter_markdown, parse_frontmatter, safe_read

SEARCH_INPUT_ROOT = ".memoria/index/search/checked"
SEARCH_MANIFEST = ".memoria/index/search/manifest.json"


def rebuild_checked_search_index(
    vault: Path, output_root: str = SEARCH_INPUT_ROOT
) -> dict[str, Any]:
    """Rebuild the disposable checked retrieval tree and BM25 manifest."""
    vault = Path(vault)
    out = vault / normalize_path(output_root)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    docs = []
    for document in checked_search_documents(vault):
        target = out / document["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        source = document.get("source")
        if isinstance(source, Path):
            shutil.copyfile(source, target)
        else:
            target.write_text(str(document["text"]), encoding="utf-8")
        docs.append(
            {
                "path": document["path"],
                "type": document["frontmatter"].get("type"),
                "title": document["frontmatter"].get("title"),
                "sha256": sha256_file(target),
            }
        )
    manifest = {
        "backend": "bm25",
        "mode": "bm25",
        "input_root": normalize_path(output_root),
        "documents": docs,
    }
    manifest_path = vault / SEARCH_MANIFEST
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    indexing.rebuild_passage_index(vault)
    return manifest


def checked_search_documents(vault: Path, *, include_stale: bool = False) -> list[dict[str, Any]]:
    vault = Path(vault)
    docs: list[dict[str, Any]] = []
    for path in checked_concepts(vault, include_stale=include_stale):
        text = safe_read(path)
        rel = path.relative_to(vault).as_posix()
        docs.append(
            {
                "path": rel,
                "text": text,
                "frontmatter": _frontmatter_with_flags(vault, rel, text),
                "source": path,
            }
        )
    if not include_stale:
        docs.extend(_checked_work_documents(vault))
    return sorted(docs, key=lambda row: str(row["path"]))


def checked_concepts(vault: Path, *, include_stale: bool = False) -> list[Path]:
    """Return searchable bundle markdown files with a DB ``checked`` verdict."""
    vault = Path(vault)
    roots = _bundle_roots(vault)
    docs = []
    for root in roots:
        base = vault / root
        if not base.exists():
            continue
        for path in iter_markdown(base, skip_dirs=frozenset()):
            rel = path.relative_to(vault).as_posix()
            if not is_consumable_checked_file(vault, rel):
                continue
            frontmatter = _frontmatter_with_flags(vault, rel, safe_read(path))
            if _is_searchable_frontmatter(frontmatter, include_stale=include_stale):
                docs.append(path)
    return sorted(docs)


def filter_checked_results(vault: Path, rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter search result rows to checked retrieval documents."""
    vault = Path(vault)
    out = []
    for row in rows:
        rel = search_result_path(row.get("file") or row.get("path") or "", vault)
        if rel and is_checked_concept(vault, rel):
            out.append(row)
    return out


def search_result_path(ref: object, vault: Path) -> str:
    """Resolve a result URI/path to a vault-relative path."""
    text = str(ref or "")
    if text.startswith("search://"):
        parts = text.split("/", 3)
        return normalize_path(parts[3]) if len(parts) > 3 else ""
    text = text.split(":", 1)[0].removeprefix("./")
    path = Path(text)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(Path(vault).resolve()).as_posix()
        except (OSError, ValueError):
            return ""
    return normalize_path(text)


def is_checked_concept(vault: Path, relpath: str) -> bool:
    rel = normalize_path(relpath)
    if rel.startswith(f"{SEARCH_INPUT_ROOT}/"):
        rel = rel.removeprefix(f"{SEARCH_INPUT_ROOT}/")
    if _is_checked_generated_work_document(vault, rel):
        return True
    path = Path(vault) / rel
    if (
        path.is_file()
        and is_consumable_checked_file(vault, rel)
        and _is_searchable_frontmatter(_frontmatter_with_flags(vault, rel, safe_read(path)))
    ):
        return True
    return False


def _is_checked_generated_work_document(vault: Path, rel: str) -> bool:
    if not rel.startswith(("fulltexts/", "graph-neighborhoods/")):
        return False
    work_id = _work_id_from_generated_path(rel)
    if not work_id:
        return False
    source = state.catalog_source(vault, work_id)
    return bool(source and source.get("check_status") == "checked")


def answer_query(
    vault: Path,
    query: str,
    *,
    k: int = 5,
    include_stale: bool = False,
    project_id: str = "",
) -> dict[str, Any]:
    """Return a deterministic Ask/Query contract over checked retrieval hits."""
    vault = Path(vault)
    indexing.refresh_stale_passages(vault)
    docs = [
        (document["path"], document["text"], document["frontmatter"])
        for document in checked_search_documents(vault, include_stale=include_stale)
    ]
    project_context = _project_context(project_id, docs)
    retrieval_query = _project_query(query, project_context)
    tokenized = [(path, _tokens(text)) for path, text, _frontmatter in docs]
    frontmatter_by_path = {path: frontmatter for path, _text, frontmatter in docs}
    hits = _bm25(tokenized, retrieval_query)[:k]
    return _answer_from_hits(
        query, hits, frontmatter_by_path, engine="bm25", project_context=project_context
    )


def search_checked_index(
    vault: Path,
    query: str,
    *,
    k: int = 10,
    include_stale: bool = False,
) -> list[dict[str, Any]]:
    """Return BM25 hits over checked retrieval documents."""
    vault = Path(vault)
    indexing.refresh_stale_passages(vault)
    docs = checked_search_documents(vault, include_stale=include_stale)
    by_path = {str(document["path"]): document for document in docs}
    tokenized = [(str(document["path"]), _tokens(str(document["text"]))) for document in docs]
    rows = []
    for path, score in _bm25(tokenized, query)[:k]:
        document = by_path[path]
        frontmatter = dict(document["frontmatter"])
        rows.append(
            {
                "path": path,
                "title": frontmatter.get("title") or Path(path).stem,
                "type": frontmatter.get("type"),
                "score": score,
                "frontmatter": frontmatter,
            }
        )
    return rows


def _answer_from_hits(
    query: str,
    hits: list[tuple[str, float]],
    frontmatter_by_path: dict[str, dict[str, Any]],
    *,
    engine: str,
    project_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sources = []
    staleness = []
    contradictions = []
    for path, score in hits:
        frontmatter = frontmatter_by_path.get(path)
        if frontmatter is None:
            continue
        source = {
            "path": path,
            "title": frontmatter.get("title") or Path(path).stem,
            "type": frontmatter.get("type"),
            "score": score,
        }
        sources.append(source)
        stale = _staleness(path, frontmatter)
        if stale:
            staleness.append(stale)
        if isinstance(frontmatter.get("contradictions"), list):
            for item in frontmatter["contradictions"]:
                contradictions.append({"path": path, "contradiction": item})
    answer = {
        "query": query,
        "engine": engine,
        "sources": sources,
        "unknowns": [] if sources else [f"No checked current sources matched: {query}"],
        "staleness": staleness,
        "contradictions": contradictions,
    }
    if project_context:
        answer["project_context"] = project_context
    return answer


def _project_context(
    project_id: str, docs: list[tuple[str, str, dict[str, Any]]]
) -> dict[str, Any]:
    normalized = normalize_path(project_id.strip()) if project_id.strip() else ""
    if not normalized:
        return {}
    target = normalized.removesuffix(".md")
    for path, _text, frontmatter in docs:
        if frontmatter.get("type") != "project":
            continue
        path_id = (
            path.removesuffix("/project.md")
            if path.endswith("/project.md")
            else path.removesuffix(".md")
        )
        project_slug = Path(path).parent.name if path.endswith("/project.md") else Path(path).stem
        aliases = {
            path,
            path_id,
            Path(path).stem,
            project_slug,
            str(frontmatter.get("slug") or ""),
            str(frontmatter.get("title") or ""),
        }
        if target not in aliases and normalized not in aliases:
            continue
        thesis = _project_link(frontmatter.get("thesis") or frontmatter.get("active_thesis"))
        context = {
            "project_id": path_id,
            "project_path": path,
            "title": frontmatter.get("title") or Path(path).stem,
            "thesis_path": thesis,
        }
        terms = _frontmatter_terms(frontmatter)
        terms.extend(_linked_concept_terms(thesis, docs))
        if terms:
            context["retrieval_terms"] = sorted(set(terms))
        return context
    return {"project_id": target, "project_path": normalized if normalized.endswith(".md") else ""}


def _project_query(query: str, project_context: dict[str, Any]) -> str:
    if not project_context:
        return query
    terms = [
        str(project_context.get("title") or ""),
        Path(str(project_context.get("project_id") or "")).name,
        Path(str(project_context.get("thesis_path") or "")).stem,
        *[str(term) for term in project_context.get("retrieval_terms") or []],
    ]
    return " ".join([query, *(term for term in terms if term)]).strip()


def _project_link(raw: object) -> str:
    value = raw
    if isinstance(raw, dict):
        value = raw.get("target") or raw.get("path") or raw.get("id")
    if not isinstance(value, str):
        return ""
    text = value.strip()
    if text.startswith("[[") and text.endswith("]]"):
        text = text[2:-2].split("|", 1)[0].split("#", 1)[0]
    return normalize_path(text).removesuffix(".md") + ".md" if text else ""


def _linked_concept_terms(relpath: str, docs: list[tuple[str, str, dict[str, Any]]]) -> list[str]:
    if not relpath:
        return []
    target = normalize_path(relpath)
    return next(
        (_frontmatter_terms(frontmatter) for path, _text, frontmatter in docs if path == target), []
    )


def _frontmatter_terms(frontmatter: dict[str, Any]) -> list[str]:
    terms = []
    for key in ("scope_topics", "topics", "tags", "keywords", "research_area", "methodology"):
        terms.extend(_string_list(frontmatter.get(key)))
    facets = frontmatter.get("facets") if isinstance(frontmatter.get("facets"), dict) else {}
    for key in ("research_area", "methodology", "topics"):
        terms.extend(_string_list(facets.get(key)))
    return [term for term in terms if term]


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return []


def evaluate_bm25(
    vault: Path,
    cases: Iterable[dict[str, Any]],
    *,
    k: int = 5,
) -> dict[str, Any]:
    """Run a tiny BM25 baseline over checked retrieval documents."""
    docs = [(document["path"], document["text"]) for document in checked_search_documents(vault)]
    tokenized = [(path, _tokens(text)) for path, text in docs]
    results = []
    for case in cases:
        query = str(case["query"])
        expected = {normalize_path(path) for path in case.get("relevant", [])}
        hits = _bm25(tokenized, query)[:k]
        hit_paths = [path for path, _score in hits]
        results.append(
            {
                "query": query,
                "hits": hit_paths,
                "relevant": sorted(expected),
                "hit": bool(expected.intersection(hit_paths)),
            }
        )
    total = len(results)
    hits = sum(1 for result in results if result["hit"])
    return {
        "engine": "bm25",
        "documents": len(docs),
        "queries": total,
        "hits": hits,
        "recall_at_k": hits / total if total else 0.0,
        "results": results,
    }


def _is_searchable_frontmatter(frontmatter: dict[str, Any], *, include_stale: bool = False) -> bool:
    if frontmatter.get("type") not in {"work", "digest", "note", "hub", "project"}:
        return False
    return include_stale or not _hard_staleness("", frontmatter)


def _frontmatter_with_flags(vault: Path, relpath: str, text: str) -> dict[str, Any]:
    frontmatter = parse_frontmatter(text)
    if "stale" in state.concept_flags(vault, relpath):
        frontmatter["_memoria_stale"] = True
    note_status = state.note_curation_status(vault, relpath)
    if note_status:
        frontmatter["_memoria_note_status"] = note_status
    return frontmatter


def _staleness(path: str, frontmatter: dict[str, Any]) -> dict[str, Any]:
    hard = _hard_staleness(path, frontmatter)
    if hard:
        return hard
    if frontmatter.get("_memoria_stale"):
        return {"path": path, "field": "stale", "value": True}
    return {}


def _hard_staleness(path: str, frontmatter: dict[str, Any]) -> dict[str, Any]:
    lifecycle = str(frontmatter.get("lifecycle") or "")
    status = str(frontmatter.get("_memoria_note_status") or "")
    if lifecycle in {"retracted", "archived"}:
        return {"path": path, "field": "lifecycle", "value": lifecycle}
    if status in {"candidate", "rejected"}:
        return {"path": path, "field": "note_curation_status", "value": status}
    return {}


def _bundle_roots(vault: Path) -> list[str]:
    folders = yaml.safe_load(
        (Path(vault) / ".memoria/schemas/folders.yaml").read_text(encoding="utf-8")
    )
    return [
        normalize_path(root)
        for root in folders.get("bundle_roots") or []
        if normalize_path(root) in {"notes", "hubs", "projects", "digests", "fulltexts"}
    ]


def _checked_work_documents(vault: Path) -> list[dict[str, Any]]:
    docs = []
    for source in state.catalog_sources(vault):
        work_id = str(source["work_id"])
        if source.get("text_status") != "full-text":
            continue
        content_path = Path(vault) / normalize_path(str(source.get("content_path") or ""))
        if not content_path.is_file():
            continue
        work_frontmatter = {
            "type": "fulltext",
            "id": work_id,
            "title": source["title"],
            "work_id": work_id,
            "tags": [],
            "links": {},
        }
        docs.append(
            _generated_doc(
                f"fulltexts/{safe_filename(work_id)}.md",
                work_frontmatter,
                [
                    f"# {source['title']}",
                    "",
                    "## Compact Citation",
                    "",
                    "```json",
                    json.dumps(
                        state.compact_citation(vault, work_id),
                        ensure_ascii=False,
                        sort_keys=True,
                        indent=2,
                    ),
                    "```",
                    "",
                    *_work_aspect_body(vault, work_id),
                    "## Full Text",
                    "",
                    safe_read(content_path),
                ],
            )
        )
        edges = _work_graph_edges(vault, work_id)
        if edges:
            docs.append(
                _generated_doc(
                    f"graph-neighborhoods/{safe_filename(work_id)}.md",
                    {
                        "type": "graph-neighborhood",
                        "title": f"Graph neighborhood: {source['title']}",
                        "work_id": work_id,
                    },
                    _graph_neighborhood_body(source, edges),
                )
            )
    return docs


def _work_id_from_generated_path(rel: str) -> str:
    rel = normalize_path(rel)
    if rel.startswith("graph-neighborhoods/") and rel.endswith(".md"):
        return Path(rel).stem
    if rel.startswith("fulltexts/"):
        parts = rel.split("/")
        if len(parts) == 2 and parts[1].endswith(".md"):
            return Path(parts[1]).stem
    return ""


def _work_aspect_body(vault: Path, work_id: str) -> list[str]:
    aspects = state.work_aspects(vault, work_id)
    if not aspects:
        return []
    lines = ["## Work Aspects", ""]
    for aspect in aspects:
        lines.extend(
            [
                f"### {str(aspect['aspect_type']).replace('_', ' ').title()}",
                "",
                str(aspect["aspect_text"]),
                "",
            ]
        )
    return lines


def _work_graph_edges(vault: Path, work_id: str) -> list[dict[str, Any]]:
    if not state.db_path(vault).is_file():
        return []
    with state.connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT relation_type, target_id, target_title, target_doi, source_provider, raw_json
            FROM work_graph_edges
            WHERE work_id = ?
            ORDER BY relation_type, target_id
            """,
            (work_id,),
        ).fetchall()
    out = []
    for row in rows:
        edge = dict(row)
        try:
            raw = json.loads(str(edge.get("raw_json") or "{}"))
        except json.JSONDecodeError:
            raw = {}
        edge["raw"] = raw if isinstance(raw, dict) else {}
        out.append(edge)
    return out


def _graph_neighborhood_body(source: dict[str, Any], edges: list[dict[str, Any]]) -> list[str]:
    lines = [
        f"# Graph neighborhood: {source['title']}",
        "",
        "## Edges",
        "",
    ]
    for edge in edges:
        title = edge.get("target_title") or edge["target_id"]
        lines.append(
            "- "
            f"{edge['relation_type']}: {title} "
            f"({edge['target_id']}; provider: {edge['source_provider']})"
        )
        details = _graph_edge_details(edge)
        if details:
            lines.append(f"  - metadata: {', '.join(details)}")
    return lines


def _graph_edge_details(edge: dict[str, Any]) -> list[str]:
    details = []
    if edge.get("target_doi"):
        details.append(f"doi: {edge['target_doi']}")
    raw = edge.get("raw") if isinstance(edge.get("raw"), dict) else {}
    for field in ("subfield", "field", "domain"):
        value = _raw_display_name(raw.get(field))
        if value:
            details.append(f"{field}: {value}")
    score = raw.get("score")
    if isinstance(score, int | float):
        details.append(f"score: {score:g}")
    return details


def _raw_display_name(value: object) -> str:
    if isinstance(value, dict):
        return str(value.get("display_name") or value.get("name") or "").strip()
    if isinstance(value, str):
        return value.strip()
    return ""


def _generated_doc(path: str, frontmatter: dict[str, Any], body: list[str]) -> dict[str, Any]:
    text = "\n".join(
        [
            "---",
            *[
                f"{key}: {json.dumps(value, ensure_ascii=False)}"
                for key, value in frontmatter.items()
            ],
            "---",
            "",
            *body,
            "",
        ]
    )
    return {
        "path": normalize_path(path),
        "text": text,
        "frontmatter": dict(frontmatter),
    }


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _bm25(docs: list[tuple[str, list[str]]], query: str) -> list[tuple[str, float]]:
    if not docs:
        return []
    doc_freq: Counter[str] = Counter()
    for _path, tokens in docs:
        doc_freq.update(set(tokens))
    avg_len = sum(len(tokens) for _path, tokens in docs) / len(docs)
    query_terms = _tokens(query)
    scored = []
    for path, tokens in docs:
        counts = Counter(tokens)
        score = 0.0
        for term in query_terms:
            if not counts[term]:
                continue
            score += _bm25_term(counts[term], len(tokens), doc_freq[term], len(docs), avg_len)
        if score > 0:
            scored.append((path, score))
    return sorted(scored, key=lambda item: (-item[1], item[0]))


def _bm25_term(freq: int, doc_len: int, doc_freq: int, corpus_size: int, avg_len: float) -> float:
    k1 = 1.5
    b = 0.75
    idf = math.log(1 + (corpus_size - doc_freq + 0.5) / (doc_freq + 0.5))
    denom = freq + k1 * (1 - b + b * doc_len / (avg_len or 1))
    return idf * (freq * (k1 + 1) / denom)
