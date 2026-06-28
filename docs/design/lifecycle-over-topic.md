---
title: Lifecycle, not topic — and state, not folders
parent: Design Book
grand_parent: Developers
nav_order: 20
---

# Lifecycle, not topic — and state, not folders

Two organizational decisions shape the vault: **a note's position in the system is its lifecycle, never its topic**, and **lifecycle is a state property in frontmatter, not a folder**. Folders encode one thing only — the *type-first category* a note belongs to (`catalog/`, `notes/sources/`, `notes/claims/`, …). Where a note stands — `proposed`, `provisional`, `current`, `retracted`, `archived` — is a frontmatter field on the universal chain.

---

## Why folders encode type

Topics are many-to-many; a folder is one location. Memoria therefore reserves
folders for the one fact that is one-to-one: what kind of file this is — catalog
entity, source note, claim, hub, Inbox card. Topics live in frontmatter facets
(`research_area`, `methodology`) and authored links, following the Zettelkasten
link-first inheritance described in [Intellectual
foundations](intellectual-foundations.md#luhmanns-zettelkasten).

---

## Lifecycle lives in frontmatter
The vault's top level is organized by **category** ([ADR-47](../adr/47-type-first-category-folders.md)): one folder per category (`catalog/`, `notes/` with its prose subfolders, `projects/`, `inbox/`, `spaces/`, `system/`), never mixing two categories, with no lifecycle numbers and no archive folder. The full tree is catalogued in [On-disk layout](../reference/on-disk-layout.md). A claim doesn't travel anywhere when the PI retracts it; a source note doesn't become a different kind of thing when it's read. What changes is its *standing* — and standing is a property, not a location.

Direction lives instead in the `lifecycle` frontmatter property — one chain for everything, each type using a subset of it ([ADR-50](../adr/50-universal-lifecycle-and-maturity.md)); the chain and its per-type subsets are defined in [Frontmatter fields](../reference/frontmatter.md). A source note awaiting reading is `proposed`; a claim the PI stands behind is `current`; a claim invalidated by new evidence is `retracted`, with lineage links to its successor.

---

## Why state-not-folders is strictly better

**Promotion is a frontmatter edit, not a file move.** A state change does not move a file, so it cannot break wikilinks, lose Git history continuity, or invalidate saved queries. A note is born in its type-home and dies in its type-home.

**Links survive every transition.** A claim cited by twelve other notes can be retracted, superseded, and archived without a single inbound link breaking. Provenance — the property the whole system is built to protect — does not depend on link-rewriting tooling getting every move right.

**`archived` is a state, not a folder.** An archived note stays exactly where it always lived and simply drops out of active views (Bases and Dataview filter on `lifecycle`). It remains readable, linkable, and traceable from every note that ever cited it — *archive, never delete* with zero file churn.

**Queries get honest.** "What's awaiting me?" is a lifecycle query (`lifecycle: proposed`), "what is this thing?" is a folder fact, and "what's it about?" is a facet query — three different questions, three different mechanisms, none overloaded onto the others.

**The agent's permissions stay tractable.** The gated zones (`notes/claims/`, `notes/hubs/`) are stable paths that never gain or lose members through state changes. The policy gate reasons about *where an agent may write*, and the answer never shifts under it mid-task.

One consequence to know: because Inbox cards use the same lifecycle vocabulary as notes (a card awaiting you is `proposed`), queries that filter on `lifecycle` scope by category folder — which the type-first tree makes trivial.

---

## Topics in frontmatter, not folders

With folders carrying the type and frontmatter carrying the state, topics are encoded as **facets** on source and claim notes:

- `research_area` — seeded from OpenAlex topics by the ingest operation
- `methodology` — a controlled vocabulary covering method and study design
- `topics` on claim notes

Topical *navigation* is built on top by **hubs** (`notes/hubs/`): curated notes that link the relevant sources and claims for an area, regardless of state or project. A hub is authored perspective over the graph, not a folder in disguise.

---

## Related

- The type system the folders encode: [Document types and epistemic roles](../explanation/knowledge/document-types.md)
- How state changes are gated: [Why promotion is gated](../explanation/knowledge/promotion-and-gated-zones.md)
- The decisions: [ADR-47](../adr/47-type-first-category-folders.md), [ADR-50](../adr/50-universal-lifecycle-and-maturity.md)
- The folder tree itself: [The vault](../explanation/architecture/vault.md)
- The facet fields: [Frontmatter fields](../reference/frontmatter.md)
