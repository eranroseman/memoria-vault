"""Schema v16 identity floor: concepts.path, FK parents, and scoped edges.

Fresh installs receive v16 directly, so every test here builds its vault with
``state.connect(tmp_path)``. There is no migration ladder and no legacy fixture.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.trusted_writer import OperationContext, rebuild_concept_mirror_from_files
from tests.helpers import copy_memoria_dirs

CONTEXT = OperationContext(
    actor="operation",
    run_id="v16",
    request_id="v16",
    operation_id="v16",
    machine="v16",
)
CATALOG_FORMS = (
    "smith-2020",
    "catalog/sources/smith-2020",
    "./catalog/sources/smith-2020",
    "catalog/sources/smith-2020/source.md",
)
ULID_A = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
ULID_B = "01BX5ZZKBKACTAV9WEVGEMMVRZ"


def _mirror(vault: Path, *rels: str) -> None:
    state.rebuild_file_concept_mirror(
        vault, [{"concept_id": rel, "concept_type": "note"} for rel in rels]
    )


def _edge_row(source: str, target: str, relation: str = "supports") -> dict[str, str]:
    return {
        "source_concept_id": source,
        "relation_type": relation,
        "target_concept_id": target,
        "check_status": "checked",
        "source_path": source,
    }


def test_v16_lands_with_path_attribute_and_real_fks(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        assert state.SCHEMA_VERSION == 16
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 16
        concept_columns = {row["name"] for row in conn.execute("PRAGMA table_info(concepts)")}
        status_columns = {row["name"] for row in conn.execute("PRAGMA table_info(concept_status)")}
        edge_columns = {
            row["name"]: dict(row) for row in conn.execute("PRAGMA table_info(concept_edges)")
        }
        verdict_fks = {
            (row["table"], row["from"], row["to"])
            for row in conn.execute("PRAGMA foreign_key_list(concept_verdicts)")
        }
        edge_fks = {
            (row["table"], row["from"], row["to"])
            for row in conn.execute("PRAGMA foreign_key_list(concept_edges)")
        }

    assert "path" in concept_columns
    assert "path" in status_columns
    assert "target_path" in edge_columns
    assert edge_columns["target_concept_id"]["notnull"] == 0
    assert ("concepts", "concept_id", "concept_id") in verdict_fks
    assert {
        ("concepts", "source_concept_id", "concept_id"),
        ("concepts", "target_concept_id", "concept_id"),
    } <= edge_fks


def test_v16_rejects_orphan_verdict_and_edge_rows(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO concept_verdicts(concept_id, check_status)"
                " VALUES ('no-such-concept', 'checked')"
            )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO concept_edges("
                " edge_id, source_concept_id, relation_type, target_concept_id,"
                " target_path, check_status, source_path, updated_at)"
                " VALUES ('', 'no-such-concept', 'supports', NULL,"
                " 'notes/x.md', 'unchecked', '', '2026-07-15T00:00:00Z')"
            )


def test_v16_catalog_child_restricts_to_its_concept_parent(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        catalog_fks = [
            (row["table"], row["from"], row["to"], row["on_update"], row["on_delete"])
            for row in conn.execute("PRAGMA foreign_key_list(catalog_sources)")
        ]
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO catalog_sources("
                " work_id, concept_path, title, provider_coverage, text_status, check_status)"
                " VALUES ('orphan-2020', 'catalog/sources/orphan-2020', 'Orphan',"
                " 'partial', 'metadata-only', 'unchecked')"
            )

    assert catalog_fks == [("concepts", "work_id", "concept_id", "RESTRICT", "RESTRICT")]


def test_catalog_upsert_mints_exactly_one_bare_work_parent(tmp_path: Path) -> None:
    state.upsert_catalog_record(
        tmp_path, work_id="smith-2020", title="Smith 2020", check_status="checked"
    )

    with state.connect(tmp_path) as conn:
        parents = [
            dict(row)
            for row in conn.execute("SELECT concept_id, concept_type, store, path FROM concepts")
        ]
        catalog = dict(conn.execute("SELECT * FROM catalog_sources").fetchone())
        verdicts = {
            row["concept_id"]: row["check_status"]
            for row in conn.execute("SELECT * FROM concept_verdicts")
        }
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

    assert parents == [
        {
            "concept_id": "smith-2020",
            "concept_type": "work",
            "store": "db",
            "path": "catalog/sources/smith-2020",
        }
    ]
    assert catalog["concept_path"] == "catalog/sources/smith-2020"
    assert verdicts == {"smith-2020": "checked"}


def test_catalog_alias_is_a_non_identity_read_scope_alias(tmp_path: Path) -> None:
    state.upsert_catalog_record(
        tmp_path, work_id="smith-2020", title="Smith 2020", concept_path="notes/alpha.md"
    )

    with state.connect(tmp_path) as conn:
        catalog = dict(conn.execute("SELECT * FROM catalog_sources").fetchone())
        parents = [
            (row["concept_id"], row["path"])
            for row in conn.execute("SELECT concept_id, path FROM concepts")
        ]
        verdict_ids = [
            row["concept_id"] for row in conn.execute("SELECT concept_id FROM concept_verdicts")
        ]

    assert catalog["concept_path"] == "notes/alpha.md"
    assert parents == [("smith-2020", "catalog/sources/smith-2020")]
    assert verdict_ids == ["smith-2020"]


def test_every_catalog_reference_form_shares_one_parent(tmp_path: Path) -> None:
    state.upsert_catalog_record(tmp_path, work_id="smith-2020", title="Smith 2020")
    _mirror(tmp_path, "notes/alpha.md")

    for form in CATALOG_FORMS:
        state.set_concept_verdict(tmp_path, form, "checked")
    state.replace_concept_edges(
        tmp_path, [_edge_row("notes/alpha.md", form) for form in CATALOG_FORMS]
    )
    payload = "---\ntype: note\n---\n\nDerived.\n"
    for form in CATALOG_FORMS:
        state.record_file_output(
            tmp_path,
            output_id="notes/derived.md",
            concept_type="note",
            check_status="unchecked",
            output_sha256="sha256:" + hashlib.sha256(payload.encode()).hexdigest(),
            staging_id=".memoria/staging/notes/derived.md",
            payload_text=payload,
            context=CONTEXT,
            inputs=[{"id": form}],
        )

    with state.connect(tmp_path) as conn:
        works = [
            row["concept_id"]
            for row in conn.execute("SELECT concept_id FROM concepts WHERE concept_type = 'work'")
        ]
        verdicts = {
            row["concept_id"]: row["check_status"]
            for row in conn.execute("SELECT * FROM concept_verdicts")
        }
        edges = [dict(row) for row in conn.execute("SELECT * FROM concept_edges")]
        inputs = [row["input_id"] for row in conn.execute("SELECT input_id FROM derivations")]

    assert works == ["smith-2020"]
    assert verdicts["smith-2020"] == "checked"
    assert [(edge["target_concept_id"], edge["target_path"]) for edge in edges] == [
        ("smith-2020", "catalog/sources/smith-2020")
    ]
    assert inputs == ["smith-2020"]


def test_file_mirror_maps_document_types_through_the_registry(tmp_path: Path) -> None:
    state.rebuild_file_concept_mirror(
        tmp_path,
        [
            {"concept_id": "fulltexts/smith-2020.md", "concept_type": "fulltext"},
            {"concept_id": "notes/alpha.md", "concept_type": "note"},
        ],
    )

    with state.connect(tmp_path) as conn:
        rows = {row["concept_id"]: dict(row) for row in conn.execute("SELECT * FROM concepts")}

    fulltext = rows["fulltexts/smith-2020.md"]
    assert fulltext["concept_type"] == "work"
    assert fulltext["path"] == "fulltexts/smith-2020.md"
    assert fulltext["store"] == "file"
    assert rows["notes/alpha.md"]["concept_type"] == "note"


def test_file_records_map_raw_document_types_before_the_db_check(tmp_path: Path) -> None:
    state.record_observed_file_edit(
        tmp_path,
        output_id="fulltexts/smith-2020.md",
        concept_type="fulltext",
        output_sha256="sha256:deadbeef",
    )
    payload = "---\ntype: code-artifact\n---\n\nBody.\n"
    state.record_file_output(
        tmp_path,
        output_id="projects/alpha/analysis.md",
        concept_type="code-artifact",
        check_status="unchecked",
        output_sha256="sha256:" + hashlib.sha256(payload.encode()).hexdigest(),
        staging_id=".memoria/staging/projects/alpha/analysis.md",
        payload_text=payload,
        context=CONTEXT,
        inputs=[],
    )

    with state.connect(tmp_path) as conn:
        types = {
            row["concept_id"]: row["concept_type"]
            for row in conn.execute("SELECT concept_id, concept_type FROM concepts")
        }

    assert types["fulltexts/smith-2020.md"] == "work"
    assert types["projects/alpha/analysis.md"] == "project"


def test_mirror_prunes_absent_verdictless_rows_and_pends_inbound_edges(tmp_path: Path) -> None:
    _mirror(tmp_path, "notes/alpha.md", "notes/gone.md", "notes/kept.md")
    state.set_concept_verdict(tmp_path, "notes/kept.md", "checked")
    state.replace_concept_edges(
        tmp_path,
        [
            _edge_row("notes/alpha.md", "notes/gone.md"),
            _edge_row("notes/alpha.md", "notes/kept.md", "extends"),
        ],
    )

    result = state.rebuild_file_concept_mirror(
        tmp_path, [{"concept_id": "notes/alpha.md", "concept_type": "note"}]
    )

    with state.connect(tmp_path) as conn:
        ids = sorted(row["concept_id"] for row in conn.execute("SELECT concept_id FROM concepts"))
        edges = {
            row["target_path"]: dict(row) for row in conn.execute("SELECT * FROM concept_edges")
        }
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

    assert result["deleted"] == 1
    assert ids == ["notes/alpha.md", "notes/kept.md"]
    assert edges["notes/gone.md"]["target_concept_id"] is None
    assert edges["notes/kept.md"]["target_concept_id"] == "notes/kept.md"


def test_deleting_a_file_concept_cascades_its_outgoing_edges(tmp_path: Path) -> None:
    _mirror(tmp_path, "notes/alpha.md", "notes/beta.md")
    state.replace_concept_edges(tmp_path, [_edge_row("notes/alpha.md", "notes/beta.md")])

    state.rebuild_file_concept_mirror(
        tmp_path, [{"concept_id": "notes/beta.md", "concept_type": "note"}]
    )

    with state.connect(tmp_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM concept_edges").fetchone()[0] == 0


def test_empty_edge_scope_is_a_no_op_that_spares_direct_tension_rows(tmp_path: Path) -> None:
    _mirror(tmp_path, "notes/alpha.md", "notes/beta.md")
    with state.connect(tmp_path) as conn:
        conn.execute(
            "INSERT INTO concept_edges("
            " source_concept_id, relation_type, target_concept_id, target_path,"
            " check_status, source_path, updated_at)"
            " VALUES ('notes/alpha.md', 'tension', 'notes/beta.md', 'notes/beta.md',"
            " 'checked', '', '2026-07-15T00:00:00Z')"
        )

    assert state.replace_concept_edges(
        tmp_path, [_edge_row("notes/alpha.md", "notes/beta.md")], paths=[]
    ) == {"deleted": 0, "inserted": 0}

    with state.connect(tmp_path) as conn:
        rows = [dict(row) for row in conn.execute("SELECT * FROM concept_edges")]

    assert [(row["relation_type"], row["target_path"]) for row in rows] == [
        ("tension", "notes/beta.md")
    ]


def test_producer_rows_without_target_path_resolve_under_v16(tmp_path: Path) -> None:
    _mirror(tmp_path, "notes/alpha.md", "notes/beta.md")

    state.replace_concept_edges(tmp_path, [_edge_row("notes/alpha.md", "notes/beta.md")])

    edges = state.concept_edges(tmp_path)
    assert [
        (edge["target_concept_id"], edge["target_path"], edge["edge_id"]) for edge in edges
    ] == [
        (
            "notes/beta.md",
            "notes/beta.md",
            state.concept_edge_id("notes/alpha.md", "supports", "notes/beta.md"),
        )
    ]


def test_resolve_concept_id_reads_without_minting(tmp_path: Path) -> None:
    state.upsert_catalog_record(tmp_path, work_id="smith-2020", title="Smith 2020")

    with state.connect(tmp_path) as conn:
        resolved = [state.resolve_concept_id(conn, form) for form in CATALOG_FORMS]
        unknown = state.resolve_concept_id(conn, "./notes/ghost.md")
        count = conn.execute("SELECT COUNT(*) FROM concepts").fetchone()[0]

    assert resolved == ["smith-2020"] * len(CATALOG_FORMS)
    assert unknown == "notes/ghost.md"
    assert count == 1


def test_ensure_concept_parent_conn_is_idempotent_and_fails_closed(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        first = state.ensure_concept_parent_conn(
            conn, "notes/alpha.md", concept_type="note", store="file", path="notes/alpha.md"
        )
        second = state.ensure_concept_parent_conn(
            conn, "./notes/alpha.md", concept_type="note", store="file", path="notes/alpha.md"
        )
        catalog = state.ensure_concept_parent_conn(
            conn,
            "catalog/sources/smith-2020",
            concept_type="work",
            store="db",
            path="catalog/sources/smith-2020",
        )
        count = conn.execute("SELECT COUNT(*) FROM concepts").fetchone()[0]
        with pytest.raises(ValueError):
            state.ensure_concept_parent_conn(
                conn, "notes/beta.md", concept_type="gizmo", store="file", path="notes/beta.md"
            )

    assert first == second == "notes/alpha.md"
    assert catalog == "smith-2020"
    assert count == 2


def test_v16_cascade_triggers_use_bare_work_id_endpoints(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        trigger_sql = " ".join(
            str(row["sql"])
            for row in conn.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'trigger'"
                " AND name LIKE '%passage_cascade%'"
            )
        )

    assert trigger_sql
    assert "'catalog/sources/' ||" not in trigger_sql


def test_catalog_upsert_refuses_to_hijack_a_file_concept(tmp_path: Path) -> None:
    """Contract 10: an identity collision is never silently accepted."""
    with state.connect(tmp_path) as conn:
        state.ensure_concept_parent_conn(
            conn, "alpha.md", concept_type="note", store="file", path="alpha.md"
        )
        state._set_concept_verdict_conn(conn, "alpha.md", "checked")

    with pytest.raises(RuntimeError, match="concept identity collision"):
        state.upsert_catalog_record(tmp_path, work_id="alpha.md", title="Alpha")

    with state.connect(tmp_path) as conn:
        concept = conn.execute(
            "SELECT concept_id, concept_type, store, path FROM concepts"
        ).fetchall()
        verdicts = conn.execute("SELECT concept_id, check_status FROM concept_verdicts").fetchall()
        catalog = conn.execute("SELECT COUNT(*) FROM catalog_sources").fetchone()[0]
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

    # No silent mutation: type, store, path and the PI's verdict all survive.
    assert [tuple(row) for row in concept] == [("alpha.md", "note", "file", "alpha.md")]
    assert [tuple(row) for row in verdicts] == [("alpha.md", "checked")]
    assert catalog == 0


def test_mirror_rebuild_refuses_to_hijack_a_catalog_work(tmp_path: Path) -> None:
    """A catalog work's Concept is FK'd by catalog_sources; the mirror cannot re-shape it."""
    state.upsert_catalog_record(tmp_path, work_id="smith-2020", title="Smith 2020")

    with pytest.raises(RuntimeError, match="concept identity collision"):
        state.rebuild_file_concept_mirror(
            tmp_path,
            [{"concept_id": "catalog/sources/smith-2020", "concept_type": "note"}],
        )

    with state.connect(tmp_path) as conn:
        concept = conn.execute(
            "SELECT concept_id, concept_type, store, path FROM concepts"
        ).fetchall()
        work_id = conn.execute("SELECT work_id FROM catalog_sources").fetchone()[0]
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

    assert [tuple(row) for row in concept] == [
        ("smith-2020", "work", "db", "catalog/sources/smith-2020")
    ]
    assert str(work_id) == "smith-2020"


def test_two_identities_claiming_one_path_raise_a_descriptive_error(tmp_path: Path) -> None:
    """The NID-B.2 shape (ULID id + path attribute) must not surface a bare UNIQUE error."""
    first = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    second = "01BX5ZZKBKACTAV9WEVGEMMVRZ"
    with state.connect(tmp_path) as conn:
        state.ensure_concept_parent_conn(
            conn, first, concept_type="note", store="file", path="notes/alpha.md"
        )
        with pytest.raises(RuntimeError, match="concept identity collision") as excinfo:
            state.ensure_concept_parent_conn(
                conn, second, concept_type="note", store="file", path="notes/alpha.md"
            )
        owner = conn.execute(
            "SELECT concept_id FROM concepts WHERE path = 'notes/alpha.md'"
        ).fetchone()[0]

    message = str(excinfo.value)
    assert not isinstance(excinfo.value, sqlite3.IntegrityError)
    # Both shapes are named, so the re-key that hit the collision is diagnosable.
    assert first in message
    assert second in message
    assert "notes/alpha.md" in message
    assert str(owner) == first


def test_same_identity_rename_updates_the_path_instead_of_colliding(tmp_path: Path) -> None:
    """A rename is an attribute update: same id, requested path owned by nobody."""
    with state.connect(tmp_path) as conn:
        state.ensure_concept_parent_conn(
            conn, ULID_A, concept_type="note", store="file", path="notes/old.md"
        )
        state._set_concept_verdict_conn(conn, ULID_A, "checked")
        renamed = state.ensure_concept_parent_conn(
            conn, ULID_A, concept_type="note", store="file", path="notes/new.md"
        )
        concepts = conn.execute("SELECT concept_id, path FROM concepts").fetchall()
        verdicts = conn.execute("SELECT concept_id, check_status FROM concept_verdicts").fetchall()
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

    assert renamed == ULID_A
    assert [tuple(row) for row in concepts] == [(ULID_A, "notes/new.md")]
    # The PI's verdict rides along; a rename never drops it.
    assert [tuple(row) for row in verdicts] == [(ULID_A, "checked")]


def test_same_identity_concept_type_change_at_one_path_updates(tmp_path: Path) -> None:
    """An in-place concept_type change is an attribute update, not a collision."""
    with state.connect(tmp_path) as conn:
        state.ensure_concept_parent_conn(
            conn, ULID_A, concept_type="note", store="file", path="notes/alpha.md"
        )
        retyped = state.ensure_concept_parent_conn(
            conn, ULID_A, concept_type="hub", store="file", path="notes/alpha.md"
        )
        concepts = conn.execute("SELECT concept_id, concept_type, path FROM concepts").fetchall()

    assert retyped == ULID_A
    assert [tuple(row) for row in concepts] == [(ULID_A, "hub", "notes/alpha.md")]


def test_rename_onto_a_path_another_identity_owns_still_collides(tmp_path: Path) -> None:
    """The allowance is scoped to an unowned path; two ids for one path still raise."""
    with state.connect(tmp_path) as conn:
        state.ensure_concept_parent_conn(
            conn, ULID_A, concept_type="note", store="file", path="notes/alpha.md"
        )
        state.ensure_concept_parent_conn(
            conn, ULID_B, concept_type="note", store="file", path="notes/beta.md"
        )
        with pytest.raises(RuntimeError, match="concept identity collision") as excinfo:
            state.ensure_concept_parent_conn(
                conn, ULID_B, concept_type="note", store="file", path="notes/alpha.md"
            )
        paths = dict(conn.execute("SELECT concept_id, path FROM concepts").fetchall())

    message = str(excinfo.value)
    assert ULID_A in message and ULID_B in message and "notes/alpha.md" in message
    assert paths == {ULID_A: "notes/alpha.md", ULID_B: "notes/beta.md"}


def test_a_batch_rename_does_not_roll_back_the_whole_mirror_pass(tmp_path: Path) -> None:
    """One renamed row must not refuse — and so must not lose — its batch."""
    state.rebuild_file_concept_mirror(
        tmp_path,
        [
            {"concept_id": ULID_A, "concept_type": "note", "path": "notes/old.md"},
            {"concept_id": "notes/plain.md", "concept_type": "note"},
        ],
    )

    state.rebuild_file_concept_mirror(
        tmp_path,
        [
            {"concept_id": ULID_A, "concept_type": "note", "path": "notes/new.md"},
            {"concept_id": "notes/plain.md", "concept_type": "note"},
        ],
    )

    with state.connect(tmp_path) as conn:
        rows = dict(conn.execute("SELECT concept_id, path FROM concepts").fetchall())

    assert rows == {ULID_A: "notes/new.md", "notes/plain.md": "notes/plain.md"}


def test_flagging_an_unmirrored_concept_raises_a_descriptive_error(tmp_path: Path) -> None:
    """A missing FK parent is named, not surfaced as a bare IntegrityError."""
    with pytest.raises(RuntimeError) as excinfo:
        state.set_concept_flag(tmp_path, "notes/ghost.md", "stale", reason="upstream demoted")

    assert not isinstance(excinfo.value, sqlite3.IntegrityError)
    message = str(excinfo.value)
    assert "notes/ghost.md" in message
    assert "stale" in message


def _write(vault: Path, rel: str, frontmatter: str) -> None:
    path = vault / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}---\nBody.\n", encoding="utf-8")


def test_concept_key_for_file_prefers_a_valid_frontmatter_ulid(tmp_path: Path) -> None:
    _write(tmp_path, "notes/alpha.md", f"type: note\nid: {ULID_A}\n")
    _write(tmp_path, "notes/plain.md", "type: note\n")
    _write(tmp_path, "fulltexts/smith-2020.md", "type: fulltext\nid: smith-2020\n")

    assert state._concept_key_for_file(tmp_path, "notes/alpha.md") == ULID_A
    # A non-ULID identity keeps its B.1 path key, normalized.
    assert state._concept_key_for_file(tmp_path, "./notes/plain.md") == "notes/plain.md"
    assert (
        state._concept_key_for_file(tmp_path, "fulltexts/smith-2020.md")
        == "fulltexts/smith-2020.md"
    )
    # A staged payload is the identity of record before the file exists.
    assert (
        state._concept_key_for_file(
            tmp_path, "notes/ghost.md", f"---\ntype: note\nid: {ULID_B}\n---\n"
        )
        == ULID_B
    )
    assert state._concept_key_for_file(tmp_path, "notes/ghost.md") == "notes/ghost.md"


def test_check_status_projection_keys_by_rendered_path(tmp_path: Path) -> None:
    """The search index gates files by path, so the bulk verdict map must key by path."""
    _write(tmp_path, "notes/alpha.md", f"type: note\nid: {ULID_A}\ntitle: Alpha\n")
    state.record_observed_file_edit(
        tmp_path, output_id="notes/alpha.md", concept_type="note", output_sha256="sha256:beef"
    )
    state.set_concept_verdict(tmp_path, "notes/alpha.md", "checked")
    state.upsert_catalog_record(
        tmp_path, work_id="smith-2020", title="Smith 2020", check_status="checked"
    )

    assert state.concept_check_statuses(tmp_path) == {
        "notes/alpha.md": "checked",
        "catalog/sources/smith-2020": "checked",
    }


def test_observed_file_edit_keys_the_concept_by_its_frontmatter_ulid(tmp_path: Path) -> None:
    _write(tmp_path, "notes/alpha.md", f"type: note\nid: {ULID_A}\ntitle: Alpha\n")

    state.record_observed_file_edit(
        tmp_path, output_id="notes/alpha.md", concept_type="note", output_sha256="sha256:beef"
    )

    with state.connect(tmp_path) as conn:
        concepts = conn.execute(
            "SELECT concept_id, concept_type, store, path FROM concepts"
        ).fetchall()
        outputs = conn.execute("SELECT output_id FROM outputs").fetchall()
    assert [tuple(row) for row in concepts] == [(ULID_A, "note", "file", "notes/alpha.md")]
    # `outputs` keeps its own path-keyed space.
    assert [tuple(row) for row in outputs] == [("notes/alpha.md",)]
    # Path references still resolve onto the id-keyed row.
    assert state.concept_check_status(tmp_path, "notes/alpha.md") == "unchecked"
    state.set_concept_verdict(tmp_path, "notes/alpha.md", "checked")
    assert state.concept_check_status(tmp_path, ULID_A) == "checked"


def test_file_output_keys_by_payload_ulid_and_identity_keys_its_derivation(
    tmp_path: Path,
) -> None:
    state.upsert_catalog_record(tmp_path, work_id="smith-2020", title="Smith 2020")
    payload = f"---\ntype: note\nid: {ULID_A}\ntitle: Alpha\n---\n\nBody.\n"

    state.record_file_output(
        tmp_path,
        output_id="notes/alpha.md",
        concept_type="note",
        check_status="unchecked",
        output_sha256="sha256:" + hashlib.sha256(payload.encode()).hexdigest(),
        staging_id=".memoria/staging/notes/alpha.md",
        payload_text=payload,
        context=CONTEXT,
        inputs=[{"id": "catalog/sources/smith-2020/source.md", "role": "source"}],
    )

    with state.connect(tmp_path) as conn:
        concept = conn.execute(
            "SELECT concept_id, path FROM concepts WHERE store = 'file'"
        ).fetchone()
        derivations = conn.execute("SELECT input_id, output_id FROM derivations").fetchall()
        verdict = conn.execute("SELECT concept_id FROM concept_verdicts").fetchall()
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

    assert tuple(concept) == (ULID_A, "notes/alpha.md")
    # Both derivation endpoints are canonical identities, never renderings.
    assert [tuple(row) for row in derivations] == [("smith-2020", ULID_A)]
    assert sorted(str(row["concept_id"]) for row in verdict) == sorted([ULID_A, "smith-2020"])


def test_mirror_rebuild_keys_files_by_ulid_and_maps_types_through_the_registry(
    tmp_path: Path,
) -> None:
    copy_memoria_dirs(tmp_path, "schemas")
    _write(tmp_path, "notes/alpha.md", f"type: note\nid: {ULID_A}\ntitle: Alpha\n")
    # A fulltext's `id` is its work_id, not a ULID: it stays on its B.1 path key.
    _write(tmp_path, "fulltexts/smith-2020.md", "type: fulltext\nid: smith-2020\n")
    # Tolerant observation: an untrusted external file missing authored fields is
    # still mirrored, keyed by its path because it carries no ULID.
    _write(tmp_path, "notes/external.md", "type: note\n")

    rebuild_concept_mirror_from_files(tmp_path)

    with state.connect(tmp_path) as conn:
        rows = {
            str(row["concept_id"]): (str(row["concept_type"]), str(row["path"]))
            for row in conn.execute("SELECT concept_id, concept_type, path FROM concepts")
        }

    assert rows == {
        ULID_A: ("note", "notes/alpha.md"),
        "fulltexts/smith-2020.md": ("work", "fulltexts/smith-2020.md"),
        "notes/external.md": ("note", "notes/external.md"),
    }


def test_mirror_rebuild_keeps_one_identity_across_a_file_rename(tmp_path: Path) -> None:
    copy_memoria_dirs(tmp_path, "schemas")
    _write(tmp_path, "notes/old.md", f"type: note\nid: {ULID_A}\ntitle: Alpha\n")
    rebuild_concept_mirror_from_files(tmp_path)
    state.set_concept_verdict(tmp_path, "notes/old.md", "checked")

    (tmp_path / "notes/old.md").rename(tmp_path / "notes/new.md")
    rebuild_concept_mirror_from_files(tmp_path)

    with state.connect(tmp_path) as conn:
        rows = dict(conn.execute("SELECT concept_id, path FROM concepts").fetchall())
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

    assert rows == {ULID_A: "notes/new.md"}
    # The verdict rode the rename because the identity never moved.
    assert state.concept_check_status(tmp_path, "notes/new.md") == "checked"


def test_identity_correct_verdict_clears_a_path_written_stale_flag(tmp_path: Path) -> None:
    """set_concept_verdict resolves once: verdict and flag share one key space."""
    state.upsert_catalog_record(tmp_path, work_id="smith-2020", title="Smith 2020")
    # seeded_errors writes the flag in the rendered path form.
    state.set_concept_flag(tmp_path, "catalog/sources/smith-2020", "stale", reason="retracted")
    assert "stale" in state.concept_flags(tmp_path, "catalog/sources/smith-2020")

    # The identity-correct call is the one that must clear it.
    state.set_concept_verdict(tmp_path, "smith-2020", "checked")

    assert state.concept_flags(tmp_path, "smith-2020") == {}
    assert state.concept_flags(tmp_path, "catalog/sources/smith-2020") == {}
    assert state.concept_check_status(tmp_path, "smith-2020") == "checked"


def test_concept_flags_are_fk_backed_and_cascade_on_prune(tmp_path: Path) -> None:
    """Flags live inside v16's key discipline: no orphan survives a pruned Concept."""
    state.rebuild_file_concept_mirror(
        tmp_path, [{"concept_id": "notes/alpha.md", "concept_type": "note"}]
    )
    state.set_concept_flag(tmp_path, "notes/alpha.md", "stale", reason="upstream demoted")
    assert "stale" in state.concept_flags(tmp_path, "notes/alpha.md")

    with state.connect(tmp_path) as conn:
        flag_fks = {
            (row["table"], row["from"], row["to"], row["on_delete"])
            for row in conn.execute("PRAGMA foreign_key_list(concept_flags)")
        }
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO concept_flags(concept_id, flag, created_at)"
                " VALUES ('no-such-concept', 'stale', '2026-07-15T00:00:00Z')"
            )

    assert ("concepts", "concept_id", "concept_id", "CASCADE") in flag_fks

    # Pruning the verdictless file Concept must take its flag with it.
    state.rebuild_file_concept_mirror(tmp_path, [])

    with state.connect(tmp_path) as conn:
        concepts = conn.execute("SELECT COUNT(*) FROM concepts").fetchone()[0]
        flags = conn.execute("SELECT COUNT(*) FROM concept_flags").fetchone()[0]
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

    assert concepts == 0
    assert flags == 0
