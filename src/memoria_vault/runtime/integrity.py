"""Alpha.11 integrity check routing and trace rollback helpers."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections import deque
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.policy.audit import EMPTY_SHA256, sha256_file
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.subsystems.lib.inbox import write_work_prompt
from memoria_vault.runtime.time import now_iso
from memoria_vault.runtime.trusted_writer import (
    EVENT_CHECK_FIRED,
    EVENT_DERIVED,
    EVENT_OBSERVED_EXTERNAL_EDIT,
    EVENT_RESOLVED,
    append_journal_event,
    commit_writer_changes,
)
from memoria_vault.runtime.vaultio import (
    iter_markdown,
    read_frontmatter,
    safe_read,
    split_frontmatter,
    write_frontmatter_doc,
)

NLI_SUPPORTED = "SUPPORTED"
NLI_REFUTED = "REFUTED"
NLI_NOTENOUGHINFO = "NOTENOUGHINFO"
_NEGATORS = frozenset({"no", "not", "never", "without"})
_STOP_TERMS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "for",
        "in",
        "is",
        "of",
        "on",
        "the",
        "to",
        "with",
    }
)
_HANS_ACCEPTANCE = (
    (
        "The intervention improved recall.",
        "The intervention did not improve recall.",
        NLI_REFUTED,
    ),
    (
        "The archive contains complete correspondence.",
        "The archive contains no complete correspondence.",
        NLI_REFUTED,
    ),
)


def record_integrity_check(
    vault: Path,
    target_id: str,
    *,
    check: str,
    status: str,
    reason: str = "",
    shadow: bool = True,
    route: str | None = None,
    auto_revert: bool = False,
    machine: str | None = None,
) -> dict[str, Any]:
    """Record one check verdict with alpha.11 shadow-first routing metadata."""
    vault = Path(vault)
    target = normalize_path(target_id)
    target_path = vault / target
    target_sha = sha256_file(target_path) if target_path.is_file() else EMPTY_SHA256
    event: dict[str, Any] = {
        "event": EVENT_CHECK_FIRED,
        "check": check,
        "status": status,
        "target_id": target,
        "target_sha256": target_sha,
        "output_sha256": target_sha,
        "shadow": shadow,
        "route": route or route_check(status, shadow=shadow, auto_revert=auto_revert),
    }
    if reason:
        event["reason"] = reason
    return append_journal_event(vault, event, machine=machine)


def route_check(status: str, *, shadow: bool = True, auto_revert: bool = False) -> str:
    if status == "passed" or shadow:
        return "drop"
    if auto_revert:
        return "act"
    return "ask"


def _is_checked_concept(vault: Path, relpath: str) -> bool:
    return state.concept_check_status(vault, relpath) == "checked"


def check_evidence_integrity(
    vault: Path,
    *,
    shadow: bool = True,
    machine: str | None = None,
    commit: bool = False,
) -> dict[str, Any]:
    """Flag checked notes/digests whose declared evidence is not checked."""
    vault = Path(vault)
    findings: list[dict[str, Any]] = []
    for path in iter_markdown(vault):
        rel = path.relative_to(vault).as_posix()
        frontmatter = read_frontmatter(path)
        if not _is_checked_concept(vault, rel):
            continue
        if frontmatter.get("type") not in {"work", "note"}:
            continue
        for evidence_rel in _evidence_refs(frontmatter):
            status = _evidence_status(vault, evidence_rel)
            if status["status"] in {"missing", "unchecked"}:
                findings.append(
                    record_integrity_check(
                        vault,
                        rel,
                        check="evidence-resolves",
                        status="failed",
                        reason=f"unresolved checked evidence: {evidence_rel}",
                        shadow=shadow,
                        machine=machine,
                    )
                )
            elif status["status"] == "stale":
                findings.append(
                    record_integrity_check(
                        vault,
                        rel,
                        check="evidence-current",
                        status="failed",
                        reason=f"stale checked evidence: {evidence_rel} ({status['lifecycle']})",
                        shadow=shadow,
                        machine=machine,
                    )
                )
    commit_hash = ""
    if findings and commit:
        commit_hash = commit_writer_changes(vault, "integrity evidence check", [], machine=machine)
    return {"findings": findings, "commit": commit_hash}


def check_claim_quote_support(
    vault: Path,
    *,
    shadow: bool = True,
    machine: str | None = None,
    commit: bool = False,
) -> dict[str, Any]:
    """Flag checked notes whose claim has no substantive term overlap with its quote."""
    vault = Path(vault)
    findings: list[dict[str, Any]] = []
    for path in iter_markdown(vault):
        rel = path.relative_to(vault).as_posix()
        frontmatter = read_frontmatter(path)
        if frontmatter.get("type") != "note" or not _is_checked_concept(vault, rel):
            continue
        claim_terms = _support_terms(str(frontmatter.get("claim_text") or ""))
        quote_terms = _support_terms(str(frontmatter.get("quote") or ""))
        if claim_terms and quote_terms and claim_terms.isdisjoint(quote_terms):
            findings.append(
                record_integrity_check(
                    vault,
                    rel,
                    check="claim-quote-support",
                    status="failed",
                    reason="claim and cited quote share no substantive terms",
                    shadow=shadow,
                    machine=machine,
                )
            )
    commit_hash = ""
    if findings and commit:
        commit_hash = commit_writer_changes(
            vault, "integrity claim quote check", [], machine=machine
        )
    return {"findings": findings, "commit": commit_hash}


def check_prompt_injection_markers(
    vault: Path,
    *,
    shadow: bool = True,
    machine: str | None = None,
    commit: bool = False,
) -> dict[str, Any]:
    """Flag checked Concepts carrying explicit prompt-injection marker text."""
    vault = Path(vault)
    findings: list[dict[str, Any]] = []
    for row in state.catalog_sources(vault):
        marker = _prompt_injection_marker(_source_row_scan_text(vault, row))
        if marker:
            findings.append(
                record_integrity_check(
                    vault,
                    f"catalog/sources/{row['source_id']}",
                    check="prompt-injection",
                    status="failed",
                    reason=f"prompt-injection marker: {marker}",
                    shadow=shadow,
                    machine=machine,
                )
            )
    for path in iter_markdown(vault):
        rel = path.relative_to(vault).as_posix()
        frontmatter = read_frontmatter(path)
        if not _is_checked_concept(vault, rel):
            continue
        if frontmatter.get("type") not in {"source", "work", "note"}:
            continue
        marker = _prompt_injection_marker(_concept_scan_text(vault, path, frontmatter))
        if marker:
            findings.append(
                record_integrity_check(
                    vault,
                    rel,
                    check="prompt-injection",
                    status="failed",
                    reason=f"prompt-injection marker: {marker}",
                    shadow=shadow,
                    machine=machine,
                )
            )
    commit_hash = ""
    if findings and commit:
        commit_hash = commit_writer_changes(
            vault, "integrity prompt injection check", [], machine=machine
        )
    return {"findings": findings, "commit": commit_hash}


def check_quote_anchor_support(
    vault: Path,
    *,
    shadow: bool = True,
    machine: str | None = None,
    commit: bool = False,
) -> dict[str, Any]:
    """Flag checked notes whose quoted span is absent from checked source text."""
    vault = Path(vault)
    findings: list[dict[str, Any]] = []
    for path in iter_markdown(vault):
        rel = path.relative_to(vault).as_posix()
        frontmatter = read_frontmatter(path)
        if frontmatter.get("type") != "note" or not _is_checked_concept(vault, rel):
            continue
        quote = str(frontmatter.get("quote") or "").strip()
        if not quote:
            continue
        source_texts = _checked_source_texts(vault, frontmatter)
        if source_texts and not any(_contains_span(text, quote) for text in source_texts):
            findings.append(
                record_integrity_check(
                    vault,
                    rel,
                    check="quote-anchor",
                    status="failed",
                    reason="quoted span is absent from checked source text",
                    shadow=shadow,
                    machine=machine,
                )
            )
    commit_hash = ""
    if findings and commit:
        commit_hash = commit_writer_changes(
            vault, "integrity quote anchor check", [], machine=machine
        )
    return {"findings": findings, "commit": commit_hash}


def check_source_metadata(
    vault: Path,
    *,
    shadow: bool = True,
    machine: str | None = None,
    commit: bool = False,
) -> dict[str, Any]:
    """Flag checked sources whose bibliographic metadata is too thin."""
    vault = Path(vault)
    findings: list[dict[str, Any]] = []
    for row in state.catalog_sources(vault, checked_only=False):
        target_id = f"catalog/sources/{row['source_id']}"
        if state.concept_check_status(vault, target_id) != "checked":
            continue
        frontmatter = _source_row_frontmatter(row)
        for reason in [
            *_source_metadata_issues(frontmatter),
            *_linked_entity_identity_issues(vault, frontmatter),
        ]:
            findings.append(
                record_integrity_check(
                    vault,
                    target_id,
                    check="source-metadata",
                    status="failed",
                    reason=reason,
                    shadow=shadow,
                    machine=machine,
                )
            )
    for path in iter_markdown(vault):
        rel = path.relative_to(vault).as_posix()
        frontmatter = read_frontmatter(path)
        if frontmatter.get("type") != "source" or not _is_checked_concept(vault, rel):
            continue
        if _source_ref(rel):
            continue
        for reason in [
            *_source_metadata_issues(frontmatter),
            *_linked_entity_identity_issues(vault, frontmatter),
        ]:
            findings.append(
                record_integrity_check(
                    vault,
                    rel,
                    check="source-metadata",
                    status="failed",
                    reason=reason,
                    shadow=shadow,
                    machine=machine,
                )
            )
    commit_hash = ""
    if findings and commit:
        commit_hash = commit_writer_changes(vault, "source metadata check", [], machine=machine)
    return {"findings": findings, "commit": commit_hash}


def check_citation_survival(
    vault: Path,
    *,
    shadow: bool = True,
    machine: str | None = None,
    commit: bool = False,
) -> dict[str, Any]:
    """Flag checked keep-set Concepts whose source references lack survival citations."""
    vault = Path(vault)
    findings: list[dict[str, Any]] = []
    for path in iter_markdown(vault):
        rel = path.relative_to(vault).as_posix()
        frontmatter = read_frontmatter(path)
        if not _is_checked_concept(vault, rel):
            continue
        if frontmatter.get("type") not in {"work", "note", "hub"}:
            continue
        for reason in state.check_citation_payload(frontmatter):
            findings.append(
                record_integrity_check(
                    vault,
                    rel,
                    check="citation-survival",
                    status="failed",
                    reason=reason,
                    shadow=shadow,
                    machine=machine,
                )
            )
    commit_hash = ""
    if findings and commit:
        commit_hash = commit_writer_changes(
            vault, "integrity citation survival check", [], machine=machine
        )
    return {"findings": findings, "commit": commit_hash}


def check_provenance_checkpoint(
    vault: Path,
    *,
    shadow: bool = True,
    machine: str | None = None,
    commit: bool = False,
) -> dict[str, Any]:
    """Flag checked synthesis that depends on uncorroborated checked sources."""
    vault = Path(vault)
    findings: list[dict[str, Any]] = []
    for path in iter_markdown(vault):
        rel = path.relative_to(vault).as_posix()
        frontmatter = read_frontmatter(path)
        if not _is_checked_concept(vault, rel):
            continue
        if frontmatter.get("type") not in {"work", "note"}:
            continue
        for evidence_rel in _evidence_refs(frontmatter):
            source_ref, status = _source_provider_coverage(vault, evidence_rel)
            if status in {"partial", "degraded"}:
                findings.append(
                    record_integrity_check(
                        vault,
                        rel,
                        check="provenance-checkpoint",
                        status="failed",
                        reason=f"uncorroborated checked source: {source_ref} ({status})",
                        shadow=shadow,
                        machine=machine,
                    )
                )
                break
    commit_hash = ""
    if findings and commit:
        commit_hash = commit_writer_changes(
            vault, "integrity provenance checkpoint", [], machine=machine
        )
    return {"findings": findings, "commit": commit_hash}


def check_contradiction_links(
    vault: Path,
    *,
    shadow: bool = True,
    machine: str | None = None,
    commit: bool = False,
) -> dict[str, Any]:
    """Flag checked digests whose explicit contradiction targets are not current."""
    vault = Path(vault)
    findings: list[dict[str, Any]] = []
    for path in iter_markdown(vault):
        rel = path.relative_to(vault).as_posix()
        frontmatter = read_frontmatter(path)
        if frontmatter.get("type") != "work" or not _is_checked_concept(vault, rel):
            continue
        contradictions = frontmatter.get("contradictions")
        if not isinstance(contradictions, list):
            continue
        for item in contradictions:
            if not isinstance(item, str) or not item.strip():
                continue
            target = _concept_rel(item)
            status = _concept_status(vault, target)
            if status["status"] == "checked":
                continue
            findings.append(
                record_integrity_check(
                    vault,
                    rel,
                    check="contradiction-link",
                    status="failed",
                    reason=f"unresolved contradiction target: {target}",
                    shadow=shadow,
                    machine=machine,
                )
            )
    commit_hash = ""
    if findings and commit:
        commit_hash = commit_writer_changes(
            vault, "integrity contradiction check", [], machine=machine
        )
    return {"findings": findings, "commit": commit_hash}


def contradiction_tier1_gate(
    *, comparator: Any | None = None, min_accuracy: float = 1.0
) -> dict[str, Any]:
    """Run the high-overlap/opposite-meaning gate before Tier-1 may classify pairs."""
    compare = comparator or _compare_claims
    failures: list[dict[str, Any]] = []
    baseline_failures = 0
    for premise, hypothesis, expected in _HANS_ACCEPTANCE:
        verdict = compare(premise, hypothesis)
        baseline = _lexical_baseline_verdict(premise, hypothesis)
        if baseline != expected:
            baseline_failures += 1
        if verdict["verdict"] != expected:
            failures.append(
                {
                    "premise": premise,
                    "hypothesis": hypothesis,
                    "expected": expected,
                    "actual": verdict["verdict"],
                }
            )
    total = len(_HANS_ACCEPTANCE)
    accuracy = (total - len(failures)) / total
    return {
        "passed": accuracy >= min_accuracy and baseline_failures > 0,
        "accuracy": accuracy,
        "total": total,
        "failures": failures,
        "baseline_failures": baseline_failures,
    }


def surface_tensions(
    vault: Path,
    *,
    max_pairs: int = 20,
    min_overlap: float = 0.55,
    machine: str | None = None,
    commit: bool = False,
    comparator: Any | None = None,
) -> dict[str, Any]:
    """Propose unchecked contradiction candidates; never writes contradiction links."""
    vault = Path(vault)
    compare = comparator or _compare_claims
    gate = contradiction_tier1_gate(comparator=compare)
    rows = _checked_tension_rows(vault)
    candidates: list[dict[str, Any]] = []
    abstain_count = 0
    seen: set[tuple[str, str]] = set()
    for left_index, left in enumerate(rows):
        for right in rows[left_index + 1 :]:
            pair_key = tuple(sorted((left["canonical_id"], right["canonical_id"])))
            if pair_key in seen or pair_key[0] == pair_key[1]:
                continue
            seen.add(pair_key)
            overlap = _lexical_overlap(left["text"], right["text"])
            if overlap < min_overlap:
                continue
            if not gate["passed"]:
                candidates.append(_tension_candidate(left, right, overlap, verdict="DEGRADED"))
            else:
                verdict = compare(left["text"], right["text"])
                if verdict["verdict"] == NLI_REFUTED:
                    candidates.append(
                        _tension_candidate(
                            left,
                            right,
                            overlap,
                            verdict=NLI_REFUTED,
                            warrant=str(verdict.get("warrant") or ""),
                        )
                    )
                elif verdict["verdict"] == NLI_NOTENOUGHINFO:
                    abstain_count += 1
            if len(candidates) >= max_pairs:
                break
        if len(candidates) >= max_pairs:
            break
    attention_path = ""
    finding: dict[str, Any] | None = None
    commit_hash = ""
    if not gate["passed"]:
        finding = record_integrity_check(
            vault,
            "knowledge",
            check="contradiction-tier1-hans",
            status="failed",
            reason="contradiction detection degraded: NLI below HANS bar",
            shadow=False,
            route="ask",
            machine=machine,
        )
        if commit:
            path = write_work_prompt(
                vault,
                "Contradiction detection degraded",
                "Review lexical tension candidates before setting contradiction links.",
                (
                    "Tier-1 contradiction detection did not pass the HANS-style "
                    "overlap-but-opposite gate, so lexical candidates require PI review."
                ),
                "surface-tensions",
                target="knowledge",
                posture="co-pi",
                loudness="alert",
                dedupe_slug="contradiction-detection-degraded",
            )
            attention_path = path.relative_to(vault).as_posix() if path else ""
            commit_paths = [attention_path] if attention_path else []
            commit_hash = commit_writer_changes(
                vault, "surface degraded contradiction detection", commit_paths, machine=machine
            )
    return {
        "gate": gate,
        "degraded": not gate["passed"],
        "candidate_count": len(candidates),
        "abstain_count": abstain_count,
        "candidates": candidates,
        "attention_path": attention_path,
        "finding": finding,
        "commit": commit_hash,
    }


def check_link_targets(
    vault: Path,
    *,
    shadow: bool = True,
    machine: str | None = None,
    commit: bool = False,
) -> dict[str, Any]:
    """Flag checked Concepts whose declared link targets are not current."""
    vault = Path(vault)
    findings: list[dict[str, Any]] = []
    for path in iter_markdown(vault):
        rel = path.relative_to(vault).as_posix()
        frontmatter = read_frontmatter(path)
        if not _is_checked_concept(vault, rel):
            continue
        for target in _link_refs(frontmatter):
            status = _concept_status(vault, target)
            if status["status"] == "checked":
                continue
            findings.append(
                record_integrity_check(
                    vault,
                    rel,
                    check="link-target",
                    status="failed",
                    reason=f"unresolved link target: {target}",
                    shadow=shadow,
                    machine=machine,
                )
            )
    commit_hash = ""
    if findings and commit:
        commit_hash = commit_writer_changes(
            vault, "integrity link target check", [], machine=machine
        )
    return {"findings": findings, "commit": commit_hash}


def trace_downstream(vault: Path, target_id: str) -> list[dict[str, Any]]:
    """Return latest derived events whose inputs descend from ``target_id``."""
    return [event for _depth, event in _downstream_events(vault, target_id)]


def propagate_scan_demotion(
    vault: Path,
    target_id: str,
    *,
    reason: str,
    machine: str | None = None,
) -> dict[str, Any]:
    """Propagate a scan-side demotion through checked downstream Concepts."""
    vault = Path(vault)
    target = normalize_path(target_id)
    demoted: list[str] = []
    needs_human: list[str] = []
    stale: list[str] = []
    skipped: list[str] = []
    for depth, event in _downstream_events(vault, target):
        output_id = event.get("output_id")
        if not isinstance(output_id, str):
            continue
        output_id = normalize_path(output_id)
        status = state.concept_check_status(vault, output_id)
        if status != "checked":
            skipped.append(output_id)
            continue
        actor = str(event.get("actor") or "")
        if actor == "pi":
            _flag_human_descendant(vault, output_id, target, reason, machine)
            needs_human.append(output_id)
        elif depth == 1:
            _demote_machine_descendant(vault, output_id, target, reason, machine)
            demoted.append(output_id)
        else:
            _flag_stale_machine_descendant(vault, output_id, target, reason, machine)
            stale.append(output_id)
    return {
        "target_id": target,
        "demoted": demoted,
        "needs_human": needs_human,
        "stale": stale,
        "skipped": skipped,
    }


def _downstream_events(vault: Path, target_id: str) -> list[tuple[int, dict[str, Any]]]:
    target = normalize_path(target_id)
    target_aliases = _trace_aliases(vault, target)
    derived = _latest_derived(Path(vault))
    by_input: dict[str, list[str]] = {}
    for output_id, event in derived.items():
        for row in event.get("inputs") or []:
            input_id = row.get("id") if isinstance(row, dict) else None
            if isinstance(input_id, str):
                by_input.setdefault(normalize_path(input_id), []).append(output_id)

    found: list[tuple[int, dict[str, Any]]] = []
    seen: set[str] = set()
    queue: deque[tuple[str, int]] = deque((alias, 0) for alias in sorted(target_aliases))
    expanded: set[str] = set()
    while queue:
        current, depth = queue.popleft()
        if current in expanded:
            continue
        expanded.add(current)
        for output_id in sorted(by_input.get(current, [])):
            if output_id in seen:
                continue
            seen.add(output_id)
            found.append((depth + 1, derived[output_id]))
            queue.append((output_id, depth + 1))
    return found


def cascade_rollback(
    vault: Path,
    target_id: str,
    *,
    reason: str,
    include_target: bool = False,
    machine: str | None = None,
) -> dict[str, Any]:
    """Quarantine machine-derived descendants and flag PI-derived descendants."""
    vault = Path(vault)
    target = normalize_path(target_id)
    derived = _latest_derived(vault)
    events = trace_downstream(vault, target)
    catalog_target = ""
    catalog_quarantine_id = ""
    if include_target:
        catalog_target, catalog_quarantine_id = _quarantine_catalog_source(
            vault, target, reason, machine
        )
    if include_target and target in derived:
        events = [derived[target], *events]

    reverted: list[str] = [catalog_target] if catalog_target else []
    needs_human: list[str] = []
    skipped: list[str] = []
    touched: list[str] = [catalog_quarantine_id] if catalog_quarantine_id else []
    seen: set[str] = set()
    for event in events:
        output_id = event.get("output_id")
        if not isinstance(output_id, str):
            continue
        output_id = normalize_path(output_id)
        if output_id in seen:
            continue
        seen.add(output_id)

        if event.get("actor") == "pi":
            _flag_human_descendant(vault, output_id, target, reason, machine)
            needs_human.append(output_id)
            continue

        path = vault / output_id
        if not path.is_file():
            skipped.append(output_id)
            continue
        _quarantine_machine_descendant(vault, output_id, target, reason, machine)
        reverted.append(output_id)
        touched.append(output_id)

    commit = ""
    if reverted or needs_human:
        commit = commit_writer_changes(
            vault,
            f"cascade rollback {Path(target).stem}",
            touched,
            machine=machine,
        )
    return {
        "target_id": target,
        "reverted": reverted,
        "needs_human": needs_human,
        "skipped": skipped,
        "commit": commit,
    }


def resolve_attention(
    vault: Path,
    target_id: str,
    *,
    resolution: str,
    outcome: str | None = None,
    routing_class: str = "ask",
    reason: str = "",
    machine: str | None = None,
) -> dict[str, Any]:
    """Record a PI attention disposition through the worker-owned journal."""
    if resolution not in {"acknowledged", "resolved"}:
        raise ValueError(f"unsupported attention resolution: {resolution!r}")
    outcome = outcome or resolution
    supported_outcomes = (
        {"acknowledged"} if resolution == "acknowledged" else {"apply", "reject", "defer"}
    )
    if outcome not in supported_outcomes:
        raise ValueError(f"unsupported attention outcome for {resolution}: {outcome!r}")
    if routing_class not in {"act", "ask", "log"}:
        raise ValueError(f"unsupported attention routing class: {routing_class!r}")
    vault = Path(vault)
    target = normalize_path(target_id)
    decided_at = now_iso()
    event = {
        "event": EVENT_RESOLVED,
        "resolution": resolution,
        "outcome": outcome,
        "resolution_outcome": outcome,
        "routing_class": routing_class,
        "decided_at": decided_at,
        "target_id": target,
        "reason": reason,
        "actor": "pi",
        "source": "attention",
    }
    row = append_journal_event(vault, event, machine=machine)
    touched: list[str] = []
    target_path = vault / target
    if resolution == "resolved" and target_path.is_file():
        frontmatter, body = split_frontmatter(target_path.read_text(encoding="utf-8"))
        if frontmatter.get("projection") == "attention":
            frontmatter["attention_status"] = "deferred" if outcome == "defer" else "resolved"
            frontmatter["resolution_outcome"] = outcome
            frontmatter["routing_class"] = routing_class
            frontmatter["resolved_at"] = decided_at
            write_frontmatter_doc(target_path, frontmatter, body)
            touched.append(target)
    commit = commit_writer_changes(
        vault,
        f"{outcome} attention {Path(target).stem}",
        touched,
        machine=machine,
    )
    return {"event": row, "commit": commit}


def _flag_human_descendant(
    vault: Path, output_id: str, target: str, reason: str, machine: str | None
) -> None:
    path = vault / output_id
    target_sha = sha256_file(path) if path.is_file() else EMPTY_SHA256
    append_journal_event(
        vault,
        {
            "event": EVENT_CHECK_FIRED,
            "check": "cascade-rollback",
            "status": "failed",
            "reason": reason,
            "target_id": output_id,
            "target_sha256": target_sha,
            "output_sha256": target_sha,
            "trigger_id": target,
            "shadow": False,
            "route": "ask",
        },
        machine=machine,
    )


def _demote_machine_descendant(
    vault: Path, output_id: str, target: str, reason: str, machine: str | None
) -> None:
    path = vault / output_id
    target_sha = sha256_file(path) if path.is_file() else EMPTY_SHA256
    state.set_concept_verdict(vault, output_id, "unchecked")
    append_journal_event(
        vault,
        {
            "event": EVENT_CHECK_FIRED,
            "check": "scan-demotion-propagation",
            "status": "failed",
            "reason": reason,
            "target_id": output_id,
            "target_sha256": target_sha,
            "output_sha256": target_sha,
            "trigger_id": target,
            "shadow": False,
            "route": "act",
        },
        machine=machine,
    )


def _flag_stale_machine_descendant(
    vault: Path, output_id: str, target: str, reason: str, machine: str | None
) -> None:
    path = vault / output_id
    target_sha = sha256_file(path) if path.is_file() else EMPTY_SHA256
    state.set_concept_flag(vault, output_id, "stale", reason=reason, trigger_id=target)
    append_journal_event(
        vault,
        {
            "event": EVENT_CHECK_FIRED,
            "check": "scan-demotion-stale",
            "status": "failed",
            "reason": reason,
            "target_id": output_id,
            "target_sha256": target_sha,
            "output_sha256": target_sha,
            "trigger_id": target,
            "shadow": False,
            "route": "log",
        },
        machine=machine,
    )


def _quarantine_machine_descendant(
    vault: Path, output_id: str, target: str, reason: str, machine: str | None
) -> None:
    source = vault / output_id
    original_sha = sha256_file(source)
    quarantine_path = _unique_path(vault / ".memoria/quarantine" / output_id)
    quarantine_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), quarantine_path)
    restore_source = _restore_pre_materialization(vault, output_id)
    quarantine_id = quarantine_path.relative_to(vault).as_posix()
    state.set_concept_verdict(vault, output_id, "quarantined")
    append_journal_event(
        vault,
        {
            "event": EVENT_RESOLVED,
            "resolution": "rolled_back",
            "target_id": output_id,
            "target_sha256": original_sha,
            "quarantined_id": quarantine_id,
            "quarantined_sha256": original_sha,
            "restore_source": restore_source,
            "trigger_id": target,
            "reason": reason,
        },
        machine=machine,
    )
    append_journal_event(
        vault,
        {
            "event": EVENT_DERIVED,
            "output_id": output_id,
            "output_sha256": EMPTY_SHA256,
            "inputs": [
                {"id": output_id, "sha256": original_sha, "role": "rolled-back-head"},
                {"id": target, "role": "rollback-trigger"},
            ],
            "operation": "cascade-rollback",
            "actor": "integrity",
            "quarantined_id": quarantine_id,
            "restore_source": restore_source,
        },
        machine=machine,
    )


def _restore_pre_materialization(vault: Path, output_id: str) -> str:
    with state.connect(vault) as conn:
        row = conn.execute(
            "SELECT materialized_commit FROM outputs WHERE output_id = ?",
            (output_id,),
        ).fetchone()
    commit = "" if row is None else str(row["materialized_commit"] or "")
    parent = _git_stdout(vault, "rev-parse", f"{commit}^") if commit else ""
    if parent:
        proc = subprocess.run(
            ["git", "restore", "--source", parent, "--", output_id],
            cwd=vault,
            check=False,
            text=True,
            capture_output=True,
        )
        if proc.returncode == 0:
            return parent
    (vault / output_id).unlink(missing_ok=True)
    return ""


def _git_stdout(vault: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=vault,
        check=False,
        text=True,
        capture_output=True,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _quarantine_catalog_source(
    vault: Path, target: str, reason: str, machine: str | None
) -> tuple[str, str]:
    source_ref = _source_ref(target)
    if not source_ref:
        return "", ""
    row = state.catalog_source(vault, source_ref)
    if row is None:
        return "", ""
    source_id = str(row["source_id"])
    with state.connect(vault) as conn:
        conn.execute(
            "UPDATE catalog_sources SET check_status = 'quarantined' WHERE source_id = ?",
            (source_id,),
        )
        conn.execute(
            """
            INSERT INTO concept_verdicts(concept_id, check_status)
            VALUES (?, 'quarantined')
            ON CONFLICT(concept_id) DO UPDATE SET check_status = 'quarantined'
            """,
            (source_ref,),
        )
    quarantine_path = _unique_path(vault / ".memoria/quarantine" / source_ref)
    quarantine_path.parent.mkdir(parents=True, exist_ok=True)
    quarantine_path.write_text(
        json.dumps(
            {
                "target_id": source_ref,
                "store": "db",
                "reason": reason,
                "check_status": "quarantined",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    quarantine_id = quarantine_path.relative_to(vault).as_posix()
    append_journal_event(
        vault,
        {
            "event": EVENT_DERIVED,
            "output_id": source_ref,
            "inputs": [{"id": target, "role": "rollback-trigger"}],
            "operation": "cascade-rollback",
            "actor": "integrity",
            "store": "db",
            "status": "quarantined",
            "quarantined_id": quarantine_id,
            "reason": reason,
        },
        machine=machine,
    )
    return source_ref, quarantine_id


def _latest_derived(vault: Path) -> dict[str, dict[str, Any]]:
    derived: dict[str, dict[str, Any]] = {}
    for path in sorted((vault / "journal").glob("*.jsonl")):
        for event in iter_jsonl(path):
            if event.get("event") not in {EVENT_DERIVED, EVENT_OBSERVED_EXTERNAL_EDIT}:
                continue
            output_id = event.get("output_id")
            if isinstance(output_id, str):
                derived[normalize_path(output_id)] = event
    return derived


def _trace_aliases(vault: Path, target: str) -> set[str]:
    aliases = {target}
    row = state.catalog_source(vault, target)
    if row is None:
        return aliases
    source_id = str(row.get("source_id") or "").strip()
    concept_path = str(row.get("concept_path") or "").strip()
    if source_id:
        aliases.add(f"catalog/sources/{source_id}")
    if concept_path:
        aliases.add(normalize_path(concept_path))
    return aliases


def _checked_tension_rows(vault: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in iter_markdown(vault):
        rel = path.relative_to(vault).as_posix()
        frontmatter, body = split_frontmatter(safe_read(path))
        if frontmatter.get("type") not in {"note", "work"}:
            continue
        if not _is_checked_concept(vault, rel):
            continue
        title = str(frontmatter.get("title") or path.stem).strip()
        text = " ".join(
            str(value).strip()
            for value in (
                frontmatter.get("claim_text"),
                frontmatter.get("description"),
                title,
                body,
            )
            if value
        )
        if len(_claim_terms(text)) < 3:
            continue
        rows.append(
            {
                "id": rel,
                "canonical_id": str(frontmatter.get("id") or frontmatter.get("source_id") or rel),
                "title": title,
                "text": text,
            }
        )
    return rows


def _compare_claims(premise: str, hypothesis: str) -> dict[str, Any]:
    premise_terms = set(_claim_terms(premise))
    hypothesis_terms = set(_claim_terms(hypothesis))
    overlap = _lexical_overlap_terms(premise_terms, hypothesis_terms)
    premise_negated = bool(premise_terms & _NEGATORS)
    hypothesis_negated = bool(hypothesis_terms & _NEGATORS)
    shared_non_negated = (premise_terms - _NEGATORS) & (hypothesis_terms - _NEGATORS)
    # ponytail: local negation-NLI stand-in; replace with a pinned model when packaged.
    if overlap >= 0.55 and premise_negated != hypothesis_negated and len(shared_non_negated) >= 3:
        return {
            "verdict": NLI_REFUTED,
            "confidence": 0.9,
            "warrant": "high lexical overlap with opposite negation",
        }
    if overlap >= 0.75 and premise_negated == hypothesis_negated:
        return {
            "verdict": NLI_SUPPORTED,
            "confidence": 0.8,
            "warrant": "high lexical overlap with matching polarity",
        }
    return {
        "verdict": NLI_NOTENOUGHINFO,
        "confidence": 0.0,
        "warrant": "insufficient deterministic support",
    }


def _lexical_baseline_verdict(premise: str, hypothesis: str) -> str:
    if _lexical_overlap(premise, hypothesis) >= 0.55:
        return NLI_SUPPORTED
    return NLI_NOTENOUGHINFO


def _tension_candidate(
    left: dict[str, str],
    right: dict[str, str],
    overlap: float,
    *,
    verdict: str,
    warrant: str = "",
) -> dict[str, Any]:
    route = "ask"
    return {
        "left": left["id"],
        "right": right["id"],
        "left_title": left["title"],
        "right_title": right["title"],
        "verdict": verdict,
        "route": route,
        "lexical_overlap": round(overlap, 3),
        "warrant": warrant or "Tier-1 unavailable; route lexical candidate to PI review",
    }


def _lexical_overlap(left: str, right: str) -> float:
    return _lexical_overlap_terms(set(_claim_terms(left)), set(_claim_terms(right)))


def _lexical_overlap_terms(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / min(len(left), len(right))


def _claim_terms(text: str) -> list[str]:
    terms: list[str] = []
    for raw in re.findall(r"[a-z0-9]+", text.lower()):
        if raw in _STOP_TERMS:
            continue
        terms.append(_stem_claim_term(raw))
    return terms


def _stem_claim_term(term: str) -> str:
    for suffix in ("ing", "ed", "es", "s"):
        if len(term) > len(suffix) + 3 and term.endswith(suffix):
            return term[: -len(suffix)]
    if len(term) > 4 and term.endswith("e"):
        return term[:-1]
    return term


def _evidence_refs(frontmatter: dict[str, Any]) -> list[str]:
    refs = set()
    source_id = frontmatter.get("source_id")
    if isinstance(source_id, str) and source_id.strip():
        refs.add(_source_rel(source_id))
    evidence_set = frontmatter.get("evidence_set")
    if isinstance(evidence_set, list):
        for item in evidence_set:
            if isinstance(item, str) and item.strip():
                refs.add(_concept_rel(item))
    return sorted(refs)


def _link_refs(frontmatter: dict[str, Any]) -> list[str]:
    refs: set[str] = set()
    _collect_link_refs(frontmatter.get("links"), refs)
    return sorted(refs)


def _collect_link_refs(value: Any, refs: set[str]) -> None:
    if isinstance(value, str):
        ref = _link_ref(value)
        if ref:
            refs.add(ref)
        return
    if isinstance(value, list):
        for item in value:
            _collect_link_refs(item, refs)
        return
    if isinstance(value, dict):
        for item in value.values():
            _collect_link_refs(item, refs)


def _link_ref(value: str) -> str:
    raw = value.strip()
    if not raw or "://" in raw or raw.startswith("mailto:"):
        return ""
    if raw.startswith("[[") and raw.endswith("]]"):
        raw = raw[2:-2].split("|", 1)[0].strip()
    rel = _concept_rel(raw)
    if rel.startswith(("knowledge/", "capabilities/", "catalog/entities/")) and not rel.endswith(
        ".md"
    ):
        rel = f"{rel}.md"
    if rel.endswith(".md") or rel.startswith(("catalog/", "knowledge/", "capabilities/")):
        return rel
    return ""


def _source_rel(value: str) -> str:
    rel = normalize_path(value)
    if source_ref := _source_ref(rel):
        return source_ref
    return f"catalog/sources/{rel.strip('/')}"


def _concept_rel(value: str) -> str:
    rel = normalize_path(value)
    if source_ref := _source_ref(rel):
        return source_ref
    return rel


def _evidence_status(vault: Path, rel: str) -> dict[str, str]:
    return _concept_status(vault, rel)


def _concept_status(vault: Path, rel: str) -> dict[str, str]:
    if source_ref := _source_ref(rel):
        row = state.catalog_source(vault, source_ref)
        if row is not None:
            return _source_row_status(vault, row)
        return {"status": "missing"}
    path = vault / rel
    if not path.is_file():
        return {"status": "missing"}
    if not _is_checked_concept(vault, rel):
        return {"status": "unchecked"}
    return _frontmatter_status(read_frontmatter(path))


def _frontmatter_status(frontmatter: dict[str, Any]) -> dict[str, str]:
    lifecycle = str(frontmatter.get("lifecycle") or "")
    if lifecycle in {"retracted", "archived"}:
        return {"status": "stale", "lifecycle": lifecycle}
    status = str(frontmatter.get("status") or "")
    if status in {"rejected", "superseded"}:
        return {"status": "stale", "lifecycle": status}
    return {"status": "checked"}


def _source_row_status(vault: Path, row: dict[str, Any]) -> dict[str, str]:
    source_ref = f"catalog/sources/{row.get('source_id') or ''}"
    if state.concept_check_status(vault, source_ref) != "checked":
        return {"status": "unchecked"}
    flags = state.concept_flags(vault, source_ref)
    if "stale" in flags:
        return {"status": "stale", "lifecycle": "stale"}
    csl_json = row.get("csl_json") if isinstance(row.get("csl_json"), dict) else {}
    memoria = csl_json.get("memoria") if isinstance(csl_json.get("memoria"), dict) else {}
    standing = str(memoria.get("standing") or "")
    if standing in {"retracted", "archived", "superseded"}:
        return {"status": "stale", "lifecycle": standing}
    return {"status": "checked"}


def _checked_source_texts(vault: Path, frontmatter: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    for evidence_rel in _evidence_refs(frontmatter):
        if source_ref := _source_ref(evidence_rel):
            row = state.catalog_source(vault, source_ref)
            if row is not None:
                if row.get("check_status") == "checked":
                    _append_content_path_text(vault, texts, str(row.get("content_path") or ""))
            continue
        path = vault / evidence_rel
        evidence_fm = read_frontmatter(path)
        if evidence_fm.get("type") != "source" or not _is_checked_concept(vault, evidence_rel):
            continue
        _append_content_path_text(vault, texts, str(evidence_fm.get("content_path") or ""))
        if path.is_file():
            texts.append(path.read_text(encoding="utf-8"))
    return texts


def _append_content_path_text(vault: Path, texts: list[str], content_path: str) -> None:
    if not content_path.strip():
        return
    content = vault / normalize_path(content_path)
    if content.is_file():
        texts.append(content.read_text(encoding="utf-8"))


def _source_provider_coverage(vault: Path, rel: str) -> tuple[str, str]:
    if source_ref := _source_ref(rel):
        row = state.catalog_source(vault, source_ref)
        if row is not None:
            if row.get("check_status") != "checked":
                return source_ref, ""
            return source_ref, str(row.get("provider_coverage") or "")
        return source_ref, ""
    source_ref = rel
    path = vault / rel
    if not path.is_file():
        return source_ref, ""
    source_fm = read_frontmatter(path)
    if source_fm.get("type") != "source" or source_fm.get("check_status") != "checked":
        return source_ref, ""
    return source_ref, str(source_fm.get("provider_coverage") or "")


def _source_row_frontmatter(row: dict[str, Any]) -> dict[str, Any]:
    csl_json = row.get("csl_json") if isinstance(row.get("csl_json"), dict) else {}
    memoria = csl_json.get("memoria") if isinstance(csl_json.get("memoria"), dict) else {}
    return {
        "type": "source",
        "check_status": row.get("check_status") or "",
        "title": row.get("title") or "",
        "description": row.get("description") or "",
        "source_id": f"catalog/sources/{row.get('source_id') or ''}",
        "citekey": row.get("citekey") or "",
        "provider_coverage": row.get("provider_coverage") or "",
        "text_status": row.get("text_status") or "",
        "resource": row.get("resource") or "",
        "identifiers": row.get("identifiers") if isinstance(row.get("identifiers"), dict) else {},
        "csl_json": csl_json,
        "links": memoria.get("links") if isinstance(memoria.get("links"), dict) else {},
    }


def _source_row_scan_text(vault: Path, row: dict[str, Any]) -> str:
    parts = [
        str(row.get("title") or ""),
        str(row.get("description") or ""),
        json.dumps(row.get("csl_json") or {}, sort_keys=True),
    ]
    content_path = str(row.get("content_path") or "")
    if content_path.strip():
        content = vault / normalize_path(content_path)
        if content.is_file():
            parts.append(content.read_text(encoding="utf-8"))
    return "\n".join(parts)


def _source_ref(value: str) -> str:
    rel = normalize_path(value).rstrip("/")
    prefix = "catalog/sources/"
    if not rel.startswith(prefix):
        return ""
    source_id = rel.removeprefix(prefix)
    if source_id.endswith("/source.md"):
        source_id = source_id.removesuffix("/source.md")
    if not source_id or "/" in source_id:
        return ""
    return f"{prefix}{source_id}"


def _source_metadata_issues(frontmatter: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    provider_coverage = str(frontmatter.get("provider_coverage") or "")
    if provider_coverage == "degraded":
        issues.append(f"provider_coverage is {provider_coverage}")
    if not str(frontmatter.get("citekey") or "").strip():
        issues.append("missing citekey alias")
    csl_json = frontmatter.get("csl_json")
    if not isinstance(csl_json, dict) or not csl_json:
        issues.append("missing CSL-JSON metadata")
        return issues
    if not str(csl_json.get("title") or "").strip():
        issues.append("missing CSL title")
    item_type = str(frontmatter.get("item_type") or "")
    if item_type in {"article", "book", "report"}:
        if not _has_csl_authors(csl_json):
            issues.append("missing CSL author")
        if not _has_csl_year(csl_json):
            issues.append("missing CSL issued year")
    if _has_conflicting_doi(frontmatter, csl_json):
        issues.append("conflicting DOI metadata")
    if not _has_external_identifier(frontmatter, csl_json):
        issues.append("missing external resource or identifier")
    return issues


def _linked_entity_identity_issues(vault: Path, frontmatter: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for entity_rel in _linked_entity_refs(frontmatter):
        entity = vault / entity_rel
        if not entity.is_file():
            continue
        entity_fm = read_frontmatter(entity)
        if state.concept_check_status(vault, entity_rel) != "checked":
            continue
        metadata = entity_fm.get("metadata") if isinstance(entity_fm.get("metadata"), dict) else {}
        if metadata.get("identity_status") == "ambiguous":
            issues.append(f"ambiguous entity identity: {entity_rel}")
    return issues


def _linked_entity_refs(frontmatter: dict[str, Any]) -> list[str]:
    links = frontmatter.get("links") if isinstance(frontmatter.get("links"), dict) else {}
    refs: list[str] = []
    for values in links.values():
        if not isinstance(values, list):
            continue
        for value in values:
            if not isinstance(value, str):
                continue
            rel = _concept_rel(value)
            if rel.startswith("catalog/entities/"):
                refs.append(rel if rel.endswith(".md") else f"{rel}.md")
    return refs


def _has_csl_authors(csl_json: dict[str, Any]) -> bool:
    authors = csl_json.get("author")
    return isinstance(authors, list) and any(
        isinstance(author, dict) and author for author in authors
    )


def _has_csl_year(csl_json: dict[str, Any]) -> bool:
    issued = csl_json.get("issued")
    if not isinstance(issued, dict):
        return False
    parts = issued.get("date-parts")
    if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0]:
        return True
    return bool(str(issued.get("raw") or "").strip())


def _has_external_identifier(frontmatter: dict[str, Any], csl_json: dict[str, Any]) -> bool:
    if str(frontmatter.get("resource") or "").strip():
        return True
    identifiers = frontmatter.get("identifiers")
    if isinstance(identifiers, dict) and any(str(value).strip() for value in identifiers.values()):
        return True
    return bool(str(csl_json.get("DOI") or csl_json.get("URL") or "").strip())


def _has_conflicting_doi(frontmatter: dict[str, Any], csl_json: dict[str, Any]) -> bool:
    identifiers = frontmatter.get("identifiers")
    if not isinstance(identifiers, dict):
        return False
    top_level = _normalized_doi(str(identifiers.get("doi") or ""))
    csl = _normalized_doi(str(csl_json.get("DOI") or ""))
    return bool(top_level and csl and top_level != csl)


def _normalized_doi(value: str) -> str:
    doi = value.strip().casefold()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi)
    doi = re.sub(r"^doi:\s*", "", doi)
    return doi.strip()


def _contains_span(text: str, quote: str) -> bool:
    return _normalized_span(quote) in _normalized_span(text)


def _normalized_span(text: str) -> str:
    return " ".join(str(text).casefold().split())


def _support_terms(text: str) -> set[str]:
    stopwords = {
        "about",
        "after",
        "before",
        "from",
        "into",
        "that",
        "their",
        "there",
        "this",
        "with",
    }
    return {term for term in re.findall(r"[a-z0-9]{4,}", text.lower()) if term not in stopwords}


def _concept_scan_text(vault: Path, path: Path, frontmatter: dict[str, Any]) -> str:
    parsed, body = split_frontmatter(path.read_text(encoding="utf-8"))
    parts = [
        body,
        str(parsed.get("title") or frontmatter.get("title") or ""),
        str(parsed.get("description") or frontmatter.get("description") or ""),
        str(parsed.get("claim_text") or frontmatter.get("claim_text") or ""),
        str(parsed.get("quote") or frontmatter.get("quote") or ""),
    ]
    content_path = frontmatter.get("content_path")
    if isinstance(content_path, str) and content_path.strip():
        content = vault / normalize_path(content_path)
        if content.is_file():
            parts.append(content.read_text(encoding="utf-8"))
    return "\n".join(parts)


def _prompt_injection_marker(text: str) -> str:
    normalized = _normalized_span(text)
    markers = (
        "ignore previous instructions",
        "ignore all previous instructions",
        "disregard previous instructions",
        "disregard all previous instructions",
        "forget previous instructions",
        "reveal the system prompt",
        "reveal system prompt",
        "reveal the developer message",
        "reveal developer message",
    )
    for marker in markers:
        if marker in normalized:
            return marker
    return ""


def _unique_path(path: Path) -> Path:
    candidate = path
    index = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        index += 1
    return candidate
