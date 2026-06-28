---
type: eval-task
title: "Link BERT to the Transformer it builds on"
lifecycle: current
workflow: link
lane: link
created: 2026-06-10
references:
  - devlin2019bert
  - vaswani2017attention
---

## Input

The catalog record for `devlin2019bert` (*BERT: Pre-training of Deep
Bidirectional Transformers for Language Understanding*, Devlin et al., 2019),
with both it and `vaswani2017attention` present in the catalog. Task: propose
the typed relations this record should carry.

## Expected behavior

A proposed `builds-on` (or the vault's equivalent extends/uses-method) relation
from `devlin2019bert` to `vaswani2017attention` — BERT's encoder *is* the
Transformer encoder. The proposal must be typed (not a bare mention), point at
the existing catalog note, and be framed as a proposal for the PI, not an
applied edit (link writes are reviewed).

## Scoring rubric

- **Pass (1.0):** the builds-on relation to `vaswani2017attention` proposed,
  correctly typed and directed, as a proposal.
- **Partial (0.5):** the connection surfaced but untyped, reversed, or pointed
  at a non-existent note.
- **Fail (0):** no relation proposed, or relations invented to papers not in
  the catalog.
