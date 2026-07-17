"""Contract tests for deterministic graph-SQL primitives (R2 design section 2)."""

from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

from memoria_vault.runtime import graph_sql, state

SHIPPED_RELATIONS = {"supports", "contradicts", "extends", "tension"}


def _seed_concept_edges(vault: Path) -> None:
    state.replace_concept_edges(
        vault,
        [
            {
                "source_concept_id": "notes/a.md",
                "relation_type": "supports",
                "target_concept_id": "notes/b.md",
                "check_status": "checked",
            },
            {
                "source_concept_id": "notes/b.md",
                "relation_type": "extends",
                "target_concept_id": "notes/c.md",
                "check_status": "checked",
            },
            {
                "source_concept_id": "notes/a.md",
                "relation_type": "contradicts",
                "target_concept_id": "notes/x.md",
                "check_status": "unchecked",
            },
        ],
    )
    # Tensions are PI-owned, so the mirror writer deliberately does not persist
    # them. Direct rows also cover parallel relations and the full check gate.
    with state.connect(vault) as conn:
        conn.executemany(
            "INSERT INTO concept_edges("
            " source_concept_id, relation_type, target_concept_id,"
            " check_status, source_path, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("notes/c.md", "tension", "notes/d.md", "checked", "", "2026-07-17T00:00:00Z"),
                (
                    "notes/a.md",
                    "contradicts",
                    "notes/b.md",
                    "checked",
                    "",
                    "2026-07-17T00:00:00Z",
                ),
                (
                    "notes/a.md",
                    "supports",
                    "notes/y.md",
                    "quarantined",
                    "",
                    "2026-07-17T00:00:00Z",
                ),
            ],
        )


def test_concept_edge_relations_matches_packaged_schema(tmp_path: Path) -> None:
    roster = graph_sql.concept_edge_relations(tmp_path)

    schema_text = files("memoria_vault.runtime").joinpath("schema.sql").read_text(encoding="utf-8")
    block = schema_text.split("CREATE TABLE IF NOT EXISTS concept_edges", 1)[1]
    match = re.search(r"relation_type\s+IN\s*\(([^)]*)\)", block)
    assert match is not None
    packaged = {value.strip().strip("'\"") for value in match.group(1).split(",") if value.strip()}

    assert roster == packaged
    assert SHIPPED_RELATIONS <= roster


def test_neighborhood_rejects_depth_beyond_cap(tmp_path: Path) -> None:
    for depth in (0, 3):
        try:
            graph_sql.neighborhood(tmp_path, ["notes/a.md"], depth=depth)
        except ValueError as exc:
            assert "hard cap 2" in str(exc)
        else:
            raise AssertionError(f"depth {depth} must be rejected naming the cap")


def test_neighborhood_rejects_unknown_relations(tmp_path: Path) -> None:
    try:
        graph_sql.neighborhood(tmp_path, ["notes/a.md"], relations={"refutes"})
    except ValueError as exc:
        assert "unknown concept edge relations" in str(exc)
    else:
        raise AssertionError("an unadmitted relation must be rejected")


def test_neighborhood_depth_one_walks_checked_edges_undirected(tmp_path: Path) -> None:
    _seed_concept_edges(tmp_path)

    forward = graph_sql.neighborhood(tmp_path, ["notes/a.md"], depth=1)
    assert forward["ids"] == ["notes/a.md", "notes/b.md"]
    assert forward["counts"] == {"seeds": 1, "neighbors": 1, "returned": 2}
    assert "notes/x.md" not in forward["ids"]
    assert "notes/y.md" not in forward["ids"]

    reverse = graph_sql.neighborhood(tmp_path, ["notes/b.md"], depth=1)
    assert reverse["ids"] == ["notes/a.md", "notes/b.md", "notes/c.md"]


def test_neighborhood_depth_two_reaches_two_hops(tmp_path: Path) -> None:
    _seed_concept_edges(tmp_path)

    result = graph_sql.neighborhood(tmp_path, ["notes/a.md"], depth=2)

    assert result["ids"] == ["notes/a.md", "notes/b.md", "notes/c.md"]
    assert result["counts"] == {"seeds": 1, "neighbors": 2, "returned": 3}


def test_neighborhood_relations_filter_restricts_expansion(tmp_path: Path) -> None:
    _seed_concept_edges(tmp_path)

    default = graph_sql.neighborhood(tmp_path, ["notes/c.md"], depth=1)
    assert default["ids"] == ["notes/b.md", "notes/c.md", "notes/d.md"]

    tension_only = graph_sql.neighborhood(tmp_path, ["notes/c.md"], depth=1, relations={"tension"})

    assert tension_only["ids"] == ["notes/c.md", "notes/d.md"]
    assert tension_only["counts"] == {"seeds": 1, "neighbors": 1, "returned": 2}


def test_neighborhood_empty_seeds_returns_empty_with_counts(tmp_path: Path) -> None:
    result = graph_sql.neighborhood(tmp_path, [])

    assert result == {"ids": [], "counts": {"seeds": 0, "neighbors": 0, "returned": 0}}


def _seed_work_graph(vault: Path) -> None:
    state.replace_work_graph_edges(
        vault,
        "alpha",
        [
            {"relation_type": "references", "target_id": "W:t1"},
            {"relation_type": "references", "target_id": "W:t2"},
            {"relation_type": "topic", "target_id": "memory"},
        ],
    )
    state.replace_work_graph_edges(
        vault,
        "beta",
        [
            {"relation_type": "references", "target_id": "W:t1"},
            {"relation_type": "references", "target_id": "W:t2"},
            {"relation_type": "references", "target_id": "W:t3"},
        ],
    )
    state.replace_work_graph_edges(
        vault,
        "gamma",
        [{"relation_type": "references", "target_id": "W:t3"}],
    )
    state.replace_work_graph_edges(
        vault,
        "delta",
        [
            {"relation_type": "topic", "target_id": "W:t1"},
            {"relation_type": "references", "target_id": "W:noise"},
            {"relation_type": "references", "target_id": "memory"},
        ],
    )


def test_co_citation_orders_by_shared_citing_works(tmp_path: Path) -> None:
    _seed_work_graph(tmp_path)

    result = graph_sql.co_citation(tmp_path, "W:t1")

    assert result["work_ids"] == ["W:t2", "W:t3"]
    assert result["counts"] == {"citing_works": 2, "co_cited": 2}
    assert "W:noise" not in result["work_ids"]


def test_coupling_orders_by_shared_references(tmp_path: Path) -> None:
    _seed_work_graph(tmp_path)

    result = graph_sql.coupling(tmp_path, "alpha")
    assert result["work_ids"] == ["beta"]
    assert result["counts"] == {"references": 2, "coupled": 1}
    assert "delta" not in result["work_ids"]

    both = graph_sql.coupling(tmp_path, "beta")
    assert both["work_ids"] == ["alpha", "gamma"]
    assert both["counts"] == {"references": 3, "coupled": 2}


def test_degree_centrality_returns_zero_for_isolated_ids(tmp_path: Path) -> None:
    _seed_concept_edges(tmp_path)

    degrees = graph_sql.degree_centrality(tmp_path, ["notes/a.md", "notes/b.md", "notes/zzz.md"])

    assert degrees == {"notes/a.md": 1, "notes/b.md": 2, "notes/zzz.md": 0}
    assert graph_sql.degree_centrality(tmp_path, []) == {}
