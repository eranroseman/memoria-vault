"""Alpha.19 retrieval substrate checks and candidate ranking."""

from __future__ import annotations

import importlib.util
import json
import math
import re
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from memoria_vault.runtime import indexing, state
from memoria_vault.runtime.trusted_writer import OperationContext

SELECTED_RETRIEVAL_SUBSTRATE = "bm25"


@dataclass(frozen=True)
class Capability:
    available: bool
    reason: str = ""


def fts5_capability() -> Capability:
    try:
        with sqlite3.connect(":memory:") as conn:
            conn.execute("CREATE VIRTUAL TABLE t USING fts5(x)")
    except sqlite3.Error as exc:
        return Capability(False, str(exc))
    return Capability(True)


def sqlite_vec_capability() -> Capability:
    if importlib.util.find_spec("sqlite_vec") is None:
        return Capability(False, "sqlite-vec optional extra is not installed")
    return Capability(True)


def dense_substrate_capability() -> Capability:
    fts = fts5_capability()
    if not fts.available:
        return fts
    vec = sqlite_vec_capability()
    if not vec.available:
        return vec
    return Capability(True)


def fts_search(
    vault: Path, query: str, *, context: OperationContext, k: int = 10
) -> list[dict[str, Any]]:
    indexing.refresh_stale_passages(vault, context=context)
    match = _fts_query(query)
    if not match:
        return []
    with state.connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT p.path, p.passage_id, p.text, p.work_id, bm25(passage_fts) AS score
            FROM passage_fts
            JOIN passages p ON p.passage_id = passage_fts.passage_id
            WHERE passage_fts MATCH ?
              AND p.check_status = 'checked'
            ORDER BY score ASC, p.path
            LIMIT ?
            """,
            (match, k),
        ).fetchall()
    return [dict(row) for row in rows]


def vector_search(
    vault: Path, query: str, *, context: OperationContext, k: int = 10
) -> list[dict[str, Any]]:
    indexing.refresh_stale_passages(vault, context=context)
    query_vector = indexing.hash_embedding(query)
    with state.connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT p.path, p.passage_id, p.text, p.work_id, v.vector_json
            FROM passage_vec v
            JOIN passages p ON p.passage_id = v.passage_id
            WHERE p.check_status = 'checked'
              AND v.embedding_model_id = ?
              AND v.vector_dim = ?
            ORDER BY p.path
            """,
            (indexing.EMBEDDING_MODEL_ID, indexing.VECTOR_DIM),
        ).fetchall()
    scored = []
    for row in rows:
        vector = json.loads(str(row["vector_json"] or "[]"))
        score = _cosine(query_vector, vector)
        scored.append({**dict(row), "score": score})
    return sorted(scored, key=lambda row: (-float(row["score"]), str(row["path"])))[:k]


def hybrid_search(
    vault: Path, query: str, *, context: OperationContext, k: int = 10
) -> list[dict[str, Any]]:
    fts = fts_search(vault, query, k=k * 4, context=context)
    vectors = vector_search(vault, query, k=k * 4, context=context)
    scores: dict[str, float] = {}
    rows: dict[str, dict[str, Any]] = {}
    for ranking in (fts, vectors):
        for rank, row in enumerate(ranking, start=1):
            passage_id = str(row["passage_id"])
            scores[passage_id] = scores.get(passage_id, 0.0) + 1.0 / (60 + rank)
            rows[passage_id] = row
    return [
        {**rows[passage_id], "score": score}
        for passage_id, score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:k]
    ]


def evaluate_fixture(
    vault: Path,
    cases: Iterable[dict[str, Any]],
    *,
    context: OperationContext,
    k: int = 5,
) -> dict[str, Any]:
    from memoria_vault.runtime.search_index import evaluate_bm25

    cases = list(cases)
    bm25 = evaluate_bm25(vault, cases, k=k)
    variants = {
        "bm25": bm25,
        "fts5": _evaluate(fts_search, vault, cases, context=context, k=k),
    }
    if state.indexed_passages(vault):
        variants["vector"] = _evaluate(vector_search, vault, cases, context=context, k=k)
        variants["hybrid"] = _evaluate(hybrid_search, vault, cases, context=context, k=k)
    return {
        "selected": SELECTED_RETRIEVAL_SUBSTRATE,
        "dense_capability": dense_substrate_capability().__dict__,
        "variants": variants,
    }


def _evaluate(
    fn: Any,
    vault: Path,
    cases: list[dict[str, Any]],
    *,
    context: OperationContext,
    k: int,
) -> dict[str, Any]:
    results = []
    for case in cases:
        expected = {str(path) for path in case.get("relevant", [])}
        hits = [str(row["path"]) for row in fn(vault, str(case["query"]), k=k, context=context)]
        results.append(
            {
                "query": str(case["query"]),
                "hits": hits,
                "relevant": sorted(expected),
                "hit": bool(expected.intersection(hits)),
            }
        )
    total = len(results)
    hits = sum(1 for result in results if result["hit"])
    return {"queries": total, "hits": hits, "recall_at_k": hits / total if total else 0.0}


def _fts_query(query: str) -> str:
    terms = re.findall(r"[A-Za-z0-9]+", query.lower())
    return " OR ".join(terms)


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_mag = math.sqrt(sum(a * a for a in left))
    right_mag = math.sqrt(sum(b * b for b in right))
    return numerator / (left_mag * right_mag) if left_mag and right_mag else 0.0
