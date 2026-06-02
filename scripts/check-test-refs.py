#!/usr/bin/env python3
"""check-test-refs — every path a test protocol references must resolve.

Test protocols rot when the design moves under them (a renamed or dissolved path
they still cite — e.g. `00-meta/04-reference/` after it was dissolved). This checks
the resolvable classes — relative Markdown links and bare `docs/…`/`project-files/…`
repo-path mentions — across every protocol in project-files/tests/ (and the GUI
protocol wherever it lives), so the rot fails CI instead of misleading a tester.

Exit 0 if clean, 1 if any reference is broken.
Usage: python scripts/check-test-refs.py
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROTOCOLS = sorted((ROOT / "project-files" / "tests").glob("*.md"))
# Also validate any versioned working copy of the GUI protocol kept under plans/
# (e.g. gui-test-protocol_v0.1.md). The reusable template lives in tests/ and is
# already covered by the glob above; run records live in plans/ as _v0.x.
for extra in sorted((ROOT / "project-files" / "plans").glob("gui-test-protocol*.md")):
    if extra not in PROTOCOLS:
        PROTOCOLS.append(extra)

MD_LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)]+)\)")
REPO_PATH = re.compile(r"`((?:docs|project-files)/[A-Za-z0-9/_.-]+\.md)`")


def main() -> int:
    errors: list[str] = []
    for p in PROTOCOLS:
        text = p.read_text(encoding="utf-8")
        for raw in MD_LINK.findall(text):
            target = raw.strip().split()[0].split("#")[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if not (p.parent / target).resolve().exists():
                errors.append(f"{p.relative_to(ROOT)}: broken link -> {raw.strip()}")
        for rel in REPO_PATH.findall(text):
            if not (ROOT / rel).exists():
                errors.append(f"{p.relative_to(ROOT)}: stale repo path -> `{rel}`")

    if errors:
        print(f"check-test-refs: {len(errors)} broken reference(s)\n")
        for e in errors:
            print(f"  ✗ {e}")
        return 1
    print(f"check-test-refs: clean ✓ ({len(PROTOCOLS)} protocol(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
