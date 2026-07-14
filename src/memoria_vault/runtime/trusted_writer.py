"""Trusted-writer primitives for staging, promotion, and trace scans."""

from __future__ import annotations

import hashlib
import json
import platform
import re
import shutil
import subprocess
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from memoria_vault.runtime import state
from memoria_vault.runtime.content_security import (
    markdown_code_span,
    neutralize_untrusted_markdown_fragment,
)
from memoria_vault.runtime.jsonl import append_jsonl
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.audit import EMPTY_SHA256, sha256_file
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.subsystems.lib import schema as schema_lib
from memoria_vault.runtime.subsystems.lib.inbox import write_work_prompt
from memoria_vault.runtime.time import now_iso
from memoria_vault.runtime.vaultio import (
    RETIRED_FRONTMATTER_FIELDS,
    apply_universal_concept_frontmatter,
    frontmatter_doc,
    iter_markdown,
    retired_frontmatter_field_errors,
    split_frontmatter,
    universal_concept_frontmatter_errors,
    write_bytes_durable,
    write_frontmatter_doc,
)

EVENT_DERIVED = "derived"
EVENT_OBSERVED_EXTERNAL_EDIT = "observed_external_edit"
EVENT_CHECK_FIRED = "check-fired"
EVENT_RESOLVED = "resolved"
TRACE_OUTPUT_EVENTS = frozenset({EVENT_DERIVED, EVENT_OBSERVED_EXTERNAL_EDIT})
SUPPORTED_PROMOTION_CHECKS = frozenset({"memoria-runtime"})
ARGUMENT_EDGE_TYPES = frozenset({"supports", "contradicts", "extends"})
TYPED_WIKILINK_RE = re.compile(r"\[\[([a-z][a-z0-9-]*)::([^\]\|]+)(?:\|[^\]]*)?\]\]")


@dataclass(frozen=True, slots=True)
class OperationContext:
    actor: str
    run_id: str
    request_id: str
    operation_id: str
    machine: str


_CONTEXT_EVENT_FIELDS = {
    "actor": "actor",
    "run_id": "run_id",
    "request_id": "request_id",
    "operation": "operation_id",
    "machine": "machine",
}


def operation_context_from_job(job: Mapping[str, Any], machine: str | None) -> OperationContext:
    """Build the validated provenance context for one claimed request."""
    envelope = job.get("request_envelope")
    if not isinstance(envelope, Mapping):
        raise ValueError("request envelope must be a mapping")

    actor_value = envelope.get("actor")
    actor = actor_value.strip() if isinstance(actor_value, str) else ""
    if actor not in state.ACTORS:
        raise ValueError(f"request envelope actor must be one of {sorted(state.ACTORS)}")

    request_id = _required_context_identifier(job, "job_id", "job request")
    envelope_request_id = _required_context_identifier(envelope, "request_id", "envelope request")
    if request_id != envelope_request_id:
        raise ValueError("job and envelope request identifiers must match")

    operation_key = "operation" if job.get("kind") == "trusted_write" else "operation_id"
    operation_id = _required_context_identifier(job, operation_key, "job operation")
    envelope_operation_id = _required_context_identifier(
        envelope, "operation_id", "envelope operation"
    )
    if operation_id != envelope_operation_id:
        raise ValueError("job and envelope operation identifiers must match")

    args = envelope.get("args", {})
    if not isinstance(args, Mapping):
        raise ValueError("request envelope args must be a mapping")
    if job.get("kind") == "operation":
        payload = job.get("payload", {})
        if not isinstance(payload, Mapping) or _canonical_json(dict(payload)) != _canonical_json(
            dict(args)
        ):
            raise ValueError("operation job payload must match request envelope args")
    run_value = args.get("run_id")
    if run_value is not None and not isinstance(run_value, str):
        raise ValueError("request envelope run_id must be a string")
    run_id = run_value.strip() if isinstance(run_value, str) else ""

    return OperationContext(
        actor=actor,
        run_id=run_id or request_id,
        request_id=request_id,
        operation_id=operation_id,
        machine=safe_filename(machine or platform.node() or "local"),
    )


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _required_context_identifier(source: Mapping[str, Any], key: str, label: str) -> str:
    value = source.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} identifier must be a nonblank string")
    return value.strip()


def operation_context_record(context: OperationContext) -> dict[str, str]:
    """Return the exact persisted representation of one built context."""
    return {
        "actor": context.actor,
        "run_id": context.run_id,
        "request_id": context.request_id,
        "operation_id": context.operation_id,
        "machine": context.machine,
    }


def validate_operation_context(vault: Path, context: OperationContext) -> Mapping[str, Any]:
    """Authenticate a request context against the worker-bound request record."""
    if context.actor not in state.ACTORS:
        raise ValueError(f"operation context actor must be one of {sorted(state.ACTORS)}")
    for field in ("run_id", "request_id", "operation_id", "machine"):
        value = getattr(context, field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"operation context {field} must be a nonblank string")
    persisted = state.request_row(vault, context.request_id)
    if persisted is None:
        raise ValueError(f"operation context request does not exist: {context.request_id}")
    if persisted["status"] != "running":
        raise ValueError("operation context request must be running")
    request = json.loads(persisted["job_json"])
    if request.get("bound_context") != operation_context_record(context):
        raise ValueError("operation context does not match the bound request context")
    return request


