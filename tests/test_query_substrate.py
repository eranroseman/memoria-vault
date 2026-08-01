from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

from memoria_vault.runtime import graph_sql, indexing, retrieval, state
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.search_index import answer_query as _answer_query
from memoria_vault.runtime.subsystems.lib import edges as edges_lib
from memoria_vault.runtime.subsystems.lib import schema
from memoria_vault.runtime.trusted_writer import append_explicit_journal_event
from memoria_vault.runtime.trusted_writer import promote_checked as _promote_checked
from memoria_vault.runtime.trusted_writer import stage_concept as _stage_concept
from memoria_vault.runtime.vaultio import read_frontmatter, safe_read
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

    assert state.SCHEMA_VERSION == 18
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
        # A wikilink whose braces close early, and a bare target carrying brackets:
        # each has its own rejection arm inside the normalizer.
        ("[[notes/a[b]]", "expected local Concept target"),
        ("notes/a[1]", "expected local Concept target"),
        # The one target that empties out only after the braces come off. Its
        # distinct message is the sole observer of the normalizer's `empty`
        # reason code — a bare blank target never reaches that arm.
        ("[[ ]]", "expected non-empty target string"),
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


@pytest.mark.parametrize(
    ("label", "value", "expected"),
    [
        ("canonical path", "notes/thesis.md", "notes/thesis.md"),
        ("wikilink-wrapped path", "[[notes/thesis]]", "notes/thesis.md"),
        (
            "wikilink with alias and anchor",
            "[[notes/thesis.md#Claim|the thesis]]",
            "notes/thesis.md",
        ),
        ("bare stem completing under notes/", "thesis", "notes/thesis.md"),
        ("hub path", "hubs/sleep.md", "hubs/sleep.md"),
        ("catalog source row", "catalog/sources/sleep", "catalog/sources/sleep"),
        ("leading ./", "./notes/thesis.md", "notes/thesis.md"),
        # Everything below is a namespace the ruling refuses: a title, a slug
        # sentence, an escape, or a path outside the Concept roots.
        ("title carrying a colon", "Toulmin: the warrant", ""),
        ("prose sentence with a colon", "Claim: sleep drives plasticity", ""),
        ("traversal", "notes/../secrets.md", ""),
        ("absolute", "/notes/thesis.md", ""),
        ("bracketed", "notes/a[1]", ""),
        ("unbalanced wikilink", "[[notes/thesis", ""),
        ("non-markdown suffix", "notes/thesis.txt", ""),
        # `normalize_path('.')` is empty, and the `notes/` + `.md` completion
        # would render `notes/.md` — one absorbing sink every junk value fell into.
        ("bare dot", ".", ""),
        ("outside the Concept roots", "projects/demo/project.md", ""),
        ("catalog source with an extra segment", "catalog/sources/sleep/extra", ""),
    ],
)
def test_thesis_rel_normalizes_every_thesis_shape_in_one_path_space(
    label: str, value: str, expected: str
) -> None:
    """`thesis:` is path space with exactly one normalizer (issue #1623).

    Namespace-conflated fixtures are what hid the split: five readers were only
    ever shown values legal in both alias and path space. Every row here is a
    shape that used to separate them.
    """
    assert edges_lib.thesis_rel({"thesis": value}) == expected, label


def test_thesis_rel_reads_only_thesis_and_never_raises() -> None:
    assert edges_lib.thesis_rel({}) == ""
    assert edges_lib.thesis_rel({"thesis": None}) == ""
    assert edges_lib.thesis_rel({"thesis": 42}) == ""
    assert edges_lib.thesis_rel({"thesis": ["notes/thesis.md"]}) == ""
    assert edges_lib.thesis_rel({"thesis": {"target": "[[notes/thesis]]"}}) == "notes/thesis.md"
    assert edges_lib.thesis_rel("notes/thesis.md") == ""
    # `active_thesis:` is retired by project.yaml, so no reader honours it.
    assert edges_lib.thesis_rel({"active_thesis": "notes/thesis.md"}) == ""


