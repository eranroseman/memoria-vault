"""Drift closure: concept-types.yaml is the single source of the DB Concept roster.

NODES spec §2 — the schema.sql CHECK must match the seeded registry exactly, the
same pattern the F1 audit demanded for the actor vocabulary. Any migration that
edits the concepts.concept_type CHECK must edit concept-types.yaml in the same
commit, and vice versa.
"""

from __future__ import annotations

import re
import sys
from importlib.resources import files

import pytest

from memoria_vault.runtime.vocabulary import schema

pytestmark = pytest.mark.contract


def _check_roster() -> set[str]:
    sql = files("memoria_vault.runtime").joinpath("schema.sql").read_text(encoding="utf-8")
    concepts = re.search(r"CREATE TABLE IF NOT EXISTS concepts\s*\((.*?)\);", sql, re.DOTALL)
    assert concepts, "concepts table not found in schema.sql"
    match = re.search(
        r"concept_type TEXT NOT NULL\s*CHECK \(concept_type IN \(([^)]*)\)",
        concepts.group(1),
    )
    assert match, "concepts.concept_type CHECK not found in schema.sql"
    values = set(re.findall(r"'([a-z-]+)'", match.group(1)))
    assert values, "concepts.concept_type CHECK parsed empty"
    return values


def test_registry_matches_db_check():
    registry = set(schema.load_concept_types())
    assert len(registry) == 10
    assert registry == _check_roster()


def test_check_roster_scopes_to_concepts_table(monkeypatch):
    sql = """
CREATE TABLE distractor (
    concept_type TEXT NOT NULL CHECK (concept_type IN ('distractor'))
);
CREATE TABLE IF NOT EXISTS concepts (
    concept_id TEXT PRIMARY KEY,
    concept_type TEXT NOT NULL CHECK (concept_type IN ('work', 'digest'))
);
"""

    class SyntheticSchema:
        def joinpath(self, name: str) -> SyntheticSchema:
            assert name == "schema.sql"
            return self

        def read_text(self, *, encoding: str) -> str:
            assert encoding == "utf-8"
            return sql

    monkeypatch.setattr(sys.modules[__name__], "files", lambda _: SyntheticSchema())

    assert _check_roster() == {"work", "digest"}