def normalize_promotion_checks(
    checks: Iterable[str] | None = None,
    *,
    default: str = "memoria-runtime",
) -> list[str]:
    """Return the checks the worker can enforce before marking a Concept checked."""
    raw_checks = [default] if checks is None else list(checks)
    normalized: list[str] = []
    for value in raw_checks:
        if not isinstance(value, str):
            raise ValueError("promotion checks must be strings")
        check = value.strip()
        if not check:
            raise ValueError("promotion checks must be non-empty")
        if check not in normalized:
            normalized.append(check)
    if not normalized:
        raise ValueError("promotion requires at least one check")
    unsupported = sorted(set(normalized) - SUPPORTED_PROMOTION_CHECKS)
    if unsupported:
        raise ValueError(f"unsupported promotion checks: {', '.join(unsupported)}")
    return normalized


def _decorate_context_event(event: Mapping[str, Any], context: OperationContext) -> dict[str, Any]:
    """Copy an event, reject conflicting reserved keys, and add context."""
    row = dict(event)
    for event_key, context_field in _CONTEXT_EVENT_FIELDS.items():
        expected = getattr(context, context_field)
        if event_key in row and row[event_key] != expected:
            raise ValueError(f"journal event {event_key} conflicts with operation context")
        row[event_key] = expected
    return row


def append_journal_event(
    vault: Path,
    event: Mapping[str, Any],
    *,
    context: OperationContext,
) -> dict[str, Any]:
    """Append one request event with provenance owned by its operation context."""
    request = validate_operation_context(vault, context)
    row = _decorate_context_event(event, context)
    envelope = request.get("request_envelope")
    provenance = envelope.get("provenance") if isinstance(envelope, Mapping) else None
    if not isinstance(provenance, Mapping):
        raise ValueError("journal request provenance must be a mapping")
    request_provenance = dict(provenance)
    if "request_provenance" in row and row["request_provenance"] != request_provenance:
        raise ValueError("journal event request_provenance conflicts with request envelope")
    row["request_provenance"] = request_provenance
    row.setdefault("timestamp", now_iso())
    _append_decorated_event(Path(vault), row, machine=context.machine)
    return row


def append_explicit_journal_event(
    vault: Path,
    event: Mapping[str, Any],
    *,
    actor: str,
    machine: str,
) -> dict[str, Any]:
    """Append an event created outside an operation envelope."""
    if not isinstance(actor, str) or actor not in state.ACTORS:
        raise ValueError(f"journal actor must be one of {sorted(state.ACTORS)}")
    if not isinstance(machine, str) or not machine.strip():
        raise ValueError("journal machine must be a nonblank string")
    machine_name = safe_filename(machine)
    row = dict(event)
    for key, expected in (("actor", actor), ("machine", machine_name)):
        if key in row and row[key] != expected:
            raise ValueError(f"journal event {key} conflicts with explicit provenance")
        row[key] = expected
    row.setdefault("timestamp", now_iso())
    _append_decorated_event(Path(vault), row, machine=machine_name)
    return row


def commit_writer_changes(
    vault: Path,
    message: str,
    paths: Iterable[str | Path],
    *,
    context: OperationContext,
    expected_sha256s: Mapping[str, str] | None = None,
) -> str:
    """Commit request-owned files plus the SQLite journal-head anchor."""
    validate_operation_context(vault, context)
    return _commit_writer_changes(vault, message, paths, expected_sha256s=expected_sha256s)


def commit_explicit_writer_changes(
    vault: Path,
    message: str,
    paths: Iterable[str | Path],
    *,
    actor: str,
    machine: str,
    expected_sha256s: Mapping[str, str] | None = None,
) -> str:
    """Commit files written outside an operation envelope with explicit provenance."""
    if actor not in state.ACTORS:
        raise ValueError(f"writer actor must be one of {sorted(state.ACTORS)}")
    if not isinstance(machine, str) or not machine.strip():
        raise ValueError("writer machine must be a nonblank string")
    safe_filename(machine)
    return _commit_writer_changes(vault, message, paths, expected_sha256s=expected_sha256s)


def _commit_writer_changes(
    vault: Path,
    message: str,
    paths: Iterable[str | Path],
    *,
    expected_sha256s: Mapping[str, str] | None = None,
) -> str:
    vault = Path(vault)
    output_rels = {_commit_relpath(vault, path) for path in paths}
    edge_rels = _write_edge_candidate_prompts(vault, output_rels)
    anchor = state.write_journal_head_anchor(vault)
    selected = sorted({*output_rels, *edge_rels, anchor})
    _git(vault, ["git", "add", "--", *selected])
    for raw_path, expected_hash in (expected_sha256s or {}).items():
        target = _commit_relpath(vault, raw_path)
        if target not in output_rels:
            raise ValueError(f"expected snapshot is not a committed output: {target}")
        if _staged_sha256(vault, target) != expected_hash:
            _unstage_path(vault, target)
            raise RuntimeError(f"file changed while staging observed edit: {target}")
    _git(vault, ["git", "commit", "-m", message, "--", *selected])
    commit = _git(vault, ["git", "rev-parse", "HEAD"])
    for rel in sorted(output_rels):
        state.mark_materialized(vault, rel, commit=commit)
    _refresh_committed_file_baselines(
        vault,
        output_rels,
        expected_sha256s=expected_sha256s,
    )
    return commit


