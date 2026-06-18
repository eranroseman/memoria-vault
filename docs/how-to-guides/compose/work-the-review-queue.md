---
title: Work the review queue
parent: Compose
nav_order: 8
---

# Work the review queue

Clear the decisions waiting on you. The review surface is the **Inbox**: agents finish board cards, and what needs your judgment lands as typed cards (`candidate` / `gap` / `flag` / `alert`) at `lifecycle: proposed`. Anything an agent wanted to write into a **review-gated zone** (`notes/claims/`, `notes/hubs/`) was degraded to `dry_run` by the policy MCP — the proposal reaches you as a card; the write only happens by your hand.

## Prerequisites

- Cards in the Inbox at `lifecycle: proposed` (the **Needs me** view of `inbox/inbox.base` on the Inbox gate)

## Steps

**1. Open the queue and work it as one batch.**

Sit down once and sweep the queue — high-cardinality decisions belong in one worklist worked in one sitting, never N cards trickling at you ([ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md)).

**2. Read each card the right way round.**

- **Proposals** (`candidate`, `gap`) carry the honesty body — read `argument_against` and `certainty` first; the card existing *is* the recommendation, so there is no verdict field.
- **Verification cards** (`flag`, `alert`) lead with the `finding` and carry an `agent_recommendation` — a recommendation, never the decision ([Inbox card fields](../../reference/inbox-card-fields.md)). You can reject a `clean` and accept an `issues-found`.

**3. Act, then resolve.**

Acting on a card is whatever the card proposes — write the link, fix the claim, queue the discovery task, apply the gated write yourself. Then flip the card in place: `Cmd/Ctrl-P` → **Memoria: resolve inbox card** sets your outcome (`current` = accepted, `archived` = rejected / done) and stamps `resolved:`. You don't archive accepted cards by hand: the archival sweep flips resolved `current` cards to `lifecycle: archived` once the stamp is older than `inbox.archive_after_days` (default 30, set in calibration.yaml), so accepted verdicts stay visible while fresh and the Inbox converges to empty; empty is success.

**4. Reject cleanly.**

Rejecting costs one decision and leaves nothing behind — the proposed write never landed. If the *task* behind a card was mis-specified and should be redone, delegate a corrected card via the Co-PI; on the board, rejection spawns a new card (`supersedes:` the original) rather than re-running the old one, so the audit trail can't lie.

**5. Mind the back-pressure.**

The board caps `done` cards awaiting you at 5 — when the queue fills, the dispatcher slows new work on that lane. That's the system protecting your review capacity, not a malfunction. If a lane stalls, clear your queue rather than wishing the cap away.

**6. Watch your own accept rate.**

The fleet-health dashboard tracks accept/reject ratios per proposing lane — very high acceptance reads as rubber-stamping, very low means candidate scoring needs tuning ([Dashboards](../../reference/dashboards.md)). Both are signals to act on.

## Verify

- No card sits at `lifecycle: proposed` longer than your review cadence (the weekly review is the backstop)
- Every accepted proposal resulted in a change made by your hand; rejected cards left nothing behind
- the Inbox's **Needs me** view is empty at the end of the pass

## Related

- Resolving cards from the palette: [Command palette](../using-obsidian/obsidian-command-palette.md)
- The card shapes and their fields: [Note types](../../reference/note-types.md)
- The gate that holds agent writes: [Policy MCP](../../reference/policy-mcp.md)
- Why review is structural, not a convention: [Why a human gate](../../explanation/rationale/why-human-gate.md)
