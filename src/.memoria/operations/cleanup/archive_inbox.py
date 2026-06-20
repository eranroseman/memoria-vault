#!/usr/bin/env python3
"""archive_inbox.py — the inbox archival sweep (#338).

The resolve affordance (QuickAdd "Memoria: resolve inbox card",
src/system/scripts/resolve-inbox-card.js) flips a card's frontmatter
``lifecycle:`` to a schema-valid inbox outcome and stamps ``resolved:``. Accepted
cards stay in ``inbox/`` as ``current`` so the verdict remains visible while it is
fresh; rejected/no-action cards go straight to ``archived``. This sweep is the
second half of the drain: a card whose lifecycle is a *resolved-but-not-archived*
value (``current``) AND whose ``resolved:`` stamp is
older than N days flips to ``lifecycle: archived``, leaving every active view
(``transient_prefixes`` — items converge to ``archived``). The inbox therefore
demonstrably converges to empty once cards are handled.

Mechanics mirror the resolve script: a **frontmatter flip in place** — the card
schema defines ``archived`` as a lifecycle value, not a file move, so the file
never moves and every other frontmatter field and body byte is preserved (the
sweep rewrites only the single ``lifecycle:`` line).

Like other cleanup sweeps, this writes the vault DIRECTLY —
exempt from the board-serialization rule (ADR-30) because it is a
deterministic, idempotent, single-line rewrite with no find-or-create
semantics: an already-``archived`` card is skipped, so a re-run is a no-op.

Guardrails:
  * a card with no ``resolved:`` stamp is NEVER touched (unresolved, or
    resolved by hand without a stamp — either way, not the sweep's call);
  * ``proposed`` cards (awaiting the PI) are never touched;
  * malformed frontmatter (unclosed fence, YAML error, missing/odd
    ``lifecycle:`` line) → skip + one stderr warning, never a write.

N comes from ``.memoria/schemas/calibration.yaml`` (``inbox.archive_after_days``,
default 30 when absent), the same warn-once read pattern as classify.py's
thresholds(). ``--dry-run`` reports what would flip without touching anything.

    python archive_inbox.py --vault V             # archive eligible cards
    python archive_inbox.py --vault V --dry-run   # report only
"""

from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path

INBOX_FOLDER = "inbox"
# lifecycle values written by the resolve affordance that still await archival.
RESOLVED_LIFECYCLES = ("current",)
DEFAULT_ARCHIVE_AFTER_DAYS = 30

_warned_calibration = False  # one stderr warning per process (classify.py pattern)


def archive_after_days(vault: Path | None) -> int:
    """``inbox.archive_after_days`` from calibration.yaml, with a default.

    A parse/read failure (or an absent key) degrades to the default — but
    loudly (one stderr warning per process), so a miscalibrated vault is
    visible, not silent."""
    global _warned_calibration
    try:
        import yaml

        f = Path(vault) / ".memoria" / "schemas" / "calibration.yaml"
        return int(yaml.safe_load(f.read_text(encoding="utf-8"))["inbox"]["archive_after_days"])
    except Exception as exc:  # noqa: BLE001
        if not _warned_calibration:
            _warned_calibration = True
            print(
                f"[archive-inbox] WARNING: cannot read inbox.archive_after_days from "
                f"calibration.yaml ({type(exc).__name__}: {exc}) — using default "
                f"{DEFAULT_ARCHIVE_AFTER_DAYS} days",
                file=sys.stderr,
            )
        return DEFAULT_ARCHIVE_AFTER_DAYS


def _resolved_date(value) -> datetime.date | None:
    """Coerce a frontmatter ``resolved:`` value to a date (YAML may give either)."""
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        try:
            return datetime.date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def _flip_lifecycle(md: Path, text: str, fence_end: int, dry_run: bool) -> bool:
    """Rewrite ONLY the ``lifecycle:`` line inside the frontmatter block.

    Returns False (caller warns) if the line isn't found in the expected
    top-level form — never re-dumps YAML, so all other bytes are preserved."""
    head, body = text[:fence_end], text[fence_end:]
    new_head, n = re.subn(r"(?m)^lifecycle:[^\n]*$", "lifecycle: archived", head, count=1)
    if n != 1:
        return False
    if not dry_run:
        md.write_text(new_head + body, encoding="utf-8")
    return True


