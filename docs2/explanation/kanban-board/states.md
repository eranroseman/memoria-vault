
# Board states and the review gate

This page explains why the board's state machine is shaped the way it is: why execution and review are two separate lifecycles, what each state transition represents, why the review gate has five rules, and why the WIP limits are set where they are. For the state lookup tables — the `status` enum, the `review_status` enum, the lane-assignment table, and the WIP-cap values — see the [board-states reference](../../../docs/reference/board-states.md).

---

## The execution lifecycle

The execution lifecycle is linear with two escape edges. This is deliberate:

**`triage → todo → ready` exists so work is never dispatched before it's specified.** The dispatcher ignores `triage` cards. This is not a limitation — it is what makes "specify before release" enforceable rather than advisory. A `triage` card will never be accidentally claimed by a worker; only a human's deliberate release moves it to `ready`.

**Retries are not a distinct state.** A recoverable run failure returns the card to `ready` for re-dispatch on the same card. A transient failure looks like a re-queue rather than a new state to reason about. Only unrecoverable failures — those that require human judgment before work can continue — move the card to `blocked`.

**`blocked` exists for failures a worker cannot resolve alone.** When the dispatcher escalates a card to `blocked` (after `max_retries`, or when the worker explicitly signals an unresolvable problem), it carries a reason. Only a human can clear it back to `ready`. This is the board's mechanism for surfacing stuck work rather than letting it silently fail or retry forever.

---

## The review lifecycle

The review lifecycle only becomes meaningful once `status` reaches `done`. This separation is what lets a worker make progress on a card without implying anything about whether the human will accept it.

The five rules of review:

**1. Agent recommendation and human acceptance are separate.** `agent_verdict: approve` (from Verifier or Linter) and `review_status: approved` (from the human) are not the same thing and cannot substitute for each other. The agent recommends; the human decides. A card with agent approval but no human approval is waiting for review — that is the normal state after a checked artifact.

**2. Review is a state, not a comment.** A card is canonical only after `review_status: approved` is set, not because a worker claimed to finish or because a comment said "looks fine." The field is authoritative; comments are not.

**3. Review states block dispatch.** Cards in `done` (awaiting review), `blocked`, `triage`, or `todo` are not claimable by any worker. Hermes enforces the execution states; Memoria's policy MCP additionally blocks dispatch from review-pending zones.

**4. Review has ownership.** The reviewing party is recorded in `review_owner` — human, Verifier, or Linter depending on the card type. The board can always show who owes the next decision.

**5. Rejection starts a new card.** A rejected card is archived. Any rework begins on a fresh card with a revised spec. The original is never quietly reopened. This is what keeps the audit trail honest: each card represents one attempt, with a stated outcome.

---

## Why the WIP limits

Three distinct caps, each motivated by a different failure mode:

**Active per profile = 1.** The strictest cap, and the only one Hermes enforces natively. Parallel runs of the same profile would contend for the same write scope and make the audit trail ambiguous about which run touched what file. Keeping one `running` card per profile at a time keeps the per-write attribution unambiguous.

**Review-queue depth (bounded).** The bottleneck is human attention, not machine capacity. An unbounded review queue grows faster than a human can clear it, and the excess silently converts "reviewed" into "rubber-stamped." When the queue depth exceeds its cap, the dispatcher delays new card creation on that lane — back-pressure that forces the queue depth to become visible before it becomes invisible.

**Writer lane (bounded).** Too many drafts in flight simultaneously means synthesis quality drops because evidence cannot be fully integrated. A writer working on many drafts integrates none of them well. The cap protects synthesis quality, not throughput.

---

## Socratic is not a board lane

Socratic runs synchronously through the ACP pane — the human opens it, converses, and closes it. It never appears on the board, never claims a card, and never produces a `done` card. Its write-denial and interactive-only routing make it architecturally incompatible with board dispatch. This is not a gap; it is the design.

---

## Related

- Conceptual overview: [README.md](README.md)
- Card fields: [card-schema.md](card-schema.md)
- Why no Reviewer: [README.md § why no Reviewer and no Orchestrator](README.md#why-no-reviewer-and-no-orchestrator)
- Board-states lookup table: [reference/board-states](../../../docs/reference/board-states.md)
- Recovery for stuck cards: [how-to-guides/recovery/fix-stuck-card](../../how-to-guides/recovery/fix-stuck-card.md)
