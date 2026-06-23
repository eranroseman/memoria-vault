---
topic: decisions
id: 117
title: "Document types: kind-scoped singular nouns; folder names never collide with spaces"
status: accepted
date_proposed: 2026-06-23
date_resolved: 2026-06-23
assumes: [47, 51, 101, 116]
supersedes: []
superseded_by: []
---

# ADR-117: Document types — kind-scoped singular nouns; no folder/space collision

## Context

A clean-slate review walked all 26 typed-document types. Most are well-chosen field terms —
`paper`, `venue`, `claim`, `source`, `hub`, the kanban `card` — but there is **no stated
naming rule**, and that absence costs twice:

- **Apparent overloads read as bugs.** A reviewer "fixes" `worker-card` → `worker-row`, not
  knowing the board is a *kanban* board where `card` is the correct, Hermes-native term; or
  flags `card` as colliding with the Inbox's ADR-51 honesty card. Neither is a defect.
- **New types can drift in form** with nothing to check them against.

Three concrete issues surfaced: **`fleeting`** is the lone adjective among nouns; the
**`notes/` category doubles the medium word** — every typed object is a note, yet one category
is named "notes"; and a tempting fix for that doubling (`notes/ → knowledge/`) would have
created a *worse* problem — a `knowledge/` folder and the **Knowledge space** sharing a name
with **different meanings** (the folder holds `source` documents shown in the *Library* space,
not just claims). The resolution turns out to be cheaper than any folder rename: change the
**umbrella term**, not the folder.

## Decision

Adopt an explicit naming rule, apply two renames, and record what the rule deliberately
leaves alone.

### The rule

**The umbrella term for a typed object is "document," not "note."** Every typed object is a
*document*; a *note* is then **one kind** of document (the `notes/` documents — `source`,
`claim`, `hub`, `index`, `fleeting-note`). This single move dissolves the `notes/` doubling:
once the umbrella is "document," a `notes/` folder is a legitimate subset, not a circular
"notes are notes." Type schemas, the page that lists them, and prose say **document type**.

