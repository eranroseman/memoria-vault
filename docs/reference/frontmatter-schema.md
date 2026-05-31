---
topic: vault
---

# Frontmatter schema (reference)

Frontmatter discipline has two concerns: **field shape** (what fields exist, what values they take) and **namespace ownership** (who is allowed to write which field). This document is the authoritative reference for both. For the conceptual model (folder structure, note types, promotion map) see [README.md](../explanation/vault/README.md); for the universal `lifecycle` field and per-type refinements see [note-types.md](note-types.md#lifecycle).

The vault ships a human-facing companion at `00-meta/04-reference/schema-reference.md` (see [README.md vault skeleton](../explanation/vault/README.md#vault-skeleton-human-facing-notes)). That note is the in-vault version templates and the Linter point at; this document is the design source it's generated from.

**Precedence.** When a runtime template (`00-meta/03-templates/*.md`) and this schema disagree, **this schema governs** — the template is the thing that must change. A template that carries a field or value not sanctioned here is the bug, not the reference. (Implementation status of individual fields is tracked in [implementation-status.md](../project/implementation-status.md).)

## Frontmatter

Every note has a `type` field (one of the 15 type names) and a universal `lifecycle` field (`proposed` / `current` / `dormant` / `archived`). Some types add a refinement within a phase (`maturity` for claim-notes; `project_phase`, `draft_stage`). `status` is reserved for board cards, not notes — the two value sets are disjoint.

### Frontmatter namespace discipline

Frontmatter has three namespaces. Each has a different owner.

| Namespace | Owner | Example fields | Rule |
| --- | --- | --- | --- |
| **Main YAML** | Human (authoritative) | `title`, `type`, `topic`, `methods`, `lifecycle`, `maturity` | Human-set values are authoritative; the agent must never silently rewrite. |
| **`_proposed_classification`** | Agent (proposal only) | proposed `topic`, `methods`, `study_design` | Agent populates; human reviews; on classification, selected fields are promoted to main YAML and the proposed block is removed. |
| **`_enrichment`** | Agent (maintained) | API-derived fields: citation counts, abstract, venue. The `enriched_date` field sits at the top level (not inside `_enrichment`) because dashboards and the Linter's stale-enrichment check query it directly. | Agent refreshes on schedule; values are mutable; never overwrite human edits to corresponding main fields. |

Rules:

- Stable identifiers (DOI, OpenAlex ID, ORCID, ROR) may be promoted from `_enrichment` to main YAML once verified.
- Derived metrics (citation counts, OA status) stay in `_enrichment` — they drift over time.
- The agent must never overwrite human-set frontmatter fields, even if API data contradicts.
- Zotero is the source of truth for bibliographic fields (citekey, DOI, title, authors). The paper note references these for navigation but does not duplicate them; Zotero wins on disagreement, the vault wins for synthesis and links.

## Frontmatter field categorization

Frontmatter fields split into four categories by *what they're for*. The split keeps the core query surface small — every note carries the global and time fields, but only the notes that need them carry domain fields.

| Category | What it's for | Example fields | Present on |
| --- | --- | --- | --- |
| **Global** | Identity. The minimal fields every note carries. | `type`, `schema_version` | Every note |
| **Lifecycle** | The note's durability phase. One universal field, plus an optional type-specific refinement. | `lifecycle` (universal); `maturity`, `project_phase`, `draft_stage` (refinements) | `lifecycle` on every note; a refinement only on types that need it |
| **Time** | When the note was created, last touched, or is due. | `created`, `updated`, `enriched_date`, `triage_completed`, `promoted_date` | Every note carries `created` and `updated` (paper-note uses `added` instead of `created`); the rest are type-specific |
| **Domain** | Type-specific data. The fields one kind of note uses but others don't. | `citekey`, `doi`, `authors`, `methods`, `topic`, `sources`, `moc`, `projects`, `zotero_uri`, `pdf_uri`, `extract_path` | Only the note types that need them |

## Proposed and enrichment block schema

The two agent namespaces are stored as HTML-comment blocks in the note body (so they never pollute the queryable frontmatter and are easy to strip on promotion). Their shapes:

- **`_proposed_classification`** — the Librarian's classification proposal, awaiting human review. Sub-fields mirror the main-YAML domain fields the human will set: `topic`, `methods`, `study_design`, `projects` (each a proposed value or list). Lifecycle: agent **populates** at ingest → human **reviews** at [Classify](../how-to/workflows/upstream/classify.md) → selected fields are **promoted** into main YAML and the **entire block is deleted**. A note at `lifecycle: current` should carry no `_proposed_classification` block.
- **`_enrichment`** — API-derived metadata the agent refreshes on a schedule: `citation_count`, `abstract`, `venue`, `oa_status`, and similar mutable values. Lifecycle: agent **refreshes** periodically; values are **mutable** and never overwrite human-set main-YAML fields. The `enriched_date` timestamp sits **top-level** (not inside the block) because the Linter's stale-enrichment check and the dashboards query it directly. Stable identifiers (DOI, OpenAlex ID, ORCID, ROR) graduate from `_enrichment` to main YAML once verified; derived metrics stay in the block because they drift.

Both blocks are agent-owned (see the namespace table above): the agent writes them, the human promotes from them, and the agent never writes the main YAML directly. **No HTML-comment-stripping Obsidian Linter plugin rule may run** — it would silently delete these blocks (see [obsidian-plugins/reference/obsidian-linter.md](../project/evaluated-alternatives/obsidian-linter.md)).

### Enrichment refresh cadence

How often the Librarian re-enriches `_enrichment` fields, by source type, and what typically changes. The Linter's stale-enrichment check reads `enriched_date` against these per-type intervals (sharper than a single generic "> 90 days" default):

| Source type | Re-enrich every | What changes |
| --- | --- | --- |
| Article | 180 days | citation count, related papers |
| Preprint | 30 days | may have been published |
| Person | 90 days | new papers, affiliation changes |
| Organization | 365 days | rarely changes |
| Repository | 30 days | stars, issues, releases |
| Package | 30 days | new versions, deprecation |

## Rules

- **`type` is universal and required.** Every note has a `type` field whose value is one of the 15 type names. Missing or unknown `type` is a schema-hygiene flag for the Linter.
- **`lifecycle` is universal; refinements are type-specific.** Every note carries `lifecycle` ∈ `proposed` / `current` / `dormant` / `archived`. Types that need finer state within a phase add a refinement: `maturity` (claim-note, within `current`), `project_phase` (project-note), `draft_stage` (draft). For sources, triage *is* the `proposed`→`current` transition — no separate field. Orthogonal `*_status` fields (`pub_status`, `maintenance_status`) describe the *thing the note is about*, not the note's lifecycle. See [Lifecycle](note-types.md#lifecycle).
- **Claim supersession is a typed relation, not a status.** A `claim-note` overturned by a newer claim carries `superseded_by: [[newer-claim]]` (with an optional inverse `supersedes:` on the newer note). A claim's currency — *current* vs. *superseded* — is **derived from the presence of `superseded_by`**, not a separate field, and is **human-set** (the agent may propose the link in `_proposed_classification`; it never writes it). `query` and `write` exclude superseded claims by default, and the Linter flags any draft or answer that cites one. Supersession is kept **top-level** because it governs a claim's *currency*; it is distinct from the associative `relations:` block (next bullet) adopted in [ADR-9](../project/decisions/09-typed-relations-frontmatter.md) — see [ADR-22](../project/decisions/22-claim-supersession.md).
- **Associative links live in a nested `relations:` block.** Claim-notes may carry typed associative relations under a single `relations:` key — v1 vocabulary `supports` (directional: this claim supports the target) and `contradicts` (symmetric: the two disagree). These are **human-set and opt-in**: untyped wikilinks remain first-class and coexist; the agent may propose a relation in `_proposed_classification` but never writes one onto a canonical note. This is distinct from top-level `superseded_by` (which is *temporal* — currency — not associative). The vocabulary is controlled (see below) and extends on felt need; the [`contradictions` dashboard](../explanation/dashboards/contradictions.md) reads `relations.contradicts`. See [ADR-9](../project/decisions/09-typed-relations-frontmatter.md).
- **Time fields are mostly common.** `created` and `updated` are universal except that `paper-note` historically uses `added` instead of `created`; treat the two as synonymous for paper notes.
- **Domain fields are scoped to their type.** Don't pad every note with null domain fields. A `claim-note` should not carry a `doi` field just to keep the schema "uniform."
- **`sources` links to source *notes*, not citekeys.** A `claim-note`'s `sources:` lists wikilinks to the source notes it draws on — `[[paper-note]]`, `[[item-note]]`, or entity notes in `20-sources/` — never a bare BibTeX citekey or a Pandoc `[@key]` citation (those belong to the draft→export layer). A paper-note's filename *is* its citekey, so `[[mamykina2010sense]]` links to the note, not a citation. There is no `tags` field — classification is the controlled `topic` / `methods` vocabularies, not free tags.
- **`status` is card-only; notes use `lifecycle`.** The board card's `status` is the Hermes Kanban enum (`triage` / `todo` / `ready` / `running` / `blocked` / `done` / `archived` — see [kanban-board/states.md](../explanation/kanban-board/states.md)). Notes never carry `status`; their durability phase is `lifecycle` (`proposed` / `current` / `dormant` / `archived`). A note never carries `status` and a card never carries `lifecycle`, so although both value sets include `archived`, the field name alone disambiguates the two.
- **Once the design is in use, any frontmatter change to a template bumps that template's `schema_version`.** Adding a field, removing a field, renaming a field, changing a field's value space — all of these are schema changes that require a version bump *if there are existing notes in human vaults that would lag behind*. New notes get the new version; existing notes stay on the old version until migrated. The Linter's schema-version-mismatch check ([profiles/linter.md](../explanation/profiles/linter.md)) surfaces notes still on older versions; `schema-migrate --dry-run` proposes the migration. This rule is what turns per-field migration debt into a single rollup signal — "127 notes still on v1" rather than "127 notes missing field X, 89 missing field Y, ..." per field. **Bumping is per-template, not global** — only the template whose schema changed bumps. Paper-note and code-note can be on different versions independently. **Pre-first-deployment, the design is fluid; the baseline is `schema_version: 1` for every template and the bump discipline activates the first time a template ships into a vault that holds real notes.**

## Controlled vocabularies

For controlled-vocabulary fields, the allowed values are:

| Field | Where it lives | Allowed values |
| --- | --- | --- |
| `lifecycle` | Every note | `proposed`, `current`, `dormant`, `archived` |
| `status` (card-only) | Board card | Hermes enum: `triage`, `todo`, `ready`, `running`, `blocked`, `done`, `archived` |
| `review_status` (card-only) | Board card `metadata` | `unreviewed`, `requested`, `in-review`, `approved`, `rejected` |
| `maturity` | claim-note | `seedling`, `budding`, `evergreen` |
| `project_phase` | project-note | `planning`, `active`, `paused`, `complete` |
| `draft_stage` | draft | `outline`, `in-progress`, `submitted` |
| `pub_status` | paper-note | `active`, `preprint`, `retracted`, `deprecated`, `expression-of-concern` |
| `maintenance_status` | item-note | `active`, `deprecated`, `archived`, `unmaintained` |
| `role_in_stack` | item-note | `primary-tool`, `dependency`, `alternative`, `reference-only` |
| `item_category` | item-note | `repo`, `package`, `product`, `standard` |
| `source_type` | paper-note | `paper` (fixed; marks the source kind alongside `type: paper-note`) |
| `relationship_to_research` | person-note | `advisor-candidate`, `collaborator`, `author-to-follow`, `institutional`, `funder` |
| `outreach_status` | person-note | `""`, `not-contacted`, `contacted`, `replied`, `meeting-scheduled` |
| `scope` | moc | `topic`, `domain`, `project`, `child` |
| `relations` keys | claim-note | `supports`, `contradicts` (v1; extends on felt need) |

The Linter's `schema-check` (see [linter.md](../explanation/profiles/linter.md)) validates frontmatter against this reference. **New allowed values go through this reference first, not the other way around** — a template or query that uses a value not listed here is the bug, not the reference.

## Reach-into-source fields (paper-note)

The `paper-note` frontmatter carries three deliberate hooks into the underlying paper. Each gives a different reach with different access semantics:

| Field | Form | What it opens | When to use |
| --- | --- | --- | --- |
| `zotero_uri` | `zotero://select/items/<key>` | Zotero item record (metadata, attachments list, tags) | Managing citation metadata, retraction status, attachments |
| `pdf_uri` | `zotero://open-pdf/library/items/<key>` | PDF directly in Zotero's reader | Reading or annotating the paper |
| `extract_path` | Vault-relative path (e.g., `90-assets/extracts/mamykina2010sense.md`) | Marker-extracted markdown — the in-vault, searchable representation | Grep, quoting in claim notes, feeding text to a model |

All three are populated by the Librarian profile during [ingest](../how-to/workflows/upstream/ingest.md) — none are human-typed. The PDF itself lives in Zotero's storage, not in the vault; see [workflows/upstream/zotero-capture.md](../how-to/workflows/upstream/zotero-capture.md) for the source-of-truth rationale.

## Properties UI vs YAML frontmatter

Obsidian's Properties UI is a UI layer over the underlying YAML. Same storage, different editor. Use them deliberately:

- **Properties UI** for ad-hoc human edits — single-note changes, quick field updates. Lower syntax-error risk.
- **YAML frontmatter** for system notes, dashboards, registry files, and any Templater-generated note. Better Git diffs, deterministic for automation, full formatting control.

The rule: if the field is being set by code or by a template, treat the YAML as authoritative. If it's being set by a person reading the note, the Properties UI is friendlier.

## Related design documents

- [vault/README.md](../explanation/vault/README.md) — folder structure, note types, lifecycle states, namespace discipline (who writes what)
- [linter.md](../explanation/profiles/linter.md) — schema-check lint rules that enforce this reference
- [vault/README.md#vault-skeleton-human-facing-notes](../explanation/vault/README.md#vault-skeleton-human-facing-notes) — the human-facing companion in `00-meta/04-reference/schema-reference.md`
