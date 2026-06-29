---
topic: decisions
id: 07
title: Code agent attachment
nav_exclude: true
status: accepted
date_proposed: 2026-05-15
date_resolved: 2026-05-15
assumes: []
supersedes: []
superseded_by: []
---

# ADR-07: Code agent attachment

## Context

> *Note (0.1.0-alpha.2): "Coder" below is the profile's original name — [ADR-48](48-copi-and-agent-consolidation.md) renamed it the **Engineer** (`memoria-engineer`, lane-override `engineer.yaml`). The delegate-don't-implement decision is unchanged.*

Does the Coder profile delegate substantive coding work to an external coding agent (Kilocode, Aider, Claude Code, Codex), or implement coding capabilities itself?

## Decision

**Delegate.** The Coder profile scaffolds `code-note` handoffs with vault context (motivating sources, project links, purpose) and coordinates the review gate. The actual code editing happens in a specialized external agent running as a peer with a shared filesystem. The current lane context lives in [The Engineer](../explanation/profiles/engineer.md).

> **Current vs. planned agents.** The shipped Engineer lane wires **`codex` and `claude-code`** as the current external coding agents — the agent IDs referenced in `memoria-engineer/distribution.yaml` (env keys per agent), with the lane scoped by `lane-overrides/engineer.yaml`. **Kilo Code and Aider are planned future additions**, not yet wired. (`kilocode` today is the Engineer's *model provider* in `config.yaml`, distinct from a coding-agent skill.)

## Consequences

- The Coder profile stays narrow (scaffold + document); doesn't accumulate coding complexity it wasn't designed for.
- Human can use whichever coding agent fits the project (Claude Code for unfamiliar codebases, Aider for fast diffs, etc.).
- Adds a tool dependency — the human must install and configure one of the external agents.
- The same parallel-agents-with-shared-filesystem pattern generalizes to rendering agents.

## Alternatives considered

**Coder runs code itself** (in-profile execution): rejected because it conflates research-side Hermes (curating provenance) with code-side tools (editing files, running tests). Mixing the two would either bloat the Hermes side with redundant coding capabilities or leave the code-side underdeveloped relative to specialized tools.

## Related

- **Workflows affected:** code handoff through the [Engineer](../explanation/profiles/engineer.md)
- **Files affected:** [The Coder](../explanation/profiles/engineer.md), `99-system/templates/code-note.md` (in the starter vault)
