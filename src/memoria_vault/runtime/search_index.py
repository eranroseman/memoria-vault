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

from memoria_vault.runtime import state
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.vaultio import iter_markdown, parse_frontmatter, safe_read

QMD_INPUT_ROOT = ".memoria/index/qmd/checked"
QMD_MANIFEST = ".memoria/index/qmd/manifest.json"


def rebuild_checked_qmd_source(vault: Path, output_root: str = QMD_INPUT_ROOT) -> dict[str, Any]:
    """Rebuild qmd's disposable input tree from checked Concepts only."""
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
        "backend": "qmd",
        "mode": "bm25",
        "input_root": normalize_path(output_root),
        "documents": docs,
        "qmd_commands": [
            f"qmd collection add {normalize_path(output_root)} --name memoria-checked --mask '**/*.md'",
            "qmd update",
        ],
    }
    manifest_path = vault / QMD_MANIFEST
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


def checked_search_documents(vault: Path, *, include_stale: bool = False) -> list[dict[str, Any]]:
    vault = Path(vault)
    docs: list[dict[str, Any]] = []
    for path in checked_concepts(vault, include_stale=include_stale):
        text = safe_read(path)
        docs.append(
            {
                "path": path.relative_to(vault).as_posix(),
                "text": text,
                "frontmatter": parse_frontmatter(text),
                "source": path,
            }
        )
    if not include_stale:
        docs.extend(_checked_work_documents(vault))
    return sorted(docs, key=lambda row: str(row["path"]))


def checked_concepts(vault: Path, *, include_stale: bool = False) -> list[Path]:
    """Return searchable bundle markdown files with ``check_status: checked``."""
    vault = Path(vault)
    roots = _bundle_roots(vault)
    docs = []
    for root in roots:
        base = vault / root
        if not base.exists():
            continue
        for path in iter_markdown(base, skip_dirs=frozenset()):
            frontmatter = parse_frontmatter(safe_read(path))
            if _is_searchable_frontmatter(frontmatter, include_stale=include_stale):
                docs.append(path)
    return sorted(docs)


def filter_checked_results(vault: Path, rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter qmd-style JSON result rows to checked Concepts."""
    vault = Path(vault)
    out = []
    for row in rows:
        rel = qmd_result_path(row.get("file") or row.get("path") or "", vault)
        if rel and is_checked_concept(vault, rel):
            out.append(row)
    return out


def qmd_result_path(ref: object, vault: Path) -> str:
    """Resolve qmd URI/path output to a vault-relative path."""
    text = str(ref or "")
    if text.startswith("qmd://"):
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
    path = Path(vault) / rel
    if path.is_file() and _is_searchable_frontmatter(parse_frontmatter(safe_read(path))):
        return True
    qmd_path = Path(vault) / QMD_INPUT_ROOT / rel
    return qmd_path.is_file() and _is_searchable_frontmatter(parse_frontmatter(safe_read(qmd_path)))


def answer_query(
    vault: Path,
    query: str,
    *,
    k: int = 5,
    include_stale: bool = False,
) -> dict[str, Any]:
    """Return a deterministic Ask/Query contract over checked BM25 hits."""
    vault = Path(vault)
    docs = [
        (document["path"], document["text"], document["frontmatter"])
        for document in checked_search_documents(vault, include_stale=include_stale)
    ]
    tokenized = [(path, _tokens(text)) for path, text, _frontmatter in docs]
    frontmatter_by_path = {path: frontmatter for path, _text, frontmatter in docs}
    hits = _bm25(tokenized, query)[:k]
    sources = []
    staleness = []
    contradictions = []
    for path, score in hits:
        frontmatter = frontmatter_by_path[path]
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
    return {
        "query": query,
        "engine": "bm25",
        "sources": sources,
        "unknowns": [] if sources else [f"No checked current sources matched: {query}"],
        "staleness": staleness,
        "contradictions": contradictions,
    }


def evaluate_bm25(
    vault: Path,
    cases: Iterable[dict[str, Any]],
    *,
    k: int = 5,
) -> dict[str, Any]:
    """Run a tiny BM25 baseline over checked Concepts for later retrieval evals."""
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
    if frontmatter.get("check_status") != "checked":
        return False
    return include_stale or not _staleness("", frontmatter)


def _staleness(path: str, frontmatter: dict[str, Any]) -> dict[str, Any]:
    lifecycle = str(frontmatter.get("lifecycle") or "")
    status = str(frontmatter.get("status") or "")
    if lifecycle in {"retracted", "archived"}:
        return {"path": path, "field": "lifecycle", "value": lifecycle}
    if status in {"candidate", "needs_review", "rejected", "superseded"}:
        return {"path": path, "field": "status", "value": status}
    return {}


def _bundle_roots(vault: Path) -> list[str]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - packaged deployments install PyYAML.
        raise RuntimeError("search index requires PyYAML to load folders.yaml") from exc

    folders = yaml.safe_load(
        (Path(vault) / ".memoria/schemas/folders.yaml").read_text(encoding="utf-8")
    )
    return [
        normalize_path(root)
        for root in folders.get("bundle_roots") or []
        if normalize_path(root) in {"catalog", "knowledge"}
    ]


def _checked_work_documents(vault: Path) -> list[dict[str, Any]]:
    docs = []
    for source in state.catalog_sources(vault):
        source_id = str(source["source_id"])
        if source.get("text_status") != "full-text":
            continue
        content_path = Path(vault) / normalize_path(str(source.get("content_path") or ""))
        if not content_path.is_file():
            continue
        work_frontmatter = {
            "type": "work",
            "check_status": "checked",
            "title": source["title"],
            "source_id": source_id,
        }
        docs.append(
            _generated_doc(
                f"works/{safe_filename(source_id)}.md",
                work_frontmatter,
                [
                    f"# {source['title']}",
                    "",
                    "## Compact Citation",
                    "",
                    "```json",
                    json.dumps(
                        state.compact_citation(vault, source_id),
                        ensure_ascii=False,
                        sort_keys=True,
                        indent=2,
                    ),
                    "```",
                    "",
                    "## Full Text",
                    "",
                    safe_read(content_path),
                ],
            )
        )
        edges = _work_graph_edges(vault, source_id)
        if edges:
            docs.append(
                _generated_doc(
                    f"graph-neighborhoods/{safe_filename(source_id)}.md",
                    {
                        "type": "graph-neighborhood",
                        "check_status": "checked",
                        "title": f"Graph neighborhood: {source['title']}",
                        "source_id": source_id,
                    },
                    _graph_neighborhood_body(source, edges),
                )
            )
    return docs


def _work_graph_edges(vault: Path, work_id: str) -> list[dict[str, Any]]:
    if not state.db_path(vault).is_file():
        return []
    with state.connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT relation_type, target_id, target_title, target_doi, source_provider
            FROM work_graph_edges
            WHERE work_id = ?
            ORDER BY relation_type, target_id
            """,
            (work_id,),
        ).fetchall()
    return [dict(row) for row in rows]


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
    return lines


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
