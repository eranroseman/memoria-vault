## alpha.18 - data-structure normalization

**Theme:** alpha.18 normalizes the released alpha.17 data structures without
building the deferred query engine. It fixes name collisions, removes redundant
markdown document types, makes the bundle roots explicit, adds the drift guard
that keeps schema docs honest, and bumps the runtime SQLite schema to
`user_version = 7`.

What drove it: the data-structure audit found that Memoria had several live
collisions and duplicate sources of truth: `source_id` versus Work identity,
`source_type` versus item classification, `journal_events` versus event logs,
markdown `work`/`source-note` types beside the SQLite catalog, and docs that
could drift from schema YAML. alpha.18 shipped those corrections through PRs
#1290, #1291, #1292, #1294, #1295, #1296, #1297, and #1299.

---

### 1. Scope boundary

- **What:** alpha.18 is normalization-only. It renames, deletes, and folds the
  existing schema/frontmatter/layout surface, but it does not add `passages`,
  `passages_fts`, `passages_vec`, `file_index_state`, `concept_edges`,
  embedding/reindex machinery, RRF, reranking, or grounded synthesis. **Why:**
  those are derived query caches plus the engine that consumes them, so they
  ship together in the later `query-architecture` release.

- **What:** tension recordability remains deferred with `concept_edges`. **Why:**
  pulling one edge value forward would create one-off machinery before the table
  and reindex loop that make the value useful.

### 2. Catalog and schema names

- **What:** Work identity is now `work_id` across catalog state, enrichment,
  provenance, aspects, and docs; `source_type` became `item_type`; the SQLite
  journal table became `event_log`; enrichment rows use `event_id`; publication
  venue edges use `published_in`. **Why:** each old spelling collided with a
  different domain sense of "source" or "journal", which made schema and docs
  ambiguous.

- **What:** `concepts.concept_type` now accepts exactly ten DB-tracked values:
  `work`, `digest`, `note`, `hub`, `project`, `capability`, `operation`,
  `skill`, `adapter`, and `workflow`. **Why:** `work` names the SQLite catalog
  mirror row, while `person`, `organization`, and `venue` were declared but had
  no writer or lifecycle as markdown Concepts.

### 3. Delete-and-fold document types

- **What:** The markdown `work` type and `work.yaml` were deleted. Catalog Works
  live in SQLite and source-derived artifacts live under `digests/` and
  `fulltext/`. **Why:** no deployed content used `type: work`, and the old
  markdown wrapper duplicated the catalog identity.

- **What:** `source-note` was deleted and folded into `note` as `mode: work`.
  `note.yaml` now has `required_when` rules for `claim_text`,
  `question_status`, and `work_id`. **Why:** source interpretation is a note
  mode, not a separate Concept type; conditional requirements are decidable from
  frontmatter and belong in the schema validator.

- **What:** Retired frontmatter fields such as `citations`, `evidence_set`,
  `citekey`, and `project` are rejected where the schema names them forbidden.
  **Why:** evidence sets live as body markers plus rebuildable SQLite rows, and
  bibliography/citation survival is checked against catalog state and
  `bibliography.bib`, not copied into every Concept.

### 4. Bundle roots and `fulltext`

- **What:** The file-backed bundle roots are `notes/`, `hubs/`, `projects/`,
  `digests/`, and `fulltext/`; templates, eval fixtures, operation preamble, and
  journal/runtime files live under `.memoria/`. **Why:** `works/` and `sources/`
  encoded the deleted document types, while the surviving roots are the actual
  user-visible file surfaces.

- **What:** `fulltext` is a frontmatter `type:` label with
  `.memoria/schemas/types/fulltext.yaml`; it is not a `concepts.concept_type`
  value and gets no Concept DB row. **Why:** generated full text is an OKF-like
  document for validation and retrieval, but it is not a PI-authored checked
  Concept.

### 5. Gap analysis and docs drift

- **What:** `analyze_gaps` now free-joins checked catalog rows through
  `work_graph_edges` for authorship, institution, and `published_in` venue
  signals. **Why:** the raw OpenAlex IDs already exist; a new entity table would
  be speculative until real deduplication or browsing needs appear.

- **What:** `scripts/checks/schema_doc_drift.py` compares the live schema YAML
  with the field/enum claims in `docs/reference/frontmatter.md` and
  `docs/reference/document-types.md`. **Why:** this is the cheap guard that
  catches stale schema docs without generating the docs from YAML yet.

### 6. Migration and release management

- **What:** `_migrate_v4_to_v5` was deleted, no `_migrate_v6_to_v7` was added,
  and `SCHEMA_VERSION`/`PRAGMA user_version` moved to 7. Legacy DB user
  versions now fail fast. **Why:** alpha.18 has no real installed vault rows to
  preserve; local dev vaults are rebuilt by deleting `.memoria/memoria.sqlite`
  and reinstalling/refreshing the workspace.

- **What:** The schema-change skill now records the future rule: once installed
  vaults may contain durable rows, every table-shape change to existing rows
  ships as a numbered `ALTER` migration unless a release decision explicitly
  records that no durable data must be preserved. **Why:** alpha.18 can still be
  delete-and-rebuild, but the first real vault cannot.

- **What:** The Python package version is bumped to `0.1.0a18`, but no formal
  tag or GitHub Release is cut. `release-please` remains `workflow_dispatch`
  only and was not dispatched for this checkpoint. **Why:** release-please is
  still paused for pre-alpha to avoid minting phantom releases; alpha.18 closes
  as a source-install checkpoint.

---

### Notable decisions and deferrals

| Decision / deferral | Disposition |
| --- | --- |
| Normalization/query split | Adopted; query substrate and engine defer to `query-architecture`. |
| `source_id` / `source_type` / journal naming collisions | Renamed to `work_id`, `item_type`, and event-log terminology. |
| Markdown `work` type | Deleted; catalog Work is SQLite state. |
| `source-note` type | Deleted; folded into `note` as `mode: work`. |
| `fulltext` | Added as a frontmatter schema label, not a DB Concept type. |
| `required_when` schema primitive | Adopted in the shared schema validator. |
| `analyze_gaps` entity handling | Free-join over existing graph edges; no entity table yet. |
| Schema-doc drift prevention | Adopted as a lint; generated docs remain deferred. |
| SQLite migration path | No alpha.18 migration function; delete-and-rebuild for local dev vaults. |
| Future real-row migrations | Numbered `ALTER` migration required once durable installed rows exist. |
| Formal release-please release | Not cut; workflow stays manual-only/pre-tag. |
