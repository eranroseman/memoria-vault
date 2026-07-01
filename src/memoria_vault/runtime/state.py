"""SQLite-backed working state for queue, journal, catalog, and barriers."""

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

DB_REL = ".memoria/memoria.sqlite"
REQUEST_STATUSES = frozenset({"pending", "running", "done", "failed", "cancelled"})


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
    operation_id: str,
    args: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
    input_refs: Iterable[str | dict[str, Any]] = (),
    output_intents: Iterable[str | dict[str, Any]] = (),
    primary_target: str = "",
    precondition_hashes: dict[str, Any] | None = None,
    causal_refs: Iterable[str | dict[str, Any]] = (),
    actor: str = "pi",
    provenance: dict[str, Any] | None = None,
    schedule_id: str | None = None,
) -> dict[str, Any]:
    operation = operation_id.strip()
    if not operation:
        raise ValueError("operation_id is required")
    return {
        "request_id": safe_filename(request_id),
        "operation_id": operation,
        "args": dict(args or {}),
        "idempotency_key": idempotency_key or request_id,
        "input_refs": _json_rows(input_refs),
        "output_intents": _json_rows(output_intents),
        "primary_target": normalize_path(primary_target) if primary_target else "",
        "precondition_hashes": dict(precondition_hashes or {}),
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
                operation_id,
                args_json,
                idempotency_key,
                input_refs_json,
                output_intents_json,
                primary_target,
                precondition_hashes_json,
                causal_refs_json,
                actor,
                provenance_json,
                schedule_id,
                status,
                created_at,
                kind,
                job_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
            """,
            (
                envelope["request_id"],
                envelope["operation_id"],
                _json(envelope["args"]),
                idem,
                _json(envelope["input_refs"]),
                _json(envelope["output_intents"]),
                envelope["primary_target"],
                _json(envelope["precondition_hashes"]),
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


def record_observed_file_edit(
    vault: Path,
    *,
    output_id: str,
    concept_type: str,
    output_sha256: str,
) -> None:
    target = normalize_path(output_id)
    with connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO concepts(concept_id, concept_type, store, check_status)
            VALUES (?, ?, 'file', 'unchecked')
            ON CONFLICT(concept_id) DO UPDATE SET
                concept_type = excluded.concept_type,
                store = excluded.store,
                check_status = 'unchecked'
            """,
            (target, concept_type),
        )
        conn.execute(
            """
            INSERT INTO outputs(
                output_id,
                concept_type,
                store,
                target_path,
                check_status,
                materialization_status,
                output_sha256
            )
            VALUES (?, ?, 'file', ?, 'unchecked', 'materialized', ?)
            ON CONFLICT(output_id) DO UPDATE SET
                concept_type = excluded.concept_type,
                store = excluded.store,
                target_path = excluded.target_path,
                check_status = 'unchecked',
                materialization_status = 'materialized',
                output_sha256 = excluded.output_sha256,
                failure_reason = NULL
            """,
            (target, concept_type, target, output_sha256),
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


def record_projection_output(
    vault: Path,
    *,
    output_id: str,
    output_sha256: str,
    payload_text: str,
) -> None:
    target = normalize_path(output_id)
    if _sha256_text(payload_text) != output_sha256:
        raise ValueError(f"projection payload hash mismatch for {target}")
    with connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO outputs(
                output_id,
                concept_type,
                store,
                target_path,
                check_status,
                materialization_status,
                output_sha256
            )
            VALUES (?, 'projection', 'file', ?, 'checked', 'pending', ?)
            ON CONFLICT(output_id) DO UPDATE SET
                concept_type = excluded.concept_type,
                store = excluded.store,
                target_path = excluded.target_path,
                check_status = excluded.check_status,
                materialization_status = 'pending',
                output_sha256 = excluded.output_sha256,
                failure_reason = NULL
            """,
            (target, target, output_sha256),
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
    upsert_catalog_record(
        vault,
        source_id=source_id,
        concept_path=source_rel,
        doi=doi,
        title=str(frontmatter.get("title") or source_id),
        description=str(frontmatter.get("description") or ""),
        resource=str(frontmatter.get("resource") or ""),
        identifiers=identifiers,
        citekey=str(frontmatter.get("citekey") or csl_json.get("id") or ""),
        csl_json=csl_json,
        metadata_status=str(frontmatter.get("metadata_status") or "partial"),
        text_status=str(frontmatter.get("text_status") or "metadata-only"),
        check_status=str(frontmatter.get("check_status") or "unchecked"),
        content_hash=str(frontmatter.get("normalized_text_sha256") or ""),
        raw_hash=str(frontmatter.get("raw_text_sha256") or ""),
        content_path=str(frontmatter.get("content_path") or ""),
        raw_path=str(frontmatter.get("raw_copy_path") or ""),
    )


def upsert_catalog_record(
    vault: Path,
    *,
    source_id: str,
    title: str,
    description: str = "",
    concept_path: str = "",
    doi: str | None = None,
    resource: str = "",
    identifiers: dict[str, Any] | None = None,
    citekey: str = "",
    csl_json: dict[str, Any] | None = None,
    metadata_status: str = "partial",
    text_status: str = "metadata-only",
    check_status: str = "unchecked",
    content_hash: str = "",
    raw_hash: str = "",
    content_path: str = "",
    raw_path: str = "",
) -> None:
    stable_source_id = _source_id(source_id)
    identifiers = dict(identifiers or {})
    csl_json = dict(csl_json or {})
    stable_doi = str(doi or identifiers.get("doi") or csl_json.get("DOI") or "").strip() or None
    with connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO catalog_sources(
                source_id,
                concept_path,
                doi,
                title,
                description,
                resource,
                identifiers_json,
                citekey,
                csl_json,
                metadata_status,
                text_status,
                check_status,
                content_hash,
                raw_hash,
                content_path,
                raw_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
                concept_path = excluded.concept_path,
                doi = excluded.doi,
                title = excluded.title,
                description = excluded.description,
                resource = excluded.resource,
                identifiers_json = excluded.identifiers_json,
                citekey = excluded.citekey,
                csl_json = excluded.csl_json,
                metadata_status = excluded.metadata_status,
                text_status = excluded.text_status,
                check_status = excluded.check_status,
                content_hash = excluded.content_hash,
                raw_hash = excluded.raw_hash,
                content_path = excluded.content_path,
                raw_path = excluded.raw_path
            """,
            (
                stable_source_id,
                normalize_path(concept_path)
                if concept_path
                else f"catalog/sources/{stable_source_id}",
                stable_doi,
                title or stable_source_id,
                description,
                resource,
                _json(identifiers),
                citekey,
                _json(csl_json),
                metadata_status,
                text_status,
                check_status,
                content_hash,
                raw_hash,
                normalize_path(content_path) if content_path else "",
                normalize_path(raw_path) if raw_path else "",
            ),
        )
        concept_id = f"catalog/sources/{stable_source_id}"
        conn.execute(
            """
            INSERT INTO concepts(concept_id, concept_type, store, check_status)
            VALUES (?, 'source', 'db', ?)
            ON CONFLICT(concept_id) DO UPDATE SET
                store = excluded.store,
                check_status = excluded.check_status
            """,
            (concept_id, check_status),
        )


