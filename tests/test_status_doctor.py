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
            good.write_text("---\nstatus: complete\nreleased: false\n---\n[x](adr/x.md) {{ #NN }} placeholder ok\n")
            check("clean file -> no findings", check_file(good, root) == [])

            released_ok = rel / "released.md"
            released_ok.write_text("---\nstatus: released\nreleased: true\n---\n# x\n")
            check("released true + status released -> no findings", check_file(released_ok, root) == [])

            candidate_ok = rel / "candidate.md"
            candidate_ok.write_text("---\nstatus: candidate\nreleased: false\n---\n# x\n")
            check("candidate false -> no findings", check_file(candidate_ok, root) == [])

            draft_no_flag = rel / "draft-no-flag.md"
            draft_no_flag.write_text("---\nstatus: draft\n---\n# x\n")
            check("status without released flag -> no findings", check_file(draft_no_flag, root) == [])

            stale = rel / "stale.md"
            stale.write_text(
                "see [r](../tests/g9.md), `project/releases/v0.1/p.md`, "
                "`release/vX.Y/p.md`, `releasing/vX.Y/p.md`, and `docs/releasing/vX.Y/p.md`\n")
            errs = check_file(stale, root)
            check("stale ../tests/ flagged", any("tests" in e and "stale path" in e for e in errs))
            check("stale project/releases/ flagged", any("releases" in e and "stale path" in e for e in errs))
            check("stale release/vX.Y/ flagged", any("release/vX.Y/" in e and "stale path" in e for e in errs))
            check("stale releasing/vX.Y/ flagged", any("releasing/vX.Y/" in e and "stale path" in e for e in errs))
            check("stale docs/releasing/vX.Y/ flagged", any("docs/releasing/vX.Y/" in e and "stale path" in e for e in errs))

            broken = rel / "broken.md"
            broken.write_text("[gone](nope/missing.md)\n")
            check("broken link flagged", any("broken link" in e for e in check_file(broken, root)))

            ignored_links = rel / "ignored-links.md"
            ignored_links.write_text(
                "[web](https://example.com) [mail](mailto:a@example.com) [anchor](#x) "
                "[placeholder]({{ #NN }}) [ellipsis](...) [unicode](…)\n")
            check("external/placeholders/ellipsis links ignored", check_file(ignored_links, root) == [])

            bad_fm = rel / "bad.md"
            bad_fm.write_text("---\nstatus: released\nreleased: false\n---\n# x\n")
            check("released-flag inconsistency flagged",
                  any("inconsistent" in e for e in check_file(bad_fm, root)))

            bad_status = rel / "bad-status.md"
            bad_status.write_text("---\nstatus: done\nreleased: false\n---\n# x\n")
            check("invalid release status flagged",
                  any("invalid release status" in e for e in check_file(bad_status, root)))

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

            release_tmp = root / "docs" / "releasing" / "0.1.0-alpha.3" / "tmp"
            release_tmp.mkdir(parents=True)
            scratch = release_tmp / "note.md"
            scratch.write_text("[private](../../../../../.claude/projects/x/memory/rule.md)\n")
            check("release tmp files are in scope", scratch in targets(root))
            check("private scratch memory link flagged",
                  any("local/private memory" in e for e in check_file(scratch, root)))

            other_tmp = root / "docs" / "testing" / "tmp" / "note.md"
            other_tmp.parent.mkdir(parents=True)
            other_tmp.write_text("# scratch\n")
            check("tmp outside release folder flagged",
                  any("tmp/ is allowed only" in e for e in check_file(other_tmp, root)))

            check("release tmp helper accepts canonical release scratch",
                  _release_tmp(Path("docs/releasing/0.1.0-alpha.3/tmp/note.md")))
            check("release tmp helper rejects non-release scratch",
                  not _release_tmp(Path("docs/testing/tmp/note.md")))

            # scope: the portable release playbook is canonical.
            playbook = root / ".agents" / "playbooks" / "release.md"
            playbook.parent.mkdir(parents=True)
            playbook.write_text("# Release\n")
            check("targets() includes portable release playbook", playbook in targets(root))

            old_root = _m.ROOT
            try:
                _m.ROOT = root
                check("main returns nonzero on findings", _m.main() == 1)
                bad_status.write_text("---\nstatus: draft\nreleased: false\n---\n# x\n")
                bad_fm.write_text("---\nstatus: draft\nreleased: false\n---\n# x\n")
                broken.write_text("[ok](adr/x.md)\n")
                stale.write_text("release prose, no stale path\n")
                tp.write_text("test plan, no broken links\n")
                (root / "docs" / "adr").mkdir(parents=True)
                (root / "docs" / "adr" / "72-command-surfacing.md").write_text("# ADR 72\n")
                scratch.write_text("[repo](../../../adr/72-command-surfacing.md)\n")
                other_tmp.unlink()
                check("main returns zero when clean", _m.main() == 0)
            finally:
                _m.ROOT = old_root

        print(f"\n{'OK' if not failures else f'{failures} FAILING'}: status-doctor self-test")
        return 1 if failures else 0
    assert _run() == 0
