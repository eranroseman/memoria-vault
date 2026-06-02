---
title: Frontmatter fields
parent: Reference
---

# Frontmatter fields

Every YAML field Memoria uses, its type, allowed values, who owns it, and which note types carry it. For the field-namespace model see [Namespace ownership](#namespace-ownership). For per-type lifecycle refinements see [note-types.md](note-types.md).

**Precedence.** When a runtime template (`00-meta/03-templates/*.md`) disagrees with this file, this file governs — the template is what must change. When in doubt, [implementation-status.md](../../project-files/plans/implementation-status.md) tracks build state.

---

## Namespace ownership

Frontmatter is divided into three namespaces with distinct owners. Mixing namespaces or crossing ownership boundaries is a policy violation.

| Namespace | Owner | Rule |
| --- | --- | --- |
| **Main YAML** | Human (authoritative) | Human-set values are authoritative. An agent must never silently overwrite. |
| **`_proposed_classification`** | Agent (proposal only) | Agent populates; human reviews and promotes to main YAML on classification; block is then removed. |
| **`_enrichment`** | Agent (maintained) | Agent refreshes on schedule. Values are mutable. Agent must never overwrite corresponding human-set main fields. |

---

## Global fields

Present on every note.

| Field | Type | Allowed values | Owner | Notes |
| --- | --- | --- | --- | --- |
| `type` | string (enum) | See [Note types](#note-type-values) | Human | Set at creation; never changed after. |
| `schema_version` | integer | `1` (current) | System | Bumped when the schema breaks backward compatibility. |

---

## Lifecycle fields

| Field | Type | Allowed values | Owner | Present on |
| --- | --- | --- | --- | --- |
| `lifecycle` | string (enum) | `proposed` · `current` · `dormant` · `archived` | Human | Every note |
| `maturity` | string (enum) | `seedling` · `budding` · `evergreen` | Human | `claim-note` only |
| `project_phase` | string (enum) | `active` · `paused` · `complete` · `abandoned` | Human | `project-note` only |
| `draft_stage` | string (enum) | `outline` · `rough` · `polished` · `submitted` | Human | `draft` only |

### `lifecycle` values

| Value | Meaning |
| --- | --- |
| `proposed` | New; not yet reviewed or classified. Default at creation for most types. |
| `current` | Active and maintained. Dashboards surface this state. |
| `dormant` | Created, not actively maintained; may be revived. Used by `moc`. |
| `archived` | Terminal. Retired from active use. Never deleted; queryable. |

### `maturity` values (claim-notes only)

| Value | Meaning |
| --- | --- |
| `seedling` | First draft; connections sparse. Default at creation. |
| `budding` | Supported by multiple sources; linked from at least one other note. |
| `evergreen` | Well-connected, tested against the corpus, stable. Qualifies when it has cross-links from at least three distinct sources or claim notes. Ready for promotion to `reference-note`. |

A superseded claim is not tracked by `maturity` — it carries `superseded_by` and `lifecycle: archived` (see [Claim-note fields](#claim-note-fields)).

---

## Identity and time fields

| Field | Type | Owner | Present on | Notes |
| --- | --- | --- | --- | --- |
| `title` | string | Human | Every note | Human-set; authoritative. Do not let agents overwrite. |
| `created` | date (`YYYY-MM-DD`) | Human / system | Every note | Date the note entered the vault. Set once at creation. |
| `updated` | date (`YYYY-MM-DD`) | Human / system | Every note | Last substantive edit. The Linter's `skeleton-drift` check compares this against the design file it mirrors. |
| `citekey` | string | Zotero via Better BibTeX | `paper-note` | Format: `auth.lower + year + shorttitle(1,0)`. Zotero is the source of truth. |
| `doi` | string | Zotero / agent (promoted from `_enrichment`) | `paper-note` | Promote from `_enrichment` once verified. |
| `projects` | list of strings | Human | Most notes | Project slugs this note belongs to. Links a note to `40-workbench/<project>/`. |

---

## Domain fields

Open fields — Memoria does not enforce a controlled vocabulary for these. Define your own in a vocabulary reference (see [linking.md](linking.md#vocabulary-discipline)).

| Field | Type | Owner | Notes |
| --- | --- | --- | --- |
| `topic` | string or list | Human | Research topic(s). Keep to ~30 terms per corpus for consistency. |
| `study_design` | string | Human | e.g. `rct`, `observational`, `meta-analysis`. Not enforced; define per project. |
| `methods` | list of strings | Human | Methodological keywords. Not enforced. |

---

## MOC fields

| Field | Type | Owner | Notes |
| --- | --- | --- | --- |
| `scope` | string (enum) | Human | The MOC's organizing axis (`moc` notes only): `topic` (conceptual cluster) · `domain` (broad research area) · `project` (per-project synthesis hub) · `method` (methodological cluster). |

---

## Source-note fields

Fields specific to ingested sources (`paper-note`, `item-note`, entities).

| Field | Type | Allowed values | Owner | Present on |
| --- | --- | --- | --- | --- |
| `pub_status` | string (enum) | `active` · `preprint` · `retracted` · `deprecated` · `expression-of-concern` | Human / agent | `paper-note` |
| `maintenance_status` | string (enum) | `active` · `deprecated` · `archived` · `unmaintained` | Human / agent | `item-note` |
| `role_in_stack` | string (enum) | `primary-tool` · `dependency` · `alternative` · `reference-only` | Human | `item-note` |
| `outreach_status` | string | — | Human | `person-note` (people you intend to contact; blank for entities tracked only for the research graph) |
| `full_text_reviewed` | boolean | `true` · `false` | Human | `paper-note` · `item-note` | Human sets to `true` after reviewing the full text. Dashboards query this. |
| `enriched_date` | date (`YYYY-MM-DD`) | — | Agent | Top-level (not inside `_enrichment`) — dashboards and the Linter's stale-enrichment check query it directly. |
| `promoted_date` | date (`YYYY-MM-DD`) | — | Human | `claim-note` | Set when the note is moved to `30-synthesis/02-reference/` with `lifecycle: current`. Used to measure triage-to-promotion latency. |

> **Note on `added`.** Earlier schema revisions used a single `added` field; the canonical pair is now `created` + `updated`. Any lingering `added` in an old note should be read as an alias for `created`.

### Enrichment staleness cadence

`enriched_date` is read against a per-type cadence — different source types decay at different rates, so a single universal threshold over- or under-flags depending on type. The Linter is the authority for these values (`memoria-linter` SOUL.md, "Enrichment staleness by type"); it surfaces stale notes in the weekly dashboard and never re-enriches without an explicit or scheduled trigger.

| Source type | Re-enrich every | What changes |
| --- | --- | --- |
| Article | 180 days | Citation count, related papers |
| Preprint | 30 days | May have been published; check for a journal version |
| Person | 90 days | New papers, affiliation changes |
| Organization | 365 days | Rarely changes |
| Repository | 30 days | Stars, issues, releases, maintenance status |
| Package | 30 days | New versions, deprecation |

### `pub_status` values (paper-note)

- `active` — published, not retracted, current.
- `preprint` — not yet peer-reviewed.
- `retracted` — formally withdrawn; the note stays for provenance but is excluded from active queries.
- `expression-of-concern` — flagged by the publisher but not retracted.
- `deprecated` — superseded by a stronger synthesis or newer paper (use `superseded_by:` to point at the superseding note).

Retraction tracking lives **outside** the vault: Zotero 9 with retraction monitoring (`extensions.zotero.retractionWatch.enabled: true`) checks CrossRef and Retraction Watch automatically, and the Verifier's `retraction-check` skill surfaces disagreements so the human can update `pub_status`. The agent never silently flips a note to `retracted` — see [run-a-retraction-sweep.md](../how-to-guides/maintenance/run-a-retraction-sweep.md).

### `role_in_stack` values (item-note)

Disambiguates how an item relates to your work — and powers queries like "primary tools not re-enriched in 30 days," where alternatives and reference-only items can decay quietly but primary tools shouldn't.

- `primary-tool` — actively used day-to-day (e.g. Obsidian, Hermes, Zotero).
- `dependency` — something a primary tool depends on (e.g. Better BibTeX under Zotero).
- `alternative` — evaluated and not chosen; kept for comparison and provenance.
- `reference-only` — referenced in the literature but not part of your stack.

`maintenance_status` is the item equivalent of a paper note's `pub_status`; the Linter's "stale items" check surfaces items whose `last_checked` is older than 90 days.

### Source tagging: `study_design`, `methods`, `topic`

Three fields, three distinct jobs — mixing them in one field makes all three query types unreliable.

| Field | Question | Cardinality | Vocabulary |
| --- | --- | --- | --- |
| `study_design` | What is the research architecture? | One value | Controlled (e.g. RCT, qualitative, design-science) |
| `methods` | What specific techniques? | Many values | Free-tag first, consolidate at ~50 papers |
| `topic` | What conceptual content? | Many values | Free-tag first, consolidate at ~50 papers |

### The paper-note URI fields: `zotero_uri`, `pdf_uri`, `extract_path`

Three different reaches into the same paper — each a one-click affordance from the paper-note into a specific representation. **The PDF lives in Zotero, not in the vault** (Memoria treats Zotero as the authoritative PDF store; the vault holds the curated paper-note and the machine-generated extract). The Librarian populates all three during ingest — none are human-typed.

- **`zotero_uri`** — `zotero://select/items/<key>`. Opens the *item record* in Zotero (citation metadata, attachments, tags, retraction status). Two-click reach to the PDF.
- **`pdf_uri`** — `zotero://open-pdf/library/items/<key>`. Opens the *PDF itself* in Zotero's reader. One-click reach to read or annotate.
- **`extract_path`** — vault-relative path to the Marker-extracted markdown (conventionally `90-assets/extracts/<citekey>.md`). The in-vault, searchable representation — use to grep, quote, or feed the text to a model.

---

## Claim-note fields

| Field | Type | Owner | Notes |
| --- | --- | --- | --- |
| `superseded_by` | wikilink | Human | Points to the claim-note that replaces this one. Sets `lifecycle: archived` implicitly. See ADR-10. |
| `relations` | block | Human | Opt-in typed relations block (ADR-8). Structure: `supports: [...]` / `contradicts: [...]`. Human-set only. |

---

## Agent-managed namespaces

### `_proposed_classification` block

Agent-written proposal; human reviews and selectively promotes fields to main YAML. Removed after classification is complete.

| Sub-field | Type | Notes |
| --- | --- | --- |
| `topic` | string or list | Agent's proposed topic(s). |
| `study_design` | string | Agent's proposed study design. |
| `methods` | list of strings | Agent's proposed methods. |

### `_enrichment` block

Agent-maintained; refreshed on schedule. Values drift over time; keep in `_enrichment`, not in main YAML.

| Sub-field | Type | Notes |
| --- | --- | --- |
| `abstract` | string | Paper abstract from API. |
| `citation_count` | integer | Citation count at last refresh. |
| `open_access` | boolean | OA status at last refresh. |
| `venue` | string | Journal/conference name from API. |
| `openalex_id` | string | OpenAlex record ID. May be promoted to main YAML once verified. |
| `orcid` | string | Author ORCID. May be promoted once verified. |
| `ror` | string | Institution ROR ID. May be promoted once verified. |

**Promotion rule.** Stable identifiers (DOI, OpenAlex ID, ORCID, ROR) may be promoted from `_enrichment` to main YAML once verified. Derived metrics (citation counts, OA status) remain in `_enrichment`.

---

## Note-type values

The complete set of valid `type` values. Each maps to exactly one note type in [note-types.md](note-types.md).

```text
fleeting-note  answer-note    paper-note    item-note
person-note    organization-note  venue-note  claim-note
reference-note  moc           project-note  code-note
canvas         draft          deliverable    candidate-note
```

### Candidate-note fields

Transient leads / ingestion dead-letters in `10-inbox/03-candidates/` ([ADR — shared candidate frontmatter](../../project-files/decisions/17-shared-candidate-frontmatter.md)).

| Field | Type | Allowed values | Owner | Present on |
| --- | --- | --- | --- | --- |
| `source` | string (enum) | `find` · `database-search` · `manual` · `capture-timeout` · `gap` | Agent / human | `candidate-note` |
| `candidate_status` | string (enum) | `pending-screen` · `pending-ingest` · `included` · `excluded` | Human | `candidate-note` |
| `exclusion_reason` | string | — | Human | `candidate-note` (set only when `excluded`) |

---

## Frontmatter not for notes

`status` is a **board card field** (Hermes built-in). It is not a note field. The value sets for `status` (execution lifecycle) and `lifecycle` (note lifecycle) are deliberately disjoint — never use one in place of the other. See [kanban-board.md](kanban-board.md#execution-lifecycle).

---

## Related

- Why lifecycle fields exist: [lifecycle-over-topic.md](../explanation/knowledge/lifecycle-over-topic.md)
- The promotion rules over these fields: [promotion-model.md](../explanation/knowledge/promotion-model.md)
