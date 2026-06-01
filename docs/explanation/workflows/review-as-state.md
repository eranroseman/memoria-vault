---
title: Review as a first-class state
parent: Workflows
---

# Review as a first-class state

In most collaborative systems, "reviewed" is a convention — a comment, a tag, a verbal confirmation. In Memoria, review is a **structured state** in the card schema. The difference is not cosmetic; it is the mechanism that makes review queryable, enforceable, and honest about what has and hasn't been decided.

---

## The problem with review-as-convention

Consider three ways review can be represented:

1. **A comment**: "Looks good" in a card comment.
2. **A tag**: `#reviewed` added to a note.
3. **A field**: `review_status: approved` in structured frontmatter.

Comments and tags share a fatal problem: they are not queryable in a way that can enforce behavior. A Dataview query can find all notes with `review_status: approved` and act on them. A query that depends on "does this note have a `#reviewed` tag?" can be wrong if someone forgot to add the tag, added it before actually reviewing, or removed it. Tags and comments represent *attention*; fields represent *state*.

More critically: comments and tags cannot be used as preconditions by the dispatch system or the policy MCP. The board's dispatcher cannot check "has this card been reviewed?" if review lives in a comment. The policy MCP cannot prevent a write to a review-gated zone if "reviewed" is a convention rather than a field.

---

## Three dimensions, one card

A card in `done` state carries three simultaneous assessments that are kept separate:

**Execution state** (`status: done`) says: "The worker has finished executing the task."

**Review state** (`review_status: requested`) says: "The human has not yet decided whether to accept the output."

**Agent recommendation** (`agent_recommendation`) says: "The checking agent assessed the output as clean/issues-found/inconclusive."

These three can disagree, and they frequently do. A worker finishes (`status: done`); the Verifier finds no issues (`agent_recommendation: clean`; the other values are `issues-found` and `inconclusive`); the human reads the draft and rejects it (`review_status: rejected`). All three are correct — they describe three different assessments at three different times.

Keeping them separate makes each one useful. If `agent_recommendation` folded into `review_status`, you couldn't ask "how often does a clean agent verdict correlate with human approval?" If `status` and `review_status` were collapsed, "worker finished" and "human approved" would be the same event — which is exactly the collapse that makes the system unreliable.

---

## What "blocking" means technically

`review_status: requested` is a blocking state. In practice:

- The dispatcher does not advance a `done` card further until the human changes `review_status`.
- The policy MCP applies `dry_run` to any write targeting review-gated zones regardless of which profile is writing. Even if a worker tried to write directly to `30-synthesis/01-claims/` without the card going through review, the MCP would block it.
- A WIP cap on the `done-awaiting-review` queue limits how many cards can accumulate. When the cap is hit, the dispatcher slows new work on that lane. The cap is back-pressure, not punishment — it keeps the board from racing ahead of the human's review capacity.

The back-pressure mechanism is sometimes misread as a problem (the system slows down). It is the opposite: the cap prevents the worst failure mode (agents producing hundreds of done-awaiting-review cards that the human will never actually review, making the whole queue worthless as a signal).

---

## Post-rejection paths

A rejected card is not "returned to the queue." The human has judged the work wrong, and what happens next is a fresh human decision:

**Supersede**: The human creates a new card on the same lane with a revised specification. The new card carries a reference back to the rejected one. The old card is archived with `archive_reason: superseded`. This is the standard path: the original task spec was wrong, not just the execution.

**Discard**: The work shouldn't have been created. The card is archived with `archive_reason: discarded`. This is the right path when the human decides the task itself was mistaken.

There is no path "back to the worker" — a worker cannot be told "do the same thing but better" without a new specification. Revision is not iteration; it is a fresh task with clearer constraints.

This is different from a **retry**, which is automatic re-dispatch of the same card after a transient failure (a rate-limited API, a timeout, a lookup that failed). Retries use the same card; rejections create new ones. The difference: retries address execution failures; rejections address quality failures.

---

## What review does not mean

**Review does not mean approval of everything the agent produced.** A human can approve a card while noting that one citation needs to be checked later. Approval means "this is good enough to move forward"; it doesn't mean "every claim in this output is verified."

**Review does not mean the Verifier checked it.** The Verifier's `agent_recommendation` is a recommendation that informs human review, not a replacement for it. The human might reject something the Verifier found clean, or approve something the Verifier flagged (after reading the flag and deciding it's not significant).

**Review does not happen in the vault.** Review happens on the board card, not on the note itself. A note that has been produced by a reviewed and approved card is not individually marked "reviewed" — the review happened at the card level. This is why it's important to understand cards and notes as distinct things.

---

## Related

- The card lifecycle and state machine: [board-as-state-machine.md](board-as-state-machine.md)
- Why the review gate is structural: [../architecture/why-human-gate.md](../architecture/why-human-gate.md)
- Why synthesis promotion is gated: [../knowledge/promotion-model.md](../knowledge/promotion-model.md)
- The execution-state breakdown: [states.md](../kanban-board/states.md)
- The review_status enum and WIP limits: [kanban-board.md](../../reference/kanban-board.md)
