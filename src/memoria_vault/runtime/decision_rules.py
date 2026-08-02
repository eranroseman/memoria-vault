"""Pre-registered decision rules (I1 spec §5): pre-registration as data, not memory.

Every beta.1 §4 blocker is written down *before* its evidence arrives -- what gets
measured, over what window, which number decides it, and what the decision then
is. That is the whole point: a rule the PI can read today cannot be quietly
re-derived once the numbers are in.

**Where the registry lives.** The sixteen shipped rules are `DEFAULT_RULES_YAML`
below; `.memoria/config/decision-rules.yaml` is the per-vault override. Absent, the
shipped registry loads; present, the file *is* the registry. That is the shape the
other I1-era configs already use -- `attention.yaml` (`runtime/attention_config`),
`policy.yaml`, `edges.yaml` -- none of which is in `workspace_seed` either, and it
keeps one source of truth for the rule text while still letting the PI edit a
threshold, retire a rule, or carry a per-vault `fired` status.
`update_rule_status` materializes the file on its first write.

**Assessment is not application.** `assess_decision_rules` is pure: it reads the
assembled dashboard panels and reports which armed `auto` rules *would* fire, with
the numbers that crossed and the producer to act on. Minting a notice card and
flipping `armed` to `fired` is the separate PI-protected
`apply-decision-rule-notices` operation (plan amendment 2026-07-29 §1), never a
read. A rule recommends; it never acts.

**The four auto thresholds are pre-registered constants, right here.** The spec
records them as free text ("routine alert", "sustained staleness"); the constants
below are that text resolved once, in the open, where review can argue with them --
not a heuristic buried inside a predicate. Each `threshold:` line in the registry
restates its constant in words, so the PI reads the same number the evaluator uses.
Twelve rules are `manual`: they render as armed reminders and no predicate can fire
them, because their evidence is the PI's own observation, not a counter.
"""

from __future__ import annotations

import datetime
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import yaml

from memoria_vault.runtime.vaultio import write_text_durable

RULES_CONFIG = ".memoria/config/decision-rules.yaml"

# Contract 8's entry shape. A row missing any of these, or carrying an unknown
# `check`/`status`, is skipped rather than raised: a hand-edited registry must not
# be able to take the dashboard down.
REQUIRED: tuple[str, ...] = (
    "id",
    "blocker",
    "metric",
    "window",
    "threshold",
    "recommendation",
    "check",
    "status",
)
CHECKS = frozenset({"auto", "manual"})
STATUSES = frozenset({"armed", "fired", "retired"})

# --- the four pre-registered auto thresholds ---------------------------------
# Each backs one rule below and is restated in that rule's `threshold:` prose.

# attention-throttle: inflow must beat drain on *every* UTC day in the window.
THROTTLE_WINDOW_DAYS = 7
# attention-loudness: a push band is alert or louder; `block` counts because the
# rule is about routine pushing, and block pushes harder than alert.
PUSH_BANDS: tuple[str, ...] = ("alert", "block")
LOUDNESS_MIN_OPEN = 10
LOUDNESS_PUSH_SHARE = 0.5
# reactive-substrate-priority: staleness has to be felt, not merely possible.
STALENESS_MIN_READS = 20
STALENESS_HIT_SHARE = 0.1
# evidence-review-sizing: the gate is skipped when most reviewed items get no
# decision recorded.
REVIEW_MIN_EVENTS = 10
REVIEW_MIN_DECIDED_SHARE = 0.5

