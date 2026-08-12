"""SQLite-backed working state for queue, journal, catalog, and barriers."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import subprocess
from collections import Counter
from collections.abc import Container, Iterable, Mapping, Sequence
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING, Any

from memoria_vault.runtime.content_security import neutralize_untrusted_markdown
from memoria_vault.runtime.evidence import (
    EvidenceMarker,
    evidence_ref_kind,
    parse_code_grounds_ref,
    parse_source_span_ref,
)
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.policy.paths import normalize_path

# Same re-export contract as workspace_lock below: readers outside `state`
# use four of these public names via `state.` attribute access
# (`markdown_code_literals_masked` has no external caller -- only
# markdown.py's own `markdown_visible_code_literals_masked` calls it); some
# private names are what `evidence_marker_rows` and
# `block_canonical_text_from_text` (below) still call after the
# markdown/evidence-marker extraction, and others (e.g. `_has_raw_tex_syntax`)
# are what tests still reach via `state.<name>`.
from memoria_vault.runtime.state.markdown import (  # noqa: F401
    _direct_evidence_marker_matches,
    _has_raw_tex_syntax,
    _markdown_control_text,
    direct_evidence_marker_spans_from_markdown,
    evidence_marker_occurrences_from_markdown,
    evidence_markers_from_markdown,
    markdown_citation_visibility_is_ambiguous,
    markdown_code_literals_masked,
    markdown_visible_code_literals_masked,
)

# workspace_lock is the public context manager, used below in this module.
# _open_workspace_lock_file is re-exported because
# tests/test_backup_restore.py still calls it as
# `state._open_workspace_lock_file(...)`. The other two lock internals
# (`_workspace_lock_key`, `_workspace_thread_lock`) and the Windows opener
# (`_open_workspace_lock_file_windows`, monkeypatched on the workspace_lock
# submodule directly, not through this facade) have no reference through
# `state.<name>` and are not re-exported.
from memoria_vault.runtime.state.workspace_lock import (  # noqa: F401
    _open_workspace_lock_file,
    workspace_lock,
)
from memoria_vault.runtime.time import now_iso
from memoria_vault.runtime.vaultio import is_ulid, parse_frontmatter, safe_read, write_text_durable
from memoria_vault.runtime.vocabulary.edges import EDGE_RELATIONS

if TYPE_CHECKING:
    from memoria_vault.runtime.trusted_writer import OperationContext

DB_REL = ".memoria/memoria.sqlite"
JOURNAL_HEAD_REL = ".memoria/journal-head"
SCHEMA_VERSION = 20
ACTORS = frozenset({"pi", "agent", "operation", "integrity"})
REQUEST_STATUSES = frozenset({"pending", "running", "done", "failed", "cancelled"})
CHECK_STATUSES = frozenset({"unchecked", "checked", "quarantined"})
WORK_ASPECT_TYPES = frozenset(
    {"context", "key_idea", "method", "outcome", "limitation", "assumption"}
)
_CONCEPT_TYPE_MAPS: dict[Path, dict[str, str]] = {}
_FOLDER_CONCEPT_TYPES: dict[Path, dict[str, str]] = {}


def db_path(vault: Path) -> Path:
    return Path(vault) / DB_REL


class _ClosingConnection(sqlite3.Connection):
    def __exit__(self, *exc_info: object) -> bool:
        try:
            return super().__exit__(*exc_info)
        finally:
            self.close()


def connect(vault: Path) -> sqlite3.Connection:
    path = db_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, factory=_ClosingConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = FULL")
    _init(conn)
    return conn


def _schema_sql() -> str:
    return files("memoria_vault.runtime").joinpath("schema.sql").read_text(encoding="utf-8")


def ensure_schema(vault: Path) -> None:
    """Re-execute the idempotent DDL against an already-current DB.

    connect() skips schema.sql when user_version is current, so paths that
    exist to repair damage (init re-init, doctor --repair, journal-driven
    recovery) must re-run it explicitly.
    """
    with connect(vault) as conn:
        conn.executescript(_schema_sql())


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
    actor: str,
    machine_authored: bool = False,
    provenance: dict[str, Any] | None = None,
    schedule_id: str | None = None,
) -> dict[str, Any]:
    operation = operation_id.strip()
    if not operation:
        raise ValueError("operation_id is required")
    actor = actor.strip()
    if actor not in ACTORS:
        raise ValueError(f"envelope actor must be one of {sorted(ACTORS)}, got: {actor!r}")
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
        "actor": actor,
        # Authority (`actor`) is not authorship. A door authenticated as the PI can
        # still be posting a body a machine composed; that body must stay untrusted.
        "machine_authored": bool(machine_authored),
        "provenance": dict(provenance or {}),
        "schedule_id": schedule_id or None,
    }


def save_request(
    vault: Path,
    envelope: dict[str, Any],
    job: dict[str, Any],
    *,
    supersede_request_id: str | None = None,
) -> dict[str, Any]:
    created_at = str(job.get("created_at") or now_iso())
    job = json.loads(_json({**job, "request_envelope": envelope}))
    envelope = job["request_envelope"]
    payload = _json(job)
    idem = str(envelope.get("idempotency_key") or envelope["request_id"])
    kind = str(job.get("kind") or "operation")
    superseded_id = safe_filename(supersede_request_id or "")
    if superseded_id:
        if envelope["actor"] != "pi":
            raise ValueError("request supersession requires PI actor authority")
        if superseded_id == envelope["request_id"]:
            raise ValueError("request cannot supersede itself")
        provenance = envelope.get("provenance")
        bound_source = (
            safe_filename(str(provenance.get("supersedes_request_id") or ""))
            if isinstance(provenance, dict)
            else ""
        )
        if bound_source != superseded_id:
            raise ValueError("superseded request id must be bound in request provenance")
        causal_ids = {
            safe_filename(str(ref.get("id") or ""))
            for ref in envelope.get("causal_refs", [])
            if isinstance(ref, dict)
        }
        if superseded_id not in causal_ids:
            raise ValueError("superseded request id must be a causal reference")
    with connect(vault) as conn:
        # Serialize lookup and insertion so a concurrent retry cannot bypass the
        # request-identity comparison between a different actor or payload.
        conn.execute("BEGIN IMMEDIATE")
        existing = conn.execute(
            """
            SELECT kind, job_json
            FROM operation_requests
            WHERE request_id = ? OR idempotency_key = ?
            LIMIT 1
            """,
            (envelope["request_id"], idem),
        ).fetchone()
        if existing is not None:
            existing_job = json.loads(existing["job_json"])
            existing_kind = str(existing_job.get("kind") or existing["kind"])
            if (
                _json(existing_job.get("request_envelope")) != _json(envelope)
                or existing["kind"] != kind
                or existing_kind != kind
            ):
                raise ValueError("idempotency key is already bound to a different request")
            return existing_job
        superseded = None
        superseded_job: dict[str, Any] | None = None
        if superseded_id:
            superseded = conn.execute(
                "SELECT status, job_json FROM operation_requests WHERE request_id = ?",
                (superseded_id,),
            ).fetchone()
            if superseded is None:
                raise FileNotFoundError(f"request not found: {supersede_request_id}")
            if superseded["status"] == "running":
                raise ValueError("request amendment requires a non-running request")
            superseded_job = json.loads(superseded["job_json"])
            prior_successor = str(superseded_job.get("superseded_by_request_id") or "")
            if prior_successor and safe_filename(prior_successor) != envelope["request_id"]:
                raise ValueError(f"request already superseded by request {prior_successor}")
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
                kind,
                payload,
            ),
        )
        if superseded is not None and superseded_job is not None:
            superseded_job["superseded_by_request_id"] = envelope["request_id"]
            if superseded["status"] != "pending":
                conn.execute(
                    "UPDATE operation_requests SET job_json = ? WHERE request_id = ?",
                    (_json(superseded_job), superseded_id),
                )
            else:
                error = f"superseded by request {envelope['request_id']}"
                superseded_job.update({"status": "cancelled", "error": error})
                conn.execute(
                    """
                    UPDATE operation_requests
                    SET status = 'cancelled', completed_at = ?, job_json = ?, error = ?
                    WHERE request_id = ?
                    """,
                    (now_iso(), _json(superseded_job), error, superseded_id),
                )
    return job


def request_job(vault: Path, request_id: str) -> dict[str, Any] | None:
    with connect(vault) as conn:
        row = conn.execute(
            "SELECT job_json FROM operation_requests WHERE request_id = ?",
            (safe_filename(request_id),),
        ).fetchone()
    return json.loads(row["job_json"]) if row is not None else None


def request_row(vault: Path, request_id: str) -> Any | None:
    with connect(vault) as conn:
        return conn.execute(
            """
            SELECT *
            FROM operation_requests
            WHERE request_id = ?
            """,
            (safe_filename(request_id),),
        ).fetchone()


def _neutralized_request_error(error: Any) -> Any:
    """requests.error is the designated home for untrusted operation text (#1608).

    A raised operation's ``str(exc)`` can be composed from file-derived text the
    PI never authored, and ``requests.get`` carries both an HTTP and an MCP
    binding. Neutralizing here covers the column that ``request_summary`` and
    ``request_detail`` both read; ``request_detail`` additionally neutralizes
    the copy of that same text worker.py persists into ``job["error"]`` (see
    ``request_detail`` below) so neither read path serves it verbatim. The
    stored row keeps the raw text in both places.

    Still open, and deliberately out of this seam: ``run_operation`` returns the
    failed job dict inline, so ``POST /operation/run`` and the MCP ``operation``
    tool serve the same raw text on the *run-result* path rather than a stored-
    request read. Same class, different seam; tracked on #1608.
    """
    if not isinstance(error, str) or not error:
        return error
    return neutralize_untrusted_markdown(error)


def _neutralize_request_diagnostics(value: Any) -> Any:
    if isinstance(value, str):
        return neutralize_untrusted_markdown(value)
    if isinstance(value, list):
        return [_neutralize_request_diagnostics(item) for item in value]
    if isinstance(value, dict):
        return {key: _neutralize_request_diagnostics(item) for key, item in value.items()}
    return value


def request_summary(row: Any) -> dict[str, Any]:
    return {
        "request_id": row["request_id"],
        "operation_id": row["operation_id"],
        "status": row["status"],
        "created_at": row["created_at"],
        "completed_at": row["completed_at"],
        "error": _neutralized_request_error(row["error"]),
    }


def request_detail(row: Any) -> dict[str, Any]:
    job = json.loads(row["job_json"])
    if "error" in job:
        job = {**job, "error": _neutralized_request_error(job["error"])}
    if "diagnostics" in job:
        job = {
            **job,
            "diagnostics": _neutralize_request_diagnostics(job["diagnostics"]),
        }
    return {
        **request_summary(row),
        "args": json.loads(row["args_json"]),
        "idempotency_key": row["idempotency_key"],
        "input_refs": json.loads(row["input_refs_json"]),
        "output_intents": json.loads(row["output_intents_json"]),
        "primary_target": row["primary_target"],
        "precondition_hashes": json.loads(row["precondition_hashes_json"]),
        "causal_refs": json.loads(row["causal_refs_json"]),
        "actor": row["actor"],
        "provenance": json.loads(row["provenance_json"]),
        "schedule_id": row["schedule_id"],
        "kind": row["kind"],
        "job": job,
    }


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


def claim_request(vault: Path, request_id: str, job: dict[str, Any]) -> bool:
    """Mark one pending request running only if it has not been superseded."""
    request_id = safe_filename(request_id)
    now = now_iso()
    running = {**job, "status": "running"}
    with connect(vault) as conn:
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.execute(
            """
            UPDATE operation_requests
            SET status = 'running', started_at = ?, job_json = ?, error = ''
            WHERE request_id = ? AND status = 'pending'
            """,
            (now, _json(running), request_id),
        )
    return cursor.rowcount == 1


def set_request_running(vault: Path, request_id: str, job: dict[str, Any]) -> None:
    _set_request_status(vault, request_id, "running", {**job, "status": "running"})


def finish_request(vault: Path, request_id: str, status: str, job: dict[str, Any]) -> None:
    _set_request_status(vault, request_id, status, job)


def recover_running_requests(vault: Path) -> list[str]:
    if not db_path(vault).is_file():
        return []
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


def append_journal_row(vault: Path, event: dict[str, Any], *, machine: str) -> None:
    """Store an already decorated journal event without provenance fallback."""
    row = dict(event)
    if row.get("machine") != machine:
        raise AssertionError("journal payload machine must match row machine")
    _insert_journal_row(vault, row, machine=machine)


def _insert_journal_row(vault: Path, row: dict[str, Any], *, machine: str) -> None:
    with connect(vault) as conn:
        conn.execute("BEGIN IMMEDIATE")
        insert_journal_row_conn(conn, row, machine=machine)


def insert_journal_row_conn(conn: sqlite3.Connection, row: dict[str, Any], *, machine: str) -> None:
    """Insert one authoritative journal row using the caller's transaction."""
    timestamp = str(row.get("timestamp") or now_iso())
    event_type = str(row.get("event") or row.get("type") or "event")
    payload = _json(row)
    last = conn.execute(
        "SELECT event_id, row_hash FROM event_log ORDER BY event_id DESC LIMIT 1"
    ).fetchone()
    prev_hash = "GENESIS" if last is None else str(last["row_hash"])
    event_id = 1 if last is None else int(last["event_id"]) + 1
    row_hash = _journal_hash(event_id, timestamp, event_type, machine, payload, prev_hash)
    conn.execute(
        """
        INSERT INTO event_log(
            event_id, timestamp, event_type, machine, payload_json, prev_hash, row_hash
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (event_id, timestamp, event_type, machine, payload, prev_hash, row_hash),
    )


def journal_head(vault: Path) -> str:
    with connect(vault) as conn:
        row = conn.execute(
            "SELECT row_hash FROM event_log ORDER BY event_id DESC LIMIT 1"
        ).fetchone()
    return "" if row is None else str(row["row_hash"])


def journal_head_anchor(vault: Path) -> str:
    return journal_head(vault) or "GENESIS"


def write_journal_head_anchor(vault: Path) -> str:
    write_text_durable(Path(vault) / JOURNAL_HEAD_REL, journal_head_anchor(vault) + "\n")
    return JOURNAL_HEAD_REL


def verify_journal_chain(vault: Path) -> dict[str, Any]:
    """Verify the authoritative event chain and its tracked head anchor."""
    with connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT event_id, timestamp, event_type, machine,
                   payload_json, prev_hash, row_hash
            FROM event_log
            ORDER BY event_id
            """
        ).fetchall()

    previous = "GENESIS"
    row_hashes: set[str] = set()
    for row in rows:
        event_id = int(row["event_id"])
        try:
            event = json.loads(str(row["payload_json"]))
            if not isinstance(event, dict):
                raise ValueError("journal payload must be an object")
            expected = _journal_hash(
                event_id,
                str(row["timestamp"]),
                str(row["event_type"]),
                str(row["machine"]),
                str(row["payload_json"]),
                previous,
            )
        except (TypeError, ValueError, json.JSONDecodeError):
            return _journal_verification_failure(
                rows, error=f"journal chain has invalid payload JSON at event {event_id}"
            )
        payload_type = str(event.get("event") or event.get("type") or "event")
        if payload_type != str(row["event_type"]):
            return _journal_verification_failure(
                rows, error=f"journal event type conflicts with payload at event {event_id}"
            )
        if event.get("machine") != str(row["machine"]):
            return _journal_verification_failure(
                rows, error=f"journal machine conflicts with payload at event {event_id}"
            )
        if str(row["prev_hash"]) != previous or str(row["row_hash"]) != expected:
            return _journal_verification_failure(
                rows, error=f"journal chain broken at event {event_id}"
            )
        previous = str(row["row_hash"])
        row_hashes.add(previous)

    tip = previous
    anchor_path = Path(vault) / JOURNAL_HEAD_REL
    try:
        anchor = anchor_path.read_text(encoding="utf-8").strip() if anchor_path.is_file() else ""
    except (OSError, UnicodeError) as exc:
        return _journal_verification_failure(
            rows,
            tip=tip,
            error=f"journal-head anchor is unreadable: {exc}",
        )
    if rows and not anchor:
        return _journal_verification_failure(
            rows,
            tip=tip,
            error="journal-head anchor is missing for a nonempty chain",
        )
    if anchor and anchor != tip:
        return _journal_verification_failure(
            rows,
            tip=tip,
            anchor=anchor,
            error="journal-head anchor does not match chain tip",
        )
    committed_anchor = _committed_journal_head_anchor(Path(vault))
    if committed_anchor is not None and committed_anchor not in {"GENESIS", *row_hashes}:
        return _journal_verification_failure(
            rows,
            tip=tip,
            anchor=anchor,
            error="committed journal-head anchor is not a prefix of the live chain",
        )
    export_error = _journal_export_subset_error(Path(vault), rows)
    if export_error:
        return _journal_verification_failure(
            rows,
            tip=tip,
            anchor=anchor,
            error=export_error,
        )
    return {
        "ok": True,
        "events": len(rows),
        "tip": tip,
        "anchor": anchor,
        "error": "",
    }


def read_event_log(
    vault: Path,
    *,
    event_types: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Read authoritative journal payloads in event order."""
    selected = sorted({str(value) for value in event_types or ()})
    query = "SELECT event_type, machine, payload_json FROM event_log"
    params: tuple[str, ...] = ()
    if selected:
        query += f" WHERE event_type IN ({','.join('?' for _ in selected)})"
        params = tuple(selected)
    query += " ORDER BY event_id"
    with connect(vault) as conn:
        rows = conn.execute(query, params).fetchall()

    events: list[dict[str, Any]] = []
    for row in rows:
        try:
            event = json.loads(str(row["payload_json"]))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("event_log payload must be valid JSON") from exc
        if not isinstance(event, dict):
            raise ValueError("event_log payload must be a JSON object")
        if event.get("machine") != str(row["machine"]):
            raise ValueError("event_log payload machine does not match its row")
        payload_type = str(event.get("event") or event.get("type") or "event")
        if payload_type != str(row["event_type"]):
            raise ValueError("event_log payload type does not match its row")
        events.append(event)
    return events


def journal_export_complete_prefix(raw: bytes) -> bytes:
    """Return the complete CR/LF-delimited journal export records in ``raw``."""
    if not raw or raw.endswith((b"\n", b"\r")):
        return raw
    return raw[: max(raw.rfind(b"\n"), raw.rfind(b"\r")) + 1]


def _journal_export_subset_error(vault: Path, rows: list[Any]) -> str:
    authoritative: Counter[tuple[str, str]] = Counter()
    for row in rows:
        try:
            event = json.loads(str(row["payload_json"]))
        except (TypeError, ValueError, json.JSONDecodeError):
            return f"event_log contains invalid payload JSON at event {row['event_id']}"
        if not isinstance(event, dict):
            return f"event_log payload is not an object at event {row['event_id']}"
        machine = str(row["machine"])
        if event.get("machine") != machine:
            return f"event_log machine conflicts with payload at event {row['event_id']}"
        authoritative[(machine, _json(event))] += 1

    root = vault / ".memoria/journal"
    for path in sorted(root.glob("*.jsonl")):
        try:
            raw = path.read_bytes()
        except OSError as exc:
            return f"journal JSONL export is unreadable: {path.name}: {exc}"
        lines = journal_export_complete_prefix(raw).splitlines()
        machine = path.stem
        for line_number, raw_line in enumerate(lines, start=1):
            try:
                line = raw_line.decode("utf-8")
            except UnicodeDecodeError:
                return f"invalid UTF-8 in {path.name} at line {line_number}"
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                return f"invalid JSONL in {path.name} at line {line_number}"
            if not isinstance(event, dict):
                return f"invalid JSONL object in {path.name} at line {line_number}"
            if event.get("machine") != machine:
                return f"JSONL machine mismatch in {path.name} at line {line_number}"
            key = (machine, _json(event))
            if not authoritative[key]:
                return (
                    f"JSONL event in {path.name} at line {line_number} "
                    "has no authoritative event_log row"
                )
            authoritative[key] -= 1
    return ""


def _committed_journal_head_anchor(vault: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "show", f"HEAD:{JOURNAL_HEAD_REL}"],
            cwd=vault,
            check=False,
            text=True,
            capture_output=True,
        )
    except OSError:
        return None
    return None if proc.returncode else proc.stdout.strip()


def _journal_verification_failure(
    rows: list[Any],
    *,
    error: str,
    tip: str = "",
    anchor: str = "",
) -> dict[str, Any]:
    return {
        "ok": False,
        "events": len(rows),
        "tip": tip,
        "anchor": anchor,
        "error": error,
    }


def set_concept_verdict(vault: Path, concept_id: str, check_status: str) -> None:
    status = _check_status(check_status)
    with connect(vault) as conn:
        # One key space per identity: the verdict and its flags are both FK-backed
        # by concepts.concept_id, so resolve once and write both by that id.
        # `outputs` keeps its own path-keyed output_id space.
        target = resolve_concept_id(conn, concept_id)
        _set_concept_verdict_conn(conn, target, status)
        conn.execute(
            "UPDATE outputs SET check_status = ? WHERE output_id = ?",
            (status, normalize_path(concept_id)),
        )
        if status == "checked":
            # Re-verification wipes the propagation mark in both places it lives:
            # the compatibility `stale` flag and the v19 verdict-row mirror.
            conn.execute(
                "DELETE FROM concept_flags WHERE concept_id = ? AND flag = 'stale'",
                (target,),
            )
            conn.execute(
                "UPDATE concept_verdicts SET consequence = '' WHERE concept_id = ?",
                (target,),
            )


def set_catalog_check_status(vault: Path, work_id: str, check_status: str) -> None:
    """The one writer for a catalog Work's verdict.

    Keeps every store the read-barrier/retrieval path gates on in step, in
    one transaction: `catalog_sources.check_status`, the `concept_verdicts`
    row, the `passages.check_status` cascade retrieval filters on, and the
    `outputs.check_status` mirror when a file-backed output row exists (a
    catalog Work is db-store, so this is structurally a no-op for it).
    Re-checking clears the propagation mark exactly like
    `set_concept_verdict`. Scope excludes `work_aspects.check_status`
    (written at capture time), which nothing consumes without first
    checking `catalog_sources`.
    """
    status = _check_status(check_status)
    stable_work_id = _work_id(work_id)
    with connect(vault) as conn:
        conn.execute(
            "UPDATE catalog_sources SET check_status = ? WHERE work_id = ?",
            (status, stable_work_id),
        )
        target = resolve_concept_id(conn, stable_work_id)
        _set_concept_verdict_conn(conn, target, status)
        conn.execute(
            "UPDATE outputs SET check_status = ? WHERE output_id = ?",
            (status, normalize_path(stable_work_id)),
        )
        if status == "checked":
            conn.execute(
                "DELETE FROM concept_flags WHERE concept_id = ? AND flag = 'stale'",
                (target,),
            )
            conn.execute(
                "UPDATE concept_verdicts SET consequence = '' WHERE concept_id = ?",
                (target,),
            )


def concept_check_status(vault: Path, concept_id: str) -> str:
    if not db_path(vault).is_file():
        return "unchecked"
    with connect(vault) as conn:
        row = conn.execute(
            "SELECT check_status FROM concept_status WHERE concept_id = ?",
            (resolve_concept_id(conn, concept_id),),
        ).fetchone()
    return "unchecked" if row is None else str(row["check_status"])


def concept_check_statuses(vault: Path) -> dict[str, str]:
    """Return every Concept verdict keyed by its rendered path, id when it has none.

    v16 decouples the identity from the path, so this bulk projection keys by the
    path its one caller walks the vault by — the id-keyed map it used to return
    reads as ``unchecked`` for every ULID-keyed file Concept.
    """
    if not db_path(vault).is_file():
        return {}
    with connect(vault) as conn:
        rows = conn.execute("SELECT concept_id, path, check_status FROM concept_status").fetchall()
    return {str(row["path"] or row["concept_id"]): str(row["check_status"]) for row in rows}


def output_record(vault: Path, output_id: str) -> dict[str, Any] | None:
    target = normalize_path(output_id)
    if not db_path(vault).is_file():
        return None
    with connect(vault) as conn:
        row = conn.execute(
            """
            SELECT output_id, concept_type, store, target_path, check_status,
                   materialization_status, materialized_commit, output_sha256
            FROM outputs
            WHERE output_id = ?
            """,
            (target,),
        ).fetchone()
    return None if row is None else dict(row)


def rebuild_file_concept_mirror(vault: Path, rows: Iterable[dict[str, str]]) -> dict[str, int]:
    """Rebuild identity-keyed file Concept parents, normalizing types through the registry.

    Each row carries its own ``concept_id`` and ``path``: v16 decouples the two, so
    a row whose ``id`` is a frontmatter ULID keeps that identity across a rename,
    and one without a ULID keeps its path key. Only absent file rows carrying no
    verdict are pruned: a verdict-bearing row is the PI's judgment and survives its
    file. Pruning a row cascades its outgoing edges and pends inbound ones through
    the v16 foreign keys. A reconciled rename also carries the path-keyed ``outputs``
    row to the new path, so the read barrier still finds the PI's checked record
    there (``_reconcile_renamed_output_conn``).
    """
    rows = list(rows)
    _refuse_duplicate_batch_identities(rows)
    with connect(vault) as conn:
        for row in rows:
            _reconcile_renamed_output_conn(
                conn,
                normalize_path(row["concept_id"]),
                normalize_path(str(row.get("path") or row["concept_id"])),
            )
        keep = [
            ensure_concept_parent_conn(
                conn,
                normalize_path(row["concept_id"]),
                concept_type=str(row["concept_type"]),
                store="file",
                path=normalize_path(str(row.get("path") or row["concept_id"])),
            )
            for row in rows
        ]
        deleted = conn.execute(
            """
            DELETE FROM concepts
            WHERE store = 'file'
              AND concept_id NOT IN (SELECT value FROM json_each(?))
              AND concept_id NOT IN (SELECT concept_id FROM concept_verdicts)
            """,
            (_json(keep),),
        ).rowcount
    return {"deleted": int(deleted), "inserted": len(rows)}


def update_concept_path(vault: Path, concept_id: str, old_path: str, new_path: str) -> None:
    """Move one Concept's path across every path-keyed table, in one transaction.

    The in-band seam behind ``memoria mv``. It is a strict superset of the
    out-of-band reconcile it calls (``_reconcile_renamed_output_conn``): that pass
    only has to keep the materialization ledger findable at the new path, while a
    move must also carry the edge mirror, the passage index and
    ``file_index_state`` — the row the out-of-band pass strands, and the one
    ``refresh_stale_passages`` computes its removed set from. The reconcile
    statement is *called*, never re-issued: it shipped a Critical once already
    (``materialization_payloads`` had no ``ON UPDATE CASCADE``) and a second copy
    is a second place for the next one to hide. For the same reason neither
    enumeration is written out here: ``_rekey_path_keyed_concept_conn`` is identity
    space and ``_rekey_path_space_conn`` is path space, one named home each.

    Nothing here touches ``output_sha256``. A rename does not change a byte, so
    the barrier keeps hashing the same content at the new path and edited content
    still cannot keep a ``checked`` verdict.
    """
    old_rel = normalize_path(old_path)
    new_rel = normalize_path(new_path)
    with connect(vault) as conn:
        if concept_id == new_rel:
            _rekey_path_keyed_concept_conn(conn, old_rel, new_rel)
        # Reads `concepts.path` for the old key, so it runs before that column moves.
        _reconcile_renamed_output_conn(conn, concept_id, new_rel)
        conn.execute("UPDATE concepts SET path = ? WHERE concept_id = ?", (new_rel, concept_id))
        _rekey_path_space_conn(conn, old_rel, new_rel)


def _rekey_path_space_conn(conn: sqlite3.Connection, old_rel: str, new_rel: str) -> None:
    """Move every row that references a Concept by its **path**, and this is the whole set.

    Identity space is ``_rekey_path_keyed_concept_conn`` and the materialization
    ledger is ``_reconcile_renamed_output_conn``; this is the third enumeration,
    and it lives in one named place because each of the first two shipped a defect
    by stopping one table short. Add here, never at a call site.

    The two tables the first path-space pass missed are the two that key no
    verdict, which is exactly why they hid. ``file_baseline`` keys the *alert*
    layer: leave its row at the vacated path and both ``_reconcile_file_baselines``
    and the observe loop take their ``baseline is None`` early exit, so a tampered
    moved file raises no ``foreign-edit`` and the baseline adopts the tampered
    bytes as truth — while a newcomer at the vacated path inherits the stale hash
    and raises a ``foreign-edit`` nobody caused. ``evidence_sets.block_ref`` is
    ``{path}#^blk-…`` and a draft's evidence is joined by prefix, so a stale prefix
    reads as a draft with no evidence at all; ``evidence_bindings`` is immutable by
    trigger, so the binding cannot simply be reissued afterwards.

    ``UPDATE OR REPLACE`` carries the caller's stated reverse limit: a row already
    sitting at the destination is dropped, and reversing the update cannot
    resurrect it.
    """
    conn.execute(
        "UPDATE OR REPLACE concept_edges SET target_path = ? WHERE target_path = ?",
        (new_rel, old_rel),
    )
    conn.execute(
        "UPDATE concept_edges SET source_path = ? WHERE source_path = ?", (new_rel, old_rel)
    )
    conn.execute("UPDATE passages SET path = ? WHERE path = ?", (new_rel, old_rel))
    conn.execute(
        "UPDATE OR REPLACE file_index_state SET path = ? WHERE path = ?", (new_rel, old_rel)
    )
    conn.execute(
        "UPDATE OR REPLACE file_baseline SET subject_id = ? WHERE subject_id = ?",
        (new_rel, old_rel),
    )
    # Exact-prefix rewrite, not LIKE: a path may hold `%` or `_`, which LIKE would
    # read as wildcards and match a sibling Concept's block refs.
    prefix = f"{old_rel}#"
    conn.execute(
        "UPDATE evidence_sets SET block_ref = ? || substr(block_ref, ?) "
        "WHERE substr(block_ref, 1, ?) = ?",
        (f"{new_rel}#", len(prefix) + 1, len(prefix), prefix),
    )


def _rekey_path_keyed_concept_conn(conn: sqlite3.Connection, old_id: str, new_id: str) -> None:
    """Move a path-keyed Concept's identity, and every row that keys by it without an FK.

    A Concept with no frontmatter ULID keys by its path, so a rename moves its
    identity too. Left behind, the next file dropped at the vacated path resolves
    onto this row and inherits the PI's verdict.

    ``concept_verdicts``, ``concept_flags`` and ``concept_edges``' endpoint ids all
    declare ``REFERENCES concepts(concept_id) ON UPDATE CASCADE``, so they ride the
    first statement. **Everything below keys by the same identity with no foreign
    key to carry it, and this is the whole enumeration** — the reason it lives in
    one named place is that the first pass at it stopped one table short and left
    ``passages.concept_id`` at the vacated path, where the verdict-cascade triggers
    (``WHERE concept_id = NEW.concept_id``) hand the *moved* Concept's passages to
    whatever lands there next while its verdict still reads ``checked``. Add here,
    never at a call site.

    A conflicting id raises and rolls the caller's whole move back, which is the
    refusal it wants.

    ``concept_edges.edge_id`` is a hash of the identity triple, so the cascade
    invalidates it on every edge touching this Concept. It is blanked here rather
    than recomputed in place: ``idx_concept_edges_edge_id`` is UNIQUE and checked
    per statement, so a row recomputed to a value another affected row is still
    carrying stale would raise mid-enumeration. ``''`` is already this column's
    unresolved value and the partial index skips it, so the next
    ``replace_concept_edges`` settles it over the live triple. A *stale* id instead
    survives as a plausible-looking hash that the next file dropped at the vacated
    path recomputes exactly — a UNIQUE violation that kills the whole mirror
    rebuild, which is the one failure "it self-heals next pass" cannot cover.
    """
    conn.execute("UPDATE concepts SET concept_id = ? WHERE concept_id = ?", (new_id, old_id))
    conn.execute("UPDATE derivations SET input_id = ? WHERE input_id = ?", (new_id, old_id))
    conn.execute("UPDATE derivations SET output_id = ? WHERE output_id = ?", (new_id, old_id))
    conn.execute("UPDATE passages SET concept_id = ? WHERE concept_id = ?", (new_id, old_id))
    conn.execute(
        "UPDATE concept_edges SET edge_id = ''"
        " WHERE source_concept_id = ? OR target_concept_id = ?",
        (new_id, new_id),
    )


def _reconcile_renamed_output_conn(
    conn: sqlite3.Connection, concept_id: str, new_path: str
) -> None:
    """Carry the path-keyed materialization ledger row along a reconciled rename.

    ``outputs`` stays path-keyed (NID-B.2), but its key is the *current* path: a
    rename that reconciles ``concepts.path`` must move it, or the read barrier
    reads no checked output record at the new path and refuses content the PI did
    check. The sha256 comparison in ``is_consumable_checked_file`` is untouched, so
    a rename *and* edit arriving in one reindex pass is still refused. An edit made
    after the rename has been indexed is a different case: ``indexing`` re-indexes
    any path already recorded ``checked`` without re-running the barrier, which it
    does for a never-renamed file too — this reconcile leaves a renamed file at
    exactly that standing, neither creating nor widening the gap.

    The FK to ``outputs`` from ``materialization_payloads`` is ``ON UPDATE
    CASCADE`` (``schema.sql``) so this key move carries the writer's payload child
    with it; without that the statement violates the constraint on any Concept
    staged through ``record_file_output``.
    """
    resident = conn.execute(
        "SELECT path FROM concepts WHERE concept_id = ?", (concept_id,)
    ).fetchone()
    old_path = str(resident["path"]) if resident is not None else ""
    if not old_path or not new_path or old_path == new_path:
        return
    conn.execute(
        "UPDATE OR REPLACE outputs SET output_id = ?, target_path = ? WHERE output_id = ?",
        (new_path, new_path, old_path),
    )


def _refuse_duplicate_batch_identities(rows: list[dict[str, str]]) -> None:
    """Refuse a mirror batch in which two files claim one Concept identity.

    Copying a file (``cp``, Obsidian's "Make a copy") duplicates its frontmatter
    ``id``. Per row that reads as *same identity, requested path unowned* — a
    rename, which the guard allows — so the batch is the only place the duplicate
    is visible. Left unchecked the later row moves the Concept's path onto content
    the PI never reviewed and hands it the verdict rendered over the original,
    with directory order deciding the survivor. This is the dual of two identities
    claiming one path, which ``ensure_concept_parent_conn`` already refuses.
    """
    seen: dict[str, str] = {}
    for row in rows:
        concept_id = normalize_path(str(row["concept_id"]))
        path = normalize_path(str(row.get("path") or row["concept_id"]))
        if concept_id in seen:
            raise RuntimeError(
                f"duplicate Concept identity in one mirror batch: concept_id={concept_id!r}"
                f" is claimed by both {seen[concept_id]!r} and {path!r}; give each file its"
                " own frontmatter id before mirroring"
            )
        seen[concept_id] = path


def record_file_output(
    vault: Path,
    *,
    output_id: str,
    concept_type: str,
    check_status: str,
    output_sha256: str,
    staging_id: str,
    payload_text: str,
    context: OperationContext,
    inputs: Iterable[dict[str, Any]],
) -> None:
    target = normalize_path(output_id)
    if not payload_text:
        raise ValueError("file materialization payload is required")
    if _sha256_text(payload_text) != output_sha256:
        raise ValueError(f"materialization payload hash mismatch for {target}")
    with connect(vault) as conn:
        # `outputs` and its materialization payload stay path-keyed; the Concept
        # parent, its verdict, and the derivation endpoints use the file identity.
        key = ensure_concept_parent_conn(
            conn,
            _concept_key_for_file(vault, target, payload_text),
            concept_type=concept_type,
            store="file",
            path=target,
        )
        _set_concept_verdict_conn(conn, key, _check_status(check_status))
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
                    INSERT INTO derivations(input_id, output_id, actor)
                    VALUES (?, ?, ?)
                    ON CONFLICT(input_id, output_id)
                    DO UPDATE SET actor = excluded.actor
                    """,
                    (resolve_concept_id(conn, input_id), key, context.actor),
                )


def mark_checked(vault: Path, output_id: str, output_sha256: str, payload_text: str = "") -> None:
    target = normalize_path(output_id)
    with connect(vault) as conn:
        conn.execute(
            "UPDATE outputs SET check_status = 'checked', output_sha256 = ? WHERE output_id = ?",
            (output_sha256, target),
        )
        # Same one-key-space rule as set_concept_verdict: the flag delete must use
        # the resolved identity, not the raw output path.
        concept_id = resolve_concept_id(conn, target)
        _set_concept_verdict_conn(conn, concept_id, "checked")
        conn.execute(
            "DELETE FROM concept_flags WHERE concept_id = ? AND flag = 'stale'",
            (concept_id,),
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


def refresh_output_sha256(vault: Path, output_id: str, output_sha256: str) -> None:
    """Record new bytes for an existing output without re-judging it.

    A machine write that only *labels* a Concept — the typed-consequence mark —
    moves the file's hash without changing what the PI checked, and ``outputs``
    holds the hash ``read_barrier.is_consumable_checked_file`` compares the file
    against. Leaving it behind makes the labelling writer's own write read as a
    foreign edit, so the note it labelled stops being consumable as checked and
    every reader enqueues a scan for it. Only the hash moves: ``check_status``,
    ``materialization_status`` and the verdict all stay as they were, because a
    label is not a verdict (the same rule ``set_concept_consequence`` follows).
    """
    with connect(vault) as conn:
        conn.execute(
            "UPDATE outputs SET output_sha256 = ? WHERE output_id = ?",
            (output_sha256, normalize_path(output_id)),
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
        key = ensure_concept_parent_conn(
            conn,
            _concept_key_for_file(vault, target),
            concept_type=concept_type,
            store="file",
            path=target,
        )
        _set_concept_verdict_conn(conn, key, "unchecked")
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


def upsert_file_baseline(
    vault: Path,
    subject_id: str,
    *,
    human_sha256: str,
    restriction_keys: list[str],
) -> None:
    target = normalize_path(subject_id)
    keys = [str(key) for key in restriction_keys]
    with connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO file_baseline(subject_id, human_sha256, restriction_keys_json, observed_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(subject_id) DO UPDATE SET
                human_sha256 = excluded.human_sha256,
                restriction_keys_json = excluded.restriction_keys_json,
                observed_at = excluded.observed_at
            """,
            (target, human_sha256, _json(keys), now_iso()),
        )


def file_baseline(vault: Path, subject_id: str) -> dict[str, Any] | None:
    if not db_path(vault).is_file():
        return None
    target = normalize_path(subject_id)
    with connect(vault) as conn:
        row = conn.execute(
            """
            SELECT subject_id, human_sha256, restriction_keys_json
            FROM file_baseline
            WHERE subject_id = ?
            """,
            (target,),
        ).fetchone()
    if row is None:
        return None
    return {
        "subject_id": row["subject_id"],
        "human_sha256": row["human_sha256"],
        "restriction_keys": json.loads(row["restriction_keys_json"] or "[]"),
    }


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
    with connect(vault) as conn:
        # v16 keys flags by the resolved Concept identity: the FK to
        # concepts(concept_id) rejects a flag on a Concept that does not exist and
        # cascades the row away when that Concept is pruned.
        target = resolve_concept_id(conn, concept_id)
        try:
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
        except sqlite3.IntegrityError as exc:
            if "FOREIGN KEY" not in str(exc):
                raise
            raise _concept_missing_parent(concept_id, target, f"flag {flag!r}") from exc


def concept_flags(vault: Path, concept_id: str) -> dict[str, dict[str, str]]:
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
            (resolve_concept_id(conn, concept_id),),
        ).fetchall()
    return {
        str(row["flag"]): {
            "reason": str(row["reason"]),
            "trigger_id": str(row["trigger_id"]),
            "created_at": str(row["created_at"]),
        }
        for row in rows
    }


def set_concept_consequence(vault: Path, concept_id: str, consequence: str) -> None:
    """Mirror a typed-consequence mark on the verdict row (EDGES section 5).

    The mark is a statement about what fell upstream, not a re-judgment, so the
    upsert leaves an existing ``check_status`` alone and inserts at ``unchecked``
    when the Concept has no verdict yet. The roster lives in the column's CHECK,
    which is where an unrostered value is refused. Identity, not path: the walk
    that produces these marks names Concepts by their rendered path, and v16
    keys the verdict row by the identity that path resolves to.
    """
    with connect(vault) as conn:
        target = resolve_concept_id(conn, concept_id)
        try:
            conn.execute(
                """
                INSERT INTO concept_verdicts(concept_id, check_status, consequence)
                VALUES (?, 'unchecked', ?)
                ON CONFLICT(concept_id) DO UPDATE SET consequence = excluded.consequence
                """,
                (target, consequence),
            )
        except sqlite3.IntegrityError as exc:
            if "FOREIGN KEY" not in str(exc):
                raise
            raise _concept_missing_parent(concept_id, target, "consequence") from exc


def concept_consequence(vault: Path, concept_id: str) -> str:
    """Return the mirrored consequence mark, ``''`` when unmarked, unknown, or DB-less."""
    if not db_path(vault).is_file():
        return ""
    with connect(vault) as conn:
        row = conn.execute(
            "SELECT consequence FROM concept_verdicts WHERE concept_id = ?",
            (resolve_concept_id(conn, concept_id),),
        ).fetchone()
    return "" if row is None else str(row["consequence"])


def concept_exists(vault: Path, concept_id: str) -> bool:
    """Return whether the mirror already holds this Concept, minting nothing.

    ``resolve_concept_id`` answers with the normalized reference itself when
    nothing is mirrored, so it cannot tell a known Concept from an unknown one.
    Every FK-backed writer above — ``set_concept_flag``,
    ``set_concept_consequence`` — refuses a reference with no ``concepts`` row,
    and the graph legally names nodes the mirror has never seen: a forward link
    to a note that does not exist yet parks as a pending edge whose
    ``target_path`` still projects into path space. A caller walking that graph
    has to be able to ask before it writes.
    """
    if not db_path(vault).is_file():
        return False
    with connect(vault) as conn:
        return _lookup_concept_id(conn, concept_id) is not None


def note_curation_status(vault: Path, concept_id: str) -> str:
    """Return note-candidate lifecycle from journal events, not frontmatter."""
    target = normalize_path(concept_id)
    if not db_path(vault).is_file():
        return ""
    status = ""
    with connect(vault) as conn:
        rows = conn.execute("SELECT payload_json FROM event_log ORDER BY event_id").fetchall()
    # ponytail: journal scan is fine at current volume; project if candidate volume matters.
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
    if not db_path(vault).is_file():
        return []
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


def upsert_catalog_record(
    vault: Path,
    *,
    work_id: str,
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
    stable_work_id = _work_id(work_id)
    identifiers = dict(identifiers or {})
    csl_json = dict(csl_json or {})
    stable_doi = str(doi or identifiers.get("doi") or csl_json.get("DOI") or "").strip() or None
    with connect(vault) as conn:
        concept_id = ensure_concept_parent_conn(
            conn,
            stable_work_id,
            concept_type="work",
            store="db",
            path=f"catalog/sources/{stable_work_id}",
        )
        conn.execute(
            """
            INSERT INTO catalog_sources(
                work_id,
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
            ON CONFLICT(work_id) DO UPDATE SET
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
                stable_work_id,
                normalize_path(concept_path)
                if concept_path
                else f"catalog/sources/{stable_work_id}",
                stable_doi,
                title or stable_work_id,
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
        _set_concept_verdict_conn(conn, concept_id, _check_status(check_status))


def catalog_source(vault: Path, source_ref: str) -> dict[str, Any] | None:
    if not db_path(vault).is_file():
        return None
    work_id = _work_id(source_ref)
    with connect(vault) as conn:
        row = conn.execute(
            "SELECT * FROM catalog_sources WHERE work_id = ?",
            (work_id,),
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
                ORDER BY work_id
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT *
                FROM catalog_sources
                ORDER BY work_id
                """
            ).fetchall()
    return [_source_row(row) for row in rows]


def start_enrichment_run(
    vault: Path,
    *,
    run_id: str,
    work_id: str,
    required_provider_policy: dict[str, Any],
    request_id: str = "",
) -> None:
    with connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO enrichment_runs(
                run_id,
                work_id,
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
            (run_id, _work_id(work_id), _json(required_provider_policy), now_iso(), request_id),
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
    work_id: str,
    rows: Iterable[dict[str, Any]],
) -> None:
    stable_work_id = _work_id(work_id)
    with connect(vault) as conn:
        conn.execute("DELETE FROM field_provenance WHERE work_id = ?", (stable_work_id,))
        for row in rows:
            conn.execute(
                """
                INSERT INTO field_provenance(
                    work_id,
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
                    stable_work_id,
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
                    confidence
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(row["owner_type"]),
                    str(row["owner_id"]),
                    str(row["namespace"]),
                    str(row["value"]),
                    str(row.get("source_provider") or ""),
                    str(row.get("confidence") or "high"),
                ),
            )


def replace_work_graph_edges(vault: Path, work_id: str, rows: Iterable[dict[str, Any]]) -> None:
    stable_work_id = _work_id(work_id)
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


def related_work_candidates(
    vault: Path, work_ids: Sequence[str], limit: int
) -> list[dict[str, Any]]:
    """Rank other catalog works by shared 'references' targets with a work set."""
    ids = sorted({_work_id(work_id) for work_id in work_ids if str(work_id).strip()})
    if not ids or limit <= 0:
        return []
    with connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT other.work_id AS work_id,
                   COUNT(DISTINCT other.target_id) AS shared_references
            FROM work_graph_edges AS mine
            JOIN work_graph_edges AS other
              ON other.relation_type = 'references'
             AND other.target_id = mine.target_id
            WHERE mine.relation_type = 'references'
              AND mine.work_id IN (SELECT value FROM json_each(?))
              AND other.work_id NOT IN (SELECT value FROM json_each(?))
            GROUP BY other.work_id
            ORDER BY shared_references DESC, other.work_id ASC
            LIMIT ?
            """,
            (_json(ids), _json(ids), limit),
        ).fetchall()
    return [
        {"work_id": str(row["work_id"]), "shared_references": int(row["shared_references"])}
        for row in rows
    ]


def replace_work_aspects(vault: Path, source_ref: str, rows: Iterable[dict[str, Any]]) -> None:
    work_id = _work_id(source_ref)
    with connect(vault) as conn:
        conn.execute("DELETE FROM work_aspects WHERE work_id = ?", (work_id,))
        for row in rows:
            aspect_text = str(row.get("aspect_text") or "").strip()
            if not aspect_text:
                continue
            aspect_type = _work_aspect_type(str(row.get("aspect_type") or ""))
            conn.execute(
                """
                INSERT INTO work_aspects(
                    work_id,
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
                    work_id,
                    aspect_type,
                    aspect_text,
                    str(row.get("anchor_text") or "").strip(),
                    _check_status(str(row.get("check_status") or "unchecked")),
                    str(row.get("source_provider") or "deterministic"),
                    now_iso(),
                ),
            )


def replace_indexed_passages(
    vault: Path,
    rows: Iterable[dict[str, Any]],
    *,
    paths: Iterable[str] | None = None,
) -> dict[str, int]:
    rows = [dict(row) for row in rows]
    target_paths = {normalize_path(path) for path in paths or []}
    now = now_iso()
    with connect(vault) as conn:
        if target_paths:
            for path in sorted(target_paths):
                conn.execute("DELETE FROM passages WHERE path = ?", (path,))
                conn.execute("DELETE FROM file_index_state WHERE path = ?", (path,))
        else:
            conn.execute("DELETE FROM passages")
            conn.execute("DELETE FROM file_index_state")
        for row in rows:
            text = str(row["text"])
            path = normalize_path(str(row["path"]))
            check_status = _check_status(str(row.get("check_status") or "unchecked"))
            text_sha256 = str(row.get("text_sha256") or _sha256_text(text))
            passage_id = str(row.get("passage_id") or _passage_id(path, text_sha256))
            vector = row.get("vector")
            conn.execute(
                """
                INSERT INTO passages(
                    passage_id,
                    origin,
                    concept_id,
                    work_id,
                    path,
                    anchor,
                    page,
                    byte_start,
                    byte_end,
                    text_sha256,
                    text,
                    check_status,
                    mode,
                    question_status,
                    source_mtime_ns,
                    indexed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    passage_id,
                    str(row.get("origin") or "file"),
                    normalize_path(str(row.get("concept_id") or path)),
                    str(row.get("work_id") or ""),
                    path,
                    str(row.get("anchor") or ""),
                    str(row.get("page") or ""),
                    int(row.get("byte_start") or 0),
                    int(row.get("byte_end") or len(text.encode())),
                    text_sha256,
                    text,
                    check_status,
                    str(row.get("mode") or ""),
                    str(row.get("question_status") or ""),
                    int(row.get("source_mtime_ns") or 0),
                    now,
                ),
            )
            if isinstance(vector, list) and vector:
                conn.execute(
                    """
                    INSERT INTO passage_vec(
                        passage_id,
                        text_sha256,
                        embedding_model_id,
                        vector_dim,
                        vector_json,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        passage_id,
                        text_sha256,
                        str(row.get("embedding_model_id") or "memoria-hash-test-v1"),
                        int(row.get("vector_dim") or len(vector)),
                        _json(vector),
                        now,
                    ),
                )
            conn.execute(
                """
                INSERT INTO file_index_state(
                    path,
                    source_mtime_ns,
                    source_sha256,
                    check_status,
                    indexed_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    source_mtime_ns = excluded.source_mtime_ns,
                    source_sha256 = excluded.source_sha256,
                    check_status = excluded.check_status,
                    indexed_at = excluded.indexed_at
                """,
                (
                    path,
                    int(row.get("source_mtime_ns") or 0),
                    text_sha256,
                    check_status,
                    now,
                ),
            )
    return {"inserted": len(rows), "paths": len({str(row["path"]) for row in rows})}


def indexed_passages(vault: Path, *, checked_only: bool = False) -> list[dict[str, Any]]:
    if not db_path(vault).is_file():
        return []
    with connect(vault) as conn:
        if checked_only:
            rows = conn.execute(
                """
                SELECT *
                FROM passages
                WHERE check_status = 'checked'
                ORDER BY path, passage_id
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT *
                FROM passages
                ORDER BY path, passage_id
                """
            ).fetchall()
    return [dict(row) for row in rows]


def file_index_states(vault: Path) -> dict[str, dict[str, Any]]:
    if not db_path(vault).is_file():
        return {}
    with connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT path, source_mtime_ns, source_sha256, check_status, indexed_at
            FROM file_index_state
            ORDER BY path
            """
        ).fetchall()
    return {str(row["path"]): dict(row) for row in rows}


def replace_concept_edges(
    vault: Path,
    rows: Iterable[dict[str, Any]],
    *,
    paths: Iterable[str] | None = None,
) -> dict[str, int]:
    """Reconcile the links mirror without changing PI-owned tension rows.

    Rows key by the v16 scoped triple ``(source_concept_id, relation_type,
    target_path)``, so the bare, rendered, ``./``, and ``/source.md`` catalog
    forms share one edge. Sources are resolved or ensured; targets are resolved
    but never created, and an unresolved target parks the edge as a pending row.
    ``paths=None`` is a full mirror pass; an empty scope is a no-op.
    """
    path_list = None if paths is None else list(paths)
    if path_list == []:
        return {"deleted": 0, "inserted": 0}
    target_paths = (
        None
        if path_list is None
        else {normalize_path(str(path)) for path in path_list if normalize_path(str(path))}
    )

    with connect(vault) as conn:
        catalog_ids = {
            str(row["work_id"]) for row in conn.execute("SELECT work_id FROM catalog_sources")
        }
        prepared = []
        for value in rows:
            row = dict(value)
            relation = _concept_edge_relation(str(row["relation_type"]))
            if relation == "tension":
                continue
            source_path = normalize_path(str(row.get("source_path") or ""))
            if target_paths is not None and source_path not in target_paths:
                continue
            source = _resolve_or_ensure_concept_conn(
                conn, normalize_path(str(row["source_concept_id"]))
            )
            target_path = _concept_edge_target_path(
                str(row.get("target_path") or row.get("target_concept_id") or ""), catalog_ids
            )
            prepared.append((row, source, relation, target_path, source_path))

        keep = {(source, relation, path) for _row, source, relation, path, _ in prepared}
        existing = conn.execute(
            """
            SELECT source_concept_id, relation_type, target_path, source_path
            FROM concept_edges
            WHERE relation_type != 'tension'
            """
        ).fetchall()
        deleted = 0
        for stale in existing:
            key = (
                str(stale["source_concept_id"]),
                str(stale["relation_type"]),
                str(stale["target_path"]),
            )
            if key in keep:
                continue
            if target_paths is not None and str(stale["source_path"]) not in target_paths:
                continue
            conn.execute(
                """
                DELETE FROM concept_edges
                WHERE source_concept_id = ? AND relation_type = ? AND target_path = ?
                """,
                key,
            )
            deleted += 1
        for row, source, relation, target_path, source_path in prepared:
            target_id = _lookup_concept_id(conn, target_path)
            conn.execute(
                """
                INSERT INTO concept_edges(
                    edge_id,
                    source_concept_id,
                    relation_type,
                    target_concept_id,
                    target_path,
                    attributes_json,
                    check_status,
                    source_path,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_concept_id, relation_type, target_path)
                DO UPDATE SET
                    edge_id = CASE
                        WHEN excluded.edge_id != '' THEN excluded.edge_id
                        ELSE concept_edges.edge_id
                    END,
                    target_concept_id = COALESCE(
                        excluded.target_concept_id, concept_edges.target_concept_id
                    ),
                    check_status = excluded.check_status,
                    source_path = excluded.source_path,
                    updated_at = excluded.updated_at
                """,
                (
                    concept_edge_id(source, relation, target_id) if target_id else "",
                    source,
                    relation,
                    target_id,
                    target_path,
                    str(row.get("attributes_json") or "{}"),
                    _check_status(str(row.get("check_status") or "unchecked")),
                    source_path,
                    now_iso(),
                ),
            )
        # After the loop, not before: this pass's own inserts can mint the Concept a
        # retained row has been waiting for. Running it first is not a corruption --
        # those rows just wait one more reindex -- which is why nothing pins the
        # ordering.
        _resolve_pending_concept_edges_conn(conn)
    return {"deleted": int(deleted), "inserted": len(prepared)}


def _resolve_pending_concept_edges_conn(conn: sqlite3.Connection) -> None:
    """Settle every retained edge row the upsert loop above never reached (NODES §1.6).

    A forward link to a note that does not exist yet is legal Zettelkasten practice,
    so the mirror parks it as a pending row instead of dropping it. The loop
    re-resolves only the rows it (re)inserts, which leaves two kinds behind: a
    PI-owned ``tension`` row, which the loop skips by design and no reindex ever
    rewrites, and any pending row a scoped pass spared. Both have to resolve at the
    reindex where their target materializes, or a dangling link stays dangling for
    the life of the vault.

    The same pass recomputes a blank ``edge_id``, which is what an identity re-key
    leaves behind (``_rekey_path_keyed_concept_conn``). Resolution and recomputation
    are one pass because they answer one question — does this row's stored identity
    still agree with the id space — and write the answer the same way.
    ``_lookup_concept_id`` is the module's one resolver, so a catalog reference
    resolves here exactly as it does at insert.

    **This pass is graph-wide and ignores the caller's ``paths`` scope.** That is
    deliberate — the rows it settles are exactly the ones a scoped pass spared, so
    scoping it would re-create the leak — but it does mean a scoped
    ``replace_concept_edges`` can write rows outside the requested scope, while an
    empty scope still short-circuits before reaching here. ``indexing.py`` is the
    only caller today and passes ``paths=None``; a future scoped caller has to
    accept that asymmetry or move the pass out of this function.
    """
    unsettled = conn.execute(
        "SELECT source_concept_id, relation_type, target_path, target_concept_id"
        " FROM concept_edges WHERE target_concept_id IS NULL OR edge_id = ''"
    ).fetchall()
    for row in unsettled:
        target_path = str(row["target_path"])
        target_id = row["target_concept_id"] or _lookup_concept_id(conn, target_path)
        if not target_id:
            continue
        source = str(row["source_concept_id"])
        relation = str(row["relation_type"])
        conn.execute(
            """
            UPDATE concept_edges
            SET target_concept_id = ?, edge_id = ?
            WHERE source_concept_id = ? AND relation_type = ? AND target_path = ?
            """,
            (
                target_id,
                concept_edge_id(source, relation, str(target_id)),
                source,
                relation,
                target_path,
            ),
        )


def _resolve_or_ensure_concept_conn(conn: sqlite3.Connection, ref: str) -> str:
    """Return an edge endpoint's parent id, minting a registry-shaped one if absent."""
    resolved = _lookup_concept_id(conn, ref)
    if resolved is not None:
        return resolved
    concept_type, store, path = _concept_parent_shape(ref)
    return ensure_concept_parent_conn(conn, ref, concept_type=concept_type, store=store, path=path)


def _concept_edge_target_path(raw_target: str, catalog_ids: set[str]) -> str:
    """Return the v16 edge path key: catalog references collapse to one rendering."""
    rel = normalize_path(raw_target)
    rendered = rel.removeprefix("catalog/sources/").removesuffix("/source.md")
    return f"catalog/sources/{rendered}" if rendered in catalog_ids else rel


def insert_concept_edge(
    vault: Path,
    *,
    source: str,
    relation_type: str,
    target: str,
    attributes: dict[str, Any] | None = None,
    context: OperationContext,
) -> dict[str, Any]:
    """Upsert one PI-confirmed concept edge without touching any other row.

    The single-row seam for edges no frontmatter mirrors — a confirmed
    ``tension``, or warrant text hung on a grounding edge. On conflict the given
    attributes merge over the stored ``attributes_json``; ``None`` leaves the
    stored attributes untouched, and the row's ``check_status``/``source_path``
    stay as written so hanging an attribute on a mirrored edge never takes that
    edge out of the demotion triggers' scope.

    Both endpoints resolve through the exact functions ``replace_concept_edges``
    uses, because this is the second writer into one keyspace. ``source`` may be
    spelled as a path or as an identity and resolves to one ``concepts`` key,
    minting nothing: an unmirrored source is a foreign-key refusal, not a new
    Concept. ``target`` is path space, and its durable key **must** come from
    ``_concept_edge_target_path`` rather than a bare ``normalize_path`` — that is
    the function folding the bare ``work_id``, the rendered
    ``catalog/sources/<work_id>``, the ``./`` form and the ``/source.md`` form of
    one catalog work onto one ``target_path``. Admitted as distinct PK triples
    those spellings still resolve to one ``target_concept_id``, so they mint one
    deterministic ``edge_id`` twice and violate the UNIQUE
    ``idx_concept_edges_edge_id`` — inside ``replace_concept_edges``' single
    transaction, which rolls the whole mirror pass back and takes out `memoria
    index` vault-wide instead of the one bad row.
    """
    from memoria_vault.runtime.trusted_writer import validate_operation_context

    validate_operation_context(vault, context)
    relation = _concept_edge_relation(str(relation_type))
    with connect(vault) as conn:
        catalog_ids = {
            str(row["work_id"]) for row in conn.execute("SELECT work_id FROM catalog_sources")
        }
        source_concept = resolve_concept_id(conn, str(source))
        target_path = _concept_edge_target_path(str(target), catalog_ids)
        target_id = _lookup_concept_id(conn, target_path)
        if not source_concept or not target_path or source_concept == (target_id or target_path):
            raise ValueError("concept edge requires two distinct endpoints")
        stored = conn.execute(
            """
            SELECT edge_id, target_concept_id, attributes_json FROM concept_edges
            WHERE source_concept_id = ? AND relation_type = ? AND target_path = ?
            """,
            (source_concept, relation, target_path),
        ).fetchone()
        if stored is not None and target_id is None:
            # A settled row whose spelling stopped resolving — its target moved out
            # of band, so `concepts.path` left this `target_path` behind — keeps the
            # identity it already holds, the same call the mirror pass's COALESCE
            # makes. Re-deriving NULL here would un-resolve a live edge and blank an
            # edge_id every caller was promised is stable.
            target_id = stored["target_concept_id"]
        merged = {
            **(json.loads(stored["attributes_json"] or "{}") if stored is not None else {}),
            **(attributes or {}),
        }
        edge_id = concept_edge_id(source_concept, relation, str(target_id)) if target_id else ""
        conn.execute(
            """
            INSERT INTO concept_edges(
                edge_id,
                source_concept_id,
                relation_type,
                target_concept_id,
                target_path,
                attributes_json,
                check_status,
                source_path,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 'checked', '', ?)
            ON CONFLICT(source_concept_id, relation_type, target_path) DO UPDATE SET
                edge_id = excluded.edge_id,
                target_concept_id = excluded.target_concept_id,
                attributes_json = excluded.attributes_json,
                updated_at = excluded.updated_at
            """,
            (
                edge_id,
                source_concept,
                relation,
                target_id,
                target_path,
                json.dumps(merged, sort_keys=True),
                now_iso(),
            ),
        )
    return {"edge_id": edge_id, "created": stored is None, "attributes": merged}


def delete_concept_edge(
    vault: Path, *, source: str, relation_type: str, target: str
) -> dict[str, int]:
    """Retract one PI-confirmed concept edge; row absence is the entire record.

    A ``tension`` row carries no status column and no frontmatter mirror
    (existence IS confirmation), so deleting the row is the whole retraction and
    no reindex regenerates it. Idempotent by construction: a triple that matches
    nothing reports ``{"deleted": 0}``.

    Both endpoints are keyed by the exact functions ``insert_concept_edge``
    writes them with — ``resolve_concept_id`` for the source, and
    ``_concept_edge_target_path`` (never a bare ``normalize_path``) for the
    durable ``target_path``. This deletes by the triple that function inserts by,
    so it inherits the catalog fold ``insert_concept_edge``'s docstring makes
    binding: a delete keyed one spelling narrower resolves to a triple no row
    holds, and silently leaves the row it was asked to retract.

    Authority stays at the operation seams, as it does for the far more
    destructive ``replace_concept_edges``: this takes no ``OperationContext``.
    """
    relation = _concept_edge_relation(str(relation_type))
    with connect(vault) as conn:
        catalog_ids = {
            str(row["work_id"]) for row in conn.execute("SELECT work_id FROM catalog_sources")
        }
        deleted = conn.execute(
            """
            DELETE FROM concept_edges
            WHERE source_concept_id = ? AND relation_type = ? AND target_path = ?
            """,
            (
                resolve_concept_id(conn, str(source)),
                relation,
                _concept_edge_target_path(str(target), catalog_ids),
            ),
        ).rowcount
    return {"deleted": int(deleted)}


def concept_edges(vault: Path, *, checked_only: bool = True) -> list[dict[str, Any]]:
    if not db_path(vault).is_file():
        return []
    with connect(vault) as conn:
        if checked_only:
            rows = conn.execute(
                """
                SELECT edge_id, source_concept_id, relation_type, target_concept_id,
                       target_path, attributes_json, check_status, source_path
                FROM concept_edges
                WHERE check_status = 'checked'
                ORDER BY source_concept_id, relation_type, target_path
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT edge_id, source_concept_id, relation_type, target_concept_id,
                       target_path, attributes_json, check_status, source_path
                FROM concept_edges
                ORDER BY source_concept_id, relation_type, target_path
                """
            ).fetchall()
    return [dict(row) for row in rows]


def upsert_code_artifact(
    vault: Path,
    *,
    artifact_id: str,
    project_path: str,
    record_path: str,
    source_dir: str,
    output_dir: str,
    purpose: str,
    approved_command: Iterable[str],
    declared_inputs: Iterable[str] = (),
    declared_outputs: Iterable[str] = (),
    dependency_notes: str = "",
    status: str = "draft",
) -> dict[str, Any]:
    now = now_iso()
    artifact = safe_filename(artifact_id).strip("._-")
    if not artifact:
        raise ValueError("artifact_id is required")
    with connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO code_artifacts(
                artifact_id,
                project_path,
                record_path,
                source_dir,
                output_dir,
                purpose,
                approved_command_json,
                declared_inputs_json,
                declared_outputs_json,
                dependency_notes,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(artifact_id) DO UPDATE SET
                project_path = excluded.project_path,
                record_path = excluded.record_path,
                source_dir = excluded.source_dir,
                output_dir = excluded.output_dir,
                purpose = excluded.purpose,
                approved_command_json = excluded.approved_command_json,
                declared_inputs_json = excluded.declared_inputs_json,
                declared_outputs_json = excluded.declared_outputs_json,
                dependency_notes = excluded.dependency_notes,
                status = excluded.status,
                updated_at = excluded.updated_at
            """,
            (
                artifact,
                normalize_path(project_path),
                normalize_path(record_path),
                normalize_path(source_dir),
                normalize_path(output_dir),
                _code_purpose(purpose),
                _json([str(part) for part in approved_command]),
                _json([normalize_path(path) for path in declared_inputs]),
                _json([normalize_path(path) for path in declared_outputs]),
                dependency_notes,
                _code_artifact_status(status),
                now,
                now,
            ),
        )
    artifact_row = code_artifact(vault, artifact)
    if artifact_row is None:
        raise RuntimeError(f"code artifact was not stored: {artifact}")
    return artifact_row


def code_artifact(vault: Path, artifact_id: str) -> dict[str, Any] | None:
    if not db_path(vault).is_file():
        return None
    artifact = safe_filename(artifact_id).strip("._-")
    with connect(vault) as conn:
        row = conn.execute(
            """
            SELECT *
            FROM code_artifacts
            WHERE artifact_id = ?
            """,
            (artifact,),
        ).fetchone()
    return None if row is None else _code_artifact_row(row)


def record_code_run(
    vault: Path,
    *,
    run_id: str,
    artifact_id: str,
    command: Iterable[str],
    cwd: str,
    sanitized_env: Iterable[str] = (),
    input_hashes: dict[str, str] | None = None,
    output_hashes: dict[str, str] | None = None,
    stdout_sha256: str = "",
    stderr_sha256: str = "",
    stdout_path: str = "",
    stderr_path: str = "",
    exit_status: int | None = None,
    timeout_result: str = "",
    sandbox_backend: str = "",
    sandbox_profile_hash: str = "",
    run_status: str = "pending",
    started_at: str | None = None,
    ended_at: str | None = None,
) -> dict[str, Any]:
    run = safe_filename(run_id).strip("._-")
    if not run:
        raise ValueError("run_id is required")
    with connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO code_runs(
                run_id,
                artifact_id,
                command_json,
                cwd,
                sanitized_env_json,
                input_hashes_json,
                output_hashes_json,
                stdout_sha256,
                stderr_sha256,
                stdout_path,
                stderr_path,
                exit_status,
                timeout_result,
                sandbox_backend,
                sandbox_profile_hash,
                run_status,
                started_at,
                ended_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                command_json = excluded.command_json,
                cwd = excluded.cwd,
                sanitized_env_json = excluded.sanitized_env_json,
                input_hashes_json = excluded.input_hashes_json,
                output_hashes_json = excluded.output_hashes_json,
                stdout_sha256 = excluded.stdout_sha256,
                stderr_sha256 = excluded.stderr_sha256,
                stdout_path = excluded.stdout_path,
                stderr_path = excluded.stderr_path,
                exit_status = excluded.exit_status,
                timeout_result = excluded.timeout_result,
                sandbox_backend = excluded.sandbox_backend,
                sandbox_profile_hash = excluded.sandbox_profile_hash,
                run_status = excluded.run_status,
                ended_at = excluded.ended_at
            """,
            (
                run,
                safe_filename(artifact_id).strip("._-"),
                _json([str(part) for part in command]),
                normalize_path(cwd),
                _json([str(name) for name in sanitized_env]),
                _json(input_hashes or {}),
                _json(output_hashes or {}),
                stdout_sha256,
                stderr_sha256,
                normalize_path(stdout_path) if stdout_path else "",
                normalize_path(stderr_path) if stderr_path else "",
                exit_status,
                timeout_result,
                sandbox_backend,
                sandbox_profile_hash,
                _code_run_status(run_status),
                started_at or now_iso(),
                ended_at,
            ),
        )
    run_row = code_run(vault, run)
    if run_row is None:
        raise RuntimeError(f"code run was not stored: {run}")
    return run_row


def code_run(vault: Path, run_id: str) -> dict[str, Any] | None:
    if not db_path(vault).is_file():
        return None
    run = safe_filename(run_id).strip("._-")
    with connect(vault) as conn:
        row = conn.execute(
            """
            SELECT *
            FROM code_runs
            WHERE run_id = ?
            """,
            (run,),
        ).fetchone()
    return None if row is None else _code_run_row(row)


def replace_evidence_sets(vault: Path, rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    with connect(vault) as conn:
        return replace_evidence_sets_conn(conn, rows)


def replace_evidence_sets_conn(
    conn: sqlite3.Connection, rows: Iterable[dict[str, Any]]
) -> dict[str, Any]:
    """Replace active evidence sets using an existing transaction."""
    rows = list(rows)
    minted: list[dict[str, Any]] = []
    for row in rows:
        if not bool(row.get("bind", True)):
            continue
        cursor = conn.execute(
            """
            INSERT INTO evidence_bindings(id, block_text_sha256)
            VALUES (?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (str(row["id"]), row.get("block_text_sha256")),
        )
        if cursor.rowcount:
            minted.append(
                {
                    "evidence_id": str(row["id"]),
                    "block_ref": normalize_path(str(row["block_ref"])),
                    "block_text_sha256": row.get("block_text_sha256"),
                }
            )
    existing_bindings = {
        row["id"]: row["block_text_sha256"]
        for row in conn.execute("SELECT id, block_text_sha256 FROM evidence_bindings")
    }
    deleted = conn.execute("DELETE FROM evidence_sets").rowcount
    for row in rows:
        evidence_id = str(row["id"])
        items = [str(item) for item in row.get("items", [])]
        bind = bool(row.get("bind", True))
        block_text_sha256 = (
            existing_bindings[evidence_id]
            if bind and evidence_id in existing_bindings
            else row.get("block_text_sha256")
            if bind
            else None
        )
        conn.execute(
            """
            INSERT INTO evidence_sets(
                id,
                block_ref,
                items_json,
                type,
                completeness_status,
                review_required,
                run_id,
                block_text_sha256
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence_id,
                normalize_path(str(row["block_ref"])),
                _json(items),
                str(row["type"]),
                str(row["completeness_status"]),
                1 if bool(row.get("review_required")) else 0,
                str(row.get("run_id") or ""),
                block_text_sha256,
            ),
        )
    result: dict[str, Any] = {"deleted": int(deleted), "inserted": len(rows)}
    if minted:
        result["minted"] = minted
    return result


def evidence_sets(vault: Path) -> list[dict[str, Any]]:
    if not db_path(vault).is_file():
        return []
    with connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT id, block_ref, items_json, type, completeness_status, review_required,
                   run_id, block_text_sha256
            FROM evidence_sets
            ORDER BY block_ref, id
            """
        ).fetchall()
    return [_evidence_set_row(row) for row in rows]


def rebuild_evidence_sets_from_markers(vault: Path, *, run_id: str = "") -> dict[str, Any]:
    vault = Path(vault)
    marker_rows, duplicate_ids = evidence_marker_rows(vault, run_id=run_id)
    result = replace_evidence_sets(vault, marker_rows)
    if duplicate_ids:
        result["duplicate_ids"] = duplicate_ids
    return result


def rebuild_evidence_bindings_from_journal(vault: Path) -> dict[str, int]:
    """Replay verified first-time evidence mints into the immutable bindings ledger."""
    vault = Path(vault)
    with workspace_lock(vault):
        # Recovery cannot assume the ledger schema survived — this path exists
        # precisely for damaged databases (e.g. a dropped evidence_bindings
        # table). Re-run the idempotent DDL before touching it.
        ensure_schema(vault)
        verification = verify_journal_chain(vault)
        if not verification["ok"]:
            raise ValueError(
                "cannot rebuild evidence bindings: journal chain is invalid: "
                f"{verification['error']}"
            )
        mints = [
            _evidence_mint_event_binding(event)
            for event in read_event_log(vault, event_types=("evidence-minted",))
        ]
        replayed = 0
        inserted = 0
        with connect(vault) as conn:
            conn.execute("BEGIN IMMEDIATE")
            for evidence_id, block_text_sha256 in mints:
                replayed += 1
                cursor = conn.execute(
                    """
                    INSERT INTO evidence_bindings(id, block_text_sha256)
                    VALUES (?, ?)
                    ON CONFLICT(id) DO NOTHING
                    """,
                    (evidence_id, block_text_sha256),
                )
                inserted += cursor.rowcount
    return {"replayed": replayed, "inserted": inserted}


def _evidence_mint_event_binding(event: Mapping[str, Any]) -> tuple[str, str | None]:
    """Validate the canonical payload used to restore one immutable binding."""
    evidence_id = event.get("evidence_id")
    block_ref = event.get("block_ref")
    block_text_sha256 = event.get("block_text_sha256")
    actor = event.get("actor")
    valid_provenance = (
        isinstance(actor, str)
        and actor in ACTORS
        and isinstance(event.get("request_provenance"), dict)
        and all(
            isinstance(event.get(field), str) and event[field].strip()
            for field in ("run_id", "request_id", "operation", "machine", "timestamp")
        )
    )
    if (
        event.get("event") != "evidence-minted"
        or not isinstance(evidence_id, str)
        or re.fullmatch(r"ev-[0-9a-f]{8}", evidence_id) is None
        or not isinstance(block_ref, str)
        or not valid_provenance
        or (
            block_text_sha256 is not None
            and (
                not isinstance(block_text_sha256, str)
                or re.fullmatch(r"sha256:[0-9a-f]{64}", block_text_sha256) is None
            )
        )
    ):
        raise ValueError("invalid evidence-minted journal event")
    try:
        rel, separator, _anchor = block_ref.partition("#^")
        canonical_block_ref = _evidence_block_ref(rel, evidence_id)
    except ValueError as exc:
        raise ValueError("invalid evidence-minted journal event") from exc
    if not separator or not rel.strip() or block_ref != canonical_block_ref:
        raise ValueError("invalid evidence-minted journal event")
    return evidence_id, block_text_sha256


def work_aspects(vault: Path, source_ref: str) -> list[dict[str, Any]]:
    if not db_path(vault).is_file():
        return []
    work_id = _work_id(source_ref)
    with connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT work_id, aspect_type, aspect_text, anchor_text, check_status,
                   source_provider, updated_at
            FROM work_aspects
            WHERE work_id = ?
            ORDER BY aspect_type
            """,
            (work_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def compact_citation(vault: Path, source_ref: str) -> dict[str, Any]:
    if not db_path(vault).is_file():
        return {}
    work_id = _work_id(source_ref)
    with connect(vault) as conn:
        row = conn.execute(
            "SELECT * FROM catalog_sources WHERE work_id = ?",
            (work_id,),
        ).fetchone()
    if row is None:
        return {}
    source = _source_row(row)
    csl = source.get("csl_json")
    if not isinstance(csl, dict):
        csl = {}
    identifiers = source.get("identifiers")
    if not isinstance(identifiers, dict):
        identifiers = {}
    citation: dict[str, Any] = {
        "work_id": f"catalog/sources/{work_id}",
        "title": source["title"],
        "authors": _csl_authors(csl),
        "issued": _csl_issued(csl),
    }
    if doi := str(identifiers.get("doi") or csl.get("DOI") or "").strip():
        citation["doi"] = doi
    elif url := str(source.get("resource") or csl.get("URL") or "").strip():
        citation["url"] = url
    else:
        citation["citekey"] = str(source.get("citekey") or work_id)
    return citation


def _init(conn: sqlite3.Connection) -> None:
    current = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if current == SCHEMA_VERSION:
        # 1733: re-running the 445-line schema.sql here cost ~19.6ms on EVERY
        # connect (heavy tests open 300-700 connections; the CLI pays it per
        # command). The script is pure IF-NOT-EXISTS DDL, so on a current DB
        # it was always a semantic no-op. A version mismatch still hard-fails
        # below, and a dev editing schema.sql must bump SCHEMA_VERSION —
        # tests/test_schema_version.py hash-pins the DDL to it. Repair paths
        # that must heal a current DB call ensure_schema() instead.
        return
    if current != 0:
        raise RuntimeError(f"unsupported Memoria DB schema version: {current}")
    conn.executescript(_schema_sql())
    applied = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if applied != SCHEMA_VERSION:
        raise RuntimeError(f"Memoria DB schema initialization failed: {applied}")


def _set_request_status(vault: Path, request_id: str, status: str, job: dict[str, Any]) -> None:
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
    csl_json = json.loads(row["csl_json"] or "{}")
    return {
        "work_id": row["work_id"],
        "concept_path": row["concept_path"],
        "doi": row["doi"],
        "title": row["title"],
        "description": row["description"],
        "resource": row["resource"],
        "item_type": row["item_type"],
        "identifiers": json.loads(row["identifiers_json"] or "{}"),
        "citekey": row["citekey"],
        "csl_json": csl_json,
        "provider_coverage": row["provider_coverage"],
        "text_status": row["text_status"],
        "check_status": row["check_status"],
        "normalized_text_sha256": row["content_hash"],
        "raw_text_sha256": row["raw_hash"],
        "content_path": row["content_path"],
        "raw_path": row["raw_path"],
    }


def _evidence_set_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "block_ref": row["block_ref"],
        "items": json.loads(row["items_json"] or "[]"),
        "type": row["type"],
        "completeness_status": row["completeness_status"],
        "review_required": bool(row["review_required"]),
        "run_id": row["run_id"],
        "block_text_sha256": row["block_text_sha256"],
    }


def _code_artifact_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "artifact_id": row["artifact_id"],
        "project_path": row["project_path"],
        "record_path": row["record_path"],
        "source_dir": row["source_dir"],
        "output_dir": row["output_dir"],
        "purpose": row["purpose"],
        "approved_command": json.loads(row["approved_command_json"] or "[]"),
        "declared_inputs": json.loads(row["declared_inputs_json"] or "[]"),
        "declared_outputs": json.loads(row["declared_outputs_json"] or "[]"),
        "dependency_notes": row["dependency_notes"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _code_run_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "run_id": row["run_id"],
        "artifact_id": row["artifact_id"],
        "command": json.loads(row["command_json"] or "[]"),
        "cwd": row["cwd"],
        "sanitized_env": json.loads(row["sanitized_env_json"] or "[]"),
        "input_hashes": json.loads(row["input_hashes_json"] or "{}"),
        "output_hashes": json.loads(row["output_hashes_json"] or "{}"),
        "stdout_sha256": row["stdout_sha256"],
        "stderr_sha256": row["stderr_sha256"],
        "stdout_path": row["stdout_path"],
        "stderr_path": row["stderr_path"],
        "exit_status": row["exit_status"],
        "timeout_result": row["timeout_result"],
        "sandbox_backend": row["sandbox_backend"],
        "sandbox_profile_hash": row["sandbox_profile_hash"],
        "run_status": row["run_status"],
        "started_at": row["started_at"],
        "ended_at": row["ended_at"],
    }


def evidence_marker_rows(
    vault: Path,
    *,
    run_id: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    occurrences_by_id: dict[str, list[tuple[str, EvidenceMarker, bool]]] = {}
    bound_ids = _evidence_binding_ids(vault)
    for path in sorted(vault.rglob("*.md")):
        if _skip_evidence_scan_path(path.relative_to(vault)):
            continue
        rel = normalize_path(path.relative_to(vault).as_posix())
        text = path.read_text(encoding="utf-8")
        for marker, is_direct in evidence_marker_occurrences_from_markdown(text):
            occurrences_by_id.setdefault(marker.evidence_id, []).append((rel, marker, is_direct))

    prior_block_refs = _evidence_set_block_refs(vault)
    selected: list[tuple[str, EvidenceMarker, bool, str | None]] = []
    duplicate_ids: list[str] = []
    for evidence_id in sorted(occurrences_by_id):
        occurrences = occurrences_by_id[evidence_id]
        direct = [occurrence for occurrence in occurrences if occurrence[2]]
        if not direct and evidence_id not in bound_ids:
            continue
        rel, marker, _is_direct = direct[0] if direct else occurrences[0]
        bind = bool(direct) and len(occurrences) == 1
        if len(occurrences) > 1:
            duplicate_ids.append(evidence_id)
        prior_block_ref = None if direct else prior_block_refs.get(evidence_id)
        selected.append((rel, marker, bind, prior_block_ref))

    items_by_id = {
        marker.evidence_id: tuple(marker.items) for _rel, marker, _bind, _prior in selected
    }
    source_spans = _source_span_pages(vault)
    completeness = _evidence_set_completeness(vault, items_by_id, source_spans=source_spans)
    rows = []
    for rel, marker, bind, prior_block_ref in selected:
        row = _derived_evidence_row(
            vault,
            rel,
            marker,
            completeness_value=completeness[marker.evidence_id],
            run_id=run_id,
        )
        if prior_block_ref is not None:
            row["block_ref"] = prior_block_ref
            row["block_text_sha256"] = _block_text_sha256(vault, prior_block_ref)
        row["bind"] = bind
        rows.append(row)
    return rows, duplicate_ids


def _skip_evidence_scan_path(rel: Path) -> bool:
    return any(part in {".git", ".memoria"} for part in rel.parts)


def _evidence_binding_ids(vault: Path) -> set[str]:
    if not db_path(vault).is_file():
        return set()
    with connect(vault) as conn:
        return {str(row["id"]) for row in conn.execute("SELECT id FROM evidence_bindings")}


def _evidence_set_block_refs(vault: Path) -> dict[str, str]:
    if not db_path(vault).is_file():
        return {}
    with connect(vault) as conn:
        return {
            str(row["id"]): str(row["block_ref"])
            for row in conn.execute("SELECT id, block_ref FROM evidence_sets")
        }


def _derived_evidence_row(
    vault: Path,
    rel: str,
    marker: EvidenceMarker,
    *,
    completeness_value: str,
    run_id: str,
) -> dict[str, Any]:
    items = list(marker.items)
    evidence_type = derive_evidence_type(items)
    block_ref = _evidence_block_ref(rel, marker.evidence_id)
    return {
        "id": marker.evidence_id,
        "block_ref": block_ref,
        "items": items,
        "type": evidence_type,
        "completeness_status": completeness_value,
        "review_required": evidence_type in {"implicit", "multi-hop"},
        "run_id": run_id,
        "block_text_sha256": _block_text_sha256(vault, block_ref),
    }


def derive_evidence_type(items: list[str]) -> str:
    """Derive the grounds type from a record's own items (spec §4, rules R1-R4)."""
    if not items:
        return "implicit"
    kinds = [evidence_ref_kind(item) for item in items]
    span_works = {
        parse_source_span_ref(item).work_id
        for item, kind in zip(items, kinds, strict=True)
        if kind == "source-span"
    }
    has_code = "code-grounds" in kinds
    if "evidence-set" in kinds or len(span_works) >= 2 or (has_code and span_works):
        return "multi-hop"
    if has_code:
        return "computed"
    return "single-span" if len(items) == 1 else "multi-span"


def _evidence_set_completeness(
    vault: Path,
    items_by_id: dict[str, tuple[str, ...]],
    *,
    source_spans: dict[str, set[str]],
) -> dict[str, str]:
    """Resolve completeness bottom-up over nested sets; cycles fail closed."""
    completeness: dict[str, str] = {}

    def visit(evidence_id: str, visiting: frozenset[str]) -> str:
        known = completeness.get(evidence_id)
        if known is not None:
            return known
        if evidence_id in visiting:
            return "evidence-incomplete"

        items = items_by_id.get(evidence_id) or ()
        complete = bool(items)
        visiting = visiting | {evidence_id}
        for item in items:
            kind = evidence_ref_kind(item)
            if kind == "code-grounds":
                resolved = _code_grounds_resolves(vault, item)
            elif kind == "evidence-set":
                resolved = item in items_by_id and visit(item, visiting) == "complete"
            else:
                source = parse_source_span_ref(item)
                resolved = source.page in source_spans.get(source.work_id, set())
            if not resolved:
                complete = False
                break

        completeness[evidence_id] = "complete" if complete else "evidence-incomplete"
        return completeness[evidence_id]

    for evidence_id in sorted(items_by_id):
        visit(evidence_id, frozenset())
    return completeness


def evidence_item_closure(
    rows_by_id: Mapping[str, Mapping[str, Any]], evidence_id: str
) -> list[tuple[str, tuple[str, ...]]]:
    """Return non-set evidence leaves with their nested evidence-set paths."""
    leaves: list[tuple[str, tuple[str, ...]]] = []

    def visit(current_id: str, path: tuple[str, ...], visiting: frozenset[str]) -> None:
        row = rows_by_id.get(current_id)
        if row is None:
            return
        for item in row.get("items", ()):
            if evidence_ref_kind(item) != "evidence-set":
                leaves.append((item, path))
                continue
            if item in visiting or item not in rows_by_id:
                continue
            visit(item, (*path, item), visiting | {item})

    visit(evidence_id, (), frozenset({evidence_id}))
    return leaves


def _code_grounds_resolves(vault: Path, item: str) -> bool:
    from memoria_vault.runtime.code.runs import code_grounds_complete

    grounds = parse_code_grounds_ref(item)
    return code_grounds_complete(
        vault,
        run_id=grounds.run_id,
        artifact_id=grounds.artifact_id,
        output_sha256=grounds.output_sha256,
    )


def _source_span_pages(vault: Path) -> dict[str, set[str]]:
    spans: dict[str, set[str]] = {}
    for source in catalog_sources(vault, checked_only=False):
        work_id = str(source["work_id"])
        content_path = Path(vault) / normalize_path(str(source.get("content_path") or ""))
        if not content_path.is_file():
            spans[work_id] = set()
            continue
        text = content_path.read_text(encoding="utf-8")
        spans[work_id] = set(re.findall(r"\^p\d{4,}", text))
    return {work_id: {page.removeprefix("^") for page in pages} for work_id, pages in spans.items()}


def _evidence_block_ref(rel: str, evidence_id: str) -> str:
    return f"{normalize_path(rel)}#^blk-{evidence_id.removeprefix('ev-')}"


def _block_text_sha256(vault: Path, block_ref: str) -> str | None:
    rel, separator, anchor = str(block_ref).partition("#^")
    if not separator or not rel or not anchor:
        return None
    try:
        path = Path(vault) / normalize_path(rel)
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError):
        return None
    return block_text_sha256_from_text(text, block_ref)


def block_canonical_text_from_text(text: str, block_ref: str) -> str | None:
    _rel, separator, anchor = str(block_ref).partition("#^")
    if not separator or not anchor:
        return None
    evidence_id = _evidence_id_for_block_anchor(anchor)
    if evidence_id is None:
        return None

    anchor_token = f"^{anchor}"
    anchor_pattern = rf"(?<!\S){re.escape(anchor_token)}(?=\s|$)"
    visible = _markdown_control_text(text)
    original_blocks = re.split(r"\n[ \t]*\n+", text)
    visible_blocks = re.split(r"\n[ \t]*\n+", visible)
    if len(original_blocks) != len(visible_blocks):
        return None

    blocks = [
        (original, control)
        for original, control in zip(original_blocks, visible_blocks, strict=True)
        if re.search(anchor_pattern, control)
    ]
    if len(blocks) != 1:
        return None

    block, control = blocks[0]
    matching_markers = [
        (match, marker)
        for match, marker in _direct_evidence_marker_matches(control)
        if marker.evidence_id == evidence_id
    ]
    if len(matching_markers) != 1:
        return None
    marker_match, _marker = matching_markers[0]
    anchor_matches = [
        match
        for match in re.finditer(anchor_pattern, control)
        if "\n" not in control[match.end() : marker_match.start("marker")]
        and not control[match.end() : marker_match.start("marker")].strip()
    ]
    if len(anchor_matches) != 1:
        return None

    canonical = block
    for start, end in sorted(
        (anchor_matches[0].span(), marker_match.span("marker")),
        reverse=True,
    ):
        canonical = canonical[:start] + canonical[end:]
    return canonical.strip()


def block_text_sha256_from_text(text: str, block_ref: str) -> str | None:
    canonical = block_canonical_text_from_text(text, block_ref)
    if canonical is None:
        return None
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _evidence_id_for_block_anchor(anchor: str) -> str | None:
    if not anchor.startswith("blk-"):
        return None
    evidence_id = f"ev-{anchor.removeprefix('blk-')}"
    return evidence_id if re.fullmatch(r"ev-[0-9a-f]{8}", evidence_id) else None


def resolve_concept_id(conn: sqlite3.Connection, ref: str) -> str:
    """Return the canonical ``concepts`` key for a reference, minting nothing.

    v16 identity: a catalog work keys by its bare ``work_id`` while its
    ``concepts.path`` renders as ``catalog/sources/<work_id>``, so the bare,
    rendered, ``./``-prefixed, and ``/source.md`` forms all resolve to one
    parent. An unknown reference resolves to its normalized self.
    """
    rel = normalize_path(ref)
    return _lookup_concept_id(conn, rel) or rel


def _concept_key_for_file(vault: Path, path: str, payload_text: str = "") -> str:
    """Return the identity a file Concept is created with on first observation.

    A valid frontmatter ULID is the identity; any other ``id`` (a catalog
    ``work_id``, a blank, a hand-written slug) leaves the Concept on its B.1 path
    key. ``payload_text`` is the staged content for a file that is not on disk yet.
    """
    text = payload_text or safe_read(Path(vault) / path)
    raw_id = str(parse_frontmatter(text).get("id") or "")
    return raw_id if is_ulid(raw_id) else normalize_path(path)


def ensure_concept_parent_conn(
    conn: sqlite3.Connection,
    ref: str,
    *,
    concept_type: str,
    store: str,
    path: str,
) -> str:
    """Create or refresh the FK parent row for one Concept and return its id.

    Never silently accepts an identity collision (contract 10), while still
    letting one identity update its own attributes. v16 decouples the id from the
    path, so *same resolved id, requested path owned by nobody else* is a rename
    (or an in-place ``concept_type`` change), not a collision, and it updates.
    Two refusals remain, each a descriptive ``RuntimeError`` naming both shapes:
    a reference resolving onto a row of a different ``store`` — the line between
    a db catalog work and a mirrored file Concept, which is the hijack contract 10
    forbids — and two distinct ids claiming one path, caught below by
    ``idx_concepts_path`` so the message names the resident owner.
    """
    concept_id = _lookup_concept_id(conn, ref) or _canonical_concept_ref(ref)
    if not concept_id:
        raise ValueError("concept reference is required")
    wanted = (_registry_concept_type(concept_type), store, normalize_path(path))
    resident = conn.execute(
        "SELECT concept_type, store, path FROM concepts WHERE concept_id = ?",
        (concept_id,),
    ).fetchone()
    if resident is not None and str(resident["store"]) != wanted[1]:
        found = (str(resident["concept_type"]), str(resident["store"]), str(resident["path"]))
        raise _concept_shape_collision(ref, concept_id, found, concept_id, wanted)
    if resident is None:
        _adopt_path_key_identity_conn(conn, concept_id, wanted)
    try:
        conn.execute(
            """
            INSERT INTO concepts(concept_id, concept_type, store, path)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(concept_id) DO UPDATE SET
                concept_type = excluded.concept_type,
                store = excluded.store,
                path = excluded.path
            """,
            (concept_id, *wanted),
        )
    except sqlite3.IntegrityError as exc:
        # idx_concepts_path: a different identity already renders at this path.
        if "concepts.path" not in str(exc):
            raise
        owner = conn.execute(
            "SELECT concept_id, concept_type, store, path FROM concepts WHERE path = ?",
            (wanted[2],),
        ).fetchone()
        found = (
            (str(owner["concept_type"]), str(owner["store"]), str(owner["path"]))
            if owner is not None
            else wanted
        )
        owner_id = str(owner["concept_id"]) if owner is not None else "<unknown>"
        raise _concept_shape_collision(ref, owner_id, found, concept_id, wanted) from exc
    return concept_id


def _adopt_path_key_identity_conn(
    conn: sqlite3.Connection,
    concept_id: str,
    wanted: tuple[str, str, str],
) -> None:
    """Let the still-provisional row at one path take the ULID its file now carries.

    v16 mirrors an id-less file — hand-written, externally dropped — under its own
    path as a provisional key, so the moment that file authors a ULID the same path
    presents a new identity. That is this Concept's first real identity, not a
    second Concept claiming the path: the row takes it in place and the v16 foreign
    keys carry its verdict, flags and edges along. Every genuine collision is left
    to the caller's ``idx_concepts_path`` refusal — a resident that is already
    id-keyed, a non-ULID claim, a different ``store``, or an incoming identity that
    already lives at another path (which would merge two Concepts).

    The re-key itself is ``_rekey_path_keyed_concept_conn``, never a second copy of
    its statement: adoption moves the same identity a rename moves, so it owes the
    same tables. Only the path is unchanged, and the path is exactly what the
    identity-space enumeration does not touch.
    """
    _concept_type, store, path = wanted
    if not path or not is_ulid(concept_id):
        return
    owner = conn.execute(
        "SELECT concept_id, store FROM concepts WHERE path = ?", (path,)
    ).fetchone()
    if owner is None or str(owner["concept_id"]) != path or str(owner["store"]) != store:
        return
    if conn.execute("SELECT 1 FROM concepts WHERE concept_id = ?", (concept_id,)).fetchone():
        return
    _rekey_path_keyed_concept_conn(conn, path, concept_id)


def _concept_shape_collision(
    ref: str,
    found_id: str,
    found: tuple[str, str, str],
    wanted_id: str,
    wanted: tuple[str, str, str],
) -> RuntimeError:
    """Return the descriptive refusal for a v16 Concept identity collision."""

    def shape(concept_id: str, values: tuple[str, str, str]) -> str:
        return (
            f"(concept_id={concept_id!r}, concept_type={values[0]!r},"
            f" store={values[1]!r}, path={values[2]!r})"
        )

    return RuntimeError(
        f"concept identity collision for {ref!r}: {shape(found_id, found)}"
        f" already exists; refusing to rewrite it as {shape(wanted_id, wanted)}"
    )


def _concept_missing_parent(ref: str, concept_id: str, subject: str) -> RuntimeError:
    """Return the descriptive refusal for an FK-backed write with no Concept parent."""
    return RuntimeError(
        f"unknown Concept for {subject}: {ref!r} resolves to concept_id={concept_id!r},"
        " which has no concepts row; mirror the Concept before writing to it"
    )


def _lookup_concept_id(conn: sqlite3.Connection, ref: str) -> str | None:
    """Return the existing concepts key for a reference, or None."""
    rel = normalize_path(ref)
    if not rel:
        return None
    candidates = [rel]
    rendered = _canonical_concept_ref(rel)
    if rendered and rendered != rel:
        candidates.append(rendered)
    for candidate in candidates:
        row = conn.execute(
            "SELECT concept_id FROM concepts WHERE concept_id = ? OR path = ?",
            (candidate, candidate),
        ).fetchone()
        if row is not None:
            return str(row["concept_id"])
    return None


def _canonical_concept_ref(ref: str) -> str:
    """Return the identity a reference would mint: catalog renderings go bare."""
    rel = normalize_path(ref)
    if rel.startswith("catalog/sources/"):
        return rel.removeprefix("catalog/sources/").removesuffix("/source.md")
    return rel


def _concept_parent_shape(rel: str) -> tuple[str, str, str]:
    """Return the (concept_type, store, path) to mint for an unmirrored reference."""
    if rel.startswith("catalog/sources/"):
        return "work", "db", f"catalog/sources/{_canonical_concept_ref(rel)}"
    return _folder_concept_types().get(rel.split("/", 1)[0], "note"), "file", rel


def _registry_concept_type(value: str) -> str:
    """Map a document type onto its Concept-type registry member, failing closed.

    Deliberately a superset of the named Consumes seam
    ``schema.concept_type_for(document_type)``, which accepts document types only
    and re-reads every types/*.yaml per call. The v16 parent-ensure seam is on the
    hot path of every mirror rebuild and edge pass, and its callers pass registry
    members (``work``, ``note``) as often as document types (``fulltext``,
    ``code-artifact``), so this maps both domains over one cached table. For the
    document-type domain it returns exactly what ``concept_type_for`` returns —
    `tests/test_concept_types.py` pins that equivalence.
    """
    name = str(value).strip()
    mapped = _concept_type_map().get(name)
    if mapped is None:
        raise ValueError(f"unknown concept type: {value!r}")
    return mapped


def _concept_type_map() -> dict[str, str]:
    """Return {document or concept type: registry concept type} from the seed."""
    from memoria_vault.runtime.vocabulary import schema as schema_lib

    schemas_dir = Path(schema_lib.SCHEMAS_DIR)
    cached = _CONCEPT_TYPE_MAPS.get(schemas_dir)
    if cached is None:
        cached = {str(name): str(name) for name in schema_lib.load_concept_types(schemas_dir)}
        cached.update(
            {
                str(name): str(data["concept_type"])
                for name, data in schema_lib.load_types(schemas_dir).items()
            }
        )
        _CONCEPT_TYPE_MAPS[schemas_dir] = cached
    return cached


def _folder_concept_types() -> dict[str, str]:
    """Return {bundle folder: registry concept type} from the seeded folder homes."""
    from memoria_vault.runtime.vocabulary import schema as schema_lib

    schemas_dir = Path(schema_lib.SCHEMAS_DIR)
    cached = _FOLDER_CONCEPT_TYPES.get(schemas_dir)
    if cached is None:
        homes = schema_lib.load_folders(schemas_dir).get("homes") or {}
        cached = {
            str(folder): _registry_concept_type(str(document_type))
            for document_type, folder in homes.items()
        }
        _FOLDER_CONCEPT_TYPES[schemas_dir] = cached
    return cached


def _set_concept_verdict_conn(
    conn: sqlite3.Connection,
    concept_id: str,
    check_status: str,
) -> None:
    target = resolve_concept_id(conn, concept_id)
    conn.execute(
        """
        INSERT INTO concept_verdicts(concept_id, check_status)
        VALUES (?, ?)
        ON CONFLICT(concept_id) DO UPDATE SET
            check_status = excluded.check_status
        """,
        (target, _check_status(check_status)),
    )
    _cascade_passage_check_status_conn(conn, target, check_status)


def _cascade_passage_check_status_conn(
    conn: sqlite3.Connection,
    concept_id: str,
    check_status: str,
) -> None:
    status = _check_status(check_status)
    conn.execute(
        """
        UPDATE passages
        SET check_status = ?
        WHERE concept_id = ?
           OR work_id = ?
           OR path = (SELECT path FROM concepts WHERE concept_id = ?)
        """,
        (status, concept_id, concept_id, concept_id),
    )


def _enum(value: str, allowed: Container[str], message: str, *, lower: bool = True) -> str:
    """Return `value` stripped (and lowered) if `allowed` holds it, else raise `message`."""
    normalized = value.strip().lower() if lower else value.strip()
    if normalized not in allowed:
        raise ValueError(message)
    return normalized


def _check_status(check_status: str) -> str:
    return _enum(
        check_status, CHECK_STATUSES, f"invalid check_status: {check_status!r}", lower=False
    )


def _work_aspect_type(value: str) -> str:
    aspect_type = value.strip().lower().replace("-", "_")
    if aspect_type not in WORK_ASPECT_TYPES:
        raise ValueError(f"unknown work aspect type: {value}")
    return aspect_type


def _concept_edge_relation(value: str) -> str:
    return _enum(value, EDGE_RELATIONS, f"unknown concept edge relation: {value}")


def concept_edge_id(source_concept_id: str, relation_type: str, target_concept_id: str) -> str:
    """Return the deterministic id for a normalized concept-edge triple."""
    key = f"{source_concept_id}\0{relation_type}\0{target_concept_id}"
    return hashlib.sha256(key.encode()).hexdigest()[:24]


def _code_purpose(value: str) -> str:
    message = f"invalid code artifact purpose: {value!r}"
    return _enum(value, {"grounds", "deliverable", "both"}, message)


def _code_artifact_status(value: str) -> str:
    message = f"invalid code artifact status: {value!r}"
    return _enum(value, {"draft", "ready", "failed", "retired"}, message)


def _code_run_status(value: str) -> str:
    message = f"invalid code run status: {value!r}"
    return _enum(value, {"pending", "running", "succeeded", "failed", "unavailable"}, message)


def _passage_id(path: str, text_sha256: str) -> str:
    return hashlib.sha256(f"{path}\0{text_sha256}".encode()).hexdigest()[:24]


def _work_id(value: str) -> str:
    rel = normalize_path(value)
    rel = rel.removeprefix("catalog/sources/").removesuffix("/source.md")
    work_id = safe_filename(rel.strip("/")).strip("._-")
    if not work_id:
        raise ValueError("work_id is required")
    return work_id


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
    return hashlib.sha256(_json(payload).encode("utf-8")).hexdigest()
