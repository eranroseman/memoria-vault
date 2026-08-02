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

from memoria_vault.runtime import propagation, state
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.subsystems.lib.edges import (
    concept_edge_path_pairs,
    projected_edge_endpoints,
)

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
    # Eligibility in SQL, endpoints through the one projection rule. The first
    # query is the part `edges.concept_edge_path_pairs` cannot serve: it needs the
    # edge's own `source_path` (blank marks a PI-owned row, which no verdict
    # gates) and the source Concept's verdict, two columns the strict endpoint API
    # deliberately withholds, and it cannot re-derive them from a projected triple
    # because two edge rows can project to the same one. Identity is matched
    # against identity — `source_status.concept_id` against
    # `edge.source_concept_id`, never against a path — which is the ERP-A.6
    # correction to the NID-B.2 join.
    #
    # Everything after that is `edges.projected_edge_endpoints`, the same call the
    # producer makes on every row it returns. It is a call and not a second copy
    # of the rule because both escapes this walk shipped were exactly that: a
    # blank endpoint the producer dropped and this copy did not, and a stored
    # `./notes/x.md` the producer normalized and this copy did not — each one
    # putting a second id for one Concept into a path-space answer.
    with state.connect(vault) as conn:
        eligible = conn.execute(
            """
            SELECT source_status.path AS source_path,
                   COALESCE(NULLIF(target.path, ''), edge.target_path) AS target_path
            FROM concept_edges AS edge
            JOIN concept_status AS source_status
              ON source_status.concept_id = edge.source_concept_id
            LEFT JOIN concepts AS target
              ON target.concept_id = edge.target_concept_id
            WHERE edge.check_status = 'checked'
              AND edge.relation_type IN (SELECT value FROM json_each(?))
              AND (
                  edge.source_path = ''
                  OR source_status.check_status = 'checked'
              )
            """,
            (relations_json,),
        ).fetchall()
        adjacency = json.dumps(
            [
                list(endpoints)
                for row in eligible
                if (endpoints := projected_edge_endpoints(row["source_path"], row["target_path"]))
                is not None
            ]
        )
        rows = conn.execute(
            """
            WITH RECURSIVE
            eligible_edges(origin_id, target_id) AS (
                SELECT json_extract(value, '$[0]'), json_extract(value, '$[1]')
                FROM json_each(?)
            ),
            edges(origin_id, target_id) AS (
                SELECT origin_id, target_id
                FROM eligible_edges
                UNION
                SELECT target_id, origin_id
                FROM eligible_edges
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
            (adjacency, seeds_json, depth),
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
    # Both endpoints come from the one graph-owned path projection, so a ULID
    # source and a bare `work_id` source are counted at the paths their callers
    # know them by. Parallel relations between the same two Concepts are one
    # neighbor, which is what the pre-ERP-A.6 `UNION` + `COUNT(DISTINCT …)` said.
    neighbors: dict[str, set[str]] = {value: set() for value in wanted}
    for pair in concept_edge_path_pairs(vault):
        source, target = pair["source_path"], pair["target_path"]
        if source in neighbors:
            neighbors[source].add(target)
        if target in neighbors:
            neighbors[target].add(source)
    return {value: len(neighbors[value]) for value in wanted}


def project_slice(vault: Path, project: str) -> dict[str, Any]:
    """Return concept ids in one project's slice without emitting a rank signal.

    `propagation.active_project_slices` is the sole provider (graph contract 4):
    path space on both sides, so the project key this resolves and the member
    paths it returns are the same namespace `neighborhood` and `filter_ids`
    answer in. The project document is subtracted because retrieval asks *what
    is in* the project — the producer keeps the container in its closure, which
    is right for a cascade's reach and noise in an answer.
    """
    vault = Path(vault)
    project_rel = _project_rel(vault, project)
    members = propagation.active_project_slices(vault).get(project_rel, set())
    ids = sorted(members - {project_rel})
    return {
        "ids": ids,
        "counts": {"members": len(ids)},
        "source": "active-project-slices",
    }


def _project_rel(vault: Path, project: str) -> str:
    rel = normalize_path(str(project))
    if "/" not in rel:
        nested = f"projects/{rel}/project.md"
        return nested if (vault / nested).is_file() else f"projects/{rel}.md"
    if not rel.endswith(".md"):
        rel += ".md"
    if not rel.startswith("projects/"):
        raise ValueError(f"project must live under projects: {rel}")
    return rel


def filter_ids(
    vault: Path,
    ids: list[str],
    *,
    types: set[str] | None = None,
    check_status: set[str] | None = None,
) -> dict[str, Any]:
    """Prune ids by concept type and/or status from the concept status view."""
    wanted = list(dict.fromkeys(normalize_path(str(value)) for value in ids if str(value).strip()))
    if not wanted:
        return {"ids": [], "counts": {"before": 0, "after": 0}}
    if types is None and check_status is None:
        return {"ids": wanted, "counts": {"before": len(wanted), "after": len(wanted)}}
    # Path space in, path space out: these ids are the ones `neighborhood` and
    # `project_slice` return, so a Concept is found by its `concepts.path`
    # rendering and keyed back by it. The `concept_id` arm is what still finds a
    # db-store Concept that renders nowhere, and is the only reason a caller
    # holding such an id keeps working; it is not a licence to pass a ULID.
    with state.connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT concept_id, path, concept_type, check_status
            FROM concept_status
            WHERE path IN (SELECT value FROM json_each(?))
               OR concept_id IN (SELECT value FROM json_each(?))
            """,
            (json.dumps(wanted), json.dumps(wanted)),
        ).fetchall()
    known = {
        str(row["path"] or row["concept_id"]): (
            str(row["concept_type"]),
            str(row["check_status"]),
        )
        for row in rows
    }
    kept = []
    for concept_id in wanted:
        concept_type, status = known.get(concept_id, ("", "unchecked"))
        if types is not None and concept_type not in types:
            continue
        if check_status is not None and status not in check_status:
            continue
        kept.append(concept_id)
    return {"ids": kept, "counts": {"before": len(wanted), "after": len(kept)}}
