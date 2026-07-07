---
type: eval-task
title: "Extract the Adam optimizer's default hyperparameters"
lifecycle: current
workflow: extract
eval_role: extract
created: 2026-06-10
references:
  - kingma2015adam
---

## Input

The catalog record (and extract, if present) for `kingma2015adam` (*Adam: A
Method for Stochastic Optimization*, Kingma & Ba, 2015). Task: extract the
method's proposed default settings as a methodological claim stub.

## Expected behavior

One claim stub stating the paper's suggested defaults — β₁ = 0.9, β₂ = 0.999,
ε = 10⁻⁸ — sourced to `kingma2015adam`. This tests **numerical fidelity**:
the values must be transcribed exactly, not rounded or swapped.

## Scoring rubric

- **Pass (1.0):** all three values exact, correct source.
- **Partial (0.5):** two of three values exact (one missing — not wrong).
- **Fail (0):** any *incorrect* value (a wrong number is worse than a missing
  one — it poisons downstream drafts), or a fabricated source.
