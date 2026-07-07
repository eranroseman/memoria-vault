---
type: eval-task
title: "Find the residual-learning paper from a paraphrase"
lifecycle: current
workflow: find
eval_role: catalog
created: 2026-06-10
references:
  - he2016deep
---

## Input

Query phrased *without* the paper's own vocabulary, to test retrieval beyond
keyword match:

> I remember a vision paper arguing that very deep networks get *worse* as you
> stack layers, and fixing it by letting layers learn an offset from identity
> instead of a full mapping. Which paper is that?

## Expected behavior

The Librarian resolves the paraphrase (the degradation problem; learning
residual functions with reference to layer inputs) to *Deep Residual Learning
for Image Recognition* (He et al., 2016; citekey `he2016deep`) and returns its
catalog note. A keyword-only search will miss this — the description avoids
"residual" as the lead term.

## Scoring rubric

- **Pass (1.0):** `he2016deep` returned in the top 3, identified by its vault
  note.
- **Partial (0.5):** the right paper named but no vault note cited, or only
  found after the PI supplies the word "residual".
- **Fail (0):** a different paper asserted, or no answer.