def _staged_sha256(vault: Path, target: str) -> str:
    proc = subprocess.run(
        ["git", "show", f":{target}"],
        cwd=vault,
        check=False,
        capture_output=True,
    )
    if proc.returncode:
        return ""
    return "sha256:" + hashlib.sha256(proc.stdout).hexdigest()


def _unstage_path(vault: Path, target: str) -> None:
    exists_at_head = (
        subprocess.run(
            ["git", "cat-file", "-e", f"HEAD:{target}"],
            cwd=vault,
            check=False,
            capture_output=True,
        ).returncode
        == 0
    )
    if exists_at_head:
        _git(vault, ["git", "restore", "--staged", "--", target])
    else:
        _git(vault, ["git", "rm", "--cached", "--ignore-unmatch", "--", target])


def _refresh_committed_file_baselines(
    vault: Path,
    output_rels: Iterable[str],
    *,
    expected_sha256s: Mapping[str, str] | None,
) -> None:
    if not (vault / ".memoria/schemas/folders.yaml").is_file():
        return
    contract = _load_contract(vault, None)
    expected = {
        _commit_relpath(vault, path): output_hash
        for path, output_hash in (expected_sha256s or {}).items()
    }
    known = _known_current_hashes(vault)
    for target in sorted(set(output_rels)):
        if not target.endswith(".md") or not _is_bundle_target(contract, target):
            continue
        proc = subprocess.run(
            ["git", "show", f"HEAD:{target}"],
            cwd=vault,
            check=False,
            capture_output=True,
        )
        if proc.returncode:
            continue
        committed_hash = "sha256:" + hashlib.sha256(proc.stdout).hexdigest()
        if expected.get(target) != committed_hash and known.get(target) != committed_hash:
            continue
        text = proc.stdout.decode("utf-8")
        frontmatter, _body = split_frontmatter(text)
        state.upsert_file_baseline(
            vault,
            target,
            human_sha256=committed_hash,
            restriction_keys=_restriction_keys(frontmatter),
        )


def _write_edge_candidate_prompts(vault: Path, output_rels: set[str]) -> list[str]:
    prompts: list[str] = []
    for source_rel in sorted(output_rels):
        if not source_rel.endswith(".md"):
            continue
        source_path = vault / source_rel
        if not source_path.is_file():
            continue
        frontmatter, body = split_frontmatter(source_path.read_text(encoding="utf-8"))
        if frontmatter.get("type") not in {"note", "digest", "hub", "project"}:
            continue
        title = str(frontmatter.get("title") or Path(source_rel).stem)
        for match in TYPED_WIKILINK_RE.finditer(body):
            edge_type = match.group(1).strip().lower()
            target = match.group(2).strip()
            if edge_type not in ARGUMENT_EDGE_TYPES or not target:
                continue
            safe_title = neutralize_untrusted_markdown_fragment(title)
            safe_target = neutralize_untrusted_markdown_fragment(target)
            # ponytail: unchecked prompt per explicit edge; add DB edge rows only with act tuning.
            prompt = write_work_prompt(
                vault,
                f"Review extracted {edge_type} link",
                (
                    f"Review {markdown_code_span(edge_type)} from "
                    f"{markdown_code_span(source_rel)} to "
                    f"{markdown_code_span(safe_target)}."
                ),
                (
                    f"{markdown_code_span(safe_title)} contains explicit typed link "
                    f"{markdown_code_span(f'[[{edge_type}::{safe_target}]]')}. "
                    "It is an unchecked candidate; curate it with `memoria link` if correct."
                ),
                "edge-extraction",
                target=source_rel,
                posture="co-pi",
                dedupe_slug=f"edge-candidate-{source_rel}-{edge_type}-{target}",
                prompt_kind="edge-candidate",
            )
            if prompt:
                prompts.append(prompt.relative_to(vault).as_posix())
    return prompts


