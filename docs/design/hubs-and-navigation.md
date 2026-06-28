---
title: Why hubs
parent: Design Book
grand_parent: Developers
nav_order: 21
---

# Why hubs

The vault organizes notes by type and carries topic in links and frontmatter, not folders ([Lifecycle, not topic — and state, not folders](lifecycle-over-topic.md)). That keeps claims reusable across topics and avoids file moves during reorganization. It also removes one useful folder affordance: a place to *go* for a subject. A **hub** restores that place as a first-class note.

> **Lineage.** The hub is Memoria's name for the **Map of Content** from the evergreen-notes tradition, itself descended from Luhmann's structure notes ([Intellectual foundations](intellectual-foundations.md#luhmanns-zettelkasten)). As elsewhere in the knowledge model, the method is borrowed; what Memoria adds is the *delegation boundary* — which parts of maintaining a Map of Content an agent may help with, and which it may not.

---

## A hub is navigation, not retrieval

| Surface | Answers | Lifespan |
| --- | --- | --- |
| Search, clustering, Bases | "What notes touch this topic?" | Re-derived on demand. |
| Hub | "What does this topic hold, and where should I look first?" | Durable, curated note. |

A hub adds perspective a query cannot produce: framing, curation, and a diagnosis of thin or contested areas ([Note body structure](../explanation/knowledge/note-body-structure.md#why-hubs-answer-three-distinct-questions)). A flat link list is a failed hub; a Base can list links faster.

---

## Why curation can't be delegated

Hubs live under `notes/hubs/`, a review-gated prefix: an agent write there degrades to a dry-run ([Document types and epistemic roles](../explanation/knowledge/document-types.md), [Wikilink and link conventions](../reference/wikilink-and-link-conventions.md)). That follows from what a hub is for. The curation *is* the hub: framing, membership, and "why these belong together" annotations. A generated list that looks curated is worse than no hub because it asks the reader to trust organization no one performed ([Common pitfalls](../explanation/knowledge/common-pitfalls.md)).

So the agent stops at the threshold of judgment. The Librarian's `map` lane may propose that a dense cluster needs a hub, but only as a **bare member list plus threshold evidence** in staging ([Agent-proposed hubs](../adr/19-moc-threshold-alert.md)). The human writes the framing, curates membership, and names gaps.

---

## Why a threshold, not on-demand or always-on

| Timing | Problem |
| --- | --- |
| Too early | The topic's shape is not known, so the hub becomes premature structure. |
| Too late | The cluster is already hard to navigate. |
| Threshold crossing | The Linter can prompt the human without auto-creating the hub. |

The current threshold is roughly **15-20 notes** ([Wikilink and link conventions](../reference/wikilink-and-link-conventions.md#hub-thresholds)). It is advisory only: when one branch grows too large, the human splits it into a child hub rather than letting one map become a dumping ground.

---

## Where hubs sit in the knowledge model

Claims are the atomic units: what the PI has come to think, in their own words ([Why promotion is gated](../explanation/knowledge/promotion-and-gated-zones.md)). Hubs keep those units findable as they multiply. They are human-owned end to end because navigation of one's own knowledge does not survive full delegation. To build one, see [Build a hub](../how-to-guides/knowledge/build-a-hub.md).

---

## Related

- The folder-light, link-first organization that makes hubs necessary: [Lifecycle, not topic — and state, not folders](lifecycle-over-topic.md)
- What the three hub body sections each make the note able to do: [Note body structure](../explanation/knowledge/note-body-structure.md#why-hubs-answer-three-distinct-questions)
- The hub-as-folder-dump failure mode: [Common pitfalls](../explanation/knowledge/common-pitfalls.md)
- The machine surfaces a hub is *not*: [Search](../reference/search.md), [Clustering](../reference/clustering.md)
- Building one: [Build a hub](../how-to-guides/knowledge/build-a-hub.md)
