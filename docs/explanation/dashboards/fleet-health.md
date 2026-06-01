---
title: fleet-health dashboard
parent: Dashboards
---

# `fleet-health` dashboard

Tracks whether the Hermes agent fleet is performing well over time. This dashboard matters once the fleet is doing enough work per week that one stuck card or one runaway loop is hard to spot by eye.

## What it shows

Operational health per lane over time: cost per task, success rate, retry frequency, latency, and the headline **trust score** (0–100). The trust score is the number to read first; the rest are the signals it rolls up.

The trust score for each lane is a composite of several signals: audit deny rate, structural drift incidents, secret-field access attempts, retry rate, success rate, and — for lanes that produce `[!suggestions]` callouts — accept/reject ratios on those suggestions.

The score is designed so that no single signal dominates, which means a lane can have a perfect citation-check record but a low trust score if its suggestion accept rate signals rubber-stamping. Conversely, a high accept rate combined with a low success rate would still produce a low score. The composite is what makes the number a summary of overall lane health rather than a measure of any one metric.

The suggestion-ratio signal is worth understanding in both directions. A very high accept rate (above ~90%) indicates the human is approving suggestions without reading them — the signal has become noise. A very low accept rate (below ~20%) indicates the candidate scoring algorithm is producing poor candidates that need tuning. Both extremes down-weight the lane score, because both represent a failure of the suggestions mechanism to do useful work.

For the exact band thresholds and the score formula, see [reference/glossary.md](../../reference/glossary.md).

## What it is not

**Not audit-log.** Fleet-health aggregates across many completed writes into trends. The audit log is per-decision forensics.

**Not board-state.** Board-state shows what work is currently in flight. Fleet-health shows the quality and cost of completed work over time.

**Not drift-watch.** Fleet-health is operational (cost, latency, success rates). Drift-watch is structural (Linter structural-detector findings). They are complementary: trust score is the operational headline; verdict band is the structural headline. Both are reproduced from logs without LLM judgment.

## When it shows real data

The dashboard and its metrics aggregator ship with the starter vault. It shows meaningful data only once weekly fleet volume accumulates — a vault with two runs per week produces statistics that are meaningless. Until volume builds up, board-state and audit-log catch issues directly. The dashboard degrades gracefully: it shows explanatory text rather than empty or misleading small-sample tables.

## Related

- [explanation/dashboards/audit-log.md](audit-log.md) — per-decision forensics that feed the deny-rate input
- [explanation/dashboards/drift-watch.md](drift-watch.md) — structural complement; verdict band is the structural sibling of trust score
- [reference/glossary.md](../../reference/glossary.md) — trust score formula and band definitions