def observe_pi_edit(
    vault: Path,
    target_path: str,
    prior_sha256: str,
    *,
    inputs: Iterable[str | dict[str, Any]] = (),
    operation: str = "pi-edit",
    run_id: str | None = None,
    machine: str,
    schemas_dir: Path | None = None,
) -> dict[str, Any]:
    """Backfill provenance for a direct PI edit and make it ineligible until checked."""
    if not isinstance(machine, str) or not machine.strip():
        raise ValueError("PI edit observation machine must be a nonblank string")
    vault = Path(vault)
    target = _target_path(target_path)
    contract = _load_contract(vault, schemas_dir)
    _bundle_for_target(contract, target)

    path = vault / target
    frontmatter, _body = split_frontmatter(path.read_text(encoding="utf-8"))
    _validate_concept(contract, target, frontmatter, strict_writer=False)

    output_sha256 = sha256_file(path)
    state.record_observed_file_edit(
        vault,
        output_id=target,
        concept_type=str(frontmatter["type"]),
        output_sha256=output_sha256,
    )

    event = {
        "event": EVENT_OBSERVED_EXTERNAL_EDIT,
        "timestamp": now_iso(),
        "output_id": target,
        "output_sha256": output_sha256,
        "inputs": [
            *_input_rows(inputs),
            {"id": target, "sha256": prior_sha256, "role": "prior-head"},
        ],
        "operation": operation,
        "actor": "pi",
    }
    if run_id:
        event["run_id"] = run_id
    return append_explicit_journal_event(vault, event, actor="pi", machine=machine)


def observe_pi_edit_from_head(
    vault: Path,
    target_path: str,
    *,
    operation: str = "pi-edit",
    run_id: str | None = None,
    machine: str,
    schemas_dir: Path | None = None,
) -> dict[str, Any]:
    """Backfill a PI edit using the prior git HEAD hash and prior derivation inputs."""
    vault = Path(vault)
    target = _target_path(target_path)
    return observe_pi_edit(
        vault,
        target,
        _head_sha256(vault, target),
        inputs=_latest_derived_inputs(vault, target),
        operation=operation,
        run_id=run_id,
        machine=machine,
        schemas_dir=schemas_dir,
    )


def observe_pi_edits_from_status(
    vault: Path,
    *,
    context: OperationContext,
    paths: Iterable[str] | None = None,
    schemas_dir: Path | None = None,
) -> dict[str, Any]:
    """Observe PI edits while preserving the enclosing integrity request context."""
    validate_operation_context(vault, context)
    return _observe_pi_edits_from_status(
        vault,
        context=context,
        paths=paths,
        schemas_dir=schemas_dir,
        explicit_actor="",
        explicit_machine="",
    )


def observe_pi_edits_explicit_from_status(
    vault: Path,
    *,
    actor: str,
    machine: str,
    paths: Iterable[str] | None = None,
    schemas_dir: Path | None = None,
) -> dict[str, Any]:
    """Observe PI edits from an explicit integrity scan outside an envelope."""
    if actor != "integrity":
        raise ValueError("explicit PI edit scan actor must be integrity")
    if not isinstance(machine, str) or not machine.strip():
        raise ValueError("explicit PI edit scan machine must be a nonblank string")
    return _observe_pi_edits_from_status(
        vault,
        context=None,
        paths=paths,
        schemas_dir=schemas_dir,
        explicit_actor=actor,
        explicit_machine=machine,
    )


def _observe_pi_edits_from_status(
    vault: Path,
    *,
    context: OperationContext | None,
    paths: Iterable[str] | None,
    schemas_dir: Path | None,
    explicit_actor: str,
    explicit_machine: str,
) -> dict[str, Any]:
    vault = Path(vault)
    contract = _load_contract(vault, schemas_dir)
    targets = _pi_edit_targets(vault, contract, paths)
    for target in targets:
        _validate_pi_edit_target(vault, contract, target)
    _seed_missing_file_baselines(vault, contract, excluded=targets)

    observed = []
    findings = []
    for target in targets:
        baseline = state.file_baseline(vault, target)
        event = observe_pi_edit_from_head(
            vault,
            target,
            operation=context.operation_id if context else "observe-pi-edits",
            run_id=context.run_id if context else None,
            machine=context.machine if context else explicit_machine,
            schemas_dir=schemas_dir,
        )
        path = vault / target
        current_hash = sha256_file(path)
        if event["output_sha256"] != current_hash:
            raise RuntimeError(f"file changed while observing edit: {target}")
        frontmatter, _body = split_frontmatter(path.read_text(encoding="utf-8"))
        if sha256_file(path) != current_hash:
            raise RuntimeError(f"file changed while observing edit: {target}")
        if baseline is not None and baseline["human_sha256"] != current_hash:
            findings.append(
                {
                    "kind": "foreign-edit",
                    "event": EVENT_OBSERVED_EXTERNAL_EDIT,
                    "route": "ask",
                    "subject_id": target,
                    "prior_human_sha256": baseline["human_sha256"],
                    "current_human_sha256": current_hash,
                }
            )
        observed.append(event)
        restriction_keys = _restriction_keys(frontmatter)
        if baseline is not None:
            for key in sorted(set(baseline["restriction_keys"]) - set(restriction_keys)):
                findings.append(
                    {
                        "kind": "restriction-key-removed",
                        "event": EVENT_OBSERVED_EXTERNAL_EDIT,
                        "route": "ask",
                        "subject_id": target,
                        "key": key,
                    }
                )
    if observed:
        from memoria_vault.runtime.integrity import (
            propagate_scan_demotion,
            propagate_scan_demotion_explicit,
        )

        for event in observed:
            output_id = str(event["output_id"])
            if context:
                propagate_scan_demotion(
                    vault,
                    output_id,
                    reason=f"scan observed unchecked edit: {output_id}",
                    context=context,
                )
            else:
                propagate_scan_demotion_explicit(
                    vault,
                    output_id,
                    reason=f"scan observed unchecked edit: {output_id}",
                    actor=explicit_actor,
                    machine=explicit_machine,
                )
    commit = ""
    if observed:
        if context is None:
            commit = commit_explicit_writer_changes(
                vault,
                "observe PI edits",
                targets,
                actor=explicit_actor,
                machine=explicit_machine,
                expected_sha256s={
                    str(event["output_id"]): str(event["output_sha256"]) for event in observed
                },
            )
        else:
            commit = commit_writer_changes(
                vault,
                "observe PI edits",
                targets,
                context=context,
                expected_sha256s={
                    str(event["output_id"]): str(event["output_sha256"]) for event in observed
                },
            )
    return {"paths": targets, "observed": observed, "findings": findings, "commit": commit}


