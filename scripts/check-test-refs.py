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
PROTOCOLS = sorted((ROOT / "project-files" / "tests").rglob("*.md"))

MD_LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)]+)\)")
REPO_PATH = re.compile(r"`((?:docs|project-files)/[A-Za-z0-9/_.-]+\.md)`")


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


def _self_test() -> int:
    """Synthetic-fixture unit tests for check_protocol and the regex patterns."""
    import tempfile

    failures = 0

    def check(name, ok):
        nonlocal failures
        if not ok:
            failures += 1
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")

    # --- MD_LINK regex ---
    check("MD_LINK: matches standard link",
          MD_LINK.findall("[text](target.md)") == ["target.md"])
    check("MD_LINK: ignores images",
          MD_LINK.findall("![alt](image.png)") == [])
    check("MD_LINK: matches with anchor",
          MD_LINK.findall("[t](file.md#heading)") == ["file.md#heading"])
    check("MD_LINK: matches multiple",
          len(MD_LINK.findall("[a](x.md) and [b](y.md)")) == 2)

    # --- REPO_PATH regex ---
    check("REPO_PATH: matches docs/ path",
          REPO_PATH.findall("`docs/reference/policy-mcp.md`") == ["docs/reference/policy-mcp.md"])
    check("REPO_PATH: matches project-files/ path",
          REPO_PATH.findall("`project-files/tests/coverage-matrix.md`") == ["project-files/tests/coverage-matrix.md"])
    check("REPO_PATH: ignores non-matching prefix",
          REPO_PATH.findall("`vault/something.md`") == [])
    check("REPO_PATH: ignores non-backtick text",
          REPO_PATH.findall("docs/reference/policy-mcp.md") == [])

    # --- check_protocol with synthetic files ---
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        proto_dir = root / "project-files" / "tests"
        proto_dir.mkdir(parents=True)
        (root / "docs" / "reference").mkdir(parents=True)
        (root / "docs" / "reference" / "policy-mcp.md").write_text("# Policy MCP\n")

        # valid protocol: relative link resolves, repo path resolves
        valid = proto_dir / "valid.md"
        valid.write_text(
            "See [policy](../../docs/reference/policy-mcp.md) and "
            "`docs/reference/policy-mcp.md` for details.\n"
            "[external](https://example.com) should be skipped.\n"
        )
        errs = check_protocol(valid, root)
        check("check_protocol: valid links produce no errors", len(errs) == 0)

        # broken relative link
        # Note: paths below are built at runtime to avoid triggering the
        # pre-commit repo-path grep on the .py source itself.
        _d = "docs"
        broken_link = proto_dir / "broken-link.md"
        broken_link.write_text(f"[missing](../../{_d}/nonexistent.md)\n")
        errs = check_protocol(broken_link, root)
        check("check_protocol: broken relative link detected", len(errs) == 1)
        check("check_protocol: error mentions broken link",
              "broken link" in errs[0])

        # stale repo path
        stale = proto_dir / "stale.md"
        stale.write_text(f"Refer to `{_d}/dissolved/old-page.md` here.\n")
        errs = check_protocol(stale, root)
        check("check_protocol: stale repo path detected", len(errs) == 1)
        check("check_protocol: error mentions stale repo path",
              "stale repo path" in errs[0])

        # multiple errors in one file
        multi = proto_dir / "multi.md"
        multi.write_text(
            "[bad](../../no-such.md)\n"
            f"`{_d}/fake/path.md` and `project-files/fake.md`\n"
        )
        errs = check_protocol(multi, root)
        check("check_protocol: multiple errors all caught", len(errs) == 3)

    print(f"\n{'OK' if not failures else f'{failures} FAILING'}: check-test-refs self-test")
    return 1 if failures else 0


def main() -> int:
    if "--self-test" in sys.argv:
        return _self_test()

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
