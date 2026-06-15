"""L1 component test for pr_policy — extracted from its former --self-test (ADR-44)."""
import pr_policy as _m

decide = _m.decide
is_safe = _m.is_safe
is_sensitive = _m.is_sensitive


def test_pr_policy():
    def _run():
        """Offline unit tests for the classification and decision logic."""
        failures = 0

        def check(name, ok):
            nonlocal failures
            if not ok:
                failures += 1
            print(f"  {'PASS' if ok else 'FAIL'}  {name}")

        # --- is_safe ---
        check("is_safe: docs/ prefix", is_safe("docs/reference/policy-mcp.md"))
        check(
            "is_safe: releasing docs prefix",
            is_safe("docs/releasing/0.1.0-alpha.2/release-plan-0.1.0-alpha.2.md"),
        )
        check("is_safe: explanation prose prefix", is_safe("docs/explanation/architecture/human-channels.md"))
        check("is_safe: _notes/ prefix", is_safe("_notes/scratch.md"))
        check("is_safe: README root markdown NOT safe", not is_safe("README.md"))
        check("is_safe: arbitrary .txt NOT safe", not is_safe("CHANGELOG.txt"))
        check("is_safe: non-prose under docs/ NOT safe", not is_safe("docs/_data/nav.yml"))
        check("is_safe: .py file NOT safe", not is_safe("scripts/install.py"))
        check("is_safe: .yml NOT safe (outside safe prefix)", not is_safe(".github/workflows/ci.yml"))
        check("is_safe: vault code NOT safe", not is_safe("src/.memoria/mcp/policy_mcp.py"))

        # --- is_sensitive ---
        check("is_sensitive: workflow", is_sensitive(".github/workflows/ci.yml"))
        check("is_sensitive: .github/scripts/", is_sensitive(".github/scripts/pr_policy.py"))
        check("is_sensitive: all .github/", is_sensitive(".github/CODEOWNERS"))
        check("is_sensitive: AGENTS.md", is_sensitive("AGENTS.md"))
        check("is_sensitive: .agents/", is_sensitive(".agents/skills/schema-change/SKILL.md"))
        check("is_sensitive: .claude/", is_sensitive(".claude/skills/release/SKILL.md"))
        check("is_sensitive: .codex/", is_sensitive(".codex/agents-doctor.md"))
        check("is_sensitive: .kilo/", is_sensitive(".kilo/config.md"))
        check("is_sensitive: scripts/", is_sensitive("scripts/install.sh"))
        check("is_sensitive: vault profiles", is_sensitive("src/.memoria/profiles/memoria-linter/detectors.py"))
        check("is_sensitive: vault mcp", is_sensitive("src/.memoria/mcp/policy_mcp.py"))
        check("is_sensitive: lane-overrides", is_sensitive("src/.memoria/lane-overrides/coder.yaml"))
        check("is_sensitive: vault engines", is_sensitive("src/.memoria/operations/processing/ingest/runner.py"))
        check("is_sensitive: vault schemas", is_sensitive("src/.memoria/schemas/folders.yaml"))
        check("is_sensitive: vault design docs", is_sensitive("src/.memoria/design-system.md"))
        check("is_sensitive: adr (docs/adr/)", is_sensitive("docs/adr/29-testing-framework.md"))
        check("is_sensitive: testing docs NOT sensitive", not is_sensitive("docs/testing/coverage-matrix.md"))
        check("is_sensitive: docs/ NOT sensitive", not is_sensitive("docs/reference/policy-mcp.md"))
        check("is_sensitive: explanation prose NOT sensitive", not is_sensitive("docs/explanation/overview/what-memoria-is.md"))
        check("is_sensitive: README NOT sensitive", not is_sensitive("README.md"))
        # docs/adr/ is both safe (docs/ prefix) and sensitive (docs/adr/ prefix) — sensitive wins
        d, _ = decide(["docs/adr/03-structural-review-gate.md"], "eranroseman", False)
        check("decide: ADR edit by trusted -> needs_human (review-required)", d == "needs_human")

        # --- decide: trusted author, docs-only ---
        d, r = decide(["docs/reference/policy-mcp.md", "docs/reference/profiles.md"], "eranroseman", False)
        check("decide: trusted + all safe -> auto_approve", d == "auto_approve")

        # --- decide: trusted author, sensitive paths ---
        d, r = decide(["scripts/install.sh", "docs/reference/policy-mcp.md"], "eranroseman", False)
        check("decide: trusted + sensitive -> needs_human", d == "needs_human")
        check("decide: reason mentions sensitive paths", "sensitive" in r.lower() or "Sensitive" in r)

        # --- decide: untrusted author, sensitive paths -> block ---
        d, r = decide(["scripts/install.sh"], "random-user", False)
        check("decide: untrusted + sensitive -> block", d == "block")

        # --- decide: untrusted author, safe paths only -> needs_human ---
        d, r = decide(["docs/reference/glossary.md"], "random-user", False)
        check("decide: untrusted + safe -> needs_human", d == "needs_human")
        check("decide: reason mentions untrusted", "not on the trusted" in r)

        # --- decide: draft PR -> needs_human ---
        d, r = decide(["docs/reference/policy-mcp.md"], "eranroseman", True)
        check("decide: draft PR -> needs_human", d == "needs_human")
        check("decide: draft reason", "Draft" in r)

        # --- decide: empty changeset -> needs_human (all_safe is False for empty) ---
        d, r = decide([], "eranroseman", False)
        check("decide: empty changeset -> needs_human", d == "needs_human")

        # --- decide: mixed safe + non-safe, non-sensitive -> needs_human ---
        d, r = decide(["docs/reference/glossary.md", "src/.obsidian/app.json"], "eranroseman", False)
        check("decide: mixed (non-sensitive, non-all-safe) -> needs_human", d == "needs_human")

        # --- edge: .md file in sensitive prefix is sensitive, not safe ---
        check("is_safe: .md in scripts/ NOT safe",
              not is_safe("scripts/README.md"))
        check("is_sensitive: .md in scripts/ IS sensitive (prefix match)",
              is_sensitive("scripts/README.md"))
        d, r = decide(["scripts/README.md"], "eranroseman", False)
        check("decide: sensitive .md by trusted -> needs_human (sensitive wins)",
              d == "needs_human")

        d, r = decide(["README.md"], "eranroseman", False)
        check("decide: root markdown by trusted -> needs_human", d == "needs_human")

        d, r = decide(["AGENTS.md"], "random-user", False)
        check("decide: AGENTS.md by untrusted -> block", d == "block")

        print(f"\n{'FAILED' if failures else 'OK'}: {failures} failing check(s) — pr_policy self-test")
        return failures
    assert _run() == 0
