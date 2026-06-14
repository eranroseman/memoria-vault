---
title: Build a hub
parent: Curate
nav_order: 3
---

# Build a hub

Create a structure note in `notes/hubs/` that gives a dense claim cluster a stable entry point — a navigational home that says what a topic holds, what's settled, and what's still fighting. Like claims, hubs are review-gated: agents only propose; you author (the hub is the renamed MOC, [ADR-50](../../adr/50-universal-lifecycle-and-maturity.md)).

## When to create a hub

When a topic has accumulated a handful of claims that belong together — typically by the third or fourth settled claim on one topic. Earlier is premature structure; much later and the cluster is already hard to navigate.

## Steps

**1. Create the note from the template.**

In `notes/hubs/`, create a new note from `system/templates/hub.md`:

```yaml
type: hub
lifecycle: current
topic: <your-topic>
members: []
links: {}
```

**2. Name it after the topic.**

`receptivity-timing.md`, not `receptivity-timing-moc.md` — the folder already says what it is.

**3. Write the shape of the topic.**

Two to four sentences in the **Shape of the topic** section: what this cluster is about, how the member claims relate, what's settled, what's still contested.

**4. List the members.**

Add the claim notes (and key source notes) to the `members` list and wikilink them in the **Members** section. Curate — omit tangentially related notes; one strong hub beats a complete-but-noisy one.

**5. Name the gaps.**

Note what the cluster is missing — thin sub-topics, open questions, papers not yet captured. Each named gap is a ready-made discovery prompt for the Co-PI ([Find new sources](../compile/find-new-sources.md)).

## Splitting a hub

When one branch of a hub grows past ~15–20 member claims, split it: create a new hub for the branch, move those members over, and in the parent replace the individual links with one link to the child hub.

## Owners

You author and curate hubs. The Librarian's `map` lane can propose that a cluster deserves one (a `gap` card in the Inbox), and the Linter's `graph-analyze` detector flags orphan hubs with zero inlinks — but every structural decision is yours.

## Verify

- The hub validates: `type: hub`, `topic` set, every `members` entry resolving to a real note
- The member claims link back (open the backlinks panel on the hub)
- The hub shows up where you'd look for the topic — link it from `research-focus.md` or a parent hub if not

## Related

- The claims that fill it: [Advance a claim to evergreen](../compile/promote-a-claim.md)
- The hub type and schema: [Note types](../../reference/note-types.md)
- Why hubs matter to the cycle: [The knowledge cycle](../../explanation/knowledge/knowledge-cycle.md)
