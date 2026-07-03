---
title: Structural health
parent: Surfaces and dashboards
nav_order: 3
grand_parent: Explanation
permalink: /explanation/dashboards/structural-health/
---

# Structural health

Views that surface drift, loose ends, board state, and the weekly maintenance agenda — the *Linter operation's* structural debt plus the worker-board view. The Maintenance collection (`spaces/maintenance.md`) is the rail target for this cadence. The synthesis-agenda group is the PI's unfinished thinking; the actor-split rationale is in [Surfaces and dashboards](README.md).

| View | Question it answers |
|---|---|
| Maintenance collection | Which weekly structural-debt views should I review together? |
| Drift watch | What drift have the Linter and the sweeps detected — which `flag`/`alert` attention items are open? |
| Loose ends | Which `notice`-loudness `flag` findings are batched for the weekly pass? |
| Board state | What work is in flight below the action queue? |
| Weekly review | What Friday sequence keeps Inbox, Maintenance, and Knowledge from aging? |

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

Board state is the full maintenance/debugging view over the Inbox board and worker
projections. Use it when the Inbox Activity strip is too compact and you need to
see runtime queue projections underneath.

## Weekly review

Weekly review is the scheduled structural-health pass. It gathers Inbox cleanup,
Maintenance, new content, and claim state into one deliberate rhythm. The
step-by-step ritual lives in [Run the weekly
review](../../how-to-guides/inbox/run-the-weekly-review.md).

## Related

- Exact shipped surfaces: [Dashboards](../../reference/dashboards.md)
- Detector severity reference: [Linter: detectors and auto-fix](../../reference/linter.md)
- The attention prompt format behind `flag` and `alert`: [The honesty prompt](../kanban-board/honesty-card.md)
