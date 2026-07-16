# Graph substrate I · Nodes & identity — Design

Date: 2026-07-15. Status: **design (PI-approved in session), pre-plan**.
First half of Plan 22's G2S1.5 design gate — whose single-file deliverable
(`...graph-substrate-design.md`) is superseded by this two-spec split (PI
ruling). Companion: `2026-07-15-graph-edges-roles-propagation-design.md`.
Schema changes here ride G1's numbered-migration chain at **version 16+**
(Plan 22 reserves 16+ for graph-substrate work — G3 and the companion's
G2/G4/G5 migrations alike, serialized).

## 0. Shipped baseline (this spec does NOT re-decide)

A code audit at `80e62bbd` found the consolidation's S1/G3 markers stale.
Already shipped and test-enforced, ratified as-is: mode collapse 6→4
(`note.yaml:5`; the audit found zero old-mode writers or filters surviving
in search/index/CLI), fold-source-note, concept-type roster 15→10 (the DB CHECK
at `schema.sql:54-58` already matches the data-structure-analysis target
exactly), certainty-hypothesized, required-when grammar, item-type rename,
todo-field, delete-survival-copies, delete-dead-migration, and the entire
G3 rename map (`source_id`→`work_id`, `journal_events`→`event_log`,
`source_type`→`item_type`, `work_graph_edges.relation source`→
`published_in`) — all guarded by `tests/test_identifier_renames.py`.
Also ratified unchanged from the analysis: `work_id` stays a slug (never a
ULID); digests/fulltexts keep `work_id` itself as identity (`id: str`
exemption); entity types (`person`/`organization`/`venue`) stay dropped in
favor of free joins on already-captured raw ids.

## 1. Identity: full ULID re-keying (PI ruling)

**Ruling: option B — the database re-keys to frontmatter identity.**
Rationale of record: no production vault exists, so migration-cost-is-zero
has not expired — schema-before-corpus says the invasive re-key happens
now, cheap-while-empty, not later against 50k rows.

1. **`concept_id` = the frontmatter `id`, everywhere.** ULID for
   notes/hubs/projects (already required by `note.yaml:10`; extend the
   requirement to hub/project types); `work_id` for digests/fulltexts per
   the standing exemption. The key is "the id field" — uniform in
   mechanism, two forms. Every DB table that today keys concepts by
   vault-relative path (`concepts`, `concept_verdicts`, `concept_edges`
   endpoints, derivation rows, the `catalog/sources/ || work_id` triggers
   at `schema.sql:258,267,275`) re-keys; `path` becomes a unique,
   updatable attribute column.
2. **Filenames stay human kebab-slugs.** This explicitly **supersedes**
   the analysis' `<ulid>.md` filename decision
   (`data-structure-analysis.md:237-249,1448`), whose only purpose was
   path-as-identity — unnecessary once identity lives in frontmatter and
   the DB. U3's id-filenames rule (machine-created concepts get stable
   kebab-slugs) is unchanged.
3. **Markdown keeps wikilink paths.** `links:` targets remain
   Obsidian-native wikilinks (the seeded `.base` views depend on
   frontmatterLink backlinks). The indexer resolves path→id at reindex; a
   rename missed by any rewriter reconciles by frontmatter `id` match at
   the next index pass. Obsidian rewrites wikilinks on in-app renames;
   `memoria mv <old> <new>` covers CLI/editor renames — inbound `links:`
   rewrite + `path` column update in one trusted-writer transaction.
4. **Real foreign keys** land with the re-key: concepts ↔ verdicts ↔
   edges (and the catalog↔concepts join), enforced at schema v16+.
5. **No rename-tracking table.** Reconciliation-by-id makes tracking
   machinery unnecessary; `memoria mv` is a convenience, not a
   correctness requirement.
