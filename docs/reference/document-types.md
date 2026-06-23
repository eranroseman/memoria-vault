---
title: Document types
parent: Reference
---

# Document types

The 26 document types by category, with their folder homes, lifecycle subsets, and required fields. **The schemas are authoritative:** every type is defined by one YAML file under `src/.memoria/schemas/types`, and the type → folder map lives in `src/.memoria/schemas/folders.yaml` ([ADR-47](../adr/47-type-first-category-folders.md)). The Linter, the pre-commit hook, the policy MCP, and the installer all read those files — this page is the human-readable view, and the schemas win on any disagreement. For field semantics see [Frontmatter fields](frontmatter.md).

The 26 types group into: **6 entities** (catalog), **3 project types**, **5 notes**, **5 cards** (inbox), **4 system types** (pattern, eval task, worklist item, and worker card), and **3 navigation surfaces** (`space`, `queue`, and `maintenance`).

---

## Catalog entities (6)

Bibliographic / world records, keyed on stable IDs and carrying **given** `relationships` edges (the field contract is in [Frontmatter fields](frontmatter.md)). None is review-gated.

| Type | Folder | Lifecycle subset | Required fields | Key optional fields |
| --- | --- | --- | --- | --- |
| `paper` | `catalog/papers/` | `current → retracted → archived` | `citekey`, `title` | `doi`, `authors`, `year`, `venue`, `url`, `relationships`, `research_area`, `methodology` |
| `person` | `catalog/people/` | `current → archived` | `name` | `orcid`, `affiliations`, `relationships` |
| `organization` | `catalog/organizations/` | `current → archived` | `name` | `subtype` (lab · university · company · funder …), `location`, `relationships` |
| `venue` | `catalog/venues/` | `current → archived` | `name` | `subtype` (journal · conference · publisher …), `issn`, `relationships` |
| `dataset` | `catalog/datasets/` | `current → retracted → archived` | `name` | `doi`, `url`, `license`, `relationships` |
| `repository` | `catalog/repositories/` | `current → archived` | `name` | `url`, `language`, `license`, `relationships` |

---

## Projects (3)

Project records live under `projects/` and anchor the Project space ([ADR-77](../adr/77-project-gate.md)). They are not review-gated folders; the gated transition is the thesis promotion to `current`.

| Type | Folder | Lifecycle subset | Required fields | Key optional fields |
| --- | --- | --- | --- | --- |
| `project` | `projects/` | `current → archived` | `title`, `slug`, `scope_topics`, `inquiry`, `finer`, `output_mode`, `question_version`, `question_log` | `active_thesis`, `refutation_sufficiency`, `impact`, `on_path`, `evidence_saturation`, `argument_stage`, `computed_at` |
| `thesis` | `projects/` | full chain | `title`, `project`, `sources` | `links`, `superseded_by`, `refutation_sufficiency`, `promoted_at`, `promoted_by`, `impact`, `on_path`, `evidence_saturation`, `argument_stage`, `computed_at` |
| `code-note` | `projects/` | `proposed → current → archived` | `title`, `project`, `agent`, `task`, `acceptance` | `motivating_claims`, `inputs`, `outputs`, `run_command`, `dependencies`, `repository`, `created` |

`project.inquiry` carries the PICO block (`population`, `intervention`, `comparison`, `outcome`) and `project.finer` carries the answerability lens. A `thesis` starts at `proposed`; promotion to `current` is the project's review transition, not a template default. Current theses must carry `promoted_at` so the promotion is visible to the Linter and pre-commit hook. A `code-note` is the Engineer's handoff/provenance note for external coding agents under a project's `code/` scratch.

---

## Notes (5)

The PI's knowledge, carrying **authored** `links:` edges (the field contract is in [Frontmatter fields](frontmatter.md)). Two of the five live in review-gated zones — the policy MCP degrades every agent write there to `dry_run`.

| Type | Folder | Gated | Lifecycle subset | Required fields | Key optional fields |
| --- | --- | --- | --- | --- | --- |
| `fleeting` | `notes/fleeting/` | no | `proposed → archived` | `origin` (`human` / `agent` / `chat`) | `title` |
| `source` | `notes/sources/` | no | `proposed → provisional → current → retracted → archived` (the full chain) | `title`, `entity` (wikilink to the Catalog entity it is about) | `source_type`, `research_area`, `methodology`, `links` |
| `claim` | `notes/claims/` | **yes** | `current → retracted → archived` | `title`, `maturity`, `sources` (every claim → a citekey) | `schema_version`, `links` (supports / contradicts / …), `topics`, `superseded_by` |
| `hub` | `notes/hubs/` | **yes** | `current → archived` | `title`, `topic` | `members`, `links` |
| `index` | `notes/indexes/` | no | `current → archived` | `title` | — |

`hub` and `index` are both navigation aids, but they are not substitutes. A `hub` is a curated synthesis surface: it explains an area, selects members, and lives behind the review gate. An `index` is a lightweight entry-point register under `notes/indexes/`: useful for lists and signposts, but not a claim that the set has been synthesized or curated.

`maturity` is a claim **property, never a gate** — its values and the universal lifecycle chain are specified in [Frontmatter fields](frontmatter.md). Claim template version 2 includes `schema_version: 2`; query and write-assist surfaces exclude claims with non-empty `superseded_by` unless the task is explicitly about supersession history.

