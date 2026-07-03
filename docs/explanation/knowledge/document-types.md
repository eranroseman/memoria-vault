---
title: Document types and epistemic roles
parent: Knowledge
grand_parent: Explanation
nav_order: 1
---

# Document types and epistemic roles

Alpha.15 treats durable vault records as **Concepts**. The folder root says what
kind of work the Concept belongs to; `check_status` says whether it is readable
as checked knowledge.

---

## Three bundles

| Bundle | Holds | Concept types |
| --- | --- | --- |
| `catalog/` | Source records and named entities. | `source`, `person`, `organization`, `venue` |
| `knowledge/` | Readable knowledge artifacts and PI curation. | `digest`, `note`, `hub`, `project` |

Operation manifests are packaged product data under
`memoria_vault.product.capabilities`, not runtime-vault Concepts.

The exhaustive field lists live in [Document types](../../reference/document-types.md).

---

## Read state

Every Concept carries `check_status`:

- `unchecked`: captured or generated, but not promoted as checked.
- `checked`: usable by checked read surfaces.
- `quarantined`: failed validation, provenance, or foreign-write checks.

Machine writes and promotions go through the worker path. PI edits are direct
edits, then observed and backfilled. Foreign writes are quarantined by scan
instead of silently accepted.

---

## Why the split matters

**Provenance.** `source` and entity records preserve where material came from.
`digest` records are machine-owned checked summaries. `hub` edits are curated PI
views; machine-generated hub changes are suggestions until accepted.

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

**Capability audit.** Prompt operations, optional adapter servers, skills, and workflows are
Concepts too. That makes runnable capability metadata visible, typed, and subject
to the same checked/quarantine discipline as knowledge records.

---

## Related

- Complete type reference: [Document types](../../reference/document-types.md)
- Field grammar and `check_status`: [Frontmatter fields](../../reference/frontmatter.md)
- How material crosses the review gate: [Why promotion is gated](promotion-and-gated-zones.md)
- The how of note bodies: [Note body structure](note-body-structure.md)
