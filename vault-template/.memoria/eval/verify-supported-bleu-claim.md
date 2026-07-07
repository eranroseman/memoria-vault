---
type: eval-task
title: "Verify a supported numerical claim (positive control)"
lifecycle: current
workflow: verify
eval_role: verify
created: 2026-06-10
references:
  - vaswani2017attention
---

## Input

Cite-check this draft sentence against its cited source:

> The Transformer achieved 28.4 BLEU on the WMT 2014 English-to-German
> translation task [@vaswani2017attention].

## Expected behavior

Verdict: **supported**. The figure and task match the paper's reported result
exactly. This is the positive control — a verifier that flags it is
over-triggering, which erodes trust in every other flag.

## Scoring rubric

- **Pass (1.0):** verdict supported, citing where in the source the figure
  appears.
- **Partial (0.5):** supported, but with hedging that would send the PI to
  re-check a correct sentence.
- **Fail (0):** flagged as unsupported or mis-cited.
