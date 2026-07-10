# DB schema analysis — 2026-07-09

Full read of `src/memoria_vault/runtime/schema.sql` (20 tables, 2 views,
8 triggers, `PRAGMA user_version = 8`), judged against the placement
doctrine, consistency model, axioms, and roadmap (`okf-note.md`,
`roadmap.md`).

## What the schema gets structurally right

- **The placement doctrine in relational form.** Verdicts live in a
  separate 1:1 table (`concept_verdicts`), not as a column on identity —
  judgment physically separated from existence. The `concept_status` view
  LEFT JOINs with `COALESCE(…, 'unchecked')`: **fail-closed by default at
  the view layer** — a concept with no verdict row is unchecked, never
  assumed good.
- **Axiom 1 as CHECK constraints.** Every status vocabulary is truth-free
  and closed: `{unchecked, checked, quarantined}` on five tables,
  materialization `{none, pending, materialized, failed}`, enrichment
  `{…, needs_human, contested}`. No column anywhere can hold a truth
  verdict.
- **The outbox/saga is real schema.** `outputs` (verdict + materialization
  + sha + `materialized_commit`) with `materialization_payloads` (FK,
  CASCADE) is the cross-substrate transaction coordinator; the
  `consumable_outputs` view is the trust-plane read gate in SQL.
- **The `catalog/sources/<work_id>` bridge is baked into the schema** —
  the verdict-cascade triggers translate the virtual namespace, so
  DB-space works and file-space concepts share one verdict propagation
  path. (Undocumented until `okf-note.md`; the schema had it all along.)
- **Evidence discipline everywhere:** `provider_payloads` is
  content-addressed with a uniqueness key per request; `field_provenance`
  records the winning provider *per metadata field* with alternatives —
  grounding-per-field, the axioms applied to bibliographic data;
  `code_runs` captures sanitized env, input/output hashes, and sandbox
  profile hash — the reproducible-run-as-grounds substrate is fully built
  at the schema level.
- **Two pleasant surprises for the roadmap:** `file_index_state`
  (mtime+sha per path) means the incremental-indexing substrate for the
  reactive substrate's Tier A already exists; and `concepts.concept_type`
  includes `'work'` with `store='db'` — the schema always anticipated
  works as first-class concepts, proving the un-listable catalog is
  purely an API-layer gap. `operation_requests.schedule_id` similarly
  pre-anticipates the scheduler.
- `passage_vec` carries per-row `embedding_model_id`/`vector_dim` —
  the real-embeddings upgrade (Tier 2) needs no schema change.

## Defects and gaps (ranked)

1. **The actor vocabulary fails in both directions at once.**
   `operation_requests.actor` is unconstrained TEXT with `DEFAULT 'pi'`
   (absence recorded as the human — the known T0 finding), while
   `derivations.actor` CHECK `('pi','operation','integrity')` *forbids*
   `'agent'`. One vocabulary, two tables, opposite failure modes. The T0
   migration should define one actor enum and apply the same CHECK to
   both — and drop the default.
2. **No reverse-traversal indexes for the central operation.** PKs cover
   source-side lookups only: `concept_edges(target_concept_id)` and
   `work_graph_edges(target_id/target_doi)` have no index, so
   "what supports X" / "who cites X" — the blast-radius direction — scans.
   Add target-side indexes before roadmap item 9 wires propagation.
   `event_log` likewise has no index on `event_type`/`timestamp`; journal
   queries scan at years scale (fold into T0 item 2).
3. **Constraint discipline is inconsistent at the edges.** Core
   vocabularies are CHECKed; rosters that matter are free text:
   `outputs.concept_type` (unlike `concepts`), `catalog_sources.item_type`
   (DEFAULT 'article', no CHECK — **item 20's closed source-type roster
   wants its enforcing line exactly here**),
   `field_provenance.confidence/conflict_status`,
   `external_ids.confidence`. Per the repo's own rule, an unchecked roster
   is a label.
4. **Identity fragmentation, no join spine.** Five identity vocabularies
   (`concept_id`, `output_id`, `work_id`, `passage_id`, raw `path`) with
   only three FKs in the whole schema; `derivations` and `outputs` key on
   paths. Deliberate looseness for rebuildable indexes is fine; for
   provenance tables it's the known ULID problem (roadmap item 6) —
   the migration's real work is giving the trust plane one stable key.
5. **`work_aspects` PK `(work_id, aspect_type)` forces one aspect per
   type per work** — one `key_idea`, one `limitation`. Real papers have
   several of each; texts must concatenate. Widen the PK (add an ordinal
   or aspect_id) when item 20's textual layers make aspects load-bearing.
6. **`concept_edges` cannot carry the six-role future as shaped**: PK
   `(source, relation, target)` with no edge_id and no attribute columns —
   nothing to hang a warrant reference or qualifier on; the `'tension'`
   relation exists in the CHECK but no write path can author it (known).
   This is the schema half of roadmap item 8, gated on item 6's migration
   machinery (`user_version` hard-fails on anything but 0/8; `CREATE TABLE
   IF NOT EXISTS` cannot alter existing tables).

## Fulltext v2 bonus finding

`'fulltext'` is **not** in the `concepts` type roster — fulltext files
were never DB concepts (they exist as `passages` with `origin='generated'`
plus outputs rows). Retiring `fulltexts/` as a bundle root therefore needs
no concept-type migration: the change is folders.yaml/CONCEPT_HOMES plus
outputs/index code — cheaper than the roadmap assumed.

## Verdict

The core is the placement doctrine and axiom 1 rendered in SQL — verdict
separation, fail-closed view defaults, closed status vocabularies, an
outbox with crash payloads, and per-field provenance that most metadata
systems never attempt. The defects cluster at the edges: one vocabulary
constrained inconsistently (actor — both T0-critical), missing
reverse-path indexes for the operation the product calls central, free
text where item 20 needs a roster, path-keyed provenance awaiting ULIDs,
and an edge table one migration away from the graph the statement
promises. Nothing here contradicts the roadmap; the schema findings
sharpen items 1, 2, 8, 9, and 20 with exact columns.
