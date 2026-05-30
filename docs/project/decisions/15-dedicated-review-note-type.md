---
topic: decisions
id: 15
title: Dedicated review-note type
status: proposed
date_proposed: 2026-05-15
date_resolved:
supersedes: []
superseded_by: []
---

# ADR-15: Dedicated review-note type

## Context

Add a `review-note` type for storing reviewer judgments with provenance, separate from the reviewed note itself? This would give every review decision a durable, queryable home.

## Decision

**Defer.** The board card's `review_status`, `reviewed_at`, and handoff `summary` carry enough provenance for the current single-user workflow. Add a review-note type only if audit history needs to outlive the card.

## Consequences

- Review provenance lives on the card, not in a parallel note tree.
- Once a card closes, its review history is in the audit log — not directly browsable as notes.
- If a future audit requirement demands persistent review records, adopting the type is straightforward (the card fields already carry the data).

## Alternatives considered

**Adopt now**: rejected — adds a note type to the 15 ([vault/note-types.md](../../reference/note-types.md#note-types)) for a benefit that isn't currently felt.

**Use the audit log directly** (no new type, but query the JSONL more): the current approach. Works for now.

## Related

- **See also:** [kanban-board/README.md](../../explanation/kanban-board/README.md) for the existing review_status semantics
- **Files affected:** none currently
