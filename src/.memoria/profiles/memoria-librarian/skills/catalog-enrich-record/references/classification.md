# Classification (`_proposed_classification`) — hybrid method

The classification step is the most cost-sensitive part of ingest because every new source
gets one. Memoria uses the **hybrid pattern** from the project's computational-methods design
notes (not shipped to the runtime vault): a trained classifier with a confidence gate, an LLM
fallback for the low-confidence tail, and human review as the final authority.

## The four steps

1. **Classifier proposal (deterministic).** A small multi-label classifier trained on the
   human's past `lifecycle: current` paper-notes proposes values for `topic`, `methods`, and
   `study_design`. The classifier emits a calibrated softmax probability per label.
2. **Confidence gate.** If the classifier's confidence exceeds the threshold (default `0.85`),
   accept the proposal directly into `_proposed_classification`.
3. **LLM fallback.** For sources where classifier confidence is below the threshold, fall back
   to an LLM proposal. This usually means the source is genuinely novel in topic or
   methodology — the classifier hasn't seen enough similar examples yet.
4. **Human review.** Either way, `_proposed_classification` is a *proposal*, not canonical. The
   human confirms during classification; their confirmations become tomorrow's training data.

## Retraining cadence

The retraining loop runs monthly on a cron (or when the override rate crosses 25%). As the
corpus grows, the classifier becomes more accurate and the LLM-fallback rate drops. This is
calibrated learning, not LLM self-reported confidence — see the project's computational-methods
design notes' anti-patterns (not shipped to the runtime vault) for why that distinction matters.

## Corpus milestones

- **First ~200 paper-notes:** the classifier hasn't trained yet; all proposals go through the
  LLM path.
- **After ~500 classified paper-notes:** the classifier becomes useful.
- **After ~1,000:** the classifier is calibrated.

This pattern is also the resolution to the design question of confidence scoring on
`_proposed_classification`; the project's decision records (not shipped to the runtime vault)
carry the current ADRs.
