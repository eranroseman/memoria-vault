---
title: Review link suggestions
parent: Inbox
nav_order: 2
---

# Review link suggestions

Work through the `[!suggestions]` callout and link proposals the Librarian's **`link` lane** raises — candidate connections (`link-suggest-claim`) and tensions (`link-surface-tension`) — approving the ones that belong and rejecting the rest. This is the curation step that turns proposed connections into real `links:` entries without rubber-stamping.

This is different from [Link related claims](../knowledge/link-related-claims.md): that guide is for *manually* typing a `supports`/`contradicts` link you've decided on; this one is for *triaging the agent's proposals*.

Because `notes/claims/` is review-gated, the link lane can't touch your `links:` maps — its findings land as Inbox cards instead: a suggested connection as a **`gap`** proposal carrying the honesty body — never a verdict ([Frontmatter fields](../../reference/frontmatter.md)) — a surfaced tension leading with the `finding`.

## Prerequisites

- A claim note with a `[!suggestions]` callout from `Cmd/Ctrl-P` → **Memoria: link claim**, or link-lane cards in the Inbox from the delegated `link` lane

## Steps

**1. Open the suggestions in context.**

Run **Memoria: link claim** from the claim note. The command writes a collapsed `[!suggestions]` callout with deterministic top-K candidates, then delegates the richer link-lane review. Open the callout first, in the note where the edge would matter.

If the lane also raised cards, open the **Needs me** view of `inbox/inbox.base` on the Inbox queue. Triage the batch together — the one-pass discipline keeps your judgment sharp ([ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md)).

**2. Read each candidate before deciding.**

For each callout row or proposed link card, ask: *would I want this edge to exist when I come back to either note?* A good link is one a future reading or writing session would actually traverse. Read `argument_against` first — it's the information-bearing field; high similarity can still be a link not worth making.

**3. Approve by writing the link yourself.**

Accepting a proposal means *you* open the claim and add the entry to its `links:` map, exactly as you would type one by hand ([Link related claims](../knowledge/link-related-claims.md)). Then resolve the card to `current` → `archived` ([Work the review queue](../inbox/work-the-review-queue.md)). The agent proposed; your hand on the file is the approval.

**4. Reject the rest — don't leave them pending.**

Resolve unconvincing cards straight to `archived`. Leaving cards undecided defeats the mechanism: the Inbox converges to empty, and a stale half-reviewed queue is noise.

**5. Resist approve-all.**

The fleet-health dashboard tracks your accept/reject ratio as a trust-score signal — both a too-high rate (rubber-stamping) and a too-low one (scoring needs tuning) are worth acting on ([Dashboards](../../reference/dashboards.md)).

## Verify

- No link-lane card remains at `lifecycle: proposed`
- The latest `[!suggestions]` callout has been read, not mass-approved
- Every approved proposal exists as a `links:` entry on the claim, in your hand
- A `contradicts` approval now shows on `system/dashboards/contradictions.md`

## Related

**How-to**

- The deliberate, non-proposed path: [Link related claims](../knowledge/link-related-claims.md)
- The callout shape: [Obsidian callouts](../../reference/obsidian-callouts.md)
- Resolving cards from the palette: [Command palette](../using-obsidian/obsidian-command-palette.md)

**Reference**

- The card shapes: [Note types](../../reference/note-types.md)
- The accept-ratio signal: [Dashboards](../../reference/dashboards.md)

**Explanation**

- Why proposals carry arguments, not verdicts: [The honesty card](../../explanation/kanban-board/card-schema.md)
