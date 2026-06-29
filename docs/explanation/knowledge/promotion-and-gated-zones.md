---
title: Promotion and the write boundary
parent: Knowledge
grand_parent: Explanation
nav_order: 4
---

# Promotion and the write boundary

Promotion is the act of making content readable as checked knowledge. In
alpha.11, that means a worker-owned transition into `check_status: checked`
with a journal row. The PI still decides what claims, links, and hub curation
mean; the worker owns the mechanical write boundary.

---

## What "canonical" means now

Canonical readers consume checked Concepts under `catalog/`, `knowledge/`, and
`capabilities/`. Unchecked or quarantined Concepts can exist on disk, but they
do not enter the checked qmd index or Ask path.

Promotion is not a file move. A Concept is born in its type home and stays
there; the boundary is the **state transition** and its trace. Machine writes
stage first, promote through the trusted writer, and record `derived` plus
`check-fired` events. Operation-owned promotions use that operation's
`required_checks`; alpha.11 enforces `memoria-profile` before promotion and
fails closed on an empty or unsupported promotion-check list. PI edits are direct
and then observed/backfilled. Foreign writes are quarantined by scan.

What is deliberately not reintroduced: a per-write approval loop. The PI enters
for direction, curation, direct edits, and high-risk `ask` flags, not as a
rubber stamp on every machine write.

---

## What the flag router hands you

Checks route findings as `act`, `ask`, or `drop`. `act` is a deterministic
reversible worker fix, `ask` surfaces a PI decision, and `drop` records a
low-value finding without interrupting work.

---

## Notes Replace Claim Maturity

The alpha.10 `claim` type and `maturity` ladder are retired. Alpha.11 uses one
`note` type with optional `claim_text`, `evidence_set`, and typed links. A note
is safe to read when it is checked; whether the claim is important is represented
by evidence, links, and hub/project context.

---

## Related

**Explanation**

- The types involved: [Document types and epistemic roles](document-types.md)
- Why state replaced folders: [Lifecycle, not topic — and state, not folders](../../design/lifecycle-over-topic.md)
- The card fields in detail: [The honesty card](../kanban-board/honesty-card.md)
- Approval gates vs work prompts: [Decision points](../kanban-board/decision-points.md)
- The operations behind the boundary: [Operations](../operations.md)

**Decisions**

- [ADR-51](../../adr/51-inbox-category-and-honesty-card.md) — the Inbox category and the honesty card
- [ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md) — approval gates vs work prompts; classify automated; batch worklists
