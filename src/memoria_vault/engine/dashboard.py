"""Honest dashboard assembly (I1 spec §4): raw counts from both planes, never a score.

Two planes, one reader: the hash-chained journal (`event_log`) for the streams a
gate or verifier reads, and `telemetry_events` for the analytics-only ones. The
dashboard writes to neither -- it is a reader of both, never a third store, so a
repeated call leaves every non-SQLite vault file and every row untouched.

Every panel is raw counts with its own denominator. There is deliberately no
composite key anywhere in the payload (`tests/test_dashboard_view.py` scans the
serialized payload for `score`/`health`/`grade`): the three orthogonal signals --
dispositions, usage/load, staleness -- stay separate panels precisely so nobody
can average them into one number.

Several counters are honestly empty until their producer lands: `inflow_by_day`
and `per_producer` need I1 A.3's admission emitters, `skipped_runs` needs A.4's
throttles, `edge_writes` needs the graph plan's ERP-D.6, and `evidence_review`
needs V2R-C's client emitters. Zero is the honest reading of a stream nothing
writes yet, so each stays a real query over the real table rather than a stub the
later task has to find and replace.

`decision_rules` is the one panel that is *not* empty on a fresh vault: the
seventeen-rule pre-registration ships with the product (`runtime.decision_rules`),
so a PI sees every blocker armed on day one and `would_fire` empty. Assembly stays
pure -- assessment reports, `apply-decision-rule-notices` applies.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.decision_rules import assess_decision_rules, load_decision_rules

# The panel roster and its order, in one place: `assemble_dashboard` builds its
# dict in this order and `engine.api.read_dashboard_view` renders one text block
# per entry from the same tuple, so the wire order cannot drift from the payload.
DASHBOARD_PANELS: tuple[str, ...] = (
    "attention_flow",
    "dispositions",
    "evidence_review",
    "reads_staleness",
    "edge_writes",
    "exploration",
    "decision_rules",
)

# Open-card age buckets, widest last. `engine.cockpit._flow_panel` reads these
# three names to name its oldest non-empty bucket.
#
# The age itself is not computed here. `engine.api._rank_factors` derives
# `age_days` from the card's `created:` stamp against a local `date.today()` --
# the same basis `inbox`'s writers stamp in -- and every card payload carries it,
# so this panel buckets one number rather than deriving a second one that could
# drift from the order the list is sorted in. (I1 H.1 shipped a private
# `_age_days` because A.1 was unlanded; A.1 deleted it, which is what its own
# section instructed.)
AGE_BUCKETS = ("0-7d", "8-30d", ">30d")

# The producer whose surfaced candidates panel 6 (spec §4.6, the diversity
# channel) measures acted-on rates for.
EXPLORATION_PRODUCER = "analyze-gaps"


def assemble_dashboard(vault: Path) -> dict[str, Any]:
    """Seven raw-count panels over the journal and the telemetry table.

    Pure: no vault write, no journal append, no telemetry row, no decision-rule
    status change (I1 plan amendment 2026-07-29 §1 -- application is the separate
    `apply-decision-rule-notices` operation, never assembly).
    """
    vault = Path(vault)
    cards = _attention_cards(vault)
    panels: dict[str, Any] = {
        "attention_flow": _attention_flow_panel(vault, cards),
        "dispositions": _dispositions_panel(vault),
        "evidence_review": _evidence_review_panel(vault),
        "reads_staleness": _reads_panel(vault),
        "edge_writes": _telemetry_group_counts(vault, "edge-write.v1", "relation_type"),
        "exploration": _exploration_panel(vault, cards),
    }
    # Last, and last in `DASHBOARD_PANELS`, because it is the only panel that reads
    # the other six.
    panels["decision_rules"] = _decision_rules_panel(vault, panels)
    return panels


def _attention_cards(vault: Path) -> list[dict[str, Any]]:
    """Every attention projection in `inbox/`, open or not.

    Imported inside the call: `engine.api` imports this module for
    `read_dashboard_view`, so a module-level import here would be a cycle.
    """
    from memoria_vault.engine.api import _attention_cards as read_cards

    return read_cards(vault)


def _attention_flow_panel(vault: Path, cards: list[dict[str, Any]]) -> dict[str, Any]:
    open_cards = [card for card in cards if card["status"] == "open"]
    # A hand-written `inbox/` card need not carry `loudness:`; `_attention_card`
    # hands that through as "". The band such a card is actually treated as is
    # `notice` -- the same default `inbox.write_proposal` writes.
    open_by_loudness = Counter(card["loudness"] or "notice" for card in open_cards)
    ages: Counter[str] = Counter()
    for card in open_cards:
        ages[_age_bucket(int(card["rank_factors"]["age_days"]))] += 1
    inflow = _telemetry_day_counts(vault, "attention-admitted")
    drain = _journal_day_counts(vault, "disposition")
    return {
        "open_total": len(open_cards),
        "open_by_loudness": dict(open_by_loudness),
        "inflow_by_day": inflow,
        "drain_by_day": drain,
        "net_by_day": {
            day: inflow.get(day, 0) - drain.get(day, 0) for day in sorted(set(inflow) | set(drain))
        },
        "age_distribution": dict(ages),
        "per_producer": _telemetry_group_counts(vault, "attention-admitted", "raised_by"),
        "skipped_runs": _telemetry_group_counts(vault, "producer-run-skipped", "producer"),
    }


def _age_bucket(days: int) -> str:
    if days <= 7:
        return AGE_BUCKETS[0]
    if days <= 30:
        return AGE_BUCKETS[1]
    return AGE_BUCKETS[2]


def _dispositions_panel(vault: Path) -> dict[str, Any]:
    by_decision: Counter[str] = Counter()
    by_item_type: dict[str, Counter[str]] = {}
    for event in _journal_payloads(vault, "disposition"):
        decision = str(event.get("decision") or "")
        item_type = str(event.get("item_type") or "")
        by_decision[decision] += 1
        by_item_type.setdefault(item_type, Counter())[decision] += 1
    return {
        "by_decision": dict(by_decision),
        "by_item_type": {key: dict(value) for key, value in by_item_type.items()},
        "total": sum(by_decision.values()),
    }


def _evidence_review_panel(vault: Path) -> dict[str, Any]:
    events = _telemetry_payloads(vault, "empirical_event.v1")
    review = [event for event in events if event.get("workflow") == "evidence-review"]
    durations = [float(event["duration_s"]) for event in review if event.get("duration_s")]
    actions = Counter(str(event["decision"]) for event in review if event.get("decision"))
    return {
        "events": len(review),
        "actions": dict(actions),
        "mean_duration_s": round(sum(durations) / len(durations), 1) if durations else 0,
    }


def _reads_panel(vault: Path) -> dict[str, Any]:
    reads = _telemetry_payloads(vault, "read-observed.v1")
    return {
        "reads": len(reads),
        "staleness_hits": sum(1 for event in reads if event.get("staleness_hit") is True),
    }


def _exploration_panel(vault: Path, cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Panel 6: acted-on exploration candidates over candidates surfaced.

    The denominator is every surfaced candidate still on disk, not only the open
    ones. Acting on a card resolves it, so a surfaced/acted pair measured over
    open cards alone could only ever report zero -- the numerator would leave the
    denominator at the moment it became nonzero.
    """
    surfaced = {
        card["path"]
        for card in cards
        if card["frontmatter"].get("raised_by") == EXPLORATION_PRODUCER
    }
    acted = {
        str(event.get("item_id") or "")
        for event in _journal_payloads(vault, "disposition")
        if str(event.get("item_id") or "") in surfaced
    }
    return {"surfaced": len(surfaced), "acted_on": len(acted)}


