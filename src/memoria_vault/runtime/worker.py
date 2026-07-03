"""Local worker for SQLite-backed operation requests."""

from __future__ import annotations

import base64
import contextlib
import json
import subprocess
import tempfile
import time
import uuid
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback is exercised only on Windows.
    fcntl = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - POSIX path is exercised in CI.
    msvcrt = None

from memoria_vault.runtime import state
from memoria_vault.runtime.jsonl import append_jsonl
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.time import now_iso
from memoria_vault.runtime.trusted_writer import (
    commit_writer_changes,
    materialize_unchecked,
    promote_checked,
    stage_concept,
)
from memoria_vault.runtime.vaultio import split_frontmatter

INTEGRITY_SWEEP_OPERATIONS = (
    "trace-integrity-scan",
    "check-source-metadata",
    "integrity-evidence-check",
    "integrity-quote-anchor-check",
    "integrity-claim-quote-check",
    "integrity-prompt-injection-check",
    "integrity-provenance-checkpoint",
    "integrity-citation-survival-check",
    "integrity-contradiction-check",
    "integrity-link-target-check",
)
OVERRIDE_LOG_REL = ".memoria/overrides.jsonl"
CREATE_CONCEPT_HOMES = {
    "note": "knowledge/notes",
    "hub": "knowledge/hubs",
    "project": "knowledge/projects",
}


@contextlib.contextmanager
def _workspace_lock(vault: Path):
    # ponytail: one workspace-wide worker lock; split only if throughput requires it.
    lock_path = Path(vault) / ".memoria/locks/worker.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock_file:
        if fcntl is not None:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            return
        if msvcrt is not None:
            lock_file.write(b"\0")
            lock_file.flush()
            lock_file.seek(0)
            while True:
                try:
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    time.sleep(0.05)
            try:
                yield
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            return
        yield


def _payload_doi(payload: dict[str, Any]) -> str:
    identifiers = payload.get("identifiers") if isinstance(payload.get("identifiers"), dict) else {}
    csl_json = payload.get("csl_json") if isinstance(payload.get("csl_json"), dict) else {}
    return str(identifiers.get("doi") or csl_json.get("DOI") or "").strip()


