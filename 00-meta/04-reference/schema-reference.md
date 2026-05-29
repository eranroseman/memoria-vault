# Schema reference

Canonical list of every frontmatter field used in this vault. The source of truth that templates and the Linter point at.

## Global fields (every note)

| Field | Type | Allowed values | Notes |
| --- | --- | --- | --- |
| `type` | string | one of the 15 note types | Required. |
| `schema_version` | int | current: `1` | Required. |
| `created` | datetime | ISO 8601 | Auto-set by Templater. |
| `updated` | datetime | ISO 8601 | Linter refreshes on touch. |

## Note types (15)

`claim-note`, `paper-note`, `answer-note`, `reference-note`, `moc`, `project-note`, `code-note`, `canvas`, `person-note`, `organization-note`, `venue-note`, `fleeting-note`, `item-note`, `deliverable`, `draft`.

Templates for each in `03-templates/`.

### What the `-note` suffix means

The `-note` suffix marks a **knowledge node** — a note that is the authoritative record of one thing (an idea, source, entity, concept, project, code artifact, or answer) and carries its own content. Eleven of the fifteen types are nodes and carry it.

Four types are **bare** because they are not records:

| Bare type | What it is |
| --- | --- |
| `moc`, `canvas` | **Views** that organize other notes (an index/map; a spatial layout). Empty without the notes they point at. |
| `draft`, `deliverable` | **Outputs** produced from notes (a manuscript; an export). |

Rule of thumb: if the note *is* a thing you curate, it gets `-note`; if it *arranges* other notes or *is produced from* them, it stays bare. Every `-note` is also a markdown note with a `type` and a lifecycle field — but being markdown isn't enough to earn the suffix (`moc` is markdown too). `project-note` keeps the suffix because it records a project's own scope and status, not just a map of its parts. Full definition: [vault/templates.md](../../../memoria-docs/vault/templates.md#naming-convention--note-vs-bare-names).

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

**For depth:** [vault/frontmatter-schema.md](../../../memoria-docs/vault/frontmatter-schema.md) — the authoritative schema design.

**Drift discipline.** When the design schema changes, update this file to match. The Linter's structural-drift check flags this file if `updated` is older than the corresponding design doc.
