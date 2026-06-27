---
title: Why the board is a state machine
parent: Design Book
grand_parent: Developers
nav_order: 26
---

# Why the board is a state machine

A research task does not fit a single chat session. Sources are found over days,
synthesis develops over weeks, verification happens in parallel with drafting,
and failures need retry or escalation without losing context. That requires
explicit state, not conversational memory.

A state-machine card says: this task is in this state, assigned to this lane,
with this handoff payload and history. The state is persistent, queryable, and
safe to hand to another profile. If work fails, the card stays put with the
failure recorded. If a human needs to decide, the card waits.

Chat cannot provide the same guarantees:

- It is session-scoped; the next session has to reconstruct the task.
- It has no reliable WIP view.
- It conflates work-in-progress with knowledge worth keeping.
- It makes handoffs depend on retelling context instead of structured payloads.

Routing stays encoded in card metadata and lane overrides. A reasoning
Orchestrator would make routing less auditable, not more capable.

## Related

- Operational board model: [The board as a state machine](../explanation/workflows/board-as-state-machine.md)
- Board state reference: [Kanban board reference](../reference/kanban-board.md)
- Layering rationale: [Why the architecture is layered](why-three-layers.md)
