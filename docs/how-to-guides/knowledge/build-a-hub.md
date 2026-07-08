---
title: Build a hub
parent: Knowledge
grand_parent: How-to guides
nav_order: 4
---

# Build a hub

Curate a `hub` Concept in `hubs/` that gives a dense checked-note
cluster a stable entry point: what the topic holds, what's settled, and what's
still contested. The worker may suggest hub updates, but the PI owns curation.

## When to create a hub

When a topic has accumulated a handful of checked notes that belong together.
Earlier is premature structure; much later and the cluster is already hard to
navigate.

## Steps

**1. Create the hub.**

Use the CLI:

```bash
memoria new hub receptivity-timing --workspace .
```

Or create a Markdown file in `hubs/` with the same required shape:

```yaml
type: hub
id: <ULID>
title: <topic title>
description: <one-sentence topic shape>
tags: []
links: {}
tag: <topic-tag>
```

**2. Name it after the topic.**

Use the topic slug directly, for example `receptivity-timing.md` — the folder already says what it is.

**3. Write the shape of the topic.**

Two to four sentences in the **Shape of the topic** section: what this cluster is about, how the member claims relate, what's settled, what's still contested.

**4. Curate the membership.**

Use the hub's `tag` as the stable membership key. Add that tag to checked notes
and digests that genuinely belong in the cluster, then write the curated hub
body to explain why those items belong together. Curate: omit tangentially
related notes; one strong hub beats a complete-but-noisy one.

**5. Name the gaps.**

Note what the cluster is missing — thin sub-topics, open questions, papers not
yet captured. Each named gap is input for Ask, gap analysis, or the next source
capture pass.

## Splitting a hub

When one branch of a hub grows past ~15-20 member notes, split it: create a new
hub for the branch, give it a narrower `tag`, apply that tag to those notes, and
in the parent link to the child hub instead of trying to enumerate every item.

## Owners

You author and curate hubs. Machine synthesis is a suggestion; the worker does
not overwrite curated hub judgment.

## Verify

- The hub validates: `type: hub`, a stable ULID `id`, `tag: <topic-tag>`, `tags: []`, and `links: {}`
- Every intended member has the hub tag and is checked in the DB/read API
- The member notes link back (open the backlinks panel on the hub)
- The hub shows up where you'd look for the topic — link it from `steering.md` or a parent hub if not

## Related

- The note links that fill it: [Link checked notes](../knowledge/link-checked-notes.md)
- The hub type and schema: [Document types](../../reference/document-types.md)
- Why hubs matter to the cycle: [The knowledge cycle](../../explanation/knowledge/knowledge-cycle.md)
