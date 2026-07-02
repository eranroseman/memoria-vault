---
type: eval-task
title: "Verify a contradicted architectural claim"
lifecycle: current
workflow: verify
eval_role: verify
created: 2026-06-10
references:
  - vaswani2017attention
---

## Input

Cite-check this draft sentence against its cited source:

> The Transformer architecture eliminates the need for positional information
> in the input sequence [@vaswani2017attention].

## Expected behavior

Verdict: **contradicted / unsupported**. The paper does the opposite of what
the sentence claims: *because* self-attention contains no recurrence or
convolution, the model must inject sequence order explicitly, via sinusoidal
positional encodings added to the input embeddings. The sentence is a plausible
misreading — exactly the failure mode cite-check exists to catch.

## Scoring rubric

- **Pass (1.0):** flagged, with the positional-encoding mechanism named as the
  contradicting evidence.
- **Partial (0.5):** flagged as unsupported, but without locating the
  contradicting passage.
- **Fail (0):** passed as supported.
