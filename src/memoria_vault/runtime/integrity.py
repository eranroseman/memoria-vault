"""Alpha.11 integrity check routing and trace rollback helpers."""

from __future__ import annotations

import re
import shutil
from collections import deque
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.policy.audit import EMPTY_SHA256, sha256_file
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.time import now_iso
from memoria_vault.runtime.trusted_writer import (
    EVENT_CHECK_FIRED,
    EVENT_DERIVED,
    EVENT_RESOLVED,
    append_journal_event,
    commit_writer_changes,
)
from memoria_vault.runtime.vaultio import (
    iter_markdown,
    read_frontmatter,
    split_frontmatter,
    write_frontmatter_doc,
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
        if frontmatter.get("check_status") != "checked":
            continue
        if frontmatter.get("type") not in {"digest", "note"}:
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
        if frontmatter.get("type") != "note" or frontmatter.get("check_status") != "checked":
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
    for path in iter_markdown(vault):
        rel = path.relative_to(vault).as_posix()
        frontmatter = read_frontmatter(path)
        if frontmatter.get("check_status") != "checked":
            continue
        if frontmatter.get("type") not in {"source", "digest", "note"}:
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
        if frontmatter.get("type") != "note" or frontmatter.get("check_status") != "checked":
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
    for path in iter_markdown(vault):
        rel = path.relative_to(vault).as_posix()
        frontmatter = read_frontmatter(path)
        if frontmatter.get("type") != "source" or frontmatter.get("check_status") != "checked":
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
        if frontmatter.get("check_status") != "checked":
            continue
        if frontmatter.get("type") not in {"digest", "note", "hub"}:
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
        if frontmatter.get("check_status") != "checked":
            continue
        if frontmatter.get("type") not in {"digest", "note"}:
            continue
        for evidence_rel in _evidence_refs(frontmatter):
            source = vault / evidence_rel
            if not source.is_file():
                continue
            source_fm = read_frontmatter(source)
            if source_fm.get("type") != "source" or source_fm.get("check_status") != "checked":
                continue
            status = str(source_fm.get("metadata_status") or "")
            if status in {"partial", "unverified", "not-indexed"}:
                findings.append(
                    record_integrity_check(
                        vault,
                        rel,
                        check="provenance-checkpoint",
                        status="failed",
                        reason=f"uncorroborated checked source: {evidence_rel} ({status})",
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
        if frontmatter.get("type") != "digest" or frontmatter.get("check_status") != "checked":
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
        if frontmatter.get("check_status") != "checked":
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
    target = normalize_path(target_id)
    derived = _latest_derived(Path(vault))
    by_input: dict[str, list[str]] = {}
    for output_id, event in derived.items():
        for row in event.get("inputs") or []:
            input_id = row.get("id") if isinstance(row, dict) else None
            if isinstance(input_id, str):
                by_input.setdefault(normalize_path(input_id), []).append(output_id)

    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    queue: deque[str] = deque([target])
    while queue:
        current = queue.popleft()
        for output_id in sorted(by_input.get(current, [])):
            if output_id in seen:
                continue
            seen.add(output_id)
            found.append(derived[output_id])
            queue.append(output_id)
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
    if include_target and target in derived:
        events = [derived[target], *events]

    reverted: list[str] = []
    needs_human: list[str] = []
    skipped: list[str] = []
    touched: list[str] = []
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
    reason: str = "",
    machine: str | None = None,
) -> dict[str, Any]:
    """Record a PI attention disposition through the worker-owned journal."""
    if resolution not in {"acknowledged", "resolved"}:
        raise ValueError(f"unsupported attention resolution: {resolution!r}")
    outcome = outcome or resolution
    supported_outcomes = (
        {"acknowledged"} if resolution == "acknowledged" else {"resolved", "dismissed"}
    )
    if outcome not in supported_outcomes:
        raise ValueError(f"unsupported attention outcome for {resolution}: {outcome!r}")
    vault = Path(vault)
    target = normalize_path(target_id)
    event = {
        "event": EVENT_RESOLVED,
        "resolution": resolution,
        "outcome": outcome,
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
            frontmatter["attention_status"] = "resolved"
            frontmatter["resolved_at"] = now_iso()
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


def _quarantine_machine_descendant(
    vault: Path, output_id: str, target: str, reason: str, machine: str | None
) -> None:
    source = vault / output_id
    original_sha = sha256_file(source)
    frontmatter, body = split_frontmatter(source.read_text(encoding="utf-8"))
    if frontmatter:
        frontmatter["check_status"] = "quarantined"
        write_frontmatter_doc(source, frontmatter, body)
    quarantined_sha = sha256_file(source)
    quarantine_path = _unique_path(vault / ".memoria/quarantine" / output_id)
    quarantine_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), quarantine_path)
    quarantine_id = quarantine_path.relative_to(vault).as_posix()
    append_journal_event(
        vault,
        {
            "event": EVENT_RESOLVED,
            "resolution": "rolled_back",
            "target_id": output_id,
            "target_sha256": original_sha,
            "quarantined_id": quarantine_id,
            "quarantined_sha256": quarantined_sha,
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
        },
        machine=machine,
    )


def _latest_derived(vault: Path) -> dict[str, dict[str, Any]]:
    derived: dict[str, dict[str, Any]] = {}
    for path in sorted((vault / "journal").glob("*.jsonl")):
        for event in iter_jsonl(path):
            if event.get("event") != EVENT_DERIVED:
                continue
            output_id = event.get("output_id")
            if isinstance(output_id, str):
                derived[normalize_path(output_id)] = event
    return derived


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
    if rel.endswith(".md"):
        return rel
    if rel.startswith("catalog/sources/"):
        return f"{rel.rstrip('/')}/source.md"
    return f"catalog/sources/{rel.strip('/')}/source.md"


def _concept_rel(value: str) -> str:
    rel = normalize_path(value)
    if rel.startswith("catalog/sources/") and not rel.endswith(".md"):
        return f"{rel.rstrip('/')}/source.md"
    return rel


def _evidence_status(vault: Path, rel: str) -> dict[str, str]:
    return _concept_status(vault, rel)


def _concept_status(vault: Path, rel: str) -> dict[str, str]:
    path = vault / rel
    if not path.is_file():
        return {"status": "missing"}
    frontmatter = read_frontmatter(path)
    if frontmatter.get("check_status") != "checked":
        return {"status": "unchecked"}
    lifecycle = str(frontmatter.get("lifecycle") or "")
    if lifecycle in {"retracted", "archived"}:
        return {"status": "stale", "lifecycle": lifecycle}
    status = str(frontmatter.get("status") or "")
    if status in {"rejected", "superseded"}:
        return {"status": "stale", "lifecycle": status}
    return {"status": "checked"}


def _checked_source_texts(vault: Path, frontmatter: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    for evidence_rel in _evidence_refs(frontmatter):
        path = vault / evidence_rel
        evidence_fm = read_frontmatter(path)
        if evidence_fm.get("type") != "source" or evidence_fm.get("check_status") != "checked":
            continue
        content_path = evidence_fm.get("content_path")
        if isinstance(content_path, str) and content_path.strip():
            content = vault / normalize_path(content_path)
            if content.is_file():
                texts.append(content.read_text(encoding="utf-8"))
        if path.is_file():
            texts.append(path.read_text(encoding="utf-8"))
    return texts


def _source_metadata_issues(frontmatter: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    metadata_status = str(frontmatter.get("metadata_status") or "")
    if metadata_status in {"unverified", "not-indexed"}:
        issues.append(f"metadata_status is {metadata_status}")
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
        if entity_fm.get("check_status") != "checked":
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