def rebuild_concept_mirror_from_files(
    vault: Path,
    *,
    schemas_dir: Path | None = None,
) -> dict[str, int]:
    """Rebuild file Concept mirror rows without trusting file verdict fields."""
    vault = Path(vault)
    contract = _load_contract(vault, schemas_dir)
    rows: list[dict[str, str]] = []
    for root in contract["folders"].get("bundle_roots") or ():
        base = vault / str(root).strip("/")
        if not base.exists():
            continue
        for path in iter_markdown(base, skip_dirs=frozenset()):
            target = path.relative_to(vault).as_posix()
            frontmatter, _body = split_frontmatter(path.read_text(encoding="utf-8"))
            try:
                _validate_concept(contract, target, frontmatter, strict_writer=False)
            except ValueError:
                continue
            rows.append({"concept_id": target, "concept_type": str(frontmatter["type"])})
    return state.rebuild_file_concept_mirror(vault, rows)


def mark_checked(
    vault: Path,
    target_path: str,
    *,
    context: OperationContext,
    check: str = "memoria-runtime",
    checks: Iterable[str] | None = None,
    schemas_dir: Path | None = None,
) -> dict[str, Any]:
    """Mark an existing live Concept checked after the worker's checks pass."""
    validate_operation_context(vault, context)
    vault = Path(vault)
    target = _target_path(target_path)
    promotion_checks = normalize_promotion_checks([check] if checks is None else checks)
    contract = _load_contract(vault, schemas_dir)
    _bundle_for_target(contract, target)
    output_path = vault / target
    frontmatter, body = split_frontmatter(output_path.read_text(encoding="utf-8"))
    return _write_checked(
        vault,
        target,
        output_path,
        frontmatter,
        body,
        promotion_checks,
        context,
        contract,
        allow_retired_input=True,
    )


def stage_concept(
    vault: Path,
    target_path: str,
    content: str,
    *,
    context: OperationContext,
    inputs: Iterable[str | dict[str, Any]] = (),
    schemas_dir: Path | None = None,
) -> dict[str, Any]:
    """Validate a machine Concept request, stage it unchecked, and journal derivation."""
    validate_operation_context(vault, context)
    vault = Path(vault)
    target = _target_path(target_path)
    contract = _load_contract(vault, schemas_dir)
    _bundle_for_target(contract, target)

    frontmatter, body = split_frontmatter(content)
    _validate_concept(contract, target, frontmatter)

    staged_path = _staged_path(vault, target)
    write_frontmatter_doc(staged_path, frontmatter, body, create_parent=True)
    event = {
        "event": EVENT_DERIVED,
        "timestamp": now_iso(),
        "output_id": target,
        "staging_id": _rel(vault, staged_path),
        "output_sha256": sha256_file(staged_path),
        "inputs": _input_rows(inputs),
    }
    event = append_journal_event(vault, event, context=context)
    state.record_file_output(
        vault,
        output_id=target,
        concept_type=str(frontmatter["type"]),
        check_status="unchecked",
        output_sha256=event["output_sha256"],
        staging_id=event["staging_id"],
        payload_text=staged_path.read_text(encoding="utf-8"),
        context=context,
        inputs=event["inputs"],
    )
    return event


def promote_checked(
    vault: Path,
    target_path: str,
    *,
    context: OperationContext,
    check: str = "memoria-runtime",
    checks: Iterable[str] | None = None,
    schemas_dir: Path | None = None,
) -> dict[str, Any]:
    """Promote a staged Concept into its bundle only after it validates as checked."""
    validate_operation_context(vault, context)
    vault = Path(vault)
    target = _target_path(target_path)
    promotion_checks = normalize_promotion_checks([check] if checks is None else checks)
    contract = _load_contract(vault, schemas_dir)
    _bundle_for_target(contract, target)

    staged_path = _staged_path(vault, target)
    if not staged_path.is_file():
        raise FileNotFoundError(staged_path)
    frontmatter, body = split_frontmatter(staged_path.read_text(encoding="utf-8"))
    output_path = vault / target
    event = _write_checked(
        vault,
        target,
        output_path,
        frontmatter,
        body,
        promotion_checks,
        context,
        contract,
    )
    staged_path.unlink()
    return event


