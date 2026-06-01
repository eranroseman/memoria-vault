---
title: Note types
parent: Reference
---

# Note types

The 16 note types, their canonical folders, templates, lifecycle, and ownership. For field-level detail see [frontmatter.md](frontmatter.md); for conceptual model see [explanation/architecture/vault.md](../explanation/architecture/vault.md).

---

## Type table

| Type | Folder | Template | Created by | Promoted by | Lifecycle |
| --- | --- | --- | --- | --- | --- |
| `fleeting-note` | `10-inbox/01-fleeting/` | `fleeting-note.md` | Human | Human (or discard) | `proposed` → `archived` |
| `answer-note` | `10-inbox/02-answers/` | `answer-note.md` | Writer | Writer until review; then human | Human → `claim-note` |
| `paper-note` | `20-sources/01-papers/` | `paper-note.md` | Librarian | Human (classification) | `proposed` → `current` |
| `item-note` | `20-sources/02-items/` | `item-note.md` | Librarian | Human (classification) | `proposed` → `current` |
| `person-note` | `20-sources/03-entities/01-people/` | `person-note.md` | Librarian | Human (classification) | `proposed` → `current` |
| `organization-note` | `20-sources/03-entities/02-organizations/` | `organization-note.md` | Librarian | Human (classification) | `proposed` → `current` |
| `venue-note` | `20-sources/03-entities/03-venues/` | `venue-note.md` | Librarian | Human (classification) | `proposed` → `current` |
| `claim-note` | `30-synthesis/01-claims/` | `claim-note.md` | Human | Human | `current` (+ `maturity`) |
| `reference-note` | `30-synthesis/02-reference/` | `reference-note.md` | Writer (draft) | Human (finalizes) | `proposed` → `current` |
| `moc` | `30-synthesis/03-moc/` | `moc.md` | Human | Human | `current` / `dormant` / `archived` |
| `project-note` | `40-workbench/` | `project-note.md` | Human | Human | `proposed` → `current` (+ `project_phase`) |
| `code-note` | `40-workbench/*/06-code/` | `code-note.md` | Coder or human | Human (review gate) | `proposed` → `current` → `archived` |
| `canvas` | `40-workbench/*/03-canvas/` | `canvas.md` | Human | Human | `proposed` → `current` |
| `draft` | `40-workbench/*/04-drafts/` | `draft.md` | Human | Human → `deliverable` on export | `proposed` → `current` (+ `draft_stage`) |
| `deliverable` | `50-deliverables/` | `deliverable.md` | Human / Coder (export task) | Terminal | `current` |
| `candidate-note` | `10-inbox/03-candidates/` | `candidate-note.md` | Librarian (`find`) / Verifier (`gap`) / human | Human (include → ingest; exclude → archive) | `proposed` → `archived` |

All 16 templates live in `00-meta/03-templates/`.

> **`candidate-note` is transient** — a discovery lead or ingestion dead-letter awaiting a human include/exclude decision. Carries `source` (`find` / `database-search` / `manual` / `capture-timeout` / `gap`), `candidate_status`, and `exclusion_reason`. It unifies the Librarian's discovery candidates and the Verifier's gap-cards. See [ADR — shared candidate frontmatter](../../project-files/decisions/21-shared-candidate-frontmatter.md).

---

## `-note` suffix rule

The `-note` suffix marks a **knowledge node** — an authoritative record of one unit of knowledge that carries its own content. Twelve of the 16 types carry the `-note` suffix — the durable knowledge nodes plus the transient `fleeting-note` and `candidate-note` — and their templates carry it too (`paper-note.md`, `claim-note.md`, …). The four bare-name views use bare template filenames (`moc.md`, `canvas.md`, `draft.md`, `deliverable.md`).

The four **bare names** (`moc`, `canvas`, `draft`, `deliverable`) are not knowledge nodes:

| Bare type | Kind |
| --- | --- |
| `moc` | View — aggregates links to other notes; content is its link graph. |
| `canvas` | View — a spatial composition of notes; Obsidian Canvas format. |
| `draft` | Output artifact — produced from claim notes and reference notes; not a record. |
| `deliverable` | Terminal output — exported; never edited after creation. |

---

## Lifecycle per type

Standard lifecycle is `proposed → current → archived`. Deviations:

| Type | Lifecycle notes |
| --- | --- |
| `fleeting-note` | Terminal is `archived` (discarded) or promoted (converted to another type and then archived). |
| `claim-note` | No `proposed` phase — created as `current`. Refinement tracked by `maturity` (`seedling` → `budding` → `evergreen`). |
| `moc` | Can be `dormant` (topic has gone quiet; not archived yet). |
| `deliverable` | Created as `current`; never promoted or archived in normal flow. |
| `project-note` | Refines `current` with `project_phase` (`active` · `paused` · `complete` · `abandoned`). |
| `draft` | Refines `current` with `draft_stage` (`outline` · `rough` · `polished` · `submitted`). |

---

## Promotion map

Legal promotion paths — what type a note becomes when it advances.

```text
fleeting-note ──┬──► paper-note / item-note   (Librarian classifies → human)
                ├──► claim-note               (human writes directly)
                └──► (discarded)

answer-note ───► claim-note      (human distills, after review)
claim-note ────► reference-note  (when evergreen + cross-linked)
claim-note ────► moc membership  (via frontmatter moc:)
claim-note ────► draft section   (cited in body)
draft ─────────► deliverable     (on export)
canvas ────────► draft           (informs structure; canvas then archived)
code-note ─────► project-note    (linked from project)
```

This is the mechanical view of every type transition, including the workbench-internal moves (`canvas → draft`, `code-note → project-note`) that the conceptual model omits. An `answer-note` is created fresh by the Writer in response to a query — it is **not** promoted from a `fleeting-note`. For *why* the gated promotions require human authorship — and why a `paper-note` never becomes a `claim-note` — see [promotion-model.md](../explanation/knowledge/promotion-model.md).

Promotion constraints:

| Rule | Detail |
| --- | --- |
| `fleeting-note` must move | Reviewed and either promoted or discarded — does not linger. |
| `answer-note` → `claim-note` | Only after human review. |
| `claim-note` → `reference-note` | Only when `maturity: evergreen` and sufficiently cross-linked. |
| `paper-note` never becomes `claim-note` | A source describes what the paper says; a claim is what the human thinks. |
| Archive, not delete | Archived notes remain for historical traceability. Only humans move notes to `95-archive/`. |
| Review-gated folder moves | Moving into `30-synthesis/` or `50-deliverables/` is human-only. |

---

## MOC creation threshold

Create a new MOC when a topic reaches **≥ 15–20 notes** (papers + claim notes combined). Build child MOCs when a branch has **> 20 claim notes + > 10 paper notes**. See [linking.md](linking.md#moc-thresholds) for the full threshold table.

---

## Template locations

Templates ship at `00-meta/03-templates/<type>.md`. The Templater plugin reads them; QuickAdd commands invoke them. The Linter's `skeleton-drift` detector validates that in-vault templates match this reference.

---

## Related

- The conceptual model behind the types: [note-types.md](../explanation/knowledge/note-types.md)
- The promotion rules referenced here: [promotion-model.md](../explanation/knowledge/promotion-model.md)
