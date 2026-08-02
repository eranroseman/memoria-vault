"""Contract tests for deterministic graph-SQL primitives (R2 design section 2)."""

from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

import pytest

from memoria_vault.runtime import graph_sql, propagation, state

pytestmark = pytest.mark.contract

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


ULIDS = {
    "notes/a.md": "01JXAAAAAAAAAAAAAAAAAAAAAA",
    "notes/b.md": "01JXBBBBBBBBBBBBBBBBBBBBBB",
    "notes/c.md": "01JXCCCCCCCCCCCCCCCCCCCCCC",
    "notes/d.md": "01JXDDDDDDDDDDDDDDDDDDDDDD",
    "notes/z.md": "01JXZZZZZZZZZZZZZZZZZZZZZZ",
}


def _ulid_edge(
    source: str, relation: str, target: str, *, pi_owned: bool = False
) -> dict[str, str]:
    return {
        "source_concept_id": ULIDS.get(source, source),
        "relation_type": relation,
        "target_path": target,
        "check_status": "checked",
        "source_path": "" if pi_owned else source,
    }


def _seed_ulid_keyed_graph(vault: Path) -> None:
    """Seed the normal v16 shape, carrying every endpoint shape the producer projects.

    `neighborhood` re-implements `edges.concept_edge_path_records`'s projection in
    SQL, so this fixture carries the same endpoint shapes `tests/test_edges.py`
    seeds against the producer — a ULID source, a resolved target, a pending
    target that no Concept claims, a resolved target whose Concept renders
    nowhere, and a blank endpoint on each side. A sanctioned second
    implementation inherits the claim, not the coverage.
    """
    state.rebuild_file_concept_mirror(
        vault,
        [
            {"concept_id": ulid, "concept_type": "note", "path": path}
            for path, ulid in ULIDS.items()
        ],
    )
    for path in ("notes/a.md", "notes/b.md", "notes/z.md"):
        state.set_concept_verdict(vault, path, "checked")
    # A db-store Concept that renders nowhere. Its own edge is PI-owned
    # (`source_path = ''`), so the verdict gate exempts it and only the
    # blank-path guard can keep `''` out of the walk.
    with state.connect(vault) as conn:
        state.ensure_concept_parent_conn(
            conn, "cap-mv", concept_type="capability", store="db", path=""
        )
    state.replace_concept_edges(
        vault,
        [
            _ulid_edge("notes/a.md", "supports", "notes/b.md"),
            # Parallel relation between the same two Concepts: one neighbor.
            _ulid_edge("notes/a.md", "contradicts", "notes/b.md"),
            # A second distinct target, so `notes/a.md` — a source and never a
            # target — has a degree no self-count can reach.
            _ulid_edge("notes/a.md", "qualifier", "notes/c.md"),
            _ulid_edge("notes/b.md", "extends", "notes/c.md"),
            # Pending: no Concept claims this path, so only the durable
            # `target_path` can render it.
            _ulid_edge("notes/b.md", "warrant", "notes/pending.md"),
            # Resolved onto a Concept that renders nowhere: the durable
            # `target_path` is still the honest answer (the `NULLIF` arm).
            _ulid_edge("notes/b.md", "rebuttal", "cap-mv"),
            # Same shape as the others, but its source Concept carries no
            # `checked` verdict.
            _ulid_edge("notes/c.md", "supports", "notes/d.md"),
            _ulid_edge("cap-mv", "warrant", "notes/b.md", pi_owned=True),
            # Two blank targets from unrelated sources. Unguarded, `''` enters
            # the undirected walk as a hub and joins `notes/a.md` to a
            # `notes/z.md` it shares no edge with.
            _ulid_edge("notes/a.md", "rebuttal", ""),
            _ulid_edge("notes/z.md", "supports", ""),
        ],
    )
    # PI-owned, and written outside the mirror pass exactly as a confirmed
    # tension is — which is the one seam that can store an unnormalized durable
    # `target_path`. `notes/unwritten.md` is the id every consumer holds.
    with state.connect(vault) as conn:
        conn.execute(
            "INSERT INTO concept_edges("
            " source_concept_id, relation_type, target_concept_id, target_path,"
            " check_status, source_path, updated_at)"
            " VALUES (?, 'tension', NULL, './notes/unwritten.md', 'checked', '', ?)",
            (ULIDS["notes/z.md"], "2026-08-01T00:00:00Z"),
        )


