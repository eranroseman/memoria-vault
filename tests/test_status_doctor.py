"""L1 component tests for status_doctor (ADR-44)."""

import status_doctor as _m

Path = _m.Path
_release_scratch = _m._release_scratch
check_file = _m.check_file
targets = _m.targets


def _routing_root(tmp_path):
    (tmp_path / ".agents" / "playbooks").mkdir(parents=True)
    (tmp_path / ".agents" / "templates").mkdir(parents=True)
    (tmp_path / "docs" / "adr").mkdir(parents=True)
    (tmp_path / "docs" / "adr" / "x.md").write_text("# x\n")
    return tmp_path


def test_check_file_accepts_valid_links_and_placeholders(tmp_path):
    root = _routing_root(tmp_path)
    good = root / "CONTRIBUTING.md"
    good.write_text("[x](docs/adr/x.md) {{ #NN }} placeholder ok\n")

    assert check_file(good, root) == []


def test_check_file_flags_stale_release_and_test_paths(tmp_path):
    root = _routing_root(tmp_path)
    stale = root / "CONTRIBUTING.md"
    stale.write_text(
        "see docs/testing/README.md, docs/releasing/README.md, "
        "`project/releases/0.1.0/p.md`, `release/0.1.0/p.md`, "
        "and `releasing/0.1.0/p.md`\n"
    )

    errs = check_file(stale, root)

    assert any("docs/testing/" in e and "stale path" in e for e in errs)
    assert any("docs/releasing/" in e and "stale path" in e for e in errs)
    assert any("project/releases/" in e and "stale path" in e for e in errs)
    assert any("release/0.1.0/" in e and "stale path" in e for e in errs)
    assert any("releasing/0.1.0/" in e and "stale path" in e for e in errs)


def test_check_file_flags_deleted_testing_plan_names(tmp_path):
    root = _routing_root(tmp_path)
    stale = root / ".agents" / "playbooks" / "verify-change.md"
    stale.write_text("Follow coverage-matrix.md, gui-test-plan.md, and test-plan-template.md.\n")

    errs = check_file(stale, root)

    assert any("coverage-matrix.md" in e and "CONTRIBUTING.md" in e for e in errs)
    assert any("gui-test-plan.md" in e and "verify-change.md" in e for e in errs)
    assert any("test-plan-template.md" in e and "verify-change.md" in e for e in errs)


def test_check_file_flags_broken_links_but_ignores_external_placeholders_and_ellipsis(tmp_path):
    root = _routing_root(tmp_path)
    broken = root / ".agents" / "playbooks" / "release.md"
    broken.write_text("[gone](nope/missing.md)\n")
    ignored_links = root / ".agents" / "playbooks" / "verify-change.md"
    ignored_links.write_text(
        "[web](https://example.com) [mail](mailto:a@example.com) [anchor](#x) "
        "[placeholder]({{ #NN }}) [ellipsis](...) [unicode](\u2026)\n"
    )

    assert any("broken link" in e for e in check_file(broken, root))
    assert check_file(ignored_links, root) == []


def test_targets_include_contributor_playbooks_templates_and_release_scratch(tmp_path):
    root = _routing_root(tmp_path)
    contributing = root / "CONTRIBUTING.md"
    contributing.write_text("# Contributing\n")
    release = root / ".agents" / "playbooks" / "release.md"
    release.write_text("# Release\n")
    verify = root / ".agents" / "playbooks" / "verify-change.md"
    verify.write_text("# Verify\n")
    exec_plan = root / ".agents" / "playbooks" / "exec-plan.md"
    exec_plan.write_text("# ExecPlan\n")
    release_template = root / ".agents" / "templates" / "release-plan.md"
    release_template.write_text("# Release template\n")
    exec_template = root / ".agents" / "templates" / "exec-plan.md"
    exec_template.write_text("# ExecPlan template\n")
    handoff_template = root / ".agents" / "templates" / "handoff.md"
    handoff_template.write_text("# Handoff\n")
    scratch = root / ".agents" / "tmp" / "releases" / "0.1.0-alpha.3" / "notes" / "note.md"
    scratch.parent.mkdir(parents=True)
    scratch.write_text("# Scratch\n")

    found = targets(root)

    assert contributing in found
    assert release in found
    assert verify in found
    assert exec_plan in found
    assert release_template in found
    assert exec_template in found
    assert handoff_template in found
    assert scratch in found


def test_release_scratch_helper_and_tmp_scope_guard(tmp_path):
    root = _routing_root(tmp_path)
    other_tmp = root / ".agents" / "tmp" / "note.md"
    other_tmp.parent.mkdir(parents=True)
    other_tmp.write_text("# scratch\n")

    assert _release_scratch(Path(".agents/tmp/releases/0.1.0-alpha.3/note.md"))
    assert not _release_scratch(Path(".agents/tmp/note.md"))
    assert any("tmp/ is allowed only" in e for e in check_file(other_tmp, root))


def test_release_scratch_rejects_private_memory_links(tmp_path):
    root = _routing_root(tmp_path)
    scratch = root / ".agents" / "tmp" / "releases" / "0.1.0-alpha.3" / "note.md"
    scratch.parent.mkdir(parents=True)
    scratch.write_text("[private](../../../../.claude/projects/x/memory/rule.md)\n")

    assert any("local/private memory" in e for e in check_file(scratch, root))


def test_main_returns_nonzero_with_findings_and_zero_when_clean(tmp_path):
    root = _routing_root(tmp_path)
    contributing = root / "CONTRIBUTING.md"
    contributing.write_text("see docs/testing/coverage-matrix.md\n")
    release = root / ".agents" / "playbooks" / "release.md"
    release.write_text("[gone](missing.md)\n")
    verify = root / ".agents" / "playbooks" / "verify-change.md"
    verify.write_text("# Verify\n")
    exec_plan = root / ".agents" / "playbooks" / "exec-plan.md"
    exec_plan.write_text("# ExecPlan\n")
    release_template = root / ".agents" / "templates" / "release-plan.md"
    release_template.write_text("# Release template\n")
    exec_template = root / ".agents" / "templates" / "exec-plan.md"
    exec_template.write_text("# ExecPlan template\n")

    old_root = _m.ROOT
    try:
        _m.ROOT = root
        assert _m.main() == 1
        contributing.write_text("# Contributing\n")
        release.write_text("# Release\n")
        assert _m.main() == 0
    finally:
        _m.ROOT = old_root
