---
topic: decisions
id: 36
title: Dedicated review-note type
status: superseded
folded_into: memoria-redesign  # subsumed by the Inbox review-request type (D6)
assumes: []
date_proposed: 2026-05-15
parent: Decisions
grand_parent: Explanation
nav_order: 36
---

# ADR-36: Dedicated review-note type

## What

A `review-note` type that stores reviewer judgments with provenance, separate from the note being reviewed — giving every review decision a durable, queryable home.

## Why

Review provenance today lives on the board card (`review_status`, `reviewed_at`, handoff `summary`) and in the audit log. Once a card closes, its review history is not directly browsable as notes.

## Trade-offs

- Adds another note type to the schema for a benefit not currently felt.
- A parallel review-note tree to maintain alongside the card/audit record.

## When this matters

An audit requirement emerges that needs persistent, browsable review records outliving the board card.


## Alternatives considered

**Adopt now.** Rejected: adds a note type for an unfelt benefit.

**Query the audit-log JSONL directly** (no new type). The current approach; works for now.

## Related

- **See also:** [Kanban board](../explanation/kanban-board/README.md) (existing `review_status` semantics).
- **Files:** none currently.
