---
title: Request control plane
parent: Execution
grand_parent: Explanation
nav_order: 30
permalink: /explanation/execution/control-plane/
---

# The request control plane

The control plane is the durable request-and-attention layer between PI intent
and worker execution. A CLI command, an observed file change, or an
operator-managed scheduled job creates the same kind of durable request; the
worker runs it; the result resurfaces as attention when the PI needs to decide
something.

Old profile and lane names survive only as operation-posture vocabulary. Intake,
extraction, linking, mapping, and verification are capability-backed operations
with request rows and manifest ceilings, not shipped Hermes lanes or installed
profile packages; see [Operation postures](../operation-postures/README.md) and
[Operations](../operations.md).

The central design move is still to keep three dimensions separate: execution
status, PI-facing attention state, and any machine recommendation. A worker
finishing never silently becomes a PI disposition. Why those dimensions stay
separate is developed in [Request states and the review gate](states.md); the
current command lookup is in the [Control plane reference](../../../reference/control-plane.md).
A request is *work*
(transient, closed when done); a vault note is *knowledge* (durable).

## Documents in this section

| Page | What it covers |
| --- | --- |
| [Request states and the review gate](states.md) | Why execution, review, and PI-facing attention state are separate. |
| [The honesty prompt](honesty-card.md) | Why attention prompts provide decision material instead of verdicts. |
| [Decision points](decision-points.md) | Why review gates, work prompts, batch worklists, and automated steps differ. |
| [WIP limits and back-pressure](wip-limits.md) | Why request concurrency and review caps intentionally slow work. |

For the current control-plane command lookup, see the
[Control plane reference](../../../reference/control-plane.md).

## Related

**Explanation**

- Why review is structural: [Why the review gate is structural](../../../design/boundaries/why-review-gate-is-structural.md)
- The decision model behind attention prompts: [Decision points](decision-points.md)
- Attention projections and retired Inbox-card schema: [Inbox card fields](../../../reference/inbox-card-fields.md)

**Dashboards**

- The Inbox board view: [The board-state dashboard](../../surfaces/dashboards/daily-glance.md#board-state-support)
