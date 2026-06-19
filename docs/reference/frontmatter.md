---
title: Frontmatter fields
parent: Reference
---

# Frontmatter fields

The frontmatter contract for every typed note. **The single source is `.memoria/schemas/`** — per-type field schemas in `src/.memoria/schemas/types`, the type → folder map in `src/.memoria/schemas/folders.yaml`, and the calibrated thresholds in `src/.memoria/schemas/calibration.yaml`. The shared loader/validator is `src/.memoria/operations/lib/schema.py`; the Linter, the pre-commit gate, and the installer-skeleton tests all read it, so a schema change is a one-file edit, never a hunt across hardcoded lists. This page explains the grammar and the universal fields; the per-type tables live in [Note types](note-types.md).

---

## The field-kind grammar

Each type schema declares `required:` and `optional:` maps of `field: kind`, plus an `enums:` block and (optionally) `required_any:` — a list of field names of which at least one must be present (e.g. a `flag` needs `target` or `citekey`). The kinds:

| Kind | Accepts |
| --- | --- |
| `str` | a string |
| `int` | an integer (not a bool) |
| `bool` | a boolean |
| `date` | a YAML date or an ISO-8601 date string |
| `list` | a YAML sequence |
| `map` | a YAML mapping |
| `literal:<value>` | exactly that value — e.g. `type: literal:claim` pins the `type` field |
| `enum:<name>` | one of the values the schema's `enums.<name>` lists |

Unknown extra fields are **allowed** — the schema constrains, it does not enumerate. A schema example (`types/claim.yaml`):

```yaml
type: claim
category: notes
gated: true
enums:
  lifecycle: [current, retracted, archived]
  maturity: [seedling, budding, evergreen]
required:
  type: literal:claim
  lifecycle: enum:lifecycle
  title: str
  maturity: enum:maturity
  sources: list
optional:
  schema_version: int
  links: map
  topics: list
  superseded_by: str
  created: date
```

---


## Display order and grouping

The schema validates field presence and kind; display order is a shipped-vault convention so the Properties pane is scannable. Templates and deterministic emitters put fields in this order:

1. Human identity: `title` or `name`.
2. Schema identity and PI-facing state: `type`, then `lifecycle`.
3. Type-specific state: `maturity`, `certainty`, `agent_recommendation`, `loudness`, `origin`, or `ingest_status`.
4. Primary references: `citekey`, `entity`, `target`, `task_id`, `url`, `doi`.
5. Classification and relations: `research_area`, `methodology`, `topics`, `sources`, `links`, `relationships`.
6. Provenance and housekeeping: owned namespaces such as `_enrichment` / `_proposed_classification`, then `created`, `updated`, `enriched_date`, and version fields.

Obsidian does not have a global property-order schema file, so the shipped templates, emitters, and Bases carry this convention directly. The `memoria-property-badges.css` snippet colors the scan-critical state fields (`lifecycle`, `ingest_status`, `loudness`, and verification status) when Obsidian exposes editable property values; the field order still carries the meaning when snippets are disabled.

---

## `lifecycle` — the one chain

Every typed note carries `lifecycle`, drawn from the **universal chain** ([ADR-50](../adr/50-universal-lifecycle-and-maturity.md)):

```text
proposed → provisional → current → retracted → archived
```

Each type's schema declares the **subset** it uses (validated as `enum:lifecycle`; the subset must be ⊆ the chain — test-enforced):

| Subset | Types |
| --- | --- |
| full chain | `source`, `thesis` |
| `proposed → current → archived` | `candidate`, `gap`, `flag`, `alert`, `work-prompt`, `code-note`, `pattern`, `eval-task`, `worklist-item` |
| `proposed → archived` | `fleeting` |
| `current → retracted → archived` | `claim`, `paper`, `dataset` |
| `current → archived` | `project`, `person`, `organization`, `venue`, `repository`, `hub`, `index` |

`proposed` always means _awaiting the PI_. `retracted` is a state, not a deletion — supersession keeps the lineage (`superseded_by`). Claim queries and write-assist surfaces exclude claims with a non-empty `superseded_by` by default; include them only for lineage, audit, or supersession-history work. This lifecycle is the **PI-facing state**; the board's `status` enum is a separate, hidden execution mechanic (see [Kanban board reference](kanban-board.md)).

## `maturity` — a claim property, never a gate

Claims only: `seedling → budding → evergreen`. It describes how settled a claim is; nothing in the system blocks on it ([ADR-50](../adr/50-universal-lifecycle-and-maturity.md)).

---

## `links:` vs `relationships` — field presence

Notes (`source`, `claim`, `hub`) carry the authored `links:` map; catalog entities carry the given `relationships` map. Why the split exists and who asserts each — the authored-vs-given distinction — is owned by [Wikilink and link conventions](linking.md).