def materialize_unchecked(
    vault: Path, target_path: str, *, context: OperationContext
) -> dict[str, Any]:
    """Move a staged unchecked Concept into its bundle without promotion."""
    validate_operation_context(vault, context)
    vault = Path(vault)
    target = _target_path(target_path)
    staged_path = _staged_path(vault, target)
    if not staged_path.is_file():
        raise FileNotFoundError(staged_path)
    frontmatter, body = split_frontmatter(staged_path.read_text(encoding="utf-8"))
    output_path = vault / target
    write_frontmatter_doc(output_path, frontmatter, body, create_parent=True)
    staged_path.unlink()
    return {"output_id": target, "output_sha256": sha256_file(output_path)}


def quarantine_untraced(
    vault: Path,
    paths: Iterable[str],
    *,
    context: OperationContext,
    reason: str = "foreign-untraced",
) -> list[dict[str, Any]]:
    """Move explicit bundle files whose current hash is not journal-backed."""
    validate_operation_context(vault, context)
    vault = Path(vault)
    known = _known_current_hashes(vault)
    events: list[dict[str, Any]] = []
    contract = _load_contract(vault, None)
    for raw_path in paths:
        target = normalize_path(raw_path)
        source_path = vault / target
        if not source_path.is_file():
            continue
        original_sha = sha256_file(source_path)
        if known.get(target) == original_sha:
            continue

        concept_type = _concept_type_for_quarantine(vault, contract, target)
        quarantined_sha = original_sha
        quarantine_path = _unique_quarantine_path(vault / ".memoria/quarantine" / target)
        quarantine_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_path), quarantine_path)
        if concept_type:
            state.record_observed_file_edit(
                vault,
                output_id=target,
                concept_type=concept_type,
                output_sha256=quarantined_sha,
            )
            state.set_concept_verdict(vault, target, "quarantined")
        event = {
            "event": EVENT_CHECK_FIRED,
            "timestamp": now_iso(),
            "check": "trace-integrity",
            "status": "failed",
            "reason": reason,
            "target_id": target,
            "target_sha256": original_sha,
            "quarantined_id": _rel(vault, quarantine_path),
            "output_sha256": quarantined_sha,
        }
        events.append(append_journal_event(vault, event, context=context))
    return events


def _concept_type_for_quarantine(vault: Path, contract: dict[str, Any], target: str) -> str:
    if not target.endswith(".md") or not _is_bundle_target(contract, target):
        return ""
    frontmatter, _body = split_frontmatter((vault / target).read_text(encoding="utf-8"))
    concept_type = str(frontmatter.get("type") or "")
    return concept_type if concept_type in contract["types"] else ""


