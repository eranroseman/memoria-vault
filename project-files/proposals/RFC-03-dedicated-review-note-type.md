---
topic: proposals
id: RFC-03
title: Dedicated review-note type
status: deferred
created: 2026-05-15
---

# RFC-03: Dedicated review-note type

## What

A `review-note` type that stores reviewer judgments with provenance, separate from the note being reviewed — giving every review decision a durable, queryable home.

## Why

Review provenance today lives on the board card (`review_status`, `reviewed_at`, handoff `summary`) and in the audit log. Once a card closes, its review history is not directly browsable as notes.

## Trade-offs

- Adds another note type to the schema for a benefit not currently felt.
- A parallel review-note tree to maintain alongside the card/audit record.

## Adoption trigger

An audit requirement emerges that needs persistent, browsable review records outliving the board card.

## Guard

Do not add the type speculatively: the card fields plus the audit log already carry the data for the current single-user workflow, so adoption is cheap to defer and straightforward later (the data is already captured).

## Alternatives considered

**Adopt now.** Rejected: adds a note type for an unfelt benefit.

**Query the audit-log JSONL directly** (no new type). The current approach; works for now.

## Related

- **See also:** [kanban-board/README.md](../../docs/explanation/kanban-board/README.md) (existing `review_status` semantics).
- **Files:** none currently.
