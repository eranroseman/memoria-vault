"""Schema-version and migration-policy tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from tests.helpers import ROOT


def test_schema_lands_at_user_version_11(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        assert state.SCHEMA_VERSION == 11
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 11


def test_rejects_v6_without_migration(tmp_path: Path) -> None:
    db = tmp_path / state.DB_REL
    db.parent.mkdir(parents=True)
    with sqlite3.connect(db) as conn:
        conn.execute("PRAGMA user_version = 6")

    with pytest.raises(RuntimeError, match="unsupported Memoria DB schema version: 6"):
        state.connect(tmp_path)


def test_source_has_no_private_migration_helpers() -> None:
    offenders = [
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "src/memoria_vault").rglob("*.py")
        if "_migrate_" in path.read_text(encoding="utf-8")
    ]

    assert offenders == []
