---
title: Calibration
parent: Analysis and surfaces
nav_order: 4
grand_parent: Reference
---

# Calibration

Memoria ships no shared threshold file or generic calibration gate. Current
thresholds are operation-specific constants. The seeded-error review payload
exposes a fixed `production_enabled: false` marker, but it is report metadata,
not an activation mechanism.

## Planned production-calibration contract

> **Planned beta.1 — I1/E1:** A reusable calibration contract does not ship
> today. Before a future score can alter routing, promotion, or other canonical
> work, it will require the evidence below.

A future score may affect production behavior only when all of these are true:

- `production_enabled: true`
- the relevant threshold fields are non-null
- `grounding_dataset` names the reviewed dataset or log slice used to fit the
  thresholds
- `model_version` pins the model, scorer, or upstream source version whose scores
  were calibrated
- the sample-count and error-budget fields in that block are satisfied

If any future threshold is `null`, the score will remain report-only. It may
appear in a review surface, but it must not auto-accept, auto-defer, hide,
merge, block, or reorder canonical work.

Seeded-error currently emits a fixed report-only review batch; it does not
implement this generic contract.

## Planned recalibration

When the generic contract ships, an enabled block will need recalibration after
a scoring model, embedding model, upstream classification source, prompt, or
feature-extraction change. Until recalibration passes the same sample and
error-budget checks, it will set `production_enabled: false` and return the
score to shadow mode.

## Related

- The seeded-error bundle behind the current report-only marker: [Vault eval](vault-eval.md)
- Why an uncalibrated score must stay report-only: [Design principles](../../explanation/rationale/foundations/design-principles.md) (Grounding, not truth)
