#!/usr/bin/env python3
"""sweeps.py — the ingest backstops (ADR-30) + the chat-export stamp (#185).

Re-ingest must be **board-serialized** (ADR-30): find-or-create is idempotent in
writes but only safe under the single-lane WIP=1 invariant, which only serializes
*board-dispatched* work. So neither ingest sweep writes the vault — each is a
**detector that enqueues an idempotent re-ingest card** (`hermes kanban create`,
`--idempotency-key reingest:<citekey>`). The board then provides serialization,
dedup, backoff, and the failure circuit-breaker (= the `needs-human` floor).

Two distinct backstops, distinct sources:

  (a) reconcile  — reconcile capture-intake.jsonl against created notes; re-drive
                   any capture whose Tier-0 stub never landed (a failed first write).
  (b) retry      — scan the vault for notes still at `ingest_status: tier0`
                   (Tier-1 never completed) and re-drive their enrichment.

A third pass rides the same cron but is NOT a re-ingest detector:

  (c) stamp      — ACP-pane session exports land in notes/fleeting/chats/ as bare
                   markdown (the agent-client plugin writes no Memoria frontmatter).
                   This pass prepends valid fleeting frontmatter (type: fleeting,
                   lifecycle: proposed, origin: chat) so the exports surface in the
                   existing fleeting triage flow (fleeting.base, the stale-fleeting
                   detector) instead of rotting. It writes the vault DIRECTLY —
                   exempt from the board-serialization rule above because it is a
                   deterministic, idempotent, single-file rewrite with no
                   find-or-create semantics, on files no board lane touches (sole
                   other writer = the Obsidian plugin, which writes once on close).
                   Files that already start with a frontmatter fence are skipped.

`--dry-run` reports what *would* be enqueued/stamped without touching anything.

capture-intake.jsonl record (one JSON object per line, append-only; written by the
capture entry point *before* the gated note write — the durability anchor):

    {"ts": "<ISO-8601 UTC>", "citekey": "<key>", "source": "zotero",
     "note_path": "catalog/papers/<citekey>.md"}
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# import the shared frontmatter reader from the linker (same scripts dir)
try:
    from link import read_frontmatter
except ImportError:  # executed from elsewhere
    sys.path.insert(0, str(Path(__file__).parent))
    from link import read_frontmatter

SOURCE_FOLDERS = ("catalog/papers", "catalog/datasets", "catalog/repositories")
CHATS_FOLDER = "notes/fleeting/chats"  # ACP-pane export target (exportSettings.defaultFolder)
LIBRARIAN = "memoria-librarian"
SKILL = "catalog-enrich-record"  # on-disk form of catalog:enrich-record


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
    for folder in SOURCE_FOLDERS:
        p = vault / folder / f"{citekey}.md"
        if p.is_file():
            return p
    return None


def scan_captured(vault: Path) -> list:
    """Notes still parked at the Tier-0 floor: ingest_status==tier0 (Tier-1 never completed).

    The entity itself is ``lifecycle: current`` from creation (ADR-50); ``ingest_status``
    is the tier discriminator, so the retry sweep keys on it alone.
    """
    out = []
    for folder in SOURCE_FOLDERS:
        d = vault / folder
        if not d.is_dir():
            continue
        for md in sorted(d.glob("*.md")):
            fm = read_frontmatter(md)
            if fm.get("ingest_status") == "tier0":
                out.append({"citekey": fm.get("citekey") or md.stem, "path": str(md)})
    return out


def enqueue_reingest(citekey: str, reason: str, dry_run: bool = False) -> str:
    """Enqueue ONE idempotent re-ingest card for a citekey. Returns the card id (or 'DRY')."""
    if dry_run:
        return "DRY"
    cmd = [
        "hermes", "kanban", "create", f"Re-ingest {citekey}",
        "--assignee", LIBRARIAN, "--skill", SKILL,
        "--idempotency-key", f"reingest:{citekey}",
        "--created-by", "sweeps", "--body", f"Re-ingest {citekey} ({reason}).",
        "--json",
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=True)
        obj = json.loads(r.stdout or "{}")
        return str(obj.get("id") or obj.get("task_id") or "queued")
    except subprocess.CalledProcessError as e:
        detail = (e.stderr or e.stdout or "").strip()[:200]
        print(f"[sweeps] enqueue failed for {citekey} (exit {e.returncode}): {detail}",
              file=sys.stderr)
        return f"error:CalledProcessError:exit{e.returncode}"
    except subprocess.TimeoutExpired:
        print(f"[sweeps] enqueue timed out for {citekey}", file=sys.stderr)
        return "error:TimeoutExpired"
    except FileNotFoundError:
        print("[sweeps] 'hermes' not found on PATH", file=sys.stderr)
        return "error:FileNotFoundError:hermes-not-found"


def reconcile(log_path: Path, vault: Path, dry_run: bool = False) -> dict:
    """(a) re-drive captures logged but with no note on disk."""
    records = read_log(log_path)
    orphans, enqueued = [], []
    for ck in records:
        if note_for(ck, vault) is None:
            orphans.append(ck)
            enqueued.append({"citekey": ck, "card": enqueue_reingest(ck, "stub-never-landed", dry_run)})
    return {"pass": "reconcile", "logged": len(records), "orphans": len(orphans),
            "enqueued": enqueued, "dry_run": dry_run}


def retry(vault: Path, dry_run: bool = False) -> dict:
    """(b) re-drive captured notes stuck at the Tier-0 floor (Tier-1 never completed)."""
    stuck = scan_captured(vault)
    enqueued = [{"citekey": n["citekey"], "card": enqueue_reingest(n["citekey"], "tier1-incomplete", dry_run)}
                for n in stuck]
    return {"pass": "retry", "stuck": len(stuck), "enqueued": enqueued, "dry_run": dry_run}


def _chat_frontmatter(md: Path) -> str:
    """Build the fleeting stamp for one exported chat file."""
    import datetime
    title = md.stem.replace("_", " ").strip() or md.stem
    created = datetime.date.fromtimestamp(md.stat().st_mtime).isoformat()
    safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
    return ("---\n"
            f'title: "{safe_title}"\n'
            "type: fleeting\n"
            "lifecycle: proposed\n"
            "origin: chat\n"
            f"created: {created}\n"
            "---\n")


def stamp_chats(vault: Path, dry_run: bool = False) -> dict:
    """(c) stamp bare ACP chat exports in notes/fleeting/chats/ with fleeting frontmatter.

    Idempotent: a file that already opens with a `---` frontmatter fence is left
    untouched, so a second sweep (or a hand-edited export) is a no-op.
    """
    folder = vault / CHATS_FOLDER
    stamped, skipped = [], 0
    if not folder.is_dir():
        return {"pass": "stamp", "stamped": [], "skipped": 0, "dry_run": dry_run}
    for md in sorted(folder.rglob("*.md")):
        text = md.read_text(encoding="utf-8", errors="ignore")
        if text.lstrip().startswith("---"):
            skipped += 1
            continue
        if not dry_run:
            md.write_text(_chat_frontmatter(md) + "\n" + text, encoding="utf-8")
        stamped.append(str(md.relative_to(vault)))
    return {"pass": "stamp", "stamped": stamped, "skipped": skipped, "dry_run": dry_run}


# --------------------------------------------------------------------------- #
def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(
        description="Ingest backstops: reconcile + retry sweeps (ADR-30) + chat-export stamp (#185)")
    ap.add_argument("--vault", help="vault root")
    ap.add_argument("--log", help="capture-intake.jsonl (default <vault>/system/logs/capture-intake.jsonl)")
    ap.add_argument("--reconcile", action="store_true", help="run pass (a) only")
    ap.add_argument("--retry", action="store_true", help="run pass (b) only")
    ap.add_argument("--stamp-chats", action="store_true", help="run pass (c) only")
    ap.add_argument("--dry-run", action="store_true", help="report without enqueuing/stamping")
    a = ap.parse_args()
    if not a.vault:
        ap.error("provide --vault")
    vault = Path(a.vault)
    log = Path(a.log) if a.log else vault / "system/logs/capture-intake.jsonl"
    do_all = not (a.reconcile or a.retry or a.stamp_chats)
    out = []
    if a.reconcile or do_all:
        out.append(reconcile(log, vault, a.dry_run))
    if a.retry or do_all:
        out.append(retry(vault, a.dry_run))
    if a.stamp_chats or do_all:
        out.append(stamp_chats(vault, a.dry_run))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
