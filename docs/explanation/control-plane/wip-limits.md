---
title: WIP limits and back-pressure
parent: Request control plane
grand_parent: Explanation
nav_order: 5
---

# WIP limits and back-pressure

Back-pressure exists to make overload visible before it becomes
rubber-stamping. In the standalone engine, request concurrency and review-queue
limits protect auditability, human review, and synthesis quality. The current
alpha.15 reference records that Hermes board WIP caps are not a baseline control:
[Control plane reference](../../reference/control-plane.md#wip-limits).

## One active request per collision domain

Parallel runs that write the same output family would contend for the same write
scope and make the audit trail ambiguous about which request touched which file.
Serializing those collision domains keeps each write attributable to one request.

This also serializes idempotent-but-not-output-stable work such as source
ingest: repeated runs may refresh metadata, but they should not race each other.

## Review queue cap

The bottleneck is human attention, not machine capacity. If completed prompts
pile up faster than the PI can review them, "reviewed" quietly turns into "machine
finished." The review cap creates back-pressure: when the review queue is full,
new work slows until the PI clears the queue.

That delay is the point. A visible bottleneck is better than an invisible loss of
review quality.

## Draft-work bound

Too many drafts in flight lowers synthesis quality because evidence cannot be
integrated across parallel compositions. The draft-work cap protects argument
quality, not throughput.

## Related

- State-machine explanation: [Request states and the review gate](states.md)
- Control plane commands: [Control plane reference](../../reference/control-plane.md)
- Why review remains human-owned: [Why the review gate is structural](../../design/why-review-gate-is-structural.md)
