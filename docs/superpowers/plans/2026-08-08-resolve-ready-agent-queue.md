# Ready-for-agent Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` task by task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve every live, unassigned, unblocked `ready-for-agent` issue in oldest-to-newest order.

**Architecture:** The queue contains eight documentation changes, one sandbox-lifecycle regression test, and one developer-bootstrap repair. Each issue remains a narrow task with its GitHub Agent Brief as the authoritative contract. The branch stays isolated in `.worktrees/codex-ready-agent-queue`; changes share one reviewable queue diff but must remain separable by issue.

**Tech Stack:** Python, pytest, Bash, Markdown, Jekyll front matter, Mermaid, GitHub CLI.

## Global Constraints

- Claim each issue with `gh issue edit <N> --add-assignee @me` before its first repository edit; re-read its live state immediately before claiming.
- Work oldest to newest unless an earlier brief explicitly creates a semantic prerequisite. #1293 precedes #1753 and #1771 because it separates evidence **grounds** from genuine Toulmin **warrants**.
- Stage explicit paths only; do not stage, commit, push, create a PR, or close an issue without the required user authorization.
- Use only disposable vaults under `test-vault/` for transcript or runtime examples. Never use personal-vault data.
- Preserve frozen `design-history/` and do not mechanically rename genuine Toulmin warrant terminology.
- The baseline gate fails locally because MCP 1.x is installed; Task 10 fixes the bootstrap contract. The sandbox also denies loopback sockets, so use elevated verification or CI evidence for HTTP tests.
- Run `python scripts/verify` after the final queue change. For #1781, also run the explicit installer/bootstrap security-diff scan required by its brief.

---

### Task 1: #1293 — Reconcile evidence-set terminology as grounds

**Files:** Active beta.1 design/spec/roadmap prose found by semantic `warrant` search; preserve `docs/reference/control-and-policy/evidence-sets.md` unless a real inconsistency is found.

- [x] Re-read #1293’s Agent Brief and classify every live, non-frozen `warrant` occurrence by meaning.
- [x] Rename only evidence-set or computed-evidence meanings to `grounds`; retain Toulmin `warrant`, `unstated-warrant`, NLI judge fields, and `warrant-lost`.
- [x] Reconcile the beta.1 marker sketch with its v2 `id` plus ordered `items` contract, derived type/completeness/review routing, and remove stale `code-warrant` vocabulary.
- [x] Run `rg` to confirm the remaining occurrences have the intended meanings, then run the evidence-set tests and documentation gates.

### Task 2: #1649 — Explain the checked read verdict

**Files:** New Knowledge explanation; Knowledge explanation index; Home; root README; terminology gate and its focused tests.

- [x] Add a concise explanation of `unchecked`, `checked`, and `quarantined`; distinguish checked eligibility from truth, citation, PI content approval, evidence resolution, and export readiness.
- [x] Document fail-closed checked-file reads and distinguish trusted-writer checked promotion from project-passage promotion.
- [x] Link Home’s first use of “checked”, correct Home/README language and diagrams that equate every checked state with PI approval, and keep valid PI-operated routes intact.
- [x] Extend the terminology guard with positive and negative regression cases for universal approval-equivalence language; run its focused tests and documentation gates.

### Task 3: #1650 — Move the detailed model and route command-reference readers

**Files:** New `docs/overview.md`; docs portal/indexes; Home; root README; Knowledge-cycle route; commands-and-transports portal.

- [x] Move Home’s five-term table, detailed working loop, and control rule into the visible Overview page; retain Home’s concise introduction and Mermaid.
- [x] Ensure the move preserves #1649’s checked-versus-PI distinction, with no compatibility stub or duplicate glossary definitions.
- [x] Replace the Commands and transports bare list with a `Page | Use it for` routing table covering every existing entry and distinguishing the five system-action pages.
- [x] Run link, claims, terminology, spelling, structure, and full documentation verification.

### Task 4: #1647 — Publish the captured first-session transcript

**Files:** New tutorial page; tutorial index; published Home; root README; any required docs indexes.

- [x] Capture one continuous, deterministic public-CLI run in a fresh disposable vault: Work capture/check/citation key/digest, checked claim, checked project/slice/outline, Ask `sources` and `unknowns`, draft compose/verify, refused export, PI disposition, re-verification, and citation-bearing Markdown export.
- [x] Build the page from captured commands and output, marking only transient path/time/ID values as consistent redactions.
- [x] Route Home’s hero and first-session section, the root README, and the tutorial portal to the new page without claiming a measured five-minute execution.
- [x] Re-run the documented flow in a fresh disposable vault, confirm the final citation, and run documentation checks.

