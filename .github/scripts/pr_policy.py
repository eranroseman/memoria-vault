"""pr_policy.py — PR gate policy for eranroseman/memoria-vault.

Emits two GitHub Actions outputs:
  decision = auto_approve | needs_human | block
  reason   = human-readable string

Auto-approve: PRs from a trusted author whose changes are entirely within safe
paths (docs, plans, release notes, markdown) get decision=auto_approve, which
causes the workflow to enable auto-merge. Safe PRs can be any size — a single
docs pass legitimately touches 100+ nav_order fields.

Block: any PR touching sensitive paths (CI workflows, vault profiles, scripts,
ADRs) is blocked regardless of author, requiring a human decision.

    python pr_policy.py --self-test      # offline unit tests (no GitHub API)
"""
import os
import sys

# Authors whose docs-only PRs may be auto-approved.
TRUSTED_AUTHORS = {
    "eranroseman",
    "github-actions[bot]",
}

# A path is safe if it matches any prefix or suffix below.
SAFE_PREFIXES = (
    "docs/",
    "project-files/releases/",
    "project-files/proposals/",
    "_notes/",
    "_reports/",
)
SAFE_SUFFIXES = (".md", ".txt")

# Any change to these paths is always blocked for human review.
SENSITIVE_PREFIXES = (
    ".github/workflows/",
    ".github/scripts/",
    "scripts/",
    "vault/.memoria/profiles/",
    "vault/.memoria/mcp/",
    "vault/.memoria/lane-overrides/",
    "project-files/decisions/",
    "project-files/tests/",
)


def is_safe(path: str) -> bool:
    return (
        any(path.startswith(p) for p in SAFE_PREFIXES)
        or any(path.endswith(s) for s in SAFE_SUFFIXES)
    )


def is_sensitive(path: str) -> bool:
    return any(path.startswith(p) for p in SENSITIVE_PREFIXES)


def decide(changed_paths: list[str], pr_author: str, pr_draft: bool) -> tuple[str, str]:
    """Pure decision logic. Returns (decision, reason)."""
    all_safe = all(is_safe(p) for p in changed_paths) if changed_paths else False
    sensitive_paths = [p for p in changed_paths if is_sensitive(p)]
    trusted = pr_author in TRUSTED_AUTHORS

    if pr_draft:
        return "needs_human", "Draft PR — awaiting author readiness."
    if sensitive_paths and not trusted:
        return "block", f"Sensitive paths changed by untrusted author: {sensitive_paths[:5]}"
    if sensitive_paths:
        return "needs_human", f"Sensitive paths changed — manual review required: {sensitive_paths[:5]}"
    if trusted and all_safe:
        return "auto_approve", (
            f"Trusted author (@{pr_author}), all {len(changed_paths)} changed "
            "file(s) are docs/plans only."
        )
    if all_safe:
        return "needs_human", f"Safe file types only, but @{pr_author} is not on the trusted-author list."
    return "needs_human", "Application code or unclassified path — human review required."


def get_pr_files(session, repo: str, pr_number: str) -> list:
    files, page = [], 1
    while True:
        r = session.get(
            f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files",
            params={"per_page": 100, "page": page},
            timeout=30,
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        files.extend(batch)
        page += 1
    return files


def _self_test() -> int:
    """Offline unit tests for the classification and decision logic."""
    failures = 0

    def check(name, ok):
        nonlocal failures
        if not ok:
            failures += 1
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")

    # --- is_safe ---
    check("is_safe: docs/ prefix", is_safe("docs/reference/policy-mcp.md"))
    check("is_safe: releases/ prefix", is_safe("project-files/releases/v0.1.md"))
    check("is_safe: proposals/ prefix", is_safe("project-files/proposals/idea.md"))
    check("is_safe: _notes/ prefix", is_safe("_notes/scratch.md"))
    check("is_safe: _reports/ prefix", is_safe("_reports/analysis.md"))
    check("is_safe: .md suffix (arbitrary path)", is_safe("README.md"))
    check("is_safe: .txt suffix", is_safe("CHANGELOG.txt"))
    check("is_safe: .py file NOT safe", not is_safe("scripts/install.py"))
    check("is_safe: .yml NOT safe (outside safe prefix)", not is_safe(".github/workflows/ci.yml"))
    check("is_safe: vault code NOT safe", not is_safe("vault/.memoria/mcp/policy_mcp.py"))

    # --- is_sensitive ---
    check("is_sensitive: workflow", is_sensitive(".github/workflows/ci.yml"))
    check("is_sensitive: .github/scripts/", is_sensitive(".github/scripts/pr_policy.py"))
    check("is_sensitive: scripts/", is_sensitive("scripts/install.sh"))
    check("is_sensitive: vault profiles", is_sensitive("vault/.memoria/profiles/memoria-linter/detectors.py"))
    check("is_sensitive: vault mcp", is_sensitive("vault/.memoria/mcp/policy_mcp.py"))
    check("is_sensitive: lane-overrides", is_sensitive("vault/.memoria/lane-overrides/coder.yaml"))
    check("is_sensitive: decisions", is_sensitive("project-files/decisions/29-testing.md"))
    check("is_sensitive: tests dir", is_sensitive("project-files/tests/coverage-matrix.md"))
    check("is_sensitive: docs/ NOT sensitive", not is_sensitive("docs/reference/policy-mcp.md"))
    check("is_sensitive: README NOT sensitive", not is_sensitive("README.md"))

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
    d, r = decide(["docs/reference/glossary.md", "vault/.memoria/plugins/__init__.py"], "eranroseman", False)
    check("decide: mixed (non-sensitive, non-all-safe) -> needs_human", d == "needs_human")

    # --- edge: .md file in sensitive prefix is both safe and sensitive ---
    check("is_safe: .md in scripts/ IS safe (suffix match)",
          is_safe("scripts/README.md"))
    check("is_sensitive: .md in scripts/ IS sensitive (prefix match)",
          is_sensitive("scripts/README.md"))
    d, r = decide(["scripts/README.md"], "eranroseman", False)
    check("decide: sensitive .md by trusted -> needs_human (sensitive wins)",
          d == "needs_human")

    print(f"\n{'FAILED' if failures else 'OK'}: {failures} failing check(s) — pr_policy self-test")
    return failures


def main() -> int:
    if "--self-test" in sys.argv:
        sys.exit(1 if _self_test() else 0)

    import requests

    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["REPO"]
    pr_number = os.environ["PR_NUMBER"]
    pr_author = os.environ["PR_AUTHOR"]
    pr_draft = os.environ.get("PR_DRAFT", "false").lower() == "true"

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })

    files = get_pr_files(session, repo, pr_number)
    changed_paths = [f["filename"] for f in files]

    decision, reason = decide(changed_paths, pr_author, pr_draft)
    print(f"decision={decision}")
    print(f"reason={reason}")
    return 0


if __name__ == "__main__":
    main()
