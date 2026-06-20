#!/usr/bin/env python3
"""check-test-refs — every path a test plan references must resolve.

Test plans rot when the design moves under them (a renamed or dissolved path
they still cite — e.g. `00-meta/04-reference/` after it was dissolved). This checks
the resolvable classes — relative Markdown links and bare `docs/…`/`project/…`
repo-path mentions — across every plan in docs/testing/, so the rot fails CI
instead of misleading a tester. A lingering `project-files/…` mention (the
pre-reorg path) is also caught: it matches the pattern but no longer resolves.

Exit 0 if clean, 1 if any reference is broken.
Usage: python scripts/check_test_refs.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROTOCOLS = sorted((ROOT / "docs" / "testing").rglob("*.md"))

MD_LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)]+)\)")
REPO_PATH = re.compile(r"`((?:docs|project|project-files)/[A-Za-z0-9/_.-]+\.md)`")


def check_protocol(p: Path, root: Path) -> list[str]:
    """Check a single protocol file for broken references. Returns error strings."""
    errors: list[str] = []
    text = p.read_text(encoding="utf-8")
    for raw in MD_LINK.findall(text):
        target = raw.strip().split()[0].split("#")[0]
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        if not (p.parent / target).resolve().exists():
            errors.append(f"{p.relative_to(root)}: broken link -> {raw.strip()}")
    for rel in REPO_PATH.findall(text):
        if not (root / rel).exists():
            errors.append(f"{p.relative_to(root)}: stale repo path -> `{rel}`")
    return errors


def main() -> int:
    errors: list[str] = []
    for p in PROTOCOLS:
        errors.extend(check_protocol(p, ROOT))

    if errors:
        print(f"check-test-refs: {len(errors)} broken reference(s)\n")
        for e in errors:
            print(f"  ✗ {e}")
        return 1
    print(f"check-test-refs: clean ✓ ({len(PROTOCOLS)} protocol(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