DEFAULT_RULES_YAML = """\
# Pre-registered decision rules (I1 spec §5). Every beta.1 §4 blocker routes
# through an entry here, not through memory. auto rules are assessed at dashboard
# assembly and applied only by `apply-decision-rule-notices`; manual rules render
# as armed reminders.
- id: evidence-review-sizing
  blocker: "Evidence-review UI"
  metric: "items/session, time/item, accept/reject/edit/defer, reopen rate"
  window: "ten items across two sessions"
  threshold: "at least 10 recorded evidence-review events with a decision on fewer than half of them"
  recommendation: "Batch and filter until review fits a session; if skipped, simplify the gate"
  check: auto
  status: armed
- id: attention-loudness
  blocker: "Attention loudness"
  metric: "items per loudness level, push-worthy events, triage deferrals"
  window: "all sessions"
  threshold: "at least 10 open attention cards, more than half of them in the alert or block band"
  recommendation: "Calibrate the loudness policy; any routine push means the policy is wrong"
  check: auto
  status: armed
- id: reactive-substrate-priority
  blocker: "Reactive-substrate priority"
  metric: "staleness_hit count, index-refresh latency at 1000 works, on-read wait time"
  window: "all sessions"
  threshold: "at least 20 observed reads with staleness hits on more than 10% of them"
  recommendation: "Frequent staleness or painful refresh promotes the daemon (Tier A) up the roadmap; silence defers it behind Tier C nightly only"
  check: auto
  status: armed
- id: attention-throttle
  blocker: "Flow visibility + PI-owned throttles"
  metric: "attention inflow vs drain per UTC day"
  window: "rolling seven-day window"
  threshold: "attention inflow exceeds drain on every one of the last 7 UTC days"
  recommendation: "Recommend quieting or pausing the top producer (producers map in attention.yaml)"
  check: auto
  status: armed
- id: srd-contract
  blocker: "SRD contract"
  metric: "sections added/edited/deleted, unresolved requirements, missing trace links"
  window: "two SRDs or one revised twice"
  threshold: "a section is repeatedly deleted or never edited across the window"
  recommendation: "Keep sections that survive real editing; rare ones to optional appendix"
  check: manual
  status: armed
- id: seed-corpus
  blocker: "Seed corpus"
  metric: "source list, license, fetch method, time to first grounded answer"
  window: "one clean install rehearsal"
  threshold: "an unclear-license source, or first grounded answer over 30 minutes"
  recommendation: "Ship only clear-license sources with first answer under 30 minutes"
  check: manual
  status: armed
- id: workspace-gate-topology
  blocker: "Workspace/gate topology"
  metric: "path between ask/review/writing/SRD/export; context switches; abandons"
  window: "two full loops"
  threshold: "a lost-return or hidden-gate failure observed in a loop"
  recommendation: "Shortest path avoiding lost-return or hidden-gate failures"
  check: manual
  status: armed
- id: export-target
  blocker: "Export target"
  metric: "recipient/tool, format, refusal reasons, cleanup time"
  window: "two export attempts"
  threshold: "a real export demands a target beyond markdown + bibliography"
  recommendation: "First target appearing in real use; defer live citation fields unless required"
  check: manual
  status: armed
- id: multi-device-topology
  blocker: "Multi-device topology"
  metric: "second-device attempts, conflicts, sync workarounds"
  window: "all sessions"
  threshold: "repeated real handoffs between devices"
  recommendation: "Single-writer unless repeated real handoffs demand more"
  check: manual
  status: armed
- id: raw-dataset-bundling
  blocker: "Raw dataset bundling"
  metric: "dataset size/type, mutation, sharing/export need"
  window: "every dataset project"
  threshold: "a real export requires packaged data"
  recommendation: "Catalog-by-reference unless a real export requires packaged data"
  check: manual
  status: armed
- id: mode-work-creation
  blocker: "mode: work creation"
  metric: "creation attempts, confusion, alias requests"
  window: "all Work-note creations"
  threshold: "the alias is reached for or worked around repeatedly"
  recommendation: "Alias only if reached for or worked around repeatedly"
  check: manual
  status: armed
- id: non-api-schema-drift
  blocker: "Non-API schema drift"
  metric: "drift incidents, stale doc fields, failed checks"
  window: "every release-doc/schema edit"
  threshold: "an observed drift incident the current checks missed"
  recommendation: "Cheapest lint that catches observed drift"
  check: manual
  status: armed
- id: fulltext-v2-shape
  blocker: "Fulltext v2 shape"
  metric: "PDF-opens vs extracted-text reads vs anchored-span requests; anchor resolutions from files vs engine"
  window: "every source consultation in Phase 2"
  threshold: "spans consumed via engine while reading happens in PDF, or persistent file reads"
  recommendation: "If spans are consumed via engine and reading happens in PDF, full v2; if file reads persist, partial retirement (anchor-bearing files for evidence-bearing works)"
  check: manual
  status: armed
- id: warrant-touch-budget
  blocker: "Warrant touch budget"
  metric: "under-warranted findings raised, state-the-warrant demands, PI minutes per warrant made explicit"
  window: "one full project loop"
  threshold: "explicit warrants exceed budget, or are never demanded"
  recommendation: "If explicit warrants stay under budget and get demanded, ratify hybrid-with-nodes; if never demanded, keep demandable-only and defer nodes"
  check: manual
  status: armed
- id: two-window-friction
  blocker: "Two-window friction"
  metric: "context switches between editor and agent per session, dropped handoffs, context.read misses"
  window: "all Phase 2 sessions"
  threshold: "repeated editor-agent friction across sessions"
  recommendation: "Repeated friction triggers the embedded-panel earn-back; otherwise plugin+agent stands"
  check: manual
  status: armed
- id: canvas-authoring
  blocker: "Canvas authoring (scoped ADR-103 reopen)"
  metric: "outline-composition friction events: list reorder sufficed vs reached for spatial arrangement"
  window: "every outline session in Phase 2"
  threshold: "repeated reaching for spatial arrangement during outline work"
  recommendation: "Repeated spatial reaching admits canvas-as-authoring (read .canvas back as authored input); silence keeps canvases projection-only"
  check: manual
  status: armed
"""


