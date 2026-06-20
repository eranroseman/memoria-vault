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
  system/logs/disposition.jsonl   accept | edit | reject per review decision (QuickAdd review action)
  system/logs/cost.jsonl          API spend + token counts per card at completion
  system/logs/cost-misses.jsonl   completion rows whose Hermes session join could not be completed
  system/logs/blind-review-samples.jsonl  deterministic sample requests for blind re-review
  inbox/work-prompt-review-*.md   ONE review prompt per card that reaches `done`
                                  (the Inbox is the PI's slice of the board, ADR-51)

Transitions/cost are computed by diffing this run's board against the previous run,
cached in `system/logs/.board-state-cache.json`. Source of truth:
`hermes kanban list --json` (or `--from-json <file>` for tests/offline). Cost rows
join completed cards to Hermes per-profile `state.db` session rows through
`hermes kanban show <id> --json` -> `runs[].metadata.worker_session_id`.
The export is ONE-WAY (board -> files). Run on a cron cadence (~60s); the Linter
owns rotation/cleanup of the projected files and logs.

    python board_export.py --vault <path>                  # read `hermes kanban list --json`
    python board_export.py --vault <path> --from-json cards.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Direct cron/script execution may run before an editable install is active.
_REPO_DIR = Path(__file__).resolve().parents[3]
if str(_REPO_DIR) not in sys.path:
    sys.path.insert(0, str(_REPO_DIR))

from _shared import append_jsonl, now_iso, resolve_vault, safe_filename  # noqa: E402

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
COST_MISSES_RELPATH = "system/logs/cost-misses.jsonl"        # done cards whose session join was unavailable
BLIND_REVIEW_RELPATH = "system/logs/blind-review-samples.jsonl"  # sampled terminal reviews
STATE_CACHE_RELPATH = "system/logs/.board-state-cache.json"  # internal: last-seen state per card (for diffing)
LIVE_STATUSES = ("triage", "todo", "ready", "running", "blocked", "done")  # not archived
REVIEW_QUEUE_STATES = ("requested",)   # done cards handed off for human review (review_status: requested)
TERMINAL_REVIEW = {"approved": "accepted", "rejected": "rejected", "changes-requested": "rejected"}
REQUIRED_SESSION_COLUMNS = {
    "id",
    "model",
    "input_tokens",
    "output_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
    "reasoning_tokens",
    "estimated_cost_usd",
    "actual_cost_usd",
    "cost_status",
    "cost_source",
    "billing_provider",
    "pricing_version",
}


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


class CostDoctorError(RuntimeError):
    """Raised when the Hermes cost-capture contract drifts."""


def load_card_detail(task_id: str) -> dict:
    """Return `hermes kanban show <task_id> --json` as a dict."""
    try:
        proc = subprocess.run(
            ["hermes", "kanban", "show", task_id, "--json"],
            capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        raise CostDoctorError(
            f"hermes kanban show {task_id!r} failed with exit {exc.returncode}: "
            f"{exc.stderr.strip()}"
        ) from exc
    except FileNotFoundError as exc:
        raise CostDoctorError("'hermes' not found on PATH for cost join") from exc
    data = json.loads(proc.stdout)
    if isinstance(data, dict) and isinstance(data.get("task"), dict):
        return data["task"]
    if isinstance(data, dict):
        return data
    raise CostDoctorError(f"hermes kanban show {task_id!r} returned non-object JSON")


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


def _metadata_value(value) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def worker_session_ids(card: dict) -> list[str]:
    """Extract worker session ids from Hermes run metadata."""
    out: list[str] = []
    runs = card.get("runs") or []
    if not isinstance(runs, list):
        return out
    for run in runs:
        if not isinstance(run, dict):
            continue
        md = _metadata_value(run.get("metadata"))
        sid = md.get("worker_session_id") or run.get("worker_session_id")
        if sid:
            out.append(str(sid))
    return out


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
        "agent_recommendation": md.get("agent_recommendation", ""),
        "expanded_at": md.get("expanded_at", ""),
        "review_requested_at": md.get("review_requested_at", ""),
        "reviewed_at": md.get("reviewed_at", ""),
        "blind_rereview": md.get("blind_rereview", False),
    }


# --------------------------------------------------------------------------- #
# Hermes cost join
# --------------------------------------------------------------------------- #
def _hermes_home(hermes_home: Path | str | None = None) -> Path:
    raw = hermes_home or os.environ.get("HERMES_HOME") or "~/.hermes"
    return Path(raw).expanduser()


def state_db_for_lane(lane: str, hermes_home: Path | str | None = None) -> Path:
    return _hermes_home(hermes_home) / "profiles" / lane / "state.db"


def validate_session_schema(db_path: Path) -> None:
    """Fail closed when Hermes' pinned session-store schema drifts."""
    try:
        with sqlite3.connect(db_path) as con:
            rows = con.execute("PRAGMA table_info(sessions)").fetchall()
    except sqlite3.DatabaseError as exc:
        raise CostDoctorError(f"cannot inspect Hermes session store {db_path}: {exc}") from exc
    columns = {row[1] for row in rows}
    if not columns:
        raise CostDoctorError(f"Hermes session store {db_path} has no sessions table")
    missing = sorted(REQUIRED_SESSION_COLUMNS - columns)
    if missing:
        raise CostDoctorError(
            f"Hermes session schema drift in {db_path}: missing columns {', '.join(missing)}"
        )


def run_cost_doctor(hermes_home: Path | str | None = None) -> dict:
    """Validate the Hermes session-store contract before trusting cost joins."""
    home = _hermes_home(hermes_home)
    profiles = home / "profiles"
    checked: list[str] = []
    if profiles.exists():
        for db_path in sorted(profiles.glob("*/state.db")):
            validate_session_schema(db_path)
            checked.append(db_path.parent.name)
    return {
        "ok": True,
        "hermes_home": str(home),
        "profiles_checked": checked,
        "required_session_columns": sorted(REQUIRED_SESSION_COLUMNS),
    }


def read_session_row(db_path: Path, session_id: str) -> dict | None:
    validate_session_schema(db_path)
    fields = ", ".join(sorted(REQUIRED_SESSION_COLUMNS))
    try:
        with sqlite3.connect(db_path) as con:
            con.row_factory = sqlite3.Row
            row = con.execute(
                f"SELECT {fields} FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
    except sqlite3.DatabaseError as exc:
        raise CostDoctorError(f"cannot read Hermes session store {db_path}: {exc}") from exc
    return dict(row) if row is not None else None


def cost_event_from_session(ts: str, task_id: str, lane: str, session_id: str,
                            row: dict) -> dict:
    cost = row.get("actual_cost_usd")
    if cost in (None, ""):
        cost = row.get("estimated_cost_usd")
    return {
        "timestamp": ts,
        "task_id": task_id,
        "lane": lane,
        "session_id": session_id,
        "cost": cost,
        "tokens_in": row.get("input_tokens"),
        "tokens_out": row.get("output_tokens"),
        "input_tokens": row.get("input_tokens"),
        "output_tokens": row.get("output_tokens"),
        "cache_read_tokens": row.get("cache_read_tokens"),
        "cache_write_tokens": row.get("cache_write_tokens"),
        "reasoning_tokens": row.get("reasoning_tokens"),
        "estimated_cost_usd": row.get("estimated_cost_usd"),
        "actual_cost_usd": row.get("actual_cost_usd"),
        "cost_status": row.get("cost_status"),
        "cost_source": row.get("cost_source"),
        "billing_provider": row.get("billing_provider"),
        "pricing_version": row.get("pricing_version"),
        "model": row.get("model"),
        "source": "hermes-session-store",
    }


def cost_miss(ts: str, task_id: str, lane: str, reason: str, *,
              session_id: str = "", source: str = "hermes-session-store") -> dict:
    return {
        "timestamp": ts,
        "task_id": task_id,
        "lane": lane,
        "reason": reason,
        "session_id": session_id,
        "source": source,
    }


class HermesCostLookup:
    """Join completed board cards to Hermes per-profile session cost rows."""

    def __init__(self, hermes_home: Path | str | None = None, show_card=None):
        self.hermes_home = _hermes_home(hermes_home)
        self.show_card = show_card or load_card_detail

    def _session_id_for(self, raw: dict, task_id: str) -> str:
        ids = worker_session_ids(raw)
        if ids:
            return ids[-1]
        detail = self.show_card(task_id)
        ids = worker_session_ids(detail)
        if not ids:
            raise CostDoctorError(
                f"hermes kanban show {task_id!r} did not expose "
                "runs[].metadata.worker_session_id"
            )
        return ids[-1]

    def __call__(self, raw: dict, card: dict, ts: str) -> tuple[dict | None, dict | None]:
        task_id, lane = card["task_id"], card["assignee"]
        session_id = self._session_id_for(raw, task_id)
        db_path = state_db_for_lane(lane, self.hermes_home)
        if not db_path.exists():
            return None, cost_miss(ts, task_id, lane, "missing-state-db",
                                   session_id=session_id)
        row = read_session_row(db_path, session_id)
        if row is None:
            return None, cost_miss(ts, task_id, lane, "missing-session-row",
                                   session_id=session_id)
        return cost_event_from_session(ts, task_id, lane, session_id, row), None


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
    frontmatter = {
        "title": card["title"],
        "type": "worker-card",
        "lifecycle": "current",
        "task_id": card["task_id"],
        "lane": card["assignee"],
        "status": card["status"],
        "review_status": card["review_status"],
        "retry_count": card["retry_count"],
        "reason": card["reason"],
        "as_of": card["last_updated"],
        "created": card["created_at"],
    }
    lines = ["---"]
    lines += [f"{k}: {_yaml_scalar(v)}" for k, v in frontmatter.items()]
    lines += ["---", "", f"# {card['title']}", ""]
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


def compute_events(prev: dict, cards: list[dict], cost_lookup=None) -> dict:
    """Diff previous per-card state vs current; return transition / disposition /
    cost event rows. A card unseen before counts as a transition into its state."""
    ts = _ts()
    transitions: list[dict] = []
    dispositions: list[dict] = []
    costs: list[dict] = []
    cost_misses: list[dict] = []
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
            if c["status"] == "done" and cost_lookup is not None:
                cost_row, miss_row = cost_lookup(raw, c, ts)
                if cost_row is not None:
                    costs.append(cost_row)
                if miss_row is not None:
                    cost_misses.append(miss_row)

        if c["review_status"] != old_review:
            transitions.append({"timestamp": ts, "task_id": tid, "lane": lane,
                                 "kind": "review", "from": old_review, "to": c["review_status"]})
            # Disposition is emitted by the human review action. The exporter only
            # samples terminal reviews for optional blind re-review.
            if c["review_status"] in TERMINAL_REVIEW:
                disp = TERMINAL_REVIEW[c["review_status"]]
                if c["blind_rereview"] or should_sample_blind_review(tid):
                    blind_reviews.append({"timestamp": ts, "task_id": tid, "lane": lane,
                                          "disposition": disp,
                                          "review_status": c["review_status"],
                                          "sample_reason": "blind-rereview",
                                          "agent_recommendation": c["agent_recommendation"]})
    return {"transitions": transitions, "dispositions": dispositions, "costs": costs,
            "cost_misses": cost_misses, "blind_reviews": blind_reviews}


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


def run_export(vault: Path, from_json: Path | None = None,
               hermes_home: Path | str | None = None) -> dict:
    cards = load_cards(from_json)
    prev = load_state_cache(vault)
    cost_lookup = None
    if from_json is None:
        run_cost_doctor(hermes_home)
        cost_lookup = HermesCostLookup(hermes_home=hermes_home)
    events = export_events(vault, prev, cards, cost_lookup=cost_lookup)   # diff BEFORE cache update
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
    ap.add_argument("--hermes-home", type=Path, help="Hermes home directory (default: $HERMES_HOME or ~/.hermes)")
    ap.add_argument("--cost-doctor", action="store_true", help="validate Hermes session-store cost capture and exit")
    args = ap.parse_args()

    if args.cost_doctor:
        try:
            print(json.dumps(run_cost_doctor(args.hermes_home), indent=2))
        except CostDoctorError as exc:
            sys.exit(f"[board_export] cost doctor failed: {exc}")
        return

    if not args.vault:
        ap.error("provide --vault <path>")
    vault = resolve_vault(args.vault)

    try:
        result = run_export(vault, args.from_json, hermes_home=args.hermes_home)
    except FileNotFoundError:
        sys.exit("`hermes` not found on PATH (and no --from-json given).")
    except subprocess.CalledProcessError as exc:
        sys.exit(f"`hermes kanban list --json` failed (exit {exc.returncode}): {exc.stderr}")
    except CostDoctorError as exc:
        sys.exit(f"[board_export] cost doctor failed: {exc}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
