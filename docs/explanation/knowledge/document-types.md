---
title: Document types and epistemic roles
parent: Knowledge
grand_parent: Explanation
nav_order: 1
---

# Document types and epistemic roles

Memoria treats durable knowledge files as **Concepts**. The folder root and
frontmatter say what kind of Concept the file is; SQLite/read-API verdict state
says whether it is readable as checked knowledge.

---

## Stores and bundles

Memoria separates source catalog state, durable knowledge Concepts, and packaged
operation metadata. That split keeps objective imported records, PI-curated
knowledge, and product capabilities from pretending to be the same kind of
thing.

The schema YAML owns exhaustive fields. The reader-facing roster lives in
[Document types](../../reference/data-model/document-types.md), and field grammar lives in
[Frontmatter fields](../../reference/data-model/frontmatter.md).

---

## Read state

Read state is not frontmatter. Machine writes and promotions go through the
worker path. PI edits are direct edits, then observed and backfilled. Foreign
writes are quarantined by scan instead of silently accepted. The exact state
values belong in the reference.

---

## Why the split matters

**Provenance.** Catalog rows and graph records preserve where source material
came from. `digest` and `fulltext` files hold source-derived material keyed by
`work_id`. `hub` edits are curated PI views; machine-generated hub changes are
suggestions until accepted.

**Note candidates.** `note` is the single atomic note type. Machine-proposed
notes are checked Concepts whose candidate state lives in SQLite's authoritative
event log; per-machine JSONL files are derived synchronization exports. The PI
still decides whether to accept, edit, reject, or link them.

**Gap analysis.** The runtime compares checked catalog, fulltext, and digest
signals with checked notes. `new-topic` means no checked material exists for a
seed term; `undigested` means source/digest signals are dense but notes are
absent; `under-warranted` means notes exist without enough source support.

**Readable boundaries.** A Concept can exist before checks pass. Consumers that
need checked knowledge filter to DB/read API `check_status = checked`; repair surfaces can
show `unchecked` and `quarantined` records explicitly.

**Capability audit.** Operation manifests are packaged product data. They are
audited through manifest tests and operation gates, not by pretending runtime
capability files are knowledge Concepts.

---

## Related

- Complete type reference: [Document types](../../reference/data-model/document-types.md)
- Field grammar and verdict state: [Frontmatter fields](../../reference/data-model/frontmatter.md)
- How material crosses the review gate: [Promotion and the write boundary](promotion-and-gated-zones.md)
- The how of note bodies: [Note body structure](note-body-structure.md)
