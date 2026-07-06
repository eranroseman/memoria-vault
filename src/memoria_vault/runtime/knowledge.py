"""Note-candidate, gap-analysis, and project-export helpers."""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
import shutil
import subprocess
from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from itertools import pairwise
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.operations import (
    load_operation_policy,
    required_promotion_checks,
    resolve_operation_runner,
)
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.read_barrier import is_consumable_checked_file
from memoria_vault.runtime.subsystems.lib import schema as schema_lib
from memoria_vault.runtime.trusted_writer import (
    append_journal_event,
    commit_writer_changes,
    materialize_unchecked,
    promote_checked,
    stage_concept,
)
from memoria_vault.runtime.vaultio import (
    apply_universal_concept_frontmatter,
    concept_text,
    frontmatter_doc,
    iter_markdown,
    read_frontmatter,
    split_frontmatter,
    write_frontmatter_doc,
)

GAP_KINDS = {
    "new-topic",
    "undigested",
    "under-warranted",
    "citation-neighborhood",
    "full-text-missing",
    "argument-unsupported",
    "argument-uncountered",
    "argument-fragile",
    "paper-readiness",
    "bounded-universe-incomplete",
}
_TAG_CANDIDATE_MIN_COUNT = 2
_TAG_CANDIDATE_LIMIT = 5
_TAG_CANDIDATE_STOPWORDS = frozenset(
    {
        "about",
        "also",
        "and",
        "are",
        "but",
        "for",
        "from",
        "into",
        "the",
        "this",
        "with",
    }
)
_DISCOVERY_RELEVANCE_STOPWORDS = _TAG_CANDIDATE_STOPWORDS | {
    "candidate",
    "current",
    "paper",
    "papers",
    "priority",
    "question",
    "questions",
    "research",
    "source",
    "sources",
    "steering",
    "system",
    "work",
    "works",
}
PAPER_PLAN_REQUIRED_FIELDS = (
    "target",
    "audience",
    "research_question",
    "central_contribution",
    "gap_statement",
    "claim_evidence_map",
    "figure_plan",
    "limitations",
)


def frame_project_paper(
    vault: Path,
    project_path: str,
    *,
    paper_plan: dict[str, Any],
    machine: str | None = None,
    run_id: str = "",
    actor: str = "pi",
) -> dict[str, Any]:
    """Record PI-supplied paper framing fields on a project and leave it unchecked."""
    vault = Path(vault)
    project_rel = _project_rel(vault, project_path)
    path = vault / project_rel
    if not path.is_file():
        raise FileNotFoundError(path)
    frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
    if frontmatter.get("type") != "project":
        raise ValueError(f"{project_rel} is not a project")
    plan = _normalize_paper_plan(paper_plan)
    frontmatter["paper_plan"] = plan
    frontmatter["outcome_frame"] = {
        "kind": "paper",
        "target": plan["target"],
        "audience": plan["audience"],
        "research_question": plan["research_question"],
        "status": "framed",
    }
    stage_concept(
        vault,
        project_rel,
        frontmatter_doc(frontmatter, body),
        operation="frame-paper",
        run_id=run_id,
        actor=actor,
        machine=machine,
    )
    materialized = materialize_unchecked(vault, project_rel)
    commit = commit_writer_changes(
        vault, f"frame paper {Path(project_rel).stem}", [project_rel], machine=machine
    )
    return {
        "project_path": project_rel,
        "paper_plan": plan,
        "outcome_frame": frontmatter["outcome_frame"],
        "check_status": state.concept_check_status(vault, project_rel),
        "materialized": materialized,
        "commit": commit,
    }


def _normalize_paper_plan(raw: dict[str, Any]) -> dict[str, Any]:
    plan = {
        field: raw.get(field)
        for field in PAPER_PLAN_REQUIRED_FIELDS
        if field in {"claim_evidence_map", "figure_plan"}
    }
    for field in PAPER_PLAN_REQUIRED_FIELDS:
        if field in plan:
            continue
        plan[field] = str(raw.get(field) or "").strip()
    if not isinstance(plan["claim_evidence_map"], dict) or not plan["claim_evidence_map"]:
        raise ValueError("paper_plan.claim_evidence_map must be a non-empty map")
    if not isinstance(plan["figure_plan"], dict) or not plan["figure_plan"]:
        raise ValueError("paper_plan.figure_plan must be a non-empty map")
    missing = [field for field in PAPER_PLAN_REQUIRED_FIELDS if not plan[field]]
    if missing:
        raise ValueError(f"paper_plan missing required field(s): {', '.join(missing)}")
    return plan


