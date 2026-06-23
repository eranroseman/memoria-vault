---
title: Review link suggestions
parent: Inbox
nav_order: 2
---

# Review link suggestions

**Goal:** decide which of Memoria's proposed links between your claims to accept, and add the accepted ones to the graph yourself.

A **link suggestion** proposes a connection between two claim notes. It is raised by the **Librarian**, a background worker (a **lane**) that scans your claims and proposes links. The Librarian never edits your notes directly. Instead its proposals arrive for you to approve or reject. This is the **link gate**: nothing enters the graph behind your back.

Suggestions reach you in two places. First, as a `[!suggestions]` callout written into a claim note. Second, as cards in the **Inbox**, your review queue. Each card is a **`gap` card** carrying an honest argument for and against the link, not a verdict — you make the call. There are two card kinds: a candidate connection (`link-suggest-claim`) and a surfaced tension (`link-surface-tension`).

This guide is for *triaging Memoria's proposals*. To type a `supports`/`contradicts` link you've already decided on yourself, see [Link related claims](../knowledge/link-related-claims.md) instead.

## Prerequisites

- A claim note with a `[!suggestions]` callout, or Librarian cards in the Inbox. To generate them, run **Memoria: link claim** from a claim note: open the command palette with `Cmd/Ctrl-P` and run it.

## Steps

**1. Open the suggestions in context.**

Run **Memoria: link claim** from the claim note. It writes a collapsed `[!suggestions]` callout listing the top candidate links, then hands off the richer review to the Librarian. Open the callout first, in the note where the link would matter.

If the Librarian also raised cards, open the **Needs me** view of `inbox/inbox.base` on the Inbox queue. Triage the whole batch in one pass. Reviewing them together keeps your judgment sharp ([ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md)).

**2. Read each suggestion before deciding.**

For each callout row or `gap` card, ask: *would I want this link to exist when I come back to either note?* A good link is one a future reading or writing session would actually follow. Read the `argument_against` field first. It carries the most information. Two notes can be very similar and still not be worth linking.

**3. Approve by writing the link yourself.**

To accept a suggestion, *you* open the claim and add the entry to its `links:` map, exactly as you would type one by hand ([Link related claims](../knowledge/link-related-claims.md)). Then resolve the card from `current` to `archived` ([Work the review queue](../inbox/work-the-review-queue.md)). Memoria proposed; your edit to the file is the approval.

**4. Reject the rest. Don't leave them pending.**

Resolve unconvincing cards straight to `archived`. Leaving cards undecided defeats the queue: the Inbox is meant to empty out, and a stale half-reviewed queue is just noise.

**5. Resist approve-all.**

The fleet-health dashboard tracks your accept/reject ratio. A too-high rate means rubber-stamping; a too-low one means the scoring needs tuning. Both are worth acting on ([Dashboards](../../reference/dashboards.md)).

## Verify

- No Librarian card remains at `lifecycle: proposed`
- The latest `[!suggestions]` callout has been read, not mass-approved
- Every approved suggestion exists as a `links:` entry on the claim, written by your hand
- A `contradicts` approval now shows in Knowledge's **Contradictions** view

## Related

**How-to**

- The deliberate, non-proposed path: [Link related claims](../knowledge/link-related-claims.md)
- The callout shape: [Obsidian callouts](../../reference/obsidian-callouts.md)
- Resolving cards from the palette: [Command palette](../using-obsidian/obsidian-command-palette.md)

**Reference**

- The card shapes: [Document types](../../reference/document-types.md)
- The accept-ratio signal: [Dashboards](../../reference/dashboards.md)

**Explanation**

- Why proposals carry arguments, not verdicts: [The honesty card](../../explanation/kanban-board/card-schema.md)
