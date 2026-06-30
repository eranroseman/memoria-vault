#!/usr/bin/env python3
"""Disposable alpha.12 pre-implementation storage spikes."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
RUN_DIR = SCRIPT_DIR / f"run-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"


class SpikeFailure(AssertionError):
    """A spike expectation was not met."""


@dataclass
class SpikeResult:
    name: str
    status: str
    observations: list[str] = field(default_factory=list)
    artifacts: list[Path] = field(default_factory=list)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SpikeFailure(message)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": "Memoria Spike",
            "GIT_AUTHOR_EMAIL": "spike@example.invalid",
            "GIT_COMMITTER_NAME": "Memoria Spike",
            "GIT_COMMITTER_EMAIL": "spike@example.invalid",
        }
    )
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise SpikeFailure(
            f"git {' '.join(args)} failed in {cwd}:\n{result.stdout}\n{result.stderr}"
        )
    return result


def spike_lifecycle_crash_fixture() -> SpikeResult:
    base = RUN_DIR / "01_lifecycle_crash"
    base.mkdir(parents=True)
    crash_points = [
        "requested",
        "staged",
        "check_passed",
        "db_commit_pending",
        "file_promoted_before_status",
        "complete",
    ]
    outcomes: dict[str, dict[str, str | bool | None]] = {}

    def init_db(db_path: Path) -> None:
        with connect(db_path) as conn:
            conn.executescript(
                """
                CREATE TABLE journal_events (
                    event_id INTEGER PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    output_id TEXT,
                    payload TEXT NOT NULL DEFAULT '{}'
                );
                CREATE TABLE outputs (
                    output_id TEXT PRIMARY KEY,
                    check_status TEXT NOT NULL,
                    materialization_status TEXT NOT NULL,
                    expected_hash TEXT NOT NULL,
                    consumable INTEGER NOT NULL DEFAULT 0,
                    failure_reason TEXT
                );
                """
            )

    def write_event(conn: sqlite3.Connection, event_type: str, output_id: str | None = None) -> None:
        conn.execute(
            "INSERT INTO journal_events(event_type, output_id) VALUES (?, ?)",
            (event_type, output_id),
        )

    def recover(case: Path) -> None:
        db_path = case / "state.sqlite"
        staging_path = case / "staging" / "note.md"
        final_path = case / "knowledge" / "note.md"
        with connect(db_path) as conn:
            row = conn.execute("SELECT * FROM outputs WHERE output_id = 'note-1'").fetchone()
            if row is None:
                if staging_path.exists():
                    staging_path.unlink()
                return

            if row["materialization_status"] == "materialized":
                require(final_path.exists(), "materialized DB row must have promoted file")
                require(sha256_file(final_path) == row["expected_hash"], "promoted file hash mismatch")
                return

            require(row["consumable"] == 0, "pending file output must not be consumable")
            if staging_path.exists() and sha256_file(staging_path) == row["expected_hash"]:
                final_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(staging_path), final_path)
                conn.execute(
                    """
                    UPDATE outputs
                    SET materialization_status = 'materialized', consumable = 1
                    WHERE output_id = 'note-1'
                    """
                )
                write_event(conn, "materialized", "note-1")
                return

            if final_path.exists() and sha256_file(final_path) == row["expected_hash"]:
                conn.execute(
                    """
                    UPDATE outputs
                    SET materialization_status = 'materialized', consumable = 1
                    WHERE output_id = 'note-1'
                    """
                )
                write_event(conn, "materialized", "note-1")
                return

            conn.execute(
                """
                UPDATE outputs
                SET materialization_status = 'failed',
                    failure_reason = 'missing staged or promoted payload',
                    consumable = 0
                WHERE output_id = 'note-1'
                """
            )

    for crash_point in crash_points:
        case = base / crash_point
        (case / "staging").mkdir(parents=True)
        (case / "knowledge").mkdir()
        db_path = case / "state.sqlite"
        init_db(db_path)
        payload = "# Checked note\n\nSource: doi:10.5555/alpha12\n"
        expected_hash = sha256_text(payload)

        with connect(db_path) as conn:
            write_event(conn, "requested", "note-1")
        if crash_point == "requested":
            recover(case)
        else:
            staging_path = case / "staging" / "note.md"
            staging_path.write_text(payload, encoding="utf-8")
            if crash_point == "staged":
                recover(case)
            else:
                with connect(db_path) as conn:
                    write_event(conn, "check-fired", "note-1")
                if crash_point == "check_passed":
                    recover(case)
                else:
                    with connect(db_path) as conn:
                        conn.execute(
                            """
                            INSERT INTO outputs(
                                output_id,
                                check_status,
                                materialization_status,
                                expected_hash,
                                consumable
                            )
                            VALUES ('note-1', 'checked', 'pending', ?, 0)
                            """,
                            (expected_hash,),
                        )
                        write_event(conn, "derived", "note-1")
                        write_event(conn, "checked", "note-1")
                    if crash_point == "db_commit_pending":
                        recover(case)
                    else:
                        final_path = case / "knowledge" / "note.md"
                        shutil.move(str(staging_path), final_path)
                        if crash_point == "file_promoted_before_status":
                            recover(case)
                        else:
                            with connect(db_path) as conn:
                                conn.execute(
                                    """
                                    UPDATE outputs
                                    SET materialization_status = 'materialized', consumable = 1
                                    WHERE output_id = 'note-1'
                                    """
                                )
                                write_event(conn, "materialized", "note-1")
                            recover(case)

        with connect(db_path) as conn:
            row = conn.execute("SELECT * FROM outputs WHERE output_id = 'note-1'").fetchone()
            pending_consumable = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM outputs
                WHERE materialization_status != 'materialized' AND consumable = 1
                """
            ).fetchone()["count"]
        require(pending_consumable == 0, f"{crash_point}: pending output became consumable")
        final_exists = (case / "knowledge" / "note.md").exists()
        outcomes[crash_point] = {
            "row_exists": row is not None,
            "materialization_status": None if row is None else row["materialization_status"],
            "consumable": None if row is None else bool(row["consumable"]),
            "final_file_exists": final_exists,
        }

    for early_point in ("requested", "staged", "check_passed"):
        require(
            outcomes[early_point]["row_exists"] is False,
            f"{early_point}: recovery should not promote without durable DB output row",
        )
    for durable_point in ("db_commit_pending", "file_promoted_before_status", "complete"):
        require(
            outcomes[durable_point]["materialization_status"] == "materialized",
            f"{durable_point}: recovery should reach materialized state",
        )
        require(outcomes[durable_point]["consumable"] is True, f"{durable_point}: not consumable")

    (base / "outcomes.json").write_text(json.dumps(outcomes, indent=2), encoding="utf-8")
    return SpikeResult(
        name="1. lifecycle/crash fixture",
        status="PASS",
        observations=[
            "No forced crash point left a pending file-owned output consumable.",
            "Crashes before the DB output row are recoverable only by discarding staged files.",
            "Crashes after the DB pending row require staged or promoted payload recovery.",
            "The fixture enforces checked as a check result; consumability requires materialized file output.",
        ],
        artifacts=[base / "outcomes.json"],
    )


