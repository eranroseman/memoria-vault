---
title: Why hubs
parent: Knowledge
grand_parent: Explanation
nav_order: 8
---

# Why hubs

The vault organizes notes type-first into category folders and carries topic in links and frontmatter, not in folders ([Lifecycle, not topic — and state, not folders](lifecycle-over-topic.md)). That choice buys a lot — a claim can belong to many topics at once, and reorganizing a topic never means moving files — but it removes the thing a folder quietly provided: a place to *go* when you want to see everything about a subject. A **hub** is that place, rebuilt as a first-class note. This page explains why the vault needs a human-curated navigation layer at all, and why hubs are authored rather than generated.

> **Lineage.** The hub is Memoria's name for the **Map of Content** from the evergreen-notes tradition, itself descended from Luhmann's structure notes ([Intellectual foundations](../overview/intellectual-foundations.md#luhmanns-zettelkasten)). As elsewhere in the knowledge model, the method is borrowed; what Memoria adds is the *delegation boundary* — which parts of maintaining a Map of Content an agent may help with, and which it may not.

---

## A hub is navigation, not retrieval

The vault already has machine ways to gather notes on a topic: [Search](../../reference/search.md) ranks notes by text similarity, [Clustering](../../reference/clustering.md) computes communities over the typed graph, and a Dataview or Bases view lists every note matching a field. All three are fast, and all three are *re-derived on demand* — you run the query, read the result, and the result evaporates.

A hub is the opposite kind of object. It is a durable note you return to, and what it adds over any query is **perspective a query cannot produce**: a framing of what the cluster is about, a curation of what matters most in it right now, and a diagnosis of where it is thin or contested ([Note body structure](note-body-structure.md#why-hubs-answer-three-distinct-questions)). A hub that is merely a flat list of links is a failed hub — no one opens it, because a Base does the same listing faster. The value is in the judgment: *these* notes belong, in *this* framing, with *these* gaps still open.

So the division of labor is clean. Retrieval (search, clustering, queries) answers "what notes touch this topic?" — a question machines answer well. Navigation (hubs) answers "what does this topic *hold*, and where should I look first?" — a question that is an act of synthesis. Keeping them separate is what lets the machine surfaces stay ephemeral and the hub stay a stable, curated home.

---

## Why curation can't be delegated

Hubs live under `notes/hubs/`, which is a review-gated prefix: an agent's write there degrades to a dry-run ([Note types and epistemic roles](note-types.md), [Wikilink and link conventions](../../reference/linking.md)). That is deliberate, and it follows directly from what a hub is for. The curation *is* the hub — the framing and the "why these belong together" annotations are the entire value-add over a query. An agent can list the notes that mention a topic, but a list that *looks* curated without being curated is worse than no hub: it invites the reader to trust an organization no one actually performed, which is precisely the "hub-as-folder-dump" failure the design warns against ([Common pitfalls](common-pitfalls.md)).

This is why the agent's role around hubs stops at the threshold of judgment. The Librarian's `map` lane can notice that a cluster has grown dense and propose that a hub is due — but the proposal it is allowed to make is a **bare member list plus the threshold evidence**, written to staging, never the annotations and never into `notes/hubs/` itself ([Agent-proposed hubs](../../adr/19-moc-threshold-alert.md)). The human writes the framing, curates the membership, and names the gaps. The agent absorbs the bookkeeping (counting notes per topic) that the system is built to absorb; it does not absorb the synthesis, which is the part that defines the type.

---

## Why a threshold, not on-demand or always-on

A hub is worth creating only when there is something to navigate. Below roughly **15–20 notes** on a topic, the friction of a missing hub is lower than the cost of maintaining a premature one — an early hub is structure imposed before the shape of the topic is known, and it has to be rebuilt as the cluster actually forms ([Wikilink and link conventions](../../reference/linking.md#hub-thresholds)). Much past that, the cluster is already hard to move through, and the hub arrives late.

Rather than make the human watch note counts by hand, the Linter's `hub-threshold` detector makes the crossing visible — "topic *X* has 18 notes and no hub; consider one" — as a low-priority advisory, never an auto-creation ([Agent-proposed hubs](../../adr/19-moc-threshold-alert.md)). The threshold is a prompt to the human's judgment, not a trigger for the machine's. The same logic governs splitting: when one branch of a hub outgrows it, the hub spawns a child hub and the parent links to it, so navigation scales as a shallow hierarchy of curated maps rather than one ever-growing list.

---

## Where hubs sit in the knowledge model

Hubs are the navigational layer over the durable knowledge the vault accumulates. Claims are the atomic units — what the PI has come to think, in their own words ([Why promotion is gated](promotion-model.md)); hubs are how those units stay findable and legible as they multiply, the difference between a vault that compounds and one that merely accumulates ([The knowledge cycle](knowledge-cycle.md)). They are the one structural note type the human owns end to end, because navigation of one's own knowledge is not a task that survives being handed off. To build one in practice, see [Build a hub](../../how-to-guides/knowledge/build-a-moc.md).

---

## Related

- The folder-light, link-first organization that makes hubs necessary: [Lifecycle, not topic — and state, not folders](lifecycle-over-topic.md)
- What the three hub body sections each make the note able to do: [Note body structure](note-body-structure.md#why-hubs-answer-three-distinct-questions)
- The hub-as-folder-dump failure mode: [Common pitfalls](common-pitfalls.md)
- The machine surfaces a hub is *not*: [Search](../../reference/search.md), [Clustering](../../reference/clustering.md)
- Building one: [Build a hub](../../how-to-guides/knowledge/build-a-moc.md)