def quarantine_untraced_from_status(
    vault: Path,
    *,
    context: OperationContext,
    reason: str = "foreign-untraced",
    schemas_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Quarantine untraced bundle files reported by git status."""
    validate_operation_context(vault, context)
    vault = Path(vault)
    contract = _load_contract(vault, schemas_dir)
    return quarantine_untraced(
        vault,
        _git_status_paths(vault, contract),
        context=context,
        reason=reason,
    )


def rebuild_trace_state(vault: Path) -> dict[str, dict[str, Any]]:
    """Rebuild the latest known output/check state from the authoritative event log."""
    outputs: dict[str, dict[str, Any]] = {}
    for event in state.read_event_log(
        Path(vault),
        event_types=(*TRACE_OUTPUT_EVENTS, EVENT_CHECK_FIRED),
    ):
        if event.get("event") in TRACE_OUTPUT_EVENTS:
            output_id = event.get("output_id")
        elif event.get("event") == EVENT_CHECK_FIRED:
            output_id = event.get("target_id")
        else:
            continue
        if isinstance(output_id, str):
            outputs[output_id] = event
    return outputs


def _load_contract(vault: Path, schemas_dir: Path | None) -> dict[str, Any]:
    root = Path(schemas_dir) if schemas_dir else vault / ".memoria/schemas"
    folders = yaml.safe_load((root / "folders.yaml").read_text(encoding="utf-8")) or {}
    types: dict[str, dict[str, Any]] = {}
    for path in sorted((root / "types").glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if data.get("type"):
            types[str(data["type"])] = data
    return {"folders": folders, "types": types}


def _target_path(path: str) -> str:
    target = normalize_path(path)
    if not target.endswith(".md"):
        raise ValueError(f"Concept path must be markdown: {path!r}")
    if target.startswith(".memoria/"):
        raise ValueError(f"Concept path must be in a bundle: {path!r}")
    return target


def _bundle_for_target(contract: dict[str, Any], target: str) -> str:
    for root in contract["folders"].get("bundle_roots") or ():
        root = str(root).strip("/")
        if target == root or target.startswith(root + "/"):
            return root
    raise ValueError(f"target is outside bundle roots: {target}")


def _is_bundle_target(contract: dict[str, Any], target: str) -> bool:
    try:
        _bundle_for_target(contract, target)
    except ValueError:
        return False
    return True


def _pi_edit_targets(
    vault: Path,
    contract: dict[str, Any],
    paths: Iterable[str] | None,
) -> list[str]:
    known = _known_current_hashes(vault)
    dirty_targets = set(_git_status_paths(vault, contract))
    raw_paths = (
        list(paths)
        if paths is not None
        else [
            *dirty_targets,
            *(path.relative_to(vault).as_posix() for path in iter_markdown(vault)),
        ]
    )
    targets: list[str] = []
    for raw_path in raw_paths:
        try:
            target = _target_path(raw_path)
        except ValueError:
            continue
        path = vault / target
        if not path.is_file() or not _is_bundle_target(contract, target):
            continue
        current_hash = sha256_file(path)
        baseline = state.file_baseline(vault, target)
        if baseline is not None:
            if baseline["human_sha256"] != current_hash:
                targets.append(target)
            continue
        if target in dirty_targets and known.get(target) != current_hash:
            targets.append(target)
    return sorted(set(targets))


def _seed_missing_file_baselines(
    vault: Path,
    contract: dict[str, Any],
    *,
    excluded: Iterable[str],
) -> None:
    excluded_targets = set(excluded)
    dirty_targets = set(_git_status_paths(vault, contract))
    for path in iter_markdown(vault):
        target = path.relative_to(vault).as_posix()
        if (
            target in excluded_targets
            or target in dirty_targets
            or not _is_bundle_target(contract, target)
            or state.file_baseline(vault, target) is not None
        ):
            continue
        frontmatter, _body = split_frontmatter(path.read_text(encoding="utf-8"))
        _validate_concept(contract, target, frontmatter, strict_writer=False)
        state.upsert_file_baseline(
            vault,
            target,
            human_sha256=sha256_file(path),
            restriction_keys=_restriction_keys(frontmatter),
        )


def _git_status_paths(vault: Path, contract: dict[str, Any]) -> list[str]:
    roots = [str(root).strip("/") for root in contract["folders"].get("bundle_roots") or ()]
    if not roots:
        return []
    proc = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", *roots],
        cwd=vault,
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.returncode:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"git status failed: {detail}")
    paths: list[str] = []
    for line in proc.stdout.splitlines():
        if len(line) < 4 or "D" in line[:2]:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.rsplit(" -> ", 1)[1]
        paths.append(path)
    return paths


def _validate_pi_edit_target(vault: Path, contract: dict[str, Any], target: str) -> None:
    frontmatter, _body = split_frontmatter((vault / target).read_text(encoding="utf-8"))
    _validate_concept(contract, target, frontmatter, strict_writer=False)


def _restriction_keys(frontmatter: dict[str, Any]) -> list[str]:
    return [key for key in ("superseded", "local-only") if frontmatter.get(key) is True]


def _staged_path(vault: Path, target: str) -> Path:
    return vault / ".memoria/staging" / target


def _validate_concept(
    contract: dict[str, Any],
    target: str,
    frontmatter: dict[str, Any],
    *,
    strict_writer: bool = True,
) -> None:
    apply_universal_concept_frontmatter(frontmatter, target)
    if strict_writer:
        retired = retired_frontmatter_field_errors(frontmatter)
        if retired:
            raise ValueError("; ".join(retired))
    concept_type = str(frontmatter.get("type") or "")
    schema = contract["types"].get(concept_type)
    if not schema:
        raise ValueError(f"unknown Concept type: {concept_type or '<missing>'}")
    home = str(contract["folders"].get("homes", {}).get(concept_type) or "").strip("/")
    if not home or not target.startswith(home + "/"):
        raise ValueError(f"{concept_type} must live under {home or '<missing home>'}: {target}")
    if not strict_writer:
        return
    errors = schema_lib.validate_frontmatter(frontmatter, schema)
    if errors:
        raise ValueError("; ".join(errors))
    for error in universal_concept_frontmatter_errors(frontmatter, target):
        raise ValueError(error)


def _write_checked(
    vault: Path,
    target: str,
    output_path: Path,
    frontmatter: dict[str, Any],
    body: str,
    checks: Iterable[str],
    context: OperationContext,
    contract: dict[str, Any],
    *,
    allow_retired_input: bool = False,
) -> dict[str, Any]:
    promotion_checks = normalize_promotion_checks(checks)
    if allow_retired_input:
        for field in RETIRED_FRONTMATTER_FIELDS:
            frontmatter.pop(field, None)
    _validate_concept(contract, target, frontmatter)
    payload_text = frontmatter_doc(frontmatter, body)
    output_sha256 = "sha256:" + hashlib.sha256(payload_text.encode("utf-8")).hexdigest()
    events = []
    for check in promotion_checks:
        event = {
            "event": EVENT_CHECK_FIRED,
            "timestamp": now_iso(),
            "check": check,
            "status": "passed",
            "target_id": target,
            "output_sha256": output_sha256,
        }
        events.append(append_journal_event(vault, event, context=context))
    state.mark_checked(vault, target, output_sha256, payload_text)
    write_frontmatter_doc(output_path, frontmatter, body, create_parent=True)
    return events[0]


def _input_rows(inputs: Iterable[str | dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in inputs:
        if isinstance(item, dict):
            rows.append(dict(item))
        else:
            rows.append({"id": normalize_path(str(item))})
    return rows


def _append_decorated_event(vault: Path, event: dict[str, Any], *, machine: str) -> None:
    with state.workspace_lock(vault):
        if _has_unterminated_journal_export_tail(vault):
            reconcile_journal_export(vault)
        state._append_journal_row(vault, event, machine=machine)
        state.write_journal_head_anchor(vault)
        append_jsonl(_journal_path(vault, machine), [event])


def _journal_path(vault: Path, machine: str) -> Path:
    return vault / ".memoria/journal" / f"{machine}.jsonl"


def _iter_journal_exports(vault: Path) -> Iterable[tuple[str, dict[str, Any]]]:
    for path in sorted((vault / ".memoria/journal").glob("*.jsonl")):
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise ValueError(f"journal JSONL export is unreadable: {path.name}: {exc}") from exc
        raw = state.journal_export_complete_prefix(raw)
        machine = path.stem
        for line_number, raw_line in enumerate(raw.splitlines(), start=1):
            try:
                line = raw_line.decode("utf-8").strip()
            except UnicodeDecodeError as exc:
                raise ValueError(f"invalid UTF-8 in {path.name} at line {line_number}") from exc
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL in {path.name} at line {line_number}") from exc
            if not isinstance(event, dict):
                raise ValueError(f"invalid JSONL object in {path.name} at line {line_number}")
            if event.get("machine") != machine:
                raise ValueError(f"JSONL machine mismatch in {path.name} at line {line_number}")
            yield path.stem, event


def reconcile_journal_export(vault: Path) -> int:
    """Re-emit authoritative rows missing from per-machine JSONL exports."""
    vault = Path(vault)
    with state.workspace_lock(vault):
        exported = Counter(
            (machine, _canonical_journal_event(event))
            for machine, event in _iter_journal_exports(vault)
        )
        missing: list[tuple[str, dict[str, Any]]] = []
        with state.connect(vault) as conn:
            rows = conn.execute(
                "SELECT machine, payload_json FROM event_log ORDER BY event_id"
            ).fetchall()
        for row in rows:
            machine = str(row["machine"])
            event = json.loads(str(row["payload_json"]))
            if not isinstance(event, dict):
                raise ValueError("event_log payload must be a JSON object")
            if event.get("machine") != machine:
                raise ValueError("event_log payload machine does not match its row")
            key = (machine, _canonical_journal_event(event))
            if exported[key]:
                exported[key] -= 1
            else:
                missing.append((machine, event))
        extra_count = sum(exported.values())
        if extra_count:
            raise ValueError(
                f"journal JSONL export contains {extra_count} row(s) absent from event_log"
            )
        _normalize_journal_export_tails(vault)
        for machine, event in missing:
            append_jsonl(_journal_path(vault, machine), [event])
        return len(missing)


def _canonical_journal_event(event: dict[str, Any]) -> str:
    return json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _normalize_journal_export_tails(vault: Path) -> bool:
    normalized = False
    for path in sorted((vault / ".memoria/journal").glob("*.jsonl")):
        normalized = _truncate_partial_jsonl_tail(path) or normalized
    return normalized


def _has_unterminated_journal_export_tail(vault: Path) -> bool:
    for path in sorted((vault / ".memoria/journal").glob("*.jsonl")):
        try:
            data = path.read_bytes()
        except FileNotFoundError:
            continue
        if data and not data.endswith((b"\n", b"\r")):
            return True
    return False


def _truncate_partial_jsonl_tail(path: Path) -> bool:
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return False
    if not data or data.endswith((b"\n", b"\r")):
        return False
    write_bytes_durable(path, state.journal_export_complete_prefix(data))
    return True


def _known_current_hashes(vault: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for target, event in rebuild_trace_state(vault).items():
        output_sha = event.get("output_sha256")
        if isinstance(output_sha, str):
            hashes[target] = output_sha
    return hashes


def _latest_derived_inputs(vault: Path, target: str) -> list[dict[str, Any]]:
    inputs: list[dict[str, Any]] = []
    for event in state.read_event_log(vault, event_types=TRACE_OUTPUT_EVENTS):
        if event.get("output_id") == target:
            inputs = _input_rows(event.get("inputs") or [])
    return inputs


def _head_sha256(vault: Path, target: str) -> str:
    proc = subprocess.run(
        ["git", "show", f"HEAD:{target}"],
        cwd=vault,
        check=False,
        capture_output=True,
    )
    if proc.returncode:
        return EMPTY_SHA256
    import hashlib

    return "sha256:" + hashlib.sha256(proc.stdout).hexdigest()


def _unique_quarantine_path(path: Path) -> Path:
    candidate = path
    index = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        index += 1
    return candidate


def _commit_relpath(vault: Path, path: str | Path) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate.relative_to(vault).as_posix()
    return normalize_path(str(path))


def _git(vault: Path, args: list[str]) -> str:
    proc = subprocess.run(
        args,
        cwd=vault,
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.returncode:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"{' '.join(args)} failed: {detail}")
    return proc.stdout.strip()


def _rel(vault: Path, path: Path) -> str:
    return path.relative_to(vault).as_posix()
