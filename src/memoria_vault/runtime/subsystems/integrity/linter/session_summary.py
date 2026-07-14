#!/usr/bin/env python3
"""session_summary — per-request deterministic digests of the audit log.

The Linter is zero-LLM, so the per-request
record is a *deterministic digest*, not an LLM narrative: this operation groups
`system/logs/audit.jsonl` entries by `request_id` and, for each request not yet
summarized, writes one JSONL file under
`system/logs/sessions/` named `YYYY-MM-DD-HHMM.jsonl` from the session's first
timestamp (a deterministic `-2`, `-3`, … suffix disambiguates two requests that
share a start minute). Each file carries a header record (request_id, actors,
start/end, counts by action and decision) and one record per touched path
(actions, final decision, final after_hash).

Idempotent by construction: a request whose `request_id` already appears in an
existing digest header is never re-written, and a request whose last activity
is younger than the quiet window (24 h) is left for a later run so an in-flight
request is never summarized early. Malformed audit lines are skipped, mirroring
the detectors.

Usage:
  python3 session_summary.py --vault <path> [--quiet-hours H]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from memoria_vault.runtime.time import parse_iso
from memoria_vault.runtime.vaultio import write_text_durable

AUDIT_RELPATH = "system/logs/audit.jsonl"
SESSIONS_RELDIR = "system/logs/sessions"
QUIET_HOURS = 24.0


def _parse_ts(value) -> datetime | None:
    ts = parse_iso(value)
    return ts if ts is None or ts.tzinfo else ts.replace(tzinfo=UTC)


def load_sessions(vault: Path) -> dict[str, list[dict]]:
    """Audit entries grouped by request_id."""
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
        request_id, ts = e.get("request_id"), _parse_ts(e.get("timestamp"))
        if not request_id or ts is None:
            continue
        e["_ts"] = ts
        sessions.setdefault(str(request_id), []).append(e)
    return sessions


def summarized_request_ids(vault: Path) -> set[str]:
    """request_ids already digested -- read from each existing file's header line."""
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
            if isinstance(h, dict) and h.get("record") == "session" and h.get("request_id"):
                out.add(str(h["request_id"]))
    return out


def digest(request_id: str, entries: list[dict]) -> list[dict]:
    """The JSONL records for one session: a header, then one record per path."""
    entries = sorted(entries, key=lambda e: e["_ts"])
    actions: dict[str, int] = {}
    decisions: dict[str, int] = {}
    actors: set[str] = set()
    paths: dict[str, dict] = {}
    for e in entries:
        if e.get("actor"):
            actors.add(str(e["actor"]))
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
        "request_id": request_id,
        "actors": sorted(actors),
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
    now = now or datetime.now(UTC)
    done = summarized_request_ids(vault)
    outdir = vault / SESSIONS_RELDIR
    written: list[Path] = []
    sessions = load_sessions(vault)
    # Deterministic order (first timestamp, then request_id) so suffixes are stable.
    for request_id, entries in sorted(
        sessions.items(), key=lambda kv: (min(e["_ts"] for e in kv[1]), kv[0])
    ):
        if request_id in done:
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
        records = digest(request_id, entries)
        write_text_durable(
            outdir / name,
            "\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n",
        )
        written.append(outdir / name)
        done.add(request_id)
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