def test_graph_primitives_serve_ulid_keyed_concepts_at_their_paths(tmp_path: Path) -> None:
    """The NID-B.2 regression these primitives owned: identity joined against path.

    A machine-authored note keys by its frontmatter ULID, so `source_concept_id`
    and `source_path` name the same Concept in two different spaces. Joining one
    against the other served no neighbours at all and leaked a raw ULID into a
    path-space result; `degree_centrality` counted one endpoint of each edge and
    `filter_ids` matched nothing.
    """
    _seed_ulid_keyed_graph(tmp_path)
    with state.connect(tmp_path) as conn:
        stored = {
            str(row["source_concept_id"])
            for row in conn.execute("SELECT source_concept_id FROM concept_edges")
        }
    # Not a degenerate fixture: no stored identity is its Concept's path.
    assert stored == {
        ULIDS["notes/a.md"],
        ULIDS["notes/b.md"],
        ULIDS["notes/c.md"],
        ULIDS["notes/z.md"],
        "cap-mv",
    }

    hood = graph_sql.neighborhood(tmp_path, ["notes/a.md"], depth=2)

    # Exact, so it is equally the proof of what is *not* here: no `''` hub, no
    # `notes/z.md` reached through one, no `notes/d.md` behind the unvetted
    # `notes/c.md`, and no raw identity.
    assert hood["ids"] == [
        "cap-mv",
        "notes/a.md",
        "notes/b.md",
        "notes/c.md",
        "notes/pending.md",
    ]
    assert hood["counts"] == {"seeds": 1, "neighbors": 4, "returned": 5}
    assert not set(hood["ids"]) & set(ULIDS.values())
    assert graph_sql.neighborhood(tmp_path, ["notes/a.md"], depth=1)["ids"] == [
        "notes/a.md",
        "notes/b.md",
        "notes/c.md",
    ]
    # The revoked-source gate still refuses, and in identity space: `notes/c.md`
    # holds no checked verdict, so its own mirrored edge to `notes/d.md` is not
    # walked, while the checked edges that reach it still are.
    assert graph_sql.neighborhood(tmp_path, ["notes/c.md"], depth=1)["ids"] == [
        "notes/a.md",
        "notes/b.md",
        "notes/c.md",
    ]
    # The stored `./notes/unwritten.md` reaches the walk through the one endpoint
    # rule, so it is walked — and returned — as the id consumers hold.
    assert graph_sql.neighborhood(tmp_path, ["notes/z.md"], depth=1)["ids"] == [
        "notes/unwritten.md",
        "notes/z.md",
    ]

    # No source gate here, as before ERP-A.6: `notes/d.md` keeps the degree its
    # checked-but-unvetted inbound edge gives it. `notes/a.md` is only ever a
    # source and `notes/c.md` only ever reached from two, so neither count is
    # satisfiable by counting the node itself.
    assert graph_sql.degree_centrality(
        tmp_path, ["notes/a.md", "notes/b.md", "notes/c.md", "notes/d.md", "notes/z.md"]
    ) == {
        "notes/a.md": 2,
        "notes/b.md": 4,
        "notes/c.md": 3,
        "notes/d.md": 1,
        "notes/z.md": 1,
    }

    assert graph_sql.filter_ids(tmp_path, ["notes/a.md", "notes/c.md"], types={"note"})["ids"] == [
        "notes/a.md",
        "notes/c.md",
    ]
    assert graph_sql.filter_ids(
        tmp_path, ["notes/a.md", "notes/c.md"], check_status={"checked"}
    ) == {"ids": ["notes/a.md"], "counts": {"before": 2, "after": 1}}
    # The identity arm: a Concept with no path is still found by the only handle
    # it has, and keyed back under it.
    assert graph_sql.filter_ids(tmp_path, ["cap-mv"], types={"capability"})["ids"] == ["cap-mv"]

    # An out-of-band rename moves `concepts.path` and leaves the edge's durable
    # `target_path` at the vacated path. The walk must serve the live rendering.
    state.rebuild_file_concept_mirror(
        tmp_path,
        [
            {"concept_id": ulid, "concept_type": "note", "path": path}
            for path, ulid in {**ULIDS, "notes/c-renamed.md": ULIDS["notes/c.md"]}.items()
            if path != "notes/c.md"
        ],
    )

    assert graph_sql.neighborhood(tmp_path, ["notes/a.md"], depth=2)["ids"] == [
        "cap-mv",
        "notes/a.md",
        "notes/b.md",
        "notes/c-renamed.md",
        "notes/pending.md",
    ]


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


