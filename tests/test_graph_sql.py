"""Contract tests for deterministic graph-SQL primitives (R2 design section 2)."""

from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

import pytest

from memoria_vault.runtime import graph_sql, state

SHIPPED_RELATIONS = {"supports", "contradicts", "extends", "tension"}


def _seed_concept_edges(vault: Path) -> None:
    # v16 edges are FK-backed, so every endpoint needs its Concept parent first.
    state.rebuild_file_concept_mirror(
        vault,
        [
            {"concept_id": f"notes/{name}.md", "concept_type": "note"}
            for name in ("a", "b", "c", "d", "x", "y")
        ],
    )
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
            " source_concept_id, relation_type, target_concept_id, target_path,"
            " check_status, source_path, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    "notes/c.md",
                    "tension",
                    "notes/d.md",
                    "notes/d.md",
                    "checked",
                    "",
                    "2026-07-17T00:00:00Z",
                ),
                (
                    "notes/a.md",
                    "contradicts",
                    "notes/b.md",
                    "notes/b.md",
                    "checked",
                    "",
                    "2026-07-17T00:00:00Z",
                ),
                (
                    "notes/a.md",
                    "supports",
                    "notes/y.md",
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


def test_neighborhood_rejects_stale_checked_mirror_edges_for_revoked_source(tmp_path: Path) -> None:
    state.rebuild_file_concept_mirror(
        tmp_path,
        [
            {"concept_id": "notes/a.md", "concept_type": "note"},
            {"concept_id": "notes/b.md", "concept_type": "note"},
            {"concept_id": "notes/c.md", "concept_type": "note"},
        ],
    )
    state.set_concept_verdict(tmp_path, "notes/b.md", "unchecked")
    state.replace_concept_edges(
        tmp_path,
        [
            {
                "source_concept_id": "notes/b.md",
                "relation_type": "supports",
                "target_concept_id": "notes/a.md",
                "check_status": "checked",
                "source_path": "notes/b.md",
            },
            {
                "source_concept_id": "notes/b.md",
                "relation_type": "supports",
                "target_concept_id": "notes/c.md",
                "check_status": "checked",
                "source_path": "notes/b.md",
            },
        ],
    )

    assert graph_sql.neighborhood(tmp_path, ["notes/a.md"], depth=2)["ids"] == ["notes/a.md"]


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


def _seed_project_files(vault: Path) -> None:
    (vault / "projects").mkdir(exist_ok=True)
    (vault / "notes").mkdir(exist_ok=True)
    (vault / "projects/p1.md").write_text(
        "---\ntype: project\nlinks:\n  supports:\n    - notes/a.md\n"
        "    - archive/legacy.md\n    - '../../outside.md'\n---\nbody\n",
        encoding="utf-8",
    )
    (vault / "notes/a.md").write_text(
        "---\ntype: note\nlinks:\n  extends:\n    - '[[b]]'\n---\nalpha\n",
        encoding="utf-8",
    )
    (vault / "notes/b.md").write_text("---\ntype: note\n---\nbeta\n", encoding="utf-8")
    (vault / "notes/orphan.md").write_text("---\ntype: note\n---\norphan\n", encoding="utf-8")


def test_project_slice_falls_back_to_links_closure(tmp_path: Path) -> None:
    _seed_project_files(tmp_path)

    result = graph_sql.project_slice(tmp_path, "p1")

    # [[b]] resolves to notes/b.md. Unsupported and escaping targets are ignored,
    # and the unlinked orphan note stays outside the project's links closure.
    assert result["ids"] == ["notes/a.md", "notes/b.md"]
    assert result["counts"] == {"members": 2}
    assert result["source"] == "links-closure"


def test_project_slice_prefers_active_project_slices_seam(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_project_files(tmp_path)
    monkeypatch.setattr(
        graph_sql,
        "_active_project_slices",
        lambda vault: {"projects/p1.md": {"notes/z.md"}},
    )

    result = graph_sql.project_slice(tmp_path, "p1")

    assert result["ids"] == ["notes/z.md"]
    assert result["counts"] == {"members": 1}
    assert result["source"] == "active-project-slices"


def test_filter_ids_prunes_by_type_and_check_status(tmp_path: Path) -> None:
    state.rebuild_file_concept_mirror(
        tmp_path,
        [
            {"concept_id": "notes/a.md", "concept_type": "note"},
            {"concept_id": "notes/b.md", "concept_type": "note"},
            {"concept_id": "digests/d.md", "concept_type": "digest"},
        ],
    )
    state.set_concept_verdict(tmp_path, "notes/a.md", "checked")

    typed = graph_sql.filter_ids(
        tmp_path, ["notes/a.md", "notes/b.md", "digests/d.md"], types={"note"}
    )
    assert typed["ids"] == ["notes/a.md", "notes/b.md"]
    assert typed["counts"] == {"before": 3, "after": 2}

    checked = graph_sql.filter_ids(
        tmp_path, ["notes/a.md", "notes/b.md", "notes/ghost.md"], check_status={"checked"}
    )
    assert checked["ids"] == ["notes/a.md"]
    assert checked["counts"] == {"before": 3, "after": 1}

    assert graph_sql.filter_ids(tmp_path, []) == {
        "ids": [],
        "counts": {"before": 0, "after": 0},
    }


def test_primitives_compose_neighborhood_slice_filter(tmp_path: Path) -> None:
    _seed_concept_edges(tmp_path)
    _seed_project_files(tmp_path)
    state.rebuild_file_concept_mirror(
        tmp_path,
        [
            {"concept_id": "notes/a.md", "concept_type": "note"},
            {"concept_id": "notes/b.md", "concept_type": "note"},
            {"concept_id": "notes/c.md", "concept_type": "note"},
        ],
    )
    state.set_concept_verdict(tmp_path, "notes/a.md", "checked")

    hood = graph_sql.neighborhood(tmp_path, ["notes/a.md"], depth=2)
    sliced = sorted(set(hood["ids"]) & set(graph_sql.project_slice(tmp_path, "p1")["ids"]))
    final = graph_sql.filter_ids(tmp_path, sliced, check_status={"checked"})

    assert hood["counts"]["returned"] == 3
    assert sliced == ["notes/a.md", "notes/b.md"]
    assert final["ids"] == ["notes/a.md"]
    assert final["counts"] == {"before": 2, "after": 1}


def test_links_closure_ignores_targets_the_validator_rejects(tmp_path: Path) -> None:
    """The reader and the validator must agree on what a link target is.

    `notes/../secret.md` and `notes/a[1]` both fail `links` validation, yet the
    closure used to follow the first into a real note (path normalization
    collapses the `..` while staying inside the vault) and invent the second.
    """
    (tmp_path / "projects").mkdir(exist_ok=True)
    (tmp_path / "notes").mkdir(exist_ok=True)
    (tmp_path / "projects/p2.md").write_text(
        "---\ntype: project\nlinks:\n  supports:\n    - notes/../secret.md\n"
        "    - notes/a[1]\n    - notes/plain.md\n---\nbody\n",
        encoding="utf-8",
    )
    (tmp_path / "notes/secret.md").write_text("---\ntype: note\n---\nsecret\n", encoding="utf-8")
    (tmp_path / "notes/plain.md").write_text("---\ntype: note\n---\nplain\n", encoding="utf-8")

    result = graph_sql.project_slice(tmp_path, "p2")

    assert result["ids"] == ["notes/plain.md"]
    assert result["source"] == "links-closure"
