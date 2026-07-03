"""Checked-only search-index helpers."""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.read_barrier import is_consumable_checked_file
from memoria_vault.runtime.vaultio import iter_markdown, parse_frontmatter, safe_read

QMD_INPUT_ROOT = ".memoria/index/qmd/checked"
QMD_MANIFEST = ".memoria/index/qmd/manifest.json"
QMD_BIN_ENV = "MEMORIA_QMD_BIN"


def resolve_qmd_executable() -> dict[str, str]:
    explicit = os.environ.get(QMD_BIN_ENV, "").strip()
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_absolute():
            return {"path": "", "source": QMD_BIN_ENV, "error": f"{QMD_BIN_ENV} must be absolute"}
        if not _is_executable(path):
            return {
                "path": "",
                "source": QMD_BIN_ENV,
                "error": f"{QMD_BIN_ENV} is not executable: {path}",
            }
        return {"path": str(path.resolve()), "source": QMD_BIN_ENV, "error": ""}

    npm_qmd = _npm_global_qmd()
    if npm_qmd and _is_executable(npm_qmd):
        return {"path": str(npm_qmd.resolve()), "source": "npm-global", "error": ""}

    path_qmd = shutil.which("qmd")
    if path_qmd:
        resolved = Path(path_qmd).resolve()
        return {
            "path": "",
            "source": "path",
            "error": (
                f"qmd found at {resolved}; set {QMD_BIN_ENV} to an absolute qmd path "
                "or install @tobilu/qmd globally with npm"
            ),
        }
    return {"path": "", "source": "", "error": "qmd not found"}


def _npm_global_qmd() -> Path | None:
    npm = shutil.which("npm")
    if not npm:
        return None
    try:
        proc = subprocess.run(
            [npm, "prefix", "-g"],
            check=False,
            text=True,
            capture_output=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    prefix = proc.stdout.strip().splitlines()
    if proc.returncode != 0 or not prefix:
        return None
    root = Path(prefix[0]).expanduser()
    candidates = (
        root / "qmd.cmd",
        root / "qmd.exe",
        root / "bin" / "qmd",
        root / "qmd",
    )
    return next((path for path in candidates if _is_executable(path)), None)


def _is_executable(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def rebuild_checked_qmd_source(
    vault: Path, output_root: str = QMD_INPUT_ROOT, *, embeddings: bool = False
) -> dict[str, Any]:
    """Rebuild qmd's disposable input tree from checked retrieval documents."""
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
        "mode": "hybrid" if embeddings else "bm25",
        "embeddings": embeddings,
        "input_root": normalize_path(output_root),
        "documents": docs,
        "qmd_commands": [
            f"qmd collection add {normalize_path(output_root)} --name memoria-checked --mask '**/*.md'",
            "qmd update",
        ],
    }
    if embeddings:
        manifest["qmd_commands"].append("qmd embed --chunk-strategy auto")
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
            frontmatter = parse_frontmatter(safe_read(path))
            if _is_searchable_frontmatter(frontmatter, include_stale=include_stale):
                docs.append(path)
    return sorted(docs)


def filter_checked_results(vault: Path, rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter qmd-style JSON result rows to checked retrieval documents."""
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
    if rel.startswith(f"{QMD_INPUT_ROOT}/"):
        rel = rel.removeprefix(f"{QMD_INPUT_ROOT}/")
    if _is_checked_generated_work_document(vault, rel):
        return True
    path = Path(vault) / rel
    if (
        path.is_file()
        and is_consumable_checked_file(vault, rel)
        and _is_searchable_frontmatter(parse_frontmatter(safe_read(path)))
    ):
        return True
    qmd_path = Path(vault) / QMD_INPUT_ROOT / rel
    return (
        qmd_path.is_file()
        and is_consumable_checked_file(vault, rel)
        and _is_searchable_frontmatter(parse_frontmatter(safe_read(qmd_path)))
    )


def _is_checked_generated_work_document(vault: Path, rel: str) -> bool:
    if not rel.startswith(("works/", "graph-neighborhoods/")):
        return False
    source = state.catalog_source(vault, Path(rel).stem)
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
    docs = [
        (document["path"], document["text"], document["frontmatter"])
        for document in checked_search_documents(vault, include_stale=include_stale)
    ]
    project_context = _project_context(project_id, docs)
    retrieval_query = _project_query(query, project_context)
    qmd_hits = _qmd_query_hits(vault, retrieval_query, k=k, include_stale=include_stale)
    if qmd_hits is not None:
        frontmatter_by_path = {path: frontmatter for path, _text, frontmatter in docs}
        return _answer_from_hits(
            query,
            qmd_hits,
            frontmatter_by_path,
            engine="qmd",
            project_context=project_context,
        )
    tokenized = [(path, _tokens(text)) for path, text, _frontmatter in docs]
    frontmatter_by_path = {path: frontmatter for path, _text, frontmatter in docs}
    hits = _bm25(tokenized, retrieval_query)[:k]
    return _answer_from_hits(
        query, hits, frontmatter_by_path, engine="bm25", project_context=project_context
    )


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
        path_id = path.removesuffix(".md")
        aliases = {
            path,
            path_id,
            Path(path).stem,
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


def _qmd_query_hits(
    vault: Path, query: str, *, k: int, include_stale: bool
) -> list[tuple[str, float]] | None:
    qmd = resolve_qmd_executable()["path"]
    if not qmd or include_stale or not (vault / QMD_MANIFEST).is_file():
        return None
    text = " ".join(query.split())
    if not text:
        return []
    try:
        proc = subprocess.run(
            [
                qmd,
                "query",
                f"lex: {text}\nvec: {text}",
                "--no-rerank",
                "--format",
                "json",
                "-n",
                str(max(k * 3, k)),
                "-c",
                "memoria-checked",
            ],
            cwd=vault,
            env=_qmd_env(vault),
            check=False,
            text=True,
            capture_output=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return None
    if proc.returncode:
        return None
    try:
        rows = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return None
    if not isinstance(rows, list):
        return None
    hits: list[tuple[str, float]] = []
    seen: set[str] = set()
    for row in filter_checked_results(vault, (row for row in rows if isinstance(row, dict))):
        rel = qmd_result_path(row.get("file") or row.get("path") or "", vault)
        if rel.startswith(f"{QMD_INPUT_ROOT}/"):
            rel = rel.removeprefix(f"{QMD_INPUT_ROOT}/")
        if not rel or rel in seen:
            continue
        seen.add(rel)
        score = row.get("score")
        hits.append((rel, float(score) if isinstance(score, int | float) else 0.0))
        if len(hits) >= k:
            break
    return hits


def _qmd_env(vault: Path) -> dict[str, str]:
    env = dict(os.environ)
    root = vault / ".memoria/index/qmd"
    env["QMD_CONFIG_DIR"] = str(root / "config")
    env["INDEX_PATH"] = str(root / "index.sqlite")
    return env


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
    if frontmatter.get("type") not in {"work", "note", "hub", "project"}:
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
            "title": source["title"],
            "work_id": source_id,
            "tags": [],
            "links": {},
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
