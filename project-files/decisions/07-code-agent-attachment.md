---
topic: decisions
id: 07
title: Code agent attachment
status: accepted
date_proposed: 2026-05-15
date_resolved: 2026-05-15
supersedes: []
superseded_by: []
---

# ADR-07: Code agent attachment

## Context

Does the Coder profile delegate substantive coding work to an external coding agent (Kilocode, Aider, Claude Code, Codex), or implement coding capabilities itself?

## Decision

**Delegate.** The Coder profile scaffolds `code-note` handoffs with vault context (motivating sources, project links, purpose) and coordinates the review gate. The actual code editing happens in a specialized external agent running as a peer with a shared filesystem. The full setup pattern lives in [create a code artifact](../../docs/how-to-guides/writing/create-a-code-artifact.md).

> The agents named in the Context above (Kilocode, Aider, …) were the decision-time *candidates*. The shipped Coder lane allows **`claude-code`, `codex`, `opencode`** — see [memoria-coder SOUL.md](../../vault/.memoria/profiles/memoria-coder/SOUL.md) for the current set.

## Consequences

- The Coder profile stays narrow (scaffold + document); doesn't accumulate coding complexity it wasn't designed for.
- Human can use whichever coding agent fits the project (Claude Code for unfamiliar codebases, Aider for fast diffs, etc.).
- Adds a tool dependency — the human must install and configure one of the external agents.
- The same parallel-agents-with-shared-filesystem pattern generalizes to rendering agents ([open-design](../../docs/how-to-guides/writing/create-a-code-artifact.md)).

## Alternatives considered

**Coder runs code itself** (in-profile execution): rejected because it conflates research-side Hermes (curating provenance) with code-side tools (editing files, running tests). Mixing the two would either bloat the Hermes side with redundant coding capabilities or leave the code-side underdeveloped relative to specialized tools.

## Related

- **Workflows affected:** [Code](../../docs/how-to-guides/writing/create-a-code-artifact.md)
- **Files affected:** [profiles/coder.md](../../docs/explanation/profiles/coder.md), [create a code artifact](../../docs/how-to-guides/writing/create-a-code-artifact.md), `00-meta/03-templates/code-note.md` (in the starter vault)
