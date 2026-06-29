"""Minimal alpha.11 local worker queue."""

from __future__ import annotations

import base64
import json
import subprocess
import tempfile
import uuid
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.time import now_iso
from memoria_vault.runtime.trusted_writer import (
    commit_writer_changes,
    promote_checked,
    stage_concept,
)

QUEUE_ROOT = ".memoria/queue"
QUEUE_STATES = ("pending", "running", "done", "failed")
INTEGRITY_SWEEP_OPERATIONS = (
    "trace-integrity-scan",
    "check-source-metadata",
    "integrity-evidence-check",
    "integrity-quote-anchor-check",
    "integrity-claim-quote-check",
    "integrity-prompt-injection-check",
    "integrity-provenance-checkpoint",
    "integrity-contradiction-check",
    "integrity-link-target-check",
)


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
    existing = _find_job(vault, job_id)
    if existing:
        return _read_json(existing)

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
    _write_json(_job_path(vault, "pending", job_id), job)
    return job


def enqueue_operation(
    vault: Path,
    operation_id: str,
    *,
    payload: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Queue one operation request for the local worker."""
    vault = Path(vault)
    job_id = safe_filename(idempotency_key or f"{operation_id}-{uuid.uuid4().hex}")
    existing = _find_job(vault, job_id)
    if existing:
        return _read_json(existing)

    job = {
        "job_id": job_id,
        "kind": "operation",
        "status": "pending",
        "created_at": now_iso(),
        "operation_id": operation_id,
        "payload": dict(payload or {}),
    }
    _write_json(_job_path(vault, "pending", job_id), job)
    return job


def run_next_job(vault: Path, *, machine: str | None = None) -> dict[str, Any] | None:
    """Claim and run the oldest pending worker job."""
    vault = Path(vault)
    pending = sorted(_queue_dir(vault, "pending").glob("*.json"))
    if not pending:
        return None
    running = _claim_job(vault, pending[0])
    job = _read_json(running)
    try:
        result = _run_job(vault, job, machine)
    except Exception as exc:  # noqa: BLE001 -- worker records failed jobs instead of losing them.
        job.update({"status": "failed", "failed_at": now_iso(), "error": str(exc)})
        _finish_job(vault, running, "failed", job)
        return job
    job.update({"status": "done", "completed_at": now_iso(), **result})
    _finish_job(vault, running, "done", job)
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
    from memoria_vault.runtime.operations import load_operation_policy, require_allowed_network

    policy = load_operation_policy(vault, operation_id)
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
        result = analyze_gaps(
            vault,
            seed_terms=seed_terms,
            dense_threshold=dense_threshold,
        )
        return {
            "checked_topics": result["checked_topics"],
            "dense_threshold": result["dense_threshold"],
            "gap_count": len(result["gaps"]),
            "gaps": result["gaps"],
        }
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
        )
    if operation_id == "run-seeded-error-verdict":
        from memoria_vault.runtime.seeded_errors import run_seeded_error_verdict

        bundle_path = vault / "system/eval/alpha11-seeded-errors.json"
        with tempfile.TemporaryDirectory(prefix="memoria-seeded-gate-") as tmpdir:
            return run_seeded_error_verdict(
                Path(tmpdir),
                template_root=vault,
                bundle_path=bundle_path,
                machine=machine or "seeded-gate",
            )
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
            reason=str(payload.get("reason") or operation_id),
            machine=machine,
        )
        return {"commit": result["commit"], "resolution": result["event"]}
    if operation_id == "observe-pi-edits":
        from memoria_vault.runtime.trusted_writer import observe_pi_edits_from_status

        result = observe_pi_edits_from_status(vault, machine=machine)
        return {
            "commit": result["commit"],
            "observed_count": len(result["observed"]),
            "paths": result["paths"],
        }
    if operation_id == "mark-checked":
        from memoria_vault.runtime.trusted_writer import mark_checked

        target_path = str(payload.get("target_path") or "").strip()
        if not target_path:
            raise ValueError("mark-checked requires target_path")
        check = str(payload.get("check") or "memoria-profile").strip() or "memoria-profile"
        event = mark_checked(vault, target_path, check=check, machine=machine)
        commit = commit_writer_changes(
            vault,
            f"mark checked {Path(target_path).stem}",
            [target_path],
            machine=machine,
        )
        return {"commit": commit, "check": event}
    if operation_id == "capture-source":
        from memoria_vault.runtime.capture import capture_source

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
        result = capture_source(
            vault,
            source_id,
            title,
            description,
            content_text,
            raw_bytes=payload["raw_text"].encode() if "raw_text" in payload else None,
            raw_filename=str(payload.get("raw_filename") or "source.txt"),
            resource=str(payload.get("resource") or ""),
            item_type=str(payload.get("item_type") or "article"),
            identifiers=identifiers,
            csl_json=csl_json,
            metadata_status=str(payload.get("metadata_status") or "partial"),
            citekey=str(payload.get("citekey") or ""),
            machine=machine,
            run_id=str(payload.get("run_id") or "") or None,
        )
        return {
            "commit": result["commit"],
            "source_path": result["source_path"],
            "content_path": result["content_path"],
            "raw_path": result["raw_path"],
            "entity_paths": result["entity_paths"],
        }
    if operation_id == "capture-bibtex-source":
        from memoria_vault.runtime.capture import capture_bibtex_source

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
        result = capture_bibtex_source(
            vault,
            bibtex,
            content_text=content_text,
            source_id=source_id or None,
            description=description or None,
            machine=machine,
            run_id=run_id or None,
        )
        return {
            "commit": result["commit"],
            "source_path": result["source_path"],
            "content_path": result["content_path"],
            "raw_path": result["raw_path"],
            "entity_paths": result["entity_paths"],
        }
    if operation_id == "capture-zotero-source":
        from memoria_vault.runtime.capture import capture_zotero_local_source, capture_zotero_source

        item = payload.get("zotero_item")
        item_key = str(payload.get("item_key") or "").strip()
        if item is not None and not isinstance(item, dict):
            raise ValueError("capture-zotero-source zotero_item must be an object")
        if item is None and not item_key:
            raise ValueError("capture-zotero-source requires zotero_item object or item_key")
        content_text = payload.get("content_text")
        source_id = payload.get("source_id")
        description = payload.get("description")
        raw_filename = payload.get("raw_filename")
        run_id = payload.get("run_id")
        if content_text is not None and not isinstance(content_text, str):
            raise ValueError("capture-zotero-source content_text must be a string")
        if source_id is not None and not isinstance(source_id, str):
            raise ValueError("capture-zotero-source source_id must be a string")
        if description is not None and not isinstance(description, str):
            raise ValueError("capture-zotero-source description must be a string")
        if raw_filename is not None and not isinstance(raw_filename, str):
            raise ValueError("capture-zotero-source raw_filename must be a string")
        if run_id is not None and not isinstance(run_id, str):
            raise ValueError("capture-zotero-source run_id must be a string")
        kwargs = {
            "content_text": content_text,
            "source_id": source_id or None,
            "description": description or None,
            "raw_filename": raw_filename or None,
            "machine": machine,
            "run_id": run_id or None,
        }
        if item is None:
            timeout = payload.get("timeout", 5.0)
            if not isinstance(timeout, int | float):
                raise ValueError("capture-zotero-source timeout must be numeric")
            local_api_base = str(
                payload.get("local_api_base") or "http://localhost:23119/api/users/0"
            )
            require_allowed_network(policy, local_api_base)
            result = capture_zotero_local_source(
                vault,
                item_key,
                local_api_base=local_api_base,
                timeout=float(timeout),
                **kwargs,
            )
        else:
            result = capture_zotero_source(vault, item, **kwargs)
        return {
            "commit": result["commit"],
            "source_path": result["source_path"],
            "content_path": result["content_path"],
            "raw_path": result["raw_path"],
            "entity_paths": result["entity_paths"],
        }
    if operation_id == "capture-url-source":
        from memoria_vault.runtime.capture import capture_url_source

        url = str(payload.get("url") or "").strip()
        if not url:
            raise ValueError("capture-url-source requires url")
        timeout = payload.get("timeout", 10.0)
        if not isinstance(timeout, int | float):
            raise ValueError("capture-url-source timeout must be numeric")
        require_allowed_network(policy, url)
        result = capture_url_source(
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
            "source_path": result["source_path"],
            "content_path": result["content_path"],
            "raw_path": result["raw_path"],
        }
    if operation_id == "capture-pdf-source":
        from memoria_vault.runtime.capture import capture_pdf_source

        source_id = str(payload.get("source_id") or "").strip()
        title = str(payload.get("title") or "").strip()
        description = str(payload.get("description") or "").strip()
        raw_pdf_base64 = str(payload.get("raw_pdf_base64") or "").strip()
        annotation_quotes = payload.get("annotation_quotes") or []
        if not source_id:
            raise ValueError("capture-pdf-source requires source_id")
        if not title:
            raise ValueError("capture-pdf-source requires title")
        if not description:
            raise ValueError("capture-pdf-source requires description")
        if not raw_pdf_base64:
            raise ValueError("capture-pdf-source requires raw_pdf_base64")
        if not isinstance(annotation_quotes, list) or not all(
            isinstance(quote, str) for quote in annotation_quotes
        ):
            raise ValueError("capture-pdf-source annotation_quotes must be strings")
        identifiers = payload.get("identifiers")
        csl_json = payload.get("csl_json")
        if identifiers is not None and not isinstance(identifiers, dict):
            raise ValueError("capture-pdf-source identifiers must be an object")
        if csl_json is not None and not isinstance(csl_json, dict):
            raise ValueError("capture-pdf-source csl_json must be an object")
        result = capture_pdf_source(
            vault,
            source_id,
            title,
            description,
            base64.b64decode(raw_pdf_base64),
            annotation_quotes=annotation_quotes,
            raw_filename=str(payload.get("raw_filename") or "source.pdf"),
            resource=str(payload.get("resource") or ""),
            item_type=str(payload.get("item_type") or "article"),
            identifiers=identifiers,
            csl_json=csl_json,
            metadata_status=str(payload.get("metadata_status") or "partial"),
            citekey=str(payload.get("citekey") or ""),
            machine=machine,
            run_id=str(payload.get("run_id") or "") or None,
        )
        return {
            "commit": result["commit"],
            "source_path": result["source_path"],
            "content_path": result["content_path"],
            "raw_path": result["raw_path"],
            "entity_paths": result["entity_paths"],
            "annotation_refs": result["annotation_refs"],
        }
    if operation_id == "regenerate-references-bib":
        from memoria_vault.runtime.capture import write_references_bib

        result = write_references_bib(vault, commit=True, machine=machine)
        return {
            "commit": result["commit"],
            "changed": result["changed"],
            "output": result["path"],
        }
    if operation_id == "regenerate-ai-catalog":
        from memoria_vault.runtime.capabilities import write_ai_catalog

        result = write_ai_catalog(vault, commit=True, machine=machine)
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


def _claim_job(vault: Path, path: Path) -> Path:
    job = _read_json(path)
    job["status"] = "running"
    job["started_at"] = now_iso()
    running = _job_path(vault, "running", str(job["job_id"]))
    _write_json(path, job)
    running.parent.mkdir(parents=True, exist_ok=True)
    path.replace(running)
    return running


def _finish_job(vault: Path, running: Path, state: str, job: dict[str, Any]) -> None:
    target = _job_path(vault, state, str(job["job_id"]))
    _write_json(running, job)
    target.parent.mkdir(parents=True, exist_ok=True)
    running.replace(target)


def _find_job(vault: Path, job_id: str) -> Path | None:
    for state in QUEUE_STATES:
        path = _job_path(vault, state, job_id)
        if path.exists():
            return path
    return None


def _job_path(vault: Path, state: str, job_id: str) -> Path:
    return _queue_dir(vault, state) / f"{safe_filename(job_id)}.json"


def _queue_dir(vault: Path, state: str) -> Path:
    if state not in QUEUE_STATES:
        raise ValueError(f"unknown queue state: {state}")
    return vault / QUEUE_ROOT / state


def _git_path_tracked(vault: Path, relpath: str) -> bool:
    proc = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relpath],
        cwd=vault,
        check=False,
        text=True,
        capture_output=True,
    )
    return proc.returncode == 0


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"worker job is not an object: {path}")
    return data


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = ArgumentParser(description="Run alpha.11 local worker jobs.")
    parser.add_argument(
        "command",
        choices=("enqueue-operation", "integrity-sweep", "observe-pi-edits", "run-pending"),
    )
    parser.add_argument("--vault", required=True)
    parser.add_argument("--machine", default="memoria-scheduled-checks")
    parser.add_argument("--active", action="store_true")
    parser.add_argument("--sweep-id", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--operation-id", default=None)
    parser.add_argument("--payload", default="{}")
    parser.add_argument("--idempotency-key", default=None)
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
    run_pending_jobs(vault, machine=args.machine, limit=args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
