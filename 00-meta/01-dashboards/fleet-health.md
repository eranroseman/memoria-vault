# `fleet-health.md` — operational health

**Location.** `00-meta/01-dashboards/fleet-health.md`

**Status.** Stub — not yet implemented. The runtime queries depend on the scheduled metrics aggregator writing `00-meta/08-metrics/lane-metric-*`; until that is in place this dashboard has no data. The full design lives in the design repo: memoria-docs/dashboards/fleet-health.md.

**Decision.** Per-lane operational health for the agent fleet — a trust score per lane plus the cost and reliability trends behind it. Open this when deciding whether scheduled (cron) work should keep running or pause.

## System trust score

A 0–100 score per lane, aggregated from the contributing inputs below. Bands:

- **90+** — healthy; no action.
- **70–89** — watch; something is slipping.
- **<70** — act; pause scheduled work for that lane until resolved.

## Contributing inputs

- Audit deny rate (policy MCP denials / total actions).
- Drift incidents (schema, plugin-config, vault-hash).
- Retry rate (cards re-dispatched).
- Accept / reject ratio on agent proposals.
- Cost trends (per-lane API spend over time).

Source: `00-meta/08-metrics/lane-metric-*`, written by the scheduled metrics aggregator. (Dataview queries land here once the aggregator is implemented.)

## What this dashboard is not

- **Not [`drift-watch`](drift-watch.md).** Drift-watch is *structural* health (schema / link / config drift); fleet-health is *operational* health (cost, retries, trust). Complementary views.
- **Not the Linter verdict.** The lint verdict is a *structural* aggregate; the trust score is an *operational* one.

## Related

- [Daily Health](index.md) — shows the per-lane trust-score summary and links here for the contributing inputs.
- [`drift-watch.md`](drift-watch.md) — complementary structural-health view.
- Design spec: memoria-docs/dashboards/fleet-health.md.
