from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

from memoria_vault.runtime import graph_sql, indexing, retrieval, state
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.search_index import answer_query as _answer_query
from memoria_vault.runtime.subsystems.lib import schema
from memoria_vault.runtime.trusted_writer import promote_checked as _promote_checked
from memoria_vault.runtime.trusted_writer import stage_concept as _stage_concept
from memoria_vault.runtime.vaultio import safe_read
from tests.helpers import (
    call_with_context,
    copy_memoria_dirs,
    init_git,
    mark_file_status,
    write_checked_concept,
)


def answer_query(vault: Path, *args, **kwargs):
    return call_with_context(_answer_query, vault, *args, **kwargs)


def rebuild_passage_index(vault: Path, *args, **kwargs):
    return call_with_context(indexing.rebuild_passage_index, vault, *args, **kwargs)


def stage_concept(vault: Path, *args, **kwargs):
    return call_with_context(_stage_concept, vault, *args, **kwargs)


def promote_checked(vault: Path, *args, **kwargs):
    return call_with_context(_promote_checked, vault, *args, **kwargs)


def test_schema_creates_query_tables_and_rejects_v7(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        names = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
            ).fetchall()
        }

    assert state.SCHEMA_VERSION == 16
    assert {
        "passages",
        "passage_fts",
        "passage_vec",
        "file_index_state",
        "concept_edges",
        "code_artifacts",
        "code_runs",
    }.issubset(names)

    legacy = tmp_path / "legacy"
    db = legacy / state.DB_REL
    db.parent.mkdir(parents=True)
    with sqlite3.connect(db) as conn:
        conn.execute("PRAGMA user_version = 7")
    with pytest.raises(RuntimeError, match="unsupported Memoria DB schema version: 7"):
        state.connect(legacy)


def test_passage_index_refreshes_stale_file_and_cascades_status(tmp_path: Path) -> None:
    vault = tmp_path
    copy_memoria_dirs(vault, "schemas")
    write_checked_concept(
        vault,
        "notes/alpha.md",
        "type: note\ntitle: Alpha\ntags: []\nlinks: {}\n",
        body="rarealpha first version",
    )

    rebuild_passage_index(vault)
    assert state.indexed_passages(vault, checked_only=True)[0]["text"].endswith(
        "rarealpha first version\n"
    )

    path = vault / "notes/alpha.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("first version", "second version"),
        encoding="utf-8",
    )
    mark_file_status(vault, "notes/alpha.md")
    answer = answer_query(vault, "rarealpha")

    assert answer["engine"] == "bm25"
    assert state.file_index_states(vault)["notes/alpha.md"]["source_sha256"] == sha256_file(path)
    assert state.indexed_passages(vault, checked_only=True)[0]["text"].endswith(
        "rarealpha second version\n"
    )

    state.set_concept_verdict(vault, "notes/alpha.md", "unchecked")
    assert state.indexed_passages(vault)[0]["check_status"] == "unchecked"
    assert state.indexed_passages(vault, checked_only=True) == []


def test_retrieval_fixture_keeps_bm25_selected_and_vector_optional(tmp_path: Path) -> None:
    vault = tmp_path
    copy_memoria_dirs(vault, "schemas")
    write_checked_concept(
        vault,
        "notes/alpha.md",
        "type: note\ntitle: Alpha\ntags: []\nlinks: {}\n",
        body="retrieval fixture rarealpha token",
    )
    rebuild_passage_index(vault)

    report = call_with_context(
        retrieval.evaluate_fixture,
        vault,
        [{"query": "rarealpha", "relevant": ["notes/alpha.md"]}],
    )

    assert report["selected"] == "bm25"
    assert report["variants"]["bm25"]["recall_at_k"] == 1.0
    assert report["variants"]["fts5"]["recall_at_k"] == 1.0
    assert report["dense_capability"]["available"] is False


def test_parse_links_normalizes_alias_anchor_and_keeps_bare_concept_targets() -> None:
    links = {
        "supports": [
            "[[notes/gamma.md#Evidence|Gamma]]",
            "[[notes/beta]]",
            "notes/delta",
        ]
    }
    note = schema.load_types()["note"]

    assert schema.normalize_link_target("[[notes/gamma.md#Evidence|Gamma]]") == "notes/gamma.md"
    assert schema.parse_links(links) == [
        ("supports", "notes/gamma.md"),
        ("supports", "notes/beta"),
        ("supports", "notes/delta"),
    ]
    assert schema.parse_links({"tension": ["notes/ignored"], "extends": "notes/ignored"}) == []
    assert (
        schema.validate_frontmatter(
            {
                "id": "01KBN6V6KX0000000000000001",
                "type": "note",
                "title": "T",
                "tags": [],
                "links": links,
            },
            note,
        )
        == []
    )


