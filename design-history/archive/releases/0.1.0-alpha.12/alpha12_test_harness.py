"""Disposable alpha.12 design-spike tests."""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TMP = ROOT / ".agents" / "tmp"
WORK = TMP / "alpha12-fixture"
RESULTS = TMP / "alpha12-test-results.md"


@dataclass
class TestResult:
    name: str
    status: str
    details: list[str]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_jsonl(path: Path, events: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(event, sort_keys=True) + "\n" for event in events))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def connect_catalog(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS catalog_sources (
            source_id TEXT PRIMARY KEY,
            doi TEXT UNIQUE,
            title TEXT NOT NULL,
            citekey TEXT NOT NULL,
            metadata_status TEXT NOT NULL
                CHECK (metadata_status IN ('verified', 'partial', 'unverified')),
            check_status TEXT NOT NULL
                CHECK (check_status IN ('unchecked', 'checked', 'quarantined'))
        );
        CREATE TABLE IF NOT EXISTS concepts (
            concept_id TEXT PRIMARY KEY,
            type TEXT NOT NULL CHECK (type IN ('source', 'digest', 'note', 'hub', 'capability')),
            store TEXT NOT NULL CHECK (store IN ('db', 'file')),
            check_status TEXT NOT NULL
                CHECK (check_status IN ('unchecked', 'checked', 'quarantined'))
        );
        CREATE TABLE IF NOT EXISTS citations (
            concept_id TEXT NOT NULL REFERENCES concepts(concept_id),
            source_id TEXT NOT NULL REFERENCES catalog_sources(source_id),
            PRIMARY KEY (concept_id, source_id)
        );
        """
    )
    return conn


def materialize_from_events(log: Path, workspace: Path, *, require_payload: bool) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    conn = connect_catalog(workspace / "memoria.db")
    for event in read_jsonl(log):
        if event["type"] != "derived":
            continue
        for output in event["outputs"]:
            payload = output.get("payload")
            if require_payload and payload is None:
                raise ValueError(f"missing payload for {output['id']}")
            if output["store"] == "catalog":
                data = payload
                conn.execute(
                    """
                    INSERT OR REPLACE INTO catalog_sources
                    (source_id, doi, title, citekey, metadata_status, check_status)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data["source_id"],
                        data["doi"],
                        data["title"],
                        data["citekey"],
                        data["metadata_status"],
                        data["check_status"],
                    ),
                )
                conn.execute(
                    "INSERT OR REPLACE INTO concepts VALUES (?, 'source', 'db', ?)",
                    (data["source_id"], data["check_status"]),
                )
            elif output["store"] == "file":
                data = payload
                out_path = workspace / output["path"]
                out_path.parent.mkdir(parents=True, exist_ok=True)
                if sha256_text(data["body"]) != output["sha256"]:
                    raise ValueError(f"hash mismatch for {output['id']}")
                out_path.write_text(data["body"])
                conn.execute(
                    "INSERT OR REPLACE INTO concepts VALUES (?, ?, 'file', ?)",
                    (output["id"], data["type"], data["check_status"]),
                )
    conn.commit()
    conn.close()


