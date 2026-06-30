"""SQLite-backed alpha.12 working state for queue, journal, catalog, and barriers."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.audit import EMPTY_SHA256, sha256_file
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.time import now_iso

DB_REL = ".memoria/state/memoria.sqlite"
TRIGGER_TYPES = frozenset({"command", "file_change", "schedule"})
REQUEST_STATUSES = frozenset({"pending", "running", "done", "failed"})


def db_path(vault: Path) -> Path:
    return Path(vault) / DB_REL


def connect(vault: Path) -> sqlite3.Connection:
    path = db_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    _init(conn)
    return conn


def request_envelope(
    *,
    request_id: str,
    trigger_type: str,
    operation_id: str,
    args: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
    target_path: str = "",
    target_hash: str = "",
    causal_refs: Iterable[str | dict[str, Any]] = (),
    actor: str = "pi",
    provenance: dict[str, Any] | None = None,
    schedule_id: str | None = None,
) -> dict[str, Any]:
    trigger = trigger_type.strip()
    if trigger not in TRIGGER_TYPES:
        raise ValueError(f"trigger_type must be one of {sorted(TRIGGER_TYPES)}")
    operation = operation_id.strip()
    if not operation:
        raise ValueError("operation_id is required")
    return {
        "request_id": safe_filename(request_id),
        "trigger_type": trigger,
        "operation_id": operation,
        "args": dict(args or {}),
        "idempotency_key": idempotency_key or request_id,
        "target_path": normalize_path(target_path) if target_path else "",
        "target_hash": target_hash,
        "causal_refs": _json_rows(causal_refs),
        "actor": actor.strip() or "pi",
        "provenance": dict(provenance or {}),
        "schedule_id": schedule_id or None,
    }


def save_request(vault: Path, envelope: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
    created_at = str(job.get("created_at") or now_iso())
    job = {**job, "request_envelope": envelope}
    payload = _json(job)
    idem = str(envelope.get("idempotency_key") or envelope["request_id"])
    with connect(vault) as conn:
        existing = conn.execute(
            """
            SELECT job_json
            FROM operation_requests
            WHERE request_id = ? OR idempotency_key = ?
            LIMIT 1
            """,
            (envelope["request_id"], idem),
        ).fetchone()
        if existing is not None:
            return json.loads(existing["job_json"])
        conn.execute(
            """
            INSERT INTO operation_requests(
                request_id,
                trigger_type,
                operation_id,
                args_json,
                idempotency_key,
                target_path,
                target_hash,
                causal_refs_json,
                actor,
                provenance_json,
                schedule_id,
                status,
                created_at,
                kind,
                job_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
            """,
            (
                envelope["request_id"],
                envelope["trigger_type"],
                envelope["operation_id"],
                _json(envelope["args"]),
                idem,
                envelope["target_path"],
                envelope["target_hash"],
                _json(envelope["causal_refs"]),
                envelope["actor"],
                _json(envelope["provenance"]),
                envelope["schedule_id"],
                created_at,
                str(job.get("kind") or "operation"),
                payload,
            ),
        )
    return job


def request_job(vault: Path, request_id: str) -> dict[str, Any] | None:
    with connect(vault) as conn:
        row = conn.execute(
            "SELECT job_json FROM operation_requests WHERE request_id = ?",
            (safe_filename(request_id),),
        ).fetchone()
    return json.loads(row["job_json"]) if row is not None else None


def next_pending_job(vault: Path) -> dict[str, Any] | None:
    with connect(vault) as conn:
        row = conn.execute(
            """
            SELECT job_json
            FROM operation_requests
            WHERE status = 'pending'
            ORDER BY created_at, request_id
            LIMIT 1
            """
        ).fetchone()
    return json.loads(row["job_json"]) if row is not None else None


def set_request_running(vault: Path, request_id: str, job: dict[str, Any]) -> None:
    _set_request_state(vault, request_id, "running", {**job, "status": "running"})


def finish_request(vault: Path, request_id: str, status: str, job: dict[str, Any]) -> None:
    _set_request_state(vault, request_id, status, job)


def append_journal_event(vault: Path, event: dict[str, Any], *, machine: str | None = None) -> None:
    row = dict(event)
    timestamp = str(row.get("timestamp") or now_iso())
    event_type = str(row.get("event") or row.get("type") or "event")
    machine_name = safe_filename(machine or "local")
    payload = _json(row)
    with connect(vault) as conn:
        conn.execute("BEGIN IMMEDIATE")
        last = conn.execute(
            "SELECT event_id, row_hash FROM journal_events ORDER BY event_id DESC LIMIT 1"
        ).fetchone()
        prev_hash = "GENESIS" if last is None else str(last["row_hash"])
        event_id = 1 if last is None else int(last["event_id"]) + 1
        row_hash = _journal_hash(event_id, timestamp, event_type, machine_name, payload, prev_hash)
        conn.execute(
            """
            INSERT INTO journal_events(
                event_id, timestamp, event_type, machine, payload_json, prev_hash, row_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (event_id, timestamp, event_type, machine_name, payload, prev_hash, row_hash),
        )


def journal_head(vault: Path) -> str:
    with connect(vault) as conn:
        row = conn.execute(
            "SELECT row_hash FROM journal_events ORDER BY event_id DESC LIMIT 1"
        ).fetchone()
    return "" if row is None else str(row["row_hash"])


def record_file_output(
    vault: Path,
    *,
    output_id: str,
    concept_type: str,
    check_status: str,
    output_sha256: str,
    staging_id: str,
    payload_text: str,
    actor: str,
    inputs: Iterable[dict[str, Any]],
) -> None:
    target = normalize_path(output_id)
    if not payload_text:
        raise ValueError("file materialization payload is required")
    if _sha256_text(payload_text) != output_sha256:
        raise ValueError(f"materialization payload hash mismatch for {target}")
    with connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO concepts(concept_id, concept_type, store, check_status)
            VALUES (?, ?, 'file', ?)
            ON CONFLICT(concept_id) DO UPDATE SET
                concept_type = excluded.concept_type,
                store = excluded.store,
                check_status = excluded.check_status
            """,
            (target, concept_type, check_status),
        )
        conn.execute(
            """
            INSERT INTO outputs(
                output_id,
                concept_type,
                store,
                target_path,
                staging_path,
                check_status,
                materialization_status,
                output_sha256
            )
            VALUES (?, ?, 'file', ?, ?, ?, 'pending', ?)
            ON CONFLICT(output_id) DO UPDATE SET
                concept_type = excluded.concept_type,
                store = excluded.store,
                target_path = excluded.target_path,
                staging_path = excluded.staging_path,
                check_status = excluded.check_status,
                materialization_status = 'pending',
                output_sha256 = excluded.output_sha256,
                failure_reason = NULL
            """,
            (target, concept_type, target, staging_id, check_status, output_sha256),
        )
        conn.execute(
            """
            INSERT INTO materialization_payloads(output_id, expected_sha256, payload_text)
            VALUES (?, ?, ?)
            ON CONFLICT(output_id) DO UPDATE SET
                expected_sha256 = excluded.expected_sha256,
                payload_text = excluded.payload_text
            """,
            (target, output_sha256, payload_text),
        )
        for row in inputs:
            input_id = row.get("id") if isinstance(row, dict) else None
            if isinstance(input_id, str) and input_id.strip():
                conn.execute(
                    """
                    INSERT OR IGNORE INTO derivations(input_id, output_id, actor)
                    VALUES (?, ?, ?)
                    """,
                    (normalize_path(input_id), target, actor),
                )


def mark_checked(vault: Path, output_id: str, output_sha256: str, payload_text: str = "") -> None:
    target = normalize_path(output_id)
    with connect(vault) as conn:
        conn.execute(
            "UPDATE outputs SET check_status = 'checked', output_sha256 = ? WHERE output_id = ?",
            (output_sha256, target),
        )
        conn.execute(
            "UPDATE concepts SET check_status = 'checked' WHERE concept_id = ?",
            (target,),
        )
        if payload_text:
            if _sha256_text(payload_text) != output_sha256:
                raise ValueError(f"checked payload hash mismatch for {target}")
            conn.execute(
                """
                UPDATE materialization_payloads
                SET expected_sha256 = ?, payload_text = ?
                WHERE output_id = ?
                """,
                (output_sha256, payload_text, target),
            )


def mark_materialized(vault: Path, output_id: str, *, commit: str = "") -> None:
    target = normalize_path(output_id)
    with connect(vault) as conn:
        conn.execute(
            """
            UPDATE outputs
            SET materialization_status = 'materialized',
                materialized_commit = ?,
                failure_reason = NULL
            WHERE output_id = ?
            """,
            (commit, target),
        )


def recover_pending_materializations(vault: Path) -> list[str]:
    restored: list[str] = []
    with connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT o.output_id, o.target_path, o.output_sha256, p.payload_text
            FROM outputs o
            LEFT JOIN materialization_payloads p ON p.output_id = o.output_id
            WHERE o.store = 'file'
              AND o.check_status = 'checked'
              AND o.materialization_status = 'pending'
            ORDER BY o.output_id
            """
        ).fetchall()
        for row in rows:
            target = Path(vault) / str(row["target_path"])
            expected = str(row["output_sha256"])
            if target.is_file() and sha256_file(target) == expected:
                conn.execute(
                    "UPDATE outputs SET materialization_status = 'materialized' WHERE output_id = ?",
                    (row["output_id"],),
                )
                continue
            payload = row["payload_text"]
            if not isinstance(payload, str) or not payload:
                conn.execute(
                    """
                    UPDATE outputs
                    SET materialization_status = 'failed',
                        failure_reason = 'missing durable materialization payload'
                    WHERE output_id = ?
                    """,
                    (row["output_id"],),
                )
                continue
            if _sha256_text(payload) != expected:
                conn.execute(
                    """
                    UPDATE outputs
                    SET materialization_status = 'failed',
                        failure_reason = 'materialization payload hash mismatch'
                    WHERE output_id = ?
                    """,
                    (row["output_id"],),
                )
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(payload, encoding="utf-8")
            conn.execute(
                "UPDATE outputs SET materialization_status = 'materialized' WHERE output_id = ?",
                (row["output_id"],),
            )
            restored.append(str(row["target_path"]))
    return restored


