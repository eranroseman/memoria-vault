"""Trusted-writer primitives for staging, promotion, and trace scans."""

from __future__ import annotations

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

from memoria_vault.runtime import state
from memoria_vault.runtime.content_security import (
    markdown_code_span,
    neutralize_untrusted_markdown,
    neutralize_untrusted_markdown_fragment,
)
from memoria_vault.runtime.jsonl import append_jsonl
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.audit import EMPTY_SHA256, sha256_bytes, sha256_file
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.subsystems.lib import schema as schema_lib
from memoria_vault.runtime.subsystems.lib.edges import parse_typed_wikilinks
from memoria_vault.runtime.subsystems.lib.inbox import write_finding, write_work_prompt
from memoria_vault.runtime.time import now_iso
from memoria_vault.runtime.vaultio import (
    apply_universal_concept_frontmatter,
    frontmatter_doc,
    is_ulid,
    iter_markdown,
    okf_actor,
    okf_verified_actor,
    read_frontmatter,
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


@dataclass(frozen=True, slots=True)
class OperationContext:
    """Provenance for one claimed request: who authorized it, and who wrote it.

    `actor` is *authority* — which operations the request may run. It is not
    *authorship*: a transport door can hold PI authority (loopback bind, per-boot
    bearer token) while the body it posts was composed by a machine. Doors set
    `machine_authored` so the two stay separable; see `body_is_pi_authored`.

    `agent_identity` is request provenance, not authority: which named agent
    (if any) composed the body, carried through from the request envelope's
    `provenance["agent_identity"]` for OKF actor rendering (`okf_actor`). It
    defaults to "" for contexts built without that provenance in scope.
    """

    actor: str
    run_id: str
    request_id: str
    operation_id: str
    machine: str
    machine_authored: bool = False
    agent_identity: str = ""

    @property
    def body_is_pi_authored(self) -> bool:
        """Whether Concept bodies on this request may be written verbatim.

        Only the PI's own hand earns that: PI authority *and* PI authorship.
        Every other combination — including a machine-authored body arriving
        through a door that carries PI authority — is neutralized before it is
        written, because content security follows authorship, not authority.
        """
        return self.actor == "pi" and not self.machine_authored


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

    machine_authored = envelope.get("machine_authored", False)
    if not isinstance(machine_authored, bool):
        raise ValueError("request envelope machine_authored must be a boolean")

    provenance = envelope.get("provenance")
    agent_identity_value = (
        provenance.get("agent_identity") if isinstance(provenance, Mapping) else None
    )
    agent_identity = agent_identity_value.strip() if isinstance(agent_identity_value, str) else ""

    return OperationContext(
        actor=actor,
        run_id=run_id or request_id,
        request_id=request_id,
        operation_id=operation_id,
        machine=safe_filename(machine or platform.node() or "local"),
        machine_authored=machine_authored,
        agent_identity=agent_identity,
    )


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _required_context_identifier(source: Mapping[str, Any], key: str, label: str) -> str:
    value = source.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} identifier must be a nonblank string")
    return value.strip()


