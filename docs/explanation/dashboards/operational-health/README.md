---
title: Operational health
parent: Dashboards
nav_order: 4
grand_parent: Explanation
has_children: true
permalink: /explanation/dashboards/operational-health/
---

# Operational health

Dashboards that track how the agent fleet is performing and what it decided.

| Dashboard | Question it answers |
|---|---|
| [Fleet health](fleet-health.md) | Are the agents performing well over time? Is cost trending up? |
| [Audit log](audit-log.md) | What did the policy MCP decide, and why? |

## Audit-log vs fleet-health vs drift-watch

Three dashboards sit close together but answer different questions at different layers — keeping them distinct is deliberate:

- **Audit log** is the *raw event stream*: one entry per policy-MCP write decision (per-decision forensics, newest-first).
- **Fleet health** *aggregates* those entries (and other signals) into rolled-up per-lane trend metrics over time — quality and cost of completed work, headlined by the trust score.
- **[Drift watch](../structural-health/drift-watch.md)** is *structural*, not operational: it shows the Linter engine's open integrity findings, headlined by the verdict band — a different cadence and abstraction layer from the other two.

In short: audit-log is per-decision, fleet-health is aggregated-operational, drift-watch is aggregated-structural.
