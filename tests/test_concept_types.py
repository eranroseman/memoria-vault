"""Concept-type normalization contract tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from memoria_vault.engine import api
from memoria_vault.runtime import state
from memoria_vault.runtime.vaultio import UNIVERSAL_CONCEPT_TYPES
from memoria_vault.runtime.vocabulary import schema

pytestmark = pytest.mark.contract

DB_CONCEPT_TYPES = {
    "work",
    "digest",
    "note",
    "hub",
    "project",
    "capability",
    "operation",
    "skill",
    "adapter",
    "workflow",
}


def test_fresh_schema_accepts_only_current_db_concept_types(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        for concept_type in sorted(DB_CONCEPT_TYPES):
            conn.execute(
                "INSERT INTO concepts(concept_id, concept_type, store) VALUES (?, ?, 'file')",
                (f"{concept_type}/ok", concept_type),
            )

        for concept_type in ("source", "source-note", "person", "organization", "venue"):
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO concepts(concept_id, concept_type, store) VALUES (?, ?, 'file')",
                    (f"{concept_type}/bad", concept_type),
                )


def test_catalog_record_mirror_uses_work_concept_type(tmp_path: Path) -> None:
    state.upsert_catalog_record(
        tmp_path,
        work_id="alpha-work",
        title="Alpha Work",
        description="Fixture source.",
        resource="https://example.invalid/alpha",
        identifiers={},
        csl_json={},
        provider_coverage="partial",
        text_status="metadata-only",
        check_status="checked",
    )

    with state.connect(tmp_path) as conn:
        row = conn.execute(
            "SELECT concept_id, concept_type, store, path FROM concepts WHERE concept_id = ?",
            ("alpha-work",),
        ).fetchone()

    assert tuple(row) == ("alpha-work", "work", "db", "catalog/sources/alpha-work")


def test_work_graph_edges_rename_source_relation_to_published_in(tmp_path: Path) -> None:
    state.upsert_catalog_record(
        tmp_path,
        work_id="alpha-work",
        title="Alpha Work",
        description="Fixture source.",
        resource="https://example.invalid/alpha",
        identifiers={},
        csl_json={},
        provider_coverage="partial",
        text_status="metadata-only",
        check_status="checked",
    )

    state.replace_work_graph_edges(
        tmp_path,
        "alpha-work",
        [
            {
                "relation_type": "published_in",
                "target_id": "venue-1",
                "target_title": "Journal of Tests",
            }
        ],
    )
    with pytest.raises(sqlite3.IntegrityError):
        state.replace_work_graph_edges(
            tmp_path,
            "alpha-work",
            [{"relation_type": "source", "target_id": "venue-1"}],
        )


def test_deleted_markdown_types_are_not_loaded_or_publicly_accepted() -> None:
    loaded_types = schema.load_types()

    assert "work" not in loaded_types
    assert "source-note" not in loaded_types
    assert "work" not in api.CONCEPT_TYPES
    assert "source-note" not in api.CONCEPT_TYPES
    assert "work" not in UNIVERSAL_CONCEPT_TYPES
    assert "source-note" not in UNIVERSAL_CONCEPT_TYPES


def test_state_registry_mapping_agrees_with_the_schema_seam() -> None:
    """state's cached superset must never drift from schema.concept_type_for.

    `state._registry_concept_type` maps document types *and* registry members over
    one cached table because the v16 parent-ensure seam is on a hot path. That is a
    second source of truth, so pin it: over the document-type domain it returns
    exactly what the named `schema.concept_type_for` seam returns, and its extra
    domain is precisely the registry members themselves.
    """
    document_types = schema.load_types()
    registry = schema.load_concept_types()

    assert document_types
    for type_name in document_types:
        assert state._registry_concept_type(type_name) == schema.concept_type_for(type_name)
    for member in registry:
        assert state._registry_concept_type(member) == member

    assert set(state._concept_type_map()) == set(document_types) | set(registry)
    with pytest.raises(ValueError):
        state._registry_concept_type("gizmo")
