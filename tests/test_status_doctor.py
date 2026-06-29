"""L1 component tests for status_doctor (ADR-44)."""

import status_doctor as _m

Path = _m.Path
_release_tmp = _m._release_tmp
check_file = _m.check_file
targets = _m.targets


def _release_root(tmp_path):
    rel = tmp_path / "project" / "release"
    (rel / "adr").mkdir(parents=True)
    (rel / "adr" / "x.md").write_text("# x\n")
    return rel


def test_check_file_accepts_consistent_release_frontmatter_and_valid_links(tmp_path):
    rel = _release_root(tmp_path)
    good = rel / "good.md"
    good.write_text(
        "---\nstatus: complete\nreleased: false\n---\n[x](adr/x.md) {{ #NN }} placeholder ok\n"
    )
    released_ok = rel / "released.md"
    released_ok.write_text("---\nstatus: released\nreleased: true\n---\n# x\n")
    candidate_ok = rel / "candidate.md"
    candidate_ok.write_text("---\nstatus: candidate\nreleased: false\n---\n# x\n")
    draft_no_flag = rel / "draft-no-flag.md"
    draft_no_flag.write_text("---\nstatus: draft\n---\n# x\n")

    assert check_file(good, tmp_path) == []
    assert check_file(released_ok, tmp_path) == []
    assert check_file(candidate_ok, tmp_path) == []
    assert check_file(draft_no_flag, tmp_path) == []


def test_check_file_flags_stale_release_and_test_paths(tmp_path):
    rel = _release_root(tmp_path)
    stale = rel / "stale.md"
    stale.write_text(
        "see [r](../tests/g9.md), `project/releases/0.1.0/p.md`, "
        "`release/0.1.0/p.md`, and `releasing/0.1.0/p.md`\n"
    )

    errs = check_file(stale, tmp_path)

    assert any("tests" in e and "stale path" in e for e in errs)
    assert any("releases" in e and "stale path" in e for e in errs)
    assert any("release/0.1.0/" in e and "stale path" in e for e in errs)
    assert any("releasing/0.1.0/" in e and "stale path" in e for e in errs)


def test_check_file_flags_deleted_testing_plan_names(tmp_path):
    rel = _release_root(tmp_path)
    stale = rel / "stale-testing.md"
    stale.write_text("Follow docs/testing/coverage-matrix.md and gui-test-plan.md.\n")

    errs = check_file(stale, tmp_path)

    assert any("coverage-matrix.md" in e and "verification-matrix.md" in e for e in errs)
    assert any("gui-test-plan.md" in e and "manual-gui-checks.md" in e for e in errs)


def test_check_file_flags_broken_links_but_ignores_external_placeholders_and_ellipsis(tmp_path):
    rel = _release_root(tmp_path)
    broken = rel / "broken.md"
    broken.write_text("[gone](nope/missing.md)\n")
    ignored_links = rel / "ignored-links.md"
    ignored_links.write_text(
        "[web](https://example.com) [mail](mailto:a@example.com) [anchor](#x) "
        "[placeholder]({{ #NN }}) [ellipsis](...) [unicode](…)\n"
    )

    assert any("broken link" in e for e in check_file(broken, tmp_path))
    assert check_file(ignored_links, tmp_path) == []


def test_check_file_flags_release_status_frontmatter_inconsistencies(tmp_path):
    rel = _release_root(tmp_path)
    bad_fm = rel / "bad.md"
    bad_fm.write_text("---\nstatus: released\nreleased: false\n---\n# x\n")
    bad_status = rel / "bad-status.md"
    bad_status.write_text("---\nstatus: done\nreleased: false\n---\n# x\n")
    prose = rel / "prose.md"
    prose.write_text("This records releases and test plans.\n")

    assert any("inconsistent" in e for e in check_file(bad_fm, tmp_path))
    assert any("invalid release status" in e for e in check_file(bad_status, tmp_path))
    assert not any("stale path" in e for e in check_file(prose, tmp_path))


def test_targets_include_docs_testing_release_tmp_and_release_playbook(tmp_path):
    contributing = tmp_path / "CONTRIBUTING.md"
    contributing.write_text("[adr](docs/adr)\n")
    (tmp_path / "docs" / "testing").mkdir(parents=True)
    (tmp_path / "docs" / "adr").mkdir(parents=True)
    testing = tmp_path / "docs" / "testing" / "g9.md"
    testing.write_text("see [r](missing/x.md)\n")
    release_tmp = tmp_path / "docs" / "releasing" / "0.1.0-alpha.3" / "tmp"
    release_tmp.mkdir(parents=True)
    scratch = release_tmp / "note.md"
    scratch.write_text("[private](../../../../../.claude/projects/x/memory/rule.md)\n")
    playbook = tmp_path / ".agents" / "playbooks" / "release.md"
    playbook.parent.mkdir(parents=True)
    playbook.write_text("# Release\n")

    found = targets(tmp_path)

    assert contributing in found
    assert testing in found
    assert scratch in found
    assert playbook in found
    assert any("broken link" in e for e in check_file(testing, tmp_path))
    assert any("local/private memory" in e for e in check_file(scratch, tmp_path))


def test_release_tmp_helper_and_tmp_scope_guard(tmp_path):
    other_tmp = tmp_path / "docs" / "testing" / "tmp" / "note.md"
    other_tmp.parent.mkdir(parents=True)
    other_tmp.write_text("# scratch\n")

    assert _release_tmp(Path("docs/releasing/0.1.0-alpha.3/tmp/note.md"))
    assert not _release_tmp(Path("docs/testing/tmp/note.md"))
    assert any("tmp/ is allowed only" in e for e in check_file(other_tmp, tmp_path))


def test_main_returns_nonzero_with_findings_and_zero_when_clean(tmp_path):
    rel = _release_root(tmp_path)
    bad_status = rel / "bad-status.md"
    bad_status.write_text("---\nstatus: done\nreleased: false\n---\n# x\n")
    broken = rel / "broken.md"
    broken.write_text("[gone](nope/missing.md)\n")
    stale = rel / "stale.md"
    stale.write_text("see `release/0.1.0/p.md`\n")
    testing = tmp_path / "docs" / "testing" / "g9.md"
    testing.parent.mkdir(parents=True)
    testing.write_text("see [r](missing/x.md)\n")
    scratch = tmp_path / "docs" / "releasing" / "0.1.0-alpha.3" / "tmp" / "note.md"
    scratch.parent.mkdir(parents=True)
    scratch.write_text("[private](../../../../../.claude/projects/x/memory/rule.md)\n")
    other_tmp = tmp_path / "docs" / "testing" / "tmp" / "note.md"
    other_tmp.parent.mkdir(parents=True)
    other_tmp.write_text("# scratch\n")

    old_root = _m.ROOT
    try:
        _m.ROOT = tmp_path
        assert _m.main() == 1
        bad_status.write_text("---\nstatus: draft\nreleased: false\n---\n# x\n")
        broken.write_text("[ok](adr/x.md)\n")
        stale.write_text("release prose, no stale path\n")
        testing.write_text("test plan, no broken links\n")
        (tmp_path / "docs" / "adr").mkdir(parents=True)
        (tmp_path / "docs" / "adr" / "72-command-surfacing.md").write_text("# ADR 72\n")
        scratch.write_text("[repo](../../../adr/72-command-surfacing.md)\n")
        other_tmp.unlink()
        assert _m.main() == 0
    finally:
        _m.ROOT = old_root
