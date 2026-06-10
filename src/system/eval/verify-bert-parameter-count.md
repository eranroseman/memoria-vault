---
type: eval-task
title: "Verify a near-miss numerical citation"
lifecycle: current
workflow: verify
lane: verify
created: 2026-06-10
references:
  - devlin2019bert
---

## Input

Cite-check this draft sentence against its cited source:

> BERT-Large contains 110 million parameters [@devlin2019bert].

## Expected behavior

Verdict: **mis-cited number**. The figure is real but attached to the wrong
model: 110M is BERT-**Base**; BERT-**Large** has 340M parameters. This tests
entity-level precision — a verifier that only checks whether "110 million"
appears somewhere in the paper will wrongly pass it.

## Scoring rubric

- **Pass (1.0):** flagged, with the correct correction (Base = 110M,
  Large = 340M).
- **Partial (0.5):** flagged as suspicious without identifying the Base/Large
  swap.
- **Fail (0):** passed as supported.