6. **Forward/dangling links are legal and modeled.** Linking a note that
   does not exist yet is normal Zettelkasten practice; the mirror keeps
   such edges as **pending rows** — `target_id NULL`, `target_path`
   retained — and resolves them to ids at the reindex where the target
   appears. FKs enforce only non-NULL id columns, so Plan 22 G2S1.1's
   mirror-dangling-edges acceptance behavior is preserved under v16.
   Unchecked-source visibility is the mirror row's existing
   `check_status` column (G2S1.1's edge-row contract); consumers filter
   on it — dispatching the links-mirror sub-items the consolidation
   lists.
7. **Catalog endpoints post-re-key:** edges and verdicts reference
   catalog works by bare `work_id` (their identity, per the standing
   exemption); `catalog/sources/<work_id>` remains only the virtual
   *path rendering* of that identity.
8. **`edge_id` and hung attributes survive the re-key.** The v16
   migration recomputes `edge_id = sha256(triple)` over the new id-space
   triple and rewrites every row's `edge_id` **and carries
   `attributes_json`** in the same transaction (a deterministic
   old-triple→new-triple mapping) — nothing hung on a promotion-ready
   edge dangles.

## 2. Concept-type roster: one seeded registry

`.memoria/schemas/concept-types.yaml` — the 10 values, each with a
one-line role description — becomes the single source of the roster:

- the schema validator reads it at runtime (replacing the hand-written
  acceptance set);
- the DB CHECK is derived from it when a migration regenerates
  `schema.sql`'s constraint, with a **parity test** asserting
  registry == CHECK on every run (the same drift-closure pattern the F1
  audit noted for the actor vocabulary);
- each of the six doc-type yamls must name a registry member
  (validated at load).

## 3. Close frontmatter validation (ratified)

The analysis' G1 decision, implemented as written: unknown frontmatter
fields become validation **rejections** (today `schema.py:168` documents
"unknown extra fields are accepted"); the `x:` escape hatch (already
seeded in every type yaml) stays; no grace period — no vault data exists.
The companion spec's consequence-mark fields (`stale: bool`,
`consequence:` enum — its §5) are registered as optional fields in the
type yamls as part of this closure, so the marks are valid under closed
validation from day one.

## 4. Residual hygiene

- Prune the dead `"work"` frontmatter-type literals in the five filter
  sets (`search_index.py:380`, `integrity.py:152,605,640`, `cli.py:1065`,
  `knowledge.py:1287`) — unreachable since the validator rejects unknown
  types.
- `integrity-citation-survival-check` keeps its operation id (operation
  ids are stable API); its doc line is corrected to describe the shipped
  vault-level `bibliography.bib` staleness check.

## 5. Hub Candidates block (S3's machine half)

The wiki↔ZK bridge, concrete: hub files gain a delimited terminal section

```markdown
## Candidates
%%candidates: run=<run_id>%%
- [[notes/x]] — co-cites 4 shared references with this hub's works
%%end-candidates%%
```

- `compile-source-digest` and the new deterministic `digest-related-works`
  (top-k by shared references / co-citation over `work_graph_edges` — no
  model judgment) **replace the section wholesale** each run; the curated
  body above the heading is never touched (the shipped
  never-overwrite-curated behavior at `operations.py:584-618` is the
  precursor).
- Every entry carries run attribution. Revert = delete the section (it
  regenerates). Accept = the PI moves a line into the body — a plain edit,
  observed as a PI edit.
- Machine-written region ⇒ neutralization applies (CS1 seam).

## 6. Out of scope

S2's pinned NLI model (rides E1 eval-harness promotion); entity-resolution
tables (free-join ruling stands); warrant-node reification (beta.2,
touch-budget-gated — the companion spec starts its usage clock);
suggestion/staleness tooling for hubs (post-beta, size-gated).

## 7. Acceptance criteria

A note rename (file move) leaves every DB row, edge, and verdict attached
(id-keyed) and reconciles the path column at next reindex; `memoria mv`
rewrites inbound wikilinks transactionally; the registry↔CHECK parity test
fails on any roster drift; unknown frontmatter keys are rejected while
`x:`-nested keys pass; a hub's curated body survives 100 candidate-block
regenerations byte-identical; FK violations are impossible to insert at
schema v16+.

## 8. Implementation slices (feeds the plan)

1. `concept-types.yaml` registry + validator rewire + parity test.
2. Close validation (+ fixture sweep).
3. The v16 migration: id-keyed tables + path attribute + FKs + pending
   (NULL-target) edge form + the `edge_id`/`attributes_json`
   recompute-and-carry (§1.8) — one migration, G1 chain; coordinate
   version numbers with Plan 22's contract 2.
4. Indexer path→id resolution + reconcile-by-id; `memoria mv`.
5. Hygiene prunes (§4).
6. Candidates block writer + `digest-related-works` + never-touch-body
   tests.