def emit_note_candidates(
    vault: Path,
    digest_path: str,
    candidates: Iterable[dict[str, Any]],
    *,
    operation_id: str = "propose-note-candidates",
    mode: str | None = None,
    machine: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Promote checked note candidates derived from one checked digest."""
    vault = Path(vault)
    policy = load_operation_policy(vault, operation_id)
    runner = resolve_operation_runner(vault, policy, mode)
    _require_tool(policy, "trusted_writer")
    promotion_checks = required_promotion_checks(policy)

    digest_rel = _digest_rel(digest_path)
    _require_path(policy, digest_rel)
    digest_fm = _checked_frontmatter(vault, digest_rel, "digest")
    rows = list(candidates)
    if not rows:
        raise ValueError("at least one note candidate is required")

    run_id = run_id or f"{operation_id}:{Path(digest_rel).stem}"
    started = append_journal_event(
        vault,
        {"event": "run", "run_id": run_id, "workflow": operation_id, "status": "started"},
        machine=machine,
    )
    model_call = append_journal_event(
        vault,
        {
            "event": "model_call",
            "run_id": run_id,
            "mode": runner["mode"],
            "runner": runner["runner"],
            "provider": runner["provider"],
            "model": runner["model"],
            "model_params": runner["params"],
            "route": policy.get("route", "note-candidates"),
            "purpose": "note_candidates",
            "prompt_version": policy["prompt_version"],
            "prompt_hash": _sha256_text(repr(rows)),
            "toolset": policy["allowed_tools"],
            "fallback_used": False,
            "compression_used": False,
            "input_hash": sha256_file(vault / digest_rel),
            "output_hash": _sha256_text(repr(rows)),
        },
        machine=machine,
    )

    staged = []
    checked = []
    note_paths = []
    digest_source_ref = digest_fm.get("source_id") or (
        f"catalog/sources/{digest_fm['work_id']}" if digest_fm.get("work_id") else None
    )
    for row in rows:
        title = _required_text(row, "title")
        body = _required_text(row, "body")
        note_rel = _unique_note_rel(vault, title)
        _require_path(policy, note_rel)
        frontmatter = {
            "type": "note",
            "title": title,
            "source_id": row.get("source_id") or digest_source_ref,
            "evidence_set": row.get("evidence_set")
            or digest_fm.get("evidence_set")
            or ([digest_source_ref] if digest_source_ref else []),
            "extraction_confidence": str(row.get("extraction_confidence") or "medium"),
            "tags": _string_list(row.get("tags")),
        }
        if row.get("description"):
            frontmatter["description"] = str(row["description"])
        if row.get("claim_text"):
            frontmatter["claim_text"] = str(row["claim_text"])
        if row.get("quote"):
            frontmatter["quote"] = str(row["quote"])
        if isinstance(row.get("annotation_ref"), dict):
            frontmatter["annotation_ref"] = dict(row["annotation_ref"])
        citations = row.get("citations") or digest_fm.get("citations")
        if isinstance(citations, list):
            frontmatter["citations"] = [dict(item) for item in citations if isinstance(item, dict)]

        stage = stage_concept(
            vault,
            note_rel,
            concept_text(frontmatter, title, body),
            inputs=[{"id": digest_rel, "sha256": sha256_file(vault / digest_rel)}],
            operation=operation_id,
            run_id=run_id,
            machine=machine,
        )
        check = promote_checked(vault, note_rel, checks=promotion_checks, machine=machine)
        staged.append(stage)
        checked.append(check)
        note_paths.append(note_rel)

    finished = append_journal_event(
        vault,
        {
            "event": "run",
            "run_id": run_id,
            "workflow": operation_id,
            "status": "done",
            "outputs": note_paths,
        },
        machine=machine,
    )
    commit = commit_writer_changes(
        vault, f"propose notes {Path(digest_rel).stem}", note_paths, machine=machine
    )
    return {
        "run_id": run_id,
        "note_paths": note_paths,
        "started": started,
        "model_call": model_call,
        "derived": staged,
        "checked": checked,
        "finished": finished,
        "commit": commit,
    }


def curate_note_candidate(
    vault: Path,
    note_path: str,
    status: str,
    *,
    reason: str = "",
    machine: str | None = None,
) -> dict[str, Any]:
    """Record PI acceptance or rejection of a checked candidate note."""
    vault = Path(vault)
    note_rel = _note_rel(note_path)
    status = status.strip().lower()
    if status not in {"accepted", "rejected"}:
        raise ValueError("note candidate status must be accepted or rejected")

    note = vault / note_rel
    if not note.is_file():
        raise FileNotFoundError(note)
    frontmatter, _body = split_frontmatter(note.read_text(encoding="utf-8"))
    if frontmatter.get("type") != "note" or not _has_checked_verdict(vault, note_rel):
        raise ValueError(f"{note_rel} is not a checked note")
    if state.note_curation_status(vault, note_rel) != "candidate":
        raise ValueError(f"{note_rel} is not a candidate note")

    event = append_journal_event(
        vault,
        {
            "event": "resolved",
            "actor": "pi",
            "operation": "curate-note-candidate",
            "target_id": note_rel,
            "target_sha256": sha256_file(note),
            "resolution": status,
            "reason": reason.strip(),
        },
        machine=machine,
    )
    commit = commit_writer_changes(
        vault, f"{status} note candidate {Path(note_rel).stem}", [note_rel], machine=machine
    )
    return {"note_path": note_rel, "status": status, "event": event, "commit": commit}


def curate_note_link(
    vault: Path,
    source_note_path: str,
    link_type: str,
    target_path: str,
    *,
    reason: str = "",
    machine: str | None = None,
) -> dict[str, Any]:
    """Record one PI-authored typed link on a checked note."""
    vault = Path(vault)
    source_rel = _note_rel(source_note_path)
    target_rel = _concept_rel(target_path)
    link_type = link_type.strip().lower()
    if link_type not in {"supports", "contradicts", "extends"}:
        raise ValueError("note link_type must be supports, contradicts, or extends")

    source_note = vault / source_rel
    if not source_note.is_file():
        raise FileNotFoundError(source_note)
    frontmatter, body = split_frontmatter(source_note.read_text(encoding="utf-8"))
    if frontmatter.get("type") != "note" or not _has_checked_verdict(vault, source_rel):
        raise ValueError(f"{source_rel} is not a checked note")
    _checked_concept(vault, target_rel)

    links = frontmatter.get("links")
    if links is None:
        links = {}
    if not isinstance(links, dict):
        raise ValueError(f"{source_rel} links must be a map")
    bucket = links.setdefault(link_type, [])
    if not isinstance(bucket, list):
        raise ValueError(f"{source_rel} links.{link_type} must be a list")
    changed = target_rel not in bucket
    if changed:
        bucket.append(target_rel)
        frontmatter["links"] = links
        write_frontmatter_doc(source_note, frontmatter, body)
        state.mark_checked(
            vault,
            source_rel,
            sha256_file(source_note),
            source_note.read_text(encoding="utf-8"),
        )

    event = append_journal_event(
        vault,
        {
            "event": "resolved",
            "actor": "pi",
            "operation": "curate-note-link",
            "target_id": source_rel,
            "linked_id": target_rel,
            "link_type": link_type,
            "target_sha256": sha256_file(source_note),
            "changed": changed,
            "reason": reason.strip(),
        },
        machine=machine,
    )
    commit = commit_writer_changes(
        vault, f"link note {Path(source_rel).stem}", [source_rel], machine=machine
    )
    return {
        "source_note_path": source_rel,
        "target_path": target_rel,
        "link_type": link_type,
        "changed": changed,
        "event": event,
        "commit": commit,
    }


def analyze_gaps(
    vault: Path,
    *,
    seed_terms: Iterable[str] = (),
    dense_threshold: int = 2,
    project_path: str = "",
    machine: str | None = None,
) -> dict[str, Any]:
    """Classify source/note topic mismatches over checked Concepts and search hits."""
    vault = Path(vault)
    project_path = project_path.strip()
    project_argument: dict[str, Any] | None = None
    argument_gaps: list[dict[str, Any]] = []
    paper_gaps: list[dict[str, Any]] = []
    if project_path:
        project_argument = analyze_project_argument(vault, project_path)
        argument_gaps = _project_argument_gaps(project_argument)
        paper_gaps = _project_paper_readiness_gaps(vault, project_path)
    counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"sources": 0, "digests": 0, "notes": 0}
    )
    seen: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: {"sources": set(), "digests": set(), "notes": set()}
    )
    labels: dict[str, str] = {}
    retrieval: dict[str, dict[str, Any]] = {}
    _add_catalog_source_gap_terms(vault, counts, seen, labels)
    _add_graph_topic_gap_terms(vault, counts, seen, labels)
    if project_argument is not None:
        _add_project_gap_terms(vault, project_argument, counts, seen, labels)
    for rel, frontmatter in _checked_concepts(vault):
        bucket = _bucket(rel, frontmatter)
        if not bucket:
            continue
        for term in _terms(frontmatter):
            key = term.lower()
            identity = _gap_identity(rel, bucket)
            if identity not in seen[key][bucket]:
                seen[key][bucket].add(identity)
                counts[key][bucket] += 1
            labels.setdefault(key, term)
    for term in seed_terms:
        label = " ".join(str(term).split())
        if label:
            labels.setdefault(label.lower(), label)
            counts[label.lower()]

    _add_search_gap_hits(vault, counts, seen, labels, retrieval)

    gaps = []
    for key in sorted(counts):
        source_count = counts[key]["sources"] + counts[key]["digests"]
        note_count = counts[key]["notes"]
        if source_count == 0 and note_count == 0:
            kind = "new-topic"
            seed = "capture a seed source or project note"
            why = "No checked works, digests, or notes are present for this requested topic."
            impact, confidence, actionability = 1, 2, 1
        elif source_count >= dense_threshold and note_count == 0:
            kind = "undigested"
            seed = "distill note candidates from checked digests"
            why = (
                f"{source_count} checked work input(s) mention this topic, "
                "but no checked notes cover it."
            )
            impact, confidence, actionability = 2, 2, 1
        elif note_count >= dense_threshold and source_count == 0:
            kind = "under-warranted"
            seed = "capture or link supporting sources"
            why = (
                f"{note_count} checked note(s) mention this topic, "
                "but no checked works or digests warrant it."
            )
            impact, confidence, actionability = 2, 2, 1
        else:
            continue
        gap = _gap_payload(
            {
                "topic": labels[key],
                "source_count": counts[key]["sources"],
                "digest_count": counts[key]["digests"],
                "note_count": note_count,
                "proposed_seed": seed,
            },
            kind=kind,
            target=f"topic:{labels[key]}",
            why=why,
            next_actions=[seed],
            impact=impact,
            confidence=confidence,
            actionability=actionability,
        )
        if source_ids := _source_ids_from_seen(seen[key]["sources"]):
            gap["source_ids"] = source_ids
        if key in retrieval:
            gap["retrieval_engine"] = retrieval[key]["engine"]
            gap["retrieval_sources"] = retrieval[key]["sources"]
        gaps.append(gap)
    citation_gaps = _citation_neighborhood_gaps(vault)
    gaps.extend(citation_gaps)
    full_text_gaps = _missing_full_text_gaps(vault)
    gaps.extend(full_text_gaps)
    gaps.extend(argument_gaps)
    gaps.extend(paper_gaps)
    full_text_attention_paths, full_text_attention_commit = _write_full_text_gap_attention(
        vault, full_text_gaps, machine=machine
    )
    candidate_paths, commit = _write_gap_discovery_candidates(vault, gaps, machine=machine)
    tag_candidates = _tag_candidates(vault)
    tag_candidate_paths, tag_candidate_commit = _write_tag_candidate_attention(
        vault,
        tag_candidates,
        machine=machine,
    )
    result = {
        "checked_topics": len(counts),
        "dense_threshold": dense_threshold,
        "summary": _gap_summary(gaps),
        "saturation": _saturation_block(project_argument),
        "citation_neighborhood_gap_count": len(citation_gaps),
        "full_text_gap_count": len(full_text_gaps),
        "full_text_attention_paths": full_text_attention_paths,
        "full_text_attention_commit": full_text_attention_commit,
        "argument_gap_count": len(argument_gaps),
        "paper_readiness_gap_count": len(paper_gaps),
        "discovery_candidate_paths": candidate_paths,
        "discovery_candidate_channels": _discovery_candidate_channels(vault, candidate_paths),
        "discovery_commit": commit,
        "tag_candidate_count": len(tag_candidates),
        "tag_candidate_paths": tag_candidate_paths,
        "tag_candidate_commit": tag_candidate_commit,
        "tag_candidates": tag_candidates,
        "gap_findings": gaps,
        "gaps": gaps,
    }
    if project_argument is not None:
        result.update(
            {
                "project_path": project_argument["project_path"],
                "thesis_path": project_argument["thesis_path"],
                "argument_stage": project_argument["argument_stage"],
                "evidence_saturation": project_argument["evidence_saturation"],
                "displayed_confidence": project_argument["displayed_confidence"],
            }
        )
    return result


def exploration_channel(vault: Path, *, limit: int = 10) -> dict[str, Any]:
    """Return relevance-independent coverage candidates from the citation graph."""
    vault = Path(vault)
    limit = max(1, int(limit))
    sources = [
        source
        for source in state.catalog_sources(vault)
        if source.get("check_status") == "checked" and _is_current_catalog_source(source)
    ]
    source_by_id = {str(source["source_id"]): source for source in sources}
    captured = _captured_work_ids(vault)
    candidates = []
    if source_by_id:
        with state.connect(vault) as conn:
            rows = conn.execute(
                """
                SELECT work_id, relation_type, target_id, target_title, target_doi,
                       source_provider
                FROM work_graph_edges
                WHERE relation_type IN ('references', 'related')
                ORDER BY work_id, relation_type, target_id
                """,
            ).fetchall()
        for row in rows:
            edge = dict(row)
            if str(edge["work_id"]) not in source_by_id:
                continue
            if _edge_is_captured(edge, captured):
                continue
            source = source_by_id[str(edge["work_id"])]
            title = str(edge.get("target_title") or edge["target_id"])
            candidates.append(
                {
                    "source_id": edge["work_id"],
                    "source_title": source["title"],
                    "candidate_work_id": edge["target_id"],
                    "candidate_title": title,
                    "candidate_doi": edge.get("target_doi") or "",
                    "relation_type": edge["relation_type"],
                    "provider": edge.get("source_provider") or "",
                    "why": (
                        f"Coverage candidate: checked source `{edge['work_id']}` "
                        f"{edge['relation_type']} uncaptured work `{edge['target_id']}`."
                    ),
                }
            )
    items = _coverage_round_robin(candidates, limit)
    contrary_items = _contrary_channel_items(vault, limit=limit)
    return {
        "mode": "mmr-baseline",
        "ranker": "coverage-diversity",
        "relevance_independent": True,
        "items": items,
        "contrary_items": contrary_items,
        "empty": not items and not contrary_items,
    }


def _gap_payload(
    row: dict[str, Any],
    *,
    kind: str,
    target: str,
    why: str,
    next_actions: Iterable[str],
    impact: int,
    confidence: int,
    actionability: int,
    candidate_work_ids: Iterable[str] = (),
) -> dict[str, Any]:
    if kind not in GAP_KINDS:
        raise ValueError(f"unknown gap kind: {kind}")
    for name, value in (
        ("impact", impact),
        ("confidence", confidence),
        ("actionability", actionability),
    ):
        if value not in {0, 1, 2}:
            raise ValueError(f"{name} must be 0, 1, or 2")
    score = impact * confidence * actionability
    out = dict(row)
    out["kind"] = kind
    out["gap_type"] = kind
    out["target"] = target
    out["why"] = why
    out["next_actions"] = [action for action in next_actions if str(action).strip()]
    out["candidate_work_ids"] = sorted(
        {str(candidate).strip() for candidate in candidate_work_ids if str(candidate).strip()}
    )
    out["impact"] = impact
    out["confidence"] = confidence
    out["actionability"] = actionability
    out["score"] = score
    out["severity"] = _gap_severity(score)
    out["advisory"] = actionability == 0
    return out


def _gap_severity(score: int) -> str:
    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def _gap_summary(gaps: list[dict[str, Any]]) -> dict[str, Any]:
    by_kind = dict.fromkeys(sorted(GAP_KINDS), 0)
    by_severity = {"high": 0, "medium": 0, "low": 0}
    blocking = 0
    advisories = 0
    for gap in gaps:
        kind = str(gap.get("kind") or gap.get("gap_type") or "")
        if kind in by_kind:
            by_kind[kind] += 1
        severity = str(gap.get("severity") or "low")
        if severity in by_severity:
            by_severity[severity] += 1
        if gap.get("advisory"):
            advisories += 1
        else:
            blocking += 1
    return {
        "total": len(gaps),
        "blocking": blocking,
        "advisories": advisories,
        "by_kind": by_kind,
        "by_severity": by_severity,
    }


def _saturation_block(argument: dict[str, Any] | None) -> dict[str, Any]:
    if argument is None:
        return {
            "claims": 0,
            "saturated": 0,
            "unsupported": 0,
            "uncountered": 0,
            "ready": False,
            "claim_saturation": [],
        }
    thesis = str(argument.get("thesis_path") or "").strip()
    claims = 1 if thesis and argument.get("node_count", 0) > 0 else 0
    has_support = int(argument.get("supports_count") or 0) > 0
    has_counterpoint = int(argument.get("contradicts_count") or 0) > 0
    claim_ready = claims > 0 and has_support and has_counterpoint
    return {
        "claims": claims,
        "saturated": 1 if claim_ready else 0,
        "unsupported": 1 if claims and not has_support else 0,
        "uncountered": 1 if claims and not has_counterpoint else 0,
        "ready": claim_ready,
        "claim_saturation": [
            {
                "claim": thesis,
                "has_support": has_support,
                "has_counterpoint": has_counterpoint,
                "saturated": claim_ready,
            }
        ]
        if claims
        else [],
        "conditions": argument.get("saturation_conditions") or {},
        "evidence_saturation": argument.get("evidence_saturation") or "unknown",
    }


def _add_catalog_source_gap_terms(
    vault: Path,
    counts: dict[str, dict[str, int]],
    seen: dict[str, dict[str, set[str]]],
    labels: dict[str, str],
) -> None:
    for source in state.catalog_sources(vault):
        if not _is_current_catalog_source(source):
            continue
        identity = _gap_identity(f"catalog/sources/{source['source_id']}", "sources")
        for term in _catalog_source_terms(source):
            key = term.lower()
            if identity not in seen[key]["sources"]:
                seen[key]["sources"].add(identity)
                counts[key]["sources"] += 1
            labels.setdefault(key, term)


def _catalog_source_terms(source: dict[str, Any]) -> list[str]:
    csl = source.get("csl_json") if isinstance(source.get("csl_json"), dict) else {}
    memoria = csl.get("memoria") if isinstance(csl.get("memoria"), dict) else {}
    out = []
    for field in ("tags", "topics", "research_area"):
        value = memoria.get(field)
        if isinstance(value, list):
            out.extend(item for item in value if isinstance(item, str) and item.strip())
        elif isinstance(value, str) and value.strip():
            out.append(value)
    return sorted(set(out))


def _is_current_catalog_source(source: dict[str, Any]) -> bool:
    csl = source.get("csl_json") if isinstance(source.get("csl_json"), dict) else {}
    memoria = csl.get("memoria") if isinstance(csl.get("memoria"), dict) else {}
    standing = str(memoria.get("standing") or "")
    return standing not in {"archived", "retracted", "superseded"}


def _add_graph_topic_gap_terms(
    vault: Path,
    counts: dict[str, dict[str, int]],
    seen: dict[str, dict[str, set[str]]],
    labels: dict[str, str],
) -> None:
    source_ids = [
        str(source["source_id"])
        for source in state.catalog_sources(vault)
        if _is_current_catalog_source(source)
    ]
    if not source_ids:
        return
    with state.connect(vault) as conn:
        for source_id in source_ids:
            rows = conn.execute(
                """
                SELECT target_title, raw_json
                FROM work_graph_edges
                WHERE work_id = ?
                  AND relation_type IN ('topic', 'keyword')
                ORDER BY target_id
                """,
                (source_id,),
            ).fetchall()
            identity = _gap_identity(f"catalog/sources/{source_id}", "sources")
            for row in rows:
                for term in _graph_topic_terms(dict(row)):
                    key = term.lower()
                    if identity not in seen[key]["sources"]:
                        seen[key]["sources"].add(identity)
                        counts[key]["sources"] += 1
                    labels.setdefault(key, term)


def _graph_topic_terms(row: dict[str, Any]) -> list[str]:
    terms = []
    if title := str(row.get("target_title") or "").strip():
        terms.append(title)
    try:
        raw = json.loads(str(row.get("raw_json") or "{}"))
    except json.JSONDecodeError:
        raw = {}
    if isinstance(raw, dict):
        if display := _raw_display_name(raw):
            terms.append(display)
        for field in ("subfield", "field", "domain"):
            if display := _raw_display_name(raw.get(field)):
                terms.append(display)
    return sorted(set(terms))


def _raw_display_name(value: object) -> str:
    if isinstance(value, dict):
        return str(value.get("display_name") or value.get("name") or "").strip()
    if isinstance(value, str):
        return value.strip()
    return ""


def _project_argument_gaps(argument: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for source_key, finding_type in (
        ("findings", "argument-finding"),
        ("gap_findings", "argument-gap"),
    ):
        for finding in argument.get(source_key) or []:
            finding_kind = str(finding.get("kind") or "finding")
            advice = str(finding.get("advice") or "").strip()
            seed = advice or _argument_next_action(finding_kind)
            canonical = _argument_gap_kind(finding_kind)
            gap = _gap_payload(
                {
                    "topic": f"Project argument: {finding_kind}",
                    "project_path": argument["project_path"],
                    "thesis_path": argument["thesis_path"],
                    "finding_kind": finding_kind,
                    "finding_source": finding_type,
                    "source_count": 0,
                    "digest_count": 0,
                    "note_count": argument["node_count"],
                    "proposed_seed": seed,
                },
                kind=canonical,
                target=argument["thesis_path"] or argument["project_path"],
                why=_argument_gap_why(finding_kind, argument),
                next_actions=[seed] if seed else [],
                impact=_argument_impact(finding),
                confidence=2,
                actionability=1 if seed else 0,
            )
            if advice:
                gap["advice"] = advice
            rows.append(gap)
    return rows


def _project_paper_readiness_gaps(vault: Path, project_path: str) -> list[dict[str, Any]]:
    readiness = project_export_readiness(vault, project_path)
    if readiness["ready"]:
        return []
    missing = ", ".join(readiness["missing"])
    return [
        _gap_payload(
            {
                "topic": "Project paper readiness",
                "project_path": readiness["project_path"],
                "missing": readiness["missing"],
                "source_count": 0,
                "digest_count": 0,
                "note_count": 0,
                "proposed_seed": "run project frame-paper and check supporting notes",
            },
            kind="paper-readiness",
            target=readiness["project_path"],
            why=f"Project is not export-ready: {missing}",
            next_actions=["run project frame-paper and check supporting notes"],
            impact=2,
            confidence=2,
            actionability=1,
        )
    ]


def _argument_gap_kind(finding_kind: str) -> str:
    if finding_kind in {"no-refutation"}:
        return "argument-uncountered"
    if finding_kind in {"fragility", "conflict"}:
        return "argument-fragile"
    return "argument-unsupported"


def _argument_next_action(finding_kind: str) -> str:
    if finding_kind == "no-refutation":
        return "add or preserve checked counterpoint notes"
    if finding_kind == "conflict":
        return "resolve or preserve the contradiction"
    if finding_kind == "fragility":
        return "add independent support"
    if finding_kind == "unstated-warrant":
        return "add supporting evidence notes"
    if finding_kind == "structural":
        return "seed checked notes around the thesis"
    return "curate checked notes or links around the project thesis"


def _argument_gap_why(finding_kind: str, argument: dict[str, Any]) -> str:
    if finding_kind == "no-refutation":
        return "The checked project argument has support but no checked counterpoint."
    if finding_kind == "conflict":
        return "The checked project argument contains a contradiction that needs disposition."
    if finding_kind == "fragility":
        return "The checked project argument depends on too little independent support."
    if finding_kind == "no-support":
        return "The checked project argument has no checked supporting note."
    if finding_kind == "thin-argument":
        return (
            f"The checked project argument has only {argument['relation_count']} "
            "curated relation(s)."
        )
    return "The checked project argument is missing an actionable structural element."


def _argument_impact(finding: dict[str, Any]) -> int:
    return 2 if str(finding.get("severity") or "").lower() == "high" else 1


def _add_search_gap_hits(
    vault: Path,
    counts: dict[str, dict[str, int]],
    seen: dict[str, dict[str, set[str]]],
    labels: dict[str, str],
    retrieval: dict[str, dict[str, Any]],
) -> None:
    from memoria_vault.runtime.search_index import SEARCH_MANIFEST, answer_query

    if not (vault / SEARCH_MANIFEST).is_file():
        return

    for key, label in sorted(labels.items()):
        answer = answer_query(vault, label, k=5)
        retrieval[key] = {
            "engine": answer["engine"],
            "sources": answer["sources"],
        }
        for source in answer["sources"]:
            bucket = _retrieval_bucket(source)
            if not bucket:
                continue
            identity = _gap_identity(str(source["path"]), bucket)
            if identity in seen[key][bucket]:
                continue
            seen[key][bucket].add(identity)
            counts[key][bucket] += 1


def _missing_full_text_gaps(vault: Path) -> list[dict[str, Any]]:
    gaps = []
    for source in state.catalog_sources(vault):
        if source["text_status"] == "full-text" or not _is_current_catalog_source(source):
            continue
        source_id = str(source["source_id"])
        text_status = str(source.get("text_status") or "missing")
        gaps.append(
            _gap_payload(
                {
                    "topic": source["title"],
                    "source_count": 1,
                    "digest_count": 0,
                    "note_count": 0,
                    "proposed_seed": "acquire full text or attach user-supplied text",
                    "source_id": source_id,
                    "source_ids": [source_id],
                    "text_status": text_status,
                },
                kind="full-text-missing",
                target=f"catalog/sources/{source_id}",
                why=(
                    f"`catalog/sources/{source_id}` is checked but has "
                    f"`text_status: {text_status}`."
                ),
                next_actions=["acquire full text or attach user-supplied text"],
                impact=2,
                confidence=2,
                actionability=1,
            )
        )
    return gaps


def _write_full_text_gap_attention(
    vault: Path,
    gaps: list[dict[str, Any]],
    *,
    machine: str | None,
) -> tuple[list[str], str]:
    if machine is None:
        return [], ""
    paths = []
    for gap in gaps:
        source_id = str(gap.get("source_id") or "").strip()
        if not source_id:
            continue
        source = state.catalog_source(vault, source_id)
        if source is None:
            continue
        rel = normalize_path(f"inbox/flag-gap-full-text-{safe_filename(source_id)}.md")
        path = vault / rel
        if path.exists():
            continue
        title = f"Full text needed for {source_id}"
        target = f"catalog/sources/{source_id}"
        text_status = str(source.get("text_status") or gap.get("text_status") or "missing")
        finding = (
            f"Gap analysis found `{target}` has `text_status: {text_status}`; "
            "checked digests and retrieval require full text."
        )
        write_frontmatter_doc(
            path,
            {
                "title": title,
                "projection": "attention",
                "attention_kind": "flag",
                "attention_status": "open",
                "finding": finding,
                "agent_recommendation": "issues-found",
                "target": target,
                "raised_by": "analyze-gaps",
                "loudness": "alert",
                "created": date.today().isoformat(),
            },
            (
                f"# Finding\n\n{finding}\n\n# Evidence\n\n"
                f"`{target}` must acquire or attach full text before digest compilation.\n"
            ),
            create_parent=True,
        )
        paths.append(rel)
    if not paths:
        return [], ""
    append_journal_event(
        vault,
        {
            "event": "check-fired",
            "check": "source-full-text",
            "status": "failed",
            "operation": "analyze-gaps",
            "outputs": sorted(paths),
        },
        machine=machine,
    )
    commit = commit_writer_changes(
        vault,
        "flag gap full text",
        sorted(paths),
        machine=machine,
    )
    return sorted(paths), commit


def _write_gap_discovery_candidates(
    vault: Path,
    gaps: list[dict[str, Any]],
    *,
    machine: str | None,
) -> tuple[list[str], str]:
    if machine is None:
        return [], ""
    source_ids = {
        source_id
        for gap in gaps
        for source_id in _gap_source_ids(gap)
        if state.catalog_source(vault, source_id)
    }
    edges_by_source = _candidate_edges(vault, source_ids)
    if not edges_by_source:
        return [], ""
    from memoria_vault.runtime.enrichment import _write_discovery_candidate

    captured = _captured_work_ids(vault)
    steering_tokens = _steering_tokens(vault)
    relevance_by_path: dict[str, dict[str, Any]] = {}
    new_paths = []
    for source_id in sorted(edges_by_source):
        source = state.catalog_source(vault, source_id)
        if source is None:
            continue
        for edge in edges_by_source[source_id]:
            if _edge_is_captured(edge, captured):
                continue
            rel = _discovery_candidate_rel(source_id, edge)
            existed = (vault / rel).exists()
            path = _write_discovery_candidate(
                vault,
                source,
                edge,
                raised_by="analyze-gaps",
            )
            relevance = _discovery_relevance(steering_tokens, source, edge)
            relevance_by_path[path] = relevance
            changed = _annotate_discovery_candidate(vault, path, relevance)
            if not existed or changed:
                new_paths.append(path)
    if not new_paths:
        return [], ""
    new_paths = _sort_discovery_candidate_paths(new_paths, relevance_by_path)
    append_journal_event(
        vault,
        {
            "event": "derived",
            "operation": "analyze-gaps",
            "outputs": new_paths,
        },
        machine=machine,
    )
    commit = commit_writer_changes(
        vault,
        "propose gap discovery candidates",
        new_paths,
        machine=machine,
    )
    for gap in gaps:
        related = _sort_discovery_candidate_paths(
            set(new_paths) & set(_candidate_paths_for_gap(gap, edges_by_source)),
            relevance_by_path,
        )
        if related:
            gap["discovery_candidate_paths"] = related
    return new_paths, commit


def _steering_tokens(vault: Path) -> set[str]:
    path = vault / "steering.md"
    if not path.is_file():
        return set()
    return _relevance_tokens(path.read_text(encoding="utf-8"))


def _discovery_relevance(
    steering_tokens: set[str],
    source: dict[str, Any],
    edge: dict[str, Any],
) -> dict[str, Any]:
    title_overlap = sorted(
        steering_tokens
        & _relevance_tokens(edge.get("target_title"), edge.get("target_id"), edge.get("target_doi"))
    )
    tag_tokens = set()
    for term in _catalog_source_terms(source):
        tag_tokens.update(_relevance_tokens(term))
    tag_overlap = sorted(steering_tokens & tag_tokens)
    citation_overlap = 2 if str(edge.get("relation_type")) == "references" else 1
    channel = "ranked" if title_overlap or tag_overlap else "exploration"
    score = 3 * len(title_overlap) + 2 * len(tag_overlap) + citation_overlap
    if channel == "exploration":
        score = 0
    return {
        "discovery_relevance_score": score,
        "discovery_relevance_channel": channel,
        "discovery_relevance_factors": {
            "title_overlap": title_overlap,
            "tag_overlap": tag_overlap,
            "citation_overlap": citation_overlap,
        },
    }


def _relevance_tokens(*values: object) -> set[str]:
    text = " ".join(str(value) for value in values if value)
    return {
        token
        for token in re.findall(r"[a-z0-9]{3,}", text.casefold())
        if token not in _DISCOVERY_RELEVANCE_STOPWORDS and not token.isdigit()
    }


def _annotate_discovery_candidate(vault: Path, rel: str, relevance: dict[str, Any]) -> bool:
    path = vault / rel
    if not path.is_file():
        return False
    frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
    changed = False
    for key, value in relevance.items():
        if frontmatter.get(key) != value:
            frontmatter[key] = value
            changed = True
    if changed:
        write_frontmatter_doc(path, frontmatter, body, create_parent=True)
    return changed


def _sort_discovery_candidate_paths(
    paths: Iterable[str],
    relevance_by_path: dict[str, dict[str, Any]],
) -> list[str]:
    return sorted(
        paths,
        key=lambda path: (
            relevance_by_path.get(path, {}).get("discovery_relevance_channel") != "ranked",
            -int(relevance_by_path.get(path, {}).get("discovery_relevance_score") or 0),
            path,
        ),
    )


def _discovery_candidate_channels(vault: Path, paths: Iterable[str]) -> dict[str, int]:
    counts = {"ranked": 0, "exploration": 0}
    for rel in paths:
        channel = str(read_frontmatter(vault / rel).get("discovery_relevance_channel") or "")
        if channel in counts:
            counts[channel] += 1
    return counts


def _tag_candidates(vault: Path) -> list[dict[str, Any]]:
    existing_tags = {
        normalized
        for _rel, frontmatter in _checked_concepts(vault)
        for term in _frontmatter_gap_terms(frontmatter)
        for normalized in _tag_term_forms(term)
    }
    existing_tags.update(_controlled_tag_terms(vault))
    counts: dict[str, int] = defaultdict(int)
    refs: dict[str, set[str]] = defaultdict(set)
    for rel, frontmatter in _checked_concepts(vault):
        if frontmatter.get("type") not in {"work", "digest"}:
            continue
        path = vault / rel
        _frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
        text = " ".join(
            str(value)
            for value in (frontmatter.get("title"), frontmatter.get("description"), body)
            if str(value).strip()
        )
        tokens = [
            token
            for token in re.findall(r"[a-z][a-z0-9]+", text.casefold())
            if len(token) > 2 and token not in _TAG_CANDIDATE_STOPWORDS
        ]
        for left, right in pairwise(tokens):
            phrase = f"{left} {right}"
            if phrase in existing_tags:
                continue
            counts[phrase] += 1
            refs[phrase].add(rel)
    rows = [
        {"phrase": phrase, "count": count, "refs": sorted(refs[phrase])}
        for phrase, count in counts.items()
        if count >= _TAG_CANDIDATE_MIN_COUNT
    ]
    return sorted(rows, key=lambda row: (-int(row["count"]), str(row["phrase"])))[
        :_TAG_CANDIDATE_LIMIT
    ]


def _write_tag_candidate_attention(
    vault: Path,
    candidates: list[dict[str, Any]],
    *,
    machine: str | None,
) -> tuple[list[str], str]:
    if machine is None or not candidates:
        return [], ""
    new_paths = []
    for candidate in candidates:
        phrase = str(candidate["phrase"])
        rel = _tag_candidate_rel(phrase)
        path = vault / rel
        if path.exists():
            continue
        refs = [str(ref) for ref in candidate.get("refs") or []]
        target = refs[0] if refs else "works"
        write_frontmatter_doc(
            path,
            {
                "title": f"Review tag candidate: {phrase}",
                "projection": "attention",
                "attention_kind": "candidate",
                "attention_status": "open",
                "candidate_tag": phrase,
                "target": target,
                "source_count": len(refs),
                "raised_by": "analyze-gaps",
                "loudness": "notice",
                "created": date.today().isoformat(),
            },
            f"# Candidate Tag\n\n{phrase}\n\n# Evidence\n\n"
            + "\n".join(f"- `{ref}`" for ref in refs)
            + "\n",
            create_parent=True,
        )
        new_paths.append(rel)
    if not new_paths:
        return [], ""
    append_journal_event(
        vault,
        {
            "event": "derived",
            "operation": "analyze-gaps",
            "outputs": sorted(new_paths),
        },
        machine=machine,
    )
    commit = commit_writer_changes(
        vault,
        "propose tag candidates",
        sorted(new_paths),
        machine=machine,
    )
    return sorted(new_paths), commit


def _tag_candidate_rel(phrase: str) -> str:
    slug = safe_filename(phrase.replace(" ", "-"))
    return normalize_path(f"inbox/candidate-tag-{slug}.md")


def _controlled_tag_terms(vault: Path) -> set[str]:
    vocabulary = schema_lib.load_vocabulary(vault / "system/vocabulary.md")
    return {
        normalized
        for terms in vocabulary.values()
        for term in terms
        for normalized in _tag_term_forms(term)
    }


def _tag_term_forms(term: str) -> set[str]:
    text = str(term).strip().casefold()
    if not text:
        return set()
    return {text, text.replace("-", " ")}


def _candidate_edges(vault: Path, source_ids: Iterable[str]) -> dict[str, list[dict[str, Any]]]:
    ids = sorted(set(source_ids))
    if not ids or not state.db_path(vault).is_file():
        return {}
    rows = []
    with state.connect(vault) as conn:
        for source_id in ids:
            rows.extend(
                conn.execute(
                    """
                    SELECT work_id, relation_type, target_id, target_title, target_doi,
                           source_provider
                    FROM work_graph_edges
                    WHERE work_id = ?
                      AND relation_type IN ('references', 'related')
                    ORDER BY work_id, relation_type, target_id
                    """,
                    (source_id,),
                ).fetchall()
            )
    edges: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        edges[row["work_id"]].append(dict(row))
    return edges


def _coverage_round_robin(candidates: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    remaining = sorted(
        candidates,
        key=lambda row: (
            str(row["relation_type"]) != "references",
            str(row["source_id"]),
            str(row["candidate_work_id"]),
        ),
    )
    selected = []
    used_sources: set[str] = set()
    while remaining and len(selected) < limit:
        index = next(
            (idx for idx, row in enumerate(remaining) if str(row["source_id"]) not in used_sources),
            0,
        )
        row = remaining.pop(index)
        selected.append(row)
        used_sources.add(str(row["source_id"]))
        if len(used_sources) >= len({str(item["source_id"]) for item in remaining}):
            used_sources.clear()
    return selected


def _contrary_channel_items(vault: Path, *, limit: int) -> list[dict[str, str]]:
    rows = []
    for rel, frontmatter in _checked_concepts(vault):
        contradictions = frontmatter.get("contradictions")
        if not isinstance(contradictions, list):
            continue
        for target in contradictions:
            target_ref = str(target).strip()
            if not target_ref:
                continue
            rows.append(
                {
                    "path": rel,
                    "title": str(frontmatter.get("title") or Path(rel).stem),
                    "target": target_ref,
                    "why": f"Contrary lane: checked concept `{rel}` declares contradiction `{target_ref}`.",
                }
            )
    rows = sorted(rows, key=lambda row: (row["path"], row["target"]))
    remaining = max(0, limit - len(rows))
    if remaining:
        rows.extend(_nli_contrary_channel_items(vault, limit=remaining))
    return rows[:limit]


def _nli_contrary_channel_items(vault: Path, *, limit: int) -> list[dict[str, str]]:
    from memoria_vault.runtime.integrity import (
        NLI_REFUTED,
        surface_tensions,
    )

    try:
        result = surface_tensions(vault, max_pairs=limit, tier2=False)
    except Exception:  # noqa: BLE001 -- exploration must degrade to honest empty.
        return []
    rows = []
    for candidate in result.get("candidates") or []:
        if candidate.get("verdict") != NLI_REFUTED:
            continue
        left = str(candidate.get("left") or "").strip()
        right = str(candidate.get("right") or "").strip()
        if not left or not right:
            continue
        rows.append(
            {
                "path": left,
                "title": str(candidate.get("left_title") or left),
                "target": right,
                "why": (
                    "Contrary lane: NLI REFUTED candidate between "
                    f"`{left}` and `{right}` ({candidate.get('warrant')})."
                ),
            }
        )
    return rows[:limit]


def _gap_source_ids(gap: dict[str, Any]) -> list[str]:
    ids = []
    if isinstance(gap.get("source_id"), str):
        ids.append(str(gap["source_id"]))
    source_ids = gap.get("source_ids")
    if isinstance(source_ids, list):
        ids.extend(str(source_id) for source_id in source_ids if str(source_id).strip())
    for source in gap.get("retrieval_sources") or []:
        source_id = _source_id_from_path(str(source.get("path") or ""))
        if source_id:
            ids.append(source_id)
    return sorted(set(ids))


def _source_ids_from_seen(identities: set[str]) -> list[str]:
    return sorted(
        identity.removeprefix("sources:")
        for identity in identities
        if identity.startswith("sources:")
    )


def _candidate_paths_for_gap(
    gap: dict[str, Any],
    edges_by_source: dict[str, list[dict[str, Any]]],
) -> list[str]:
    return [
        _discovery_candidate_rel(source_id, edge)
        for source_id in _gap_source_ids(gap)
        for edge in edges_by_source.get(source_id, [])
    ]


def _citation_neighborhood_gaps(vault: Path) -> list[dict[str, Any]]:
    sources = [
        source for source in state.catalog_sources(vault) if _is_current_catalog_source(source)
    ]
    source_ids = [str(source["source_id"]) for source in sources]
    edges_by_source = _candidate_edges(vault, source_ids)
    if not edges_by_source:
        return []
    captured = _captured_work_ids(vault)
    source_by_id = {str(source["source_id"]): source for source in sources}
    gaps = []
    for source_id in sorted(edges_by_source):
        source = source_by_id.get(source_id)
        if source is None:
            continue
        candidate_ids = sorted(
            {
                str(edge["target_id"])
                for edge in edges_by_source[source_id]
                if not _edge_is_captured(edge, captured)
            }
        )
        if not candidate_ids:
            continue
        count = len(candidate_ids)
        seed = "review discovered citation-neighborhood candidates"
        gaps.append(
            _gap_payload(
                {
                    "topic": f"Citation neighborhood: {source['title']}",
                    "source_count": 1,
                    "digest_count": 0,
                    "note_count": 0,
                    "proposed_seed": seed,
                    "source_id": source_id,
                    "source_ids": [source_id],
                },
                kind="citation-neighborhood",
                target=f"catalog/sources/{source_id}",
                why=(
                    f"`catalog/sources/{source_id}` has {count} uncaptured "
                    "references or related Works in provider metadata."
                ),
                next_actions=[seed],
                impact=1,
                confidence=2,
                actionability=1,
                candidate_work_ids=candidate_ids,
            )
        )
    return gaps


def _captured_work_ids(vault: Path) -> set[str]:
    captured = set()
    for source in state.catalog_sources(vault):
        captured.add(str(source["source_id"]).casefold())
        if source.get("doi"):
            captured.add(str(source["doi"]).casefold())
        identifiers = source.get("identifiers") or {}
        if isinstance(identifiers, dict):
            captured.update(str(value).casefold() for value in identifiers.values() if value)
    return captured


def _edge_is_captured(edge: dict[str, Any], captured: set[str]) -> bool:
    return any(
        str(value).casefold() in captured
        for value in (edge.get("target_id"), edge.get("target_doi"))
        if value
    )


def _discovery_candidate_rel(source_id: str, edge: dict[str, Any]) -> str:
    return normalize_path(
        "inbox/candidate-work-"
        f"{safe_filename(source_id)}-"
        f"{safe_filename(str(edge['relation_type']))}-"
        f"{safe_filename(str(edge['target_id']))}.md"
    )


def _retrieval_bucket(source: dict[str, Any]) -> str:
    path = str(source.get("path") or "")
    source_type = source.get("type")
    if path.startswith(("graph-neighborhoods/", "catalog/sources/")) or (
        path.startswith("works/") and path.endswith("/fulltext.md")
    ):
        return "sources"
    if path.startswith("works/") or source_type in {"work", "digest"}:
        return "digests"
    if path.startswith("notes/") or source_type == "note":
        return "notes"
    return ""


def _gap_identity(path: str, bucket: str) -> str:
    if bucket == "sources":
        source_id = _source_id_from_path(path)
        if source_id:
            return f"sources:{source_id}"
    return f"{bucket}:{path}"


def _source_id_from_path(path: str) -> str:
    rel = normalize_path(path)
    if rel.startswith("works/") and rel.endswith(".md"):
        parts = rel.split("/")
        if len(parts) == 3 and parts[2] in {"fulltext.md", "record.md", "digest.md"}:
            return parts[1]
        if len(parts) == 2:
            return Path(rel).stem
    if rel.startswith("graph-neighborhoods/") and rel.endswith(".md"):
        return Path(rel).stem
    if rel.startswith("catalog/sources/"):
        parts = rel.split("/")
        if len(parts) >= 3:
            return parts[2]
    return ""


def analyze_project_argument(vault: Path, project_path: str) -> dict[str, Any]:
    """Return a small argument-health lens for one checked project."""
    vault = Path(vault)
    project_rel = _project_rel(vault, project_path)
    project = _checked_frontmatter(vault, project_rel, "project")
    thesis_raw = str(project.get("thesis") or "").strip()
    if not thesis_raw:
        return _project_argument_empty(project_rel, "", "missing-thesis")

    thesis_rel = _concept_rel(thesis_raw)
    notes = {
        rel: frontmatter
        for rel, frontmatter in _checked_concepts(vault)
        if frontmatter.get("type") == "note" and _is_current_note(vault, rel, frontmatter)
    }
    thesis = notes.get(thesis_rel)
    if thesis is None:
        return _project_argument_empty(project_rel, thesis_rel, "missing-or-unchecked-thesis")

    edges = _note_edges(notes)
    component = _argument_component(thesis_rel, edges)
    component_edges = [
        edge for edge in edges if edge["source"] in component and edge["target"] in component
    ]
    counts = {
        relation: sum(1 for edge in component_edges if edge["type"] == relation)
        for relation in ("supports", "contradicts", "extends")
    }
    relation_count = len(component_edges)
    findings = _argument_findings(counts, relation_count)
    saturation_conditions = _argument_saturation_conditions(counts, relation_count)
    return {
        "project_path": project_rel,
        "thesis_path": thesis_rel,
        "argument_stage": _argument_stage(counts, relation_count),
        "evidence_saturation": _argument_saturation(saturation_conditions, relation_count),
        "displayed_confidence": _argument_confidence(counts, relation_count),
        "saturation_conditions": saturation_conditions,
        "relation_count": relation_count,
        "supports_count": counts["supports"],
        "contradicts_count": counts["contradicts"],
        "extends_count": counts["extends"],
        "node_count": len(component),
        "findings": findings,
        "gap_findings": _argument_gap_findings(counts, relation_count),
        "advisories": _argument_advisories(counts, relation_count),
        "nodes": [
            {
                "path": rel,
                "title": str(notes[rel].get("title") or Path(rel).stem),
                "role": "thesis" if rel == thesis_rel else "note",
            }
            for rel in sorted(component)
        ],
        "edges": sorted(
            component_edges, key=lambda edge: (edge["type"], edge["source"], edge["target"])
        ),
    }


def render_project_argument_canvas(vault: Path, project_path: str) -> dict[str, Any]:
    """Render the checked project argument graph as Obsidian JSON Canvas data."""
    project_rel = _project_rel(Path(vault), project_path)
    if (Path(vault) / _project_outline_rel(project_rel)).is_file():
        project_slice = read_project_slice(vault, project_rel)
        nodes = [{"path": member["path"]} for member in project_slice["members"]]
        return _canvas_from_nodes_edges(nodes, project_slice["edges"])
    result = analyze_project_argument(vault, project_path)
    return _canvas_from_nodes_edges(result["nodes"], result["edges"])


def _canvas_from_nodes_edges(
    nodes_in: list[dict[str, Any]], edges_in: list[dict[str, str]]
) -> dict[str, Any]:
    node_ids = {
        node["path"]: f"n-{hashlib.sha256(node['path'].encode()).hexdigest()[:12]}"
        for node in nodes_in
    }
    nodes = []
    for index, node in enumerate(nodes_in):
        nodes.append(
            {
                "id": node_ids[node["path"]],
                "type": "file",
                "file": node["path"],
                "x": (index % 3) * 360,
                "y": (index // 3) * 240,
                "width": 300,
                "height": 180,
            }
        )
    edges = []
    for index, edge in enumerate(edges_in):
        source = node_ids.get(edge["source"])
        target = node_ids.get(edge["target"])
        if not source or not target:
            continue
        edges.append(
            {
                "id": f"e-{index}-{source}-{target}",
                "fromNode": source,
                "toNode": target,
                "label": edge["type"],
            }
        )
    return {"nodes": nodes, "edges": edges}


def write_project_argument_canvas(
    vault: Path,
    project_path: str,
    *,
    commit: bool = False,
    machine: str | None = None,
) -> dict[str, Any]:
    """Write the checked project argument graph as a generated Canvas projection."""
    vault = Path(vault)
    project_rel = _project_rel(vault, project_path)
    canvas_rel = _project_canvas_rel(project_rel)
    canvas = render_project_argument_canvas(vault, project_rel)
    canvas_path = vault / canvas_rel
    canvas_path.parent.mkdir(parents=True, exist_ok=True)
    canvas_path.write_text(json.dumps(canvas, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    event = None
    commit_id = ""
    if commit:
        event = append_journal_event(
            vault,
            {
                "event": "run",
                "run_id": f"projection:{canvas_rel}",
                "workflow": "render-project-argument-canvas",
                "status": "done",
                "inputs": [project_rel],
                "outputs": [canvas_rel],
            },
            machine=machine,
        )
        commit_id = commit_writer_changes(
            vault,
            "render project argument canvas",
            [canvas_rel],
            machine=machine,
        )
    return {
        "project_path": project_rel,
        "canvas_path": canvas_rel,
        "node_count": len(canvas["nodes"]),
        "edge_count": len(canvas["edges"]),
        "event": event,
        "commit": commit_id,
    }


def propose_project_slice(
    vault: Path,
    project_path: str,
    *,
    query: str = "",
    limit: int = 20,
) -> dict[str, Any]:
    """Propose checked note membership for a project slice using BM25 only."""
    from memoria_vault.runtime.search_index import search_checked_index

    vault = Path(vault)
    if limit < 1:
        raise ValueError("project slice limit must be at least 1")
    project_rel = _project_rel(vault, project_path)
    project = _checked_frontmatter(vault, project_rel, "project")
    retrieval_query = _project_slice_query(vault, project_rel, project, query)
    notes = _checked_notes_by_path(vault)
    members = []
    skipped = []
    for hit in search_checked_index(vault, retrieval_query, k=max(limit * 4, limit)):
        rel = str(hit["path"])
        frontmatter = notes.get(rel)
        if frontmatter is None:
            continue
        note_id = str(frontmatter.get("id") or "").strip()
        if not note_id:
            skipped.append({"path": rel, "reason": "missing stable note id"})
            continue
        members.append(
            {
                "id": note_id,
                "path": rel,
                "title": str(frontmatter.get("title") or Path(rel).stem),
                "reasoning": _project_slice_reason(retrieval_query, float(hit["score"])),
                "order": len(members),
                "score": float(hit["score"]),
                "check_status": "checked",
            }
        )
        if len(members) >= limit:
            break
    return {
        "project_path": project_rel,
        "outline_path": _project_outline_rel(project_rel),
        "retrieval_engine": "bm25",
        "query": retrieval_query,
        "members": members,
        "skipped": skipped,
    }


def write_project_outline(
    vault: Path,
    project_path: str,
    *,
    query: str = "",
    limit: int = 20,
    commit: bool = False,
    machine: str | None = None,
) -> dict[str, Any]:
    """Write a host-neutral project outline from a BM25 project-slice proposal."""
    vault = Path(vault)
    proposal = propose_project_slice(vault, project_path, query=query, limit=limit)
    outline_rel = str(proposal["outline_path"])
    outline_path = vault / outline_rel
    outline_path.parent.mkdir(parents=True, exist_ok=True)
    outline_path.write_text(_outline_text(proposal["members"]), encoding="utf-8")
    project_slice = read_project_slice(vault, str(proposal["project_path"]))
    event = None
    commit_id = ""
    if commit:
        event = append_journal_event(
            vault,
            {
                "event": "run",
                "run_id": f"project-slice:{outline_rel}",
                "workflow": "write-project-slice",
                "status": "done",
                "inputs": [proposal["project_path"]],
                "outputs": [outline_rel],
                "retrieval_engine": proposal["retrieval_engine"],
                "query": proposal["query"],
                "member_count": len(project_slice["members"]),
            },
            machine=machine,
        )
        commit_id = commit_writer_changes(
            vault,
            "write project slice outline",
            [outline_rel],
            machine=machine,
        )
    return {
        "project_path": proposal["project_path"],
        "outline_path": outline_rel,
        "retrieval_engine": proposal["retrieval_engine"],
        "query": proposal["query"],
        "members": project_slice["members"],
        "edges": project_slice["edges"],
        "missing": project_slice["missing"],
        "skipped": proposal["skipped"],
        "member_count": len(project_slice["members"]),
        "edge_count": len(project_slice["edges"]),
        "event": event,
        "commit": commit_id,
    }


def compose_project_draft(
    vault: Path,
    project_path: str,
    *,
    token_budget: int = 4000,
    commit: bool = False,
    machine: str | None = None,
) -> dict[str, Any]:
    """Compose a deterministic draft from a project's outline slice."""
    from memoria_vault.runtime.evidence import (
        EvidenceMarker,
        evidence_ids_in_text,
        mint_evidence_id,
        serialize_evidence_marker,
    )

    vault = Path(vault)
    project_rel = _project_rel(vault, project_path)
    project = _checked_frontmatter(vault, project_rel, "project")
    project_slice = read_project_slice(vault, project_rel)
    members = list(project_slice["members"])
    if not members:
        raise ValueError("project outline has no checked members")
    token_budget = max(200, int(token_budget))
    per_node_budget = max(80, token_budget // max(len(members), 1))
    existing_ids = _existing_evidence_ids(vault, evidence_ids_in_text)
    allocated_ids = set(existing_ids)
    lines = [
        "---",
        "type: draft",
        f"project: {project_rel}",
        "generated_by: compose-project-draft",
        "---",
        "",
        f"# {project.get('title') or Path(project_rel).stem}",
        "",
        f"Slice includes {len(members)} checked notes.",
        "",
    ]
    evidence_markers = []
    for member in members:
        note_rel = str(member["path"])
        frontmatter, body = split_frontmatter((vault / note_rel).read_text(encoding="utf-8"))
        evidence_id = mint_evidence_id(allocated_ids)
        allocated_ids.add(evidence_id)
        items = _draft_evidence_items(vault, frontmatter)
        evidence_type = _draft_evidence_type(items)
        state_value = "complete" if items else "evidence-incomplete"
        marker = EvidenceMarker(
            evidence_id=evidence_id,
            evidence_type=evidence_type,
            state=state_value,
            review_required=evidence_type in {"implicit", "multi-hop"},
            items=tuple(items),
        )
        evidence_markers.append(marker)
        block_anchor = f"^blk-{evidence_id.removeprefix('ev-')}"
        excerpt = _draft_note_excerpt(body, per_node_budget)
        lines.extend(
            [
                f"## {member['title']}",
                "",
                f"Source note: `{note_rel}`",
                "",
                f"{excerpt} {block_anchor} {serialize_evidence_marker(marker)}".strip(),
                "",
            ]
        )
    draft_rel = _project_draft_rel(project_rel)
    draft_path = vault / draft_rel
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    rebuild = state.rebuild_evidence_sets_from_markers(
        vault,
        run_id=f"compose-project-draft:{project_rel}",
    )
    draft = read_project_draft(vault, project_rel)
    event = None
    commit_id = ""
    if commit:
        event = append_journal_event(
            vault,
            {
                "event": "run",
                "run_id": f"compose-project-draft:{draft_rel}",
                "workflow": "compose-project-draft",
                "status": "done",
                "inputs": [project_rel, project_slice["outline_path"]],
                "outputs": [draft_rel],
                "member_count": len(members),
                "evidence_set_count": len(evidence_markers),
            },
            machine=machine,
        )
        commit_id = commit_writer_changes(
            vault,
            "compose project draft",
            [draft_rel],
            machine=machine,
        )
    return {
        **draft,
        "member_count": len(members),
        "evidence_set_count": len(evidence_markers),
        "rebuild": rebuild,
        "event": event,
        "commit": commit_id,
    }


def read_project_draft(vault: Path, project_path: str) -> dict[str, Any]:
    """Read a composed project draft and its evidence markers."""
    from memoria_vault.runtime.evidence import extract_evidence_markers

    vault = Path(vault)
    project_rel = _project_rel(vault, project_path)
    _checked_frontmatter(vault, project_rel, "project")
    draft_rel = _project_draft_rel(project_rel)
    draft_path = vault / draft_rel
    if not draft_path.is_file():
        return {
            "project_path": project_rel,
            "draft_path": draft_rel,
            "content": "",
            "evidence_markers": [],
            "evidence_sets": [],
        }
    content = draft_path.read_text(encoding="utf-8")
    markers = extract_evidence_markers(content)
    evidence_sets = [
        row for row in state.evidence_sets(vault) if str(row["block_ref"]).startswith(draft_rel)
    ]
    return {
        "project_path": project_rel,
        "draft_path": draft_rel,
        "content": content,
        "evidence_markers": [
            {
                "id": marker.evidence_id,
                "type": marker.evidence_type,
                "state": marker.state,
                "review_required": marker.review_required,
                "items": list(marker.items),
            }
            for marker in markers
        ],
        "evidence_sets": evidence_sets,
    }


def verify_project_draft(
    vault: Path,
    project_path: str,
    *,
    max_findings: int = 20,
) -> dict[str, Any]:
    """Run deterministic structural/evidence checks for a composed project draft."""
    vault = Path(vault)
    project_rel = _project_rel(vault, project_path)
    _checked_frontmatter(vault, project_rel, "project")
    draft_rel = _project_draft_rel(project_rel)
    draft_path = vault / draft_rel
    if not draft_path.is_file():
        return {
            "project_path": project_rel,
            "draft_path": draft_rel,
            "ready": False,
            "ok": False,
            "status": "missing-draft",
            "missing": ["draft"],
            "findings": [{"kind": "missing-draft", "severity": "high"}],
            "evidence_sets": [],
            "rebuild": {"deleted": 0, "inserted": 0},
        }
    rebuild = state.rebuild_evidence_sets_from_markers(
        vault,
        run_id=f"verify-project-draft:{project_rel}",
    )
    draft = read_project_draft(vault, project_rel)
    findings = []
    disposed = _disposed_evidence_ids(vault)
    for row in draft["evidence_sets"]:
        if row["id"] in disposed:
            continue
        if row["state"] == "evidence-incomplete":
            findings.append(
                {
                    "kind": "evidence-incomplete",
                    "severity": "high",
                    "evidence_id": row["id"],
                    "block_ref": row["block_ref"],
                }
            )
        if row["review_required"]:
            findings.append(
                {
                    "kind": "review-required",
                    "severity": "medium",
                    "evidence_id": row["id"],
                    "block_ref": row["block_ref"],
                }
            )
    findings.extend(_draft_structural_reference_findings(vault, draft["content"]))
    findings.extend(_draft_number_findings(vault, project_rel, draft["content"]))
    total_findings = len(findings)
    max_findings = max(1, int(max_findings))
    findings = findings[:max_findings]
    ok = not findings and bool(draft["evidence_sets"])
    return {
        "project_path": project_rel,
        "draft_path": draft_rel,
        "ready": ok,
        "ok": ok,
        "status": "verified" if ok else "needs-review",
        "missing": [] if ok else _verification_finding_labels(findings),
        "findings": findings,
        "evidence_sets": draft["evidence_sets"],
        "rebuild": rebuild,
        "max_findings": max_findings,
        "triaged_count": total_findings,
    }


def resolve_evidence_review(
    vault: Path,
    evidence_id: str,
    *,
    decision: str,
    reason: str = "",
    machine: str | None = None,
) -> dict[str, Any]:
    """Record a PI disposition for one evidence-set review item."""
    evidence_id = evidence_id.strip()
    decision = decision.strip().lower()
    if not re.fullmatch(r"ev-[0-9a-f]{8}", evidence_id):
        raise ValueError(f"invalid evidence id: {evidence_id}")
    if decision not in {"accept", "reject"}:
        raise ValueError("evidence review decision must be accept or reject")
    return append_journal_event(
        Path(vault),
        {
            "event": "resolved",
            "operation": "resolve-evidence-review",
            "evidence_id": evidence_id,
            "decision": decision,
            "reason": reason.strip(),
        },
        machine=machine,
    )


def promote_draft_passage(
    vault: Path,
    project_path: str,
    *,
    title: str,
    passage: str,
    source_id: str = "",
    commit: bool = False,
    machine: str | None = None,
) -> dict[str, Any]:
    """Extract a selected draft passage into a new unchecked note."""
    vault = Path(vault)
    project_rel = _project_rel(vault, project_path)
    draft_rel = _project_draft_rel(project_rel)
    draft_path = vault / draft_rel
    if not draft_path.is_file():
        raise FileNotFoundError(draft_path)
    selected = passage.strip()
    if not selected:
        raise ValueError("draft passage is required")
    draft_content = draft_path.read_text(encoding="utf-8")
    if selected not in draft_content:
        raise ValueError("draft passage was not found in the project draft")
    note_title = title.strip()
    if not note_title:
        raise ValueError("draft note title is required")
    note_rel = _unique_note_rel(vault, note_title)
    note_source = _draft_source_id(source_id)
    frontmatter: dict[str, Any] = {
        "type": "note",
        "title": note_title,
        "tags": [],
        "links": {},
    }
    if note_source:
        frontmatter["source_id"] = f"catalog/sources/{note_source}"
    apply_universal_concept_frontmatter(frontmatter, note_rel)
    content = frontmatter_doc(frontmatter, selected + "\n")
    run_id = f"draft-writeback:{draft_rel}:{Path(note_rel).stem}"
    stage = stage_concept(
        vault,
        note_rel,
        content,
        inputs=[{"id": draft_rel, "sha256": sha256_file(draft_path)}],
        operation="promote-draft-passage",
        run_id=run_id,
        actor="pi",
        machine=machine,
    )
    materialized = materialize_unchecked(vault, note_rel)
    link = _draft_note_markdown_link(draft_rel, note_rel, note_title)
    if link not in draft_content:
        draft_path.write_text(
            draft_content.rstrip() + "\n\n## Extracted Notes\n\n" + f"- {link}\n",
            encoding="utf-8",
        )
    event = append_journal_event(
        vault,
        {
            "event": "resolved",
            "operation": "promote-draft-passage",
            "run_id": run_id,
            "draft_path": draft_rel,
            "output_id": note_rel,
            "source_id": frontmatter.get("source_id", ""),
        },
        machine=machine,
    )
    commit_id = ""
    if commit:
        commit_id = commit_writer_changes(
            vault,
            "promote draft passage",
            [note_rel, draft_rel],
            machine=machine,
        )
    return {
        "project_path": project_rel,
        "draft_path": draft_rel,
        "note_path": note_rel,
        "check_status": state.concept_check_status(vault, note_rel),
        "source_id": frontmatter.get("source_id", ""),
        "stage": stage,
        "materialized": materialized,
        "event": event,
        "commit": commit_id,
    }


def read_project_slice(vault: Path, project_path: str) -> dict[str, Any]:
    """Read a project's host-neutral outline slice and computed argument edges."""
    vault = Path(vault)
    project_rel = _project_rel(vault, project_path)
    _checked_frontmatter(vault, project_rel, "project")
    outline_rel = _project_outline_rel(project_rel)
    outline_path = vault / outline_rel
    if not outline_path.is_file():
        return {
            "project_path": project_rel,
            "outline_path": outline_rel,
            "members": [],
            "edges": [],
            "missing": [],
        }

    notes = _checked_notes_by_path(vault)
    by_id = {str(fm.get("id") or ""): rel for rel, fm in notes.items() if fm.get("id")}
    members = []
    missing = []
    for index, item in enumerate(_parse_outline_members(outline_path.read_text(encoding="utf-8"))):
        rel = by_id.get(item["id"])
        if rel is None:
            missing.append({"id": item["id"], "line": item["line"]})
            continue
        members.append(
            {
                "id": item["id"],
                "path": rel,
                "title": str(notes[rel].get("title") or Path(rel).stem),
                "reasoning": item["reasoning"],
                "order": index,
                "check_status": "checked",
            }
        )
    member_paths = {member["path"] for member in members}
    edges = [
        edge
        for edge in _note_edges({rel: notes[rel] for rel in member_paths})
        if edge["source"] in member_paths and edge["target"] in member_paths
    ]
    return {
        "project_path": project_rel,
        "outline_path": outline_rel,
        "members": members,
        "edges": sorted(edges, key=lambda edge: (edge["source"], edge["target"], edge["type"])),
        "missing": missing,
    }


def render_project_export_markdown(vault: Path, project_path: str) -> dict[str, Any]:
    """Render a deterministic Markdown export for one checked project."""
    vault = Path(vault)
    argument = analyze_project_argument(vault, project_path)
    project_rel = argument["project_path"]
    project_frontmatter, project_body = split_frontmatter(
        (vault / project_rel).read_text(encoding="utf-8")
    )
    project_title = str(project_frontmatter.get("title") or Path(project_rel).stem)
    node_titles = {node["path"]: node["title"] for node in argument["nodes"]}

    lines = [f"# {project_title}", ""]
    description = str(project_frontmatter.get("description") or "").strip()
    if description:
        lines.extend([description, ""])
    body = project_body.strip()
    if body:
        lines.extend(["## Project", "", body, ""])
    _append_project_export_paper_plan(lines, project_frontmatter.get("paper_plan"))

    lines.extend(
        [
            "## Argument Snapshot",
            "",
            f"- Project: `{project_rel}`",
            f"- Thesis: `{argument['thesis_path'] or 'none'}`",
            f"- Stage: {argument['argument_stage']}",
            f"- Evidence saturation: {argument['evidence_saturation']}",
            f"- Displayed confidence: {argument['displayed_confidence']}",
            f"- Relations: {argument['relation_count']}",
            f"- Supports: {argument['supports_count']}",
            f"- Contradicts: {argument['contradicts_count']}",
            f"- Extends: {argument['extends_count']}",
            "",
        ]
    )
    _append_project_export_nodes(lines, argument["nodes"])
    _append_project_export_edges(lines, argument["edges"], node_titles)
    _append_project_export_hubs(lines, _project_export_hubs(vault, project_rel))
    _append_project_export_findings(lines, "Findings", argument["findings"])
    _append_project_export_findings(lines, "Gap Findings", argument["gap_findings"])
    _append_project_export_findings(lines, "Advisories", argument["advisories"])
    _append_project_export_references(lines, vault)
    return {
        "project_path": project_rel,
        "format": "markdown",
        "content": "\n".join(lines).rstrip() + "\n",
        "node_count": argument["node_count"],
        "edge_count": len(argument["edges"]),
        "relation_count": argument["relation_count"],
    }


def _append_project_export_paper_plan(lines: list[str], paper_plan: object) -> None:
    if not isinstance(paper_plan, dict) or not any(paper_plan.values()):
        return
    labels = {
        "target": "Target",
        "audience": "Audience",
        "research_question": "Research question",
        "central_contribution": "Central contribution",
        "gap_statement": "Gap statement",
        "limitations": "Limitations",
    }
    lines.extend(["## Paper Plan", ""])
    for key, label in labels.items():
        value = str(paper_plan.get(key) or "").strip()
        if value:
            lines.append(f"- {label}: {value}")
    for key, label in (("claim_evidence_map", "Claim evidence"), ("figure_plan", "Figure plan")):
        value = paper_plan.get(key)
        if isinstance(value, dict) and value:
            rendered = "; ".join(
                f"{claim}: {evidence}" for claim, evidence in sorted(value.items())
            )
            lines.append(f"- {label}: {rendered}")
    lines.append("")


def write_project_export(
    vault: Path,
    project_path: str,
    *,
    export_format: str = "markdown",
    output_path: str = "",
    ready_only: bool = False,
    draft: bool = False,
) -> dict[str, Any]:
    """Write or return a deterministic project export."""
    vault = Path(vault)
    export_format = export_format.strip().lower() or "markdown"
    if export_format not in {"markdown", "docx", "pdf", "odt"}:
        raise ValueError(f"unsupported project export format: {export_format}")
    if draft:
        rendered = render_project_draft_export_markdown(vault, project_path)
        readiness = rendered["readiness"]
    else:
        readiness = project_export_readiness(vault, project_path)
        if ready_only and not readiness["ready"]:
            missing = ", ".join(readiness["missing"])
            raise ValueError(f"project is not export-ready: {missing}")
        rendered = render_project_export_markdown(vault, project_path)
    content = str(rendered["content"])
    output = output_path.strip()
    if export_format == "markdown":
        display_path = _write_project_export_output(vault, output, content) if output else ""
        return {
            **rendered,
            "format": export_format,
            "output_path": display_path,
            "content": "" if display_path else content,
            "readiness": readiness,
        }

    if not output:
        raise ValueError("project export --output is required for Pandoc formats")
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        raise RuntimeError(f"Pandoc is required for project export format: {export_format}")
    target = _project_export_output_path(vault, output)
    with TemporaryDirectory(prefix="memoria-project-export-") as tmp:
        source = Path(tmp) / "project.md"
        source.write_text(content, encoding="utf-8")
        proc = subprocess.run(
            [pandoc, str(source), "-o", str(target)],
            check=False,
            text=True,
            capture_output=True,
        )
    if proc.returncode:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "Pandoc export failed")
    return {
        **rendered,
        "format": export_format,
        "output_path": _project_export_display_path(vault, target),
        "content": "",
        "readiness": readiness,
    }


def render_project_draft_export_markdown(vault: Path, project_path: str) -> dict[str, Any]:
    """Render a verified project draft with internal evidence markers stripped."""
    vault = Path(vault)
    verification = verify_project_draft(vault, project_path)
    if not verification["ok"]:
        reasons = ", ".join(_verification_finding_labels(verification["findings"]))
        raise ValueError(f"project draft is not export-ready: {reasons}")
    draft = read_project_draft(vault, project_path)
    _frontmatter, body = split_frontmatter(draft["content"])
    return {
        "project_path": draft["project_path"],
        "draft_path": draft["draft_path"],
        "readiness": verification,
        "format": "markdown",
        "content": _render_draft_export_body(vault, body).strip() + "\n",
        "node_count": 0,
        "edge_count": 0,
        "relation_count": 0,
    }


def project_export_readiness(vault: Path, project_path: str) -> dict[str, Any]:
    """Return structural export readiness for a checked paper project."""
    vault = Path(vault)
    project_rel = _project_rel(vault, project_path)
    project = _checked_frontmatter(vault, project_rel, "project")
    plan = project.get("paper_plan") if isinstance(project.get("paper_plan"), dict) else {}
    missing = [field for field in PAPER_PLAN_REQUIRED_FIELDS if not plan.get(field)]
    argument = analyze_project_argument(vault, project_rel)
    # ponytail: structural gate only; semantic claim-evidence grading needs the aspect model.
    if not argument["thesis_path"]:
        missing.append("thesis")
    if argument["supports_count"] < 1:
        missing.append("checked support")
    if (vault / _project_draft_rel(project_rel)).is_file():
        draft_verification = verify_project_draft(vault, project_rel)
        missing.extend(draft_verification["missing"])
    return {
        "ready": not missing,
        "status": "export-ready" if not missing else "needs-work",
        "missing": missing,
        "project_path": project_rel,
    }


def _append_project_export_nodes(lines: list[str], nodes: list[dict[str, Any]]) -> None:
    if not nodes:
        return
    lines.extend(["## Argument Nodes", ""])
    for node in nodes:
        lines.append(f"- {node['title']} ({node['role']}): `{node['path']}`")
    lines.append("")


def _append_project_export_edges(
    lines: list[str], edges: list[dict[str, Any]], node_titles: dict[str, str]
) -> None:
    if not edges:
        return
    lines.extend(["## Argument Links", ""])
    for edge in edges:
        source = node_titles.get(edge["source"], edge["source"])
        target = node_titles.get(edge["target"], edge["target"])
        lines.append(f"- {source} --{edge['type']}--> {target}")
    lines.append("")


def _append_project_export_hubs(lines: list[str], hubs: list[dict[str, str]]) -> None:
    if not hubs:
        return
    lines.extend(["## Project Hubs", ""])
    for hub in hubs:
        description = f" -- {hub['description']}" if hub["description"] else ""
        lines.append(f"- {hub['title']}: `{hub['path']}`{description}")
    lines.append("")


def _append_project_export_findings(
    lines: list[str], heading: str, rows: list[dict[str, Any]]
) -> None:
    if not rows:
        return
    lines.extend([f"## {heading}", ""])
    for row in rows:
        severity = row.get("severity", "info")
        kind = row.get("kind", "finding")
        advice = str(row.get("advice") or "").strip()
        suffix = f": {advice}" if advice else ""
        lines.append(f"- {severity}: {kind}{suffix}")
    lines.append("")


def _append_project_export_references(lines: list[str], vault: Path) -> None:
    references = vault / "bibliography.bib"
    if not references.is_file():
        return
    text = references.read_text(encoding="utf-8").strip()
    if not text:
        return
    lines.extend(["## References", "", "```bibtex", text, "```", ""])


def _project_export_hubs(vault: Path, project_rel: str) -> list[dict[str, str]]:
    base = vault / "hubs"
    if not base.exists():
        return []
    rows = []
    for path in iter_markdown(base, skip_dirs=frozenset()):
        frontmatter = read_frontmatter(path)
        rel = path.relative_to(vault).as_posix()
        if (
            frontmatter.get("type") == "hub"
            and _has_checked_verdict(vault, rel)
            and _is_current_concept(vault, rel, frontmatter)
            and _frontmatter_mentions_project(frontmatter, project_rel)
        ):
            rows.append(
                {
                    "path": rel,
                    "title": str(frontmatter.get("title") or path.stem),
                    "description": str(frontmatter.get("description") or ""),
                }
            )
    return sorted(rows, key=lambda row: (row["title"].lower(), row["path"]))


def _frontmatter_mentions_project(frontmatter: dict[str, Any], project_rel: str) -> bool:
    project_refs = {
        project_rel,
        project_rel.removesuffix("/project.md"),
        project_rel.removesuffix(".md"),
        Path(project_rel).stem,
    }
    return any(
        value in project_refs for value in _frontmatter_string_values(frontmatter.get("project"))
    ) or any(
        value in project_refs for value in _frontmatter_string_values(frontmatter.get("links"))
    )


def _frontmatter_string_values(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        text = value.strip()
        if text:
            yield text
        return
    if isinstance(value, dict):
        for item in value.values():
            yield from _frontmatter_string_values(item)
        return
    if isinstance(value, list):
        for item in value:
            yield from _frontmatter_string_values(item)


def _write_project_export_output(vault: Path, output_path: str, content: str) -> str:
    target = _project_export_output_path(vault, output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return _project_export_display_path(vault, target)


def _project_export_output_path(vault: Path, output_path: str) -> Path:
    target = Path(output_path).expanduser()
    if not target.is_absolute():
        target = vault / target
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def _project_export_display_path(vault: Path, target: Path) -> str:
    try:
        return target.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(target)


def _checked_frontmatter(vault: Path, relpath: str, concept_type: str) -> dict[str, Any]:
    path = vault / relpath
    if not path.is_file():
        raise FileNotFoundError(path)
    frontmatter = read_frontmatter(path)
    if frontmatter.get("type") != concept_type or not _has_checked_verdict(vault, relpath):
        raise ValueError(f"{relpath} is not a checked {concept_type}")
    return frontmatter


def _checked_concepts(vault: Path) -> Iterable[tuple[str, dict[str, Any]]]:
    for root in ("works", "notes"):
        base = vault / root
        if not base.exists():
            continue
        for path in iter_markdown(base, skip_dirs=frozenset()):
            frontmatter = read_frontmatter(path)
            rel = path.relative_to(vault).as_posix()
            if _has_checked_verdict(vault, rel) and _is_current_concept(vault, rel, frontmatter):
                yield rel, frontmatter


def _checked_notes_by_path(vault: Path) -> dict[str, dict[str, Any]]:
    return {
        rel: frontmatter
        for rel, frontmatter in _checked_concepts(vault)
        if frontmatter.get("type") == "note" and _is_current_note(vault, rel, frontmatter)
    }


def _bucket(relpath: str, frontmatter: dict[str, Any]) -> str:
    concept_type = frontmatter.get("type")
    if relpath.startswith("works/") and concept_type in {"work", "digest"}:
        return "digests"
    if relpath.startswith("notes/") and concept_type == "note":
        return "notes"
    return ""


def _terms(frontmatter: dict[str, Any]) -> list[str]:
    return _frontmatter_gap_terms(frontmatter)


def _frontmatter_gap_terms(frontmatter: dict[str, Any]) -> list[str]:
    out = []
    for field in ("scope_topics", "topics", "tags", "keywords", "research_area", "methodology"):
        out.extend(_string_list(frontmatter.get(field)))
    facets = frontmatter.get("facets") if isinstance(frontmatter.get("facets"), dict) else {}
    for field in ("research_area", "methodology", "topics"):
        out.extend(_string_list(facets.get(field)))
    massw = frontmatter.get("massw")
    if isinstance(massw, dict):
        out.extend(str(value) for value in massw.values() if str(value).strip())
    return sorted(set(out))


def _add_project_gap_terms(
    vault: Path,
    argument: dict[str, Any],
    counts: dict[str, dict[str, int]],
    seen: dict[str, dict[str, set[str]]],
    labels: dict[str, str],
) -> None:
    project_rel = str(argument.get("project_path") or "").strip()
    if project_rel:
        for term in _frontmatter_gap_terms(_checked_frontmatter(vault, project_rel, "project")):
            key = term.lower()
            labels.setdefault(key, term)
            counts[key]

    thesis_rel = str(argument.get("thesis_path") or "").strip()
    if not thesis_rel:
        return
    try:
        thesis = _checked_frontmatter(vault, thesis_rel, "note")
    except (FileNotFoundError, ValueError):
        return
    identity = _gap_identity(thesis_rel, "notes")
    for term in _frontmatter_gap_terms(thesis):
        key = term.lower()
        if identity not in seen[key]["notes"]:
            seen[key]["notes"].add(identity)
            counts[key]["notes"] += 1
        labels.setdefault(key, term)


def _project_argument_empty(project_rel: str, thesis_rel: str, finding: str) -> dict[str, Any]:
    return {
        "project_path": project_rel,
        "thesis_path": thesis_rel,
        "argument_stage": "cold-start",
        "evidence_saturation": "unknown",
        "displayed_confidence": "below-threshold",
        "saturation_conditions": {
            "mature_graph": False,
            "has_support": False,
            "has_refutation": False,
        },
        "relation_count": 0,
        "supports_count": 0,
        "contradicts_count": 0,
        "extends_count": 0,
        "node_count": 0,
        "findings": [{"kind": finding, "severity": "high"}],
        "gap_findings": [
            {
                "kind": "structural",
                "severity": "high",
                "advice": "add a checked thesis note before argument analysis",
            }
        ],
        "advisories": [],
        "nodes": [],
        "edges": [],
    }


def _argument_stage(counts: dict[str, int], relation_count: int) -> str:
    if relation_count == 0:
        return "cold-start"
    if relation_count < 3:
        return "developing"
    if counts["contradicts"] > 0:
        return "contested"
    return "supported"


def _argument_findings(counts: dict[str, int], relation_count: int) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if relation_count == 0:
        findings.append({"kind": "thin-argument", "severity": "high"})
    elif relation_count < 3:
        findings.append({"kind": "thin-argument", "severity": "medium"})
    if counts["supports"] == 0:
        findings.append({"kind": "no-support", "severity": "high"})
    if counts["contradicts"] == 0:
        findings.append({"kind": "no-refutation", "severity": "medium"})
    return findings


def _argument_saturation_conditions(counts: dict[str, int], relation_count: int) -> dict[str, bool]:
    return {
        "mature_graph": relation_count >= 3,
        "has_support": counts["supports"] > 0,
        "has_refutation": counts["contradicts"] > 0,
    }


def _argument_saturation(conditions: dict[str, bool], relation_count: int) -> str:
    if relation_count == 0:
        return "unknown"
    return "saturated" if all(conditions.values()) else "unsaturated"


def _argument_confidence(counts: dict[str, int], relation_count: int) -> str:
    if relation_count < 3:
        return "below-threshold"
    if counts["contradicts"] > 0:
        return "contested"
    if counts["supports"] > 0:
        return "supported"
    return "below-threshold"


def _argument_gap_findings(counts: dict[str, int], relation_count: int) -> list[dict[str, str]]:
    gaps: list[dict[str, str]] = []
    if relation_count == 0:
        gaps.append(
            {
                "kind": "structural",
                "severity": "high",
                "advice": "seed checked notes around the thesis",
            }
        )
    if counts["supports"] == 0:
        gaps.append(
            {
                "kind": "unstated-warrant",
                "severity": "high",
                "advice": "add supporting evidence notes",
            }
        )
    elif counts["supports"] == 1 and relation_count >= 3:
        gaps.append(
            {
                "kind": "fragility",
                "severity": "medium",
                "advice": "add independent support",
            }
        )
    if counts["contradicts"] > 0:
        gaps.append(
            {
                "kind": "conflict",
                "severity": "medium",
                "advice": "resolve or preserve the contradiction",
            }
        )
    return gaps


def _argument_advisories(counts: dict[str, int], relation_count: int) -> list[dict[str, str]]:
    advisories: list[dict[str, str]] = []
    if 0 < relation_count < 3:
        advisories.append(
            {
                "kind": "structural",
                "severity": "medium",
                "advice": "connect at least three checked notes before treating the argument as mature",
            }
        )
    if relation_count >= 3 and counts["contradicts"] == 0:
        advisories.append(
            {
                "kind": "refutation",
                "severity": "medium",
                "advice": "seek a counterargument before treating the thesis as saturated",
            }
        )
    return advisories


def _note_edges(notes: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    edges = []
    for source, frontmatter in notes.items():
        for link_type in ("supports", "contradicts", "extends"):
            for raw in _link_values(frontmatter, link_type):
                target = _link_target(raw)
                if target in notes and target != source:
                    edges.append({"source": source, "target": target, "type": link_type})
    return edges


def _argument_component(root: str, edges: list[dict[str, str]]) -> set[str]:
    graph: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        graph[edge["source"]].add(edge["target"])
        graph[edge["target"]].add(edge["source"])
    seen = {root}
    queue = [root]
    while queue:
        node = queue.pop(0)
        for neighbor in sorted(graph.get(node, set())):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen


def _link_values(frontmatter: dict[str, Any], link_type: str) -> list[Any]:
    links = frontmatter.get("links")
    if not isinstance(links, dict):
        return []
    values = links.get(link_type) or []
    return values if isinstance(values, list) else [values]


def _link_target(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("target") or value.get("path") or value.get("id") or value.get("note")
    if not isinstance(value, str) or not value.strip():
        return ""
    raw = value.strip()
    if raw.startswith("[[") and raw.endswith("]]"):
        raw = raw[2:-2].split("|", 1)[0].split("#", 1)[0].strip()
    try:
        return _concept_rel(raw)
    except ValueError:
        return ""


def _is_current_concept(vault: Path, relpath: str, frontmatter: dict[str, Any]) -> bool:
    if not _is_current_frontmatter(frontmatter):
        return False
    return not relpath.startswith("notes/") or _is_current_note(vault, relpath, frontmatter)


def _is_current_frontmatter(frontmatter: dict[str, Any]) -> bool:
    return frontmatter.get("lifecycle") not in {"retracted", "archived"}


def _is_current_note(vault: Path, relpath: str, frontmatter: dict[str, Any]) -> bool:
    status = state.note_curation_status(vault, relpath)
    return _is_current_frontmatter(frontmatter) and status not in {"candidate", "rejected"}


def _digest_rel(path: str) -> str:
    rel = normalize_path(path)
    if "/" not in rel and not rel.endswith(".md"):
        rel = f"works/{rel}/digest.md"
    if not rel.endswith(".md"):
        rel += ".md"
    return rel


def _project_rel(vault: Path, path: str) -> str:
    rel = normalize_path(path)
    if "/" not in rel:
        flat = f"projects/{rel}.md"
        nested = f"projects/{rel}/project.md"
        return nested if (Path(vault) / nested).is_file() else flat
    if not rel.endswith(".md"):
        rel += ".md"
    if not rel.startswith("projects/"):
        raise ValueError(f"project must live under projects: {rel}")
    return rel


def _project_canvas_rel(project_rel: str) -> str:
    if project_rel.endswith("/project.md"):
        return f"{project_rel.removesuffix('/project.md')}/argument.canvas"
    return f"projects/{Path(project_rel).stem}/argument.canvas"


def _project_outline_rel(project_rel: str) -> str:
    if project_rel.endswith("/project.md"):
        return f"{project_rel.removesuffix('/project.md')}/outline.md"
    return f"projects/{Path(project_rel).stem}/outline.md"


def _project_draft_rel(project_rel: str) -> str:
    if project_rel.endswith("/project.md"):
        return f"{project_rel.removesuffix('/project.md')}/draft.md"
    return f"projects/{Path(project_rel).stem}/draft.md"


def _project_slice_query(
    vault: Path,
    project_rel: str,
    project: dict[str, Any],
    query: str,
) -> str:
    frontmatter, body = split_frontmatter((vault / project_rel).read_text(encoding="utf-8"))
    terms = [
        query,
        *list(_frontmatter_text_terms(frontmatter)),
        body,
    ]
    thesis_raw = str(project.get("thesis") or project.get("active_thesis") or "").strip()
    if thesis_raw:
        try:
            thesis_rel = _concept_rel(thesis_raw)
            thesis = _checked_frontmatter(vault, thesis_rel, "note")
            _thesis_fm, thesis_body = split_frontmatter(
                (vault / thesis_rel).read_text(encoding="utf-8")
            )
            terms.extend([*list(_frontmatter_text_terms(thesis)), thesis_body])
        except (FileNotFoundError, ValueError):
            terms.append(thesis_raw)
    text = " ".join(str(term).strip() for term in terms if str(term).strip())
    return text or Path(project_rel).stem


def _frontmatter_text_terms(frontmatter: dict[str, Any]) -> Iterable[str]:
    for field in (
        "title",
        "description",
        "research_question",
        "central_contribution",
        "gap_statement",
        "claim_text",
    ):
        value = frontmatter.get(field)
        if isinstance(value, str) and value.strip():
            yield value.strip()
    for field in ("scope_topics", "topics", "tags", "keywords", "research_area", "methodology"):
        yield from _string_list(frontmatter.get(field))
    plan = frontmatter.get("paper_plan")
    if isinstance(plan, dict):
        for field in ("research_question", "central_contribution", "gap_statement"):
            value = plan.get(field)
            if isinstance(value, str) and value.strip():
                yield value.strip()


def _project_slice_reason(query: str, score: float) -> str:
    label = " ".join(query.split())[:80]
    return f"BM25 score {score:.3f} for project query: {label}"


def _outline_text(members: Iterable[dict[str, Any]]) -> str:
    lines = []
    for member in members:
        note_id = str(member["id"]).strip()
        reasoning = str(member.get("reasoning") or "").strip()
        lines.append(f"- {note_id} — {reasoning}")
    return "\n".join(lines) + ("\n" if lines else "")


def _existing_evidence_ids(vault: Path, extractor: Any) -> set[str]:
    ids: set[str] = set()
    for path in sorted(vault.rglob("*.md")):
        rel = path.relative_to(vault)
        if any(part in {".git", ".memoria"} for part in rel.parts):
            continue
        ids.update(extractor(path.read_text(encoding="utf-8")))
    return ids


def _draft_evidence_items(vault: Path, frontmatter: dict[str, Any]) -> list[str]:
    items = []
    for source_id in _draft_source_ids(frontmatter):
        if state.catalog_source(vault, source_id):
            items.append(f"{source_id}#^p0001")
    return sorted(set(items))


def _draft_source_ids(frontmatter: dict[str, Any]) -> Iterable[str]:
    for field in ("work_id", "source_id"):
        value = frontmatter.get(field)
        if isinstance(value, str):
            source_id = _draft_source_id(value)
            if source_id:
                yield source_id
    evidence_set = frontmatter.get("evidence_set")
    values = evidence_set if isinstance(evidence_set, list) else [evidence_set]
    for value in values:
        if isinstance(value, str):
            source_id = _draft_source_id(value)
            if source_id:
                yield source_id


def _draft_source_id(value: str) -> str:
    text = value.strip().split("#", 1)[0].rstrip("/")
    if not text:
        return ""
    if text.startswith("catalog/sources/"):
        return text.rsplit("/", 1)[-1]
    if text.startswith(("works/", "graph-neighborhoods/")):
        return _source_id_from_path(text)
    if "/" not in text:
        return text
    return ""


def _draft_evidence_type(items: list[str]) -> str:
    if not items:
        return "implicit"
    return "single-span" if len(items) == 1 else "multi-span"


def _draft_note_excerpt(body: str, token_budget: int) -> str:
    text = body.strip()
    if not text:
        return "Abstain: this checked note has no draftable body text."
    words = text.split()
    if len(words) <= token_budget:
        return text
    return " ".join(words[:token_budget]).rstrip() + "\n\nAbstain: note text exceeded budget."


def _verification_finding_labels(findings: Iterable[dict[str, Any]]) -> list[str]:
    labels = []
    for finding in findings:
        kind = str(finding.get("kind") or "finding")
        evidence_id = str(finding.get("evidence_id") or "").strip()
        labels.append(f"{kind}:{evidence_id}" if evidence_id else kind)
    return labels


def _disposed_evidence_ids(vault: Path) -> set[str]:
    with state.connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT json_extract(payload_json, '$.evidence_id') AS evidence_id
            FROM journal_events
            WHERE json_extract(payload_json, '$.operation') = 'resolve-evidence-review'
              AND json_extract(payload_json, '$.decision') IN ('accept', 'reject')
            """
        ).fetchall()
    return {str(row["evidence_id"]) for row in rows if row["evidence_id"]}


def _draft_structural_reference_findings(vault: Path, content: str) -> list[dict[str, Any]]:
    refs = _draft_source_note_refs(content)
    if not refs:
        return [{"kind": "missing-structural-reference", "severity": "high"}]
    findings: list[dict[str, Any]] = []
    for reference in refs:
        try:
            rel = normalize_path(reference)
        except ValueError:
            findings.append(
                {
                    "kind": "broken-structural-reference",
                    "severity": "high",
                    "reference": reference,
                }
            )
            continue
        if not rel.endswith(".md"):
            rel += ".md"
        if not (vault / rel).is_file():
            findings.append(
                {
                    "kind": "broken-structural-reference",
                    "severity": "high",
                    "reference": reference,
                }
            )
            continue
        try:
            _checked_frontmatter(vault, rel, "note")
        except ValueError:
            findings.append(
                {
                    "kind": "unchecked-structural-reference",
                    "severity": "high",
                    "reference": reference,
                }
            )
    return findings


def _draft_source_note_refs(content: str) -> list[str]:
    return [
        match.group("path").strip()
        for match in re.finditer(r"(?m)^Source note:\s*`(?P<path>[^`]+)`\s*$", content)
        if match.group("path").strip()
    ]


def _draft_number_findings(vault: Path, project_rel: str, content: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    expected_count = len(read_project_slice(vault, project_rel)["members"])
    for match in re.finditer(r"Slice includes (?P<count>\d+) checked notes?\.", content):
        observed = int(match.group("count"))
        if observed != expected_count:
            findings.append(
                {
                    "kind": "deterministic-number-mismatch",
                    "severity": "high",
                    "number": "slice_checked_note_count",
                    "expected": expected_count,
                    "observed": observed,
                }
            )
    if re.search(r"\b(analysis-computed|analysis code|code-warrant)\b", content, re.I):
        findings.append(
            {
                "kind": "analysis-number-evidence-incomplete",
                "severity": "high",
            }
        )
    return findings


def _render_draft_export_body(vault: Path, content: str) -> str:
    from memoria_vault.runtime.evidence import parse_evidence_marker, parse_source_span_ref

    def citation(match: re.Match[str]) -> str:
        marker = parse_evidence_marker(match.group(0).strip())
        citekeys = []
        for item in marker.items:
            try:
                source = parse_source_span_ref(item)
            except ValueError:
                continue
            compact = state.compact_citation(vault, source.work_id)
            if compact.get("citekey"):
                citekeys.append(f"@{compact['citekey']}")
        return f" [{'; '.join(citekeys)}]" if citekeys else ""

    text = re.sub(r"\s*%%ev:\s*.*?%%", citation, content)
    return re.sub(r"\s+\^blk-[A-Za-z0-9_-]+", "", text)


def _draft_note_markdown_link(draft_rel: str, note_rel: str, title: str) -> str:
    start = Path(draft_rel).parent.as_posix()
    href = posixpath.relpath(note_rel, start=start)
    return f"[{title}]({href}) %%embed: {note_rel}%%"


def _parse_outline_members(text: str) -> list[dict[str, Any]]:
    members = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        raw = line.strip()
        if not raw.startswith("- "):
            continue
        body = raw[2:].strip()
        if not body:
            continue
        if " — " in body:
            note_id, reasoning = body.split(" — ", 1)
        elif " -- " in body:
            note_id, reasoning = body.split(" -- ", 1)
        else:
            note_id, reasoning = body, ""
        members.append({"id": note_id.strip(), "reasoning": reasoning.strip(), "line": line_number})
    return members


def _source_rel(path: str) -> str:
    rel = normalize_path(path)
    if not rel.startswith("catalog/sources/"):
        rel = f"catalog/sources/{rel}"
    rel = rel.rstrip("/")
    if rel == "catalog/sources" or rel.count("/") != 2:
        raise ValueError(f"source must be a catalog source row ref: {rel}")
    return rel


def _note_rel(path: str) -> str:
    rel = normalize_path(path)
    if "/" not in rel:
        rel = f"notes/{rel}"
    if not rel.endswith(".md"):
        rel += ".md"
    if not rel.startswith("notes/"):
        raise ValueError(f"note candidate must live under notes: {rel}")
    return rel


def _concept_rel(path: str) -> str:
    rel = normalize_path(path)
    if "/" not in rel:
        rel = f"notes/{rel}"
    if rel.startswith("catalog/sources/"):
        rel = rel.rstrip("/")
        if rel.count("/") != 2:
            raise ValueError(f"source must be a catalog source row ref: {rel}")
    elif not rel.endswith(".md"):
        rel += ".md"
    if not rel.startswith(("catalog/sources/", "sources/", "notes/", "hubs/")):
        raise ValueError(f"unsupported note link target: {rel}")
    return rel


def _checked_concept(vault: Path, relpath: str) -> dict[str, Any]:
    path = vault / relpath
    if not path.is_file():
        raise FileNotFoundError(path)
    frontmatter = read_frontmatter(path)
    if not _has_checked_verdict(vault, relpath):
        raise ValueError(f"{relpath} is not checked")
    if not _is_current_frontmatter(frontmatter):
        raise ValueError(f"{relpath} is not current")
    return frontmatter


def _has_checked_verdict(vault: Path, relpath: str) -> bool:
    return is_consumable_checked_file(vault, relpath)


def _require_tool(policy: dict[str, Any], tool: str) -> None:
    if tool not in (policy.get("allowed_tools") or []):
        raise PermissionError(f"operation {policy['operation_id']} does not allow {tool}")


def _require_path(policy: dict[str, Any], path: str) -> None:
    rel = normalize_path(path)
    for raw_prefix in policy.get("allowed_paths") or []:
        prefix = normalize_path(str(raw_prefix)).rstrip("/")
        if rel == prefix or rel.startswith(prefix + "/"):
            return
    raise PermissionError(f"operation {policy['operation_id']} cannot access {rel}")


def _unique_note_rel(vault: Path, title: str) -> str:
    slug = safe_filename(title.lower().replace(" ", "-")).strip("._-") or "note"
    base = f"notes/{slug}.md"
    candidate = base
    index = 1
    while (vault / candidate).exists() or (vault / ".memoria/staging" / candidate).exists():
        index += 1
        candidate = f"notes/{slug}-{index}.md"
    return candidate


def _required_text(row: dict[str, Any], key: str) -> str:
    value = str(row.get(key) or "").strip()
    if not value:
        raise ValueError(f"note candidate requires {key}")
    return value


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item.strip()]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()
