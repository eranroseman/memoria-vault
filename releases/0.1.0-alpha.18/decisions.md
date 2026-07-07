# 0.1.0-alpha.18 Decisions

This ledger captures release-time decisions as dated Y-statements. Historical
notes, ADRs, and design documents (here principally
`scratch/memoria-data-structure/data-structure-analysis.md`) are evidence; the
implemented system and this release ledger are the decision-time record until the
release closes into `design-history/`. Entries below are **proposed** — alpha.18 is
a design under review, not an accepted release; nothing here is ratified merely by
being written (per `0.1.0-alpha.18-design.md`'s own status line).

## 2026-07-07 - alpha.18 is normalization-only; the query substrate + engine defer to a `query-architecture` release

Y: alpha.18 will implement only the data-structure *normalization* the analysis
recommends — the OpenAlex collision renames, the delete-and-fold of the markdown
`work`/`source-note` types, the bundle-root layout, the `note` frontmatter changes,
the `analyze_gaps` free-join, drift-prevention, and the migration plumbing — and
will **not** add the new derived query-substrate tables (`passages`, `passages_fts`,
`passages_vec`, `file_index_state`, `concept_edges`), their populate/reindex/embed
machinery, or the retrieval engine (RRF, dual-level expansion, reranking, synthesis).
Those defer together to a named follow-on `query-architecture` release.

Because: the deferred tables are *derived* caches and an engine with no consumer until
that engine exists — building an embedding pipeline or a passage-sync loop before any
reader queries it is the speculative machinery the project's simplest-design guardrail
rejects. The analysis itself keeps the two halves in two documents (`data-structure-`
vs `query-mechanism-analysis.md`). The seam is clean: alpha.18 leaves every *authored*
name and shape correct, and the derived tables attach to correct names in one later
schema bump alongside the engine that reads them.

Pointers:
- Evidence: `0.1.0-alpha.18-design.md` §0/§3; `data-structure-analysis.md` Part 8, `query-mechanism-analysis.md`
- Implementation target: `0.1.0-alpha.18-exec-plan.md` slices S1–S9
- Accepted consequence: tension recordability waits for `query-architecture` (design §0 boundary case; §7 Q1 names the pull-forward option)

Status: proposed, not yet ratified.

## 2026-07-07 - Delete-and-fold, not rename-in-place, for the markdown `work` and `source-note` types

Y: The markdown `work` Concept type and `work.yaml` will be deleted (the catalog row
is the sole SSOT, taking the name `concept_type='work'`); `source-note` and
`source-note.yaml` will be deleted, folded into `note` as `mode: work`;
`person`/`organization`/`venue` will be dropped from `concept_type` entirely.

Because: owner-ratified (beta.1 design item 20). Verified against real code — no path
requires `works/<work_id>/record.md`, and a repo-wide grep found zero files using
`type: work` or `type: source-note`, so there is nothing deployed to convert. Part 8's
earlier `catalog-record`/`catalog-note` rename-in-place alternative is retired: the
migration-size concern that motivated it did not hold once the zero-deployment status
was confirmed.

Pointers:
- Evidence: `data-structure-analysis.md` Part 8 reconciliation note + Open Questions; beta.1 design item 20
- Implementation target: `0.1.0-alpha.18-exec-plan.md` S2 (concept-type + CHECK) and S3 (the `note.yaml` fold + `mode` collapse)

Status: proposed, not yet ratified.

## 2026-07-07 - `fulltext` (and `system`/`dashboard`/`eval-task`) are frontmatter `type:` labels, NOT `concepts.concept_type` CHECK values

Y: The new `fulltext` type will be a frontmatter `type:` value (with a
`.memoria/schemas/types/fulltext.yaml` schema for validation) that does **not** appear
in `concepts.concept_type`'s CHECK list and gets **no** `concepts` DB row — the same
posture as `system`/`template`/`eval-task`/`dashboard`. The `concepts.concept_type`
CHECK holds exactly ten DB-tracked values (`work`, `digest`, `note`, `hub`, `project`,
`capability`, `operation`, `skill`, `adapter`, `workflow`); `fulltext` is not one.

Because: analysis Part 1 §3.1 / Part 5 decouple OKF concept-document-hood (every `.md`
file except `index.md` has a `type:`) from Memoria's own internal Concept-hood
(whether something gets a `concepts` row / `check_status` / a DB `concept_type`).
`fulltext` is a mechanical reproduction — OKF-conformant via `type: fulltext`, but not
PI-authored checked content, so it needs no DB row. Adding it to the CHECK would either
force a spurious DB row or reject valid `fulltext` docs.

Pointers:
- Evidence: `data-structure-analysis.md` Part 1 §3.1 (item 7), Part 5 (`fulltext` field table + "Types deliberately out of this table's scope")
- Implementation target: `0.1.0-alpha.18-exec-plan.md` S4 (the `fulltext.yaml` schema; leave the CHECK at ten values)

Status: proposed, not yet ratified.

## 2026-07-07 - Add a `required_when` schema primitive (not a linter detector) for mode-conditional required fields

Y: `schema.py`'s field-kind grammar will gain a `required_when` primitive expressing
"field X is required when field Y has value Z" (`claim`→`claim_text`,
`question`→`question_status`, `work`→`work_id`), evaluated at frontmatter validation.

Because: mode-conditional-required is decidable from frontmatter alone, so it belongs
in the validator, not the linter (which is for checks needing the body too). The
existing dormant `required_any` primitive is disjunctive-across-fields and does not fit
this conditional-on-a-value shape.

Pointers:
- Evidence: `data-structure-analysis.md` Part 5 ("Conditional-required, resolved")
- Implementation target: `0.1.0-alpha.18-exec-plan.md` S3

Status: proposed, not yet ratified.

## 2026-07-07 - No migration function; edit `schema.sql` directly and delete `_migrate_v4_to_v5`

Y: alpha.18 will delete `_migrate_v4_to_v5`, edit `schema.sql` directly to its final
normalized shape, and bump `user_version`/`SCHEMA_VERSION` 6→7 — with **no**
`_migrate_v6_to_v7` and no compatibility shim. The only "migration" for a local dev
vault is delete-and-rebuild.

Because: nothing is deployed to migrate (zero real vaults; zero `type: work`/
`type: source-note` files). This matches both the analysis's G3 finding and the
project's own unbroken pre-1.0 precedent (no migration path since alpha.11; alpha.14
deleted a migration shim for the same reason). Per G3's "what to add now, cheaply,"
the written rule "a schema change to a table with real installed rows ships as a
numbered ALTER migration" is recorded so the ladder is built correctly when a real
vault first exists — not before.