def export_catalog(conn: sqlite3.Connection, export_path: Path) -> None:
    rows = conn.execute(
        """
        SELECT source_id, doi, title, citekey, metadata_status, check_status
        FROM catalog_sources
        ORDER BY source_id
        """
    ).fetchall()
    export_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "source_id": row[0],
            "doi": row[1],
            "title": row[2],
            "citekey": row[3],
            "metadata_status": row[4],
            "check_status": row[5],
        }
        for row in rows
    ]
    export_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def restore_catalog_from_export(export_path: Path, db_path: Path) -> sqlite3.Connection:
    conn = connect_catalog(db_path)
    for row in json.loads(export_path.read_text()):
        conn.execute(
            """
            INSERT INTO catalog_sources
            (source_id, doi, title, citekey, metadata_status, check_status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                row["source_id"],
                row["doi"],
                row["title"],
                row["citekey"],
                row["metadata_status"],
                row["check_status"],
            ),
        )
    conn.commit()
    return conn


def test_persistence_authority() -> TestResult:
    case = WORK / "persistence"
    case.mkdir(parents=True)
    log = case / "journal.jsonl"
    digest_body = "---\ntype: digest\ncheck_status: unchecked\n---\nDigest cites S1.\n"
    source = {
        "source_id": "sources/s1",
        "doi": "10.1000/example",
        "title": "Example Source",
        "citekey": "example2026",
        "metadata_status": "verified",
        "check_status": "unchecked",
    }

    hash_only_event = {
        "type": "derived",
        "run_id": "run-1",
        "outputs": [
            {"id": "sources/s1", "store": "catalog", "sha256": sha256_text(json.dumps(source))},
            {
                "id": "digests/s1",
                "store": "file",
                "path": "knowledge/digests/s1.md",
                "sha256": sha256_text(digest_body),
            },
        ],
    }
    write_jsonl(log, [hash_only_event])
    try:
        materialize_from_events(log, case / "recovered-hash-only", require_payload=True)
        hash_only_failed = False
    except ValueError:
        hash_only_failed = True

    payload_event = {
        "type": "derived",
        "run_id": "run-1",
        "outputs": [
            {
                "id": "sources/s1",
                "store": "catalog",
                "sha256": sha256_text(json.dumps(source, sort_keys=True)),
                "payload": source,
            },
            {
                "id": "digests/s1",
                "store": "file",
                "path": "knowledge/digests/s1.md",
                "sha256": sha256_text(digest_body),
                "payload": {"type": "digest", "check_status": "unchecked", "body": digest_body},
            },
        ],
    }
    write_jsonl(log, [payload_event])
    recovered = case / "recovered-with-payload"
    materialize_from_events(log, recovered, require_payload=True)
    row_count = sqlite3.connect(recovered / "memoria.db").execute(
        "SELECT COUNT(*) FROM catalog_sources WHERE source_id = 'sources/s1'"
    ).fetchone()[0]
    digest_exists = (recovered / "knowledge" / "digests" / "s1.md").exists()

    if hash_only_failed and row_count == 1 and digest_exists:
        return TestResult(
            "Persistence authority and crash replay",
            "FAIL",
            [
                "Hash-only derived events cannot replay materialization after staging is lost.",
                "Replay succeeds when the derived event carries durable payloads.",
                "Alpha.12 must specify event payloads or durable staging retention; hashes alone are insufficient.",
            ],
        )
    return TestResult("Persistence authority and crash replay", "FAIL", ["Unexpected replay behavior."])


def test_catalog_recovery() -> TestResult:
    case = WORK / "catalog-recovery"
    repo = case / "repo"
    repo.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Fixture"], cwd=repo, check=True)

    db = repo / "memoria.db"
    conn = connect_catalog(db)
    conn.execute(
        "INSERT INTO catalog_sources VALUES (?, ?, ?, ?, ?, ?)",
        ("sources/s1", "10.1000/example", "Example Source", "badkey", "partial", "checked"),
    )
    conn.commit()
    export = repo / "catalog" / "export.json"
    export_catalog(conn, export)
    subprocess.run(["git", "add", "catalog/export.json"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "export v1"], cwd=repo, check=True, stdout=subprocess.DEVNULL)

    conn.execute(
        """
        UPDATE catalog_sources
        SET citekey = 'corrected2026', metadata_status = 'verified'
        WHERE source_id = 'sources/s1'
        """
    )
    conn.commit()
    stale_restore = restore_catalog_from_export(export, case / "stale-restore.db")
    stale_row = stale_restore.execute(
        "SELECT citekey, metadata_status FROM catalog_sources WHERE source_id = 'sources/s1'"
    ).fetchone()
    stale_restore.close()

    export_catalog(conn, export)
    fresh_restore = restore_catalog_from_export(export, case / "fresh-restore.db")
    fresh_row = fresh_restore.execute(
        "SELECT citekey, metadata_status FROM catalog_sources WHERE source_id = 'sources/s1'"
    ).fetchone()
    fresh_restore.close()
    conn.close()

    if stale_row == ("badkey", "partial") and fresh_row == ("corrected2026", "verified"):
        return TestResult(
            "Catalog recovery from committed artifacts",
            "FAIL",
            [
                "Periodic export loses Memoria-owned catalog changes made after the last export.",
                "Recovery is complete only when export is regenerated before the DB is lost.",
                "Alpha.12 needs atomic tracked export per catalog commit or a SQLite backup/snapshot rule.",
            ],
        )
    return TestResult("Catalog recovery from committed artifacts", "FAIL", ["Unexpected recovery result."])


def test_cross_store_lifecycle() -> TestResult:
    case = WORK / "cross-store"
    case.mkdir(parents=True)
    conn = connect_catalog(case / "memoria.db")
    conn.execute("CREATE TEMP TABLE staged_sources (source_id TEXT PRIMARY KEY)")
    conn.execute("INSERT INTO staged_sources VALUES ('sources/s1')")
    conn.execute(
        "INSERT INTO catalog_sources VALUES (?, ?, ?, ?, ?, ?)",
        ("sources/s1", "10.1000/example", "Example Source", "example2026", "verified", "unchecked"),
    )
    conn.execute("INSERT INTO concepts VALUES ('digests/s1', 'digest', 'file', 'unchecked')")

    strict_ok = (
        conn.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM catalog_sources
                WHERE source_id = 'sources/s1' AND check_status = 'checked'
            )
            """
        ).fetchone()[0]
        == 1
    )
    staged_aware_ok = (
        conn.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM catalog_sources
                WHERE source_id = 'sources/s1' AND check_status = 'checked'
            )
            OR EXISTS (
                SELECT 1 FROM staged_sources WHERE source_id = 'sources/s1'
            )
            """
        ).fetchone()[0]
        == 1
    )
    conn.close()
    if not strict_ok and staged_aware_ok:
        return TestResult(
            "Cross-store same-operation citation lifecycle",
            "FAIL",
            [
                "A strict 'citation target must already be checked' oracle deadlocks source+digest in one operation.",
                "A staged-aware oracle can validate the same operation atomically.",
                "Alpha.12 should say citations may target checked rows or same-operation staged rows.",
            ],
        )
    return TestResult("Cross-store same-operation citation lifecycle", "FAIL", ["Unexpected oracle result."])


def parse_check_status(path: Path) -> str:
    text = path.read_text()
    for line in text.splitlines():
        if line.startswith("check_status:"):
            return line.split(":", 1)[1].strip()
    return "missing"


def test_checked_promotion_barrier() -> TestResult:
    case = WORK / "checked-barrier"
    staging = case / ".memoria" / "staging" / "knowledge" / "digests"
    knowledge = case / "knowledge" / "digests"
    staging.mkdir(parents=True)
    knowledge.mkdir(parents=True)
    machine = staging / "s1.md"
    machine.write_text("---\ntype: digest\ncheck_status: unchecked\n---\nMachine output\n")
    before_promote = not (knowledge / "s1.md").exists()

    checked = knowledge / "s1.md"
    checked.write_text(machine.read_text().replace("unchecked", "checked"))
    machine.unlink()

    pi_edit = case / "knowledge" / "notes" / "pi-live.md"
    pi_edit.parent.mkdir(parents=True)
    pi_edit.write_text("---\ntype: note\ncheck_status: unchecked\n---\nPI edit\n")

    consumable = [
        path
        for path in (case / "knowledge").rglob("*.md")
        if parse_check_status(path) == "checked"
    ]
    if before_promote and checked in consumable and pi_edit not in consumable:
        return TestResult(
            "Checked promotion and machine read barrier",
            "PASS",
            [
                "Machine output stays outside knowledge until checked promotion.",
                "PI live edit can exist in knowledge while machine consumers filter it out.",
            ],
        )
    return TestResult("Checked promotion and machine read barrier", "FAIL", ["Unchecked content leaked."])


def test_journal_projection_vocabulary() -> TestResult:
    case = WORK / "journal-projection"
    log = case / "journal.jsonl"
    events = [
        {"type": "requested", "operation_id": "ingest", "request_id": "req-1"},
        {"type": "derived", "request_id": "req-1", "output_id": "digests/s1"},
        {"type": "check-fired", "check": "span_entailment", "target_id": "digests/s1", "severity": "warn"},
        {"type": "checked", "target_id": "digests/s1", "status": "checked"},
        {"type": "resolved", "target_id": "digests/s1", "resolution": "accepted"},
    ]
    write_jsonl(log, events)
    queue: dict[str, str] = {}
    flags: dict[str, str] = {}
    status: dict[str, str] = {}
    for event in read_jsonl(log):
        if event["type"] == "requested":
            queue[event["request_id"]] = "requested"
        elif event["type"] == "derived":
            queue[event["request_id"]] = "derived"
            status[event["output_id"]] = "unchecked"
        elif event["type"] == "check-fired":
            flags[event["target_id"]] = "open"
        elif event["type"] == "checked":
            status[event["target_id"]] = event["status"]
        elif event["type"] == "resolved":
            flags[event["target_id"]] = "resolved"

    if queue == {"req-1": "derived"} and flags == {"digests/s1": "resolved"} and status == {
        "digests/s1": "checked"
    }:
        return TestResult(
            "Journal vocabulary and queue/flag projection rebuild",
            "PASS",
            [
                "requested, derived, check-fired, checked, and resolved can rebuild queue/flag/status views.",
                "The design should keep this full vocabulary in the journal contract.",
            ],
        )
    return TestResult("Journal vocabulary and queue/flag projection rebuild", "FAIL", ["Projection drift."])


def test_adapter_versioning() -> TestResult:
    domain = {
        "id": "digests/s1",
        "type": "digest",
        "title": "Example Digest",
        "body": "Synthesis",
        "citations": [{"source_id": "sources/s1", "doi": "10.1000/example"}],
    }

    file_v1 = {
        "frontmatter": {
            "type": domain["type"],
            "title": domain["title"],
            "citation_doi": domain["citations"][0]["doi"],
        },
        "body": domain["body"],
    }
    db_v1 = (domain["id"], domain["type"], domain["title"])
    llm_v1 = {"title": domain["title"], "summary": domain["body"]}
    llm_v2 = {"headline": domain["title"], "summary": domain["body"], "schema_version": "2"}
    mcp_v1 = {"name": "write_digest", "input_schema_version": "1"}

    stable_persistence = file_v1["frontmatter"]["title"] == "Example Digest" and db_v1[2] == "Example Digest"
    external_changed = llm_v1 != llm_v2 and mcp_v1["input_schema_version"] == "1"
    if stable_persistence and external_changed:
        return TestResult(
            "Canonical model with independently versioned adapters",
            "PASS",
            [
                "LLM output adapter can change without changing file or DB persistence shape.",
                "MCP schema is separately versioned from the LLM adapter.",
            ],
        )
    return TestResult("Canonical model with independently versioned adapters", "FAIL", ["Adapters coupled."])


def would_create_cycle(conn: sqlite3.Connection, input_id: str, output_id: str) -> bool:
    return (
        conn.execute(
            """
            WITH RECURSIVE descendants(node) AS (
                SELECT output_id FROM derivations WHERE input_id = ?
                UNION
                SELECT d.output_id
                FROM derivations d
                JOIN descendants ON d.input_id = descendants.node
            )
            SELECT EXISTS (SELECT 1 FROM descendants WHERE node = ?)
            """,
            (output_id, input_id),
        ).fetchone()[0]
        == 1
    )


def rollback_blast_radius(conn: sqlite3.Connection, root: str) -> list[str]:
    rows = conn.execute(
        """
        WITH RECURSIVE descendants(node) AS (
            SELECT output_id FROM derivations WHERE input_id = ?
            UNION
            SELECT d.output_id
            FROM derivations d
            JOIN descendants ON d.input_id = descendants.node
        )
        SELECT node FROM descendants ORDER BY node
        """,
        (root,),
    ).fetchall()
    return [row[0] for row in rows]


def test_sqlite_oracle_recursive_rollback() -> TestResult:
    case = WORK / "sqlite-oracle"
    case.mkdir(parents=True)
    conn = connect_catalog(case / "memoria.db")
    conn.executescript(
        """
        CREATE TABLE derivations (
            input_id TEXT NOT NULL REFERENCES concepts(concept_id),
            output_id TEXT NOT NULL REFERENCES concepts(concept_id),
            actor TEXT NOT NULL CHECK (actor IN ('pi', 'operation')),
            PRIMARY KEY (input_id, output_id)
        );
        """
    )
    conn.execute(
        "INSERT INTO catalog_sources VALUES (?, ?, ?, ?, ?, ?)",
        ("sources/s1", "10.1000/example", "Example Source", "example2026", "verified", "checked"),
    )
    conn.execute("INSERT INTO concepts VALUES ('sources/s1', 'source', 'db', 'checked')")
    conn.execute("INSERT INTO concepts VALUES ('digests/s1', 'digest', 'file', 'checked')")
    conn.execute("INSERT INTO concepts VALUES ('notes/n1', 'note', 'file', 'checked')")
    conn.execute("INSERT INTO concepts VALUES ('hubs/h1', 'hub', 'file', 'checked')")
    conn.execute("INSERT INTO derivations VALUES ('sources/s1', 'digests/s1', 'operation')")
    conn.execute("INSERT INTO derivations VALUES ('digests/s1', 'notes/n1', 'pi')")
    conn.execute("INSERT INTO derivations VALUES ('notes/n1', 'hubs/h1', 'operation')")

    duplicate_rejected = False
    try:
        conn.execute(
            "INSERT INTO catalog_sources VALUES (?, ?, ?, ?, ?, ?)",
            ("sources/s2", "10.1000/example", "Duplicate", "duplicate2026", "verified", "checked"),
        )
    except sqlite3.IntegrityError:
        duplicate_rejected = True

    bad_type_rejected = False
    try:
        conn.execute("INSERT INTO concepts VALUES ('bad/x', 'work', 'file', 'checked')")
    except sqlite3.IntegrityError:
        bad_type_rejected = True

    bad_fk_rejected = False
    try:
        conn.execute("INSERT INTO citations VALUES ('notes/n1', 'sources/missing')")
    except sqlite3.IntegrityError:
        bad_fk_rejected = True

    cycle_rejected = would_create_cycle(conn, "hubs/h1", "sources/s1")
    radius = rollback_blast_radius(conn, "sources/s1")
    conn.close()

    if duplicate_rejected and bad_type_rejected and bad_fk_rejected and cycle_rejected and radius == [
        "digests/s1",
        "hubs/h1",
        "notes/n1",
    ]:
        return TestResult(
            "SQLite oracle and recursive rollback fixture",
            "PASS",
            [
                "UNIQUE, FK, type enum, DAG check, and recursive blast-radius query all worked.",
                "The blast radius spans DB and file-backed concepts via the journal projection.",
            ],
        )
    return TestResult("SQLite oracle and recursive rollback fixture", "FAIL", ["Oracle or rollback failed."])


def write_results(results: list[TestResult]) -> None:
    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    lines = [
        "# alpha.12 disposable test results",
        "",
        f"Scratch: `{WORK}`",
        "",
        "## Summary",
        "",
        f"- PASS: {counts.get('PASS', 0)}",
        f"- FAIL: {counts.get('FAIL', 0)}",
        "",
        "## Results",
        "",
    ]
    for result in results:
        lines.append(f"### {result.status}: {result.name}")
        lines.append("")
        for detail in result.details:
            lines.append(f"- {detail}")
        lines.append("")
    RESULTS.write_text("\n".join(lines))


def main() -> int:
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    tests = [
        test_persistence_authority,
        test_catalog_recovery,
        test_cross_store_lifecycle,
        test_checked_promotion_barrier,
        test_journal_projection_vocabulary,
        test_adapter_versioning,
        test_sqlite_oracle_recursive_rollback,
    ]
    results = [test() for test in tests]
    write_results(results)
    for result in results:
        print(f"{result.status}: {result.name}")
    print(f"results: {RESULTS}")
    return 1 if any(result.status == "FAIL" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
