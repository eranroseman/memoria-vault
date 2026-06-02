# Fleet Health

Per-lane operational health for the agent fleet — a 0–100 trust score plus the cost and reliability trends behind it. Open when deciding whether scheduled (cron) work should keep running or pause. [Dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/operational-health/fleet-health/).

## Trust score per lane

Bands: **90+** healthy (no action) · **70–89** watch (something slipping) · **<70** act (pause that lane's scheduled work until resolved).

Aggregated from: audit deny rate, drift incidents (schema / plugin-config / vault-hash), retry rate, accept/reject ratio on agent proposals, and per-lane API cost trend. Source: `99-system/metrics/lane-metric-*`, written by the scheduled metrics aggregator — Dataview queries land here once it's implemented.

## Related

- [[daily-health]] — surfaces the trust-score summary and links here for the inputs.
- [[drift-watch]] — complementary *structural*-health view (this one is *operational*).