@pytest.mark.parametrize(
    ("target", "message"),
    [
        ("[[notes/broken", "expected local Concept target"),
        ("notes/../escape", "target must not escape the workspace"),
        ("/notes/absolute", "expected local Concept target"),
        ("https://example.test/concept", "expected local Concept target"),
        ("notes/target.txt", "expected local Concept target"),
        ("notes/target.md/", "expected local Concept target"),
        ("#Evidence", "expected local Concept target"),
    ],
)
def test_link_parser_and_validation_reject_invalid_local_targets(target: str, message: str) -> None:
    note = schema.load_types()["note"]
    frontmatter = {
        "id": "01KBN6V6KX0000000000000001",
        "type": "note",
        "title": "T",
        "tags": [],
        "links": {"supports": [target]},
    }

    assert schema.normalize_link_target(target) == ""
    assert schema.parse_links(frontmatter["links"]) == []
    assert any(message in error for error in schema.validate_frontmatter(frontmatter, note))


def test_concept_edges_mirror_links_and_persist_across_reindex(tmp_path: Path) -> None:
    vault = tmp_path
    copy_memoria_dirs(vault, "schemas")
    write_checked_concept(
        vault,
        "notes/alpha.md",
        "type: note\ntitle: Alpha\ntags: []\n"
        'links:\n  supports: ["[[notes/beta]]"]\n  contradicts: ["[[notes/gamma|Gamma]]"]\n',
    )
    write_checked_concept(vault, "notes/beta.md", "type: note\ntitle: Beta\ntags: []\nlinks: {}\n")
    write_checked_concept(
        vault, "notes/gamma.md", "type: note\ntitle: Gamma\ntags: []\nlinks: {}\n"
    )

    rebuild_passage_index(vault)
    edges = state.concept_edges(vault, checked_only=True)

    assert {
        (edge["source_concept_id"], edge["relation_type"], edge["target_concept_id"])
        for edge in edges
    } == {
        ("notes/alpha.md", "supports", "notes/beta.md"),
        ("notes/alpha.md", "contradicts", "notes/gamma.md"),
    }
    assert {edge["edge_id"] for edge in edges} == {
        state.concept_edge_id("notes/alpha.md", "supports", "notes/beta.md"),
        state.concept_edge_id("notes/alpha.md", "contradicts", "notes/gamma.md"),
    }

    with state.connect(vault) as conn:
        conn.execute(
            "UPDATE concept_edges SET attributes_json = ? "
            "WHERE source_concept_id = ? AND relation_type = ? AND target_concept_id = ?",
            (
                '{"warrant_ref":"evidence/items/alpha"}',
                "notes/alpha.md",
                "supports",
                "notes/beta.md",
            ),
        )
        conn.execute(
            "INSERT INTO concept_edges("
            " source_concept_id, relation_type, target_concept_id,"
            " check_status, source_path, updated_at)"
            " VALUES ('notes/alpha.md', 'tension', 'notes/beta.md',"
            " 'checked', '', '2026-07-15T00:00:00Z')"
        )

    rebuild_passage_index(vault)
    edges = state.concept_edges(vault, checked_only=True)

    assert len(edges) == 3
    assert {edge["relation_type"] for edge in edges} == {
        "supports",
        "contradicts",
        "tension",
    }
    support = next(edge for edge in edges if edge["relation_type"] == "supports")
    assert support["attributes_json"] == '{"warrant_ref":"evidence/items/alpha"}'
    assert support["edge_id"] == state.concept_edge_id(
        "notes/alpha.md", "supports", "notes/beta.md"
    )


