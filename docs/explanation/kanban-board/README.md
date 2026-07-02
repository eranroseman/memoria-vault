---
title: Request control plane
parent: Explanation
nav_order: 5
has_children: true
permalink: /explanation/kanban-board/
---

# The request control plane

Alpha.14's control plane is the operation request table in
`.memoria/memoria.sqlite`, surfaced through the `memoria request`,
`memoria workspace`, and `memoria attention` commands. A CLI command, an
observed file change, or an operator-managed scheduled job creates the same kind
of durable request row; the worker runs it; the result resurfaces as an
attention signal when the PI needs to decide something.

Old profile and lane names survive only as operation-posture vocabulary. Intake,
extraction, linking, mapping, and verification are capability-backed operations
with request rows and manifest ceilings, not shipped Hermes lanes or installed
profile packages; see [Operation postures](../profiles/README.md) and
[Operations](../operations.md).

The central design move is still to keep three dimensions separate: execution
status, PI-facing attention state, and any machine recommendation. A worker
finishing never silently becomes human approval. Why those dimensions stay
separate is developed in [Request states and the review gate](states.md); the
current command lookup is in the [Kanban board reference](../../reference/kanban-board.md),
which now records the no-Hermes-board alpha.14 contract. A request is *work*
(transient, closed when done); a vault note is *knowledge* (durable).

## Documents in this section

| Page                                                          | What it covers                                                                                                                                                                          |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Request states and the review gate](states.md)                 | What a request carries; why execution, review, and PI-facing attention state are separate; and why rejected work gets a new request. |
| [The honesty prompt](honesty-card.md)                            | The attention prompt the PI actually reads: argument for, argument against, what tipped it, certainty, and no automatic verdict on proposals.               |
| [Decision points](decision-points.md)                         | Approval gates, work prompts, batch worklists, and automated steps. |
| [How old board surfaces map to alpha.14](obsidian-projection.md)  | The optional editor/board projection boundary and why the CLI/engine remains authoritative. |
| [WIP limits and back-pressure](wip-limits.md)                 | Why request concurrency and review caps intentionally slow work before review quality degrades. |

For the current control-plane command lookup, see the
[Kanban board reference](../../reference/kanban-board.md).

## Related

**Explanation**

- Why review is structural: [Why the review gate is structural](../../design/why-review-gate-is-structural.md)
- The decision model behind attention prompts: [Decision points](decision-points.md)
- The Inbox card types: [Document types and epistemic roles](../knowledge/document-types.md)

**Dashboards**

- The Inbox board view: [The board-state dashboard](../dashboards/daily-glance.md#board-state-support)
