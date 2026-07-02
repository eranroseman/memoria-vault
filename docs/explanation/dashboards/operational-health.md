---
title: Operational health
parent: Surfaces and dashboards
nav_order: 4
grand_parent: Explanation
permalink: /explanation/dashboards/operational-health/
---

# Operational health

Dashboards that track runtime decisions and evaluation trends.

| Dashboard | Question it answers |
|---|---|
| Audit log | What did the policy gate decide, and why? |
| Eval trend | Is the deployed system still finding, extracting, linking, and verifying correctly on this vault? |

## Audit log vs eval trend vs Drift watch

These views sit close together but answer different questions at different
layers — keeping them distinct is deliberate:

- **Audit log** is the *raw event stream*: one entry per policy-gate write
  decision (per-decision forensics, newest-first).
- **Eval trend** is diagnostic capability evidence over the checked eval set. It
  tells you whether retrieval/extraction/linking/verification quality has moved,
  not whether a worker lane should pause.
- **[Drift watch](structural-health.md#drift-watch)** is *structural*, not operational: it is the Maintenance view over the Linter operation's open integrity findings, headlined by the verdict band — a different cadence and abstraction layer from the other two.

In short: audit log is per-decision, eval trend is capability drift, and Drift
watch is aggregated structural debt.

## Audit log

Audit log reads `system/logs/audit.jsonl`, the append-only policy-gate event
stream. Open it when a worker behaved unexpectedly, a write did not land, or a
scheduled run needs forensic review.

It is not editable. The audit log records before/after hash pairs for gated
writes; editing the log would defeat the tamper signal. The field schema and
hash-pairing contract live in [Policy gate](../../reference/policy-mcp.md).

## Eval trend

Eval trend reads `system/metrics/eval/runs.jsonl` and shows per-quarter vault-eval
capability scores: `recall@k`, support-rate, and FAMA-clean. It is diagnostic,
never a gate; capability scores are noisy enough that blocking work on them would
invite false halts.

The scoring contract is in [Vault eval](../../reference/vault-eval.md).

## Related

- Exact shipped surfaces: [Dashboards](../../reference/dashboards.md)
- Policy log schema: [Policy gate](../../reference/policy-mcp.md)
- Installed profile boundary: [Installed profiles](../../reference/profile-capabilities.md)
