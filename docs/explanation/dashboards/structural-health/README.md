---
title: Structural health
parent: Dashboards
nav_order: 3
grand_parent: Explanation
permalink: /explanation/dashboards/structural-health/
---

# Structural health

Views that surface drift, loose ends, board state, and the weekly maintenance agenda — the *Linter operation's* structural debt plus the worker-board view. The Maintenance collection (`spaces/maintenance.md`) is the rail target for this cadence. The synthesis-agenda group is the PI's unfinished thinking; the actor-split rationale is in [Dashboards](../README.md).

| View | Question it answers |
|---|---|
| Maintenance collection | Which weekly structural-debt views should I review together? |
| Drift watch | What drift have the Linter and the sweeps detected — which `flag`/`alert` cards are open? |
| Loose ends | Which `notice`-loudness `flag` findings are batched for the weekly pass? |
| Board state | What work is in flight below the action queue? |
| Weekly review | What Friday sequence keeps Inbox, Maintenance, and Knowledge from aging? |

## Drift watch

Drift watch is the structural view over open `flag` and `alert` cards produced by
the Linter and verification sweeps. It sorts loudest-first and feeds the rail
health band.

It is not audit-log or fleet-health. Those are operational views; Drift watch is
the structural layer over detectable integrity findings.

## Loose ends

Loose ends is the weekly batch for `notice`-loudness `flag` cards. Louder findings
belong higher in Drift watch; Notice findings wait here so daily work stays quiet
without losing the debt.

## Board state

Board state is the full maintenance/debugging view over the Inbox board and worker
projections. Use it when the Inbox Activity strip is too compact and you need to
see what Hermes is executing underneath.

## Weekly review

Weekly review is the scheduled structural-health pass. It gathers Inbox cleanup,
Maintenance, new content, and claim state into one deliberate rhythm. The
step-by-step ritual lives in [Run the weekly
review](../../../how-to-guides/inbox/run-the-weekly-review.md).

## Related

- Exact shipped surfaces: [Dashboards](../../../reference/dashboards.md)
- Detector severity reference: [Linter: detectors and auto-fix](../../../reference/linter.md)
- The card format behind `flag` and `alert`: [The honesty card](../../kanban-board/card-schema.md)
