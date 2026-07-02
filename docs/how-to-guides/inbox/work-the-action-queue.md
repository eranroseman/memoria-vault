---
title: Work the action queue
parent: Inbox
grand_parent: How-to guides
nav_order: 3
---

# Work the action queue

Clear the decisions waiting on you. The daily action surface is the **Inbox**:
task status stays in **Activity**, and only work needing your judgment lands in
**Needs me** as attention projections (`candidate` / `gap` / `work-prompt`) with
`attention_status: open`. Flags and alerts live in **Maintenance** unless they
emit a same-day work prompt. Machine writes go through worker staging and
promotion; PI edits are direct and then observed/backfilled.

## Prerequisites

- Open `candidate`, `gap`, or `work-prompt` attention projections in **Needs me**; task-only status belongs in **Activity**

## Steps

**1. Open the queue and work it as one batch.**

Sit down once and sweep the action queue — high-cardinality decisions belong in one worklist worked in one sitting, never N cards trickling at you ([ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md)).

**2. Read each item the right way round.**

- **Proposals** (`candidate`, `gap`) carry the honesty body — read `argument_against` and `certainty` first; the item existing *is* the recommendation, so there is no verdict field.
- **Work prompts** (`work-prompt`) tell you what finished, blocked, or needs a batch pass. Read the reason, inspect the target, then dismiss it when no action remains.
- **Verification attention** (`flag`, `alert`) is not part of daily **Needs me**. Work it from Maintenance's Drift watch unless it also raises a work prompt for same-day action.

**3. Act, then resolve.**

Acting on an item is whatever the projection proposes — write the link, fix the
note, or queue the discovery task through the worker/plugin. If you still need
the item as a reminder, leave it open. When no action remains, clear it in
place: `Cmd/Ctrl-P` -> **Memoria: resolve inbox card**. The command sets
`attention_status: resolved` and stamps `resolved_at:`, so the Inbox converges
to empty; empty is success.

**4. Reject cleanly.**

Rejecting costs one decision and leaves nothing behind — the proposed write
never landed. If the task behind an item was mis-specified and should be redone,
delegate a corrected worker job through the Co-PI or Inspector rather than
rewriting history.

**5. Mind the back-pressure.**

The board caps `done` cards awaiting you at 5 — when the action queue fills, the dispatcher slows new work on that lane. That's the system protecting your review capacity, not a malfunction. If a lane stalls, clear the queue rather than wishing the cap away.

**6. Watch your own accept/reject pattern.**

Very high acceptance reads as rubber-stamping; very low acceptance means
candidate scoring needs tuning. Use the audit log and action-queue history as
evidence until a standalone runtime summary exists ([Dashboards](../../reference/dashboards.md)).

## Verify

- No Needs me attention projection sits at `attention_status: open` longer than your review cadence (the weekly review is the backstop)
- Every accepted proposal resulted in a checked worker promotion or a change made by your hand; rejected items left nothing behind
- the Inbox's **Needs me** view is empty at the end of the pass

## Related

- Resolving cards from the palette: [Command palette](../using-obsidian/obsidian-command-palette.md)
- Attention projections: [Inbox card fields](../../reference/inbox-card-fields.md)
- Current Concept types: [Document types](../../reference/document-types.md)
- Why review is structural, not a convention: [Why the review gate is structural](../../design/why-review-gate-is-structural.md)
