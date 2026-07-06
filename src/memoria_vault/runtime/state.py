"""SQLite-backed working state for queue, journal, catalog, and barriers."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
from collections.abc import Iterable
from importlib.resources import files
from pathlib import Path
from typing import Any

from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.audit import EMPTY_SHA256, sha256_file
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.time import now_iso
from memoria_vault.runtime.vaultio import write_text_durable

DB_REL = ".memoria/memoria.sqlite"
JOURNAL_HEAD_REL = ".memoria/journal-head"
SCHEMA_VERSION = 5
REQUEST_STATUSES = frozenset({"pending", "running", "done", "failed", "cancelled"})
CHECK_STATUSES = frozenset({"unchecked", "checked", "quarantined"})
WORK_ASPECT_TYPES = frozenset(
    {"context", "key_idea", "method", "outcome", "limitation", "assumption"}
)


def db_path(vault: Path) -> Path:
    return Path(vault) / DB_REL


def connect(vault: Path) -> sqlite3.Connection:
    path = db_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = FULL")
    _init(conn)
    return conn


def _schema_sql() -> str:
    return files("memoria_vault.runtime").joinpath("schema.sql").read_text(encoding="utf-8")


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


def recover_running_requests(vault: Path) -> list[str]:
    recovered: list[str] = []
    with connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT request_id, job_json
            FROM operation_requests
            WHERE status = 'running'
            ORDER BY created_at, request_id
            """
        ).fetchall()
        now = now_iso()
        for row in rows:
            job = json.loads(row["job_json"])
            job.update(
                {
                    "status": "failed",
                    "failed_at": now,
                    "error": "interrupted during workspace recovery; retry required",
                }
            )
            conn.execute(
                """
                UPDATE operation_requests
                SET status = 'failed',
                    completed_at = ?,
                    job_json = ?,
                    error = ?
                WHERE request_id = ?
                """,
                (now, _json(job), job["error"], row["request_id"]),
            )
            recovered.append(str(row["request_id"]))
    return recovered


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


def journal_head_anchor(vault: Path) -> str:
    return journal_head(vault) or "GENESIS"


def write_journal_head_anchor(vault: Path) -> str:
    write_text_durable(Path(vault) / JOURNAL_HEAD_REL, journal_head_anchor(vault) + "\n")
    return JOURNAL_HEAD_REL


def set_concept_verdict(vault: Path, concept_id: str, check_status: str) -> None:
    target = normalize_path(concept_id)
    status = _check_status(check_status)
    with connect(vault) as conn:
        _set_concept_verdict_conn(conn, target, status)
        conn.execute(
            "UPDATE outputs SET check_status = ? WHERE output_id = ?",
            (status, target),
        )
        if status == "checked":
            conn.execute(
                "DELETE FROM concept_flags WHERE concept_id = ? AND flag = 'stale'",
                (target,),
            )


def concept_check_status(vault: Path, concept_id: str) -> str:
    target = normalize_path(concept_id)
    if not db_path(vault).is_file():
        return "unchecked"
    with connect(vault) as conn:
        row = conn.execute(
            "SELECT check_status FROM concept_status WHERE concept_id = ?",
            (target,),
        ).fetchone()
    return "unchecked" if row is None else str(row["check_status"])


def output_record(vault: Path, output_id: str) -> dict[str, Any] | None:
    target = normalize_path(output_id)
    if not db_path(vault).is_file():
        return None
    with connect(vault) as conn:
        row = conn.execute(
            """
            SELECT output_id, concept_type, store, target_path, check_status,
                   materialization_status, output_sha256
            FROM outputs
            WHERE output_id = ?
            """,
            (target,),
        ).fetchone()
    return None if row is None else dict(row)


