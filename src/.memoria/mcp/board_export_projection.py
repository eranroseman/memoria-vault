#!/usr/bin/env python3
"""Markdown and snapshot projections for board export."""

from __future__ import annotations

from pathlib import Path

from _shared import append_jsonl, now_iso, safe_filename
from board_export_common import (
    BOARD_RELDIR,
    LIVE_STATUSES,
    REVIEW_QUEUE_STATES,
    SNAPSHOT_RELPATH,
    normalize,
)


def _yaml_scalar(v) -> str:
    """Render a frontmatter scalar: ints bare, strings double-quoted+escaped."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    s = str(v).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


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
        fname = safe_filename(c["task_id"]) + ".md"
        (board / fname).write_text(card_markdown(c), encoding="utf-8")
        written.add(fname)
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
        lane = lanes.setdefault(
            c["assignee"],
            {"running": 0, "ready": 0, "blocked": 0, "review_queue": 0, "retrying": 0},
        )
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
