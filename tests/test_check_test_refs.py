"""L1 component test for check-test-refs — extracted from its former --self-test (ADR-44)."""
from _util import load_script

_m = load_script("scripts/check-test-refs.py")
MD_LINK = _m.MD_LINK
Path = _m.Path
REPO_PATH = _m.REPO_PATH
check_protocol = _m.check_protocol


def test_check_test_refs():
    def _run():
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
              REPO_PATH.findall("`src/something.md`") == [])
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
    assert _run() == 0
