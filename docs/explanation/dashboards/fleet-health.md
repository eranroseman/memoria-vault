---
topic: dashboards
---

# `fleet-health` — design summary

**Runtime artifact.** Ships at `00-meta/01-dashboards/fleet-health.md` in the [starter vault](https://github.com/eranroseman/memoria-vault) and runs in Obsidian via Dataview; the runtime queries live there. This page covers the design role.

## Mission

Track whether the Hermes fleet is healthy: cost per task trending up, success rate trending down, retries climbing, latency spikes, per-lane trust score, per-skill cost regressions. The headline is the **trust score** per lane (0–100). This is operations-tier, not architecture-tier — it only matters once the fleet is doing enough work per week that one stuck card or one runaway loop is hard to spot by eye.

## What this dashboard is not

- **Not [`drift-watch`](drift-watch.md).** Fleet-observability is *operational* (cost, latency, success rates); drift-watch is *structural* (structural-detector findings). The two are the design's complementary rollups — trust score for operations, verdict band for structure. Both are headline single numbers; both are reproducibly computed; neither involves LLM judgment in the rollup.
- **Not actionable on individual writes.** That's [`audit-log`](audit-log.md)'s job. Fleet-observability aggregates across many writes into trends.
- **Not a workflow tracker.** [`board-state`](board-state.md) shows work-in-flight; fleet-health shows *quality* of completed work.

## Design decisions

- **Reads from a new note type kept in `00-meta/08-metrics/`.** `lane-metric` notes (one per lane per period) and `skill-metric` notes (one per skill per period). These aren't among the 15 canonical note types — they're operational telemetry, not knowledge. A scheduled Hermes task aggregates the audit log and board's task history into these notes.
- **Trust score combines audit deny rate, drift incidents, secret hits, retry rate, success rate, and (for lanes that produce inline `[!suggestions]` callouts) accept/reject ratios.** Bands: 90+ healthy, 70–89 watch, <70 act. Ratio sub-thresholds: >90% accept = rubber-stamping, <20% accept = prompt drift; both down-weight the lane.
- **Trust score is shaped like ClawArena's CRS and tracks `pass^k`, not single-shot success.** Composition mirrors completion × robustness (success-cohesion / failure-dispersion), and the lane score trends **`pass^k`** consistency across repeated runs — τ-bench shows reliability collapses run-over-run (pass^1 ≈ 61% → pass^8 ≈ 25%) in a way a flat success average hides. See [roadmap/evaluation.md](../../project/roadmap/evaluation.md) (Observability).
- **When meaningful data appears.** The dashboard ships in the vault from day 1 (part of Memoria v0.1) but shows real data only once the metrics aggregator is built (Phase 6) and weekly fleet volume accumulates. Until then, board-state and audit-log catch issues directly — see [roadmap/future-directions.md](../../project/roadmap/future-directions.md).
- **Graceful degradation.** Until the metrics aggregator exists, the dashboard is a placeholder with explanatory text rather than empty tables.

## Related

- [`drift-watch`](drift-watch.md) — structural complement; verdict band is the structural sibling of trust score
- [`audit-log`](audit-log.md) — per-decision forensics that feed the trust score's audit-deny-rate input
- [`board-state`](board-state.md) — work-in-flight view (orthogonal to quality aggregation)
- [glossary.md trust-score entry](../../reference/glossary.md#observability-and-verdicts) — the scoring formula and band thresholds
