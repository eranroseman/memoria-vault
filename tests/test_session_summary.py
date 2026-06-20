"""L1 component test for session_summary — ADR-25's per-session digests."""

import json
from datetime import UTC, datetime

from operations.integrity.linter import session_summary as ss

NOW = datetime(2026, 6, 12, 12, 0, tzinfo=UTC)


def _entry(ts, task, path, action="write", decision="allow_with_log", **kw):
    e = {
        "timestamp": ts,
        "profile": "memoria-writer",
        "action": action,
        "path": path,
        "task_id": task,
        "decision": decision,
    }
    e |= kw
    return e


def _write_audit(v, records, extra_lines=()):
    (v / "system/logs").mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r) for r in records] + list(extra_lines)
    (v / "system/logs/audit.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_grouping_naming_and_content(tmp_path):
    v = tmp_path
    _write_audit(
        v,
        [
            _entry("2026-06-01T09:05:00Z", "T-A", "projects/a.md"),
            _entry(
                "2026-06-01T09:06:00Z",
                "T-A",
                "projects/a.md",
                decision="write_complete",
                after_hash="sha256:" + "a" * 64,
            ),
            _entry(
                "2026-06-01T09:07:00Z",
                "T-A",
                "notes/claims/c.md",
                action="write",
                decision="dry_run",
            ),
            _entry("2026-06-02T14:30:00Z", "T-B", "inbox/x.md", action="append"),
        ],
        extra_lines=[
            "{garbage",
            json.dumps({"timestamp": "bad", "task_id": "T-X"}),
            json.dumps({"path": "no-task.md"}),
        ],
    )
    written = ss.write_summaries(v, now=NOW)
    names = [p.name for p in written]
    assert names == ["2026-06-01-0905.jsonl", "2026-06-02-1430.jsonl"]

    lines = [
        json.loads(line)
        for line in (v / "system/logs/sessions/2026-06-01-0905.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    header, paths = lines[0], lines[1:]
    assert header["record"] == "session" and header["task_id"] == "T-A"
    assert header["profiles"] == ["memoria-writer"]
    assert header["started"] == "2026-06-01T09:05:00Z"
    assert header["ended"] == "2026-06-01T09:07:00Z"
    assert header["entries"] == 3
    assert header["decisions"] == {"allow_with_log": 1, "dry_run": 1, "write_complete": 1}
    by_path = {r["path"]: r for r in paths}
    assert set(by_path) == {"projects/a.md", "notes/claims/c.md"}
    assert by_path["projects/a.md"]["after_hash"] == "sha256:" + "a" * 64
    assert by_path["projects/a.md"]["final_decision"] == "allow_with_log"
    assert by_path["notes/claims/c.md"]["final_decision"] == "dry_run"
    assert by_path["notes/claims/c.md"]["after_hash"] is None
    # the malformed / task-less lines never produced a digest
    assert len(list((v / "system/logs/sessions").glob("*.jsonl"))) == 2


def test_idempotent_rerun_writes_nothing(tmp_path):
    v = tmp_path
    _write_audit(v, [_entry("2026-06-01T09:05:00Z", "T-A", "projects/a.md")])
    first = ss.write_summaries(v, now=NOW)
    assert len(first) == 1
    again = ss.write_summaries(v, now=NOW)
    assert again == []
    # content untouched
    assert len(list((v / "system/logs/sessions").glob("*.jsonl"))) == 1


def test_quiet_window_skips_in_flight_sessions(tmp_path):
    v = tmp_path
    recent = (NOW.replace(hour=2)).strftime("%Y-%m-%dT%H:%M:%SZ")  # 10h before NOW
    _write_audit(v, [_entry(recent, "T-LIVE", "projects/a.md")])
    assert ss.write_summaries(v, now=NOW) == []  # inside the 24h window
    later = NOW.replace(day=14)
    assert len(ss.write_summaries(v, now=later)) == 1  # quiet long enough


def test_shared_start_minute_gets_deterministic_suffix(tmp_path):
    v = tmp_path
    _write_audit(
        v,
        [
            _entry("2026-06-01T09:05:10Z", "T-A", "projects/a.md"),
            _entry("2026-06-01T09:05:50Z", "T-B", "projects/b.md"),
        ],
    )
    written = sorted(p.name for p in ss.write_summaries(v, now=NOW))
    assert written == ["2026-06-01-0905-2.jsonl", "2026-06-01-0905.jsonl"]
    # ordering is deterministic: T-A (earlier first timestamp) took the base name
    head = json.loads(
        (v / "system/logs/sessions/2026-06-01-0905.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    assert head["task_id"] == "T-A"


def test_no_audit_log_is_a_noop(tmp_path):
    assert ss.write_summaries(tmp_path, now=NOW) == []
    assert not (tmp_path / "system/logs/sessions").exists()
