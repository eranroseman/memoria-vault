"""Evidence-review queue assembly, facets, and honesty-card blocks (V2 slice 1).

The assembler, facets, filters and card projection are pure over their inputs.
The four vault-reading helpers at the bottom — dispositions, minted timestamps,
the span-source index and grounds previews — are the reads the engine collector
(V2R-B.4) needs to *build* those inputs; they only read. V2R-A owns every
disposition write; the queue only *reads* the events A journals, and it restates
its own accept-only clearing rule so the queue stays honest whether or not the
verify-side flip has landed.
"""

from __future__ import annotations

import datetime
import hashlib
import re
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.evidence import (
    evidence_ref_kind,
    parse_code_grounds_ref,
    parse_source_span_ref,
)
from memoria_vault.runtime.policy.paths import normalize_path

EVIDENCE_REVIEW_ROUTING_TYPES = ("implicit", "multi-hop", "incomplete")
PERMANENT_BLOCK_CURE = "edit the draft or the grounds; no disposition clears a permanent block"

_PROJECTS_PREFIX = "projects/"
_PROJECT_SUFFIX = "/project.md"


def assemble_evidence_review_queue(
    drafts: Iterable[Mapping[str, Any]],
    dispositions: Iterable[Mapping[str, Any]],
    *,
    minted_at: Mapping[str, str] | None = None,
    today: datetime.date,
) -> list[dict[str, Any]]:
    """Assemble the evidence-set queue (spec §1) — pure over its inputs.

    `drafts` are `knowledge.read_project_draft`-shaped mappings and
    `dispositions` are journal-ordered `resolve-evidence-review` payloads
    (latest last). Every row is an evidence-set row; SRD-gap entries are the
    collector's to union in, never this assembler's.
    """
    latest = _latest_dispositions(dispositions)
    minted = dict(minted_at or {})
    queue: list[dict[str, Any]] = []
    for draft in drafts:
        content = str(draft["content"])
        for row in draft["evidence_sets"]:
            entry = _queue_entry(draft, row, content, latest.get(str(row["id"])), minted, today)
            if entry is not None:
                queue.append(entry)
    return queue


