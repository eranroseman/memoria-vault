---
title: Structural health
parent: Surfaces and dashboards
nav_order: 3
grand_parent: Surfaces
permalink: /explanation/surfaces/dashboards/structural-health/
---

# Structural health

Structural health surfaces drift, loose ends, request state, and the weekly
maintenance agenda: the Linter operation's structural debt plus the
request/attention view. The synthesis-agenda group is the PI's unfinished
thinking; this group is the system's visible maintenance debt.

## Drift watch

Drift watch is the structural view over open `flag` and `alert` attention items
produced by the Linter and verification sweeps. It sorts loudest-first and feeds the rail
health band.

It is not the audit log or eval trend. Those are operational views; Drift watch
is the structural layer over detectable integrity findings.

## Loose ends

Loose ends is the weekly batch for `notice`-loudness `flag` attention items.
Louder findings belong higher in Drift watch; Notice findings wait here so daily
work stays quiet without losing the debt.

## Board state

Board state is the full maintenance/debugging view under the compact Inbox
activity strip. It exists so runtime queue state can be inspected without
turning the daily Inbox into a debugging surface.

## Weekly review

Weekly review is the operator-run structural-health ritual. It gathers Inbox
cleanup, Maintenance, new content, and claim state into one deliberate rhythm.
The step-by-step ritual lives in [Run the weekly
review](../../../how-to-guides/inbox/run-the-weekly-review.md).

## Related

- Exact shipped surfaces: [Dashboards](../../../reference/analysis-and-surfaces/dashboards.md)
- Detector severity reference: [Linter: detectors and auto-fix](../../../reference/analysis-and-surfaces/linter.md)
- The attention prompt format behind `flag` and `alert`: [The honesty prompt](../../execution/control-plane/honesty-card.md)