Two related fields: a `source` note's required `entity` field is a wikilink to the Catalog entity the note is about, and a `claim`'s required `sources` list holds citekeys (bibliographic provenance, not note links). The Linter's `frontmatter-link` detector checks that every wikilink in `links:` and `entity` resolves to a real note; citekeys are checked by the sweeps instead.

Project-gate argument edges may carry an optional `warrant` attribute on a
`supports` relation when the author wants to state the grounds-to-claim inference
explicitly ([ADR-79](../adr/79-argument-graph-and-warrant.md)). The schema keeps
`links:` as a map because older string-list relations and newer edge objects must
coexist during the alpha.5 transition.

---

## Project-gate fields

`project` and `thesis` notes add the Project gate's authored state and operation
cache ([ADR-77](../adr/77-project-gate.md), [ADR-78](../adr/78-thesis-note-type.md)):

| Field | Kind | Notes |
| --- | --- | --- |
| `scope_topics` | `list` | Topic boundary for the project map. |
| `inquiry` | `map` | PICO block: `population`, `intervention`, `comparison`, `outcome`. |
| `finer` | `map` | Answerability lens: `feasible`, `novel`, `relevant`. |
| `output_mode` | `enum` | `thesis` or `survey`. |
| `question_version` / `question_log` | `int` / `list` | Version and rationale log for question changes. |
| `gap_type` | `enum` | Project gap kind: `additive`, `conflict`, `fragility`, `structural`, `unstated-warrant`, or `refutation`. |
| `impact` / `on_path` | `int` / `bool` | Materialized structural-impact cache for Project dashboards. |
| `evidence_saturation` | `enum` | `unknown`, `unsaturated`, `saturated`, or `stale`. |
| `argument_stage` | `enum` | `cold-start`, `developing`, or `mature`. |
| `computed_at` | `date` | Timestamp for the derived cache; stale values are shown as stale, not silently current. |
| `refutation_sufficiency` / `refutation_sufficiency_at` | `bool` / `date` | PI stamp that the active thesis has faced its strongest available rebuttal; the Project operation treats this as saturation condition 3, not as a deterministic judgment. |
| `promoted_at` / `promoted_by` | `date` / `str` | Promotion provenance for a thesis. A `thesis` at `lifecycle: current` must carry `promoted_at`; proposed and provisional theses do not. |

Source notes also carry optional `evidence_level`, a CEBM-style enum
(`cebm-1` … `cebm-5`, `ungraded`) used when source appraisal becomes relevant to
Project work.

---

## The honesty-card fields

Inbox cards split into proposals (`candidate`, `gap`), verification cards (`flag`, `alert`), and work prompts (`work-prompt`) ([ADR-51](../adr/51-inbox-category-and-honesty-card.md)). Their field-level contract lives in [Inbox card fields](inbox-card-fields.md).

---

## Batch worklist fields

Worklist rows are `worklist-item` notes under `system/worklists/`. Their `lifecycle` says whether the row is still active in the vault; their separate `decision` field is the PI's batch-screening choice: `proposed`, `include`, `exclude`, `maybe`, or `archived`. `worklist` groups rows into one batch, `group` supports grouped sweeps, `rank` preserves report order, and `item_ref` points at the source/path/citekey being screened. The emitter raises one aggregate `work-prompt` for the batch, never one card per row.

---

## Other universal fields

| Field | Kind | Notes |
| --- | --- | --- |
| `type` | `literal:` | Pins the note to its schema. Set at creation; never changed. |
| `title` / `name` | `str` | Notes and cards use `title`; catalog entities use `name` (papers carry both `citekey` and `title`). |
| `created` | `date` | Optional everywhere. |
| `research_area`, `methodology`, `topics` | `list` | Controlled-vocabulary classification (papers, sources, claims); values live in [Vocabulary](vocabulary.md). |
| `ingest_status` | `enum` | Paper ingest floor/progress: `tier0`, `enriched`, `complete`, or `needs-human`. |

---

## Enforcement

| Where | What |
| --- | --- |
| Pre-commit gate | Every staged `.md` note must pass its type schema; exit 1 blocks the commit (`src/.memoria/operations/integrity/linter/precommit_check.py`). |
| Daily Linter cron | The `schema-check` and `frontmatter-link` detectors monitor between commits. |
| Exemptions | `system/` infrastructure (everything except `system/patterns/`) and vault-root navigation pages (`home.md`, `research-focus.md`, `troubleshooting.md`) are untyped and exempt. |

---

## Related

- The per-type field tables: [Note types](note-types.md)
- The controlled classification values: [Vocabulary](vocabulary.md)
- What validates this contract: [Linter: detectors and auto-fix](linter.md)
- Where the schema files live: [On-disk layout](on-disk-layout.md)
