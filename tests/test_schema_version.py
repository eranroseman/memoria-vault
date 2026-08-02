"""Fresh-schema version-policy tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from tests.helpers import ROOT

pytestmark = pytest.mark.contract


def test_schema_lands_at_user_version_19(tmp_path: Path) -> None:
    # Both sides are literal on purpose: comparing the applied version to
    # `state.SCHEMA_VERSION` alone passes when the constant and the DDL drift together.
    with state.connect(tmp_path) as conn:
        assert state.SCHEMA_VERSION == 19
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 19


def test_rejects_incompatible_schema_version(tmp_path: Path) -> None:
    db = tmp_path / state.DB_REL
    db.parent.mkdir(parents=True)
    with sqlite3.connect(db) as conn:
        conn.execute("PRAGMA user_version = 6")

    with pytest.raises(RuntimeError, match="unsupported Memoria DB schema version: 6"):
        state.connect(tmp_path)


def _state_source() -> str:
    state_dir = ROOT / "src/memoria_vault/runtime/state"
    return "\n".join(
        p.read_text(encoding="utf-8") for p in sorted(state_dir.glob("*.py"))
    )


def test_state_has_no_schema_migration_ladder() -> None:
    source = _state_source()

    assert not hasattr(state, "MIGRATIONS")
    assert "_backfill_concept_edge_ids" not in source
    assert "migration from schema version" not in source