def load_decision_rules(vault: Path) -> list[dict[str, Any]]:
    """The vault's registry: its own file if it has one, else the shipped rules.

    Well-formed entries only -- a malformed row is skipped, never fatal, and an
    unparsable file reads as an empty registry rather than an exception. A rule
    engine that can crash a dashboard read is worse than one that reports nothing.
    """
    path = Path(vault) / RULES_CONFIG
    return [rule for entry in _raw_entries(path) if (rule := _validated(entry)) is not None]


def update_rule_status(vault: Path, rule_id: str, status: str) -> None:
    """Flip one rule's status with a durable write, materializing the file if absent.

    The raw entries are rewritten, not the validated projection, so a field the PI
    added and this module does not know about survives the write. Comments do not
    -- PyYAML cannot round-trip them, and no comment-preserving parser is worth a
    dependency here.
    """
    if status not in STATUSES:
        raise ValueError(f"status must be one of: {', '.join(sorted(STATUSES))}")
    path = Path(vault) / RULES_CONFIG
    entries = _raw_entries(path)
    matched = [entry for entry in entries if isinstance(entry, dict) and entry.get("id") == rule_id]
    if not matched:
        raise ValueError(f"no such decision rule: {rule_id}")
    for entry in matched:
        entry["status"] = status
    write_text_durable(
        path,
        yaml.safe_dump(entries, sort_keys=False, allow_unicode=True),
        create_parent=True,
    )


