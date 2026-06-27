---
topic: decisions
id: 71
title: Structured capture — forms at entry, the Linter as authority, one schema per type
nav_exclude: true
status: accepted
date_proposed: 2026-06-14
date_resolved: 2026-06-14
assumes: [49, 30]
supersedes: []
superseded_by: []
---

# ADR-71: Structured capture — forms at entry, the Linter as authority, one schema per type

## Context

Note creation is template-based free text: there is no form abstraction, so
instructional text leaks into the saved note; there is no per-type required-field
enforcement; and controlled vocabularies (e.g. the lifecycle state) are typed as free
text with no constraint. The deterministic Linter already validates the vault
([ADR-49](49-catalog-in-bases-linter-monitor.md)).

## Decision

Human capture goes through a **form** (the Modal Forms plugin) with typed fields and
**controlled-vocabulary controls** — for a small fixed set such as the lifecycle state
(`proposed`/`current`/`archived`), radio buttons rather than a dropdown — and with help
text living **in the form, not the saved note**.

The **deterministic Linter remains the single enforcement authority**: agents, the API,
and bulk edits all create notes outside any form, so the Linter (not the form) is what
guarantees correctness. Both the form's controlled vocabularies and the Linter's
allowed-value checks **derive from one per-type schema** in `.memoria/schemas/`, so the
two layers cannot diverge. Memoria is **strict, not liberal**: an unknown value for a
fixed-set field is rejected, not coerced.

## Consequences

- Prevention at entry (the form) plus detection everywhere (the Linter) — defense in
  depth, with one schema as the single source of truth.
- Adds Modal Forms as a bundled plugin; capture commands route through it.
- Help text and field labels stop polluting note bodies.
- Enforcement stays where it already lives (the Linter), so no second system of record.

## When this matters

alpha.3 (capture is the core UI loop).

## Alternatives considered

- **Lint-only (status quo).** Detection, not prevention; bad data exists transiently and
  help text leaks into notes.
- **Form-only.** Client-side, therefore bypassable by agents/API/bulk; doesn't cover
  non-form creation paths.
- **In-panel enum widget (e.g. Better Properties).** Gives a native dropdown in the
  Properties panel but is off-store and leans on undocumented Obsidian internals — a
  version-pinned sandbox pilot at most, not a baseline dependency.

## Related

- **Related decisions / Depends on:** [ADR-49](49-catalog-in-bases-linter-monitor.md)
  (the Linter is the integrity authority), [ADR-30](30-deterministic-ingest-pipeline.md)
  (the non-form ingest write path)
- **Implementing issues:** #183 (Obsidian forms for structured capture), #145 (property
  display / lifecycle visibility)
- **Source discussion:** the alpha.3 research notes (`ui-design-research-report` §2,
  `open-issues-research` Issue 4b)
