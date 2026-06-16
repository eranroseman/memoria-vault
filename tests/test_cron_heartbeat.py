"""L1 component tests for cron heartbeat telemetry."""

import json

import cron_heartbeat


def test_append_heartbeat_writes_success_row(tmp_path):
    rec = cron_heartbeat.append_heartbeat(tmp_path, "memoria-lint")
    rows = (tmp_path / "system" / "logs" / "cron-heartbeat.jsonl").read_text(
        encoding="utf-8"
    ).splitlines()
    logged = json.loads(rows[0])

    assert rec["job"] == "memoria-lint"
    assert logged["status"] == "success"
    assert logged["timestamp"].endswith("Z")
