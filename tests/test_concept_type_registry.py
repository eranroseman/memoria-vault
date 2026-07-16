"""Drift closure: concept-types.yaml is the single source of the DB Concept roster.

NODES spec §2 — the schema.sql CHECK must match the seeded registry exactly, the
same pattern the F1 audit demanded for the actor vocabulary. Any migration that
edits the concepts.concept_type CHECK must edit concept-types.yaml in the same
commit, and vice versa.
"""

from __future__ import annotations

import re
from importlib.resources import files

from memoria_vault.runtime.subsystems.lib import schema


def _check_roster() -> set[str]:
    sql = files("memoria_vault.runtime").joinpath("schema.sql").read_text(encoding="utf-8")
    match = re.search(r"concept_type TEXT NOT NULL\s*CHECK \(concept_type IN \(([^)]*)\)", sql)
    assert match, "concepts.concept_type CHECK not found in schema.sql"
    values = set(re.findall(r"'([a-z-]+)'", match.group(1)))
    assert values, "concepts.concept_type CHECK parsed empty"
    return values


def test_registry_matches_db_check():
    registry = set(schema.load_concept_types())
    assert len(registry) == 10
    assert registry == _check_roster()
