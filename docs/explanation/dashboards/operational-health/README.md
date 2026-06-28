---
title: Operational health
parent: Dashboards
nav_order: 4
grand_parent: Explanation
permalink: /explanation/dashboards/operational-health/
---

# Operational health

Dashboards that track how the agent fleet is performing and what it decided.

| Dashboard | Question it answers |
|---|---|
| Fleet health | Are the agents performing well over time? Is cost trending up? |
| Audit log | What did the policy MCP decide, and why? |
| Eval trend | Is the deployed system still finding, extracting, linking, and verifying correctly on this vault? |
| Skill state | Which skills are active in which lane? Do lane policy and shipped skills agree? |

## Audit log vs fleet health vs Drift watch

Three dashboards sit close together but answer different questions at different layers — keeping them distinct is deliberate:

- **Audit log** is the *raw event stream*: one entry per policy-MCP write decision (per-decision forensics, newest-first).
- **Fleet health** *aggregates* those entries (and other signals) into rolled-up per-lane trend metrics over time — quality and cost of completed work, headlined by the trust score.
- **[Drift watch](../structural-health/README.md#drift-watch)** is *structural*, not operational: it is the Maintenance view over the Linter operation's open integrity findings, headlined by the verdict band — a different cadence and abstraction layer from the other two.

In short: audit log is per-decision, fleet health is aggregated-operational, Drift watch is aggregated-structural.

## Fleet health

Fleet health tracks per-lane cost, success rate, retry frequency, review latency,
PI attention timing, blind re-review sample counts, and the headline trust score.
The trust-score formula and bands are specified in the [Dashboards
reference](../../../reference/dashboards.md#trust-score-fleet-health).

It is not board state. Board state shows current work; fleet health summarizes
completed work over time. Low-volume lanes are marked `insufficient-data` rather
than pretending a thin sample is actionable.

## Audit log

Audit log reads `system/logs/audit.jsonl`, the append-only policy-MCP event
stream. Open it when a worker behaved unexpectedly, a write did not land, or a
scheduled run needs forensic review.

It is not editable. The audit log records before/after hash pairs for gated
writes; editing the log would defeat the tamper signal. The field schema and
hash-pairing contract live in [Policy MCP](../../../reference/policy-mcp.md).

## Eval trend

Eval trend reads `system/metrics/eval/runs.jsonl` and shows per-quarter vault-eval
capability scores: `recall@k`, support-rate, and FAMA-clean. It is diagnostic,
never a gate; capability scores are noisy enough that blocking work on them would
invite false halts.

The scoring contract is in [Vault eval](../../../reference/vault-eval.md).

## Skill state

Skill state renders lane policy and shipped skills from `.memoria/lane-overrides/`
and `.memoria/profiles/*/skills/`. It answers "which lane can do what?" without
opening the YAML and profile directories by hand.

It is visibility, not enforcement. The policy gate and profile configs enforce;
the dashboard only renders mismatches for review.

## Related

- Exact shipped surfaces: [Dashboards](../../../reference/dashboards.md)
- Policy log schema: [Policy MCP](../../../reference/policy-mcp.md)
- Profile capability matrix: [Profile capabilities](../../../reference/profiles.md)