def enqueue_trusted_write(
    vault: Path,
    target_path: str,
    content: str,
    *,
    inputs: list[str | dict[str, Any]] | None = None,
    operation: str = "trusted-write",
    run_id: str | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Queue one machine Concept write request for the local worker."""
    vault = Path(vault)
    job_id = safe_filename(idempotency_key or uuid.uuid4().hex)
    if existing_job := state.request_job(vault, job_id):
        return existing_job

    job = {
        "job_id": job_id,
        "kind": "trusted_write",
        "status": "pending",
        "created_at": now_iso(),
        "target_path": target_path,
        "content": content,
        "inputs": list(inputs or []),
        "operation": operation,
        "run_id": run_id or job_id,
    }
    envelope = state.request_envelope(
        request_id=job_id,
        operation_id=operation,
        args={
            "target_path": target_path,
            "content": content,
            "inputs": list(inputs or []),
            "run_id": run_id or job_id,
        },
        idempotency_key=idempotency_key or job_id,
        input_refs=inputs or [],
        output_intents=[{"id": target_path, "kind": "trusted_write"}],
        primary_target=target_path,
        actor="operation",
        provenance={"surface": "worker"},
    )
    return state.save_request(vault, envelope, job)


def enqueue_operation(
    vault: Path,
    operation_id: str,
    *,
    payload: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
    input_refs: list[str | dict[str, Any]] | None = None,
    output_intents: list[str | dict[str, Any]] | None = None,
    primary_target: str = "",
    precondition_hashes: dict[str, Any] | None = None,
    causal_refs: list[str | dict[str, Any]] | None = None,
    actor: str = "pi",
    provenance: dict[str, Any] | None = None,
    schedule_id: str | None = None,
) -> dict[str, Any]:
    """Queue one operation request for the local worker."""
    vault = Path(vault)
    job_id = safe_filename(idempotency_key or f"{operation_id}-{uuid.uuid4().hex}")
    if existing_job := state.request_job(vault, job_id):
        return existing_job

    args = dict(payload or {})
    job = {
        "job_id": job_id,
        "kind": "operation",
        "status": "pending",
        "created_at": now_iso(),
        "operation_id": operation_id,
        "payload": args,
    }
    envelope = state.request_envelope(
        request_id=job_id,
        operation_id=operation_id,
        args=args,
        idempotency_key=idempotency_key or job_id,
        input_refs=input_refs or [],
        output_intents=output_intents or [],
        primary_target=primary_target,
        precondition_hashes=precondition_hashes,
        causal_refs=causal_refs or [],
        actor=actor,
        provenance=provenance or {"surface": "worker"},
        schedule_id=schedule_id,
    )
    return state.save_request(vault, envelope, job)


def run_next_job(vault: Path, *, machine: str | None = None) -> dict[str, Any] | None:
    """Claim and run the oldest pending worker request."""
    vault = Path(vault)
    with _workspace_lock(vault):
        sqlite_job = state.next_pending_job(vault)
        if sqlite_job is None:
            return None
        running = _claim_sqlite_job(vault, sqlite_job)
        return _run_claimed_job(vault, running, machine)


def run_request(vault: Path, request_id: str, *, machine: str | None = None) -> dict[str, Any]:
    """Claim and run one pending operation request."""
    vault = Path(vault)
    with _workspace_lock(vault):
        job = state.request_job(vault, request_id)
        if job is None:
            raise FileNotFoundError(f"request not found: {request_id}")
        if job.get("status") != "pending":
            raise ValueError(f"request {request_id} is not pending")
        running = _claim_sqlite_job(vault, job)
        return _run_claimed_job(vault, running, machine)


def _run_claimed_job(vault: Path, job: dict[str, Any], machine: str | None) -> dict[str, Any]:
    try:
        result = _run_job(vault, job, machine)
    except Exception as exc:  # noqa: BLE001 -- worker records failed jobs instead of losing them.
        job.update({"status": "failed", "failed_at": now_iso(), "error": str(exc)})
        _finish_job(vault, "failed", job)
        return job
    job.update({"status": "done", "completed_at": now_iso(), **result})
    _finish_job(vault, "done", job)
    return job


def run_pending_jobs(
    vault: Path,
    *,
    machine: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Run pending jobs until the queue is empty or ``limit`` is reached."""
    results: list[dict[str, Any]] = []
    while limit is None or len(results) < limit:
        result = run_next_job(vault, machine=machine)
        if result is None:
            break
        results.append(result)
    return results


def enqueue_integrity_sweep(
    vault: Path,
    *,
    shadow: bool = True,
    sweep_id: str | None = None,
) -> list[dict[str, Any]]:
    """Queue the scheduled integrity checks once per sweep id."""
    key = safe_filename(sweep_id or now_iso()[:10])
    return [
        enqueue_operation(
            vault,
            operation_id,
            payload={"shadow": shadow},
            idempotency_key=f"{operation_id}-{key}",
            schedule_id=key,
            provenance={"surface": "worker-schedule"},
        )
        for operation_id in INTEGRITY_SWEEP_OPERATIONS
    ]


def run_integrity_sweep(
    vault: Path,
    *,
    shadow: bool = True,
    sweep_id: str | None = None,
    machine: str | None = None,
) -> dict[str, Any]:
    """Queue and run the scheduled integrity checks."""
    jobs = enqueue_integrity_sweep(vault, shadow=shadow, sweep_id=sweep_id)
    pending_count = sum(1 for job in jobs if job.get("status") == "pending")
    results = run_pending_jobs(vault, machine=machine, limit=pending_count)
    return {"jobs": jobs, "results": results}


def _run_job(vault: Path, job: dict[str, Any], machine: str | None) -> dict[str, Any]:
    if job.get("kind") == "operation":
        return _run_operation_job(vault, job, machine)
    if job.get("kind") != "trusted_write":
        raise ValueError(f"unsupported worker job kind: {job.get('kind')!r}")
    target = str(job["target_path"])
    stage_concept(
        vault,
        target,
        str(job["content"]),
        inputs=job.get("inputs") or [],
        operation=str(job.get("operation") or "trusted-write"),
        run_id=str(job.get("run_id") or job["job_id"]),
        machine=machine,
    )
    promote_checked(vault, target, machine=machine)
    commit = commit_writer_changes(vault, f"trusted write {target}", [target], machine=machine)
    return {"commit": commit, "outputs": [target]}


def _run_operation_job(vault: Path, job: dict[str, Any], machine: str | None) -> dict[str, Any]:
    operation_id = str(job.get("operation_id") or "")
    payload = job.get("payload") if isinstance(job.get("payload"), dict) else {}
    from memoria_vault.runtime.operations import (
        load_operation_policy,
        require_allowed_network,
        required_promotion_checks,
        resolve_operation_runner,
    )

    policy = load_operation_policy(vault, operation_id)
    if operation_id == "create-concept":
        target, content = _create_concept_payload(payload)
        envelope = (
            job.get("request_envelope") if isinstance(job.get("request_envelope"), dict) else {}
        )
        actor = str(envelope.get("actor") or "pi")
        stage_concept(
            vault,
            target,
            content,
            operation=operation_id,
            run_id=str(job.get("job_id") or ""),
            actor=actor,
            machine=machine,
        )
        materialized = materialize_unchecked(vault, target)
        commit = commit_writer_changes(
            vault, f"create {Path(target).stem}", [target], machine=machine
        )
        return {
            "commit": commit,
            "outputs": [target],
            "output_path": target,
            "check_status": state.concept_check_status(vault, target),
            "materialized": materialized,
        }
    if operation_id == "integrity-evidence-check":
        from memoria_vault.runtime.integrity import check_evidence_integrity

        result = check_evidence_integrity(
            vault,
            shadow=bool(payload.get("shadow", True)),
            machine=machine,
            commit=True,
        )
        return {
            "commit": result["commit"],
            "finding_count": len(result["findings"]),
            "findings": result["findings"],
        }
    if operation_id == "integrity-claim-quote-check":
        from memoria_vault.runtime.integrity import check_claim_quote_support

        result = check_claim_quote_support(
            vault,
            shadow=bool(payload.get("shadow", True)),
            machine=machine,
            commit=True,
        )
        return {
            "commit": result["commit"],
            "finding_count": len(result["findings"]),
            "findings": result["findings"],
        }
    if operation_id == "integrity-quote-anchor-check":
        from memoria_vault.runtime.integrity import check_quote_anchor_support

        result = check_quote_anchor_support(
            vault,
            shadow=bool(payload.get("shadow", True)),
            machine=machine,
            commit=True,
        )
        return {
            "commit": result["commit"],
            "finding_count": len(result["findings"]),
            "findings": result["findings"],
        }
    if operation_id == "integrity-prompt-injection-check":
        from memoria_vault.runtime.integrity import check_prompt_injection_markers

        result = check_prompt_injection_markers(
            vault,
            shadow=bool(payload.get("shadow", True)),
            machine=machine,
            commit=True,
        )
        return {
            "commit": result["commit"],
            "finding_count": len(result["findings"]),
            "findings": result["findings"],
        }
    if operation_id == "integrity-provenance-checkpoint":
        from memoria_vault.runtime.integrity import check_provenance_checkpoint

        result = check_provenance_checkpoint(
            vault,
            shadow=bool(payload.get("shadow", True)),
            machine=machine,
            commit=True,
        )
        return {
            "commit": result["commit"],
            "finding_count": len(result["findings"]),
            "findings": result["findings"],
        }
    if operation_id == "integrity-citation-survival-check":
        from memoria_vault.runtime.integrity import check_citation_survival

        result = check_citation_survival(
            vault,
            shadow=bool(payload.get("shadow", True)),
            machine=machine,
            commit=True,
        )
        return {
            "commit": result["commit"],
            "finding_count": len(result["findings"]),
            "findings": result["findings"],
        }
    if operation_id == "integrity-contradiction-check":
        from memoria_vault.runtime.integrity import check_contradiction_links

        result = check_contradiction_links(
            vault,
            shadow=bool(payload.get("shadow", True)),
            machine=machine,
            commit=True,
        )
        return {
            "commit": result["commit"],
            "finding_count": len(result["findings"]),
            "findings": result["findings"],
        }
    if operation_id == "integrity-link-target-check":
        from memoria_vault.runtime.integrity import check_link_targets

        result = check_link_targets(
            vault,
            shadow=bool(payload.get("shadow", True)),
            machine=machine,
            commit=True,
        )
        return {
            "commit": result["commit"],
            "finding_count": len(result["findings"]),
            "findings": result["findings"],
        }
    if operation_id == "trace-integrity-scan":
        from memoria_vault.runtime.trusted_writer import (
            quarantine_untraced,
            quarantine_untraced_from_status,
        )

        paths = payload.get("paths")
        reason = str(payload.get("reason") or "worker-trace-integrity")
        if paths is None:
            events = quarantine_untraced_from_status(vault, reason=reason, machine=machine)
        else:
            if not isinstance(paths, list) or not all(
                isinstance(path, str) and path.strip() for path in paths
            ):
                raise ValueError("trace-integrity-scan paths must be a list of strings")
            events = quarantine_untraced(
                vault,
                [path.strip() for path in paths],
                reason=reason,
                machine=machine,
            )
        commit = ""
        if events:
            tracked_targets = [
                str(event["target_id"])
                for event in events
                if _git_path_tracked(vault, str(event["target_id"]))
            ]
            commit = commit_writer_changes(
                vault, "trace integrity scan", tracked_targets, machine=machine
            )
        return {"commit": commit, "finding_count": len(events), "findings": events}
    if operation_id == "compile-source-digest":
        from memoria_vault.runtime.operations import compile_source_digest

        source_id = str(payload.get("source_id") or "").strip()
        hub_topics = payload.get("hub_topics")
        if not source_id:
            raise ValueError("compile-source-digest requires source_id")
        if not isinstance(hub_topics, list) or not all(
            isinstance(topic, str) and topic.strip() for topic in hub_topics
        ):
            raise ValueError("compile-source-digest requires hub_topics")
        result = compile_source_digest(
            vault,
            source_id,
            [topic.strip() for topic in hub_topics],
            mode=str(payload.get("mode") or "test"),
            machine=machine,
            run_id=str(payload.get("run_id") or "") or None,
        )
        return {
            "commit": result["commit"],
            "digest_path": result["digest_path"],
            "hub_paths": result["hub_paths"],
            "hub_suggestions": result["hub_suggestions"],
            "interview_count": result["interview_count"],
        }
    if operation_id == "record-copi-interview":
        from memoria_vault.runtime.operations import record_copi_interview_turn

        source_id = str(payload.get("source_id") or "").strip()
        response = str(payload.get("response") or "").strip()
        if not source_id:
            raise ValueError("record-copi-interview requires source_id")
        if not response:
            raise ValueError("record-copi-interview requires response")
        result = record_copi_interview_turn(
            vault,
            source_id,
            response,
            prompt=str(payload.get("prompt") or "What matters about this source?"),
            project_id=str(payload.get("project_id") or ""),
            machine=machine,
            run_id=str(payload.get("run_id") or "") or None,
        )
        return {
            "commit": result["commit"],
            "turn_id": result["event"]["turn_id"],
            "source_id": result["event"]["source_id"],
        }
    if operation_id == "propose-note-candidates":
        from memoria_vault.runtime.knowledge import emit_note_candidates

        digest_path = str(payload.get("digest_path") or "").strip()
        candidates = payload.get("candidates")
        if not digest_path:
            raise ValueError("propose-note-candidates requires digest_path")
        if not isinstance(candidates, list) or not all(
            isinstance(candidate, dict) for candidate in candidates
        ):
            raise ValueError("propose-note-candidates requires candidates")
        result = emit_note_candidates(
            vault,
            digest_path,
            candidates,
            mode=str(payload.get("mode") or "test"),
            machine=machine,
            run_id=str(payload.get("run_id") or "") or None,
        )
        return {
            "commit": result["commit"],
            "note_paths": result["note_paths"],
        }
    if operation_id == "curate-note-candidate":
        from memoria_vault.runtime.knowledge import curate_note_candidate

        note_path = str(payload.get("note_path") or "").strip()
        status = str(payload.get("status") or "").strip()
        if not note_path:
            raise ValueError("curate-note-candidate requires note_path")
        if not status:
            raise ValueError("curate-note-candidate requires status")
        result = curate_note_candidate(
            vault,
            note_path,
            status,
            reason=str(payload.get("reason") or ""),
            machine=machine,
        )
        return {
            "commit": result["commit"],
            "note_path": result["note_path"],
            "curation_status": result["status"],
        }
    if operation_id == "curate-note-link":
        from memoria_vault.runtime.knowledge import curate_note_link

        source_note_path = str(payload.get("source_note_path") or "").strip()
        link_type = str(payload.get("link_type") or "").strip()
        target_path = str(payload.get("target_path") or "").strip()
        if not source_note_path:
            raise ValueError("curate-note-link requires source_note_path")
        if not link_type:
            raise ValueError("curate-note-link requires link_type")
        if not target_path:
            raise ValueError("curate-note-link requires target_path")
        result = curate_note_link(
            vault,
            source_note_path,
            link_type,
            target_path,
            reason=str(payload.get("reason") or ""),
            machine=machine,
        )
        return {
            "commit": result["commit"],
            "source_note_path": result["source_note_path"],
            "target_path": result["target_path"],
            "link_type": result["link_type"],
            "changed": result["changed"],
        }
    if operation_id == "analyze-gaps":
        from memoria_vault.runtime.knowledge import analyze_gaps

        seed_terms = payload.get("seed_terms") or []
        dense_threshold = payload.get("dense_threshold", 2)
        if not isinstance(seed_terms, list) or not all(
            isinstance(term, str) for term in seed_terms
        ):
            raise ValueError("analyze-gaps requires seed_terms")
        if not isinstance(dense_threshold, int) or dense_threshold < 1:
            raise ValueError("analyze-gaps requires dense_threshold >= 1")
        project_path = str(payload.get("project_path") or "").strip()
        result = analyze_gaps(
            vault,
            seed_terms=seed_terms,
            dense_threshold=dense_threshold,
            project_path=project_path,
            machine=machine,
        )
        out = {
            "checked_topics": result["checked_topics"],
            "dense_threshold": result["dense_threshold"],
            "summary": result["summary"],
            "saturation": result["saturation"],
            "citation_neighborhood_gap_count": result["citation_neighborhood_gap_count"],
            "full_text_gap_count": result["full_text_gap_count"],
            "full_text_attention_paths": result["full_text_attention_paths"],
            "full_text_attention_commit": result["full_text_attention_commit"],
            "argument_gap_count": result["argument_gap_count"],
            "discovery_candidate_paths": result["discovery_candidate_paths"],
            "discovery_commit": result["discovery_commit"],
            "gap_count": len(result["gaps"]),
            "gap_findings": result["gap_findings"],
            "gaps": result["gaps"],
        }
        if project_path:
            out.update(
                {
                    "project_path": result["project_path"],
                    "thesis_path": result["thesis_path"],
                    "argument_stage": result["argument_stage"],
                    "evidence_saturation": result["evidence_saturation"],
                    "displayed_confidence": result["displayed_confidence"],
                }
            )
        return out
    if operation_id == "analyze-project-argument":
        from memoria_vault.runtime.knowledge import analyze_project_argument

        project_path = str(payload.get("project_path") or "").strip()
        if not project_path:
            raise ValueError("analyze-project-argument requires project_path")
        result = analyze_project_argument(vault, project_path)
        return {
            "project_path": result["project_path"],
            "thesis_path": result["thesis_path"],
            "argument_stage": result["argument_stage"],
            "evidence_saturation": result["evidence_saturation"],
            "displayed_confidence": result["displayed_confidence"],
            "saturation_conditions": result["saturation_conditions"],
            "relation_count": result["relation_count"],
            "supports_count": result["supports_count"],
            "contradicts_count": result["contradicts_count"],
            "extends_count": result["extends_count"],
            "node_count": result["node_count"],
            "findings": result["findings"],
            "gap_findings": result["gap_findings"],
            "advisories": result["advisories"],
            "nodes": result["nodes"],
            "edges": result["edges"],
        }
    if operation_id == "render-project-argument-canvas":
        from memoria_vault.runtime.knowledge import write_project_argument_canvas

        project_path = str(payload.get("project_path") or "").strip()
        if not project_path:
            raise ValueError("render-project-argument-canvas requires project_path")
        result = write_project_argument_canvas(
            vault,
            project_path,
            commit=True,
            machine=machine,
        )
        return {
            "commit": result["commit"],
            "project_path": result["project_path"],
            "canvas_path": result["canvas_path"],
            "node_count": result["node_count"],
            "edge_count": result["edge_count"],
        }
    if operation_id == "export-project":
        from memoria_vault.runtime.knowledge import write_project_export

        project_path = str(payload.get("project_path") or "").strip()
        if not project_path:
            raise ValueError("export-project requires project_path")
        result = write_project_export(
            vault,
            project_path,
            export_format=str(payload.get("format") or "markdown"),
            output_path=str(payload.get("output_path") or ""),
        )
        return {
            "project_path": result["project_path"],
            "format": result["format"],
            "output_path": result["output_path"],
            "content": result["content"],
            "node_count": result["node_count"],
            "edge_count": result["edge_count"],
            "relation_count": result["relation_count"],
        }
    if operation_id == "rebuild-checked-qmd-source":
        from memoria_vault.runtime.search_index import rebuild_checked_qmd_source

        manifest = rebuild_checked_qmd_source(vault)
        return {
            "input_root": manifest["input_root"],
            "document_count": len(manifest["documents"]),
            "documents": manifest["documents"],
            "qmd_commands": manifest["qmd_commands"],
        }
    if operation_id == "answer-query":
        from memoria_vault.runtime.search_index import answer_query

        query = str(payload.get("query") or "").strip()
        k = payload.get("k", 5)
        if not query:
            raise ValueError("answer-query requires query")
        if not isinstance(k, int) or k < 1:
            raise ValueError("answer-query requires k >= 1")
        return answer_query(
            vault,
            query,
            k=k,
            include_stale=bool(payload.get("include_stale", False)),
            project_id=str(payload.get("project_id") or ""),
        )
    if operation_id == "run-seeded-error-verdict":
        from memoria_vault.runtime.seeded_errors import run_seeded_error_verdict

        bundle_path = vault / "system/eval/alpha12-seeded-errors.json"
        if not bundle_path.is_file():
            bundle_path = vault / "system/eval/alpha11-seeded-errors.json"
        runner = resolve_operation_runner(vault, policy, str(payload.get("mode") or "test"))
        with tempfile.TemporaryDirectory(prefix="memoria-seeded-gate-") as tmpdir:
            return run_seeded_error_verdict(
                Path(tmpdir),
                template_root=vault,
                bundle_path=bundle_path,
                runner=runner,
                machine=machine or "seeded-gate",
            )
    if operation_id == "eval-run":
        from memoria_vault.runtime.subsystems.telemetry.eval import eval_dispatch

        dry_run = bool(payload.get("dry_run", False))
        result = eval_dispatch.dispatch(vault, dry_run=dry_run)
        outputs = [] if dry_run else ["system/eval/last-run.md"]
        return {"outputs": outputs, **result}
    if operation_id == "check-source-metadata":
        from memoria_vault.runtime.integrity import check_source_metadata

        result = check_source_metadata(
            vault,
            shadow=bool(payload.get("shadow", True)),
            machine=machine,
            commit=True,
        )
        return {
            "commit": result["commit"],
            "finding_count": len(result["findings"]),
            "findings": result["findings"],
        }
    if operation_id == "cascade-rollback":
        from memoria_vault.runtime.integrity import cascade_rollback

        target_id = str(payload.get("target_id") or "").strip()
        if not target_id:
            raise ValueError("cascade-rollback requires target_id")
        result = cascade_rollback(
            vault,
            target_id,
            reason=str(payload.get("reason") or "worker-cascade-rollback"),
            include_target=bool(payload.get("include_target", False)),
            machine=machine,
        )
        return {
            "commit": result["commit"],
            "reverted_count": len(result["reverted"]),
            "needs_human_count": len(result["needs_human"]),
            "rollback": result,
        }
    if operation_id in {"acknowledge-attention", "resolve-attention"}:
        from memoria_vault.runtime.integrity import resolve_attention

        target_id = str(payload.get("target_id") or "").strip()
        if not target_id:
            raise ValueError(f"{operation_id} requires target_id")
        result = resolve_attention(
            vault,
            target_id,
            resolution="acknowledged" if operation_id == "acknowledge-attention" else "resolved",
            outcome=str(
                payload.get("outcome")
                or ("acknowledged" if operation_id == "acknowledge-attention" else "apply")
            ),
            routing_class=str(payload.get("routing_class") or "ask"),
            reason=str(payload.get("reason") or operation_id),
            machine=machine,
        )
        return {"commit": result["commit"], "resolution": result["event"]}
    if operation_id == "observe-pi-edits":
        from memoria_vault.runtime.projections import (
            changed_tracked_projection_paths,
            write_tracked_projections,
        )
        from memoria_vault.runtime.trusted_writer import (
            observe_pi_edits_from_status,
            quarantine_untraced,
        )

        projection_paths = changed_tracked_projection_paths(vault)
        projection_events = quarantine_untraced(
            vault,
            projection_paths,
            reason="workspace-scan-generated-projection",
            machine=machine,
        )
        projection_commit = ""
        regeneration: dict[str, Any] = {}
        if projection_events:
            tracked_targets = [
                str(event["target_id"])
                for event in projection_events
                if _git_path_tracked(vault, str(event["target_id"]))
            ]
            projection_commit = commit_writer_changes(
                vault, "trace integrity scan", tracked_targets, machine=machine
            )
            regeneration = write_tracked_projections(vault, commit=True, machine=machine)
        result = observe_pi_edits_from_status(vault, machine=machine)
        commits = [
            commit
            for commit in (
                projection_commit,
                str(regeneration.get("commit") or ""),
                result["commit"],
            )
            if commit
        ]
        return {
            "commit": commits[-1] if commits else "",
            "observed_count": len(result["observed"]),
            "paths": result["paths"],
            "projection_quarantine_count": len(projection_events),
            "projection_paths": projection_paths,
            "regeneration": regeneration,
        }
    if operation_id == "mark-checked":
        from memoria_vault.runtime.trusted_writer import mark_checked

        target_path = str(payload.get("target_path") or "").strip()
        if not target_path:
            raise ValueError("mark-checked requires target_path")
        payload_check = str(payload.get("check") or "").strip()
        checks = required_promotion_checks(policy)
        if payload_check and payload_check not in checks:
            raise ValueError(f"mark-checked check must be declared by policy: {payload_check}")
        event = mark_checked(vault, target_path, checks=checks, machine=machine)
        commit = commit_writer_changes(
            vault,
            f"mark checked {Path(target_path).stem}",
            [target_path],
            machine=machine,
        )
        return {"commit": commit, "check": event}
    if operation_id == "surface-tensions":
        from memoria_vault.runtime.integrity import surface_tensions

        return surface_tensions(
            vault,
            max_pairs=int(payload.get("max_pairs") or 20),
            machine=machine,
            commit=True,
        )
    if operation_id in {
        "analyze-claims",
        "check-falsifiability",
        "compare-and-contrast",
        "extract-claim-stubs",
        "red-team-argument",
        "summarize-for-recall",
    }:
        from memoria_vault.runtime.operations import run_prompt_operation

        return run_prompt_operation(
            vault,
            operation_id,
            payload,
            mode=str(payload.get("mode") or "test"),
            machine=machine,
            run_id=str(job["job_id"]),
        )
    if operation_id == "update-work":
        source_id = str(payload.get("source_id") or "").strip()
        if not source_id:
            raise ValueError("update-work requires source_id")
        source = state.catalog_source(vault, source_id)
        if source is None:
            raise ValueError(f"work not found: {source_id}")

        identifiers = dict(source["identifiers"])
        csl_json = dict(source["csl_json"])
        if doi := str(payload.get("doi") or "").strip():
            identifiers["doi"] = doi
            csl_json["DOI"] = doi
        if "resource" in payload:
            csl_json["URL"] = str(payload.get("resource") or "")

        memoria = csl_json.get("memoria") if isinstance(csl_json.get("memoria"), dict) else {}
        if standing := str(payload.get("standing") or "").strip():
            if standing not in {"current", "archived", "retracted", "superseded"}:
                raise ValueError(f"update-work standing is invalid: {standing}")
            memoria["standing"] = standing
        for payload_key, memoria_key in (("research_area", "research_area"), ("topic", "topics")):
            if payload_key not in payload:
                continue
            values = payload[payload_key]
            if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
                raise ValueError(f"update-work {payload_key} must be a list of strings")
            memoria[memoria_key] = [value for value in values if value.strip()]
        if memoria:
            csl_json["memoria"] = memoria

        provider_coverage = str(payload.get("provider_coverage") or source["provider_coverage"])
        if provider_coverage not in {"full", "partial", "degraded"}:
            raise ValueError(f"update-work provider_coverage is invalid: {provider_coverage}")
        check_status = str(payload.get("check_status") or source["check_status"])
        if check_status not in {"unchecked", "checked", "quarantined"}:
            raise ValueError(f"update-work check_status is invalid: {check_status}")
        if provider_coverage == "degraded" and check_status == "checked":
            if "check_status" in payload:
                raise ValueError("update-work degraded provider coverage cannot set checked")
            check_status = "unchecked"

        state.upsert_catalog_record(
            vault,
            source_id=source["source_id"],
            concept_path=source["concept_path"],
            doi=identifiers.get("doi"),
            title=str(payload.get("title") or source["title"]),
            description=(
                str(payload["description"]) if "description" in payload else source["description"]
            ),
            resource=str(payload["resource"]) if "resource" in payload else source["resource"],
            identifiers=identifiers,
            citekey=str(payload["citekey"]) if "citekey" in payload else source["citekey"],
            csl_json=csl_json,
            provider_coverage=provider_coverage,
            text_status=source["text_status"],
            check_status=check_status,
            content_hash=source["normalized_text_sha256"],
            raw_hash=source["raw_text_sha256"],
            content_path=source["content_path"],
            raw_path=source["raw_path"],
        )
        updated = state.catalog_source(vault, source["source_id"])
        updates = {
            key: value
            for key, value in payload.items()
            if key != "source_id" and value not in (None, [], "")
        }
        append_jsonl(
            vault / OVERRIDE_LOG_REL,
            [
                {
                    "timestamp": now_iso(),
                    "operation": "update-work",
                    "source_id": source["source_id"],
                    "updates": updates,
                }
            ],
        )
        state.append_journal_event(
            vault,
            {
                "event": "work_updated",
                "operation": "update-work",
                "source_id": source["source_id"],
                "updates": updates,
                "override_log": OVERRIDE_LOG_REL,
            },
            machine=machine,
        )
        commit = commit_writer_changes(
            vault,
            f"update work {source['source_id']}",
            [OVERRIDE_LOG_REL],
            machine=machine,
        )
        return {
            "source_id": source["source_id"],
            "work": updated,
            "override_log": OVERRIDE_LOG_REL,
            "commit": commit,
        }
    if operation_id == "capture-source":
        from memoria_vault.runtime.capture import stage_catalog_source

        source_id = str(payload.get("source_id") or "").strip()
        title = str(payload.get("title") or "").strip()
        description = str(payload.get("description") or "").strip()
        content_text = str(payload.get("content_text") or "").strip()
        if not source_id:
            raise ValueError("capture-source requires source_id")
        if not title:
            raise ValueError("capture-source requires title")
        if not description:
            raise ValueError("capture-source requires description")
        if not content_text:
            raise ValueError("capture-source requires content_text")
        identifiers = payload.get("identifiers")
        csl_json = payload.get("csl_json")
        if identifiers is not None and not isinstance(identifiers, dict):
            raise ValueError("capture-source identifiers must be an object")
        if csl_json is not None and not isinstance(csl_json, dict):
            raise ValueError("capture-source csl_json must be an object")
        if "raw_text" in payload and not isinstance(payload["raw_text"], str):
            raise ValueError("capture-source raw_text must be a string")
        capture_kwargs = {
            "raw_bytes": payload["raw_text"].encode() if "raw_text" in payload else None,
            "raw_filename": str(payload.get("raw_filename") or "source.txt"),
            "resource": str(payload.get("resource") or ""),
            "item_type": str(payload.get("item_type") or "article"),
            "identifiers": identifiers,
            "csl_json": csl_json,
            "provider_coverage": str(payload.get("provider_coverage") or "partial"),
            "text_status": str(payload.get("text_status") or "full-text"),
            "citekey": str(payload.get("citekey") or ""),
            "machine": machine,
            "run_id": str(payload.get("run_id") or "") or None,
        }
        result = stage_catalog_source(
            vault,
            source_id,
            title,
            description,
            content_text,
            **capture_kwargs,
        )
        return {
            "commit": result["commit"],
            "source_id": result["source_id"],
            "content_path": result["content_path"],
            "raw_path": result["raw_path"],
            "text_status": result["text_status"],
            "check_status": result["check_status"],
        }
    if operation_id == "enrich-source":
        from memoria_vault.runtime.enrichment import enrich_source

        source_id = str(payload.get("source_id") or "").strip()
        if not source_id:
            raise ValueError("enrich-source requires source_id")
        provider_payloads = payload.get("provider_payloads")
        if provider_payloads is not None and not isinstance(provider_payloads, dict):
            raise ValueError("enrich-source provider_payloads must be an object")
        return enrich_source(
            vault,
            source_id,
            policy=policy,
            provider_payloads=provider_payloads,
            machine=machine,
            run_id=str(payload.get("run_id") or "") or None,
        )
    if operation_id == "capture-bibtex-source":
        from memoria_vault.runtime.capture import bibtex_capture_payload, stage_catalog_source

        bibtex_value = payload.get("bibtex")
        if bibtex_value is not None and not isinstance(bibtex_value, str):
            raise ValueError("capture-bibtex-source bibtex must be a string")
        bibtex = str(bibtex_value or "").strip()
        if not bibtex:
            raise ValueError("capture-bibtex-source requires bibtex")
        content_text = payload.get("content_text")
        if content_text is not None and not isinstance(content_text, str):
            raise ValueError("capture-bibtex-source content_text must be a string")
        source_id = payload.get("source_id")
        description = payload.get("description")
        run_id = payload.get("run_id")
        if source_id is not None and not isinstance(source_id, str):
            raise ValueError("capture-bibtex-source source_id must be a string")
        if description is not None and not isinstance(description, str):
            raise ValueError("capture-bibtex-source description must be a string")
        if run_id is not None and not isinstance(run_id, str):
            raise ValueError("capture-bibtex-source run_id must be a string")
        capture_payload = bibtex_capture_payload(
            bibtex,
            content_text=content_text,
            source_id=source_id or None,
            description=description or None,
        )
        if run_id:
            capture_payload["run_id"] = run_id
        result = stage_catalog_source(
            vault,
            str(capture_payload["source_id"]),
            str(capture_payload["title"]),
            str(capture_payload["description"]),
            str(capture_payload["content_text"]),
            raw_bytes=str(capture_payload["raw_text"]).encode(),
            raw_filename=str(capture_payload["raw_filename"]),
            resource=str(capture_payload.get("resource") or ""),
            item_type=str(capture_payload.get("item_type") or "article"),
            identifiers=capture_payload.get("identifiers"),
            csl_json=capture_payload.get("csl_json"),
            provider_coverage=str(capture_payload.get("provider_coverage") or "partial"),
            text_status=str(capture_payload.get("text_status") or "metadata-only"),
            citekey=str(capture_payload.get("citekey") or ""),
            machine=machine,
            run_id=str(capture_payload.get("run_id") or "") or None,
            workflow="capture_bibtex_source",
        )
        enrichment_job = None
        if _payload_doi(capture_payload):
            enrichment_job = enqueue_operation(
                vault,
                "enrich-source",
                payload={"source_id": result["source_id"]},
                idempotency_key=f"enrich-{result['source_id']}",
                input_refs=[{"id": result["source_id"], "kind": "catalog_source"}],
                primary_target=f"catalog/sources/{result['source_id']}",
                causal_refs=[str(job["job_id"])],
                actor="operation",
                provenance={"surface": "worker", "command": "capture-bibtex-source"},
            )
        return {
            "commit": result["commit"],
            "source_id": result["source_id"],
            "content_path": result["content_path"],
            "raw_path": result["raw_path"],
            "text_status": result["text_status"],
            "check_status": result["check_status"],
            "enrichment_job": enrichment_job,
        }
    if operation_id == "capture-url-source":
        from memoria_vault.runtime.capture import stage_url_source

        url = str(payload.get("url") or "").strip()
        if not url:
            raise ValueError("capture-url-source requires url")
        timeout = payload.get("timeout", 10.0)
        if not isinstance(timeout, int | float):
            raise ValueError("capture-url-source timeout must be numeric")
        require_allowed_network(policy, url)
        result = stage_url_source(
            vault,
            url,
            title=str(payload.get("title") or "") or None,
            description=str(payload.get("description") or "") or None,
            timeout=float(timeout),
            machine=machine,
            run_id=str(payload.get("run_id") or "") or None,
        )
        return {
            "commit": result["commit"],
            "source_id": result["source_id"],
            "content_path": result["content_path"],
            "raw_path": result["raw_path"],
            "text_status": result["text_status"],
            "check_status": result["check_status"],
        }
    if operation_id == "capture-pdf-source":
        from memoria_vault.runtime.capture import stage_pdf_source

        source_id = str(payload.get("source_id") or "").strip()
        title = str(payload.get("title") or "").strip()
        description = str(payload.get("description") or "").strip()
        raw_pdf_base64 = str(payload.get("raw_pdf_base64") or "").strip()
        if not source_id:
            raise ValueError("capture-pdf-source requires source_id")
        if not title:
            raise ValueError("capture-pdf-source requires title")
        if not description:
            raise ValueError("capture-pdf-source requires description")
        if not raw_pdf_base64:
            raise ValueError("capture-pdf-source requires raw_pdf_base64")
        identifiers = payload.get("identifiers")
        csl_json = payload.get("csl_json")
        if identifiers is not None and not isinstance(identifiers, dict):
            raise ValueError("capture-pdf-source identifiers must be an object")
        if csl_json is not None and not isinstance(csl_json, dict):
            raise ValueError("capture-pdf-source csl_json must be an object")
        result = stage_pdf_source(
            vault,
            source_id,
            title,
            description,
            base64.b64decode(raw_pdf_base64),
            raw_filename=str(payload.get("raw_filename") or "source.pdf"),
            resource=str(payload.get("resource") or ""),
            item_type=str(payload.get("item_type") or "article"),
            identifiers=identifiers,
            csl_json=csl_json,
            provider_coverage=str(payload.get("provider_coverage") or "partial"),
            citekey=str(payload.get("citekey") or ""),
            machine=machine,
            run_id=str(payload.get("run_id") or "") or None,
        )
        return {
            "commit": result["commit"],
            "source_id": result["source_id"],
            "content_path": result["content_path"],
            "raw_path": result["raw_path"],
            "text_status": result["text_status"],
            "check_status": result["check_status"],
        }
    if operation_id == "regenerate-references-bib":
        from memoria_vault.runtime.capture import write_references_bib

        result = write_references_bib(vault, commit=True, machine=machine)
        return {
            "commit": result["commit"],
            "changed": result["changed"],
            "output": result["path"],
        }
    if operation_id == "regenerate-capability-index":
        from memoria_vault.runtime.capabilities import write_capability_index

        result = write_capability_index(vault, commit=True, machine=machine)
        return {
            "commit": result["commit"],
            "changed": result["changed"],
            "output": result["path"],
        }
    if operation_id == "regenerate-indexes":
        from memoria_vault.runtime.projections import write_workspace_indexes

        result = write_workspace_indexes(vault, commit=True, machine=machine)
        return {
            "commit": result["commit"],
            "changed": result["changed"],
            "outputs": result["paths"],
        }
    if operation_id == "regenerate-tracked-projections":
        from memoria_vault.runtime.projections import write_tracked_projections

        result = write_tracked_projections(vault, commit=True, machine=machine)
        return {
            "commit": result["commit"],
            "changed": result["changed"],
            "outputs": result["paths"],
        }
    raise ValueError(f"unsupported operation: {operation_id!r}")


def _create_concept_payload(payload: dict[str, Any]) -> tuple[str, str]:
    target = normalize_path(str(payload.get("target_path") or ""))
    content = str(payload.get("content") or "")
    if not target or not content:
        raise ValueError("create-concept requires target_path and content")
    concept_type = str(payload.get("concept_type") or "").strip()
    if concept_type not in CREATE_CONCEPT_HOMES:
        allowed = ", ".join(sorted(CREATE_CONCEPT_HOMES))
        raise ValueError(f"create-concept concept_type must be one of: {allowed}")
    expected_home = CREATE_CONCEPT_HOMES[concept_type]
    if not target.startswith(f"{expected_home}/"):
        raise ValueError(f"create-concept {concept_type} target must be under {expected_home}/")
    frontmatter, _body = split_frontmatter(content)
    if str(frontmatter.get("type") or "") != concept_type:
        raise ValueError("create-concept content type must match concept_type")
    return target, content


def _claim_sqlite_job(vault: Path, job: dict[str, Any]) -> dict[str, Any]:
    job_id = str(job["job_id"])
    job = {**job, "status": "running", "started_at": now_iso()}
    state.set_request_running(vault, job_id, job)
    return job


def _finish_job(vault: Path, status: str, job: dict[str, Any]) -> None:
    state.finish_request(vault, str(job["job_id"]), status, job)


def _git_path_tracked(vault: Path, relpath: str) -> bool:
    proc = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relpath],
        cwd=vault,
        check=False,
        text=True,
        capture_output=True,
    )
    return proc.returncode == 0


