#!/usr/bin/env python3
"""status-doctor — keep release/test/contributing docs from rotting.

The project/ tree is prose plus pointers, and no other check covers its internal
links. (ADRs are guarded by docs-doctor's general link check; this adds release
state/path and tracked-scratch portability guards over release/test/contributing
prose.) Guards six drift modes:

  1. Stale path renames — old `project/releases/`/`project/tests/` paths and
     wrong `release/vX.Y/`/`releasing/vX.Y/` examples.
     These bit before, leaving broken cross-links after a folder rename.
  2. Broken relative links — every `[text](rel/path)` must resolve on disk.
  3. release-plan frontmatter — allowed statuses + `status: released` <-> `released: true`
     (only fires on the release plans that carry both keys).
  4. Tracked release-design scratch (`docs/releasing/<version>/tmp/`) must not link
     to local/private memory outside the repo. It is tracked so branches can cite it,
     but deleted before the release is done.
  5. Scratch `tmp/` dirs may exist only under `docs/releasing/<version>/tmp/`.
  6. Release agent guidance lives in the portable `.agents` playbook.

Scope: docs/{releasing,testing,contributing}/**/*.md + .agents/playbooks/release.md.
Exit 0 if clean, 1 if any issue. Usage: python scripts/status-doctor.py [--self-test]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
MD_LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)]+)\)")
ALLOWED_RELEASE_STATUSES = {"draft", "candidate", "complete", "released"}

# Pre-reorg path segments and release-folder examples that no longer match the
# repo. Canonical release prose lives in docs/releasing/<version>/.
STALE_PATHS = [
    (re.compile(r"(?:\.\./|project/)(releases)/"), "docs/releasing/"),
    (re.compile(r"(?:\.\./|project/)(tests)/"), "docs/testing/"),
    (re.compile(r"\brelease/vX\.Y/"), "docs/releasing/<version>/"),
    (re.compile(r"\breleasing/vX\.Y/"), "docs/releasing/<version>/"),
    (re.compile(r"\bdocs/releasing/vX\.Y/"), "docs/releasing/<version>/"),
]

PRIVATE_SCRATCH_LINK_RE = re.compile(r"(?:^|[/(])\.claude/projects/|/memory/")
RELEASE_PLAYBOOK = Path(".agents/playbooks/release.md")


def targets(root: Path) -> list[Path]:
    # The release/test/contributing prose moved from project/ into docs/; docs-doctor
    # checks docs/ links generally, this adds the released-flag consistency guard.
    files: list[Path] = []
    for sub in ("releasing", "testing", "contributing"):
        files += sorted((root / "docs" / sub).rglob("*.md"))
    playbook = root / RELEASE_PLAYBOOK
    if playbook.is_file():
        files.append(playbook)
    return sorted(files)


def check_file(p: Path, root: Path) -> list[str]:
    """Return drift findings for one file."""
    errs: list[str] = []
    text = p.read_text(encoding="utf-8").replace("\r\n", "\n")
    rel = p.relative_to(root)

    # 1. stale path renames / wrong canonical examples
    for rx, replacement in STALE_PATHS:
        for m in rx.finditer(text):
            errs.append(f"{rel}: stale path `{m.group(0)}` — use `{replacement}`")

    # 1b. scratch dirs are allowed only for in-work release design notes.
    if "tmp" in rel.parts and not _release_tmp(rel):
        errs.append(f"{rel}: tmp/ is allowed only under docs/releasing/<version>/tmp/")

    # 1c. tracked release-design scratch must stay portable for collaborators.
    if _release_tmp(rel) and PRIVATE_SCRATCH_LINK_RE.search(text):
        errs.append(f"{rel}: tracked tmp/ note links to local/private memory outside the repo")

    # 2. broken relative links (skip external, anchors, and {{ }} placeholders)
    for raw in MD_LINK.findall(text):
        target = raw.strip()
        if (not target or target.startswith(("http://", "https://", "mailto:", "#"))
                or "{{" in target or target in {"...", "…"}):
            continue
        path_part = target.split("#", 1)[0]
        if not path_part:
            continue
        if not (p.parent / path_part).resolve().exists():
            errs.append(f"{rel}: broken link -> {raw.strip()}")

    # 3. release-plan status vocabulary + released-flag consistency
    m = FRONTMATTER_RE.match(text)
    if m:
        fm = m.group(1)
        status = _fm_value(fm, "status")
        released = _fm_value(fm, "released")
        if released is not None and status is not None:
            status_l = status.lower()
            if status_l not in ALLOWED_RELEASE_STATUSES:
                allowed = ", ".join(sorted(ALLOWED_RELEASE_STATUSES))
                errs.append(f"{rel}: invalid release status `{status}` — expected one of: {allowed}")
            is_released = released.lower() == "true"
            if is_released != (status_l == "released"):
                errs.append(f"{rel}: frontmatter inconsistent — status:{status} vs released:{released}")
    return errs


def _fm_value(fm: str, key: str) -> str | None:
    m = re.search(rf"(?m)^{re.escape(key)}:\s*([^\n#]+)", fm)
    return m.group(1).strip() if m else None


def _release_tmp(rel: Path) -> bool:
    parts = rel.parts
    return len(parts) >= 5 and parts[0] == "docs" and parts[1] == "releasing" and parts[3] == "tmp"


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