def upsert_catalog_source(vault: Path, source_rel: str, frontmatter: dict[str, Any]) -> None:
    source_id = str(frontmatter.get("source_id") or "").strip()
    if not source_id:
        raise ValueError("catalog source requires source_id")
    identifiers = (
        frontmatter.get("identifiers") if isinstance(frontmatter.get("identifiers"), dict) else {}
    )
    csl_json = frontmatter.get("csl_json") if isinstance(frontmatter.get("csl_json"), dict) else {}
    doi = str(identifiers.get("doi") or csl_json.get("DOI") or "").strip() or None
    with connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO catalog_sources(
                source_id,
                concept_path,
                doi,
                title,
                resource,
                identifiers_json,
                citekey,
                csl_json,
                metadata_status,
                check_status,
                content_hash,
                raw_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
                concept_path = excluded.concept_path,
                doi = excluded.doi,
                title = excluded.title,
                resource = excluded.resource,
                identifiers_json = excluded.identifiers_json,
                citekey = excluded.citekey,
                csl_json = excluded.csl_json,
                metadata_status = excluded.metadata_status,
                check_status = excluded.check_status,
                content_hash = excluded.content_hash,
                raw_hash = excluded.raw_hash
            """,
            (
                source_id,
                normalize_path(source_rel),
                doi,
                str(frontmatter.get("title") or source_id),
                str(frontmatter.get("resource") or ""),
                _json(identifiers),
                str(frontmatter.get("citekey") or csl_json.get("id") or ""),
                _json(csl_json),
                str(frontmatter.get("metadata_status") or "partial"),
                str(frontmatter.get("check_status") or "unchecked"),
                str(frontmatter.get("normalized_text_sha256") or ""),
                str(frontmatter.get("raw_text_sha256") or ""),
            ),
        )
        concept_id = f"catalog/sources/{source_id}"
        conn.execute(
            """
            INSERT INTO concepts(concept_id, concept_type, store, check_status)
            VALUES (?, 'source', 'db', ?)
            ON CONFLICT(concept_id) DO UPDATE SET
                store = excluded.store,
                check_status = excluded.check_status
            """,
            (concept_id, str(frontmatter.get("check_status") or "unchecked")),
        )


def catalog_sources(vault: Path, *, checked_only: bool = True) -> list[dict[str, Any]]:
    if not db_path(vault).is_file():
        return []
    with connect(vault) as conn:
        if checked_only:
            rows = conn.execute(
                """
                SELECT *
                FROM catalog_sources
                WHERE check_status = 'checked'
                ORDER BY source_id
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT *
                FROM catalog_sources
                ORDER BY source_id
                """
            ).fetchall()
    return [_source_row(row) for row in rows]


def has_catalog_sources(vault: Path) -> bool:
    if not db_path(vault).is_file():
        return False
    with connect(vault) as conn:
        row = conn.execute("SELECT COUNT(*) AS count FROM catalog_sources").fetchone()
    return bool(row and row["count"])


def compact_citation(vault: Path, source_ref: str) -> dict[str, Any]:
    if not db_path(vault).is_file():
        return {}
    source_id = _source_id(source_ref)
    with connect(vault) as conn:
        row = conn.execute(
            "SELECT * FROM catalog_sources WHERE source_id = ?",
            (source_id,),
        ).fetchone()
    if row is None:
        return {}
    source = _source_row(row)
    csl = source.get("csl_json") if isinstance(source.get("csl_json"), dict) else {}
    identifiers = source.get("identifiers") if isinstance(source.get("identifiers"), dict) else {}
    citation: dict[str, Any] = {
        "source_id": f"catalog/sources/{source_id}",
        "title": source["title"],
        "authors": _csl_authors(csl),
        "issued": _csl_issued(csl),
    }
    if doi := str(identifiers.get("doi") or csl.get("DOI") or "").strip():
        citation["doi"] = doi
    elif url := str(source.get("resource") or csl.get("URL") or "").strip():
        citation["url"] = url
    else:
        citation["citekey"] = str(source.get("citekey") or source_id)
    return citation


def check_citation_payload(frontmatter: dict[str, Any]) -> list[str]:
    concept_type = frontmatter.get("type")
    if concept_type not in {"note", "digest", "hub"}:
        return []
    refs = _source_refs(frontmatter)
    if not refs:
        return []
    citations = frontmatter.get("citations")
    if not isinstance(citations, list):
        return ["missing citations payload"]
    by_source = {
        str(row.get("source_id") or "").rstrip("/")
        for row in citations
        if isinstance(row, dict)
        and row.get("title")
        and "authors" in row
        and "issued" in row
        and any(row.get(key) for key in ("doi", "url", "citekey"))
    }
    missing = [ref for ref in refs if ref.rstrip("/") not in by_source]
    return [f"missing compact citation for {ref}" for ref in missing]


def _init(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS operation_requests (
            request_id TEXT PRIMARY KEY,
            trigger_type TEXT NOT NULL
                CHECK (trigger_type IN ('command', 'file_change', 'schedule')),
            operation_id TEXT NOT NULL,
            args_json TEXT NOT NULL DEFAULT '{}',
            idempotency_key TEXT UNIQUE,
            target_path TEXT NOT NULL DEFAULT '',
            target_hash TEXT NOT NULL DEFAULT '',
            causal_refs_json TEXT NOT NULL DEFAULT '[]',
            actor TEXT NOT NULL DEFAULT 'pi',
            provenance_json TEXT NOT NULL DEFAULT '{}',
            schedule_id TEXT,
            status TEXT NOT NULL
                CHECK (status IN ('pending', 'running', 'done', 'failed')),
            created_at TEXT NOT NULL,
            started_at TEXT,
            completed_at TEXT,
            kind TEXT NOT NULL DEFAULT 'operation',
            job_json TEXT NOT NULL,
            error TEXT NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_operation_requests_status
            ON operation_requests(status, created_at);

        CREATE TABLE IF NOT EXISTS journal_events (
            event_id INTEGER PRIMARY KEY,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            machine TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            prev_hash TEXT NOT NULL,
            row_hash TEXT NOT NULL UNIQUE
        );
        CREATE TRIGGER IF NOT EXISTS journal_events_no_update
        BEFORE UPDATE ON journal_events
        BEGIN
            SELECT RAISE(ABORT, 'journal is append-only');
        END;
        CREATE TRIGGER IF NOT EXISTS journal_events_no_delete
        BEFORE DELETE ON journal_events
        BEGIN
            SELECT RAISE(ABORT, 'journal is append-only');
        END;

        CREATE TABLE IF NOT EXISTS concepts (
            concept_id TEXT PRIMARY KEY,
            concept_type TEXT NOT NULL
                CHECK (concept_type IN (
                    'source', 'digest', 'note', 'hub', 'capability',
                    'operation', 'skill', 'mcp', 'workflow', 'person',
                    'organization', 'venue', 'project'
                )),
            store TEXT NOT NULL CHECK (store IN ('db', 'file')),
            check_status TEXT NOT NULL CHECK (check_status IN ('unchecked', 'checked', 'quarantined'))
        );
        CREATE TABLE IF NOT EXISTS outputs (
            output_id TEXT PRIMARY KEY,
            concept_type TEXT NOT NULL,
            store TEXT NOT NULL CHECK (store IN ('db', 'file')),
            target_path TEXT NOT NULL,
            staging_path TEXT NOT NULL DEFAULT '',
            check_status TEXT NOT NULL CHECK (check_status IN ('unchecked', 'checked', 'quarantined')),
            materialization_status TEXT NOT NULL
                CHECK (materialization_status IN ('none', 'pending', 'materialized', 'failed')),
            output_sha256 TEXT NOT NULL DEFAULT '',
            materialized_commit TEXT NOT NULL DEFAULT '',
            failure_reason TEXT
        );
        CREATE TABLE IF NOT EXISTS materialization_payloads (
            output_id TEXT PRIMARY KEY REFERENCES outputs(output_id) ON DELETE CASCADE,
            expected_sha256 TEXT NOT NULL,
            payload_text TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS catalog_sources (
            source_id TEXT PRIMARY KEY,
            concept_path TEXT NOT NULL,
            doi TEXT UNIQUE,
            title TEXT NOT NULL,
            resource TEXT NOT NULL DEFAULT '',
            identifiers_json TEXT NOT NULL DEFAULT '{}',
            citekey TEXT NOT NULL DEFAULT '',
            csl_json TEXT NOT NULL DEFAULT '{}',
            metadata_status TEXT NOT NULL
                CHECK (metadata_status IN ('verified', 'partial', 'unverified', 'not-indexed')),
            check_status TEXT NOT NULL CHECK (check_status IN ('unchecked', 'checked', 'quarantined')),
            content_hash TEXT NOT NULL DEFAULT '',
            raw_hash TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS derivations (
            input_id TEXT NOT NULL,
            output_id TEXT NOT NULL,
            actor TEXT NOT NULL CHECK (actor IN ('pi', 'operation', 'integrity')),
            PRIMARY KEY (input_id, output_id)
        );
        CREATE VIEW IF NOT EXISTS consumable_outputs AS
        SELECT output_id, concept_type, store, target_path, output_sha256
        FROM outputs
        WHERE check_status = 'checked'
          AND (
            store = 'db'
            OR (store = 'file' AND materialization_status = 'materialized')
          );
        """
    )


