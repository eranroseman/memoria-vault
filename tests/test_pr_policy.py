"""L1 component tests for pr_policy."""

import pr_policy as _m

decide = _m.decide
is_main_excluded = _m.is_main_excluded
is_safe = _m.is_safe
is_sensitive = _m.is_sensitive


def test_is_safe_accepts_safe_prose_prefixes():
    assert is_safe("docs/reference/policy-mcp.md")
    assert is_safe("docs/explanation/deployment.md")
    assert is_safe("docs/explanation/architecture/interaction-channels.md")
    assert is_safe("_notes/scratch.md")


def test_is_safe_rejects_root_markdown_non_prose_and_code_paths():
    old_agent_tmp = ".agents" + "/tmp/releases/0.1.0-alpha.12/design.md"

    assert not is_safe("README.md")
    assert not is_safe("CHANGELOG.txt")
    assert not is_safe("docs/_data/nav.yml")
    assert not is_safe("scripts/install.py")
    assert not is_safe(".github/workflows/ci.yml")
    assert not is_safe("src/memoria_vault/runtime/policy/hook.py")
    assert not is_safe("scripts/README.md")
    assert not is_safe("scratch/releases/0.1.0-alpha.12/design.md")
    assert not is_safe("scratch/releases/0.1.0-alpha.12/preimpl_spikes/run.py")
    assert not is_safe("scratch/fixtures/state.sqlite")
    assert not is_safe(old_agent_tmp)


def test_is_main_excluded_flags_scratch_branch_material():
    assert is_main_excluded("scratch/releases/0.1.0-alpha.12/design.md")
    assert is_main_excluded("scratch/releases/0.1.0-alpha.12/preimpl_spikes/run.py")
    assert not is_main_excluded("docs/reference/policy-mcp.md")


def test_is_sensitive_flags_policy_and_runtime_surfaces():
    old_agent_tmp = ".agents" + "/tmp/releases/0.1.0-alpha.12/design.md"
    sensitive_paths = [
        ".github/workflows/ci.yml",
        ".github/scripts/pr_policy.py",
        ".github/CODEOWNERS",
        "AGENTS.md",
        ".agents/skills/schema-change/SKILL.md",
        old_agent_tmp,
        ".claude/skills/release/SKILL.md",
        ".codex/agents-doctor.md",
        ".kilo/config.md",
        "scripts/install.sh",
        "scripts/README.md",
        "vault-template/.memoria/profiles/memoria-linter/detectors.py",
        "src/memoria_vault/runtime/policy/hook.py",
        "vault-template/.memoria/lane-overrides/coder.yaml",
        "src/memoria_vault/runtime/subsystems/processing/project/structural_impact.py",
        "vault-template/.memoria/schemas/folders.yaml",
        "vault-template/.memoria/design-system.md",
        "docs/adr/125-standalone-cli-engine-architecture.md",
    ]

    assert all(is_sensitive(path) for path in sensitive_paths)


def test_is_sensitive_leaves_ordinary_docs_and_root_readme_reviewable_not_sensitive():
    assert not is_sensitive("docs/explanation/deployment.md")
    assert not is_sensitive("docs/reference/policy-mcp.md")
    assert not is_sensitive("docs/design/what-memoria-is.md")
    assert not is_sensitive("scratch/releases/0.1.0-alpha.12/design.md")
    assert not is_sensitive("scratch/releases/0.1.0-alpha.12/preimpl_spikes/run.py")
    assert not is_sensitive("README.md")


def test_decide_auto_approves_trusted_safe_prose_only():
    decision, _reason = decide(
        ["docs/reference/policy-mcp.md", "docs/reference/profile-capabilities.md"],
        "eranroseman",
        False,
    )

    assert decision == "auto_approve"


def test_decide_routes_trusted_sensitive_or_mixed_changes_to_human_review():
    sensitive_decision, reason = decide(
        ["scripts/install.sh", "docs/reference/policy-mcp.md"], "eranroseman", False
    )
    adr_decision, _ = decide(["docs/adr/03-structural-review-gate.md"], "eranroseman", False)
    mixed_decision, _ = decide(
        ["docs/reference/glossary.md", "vault-template/.memoria/schemas/types/note.yaml"],
        "eranroseman",
        False,
    )
    root_decision, _ = decide(["README.md"], "eranroseman", False)

    assert sensitive_decision == "needs_human"
    assert "sensitive" in reason.lower()
    assert adr_decision == "needs_human"
    assert mixed_decision == "needs_human"
    assert root_decision == "needs_human"


def test_decide_blocks_untrusted_sensitive_changes_but_reviews_safe_changes():
    blocked, _ = decide(["scripts/install.sh"], "random-user", False)
    safe_review, reason = decide(["docs/reference/glossary.md"], "random-user", False)
    agents_block, _ = decide(["AGENTS.md"], "random-user", False)

    assert blocked == "block"
    assert safe_review == "needs_human"
    assert "not on the trusted" in reason
    assert agents_block == "block"


def test_decide_blocks_scratch_prs_to_main_for_any_author():
    trusted, trusted_reason = decide(
        ["scratch/releases/0.1.0-alpha.12/design.md"], "eranroseman", False
    )
    untrusted, untrusted_reason = decide(
        ["scratch/releases/0.1.0-alpha.12/design.md"], "random-user", False
    )

    assert trusted == "block"
    assert untrusted == "block"
    assert "scratch branch" in trusted_reason
    assert "scratch branch" in untrusted_reason


def test_decide_drafts_and_empty_changesets_need_human_review():
    draft, draft_reason = decide(["docs/reference/policy-mcp.md"], "eranroseman", True)
    empty, _ = decide([], "eranroseman", False)

    assert draft == "needs_human"
    assert "Draft" in draft_reason
    assert empty == "needs_human"
