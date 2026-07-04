#!/usr/bin/env python3
"""reconcile.py — the ingest backstops (ADR-30).

Re-ingest must be serialized: find-or-create is idempotent in writes but only
safe when duplicate work converges on one durable request. Neither ingest sweep
writes the vault directly; each detector returns an idempotent local re-ingest
intent (`reingest:<citekey>`) for the engine queue to run.

Two distinct backstops, distinct sources:

  (a) reconcile  — reconcile capture-intake.jsonl against created notes; re-drive
                   any capture whose Tier-0 stub never landed (a failed first write).
  (b) retry      — scan the vault for notes still at `ingest_status: tier0`
                   (Tier-1 never completed) and re-drive their enrichment.

`--dry-run` reports what *would* be enqueued without touching anything.

capture-intake.jsonl record (one JSON object per line, append-only; written by the
capture entry point *before* the gated note write — the durability anchor):

    {"ts": "<ISO-8601 UTC>", "citekey": "<key>", "source": "zotero",
     "note_path": "catalog/sources/<source_id>/source.md"}
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from memoria_vault.runtime.subsystems.processing.ingest.link import read_frontmatter

SOURCE_ROOT = "catalog/sources"


def read_log(log_path: Path) -> dict:
    """Parse capture-intake.jsonl -> {citekey: record}, last write wins."""
    out: dict = {}
    if not log_path.is_file():
        return out
    for line in log_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        ck = rec.get("citekey")
        if ck:
            out[ck] = rec
    return out


def note_for(citekey: str, vault: Path) -> Path | None:
    """Return the existing note for a citekey (by filename) if any."""
    root = vault / SOURCE_ROOT
    for source in (root / citekey / "source.md",):
        if source.is_file():
            return source
    if root.is_dir():
        for source in root.glob("*/source.md"):
            fm = read_frontmatter(source)
            if fm.get("citekey") == citekey or fm.get("source_id") == citekey:
                return source
    return None


def scan_captured(vault: Path) -> list:
    """Notes still parked at the Tier-0 floor: ingest_status==tier0 (Tier-1 never completed).

    The entity itself is ``lifecycle: current`` from creation (ADR-50); ``ingest_status``
    is the tier discriminator, so the retry sweep keys on it alone.
    """
    out = []
    d = vault / SOURCE_ROOT
    if d.is_dir():
        for md in sorted(d.glob("*/source.md")):
            fm = read_frontmatter(md)
            if fm.get("ingest_status") == "tier0":
                out.append({"citekey": fm.get("citekey") or md.stem, "path": str(md)})
    return out


def enqueue_reingest(citekey: str, reason: str, dry_run: bool = False) -> str:
    """Return ONE idempotent local re-ingest request id for a citekey."""
    if dry_run:
        return "DRY"
    return f"planned:reingest:{citekey}:{reason}"


def reconcile(log_path: Path, vault: Path, dry_run: bool = False) -> dict:
    """(a) re-drive captures logged but with no note on disk."""
    records = read_log(log_path)
    orphans, enqueued = [], []
    for ck in records:
        if note_for(ck, vault) is None:
            orphans.append(ck)
            enqueued.append(
                {"citekey": ck, "card": enqueue_reingest(ck, "stub-never-landed", dry_run)}
            )
    return {
        "pass": "reconcile",
        "logged": len(records),
        "orphans": len(orphans),
        "enqueued": enqueued,
        "dry_run": dry_run,
    }


def retry(vault: Path, dry_run: bool = False) -> dict:
    """(b) re-drive captured notes stuck at the Tier-0 floor (Tier-1 never completed)."""
    stuck = scan_captured(vault)
    enqueued = [
        {
            "citekey": n["citekey"],
            "card": enqueue_reingest(n["citekey"], "tier1-incomplete", dry_run),
        }
        for n in stuck
    ]
    return {"pass": "retry", "stuck": len(stuck), "enqueued": enqueued, "dry_run": dry_run}


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Ingest backstops: reconcile + retry sweeps (ADR-30)")
    ap.add_argument("--vault", help="vault root")
    ap.add_argument(
        "--log", help="capture-intake.jsonl (default <vault>/system/logs/capture-intake.jsonl)"
    )
    ap.add_argument("--reconcile", action="store_true", help="run pass (a) only")
    ap.add_argument("--retry", action="store_true", help="run pass (b) only")
    ap.add_argument("--dry-run", action="store_true", help="report without enqueuing")
    a = ap.parse_args()
    if not a.vault:
        ap.error("provide --vault")
    vault = Path(a.vault)
    log = Path(a.log) if a.log else vault / "system/logs/capture-intake.jsonl"
    do_all = not (a.reconcile or a.retry)
    out = []
    if a.reconcile or do_all:
        out.append(reconcile(log, vault, a.dry_run))
    if a.retry or do_all:
        out.append(retry(vault, a.dry_run))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