def render_bibtex(source: dict[str, str]) -> str:
    return (
        "@article{"
        + source["citekey"]
        + ",\n"
        + "  title = {"
        + source["title"]
        + "},\n"
        + "  doi = {"
        + source["doi"]
        + "}\n"
        "}\n"
    )


def init_catalog(db_path: Path) -> None:
    with connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE sources (
                source_id TEXT PRIMARY KEY,
                citekey TEXT NOT NULL,
                title TEXT NOT NULL,
                doi TEXT NOT NULL,
                csl_json TEXT NOT NULL
            )
            """
        )


def upsert_source(db_path: Path, source: dict[str, str]) -> None:
    csl_json = json.dumps(source, sort_keys=True)
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO sources(source_id, citekey, title, doi, csl_json)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(source_id) DO UPDATE
            SET citekey = excluded.citekey,
                title = excluded.title,
                doi = excluded.doi,
                csl_json = excluded.csl_json
            """,
            (source["source_id"], source["citekey"], source["title"], source["doi"], csl_json),
        )


def generate_references_bib(db_path: Path, target: Path) -> None:
    with connect(db_path) as conn:
        rows = conn.execute("SELECT csl_json FROM sources ORDER BY citekey").fetchall()
    target.write_text(
        "\n".join(render_bibtex(json.loads(row["csl_json"])) for row in rows),
        encoding="utf-8",
    )


