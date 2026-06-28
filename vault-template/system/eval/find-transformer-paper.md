---
type: eval-task
title: "Find the paper that introduced the Transformer"
lifecycle: current
workflow: find
lane: catalog
created: 2026-06-10
references:
  - vaswani2017attention
---

## Input

Query, exactly as a PI would ask it:

> Which paper in the catalog introduced the Transformer architecture — the one
> that replaced recurrence with attention for sequence transduction?

## Expected behavior

The Librarian retrieves the catalog record for *Attention Is All You Need*
(Vaswani et al., 2017; citekey `vaswani2017attention`) and names it as the
answer, with the catalog path. It must not answer from model memory alone — the
response cites the vault note it found.

## Scoring rubric

- **Pass (1.0):** `vaswani2017attention` is the top result, identified by its
  vault note.
- **Partial (0.5):** the paper appears in the top 3 results but is not ranked
  first, or is named without pointing at the vault note.
- **Fail (0):** the paper is absent from the top 3, or the answer is fabricated
  from memory with no vault citation.
