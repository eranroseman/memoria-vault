---
title: Lifecycle, not topic — and state, not folders
parent: Design Book
grand_parent: Developers
nav_order: 20
---

# Lifecycle, not topic — and state, not folders

Two organizational decisions shape the vault: **a Concept's position in the
system is its type, never its topic**, and **read state is record state, not a
folder**. Folders encode one thing only: the category and type home declared in
`folders.yaml` (`knowledge/`, with SQLite-backed catalog state). Where a record
stands for reading is `check_status`, not a path move.

---

## Why folders encode type

Topics are many-to-many; a folder is one location. Memoria therefore reserves
folders for the one fact that is one-to-one: what kind of checked bundle this is.
Alpha.15 file-backed Concepts are Work, note, hub, and project; catalog Work
records live in SQLite with blob-backed source content. Topics live in catalog
metadata, Concept frontmatter facets, and authored links, following the
Zettelkasten link-first inheritance described in [Intellectual
foundations](intellectual-foundations.md#luhmanns-zettelkasten).

---

## Read state lives with the record
The vault is organized by **category**
([ADR-119](../adr/119-schema-driven-document-creation.md)): `knowledge/` holds
Work, note, hub, and project Concepts, SQLite holds catalog working state, and
packaged product data holds operation manifests. It never mixes lifecycle state
into folder names. The full tree is catalogued in [On-disk layout](../reference/on-disk-layout.md).
A note does not travel when the PI checks it; a catalog Work does not become a
different kind of thing when it is read. What changes is its read state, and read
state is a property, not a location.

For every record, read standing lives in SQLite and read-API responses:
`unchecked -> checked -> quarantined`. File-backed Concept frontmatter carries
authored meaning only; it never stores `check_status`. Catalog Work rows use the
same DB-owned verdict. The exact Concept field inventory is defined in
[Frontmatter fields](../reference/frontmatter.md); catalog source record fields
are defined in [Ingest routing](../reference/ingest.md).

---

## Why state-not-folders is strictly better

**Promotion is a record update, not a file move.** A state change does not move
a file, so it cannot break wikilinks, lose Git history continuity, or invalidate
saved queries. A note is born in its type-home and dies in its type-home; a
catalog Work keeps the same `source_id`.

**Links survive every transition.** A claim cited by twelve other notes can be retracted, superseded, and archived without a single inbound link breaking. Provenance — the property the whole system is built to protect — does not depend on link-rewriting tooling getting every move right.

**Archive is state, not a folder.** An archived item stays exactly where it always
lived and simply drops out of active views through the type-specific field that owns
that workflow. It remains readable, linkable, and traceable from every note that ever
cited it — *archive, never delete* with zero file churn.

**Queries get honest.** "What is checked?" is a `check_status` query, "what is this
thing?" is a folder/type fact, and "what's it about?" is a facet query — three
different questions, three different mechanisms, none overloaded onto the others.

**The agent's permissions stay tractable.** Type homes such as `knowledge/notes/`
and `knowledge/hubs/` are stable paths that never gain or lose members through state
changes. The policy gate reasons about *where an agent may write*, and the answer
never shifts under it mid-task.

One consequence to know: attention projections are separate from checked Concepts, so
"what needs me?" and "what is checked knowledge?" are distinct queries.

---

## Topics in frontmatter, not folders

With folders carrying the type and record state carrying the verdict, topics are
encoded as **facets** on catalog Work rows and note Concepts:

- `research_area` — seeded from OpenAlex topics by the ingest/enrichment operation
- `methodology` — a controlled vocabulary covering method and study design
- `topics` on notes where the local schema supports them

Topical *navigation* is built on top by **hubs** (`knowledge/hubs/`): curated
notes that link the relevant Works and notes for an area, regardless of state or
project. A hub is authored perspective over the graph, not a folder in disguise.

---

## Related

- The type system the folders encode: [Document types and epistemic roles](../explanation/knowledge/document-types.md)
- How state changes are gated: [Why promotion is gated](../explanation/knowledge/promotion-and-gated-zones.md)
- The schema/home decision: [ADR-119](../adr/119-schema-driven-document-creation.md)
- The folder tree itself: [The vault](../explanation/architecture/vault.md)
- The facet fields: [Frontmatter fields](../reference/frontmatter.md)
