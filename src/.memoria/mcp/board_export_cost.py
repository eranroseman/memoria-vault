#!/usr/bin/env python3
"""Hermes cost/session-store joins for board export."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from pathlib import Path

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


class CostDoctorError(RuntimeError):
    """Raised when the Hermes cost-capture contract drifts."""


def load_card_detail(task_id: str) -> dict:
    """Return `hermes kanban show <task_id> --json` as a dict."""
    try:
        proc = subprocess.run(
            ["hermes", "kanban", "show", task_id, "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
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
                # `fields` is a join of the hardcoded REQUIRED_SESSION_COLUMNS set;
                # the only runtime value (session_id) is bound via a `?` placeholder.
                f"SELECT {fields} FROM sessions WHERE id = ?",  # noqa: S608
                (session_id,),
            ).fetchone()
    except sqlite3.DatabaseError as exc:
        raise CostDoctorError(f"cannot read Hermes session store {db_path}: {exc}") from exc
    return dict(row) if row is not None else None


def cost_event_from_session(ts: str, task_id: str, lane: str, session_id: str, row: dict) -> dict:
    cost = row.get("actual_cost_usd")
    if cost in (None, ""):
        cost = row.get("estimated_cost_usd")
    return {
        "timestamp": ts,
        "task_id": task_id,
        "lane": lane,
        "session_id": session_id,
        "cost": cost,
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


def cost_miss(
    ts: str,
    task_id: str,
    lane: str,
    reason: str,
    *,
    session_id: str = "",
    source: str = "hermes-session-store",
) -> dict:
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
                f"hermes kanban show {task_id!r} did not expose runs[].metadata.worker_session_id"
            )
        return ids[-1]

    def __call__(self, raw: dict, card: dict, ts: str) -> tuple[dict | None, dict | None]:
        task_id, lane = card["task_id"], card["assignee"]
        session_id = self._session_id_for(raw, task_id)
        db_path = state_db_for_lane(lane, self.hermes_home)
        if not db_path.exists():
            return None, cost_miss(ts, task_id, lane, "missing-state-db", session_id=session_id)
        row = read_session_row(db_path, session_id)
        if row is None:
            return None, cost_miss(ts, task_id, lane, "missing-session-row", session_id=session_id)
        return cost_event_from_session(ts, task_id, lane, session_id, row), None
