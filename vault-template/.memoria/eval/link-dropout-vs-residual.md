---
type: eval-task
title: "Link two regularization approaches without conflating them"
lifecycle: current
workflow: link
eval_role: link
created: 2026-06-10
references:
  - srivastava2014dropout
  - he2016deep
---

## Input

The catalog records for `srivastava2014dropout` (*Dropout: A Simple Way to
Prevent Neural Networks from Overfitting*, Srivastava et al., 2014) and
`he2016deep` (*Deep Residual Learning for Image Recognition*, He et al., 2016).
Task: propose how these two records should relate, if at all.

## Expected behavior

A **discriminating** answer: both papers address training deep networks, but
dropout targets *overfitting* while residual connections target the
*degradation/optimization* problem — the agent should propose at most a weak
"related" / shared-topic connection (deep network training) and explicitly
**decline** a supports/builds-on relation, saying why. This is a
negative-control task: the wrong behavior is inventing a strong typed edge
between two merely co-topical papers.

## Scoring rubric

- **Pass (1.0):** declines a strong relation with the correct distinction
  (overfitting vs. degradation), optionally proposing a weak topical link.
- **Partial (0.5):** proposes only a weak/topical link without articulating the
  distinction.
- **Fail (0):** proposes builds-on/supports/contradicts between the two.
