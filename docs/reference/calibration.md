---
title: Calibration
parent: Agents and control
grand_parent: Reference
---

# Calibration

`vault-template/.memoria/schemas/calibration.yaml` is the source of truth for shared
thresholds and scorer versions. This page states the rule; the YAML owns the values.

## Production rule

A score may affect production behavior only when all of these are true:

- `production_enabled: true`
- the relevant threshold fields are non-null
- `grounding_dataset` names the reviewed dataset or log slice used to fit the
  thresholds
- `model_version` pins the model, scorer, or upstream source version whose scores
  were calibrated
- the sample-count and error-budget fields in that block are satisfied

If any threshold is `null`, the score is report-only. It may log shadow telemetry
or appear in a review surface, but it must not auto-accept, auto-defer, hide,
merge, block, or reorder canonical work.

## Drift

Recalibrate any enabled block when the scoring model, embedding model, upstream
classification source, prompt, or feature extraction changes. Until recalibration
passes the same sample and error-budget checks, set `production_enabled: false`
and return the score to shadow mode.
