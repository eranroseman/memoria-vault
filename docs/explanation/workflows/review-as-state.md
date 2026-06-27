---
title: Review as a first-class state
parent: Workflows
nav_order: 3
---

# Review as a first-class state

Review is a **structured state** in the card schema. `review_status` records the human's accept/reject decision separately from worker execution state and from any agent recommendation.

---

## The review_status dimension

A card in `done` state carries three orthogonal assessments that are kept separate — execution `status`, `review_status`, and `agent_recommendation` — and they can disagree; why all three are split is argued in [The control plane](../architecture/control-plane.md). This page focuses on the middle one, `review_status` — the field that records the human's accept/reject decision and gates promotion.

**Review state** (`review_status: requested`) says: "The human has not yet decided whether to accept the output" — distinct from `status: done` ("the worker finished") and from `agent_recommendation` (the checker's soft verdict, defined in [The Peer-reviewer](../profiles/peer-reviewer.md)). Collapsing `status` and `review_status` would make "worker finished" and "human approved" the same event — exactly the collapse that makes the system unreliable.

---

## What "blocking" means technically

`review_status: requested` is a blocking state. In practice:

- The dispatcher does not advance a `done` card further until the human changes `review_status`.
- The policy MCP applies `dry_run` to any write targeting review-gated zones regardless of which profile is writing. Even if a worker tried to write directly to `notes/claims/` without the card going through review, the MCP would block it.
- A WIP cap on the `done-awaiting-review` queue limits how many cards can accumulate. When the cap is hit, the dispatcher slows new work on that lane. The cap is back-pressure, not punishment — it keeps the board from racing ahead of the human's review capacity.

Back-pressure is intentional: a full done-awaiting-review queue slows new work
instead of letting unreviewed output masquerade as complete.

---

## What review does not mean

**Review does not mean approval of everything the agent produced.** A human can approve a card while noting that one citation needs to be checked later. Approval means "this is good enough to move forward"; it doesn't mean "every claim in this output is verified."

**Review does not mean the Peer-reviewer checked it.** The Peer-reviewer's `agent_recommendation` is a recommendation that informs human review, not a replacement for it. The human might reject something the Peer-reviewer found clean, or approve something the Peer-reviewer flagged (after reading the flag and deciding it's not significant).

**Review does not happen in the vault.** Review happens on the board card, not on the note itself. A note that has been produced by a reviewed and approved card is not individually marked "reviewed" — the review happened at the card level. This is why it's important to understand cards and notes as distinct things.

---

## Related

- The card lifecycle and state machine: [The board as a state machine (the control plane)](board-as-state-machine.md)
- Why review is schema state: [Why review is a state](../../design/why-review-is-state.md)
- Why the review gate is structural: [Why the review gate is structural](../../design/why-human-gate.md)
- Why synthesis promotion is gated: [Why promotion is gated](../knowledge/promotion-model.md)
- The execution-state breakdown: [Board states and the review gate](../kanban-board/states.md)
- The review_status enum and WIP limits: [Kanban board reference](../../reference/kanban-board.md)