### Task 5: #1652 — Remove unsupported multi-machine sync advice

**Files:** `return-to-work` guide; new troubleshooting guide; troubleshooting index; backup/recovery reference; directly misleading supporting docs if found.

- [x] Replace routine remote-pull and second-writer language with the supported local one-workstation health flow.
- [x] Add the fail-closed recovery sequence: preserve histories/backups, choose one authoritative lineage, check out its matching Git revision, restore its matching snapshot when needed, verify the journal, then scan the workspace.
- [x] Explicitly forbid blind `.memoria/journal-head` conflict resolution, journal-history merging, and improvised recovery when authority or matching backups are unavailable.
- [x] Add reciprocal navigation with Backup and recovery, then run documentation checks.

### Task 6: #1747 — Pin Bubblewrap parent-death behavior in a runtime test

**Files:** `tests/test_code_sandbox.py` only, unless a focused test helper is needed in that module.

- [x] Write a failing runtime test through `run_artifact` that starts a sandboxed child writing a heartbeat, kills only its parent helper process, and proves heartbeat stops after the parent dies.
- [ ] Run the new test in the required Bubblewrap environment, verify the red failure when `--die-with-parent` is temporarily removed from `_run_with_bwrap`, restore production code unchanged, and verify green.
- [x] Keep cleanup bounded: always reap the helper process group in `finally`; do not use `_bwrap_proof` as the production-lifecycle proof.
- [ ] Run the focused sandbox tests and the full verification gate where Bubblewrap is available.

### Task 7: #1753 — Document the evidence-set review queue

**Files:** New Project how-to; project how-to index; adjacent compose/export pages; evidence-review reference link.

- [x] Write a task-oriented guide that uses `memoria review list`, optional filters, `show`, exactly one disposition, re-listing, project verification, and optional telemetry stats.
- [x] Explain all four dispositions, accept-only hold clearing, permanent/read-only cure rows, SRD-gap repair/reverify, PI-only local execution, and the optional `--show-analysis` view.
- [x] Use the real `--type` filter rather than inventing `--routing-type`; preserve the separate inference-license meaning of `--warrant`.
- [x] Update navigation and adjacent routes, then validate commands against `tests/test_cli_review.py` and run documentation gates.

### Task 8: #1754 — Add the MCP setup how-to

**Files:** New setup how-to; setup index; only directly necessary reciprocal references.

- [x] Document installing the declared optional MCP SDK into the vault-local environment, with tested Linux/WSL and Windows forms rather than an invented package command.
- [x] Explain the seeded, PI-owned `.mcp.json`; absolute host paths; repeated non-root startup-fixed read scopes; provenance-only `--actor`; agent request authority; and the boundary between the engine envelope and optional external-adapter policy hooks.
- [x] Give a non-destructive stdio verification path and use a disposable vault for any manual smoke.
- [x] Validate terminology against the MCP transport, package, and seed contracts and run the documentation gate.

### Task 9: #1771 — Diagram shipped typed consequence propagation

**Files:** Consequence-propagation explanation and its one directly linked rationale banner.

- [x] Replace the stale blanket planned-state framing with a compact Mermaid 10.9.1 diagram grounded in `hop_consequence`.
- [x] Show transitive supports/extends/evidence/derived routes to `grounds-lost`, warrant to `warrant-lost`, qualifier to `qualifier-regression`, and direct trigger paths to `rebuttal-strengthened`.
- [x] Show a single warrant/license fan to multiple claims and state the deliberate non-traversal through generic rebuttal, contradicts, and tension relations.
- [x] Run Mermaid/docs gates and the propagation test modules.

### Task 10: #1781 — Restore developer bootstrap MCP parity

**Files:** `scripts/dev/setup.sh`; contributor setup guidance; new or existing focused script-contract test.

- [x] Write a failing offline test that pins both developer-bootstrap editable-install paths to the declared `mcp` extra and preserves the product-installer boundary.
- [x] Change the normal and fallback editable-install commands to request `.[mcp]`; update their messages and contributor documentation to say this supplies the SDK for local full verification, not product runtime installation.
- [x] Verify the focused test red/green cycle, shellcheck, MCP transport import under an isolated compatible environment, and full `python scripts/verify`.
- [x] Run `codex-security:security-diff-scan` over the bootstrap diff; resolve or track every finding before review.

## Completion Audit

- [x] Verify every issue is still implemented by its approved Agent Brief, with focused test/doc evidence recorded.
- [x] Obtain explicit authorization for staging, commits, push, and one draft PR.
- [ ] After merge evidence, close only issues whose delivered behavior is live and re-query `ready-for-agent`, unassigned, unblocked work until the queue is empty.
