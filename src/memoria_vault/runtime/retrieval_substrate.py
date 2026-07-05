"""Retrieval-substrate selection and the alpha.15 spike helpers."""

from __future__ import annotations

import re
import sqlite3
from collections import defaultdict
from typing import Any

SELECTED_RETRIEVAL_SUBSTRATE = "bm25"
RETRIEVAL_SUBSTRATE_VERDICT = {
    "selected": SELECTED_RETRIEVAL_SUBSTRATE,
    "cleared_replacement_bar": False,
    "date": "2026-07-02",
    "reason": (
        "The packaged product uses deterministic checked-only BM25 search. "
        "Semantic and hybrid retrieval remain future work until a local vector "
        "pipeline ships as product code."
    ),
}


def sqlite_fts5_available() -> bool:
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE VIRTUAL TABLE docs USING fts5(path, body)")
    except sqlite3.Error:
        return False
    finally:
        conn.close()
    return True


def evaluate_fts5_fixture(fixture: dict[str, Any], *, k: int = 3) -> dict[str, Any]:
    groups: dict[str, list[bool]] = defaultdict(list)
    results = []
    docs = fixture.get("documents") or []
    cases = fixture.get("cases") or []
    if not sqlite_fts5_available():
        return {"engine": "sqlite-fts5", "available": False, "recall_by_slice": {}, "results": []}

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE VIRTUAL TABLE docs USING fts5(path UNINDEXED, body)")
    conn.executemany(
        "INSERT INTO docs(path, body) VALUES (?, ?)",
        [(str(doc["path"]), str(doc["body"])) for doc in docs],
    )
    for case in cases:
        query = _fts5_query(str(case["query"]))
        hits = _fts5_hits(conn, query, k=k) if query else []
        expected = {str(path) for path in case.get("relevant") or []}
        hit = bool(expected.intersection(hits))
        groups[str(case["slice"])].append(hit)
        results.append(
            {
                "slice": str(case["slice"]),
                "query": str(case["query"]),
                "hits": hits,
                "relevant": sorted(expected),
                "hit": hit,
            }
        )
    conn.close()
    return {
        "engine": "sqlite-fts5",
        "available": True,
        "recall_by_slice": {
            group: sum(values) / len(values) if values else 0.0 for group, values in groups.items()
        },
        "results": results,
    }


def _fts5_hits(conn: sqlite3.Connection, query: str, *, k: int) -> list[str]:
    rows = conn.execute(
        "SELECT path FROM docs WHERE docs MATCH ? ORDER BY bm25(docs) LIMIT ?",
        (query, k),
    ).fetchall()
    return [str(row[0]) for row in rows]


def _fts5_query(query: str) -> str:
    return " ".join(re.findall(r"[A-Za-z0-9_]+", query.lower()))