def _set_request_state(vault: Path, request_id: str, status: str, job: dict[str, Any]) -> None:
    if status not in REQUEST_STATUSES:
        raise ValueError(f"unknown request status: {status}")
    request_id = safe_filename(request_id)
    now = now_iso()
    with connect(vault) as conn:
        conn.execute(
            """
            UPDATE operation_requests
            SET status = ?,
                started_at = COALESCE(started_at, ?),
                completed_at = CASE WHEN ? IN ('done', 'failed') THEN ? ELSE completed_at END,
                job_json = ?,
                error = ?
            WHERE request_id = ?
            """,
            (
                status,
                now,
                status,
                now,
                _json(job),
                str(job.get("error") or ""),
                request_id,
            ),
        )


def _source_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "source_id": row["source_id"],
        "concept_path": row["concept_path"],
        "title": row["title"],
        "resource": row["resource"],
        "identifiers": json.loads(row["identifiers_json"] or "{}"),
        "citekey": row["citekey"],
        "csl_json": json.loads(row["csl_json"] or "{}"),
        "metadata_status": row["metadata_status"],
        "check_status": row["check_status"],
        "normalized_text_sha256": row["content_hash"],
        "raw_text_sha256": row["raw_hash"],
    }


def _source_id(value: str) -> str:
    rel = normalize_path(value)
    rel = rel.removeprefix("catalog/sources/").removesuffix("/source.md")
    source_id = safe_filename(rel.strip("/")).strip("._-")
    if not source_id:
        raise ValueError("source_id is required")
    return source_id


