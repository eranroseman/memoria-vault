---
topic: decisions
id: 07
title: Code agent attachment
status: accepted
date_proposed: 2026-05-15
date_resolved: 2026-05-15
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 7
---

# ADR-07: Code agent attachment

## Context

Does the Coder profile delegate substantive coding work to an external coding agent (Kilocode, Aider, Claude Code, Codex), or implement coding capabilities itself?

## Decision

**Delegate.** The Coder profile scaffolds `code-note` handoffs with vault context (motivating sources, project links, purpose) and coordinates the review gate. The actual code editing happens in a specialized external agent running as a peer with a shared filesystem. The full setup pattern lives in [create a code artifact](../how-to-guides/compose/create-a-code-artifact.md).

> **Current vs. planned agents.** The shipped Coder lane wires **`codex` and `claude-code`** as the current external coding agents (`opencode` also available) — the real Hermes `autonomous-ai-agents` skill IDs in [Coder SOUL](../../src/.memoria/profiles/memoria-engineer/SOUL.md) and `lane-overrides/coder.yaml`. **Kilo Code and Aider are planned future additions**, not yet wired. (`kilocode` today is the Coder's *model provider* in `config.yaml`, distinct from a coding-agent skill.)

## Consequences

- The Coder profile stays narrow (scaffold + document); doesn't accumulate coding complexity it wasn't designed for.
- Human can use whichever coding agent fits the project (Claude Code for unfamiliar codebases, Aider for fast diffs, etc.).
- Adds a tool dependency — the human must install and configure one of the external agents.
- The same parallel-agents-with-shared-filesystem pattern generalizes to rendering agents ([open-design](../how-to-guides/compose/create-a-code-artifact.md)).

## Alternatives considered

**Coder runs code itself** (in-profile execution): rejected because it conflates research-side Hermes (curating provenance) with code-side tools (editing files, running tests). Mixing the two would either bloat the Hermes side with redundant coding capabilities or leave the code-side underdeveloped relative to specialized tools.

## Related

- **Workflows affected:** [Code](../how-to-guides/compose/create-a-code-artifact.md)
- **Files affected:** [The Coder](../explanation/profiles/coder.md), [create a code artifact](../how-to-guides/compose/create-a-code-artifact.md), `99-system/templates/code-note.md` (in the starter vault)
