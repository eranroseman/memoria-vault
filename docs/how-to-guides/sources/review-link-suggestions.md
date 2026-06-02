---
title: How to review link suggestions
parent: Sources
---

# How to review link suggestions

Work through the `[!suggestions]` callout the Librarian attaches to a note — approving the candidate links that belong and rejecting the rest. This is the curation step that turns proposed connections into real wikilinks without rubber-stamping.

This is different from [linking related claims](link-related-claims.md): that guide is for *manually* typing a `supports`/`contradicts` relation you've decided on; this one is for *triaging the agent's proposals*.

## Prerequisites

- A note carrying a `[!suggestions]` callout (the Librarian attaches one after an `enrich` or weekly link pass)
- The Callout Manager plugin active ([How to set up Obsidian](../setup/set-up-obsidian.md))

## Steps

**1. Open the note and expand the callout.**

The `[!suggestions]` callout sits at the bottom of the note and is **collapsed by default** — this is deliberate, so you don't approve a wall of links at a glance. Click to expand it. It holds at most five forward candidates (this note → others) and five backward (others → this note), each with Approve / Reject affordances.

**2. Read each candidate before deciding.**

For each candidate, ask: *would I want this link to exist when I come back to either note?* A good link is one a future reading session would actually traverse. The agent ranked these by similarity and shared citations, but relevance is your call — a high-similarity pair can still be a link not worth making.

**3. Approve the ones that belong.**

Approving writes the wikilink into the note body (and, for a backward suggestion, queues the reciprocal edit on the other note). Approve only what you'd have linked by hand.

**4. Reject the rest — don't leave them pending.**

Reject removes the candidate from the callout. Leaving candidates undecided defeats the mechanism: a stale half-reviewed callout is noise the next time you open the note. Clear the callout to empty in one pass.

**5. Resist approve-all.**

There is a `Memoria: approve all link suggestions` command, but use it only when you've already read the list and genuinely want every candidate. A reflexive approve-all is exactly the rubber-stamping the collapsed-by-default design exists to prevent — and the [fleet-health dashboard](../../explanation/dashboards/operational-health/fleet-health.md) tracks your accept rate as a trust-score signal (a rate near 100% reads as rubber-stamping; see the [reference cutoffs](../../reference/obsidian-callouts.md#drift-signals)).

## Verify

- The `[!suggestions]` callout on the note is empty (every candidate approved or rejected)
- Approved links appear as wikilinks in the note body
- For approved backward suggestions, the reciprocal link exists on the other note

## Related

**How-to**

- Manually type a claim relation (the deliberate, non-proposed path): [How to link related claims (typed relations)](link-related-claims.md)
- Where suggestions come from in the intake flow: [How to capture and ingest a source](capture-and-ingest.md)

**Reference**

- Callout field shapes, scoring weights, drift cutoffs: [Obsidian callouts](../../reference/obsidian-callouts.md)

**Explanation**

- Why suggestions are collapsed and producer-owned: [Callouts](../../explanation/obsidian/callouts.md)
- How the accept/reject ratio feeds the trust score: [fleet-health dashboard](../../explanation/dashboards/operational-health/fleet-health.md)
