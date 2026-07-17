"""Deterministic graph-SQL primitives for structural retrieval (R2 design, section 2).

Set-shaped returns, no model judgment: every set-building primitive returns
``{"ids": [...], "counts": {...}}`` so denominators are built where sets are
built (design section 4). Structural output is a filter + expander, never a
ranker — nothing here emits a rank signal or enters fusion.

The concept-edge extraction dependency is satisfied by Plan 22 G2S1.1. Tests
seed persisted rows directly, including a PI-owned tension edge which the
normal mirror writer intentionally leaves untouched.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.policy.paths import normalize_path

DEPTH_CAP = 2

_RELATION_CHECK_RE = re.compile(r"relation_type\s+IN\s*\(([^)]*)\)", re.IGNORECASE)


def concept_edge_relations(vault: Path) -> set[str]:
    """Return relation types the live ``concept_edges`` CHECK admits."""
    with state.connect(vault) as conn:
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'concept_edges'"
        ).fetchone()
    match = _RELATION_CHECK_RE.search(str(row["sql"])) if row is not None else None
    if match is None:
        raise ValueError("concept_edges relation CHECK not found")
    return {value.strip().strip("'\"") for value in match.group(1).split(",") if value.strip()}


def neighborhood(
    vault: Path,
    seeds: list[str],
    *,
    depth: int = 1,
    relations: set[str] | None = None,
) -> dict[str, Any]:
    """Return seed ids and their checked, undirected graph neighborhood.

    This is a filter + expander with zero rank signal. Edges are walked from
    either endpoint. By default every live-admitted relation is included, so
    tensions remain first-class retrievable.
    """
    if not 1 <= depth <= DEPTH_CAP:
        raise ValueError(
            f"depth must be between 1 and {DEPTH_CAP} (hard cap {DEPTH_CAP}), got {depth}"
        )
    admitted = concept_edge_relations(vault)
    chosen = admitted if relations is None else set(relations)
    unknown = chosen - admitted
    if unknown:
        raise ValueError(f"unknown concept edge relations: {sorted(unknown)}")
    seed_ids = sorted({normalize_path(str(seed)) for seed in seeds if str(seed).strip()})
    if not seed_ids:
        return {"ids": [], "counts": {"seeds": 0, "neighbors": 0, "returned": 0}}
    relations_json = json.dumps(sorted(chosen))
    seeds_json = json.dumps(seed_ids)
    with state.connect(vault) as conn:
        rows = conn.execute(
            """
            WITH RECURSIVE
            edges(origin_id, target_id) AS (
                SELECT source_concept_id, target_concept_id
                FROM concept_edges
                WHERE check_status = 'checked'
                  AND relation_type IN (SELECT value FROM json_each(?))
                UNION
                SELECT target_concept_id, source_concept_id
                FROM concept_edges
                WHERE check_status = 'checked'
                  AND relation_type IN (SELECT value FROM json_each(?))
            ),
            walk(concept_id, hops) AS (
                SELECT value, 0 FROM json_each(?)
                UNION
                SELECT edges.target_id, walk.hops + 1
                FROM edges
                JOIN walk ON walk.concept_id = edges.origin_id
                WHERE walk.hops < ?
            )
            SELECT DISTINCT concept_id FROM walk ORDER BY concept_id
            """,
            (relations_json, relations_json, seeds_json, depth),
        ).fetchall()
    ids = [str(row["concept_id"]) for row in rows]
    return {
        "ids": ids,
        "counts": {
            "seeds": len(seed_ids),
            "neighbors": len(ids) - len(seed_ids),
            "returned": len(ids),
        },
    }


def co_citation(vault: Path, work_id: str) -> dict[str, Any]:
    """Return works cited together with ``work_id`` by vault citing works."""
    target = str(work_id).strip()
    with state.connect(vault) as conn:
        citing = conn.execute(
            """
            SELECT COUNT(DISTINCT work_id) AS n
            FROM work_graph_edges
            WHERE relation_type = 'references' AND target_id = ?
            """,
            (target,),
        ).fetchone()
        rows = conn.execute(
            """
            SELECT other.target_id AS co_cited_id,
                   COUNT(DISTINCT other.work_id) AS shared
            FROM work_graph_edges AS anchor
            JOIN work_graph_edges AS other
              ON other.work_id = anchor.work_id
             AND other.relation_type = 'references'
             AND other.target_id <> anchor.target_id
            WHERE anchor.relation_type = 'references' AND anchor.target_id = ?
            GROUP BY other.target_id
            ORDER BY shared DESC, other.target_id
            """,
            (target,),
        ).fetchall()
    work_ids = [str(row["co_cited_id"]) for row in rows]
    return {
        "work_ids": work_ids,
        "counts": {"citing_works": int(citing["n"]), "co_cited": len(work_ids)},
    }


def coupling(vault: Path, work_id: str) -> dict[str, Any]:
    """Return vault works bibliographically coupled to ``work_id``."""
    source = str(work_id).strip()
    with state.connect(vault) as conn:
        references = conn.execute(
            """
            SELECT COUNT(DISTINCT target_id) AS n
            FROM work_graph_edges
            WHERE relation_type = 'references' AND work_id = ?
            """,
            (source,),
        ).fetchone()
        rows = conn.execute(
            """
            SELECT other.work_id AS coupled_id,
                   COUNT(DISTINCT other.target_id) AS shared
            FROM work_graph_edges AS anchor
            JOIN work_graph_edges AS other
              ON other.target_id = anchor.target_id
             AND other.relation_type = 'references'
             AND other.work_id <> anchor.work_id
            WHERE anchor.relation_type = 'references' AND anchor.work_id = ?
            GROUP BY other.work_id
            ORDER BY shared DESC, other.work_id
            """,
            (source,),
        ).fetchall()
    work_ids = [str(row["coupled_id"]) for row in rows]
    return {
        "work_ids": work_ids,
        "counts": {"references": int(references["n"]), "coupled": len(work_ids)},
    }


def degree_centrality(vault: Path, ids: list[str]) -> dict[str, int]:
    """Return checked, distinct-neighbor degree for each requested id.

    This only orders an expansion when a cap applies. It is never a relevance
    score and never enters fusion.
    """
    wanted = list(dict.fromkeys(normalize_path(str(value)) for value in ids if str(value).strip()))
    if not wanted:
        return {}
    with state.connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT concept_id, COUNT(DISTINCT neighbor) AS degree FROM (
                SELECT source_concept_id AS concept_id, target_concept_id AS neighbor
                FROM concept_edges WHERE check_status = 'checked'
                UNION
                SELECT target_concept_id AS concept_id, source_concept_id AS neighbor
                FROM concept_edges WHERE check_status = 'checked'
            )
            WHERE concept_id IN (SELECT value FROM json_each(?))
            GROUP BY concept_id
            """,
            (json.dumps(wanted),),
        ).fetchall()
    degrees = dict.fromkeys(wanted, 0)
    degrees.update({str(row["concept_id"]): int(row["degree"]) for row in rows})
    return degrees
