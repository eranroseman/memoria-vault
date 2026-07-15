from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from memoria_vault.runtime import indexing, retrieval, state
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.search_index import answer_query as _answer_query
from memoria_vault.runtime.subsystems.lib import schema
from tests.helpers import call_with_context, copy_memoria_dirs, write_checked_concept


def answer_query(vault: Path, *args, **kwargs):
    return call_with_context(_answer_query, vault, *args, **kwargs)


def rebuild_passage_index(vault: Path, *args, **kwargs):
    return call_with_context(indexing.rebuild_passage_index, vault, *args, **kwargs)


def test_schema_creates_query_tables_and_rejects_v7(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        names = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
            ).fetchall()
        }

    assert state.SCHEMA_VERSION == 12
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

    with state.connect(vault) as conn:
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


def test_replace_concept_edges_preserves_direct_tension_and_ignores_tension_mirror_rows(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    with state.connect(vault) as conn:
        conn.execute(
            "INSERT INTO concept_edges("
            " source_concept_id, relation_type, target_concept_id,"
            " check_status, source_path, updated_at)"
            " VALUES ('notes/alpha.md', 'tension', 'notes/beta.md',"
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
        (edge["source_concept_id"], edge["relation_type"], edge["target_concept_id"])
        for edge in edges
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
        (edge["source_concept_id"], edge["relation_type"], edge["target_concept_id"])
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
        (edge["source_concept_id"], edge["relation_type"], edge["target_concept_id"])
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
