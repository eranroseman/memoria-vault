"""L1 component tests for pr_policy (ADR-44)."""

import pr_policy as _m

decide = _m.decide
is_safe = _m.is_safe
is_sensitive = _m.is_sensitive


def test_is_safe_accepts_safe_prose_and_scratch_prefixes():
    assert is_safe("docs/reference/policy-mcp.md")
    assert is_safe("docs/explanation/deployment.md")
    assert is_safe("docs/explanation/architecture/interaction-channels.md")
    assert is_safe("_notes/scratch.md")
    assert is_safe("scratch/releases/0.1.0-alpha.12/design.md")
    assert is_safe("scratch/releases/0.1.0-alpha.12/preimpl_spikes/run.py")
    assert is_safe("scratch/fixtures/state.sqlite")


def test_is_safe_rejects_root_markdown_non_prose_and_code_paths():
    old_agent_tmp = ".agents" + "/tmp/releases/0.1.0-alpha.12/design.md"

    assert not is_safe("README.md")
    assert not is_safe("CHANGELOG.txt")
    assert not is_safe("docs/_data/nav.yml")
    assert not is_safe("scripts/install.py")
    assert not is_safe(".github/workflows/ci.yml")
    assert not is_safe("vault-template/.memoria/mcp/policy_mcp.py")
    assert not is_safe("scripts/README.md")
    assert not is_safe(old_agent_tmp)


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
        "vault-template/.memoria/mcp/policy_mcp.py",
        "vault-template/.memoria/lane-overrides/coder.yaml",
        "vault-template/.memoria/operations/processing/ingest/runner.py",
        "vault-template/.memoria/schemas/folders.yaml",
        "vault-template/.memoria/design-system.md",
        "docs/adr/29-testing-framework.md",
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
        ["docs/reference/glossary.md", "vault-template/.obsidian/app.json"], "eranroseman", False
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
    scratch_review, scratch_reason = decide(
        ["scratch/releases/0.1.0-alpha.12/design.md"], "random-user", False
    )

    assert blocked == "block"
    assert safe_review == "needs_human"
    assert "not on the trusted" in reason
    assert agents_block == "block"
    assert scratch_review == "needs_human"
    assert "not on the trusted" in scratch_reason


def test_decide_auto_approves_trusted_scratch_only():
    decision, reason = decide(
        [
            "scratch/releases/0.1.0-alpha.12/design.md",
            "scratch/releases/0.1.0-alpha.12/preimpl_spikes/run.py",
        ],
        "eranroseman",
        False,
    )

    assert decision == "auto_approve"
    assert "scratch" in reason.lower()


def test_decide_drafts_and_empty_changesets_need_human_review():
    draft, draft_reason = decide(["docs/reference/policy-mcp.md"], "eranroseman", True)
    empty, _ = decide([], "eranroseman", False)

    assert draft == "needs_human"
    assert "Draft" in draft_reason
    assert empty == "needs_human"