A type name is a **singular common noun for what the object is**, drawn from **ubiquitous
language** (the field's own term), scoped to its **kind**. The vault has four kinds; the kind
is a bounded context carried by the **category folder**:

| Kind | Role | Folder(s) |
| --- | --- | --- |
| **Record** | the content — entities, knowledge, project work | `catalog/` `notes/` `projects/` |
| **Signal** | a prompt awaiting a human decision | `inbox/` |
| **Surface** | a navigation view | `spaces/` |
| **Control** | agent-execution machinery | `system/` |

What the rule entails:

- **Singular noun; no adjectives or verbs.** (`fleeting` violates this.)
- **Use the established term** — `paper`/`venue` (bibliographic), `source`/`claim`/`hub`
  (Zettelkasten lineage), `card`/`lane` (kanban), `thesis`/`project` — never invent where a
  field word exists.
- **One word, one concept _within_ a kind.** A word may recur _across_ kinds only because the
  folder disambiguates: **`card`** is legitimately both the kanban execution unit
  (`worker-card`, Control) and the [ADR-51](51-inbox-category-and-honesty-card.md) inbox
  honesty card (Signal). Prose must always qualify it ("board card" / "inbox card"), never bare.
- **Suffixes are kind-local and meaningful**, not a global registry: in Control, `-card` = a
  kanban unit, `-task` = a gold-eval entry, `-item` = a list row — each correct on its own.
- **No folder name may also name a navigation surface with a *different* meaning.** A shared
  name is fine when the folder and the space are the *same* concept (1:1) — `projects/` ≈ the
  Project space, `inbox/` ≈ the Inbox queue. It is forbidden when the meanings differ — which
  is exactly why `notes/` is **not** renamed to `knowledge/`: that folder feeds *both* the
  Library space (its `source` documents) and the Knowledge space (its `claim` documents), so
  "knowledge" the folder ≠ "Knowledge" the space.

### The changes

1. **Umbrella: "note types" → "document types."** The collection of types, the page that lists
   them, and generic prose call a typed object a **document**. This dissolves the `notes/`
   doubling at the root — and because it keeps `notes/`, it also avoids the `knowledge/` ↔
   Knowledge-space collision entirely. No folder moves; no `type:` value changes.
2. **`fleeting` → `fleeting-note`.** Restores the singular-noun form — and reads cleanly under
   the new umbrella as "a fleeting *note-document*."

### What the rule validates — do NOT change

- **`notes/` stays.** Under the document umbrella it is a legitimate content-kind folder (the
  note documents), not a circular name — and renaming it would only create a space collision.
- **The spaces stay**, and the 1:1 folder overlaps `projects/` ≈ Project and `inbox/` ≈ Inbox
  are fine (same concept, not a clash).
- `worker-card` — a Hermes/kanban card; correctly named (`worker-row` would be wrong).
- `worklist-item`, `eval-task`, `work-prompt`, `code-note` — each the correct term in its kind.
- the catalog six, `claim`, `source`, `hub`, `index`, `project`, `thesis`, `pattern`, `space`,
  `queue`, `maintenance` — already conform.

### Documentation (not renames)

- Document the `flag` vs `alert` and `hub` vs `index` distinctions — the names are fine; only
  the *difference* between each pair is currently undocumented.

## Consequences

- The rule is enforceable going forward and ends the recurring "card"/"note" debate by naming
  the bounded-context and no-collision principles.
- **The umbrella rename is cheap** — terminology only: the `note-types.md` reference page (title
  and prose), schema/code comments that say "note type," and generic docs. **No folder moves, no
  `type:` values change, no paths change** — so none of `folders.yaml`, the `gated_prefixes`, the
  detectors, the producers, or existing documents are touched by it.
- **`fleeting` → `fleeting-note`** is the only type rename: it touches the capture path
  (QuickAdd/Modal Forms), the template, the `fleeting` home in `folders.yaml`, the schema file,
  the tests, and existing fleeting notes.
- Phasing: (1) adopt the rule + the "document type" umbrella + the doc clarifications (cheap);
  (2) `fleeting → fleeting-note`.
- One internal note: the four *kinds* include "Record"; "document" as the umbrella pairs cleanly
  with Record/Signal/Surface/Control, though "Record document" is faintly redundant — the kind
  could be renamed **Content** if that ever grates. Not load-bearing.

## Alternatives considered

- **Rename the `notes/` folder** (to `knowledge/`, or a Zettelkasten *slip-box* name).
  Rejected: `knowledge/` collides with the Knowledge space *with a different meaning* (the folder
  feeds Library too) — the no-collision rule forbids it; a slip-box name avoids the collision but
  is jargon and inconsistent with the non-Zettelkasten type names (`claim`, not "permanent note").
  Either way it is a heavy path migration. The document-umbrella rename fixes the same doubling
  more cheaply and keeps `notes/`.
- **`file types` as the umbrella.** Rejected: "file type" conventionally means the *extension*
  (`.md`), so it clashes with the OS sense ("the file type is Markdown"). "Document" is clean,
  collision-free, and more precise for schema-validated structured documents.
- **Kind-prefixed type names** (`entity:paper`, `signal:flag`, `board:card`). Maximally
  collision-proof, but over-engineered: the folder already encodes the kind, real collisions are
  rare and already managed, and it would churn every `type:` value and every query. Rejected on cost.
- **`worker-card` → `worker-row`, `worklist-item` → `worklist-row`.** Rejected: the board is a
  kanban board and `card` is its correct, Hermes-native term — there is no collision to fix.

## Related

- **Refines:** [ADR-47](47-type-first-category-folders.md) (type-first category folders — the
  category folders are **kept**; the only folder-map touch is the `fleeting` → `fleeting-note`
  home), [ADR-51](51-inbox-category-and-honesty-card.md) (inbox honesty cards — formalizes `card`
  as a Signal/Control dual-use), [ADR-101](101-navigation-spaces-gate-reserved-for-approval.md)
  (the overloaded-term principle — applied to types, plus the folder/space no-collision corollary),
  [ADR-116](116-obsidian-surface-architecture.md) (the storage-vs-intent two-axis model the
  no-collision rule builds on).
- **Source discussion:** the alpha.8 type-naming clean-slate review.