def rebuild_file_concept_mirror(vault: Path, rows: Iterable[dict[str, str]]) -> dict[str, int]:
    rows = list(rows)
    with connect(vault) as conn:
        deleted = conn.execute("DELETE FROM concepts WHERE store = 'file'").rowcount
        for row in rows:
            _upsert_concept_mirror_conn(
                conn,
                normalize_path(row["concept_id"]),
                str(row["concept_type"]),
                "file",
            )
    return {"deleted": int(deleted), "inserted": len(rows)}


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
        _upsert_concept_mirror_conn(conn, target, concept_type, "file")
        _set_concept_verdict_conn(conn, target, _check_status(check_status))
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
        _set_concept_verdict_conn(conn, target, "checked")
        conn.execute("DELETE FROM concept_flags WHERE concept_id = ? AND flag = 'stale'", (target,))
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
        _upsert_concept_mirror_conn(conn, target, concept_type, "file")
        _set_concept_verdict_conn(conn, target, "unchecked")
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


def set_concept_flag(
    vault: Path,
    concept_id: str,
    flag: str,
    *,
    reason: str = "",
    trigger_id: str = "",
) -> None:
    if flag != "stale":
        raise ValueError(f"invalid concept flag: {flag!r}")
    target = normalize_path(concept_id)
    with connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO concept_flags(concept_id, flag, reason, trigger_id, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(concept_id, flag) DO UPDATE SET
                reason = excluded.reason,
                trigger_id = excluded.trigger_id,
                created_at = excluded.created_at
            """,
            (target, flag, reason, normalize_path(trigger_id) if trigger_id else "", now_iso()),
        )


def concept_flags(vault: Path, concept_id: str) -> dict[str, dict[str, str]]:
    target = normalize_path(concept_id)
    if not db_path(vault).is_file():
        return {}
    with connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT flag, reason, trigger_id, created_at
            FROM concept_flags
            WHERE concept_id = ?
            ORDER BY flag
            """,
            (target,),
        ).fetchall()
    return {
        str(row["flag"]): {
            "reason": str(row["reason"]),
            "trigger_id": str(row["trigger_id"]),
            "created_at": str(row["created_at"]),
        }
        for row in rows
    }


def note_curation_status(vault: Path, concept_id: str) -> str:
    """Return note-candidate lifecycle from journal events, not frontmatter."""
    target = normalize_path(concept_id)
    if not db_path(vault).is_file():
        return ""
    status = ""
    with connect(vault) as conn:
        rows = conn.execute("SELECT payload_json FROM journal_events ORDER BY event_id").fetchall()
    # ponytail: journal scan is fine for alpha.16; project if candidate volume matters.
    for row in rows:
        try:
            payload = json.loads(row["payload_json"])
        except (TypeError, json.JSONDecodeError):
            continue
        if (
            payload.get("event") == "derived"
            and payload.get("operation") == "propose-note-candidates"
            and payload.get("output_id") == target
        ):
            status = "candidate"
        elif (
            payload.get("event") == "resolved"
            and payload.get("operation") == "curate-note-candidate"
            and payload.get("target_id") == target
        ):
            status = str(payload.get("resolution") or "").strip().lower()
    return status


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
    vault = Path(vault)
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
            commit = _committed_materialization_commit(vault, str(row["target_path"]), expected)
            if target.is_file() and sha256_file(target) == expected:
                if not commit:
                    conn.execute(
                        """
                        UPDATE outputs
                        SET materialization_status = 'failed',
                            failure_reason = 'materialization target is not committed'
                        WHERE output_id = ?
                        """,
                        (row["output_id"],),
                    )
                    continue
                conn.execute(
                    """
                    UPDATE outputs
                    SET materialization_status = 'materialized',
                        materialized_commit = ?,
                        failure_reason = NULL
                    WHERE output_id = ?
                    """,
                    (commit, row["output_id"]),
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
            if not commit:
                conn.execute(
                    """
                    UPDATE outputs
                    SET materialization_status = 'failed',
                        failure_reason = 'materialization target is not committed'
                    WHERE output_id = ?
                    """,
                    (row["output_id"],),
                )
                continue
            write_text_durable(target, payload, create_parent=True)
            conn.execute(
                """
                UPDATE outputs
                SET materialization_status = 'materialized',
                    materialized_commit = ?,
                    failure_reason = NULL
                WHERE output_id = ?
                """,
                (commit, row["output_id"]),
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
        item_type=str(frontmatter.get("item_type") or csl_json.get("type") or "article"),
        identifiers=identifiers,
        citekey=str(frontmatter.get("citekey") or csl_json.get("id") or ""),
        csl_json=csl_json,
        provider_coverage=str(frontmatter.get("provider_coverage") or "partial"),
        text_status=str(frontmatter.get("text_status") or "metadata-only"),
        check_status=concept_check_status(vault, source_rel),
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
    item_type: str = "article",
    identifiers: dict[str, Any] | None = None,
    citekey: str = "",
    csl_json: dict[str, Any] | None = None,
    provider_coverage: str = "partial",
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
                item_type,
                identifiers_json,
                citekey,
                csl_json,
                provider_coverage,
                text_status,
                check_status,
                content_hash,
                raw_hash,
                content_path,
                raw_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
                concept_path = excluded.concept_path,
                doi = excluded.doi,
                title = excluded.title,
                description = excluded.description,
                resource = excluded.resource,
                item_type = excluded.item_type,
                identifiers_json = excluded.identifiers_json,
                citekey = excluded.citekey,
                csl_json = excluded.csl_json,
                provider_coverage = excluded.provider_coverage,
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
                item_type or "article",
                _json(identifiers),
                citekey,
                _json(csl_json),
                provider_coverage,
                text_status,
                check_status,
                content_hash,
                raw_hash,
                normalize_path(content_path) if content_path else "",
                normalize_path(raw_path) if raw_path else "",
            ),
        )
        concept_id = f"catalog/sources/{stable_source_id}"
        _upsert_concept_mirror_conn(conn, concept_id, "source", "db")
        _set_concept_verdict_conn(conn, concept_id, _check_status(check_status))


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


