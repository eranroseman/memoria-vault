#!/usr/bin/env python3
"""Shared board-export card loading and normalization."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

BOARD_RELDIR = "system/board"
SNAPSHOT_RELPATH = "system/logs/board-state.jsonl"
TRANSITIONS_RELPATH = "system/logs/board-transitions.jsonl"  # per-card status/review changes
DISPOSITION_RELPATH = "system/logs/disposition.jsonl"  # accept | edit | reject (un-backfillable)
COST_RELPATH = "system/logs/cost.jsonl"  # API spend + tokens per card at completion
COST_MISSES_RELPATH = (
    "system/logs/cost-misses.jsonl"  # done cards whose session join was unavailable
)
BLIND_REVIEW_RELPATH = "system/logs/blind-review-samples.jsonl"  # sampled terminal reviews
STATE_CACHE_RELPATH = (
    "system/logs/.board-state-cache.json"  # internal: last-seen state per card (for diffing)
)
LIVE_STATUSES = ("triage", "todo", "ready", "running", "blocked", "done")  # not archived
REVIEW_QUEUE_STATES = (
    "requested",
)  # done cards handed off for human review (review_status: requested)
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


def load_cards(from_json: Path | None = None) -> list[dict]:
    """Return the board's live cards as a list of dicts. Reads a JSON file when
    given (tests/offline), else shells out to `hermes kanban list --json`."""
    if from_json is not None:
        raw = from_json.read_text(encoding="utf-8")
    else:
        try:
            proc = subprocess.run(
                ["hermes", "kanban", "list", "--json"], capture_output=True, text=True, check=True
            )
        except subprocess.CalledProcessError as exc:
            print(
                f"[board_export] hermes kanban list failed (exit {exc.returncode}): "
                f"{exc.stderr.strip()}",
                file=sys.stderr,
            )
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
    return datetime.fromtimestamp(ts, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


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
