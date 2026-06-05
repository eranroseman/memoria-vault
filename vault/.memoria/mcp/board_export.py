#!/usr/bin/env python3
"""Board exporter -- project the Hermes Kanban into Dataview-queryable files and
append the per-card telemetry time-series.

The authoritative board is the Hermes built-in Kanban (~/.hermes/kanban.db).
Obsidian's Dataview cannot query that database, so this script writes read-only
projections the dashboards consume, plus append-only event logs the metrics
aggregator and any publication analysis read (see docs/reference/telemetry.md):

  99-system/board/<task_id>.md          one markdown file per live card  (board-state dashboard)
  99-system/logs/board-state.jsonl   per-lane count snapshot, one line per run (status line)
  99-system/logs/board-transitions.jsonl  per-card state/review transitions (time-series)
  99-system/logs/disposition.jsonl   accept | edit | reject per review decision (UN-BACKFILLABLE)
  99-system/logs/cost.jsonl          API spend + token counts per card at completion

Transitions/disposition/cost are computed by diffing this run's board against the
previous run, cached in `99-system/logs/.board-state-cache.json`. Source of
truth: `hermes kanban list --json` (or `--from-json <file>` for tests/offline).
The export is ONE-WAY (board -> files). Run on a cron cadence (~60s); the Linter
owns rotation/cleanup of the projected files and logs.

    python board_export.py --vault <path>                  # read `hermes kanban list --json`
    python board_export.py --vault <path> --from-json cards.json
    python board_export.py --self-test
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BOARD_RELDIR = "99-system/board"
SNAPSHOT_RELPATH = "99-system/logs/board-state.jsonl"
TRANSITIONS_RELPATH = "99-system/logs/board-transitions.jsonl"  # per-card status/review changes
DISPOSITION_RELPATH = "99-system/logs/disposition.jsonl"        # accept | edit | reject (un-backfillable)
COST_RELPATH = "99-system/logs/cost.jsonl"                      # API spend + tokens per card at completion
STATE_CACHE_RELPATH = "99-system/logs/.board-state-cache.json"  # internal: last-seen state per card (for diffing)
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
        "last_updated": _iso_ts(_first(card, "updated_at", "modified_at", "created_at")),
        "summary": summary,
        # --- telemetry overlay (all best-effort; empty when Hermes doesn't supply them) ---
        "agent_recommendation": md.get("agent_recommendation", md.get("agent_verdict", "")),
        "disposition": md.get("disposition", ""),       # explicit "edited" wins over the derived accept/reject
        "review_requested_at": md.get("review_requested_at", ""),
        "reviewed_at": md.get("reviewed_at", ""),
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


def _safe_name(task_id: str) -> str:
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in str(task_id))


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
    """Per-lane counts (running / ready / blocked / review-queue) + totals."""
    lanes: dict[str, dict] = {}
    totals = {"running": 0, "ready": 0, "blocked": 0, "review_queue": 0}
    for raw in cards:
        c = normalize(raw)
        lane = lanes.setdefault(c["assignee"],
                                {"running": 0, "ready": 0, "blocked": 0, "review_queue": 0})
        st = c["status"]
        if st in ("running", "ready", "blocked"):
            lane[st] += 1
            totals[st] += 1
        if st == "done" and c["review_status"] in REVIEW_QUEUE_STATES:
            lane["review_queue"] += 1
            totals["review_queue"] += 1
    return {"timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "lanes": lanes, "totals": totals}


def export_snapshot(vault: Path, cards: list[dict]) -> dict:
    snap = board_snapshot(cards)
    out = vault / SNAPSHOT_RELPATH
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(snap, ensure_ascii=False) + "\n")
    return snap


# --------------------------------------------------------------------------- #
# Telemetry event logs (transitions / disposition / cost) -- diff vs last run
# --------------------------------------------------------------------------- #
def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    return {"transitions": transitions, "dispositions": dispositions, "costs": costs}


def _append_jsonl(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def export_events(vault: Path, prev: dict, cards: list[dict]) -> dict:
    ev = compute_events(prev, cards)
    _append_jsonl(vault / TRANSITIONS_RELPATH, ev["transitions"])
    _append_jsonl(vault / DISPOSITION_RELPATH, ev["dispositions"])
    _append_jsonl(vault / COST_RELPATH, ev["costs"])
    return {k: len(v) for k, v in ev.items()}


def run_export(vault: Path, from_json: Path | None = None) -> dict:
    cards = load_cards(from_json)
    prev = load_state_cache(vault)
    events = export_events(vault, prev, cards)   # diff BEFORE the cache is overwritten
    exported = export_markdown(vault, cards)
    snap = export_snapshot(vault, cards)
    save_state_cache(vault, cards)
    return {"exported_cards": len(exported), "snapshot": snap["totals"], "events": events}


# --------------------------------------------------------------------------- #
# Self-test
# --------------------------------------------------------------------------- #
def self_test() -> int:
    import tempfile

    failures = 0

    def check(name: str, cond: bool) -> None:
        nonlocal failures
        failures += not cond
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")

    sample = [
        {"task_id": "t_a1", "title": "Ingest smith2020", "status": "running",
         "assignee": "memoria-librarian", "metadata": {"review_status": "unreviewed", "retry_count": 1},
         "updated_at": "2026-05-31T10:00:00Z",
         "runs": [{"summary": "Blocker: none\nTried: lookup\nNext: enrich"}]},
        {"task_id": "t_b2", "title": "Draft answer", "status": "done",
         "assignee": "memoria-writer",
         "metadata": json.dumps({"review_status": "requested"}),    # metadata as JSON string
         "created_at": "2026-05-30T09:00:00Z"},
        {"task_id": "t_c3", "title": "Old", "status": "archived", "assignee": "memoria-writer"},
        {"task_id": "t_d4", "title": "Blocked card", "status": "blocked",
         "assignee": "memoria-librarian", "reason": "needs human input"},
    ]

    # normalize: metadata-as-string parses; defaults fill in
    n = normalize(sample[1])
    check("normalize parses string metadata", n["review_status"] == "requested")
    check("normalize defaults review_status", normalize(sample[3])["review_status"] == "unreviewed")
    check("normalize pulls run summary", "enrich" in normalize(sample[0])["summary"])
    check("normalize reads block reason", normalize(sample[3])["reason"] == "needs human input")
    check("normalize reads renamed agent_recommendation",
          normalize({"metadata": {"agent_recommendation": "clean"}})["agent_recommendation"] == "clean")
    check("normalize falls back to legacy agent_verdict",
          normalize({"metadata": {"agent_verdict": "issues-found"}})["agent_recommendation"] == "issues-found")
    check("normalize converts epoch-seconds last_updated to ISO",
          normalize({"updated_at": 1700000000})["last_updated"] == "2023-11-14T22:13:20Z")
    check("normalize converts epoch-millis last_updated to ISO",
          normalize({"updated_at": 1700000000000})["last_updated"] == "2023-11-14T22:13:20Z")
    check("normalize passes an ISO last_updated through unchanged",
          normalize(sample[0])["last_updated"] == "2026-05-31T10:00:00Z")
    check("normalize leaves last_updated empty when no timestamp",
          normalize(sample[2])["last_updated"] == "")

    with tempfile.TemporaryDirectory() as td:
        vault = Path(td)
        ids = export_markdown(vault, sample)
        board = vault / BOARD_RELDIR
        check("archived card not exported", "t_c3" not in ids and not (board / "t_c3.md").exists())
        check("live cards exported", {(board / f"{i}.md").exists() for i in ("t_a1", "t_b2", "t_d4")} == {True})
        body = (board / "t_a1.md").read_text(encoding="utf-8")
        check("markdown has frontmatter task_id", "task_id: \"t_a1\"" in body)
        check("markdown has retry_count int", "retry_count: 1" in body)
        check("markdown body carries summary", "Next: enrich" in body)

        # stale pruning: a second export without t_a1 should remove its file
        export_markdown(vault, [c for c in sample if c["task_id"] != "t_a1"])
        check("stale export pruned", not (board / "t_a1.md").exists())

        snap = export_snapshot(vault, sample)
        check("snapshot counts running", snap["totals"]["running"] == 1)
        check("snapshot counts blocked", snap["totals"]["blocked"] == 1)
        check("snapshot counts review-queue (done+requested)", snap["totals"]["review_queue"] == 1)
        check("snapshot per-lane present", snap["lanes"]["memoria-librarian"]["running"] == 1)
        lines = (vault / SNAPSHOT_RELPATH).read_text(encoding="utf-8").strip().splitlines()
        check("snapshot appends one JSONL line", len(lines) == 1 and json.loads(lines[0]))

    # --- telemetry events: two runs, diff the second against the first --------
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td)
        run1 = [
            {"task_id": "e1", "title": "x", "status": "ready",
             "assignee": "memoria-writer", "metadata": {"review_status": "unreviewed"}},
            {"task_id": "e2", "title": "y", "status": "done",
             "assignee": "memoria-writer", "metadata": {"review_status": "requested"}},
            {"task_id": "e3", "title": "z", "status": "done",
             "assignee": "memoria-verifier", "metadata": {"review_status": "requested"}},
        ]
        ev1 = export_events(vault, load_state_cache(vault), run1)
        save_state_cache(vault, run1)
        check("first run seeds cache, emits no events",
              ev1 == {"transitions": 0, "dispositions": 0, "costs": 0})

        run2 = [
            # e1: ready -> done, with cost + tokens
            {"task_id": "e1", "title": "x", "status": "done", "assignee": "memoria-writer",
             "metadata": {"review_status": "unreviewed", "cost": 0.42, "tokens_in": 800, "tokens_out": 1200}},
            # e2: requested -> approved => accepted
            {"task_id": "e2", "title": "y", "status": "done", "assignee": "memoria-writer",
             "metadata": {"review_status": "approved", "agent_recommendation": "clean"}},
            # e3: requested -> approved but human edited first => edited (explicit override)
            {"task_id": "e3", "title": "z", "status": "done", "assignee": "memoria-verifier",
             "metadata": {"review_status": "approved", "disposition": "edited"}},
        ]
        ev2 = export_events(vault, load_state_cache(vault), run2)
        save_state_cache(vault, run2)
        check("second run logs three transitions (e1 status, e2/e3 review)", ev2["transitions"] == 3)
        check("second run logs cost on completion", ev2["costs"] == 1)
        check("second run logs two dispositions", ev2["dispositions"] == 2)

        disp = [json.loads(ln) for ln in (vault / DISPOSITION_RELPATH).read_text(encoding="utf-8").strip().splitlines()]
        by_id = {d["task_id"]: d for d in disp}
        check("approve -> accepted", by_id["e2"]["disposition"] == "accepted")
        check("explicit edited overrides accepted", by_id["e3"]["disposition"] == "edited")
        cost = json.loads((vault / COST_RELPATH).read_text(encoding="utf-8").strip().splitlines()[-1])
        check("cost row carries spend + tokens", cost["cost"] == 0.42 and cost["tokens_out"] == 1200)
        tr = [json.loads(ln) for ln in (vault / TRANSITIONS_RELPATH).read_text(encoding="utf-8").strip().splitlines()]
        check("transition records status change e1 ready->done",
              any(t["task_id"] == "e1" and t["from"] == "ready" and t["to"] == "done" for t in tr))
        check("no spurious events on an unchanged re-run", export_events(vault, load_state_cache(vault), run2) ==
              {"transitions": 0, "dispositions": 0, "costs": 0})

    print(f"\n{'OK' if not failures else 'FAILED'}: {failures} failing check(s).")
    return failures


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", help="vault root")
    ap.add_argument("--from-json", type=Path, help="read cards from a JSON file instead of `hermes kanban list --json`")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(1 if self_test() else 0)
    if not args.vault:
        ap.error("provide --vault <path> or --self-test")
    vault = Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        sys.exit(f"not a directory: {vault}")

    try:
        result = run_export(vault, args.from_json)
    except FileNotFoundError:
        sys.exit("`hermes` not found on PATH (and no --from-json given).")
    except subprocess.CalledProcessError as exc:
        sys.exit(f"`hermes kanban list --json` failed (exit {exc.returncode}): {exc.stderr}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
