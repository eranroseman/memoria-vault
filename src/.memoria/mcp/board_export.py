#!/usr/bin/env python3
"""Board exporter -- project the Hermes Kanban into Dataview-queryable files and
append the per-card telemetry time-series.

The authoritative board is the Hermes built-in Kanban (~/.hermes/kanban.db).
Obsidian's Dataview cannot query that database, so this script writes read-only
projections the dashboards consume, plus append-only event logs the metrics
aggregator and any publication analysis read (see docs/reference/telemetry.md):

  system/board/<task_id>.md          one markdown file per live card  (board-state dashboard)
  system/logs/board-state.jsonl   per-lane queue-depth snapshot, one line per run (status line)
  system/logs/board-transitions.jsonl  per-card state/review transitions (time-series)
  system/logs/disposition.jsonl   accept | edit | reject per review decision (UN-BACKFILLABLE)
  system/logs/cost.jsonl          API spend + token counts per card at completion
  system/logs/blind-review-samples.jsonl  deterministic sample requests for blind re-review
  inbox/work-prompt-review-*.md   ONE review prompt per card that reaches `done`
                                  (the Inbox is the PI's slice of the board, ADR-51)

Transitions/disposition/cost are computed by diffing this run's board against the
previous run, cached in `system/logs/.board-state-cache.json`. Source of
truth: `hermes kanban list --json` (or `--from-json <file>` for tests/offline).
The export is ONE-WAY (board -> files). Run on a cron cadence (~60s); the Linter
owns rotation/cleanup of the projected files and logs.

    python board_export.py --vault <path>                  # read `hermes kanban list --json`
    python board_export.py --vault <path> --from-json cards.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from _shared import append_jsonl, now_iso, resolve_vault, safe_filename

# The shared Inbox card writer (ADR-51) — operations and lanes never invent card formats.
_LIB_DIR = Path(__file__).resolve().parent.parent / "operations" / "lib"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))
import inbox  # noqa: E402

BOARD_RELDIR = "system/board"
SNAPSHOT_RELPATH = "system/logs/board-state.jsonl"
TRANSITIONS_RELPATH = "system/logs/board-transitions.jsonl"  # per-card status/review changes
DISPOSITION_RELPATH = "system/logs/disposition.jsonl"        # accept | edit | reject (un-backfillable)
COST_RELPATH = "system/logs/cost.jsonl"                      # API spend + tokens per card at completion
BLIND_REVIEW_RELPATH = "system/logs/blind-review-samples.jsonl"  # sampled terminal reviews
STATE_CACHE_RELPATH = "system/logs/.board-state-cache.json"  # internal: last-seen state per card (for diffing)
LIVE_STATUSES = ("triage", "todo", "ready", "running", "blocked", "done")  # not archived
REVIEW_QUEUE_STATES = ("requested",)   # done cards handed off for human review (review_status: requested)
# Terminal review outcomes -> default human-loop disposition (an explicit metadata.disposition
# of "edited" overrides, capturing the human-modified-then-accepted case the diff can't see).
TERMINAL_REVIEW = {"approved": "accepted", "rejected": "rejected", "changes-requested": "rejected"}


# --------------------------------------------------------------------------- #
# Loading cards
# --------------------------------------------------------------------------- #
def load_cards(from_json: Path | None = None) -> list[dict]:
    """Return the board's live cards as a list of dicts. Reads a JSON file when
    given (tests/offline), else shells out to `hermes kanban list --json`."""
    if from_json is not None:
        raw = from_json.read_text(encoding="utf-8")
    else:
        try:
            proc = subprocess.run(
                ["hermes", "kanban", "list", "--json"],
                capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as exc:
            print(f"[board_export] hermes kanban list failed (exit {exc.returncode}): "
                  f"{exc.stderr.strip()}", file=sys.stderr)
            raise
        except FileNotFoundError:
            print("[board_export] 'hermes' not found on PATH", file=sys.stderr)
            raise
        raw = proc.stdout
    data = json.loads(raw)
    # Hermes may return a bare list or {"tasks": [...]}; accept both.
    cards = data.get("tasks", data) if isinstance(data, dict) else data
    return [c for c in cards if isinstance(c, dict)]


def _first(card: dict, *keys: str, default=""):
    for k in keys:
        if k in card and card[k] not in (None, ""):
            return card[k]
    return default


def _iso_ts(value, default="") -> str:
    """Normalize a Hermes card timestamp to ISO-8601 UTC for the dashboards.
    Hermes serializes card times as epoch seconds (occasionally milliseconds);
    older/fixture data already uses an ISO string. Pass ISO-ish strings through,
    convert epochs, and fall back to the string form so the field never silently
    drops a value it can't parse."""
    if value in (None, ""):
        return default
    if isinstance(value, str) and not value.isdigit():
        return value
    try:
        ts = float(value)
    except (TypeError, ValueError):
        return str(value)
    if ts > 1e11:  # milliseconds -> seconds
        ts /= 1000.0
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _metadata(card: dict) -> dict:
    """The Memoria overlay rides in the card's free-form `metadata` (dict, or a
    JSON-encoded string depending on the Hermes serializer)."""
    md = card.get("metadata")
    if isinstance(md, dict):
        return md
    if isinstance(md, str):
        try:
            parsed = json.loads(md)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def normalize(card: dict) -> dict:
    """Denormalize a raw Hermes card into the queryable fields the dashboards
    read (board-export.md). Defensive about field-name drift across versions."""
    md = _metadata(card)
    runs = card.get("runs") or []
    summary = ""
    if runs and isinstance(runs[-1], dict):
        summary = runs[-1].get("summary", "") or ""
    summary = summary or md.get("summary", "") or _first(card, "summary")
    return {
        "task_id": _first(card, "task_id", "id", default="unknown"),
        "title": _first(card, "title", default="(untitled)"),
        "status": _first(card, "status", default="unknown"),
        "assignee": _first(card, "assignee", default="none"),
        "review_status": md.get("review_status", "unreviewed"),
        "retry_count": md.get("retry_count", 0),
        "reason": _first(card, "reason") or md.get("blocked_reason", ""),
        "created_at": _iso_ts(_first(card, "created_at", default="")),
        "last_updated": _iso_ts(_first(card, "updated_at", "modified_at", "created_at")),
        "summary": summary,
        # --- telemetry overlay (all best-effort; empty when Hermes doesn't supply them) ---
        "agent_recommendation": md.get("agent_recommendation", md.get("agent_verdict", "")),
        "disposition": md.get("disposition", ""),       # explicit "edited" wins over the derived accept/reject
        "expanded_at": md.get("expanded_at", ""),
        "review_requested_at": md.get("review_requested_at", ""),
        "reviewed_at": md.get("reviewed_at", ""),
        "blind_rereview": md.get("blind_rereview", False),
        "cost": md.get("cost", card.get("cost", "")),   # API spend for the card ($)
        "tokens_in": md.get("tokens_in", card.get("tokens_in", "")),
        "tokens_out": md.get("tokens_out", card.get("tokens_out", "")),
    }


