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
"""
import os

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

# Authors whose docs-only PRs may be auto-approved.
TRUSTED_AUTHORS = {
    "eranroseman",
    "github-actions[bot]",
}

# A path is safe if it matches any prefix or suffix below.
SAFE_PREFIXES = (
    "docs/",
    "project-files/plans/",
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


def get_pr_files():
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


def is_safe(path: str) -> bool:
    return (
        any(path.startswith(p) for p in SAFE_PREFIXES)
        or any(path.endswith(s) for s in SAFE_SUFFIXES)
    )


def is_sensitive(path: str) -> bool:
    return any(path.startswith(p) for p in SENSITIVE_PREFIXES)


files = get_pr_files()
changed_paths = [f["filename"] for f in files]

all_safe = all(is_safe(p) for p in changed_paths) if changed_paths else False
sensitive_paths = [p for p in changed_paths if is_sensitive(p)]
trusted = pr_author in TRUSTED_AUTHORS

decision = "needs_human"
reason = "Application code or unclassified path — human review required."

if pr_draft:
    decision = "needs_human"
    reason = "Draft PR — awaiting author readiness."
elif sensitive_paths and not trusted:
    decision = "block"
    reason = f"Sensitive paths changed by untrusted author: {sensitive_paths[:5]}"
elif sensitive_paths:
    decision = "needs_human"
    reason = f"Sensitive paths changed — manual review required: {sensitive_paths[:5]}"
elif trusted and all_safe:
    decision = "auto_approve"
    reason = (
        f"Trusted author (@{pr_author}), all {len(changed_paths)} changed "
        "file(s) are docs/plans only."
    )
elif all_safe:
    decision = "needs_human"
    reason = f"Safe file types only, but @{pr_author} is not on the trusted-author list."

print(f"decision={decision}")
print(f"reason={reason}")
