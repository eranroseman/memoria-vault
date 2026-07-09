# Code review

Use this playbook for a branch, commit, pull request, or working-tree diff. A
review identifies problems; it does not silently rewrite the patch unless the
user also asks for fixes. Use the installed review skill for generic review
method; this playbook adds Memoria-specific scope, checks, and reporting.

## 1. Scope

1. Read [`AGENTS.md`](../../AGENTS.md).
2. Resolve the exact base and head or local patch being reviewed.
3. Check `git status --short --branch` and list changed files.
4. Read each changed file in full, plus only the supporting code needed to trace
   affected behavior.
5. Treat commit messages and PR descriptions as context, not proof.

When reviewing your own recent work, use `superpowers:requesting-code-review`
for context isolation: give reviewers only the base/head SHAs and requirements,
never your session history. Use [Agent Toolkit](../toolkit.md) for Claude/Codex
review routing.

## 2. Memoria checks

- Use [Source-of-truth map](../system/source-of-truth-map.md) and
  [Change-impact map](../system/change-impact-map.md) to find drift-prone
  consumers.
- For sensitive paths from `AGENTS.md` `pr-policy` tiers, also use
  [Security review](security-review.md).
- For docs, generated maps, release state, issue state, and required-check
  contracts, verify the owner named by `AGENTS.md`, not a mirror.
- Choose checks with [Test selection](../system/test-selection.md), then report
  evidence with [Verify a change](verify-change.md).

## 3. Report

- Use [the review report template](../templates/review-report.md).
- Findings come first, ordered Critical, High, Medium, Low.
- Every finding names an exact file and line, user-visible impact, and evidence.
- Separate confirmed findings from open questions.
- If there are no findings, say so explicitly and state remaining test gaps or
  environmental limitations.
- Do not report personal style preferences unless they create a concrete
  maintenance or correctness risk.
- After presenting findings, use `superpowers:receiving-code-review` when it is
  installed.
