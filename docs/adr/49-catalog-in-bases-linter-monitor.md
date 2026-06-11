---
topic: decisions
id: 49
title: Catalog entities live in Obsidian Bases; the Linter is the integrity monitor and commit gate
status: accepted
date_proposed: 2026-06-10
date_resolved: 2026-06-10
assumes: [47]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 49
---

# ADR-49: Catalog entities live in Obsidian Bases; the Linter is the integrity monitor and commit gate

## Context

The old `paper-note`/`item-note` types were entity-note hybrids — a standing tension
between structured bibliographic facts and interpretive prose. The design update (D3)
split them: **entities** are structured records, **source notes** are prose. Bases —
Obsidian's native database views over frontmatter — fit the plain-text/git/lintable
discipline, but provide **no integrity guarantees** (no schema, no constraints). The
red-team pass and D50 settled how integrity is actually supplied.

## Decision

Catalog entities (paper, person, organization, venue, dataset, repository) are
markdown records under `catalog/` with **flat, Bases-queryable frontmatter**, surfaced
through **Obsidian Bases** views. Bases are the *view layer*; the records are the
source of truth; nothing reads a Base as data.

The **Linter engine is the integrity monitor and the commit gate**: a **pre-commit
`schema-check`** gates git-tracked writes at commit (D50), and the cron/CI sweep
monitors between commits — it validates every record against its type schema
(required fields, value types, enum vocabularies, `links:`/`relationships` resolve to
real targets, keyed off the `type:` discriminator) and flags drift as Inbox `flag`s.
The Linter is honestly a *monitor* for live in-app edits (it detects, it does not
block); a file-watcher daemon is deliberately not built. Type schemas live in one
canonical home — **`.memoria/schemas/`** — read by the Linter, the policy gate, the
installer, and the tests.

## Consequences

- Entity data stays git-diffable plain text; a broken Base view loses nothing.
- Every schema change is one YAML edit in `.memoria/schemas/`, picked up by all
  consumers — no scattered hardcoded field lists.
- Between a bad live edit and the next sweep, a Base can briefly serve a malformed
  record; this window is accepted (solo premise) and bounded by the commit gate.
- Bases is a young format: `.base` views are tested against the schemas in CI so our
  side cannot silently drift.

## Alternatives considered

**SQLite / JSON / a graph DB as the store.** Opaque, not git-diffable, outside the
plain-text discipline; a derived index is fine at scale but never the source of truth.
**Keeping the hybrid paper-note.** The tension this splits was a recurring source of
schema drift. **A file-watcher write gate.** A daemon the engine model avoids; the
commit gate + sweep bound the risk acceptably.

## Related

- **Related decisions / Depends on:** [ADR-47](47-type-first-category-folders.md),
  [ADR-50](50-universal-lifecycle-and-maturity.md), [ADR-12](12-obsidian-linter-reference-only.md)