def sweep(vault: Path, days: int, dry_run: bool = False) -> dict:
    """Archive resolved inbox cards older than ``days``. Idempotent."""
    folder = vault / INBOX_FOLDER
    cutoff = datetime.date.today() - datetime.timedelta(days=days)
    archived: list[str] = []
    skipped_fresh = skipped_unresolved = skipped_malformed = skipped_done = 0
    if not folder.is_dir():
        return {
            "pass": "archive-inbox",
            "days": days,
            "archived": [],
            "skipped": 0,
            "dry_run": dry_run,
        }
    try:
        import yaml
    except ImportError:
        print("[archive-inbox] PyYAML not installed; sweep skipped", file=sys.stderr)
        return {
            "pass": "archive-inbox",
            "days": days,
            "archived": [],
            "skipped": 0,
            "dry_run": dry_run,
            "error": "no-yaml",
        }
    for md in sorted(folder.rglob("*.md")):
        rel = str(md.relative_to(vault))
        text = md.read_text(encoding="utf-8", errors="ignore")
        if not text.startswith("---"):
            skipped_malformed += 1
            print(f"[archive-inbox] skip {rel}: no frontmatter fence", file=sys.stderr)
            continue
        end = text.find("\n---", 3)
        if end == -1:
            skipped_malformed += 1
            print(f"[archive-inbox] skip {rel}: unclosed frontmatter fence", file=sys.stderr)
            continue
        try:
            fm = yaml.safe_load(text[3:end])
        except yaml.YAMLError as exc:
            skipped_malformed += 1
            print(f"[archive-inbox] skip {rel}: YAML parse error ({exc})", file=sys.stderr)
            continue
        if not isinstance(fm, dict):
            skipped_malformed += 1
            print(f"[archive-inbox] skip {rel}: frontmatter is not a mapping", file=sys.stderr)
            continue
        lifecycle = fm.get("lifecycle")
        if lifecycle == "archived":
            skipped_done += 1  # idempotence: already converged
            continue
        if lifecycle not in RESOLVED_LIFECYCLES:
            skipped_unresolved += 1  # proposed / unknown — awaiting the PI, not ours
            continue
        resolved = _resolved_date(fm.get("resolved"))
        if resolved is None:
            skipped_unresolved += 1  # no usable resolved: stamp — never touch
            continue
        if resolved > cutoff:
            skipped_fresh += 1  # verdict still fresh — keep it visible
            continue
        if not _flip_lifecycle(md, text, end, dry_run):
            skipped_malformed += 1
            print(
                f"[archive-inbox] skip {rel}: no top-level lifecycle: line to flip", file=sys.stderr
            )
            continue
        archived.append(rel)
    return {
        "pass": "archive-inbox",
        "days": days,
        "archived": archived,
        "skipped_fresh": skipped_fresh,
        "skipped_unresolved": skipped_unresolved,
        "skipped_already_archived": skipped_done,
        "skipped_malformed": skipped_malformed,
        "dry_run": dry_run,
    }


# --------------------------------------------------------------------------- #
def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(
        description="Inbox archival sweep (#338): flip resolved cards older than "
        "N days to lifecycle: archived"
    )
    ap.add_argument("--vault", help="vault root")
    ap.add_argument(
        "--days", type=int, help="override inbox.archive_after_days from calibration.yaml"
    )
    ap.add_argument("--dry-run", action="store_true", help="report without writing")
    a = ap.parse_args()
    if not a.vault:
        ap.error("provide --vault")
    vault = Path(a.vault)
    days = a.days if a.days is not None else archive_after_days(vault)
    print(json.dumps(sweep(vault, days, a.dry_run), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