def replace_work_graph_edges(vault: Path, work_id: str, rows: Iterable[dict[str, Any]]) -> None:
    stable_work_id = _source_id(work_id)
    with connect(vault) as conn:
        conn.execute("DELETE FROM work_graph_edges WHERE work_id = ?", (stable_work_id,))
        for row in rows:
            conn.execute(
                """
                INSERT INTO work_graph_edges(
                    work_id,
                    relation_type,
                    target_id,
                    target_title,
                    target_doi,
                    source_provider,
                    raw_json,
                    discovered_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    stable_work_id,
                    str(row["relation_type"]),
                    str(row["target_id"]),
                    str(row.get("target_title") or ""),
                    str(row.get("target_doi") or ""),
                    str(row.get("source_provider") or ""),
                    _json(row.get("raw") or {}),
                    now_iso(),
                ),
            )


def replace_work_aspects(vault: Path, source_ref: str, rows: Iterable[dict[str, Any]]) -> None:
    source_id = _source_id(source_ref)
    with connect(vault) as conn:
        conn.execute("DELETE FROM work_aspects WHERE source_id = ?", (source_id,))
        for row in rows:
            aspect_text = str(row.get("aspect_text") or "").strip()
            if not aspect_text:
                continue
            aspect_type = _work_aspect_type(str(row.get("aspect_type") or ""))
            conn.execute(
                """
                INSERT INTO work_aspects(
                    source_id,
                    aspect_type,
                    aspect_text,
                    anchor_text,
                    check_status,
                    source_provider,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    aspect_type,
                    aspect_text,
                    str(row.get("anchor_text") or "").strip(),
                    _check_status(str(row.get("check_status") or "unchecked")),
                    str(row.get("source_provider") or "deterministic"),
                    now_iso(),
                ),
            )


