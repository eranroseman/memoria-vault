---
topic: decisions
id: 53
title: The pattern library — curated prompt-transformations as data in system/patterns/, one runner
status: accepted
date_proposed: 2026-06-10
date_resolved: 2026-06-10
assumes: [3, 48]
supersedes: []
superseded_by: []
---

# ADR-53: The pattern library — curated prompt-transformations as data in system/patterns/, one runner

## Context

fabric "patterns" and open-notebook "transformations" showed that reusable,
single-purpose prompt-transformations are most of what assist skills do — but
importing those tools wholesale would put ungated LLM calls outside the policy MCP and
adopt a chat-with-docs epistemic model Memoria exists to prevent (D11; folds
[ADR-43](43-skill-governance.md)'s governance intent).

## Decision

Memoria ships a **pattern library**: curated prompt-transformations stored **as
markdown in `system/patterns/`** (visible, git-tracked, lintable — *not* `.memoria/`).
**Patterns are data; one runner executes them all** — "using a pattern" = the runner +
a pattern id; patterns are never individual skills. Each pattern's frontmatter declares
its **posture/agent, mode (Library/Project), action type, input, and `output_target`**;
a shared `_preamble.md` enforces the Memoria voice (your-words, concise,
propose-never-assert, cite-don't-fabricate).

Enforced constraints: a pattern **never writes a gated zone** (output goes to staging,
else the run degrades to dry-run and lint fails); propose-not-dispose; the Linter
validates pattern files against the pattern schema; runs are versioned and
reproducible with per-run provenance. Patterns are themselves gated assets
(human-authored, or agent-proposed → human-approved). The library is seeded by
*adapting* fabric patterns, retargeted to staging. Runner: an in-vault MCP; invocation
via palette · pane · selection; model: per-pattern hint with a global fallback.

## Consequences

- New assist behavior is usually a new markdown file, not new code.
- The runner is one audited chokepoint for every pattern execution (provenance,
  output-target enforcement).
- The pattern-picker is a Base over the library, filtered by current mode/task.
- Curation is a real ongoing duty — a bad pattern is a gated asset to fix, not a prompt
  buried in code.

## Alternatives considered

**Adopt fabric as a dependency.** Its value is the pattern *idea*, not the pipe-CLI;
as a dependency it bypasses the policy MCP. **One skill per pattern.** Explodes the
skill registry and makes governance per-skill instead of per-data-file.
**Chat-with-docs transformations.** The "synthesis without rigor" failure mode; rejected
on epistemics.

## Related

- **Related decisions / Depends on:** [ADR-03](03-structural-review-gate.md),
  [ADR-43](43-skill-governance.md), [ADR-51](51-inbox-category-and-honesty-card.md)
