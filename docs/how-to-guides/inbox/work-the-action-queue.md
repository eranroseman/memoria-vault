---
title: Work the action queue
parent: Inbox
grand_parent: How-to guides
nav_order: 2
---

# Work the action queue

Clear the Inbox items waiting on your judgment. Work this guide when **Needs
me** has open proposals, gaps, or work prompts.

## Prerequisites

- Open `candidate`, `gap`, or `work-prompt` attention items in **Needs me**

## Steps

**1. Open the queue and work it as one batch.**

Sweep the action queue in one sitting when you can. Many tiny review prompts are
easier to judge consistently as one worklist.

**2. Read the reason before the recommendation.**

For a proposal, read the uncertainty and counterargument before accepting it. For
a work prompt, inspect the target and the reason it needs attention.

**3. Act, then resolve.**

Acting on an item is whatever the projection proposes — write the link, fix the
note, or queue the discovery task through the CLI/worker. If you still need the
item as a reminder, leave it open. When no action remains, clear it with an
explicit outcome:

```bash
memoria attention resolve --workspace <vault> <attention-path> --apply
```

Use `--reject` when the proposed action should not land, or `--defer --reason
"..."` when it should stay out of the active queue until a later pass. The
command records the PI disposition and stamps resolution metadata, so the Inbox
converges to empty; empty is success.

**4. Reject cleanly when the proposal is wrong.**

Rejecting costs one decision and leaves nothing behind — the proposed write
never landed. If a request was mis-specified, as PI create a corrected successor
instead of rewriting it:

```bash
memoria request amend --workspace <vault> --idempotency-key <new-request-key> \
  <request-id> field=value
```

A pending source request is cancelled as superseded; a terminal source remains
terminal and is marked as superseded. Retry only when its original arguments
remain correct.

**5. Clear back-pressure before adding more work.**

The action queue intentionally back-pressures new work when too many finished
requests still need your judgment. That's the system protecting your review
capacity, not a malfunction. If work appears stalled, clear or resolve the open
attention items before adding more requests.

## Verify

- No Needs me item sits open longer than your review cadence
- Every accepted proposal resulted in a checked worker promotion or a change made by your hand; rejected items left nothing behind
- the Inbox's **Needs me** view is empty at the end of the pass

## Related

- CLI command reference: [CLI](../../reference/commands-and-transports/cli.md)
- Request and attention state: [Control plane reference](../../reference/control-and-policy/control-plane.md)
- Current Concept types: [Document types](../../reference/data-model/document-types.md)
- Why review is structural, not a convention: [Why the review gate is structural](../../explanation/rationale/boundaries/why-review-gate-is-structural.md)