def _decision_rules_panel(vault: Path, panels: dict[str, Any]) -> dict[str, Any]:
    """The pre-registration and its verdict: every rule, and which would fire now.

    `rules` is the whole registry, armed reminders included, because a
    pre-registration nobody can read is not one. `would_fire` is the pure
    `assess_decision_rules` over the six panels already assembled -- each entry
    carries the numbers that crossed, not a bare id.

    Reporting is not applying (plan amendment 2026-07-29 §1): nothing here mints a
    card or flips `armed` to `fired`. Only the explicit
    `apply-decision-rule-notices` operation may.
    """
    rules = load_decision_rules(vault)
    return {"rules": rules, "would_fire": assess_decision_rules(panels, rules)}


def _journal_payloads(vault: Path, event_type: str) -> list[dict[str, Any]]:
    with state.connect(vault) as conn:
        rows = conn.execute(
            "SELECT payload_json FROM event_log WHERE event_type = ? ORDER BY event_id",
            (event_type,),
        ).fetchall()
    return [json.loads(str(row["payload_json"])) for row in rows]


def _journal_day_counts(vault: Path, event_type: str) -> dict[str, int]:
    with state.connect(vault) as conn:
        rows = conn.execute(
            "SELECT substr(timestamp, 1, 10) AS day, COUNT(*) AS n FROM event_log"
            " WHERE event_type = ? GROUP BY day ORDER BY day",
            (event_type,),
        ).fetchall()
    return {str(row["day"]): int(row["n"]) for row in rows}


def _telemetry_day_counts(vault: Path, event_type: str) -> dict[str, int]:
    with state.connect(vault) as conn:
        rows = conn.execute(
            "SELECT substr(ts, 1, 10) AS day, COUNT(*) AS n FROM telemetry_events"
            " WHERE event_type = ? GROUP BY day ORDER BY day",
            (event_type,),
        ).fetchall()
    return {str(row["day"]): int(row["n"]) for row in rows}


def _telemetry_group_counts(vault: Path, event_type: str, field: str) -> dict[str, int]:
    with state.connect(vault) as conn:
        rows = conn.execute(
            "SELECT json_extract(payload_json, ?) AS grp, COUNT(*) AS n FROM telemetry_events"
            " WHERE event_type = ? GROUP BY grp ORDER BY grp",
            (f"$.{field}", event_type),
        ).fetchall()
    return {str(row["grp"]): int(row["n"]) for row in rows if row["grp"] is not None}


def _telemetry_payloads(vault: Path, event_type: str) -> list[dict[str, Any]]:
    with state.connect(vault) as conn:
        rows = conn.execute(
            "SELECT payload_json FROM telemetry_events WHERE event_type = ? ORDER BY ts",
            (event_type,),
        ).fetchall()
    return [json.loads(str(row["payload_json"])) for row in rows]
