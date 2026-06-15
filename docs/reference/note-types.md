---
title: Note types
parent: Reference
---

# Note types

The 18 note types by category, with their folder homes, lifecycle subsets, and required fields. **The schemas are authoritative:** every type is defined by one YAML file under `src/.memoria/schemas/types`, and the type → folder map lives in `src/.memoria/schemas/folders.yaml` ([ADR-47](../adr/47-type-first-category-folders.md)). The Linter, the pre-commit gate, the policy MCP, and the installer all read those files — this page is the human-readable view, and the schemas win on any disagreement. For field semantics see [Frontmatter fields](frontmatter.md).

The 18 types group into four categories: **6 entities** (catalog), **5 notes**, **5 cards** (inbox), and **2 system types** (the pattern and the eval task).

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

## Notes (5)

The PI's knowledge, carrying **authored** `links:` edges (the field contract is in [Frontmatter fields](frontmatter.md)). Two of the five live in review-gated zones — the policy MCP degrades every agent write there to `dry_run`.

| Type | Folder | Gated | Lifecycle subset | Required fields | Key optional fields |
| --- | --- | --- | --- | --- | --- |
| `fleeting` | `notes/fleeting/` | no | `proposed → archived` | `origin` (`human` / `agent` / `chat`) | `title` |
| `source` | `notes/sources/` | no | `proposed → provisional → current → retracted → archived` (the full chain) | `title`, `entity` (wikilink to the Catalog entity it is about) | `source_type`, `research_area`, `methodology`, `links` |
| `claim` | `notes/claims/` | **yes** | `current → retracted → archived` | `title`, `maturity`, `sources` (every claim → a citekey) | `links` (supports / contradicts / …), `topics`, `superseded_by` |
| `hub` | `notes/hubs/` | **yes** | `current → archived` | `title`, `topic` | `members`, `links` |
| `index` | `notes/indexes/` | no | `current → archived` | `title` | — |

`maturity` is a claim **property, never a gate** — its values and the universal lifecycle chain are specified in [Frontmatter fields](frontmatter.md). `hub` is the renamed MOC; the `reference` type was dropped in the same decision ([ADR-50](../adr/50-universal-lifecycle-and-maturity.md)).

---

## Inbox cards (5)

The agent → human action queue ([ADR-51](../adr/51-inbox-category-and-honesty-card.md)). All five live flat in `inbox/`, start at `lifecycle: proposed` (awaiting the PI), and converge to `archived`. Three shapes:

**Proposals** carry the honesty body — arguments, never a verdict:

| Type | Required fields | Notes |
| --- | --- | --- |
| `candidate` | `title`, `action`, `argument_for`, `argument_against`, `what_tipped_it`, `certainty` | A proposed acceptance (e.g. a discovered paper). `certainty` is the 3-level calibrated enum `confident` / `likely` / `unsure`. Optional: `citekey`, `url`. |
| `gap` | same honesty fields as `candidate` | A proposed missing piece (coverage gap, missing link). |

**Verification cards** lead with the finding and carry the verdict:

| Type | Required fields | Notes |
| --- | --- | --- |
| `flag` | `title`, `finding`, `agent_recommendation`, and at least one of `target` / `citekey` (`required_any`) | A pointed verification finding (e.g. a retraction, an identity disagreement). |
| `alert` | `title`, `finding` | A standing system warning. `agent_recommendation` is optional here. |

**Work prompts** carry an action and a pointer — never a verdict:

| Type | Required fields | Notes |
| --- | --- | --- |
| `work-prompt` | `title`, `action`, `what_happened`, and at least one of `target` / `task_id` (`required_any`) | Work waiting on the PI — e.g. the review prompt the board export raises when a card reaches `done` ([Kanban board reference](kanban-board.md)). Optional: `lane`. |

All cards share the optional `raised_by` and `loudness` fields (the `loudness` enum and the honesty-card field contract are specified in [Frontmatter fields](frontmatter.md)). Engines and lanes never invent card formats — every card goes through the shared writer `src/.memoria/operations/lib/inbox.py`.

---

## System types (2)

| Type | Folder | Lifecycle subset | Required fields | Key optional fields |
| --- | --- | --- | --- | --- |
| `pattern` | `system/patterns/` | `proposed → current → archived` | `title`, `posture`, `mode` (`library` / `project` / `both`), `action`, `input`, `output_target` | `model_hint`, `version`, `adapted_from` |
| `eval-task` | `system/eval/` | `proposed → current → archived` | `title`, `workflow`, `lane` (`catalog` / `extract` / `link` / `map` / `draft` / `verify` / `code`) | `references`, `created` |

Patterns are curated prompt-transformations stored as data ([ADR-53](../adr/53-pattern-library.md)); only `lifecycle: current` patterns are runnable, and the runner refuses an `output_target` inside a gated zone. Eval tasks are the [Vault eval](vault-eval.md) gold set ([ADR-11](../adr/11-vault-eval-maintenance.md)); only `lifecycle: current` tasks dispatch. `system/` is otherwise untyped infrastructure — patterns and eval tasks are the only typed notes under it.

---

## Gating and transience

From `folders.yaml`, the single source the policy MCP and the Linter share:

| Setting | Value |
| --- | --- |
| `gated_prefixes` (agent writes degrade to `dry_run`) | `notes/claims/` · `notes/hubs/` |
| `transient_prefixes` (items converge to `archived` and leave active views) | `inbox/` |
| `categories` (legal vault-root folders) | `catalog` · `notes` · `projects` · `inbox` · `system` |

---

## Templates

Human-facing starter notes for 16 of the 18 types ship in `src/system/templates` (patterns and eval tasks are authored directly in `system/patterns/` and `system/eval/`). Templates are scaffolding — the schemas, not the templates, are what validation runs against; the Linter's golden-copy check keeps the deployed templates byte-identical to the shipped ones.

---

## Related

- Field kinds, the universal lifecycle, and the two edge kinds: [Frontmatter fields](frontmatter.md)
- The folder tree the homes map into: [On-disk layout](on-disk-layout.md)
- What enforces the schemas: [Linter: detectors and auto-fix](linter.md) and [Policy MCP](policy-mcp.md)
