"""Checked-only search-index helpers for alpha.11."""

from __future__ import annotations

import json
import math
import re
import shutil
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

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
    for source in checked_concepts(vault):
        rel = source.relative_to(vault).as_posix()
        target = out / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        fm = parse_frontmatter(safe_read(source))
        docs.append(
            {
                "path": rel,
                "type": fm.get("type"),
                "title": fm.get("title"),
                "sha256": sha256_file(source),
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
    return path.is_file() and _is_searchable_frontmatter(parse_frontmatter(safe_read(path)))


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
        (path.relative_to(vault).as_posix(), safe_read(path), parse_frontmatter(safe_read(path)))
        for path in checked_concepts(vault, include_stale=include_stale)
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
    docs = [
        (path.relative_to(vault).as_posix(), safe_read(path)) for path in checked_concepts(vault)
    ]
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
