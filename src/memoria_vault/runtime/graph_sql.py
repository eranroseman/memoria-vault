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

import importlib
import json
import re
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.vaultio import read_frontmatter

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
            eligible_edges(origin_id, target_id) AS (
                SELECT edge.source_concept_id, edge.target_path
                FROM concept_edges AS edge
                LEFT JOIN concept_status AS source_status
                  ON source_status.concept_id = edge.source_path
                WHERE edge.check_status = 'checked'
                  AND edge.relation_type IN (SELECT value FROM json_each(?))
                  AND (
                      edge.source_path = ''
                      OR source_status.check_status = 'checked'
                  )
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
            (relations_json, seeds_json, depth),
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
                SELECT source_concept_id AS concept_id, target_path AS neighbor
                FROM concept_edges WHERE check_status = 'checked'
                UNION
                SELECT target_path AS concept_id, source_concept_id AS neighbor
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


def project_slice(vault: Path, project: str) -> dict[str, Any]:
    """Return concept ids in one project's slice without emitting a rank signal.

    Once graph propagation supplies active project slices, that authoritative
    mapping wins. Until then, use the project's own links closure.
    """
    vault = Path(vault)
    project_rel = _project_rel(vault, project)
    slices = _active_project_slices(vault)
    if slices is not None:
        ids = sorted({_member_id(row) for row in slices.get(project_rel, set())} - {""})
        return {
            "ids": ids,
            "counts": {"members": len(ids)},
            "source": "active-project-slices",
        }
    ids = _links_closure(vault, project_rel)
    return {"ids": ids, "counts": {"members": len(ids)}, "source": "links-closure"}


def _active_project_slices(vault: Path) -> dict[str, set[str]] | None:
    """Load the graph-owned active-slice producer only once it exists."""
    try:
        propagation = importlib.import_module("memoria_vault.runtime.propagation")
    except ModuleNotFoundError as exc:
        if exc.name == "memoria_vault.runtime.propagation":
            return None
        raise
    provider = getattr(propagation, "active_project_slices", None)
    return provider(vault) if callable(provider) else None


def _member_id(row: Any) -> str:
    if isinstance(row, dict):
        row = row.get("concept_id") or row.get("path") or row.get("id") or ""
    value = str(row).strip()
    return normalize_path(value) if value else ""


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


def _links_closure(vault: Path, project_rel: str) -> list[str]:
    frontmatter = read_frontmatter(vault / project_rel)
    seeds = _link_targets(frontmatter)
    thesis = _link_target(frontmatter.get("thesis"))
    if thesis:
        seeds.add(thesis)
    seen: set[str] = set()
    queue = sorted(seeds)
    while queue:
        rel = queue.pop(0)
        if rel in seen:
            continue
        seen.add(rel)
        path = vault / rel
        if not path.is_file():
            continue
        queue.extend(sorted(_link_targets(read_frontmatter(path)) - seen))
    return sorted(seen)


def _link_targets(frontmatter: dict[str, Any]) -> set[str]:
    links = frontmatter.get("links")
    if not isinstance(links, dict):
        return set()
    targets: set[str] = set()
    for values in links.values():
        for value in values if isinstance(values, list) else [values]:
            target = _link_target(value)
            if target:
                targets.add(target)
    return targets


def _link_target(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("target") or value.get("path") or value.get("id") or value.get("note")
    if not isinstance(value, str) or not value.strip():
        return ""
    raw = value.strip()
    if raw.startswith("[[") and raw.endswith("]]"):
        raw = raw[2:-2].split("|", 1)[0].split("#", 1)[0].strip()
    try:
        rel = normalize_path(raw)
    except ValueError:
        return ""
    if "/" not in rel:
        rel = f"notes/{rel}"
    if rel.startswith("catalog/sources/"):
        rel = rel.rstrip("/")
        if rel.count("/") != 2:
            return ""
    elif not rel.endswith(".md"):
        rel += ".md"
    if not rel.startswith(("catalog/sources/", "notes/", "hubs/", "digests/", "fulltexts/")):
        return ""
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
    with state.connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT concept_id, concept_type, check_status
            FROM concept_status
            WHERE concept_id IN (SELECT value FROM json_each(?))
            """,
            (json.dumps(wanted),),
        ).fetchall()
    known = {
        str(row["concept_id"]): (str(row["concept_type"]), str(row["check_status"])) for row in rows
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