Pointers:
- Evidence: `data-structure-analysis.md` Part 8 §migration (G3); alpha.11/14/17 precedent
- Implementation target: `0.1.0-alpha.18-exec-plan.md` S7

Status: proposed, not yet ratified.

## 2026-07-07 - Schema-doc drift prevention is a name-agnostic lint, not a doc generator

Y: The drift-prevention mechanism will be a CI lint that reads whatever the live
`.memoria/schemas/types/*.yaml` declares and fails if a field/enum claim in
`docs/reference/frontmatter.md`/`document-types.md` disagrees — driven off synthetic
fixtures for its own unit tests so it is independent of which names the repo currently
uses. Generating the docs *from* the schema is the richer alternative, deferred unless
the lint proves insufficient.

Because: a lint is the cheaper of the analysis's two options and would have caught both
drift incidents it found (alpha.10's `source_type` enum and `creation.form` block).
Making the lint name-agnostic (it validates alignment, not a fixed name set) lets it
land as a standing guard that is green on the pre-rename state and stays green as
S1–S8 rename schema and docs together.

Pointers:
- Evidence: `data-structure-analysis.md` Part 8 ("Preventing schema-documentation drift structurally")
- Implementation target: `0.1.0-alpha.18-exec-plan.md` S6

Status: proposed, not yet ratified.
