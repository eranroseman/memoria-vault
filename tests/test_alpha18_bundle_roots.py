"""Alpha.19 bundle-root and fulltexts contract tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.subsystems.lib import schema


def test_alpha19_bundle_roots_and_fulltexts_schema() -> None:
    folders = schema.load_folders()
    types = schema.load_types()

    assert schema.bundle_roots(folders) == ("notes", "hubs", "projects", "digests", "fulltexts")
    assert schema.home_for("digest", folders) == "digests"
    assert schema.home_for("fulltext", folders) == "fulltexts"
    assert "works" not in folders["skeleton"]
    assert "sources" not in folders["skeleton"]
    assert "system/eval" not in folders["skeleton"]
    assert ".memoria/eval" in folders["skeleton"]
    assert ".memoria/templates" in folders["skeleton"]
    assert ".memoria/patterns" in folders["skeleton"]
    assert ".memoria/journal" in folders["skeleton"]
    assert "fulltext" in types
    assert (
        schema.validate_frontmatter(
            {
                "type": "fulltext",
                "id": "source-alpha",
                "title": "Alpha Full Text",
                "tags": [],
                "links": {},
                "work_id": "source-alpha",
            },
            types["fulltext"],
        )
        == []
    )


def test_fulltext_is_not_a_db_concept_type(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO concepts(concept_id, concept_type, store) VALUES (?, ?, 'file')",
                ("fulltexts/source-alpha.md", "fulltext"),
            )
