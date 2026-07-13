---
title: Operational health
parent: Surfaces and dashboards
nav_order: 4
grand_parent: Surfaces
permalink: /explanation/surfaces/dashboards/operational-health/
---

# Operational health

Operational-health evidence ships as runtime logs and evaluation metrics. A
planned adapter may render them separately from structural health because "the
runtime did X" and "the vault has drift" are different claims.

## Audit log vs eval trend vs Drift watch

These views sit close together but answer different questions at different
layers — keeping them distinct is deliberate:

- **Audit log** is the *raw event stream*: one entry per policy-gate write
  decision (per-decision forensics, newest-first).
- **Eval trend** is diagnostic capability evidence over the checked eval set. It
  tells you whether retrieval/extraction/linking/verification quality has moved,
  not whether the request queue should pause.
- **[Drift watch](structural-health.md#drift-watch)** is a planned structural
  Maintenance view over the Linter operation's open integrity findings. Today,
  the linter verdict and file-backed attention provide that evidence directly.

In short: audit log is per-decision, eval trend is capability drift, and a
planned Drift watch would aggregate structural debt.

## Audit log

Audit log is the append-only policy-gate event stream. It explains write
decisions and preserves the evidence needed for forensic review.

It is not editable. The audit log records before/after hash pairs for gated
writes; editing the log would defeat the tamper signal. The field schema and
hash-pairing contract live in [Policy gate](../../../reference/control-and-policy/policy-mcp.md).

## Eval trend

The eval log records whether the deployed system's retrieval, extraction,
linking, and verification behavior is moving. A planned Eval trend view may
render it. The evidence is diagnostic, never a gate; capability scores are
noisy enough that blocking work on them would invite false halts.

The scoring contract is in [Vault eval](../../../reference/analysis-and-surfaces/vault-eval.md).

## Related

- Availability and backing surfaces: [Dashboards](../../../reference/analysis-and-surfaces/dashboards.md)
- Policy log schema: [Policy gate](../../../reference/control-and-policy/policy-mcp.md)