def catalog_source(vault: Path, source_ref: str) -> dict[str, Any] | None:
    if not db_path(vault).is_file():
        return None
    source_id = _source_id(source_ref)
    with connect(vault) as conn:
        row = conn.execute(
            "SELECT * FROM catalog_sources WHERE source_id = ?",
            (source_id,),
        ).fetchone()
    return _source_row(row) if row is not None else None


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


def start_enrichment_run(
    vault: Path,
    *,
    run_id: str,
    source_id: str,
    required_provider_policy: dict[str, Any],
    request_id: str = "",
) -> None:
    with connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO enrichment_runs(
                run_id,
                source_id,
                enrichment_status,
                required_provider_policy_json,
                started_at,
                request_id
            )
            VALUES (?, ?, 'pending', ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                enrichment_status = 'pending',
                required_provider_policy_json = excluded.required_provider_policy_json,
                started_at = excluded.started_at,
                finished_at = NULL,
                request_id = excluded.request_id
            """,
            (run_id, _source_id(source_id), _json(required_provider_policy), now_iso(), request_id),
        )


def finish_enrichment_run(vault: Path, run_id: str, status: str) -> None:
    with connect(vault) as conn:
        conn.execute(
            """
            UPDATE enrichment_runs
            SET enrichment_status = ?, finished_at = ?
            WHERE run_id = ?
            """,
            (status, now_iso(), run_id),
        )


def store_provider_payload(
    vault: Path,
    *,
    run_id: str,
    provider: str,
    request_key: str,
    request_params_hash: str,
    status: str,
    raw_hash: str,
    raw_path: str,
    normalized: dict[str, Any],
    error: str = "",
    latency_ms: int = 0,
    retry_count: int = 0,
) -> None:
    with connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO provider_payloads(
                run_id,
                provider,
                request_key,
                request_params_hash,
                status,
                fetched_at,
                raw_hash,
                raw_path,
                normalized_json,
                error,
                latency_ms,
                retry_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                provider,
                request_key,
                request_params_hash,
                status,
                now_iso(),
                raw_hash,
                normalize_path(raw_path),
                _json(normalized),
                error,
                latency_ms,
                retry_count,
            ),
        )


def replace_field_provenance(
    vault: Path,
    source_id: str,
    rows: Iterable[dict[str, Any]],
) -> None:
    stable_source_id = _source_id(source_id)
    with connect(vault) as conn:
        conn.execute("DELETE FROM field_provenance WHERE source_id = ?", (stable_source_id,))
        for row in rows:
            conn.execute(
                """
                INSERT INTO field_provenance(
                    source_id,
                    field_path,
                    value_hash,
                    winning_provider,
                    evidence_payload_id,
                    alternatives_json,
                    confidence,
                    conflict_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    stable_source_id,
                    str(row["field_path"]),
                    str(row["value_hash"]),
                    str(row["winning_provider"]),
                    str(row.get("evidence_payload_id") or ""),
                    _json(row.get("alternatives") or []),
                    str(row.get("confidence") or "high"),
                    str(row.get("conflict_status") or "none"),
                ),
            )