def _source_refs(frontmatter: dict[str, Any]) -> list[str]:
    refs: set[str] = set()
    _collect_source_refs(refs, frontmatter.get("source_id"))
    _collect_source_refs(refs, frontmatter.get("evidence_set"))
    _collect_source_refs(refs, frontmatter.get("members"))
    _collect_source_refs(refs, frontmatter.get("links"))
    return sorted(refs)


def _collect_source_refs(refs: set[str], value: Any) -> None:
    if isinstance(value, str):
        if value.startswith("catalog/sources/"):
            refs.add(f"catalog/sources/{_source_id(value)}")
        return
    if isinstance(value, list):
        for item in value:
            _collect_source_refs(refs, item)
        return
    if isinstance(value, dict):
        for item in value.values():
            _collect_source_refs(refs, item)


def _csl_authors(csl: dict[str, Any]) -> list[str]:
    rows = csl.get("author")
    if not isinstance(rows, list):
        return []
    authors = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if literal := str(row.get("literal") or "").strip():
            authors.append(literal)
            continue
        family = str(row.get("family") or "").strip()
        given = str(row.get("given") or "").strip()
        if family and given:
            authors.append(f"{given} {family}")
        elif family:
            authors.append(family)
    return authors


def _csl_issued(csl: dict[str, Any]) -> str:
    issued = csl.get("issued")
    if not isinstance(issued, dict):
        return ""
    parts = issued.get("date-parts")
    if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0]:
        return "-".join(str(part) for part in parts[0])
    return str(issued.get("raw") or "")


def _json_rows(values: Iterable[str | dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for value in values:
        rows.append(dict(value) if isinstance(value, dict) else {"id": normalize_path(str(value))})
    return rows


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _journal_hash(
    event_id: int,
    timestamp: str,
    event_type: str,
    machine: str,
    payload_json: str,
    prev_hash: str,
) -> str:
    payload = {
        "event_id": event_id,
        "timestamp": timestamp,
        "event_type": event_type,
        "machine": machine,
        "payload": json.loads(payload_json),
        "prev_hash": prev_hash,
    }
    return hashlib.sha256(_json(payload).encode("utf-8")).hexdigest() or EMPTY_SHA256
