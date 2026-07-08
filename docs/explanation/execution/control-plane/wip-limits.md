---
title: WIP limits and back-pressure
parent: Request control plane
grand_parent: Execution
nav_order: 4
---

# WIP limits and back-pressure

Back-pressure exists to make overload visible before it becomes rubber-stamping.
In the standalone baseline, concurrency belongs to the engine/runner and to any
operator-managed scheduler that invokes it. The current reference records that
external-board WIP caps are not a baseline control:
[Control plane reference](../../../reference/control-and-policy/control-plane.md#wip-limits).

## Why collision domains still matter

Parallel runs that write the same output family would contend for the same write
scope and make the audit trail ambiguous about which request touched which file.
The design principle is to keep each write attributable to one request; exact
runtime concurrency rules belong to the worker/runner contract and reference.

The same pressure applies to idempotent-but-not-output-stable work such as source
ingest: repeated runs may refresh metadata, but they should not race each other.

## Why review pressure must stay visible

The bottleneck is human attention, not machine capacity. If completed prompts
pile up faster than the PI can review them, "reviewed" quietly turns into "machine
finished." The design goal is visible pressure: dashboards, attention views, and
weekly review make overload explicit instead of letting machine output silently
accumulate.

That visibility is the point. A visible bottleneck is better than an invisible
loss of review quality.

## Why draft-work should stay bounded

Too many drafts in flight lowers synthesis quality because evidence cannot be
integrated across parallel compositions. The practice is to keep draft work
bounded even when the runtime can queue more requests; this protects argument
quality, not throughput.

## Related

- State-machine explanation: [Request states and the review gate](states.md)
- Control plane commands: [Control plane reference](../../../reference/control-and-policy/control-plane.md)
- Why review remains human-owned: [Why the review gate is structural](../../rationale/boundaries/why-review-gate-is-structural.md)
