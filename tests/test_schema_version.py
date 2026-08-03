"""Fresh-schema version-policy tests."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from unittest import mock

import pytest

from memoria_vault.runtime import state
from tests.helpers import ROOT

pytestmark = pytest.mark.contract

# sha256 of the schema.sql text _schema_sql() loads, pinned per SCHEMA_VERSION.
SCHEMA_SQL_SHA256 = "232897433f4458c1a8b91ee748e94e293b44aac0ddc9fed3f7a5174e5207dab0"


def test_schema_lands_at_user_version_19(tmp_path: Path) -> None:
    # Both sides are literal on purpose: comparing the applied version to
    # `state.SCHEMA_VERSION` alone passes when the constant and the DDL drift together.
    with state.connect(tmp_path) as conn:
        assert state.SCHEMA_VERSION == 19
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 19


def test_schema_sql_is_hash_pinned_to_schema_version() -> None:
    # connect() skips the DDL on current DBs, so an edit to schema.sql that
    # ships without a SCHEMA_VERSION bump silently never reaches existing
    # vaults. Pin the DDL bytes so any edit forces the bump decision.
    digest = hashlib.sha256(state._schema_sql().encode("utf-8")).hexdigest()
    assert digest == SCHEMA_SQL_SHA256, (
        "schema.sql changed: bump SCHEMA_VERSION in"
        " src/memoria_vault/runtime/state/__init__.py and update this hash —"
        " existing vaults only receive DDL through a version bump."
    )


def test_rejects_incompatible_schema_version(tmp_path: Path) -> None:
    db = tmp_path / state.DB_REL
    db.parent.mkdir(parents=True)
    with sqlite3.connect(db) as conn:
        conn.execute("PRAGMA user_version = 6")

    with pytest.raises(RuntimeError, match="unsupported Memoria DB schema version: 6"):
        state.connect(tmp_path)


def _state_source() -> str:
    state_dir = ROOT / "src/memoria_vault/runtime/state"
    files = sorted(state_dir.rglob("*.py"))
    assert files, "state source glob found no files; ROOT or state_dir is wrong"
    return "\n".join(p.read_text(encoding="utf-8") for p in files)


def test_state_has_no_schema_migration_ladder() -> None:
    source = _state_source()

    assert not hasattr(state, "MIGRATIONS")
    assert "_backfill_concept_edge_ids" not in source
    assert "migration from schema version" not in source


def test_connect_skips_schema_script_when_db_is_current(tmp_path: Path) -> None:
    """1733: _init re-ran the full schema.sql on EVERY connect (~19.6ms each,
    300-700 connects per heavy test). A current DB must skip the script."""

    vault = tmp_path / "vault"
    vault.mkdir()
    with state.connect(vault):
        pass  # first connect creates and initializes the DB

    # Patch _schema_sql to detect if it's called (a sign that executescript was invoked)
    call_count = [0]
    original_schema_sql = state._schema_sql

    def counting_schema_sql():
        call_count[0] += 1
        return original_schema_sql()

    with mock.patch("memoria_vault.runtime.state._schema_sql", side_effect=counting_schema_sql):
        with state.connect(vault) as conn:
            version = int(conn.execute("PRAGMA user_version").fetchone()[0])

    assert call_count[0] == 0, "second connect must not call _schema_sql (i.e., no executescript)"
    assert version == state.SCHEMA_VERSION


def test_connect_still_initializes_a_fresh_db(tmp_path: Path) -> None:
    vault = tmp_path / "vault2"
    vault.mkdir()
    with state.connect(vault) as conn:
        version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}

    assert version == state.SCHEMA_VERSION
    assert "concepts" in tables