def main(argv: list[str] | None = None) -> int:
    parser = ArgumentParser(description="Run SQLite-backed worker requests.")
    parser.add_argument(
        "command",
        choices=(
            "enqueue-operation",
            "integrity-sweep",
            "observe-pi-edits",
            "scan",
            "run-scheduled",
            "run-pending",
            "recover",
        ),
    )
    parser.add_argument("--vault", required=True)
    parser.add_argument("--machine", default="memoria-scheduled-checks")
    parser.add_argument("--active", action="store_true")
    parser.add_argument("--sweep-id", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--operation-id", default=None)
    parser.add_argument("--payload", default="{}")
    parser.add_argument("--idempotency-key", default=None)
    parser.add_argument("--schedule-id", default=None)
    args = parser.parse_args(argv)

    vault = Path(args.vault)
    if args.command == "enqueue-operation":
        if not args.operation_id:
            parser.error("enqueue-operation requires --operation-id")
        payload = json.loads(args.payload)
        if not isinstance(payload, dict):
            parser.error("--payload must be a JSON object")
        print(
            json.dumps(
                enqueue_operation(
                    vault,
                    args.operation_id,
                    payload=payload,
                    idempotency_key=args.idempotency_key,
                ),
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "scan":
        enqueue_operation(
            vault,
            "observe-pi-edits",
            idempotency_key=args.idempotency_key or f"scan-{now_iso()}",
            provenance={"surface": "worker-scan"},
        )
        run_pending_jobs(vault, machine=args.machine, limit=1)
        return 0
    if args.command == "run-scheduled":
        if not args.operation_id:
            parser.error("run-scheduled requires --operation-id")
        payload = json.loads(args.payload)
        if not isinstance(payload, dict):
            parser.error("--payload must be a JSON object")
        enqueue_operation(
            vault,
            args.operation_id,
            payload=payload,
            idempotency_key=args.idempotency_key or f"{args.operation_id}-{args.schedule_id}",
            schedule_id=args.schedule_id,
            provenance={"surface": "worker-schedule"},
        )
        run_pending_jobs(vault, machine=args.machine, limit=1)
        return 0
    if args.command == "integrity-sweep":
        run_integrity_sweep(
            vault,
            shadow=not args.active,
            sweep_id=args.sweep_id,
            machine=args.machine,
        )
        return 0
    if args.command == "observe-pi-edits":
        from memoria_vault.runtime.trusted_writer import observe_pi_edits_from_status

        observe_pi_edits_from_status(vault, machine=args.machine)
        return 0
    if args.command == "recover":
        print(json.dumps(state.recover_pending_materializations(vault), ensure_ascii=False))
        return 0
    run_pending_jobs(vault, machine=args.machine, limit=args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