def work_aspects(vault: Path, source_ref: str) -> list[dict[str, Any]]:
    if not db_path(vault).is_file():
        return []
    source_id = _source_id(source_ref)
    with connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT source_id, aspect_type, aspect_text, anchor_text, check_status,
                   source_provider, updated_at
            FROM work_aspects
            WHERE source_id = ?
            ORDER BY aspect_type
            """,
            (source_id,),
        ).fetchall()
    return [dict(row) for row in rows]


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
    if concept_type not in {"note", "work", "hub"}:
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
    current = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if current == 4:
        _migrate_v4_to_v5(conn)
        current = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if current not in {0, SCHEMA_VERSION}:
        raise RuntimeError(f"unsupported Memoria DB schema version: {current}")
    conn.executescript(_schema_sql())
    applied = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if applied != SCHEMA_VERSION:
        raise RuntimeError(f"Memoria DB schema initialization failed: {applied}")


def _migrate_v4_to_v5(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP VIEW IF EXISTS concept_status;
        ALTER TABLE concepts RENAME TO concepts_v4;
        CREATE TABLE concepts (
            concept_id TEXT PRIMARY KEY,
            concept_type TEXT NOT NULL
                CHECK (concept_type IN (
                    'source', 'source-note', 'work', 'digest', 'note', 'hub', 'capability',
                    'operation', 'skill', 'adapter', 'workflow', 'person',
                    'organization', 'venue', 'project'
                )),
            store TEXT NOT NULL CHECK (store IN ('db', 'file'))
        );
        INSERT INTO concepts(concept_id, concept_type, store)
        SELECT concept_id, concept_type, store
        FROM concepts_v4;
        DROP TABLE concepts_v4;
        CREATE VIEW concept_status AS
        SELECT
            c.concept_id,
            c.concept_type,
            c.store,
            COALESCE(v.check_status, 'unchecked') AS check_status
        FROM concepts c
        LEFT JOIN concept_verdicts v ON v.concept_id = c.concept_id;
        PRAGMA user_version = 5;
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
        "item_type": row["item_type"],
        "identifiers": json.loads(row["identifiers_json"] or "{}"),
        "citekey": row["citekey"],
        "csl_json": json.loads(row["csl_json"] or "{}"),
        "provider_coverage": row["provider_coverage"],
        "text_status": row["text_status"],
        "check_status": row["check_status"],
        "normalized_text_sha256": row["content_hash"],
        "raw_text_sha256": row["raw_hash"],
        "content_path": row["content_path"],
        "raw_path": row["raw_path"],
    }


def _upsert_concept_mirror_conn(
    conn: sqlite3.Connection,
    concept_id: str,
    concept_type: str,
    store: str,
) -> None:
    conn.execute(
        """
        INSERT INTO concepts(concept_id, concept_type, store)
        VALUES (?, ?, ?)
        ON CONFLICT(concept_id) DO UPDATE SET
            concept_type = excluded.concept_type,
            store = excluded.store
        """,
        (concept_id, concept_type, store),
    )


def _set_concept_verdict_conn(
    conn: sqlite3.Connection,
    concept_id: str,
    check_status: str,
) -> None:
    conn.execute(
        """
        INSERT INTO concept_verdicts(concept_id, check_status)
        VALUES (?, ?)
        ON CONFLICT(concept_id) DO UPDATE SET
            check_status = excluded.check_status
        """,
        (concept_id, _check_status(check_status)),
    )


def _check_status(check_status: str) -> str:
    status = check_status.strip()
    if status not in CHECK_STATUSES:
        raise ValueError(f"invalid check_status: {check_status!r}")
    return status


def _work_aspect_type(value: str) -> str:
    aspect_type = value.strip().lower().replace("-", "_")
    if aspect_type not in WORK_ASPECT_TYPES:
        raise ValueError(f"unknown work aspect type: {value}")
    return aspect_type


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


def _committed_materialization_commit(vault: Path, relpath: str, expected_sha256: str) -> str:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=vault,
        check=False,
        text=True,
        capture_output=True,
    )
    if head.returncode:
        return ""
    commit = head.stdout.strip()
    blob = subprocess.run(
        ["git", "show", f"{commit}:{normalize_path(relpath)}"],
        cwd=vault,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if blob.returncode:
        return ""
    if "sha256:" + hashlib.sha256(blob.stdout).hexdigest() != expected_sha256:
        return ""
    return commit


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