def assess_decision_rules(
    panels: dict[str, Any], rules: Iterable[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Which armed `auto` rules would fire against these panels, and on what numbers.

    Pure -- no vault, no clock beyond today's UTC date, no write. Each entry
    carries the `observed` numbers that crossed alongside the pre-registered
    threshold, so a rule reading the wrong panel is visible in the payload rather
    than hidden behind a bare id. `attention-throttle` additionally names the
    producer to act on, because "recommend quieting the top producer" is not a
    recommendation until it says which one.
    """
    assessed: list[dict[str, Any]] = []
    for rule in rules:
        if rule.get("check") != "auto" or rule.get("status") != "armed":
            continue
        predicate = AUTO_PREDICATES.get(str(rule.get("id") or ""))
        observed = predicate(panels) if predicate else None
        if observed is None:
            continue
        assessed.append(
            {
                "id": rule["id"],
                "threshold": rule["threshold"],
                "recommendation": rule["recommendation"],
                "observed": observed,
            }
        )
    return assessed


def _raw_entries(path: Path) -> list[Any]:
    """The registry document as parsed, from the vault file or the shipped default."""
    if path.is_file():
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return []
    else:
        text = DEFAULT_RULES_YAML
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError:
        return []
    return data if isinstance(data, list) else []


def _validated(entry: Any) -> dict[str, Any] | None:
    if not isinstance(entry, dict):
        return None
    if any(not str(entry.get(field) or "").strip() for field in REQUIRED):
        return None
    if entry["check"] not in CHECKS or entry["status"] not in STATUSES:
        return None
    return {field: entry[field] for field in REQUIRED}


def _recent_utc_days(count: int) -> list[str]:
    """The last `count` UTC days, oldest first, including today.

    UTC because both flow series are bucketed by UTC day (`substr(ts, 1, 10)` over
    a `Z` timestamp). A window anchored on the *local* date would drop or double a
    day for any PI west of Greenwich for part of every day.
    """
    today = datetime.datetime.now(datetime.UTC).date()
    return [
        (today - datetime.timedelta(days=offset)).isoformat() for offset in reversed(range(count))
    ]


def _count(mapping: Any, key: str) -> int:
    if not isinstance(mapping, dict):
        return 0
    try:
        return int(mapping.get(key, 0) or 0)
    except (TypeError, ValueError):
        return 0


def _attention_throttle(panels: dict[str, Any]) -> dict[str, Any] | None:
    flow = panels.get("attention_flow", {})
    inflow = flow.get("inflow_by_day", {})
    drain = flow.get("drain_by_day", {})
    window = _recent_utc_days(THROTTLE_WINDOW_DAYS)
    # `inflow > drain` already implies a nonzero inflow -- both are counts -- so a
    # separate `inflow > 0` conjunct would be dead weight, and a dead conjunct is
    # a rule nobody can tell is doing anything.
    if not all(_count(inflow, day) > _count(drain, day) for day in window):
        return None
    producers = flow.get("per_producer", {})
    names = sorted(producers) if isinstance(producers, dict) else []
    top = max(names, key=lambda name: _count(producers, name)) if names else ""
    return {
        "window_days": THROTTLE_WINDOW_DAYS,
        "window_start": window[0],
        "window_end": window[-1],
        "inflow": sum(_count(inflow, day) for day in window),
        "drain": sum(_count(drain, day) for day in window),
        # All-time admissions, not windowed: `per_producer` carries no day
        # dimension, and the producer to quiet is a standing property anyway.
        "top_producer": top,
        "top_producer_admissions": _count(producers, top),
    }


def _attention_loudness(panels: dict[str, Any]) -> dict[str, Any] | None:
    flow = panels.get("attention_flow", {})
    open_total = _count(flow, "open_total")
    by_loudness = flow.get("open_by_loudness", {})
    push_open = sum(_count(by_loudness, band) for band in PUSH_BANDS)
    if open_total < LOUDNESS_MIN_OPEN or push_open / open_total <= LOUDNESS_PUSH_SHARE:
        return None
    return {
        "open_total": open_total,
        "push_bands": list(PUSH_BANDS),
        "push_open": push_open,
        "push_share": round(push_open / open_total, 3),
    }


def _reactive_substrate_priority(panels: dict[str, Any]) -> dict[str, Any] | None:
    reads_panel = panels.get("reads_staleness", {})
    reads = _count(reads_panel, "reads")
    hits = _count(reads_panel, "staleness_hits")
    if reads < STALENESS_MIN_READS or hits / reads <= STALENESS_HIT_SHARE:
        return None
    return {"reads": reads, "staleness_hits": hits, "staleness_share": round(hits / reads, 3)}


def _evidence_review_sizing(panels: dict[str, Any]) -> dict[str, Any] | None:
    review = panels.get("evidence_review", {})
    events = _count(review, "events")
    actions = review.get("actions", {})
    decided = sum(_count(actions, key) for key in actions) if isinstance(actions, dict) else 0
    if events < REVIEW_MIN_EVENTS or decided / events >= REVIEW_MIN_DECIDED_SHARE:
        return None
    return {"events": events, "decided": decided, "skip_rate": round(1 - decided / events, 3)}


# One predicate per `auto` rule. A rule marked `auto` with no entry here can never
# fire, so `tests/test_decision_rules.py` pins this mapping against the registry's
# own auto set -- adding the fifth auto rule without its predicate must fail loudly
# rather than ship a rule that silently never triggers.
AUTO_PREDICATES: dict[str, Callable[[dict[str, Any]], dict[str, Any] | None]] = {
    "attention-throttle": _attention_throttle,
    "attention-loudness": _attention_loudness,
    "reactive-substrate-priority": _reactive_substrate_priority,
    "evidence-review-sizing": _evidence_review_sizing,
}