def test_replace_concept_edges_preserves_direct_tension_and_ignores_tension_mirror_rows(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    state.rebuild_file_concept_mirror(
        vault,
        [
            {"concept_id": rel, "concept_type": "note"}
            for rel in ("notes/alpha.md", "notes/beta.md", "notes/gamma.md")
        ],
    )
    with state.connect(vault) as conn:
        conn.execute(
            "INSERT INTO concept_edges("
            " source_concept_id, relation_type, target_concept_id, target_path,"
            " check_status, source_path, updated_at)"
            " VALUES ('notes/alpha.md', 'tension', 'notes/beta.md', 'notes/beta.md',"
            " 'checked', '', '2026-07-15T00:00:00Z')"
        )

    result = state.replace_concept_edges(
        vault,
        [
            {
                "source_concept_id": "notes/alpha.md",
                "relation_type": "supports",
                "target_concept_id": "notes/gamma.md",
                "check_status": "checked",
                "source_path": "notes/alpha.md",
            },
            {
                "source_concept_id": "notes/alpha.md",
                "relation_type": "tension",
                "target_concept_id": "notes/beta.md",
                "check_status": "unchecked",
                "source_path": "notes/alpha.md",
            },
            {
                "source_concept_id": "notes/alpha.md",
                "relation_type": "tension",
                "target_concept_id": "notes/ignored.md",
                "check_status": "checked",
                "source_path": "notes/alpha.md",
            },
        ],
    )

    assert result == {"deleted": 0, "inserted": 1}
    edges = state.concept_edges(vault)
    assert {
        (edge["source_concept_id"], edge["relation_type"], edge["target_path"]) for edge in edges
    } == {
        ("notes/alpha.md", "supports", "notes/gamma.md"),
        ("notes/alpha.md", "tension", "notes/beta.md"),
    }
    tension = next(edge for edge in edges if edge["relation_type"] == "tension")
    assert tension["check_status"] == "checked"
    assert tension["source_path"] == ""


def test_replace_concept_edges_scopes_upserts_pruning_and_distinguishes_empty_scope(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    initial_rows = [
        {
            "source_concept_id": "notes/alpha.md",
            "relation_type": "supports",
            "target_concept_id": "notes/beta.md",
            "check_status": "checked",
            "source_path": "notes/alpha.md",
        },
        {
            "source_concept_id": "notes/beta.md",
            "relation_type": "supports",
            "target_concept_id": "notes/gamma.md",
            "check_status": "checked",
            "source_path": "notes/beta.md",
        },
    ]
    state.replace_concept_edges(vault, initial_rows)

    assert state.replace_concept_edges(
        vault,
        [
            {
                "source_concept_id": "notes/alpha.md",
                "relation_type": "contradicts",
                "target_concept_id": "notes/ignored.md",
                "check_status": "checked",
                "source_path": "notes/alpha.md",
            }
        ],
        paths=[],
    ) == {"deleted": 0, "inserted": 0}
    assert {
        (edge["source_concept_id"], edge["relation_type"], edge["target_path"])
        for edge in state.concept_edges(vault)
    } == {
        ("notes/alpha.md", "supports", "notes/beta.md"),
        ("notes/beta.md", "supports", "notes/gamma.md"),
    }

    assert state.replace_concept_edges(
        vault,
        [
            {
                "source_concept_id": "notes/alpha.md",
                "relation_type": "contradicts",
                "target_concept_id": "notes/delta.md",
                "check_status": "checked",
                "source_path": "notes/alpha.md",
            }
        ],
        paths=["notes/alpha.md"],
    ) == {"deleted": 1, "inserted": 1}
    assert {
        (edge["source_concept_id"], edge["relation_type"], edge["target_path"])
        for edge in state.concept_edges(vault)
    } == {
        ("notes/alpha.md", "contradicts", "notes/delta.md"),
        ("notes/beta.md", "supports", "notes/gamma.md"),
    }

    assert state.replace_concept_edges(vault, [], paths=["notes/alpha.md"]) == {
        "deleted": 1,
        "inserted": 0,
    }
    assert [edge["source_concept_id"] for edge in state.concept_edges(vault)] == ["notes/beta.md"]

    assert state.replace_concept_edges(vault, []) == {"deleted": 1, "inserted": 0}
    assert state.concept_edges(vault) == []


def test_concept_edges_fresh_schema_exposes_reader_fields(tmp_path: Path) -> None:
    fresh = tmp_path / "fresh"
    with state.connect(fresh) as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(concept_edges)")}
        assert {"edge_id", "target_path", "attributes_json"}.issubset(columns)
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 16

    # v16 edges are FK-backed and resolve targets, so seed both endpoints.
    state.rebuild_file_concept_mirror(
        fresh,
        [
            {"concept_id": rel, "concept_type": "note"}
            for rel in (
                "notes/fresh.md",
                "notes/target.md",
                "notes/one.md",
                "notes/two.md",
                "notes/three.md",
                "notes/four.md",
                "notes/blank-one.md",
                "notes/blank-two.md",
                "notes/target-one.md",
                "notes/target-two.md",
            )
        ],
    )
    state.replace_concept_edges(
        fresh,
        [
            {
                "edge_id": "caller-selected-id",
                "source_concept_id": "./notes/fresh.md",
                "relation_type": "SUPPORTS",
                "target_concept_id": "/notes/target.md",
                "attributes_json": '{"warrant_ref":"evidence/items/fresh"}',
                "check_status": "checked",
                "source_path": "notes/fresh.md",
            }
        ],
    )
    state.replace_concept_edges(
        fresh,
        [
            {
                "edge_id": "another-caller-selected-id",
                "source_concept_id": "notes/fresh.md",
                "relation_type": "supports",
                "target_concept_id": "notes/target.md",
                "attributes_json": "{}",
                "check_status": "unchecked",
                "source_path": "notes/fresh.md",
            }
        ],
    )
    fresh_edge = state.concept_edges(fresh, checked_only=False)
    assert fresh_edge == [
        {
            "edge_id": state.concept_edge_id("notes/fresh.md", "supports", "notes/target.md"),
            "source_concept_id": "notes/fresh.md",
            "relation_type": "supports",
            "target_concept_id": "notes/target.md",
            "target_path": "notes/target.md",
            "attributes_json": '{"warrant_ref":"evidence/items/fresh"}',
            "check_status": "unchecked",
            "source_path": "notes/fresh.md",
        }
    ]

    with state.connect(fresh) as conn:
        conn.execute(
            "INSERT INTO concept_edges("
            "edge_id, source_concept_id, relation_type, target_concept_id, "
            "check_status, source_path, updated_at) "
            "VALUES ('duplicate-id', 'notes/one.md', 'supports', 'notes/two.md', "
            "'checked', 'notes/one.md', '2026-07-15T00:00:00Z')"
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO concept_edges("
                "edge_id, source_concept_id, relation_type, target_concept_id, "
                "check_status, source_path, updated_at) "
                "VALUES ('duplicate-id', 'notes/three.md', 'supports', 'notes/four.md', "
                "'checked', 'notes/three.md', '2026-07-15T00:00:00Z')"
            )
        conn.execute(
            "INSERT INTO concept_edges("
            "source_concept_id, relation_type, target_concept_id, "
            "check_status, source_path, updated_at) "
            "VALUES ('notes/blank-one.md', 'supports', 'notes/target-one.md', "
            "'checked', 'notes/blank-one.md', '2026-07-15T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO concept_edges("
            "source_concept_id, relation_type, target_concept_id, "
            "check_status, source_path, updated_at) "
            "VALUES ('notes/blank-two.md', 'supports', 'notes/target-two.md', "
            "'checked', 'notes/blank-two.md', '2026-07-15T00:00:00Z')"
        )
        blank_edge_ids = [
            row["edge_id"]
            for row in conn.execute(
                "SELECT edge_id FROM concept_edges "
                "WHERE source_concept_id IN (?, ?) "
                "ORDER BY source_concept_id",
                ("notes/blank-one.md", "notes/blank-two.md"),
            )
        ]

    assert blank_edge_ids == ["", ""]


def test_reverse_traversal_indexes_exist(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        names = {
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'index'")
        }

    assert "idx_concept_edges_target" in names
    assert "idx_work_graph_edges_target" in names


def test_refresh_reindexes_only_changed_files_and_keeps_concept_edges(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = tmp_path
    copy_memoria_dirs(vault, "schemas")
    write_checked_concept(
        vault,
        "notes/alpha.md",
        "type: note\ntitle: Alpha\ntags: []\nlinks: {}\n",
        body="rarealpha first version",
    )
    write_checked_concept(
        vault,
        "notes/beta.md",
        "type: note\ntitle: Beta\ntags: []\nlinks: {}\n",
        body="rarebeta first version",
    )
    rebuild_passage_index(vault)
    state.replace_concept_edges(
        vault,
        [
            {
                "source_concept_id": "notes/alpha.md",
                "relation_type": "supports",
                "target_concept_id": "notes/beta.md",
                "check_status": "checked",
                "source_path": "notes/alpha.md",
            }
        ],
    )
    reads: list[str] = []

    def counting_safe_read(path: Path) -> str:
        reads.append(Path(path).name)
        return safe_read(path)

    monkeypatch.setattr("memoria_vault.runtime.search_index.safe_read", counting_safe_read)

    unchanged = call_with_context(indexing.refresh_stale_passages, vault)

    assert unchanged["passages"] == {"inserted": 0, "paths": 0}
    assert reads == []

    path = vault / "notes/alpha.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("first version", "second version"),
        encoding="utf-8",
    )
    mark_file_status(vault, "notes/alpha.md")
    refreshed = call_with_context(indexing.refresh_stale_passages, vault)

    assert refreshed["passages"] == {"inserted": 1, "paths": 1}
    assert reads == ["alpha.md"]
    texts = {row["path"]: row["text"] for row in state.indexed_passages(vault)}
    assert texts["notes/alpha.md"].endswith("rarealpha second version\n")
    assert texts["notes/beta.md"].endswith("rarebeta first version\n")
    with state.connect(vault) as conn:
        edges = conn.execute("SELECT source_concept_id FROM concept_edges").fetchall()
    assert [str(row["source_concept_id"]) for row in edges] == ["notes/alpha.md"]


@pytest.mark.parametrize("revoked_status", ["unchecked", "quarantined"])
def test_verdict_demotion_revokes_mirror_edges_before_passage_refresh(
    tmp_path: Path, revoked_status: str
) -> None:
    vault = tmp_path
    copy_memoria_dirs(vault, "schemas")
    write_checked_concept(
        vault,
        "notes/a.md",
        "type: note\ntitle: A\ntags: []\nlinks: {}\n",
        body="alpha endpoint",
    )
    write_checked_concept(
        vault,
        "notes/b.md",
        "type: note\ntitle: B\ntags: []\nlinks:\n  supports:\n    - notes/a.md\n    - notes/c.md\n",
        body="bridge endpoint",
    )
    write_checked_concept(
        vault,
        "notes/c.md",
        "type: note\ntitle: C\ntags: []\nlinks: {}\n",
        body="gamma endpoint",
    )
    write_checked_concept(
        vault,
        "notes/d.md",
        "type: note\ntitle: D\ntags: []\nlinks: {}\n",
        body="pi tension endpoint",
    )
    rebuild_passage_index(vault)

    assert graph_sql.neighborhood(vault, ["notes/a.md"], depth=2, relations={"supports"})[
        "ids"
    ] == [
        "notes/a.md",
        "notes/b.md",
        "notes/c.md",
    ]
    with state.connect(vault) as conn:
        conn.execute(
            "INSERT INTO concept_edges("
            " source_concept_id, relation_type, target_concept_id, target_path,"
            " check_status, source_path, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "notes/a.md",
                "tension",
                "notes/d.md",
                "notes/d.md",
                "checked",
                "",
                "2026-07-18T00:00:00Z",
            ),
        )

    state.set_concept_verdict(vault, "notes/b.md", revoked_status)

    all_edges = state.concept_edges(vault, checked_only=False)
    mirror_edges = [edge for edge in all_edges if edge["source_path"] == "notes/b.md"]
    assert {
        (edge["source_concept_id"], edge["target_concept_id"], edge["check_status"])
        for edge in mirror_edges
    } == {
        ("notes/b.md", "notes/a.md", revoked_status),
        ("notes/b.md", "notes/c.md", revoked_status),
    }
    tension = next(
        edge
        for edge in all_edges
        if edge["relation_type"] == "tension" and edge["source_path"] == ""
    )
    assert {
        key: tension[key]
        for key in ("source_concept_id", "target_concept_id", "check_status", "source_path")
    } == {
        "source_concept_id": "notes/a.md",
        "target_concept_id": "notes/d.md",
        "check_status": "checked",
        "source_path": "",
    }

    refreshed = call_with_context(indexing.refresh_stale_passages, vault)

    assert refreshed["passages"] == {"inserted": 0, "paths": 0}
    assert {row["path"] for row in state.indexed_passages(vault)} == {
        "notes/a.md",
        "notes/c.md",
        "notes/d.md",
    }
    assert "notes/b.md" not in state.file_index_states(vault)
    assert graph_sql.neighborhood(vault, ["notes/a.md"], depth=2, relations={"supports"})[
        "ids"
    ] == ["notes/a.md"]
    assert graph_sql.neighborhood(vault, ["notes/a.md"], depth=2, relations={"tension"})["ids"] == [
        "notes/a.md",
        "notes/d.md",
    ]

    state.set_concept_verdict(vault, "notes/b.md", "checked")

    assert {
        edge["check_status"]
        for edge in state.concept_edges(vault, checked_only=False)
        if edge["source_path"] == "notes/b.md"
    } == {revoked_status}
    assert graph_sql.neighborhood(vault, ["notes/a.md"], depth=2, relations={"supports"})[
        "ids"
    ] == ["notes/a.md"]

    rebuild_passage_index(vault)

    assert {
        edge["check_status"]
        for edge in state.concept_edges(vault, checked_only=False)
        if edge["source_path"] == "notes/b.md"
    } == {"checked"}
    assert graph_sql.neighborhood(vault, ["notes/a.md"], depth=2, relations={"supports"})[
        "ids"
    ] == [
        "notes/a.md",
        "notes/b.md",
        "notes/c.md",
    ]
    assert graph_sql.neighborhood(vault, ["notes/a.md"], depth=2, relations={"tension"})["ids"] == [
        "notes/a.md",
        "notes/d.md",
    ]


@pytest.mark.parametrize("revoked_status", ["unchecked", "quarantined"])
def test_verdict_demotion_revokes_mirror_edges_of_a_ulid_keyed_concept(
    tmp_path: Path, revoked_status: str
) -> None:
    """The demotion trigger matches identity, not path.

    v16 decouples a file Concept's id from its path, so a trigger comparing the
    verdict's ``concept_id`` against the edge's ``source_path`` demotes nothing
    for a ULID-keyed Concept — leaving every revoked edge at ``checked`` in
    exactly the incremental window (no full rebuild) this trigger exists to close.
    """
    ulid_a = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    ulid_b = "01BX5ZZKBKACTAV9WEVGEMMVRZ"
    vault = tmp_path
    copy_memoria_dirs(vault, "schemas")
    write_checked_concept(
        vault,
        "notes/a.md",
        f"type: note\nid: {ulid_a}\ntitle: A\ntags: []\nlinks: {{}}\n",
        body="alpha endpoint",
    )
    write_checked_concept(
        vault,
        "notes/b.md",
        f"type: note\nid: {ulid_b}\ntitle: B\ntags: []\nlinks:\n  supports:\n    - notes/a.md\n",
        body="bridge endpoint",
    )
    rebuild_passage_index(vault)

    with state.connect(vault) as conn:
        keys = dict(conn.execute("SELECT path, concept_id FROM concepts").fetchall())
        # A PI-owned tension row on the same identity, which demotion never touches.
        conn.execute(
            "INSERT INTO concept_edges("
            " source_concept_id, relation_type, target_concept_id, target_path,"
            " check_status, source_path, updated_at)"
            " VALUES (?, 'tension', ?, 'notes/a.md', 'checked', '', '2026-07-31T00:00:00Z')",
            (ulid_b, ulid_a),
        )
    assert keys == {"notes/a.md": ulid_a, "notes/b.md": ulid_b}

    state.set_concept_verdict(vault, "notes/b.md", revoked_status)

    assert {
        (edge["relation_type"], edge["check_status"])
        for edge in state.concept_edges(vault, checked_only=False)
        if edge["source_concept_id"] == ulid_b
    } == {("supports", revoked_status), ("tension", "checked")}


def test_refresh_drops_passages_for_removed_files(tmp_path: Path) -> None:
    vault = tmp_path
    copy_memoria_dirs(vault, "schemas")
    write_checked_concept(
        vault,
        "notes/alpha.md",
        "type: note\ntitle: Alpha\ntags: []\nlinks: {}\n",
        body="rarealpha survives",
    )
    write_checked_concept(
        vault,
        "notes/beta.md",
        "type: note\ntitle: Beta\ntags: []\nlinks: {}\n",
        body="rarebeta gets deleted",
    )
    rebuild_passage_index(vault)
    (vault / "notes/beta.md").unlink()

    call_with_context(indexing.refresh_stale_passages, vault)

    paths = {row["path"] for row in state.indexed_passages(vault)}
    assert paths == {"notes/alpha.md"}
    assert "notes/beta.md" not in state.file_index_states(vault)


def test_refresh_removes_barrier_refused_changed_checked_file_without_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = tmp_path
    copy_memoria_dirs(vault, "schemas")
    write_checked_concept(
        vault,
        "notes/alpha.md",
        "type: note\ntitle: Alpha\ntags: []\nlinks: {}\n",
        body="rarealpha indexed version",
    )
    rebuild_passage_index(vault)

    path = vault / "notes/alpha.md"
    stored_mtime_ns = state.file_index_states(vault)["notes/alpha.md"]["source_mtime_ns"]
    path.write_text(
        path.read_text(encoding="utf-8").replace("indexed version", "CANARY"),
        encoding="utf-8",
    )
    os.utime(
        path,
        ns=(path.stat().st_atime_ns, int(stored_mtime_ns) + 1_000_000_000),
    )

    def refusing_safe_read(path: Path) -> str:
        raise AssertionError(f"refresh opened barrier-refused file: {path}")

    monkeypatch.setattr("memoria_vault.runtime.search_index.safe_read", refusing_safe_read)

    call_with_context(indexing.refresh_stale_passages, vault)

    assert state.indexed_passages(vault) == []
    assert "notes/alpha.md" not in state.file_index_states(vault)
    assert call_with_context(retrieval.fts_search, vault, "CANARY") == []


def test_refresh_removes_reverified_non_searchable_file(tmp_path: Path) -> None:
    vault = tmp_path
    copy_memoria_dirs(vault, "schemas")
    write_checked_concept(
        vault,
        "notes/alpha.md",
        "type: note\ntitle: Alpha\ntags: []\nlinks: {}\n",
        body="rarealpha indexed version",
    )
    rebuild_passage_index(vault)

    path = vault / "notes/alpha.md"
    stored_mtime_ns = state.file_index_states(vault)["notes/alpha.md"]["source_mtime_ns"]
    path.write_text(
        path.read_text(encoding="utf-8").replace("tags: []\n", "tags: []\nlifecycle: archived\n"),
        encoding="utf-8",
    )
    os.utime(
        path,
        ns=(path.stat().st_atime_ns, int(stored_mtime_ns) + 1_000_000_000),
    )
    mark_file_status(vault, "notes/alpha.md")

    call_with_context(indexing.refresh_stale_passages, vault)

    assert state.indexed_passages(vault) == []
    assert "notes/alpha.md" not in state.file_index_states(vault)


ULID_NOTE = "01BX5ZZKBKACTAV9WEVGEMMVRZ"


def test_rename_out_of_band_reconciles_by_frontmatter_id(tmp_path: Path) -> None:
    vault = tmp_path
    copy_memoria_dirs(vault, "schemas")
    write_checked_concept(
        vault,
        "notes/alpha.md",
        f"type: note\nid: {ULID_NOTE}\ntitle: Alpha\ntags: []\n"
        'links:\n  supports: ["[[notes/beta]]"]\n',
    )
    write_checked_concept(vault, "notes/beta.md", "type: note\ntitle: Beta\ntags: []\nlinks: {}\n")
    rebuild_passage_index(vault)
    with state.connect(vault) as conn:
        before = conn.execute(
            "SELECT concept_id, path FROM concepts WHERE concept_id = ?", (ULID_NOTE,)
        ).fetchone()
    assert before["path"] == "notes/alpha.md"

    # Rename out-of-band: no writer, no observer — just the file move.
    (vault / "notes/alpha.md").rename(vault / "notes/alpha-renamed.md")
    rebuild_passage_index(vault)

    with state.connect(vault) as conn:
        row = conn.execute(
            "SELECT path FROM concepts WHERE concept_id = ?", (ULID_NOTE,)
        ).fetchone()
        verdict = conn.execute(
            "SELECT check_status FROM concept_verdicts WHERE concept_id = ?",
            (ULID_NOTE,),
        ).fetchone()
        edges = conn.execute(
            "SELECT source_concept_id, relation_type, target_path FROM concept_edges"
        ).fetchall()
        passage = conn.execute(
            "SELECT concept_id FROM passages WHERE path = 'notes/alpha-renamed.md'"
        ).fetchone()
    # Every DB row survives id-keyed; the path column reconciled (spec §7).
    assert row["path"] == "notes/alpha-renamed.md"
    assert verdict["check_status"] == "checked"
    assert (ULID_NOTE, "supports", "notes/beta.md") in {
        (e["source_concept_id"], e["relation_type"], e["target_path"]) for e in edges
    }
    assert passage["concept_id"] == ULID_NOTE


def test_rename_reconciliation_still_refuses_edited_content(tmp_path: Path) -> None:
    """Reconciling the outputs path key must not launder a same-pass edit past the barrier.

    The rename reconciliation moves `outputs.output_id` to the file's new path so a
    pure move keeps its verdict (spec §7). The read barrier's sha256 comparison is
    what actually authorizes consumption, and it must still run against the file at
    that new path — otherwise renaming would become a way to smuggle unchecked
    content into the searchable universe.

    Scope: this proves the one-pass case it exercises — rename and edit both landing
    before the next reindex. A rename indexed first and edited afterwards is *not*
    refused: `indexing._previously_indexed_documents` re-indexes any path whose
    `concept_check_status` is `checked` without calling `is_consumable_checked_file`,
    so no sha256 comparison runs. That bypass predates this reconcile and is
    identical for a file that was never renamed, so the perimeter is unchanged — it
    is simply not what this test proves.
    """
    vault = tmp_path
    copy_memoria_dirs(vault, "schemas")
    write_checked_concept(
        vault,
        "notes/alpha.md",
        f"type: note\nid: {ULID_NOTE}\ntitle: Alpha\ntags: []\nlinks: {{}}\n",
        body="rarealpha the checked body",
    )
    rebuild_passage_index(vault)
    assert {row["path"] for row in state.indexed_passages(vault)} == {"notes/alpha.md"}

    # Rename AND edit out-of-band, in one move the PI never reviewed.
    (vault / "notes/alpha.md").rename(vault / "notes/alpha-edited.md")
    edited = vault / "notes/alpha-edited.md"
    edited.write_text(
        edited.read_text(encoding="utf-8").replace("rarealpha the checked body", "SMUGGLED"),
        encoding="utf-8",
    )
    rebuild_passage_index(vault)

    with state.connect(vault) as conn:
        concept = conn.execute(
            "SELECT path FROM concepts WHERE concept_id = ?", (ULID_NOTE,)
        ).fetchone()
    # The identity still reconciles its path — that half is the rename contract.
    assert concept["path"] == "notes/alpha-edited.md"
    # But the changed bytes are refused: no passage row, and the text is unreachable.
    assert state.indexed_passages(vault) == []
    assert call_with_context(retrieval.fts_search, vault, "SMUGGLED") == []


def test_rename_reconciliation_carries_the_writer_materialization_payload(
    tmp_path: Path,
) -> None:
    """A machine-authored file survives reindex after a rename, payload row and all.

    `stage_concept` is the ledger write behind every machine-authored note, digest
    and hub, and it lands *two* rows: the `outputs` parent and a path-keyed
    `materialization_payloads` child that nothing ever deletes. Reconciling a rename
    repoints the parent key, so without `ON UPDATE CASCADE` on that child the second
    reindex dies on a FOREIGN KEY violation and every caller of
    `rebuild_file_concept_mirror` — `memoria capture`, the search-index worker, and
    `memoria workspace rebuild`, the repair verb itself — stays dead until the file
    is renamed back. The path-only fixture in `write_checked_concept` never writes
    that child, which is why the rest of the rename suite cannot see this.
    """
    vault = tmp_path
    copy_memoria_dirs(vault, "schemas")
    init_git(vault, "index@example.invalid", "Index Tests")
    rel = "notes/writer-authored.md"
    stage_concept(
        vault,
        rel,
        "---\ntype: note\ntitle: Writer authored\ntags: []\nlinks: {}\n---\n"
        "# Writer authored\n\nrarealpha the machine-authored body.\n",
        machine="writer",
    )
    promote_checked(vault, rel, machine="writer")
    state.mark_materialized(vault, rel)
    with state.connect(vault) as conn:
        assert [
            row["output_id"]
            for row in conn.execute("SELECT output_id FROM materialization_payloads")
        ] == [rel]
    rebuild_passage_index(vault)
    assert {row["path"] for row in state.indexed_passages(vault)} == {rel}

    renamed = "notes/writer-renamed.md"
    (vault / rel).rename(vault / renamed)
    rebuild_passage_index(vault)

    with state.connect(vault) as conn:
        payload = conn.execute("SELECT output_id FROM materialization_payloads").fetchone()
        output = conn.execute("SELECT output_id, target_path FROM outputs").fetchone()
    # The payload child rides the parent key across the rename, and the file stays
    # consumable at its new path.
    assert payload["output_id"] == renamed
    assert (output["output_id"], output["target_path"]) == (renamed, renamed)
    assert {row["path"] for row in state.indexed_passages(vault)} == {renamed}
