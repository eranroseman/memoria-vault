#!/usr/bin/env python3
"""status-doctor — keep the project/ docs (ADRs, RFCs, release plans) from rotting.

The project/ tree is prose plus pointers, and no other check covers its internal
links — so a folder rename (the proposals/->rfc/, decisions/->adr/ reorg) silently
left 59 broken cross-links across the ADR/RFC corpus before this widened to catch
them. Guards the three ways those files drift:

  1. Stale path renames — `project/releases/` (now release/), `../decisions/`
     (now adr/), `proposals/` (now rfc/), `tests/` (now test/). These bit before.
     Skipped under project/rfc/explorations/, where such paths are *documented*
     as drift findings rather than used as live links.
  2. Broken relative links — every `[text](rel/path)` must resolve on disk.
  3. released-flag inconsistency — frontmatter `status: released` <-> `released: true`
     (only fires on the release plans that carry both keys).

Scope: project/**/*.md + .claude/skills/release/SKILL.md.
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
STALE = {"releases": "release", "decisions": "adr", "proposals": "rfc", "tests": "test"}
STALE_RE = re.compile(r"(?:\.\./|project/)(" + "|".join(STALE) + r")/")


def targets(root: Path) -> list[Path]:
    files = sorted((root / "project").rglob("*.md"))
    skill = root / ".claude" / "skills" / "release" / "SKILL.md"
    if skill.is_file():
        files.append(skill)
    return files


def check_file(p: Path, root: Path) -> list[str]:
    """Return drift findings for one file."""
    errs: list[str] = []
    text = p.read_text(encoding="utf-8").replace("\r\n", "\n")
    rel = p.relative_to(root)

    # 1. stale path renames (skip explorations/, which documents drift as findings)
    if "rfc/explorations/" not in rel.as_posix():
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
    if "--self-test" in sys.argv:
        return _self_test()
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


def _self_test() -> int:
    import tempfile

    failures = 0

    def check(name: str, cond: bool) -> None:
        nonlocal failures
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        failures += 0 if cond else 1

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        rel = root / "project" / "release"
        (rel / "adr").mkdir(parents=True)        # real target for a good link
        (rel / "adr" / "x.md").write_text("# x\n")

        good = rel / "good.md"
        good.write_text("---\nstatus: draft\nreleased: false\n---\n[x](adr/x.md) {{ #NN }} placeholder ok\n")
        check("clean file -> no findings", check_file(good, root) == [])

        stale = rel / "stale.md"
        stale.write_text("see [r](../decisions/27.md) and `project/releases/v0.1/p.md`\n")
        errs = check_file(stale, root)
        check("stale ../decisions/ flagged", any("decisions" in e and "stale path" in e for e in errs))
        check("stale project/releases/ flagged", any("releases" in e and "stale path" in e for e in errs))

        broken = rel / "broken.md"
        broken.write_text("[gone](nope/missing.md)\n")
        check("broken link flagged", any("broken link" in e for e in check_file(broken, root)))

        bad_fm = rel / "bad.md"
        bad_fm.write_text("---\nstatus: released\nreleased: false\n---\n# x\n")
        check("released-flag inconsistency flagged",
              any("inconsistent" in e for e in check_file(bad_fm, root)))

        # prose mentioning "decisions" without a path must NOT trip the stale check
        prose = rel / "prose.md"
        prose.write_text("This records architectural decisions and proposals.\n")
        check("prose 'decisions'/'proposals' (no path) -> not flagged",
              not any("stale path" in e for e in check_file(prose, root)))

        # broadened scope: targets() covers the whole project/ tree, not just release/
        (root / "project" / "adr").mkdir(parents=True)
        adr = root / "project" / "adr" / "07.md"
        adr.write_text("see [r](../proposals/x.md)\n")
        check("targets() includes non-release project/ files", adr in targets(root))
        check("broken link in an ADR flagged", any("broken link" in e for e in check_file(adr, root)))

        # explorations/ documents drift -> stale-path heuristic skipped, broken links still caught
        expl = root / "project" / "rfc" / "explorations"
        expl.mkdir(parents=True)
        ex = expl / "notes.md"
        ex.write_text("the old `project/releases/` (now release/) and [d](../../decisions/9.md)\n")
        ex_errs = check_file(ex, root)
        check("explorations stale-path string NOT flagged", not any("stale path" in e for e in ex_errs))
        check("explorations broken link STILL flagged", any("broken link" in e for e in ex_errs))

    print(f"\n{'OK' if not failures else f'{failures} FAILING'}: status-doctor self-test")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
