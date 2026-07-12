# AGENTS.md — Memoria

Facts for AI agents working in `eranroseman/memoria-vault`. *How* work happens
is owned by the installed superpowers skills (brainstorm → plan → TDD/SDD →
review → finish), not by this file. Human contributors: see
[CONTRIBUTING.md](CONTRIBUTING.md).

## What Memoria is

An opinionated, phase-gated, personal knowledge-production tool — a durable
research vault for one researcher who owns all judgment. Sources enter the
**catalog**, become connected claims in **Knowledge Bundles** (a Toulmin
argument graph parallel to the catalog graph), and drive to output in
**Projects**. Built on Karpathy's LLM-Wiki (inflow) and Luhmann's Zettelkasten
(topology), with Toulmin (logic) and autoresearch (self-improvement), expanded
with agentic capabilities. All trust is placed in inspectable grounding
structure, never in any author — human or machine — which is what reserves
judgment to the one human. It should feel like a co-PI, not a knowledge base.

## Ground truth

- **Correctness command:** `python scripts/verify` (lint, product gates, tests,
  offline smoke, syntax). It is the one gate; `main` requires a PR plus the
  `verify` and `gitleaks` checks.
- **Merge** by squash. No required commit-message format (Conventional Commits
  earns back with release tooling).
- **Sessions each work in their own worktree.** The git index is shared per
  checkout, so two sessions in one checkout can sweep each other's staged files
  into a commit — stage explicit paths, never `git add -A`.
- **Test only against disposable vaults under `test-vault/`** (never a personal
  vault). The installed test-vault carries its own nested `.git` (vault
  versioning is product behavior) and must stay reconstructible — `git clean
  -fdx` destroys it.
- **Obsidian** is seeded by `memoria init` unless `--no-obsidian`; it is not
  required. Zotero, MCP hosts, and external editors are optional adapters.
- **When layers disagree, trust order is schema → tests → code → docs.**

## Code shape

- The smallest change that solves the problem; no speculative abstractions or
  unrequested flexibility. Match the existing style.
- Tests attach to agreed interfaces/seams, not incidental internals.
- Present options with pros/cons and a recommendation — never a bare list.
- Any addition must name the expensive, recurring failure it prevents; prefer
  deletion > mechanism > rule > checker.

## Where things live

- `docs/` describes the current system (published to GitHub Pages, Diátaxis-
  structured: tutorials / how-to / reference / explanation); its repo-specific
  authoring conventions live in `docs/README.md`. `design-history/` is the frozen
  record of how it got there. `docs/superpowers/` holds working specs and plans
  (tracked, not published).
- Backlog and readiness live in GitHub issues and milestones (a milestone is a
  release) — no separate status/readiness fields, no release parent-issue ceremony.

## Cross-tool parity (Codex, Kilo)

Codex and Kilo read this file natively. Two justified asymmetries, same outcome
by platform-appropriate mechanism:

- **Security review:** Claude runs it through always-on security-guidance hooks;
  Codex has no passive-hook equivalent, so it runs an explicit `codex-security`
  scan on installer or runtime-policy changes.
- **Write perimeter:** Claude via native permission prompts and bash sandboxing;
  Codex via the sandbox's `writable_roots`.

`CLAUDE.md` is a loader (`@AGENTS.md`) with no content of its own.
