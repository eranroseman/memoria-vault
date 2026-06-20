---
title: Calibration
parent: Reference
---

# Calibration

`src/.memoria/schemas/calibration.yaml` is the source of truth for shared
thresholds. Every calibrated value follows the same discipline: grounded in real
Memoria data, bounded by an explicit error budget, recalibrated on drift, and
shadow-first before it affects routing or automation.

## Production Rule

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

## Existing Thresholds

| Block | Purpose | Production use |
| --- | --- | --- |
| `entity_resolution` | cross-source identity agreement floor | below the floor, ingest raises an Inbox near-tie flag instead of merging |
| `classify` | OpenAlex topic classification floor and near-tie margin | clear winners apply; near ties raise a review flag |
| `inbox` | resolved-card archival age | archival sweep moves old resolved cards out of active Inbox views |
| `clustering` | display defaults for graph/topic maps | layout/topic defaults only; not a canonical-write decision |

## Hybrid-Score Thresholds

#379 adds explicit threshold slots for the score families that are not yet
calibrated. They intentionally ship disabled and unfilled.

### `hybrid_scores.candidate_rank`

Future use: reorder or batch candidate review attention.

Grounding requirement: at least `min_labeled_decisions` real PI keep/archive/edit
decisions with the score recorded in shadow mode.

Error budget:

- `max_false_promote_rate`: promoted candidates that the PI later rejects or
  heavily edits
- `max_top_decile_miss_rate`: PI-kept candidates that the score failed to surface
  in the top decile

Production thresholds:

- `promote_threshold`
- `defer_threshold`

Both remain `null` until the grounding dataset meets the sample and error-budget
requirements.

### `hybrid_scores.outline_score`

Future use: prioritize or flag draft outlines for revision.

Grounding requirement: at least `min_labeled_outlines` real outlines with human
accepted/revised outcomes, collected in shadow mode.

Error budget:

- `max_false_accept_rate`: outlines scored as acceptable that the PI revises
  materially
- `max_false_revise_rate`: outlines flagged for revision that the PI accepts
  without material change

Production thresholds:

- `accept_threshold`
- `revise_threshold`

Both remain `null` until calibrated against the grounding dataset.

### `clustering.quality_thresholds`

Future use: decide whether a generated map or topic model is good enough to rank
or route downstream work.

Grounding requirement: at least `min_reviewed_maps` human-reviewed map/topic runs.

Error budget:

- `max_cluster_churn_rate`: maximum acceptable cluster membership churn across
  stable reruns or adjacent calibration windows

Production thresholds:

- `silhouette_floor`
- `topic_coherence_floor`

Both remain `null` until reviewed map runs establish useful values.

## Drift

Recalibrate any enabled block when the scoring model, embedding model, upstream
classification source, prompt, or feature extraction changes. Until recalibration
passes the same sample and error-budget checks, set `production_enabled: false`
and return the score to shadow mode.
