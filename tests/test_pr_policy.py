"""L1 component tests for pr_policy."""

import pr_policy as _m

decide = _m.decide
is_main_excluded = _m.is_main_excluded
is_safe = _m.is_safe
is_sensitive = _m.is_sensitive


def test_is_safe_accepts_safe_prose_prefixes():
    assert is_safe("docs/reference/control-and-policy/policy-mcp.md")
    assert is_safe("docs/explanation/deployment/README.md")
    assert is_safe("docs/explanation/architecture/vault.md")
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
    assert not is_safe("scratch/notes/0.1.0-alpha.12/design.md")
    assert not is_safe("scratch/notes/0.1.0-alpha.12/preimpl_spikes/run.py")
    assert not is_safe("scratch/fixtures/state.sqlite")
    assert not is_safe(old_agent_tmp)


def test_is_main_excluded_flags_scratch_branch_material():
    assert is_main_excluded("scratch/notes/0.1.0-alpha.12/design.md")
    assert is_main_excluded("scratch/notes/0.1.0-alpha.12/preimpl_spikes/run.py")
    assert not is_main_excluded("docs/reference/control-and-policy/policy-mcp.md")


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
        "src/memoria_vault/product/workspace_seed/.obsidian/app.json",
        "src/memoria_vault/runtime/policy/hook.py",
        "src/memoria_vault/product/workspace_seed/.obsidian/core-plugins.json",
        "src/memoria_vault/runtime/subsystems/processing/project/structural_impact.py",
        "src/memoria_vault/product/workspace_seed/.memoria/schemas/folders.yaml",
        "src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/main.js",
        "design-history/arcs.md",
    ]

    assert all(is_sensitive(path) for path in sensitive_paths)


def test_is_sensitive_leaves_ordinary_docs_and_root_readme_reviewable_not_sensitive():
    assert not is_sensitive("docs/explanation/deployment/README.md")
    assert not is_sensitive("docs/reference/control-and-policy/policy-mcp.md")
    assert not is_sensitive("docs/explanation/rationale/foundations/what-memoria-is.md")
    assert not is_sensitive("scratch/notes/0.1.0-alpha.12/design.md")
    assert not is_sensitive("scratch/notes/0.1.0-alpha.12/preimpl_spikes/run.py")
    assert not is_sensitive("README.md")


def test_decide_auto_approves_trusted_safe_prose_only():
    decision, _reason = decide(
        [
            "docs/reference/control-and-policy/policy-mcp.md",
            "docs/reference/data-model/glossary.md",
        ],
        "eranroseman",
        False,
    )

    assert decision == "auto_approve"


def test_decide_routes_trusted_sensitive_or_mixed_changes_to_human_review():
    sensitive_decision, reason = decide(
        ["scripts/install.sh", "docs/reference/control-and-policy/policy-mcp.md"],
        "eranroseman",
        False,
    )
    design_history_decision, _ = decide(["design-history/arcs.md"], "eranroseman", False)
    mixed_decision, _ = decide(
        [
            "docs/reference/data-model/glossary.md",
            "src/memoria_vault/product/workspace_seed/.memoria/schemas/types/note.yaml",
        ],
        "eranroseman",
        False,
    )
    root_decision, _ = decide(["README.md"], "eranroseman", False)

    assert sensitive_decision == "needs_human"
    assert "sensitive" in reason.lower()
    assert design_history_decision == "needs_human"
    assert mixed_decision == "needs_human"
    assert root_decision == "needs_human"


def test_decide_blocks_untrusted_sensitive_changes_but_reviews_safe_changes():
    blocked, _ = decide(["scripts/install.sh"], "random-user", False)
    safe_review, reason = decide(["docs/reference/data-model/glossary.md"], "random-user", False)
    agents_block, _ = decide(["AGENTS.md"], "random-user", False)

    assert blocked == "block"
    assert safe_review == "needs_human"
    assert "not on the trusted" in reason
    assert agents_block == "block"


def test_decide_blocks_scratch_prs_to_main_for_any_author():
    trusted, trusted_reason = decide(
        ["scratch/notes/0.1.0-alpha.12/design.md"], "eranroseman", False
    )
    untrusted, untrusted_reason = decide(
        ["scratch/notes/0.1.0-alpha.12/design.md"], "random-user", False
    )

    assert trusted == "block"
    assert untrusted == "block"
    assert "scratch branch" in trusted_reason
    assert "scratch branch" in untrusted_reason


def test_decide_drafts_and_empty_changesets_need_human_review():
    draft, draft_reason = decide(
        ["docs/reference/control-and-policy/policy-mcp.md"], "eranroseman", True
    )
    empty, _ = decide([], "eranroseman", False)

    assert draft == "needs_human"
    assert "Draft" in draft_reason
    assert empty == "needs_human"
