---
topic: tests
title: Release Gate
status: stable
parent: Test plans
grand_parent: Testing
nav_order: 70
---

# Release Gate

The Release Gate sequences a fresh-clone candidate through Source, Package,
Runtime, Product, and cut mechanics.

## Preconditions

- Clean Ubuntu/WSL2 box for Linux installer checks.
- Clean native Windows production path for attended production install checks
  when the release requires them.
- Throwaway vault path, for example `~/Memoria-candidate`.
- Fresh clone at the candidate commit.
- Required profile `.env` keys present; never print values.

## Sequence

| Step | Evidence |
| --- | --- |
| Source | `scripts/verify pr` passes. |
| Package | `scripts/verify package` passes. |
| Installer dry-run | `bash scripts/install.sh --dry-run --vault "$RV"` reports no mutation and resolved substitutions. |
| Real install | `bash scripts/install.sh --vault "$RV"` completes; five profiles register; re-run is idempotent. |
| Runtime | [Runtime Gate](runtime-gate.md) passes on the installed candidate. |
| Product | [Product Gate](product-gate.md) passes, including manual GUI checks when required. |
| Failure/recovery | [Failure Recovery Checks](failure-recovery-checks.md) pass for changed risk areas. |
| Blockers | No open release-milestone issue has `Readiness: Blocked`; no release readiness/stage sub-issue is open. |
| Published docs | `python scripts/check_live_docs_links.py --base-url https://eranroseman.github.io/memoria-vault/` passes after Pages deploys. |
| Cut | release-please owns version, changelog, tag, and GitHub Release. |

## Sign-off

| Gate / stage | Result | Evidence link |
| --- | --- | --- |
| Source | | |
| Package | | |
| Installer | | |
| Runtime | | |
| Product | | |
| Failure/recovery | | |
| Release blockers | | |
| Published docs | | |
| Cut mechanics | | |

Record sign-off in the release parent issue or readiness/stage sub-issues. Copy
it to a release `validation-log.md` only when the issue trail is insufficient.
