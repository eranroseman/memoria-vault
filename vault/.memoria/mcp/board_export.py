#!/usr/bin/env python3
"""Board exporter -- project the Hermes Kanban into Dataview-queryable files.

The authoritative board is the Hermes built-in Kanban (~/.hermes/kanban.db).
Obsidian's Dataview cannot query that database, so this script writes two
read-only projections the dashboards consume (see
docs/explanation/kanban-board/board-export.md):

  00-meta/board/<task_id>.md          one markdown file per live card  (board-state dashboard)
  00-meta/02-logs/board-state.jsonl   per-lane count snapshot, one line per run (status line)

Source of truth: `hermes kanban list --json` (or `--from-json <file>` for tests
and offline runs). The export is ONE-WAY (board -> files); editing the markdown
never changes the board. Intended to run on a cron cadence matching the
dispatcher (~60s); the Linter owns rotation/cleanup of the projected files.

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

BOARD_RELDIR = "00-meta/board"
SNAPSHOT_RELPATH = "00-meta/02-logs/board-state.jsonl"
LIVE_STATUSES = ("triage", "todo", "ready", "running", "blocked", "done")  # not archived
REVIEW_QUEUE_STATES = ("requested", "in-review")   # done cards awaiting a human decision


# --------------------------------------------------------------------------- #
# Loading cards
# --------------------------------------------------------------------------- #
def load_cards(from_json: Path | None = None) -> list[dict]:
    """Return the board's live cards as a list of dicts. Reads a JSON file when
    given (tests/offline), else shells out to `hermes kanban list --json`."""
    if from_json is not None:
        raw = from_json.read_text(encoding="utf-8")
    else:
        proc = subprocess.run(
            ["hermes", "kanban", "list", "--json"],
            capture_output=True, text=True, check=True)
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
        "last_updated": _first(card, "updated_at", "modified_at", "created_at"),
        "summary": summary,
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


def run_export(vault: Path, from_json: Path | None = None) -> dict:
    cards = load_cards(from_json)
    exported = export_markdown(vault, cards)
    snap = export_snapshot(vault, cards)
    return {"exported_cards": len(exported), "snapshot": snap["totals"]}


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
