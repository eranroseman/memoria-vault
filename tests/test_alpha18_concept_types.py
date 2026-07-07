"""Alpha.18 concept-type normalization contract tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from memoria_vault.engine import api
from memoria_vault.runtime import state
from memoria_vault.runtime.subsystems.lib import schema
from memoria_vault.runtime.vaultio import UNIVERSAL_CONCEPT_TYPES

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


def test_fresh_schema_accepts_only_alpha18_db_concept_types(tmp_path: Path) -> None:
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
            "SELECT concept_id, concept_type, store FROM concepts WHERE concept_id = ?",
            ("catalog/sources/alpha-work",),
        ).fetchone()

    assert tuple(row) == ("catalog/sources/alpha-work", "work", "db")


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