def _project_frontmatter(**extra: object) -> dict:
    return {
        "id": "01KBN6V6KX0000000000000001",
        "type": "project",
        "title": "T",
        "tags": [],
        "links": {},
        **extra,
    }


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("Toulmin: the warrant", "thesis: expected local Concept target"),
        ("notes/../escape.md", "thesis: target must not escape the workspace"),
        ("[[ ]]", "thesis: expected non-empty target string"),
        ("notes/thesis.txt", "thesis: expected local Concept target"),
        (42, "thesis: expected non-empty target string, got int"),
    ],
)
def test_project_thesis_is_a_visible_validation_error_outside_path_space(
    value: object, message: str
) -> None:
    """The `link` kind decides the namespace at the schema layer, not per reader."""
    project = schema.load_types()["project"]

    assert schema.validate_frontmatter(_project_frontmatter(thesis=value), project) == [message]


def test_project_thesis_accepts_the_canonical_forms_and_retires_active_thesis() -> None:
    project = schema.load_types()["project"]
    assert project["optional"]["thesis"] == "link"

    for value in ("notes/thesis.md", "[[notes/thesis]]", "thesis"):
        assert schema.validate_frontmatter(_project_frontmatter(thesis=value), project) == []
    assert schema.validate_frontmatter(_project_frontmatter(), project) == []
    assert schema.validate_frontmatter(
        _project_frontmatter(active_thesis="notes/thesis.md"), project
    ) == ["active_thesis: field is retired"]


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
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 18

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
    """A re-verified file the searchable predicate now rejects leaves the index.

    The rejection is journaled note-curation status, not frontmatter: `lifecycle`
    is retired (vaultio.RETIRED_FRONTMATTER_FIELDS) and no reader consults it
    (#1525), so the route this test used to take no longer exists. `mark_file_status`
    keeps the read barrier open, so the removal is `_is_searchable_frontmatter`
    refusing the file and not the barrier refusing to open it.
    """
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
    append_explicit_journal_event(
        vault,
        {
            "event": "derived",
            "operation": "propose-note-candidates",
            "output_id": "notes/alpha.md",
        },
        actor="operation",
        machine="test-fixture",
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


def test_pending_edges_resolve_when_target_appears(tmp_path: Path) -> None:
    """Retained rows resolve through `_lookup_concept_id`, not a bare `concept_id` probe.

    v16 decouples identity from path, so a retained row's `target_path` is a path
    and the id it has to resolve to usually is not one: a machine-authored note
    keys by its frontmatter ULID, and a catalog work keys by its bare `work_id`
    while rendering at `catalog/sources/<work_id>`. A probe matching only
    `concepts.concept_id = target_path` still passes a path-keyed fixture and
    leaves both of those permanently dangling — `target_concept_id IS NULL`,
    `edge_id = ''` — which is the one thing this pass exists to prevent, and the
    ULID case is the normal case for a machine-authored note.
    """
    vault = tmp_path
    copy_memoria_dirs(vault, "schemas")
    write_checked_concept(
        vault,
        "notes/early.md",
        'type: note\ntitle: Early\ntags: []\nlinks:\n  supports: ["[[notes/future]]"]\n',
    )
    rebuild_passage_index(vault)
    # Durable tension rows across all three target id-spaces: the path-keyed note
    # the frontmatter link also points at, a ULID-keyed note, and a catalog work.
    with state.connect(vault) as conn:
        for target_path, attributes_json in (
            ("notes/future.md", '{"warrant": "w9"}'),
            ("notes/future-ulid.md", "{}"),
            ("catalog/sources/w-alpha/source.md", "{}"),
        ):
            conn.execute(
                "INSERT INTO concept_edges("
                " edge_id, source_concept_id, relation_type, target_concept_id,"
                " target_path, attributes_json, check_status, source_path, updated_at)"
                " VALUES ('', 'notes/early.md', 'tension', NULL, ?, ?, 'checked', '',"
                " '2026-07-15T00:00:00Z')",
                (target_path, attributes_json),
            )
        pending = conn.execute(
            "SELECT target_concept_id, edge_id FROM concept_edges"
            " WHERE target_path = 'notes/future.md' AND relation_type = 'supports'"
        ).fetchone()
    # Dangling link is modeled, not dropped (clause 6).
    assert pending["target_concept_id"] is None
    assert pending["edge_id"] == ""

    # The targets appear; the next reindex resolves every retained row to its id.
    write_checked_concept(
        vault, "notes/future.md", "type: note\ntitle: Future\ntags: []\nlinks: {}\n"
    )
    write_checked_concept(
        vault,
        "notes/future-ulid.md",
        f"type: note\nid: {ULID_NOTE}\ntitle: Future ULID\ntags: []\nlinks: {{}}\n",
    )
    with state.connect(vault) as conn:
        state.ensure_concept_parent_conn(
            conn,
            "catalog/sources/w-alpha",
            concept_type="work",
            store="db",
            path="catalog/sources/w-alpha",
        )
    rebuild_passage_index(vault)

    with state.connect(vault) as conn:
        rows = {
            (str(row["relation_type"]), str(row["target_path"])): dict(row)
            for row in conn.execute(
                "SELECT relation_type, target_path, target_concept_id, edge_id,"
                " attributes_json FROM concept_edges"
            )
        }
    supports = rows[("supports", "notes/future.md")]
    assert supports["target_concept_id"] == "notes/future.md"
    assert supports["edge_id"] == state.concept_edge_id(
        "notes/early.md", "supports", "notes/future.md"
    )
    # The retained tension row resolves too — attributes still hanging on it.
    tension = rows[("tension", "notes/future.md")]
    assert tension["target_concept_id"] == "notes/future.md"
    assert tension["edge_id"] == state.concept_edge_id(
        "notes/early.md", "tension", "notes/future.md"
    )
    assert tension["attributes_json"] == '{"warrant": "w9"}'
    # Neither of these targets has `concept_id == target_path`: the note resolves
    # through `concepts.path`, and the work resolves through neither -- it is spelled
    # at its source file, so only the bare-`work_id` rendering reaches it. That is the
    # spelling a tension parks at when the work is not yet in `catalog_sources`, since
    # ERP-B.2's `_concept_edge_target_path` collapses `/source.md` only for works it
    # already knows; the rendering arm is what resolves it once the work lands.
    ulid_target = rows[("tension", "notes/future-ulid.md")]
    assert ulid_target["target_concept_id"] == ULID_NOTE
    assert ulid_target["edge_id"] == state.concept_edge_id("notes/early.md", "tension", ULID_NOTE)
    work_target = rows[("tension", "catalog/sources/w-alpha/source.md")]
    assert work_target["target_concept_id"] == "w-alpha"
    assert work_target["edge_id"] == state.concept_edge_id("notes/early.md", "tension", "w-alpha")


def test_a_pruned_target_relinks_when_its_concept_returns(tmp_path: Path) -> None:
    """`target_concept_id IS NULL` is the pass predicate's `ON DELETE SET NULL` half.

    Graph-R2: pruning a verdict-less Concept pends every inbound edge through the
    v16 foreign key, which nulls the endpoint but leaves `edge_id` at the digest it
    already carried. That row is invisible to an `edge_id = ''` scan, so without
    this half of the predicate it stays dangling even once the Concept returns.
    The other half catches the mirror-image shape a re-key leaves — live endpoint,
    blank `edge_id` — and neither half covers the other's row.
    """
    vault = tmp_path
    mirror = [
        {"concept_id": "notes/early.md", "concept_type": "note", "path": "notes/early.md"},
        {"concept_id": "notes/gone.md", "concept_type": "note", "path": "notes/gone.md"},
    ]
    state.rebuild_file_concept_mirror(vault, mirror)
    with state.connect(vault) as conn:
        conn.execute(
            "INSERT INTO concept_edges("
            " edge_id, source_concept_id, relation_type, target_concept_id, target_path,"
            " check_status, source_path, updated_at)"
            " VALUES (?, 'notes/early.md', 'tension', 'notes/gone.md', 'notes/gone.md',"
            " 'checked', '', '2026-07-15T00:00:00Z')",
            (state.concept_edge_id("notes/early.md", "tension", "notes/gone.md"),),
        )

    state.rebuild_file_concept_mirror(vault, mirror[:1])

    with state.connect(vault) as conn:
        pended = conn.execute("SELECT target_concept_id, edge_id FROM concept_edges").fetchone()
    assert pended["target_concept_id"] is None
    # The digest survived the prune, so `edge_id = ''` alone never sees this row.
    assert str(pended["edge_id"]) == state.concept_edge_id(
        "notes/early.md", "tension", "notes/gone.md"
    )

    state.rebuild_file_concept_mirror(vault, mirror)
    state.replace_concept_edges(vault, [])

    with state.connect(vault) as conn:
        relinked = conn.execute("SELECT target_concept_id, edge_id FROM concept_edges").fetchone()
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    assert str(relinked["target_concept_id"]) == "notes/gone.md"
    assert str(relinked["edge_id"]) == state.concept_edge_id(
        "notes/early.md", "tension", "notes/gone.md"
    )


def test_concept_edges_relation_check_matches_edge_relations(tmp_path: Path) -> None:
    """Parity, not a shared literal: the DB CHECK is read back and compared to the owner.

    The reader is `graph_sql.concept_edge_relations` — the same one `neighborhood`
    traverses with — so this doubles as its pin instead of a fourth copy of the
    roster-reading regex.
    """
    assert graph_sql.concept_edge_relations(tmp_path) == set(edges_lib.EDGE_RELATIONS)


def test_replace_concept_edges_accepts_activated_relations(tmp_path: Path) -> None:
    state.replace_concept_edges(
        tmp_path,
        [
            {
                "source_concept_id": "notes/a.md",
                "relation_type": relation,
                "target_concept_id": f"notes/{relation}.md",
                "check_status": "checked",
                "source_path": "notes/a.md",
            }
            for relation in sorted(edges_lib.EDGE_RELATIONS)
        ],
    )

    rows = state.concept_edges(tmp_path, checked_only=True)

    # Every EDGE_RELATIONS value clears the `_concept_edge_relation` gate and the
    # DB CHECK; `tension` then lands nowhere because the mirror writer spares
    # PI-owned tension rows rather than writing them (that skip is pinned by
    # test_replace_concept_edges_preserves_direct_tension_and_ignores_tension_mirror_rows).
    assert {row["relation_type"] for row in rows} == set(edges_lib.LINK_RELATIONS)
    # The gate's surface-form normalization, which nothing else observes: a padded,
    # capitalized relation is stored canonically rather than rejected.
    state.replace_concept_edges(
        tmp_path,
        [
            {
                "source_concept_id": "notes/b.md",
                "relation_type": " Supports ",
                "target_concept_id": "notes/c.md",
                "check_status": "checked",
                "source_path": "notes/b.md",
            }
        ],
    )
    assert [
        row["relation_type"]
        for row in state.concept_edges(tmp_path, checked_only=True)
        if row["source_path"] == "notes/b.md"
    ] == ["supports"]
    with pytest.raises(ValueError, match="unknown concept edge relation: related"):
        state.replace_concept_edges(
            tmp_path,
            [
                {
                    "source_concept_id": "notes/a.md",
                    "relation_type": "related",
                    "target_concept_id": "notes/b.md",
                    "check_status": "checked",
                    "source_path": "notes/a.md",
                }
            ],
        )


def test_activated_links_round_trip_from_frontmatter_to_edge_rows(tmp_path: Path) -> None:
    """EDGES section 10 acceptance: authored in an editor, accepted by the validator,
    and a row at reindex — for warrant/qualifier/rebuttal, on the same bytes."""
    vault = tmp_path
    copy_memoria_dirs(vault, "schemas")
    write_checked_concept(
        vault,
        "notes/claim.md",
        "type: note\ntitle: Claim\ntags: []\n"
        'links:\n  warrant: ["[[notes/license]]", "notes/second-license.md"]\n'
        '  qualifier: ["[[notes/scope|Scope]]"]\n'
        '  rebuttal: ["notes/counter.md"]\n',
    )
    for rel in ("license", "second-license", "scope", "counter"):
        write_checked_concept(
            vault, f"notes/{rel}.md", f"type: note\ntitle: {rel}\ntags: []\nlinks: {{}}\n"
        )

    authored = read_frontmatter(vault / "notes/claim.md")
    link_errors = [
        error
        for error in schema.validate_frontmatter(authored, schema.load_types()["note"])
        if error.startswith("links")
    ]
    assert link_errors == []

    rebuild_passage_index(vault)

    mirrored = state.concept_edges(vault, checked_only=True)
    assert {
        (edge["relation_type"], edge["target_path"], edge["target_concept_id"]) for edge in mirrored
    } == {
        ("warrant", "notes/license.md", "notes/license.md"),
        ("warrant", "notes/second-license.md", "notes/second-license.md"),
        ("qualifier", "notes/scope.md", "notes/scope.md"),
        ("rebuttal", "notes/counter.md", "notes/counter.md"),
    }
