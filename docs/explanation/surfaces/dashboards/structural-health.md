---
title: Structural health
parent: Surfaces and dashboards
nav_order: 3
grand_parent: Surfaces
permalink: /explanation/surfaces/dashboards/structural-health/
---

# Structural health

Structural-health data ships through linter output, file-backed attention, and
request/attention reads. Planned adapter views may group that data into drift,
loose ends, Board state, and a weekly maintenance agenda.

## Drift watch

The planned Drift watch combines linter findings with open `flag` and `alert`
attention items created by separately invoked integrity and verification
operations. The linter reports severity-ranked findings; it does not write
attention prompts. The view would keep those inputs distinct while prioritizing
urgent work in the rail health band.

It is not the audit log or eval trend. Those are operational evidence; a Drift
watch would be the structural layer over detectable integrity findings.

## Loose ends

The planned Loose ends view is a weekly batch for `notice`-loudness `flag`
attention items: batching keeps low-urgency findings out of the daily signal
without letting them vanish. The shipped weekly review considers those items
alongside Linter findings; louder findings carry greater urgency.

## Board state

Request and attention state are exposed by the standalone runtime. A planned
Board view may combine those reads while staying read-only — an editable
board would become a second authoring surface for state the runtime owns.

## Weekly review

Weekly review is the operator-run structural-health ritual. It relates Inbox
cleanup, linter output, new content, and claim state. The task steps live in
[Run the weekly review](../../../how-to-guides/inbox/run-the-weekly-review.md).

## Related

- Availability and backing surfaces: [Dashboards](../../../reference/analysis-and-surfaces/dashboards.md)
- Detector severity reference: [Linter: detectors and auto-fix](../../../reference/analysis-and-surfaces/linter.md)
- The `flag`/`alert` attention-projection types: [Glossary](../../../reference/data-model/glossary.md)
- The `quiet`/`notice`/`alert`/`block` loudness levels: [Architecture — Interaction channels](../../architecture/README.md#interaction-channels)
