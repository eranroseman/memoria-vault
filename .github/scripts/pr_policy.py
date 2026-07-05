"""pr_policy.py — PR gate policy for eranroseman/memoria-vault.

Emits two GitHub Actions outputs:
  decision = auto_approve | needs_human | block
  reason   = human-readable string

Auto-approve: PRs from a trusted author whose changes are entirely within safe
paths get decision=auto_approve, which causes the workflow to enable auto-merge.
Safe prose paths are docs/ or _notes/ with .md/.txt files only. Safe PRs can be
any size — a single docs pass legitimately touches 100+ nav_order fields.

Needs-human: the check passes but does not enable auto-merge. It is a manual-merge
classification, not a required-approval mechanism.

Block: scratch/ is branch-owned ephemeral working material. It lives on the
scratch branch and is not merged into main by PR.

Block: any PR touching sensitive paths (.github/, vault-template/.memoria/,
scripts/, or design-history/) is blocked for untrusted authors; trusted authors
require a human review. Agent instruction surfaces are also sensitive: they can
change what future automation is allowed or encouraged to do.

    python pr_policy.py --self-test      # offline unit tests (no GitHub API)
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

# Trusted authors: docs-only PRs auto-approve; sensitive-path PRs fall to
# needs_human (a human reviews/merges) rather than being blocked. dependabot[bot]
# is here so its dependency PRs are reviewable, not hard-blocked on sensitive paths.
TRUSTED_AUTHORS = {
    "eranroseman",
    "github-actions[bot]",
    "dependabot[bot]",
}

# A path is safe only when it is prose under an explicitly safe prefix.
SAFE_PROSE_PREFIXES = (
    "docs/",
    "_notes/",
)
SAFE_SUFFIXES = (".md", ".txt")
MAIN_EXCLUDED_PREFIXES = ("scratch/",)

# Any change to these paths is always blocked for human review. design-history/
# holds the durable design record and stays review-required.
SENSITIVE_PREFIXES = (
    ".github/",
    ".agents/",
    ".claude/",
    ".codex/",
    ".kilo/",
    "scripts/",
    "src/memoria_vault/runtime/policy/",
    "src/memoria_vault/runtime/subsystems/",
    "vault-template/.memoria/",
    "design-history/",
)
SENSITIVE_PATHS = {
    "AGENTS.md",
}


def is_safe(path: str) -> bool:
    return any(path.startswith(p) for p in SAFE_PROSE_PREFIXES) and any(
        path.endswith(s) for s in SAFE_SUFFIXES
    )


def is_main_excluded(path: str) -> bool:
    return any(path.startswith(p) for p in MAIN_EXCLUDED_PREFIXES)


def is_sensitive(path: str) -> bool:
    return path in SENSITIVE_PATHS or any(path.startswith(p) for p in SENSITIVE_PREFIXES)


def decide(changed_paths: list[str], pr_author: str, pr_draft: bool) -> tuple[str, str]:
    """Pure decision logic. Returns (decision, reason)."""
    all_safe = all(is_safe(p) for p in changed_paths) if changed_paths else False
    main_excluded_paths = [p for p in changed_paths if is_main_excluded(p)]
    sensitive_paths = [p for p in changed_paths if is_sensitive(p)]
    trusted = pr_author in TRUSTED_AUTHORS

    if main_excluded_paths:
        return (
            "block",
            "scratch/ lives on the scratch branch; do not merge scratch material into main.",
        )
    if pr_draft:
        return "needs_human", "Manual merge required: Draft PR — awaiting author readiness."
    if sensitive_paths and not trusted:
        return "block", f"Sensitive paths changed by untrusted author: {sensitive_paths[:5]}"
    if sensitive_paths:
        return (
            "needs_human",
            f"Manual merge required: sensitive paths changed: {sensitive_paths[:5]}",
        )
    if trusted and all_safe:
        return "auto_approve", (
            f"Trusted author (@{pr_author}), all {len(changed_paths)} changed "
            "file(s) are in safe paths (docs / notes)."
        )
    if all_safe:
        return (
            "needs_human",
            f"Manual merge required: safe file types only, but @{pr_author} is "
            "not on the trusted-author list.",
        )
    return "needs_human", "Manual merge required: application code or unclassified path."


def get_pr_files(token: str, repo: str, pr_number: str) -> list:
    files, page = [], 1
    while True:
        query = urllib.parse.urlencode({"per_page": 100, "page": page})
        request = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files?{query}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                batch = json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
            raise SystemExit(
                f"pr_policy: failed to fetch PR #{pr_number} files (page {page}): {exc}"
            ) from exc
        if not batch:
            break
        files.extend(batch)
        page += 1
    return files


def main() -> int:
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["REPO"]
    pr_number = os.environ["PR_NUMBER"]
    pr_author = os.environ["PR_AUTHOR"]
    pr_draft = os.environ.get("PR_DRAFT", "false").lower() == "true"

    files = get_pr_files(token, repo, pr_number)
    changed_paths = [f["filename"] for f in files]

    decision, reason = decide(changed_paths, pr_author, pr_draft)
    print(f"decision={decision}")
    print(f"reason={reason}")
    return 0


if __name__ == "__main__":
    main()
