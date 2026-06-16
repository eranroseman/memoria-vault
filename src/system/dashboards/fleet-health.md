# Fleet Health

Per-lane operational health for the agent fleet — a 0–100 trust score plus the cost and reliability trends behind it. Open when deciding whether scheduled (cron) work should keep running or pause. [Dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/operational-health/fleet-health).

## Trust score per lane

Bands: **90+** healthy (no action) · **70–89** watch (something slipping) · **<70** act (pause that lane's scheduled work until resolved).

```dataview
TABLE WITHOUT ID
  file.link AS Metric,
  lane AS Lane,
  trust_score AS Score,
  band AS Band,
  accept_ratio AS "Accept rate",
  time_on_gate_min AS "Gate min",
  expand_then_accept_min AS "Expand→accept min",
  card_open_resolve_min AS "Open→resolve min",
  blind_rereview_samples AS "Blind samples",
  cost AS Cost
FROM "system/metrics"
WHERE type = "lane-metric"
SORT period DESC, lane ASC
```

Aggregated from: audit deny rate, structural-drift incidents (schema / plugin-config / vault-hash), secret-field access attempts, retry rate, success rate, accept/reject ratio on agent proposals, PI attention timing, and blind re-review samples; the per-lane API cost trend is reported alongside (not a trust-score input). Source: `system/metrics/lane-*-<week>.md`, written weekly by the `memoria-metrics` cron (Mondays 06:30).

## Related

- [[board-state|Board State]] — the Inbox board; this rollup feeds its operational glance.
- [[drift-watch|Drift watch]] — complementary *structural*-health view (this one is *operational*).