def _write_note(vault: Path, rel: str, body: str) -> None:
    path = vault / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\ntype: note\n---\n{body}\n", encoding="utf-8")


def _seed_project_slice_graph(
    vault: Path,
    *,
    extra_concepts: tuple[str, ...] = (),
    extra_edges: tuple[dict[str, str], ...] = (),
) -> None:
    """One active project whose slice lives in the `concept_edges` mirror.

    The `links:` block on the project is deliberately kept and deliberately a
    lie: it names `notes/orphan.md`, which no mirror row connects. The slice is
    the propagation provider's closure now, so an orphan in the answer would
    mean retrieval had gone back to parsing frontmatter.

    Not a degenerate graph. `notes/b.md` is two hops out **and** points the
    other way, so a directed or one-hop walk fails here; `notes/pending.md`
    hangs off an unchecked edge, which separates this reader's unvetted default
    from `explore`'s vetted one.
    """
    (vault / "projects").mkdir(parents=True, exist_ok=True)
    (vault / "projects/p1.md").write_text(
        "---\ntype: project\nlinks:\n  supports:\n    - notes/orphan.md\n---\nbody\n",
        encoding="utf-8",
    )
    for name in ("a", "b", "pending", "orphan"):
        _write_note(vault, f"notes/{name}.md", name)
    for rel in extra_concepts:
        _write_note(vault, rel, Path(rel).stem)
    state.rebuild_file_concept_mirror(
        vault,
        [
            {"concept_id": "projects/p1.md", "concept_type": "project"},
            *(
                {"concept_id": rel, "concept_type": "note"}
                for rel in (
                    "notes/a.md",
                    "notes/b.md",
                    "notes/pending.md",
                    "notes/orphan.md",
                    *extra_concepts,
                )
            ),
        ],
    )
    state.replace_concept_edges(
        vault,
        [
            {
                "source_concept_id": "projects/p1.md",
                "relation_type": "supports",
                "target_concept_id": "notes/a.md",
                "check_status": "checked",
            },
            {
                "source_concept_id": "notes/b.md",
                "relation_type": "extends",
                "target_concept_id": "notes/a.md",
                "check_status": "checked",
            },
            {
                "source_concept_id": "notes/a.md",
                "relation_type": "supports",
                "target_concept_id": "notes/pending.md",
                "check_status": "unchecked",
            },
            *extra_edges,
        ],
    )


def test_project_slice_is_the_mirror_closure_minus_the_project_file(tmp_path: Path) -> None:
    """The sole provider is `propagation.active_project_slices` (graph contract 4).

    Two claims, and the second is the retrieval ruling this adapter owns. The
    membership answer is the mirror's undirected, transitive closure — not the
    project's `links:` frontmatter, which names an orphan no edge connects. And
    the project document, which the producer keeps in its closure by contract,
    is subtracted here: asking what is *in* p1 and being told "p1" is noise.
    """
    _seed_project_slice_graph(tmp_path)

    result = graph_sql.project_slice(tmp_path, "p1")

    # `notes/pending.md` rides an unchecked edge and is still a member: this
    # primitive is the unvetted read (`checked_only=False`, propagation's
    # default). `explore._vetted_project_slice_ids` is the one that passes True.
    assert result["ids"] == ["notes/a.md", "notes/b.md", "notes/pending.md"]
    assert result["counts"] == {"members": 3}
    assert result["source"] == "active-project-slices"
    # Both halves of the subtraction, so it cannot pass by the producer having
    # quietly dropped the container instead.
    assert propagation.active_project_slices(tmp_path)["projects/p1.md"] == {
        "projects/p1.md",
        *result["ids"],
    }


