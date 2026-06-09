#!/usr/bin/env python3
"""status-doctor — keep the docs/ release/test/contributing prose from rotting.

The project/ tree is prose plus pointers, and no other check covers its internal
links. (ADRs and design notes are guarded by docs-doctor's general link check;
this adds the released-flag consistency guard over the release/test/contributing prose.) Guards three drift modes:

  1. Stale path renames — `project/releases/` (now release/) and `tests/` (now test/).
     These bit before, leaving broken cross-links after a folder rename.
  2. Broken relative links — every `[text](rel/path)` must resolve on disk.
  3. released-flag inconsistency — frontmatter `status: released` <-> `released: true`
     (only fires on the release plans that carry both keys).

Scope: docs/{releasing,testing,contributing}/**/*.md + .claude/skills/release/SKILL.md.
Exit 0 if clean, 1 if any issue. Usage: python scripts/status-doctor.py [--self-test]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
MD_LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)]+)\)")
# A pre-reorg path segment used as a relative (`../`) or repo-rooted (`project/`)
# path. Maps old -> new for the message.
STALE = {"releases": "release", "tests": "test"}
STALE_RE = re.compile(r"(?:\.\./|project/)(" + "|".join(STALE) + r")/")


def targets(root: Path) -> list[Path]:
    # The release/test/contributing prose moved from project/ into docs/; docs-doctor
    # checks docs/ links generally, this adds the released-flag consistency guard.
    files: list[Path] = []
    for sub in ("releasing", "testing", "contributing"):
        files += sorted((root / "docs" / sub).rglob("*.md"))
    skill = root / ".claude" / "skills" / "release" / "SKILL.md"
    if skill.is_file():
        files.append(skill)
    return sorted(files)


def check_file(p: Path, root: Path) -> list[str]:
    """Return drift findings for one file."""
    errs: list[str] = []
    text = p.read_text(encoding="utf-8").replace("\r\n", "\n")
    rel = p.relative_to(root)

    # 1. stale path renames
    for m in STALE_RE.finditer(text):
        old = m.group(1)
        errs.append(f"{rel}: stale path `{m.group(0)}` — `{old}/` was renamed to `{STALE[old]}/`")

    # 2. broken relative links (skip external, anchors, and {{ }} placeholders)
    for raw in MD_LINK.findall(text):
        target = raw.strip()
        if (not target or target.startswith(("http://", "https://", "mailto:", "#"))
                or "{{" in target):
            continue
        path_part = target.split("#", 1)[0]
        if not path_part:
            continue
        if not (p.parent / path_part).resolve().exists():
            errs.append(f"{rel}: broken link -> {raw.strip()}")

    # 3. released-flag consistency
    m = FRONTMATTER_RE.match(text)
    if m:
        fm = m.group(1)
        status = _fm_value(fm, "status")
        released = _fm_value(fm, "released")
        if released is not None and status is not None:
            is_released = released.lower() == "true"
            if is_released != (status.lower() == "released"):
                errs.append(f"{rel}: frontmatter inconsistent — status:{status} vs released:{released}")
    return errs


def _fm_value(fm: str, key: str) -> str | None:
    m = re.search(rf"(?m)^{re.escape(key)}:\s*([^\n#]+)", fm)
    return m.group(1).strip() if m else None


def main() -> int:
    errors: list[str] = []
    files = targets(ROOT)
    for p in files:
        errors.extend(check_file(p, ROOT))
    if errors:
        print(f"status-doctor: {len(errors)} issue(s)\n")
        for e in errors:
            print(f"  ✗ {e}")
        return 1
    print(f"status-doctor: clean ✓ ({len(files)} project doc(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
