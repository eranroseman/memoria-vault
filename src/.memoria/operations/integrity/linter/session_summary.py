#!/usr/bin/env python3
"""session_summary — per-session deterministic digests of the audit log (ADR-25).

The second of ADR-25's two logs. The Linter is zero-LLM, so the per-session
record is a *deterministic digest*, not an LLM narrative: this operation groups
`system/logs/audit.jsonl` entries by `task_id` (one session = one task) and, for
each session not yet summarized, writes one JSONL file under
`system/logs/sessions/` named `YYYY-MM-DD-HHMM.jsonl` from the session's first
timestamp (a deterministic `-2`, `-3`, … suffix disambiguates two sessions that
share a start minute). Each file carries a header record (task_id, profiles,
start/end, counts by action and decision) and one record per touched path
(actions, final decision, final after_hash).

Idempotent by construction: a session whose task_id already appears in an
existing digest header is never re-written, and a session whose last activity
is younger than the quiet window (24 h) is left for a later run so an in-flight
session is never summarized early. Malformed audit lines are skipped, mirroring
the detectors.

Usage:
  python3 session_summary.py --vault <path> [--quiet-hours H]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

AUDIT_RELPATH = "system/logs/audit.jsonl"
SESSIONS_RELDIR = "system/logs/sessions"
QUIET_HOURS = 24.0


def _parse_ts(value) -> datetime | None:
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def load_sessions(vault: Path) -> dict[str, list[dict]]:
    """Audit entries grouped by task_id; entries without a parseable timestamp
    or a task_id (and malformed lines) are skipped."""
    log = vault / AUDIT_RELPATH
    sessions: dict[str, list[dict]] = {}
    if not log.is_file():
        return sessions
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(e, dict):
            continue
        tid, ts = e.get("task_id"), _parse_ts(e.get("timestamp"))
        if not tid or ts is None:
            continue
        e["_ts"] = ts
        sessions.setdefault(str(tid), []).append(e)
    return sessions


def summarized_task_ids(vault: Path) -> set[str]:
    """task_ids already digested — read from each existing file's header line."""
    out: set[str] = set()
    d = vault / SESSIONS_RELDIR
    if not d.is_dir():
        return out
    for f in sorted(d.glob("*.jsonl")):
        try:
            first = f.read_text(encoding="utf-8", errors="replace").splitlines()[:1]
        except OSError:
            continue
        for line in first:
            try:
                h = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(h, dict) and h.get("record") == "session" and h.get("task_id"):
                out.add(str(h["task_id"]))
    return out


def digest(task_id: str, entries: list[dict]) -> list[dict]:
    """The JSONL records for one session: a header, then one record per path."""
    entries = sorted(entries, key=lambda e: e["_ts"])
    actions: dict[str, int] = {}
    decisions: dict[str, int] = {}
    profiles: set[str] = set()
    paths: dict[str, dict] = {}
    for e in entries:
        if e.get("profile"):
            profiles.add(str(e["profile"]))
        a, d = e.get("action"), e.get("decision")
        if a:
            actions[a] = actions.get(a, 0) + 1
        if d:
            decisions[d] = decisions.get(d, 0) + 1
        p = e.get("path")
        if not p:
            continue
        rec = paths.setdefault(
            p,
            {
                "record": "path",
                "path": p,
                "actions": set(),
                "final_decision": None,
                "after_hash": None,
            },
        )
        if a:
            rec["actions"].add(a)
        if d == "write_complete":
            rec["after_hash"] = e.get("after_hash")
        elif d:
            rec["final_decision"] = d
    header = {
        "record": "session",
        "task_id": task_id,
        "profiles": sorted(profiles),
        "started": entries[0]["_ts"].strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ended": entries[-1]["_ts"].strftime("%Y-%m-%dT%H:%M:%SZ"),
        "entries": len(entries),
        "actions": dict(sorted(actions.items())),
        "decisions": dict(sorted(decisions.items())),
    }
    out = [header]
    for p in sorted(paths):
        rec = dict(paths[p])
        rec["actions"] = sorted(rec["actions"])
        out.append(rec)
    return out


def write_summaries(
    vault: Path, quiet_hours: float = QUIET_HOURS, now: datetime | None = None
) -> list[Path]:
    """Digest every finished, not-yet-summarized session. Returns files written."""
    now = now or datetime.now(timezone.utc)
    done = summarized_task_ids(vault)
    outdir = vault / SESSIONS_RELDIR
    written: list[Path] = []
    sessions = load_sessions(vault)
    # Deterministic order (first timestamp, then task_id) so suffixes are stable.
    for tid, entries in sorted(
        sessions.items(), key=lambda kv: (min(e["_ts"] for e in kv[1]), kv[0])
    ):
        if tid in done:
            continue
        last = max(e["_ts"] for e in entries)
        if (now - last).total_seconds() < quiet_hours * 3600:
            continue  # in-flight: inside the quiet window
        first = min(e["_ts"] for e in entries)
        base = first.strftime("%Y-%m-%d-%H%M")
        name, n = f"{base}.jsonl", 2
        while (outdir / name).exists():
            name, n = f"{base}-{n}.jsonl", n + 1
        outdir.mkdir(parents=True, exist_ok=True)
        records = digest(tid, entries)
        (outdir / name).write_text(
            "\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n", encoding="utf-8"
        )
        written.append(outdir / name)
        done.add(tid)
    return written


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--vault", type=Path, required=True, help="vault root")
    ap.add_argument(
        "--quiet-hours",
        type=float,
        default=QUIET_HOURS,
        help="leave sessions active within the last H hours unsummarized",
    )
    args = ap.parse_args()
    if not args.vault.is_dir():
        sys.exit(f"not a directory: {args.vault}")
    written = write_summaries(args.vault, quiet_hours=args.quiet_hours)
    for f in written:
        print(f"  {f.relative_to(args.vault).as_posix()}")
    print(f"session-summary: wrote {len(written)} digest(s)")


if __name__ == "__main__":
    main()
