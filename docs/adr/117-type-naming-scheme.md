---
topic: decisions
id: 117
title: "Type naming scheme: kind-scoped singular nouns in ubiquitous language"
status: accepted
date_proposed: 2026-06-23
date_resolved: 2026-06-23
assumes: [47, 51, 101]
supersedes: []
superseded_by: []
---

# ADR-117: Type naming scheme — kind-scoped singular nouns in ubiquitous language

## Context

A clean-slate review walked all 26 note types. Most are well-chosen field terms — `paper`,
`venue`, `claim`, `source`, `hub`, the kanban `card` — but there is **no stated naming
rule**, and that absence costs twice:

- **Apparent overloads read as bugs.** A reviewer "fixes" `worker-card` → `worker-row`, not
  knowing the board is a *kanban* board where `card` is the correct, Hermes-native term; or
  flags `card` as colliding with the Inbox's ADR-51 honesty card. Neither is a defect.
- **New types can drift in form** with nothing to check them against.

Two concrete defects did surface: **`fleeting`** is the lone adjective among nouns, and the
**`notes/` category doubles the medium word** — every one of the 26 types is a note, yet one
category is named "notes."

## Decision

Adopt an explicit naming rule, apply two renames, and record what the rule deliberately
leaves alone.

### The rule

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

### The renames

1. **`notes/` category → `knowledge/`.** It is the only category named for the *medium* rather
   than its *content kind*. `knowledge` makes the top level uniform —
   `catalog · knowledge · projects · inbox · spaces · system` — and parallels the existing
   `projects/` ≈ Project-space overlap (folder = storage axis, space = intent axis;
   [ADR-116](116-obsidian-surface-architecture.md)). The "Notes" doc heading follows.
2. **`fleeting` → `fleeting-note`.** Restores the singular-noun form (the Zettelkasten term is
   "fleeting note").

### What the rule validates — do NOT rename

- `worker-card` — a Hermes/kanban card; correctly named (`worker-row` would be wrong).
- `worklist-item`, `eval-task`, `work-prompt`, `code-note` — each the correct term in its kind.
- the catalog six, `claim`, `source`, `hub`, `index`, `project`, `thesis`, `pattern`, `space`,
  `queue`, `maintenance` — already conform.

### Documentation (not renames)

- Document the `flag` vs `alert` and `hub` vs `index` distinctions — the names are fine; only
  the *difference* between each pair is currently undocumented.

## Consequences

- The rule is enforceable going forward and ends the recurring "card"/"note" debate by naming
  the bounded-context principle.
- **`notes/` → `knowledge/` is the one heavy migration**: [ADR-47](47-type-first-category-folders.md)'s
  type→folder homes (`source`/`claim`/`hub`/`index`/`fleeting`), `folders.yaml`, the
  `gated_prefixes` (`notes/claims/` → `knowledge/claims/`, `notes/hubs/`), the Linter detectors,
  every producer that writes there, the templates, the test suite, **every existing note's path**,
  and a wide doc sweep. It is the costliest single change in the review and can be scheduled
  on its own.
- **`fleeting` → `fleeting-note`** is smaller but touches the capture path (QuickAdd/Modal Forms,
  the template, tests) and existing fleeting notes.
- Phasing: (1) adopt the rule + the doc clarifications (cheap); (2) `fleeting-note`; (3) the
  `knowledge/` migration (deferrable).

## Alternatives considered

- **Kind-prefixed type names** (`entity:paper`, `signal:flag`, `board:card`). Maximally
  collision-proof, but over-engineered: the folder already encodes the kind, real collisions are
  rare and already managed, and it would churn every `type:` value and every query. Rejected on cost.
- **A Zettelkasten-style folder name** (e.g. a *slip-box* folder). Precise — the folder *is* a
  slip-box — but jargon, and inconsistent with the non-Zettelkasten type names (`claim`, not
  "permanent note"). Rejected on legibility.
- **`worker-card` → `worker-row`, `worklist-item` → `worklist-row`.** Rejected: the board is a
  kanban board and `card` is its correct, Hermes-native term — there is no collision to fix.
- **Heading-only mitigation for `notes/`** (rename the doc heading, keep the folder). The cheap
  fallback if the `knowledge/` migration is deferred; leaves the folder-level doubling in place.

## Related

- **Refines:** [ADR-47](47-type-first-category-folders.md) (type-first category folders — the
  `notes/` → `knowledge/` rename), [ADR-51](51-inbox-category-and-honesty-card.md) (inbox honesty
  cards — formalizes `card` as a Signal/Control dual-use), [ADR-101](101-navigation-spaces-gate-reserved-for-approval.md)
  (the overloaded-term principle — the same lesson, applied to types).
- **Source discussion:** the alpha.8 type-naming clean-slate review.
