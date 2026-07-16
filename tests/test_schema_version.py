"""Schema-version and migration-policy tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from tests.helpers import ROOT


def test_schema_lands_at_user_version_15(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        assert state.SCHEMA_VERSION == 15
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 15


def test_code_artifact_purpose_migrates_v14_database_without_losing_runs(
    tmp_path: Path,
) -> None:
    legacy = tmp_path / "legacy"
    db = legacy / state.DB_REL
    db.parent.mkdir(parents=True)
    with sqlite3.connect(db) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(
            """
            CREATE TABLE code_artifacts (
                artifact_id TEXT PRIMARY KEY,
                project_path TEXT NOT NULL,
                record_path TEXT NOT NULL UNIQUE,
                source_dir TEXT NOT NULL,
                output_dir TEXT NOT NULL,
                purpose TEXT NOT NULL CHECK (purpose IN ('warrant', 'deliverable', 'both')),
                approved_command_json TEXT NOT NULL DEFAULT '[]',
                declared_inputs_json TEXT NOT NULL DEFAULT '[]',
                declared_outputs_json TEXT NOT NULL DEFAULT '[]',
                dependency_notes TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL CHECK (status IN ('draft', 'ready', 'failed', 'retired')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE code_runs (
                run_id TEXT PRIMARY KEY,
                artifact_id TEXT NOT NULL REFERENCES code_artifacts(artifact_id) ON DELETE CASCADE,
                command_json TEXT NOT NULL,
                cwd TEXT NOT NULL,
                sanitized_env_json TEXT NOT NULL DEFAULT '[]',
                input_hashes_json TEXT NOT NULL DEFAULT '{}',
                output_hashes_json TEXT NOT NULL DEFAULT '{}',
                stdout_sha256 TEXT NOT NULL DEFAULT '',
                stderr_sha256 TEXT NOT NULL DEFAULT '',
                stdout_path TEXT NOT NULL DEFAULT '',
                stderr_path TEXT NOT NULL DEFAULT '',
                exit_status INTEGER,
                timeout_result TEXT NOT NULL DEFAULT '',
                sandbox_backend TEXT NOT NULL DEFAULT '',
                sandbox_profile_hash TEXT NOT NULL DEFAULT '',
                state TEXT NOT NULL CHECK (state IN ('pending', 'running', 'succeeded', 'failed', 'unavailable')),
                started_at TEXT NOT NULL,
                ended_at TEXT
            );
            PRAGMA user_version = 14;
            """
        )
        conn.executemany(
            """
            INSERT INTO code_artifacts(
                artifact_id, project_path, record_path, source_dir, output_dir,
                purpose, status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "warrant-artifact",
                    "projects/alpha/project.md",
                    "projects/alpha/code/warrant-artifact.md",
                    "projects/alpha/code/warrant-artifact/src",
                    "projects/alpha/code/warrant-artifact/outputs",
                    "warrant",
                    "ready",
                    "2026-07-15T00:00:00Z",
                    "2026-07-15T00:00:00Z",
                ),
                (
                    "deliverable-artifact",
                    "projects/alpha/project.md",
                    "projects/alpha/code/deliverable-artifact.md",
                    "projects/alpha/code/deliverable-artifact/src",
                    "projects/alpha/code/deliverable-artifact/outputs",
                    "deliverable",
                    "ready",
                    "2026-07-15T00:00:00Z",
                    "2026-07-15T00:00:00Z",
                ),
                (
                    "both-artifact",
                    "projects/alpha/project.md",
                    "projects/alpha/code/both-artifact.md",
                    "projects/alpha/code/both-artifact/src",
                    "projects/alpha/code/both-artifact/outputs",
                    "both",
                    "ready",
                    "2026-07-15T00:00:00Z",
                    "2026-07-15T00:00:00Z",
                ),
            ],
        )
        conn.execute(
            """
            INSERT INTO code_runs(run_id, artifact_id, command_json, cwd, state, started_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "run-warrant",
                "warrant-artifact",
                '["python3", "main.py"]',
                "projects/alpha/code/warrant-artifact/src",
                "succeeded",
                "2026-07-15T00:01:00Z",
            ),
        )

    assert 14 in state.MIGRATIONS
    assert state.MIGRATIONS[14][0] == 15

    with state.connect(legacy) as conn:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        purposes = {
            row["artifact_id"]: row["purpose"]
            for row in conn.execute(
                "SELECT artifact_id, purpose FROM code_artifacts ORDER BY artifact_id"
            )
        }
        runs = [
            dict(row)
            for row in conn.execute(
                "SELECT run_id, artifact_id, command_json, cwd, state FROM code_runs"
            )
        ]
        foreign_key_violations = conn.execute("PRAGMA foreign_key_check").fetchall()

    assert version == state.SCHEMA_VERSION == 15
    assert purposes == {
        "both-artifact": "both",
        "deliverable-artifact": "deliverable",
        "warrant-artifact": "grounds",
    }
    assert runs == [
        {
            "run_id": "run-warrant",
            "artifact_id": "warrant-artifact",
            "command_json": '["python3", "main.py"]',
            "cwd": "projects/alpha/code/warrant-artifact/src",
            "state": "succeeded",
        }
    ]
    assert foreign_key_violations == []


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
