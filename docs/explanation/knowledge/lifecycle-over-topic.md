---
title: Lifecycle, not topic — and state, not folders
parent: Knowledge
nav_order: 4
---

# Lifecycle, not topic — and state, not folders

Two organizational decisions shape the vault. The first survives from the earliest design: **a note's position in the system is its lifecycle, never its topic**. The second is newer (ADR-47/ADR-50) and changes the mechanism: **lifecycle is a state property in frontmatter, not a folder**. Folders now encode one thing only — the *type-first category* a note belongs to (`catalog/`, `notes/source/`, `notes/claims/`, …). Where a note stands — `proposed`, `provisional`, `current`, `retracted`, `archived` — is a frontmatter field on the universal chain.

---

## Why topic folders fail

Topic folders seem natural. "Put all my cognitive science notes in `cognitive-science/`." The problem is that topics are **many-to-many**:

A paper on attention and working memory belongs in `cognitive-science/`, and in `neuroscience/`, and in `HCI/`, and possibly in a project's orbit if it's relevant to current work. A topic folder forces a choice: pick one folder and lose the connections to the others, or create duplicates that immediately diverge.

Most knowledge systems respond by letting notes exist in multiple places (aliases, copies) or by moving topics to tags. But that creates a different problem: the folder is now redundant. If topics live in frontmatter and links, the folder adds no information. If the folder adds information, it must mean something other than topic.

**What a folder can uniquely encode is what a note *is*.** A note is exactly one kind of thing: a catalog entity, a source note, a claim, a hub, an Inbox card. That one-to-one fact is the folder's job. Topics live in frontmatter facets (`research_area`, `methodology`) and in links, where many-to-many can be expressed properly. This is the part of the original decision that survives unchanged — and it is itself a **Zettelkasten** inheritance: Luhmann's slip-box had no subject folders, only a web of cross-references, precisely because a fixed hierarchy can't express a note's many relationships (see [Intellectual foundations](../overview/intellectual-foundations.md#luhmanns-zettelkasten)).

---

## What changed: lifecycle moved out of the folder names

v0.1.0-alpha.1 encoded lifecycle stage in numbered folders (`10-inbox/ → 20-sources/ → 30-synthesis/ → 50-deliverables/`), and promotion meant moving the file forward. The design update found the flaw: numbered folders imply a **pipeline**, and the knowledge is a **network**. A claim doesn't travel anywhere when the PI retracts it; a source note doesn't become a different kind of thing when it's read. What changes is its *standing* — and standing is a property, not a location.

So the vault's top level is now organized by **category** ([ADR-47](../../adr/47-type-first-category-folders.md)): one folder per category (`catalog/`, `notes/` with its prose subfolders, `projects/`, `inbox/`, `system/`), never mixing two categories, with no lifecycle numbers and no archive folder. The full tree is catalogued in [On-disk layout](../../reference/on-disk-layout.md).

Direction lives instead in the `lifecycle` frontmatter property — one chain for everything, each type using a subset of it ([ADR-50](../../adr/50-universal-lifecycle-and-maturity.md)); the chain and its per-type subsets are defined in [Frontmatter fields](../../reference/frontmatter.md). A source note awaiting reading is `proposed`; a claim the PI stands behind is `current`; a claim invalidated by new evidence is `retracted`, with lineage links to its successor.

---

## Why state-not-folders is strictly better

**Promotion is a frontmatter edit, not a file move.** Under the numbered-folder model, every state change moved a file — and every move risked breaking wikilinks, losing Git history continuity, and invalidating saved queries. Under the state model, nothing moves. A note is born in its type-home and dies in its type-home.

**Links survive every transition.** A claim cited by twelve other notes can be retracted, superseded, and archived without a single inbound link breaking. Provenance — the property the whole system is built to protect — no longer depends on link-rewriting tooling getting every move right.

**`archived` is a state, not a folder.** The old `95-archive/` is gone. An archived note stays exactly where it always lived and simply drops out of active views (Bases and Dataview filter on `lifecycle`). It remains readable, linkable, and traceable from every note that ever cited it — *archive, never delete* with zero file churn.

**Queries get honest.** "What's awaiting me?" is a lifecycle query (`lifecycle: proposed`), "what is this thing?" is a folder fact, and "what's it about?" is a facet query — three different questions, three different mechanisms, none overloaded onto the others.

**The agent's permissions stay tractable.** The gated zones (`notes/claims/`, `notes/hubs/`) are stable paths that never gain or lose members through state changes. The policy gate reasons about *where an agent may write*, and the answer never shifts under it mid-task.

One consequence to know: because Inbox cards use the same lifecycle vocabulary as notes (a card awaiting you is `proposed`), queries that filter on `lifecycle` scope by category folder — which the type-first tree makes trivial.

---

## Topics in frontmatter, not folders

With folders carrying the type and frontmatter carrying the state, topics are encoded as **facets** on source and claim notes:

- `research_area` — seeded from OpenAlex topics by the ingest engine
- `methodology` — a controlled vocabulary covering method and study design
- `topics` on claim notes

Topical *navigation* is built on top by **hubs** (`notes/hubs/` — the renamed Maps of Content): curated notes that link the relevant sources and claims for an area, regardless of state or project. A hub is authored perspective over the graph, not a folder in disguise.

---

## Related

- The type system the folders encode: [Note types and epistemic roles](note-types.md)
- How state changes are gated: [Why promotion is gated](promotion-model.md)
- The decisions: [ADR-47](../../adr/47-type-first-category-folders.md), [ADR-50](../../adr/50-universal-lifecycle-and-maturity.md)
- The folder tree itself: [The vault](../architecture/vault.md)
- The facet fields: [Frontmatter fields](../../reference/frontmatter.md)
