---
topic: decisions
id: 66
title: Semi-automatic triage, agent-consensus pre-filter, and tournament ranking
nav_exclude: true
status: accepted
date_proposed: 2026-06-11
date_resolved: 2026-06-19
assumes: [50, 51, 54]
supersedes: []
superseded_by: []
---

# ADR-66: Semi-automatic triage, agent-consensus pre-filter, and tournament ranking

## Context

Three capabilities reduce the operator's per-candidate judgment cost without moving the autonomy boundary: batching high-confidence classifications into one approval, routing a consensus pre-filter ahead of the review queue, and ranking a large inbox by pairwise comparison. None bypasses the structural review gate — they change what reaches it and in what order. They are grouped because they share that constraint and because each carries a calibration risk that makes premature adoption worse than waiting; the thresholds below are cadence-review context, not gates.

## Decision

Memoria will, when scheduled, add:

1. **Semi-autonomous batch triage.** The classifier already emits a confidence score with `_proposed_classification`. When confidence is above a threshold (e.g. > 0.92), proposals are batched into a single "approve these classifications?" card rather than reviewed individually; low-confidence proposals remain individual reviews. The threshold is calibrated against the operator's measured error rate, and the batch card surfaces the full list readably. Applies only to classification dimensions where calibrated confidence exists — never to new note types the classifier hasn't seen.

2. **Agent-consensus pre-filter.** Before a candidate reaches the review queue, a second independent profile pass reviews the output; agreement sets `consensus: true`, disagreement `consensus: false`, and the operator processes disagreement cards first. It does not bypass the gate — the gate stays structural; the pre-filter only routes. To avoid correlated errors (the Bisht et al. 2026 hivemind finding), the two profiles use models from different providers or fine-tuning regimes.

3. **Tournament pairwise ranking.** When the discovery inbox is large (> 50 candidates), candidates are ranked by pairwise LLM comparison against `steering.md` to surface the top-N first; lower-ranked candidates can be deferred. This is an explicit cold-start fallback for the learning-to-rank model — once that model has enough training data, Memoria switches to it (cheaper, faster, personalized).

## Consequences

- A too-permissive confidence threshold promotes wrong classifications silently; calibration against the actual error rate is load-bearing.
- The consensus pre-filter adds latency and per-card cost, and two profiles with correlated errors can agree and be confidently wrong together — it has diminishing value on shared-model failure modes.
- Pairwise comparison cost scales quadratically with queue size, and ranking is personalized only while `steering.md` is current.

## Current implementation mapping

#379 adds the threshold contract in
[`calibration.yaml`](../reference/calibration.md): `hybrid_scores.candidate_rank`
and `hybrid_scores.outline_score` are present but `production_enabled: false` with
null thresholds until real PI decisions/outcomes fill the grounding dataset and
error budget. The clustering quality thresholds live under
`clustering.quality_thresholds` with the same shadow-first rule. No score from this
ADR may change routing or review visibility until those fields are filled.

## When this matters

*(Cadence-review context, not a gate.)*

- **Semi-autonomous triage** — classification backlog exceeds a week's review capacity *and* the classifier has run for ≥ 2 months with a measured accuracy baseline.
- **Agent-consensus pre-filter** — review-queue depth consistently exceeds 2 weeks' backlog *and* a spot-check shows agreed cards are approved at > 90% rate. If the two profiles share an underlying model or training, the correlated-error risk is real — use different providers or regimes.
- **Tournament ranking** — the inbox regularly exceeds 50 candidates *and* the learning-to-rank model is not yet trained. It is the expensive cold-start alternative; retire it once learning-to-rank has data.

## Related

- **Related decisions / Depends on:** [ADR-50 lifecycle](50-universal-lifecycle-and-maturity.md) (the card states triage moves between); [ADR-51 inbox honesty card](51-inbox-category-and-honesty-card.md) (the inbox surface these improvements feed); [ADR-54 batch worklists](54-two-decision-kinds-batch-worklists.md) (the batch-approval mechanism semi-auto triage builds on).
- **Tracking issue:** [#416](https://github.com/eranroseman/memoria-vault/issues/416) — implementation readiness lives on the issue.