def test_project_slice_seeds_the_thesis_through_the_one_path_space_normalizer(
    tmp_path: Path,
) -> None:
    """`thesis:` is path space with one normalizer (issue #1623), observed at retrieval.

    `edges.thesis_rel` owns the rule and `test_query_substrate` pins its table;
    this is the retrieval-side observer of the seed reaching the answer. The
    thesis note is connected to nothing else, so `thesis:` is the only way in.

    A title and a bare `.` resolve to nothing, and the answer is then `[]` — not
    `["projects/title.md"]`. That is the project-file subtraction and the
    normalizer meeting: without the subtraction a junk thesis would still return
    a one-member slice, which reads as a hit.
    """
    (tmp_path / "projects").mkdir(parents=True, exist_ok=True)
    for name, thesis in (
        ("bare", "thesis"),
        ("wikilink", "'[[notes/thesis]]'"),
        ("title", "'Toulmin: the warrant'"),
        ("dot", "'.'"),
    ):
        (tmp_path / f"projects/{name}.md").write_text(
            f"---\ntype: project\nthesis: {thesis}\n---\nbody\n", encoding="utf-8"
        )
    _write_note(tmp_path, "notes/thesis.md", "thesis")
    _write_note(tmp_path, "notes/support.md", "support")
    state.rebuild_file_concept_mirror(
        tmp_path,
        [
            {"concept_id": "notes/thesis.md", "concept_type": "note"},
            {"concept_id": "notes/support.md", "concept_type": "note"},
        ],
    )
    state.replace_concept_edges(
        tmp_path,
        [
            {
                "source_concept_id": "notes/thesis.md",
                "relation_type": "extends",
                "target_concept_id": "notes/support.md",
                "check_status": "checked",
            }
        ],
    )

    assert graph_sql.project_slice(tmp_path, "bare")["ids"] == [
        "notes/support.md",
        "notes/thesis.md",
    ]
    assert graph_sql.project_slice(tmp_path, "wikilink")["ids"] == [
        "notes/support.md",
        "notes/thesis.md",
    ]
    assert graph_sql.project_slice(tmp_path, "title")["ids"] == []
    assert graph_sql.project_slice(tmp_path, "dot")["ids"] == []


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
    """Each of the three stages removes something no other stage would.

    `notes/z.md` and `notes/w.md` are a second component, seeded so the slice
    has real work to do: with one component the neighborhood is always a subset
    of its own project's closure and the intersection is a no-op that any
    mutant survives. The neighborhood drops `notes/pending.md` (unchecked
    edge), the slice drops the second component, and the filter drops the
    unchecked Concept.
    """
    _seed_project_slice_graph(
        tmp_path,
        extra_concepts=("notes/z.md", "notes/w.md"),
        extra_edges=(
            {
                "source_concept_id": "notes/z.md",
                "relation_type": "supports",
                "target_concept_id": "notes/w.md",
                "check_status": "checked",
            },
        ),
    )
    state.set_concept_verdict(tmp_path, "notes/a.md", "checked")

    hood = graph_sql.neighborhood(tmp_path, ["notes/a.md", "notes/z.md"], depth=2)
    sliced = sorted(set(hood["ids"]) & set(graph_sql.project_slice(tmp_path, "p1")["ids"]))
    final = graph_sql.filter_ids(tmp_path, sliced, check_status={"checked"})

    assert hood["ids"] == [
        "notes/a.md",
        "notes/b.md",
        "notes/w.md",
        "notes/z.md",
        "projects/p1.md",
    ]
    assert sliced == ["notes/a.md", "notes/b.md"]
    assert final["ids"] == ["notes/a.md"]
    assert final["counts"] == {"before": 2, "after": 1}
