---
title: Frontmatter fields
parent: Reference
---

# Frontmatter fields

The frontmatter contract for every typed note. **The single source is `.memoria/schemas/`** — per-type field schemas in [src/.memoria/schemas/types/](../../src/.memoria/schemas/types), the type → folder map in [src/.memoria/schemas/folders.yaml](../../src/.memoria/schemas/folders.yaml), and the calibrated thresholds in [src/.memoria/schemas/calibration.yaml](../../src/.memoria/schemas/calibration.yaml). The shared loader/validator is [src/.memoria/engines/lib/schema.py](../../src/.memoria/engines/lib/schema.py); the Linter, the pre-commit gate, and the installer-skeleton tests all read it, so a schema change is a one-file edit, never a hunt across hardcoded lists. This page explains the grammar and the universal fields; the per-type tables live in [Note types](note-types.md).

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
  links: map
  topics: list
  superseded_by: str
  created: date
```

---

## `lifecycle` — the one chain

Every typed note carries `lifecycle`, drawn from the **universal chain** ([ADR-50](../adr/50-universal-lifecycle-and-maturity.md)):

```text
proposed → provisional → current → retracted → archived
```

Each type's schema declares the **subset** it uses (validated as `enum:lifecycle`; the subset must be ⊆ the chain — test-enforced):

| Subset | Types |
| --- | --- |
| full chain | `source` |
| `proposed → current → archived` | `candidate`, `gap`, `flag`, `alert`, `work-prompt`, `pattern` |
| `proposed → archived` | `fleeting` |
| `current → retracted → archived` | `claim`, `paper`, `dataset` |
| `current → archived` | `person`, `organization`, `venue`, `repository`, `hub`, `index` |

`proposed` always means _awaiting the PI_. `retracted` is a state, not a deletion — supersession keeps the lineage (`superseded_by`). This lifecycle is the **PI-facing state**; the board's `status` enum is a separate, hidden execution mechanic (see [Kanban board reference](kanban-board.md)).

## `maturity` — a claim property, never a gate

Claims only: `seedling → budding → evergreen`. It describes how settled a claim is; nothing in the system blocks on it ([ADR-50](../adr/50-universal-lifecycle-and-maturity.md)).

---

## `links:` vs `relationships` — two kinds of connection

[ADR-52](../adr/52-links-vs-relationships.md) splits connections by who asserts them:

| Field | Carried by | Asserted by | Examples |
| --- | --- | --- | --- |
| `links:` (map) | **notes** (`source`, `claim`, `hub`) | **Authored** — the PI's thinking | `supports:`, `contradicts:`, `extends:` … values are wikilinks |
| `relationships` (map) | **catalog entities** | **Given** — facts from the bibliographic record, written by the ingest engine | `cited_by:`, `authored_by:`, `published_in:` … |

Two related fields: a `source` note's required `entity` field is a wikilink to the Catalog entity the note is about, and a `claim`'s required `sources` list holds citekeys (bibliographic provenance, not note links). The Linter's `frontmatter-link` detector checks that every wikilink in `links:` and `entity` resolves to a real note; citekeys are checked by the sweeps instead.

---

## The honesty-card fields

Inbox cards split into three shapes ([ADR-51](../adr/51-inbox-category-and-honesty-card.md)):

**Proposals** (`candidate`, `gap`) carry the honesty body — arguments, never a verdict:

| Field | Kind | Meaning |
| --- | --- | --- |
| `action` | `str` | What the PI would be accepting. |
| `argument_for` | `str` | The agent's case for it. |
| `argument_against` | `str` | The agent's honest self-rebuttal. |
| `what_tipped_it` | `str` | Why the agent raised it anyway. |
| `certainty` | `enum` | `confident` / `likely` / `unsure` — 3-level, calibrated. |

**Verification cards** (`flag`, `alert`) lead with the finding:

| Field | Kind | Meaning |
| --- | --- | --- |
| `finding` | `str` | The finding itself, first — verification verdicts are not a given. |
| `agent_recommendation` | `enum` | `inconclusive` / `issues-found` / `clean` — the verdict _is_ the payload. Required on `flag`, optional on `alert`. |
| `target` / `citekey` | `str` | What the card points at (`required_any` on `flag`). |

**Work prompts** (`work-prompt`) carry the action — like proposals, never a verdict:

| Field | Kind | Meaning |
| --- | --- | --- |
| `action` | `str` | What the PI should do (e.g. review the finished work, then accept or archive). |
| `what_happened` | `str` | What finished/triggered the prompt — e.g. which lane completed which card. |
| `target` / `task_id` | `str` | Where to look: the output path(s) and/or the board card (`required_any`). |
| `lane` | `str` | Which lane finished (optional). |

All cards share `raised_by` (`str`) and `loudness` (`enum`: `quiet` / `notice` / `alert` / `block`).

`agent_recommendation` never appears on a proposal or a work prompt — that separation (no verdict on proposals) is enforced by the shared card writer [src/.memoria/engines/lib/inbox.py](../../src/.memoria/engines/lib/inbox.py).

---

## Other universal fields

| Field | Kind | Notes |
| --- | --- | --- |
| `type` | `literal:` | Pins the note to its schema. Set at creation; never changed. |
| `title` / `name` | `str` | Notes and cards use `title`; catalog entities use `name` (papers carry both `citekey` and `title`). |
| `created` | `date` | Optional everywhere. |
| `research_area`, `methodology`, `topics` | `list` | Controlled-vocabulary classification (papers, sources, claims). |

---

## Enforcement

| Where | What |
| --- | --- |
| Pre-commit gate | Every staged `.md` note must pass its type schema; exit 1 blocks the commit ([src/.memoria/engines/linter/precommit_check.py](../../src/.memoria/engines/linter/precommit_check.py)). |
| Daily Linter cron | The `schema-check` and `frontmatter-link` detectors monitor between commits. |
| Exemptions | `system/` infrastructure (everything except `system/patterns/`) and vault-root navigation pages (`home.md`, `research-focus.md`, `troubleshooting.md`) are untyped and exempt. |

---

## Related

- The per-type field tables: [Note types](note-types.md)
- What validates this contract: [Linter: detectors and auto-fix](linter.md)
- Where the schema files live: [On-disk layout](on-disk-layout.md)