def queue_facets(queue: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Evidence-set denominators over the whole queue (spec §6 honest totals).

    No `kind` facet: the pure queue is evidence-only, and the view owns the
    evidence-set/srd-gap split it merges over these numbers.
    """
    routing: dict[str, int] = {}
    projects: dict[str, int] = {}
    total = 0
    for entry in queue:
        total += 1
        routing_type = str(entry["routing_type"])
        if routing_type:
            routing[routing_type] = routing.get(routing_type, 0) + 1
        project = str(entry["project_path"])
        projects[project] = projects.get(project, 0) + 1
    return {"routing_type": routing, "project": projects, "total": total}


def filter_queue(
    queue: Iterable[Mapping[str, Any]],
    *,
    routing_type: str = "",
    project: str = "",
    min_age_days: int = 0,
) -> list[dict[str, Any]]:
    """Apply the facet filters conjunctively (spec §6); empty means no filter."""
    if routing_type and routing_type not in EVIDENCE_REVIEW_ROUTING_TYPES:
        raise ValueError(f"routing_type must be one of {EVIDENCE_REVIEW_ROUTING_TYPES}")
    if min_age_days < 0:
        raise ValueError("min_age_days must be a nonnegative integer")
    wanted_project = canonical_project(project) if project else ""
    selected: list[dict[str, Any]] = []
    for entry in queue:
        if routing_type and entry["routing_type"] != routing_type:
            continue
        if wanted_project and entry["project_path"] != wanted_project:
            continue
        # An unknown age counts as zero: a null is not evidence of age.
        if min_age_days and (entry["age_days"] or 0) < min_age_days:
            continue
        selected.append(dict(entry))
    return selected


def canonical_project(project: str) -> str:
    """Normalize the three accepted project spellings; reject every other one.

    `<name>`, `projects/<name>`, and `projects/<name>/project.md` all normalize
    to `projects/<name>/project.md`.
    """
    value = project.strip()
    name = value
    if value.startswith(_PROJECTS_PREFIX):
        name = value[len(_PROJECTS_PREFIX) :].removesuffix(_PROJECT_SUFFIX)
    if "/" in name or name in {"", ".", ".."}:
        raise ValueError(
            f"project must be <name>, projects/<name>, or projects/<name>/project.md: {project!r}"
        )
    return f"{_PROJECTS_PREFIX}{name}{_PROJECT_SUFFIX}"


def evidence_review_blocks(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Queue rows -> one nested view-spec card per evidence row.

    Trailing `srd-gap` rows pass their already-normalized U3 card through, after
    every evidence card.
    """
    blocks: list[dict[str, Any]] = []
    srd_blocks: list[dict[str, Any]] = []
    for row in rows:
        if row.get("kind") == "srd-gap":
            srd_blocks.append(dict(row["card_block"]))
            continue
        blocks.append(evidence_review_card(row))
    return blocks + srd_blocks


def evidence_review_card(row: Mapping[str, Any]) -> dict[str, Any]:
    """Project one evidence-set queue row into one nested U3 card (spec §2).

    A re-shaping only: every queue fact — `item_count`, `cure`, the routing type
    — is consumed from the row, never recomputed here.
    """
    evidence_id = str(row["evidence_id"])
    block_ref = str(row["block_ref"])
    previews = list(row.get("item_previews") or [])
    claim_text = str(row["claim_text"])
    age_days = row["age_days"]
    reviewable = bool(row["reviewable"])
    card: dict[str, Any] = {
        "id": evidence_id,
        "kind": "card",
        "ref": block_ref,
        "title": claim_text,
        "kind_line": "evidence-review",
        "review_kind": "evidence-set",
        "evidence_id": evidence_id,
        "project": str(row["project_path"]),
        "routing_type": str(row["routing_type"]),
        "reviewable": reviewable,
        "disposition": str(row["disposition"]),
        "item_count": int(row["item_count"]),
        "age_days": age_days,
        "age_s": int(age_days) * 86_400 if age_days is not None else 0,
        "age_label": f"{age_days}d" if age_days is not None else "",
        "body_data": {"kind": "untrusted_text", "text": claim_text},
    }
    if row.get("blocked_by"):
        card["blocked_by"] = [dict(finding) for finding in row["blocked_by"]]
        card["cure"] = str(row["cure"])
    for field in ("disposition_reason", "warrant"):
        value = str(row.get(field) or "").strip()
        if value:
            card[field] = value
    card.update(analysis_fields(row, previews))
    children: list[dict[str, Any]] = [
        {
            "id": f"{evidence_id}-grounds",
            "kind": "evidence-list",
            "ref": block_ref,
            "items": previews,
        },
        {
            "id": f"{evidence_id}-routing",
            "kind": "text",
            "text": routing_reason(row, previews),
        },
    ]
    if reviewable:
        children.append(
            {
                "id": f"{evidence_id}-actions",
                "kind": "action-row",
                # Spec §2 field 7: four equals, none pre-selected.
                "actions": [
                    {
                        "label": label,
                        "operation_id": "resolve-evidence",
                        "payload": {"evidence_id": evidence_id, "decision": decision},
                    }
                    for label, decision in (
                        ("Accept", "accept"),
                        ("Reject", "reject"),
                        ("Edit", "edit"),
                        ("Defer", "defer"),
                    )
                ],
            }
        )
    card["blocks"] = children
    return card


def routing_reason(row: Mapping[str, Any], previews: Sequence[Mapping[str, Any]]) -> str:
    """The deterministic routing sentence for one row (spec §7: no judgment)."""
    routing_type = str(row["routing_type"])
    if routing_type in {"implicit", "multi-hop"}:
        return routing_type
    if routing_type == "incomplete":
        failing = _first_failing(previews)
        if failing is not None:
            return f"evidence-incomplete: {failing['ref']} does not resolve"
        return "evidence-incomplete"
    blocked = list(row["blocked_by"])
    return str(blocked[0]["reason"]) if blocked else ""


def analysis_fields(
    row: Mapping[str, Any], previews: Sequence[Mapping[str, Any]]
) -> dict[str, str]:
    """Parent-owned analysis (spec §2 fields 4-6) for a reviewable row with holds.

    Empty for every other row, so a permanently blocked read-only card never
    carries analysis it cannot act on.
    """
    if not (row["reviewable"] and row["holds"]):
        return {}
    fields: dict[str, str] = {}
    arguments = {
        field: str(row.get(field) or "").strip() for field in ("argument_for", "argument_against")
    }
    if all(arguments.values()):  # never one-sided (spec §2 field 4)
        fields.update(arguments)
    fields["tipped_by"] = _tipping_factor(row, previews)
    certainty = str(row.get("certainty") or "").strip()
    if certainty:
        fields["certainty"] = certainty
    return fields


def evidence_dispositions(vault: Path) -> list[dict[str, Any]]:
    """Read `resolve-evidence-review` disposition events in journal order."""
    vault = Path(vault)
    if not state.db_path(vault).is_file():
        return []
    return [
        event
        for event in state.read_event_log(vault, event_types=["resolved"])
        if event.get("operation") == "resolve-evidence-review"
    ]


def evidence_minted_at(vault: Path) -> dict[str, str]:
    """Map evidence ids to their *first* `evidence-minted` timestamp.

    First, not latest: age is how long the claim has waited for a decision, and
    a later re-mint of the same id does not reset that wait.
    """
    vault = Path(vault)
    if not state.db_path(vault).is_file():
        return {}
    minted: dict[str, str] = {}
    for event in state.read_event_log(vault, event_types=["evidence-minted"]):
        evidence_id = str(event.get("evidence_id") or "")
        timestamp = str(event.get("timestamp") or "")
        if evidence_id and timestamp:
            minted.setdefault(evidence_id, timestamp)
    return minted


def span_source_index(vault: Path) -> dict[str, tuple[set[str], str]]:
    """Index catalog source content: work_id -> (resolvable pages, text).

    Read once per collection: every shown row's span previews resolve and
    excerpt against this one index rather than re-reading each blob.
    """
    vault = Path(vault)
    index: dict[str, tuple[set[str], str]] = {}
    for source in state.catalog_sources(vault, checked_only=False):
        work_id = str(source["work_id"])
        content_path = vault / normalize_path(str(source.get("content_path") or ""))
        if not content_path.is_file():
            index[work_id] = (set(), "")
            continue
        text = content_path.read_text(encoding="utf-8")
        index[work_id] = ({page.removeprefix("^") for page in re.findall(r"\^p\d{4,}", text)}, text)
    return index


def resolve_item_previews(
    vault: Path,
    items: Iterable[str],
    *,
    rows_by_id: Mapping[str, Mapping[str, Any]],
    span_sources: Mapping[str, tuple[set[str], str]],
) -> list[dict[str, Any]]:
    """Resolve one row's raw grounds refs into previews (spec §2 field 2).

    Every preview says whether its ref `resolves`; the descriptive keys are
    present-only, so an absent excerpt reads as absent rather than as empty text.
    """
    previews: list[dict[str, Any]] = []
    for item in items:
        kind = evidence_ref_kind(item)
        if kind == "code-grounds":
            ref = parse_code_grounds_ref(item)
            resolves = _code_grounds_resolves(vault, ref)
            previews.append(
                {
                    "ref": item,
                    "kind": kind,
                    "run_id": ref.run_id,
                    "artifact_id": ref.artifact_id,
                    "output_sha256": ref.output_sha256,
                    "resolves": resolves,
                    "completeness_status": "complete" if resolves else "evidence-incomplete",
                }
            )
        elif kind == "evidence-set":
            nested = rows_by_id.get(item)
            preview: dict[str, Any] = {"ref": item, "kind": kind, "resolves": nested is not None}
            if nested is not None:
                preview["expansion"] = {
                    "evidence_type": str(nested["type"]),
                    "completeness_status": str(nested["completeness_status"]),
                    "item_count": len(nested["items"]),
                }
            previews.append(preview)
        else:
            span = parse_source_span_ref(item)
            pages, text = span_sources.get(span.work_id, (set(), ""))
            preview = {
                "ref": item,
                "kind": kind,
                "work_id": span.work_id,
                "anchor": f"^{span.page}",
                "resolves": span.page in pages,
            }
            excerpt = _span_excerpt(text, span.page)
            if excerpt:
                preview["excerpt"] = excerpt
            previews.append(preview)
    return previews


def _code_grounds_resolves(vault: Path, ref: Any) -> bool:
    from memoria_vault.runtime.code.runs import code_grounds_complete

    return code_grounds_complete(
        Path(vault),
        run_id=ref.run_id,
        artifact_id=ref.artifact_id,
        output_sha256=ref.output_sha256,
    )


def _span_excerpt(text: str, page: str, *, limit: int = 240) -> str:
    for line in text.splitlines():
        if f"^{page}" in line:
            return re.sub(r"\s*\^p\d{4,}\s*", " ", line).strip()[:limit]
    return ""


def _tipping_factor(row: Mapping[str, Any], previews: Sequence[Mapping[str, Any]]) -> str:
    # Total by construction: every branch names something, so `tipped_by` is
    # never present-and-empty and needs no emptiness guard above.
    routing_type = str(row["routing_type"])
    if routing_type in {"implicit", "multi-hop"}:
        return f"type={routing_type}"
    failing = _first_failing(previews)
    return str(failing["ref"]) if failing is not None else "completeness_status=evidence-incomplete"


def _first_failing(previews: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    return next((preview for preview in previews if not preview["resolves"]), None)


def _latest_dispositions(
    dispositions: Iterable[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    """Latest event per evidence id wins, across all four decisions."""
    latest: dict[str, Mapping[str, Any]] = {}
    for event in dispositions:
        evidence_id = str(event.get("evidence_id") or "")
        if evidence_id:
            latest[evidence_id] = event
    return latest


def _queue_entry(
    draft: Mapping[str, Any],
    row: Mapping[str, Any],
    content: str,
    disposition: Mapping[str, Any] | None,
    minted: Mapping[str, str],
    today: datetime.date,
) -> dict[str, Any] | None:
    blocked_by = _permanent_findings(row, content)
    holds = _hold_findings(row)
    if not blocked_by and not holds:
        return None
    decision = str((disposition or {}).get("decision") or "")
    if decision == "defer" and _defer_active(disposition or {}, today):
        return None
    if decision == "accept" and _accept_clears(row, disposition or {}):
        holds = []
        if not blocked_by:
            return None
    evidence_id = str(row["id"])
    items = [str(item) for item in row["items"]]
    entry: dict[str, Any] = {
        "kind": "evidence-set",
        "evidence_id": evidence_id,
        "project_path": str(draft["project_path"]),
        "draft_path": str(draft["draft_path"]),
        "block_ref": str(row["block_ref"]),
        "claim_text": state.block_canonical_text_from_text(content, str(row["block_ref"])) or "",
        "items": items,
        "item_count": len(items),
        "evidence_type": str(row["type"]),
        "routing_type": _routing_type(row),
        "holds": [finding["kind"] for finding in holds],
        "blocked_by": blocked_by,
        "reviewable": bool(holds) and not blocked_by,
        "disposition": "rejected" if decision == "reject" else "open",
        "age_days": _age_days(minted.get(evidence_id), today),
    }
    if blocked_by:
        entry["cure"] = PERMANENT_BLOCK_CURE
    if decision == "reject":
        reason = str((disposition or {}).get("reason") or "").strip()
        if reason:
            entry["disposition_reason"] = reason
    warrant = str((disposition or {}).get("warrant") or "").strip()
    if warrant:
        entry["warrant"] = warrant
    for field in ("argument_for", "argument_against", "certainty"):
        value = str(row.get(field) or "").strip()
        if value:
            entry[field] = value
    return entry


def _permanent_findings(row: Mapping[str, Any], content: str) -> list[dict[str, str]]:
    # Reason strings verbatim from verify_project_draft (knowledge.py, the
    # `evidence-text-unbound` / `evidence-text-drift` findings).
    stored = row["block_text_sha256"]
    if not stored:
        return [
            {
                "kind": "evidence-text-unbound",
                "reason": "stored block-text binding is missing",
            }
        ]
    current = state.block_text_sha256_from_text(content, str(row["block_ref"]))
    if current is None:
        return [
            {
                "kind": "evidence-text-unbound",
                "reason": "anchored block text cannot be resolved",
            }
        ]
    if current != stored:
        return [
            {
                "kind": "evidence-text-drift",
                "reason": "anchored block text differs from its stored binding",
            }
        ]
    return []


def _hold_findings(row: Mapping[str, Any]) -> list[dict[str, str]]:
    holds: list[dict[str, str]] = []
    if str(row["completeness_status"]) == "evidence-incomplete":
        holds.append({"kind": "evidence-incomplete"})
    if row["review_required"]:
        holds.append({"kind": "review-required"})
    return holds


def _routing_type(row: Mapping[str, Any]) -> str:
    evidence_type = str(row["type"])
    if evidence_type in {"implicit", "multi-hop"}:
        return evidence_type
    if str(row["completeness_status"]) == "evidence-incomplete":
        return "incomplete"
    return ""


def _accept_clears(row: Mapping[str, Any], disposition: Mapping[str, Any]) -> bool:
    # Digests form (plan 22 S35.4 has landed): only an accept bound to the row's
    # current items digest clears; a legacy accept with no digest is inert.
    digest = str(disposition.get("items_sha256") or "")
    return bool(digest) and digest == _items_sha256(row["items"])


def _items_sha256(items: Sequence[str]) -> str:
    # Byte-identical to knowledge._evidence_items_sha256, which writes the
    # digests this rule reads.
    return hashlib.sha256("|".join(items).encode("utf-8")).hexdigest()


def _defer_active(disposition: Mapping[str, Any], today: datetime.date) -> bool:
    deferred_on = _event_date(str(disposition.get("timestamp") or ""))
    return deferred_on is not None and today <= deferred_on


def _age_days(timestamp: str | None, today: datetime.date) -> int | None:
    minted_on = _event_date(str(timestamp or ""))
    if minted_on is None:
        return None
    return max((today - minted_on).days, 0)


def _event_date(timestamp: str) -> datetime.date | None:
    try:
        return datetime.date.fromisoformat(timestamp[:10])
    except ValueError:
        return None


# Presentation-only, and never renamed: the raw queue's own spellings
# (`routing_type`, `disposition`) are the CLI's too (V2 plan, 2026-07-29
# raw-queue amendment §3). `items` and analysis are deliberately absent —
# a list row is claim + item count + routing reason (spec §3).
SUMMARY_FIELDS = (
    "evidence_id",
    "claim_text",
    "item_count",
    "routing_type",
    "reviewable",
    "cure",
    "age_days",
    "disposition",
    "warrant",
)


def summary_row(row: dict[str, Any]) -> dict[str, Any]:
    """Project one raw queue row into its list summary.

    Both arms of the queue's discriminated union keep their `kind`, so an SRD
    gap stays a distinct read-only entry rather than an evidence row missing
    its fields.
    """
    if row["kind"] == "srd-gap":
        card = row["card_block"]
        return {"kind": "srd-gap", "title": str(card["title"]), "ref": str(card["ref"])}
    summary = {key: row[key] for key in SUMMARY_FIELDS if key in row}
    summary["kind"] = "evidence-set"
    summary["project"] = row["project_path"]
    summary["routing_reason"] = routing_reason(row, row["item_previews"])
    return summary


def detail_row(row: dict[str, Any], *, show_analysis: bool) -> dict[str, Any]:
    """The list summary plus resolved grounds previews (spec §3, evidence-first).

    Analysis is folded by default, and absent entirely when the shared helper is
    empty — a permanently blocked row never shows analysis it cannot act on.
    """
    detail = summary_row(row)
    detail["items"] = row["item_previews"]
    if show_analysis:
        analysis = analysis_fields(row, row["item_previews"])
        if analysis:
            detail["analysis"] = analysis
    return detail
