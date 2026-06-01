# Schema reference

Canonical list of every frontmatter field used in this vault. The source of truth that templates and the Linter point at.

## Global fields (every note)

| Field | Type | Allowed values | Notes |
| --- | --- | --- | --- |
| `type` | string | one of the 16 note types | Required. |
| `schema_version` | int | current: `1` | Required. |
| `created` | datetime | ISO 8601 | Auto-set by Templater. |
| `updated` | datetime | ISO 8601 | Linter refreshes on touch. |

## Note types (16)

`claim-note`, `paper-note`, `answer-note`, `reference-note`, `moc`, `project-note`, `code-note`, `canvas`, `person-note`, `organization-note`, `venue-note`, `fleeting-note`, `item-note`, `deliverable`, `draft`, `candidate-note`.

Templates for each in `03-templates/`.

> **`candidate-note` is the transient lead / dead-letter type** ([ADR — shared candidate frontmatter](../../../project-files/proposals/21-shared-candidate-frontmatter.md)). Files in `10-inbox/03-candidates/` carry `type: candidate-note` with a `source` (`find` / `database-search` / `manual` / `capture-timeout` / `gap`), a `candidate_status` (`pending-screen` / `pending-ingest` / `included` / `excluded`), and `exclusion_reason`. This **one type unifies** the Librarian's discovery candidates and the Verifier's gap-cards (`source: gap`). It is transient — promoted to a durable type on `included`, archived on `excluded` — so unlike the other 15 it isn't a permanent knowledge node.

### What the `-note` suffix means

The `-note` suffix marks a **knowledge node** — a note that is the authoritative record of one thing (an idea, source, entity, concept, project, code artifact, or answer) and carries its own content. Twelve of the sixteen types carry the suffix — the durable knowledge nodes plus the transient `fleeting-note` and `candidate-note`.

Four types are **bare** because they are not records:

| Bare type | What it is |
| --- | --- |
| `moc`, `canvas` | **Views** that organize other notes (an index/map; a spatial layout). Empty without the notes they point at. |
| `draft`, `deliverable` | **Outputs** produced from notes (a manuscript; an export). |

Rule of thumb: if the note *is* a thing you curate, it gets `-note`; if it *arranges* other notes or *is produced from* them, it stays bare. Every `-note` is also a markdown note with a `type` and a lifecycle field — but being markdown isn't enough to earn the suffix (`moc` is markdown too). `project-note` keeps the suffix because it records a project's own scope and status, not just a map of its parts. Full definition: vault/note-types.md.

## Lifecycle (universal)

Every note carries `lifecycle` — its durability phase. (`status` is reserved for board cards, not notes.)

| `lifecycle` | Meaning |
| --- | --- |
| `proposed` | created, not yet accepted as durable |
| `current` | accepted, in use, durable |
| `dormant` | set aside / paused, not retired |
| `archived` | retired — superseded, deprecated, discarded |

### Refinement fields (type-specific, within lifecycle)

| Field | On types | Values |
| --- | --- | --- |
| `maturity` | `claim-note` | `seedling` → `budding` → `evergreen` (granularity within `current`) |
| `project_phase` | `project-note` | `planning` / `active` / `paused` / `complete` |
| `draft_stage` | `draft` | `outline` / `in-progress` / `submitted` |

Orthogonal status fields (describe the *thing*, not the note's lifecycle): `pub_status` (paper), `maintenance_status` + `role_in_stack` (item), `outreach_status` (person).

### Claim-note relations and supersession

| Field | Type | Notes |
| --- | --- | --- |
| `relations` | block (`supports: []` / `contradicts: []`) | Typed relations between claim-notes ([ADR-08](../../../project-files/decisions/08-typed-relations-frontmatter.md)). Human-set; opt-in. |
| `superseded_by` | wikilink | Points to the claim-note that replaces this one; implies `lifecycle: archived` ([ADR-10](../../../project-files/decisions/10-claim-supersession.md)). |

Both are **additive, optional** fields, so `schema_version` stays `1` — per the versioning rule a bump is only for *breaking* changes, and adding optional fields doesn't break backward compatibility. (ADR-08/10 noted a possible bump; the additive-compat rule governs, so no bump is taken.)

## Controlled vocabularies

| Field | Where defined | Allowed values |
| --- | --- | --- |
| `study_design` | *(human defines as research evolves)* | controlled list |
| `methods` | *(human defines)* | controlled list |
| `topic` | *(human defines — kept open by design)* | open list |

Use [Tag Wrangler](obsidian-config.md) for bulk rename / merge when a vocabulary term evolves.

## Namespace blocks

Frontmatter has three namespaces with different ownership:

| Namespace | Owner | Example fields |
| --- | --- | --- |
| Main YAML | Human (authoritative) | `title`, `type`, `topic`, `methods`, `lifecycle`, `maturity` |
| `_proposed_classification` | Agent (proposal only) | proposed `topic`, `methods`, `study_design` awaiting classification |
| `_enrichment` | Agent (maintained) | API-derived: `citation_count`, `abstract`, `venue`, `enriched_date` (top-level) |

**Rules:**

- Agent never overwrites human-set main-YAML fields, even if API data contradicts.
- Stable identifiers (DOI, OpenAlex ID, ORCID, ROR) may be promoted from `_enrichment` to main YAML once verified.
- Derived metrics (citation counts, OA status) stay in `_enrichment` — they drift over time.
- Zotero is authoritative for bibliographic fields; the paper note references them but does not duplicate.

---

**For depth:** [docs/reference/frontmatter.md](../../../docs/reference/frontmatter.md) — the authoritative schema design (this note is the in-vault human-facing mirror; the `relations` vocabulary lives there too, per ADR-08).

**Drift discipline.** When the design schema changes, update this file to match. The Linter's structural-drift check flags this file if `updated` is older than the corresponding design doc.
