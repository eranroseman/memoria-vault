---
topic: decisions
id: 88
title: Literate code-note
status: proposed
date_proposed: 2026-06-19
date_resolved:
assumes: [47, 57]
supersedes: [58]
superseded_by: []
---

# ADR-88: Literate code-note

## Context

Research code often needs prose explanation beside executable logic. Memoria can
store project code and notes separately today, but it has no first-class note type
that weaves explanation with executable code while checking drift between them.

## Proposal

Memoria may add a `code-note` type that interleaves prose and executable code,
with weave/tangle behavior and Linter checks for code/prose drift. The note is a
research notebook artifact, not a replacement for normal repository source.

## Consequences

- Helps computational-method notes stay executable and explainable.
- Adds a new note type, schema, and drift detector.
- Must avoid blurring the boundary between canonical vault notes and source code
  maintained in a repository.

## When this matters

The human is writing computational-method notes where code and prose regularly
diverge and the divergence is costly to catch manually.

## Alternatives considered

**Keep code in repositories and prose in notes.** Simpler and clear, but makes
small method notebooks awkward.

**Use external notebooks only.** Rejected as the primary path because it moves
method rationale outside the vault's schema and review discipline.

## Related

- **Supersedes:** [ADR-58](58-adjacent-tool-integrations.md).
- **Related decisions / Depends on:** [ADR-47](47-type-first-category-folders.md), [ADR-57](57-engines-write-agents-judge.md).
- **Tracking issue:** [#701](https://github.com/eranroseman/memoria-vault/issues/701).
