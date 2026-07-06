---
title: Exploration channel
parent: Knowledge
grand_parent: Explanation
nav_order: 8
---

# Exploration channel

The exploration channel is separate from relevance-ranked search. It surfaces
coverage candidates from citation-graph edges and contrary items from checked
contradiction declarations or the existing REFUTED tension detector.

`memoria project explore` returns data only. An empty result is valid: it means
the checked graph did not expose a genuine coverage or contrary candidate.

Every surfaced item carries a `why` string so the PI can decide whether it is
worth action.
