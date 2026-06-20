#!/usr/bin/env python3
"""Append successful cron heartbeats for deferred always-on triggers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _shared import now_iso, resolve_vault

HEARTBEAT_RELPATH = "system/logs/cron-heartbeat.jsonl"


def append_heartbeat(vault: Path, job: str) -> dict:
    record = {
        "timestamp": now_iso(),
        "job": job,
        "status": "success",
        "source": "cron-wrapper",
    }
    log = vault / HEARTBEAT_RELPATH
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", required=True, help="vault root")
    ap.add_argument("--job", required=True, help="cron job name")
    args = ap.parse_args()
    append_heartbeat(resolve_vault(args.vault), args.job)


if __name__ == "__main__":
    main()
