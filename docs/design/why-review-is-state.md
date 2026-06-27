---
title: Why review is a state
parent: Design Book
grand_parent: Developers
nav_order: 27
---

# Why review is a state

Review has to be machine-readable because it is the system boundary between
"worker finished" and "human accepted." A comment, tag, or verbal confirmation
can express attention; it cannot reliably gate dispatch or policy decisions.

`review_status` keeps review separate from execution state. A card can be
`done` while still waiting for human review, and an agent recommendation can be
`clean` without becoming approval. Those dimensions must be able to disagree.

Making review structured also creates useful back-pressure. A full
done-awaiting-review queue slows new work instead of letting agents produce a
pile of unreviewed artifacts that only look complete. Rejection likewise creates
a fresh card rather than reopening the old one, because a rejected result needs
a new human specification, not a hidden retry loop.

## Related

- Operational review model: [Review as a first-class state](../explanation/workflows/review-as-state.md)
- The structural gate: [Why the review gate is structural](why-human-gate.md)
- Board reference: [Kanban board reference](../reference/kanban-board.md)
