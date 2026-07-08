---
title: Operational health
parent: Surfaces and dashboards
nav_order: 4
grand_parent: Surfaces
permalink: /explanation/surfaces/dashboards/operational-health/
---

# Operational health

Operational health surfaces runtime decisions and evaluation trends. It is
separate from structural health because "the runtime did X" and "the vault has
drift" are different claims.

## Audit log vs eval trend vs Drift watch

These views sit close together but answer different questions at different
layers — keeping them distinct is deliberate:

- **Audit log** is the *raw event stream*: one entry per policy-gate write
  decision (per-decision forensics, newest-first).
- **Eval trend** is diagnostic capability evidence over the checked eval set. It
  tells you whether retrieval/extraction/linking/verification quality has moved,
  not whether the request queue should pause.
- **[Drift watch](structural-health.md#drift-watch)** is *structural*, not operational: it is the Maintenance view over the Linter operation's open integrity findings, headlined by the verdict band — a different cadence and abstraction layer from the other two.

In short: audit log is per-decision, eval trend is capability drift, and Drift
watch is aggregated structural debt.

## Audit log

Audit log is the append-only policy-gate event stream. It explains write
decisions and preserves the evidence needed for forensic review.

It is not editable. The audit log records before/after hash pairs for gated
writes; editing the log would defeat the tamper signal. The field schema and
hash-pairing contract live in [Policy gate](../../../reference/control-and-policy/policy-mcp.md).

## Eval trend

Eval trend shows whether the deployed system's retrieval, extraction, linking,
and verification behavior is moving. It is diagnostic, never a gate; capability
scores are noisy enough that blocking work on them would invite false halts.

The scoring contract is in [Vault eval](../../../reference/analysis-and-surfaces/vault-eval.md).

## Related

- Exact shipped surfaces: [Dashboards](../../../reference/analysis-and-surfaces/dashboards.md)
- Policy log schema: [Policy gate](../../../reference/control-and-policy/policy-mcp.md)
