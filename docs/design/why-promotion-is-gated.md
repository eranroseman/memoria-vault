---
title: Why promotion is gated
parent: Design Book
grand_parent: Developers
nav_order: 28
---

# Why promotion is gated

Promotion makes content canonical. In Memoria, that means a claim, hub, link, or
project thesis now represents a PI decision and downstream work may trust it.
Only the PI can make that transition.

The rule is **propose, not dispose**. Agents and operations can stage proposals;
the PI decides what becomes part of the record. This is not a safeguard bolted
on later. It is what lets the vault remain trustworthy while agents work ahead.

The gate also protects against fake decisions. Some actions are approval gates;
some are work prompts; classification is automated because a human gate there
would be a rubber stamp. High-cardinality review becomes a worklist, not dozens
of cards, because the queue must remain a useful attention signal.

The cost is visible slowness. That is deliberate: a full review queue should
slow the system rather than silently redefine "reviewed" as "agent finished."

## Related

- Operational promotion model: [Promotion and gated zones](../explanation/knowledge/promotion-model.md)
- The structural gate: [Why the review gate is structural](why-human-gate.md)
- Honesty card fields: [The honesty card](../explanation/kanban-board/card-schema.md)
