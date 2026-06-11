"""pr_policy.py — PR gate policy for eranroseman/memoria-vault.

Emits two GitHub Actions outputs:
  decision = auto_approve | needs_human | block
  reason   = human-readable string

Auto-approve: PRs from a trusted author whose changes are entirely within safe
paths (docs/, markdown) get decision=auto_approve, which
causes the workflow to enable auto-merge. Safe PRs can be any size — a single
docs pass legitimately touches 100+ nav_order fields. Note: docs/adr/ is the one
docs/ subtree that is NOT auto-approved (it holds the decision record — see below).

Block: any PR touching sensitive paths (CI workflows, vault profiles, scripts,
ADRs at docs/adr/) is blocked regardless of author, requiring a human decision.

    python pr_policy.py --self-test      # offline unit tests (no GitHub API)
"""
import os

# Trusted authors: docs-only PRs auto-approve; sensitive-path PRs fall to
# needs_human (a human reviews/merges) rather than being blocked. dependabot[bot]
# is here so its dependency PRs are reviewable, not hard-blocked on sensitive paths.
TRUSTED_AUTHORS = {
    "eranroseman",
    "github-actions[bot]",
    "dependabot[bot]",
}

# A path is safe if it matches any prefix or suffix below.
SAFE_PREFIXES = (
    "docs/",
    "_notes/",
    "_reports/",
)
SAFE_SUFFIXES = (".md", ".txt")

# Any change to these paths is always blocked for human review. docs/adr/ holds the
# decision record (ADRs at every lifecycle status) and stays review-required even
# though it lives under the otherwise-safe docs/ tree — is_sensitive wins over is_safe.
SENSITIVE_PREFIXES = (
    ".github/workflows/",
    ".github/scripts/",
    "scripts/",
    "src/.memoria/profiles/",
    "src/.memoria/mcp/",
    "src/.memoria/lane-overrides/",
    "src/.memoria/plugins/",
    "docs/adr/",
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
            "file(s) are in safe paths (docs / release / notes)."
        )
    if all_safe:
        return "needs_human", f"Safe file types only, but @{pr_author} is not on the trusted-author list."
    return "needs_human", "Application code or unclassified path — human review required."


def get_pr_files(session, repo: str, pr_number: str) -> list:
    files, page = [], 1
    while True:
        try:
            r = session.get(
                f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files",
                params={"per_page": 100, "page": page},
                timeout=30,
            )
            r.raise_for_status()
        except requests.RequestException as exc:
            raise SystemExit(
                f"pr_policy: failed to fetch PR #{pr_number} files (page {page}): {exc}"
            ) from exc
        batch = r.json()
        if not batch:
            break
        files.extend(batch)
        page += 1
    return files


def main() -> int:
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
