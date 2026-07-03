---
title: Document types and epistemic roles
parent: Knowledge
grand_parent: Explanation
nav_order: 1
---

# Document types and epistemic roles

Alpha.15 treats durable knowledge files as **Concepts**. The folder root and
frontmatter say what kind of Concept the file is; SQLite/read-API verdict state
says whether it is readable as checked knowledge.

---

## Stores and Bundles

| Store | Holds | Types |
| --- | --- | --- |
| Catalog state | Source rows, source blobs, provider payloads, external IDs, and graph edges. | SQLite catalog rows and `.memoria/blobs/**`, not frontmatter Concept types |
| `knowledge/` | Durable knowledge files and PI curation. | `note`, `work`, `hub`, `project` |
| Packaged capability bundle | Operation manifests and product capability metadata. | Packaged data under `memoria_vault.product.capabilities`, not runtime-vault Concepts |

The exhaustive field lists live in [Document types](../../reference/document-types.md).

---

## Read state

Every Concept and catalog row has a DB/read-API `check_status`:

- `unchecked`: captured or generated, but not promoted as checked.
- `checked`: usable by checked read surfaces.
- `quarantined`: failed validation, provenance, or foreign-write checks.

The value is not frontmatter. Machine writes and promotions go through the
worker path. PI edits are direct edits, then observed and backfilled. Foreign
writes are quarantined by scan instead of silently accepted.

---

## Why the split matters

**Provenance.** Catalog rows and graph records preserve where source material
came from. `work` records hold source-derived summaries and aspects. `hub` edits
are curated PI views; machine-generated hub changes are suggestions until
accepted.

**Note candidates.** `note` is the single atomic note type. Machine-proposed
notes are checked Concepts whose candidate state lives in journal/SQLite state;
the PI still decides whether to accept, edit, reject, or link them.

**Gap analysis.** The runtime compares checked source/digest signals with
checked notes. `new-topic` means no checked material exists for a seed term;
`undigested` means sources/digests are dense but notes are absent;
`under-warranted` means notes exist without enough source support.

**Readable boundaries.** A Concept can exist before checks pass. Consumers that
need checked knowledge filter to DB/read API `check_status = checked`; repair surfaces can
show `unchecked` and `quarantined` records explicitly.

**Capability audit.** Operation manifests are packaged product data. They are
audited through manifest tests and operation gates, not by pretending runtime
capability files are knowledge Concepts.

---

## Related

- Complete type reference: [Document types](../../reference/document-types.md)
- Field grammar and verdict state: [Frontmatter fields](../../reference/frontmatter.md)
- How material crosses the review gate: [Why promotion is gated](promotion-and-gated-zones.md)
- The how of note bodies: [Note body structure](note-body-structure.md)
