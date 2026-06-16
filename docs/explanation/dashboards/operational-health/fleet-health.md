---
title: fleet-health dashboard
parent: Operational health
nav_order: 1
grand_parent: Dashboards
---

# `fleet-health` dashboard

Tracks whether the Hermes agent fleet is performing well over time. This dashboard matters once the fleet is doing enough work per week that one stuck card or one runaway loop is hard to spot by eye.

## What it shows

Operational health per lane over time: cost per task, success rate, retry frequency, review latency, PI attention timing, blind re-review sample counts, and the headline **trust score** (0–100). The trust score is the number to read first; the rest are the signals it rolls up or reports alongside it.

The point of a composite is that no single signal dominates: a lane can have a perfect citation-check record yet a low score if its proposal accept rate signals rubber-stamping, and a high accept rate paired with a low success rate still scores low. That is what makes the number a summary of overall lane health rather than a measure of any one metric. The inputs, the band thresholds, and the accept-ratio extremes (both too-high and too-low down-weight the lane) are specified in the [Dashboards](../../../reference/dashboards.md#trust-score-fleet-health) reference.

## What it is not

**Not board-state.** Board-state shows what work is currently in flight. Fleet-health shows the quality and cost of completed work over time.

**Not audit-log or drift-watch.** Fleet-health aggregates completed work into operational trends (trust score is its headline); audit-log is per-decision forensics, and drift-watch is the structural sibling (verdict band is its headline). For the full three-way distinction, see [Operational health](README.md#audit-log-vs-fleet-health-vs-drift-watch).

## When it shows real data

The dashboard and its metrics aggregator ship in `src/` and deploy with the vault. It reads `system/metrics/lane-*-<week>.md`, which the `memoria-metrics` cron computes from `system/logs/`. It shows meaningful data only once weekly fleet volume accumulates — a vault with two runs per week produces statistics that are directional at best. Until volume builds up, board-state and audit-log catch issues directly. Low-volume lane notes are marked `insufficient-data` so the table remains backed by real emitted data without pretending the sample is actionable.

## Related

- [audit-log dashboard](audit-log.md) — per-decision forensics that feed the deny-rate input
- [drift-watch dashboard](../structural-health/drift-watch.md) — structural complement; verdict band is the structural sibling of trust score
- [Dashboards](../../../reference/dashboards.md#trust-score-fleet-health) — trust score formula, inputs, and band definitions
