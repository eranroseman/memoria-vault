# `fleet-health` dashboard

Tracks whether the Hermes agent fleet is performing well over time: cost per task, success rate, retry frequency, latency, and per-lane trust scores. The headline number is the **trust score** per lane (0–100). This dashboard matters once the fleet is doing enough work per week that one stuck card or one runaway loop is hard to spot by eye.

## The trust score

The trust score for each lane combines: audit deny rate, structural drift incidents, secret-field access attempts, retry rate, success rate, and (for lanes that produce `[!suggestions]` callouts) accept/reject ratios on those suggestions.

Bands:
- **90+** — healthy; no action needed
- **70–89** — watch; investigate the contributing factor that's pulling the score down
- **< 70** — act; something is consistently wrong in this lane

Suggestion-ratio sub-thresholds: an accept rate above ~90% means the human is rubber-stamping suggestions without reviewing them (down-weight the lane score). A rate below ~20% means the candidate scoring is producing poor candidates and needs tuning (also down-weighted).

## What it is not

**Not audit-log.** Fleet-health aggregates across many completed writes into trends. The audit log is per-decision forensics.

**Not board-state.** Board-state shows what work is currently in flight. Fleet-health shows the quality and cost of completed work over time.

**Not drift-watch.** Fleet-health is operational (cost, latency, success rates). Drift-watch is structural (Linter M-detector findings). They are complementary: trust score is the operational headline; verdict band is the structural headline. Both are reproduced from logs without LLM judgment.

## When it shows real data

The dashboard ships in every vault from day 1 but shows meaningful data only once the metrics aggregator is built and weekly fleet volume accumulates. Until then, board-state and audit-log catch issues directly. The dashboard degrades gracefully — it shows explanatory text rather than empty tables before the aggregator exists.

## Related

- [explanation/dashboards/audit-log.md](audit-log.md) — per-decision forensics that feed the deny-rate input
- [explanation/dashboards/drift-watch.md](drift-watch.md) — structural complement; verdict band is the structural sibling of trust score
- [reference/glossary.md](../../reference/glossary.md) — trust score formula and band definitions
