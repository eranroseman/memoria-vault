#!/usr/bin/env python3
# ruff: noqa: E402
"""Board transition, cost, blind-review, and review-prompt event handling."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_RUNTIME_ROOT = Path(__file__).resolve().parent.parent
if str(_RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(_RUNTIME_ROOT))

from _shared import append_jsonl, now_iso
from board_export_common import (
    BLIND_REVIEW_RELPATH,
    COST_MISSES_RELPATH,
    COST_RELPATH,
    DISPOSITION_RELPATH,
    STATE_CACHE_RELPATH,
    TERMINAL_REVIEW,
    TRANSITIONS_RELPATH,
    _metadata,
    normalize,
)
from operations.lib import inbox


def load_state_cache(vault: Path) -> dict:
    """Per-card {status, review_status} seen on the previous run (for diffing)."""
    p = vault / STATE_CACHE_RELPATH
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError as exc:
            print(f"[board_export] corrupt state cache ({p}), resetting: {exc}", file=sys.stderr)
            return {}
    return {}


def save_state_cache(vault: Path, cards: list[dict]) -> None:
    cur = {}
    for raw in cards:
        c = normalize(raw)
        cur[c["task_id"]] = {"status": c["status"], "review_status": c["review_status"]}
    p = vault / STATE_CACHE_RELPATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cur, ensure_ascii=False), encoding="utf-8")


def compute_events(prev: dict, cards: list[dict], cost_lookup=None) -> dict:
    """Diff previous per-card state vs current; return transition / disposition /
    cost event rows. A card unseen before counts as a transition into its state."""
    ts = now_iso()
    transitions: list[dict] = []
    dispositions: list[dict] = []
    costs: list[dict] = []
    cost_misses: list[dict] = []
    blind_reviews: list[dict] = []
    for raw in cards:
        c = normalize(raw)
        tid, lane = c["task_id"], c["assignee"]
        if tid not in prev:
            continue  # first sight this run -- seeded into the cache below, emits no event
        before = prev[tid]
        old_status, old_review = before.get("status"), before.get("review_status")

        if c["status"] != old_status:
            transitions.append(
                {
                    "timestamp": ts,
                    "task_id": tid,
                    "lane": lane,
                    "kind": "status",
                    "from": old_status,
                    "to": c["status"],
                }
            )
            # Cost is final at completion -- log it on the transition into `done`.
            if c["status"] == "done" and cost_lookup is not None:
                cost_row, miss_row = cost_lookup(raw, c, ts)
                if cost_row is not None:
                    costs.append(cost_row)
                if miss_row is not None:
                    cost_misses.append(miss_row)

        if c["review_status"] != old_review:
            transitions.append(
                {
                    "timestamp": ts,
                    "task_id": tid,
                    "lane": lane,
                    "kind": "review",
                    "from": old_review,
                    "to": c["review_status"],
                }
            )
            # Disposition is emitted by the human review action. The exporter only
            # samples terminal reviews for optional blind re-review.
            if c["review_status"] in TERMINAL_REVIEW:
                disp = TERMINAL_REVIEW[c["review_status"]]
                if c["blind_rereview"] or should_sample_blind_review(tid):
                    blind_reviews.append(
                        {
                            "timestamp": ts,
                            "task_id": tid,
                            "lane": lane,
                            "disposition": disp,
                            "review_status": c["review_status"],
                            "sample_reason": "blind-rereview",
                            "agent_recommendation": c["agent_recommendation"],
                        }
                    )
    return {
        "transitions": transitions,
        "dispositions": dispositions,
        "costs": costs,
        "cost_misses": cost_misses,
        "blind_reviews": blind_reviews,
    }


def should_sample_blind_review(task_id: str, rate: float = 0.05) -> bool:
    """Deterministically sample terminal reviews for a second blind pass.

    The card id is hashed so repeated exports make the same choice without a
    mutable sampler state. `metadata.blind_rereview: true` on a card forces the
    sample path for tests or an intentional spot-check.
    """
    if not task_id or rate <= 0:
        return False
    bucket = int(hashlib.sha256(task_id.encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF
    return bucket < rate


_append_jsonl = append_jsonl


def export_events(vault: Path, prev: dict, cards: list[dict], cost_lookup=None) -> dict:
    ev = compute_events(prev, cards, cost_lookup=cost_lookup)
    append_jsonl(vault / TRANSITIONS_RELPATH, ev["transitions"])
    append_jsonl(vault / DISPOSITION_RELPATH, ev["dispositions"])
    append_jsonl(vault / COST_RELPATH, ev["costs"])
    append_jsonl(vault / COST_MISSES_RELPATH, ev["cost_misses"])
    append_jsonl(vault / BLIND_REVIEW_RELPATH, ev["blind_reviews"])
    return {k: len(v) for k, v in ev.items()}


# --------------------------------------------------------------------------- #
# Inbox review prompts -- a card reaching `done` is lane work awaiting the PI
# --------------------------------------------------------------------------- #
REVIEW_PROMPT_FRESH_SECONDS = 24 * 3600  # bootstrap-guard window for first-seen cards


def _recently_done(c: dict, now: datetime | None = None) -> bool:
    """True when the card's last_updated falls inside the bootstrap window.
    A missing/unparseable timestamp counts as stale -- never flood the Inbox."""
    raw = c.get("last_updated", "")
    if not raw:
        return False
    try:
        ts = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return False
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    now = now or datetime.now(UTC)
    return (now - ts).total_seconds() <= REVIEW_PROMPT_FRESH_SECONDS


def newly_done(prev: dict, cards: list[dict]) -> list[dict]:
    """The raw cards that should raise a review prompt this run: cards observed
    transitioning into `done`, plus -- bootstrap guard -- cards first seen
    already `done` only when they finished within the last 24h, so the first
    run after install never floods the Inbox with the board's history."""
    out: list[dict] = []
    for raw in cards:
        c = normalize(raw)
        if c["status"] != "done":
            continue
        before = prev.get(c["task_id"])
        if before is not None:
            if before.get("status") == "done":
                continue  # prompt already raised on the transition into done
        elif not _recently_done(c):
            continue  # first sight of an old done card -- seed cache silently
        out.append(raw)
    return out


def export_review_prompts(vault: Path, prev: dict, cards: list[dict]) -> int:
    """Raise ONE `work-prompt` card in inbox/ per card newly arrived in `done`
    (the Inbox is the PI's single slice of the board -- ADR-51). Idempotent
    twice over: the state-cache diff only fires on the transition, and the
    filename derives from the card id, so the same done card never produces
    two prompts across cron runs. Returns the number of prompts written."""
    written = 0
    for raw in newly_done(prev, cards):
        c = normalize(raw)
        outputs = _metadata(raw).get("expected_outputs", "")
        if isinstance(outputs, (list, tuple)):
            outputs = ", ".join(str(o) for o in outputs)
        path = inbox.write_work_prompt(
            vault,
            title=f"Review: {c['title']}",
            action="Review the work product, then accept it or archive the board card.",
            what_happened=f'Lane {c["assignee"]} finished "{c["title"]}" (card {c["task_id"]}).',
            raised_by="board-export",
            target=str(outputs or ""),
            task_id=c["task_id"],
            lane=c["assignee"],
            dedupe_slug=f"review-{c['task_id']}",
        )
        if path is not None:
            written += 1
    return written
