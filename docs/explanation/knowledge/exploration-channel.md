---
title: Exploration channel
parent: Knowledge
grand_parent: Explanation
nav_order: 8
---

# Exploration channel

The exploration channel is separate from relevance-ranked search because the PI
needs two different questions answered. Search asks, "what checked material
already matches this question?" Exploration asks, "what should I inspect next
because the graph suggests a gap, contrary item, or nearby candidate?"

That distinction keeps exploration from polluting answers. A ranked answer
should stay grounded in checked material; exploration may point outside the
current argument so the PI can decide whether the candidate belongs.

Every surfaced item carries a `why` string so the PI can decide whether it is
worth action.

The command contract belongs in [CLI](../../reference/cli.md) and [Operations](../../reference/operations.md).
