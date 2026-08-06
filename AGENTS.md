# AGENTS.md — Memoria

Facts for AI agents working in `eranroseman/memoria-vault`. *How* work happens
is owned by the installed superpowers skills (brainstorm → plan → TDD/SDD →
review → finish), not by this file. Human contributors: see
[CONTRIBUTING.md](CONTRIBUTING.md).

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
  paths, never `git add -A`; see Cross-tool parity for per-tool isolation.
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

## Parallel delegation

Multi-step task: name independent subtasks, dispatch subagents in parallel.
Pattern: `superpowers:dispatching-parallel-agents`.

## Where things live

- `docs/` describes the current system (published to GitHub Pages, Diátaxis-
  structured: tutorials / how-to / reference / explanation); its repo-specific
  authoring conventions live in `CONTRIBUTING.md` ("Documentation authoring
  conventions"). `design-history/` is the frozen record of how it got there.
  `docs/superpowers/` holds working specs and plans (tracked, not published).
- Backlog and readiness live in GitHub issues and milestones (a milestone is a
  release) — no separate status/readiness fields, no release parent-issue ceremony.
- Canonical term definitions live in `docs/reference/data-model/glossary.md`
  (one definition per term, usage rulings included) — read it before naming
  things, add new rulings there, and never start a second glossary. Root
  `CONTEXT.md` is a pointer stub routing to it (and back here) for tools that look for that file by
  convention.

## Cross-tool parity (Codex, Kilo)

Codex and Kilo read this file natively. Justified asymmetries, platform-
appropriate mechanism per case:

- **Security review:** Claude runs it through always-on security-guidance hooks;
  Codex has no passive-hook equivalent, so it runs an explicit `codex-security`
  scan on installer or runtime-policy changes.
- **Write perimeter:** Claude via native permission prompts and bash sandboxing;
  Codex via the sandbox's `writable_roots`.
- **Session isolation:** Codex isolates each session in its own worktree by
  default, under `.worktrees/`; Claude has to run `git worktree add
  .claude/worktrees/<name> -b wip/<name> origin/main`, then
  `EnterWorktree(path: ".claude/worktrees/<name>")` before editing. Both
  directories are gitignored and both stay — two tools' live working areas.
  The split is forced: Claude Code manages only `.claude/worktrees/`, and
  `EnterWorktree` anywhere else raises a `safetyCheck` prompt that cannot be
  pre-approved. Create new worktrees from the main checkout — `EnterWorktree`
  refuses to create one from inside another worktree (switching into an
  existing managed worktree by `path` is allowed).
- **Claude-side repo policy:** the checked-in `.claude/settings.json` carries
  what AGENTS.md promises about Claude sessions — the process spine
  (superpowers, pinned) and security-guidance enablement, a recurring-safe-
  command allowlist, and a `PreToolUse` hook
  (`.claude/hooks/block-git-add-all.py`) that rejects unbounded staging per the
  shared-index rule above. Codex needs no equivalent: its default worktree
  isolation gives each session a private index.

`CLAUDE.md` is a loader (`@AGENTS.md`) with no content of its own.