def replace_external_ids(vault: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows = list(rows)
    owner_keys = {
        (str(row["owner_type"]), str(row["owner_id"]))
        for row in rows
        if row.get("owner_type") and row.get("owner_id")
    }
    with connect(vault) as conn:
        for owner_type, owner_id in owner_keys:
            conn.execute(
                "DELETE FROM external_ids WHERE owner_type = ? AND owner_id = ?",
                (owner_type, owner_id),
            )
        for row in rows:
            conn.execute(
                """
                INSERT INTO external_ids(
                    owner_type,
                    owner_id,
                    namespace,
                    value,
                    source_provider,
                    confidence,
                    verified_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(row["owner_type"]),
                    str(row["owner_id"]),
                    str(row["namespace"]),
                    str(row["value"]),
                    str(row.get("source_provider") or ""),
                    str(row.get("confidence") or "high"),
                    now_iso(),
                ),
            )


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
            operation_id TEXT NOT NULL,
            args_json TEXT NOT NULL DEFAULT '{}',
            idempotency_key TEXT UNIQUE,
            input_refs_json TEXT NOT NULL DEFAULT '[]',
            output_intents_json TEXT NOT NULL DEFAULT '[]',
            primary_target TEXT NOT NULL DEFAULT '',
            precondition_hashes_json TEXT NOT NULL DEFAULT '{}',
            causal_refs_json TEXT NOT NULL DEFAULT '[]',
            actor TEXT NOT NULL DEFAULT 'pi',
            provenance_json TEXT NOT NULL DEFAULT '{}',
            schedule_id TEXT,
            status TEXT NOT NULL
                CHECK (status IN ('pending', 'running', 'done', 'failed', 'cancelled')),
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
            description TEXT NOT NULL DEFAULT '',
            resource TEXT NOT NULL DEFAULT '',
            identifiers_json TEXT NOT NULL DEFAULT '{}',
            citekey TEXT NOT NULL DEFAULT '',
            csl_json TEXT NOT NULL DEFAULT '{}',
            metadata_status TEXT NOT NULL
                CHECK (metadata_status IN ('verified', 'partial', 'unverified', 'not-indexed')),
            text_status TEXT NOT NULL
                CHECK (text_status IN ('full-text', 'abstract-only', 'metadata-only')),
            check_status TEXT NOT NULL CHECK (check_status IN ('unchecked', 'checked', 'quarantined')),
            content_hash TEXT NOT NULL DEFAULT '',
            raw_hash TEXT NOT NULL DEFAULT '',
            content_path TEXT NOT NULL DEFAULT '',
            raw_path TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS external_ids (
            owner_type TEXT NOT NULL,
            owner_id TEXT NOT NULL,
            namespace TEXT NOT NULL,
            value TEXT NOT NULL,
            source_provider TEXT NOT NULL DEFAULT '',
            confidence TEXT NOT NULL DEFAULT 'high',
            verified_at TEXT NOT NULL,
            PRIMARY KEY (owner_type, owner_id, namespace, value)
        );
        CREATE TABLE IF NOT EXISTS enrichment_runs (
            run_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            enrichment_status TEXT NOT NULL
                CHECK (
                    enrichment_status IN (
                        'pending', 'enriched', 'partial', 'failed', 'needs_human', 'contested'
                    )
                ),
            required_provider_policy_json TEXT NOT NULL DEFAULT '{}',
            started_at TEXT NOT NULL,
            finished_at TEXT,
            request_id TEXT NOT NULL DEFAULT '',
            journal_id TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS provider_payloads (
            payload_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            request_key TEXT NOT NULL,
            request_params_hash TEXT NOT NULL,
            status TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            raw_hash TEXT NOT NULL,
            raw_path TEXT NOT NULL,
            normalized_json TEXT NOT NULL DEFAULT '{}',
            error TEXT NOT NULL DEFAULT '',
            latency_ms INTEGER NOT NULL DEFAULT 0,
            retry_count INTEGER NOT NULL DEFAULT 0,
            ttl_until TEXT NOT NULL DEFAULT '',
            UNIQUE(run_id, provider, request_key, request_params_hash)
        );
        CREATE TABLE IF NOT EXISTS field_provenance (
            source_id TEXT NOT NULL,
            field_path TEXT NOT NULL,
            value_hash TEXT NOT NULL,
            winning_provider TEXT NOT NULL,
            evidence_payload_id TEXT NOT NULL DEFAULT '',
            alternatives_json TEXT NOT NULL DEFAULT '[]',
            confidence TEXT NOT NULL DEFAULT 'high',
            conflict_status TEXT NOT NULL DEFAULT 'none',
            PRIMARY KEY (source_id, field_path)
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
                completed_at = CASE
                    WHEN ? IN ('done', 'failed', 'cancelled') THEN ?
                    ELSE completed_at
                END,
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
        "description": row["description"],
        "resource": row["resource"],
        "identifiers": json.loads(row["identifiers_json"] or "{}"),
        "citekey": row["citekey"],
        "csl_json": json.loads(row["csl_json"] or "{}"),
        "metadata_status": row["metadata_status"],
        "text_status": row["text_status"],
        "check_status": row["check_status"],
        "normalized_text_sha256": row["content_hash"],
        "raw_text_sha256": row["raw_hash"],
        "content_path": row["content_path"],
        "raw_path": row["raw_path"],
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
