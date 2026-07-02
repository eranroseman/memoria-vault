---
type: eval-task
title: "Extract claim stubs from the Transformer paper"
lifecycle: current
workflow: extract
eval_role: extract
created: 2026-06-10
references:
  - vaswani2017attention
---

## Input

The catalog record (and extract, if present) for `vaswani2017attention`
(*Attention Is All You Need*, Vaswani et al., 2017). Task: extract the paper's
core claims as claim stubs, each with the citekey as source.

## Expected behavior

At least three distinct, correctly-sourced claim stubs, including (in any
wording):

1. The Transformer dispenses with recurrence and convolutions entirely, using
   only attention mechanisms.
2. It reached 28.4 BLEU on WMT 2014 English-to-German translation.
3. Because the model contains no recurrence, it injects sequence-order
   information through positional encodings.

Stubs must stay within the source — no claims imported from later literature
(e.g. nothing about BERT or GPT).

## Scoring rubric

- **Pass (1.0):** ≥ 3 stubs, all faithful to the paper, each carrying
  `vaswani2017attention` as source; at least two of the three expected claims
  present.
- **Partial (0.5):** 1-2 faithful stubs, or ≥ 3 stubs with one missing/wrong
  source attribution.
- **Fail (0):** any fabricated claim (content not in the paper), or no stubs.