def operation_context_record(context: OperationContext) -> dict[str, Any]:
    """Return the exact persisted representation of one built context.

    `machine_authored` is part of the bound record for the same reason `actor`
    is: it gates a security transform, so it has to be authenticated against the
    persisted request rather than asserted by whoever holds the context object.
    `agent_identity` is bound for the narrower reason that it is written into
    files as OKF provenance: an unbound field would let a caller sign its
    output with any producer name it liked.
    """
    return {
        "actor": context.actor,
        "run_id": context.run_id,
        "request_id": context.request_id,
        "operation_id": context.operation_id,
        "machine": context.machine,
        "machine_authored": context.machine_authored,
        "agent_identity": context.agent_identity,
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
    row = _prepare_context_journal_event(event, context=context, request=request)
    _append_decorated_event(Path(vault), row, machine=context.machine)
    return row


def _prepare_context_journal_event(
    event: Mapping[str, Any],
    *,
    context: OperationContext,
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Decorate one already-validated request event for authoritative storage."""
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
    return row


def rebuild_evidence_sets_and_journal_mints(
    vault: Path,
    *,
    run_id: str,
    context: OperationContext,
) -> dict[str, Any]:
    """Atomically rebuild active evidence sets and journal first-time bindings."""
    vault = Path(vault)
    request = validate_operation_context(vault, context)
    events: list[dict[str, Any]] = []
    with state.workspace_lock(vault):
        if _has_unterminated_journal_export_tail(vault):
            reconcile_journal_export(vault)
        marker_rows, duplicate_ids = state._evidence_marker_rows(vault, run_id=run_id)
        with state.connect(vault) as conn:
            conn.execute("BEGIN IMMEDIATE")
            rebuild = state._replace_evidence_sets_conn(conn, marker_rows)
            if duplicate_ids:
                rebuild["duplicate_ids"] = duplicate_ids
            for minted in rebuild.get("minted", []):
                event = _prepare_context_journal_event(
                    {
                        "event": "evidence-minted",
                        "evidence_id": minted["evidence_id"],
                        "block_ref": minted["block_ref"],
                        "block_text_sha256": minted["block_text_sha256"],
                    },
                    context=context,
                    request=request,
                )
                state._insert_journal_row_conn(conn, event, machine=context.machine)
                events.append(event)
        if events:
            state.write_journal_head_anchor(vault)
            append_jsonl(_journal_path(vault, context.machine), events)
    return rebuild


def append_explicit_event_batch(
    vault: Path,
    events: Iterable[Mapping[str, Any]],
    *,
    actor: str,
    machine: str,
) -> list[dict[str, Any]]:
    """Append explicit-provenance events as one authoritative journal batch."""
    if not isinstance(actor, str) or actor not in state.ACTORS:
        raise ValueError(f"journal actor must be one of {sorted(state.ACTORS)}")
    if not isinstance(machine, str) or not machine.strip():
        raise ValueError("journal machine must be a nonblank string")
    machine_name = safe_filename(machine)
    rows = [
        _prepare_explicit_journal_event(event, actor=actor, machine_name=machine_name)
        for event in events
    ]
    if not rows:
        return []
    vault = Path(vault)
    with state.workspace_lock(vault):
        if _has_unterminated_journal_export_tail(vault):
            reconcile_journal_export(vault)
        with state.connect(vault) as conn:
            conn.execute("BEGIN IMMEDIATE")
            for row in rows:
                state._insert_journal_row_conn(conn, row, machine=machine_name)
        state.write_journal_head_anchor(vault)
        append_jsonl(_journal_path(vault, machine_name), rows)
    return rows


def _prepare_explicit_journal_event(
    event: Mapping[str, Any], *, actor: str, machine_name: str
) -> dict[str, Any]:
    """Decorate one explicit-provenance event before batch persistence."""
    row = dict(event)
    for key, expected in (("actor", actor), ("machine", machine_name)):
        if key in row and row[key] != expected:
            raise ValueError(f"journal event {key} conflicts with explicit provenance")
        row[key] = expected
    row.setdefault("timestamp", now_iso())
    return row


def append_explicit_journal_event(
    vault: Path,
    event: Mapping[str, Any],
    *,
    actor: str,
    machine: str,
) -> dict[str, Any]:
    """Append one event created outside an operation envelope."""
    (row,) = append_explicit_event_batch(vault, [event], actor=actor, machine=machine)
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
    return sha256_bytes(proc.stdout)


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
        for edge_type, target in parse_typed_wikilinks(body):
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


def _foreign_edit_finding(target: str, prior: str, current: str) -> dict[str, str]:
    return {
        "kind": "foreign-edit",
        "event": EVENT_OBSERVED_EXTERNAL_EDIT,
        "route": "ask",
        "subject_id": target,
        "prior_human_sha256": prior,
        "current_human_sha256": current,
    }


def _restriction_key_removed_finding(target: str, key: str) -> dict[str, str]:
    return {
        "kind": "restriction-key-removed",
        "event": EVENT_OBSERVED_EXTERNAL_EDIT,
        "route": "ask",
        "subject_id": target,
        "key": key,
    }


def _route_finding_to_inbox(vault: Path, finding: Mapping[str, str]) -> None:
    """Land one CS3 scan finding on the durable Inbox attention surface."""
    subject = str(finding["subject_id"])
    if finding["kind"] == "restriction-key-removed":
        key = str(finding["key"])
        title = f"Restriction key removed: {subject}"
        detail = (
            f"Restriction key {markdown_code_span(key)} was removed from "
            f"{markdown_code_span(subject)} outside the trusted writer; until "
            "reviewed the file can re-enter Ask and pass the export gate."
        )
        prefix = "cs3-restriction-key-removed-"
        key_slug = re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-")
        subject_slug = re.sub(r"[^a-z0-9]+", "-", subject.lower()).strip("-")
        subject_fingerprint = sha256_bytes(subject.encode("utf-8")).removeprefix("sha256:")[:12]
        subject_limit = 60 - len(prefix) - len(subject_fingerprint) - len(key_slug) - 2
        slug = (
            f"{prefix}{subject_slug[:subject_limit].rstrip('-')}-{subject_fingerprint}-{key_slug}"
        )
    else:
        current = str(finding["current_human_sha256"])
        title = f"Foreign edit: {subject}"
        detail = (
            f"{markdown_code_span(subject)} changed outside the trusted writer: "
            f"expected {markdown_code_span(str(finding['prior_human_sha256']))}, "
            f"found {markdown_code_span(current)}."
        )
        prefix = "cs3-foreign-edit-"
        current_slug = current.removeprefix("sha256:")[:12]
        subject_slug = re.sub(r"[^a-z0-9]+", "-", subject.lower()).strip("-")
        subject_fingerprint = sha256_bytes(subject.encode("utf-8")).removeprefix("sha256:")[:12]
        subject_limit = 60 - len(prefix) - len(current_slug) - len(subject_fingerprint) - 2
        slug = (
            f"{prefix}{current_slug}-"
            f"{subject_slug[:subject_limit].rstrip('-')}-{subject_fingerprint}"
        )
    write_finding(
        vault,
        "flag",
        title,
        detail,
        raised_by="workspace-scan",
        agent_recommendation="issues-found",
        target=subject,
        loudness="alert",
        dedupe_slug=slug,
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
    known_hashes = _known_current_hashes(vault)
    targets = _pi_edit_targets(vault, contract, paths)
    for target in targets:
        _validate_pi_edit_target(vault, contract, target)

    observed = []
    snapshots: dict[str, tuple[str, list[str]]] = {}
    findings = _reconcile_file_baselines(
        vault,
        contract,
        known_hashes=known_hashes,
        excluded=targets,
    )
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
        current_hash, restriction_keys = _file_baseline_snapshot(vault, contract, target)
        if event["output_sha256"] != current_hash:
            raise RuntimeError(f"file changed while observing edit: {target}")
        expected_hash = known_hashes.get(target) or (
            str(baseline["human_sha256"]) if baseline is not None else ""
        )
        if baseline is not None and expected_hash != current_hash:
            findings.append(_foreign_edit_finding(target, expected_hash, current_hash))
        observed.append(event)
        snapshots[target] = (current_hash, restriction_keys)
        if baseline is not None:
            for key in sorted(set(baseline["restriction_keys"]) - set(restriction_keys)):
                findings.append(_restriction_key_removed_finding(target, key))
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
        for target, (current_hash, restriction_keys) in snapshots.items():
            if sha256_file(vault / target) != current_hash:
                continue
            state.upsert_file_baseline(
                vault,
                target,
                human_sha256=current_hash,
                restriction_keys=restriction_keys,
            )
    for finding in findings:
        _route_finding_to_inbox(vault, finding)
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
            # Read the authored id before validation: _validate_concept mints a
            # fresh ULID into an id-less Concept, which would re-key it every pass.
            raw_id = str(frontmatter.get("id") or "")
            try:
                _validate_concept(contract, target, frontmatter, strict_writer=False)
            except ValueError:
                continue
            rows.append(
                {
                    "concept_id": raw_id if is_ulid(raw_id) else target,
                    "concept_type": _concept_type_for(contract, str(frontmatter["type"])),
                    "path": target,
                }
            )
    return state.rebuild_file_concept_mirror(vault, rows)


def mark_checked(
    vault: Path,
    target_path: str,
    *,
    context: OperationContext,
    judgment: bool,
    checks: Iterable[str] | None = None,
    schemas_dir: Path | None = None,
    frontmatter: dict[str, Any] | None = None,
    body: str | None = None,
) -> dict[str, Any]:
    """Re-record a live Concept's verdict, optionally validating and writing replacement content atomically.

    ``judgment`` has no default on purpose: every caller has to say whether it
    is relaying an acceptance the PI made or performing a mechanical rewrite.
    See `_write_checked` for what each one does to the OKF confirmation field.
    """
    validate_operation_context(vault, context)
    vault = Path(vault)
    target = _target_path(target_path)
    promotion_checks = normalize_promotion_checks(checks)
    contract = _load_contract(vault, schemas_dir)
    _bundle_for_target(contract, target)
    output_path = vault / target
    current_frontmatter, current_body = split_frontmatter(output_path.read_text(encoding="utf-8"))
    return _write_checked(
        vault,
        target,
        output_path,
        current_frontmatter if frontmatter is None else frontmatter,
        current_body if body is None else body,
        promotion_checks,
        context,
        contract,
        judgment=judgment,
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
    if not context.body_is_pi_authored:
        body = neutralize_untrusted_markdown(body)
    _inherit_authored_identity(vault, target, frontmatter)
    frontmatter.pop("verified", None)
    frontmatter["generated"] = {
        "by": okf_actor(
            context.actor,
            agent_identity=context.agent_identity,
            operation_id=context.operation_id,
            machine_authored=context.machine_authored,
        ),
        "at": now_iso(),
    }
    input_rows = _input_rows(inputs)
    if not frontmatter.get("sources") and input_rows:
        frontmatter["sources"] = _sources_from_inputs(vault, input_rows)
    _validate_concept(contract, target, frontmatter)

    staged_path = _staged_path(vault, target)
    write_frontmatter_doc(staged_path, frontmatter, body, create_parent=True)
    event = {
        "event": EVENT_DERIVED,
        "timestamp": now_iso(),
        "output_id": target,
        "staging_id": _rel(vault, staged_path),
        "output_sha256": sha256_file(staged_path),
        "inputs": input_rows,
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
    checks: Iterable[str] | None = None,
    schemas_dir: Path | None = None,
) -> dict[str, Any]:
    """Promote a staged Concept into its bundle only after it validates as checked."""
    validate_operation_context(vault, context)
    vault = Path(vault)
    target = _target_path(target_path)
    promotion_checks = normalize_promotion_checks(checks)
    contract = _load_contract(vault, schemas_dir)
    _bundle_for_target(contract, target)

    staged_path = _staged_path(vault, target)
    if not staged_path.is_file():
        raise FileNotFoundError(staged_path)
    frontmatter, body = split_frontmatter(staged_path.read_text(encoding="utf-8"))
    if not context.body_is_pi_authored:
        body = neutralize_untrusted_markdown(body)
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
        judgment=True,
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
    contract = _load_contract(vault, None)
    _bundle_for_target(contract, target)
    staged_path = _staged_path(vault, target)
    if not staged_path.is_file():
        raise FileNotFoundError(staged_path)
    frontmatter, body = split_frontmatter(staged_path.read_text(encoding="utf-8"))
    _validate_concept(contract, target, frontmatter)
    output = state.output_record(vault, target)
    if output is None:
        raise ValueError(f"missing staged output record: {target}")
    if output["concept_type"] != frontmatter["type"]:
        raise ValueError(f"staged concept type does not match its output record: {target}")
    if output["check_status"] != "unchecked":
        raise ValueError(f"staged output is not unchecked: {target}")
    if not context.body_is_pi_authored:
        body = neutralize_untrusted_markdown(body)
    output_path = vault / target
    payload_text = frontmatter_doc(frontmatter, body)
    output_sha256 = sha256_bytes(payload_text.encode("utf-8"))
    if output["output_sha256"] != output_sha256:
        event = append_journal_event(
            vault,
            {
                "event": EVENT_DERIVED,
                "timestamp": now_iso(),
                "output_id": target,
                "staging_id": _rel(vault, staged_path),
                "output_sha256": output_sha256,
                "inputs": _latest_derived_inputs(vault, target),
            },
            context=context,
        )
        state.record_file_output(
            vault,
            output_id=target,
            concept_type=str(frontmatter["type"]),
            check_status="unchecked",
            output_sha256=event["output_sha256"],
            staging_id=event["staging_id"],
            payload_text=payload_text,
            context=context,
            inputs=event["inputs"],
        )
    write_frontmatter_doc(output_path, frontmatter, body, create_parent=True)
    staged_path.unlink()
    return {"output_id": target, "output_sha256": output_sha256}


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
    """Return the vault's folder homes and its registry-validated document types.

    Types load through ``schema.load_types``, which rejects a document type whose
    ``concept_type`` is not a registry member, so a mirror row's Concept type is
    never the raw frontmatter ``type`` this module is asked to trust.
    """
    root = Path(schemas_dir) if schemas_dir else vault / ".memoria/schemas"
    return {
        "folders": schema_lib.load_folders(root) or {},
        "types": schema_lib.load_types(root),
    }


def _concept_type_for(contract: dict[str, Any], document_type: str) -> str:
    """Return the registry Concept type for one document type (``schema.concept_type_for``)."""
    type_schema = contract["types"].get(document_type)
    if type_schema is None:
        raise ValueError(f"unknown document type: {document_type}")
    return str(type_schema["concept_type"])


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
    raw_paths = list(paths) if paths is not None else _git_status_paths(vault, contract)
    targets: list[str] = []
    for raw_path in raw_paths:
        try:
            target = _target_path(raw_path)
        except ValueError:
            continue
        path = vault / target
        if not path.is_file() or not _is_bundle_target(contract, target):
            continue
        if known.get(target) == sha256_file(path):
            continue
        targets.append(target)
    return sorted(set(targets))


def _reconcile_file_baselines(
    vault: Path,
    contract: dict[str, Any],
    *,
    known_hashes: Mapping[str, str],
    excluded: Iterable[str],
) -> list[dict[str, str]]:
    excluded_targets = set(excluded)
    findings = []
    for path in iter_markdown(vault):
        target = path.relative_to(vault).as_posix()
        if target in excluded_targets or not _is_bundle_target(contract, target):
            continue
        current_hash, restriction_keys = _file_baseline_snapshot(vault, contract, target)
        baseline = state.file_baseline(vault, target)
        if baseline is None:
            state.upsert_file_baseline(
                vault,
                target,
                human_sha256=current_hash,
                restriction_keys=restriction_keys,
            )
            continue
        expected_hash = known_hashes.get(target) or str(baseline["human_sha256"])
        if expected_hash == current_hash:
            if (
                baseline["human_sha256"] != current_hash
                or baseline["restriction_keys"] != restriction_keys
            ):
                state.upsert_file_baseline(
                    vault,
                    target,
                    human_sha256=current_hash,
                    restriction_keys=restriction_keys,
                )
            continue
        findings.append(_foreign_edit_finding(target, expected_hash, current_hash))
        for key in sorted(set(baseline["restriction_keys"]) - set(restriction_keys)):
            findings.append(_restriction_key_removed_finding(target, key))
    return findings


def _file_baseline_snapshot(
    vault: Path,
    contract: dict[str, Any],
    target: str,
) -> tuple[str, list[str]]:
    data = (vault / target).read_bytes()
    frontmatter, _body = split_frontmatter(data.decode("utf-8"))
    _validate_concept(contract, target, frontmatter, strict_writer=False)
    return sha256_bytes(data), _restriction_keys(frontmatter)


def _parse_git_status_porcelain(output: str) -> list[tuple[str, str]]:
    """Parse `git status --porcelain` lines into (status_code, path) pairs."""
    parsed: list[tuple[str, str]] = []
    for line in output.splitlines():
        if len(line) < 4:
            continue
        status = line[:2]
        path = line[3:]
        if " -> " in path:
            path = path.rsplit(" -> ", 1)[1]
        parsed.append((status, path))
    return parsed


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
    return [path for status, path in _parse_git_status_porcelain(proc.stdout) if "D" not in status]


def _validate_pi_edit_target(vault: Path, contract: dict[str, Any], target: str) -> None:
    frontmatter, _body = split_frontmatter((vault / target).read_text(encoding="utf-8"))
    _validate_concept(contract, target, frontmatter, strict_writer=False)


def _restriction_keys(frontmatter: dict[str, Any]) -> list[str]:
    return [key for key in ("superseded", "local-only") if frontmatter.get(key) is True]


def _staged_path(vault: Path, target: str) -> Path:
    return vault / ".memoria/staging" / target


def _inherit_authored_identity(vault: Path, target: str, frontmatter: dict[str, Any]) -> None:
    """Give id-less content the ULID already authored at its path, if there is one.

    ``apply_universal_concept_frontmatter`` mints a ULID for content that carries
    no ``id``, so without this a rewrite of one path would claim a second identity
    over the Concept living there — which v16 refuses as an identity collision.
    Staged content is the more recent authored state, so it wins over the promoted file.
    """
    if frontmatter.get("id"):
        return
    for path in (_staged_path(vault, target), vault / target):
        resident = str(read_frontmatter(path).get("id") or "")
        if is_ulid(resident):
            frontmatter["id"] = resident
            return


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
    judgment: bool,
) -> dict[str, Any]:
    """Write one plane-crossing document, stamping OKF fields at the seam.

    ``judgment`` says whether this write carries an acceptance. A judgment write
    REPLACES the `verified` field with the single confirmation it just recorded:
    entries supplied in the incoming bytes are discarded, so nothing typed into
    a file can pass itself off as the PI's confirmation, and the field stays the
    latest-confirmation projection it claims to be (full history is the
    journal's). A mechanical write — a link rewrite, a candidates block — leaves
    the field exactly as the last acceptance left it, because re-signing on a
    byte change would record a confirmation nobody made. A non-list value is
    dropped rather than carried: it would iterate as characters downstream.

    The seam works on its own copy of ``frontmatter`` so a validation failure
    leaves the caller's dict untouched.
    """
    promotion_checks = normalize_promotion_checks(checks)
    frontmatter = dict(frontmatter)
    if judgment:
        frontmatter.pop("verified", None)
        frontmatter["verified"] = [
            {
                "by": okf_verified_actor(context.actor, operation_id=context.operation_id),
                "at": now_iso(),
            }
        ]
    elif "verified" in frontmatter and not isinstance(frontmatter["verified"], list):
        frontmatter.pop("verified", None)
    if _replaces_existing_body(output_path, body):
        # Spec 5.2: `generated` is the last meaningful change, and this is the
        # one seam that changes bytes under an already-promoted document.
        frontmatter["generated"] = {
            "by": okf_actor(
                context.actor,
                agent_identity=context.agent_identity,
                operation_id=context.operation_id,
                machine_authored=context.machine_authored,
            ),
            "at": now_iso(),
        }
    _validate_concept(contract, target, frontmatter)
    payload_text = frontmatter_doc(frontmatter, body)
    output_sha256 = sha256_bytes(payload_text.encode("utf-8"))
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


def _replaces_existing_body(output_path: Path, body: str) -> bool:
    """Whether this write replaces the body of a document already on disk."""
    if not output_path.is_file():
        return False
    _frontmatter, current_body = split_frontmatter(output_path.read_text(encoding="utf-8"))
    return current_body != body


def _sources_from_inputs(vault: Path, input_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Project derivation inputs into OKF v0.2 `sources` entries (spec §5.1).

    A bundle-relative `resource` is a resolvable link, so only an input that
    really is a bundle file earns one. Every other input id — a catalog work
    key, a provider record — is emitted as written: a scope descriptor an OKF
    reader can recognize as one, rather than a path that resolves nowhere.
    """
    out: list[dict[str, str]] = []
    for row in input_rows:
        rid = str(row.get("id") or "")
        if not rid:
            continue
        slug = rid.removesuffix(".md").replace("/", "-")
        resolvable = rid.endswith(".md") and (vault / rid).is_file()
        out.append({"id": slug, "resource": f"/{rid}" if resolvable else rid})
    return out


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
            (machine, _canonical_json(event)) for machine, event in _iter_journal_exports(vault)
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
            key = (machine, _canonical_json(event))
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
    return sha256_bytes(proc.stdout)


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
