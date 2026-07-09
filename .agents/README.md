# Portable agent playbooks

This directory contains tool-neutral procedures that any coding agent can use.
It does not define repository policy.

## Authority

[`AGENTS.md`](../AGENTS.md) is authoritative for worktrees, branches, testing,
security boundaries, documentation, PRs, and merge discipline. When a playbook
conflicts with `AGENTS.md`, follow `AGENTS.md` and update the stale playbook in
the same change.

Repository scripts, schemas, workflows, and tests remain the source of truth for
their respective behavior. Playbooks should invoke those sources rather than
copying their implementation details.

## Playbooks

| Playbook | Use |
|---|---|
| [Code review](playbooks/code-review.md) | Review a patch for defects, regressions, complexity, and missing tests |
| [Documentation audit](playbooks/docs-audit.md) | Run a fresh whole-docs consistency, Diátaxis, generated-reference, terminology, coverage, and live-link audit |
| [Documentation review](playbooks/docs-review.md) | Check Diátaxis placement, links, indexing, and terminology |
| [ExecPlan](playbooks/exec-plan.md) | Author and run a self-contained living plan for a complex, multi-hour task |
| [Release](playbooks/release.md) | Start, manage, or cut a release using the GitHub-first release model |
| [Security review](playbooks/security-review.md) | Review trust boundaries, secrets, input handling, and write authority |
| [Verify a change](playbooks/verify-change.md) | Demonstrate that changed behavior works and relevant regressions are covered |

## Templates

| Template | Use |
|---|---|
| [Agent handoff](templates/handoff.md) | Transfer a bounded task without relying on chat history |
| [ExecPlan](templates/exec-plan.md) | Skeleton for a complex task's self-contained living plan (instances live on the `scratch` branch under `releases/<version>/`) |
| [Release plan](templates/release-plan.md) | Draft body for release parent issues and checkpoint prose |
| [Review report](templates/review-report.md) | Report findings first with evidence and residual risk |

## System maps

| Map | Use |
|---|---|
| [Source-of-truth map](system/source-of-truth-map.md) | Find the file that owns each repository contract |
| [Change-impact map](system/change-impact-map.md) | Identify consumers and focused checks for a changed area |
| [Test selection](system/test-selection.md) | Choose focused tests, the full gate, and runtime-dependent verification |

## Maintenance rules

- Keep procedures portable across Codex, Claude Code, Hermes, and other agents.
- Let installed skills and plugins own generic agent methods. Use `.agents/`
  only for Memoria-specific routing, paths, checks, templates, and tool-neutral
  adapters.
- Do not put secrets, runtime state, task tracking, or tool-specific settings here.
- Do not duplicate architecture or product documentation from `docs/`.
- Prefer repository commands such as `python3 scripts/verify` over hand-written command lists.
- Keep examples generic; never include real API keys, profile `.env` values, or runtime-vault content.
- Regenerate derived maps with `python3 scripts/checks/agents_doctor.py --write`.