def spike_references_bib_durability() -> SpikeResult:
    base = RUN_DIR / "02_references_bib"
    stale = base / "stale_export"
    atomic = base / "atomic_export"
    stale.mkdir(parents=True)
    atomic.mkdir(parents=True)

    first = {
        "source_id": "S1",
        "citekey": "alpha2026",
        "title": "Alpha Baseline",
        "doi": "10.5555/alpha",
    }
    second = {
        "source_id": "S2",
        "citekey": "beta2026",
        "title": "New Catalog Source",
        "doi": "10.5555/beta",
    }

    stale_db = stale / "catalog.sqlite"
    init_catalog(stale_db)
    upsert_source(stale_db, first)
    generate_references_bib(stale_db, stale / "references.bib")
    upsert_source(stale_db, second)
    stale_db.unlink()
    stale_bib = (stale / "references.bib").read_text(encoding="utf-8")
    stale_lost_new_source = "beta2026" not in stale_bib and "10.5555/beta" not in stale_bib

    atomic_db = atomic / "catalog.sqlite"
    init_catalog(atomic_db)
    upsert_source(atomic_db, first)
    generate_references_bib(atomic_db, atomic / "references.bib")
    upsert_source(atomic_db, second)
    generate_references_bib(atomic_db, atomic / "references.bib")
    atomic_db.unlink()
    atomic_bib = (atomic / "references.bib").read_text(encoding="utf-8")
    atomic_preserved_new_source = "beta2026" in atomic_bib and "10.5555/beta" in atomic_bib

    require(stale_lost_new_source, "stale references.bib unexpectedly preserved new catalog source")
    require(atomic_preserved_new_source, "atomic references.bib export did not preserve new source")

    finding = {
        "stale_export_lost_new_source_after_db_loss": stale_lost_new_source,
        "atomic_export_preserved_new_source_after_db_loss": atomic_preserved_new_source,
    }
    (base / "outcomes.json").write_text(json.dumps(finding, indent=2), encoding="utf-8")
    return SpikeResult(
        name="2. references.bib durability",
        status="PASS",
        observations=[
            "Negative control confirmed stale references.bib loses new citation data after DB loss.",
            "Regenerating references.bib as part of the catalog-changing materialization path preserves takeout.",
            "The fixture enforces references.bib as a required materialized output for bibliography-changing catalog writes.",
        ],
        artifacts=[base / "outcomes.json", stale / "references.bib", atomic / "references.bib"],
    )


