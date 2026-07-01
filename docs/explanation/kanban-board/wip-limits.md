---
title: WIP limits and back-pressure
parent: Kanban board
grand_parent: Explanation
nav_order: 5
---

# WIP limits and back-pressure

The board's WIP limits exist to make overload visible before it becomes
rubber-stamping. In the Hermes adapter, Hermes owns the dispatcher and the card
states; Memoria sets caps that protect auditability, human review, and synthesis
quality. Exact cap values live in the [Kanban board reference](../../reference/kanban-board.md#wip-limits).

## One running card per lane

Parallel runs of the same background agent would contend for the same write
scope and make the audit trail ambiguous about which run touched which file.
One `running` card per lane keeps each write attributable to one card.

This also serializes idempotent-but-not-output-stable work such as source
ingest: repeated runs may refresh metadata, but they should not race each other.

## Review queue cap

The bottleneck is human attention, not machine capacity. If completed cards pile
up faster than the PI can review them, "reviewed" quietly turns into "agent
finished." The review cap creates back-pressure: when the review queue is full,
new work slows until the PI clears the queue.

That delay is the point. A visible bottleneck is better than an invisible loss of
review quality.

## Writer lane bound

Too many drafts in flight lowers synthesis quality because evidence cannot be
integrated across parallel compositions. The Writer cap protects argument
quality, not throughput.

## Related

- State-machine explanation: [Board states and the review gate](states.md)
- Exact caps and lane assignments: [Kanban board reference](../../reference/kanban-board.md)
- Why review remains human-owned: [Why the review gate is structural](../../design/why-review-gate-is-structural.md)
