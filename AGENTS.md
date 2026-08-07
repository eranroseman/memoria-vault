# AGENTS.md — Memoria

Facts for AI agents working in `eranroseman/memoria-vault`. *How* work happens
is owned by the installed superpowers skills (brainstorm → plan → TDD/SDD →
review → finish) and, for issue work, by `/triage` — not by this file.

[CONTRIBUTING.md](CONTRIBUTING.md) is not a human-only file. It holds the craft
this one deliberately does not restate, and those sections bind agents too:
**Coding conventions**, **Documentation authoring conventions**, and the
**Pull requests** checklist. Read them before writing code, docs, or a PR. Its
**Development setup** walkthrough is for human contributors; from **Releases and
changelog**, only the rule against hand-cutting a release or hand-tagging in an
ordinary PR binds agents.

Operating policy — the gate, merge rules, the shared index, where work is
tracked — lives here and only here. When the two files appear to disagree about
policy, this one is right and the other has drifted.

## What Memoria is

An opinionated, phase-gated, personal knowledge-production tool for one
researcher who owns all judgment. Sources enter the **catalog**, become
connected claims in **Knowledge Bundles** (a Toulmin argument graph parallel
to the catalog graph), and drive to output in **Projects**. All trust lives in
inspectable grounding structure, never in any author — human or machine. It
should feel like a co-PI, not a knowledge base. Product pitch:
[README](README.md); intellectual lineage:
[intellectual-foundations](docs/explanation/rationale/foundations/intellectual-foundations.md).

## Ground truth

- **Correctness command:** `python scripts/verify` (lint, product gates, tests,
  offline smoke, syntax). It is the one gate; `main` requires a PR plus the
  `verify` and `gitleaks` checks.
- **Merge** by squash. No required commit-message format (Conventional Commits
  earns back with release tooling).
- **The git index is shared per checkout** — two sessions or subagents in one
  checkout can sweep each other's staged files into a commit. Stage explicit
  paths, never `git add -A`; a `PreToolUse` hook rejects the sweep forms. Each
  session works in its own worktree, created from the main checkout:
  `git worktree add .claude/worktrees/<name> -b wip/<name> origin/main`, then
  `EnterWorktree(path: ".claude/worktrees/<name>")`. Codex does this by
  default. Per-tool differences: `docs/agents/cross-tool-parity.md`.
- **Test only against disposable vaults under `test-vault/`** (never a personal
  vault). The installed test-vault carries its own nested `.git` (vault
  versioning is product behavior) and must stay reconstructible — `git clean
  -fdx` destroys it.
- **Obsidian** is seeded by `memoria init` unless `--no-obsidian`. Zotero, MCP
  hosts, and external editors are optional adapters.
- **When layers disagree, trust order is schema → tests → code → docs.**

## Code shape

- The smallest change that solves the problem; no speculative abstractions or
  unrequested flexibility. Match the existing style.
- Tests attach to agreed interfaces/seams, not incidental internals.
- Present options with pros/cons and a recommendation — never a bare list.
- Any addition must name the expensive, recurring failure it prevents; prefer
  deletion > mechanism > rule > checker.
- Every plan task carries a verification step — a command and its expected
  result — ahead of the step that changes anything. `main` moves faster than
  plans are authored, so a task whose premises aren't re-checked at execution
  time is the one that ships a stale one.

## Where things live

- `docs/` describes the current system (published to GitHub Pages, Diátaxis-
  structured: tutorials / how-to / reference / explanation); its repo-specific
  authoring conventions live in `CONTRIBUTING.md` ("Documentation authoring
  conventions"). `design-history/` is the frozen record of how it got there.
  `docs/superpowers/` holds working specs and plans (tracked, not published).
- Backlog lives in GitHub issues. A milestone marks intended-release scope
  when one is set — not every release gets one; the frozen `design-history/`
  chapter is the per-release record. No separate status/readiness fields; the
  labels in "Issue conventions" below record owner-gated facts and feed the
  derived pull query — they are not a stored readiness verdict. No release
  parent-issue ceremony.
- Canonical term definitions live in `docs/reference/data-model/glossary.md`
  (one definition per term, usage rulings included) — read it before naming
  things, add new rulings there, and never start a second glossary. Root
  `CONTEXT.md` is a pointer stub routing to it (and back here) for tools
  that look for that file by convention. ADRs live in `docs/adr/`, written
  when a decision resolves rather than scaffolded ahead of one.
- The engineering skills read their per-repo configuration from
  `docs/agents/`: `issue-tracker.md`, `triage-labels.md`, `domain.md`
  (single-context), and `cross-tool-parity.md`.

## Issue conventions

The tracker runs the `triage` skill's state machine. Readiness is authored
rather than derived, but only by a triage session that checks the request
isn't already built, verifies the claim, and attaches a durable brief — so the
label indexes real work instead of restating facts GitHub already tracks.

- **Labels.** A triaged issue carries exactly one **category** role (`bug`,
  `enhancement`) and exactly one **state** role (`needs-triage`, `needs-info`,
  `ready-for-agent`, `ready-for-human`, `wontfix`) — meanings in
  `docs/agents/triage-labels.md`. Two state roles is a defect: flag it and ask,
  never guess which wins. Category goes in labels, never in a title prefix. An issue
  that has not been triaged carries no role at all — a meaningful state, and the first
  bucket `/triage` surfaces. The vocabulary is closed: those roles plus
  `documentation` and the Dependabot labels are the whole set, with no priority
  or severity tier on top.
- **Filing.** Significant changes — new operation surfaces, installer
  overhauls, schema changes, provider integrations, architecture decisions —
  get an issue before the work starts. Small docs, typo, script, and test fixes
  can go straight to a PR.
- **Frontier** — the issues an agent may start right now, and the only ones:
  `ready-for-agent`, unassigned, unblocked.
  `gh issue list --state open --limit 500 --label ready-for-agent --search 'no:assignee'`,
  then drop rows whose `issue_dependencies_summary.blocked_by` is nonzero
  (`gh api repos/{owner}/{repo}/issues/N`). The label is a triage-time verdict;
  assignee and blockers are read live, so they catch what changed after triage.
  GitHub's search index lags writes by seconds — after a batch label change,
  confirm a `--search` count with per-issue reads.
- **Intake.** Before filing, search open issues and closed `wontfix` issues
  by glossary concept, not just by wording. Bodies cite symbols
  (`file.py::function`) and commit shas — never bare line numbers or plan
  task IDs; both rot. The same rule governs briefs: a brief may sit in
  `ready-for-agent` for weeks, so it states interfaces and behavioral
  contracts, not file paths.
- **Claim.** An agent working an issue assigns itself as its first write,
  before any other change (`gh issue edit N --add-assignee @me`); unassigned
  = unclaimed, first writer wins. Every agent session authenticates as the
  same GitHub identity, so the assignee field marks an issue claimed — it
  does not identify which session holds the claim. Unassign your own claim on
  abandonment; do not remove another session's assignment on suspicion of
  staleness — reclaiming an abandoned issue is an owner call.
- **Ordering.** Native `blocked_by` edges only, issue → issue.
- **Decisions.** Resolve as a comment, then close. Term-level rulings also
  land in the glossary.
- **Rejections.** A rejected *enhancement* also gets a `.out-of-scope/<concept>.md`
  entry — one file per concept, appending to its prior-request list rather than
  adding a second file. `/triage` writes it at close and reads it at intake, so
  the same idea is not re-litigated from scratch. Already-implemented requests
  and rejected bugs stay closed issues only; the intake search covers those.

`CLAUDE.md` is a loader (`@AGENTS.md`) with no content of its own.