def init_protected_journal(db_path: Path) -> None:
    with connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE journal_events (
                event_id INTEGER PRIMARY KEY,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                row_hash TEXT NOT NULL
            );
            CREATE TRIGGER journal_no_update
            BEFORE UPDATE ON journal_events
            BEGIN
                SELECT RAISE(ABORT, 'journal is append-only');
            END;
            CREATE TRIGGER journal_no_delete
            BEFORE DELETE ON journal_events
            BEGIN
                SELECT RAISE(ABORT, 'journal is append-only');
            END;
            """
        )


def journal_hash(event_id: int, event_type: str, payload: str, prev_hash: str) -> str:
    canonical = json.dumps(
        {
            "event_id": event_id,
            "event_type": event_type,
            "payload": json.loads(payload),
            "prev_hash": prev_hash,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256_text(canonical)


def append_journal_event(db_path: Path, event_type: str, payload: dict[str, str]) -> None:
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    with connect(db_path) as conn:
        last = conn.execute(
            "SELECT event_id, row_hash FROM journal_events ORDER BY event_id DESC LIMIT 1"
        ).fetchone()
        prev_hash = "GENESIS" if last is None else last["row_hash"]
        event_id = 1 if last is None else last["event_id"] + 1
        row_hash = journal_hash(event_id, event_type, payload_json, prev_hash)
        conn.execute(
            """
            INSERT INTO journal_events(event_id, event_type, payload, prev_hash, row_hash)
            VALUES (?, ?, ?, ?, ?)
            """,
            (event_id, event_type, payload_json, prev_hash, row_hash),
        )


def verify_journal(db_path: Path, anchored_head: str | None = None) -> list[str]:
    errors: list[str] = []
    with connect(db_path) as conn:
        rows = conn.execute("SELECT * FROM journal_events ORDER BY event_id").fetchall()
    prev_hash = "GENESIS"
    previous_id = 0
    for row in rows:
        if row["event_id"] != previous_id + 1:
            errors.append(f"event_id gap or reorder at {row['event_id']}")
        if row["prev_hash"] != prev_hash:
            errors.append(f"prev_hash mismatch at {row['event_id']}")
        expected_hash = journal_hash(
            row["event_id"],
            row["event_type"],
            row["payload"],
            row["prev_hash"],
        )
        if row["row_hash"] != expected_hash:
            errors.append(f"row_hash mismatch at {row['event_id']}")
        prev_hash = row["row_hash"]
        previous_id = row["event_id"]
    if anchored_head is not None and prev_hash != anchored_head:
        errors.append("anchored head hash mismatch")
    return errors


def journal_head(db_path: Path) -> str:
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT row_hash FROM journal_events ORDER BY event_id DESC LIMIT 1"
        ).fetchone()
    require(row is not None, "journal has no head")
    return row["row_hash"]


def write_journal_anchor(anchor_path: Path, db_path: Path) -> None:
    with connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT
                MIN(event_id) AS first_event_id,
                MAX(event_id) AS last_event_id,
                (
                    SELECT row_hash
                    FROM journal_events
                    ORDER BY event_id DESC
                    LIMIT 1
                ) AS head_hash
            FROM journal_events
            """
        ).fetchone()
    require(row is not None and row["head_hash"], "cannot anchor an empty journal")
    anchor_path.write_text(
        json.dumps(
            {
                "tx_id": "tx:R1",
                "first_event_id": row["first_event_id"],
                "last_event_id": row["last_event_id"],
                "head_hash": row["head_hash"],
                "git_head": "fixture-git-head",
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def read_anchored_head(anchor_path: Path) -> str:
    return json.loads(anchor_path.read_text(encoding="utf-8"))["head_hash"]


def force_drop_journal_guards(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TRIGGER journal_no_update")
    conn.execute("DROP TRIGGER journal_no_delete")


def spike_sqlite_journal_integrity() -> SpikeResult:
    base = RUN_DIR / "03_journal_integrity"
    base.mkdir(parents=True)
    db_path = base / "journal.sqlite"
    init_protected_journal(db_path)
    append_journal_event(db_path, "requested", {"run": "R1"})
    append_journal_event(db_path, "derived", {"concept": "N1"})
    append_journal_event(db_path, "checked", {"concept": "N1"})
    anchor_path = base / "journal-head-anchor.json"
    write_journal_anchor(anchor_path, db_path)
    anchored_head = read_anchored_head(anchor_path)

    update_blocked = False
    delete_blocked = False
    with connect(db_path) as conn:
        try:
            conn.execute(
                "UPDATE journal_events SET payload = ? WHERE event_id = 2",
                (json.dumps({"concept": "tampered"}),),
            )
        except sqlite3.DatabaseError:
            update_blocked = True
        try:
            conn.execute("DELETE FROM journal_events WHERE event_id = 2")
        except sqlite3.DatabaseError:
            delete_blocked = True

    require(update_blocked, "journal UPDATE was not blocked by append-only trigger")
    require(delete_blocked, "journal DELETE was not blocked by append-only trigger")

    tampered_db = base / "tampered.sqlite"
    shutil.copy2(db_path, tampered_db)
    with connect(tampered_db) as conn:
        force_drop_journal_guards(conn)
        conn.execute(
            "UPDATE journal_events SET payload = ? WHERE event_id = 2",
            (json.dumps({"concept": "tampered"}, sort_keys=True),),
        )
    require(verify_journal(tampered_db, anchored_head), "hash verifier missed payload tampering")

    deleted_db = base / "deleted_middle.sqlite"
    shutil.copy2(db_path, deleted_db)
    with connect(deleted_db) as conn:
        force_drop_journal_guards(conn)
        conn.execute("DELETE FROM journal_events WHERE event_id = 2")
    require(verify_journal(deleted_db, anchored_head), "hash verifier missed middle-row deletion")

    rewritten_db = base / "rewritten_chain.sqlite"
    shutil.copy2(db_path, rewritten_db)
    with connect(rewritten_db) as conn:
        force_drop_journal_guards(conn)
        conn.execute(
            "UPDATE journal_events SET payload = ? WHERE event_id = 2",
            (json.dumps({"concept": "rewritten"}, sort_keys=True, separators=(",", ":")),),
        )
        rows = conn.execute("SELECT * FROM journal_events ORDER BY event_id").fetchall()
        prev_hash = "GENESIS"
        for row in rows:
            new_hash = journal_hash(row["event_id"], row["event_type"], row["payload"], prev_hash)
            conn.execute(
                """
                UPDATE journal_events
                SET prev_hash = ?, row_hash = ?
                WHERE event_id = ?
                """,
                (prev_hash, new_hash, row["event_id"]),
            )
            prev_hash = new_hash
    internal_errors = verify_journal(rewritten_db)
    anchored_errors = verify_journal(rewritten_db, anchored_head)
    require(not internal_errors, "fully rewritten chain should pass internal-only verification")
    require(
        any(error == "anchored head hash mismatch" for error in anchored_errors),
        "external anchored head did not detect fully rewritten journal",
    )

    outcome = {
        "anchor": json.loads(anchor_path.read_text(encoding="utf-8")),
        "update_blocked_by_trigger": update_blocked,
        "delete_blocked_by_trigger": delete_blocked,
        "payload_tamper_errors": verify_journal(tampered_db, anchored_head),
        "middle_delete_errors": verify_journal(deleted_db, anchored_head),
        "rewritten_chain_internal_errors": internal_errors,
        "rewritten_chain_anchored_errors": anchored_errors,
    }
    (base / "outcomes.json").write_text(json.dumps(outcome, indent=2), encoding="utf-8")
    return SpikeResult(
        name="3. SQLite journal integrity",
        status="PASS",
        observations=[
            "SQLite triggers can block ordinary UPDATE/DELETE attempts on journal rows.",
            "A hash chain detects payload mutation and deleted middle rows.",
            "A concrete external head anchor detects full journal rewrites that pass internal verification.",
            "The fixture enforces tamper-evidence as SQLite hash chain plus external git-trackable anchor.",
        ],
        artifacts=[
            base / "outcomes.json",
            anchor_path,
            db_path,
            tampered_db,
            deleted_db,
            rewritten_db,
        ],
    )


def spike_rollback_graph_fixture() -> SpikeResult:
    base = RUN_DIR / "04_rollback_graph"
    repo = base / "repo"
    repo.mkdir(parents=True)
    run_git(["init", "-q"], repo)
    run_git(["config", "user.name", "Memoria Spike"], repo)
    run_git(["config", "user.email", "spike@example.invalid"], repo)
    (repo / "knowledge").mkdir()
    (repo / "README.md").write_text("rollback fixture\n", encoding="utf-8")
    run_git(["add", "README.md"], repo)
    run_git(["commit", "-q", "-m", "fixture baseline"], repo)

    db_path = base / "rollback.sqlite"
    with connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE sources (
                source_id TEXT PRIMARY KEY,
                title TEXT NOT NULL
            );
            CREATE TABLE entities (
                entity_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL REFERENCES sources(source_id)
            );
            CREATE TABLE notes (
                note_id TEXT PRIMARY KEY,
                entity_id TEXT NOT NULL REFERENCES entities(entity_id),
                git_commit TEXT
            );
            CREATE TABLE rollback_edges (
                parent_id TEXT NOT NULL,
                child_id TEXT NOT NULL,
                relation TEXT NOT NULL
            );
            CREATE TABLE rollback_actions (
                action_id INTEGER PRIMARY KEY,
                table_name TEXT NOT NULL,
                pk_column TEXT NOT NULL,
                pk_value TEXT NOT NULL,
                action_type TEXT NOT NULL
            );
            """
        )
        conn.execute("INSERT INTO sources VALUES ('S1', 'Rollback Source')")
        conn.execute("INSERT INTO entities VALUES ('E1', 'S1')")
        conn.execute("INSERT INTO notes VALUES ('N1', 'E1', NULL)")
        conn.executemany(
            "INSERT INTO rollback_edges VALUES (?, ?, ?)",
            [
                ("run:R1", "source:S1", "created"),
                ("source:S1", "entity:E1", "extracted"),
                ("entity:E1", "note:N1", "materialized"),
            ],
        )
        conn.executemany(
            """
            INSERT INTO rollback_actions(table_name, pk_column, pk_value, action_type)
            VALUES (?, ?, ?, 'insert')
            """,
            [
                ("notes", "note_id", "N1"),
                ("entities", "entity_id", "E1"),
                ("sources", "source_id", "S1"),
            ],
        )

    note_path = repo / "knowledge" / "note-n1.md"
    note_path.write_text("# Rollback note\n\nSource: S1\n", encoding="utf-8")
    run_git(["add", "knowledge/note-n1.md"], repo)
    run_git(["commit", "-q", "-m", "materialize note N1"], repo)
    materialization_commit = run_git(["rev-parse", "HEAD"], repo).stdout.strip()
    with connect(db_path) as conn:
        conn.execute("UPDATE notes SET git_commit = ? WHERE note_id = 'N1'", (materialization_commit,))
        blast_radius = [
            row["node_id"]
            for row in conn.execute(
                """
                WITH RECURSIVE reach(node_id) AS (
                    VALUES ('run:R1')
                    UNION
                    SELECT rollback_edges.child_id
                    FROM rollback_edges
                    JOIN reach ON rollback_edges.parent_id = reach.node_id
                )
                SELECT node_id FROM reach ORDER BY node_id
                """
            )
        ]
    require(
        blast_radius == ["entity:E1", "note:N1", "run:R1", "source:S1"],
        f"unexpected blast radius: {blast_radius}",
    )

    with connect(db_path) as conn:
        actions = conn.execute(
            """
            SELECT * FROM rollback_actions
            ORDER BY action_id ASC
            """
        ).fetchall()
        for action in actions:
            require(action["action_type"] == "insert", "fixture only supports inverse delete")
            conn.execute(
                f"DELETE FROM {action['table_name']} WHERE {action['pk_column']} = ?",
                (action["pk_value"],),
            )
        conn.execute("DELETE FROM rollback_edges")
        remaining = {
            "sources": conn.execute("SELECT COUNT(*) AS count FROM sources").fetchone()["count"],
            "entities": conn.execute("SELECT COUNT(*) AS count FROM entities").fetchone()["count"],
            "notes": conn.execute("SELECT COUNT(*) AS count FROM notes").fetchone()["count"],
        }
    require(remaining == {"sources": 0, "entities": 0, "notes": 0}, f"DB rollback failed: {remaining}")

    run_git(["revert", "--no-edit", materialization_commit], repo)
    require(not note_path.exists(), "inverse git commit did not remove materialized note")
    log = run_git(["log", "--oneline", "-3"], repo).stdout
    require("Revert" in log, "git history does not show inverse revert commit")

    outcome = {
        "blast_radius": blast_radius,
        "materialization_commit": materialization_commit,
        "remaining_rows_after_db_rollback": remaining,
        "recent_git_log": log.splitlines(),
    }
    (base / "outcomes.json").write_text(json.dumps(outcome, indent=2), encoding="utf-8")
    return SpikeResult(
        name="4. rollback graph fixture",
        status="PASS",
        observations=[
            "Recursive CTE blast-radius traversal works for linked run/source/entity/note rows.",
            "Inverse SQLite deletes can remove DB-owned rows in dependency order.",
            "An inverse git commit can roll back file-owned materialization without rewriting history.",
        ],
        artifacts=[base / "outcomes.json", db_path, repo],
    )


def write_report(results: list[SpikeResult]) -> Path:
    report = RUN_DIR / "report.md"
    lines = [
        "# Alpha.12 Pre-Implementation Spikes 1-4",
        "",
        f"Run: {datetime.now(UTC).isoformat()}",
        f"Root: `{RUN_DIR}`",
        "",
        "## Summary",
        "",
        "| Spike | Status | Key result |",
        "|---|---|---|",
    ]
    for result in results:
        lines.append(
            f"| {result.name} | {result.status} | {result.observations[0]} |"
        )
    lines.append("")
    for result in results:
        lines.extend([f"## {result.name}", "", f"Status: `{result.status}`", ""])
        for observation in result.observations:
            lines.append(f"- {observation}")
        lines.append("")
        if result.artifacts:
            lines.append("Artifacts:")
            for artifact in result.artifacts:
                lines.append(f"- `{artifact}`")
            lines.append("")
    report.write_text("\n".join(lines), encoding="utf-8")
    return report


def main() -> int:
    RUN_DIR.mkdir(parents=True)
    spike_functions = [
        spike_lifecycle_crash_fixture,
        spike_references_bib_durability,
        spike_sqlite_journal_integrity,
        spike_rollback_graph_fixture,
    ]
    results: list[SpikeResult] = []
    failures: list[str] = []
    for spike in spike_functions:
        try:
            results.append(spike())
        except Exception as exc:  # noqa: BLE001 -- disposable fixture reports all spike failures.
            failures.append(f"{spike.__name__}: {exc}")
            results.append(
                SpikeResult(
                    name=spike.__name__,
                    status="FAIL",
                    observations=[str(exc)],
                )
            )

    report = write_report(results)
    payload = {
        "run_dir": str(RUN_DIR),
        "report": str(report),
        "results": [
            {
                "name": result.name,
                "status": result.status,
                "observations": result.observations,
                "artifacts": [str(artifact) for artifact in result.artifacts],
            }
            for result in results
        ],
        "failures": failures,
    }
    (RUN_DIR / "results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
