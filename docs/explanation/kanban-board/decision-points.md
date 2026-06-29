---
title: Decision points
parent: Kanban board
grand_parent: Explanation
nav_order: 3
---

# Decision points

Not every Inbox item asks for the same kind of human action. Memoria keeps three
decision shapes separate so the daily queue does not become a pile of fake
approvals.

## Approval gates

Approval gates review agent-produced output: candidate triage, link
confirmation, certification before shipping, re-adjudication after a retraction,
near-tie dedup calls, and archive proposals. Each gate gives the PI decision
material, not a verdict. The card format is the [honesty card](honesty-card.md).

## Work prompts

Work prompts signal that it is time for the PI's own thinking: a kept source is
ready to distill, a corpus is ready to map, or a finished task needs review.
They are handles into work, not proposals to accept.

## Batch worklists

High-cardinality decisions become one worklist, not many cards. When a coverage
report finds forty sources to screen, the Inbox gets one aggregate prompt that
points to a Bases-backed worklist where each row carries its own decision field.
Forty cards would flood a queue meant to converge to zero.

## Automated steps

Some steps are deliberately not decisions. Classification is low-stakes,
high-volume, and correctable, so it is automated and raises a `flag` only on
genuine ambiguity. A human gate on every classification would train rubber-stamp
behavior.

## Workflow triggers

Some workflow triggers create cards automatically because the trigger itself is
the useful invariant. Committing a draft to `projects/<project>/` creates a
verification card in the Peer-reviewer's verify lane. The hook fires on
`post-commit`, creates the board card, and returns; the Peer-reviewer claims the
card through the normal dispatcher.

That does not make verification completion automatic. The result is an
`agent_recommendation`, never approval. The PI still reads the report and decides
whether to revise.

## Related

- Promotion boundary: [Promotion and the write boundary](../knowledge/promotion-and-gated-zones.md)
- Card shape: [The honesty card](honesty-card.md)
- Batch-worklist decision: [ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md)
- How to read the verification result: [Verify and revise a draft](../../how-to-guides/project/verify-and-revise.md)