---

## Inbox cards (5)

The agent → human action queue ([ADR-51](../adr/51-inbox-category-and-honesty-card.md)). All five live flat in `inbox/`, start at `lifecycle: proposed` (awaiting the PI), and converge to `archived`. Three shapes:

| Shape | Types | What it carries |
| --- | --- | --- |
| **Proposals** | `candidate`, `gap` | The honesty body — arguments, never a verdict. A `candidate` proposes an acceptance (e.g. a discovered paper); a `gap` proposes a missing piece (coverage gap, missing link). |
| **Verification cards** | `flag`, `alert` | Lead with the finding and carry the verdict. A `flag` is a pointed finding (e.g. a retraction); an `alert` is a standing system warning. |
| **Work prompts** | `work-prompt` | An action and a pointer, never a verdict — e.g. the review prompt the board export raises when a card reaches `done` ([Kanban board reference](kanban-board.md)). |

Use `flag` for a bounded verification finding that needs a decision about one object or assertion: retraction, extraction conflict, link contradiction, or failed invariant. Use `alert` for a standing warning about a condition the PI may need to monitor over time: structural drift, backlog health, or repeated runtime failure. Both are Signal documents and lead with the finding; neither is a proposal.

See [Inbox card fields](inbox-card-fields.md) for the complete per-document-type field contract (required, `required_any`, optional, and the shared `raised_by` / `loudness` fields). Operations and lanes never invent card formats — every card goes through the shared writer `src/.memoria/operations/lib/inbox.py`.

---

## System types (4)

| Type | Folder | Lifecycle subset | Required fields | Key optional fields |
| --- | --- | --- | --- | --- |
| `pattern` | `system/patterns/` | `proposed → current → archived` | `title`, `posture`, `mode` (`library` / `project` / `both`), `action`, `input`, `output_target` | `model_hint`, `version`, `adapted_from` |
| `eval-task` | `system/eval/` | `proposed → current → archived` | `title`, `workflow`, `lane` (`catalog` / `extract` / `link` / `map` / `draft` / `verify` / `code`) | `references`, `created` |
| `worklist-item` | `system/worklists/` | `proposed → current → archived` | `title`, `decision`, `worklist`, `item_ref` | `source_report`, `group`, `rank`, `reason`, `created` |
| `worker-card` | `system/board/` | `current → archived` | `title`, `task_id`, `lane`, `status` | `as_of`, `review_status`, `retry_count`, `reason`, `expected_outputs` |

Patterns are curated prompt-transformations stored as data ([ADR-53](../adr/53-pattern-library.md)); only `lifecycle: current` patterns are runnable, and the runner refuses an `output_target` inside a gated zone. Eval tasks are the [Vault eval](vault-eval.md) gold set ([ADR-11](../adr/11-vault-eval-maintenance.md)); only `lifecycle: current` tasks dispatch. Worklist items are file-backed rows for ADR-54 batch screening: the PI toggles each row's `decision` in `system/worklists/worklists.base`, while the Inbox receives one aggregate `work-prompt` for the batch. Worker cards are the file-backed board rows under `system/board/`, separate from Inbox cards because they are execution state rather than PI-facing prompts. `system/` is otherwise untyped infrastructure.

---

## Navigation surfaces (3)

The top-level surfaces under `spaces/`. The three durable **spaces** are the rooms you work in; the **queue** (the Inbox) is a transient triage surface that converges to empty; **maintenance** is the weekly structural-debt collection. Space-switching is owned by the left-pane rail, so these notes carry no nav row.

| Type | Folder | Lifecycle subset | Required fields | Key optional fields |
| --- | --- | --- | --- | --- |
| `space` | `spaces/` | `current → archived` | `title`, `space` (`library` / `knowledge` / `project`) | `created` |
| `queue` | `spaces/` | `current → archived` | `title` | `created` |
| `maintenance` | `spaces/` | `current → archived` | `title` | `created` |

---

## Gating and transience

From `folders.yaml`, the single source the policy MCP and the Linter share:

| Setting | Value |
| --- | --- |
| `gated_prefixes` (agent writes degrade to `dry_run`) | `notes/claims/` · `notes/hubs/` |
| `transient_prefixes` (items converge to `archived` and leave active views) | `inbox/` |
| `categories` (legal vault-root folders) | `catalog` · `notes` · `projects` · `inbox` · `spaces` · `system` |
| `skeleton` sample bundle | `.memoria/samples/mediterranean-diet/` holds optional tutorial notes until **Memoria: load sample vault** copies them into live homes |

---

## Templates

Human-facing starter notes for 20 of the 26 types ship in `src/system/templates` (patterns, eval tasks, spaces, the inbox queue, maintenance collection, and worker cards are authored by their owning surfaces). Templates are scaffolding — the schemas, not the templates, are what validation runs against; the Linter's golden-copy check keeps the deployed templates byte-identical to the shipped ones.

---

## Related

- Field kinds, the universal lifecycle, and the two edge kinds: [Frontmatter fields](frontmatter.md)
- The folder tree the homes map into: [On-disk layout](on-disk-layout.md)
- What enforces the schemas: [Linter: detectors and auto-fix](linter.md) and [Policy MCP](policy-mcp.md)
