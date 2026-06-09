"""L1 component test for status-doctor — extracted from its former --self-test (ADR-44)."""
from _util import load_script
_m = load_script("scripts/status-doctor.py")
globals().update({k: getattr(_m, k) for k in dir(_m) if not k.startswith("__")})


def test_status_doctor():
    def _run():
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
            stale.write_text("see [r](../tests/g9.md) and `project/releases/v0.1/p.md`\n")
            errs = check_file(stale, root)
            check("stale ../tests/ flagged", any("tests" in e and "stale path" in e for e in errs))
            check("stale project/releases/ flagged", any("releases" in e and "stale path" in e for e in errs))

            broken = rel / "broken.md"
            broken.write_text("[gone](nope/missing.md)\n")
            check("broken link flagged", any("broken link" in e for e in check_file(broken, root)))

            bad_fm = rel / "bad.md"
            bad_fm.write_text("---\nstatus: released\nreleased: false\n---\n# x\n")
            check("released-flag inconsistency flagged",
                  any("inconsistent" in e for e in check_file(bad_fm, root)))

            # prose mentioning "releases" without a path must NOT trip the stale check
            prose = rel / "prose.md"
            prose.write_text("This records releases and test plans.\n")
            check("prose 'releases' (no path) -> not flagged",
                  not any("stale path" in e for e in check_file(prose, root)))

            # scope: targets() covers the moved docs/ subtrees (releasing/testing/contributing)
            (root / "docs" / "testing").mkdir(parents=True)
            tp = root / "docs" / "testing" / "g9.md"
            tp.write_text("see [r](missing/x.md)\n")
            check("targets() includes docs/testing files", tp in targets(root))
            check("broken link in a test plan flagged", any("broken link" in e for e in check_file(tp, root)))

        print(f"\n{'OK' if not failures else f'{failures} FAILING'}: status-doctor self-test")
        return 1 if failures else 0
    assert _run() == 0