# --------------------------------------------------------------------------- #
# Projections
# --------------------------------------------------------------------------- #
def _yaml_scalar(v) -> str:
    """Render a frontmatter scalar: ints bare, strings double-quoted+escaped."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    s = str(v).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


# _safe_name: use safe_filename from _shared
_safe_name = safe_filename


def card_markdown(card: dict) -> str:
    """One card -> a markdown note: frontmatter (queryable) + body (summary)."""
    fm_keys = ["task_id", "status", "assignee", "review_status",
               "retry_count", "reason", "last_updated"]
    lines = ["---"]
    lines += [f"{k}: {_yaml_scalar(card[k])}" for k in fm_keys]
    lines += ["type: board-card", "---", "", f"# {card['title']}", ""]
    if card["summary"]:
        lines += [card["summary"], ""]
    return "\n".join(lines)


def export_markdown(vault: Path, cards: list[dict]) -> set[str]:
    """Write one markdown file per live card; remove files for cards that are no
    longer live (archived/deleted). Returns the set of task_ids exported."""
    board = vault / BOARD_RELDIR
    board.mkdir(parents=True, exist_ok=True)
    live = [normalize(c) for c in cards if c.get("status") in LIVE_STATUSES]
    written = set()
    for c in live:
        fname = _safe_name(c["task_id"]) + ".md"
        (board / fname).write_text(card_markdown(c), encoding="utf-8")
        written.add(fname)
    # Prune stale exports (keep .keep and any non-exported scaffolding).
    for f in board.glob("*.md"):
        if f.name not in written:
            f.unlink()
    return {c["task_id"] for c in live}


def board_snapshot(cards: list[dict]) -> dict:
    """Per-lane queue depths (running / ready / blocked / review / retries) + totals."""
    lanes: dict[str, dict] = {}
    totals = {"running": 0, "ready": 0, "blocked": 0, "review_queue": 0, "retrying": 0}
    for raw in cards:
        c = normalize(raw)
        lane = lanes.setdefault(c["assignee"],
                                {"running": 0, "ready": 0, "blocked": 0,
                                 "review_queue": 0, "retrying": 0})
        st = c["status"]
        if st in ("running", "ready", "blocked"):
            lane[st] += 1
            totals[st] += 1
        if st == "done" and c["review_status"] in REVIEW_QUEUE_STATES:
            lane["review_queue"] += 1
            totals["review_queue"] += 1
        if st == "ready" and int(c.get("retry_count") or 0) > 0:
            lane["retrying"] += 1
            totals["retrying"] += 1
    return {"timestamp": now_iso(), "lanes": lanes, "totals": totals}


def export_snapshot(vault: Path, cards: list[dict]) -> dict:
    snap = board_snapshot(cards)
    append_jsonl(vault / SNAPSHOT_RELPATH, [snap])
    return snap


# --------------------------------------------------------------------------- #
# Telemetry event logs (transitions / disposition / cost) -- diff vs last run
# --------------------------------------------------------------------------- #
# _ts: use now_iso from _shared
_ts = now_iso


def load_state_cache(vault: Path) -> dict:
    """Per-card {status, review_status} seen on the previous run (for diffing)."""
    p = vault / STATE_CACHE_RELPATH
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError as exc:
            print(f"[board_export] corrupt state cache ({p}), resetting: {exc}",
                  file=sys.stderr)
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


def compute_events(prev: dict, cards: list[dict]) -> dict:
    """Diff previous per-card state vs current; return transition / disposition /
    cost event rows. A card unseen before counts as a transition into its state."""
    ts = _ts()
    transitions: list[dict] = []
    dispositions: list[dict] = []
    costs: list[dict] = []
    blind_reviews: list[dict] = []
    for raw in cards:
        c = normalize(raw)
        tid, lane = c["task_id"], c["assignee"]
        if tid not in prev:
            continue   # first sight this run -- seeded into the cache below, emits no event
        before = prev[tid]
        old_status, old_review = before.get("status"), before.get("review_status")

        if c["status"] != old_status:
            transitions.append({"timestamp": ts, "task_id": tid, "lane": lane,
                                 "kind": "status", "from": old_status, "to": c["status"]})
            # Cost is final at completion -- log it on the transition into `done`.
            if c["status"] == "done" and (c["cost"] != "" or c["tokens_out"] != ""):
                costs.append({"timestamp": ts, "task_id": tid, "lane": lane,
                              "cost": c["cost"], "tokens_in": c["tokens_in"],
                              "tokens_out": c["tokens_out"]})

        if c["review_status"] != old_review:
            transitions.append({"timestamp": ts, "task_id": tid, "lane": lane,
                                 "kind": "review", "from": old_review, "to": c["review_status"]})
            # Disposition fires when review reaches a terminal outcome.
            if c["review_status"] in TERMINAL_REVIEW:
                disp = c["disposition"] or TERMINAL_REVIEW[c["review_status"]]
                dispositions.append({"timestamp": ts, "task_id": tid, "lane": lane,
                                     "disposition": disp,
                                     "agent_recommendation": c["agent_recommendation"]})
                if c["blind_rereview"] or should_sample_blind_review(tid):
                    blind_reviews.append({"timestamp": ts, "task_id": tid, "lane": lane,
                                          "disposition": disp,
                                          "review_status": c["review_status"],
                                          "sample_reason": "blind-rereview",
                                          "agent_recommendation": c["agent_recommendation"]})
    return {"transitions": transitions, "dispositions": dispositions, "costs": costs,
            "blind_reviews": blind_reviews}


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


def export_events(vault: Path, prev: dict, cards: list[dict]) -> dict:
    ev = compute_events(prev, cards)
    append_jsonl(vault / TRANSITIONS_RELPATH, ev["transitions"])
    append_jsonl(vault / DISPOSITION_RELPATH, ev["dispositions"])
    append_jsonl(vault / COST_RELPATH, ev["costs"])
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
        ts = ts.replace(tzinfo=timezone.utc)
    now = now or datetime.now(timezone.utc)
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
                continue   # prompt already raised on the transition into done
        elif not _recently_done(c):
            continue       # first sight of an old done card -- seed cache silently
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
            what_happened=f'Lane {c["assignee"]} finished "{c["title"]}" '
                          f'(card {c["task_id"]}).',
            raised_by="board-export",
            target=str(outputs or ""),
            task_id=c["task_id"],
            lane=c["assignee"],
            dedupe_slug=f"review-{c['task_id']}",
        )
        if path is not None:
            written += 1
    return written


def run_export(vault: Path, from_json: Path | None = None) -> dict:
    cards = load_cards(from_json)
    prev = load_state_cache(vault)
    events = export_events(vault, prev, cards)   # diff BEFORE the cache is overwritten
    prompts = export_review_prompts(vault, prev, cards)
    exported = export_markdown(vault, cards)
    snap = export_snapshot(vault, cards)
    save_state_cache(vault, cards)
    return {"exported_cards": len(exported), "snapshot": snap["totals"],
            "events": events, "review_prompts": prompts}


# --------------------------------------------------------------------------- #
# Self-test
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", help="vault root")
    ap.add_argument("--from-json", type=Path, help="read cards from a JSON file instead of `hermes kanban list --json`")
    args = ap.parse_args()

    if not args.vault:
        ap.error("provide --vault <path>")
    vault = resolve_vault(args.vault)

    try:
        result = run_export(vault, args.from_json)
    except FileNotFoundError:
        sys.exit("`hermes` not found on PATH (and no --from-json given).")
    except subprocess.CalledProcessError as exc:
        sys.exit(f"`hermes kanban list --json` failed (exit {exc.returncode}): {exc.stderr}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
