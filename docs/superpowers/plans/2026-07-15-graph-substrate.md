# Graph Substrate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the two merged graph-substrate specs — the fresh ULID identity model, the seeded concept-type registry with closed validation, the single edge module with Toulmin activation, the catalog bridge and tension surface, and typed-consequence propagation with the decided-wrong flow.

**Architecture:** Fresh installs receive the identity-safe v16 schema directly, then the current v17 roster and v18 consequence DDL directly as those tasks land; existing databases are never re-keyed or upgraded. `edges.py` becomes the single owner of both relation rosters (v17 activates warrant/qualifier/rebuttal); a pure propagation engine walks the grounding closure ∪ derivation DAG and marks dependents with typed consequences as validated frontmatter + verdict rows (v18), loudness-routing cards. Specs of record: `docs/superpowers/specs/2026-07-15-graph-{nodes-identity,edges-roles-propagation}-design.md` (main @ 9c77ba61).

**Tech Stack:** Python 3 / SQLite / pytest; no new dependencies.

## Global Constraints

- Correctness gate: `python scripts/verify`; `main` needs PR + `verify`/`gitleaks`; squash merge; explicit-path staging only; disposable vaults only.
- **Executes AFTER Plan 22's current fresh schema with G2S1.1–.3 (+S12.2) lands** — this plan consumes `concept_edge_id`, upsert-and-prune sparing tension, and edge-id/attribute fields, but no migration mechanism. All line refs are main @ `9c77ba61` and WILL shift after Plan 22 — re-anchor by symbol, not line.
- **Fresh-schema allocation (binding):** v16 = NID-B identity-safe DDL · v17 = ERP-A roster CHECK · v18 = ERP-C consequence storage. Each schema task updates current `schema.sql`, its trailing `PRAGMA user_version`, `SCHEMA_VERSION`, and fresh-schema assertions in one commit. There is no `MIGRATIONS` entry, backfill, re-key, legacy fixture, or compatibility branch. A nonzero database at any other version is rejected before mutation.
  **Amended 2026-08-01:** the *ordering* is binding; the *integers* are not reserved
  across plans. With no `MIGRATIONS` registry and no upgrade path, a bump only declares
  incompatibility, so a rung is claimed by whichever schema task lands next — including
  tasks in other plans (the I1 plan's `telemetry_events` T.1 is the live case). Each
  schema task therefore reads `SCHEMA_VERSION` and takes `current + 1` rather than
  asserting a pre-agreed number. See Task ERP-C.3's amendment.

## Execution status — 2026-07-17

- **NID-A.1–A.3 complete:** the registry/loader/seed and golden coverage landed in
  `24a7a341`; DB-CHECK parity in `e734361c`/`e13200a8`; and the consequence fields in
  `86d50d4b`.
- **NID-A.4 partially complete:** canonical `links.contradicts` readers landed in
  `f7b25575`, with canonical target normalization repaired in `4161cd48`. The remaining
  closure flip and boundary tests remain; the alpha.15 importer is retired by the
  clean-slate Graph-R10 override below.
- The integrated Graph slice passed `python scripts/verify` (**2370 passed, 9 skipped**)
  and its sealed security diff scan reported no findings
  (`/tmp/codex-security-scans/memoria-vault/8d2c9eaf_20260717T163549Z/report.md`).

## Cross-section contracts (BINDING — manifest seam resolutions)

1. **Edge-table shape:** NID-B's v16 redefines `concept_edges` (adds `target_path`, target nullable ON DELETE SET NULL, PK `(source_concept_id, relation_type, target_path)`). ERP-A.2's v17 CREATE/INSERT column lists extend mechanically to this shape; ERP-B/C/D SQL is written against it.
2. **Roster ownership:** ERP-A resolves the Plan-22 handoff as MOVE — `parse_links`/`normalize_link_target` relocate to `edges.py`, `schema.py` re-exports for one release. New code imports from `lib.edges`; a repo-wide guard test forbids roster literals outside it.
3. **Consequence-engine symbols:** ERP-D consumes ERP-C's real names — `propagation.compute_consequences(vault, target_id, *, trigger) -> dict[str, dict]` for the report card and `propagate_consequences(..., trigger="decided-wrong")` for marks. ERP-D's assumed `derive_consequences`/`claim_work_edges` names are superseded: the structural-impact rewire reads the identity-safe `edges.concept_edge_path_records(vault, checked_only=False)` projection, whose `catalog/sources/*` targets are the ERP-B bridge at this boundary.
4. **Insert hooks, no circularity:** ERP-B.2 lands `insert_concept_edge` bare; ERP-C.5 retrofits the `propagate_edge_change(..., added=True)` call; ERP-D.6 retrofits `emit_edge_write_event(..., write_path="insert-concept-edge")`. ~~Final call order inside the function: insert → propagate → emit.~~ **Superseded as built (2026-08-02): both hooks hang on the callers, not inside `insert_concept_edge`.** ERP-C.5 put `propagate_edge_change` in `knowledge.curate_note_link`, and ERP-D.6 put its emission in `curate_note_link` and `integrity._confirm_tension_edge` — because `curate_note_link` *calls* `insert_concept_edge` to hang a warrant, so a hook inside the storage function counts one warranted curate twice, invisibly to a counter grouped by `relation_type` alone. `state.py` depends on neither `propagation` nor `operations`. See the ERP-D.6 amendment. **Its `target_path` key function is binding too** — `state._concept_edge_target_path`, never a bare `normalize_path`; see the NID-B.7 (2026-08-01) blockquote in the ERP-B.2 task section for why a second key function rolls back the whole mirror pass.
5. **Outcome→decision dict** (`integrity.py:1169`): ERP-B adds `"confirm-tension": "accept"`, ERP-D adds `"decided-wrong": "override"` — merge, never overwrite.
6. **Tension rows** store endpoints lexicographically sorted; ERP-C propagation and ERP-D counters must not assume direction.
7. **Consequence-mark fields** (`stale: bool`, `consequence:` enum) are registered in the type yamls by NID-A's closed-validation task; ERP-C writes them, never touches yamls.
8. **Floor-golden serialization:** NID-B.6, NID-C.2/.5/.6, ERP-D.1/.5 regenerate goldens — land sequentially, never in parallel worktrees, and not concurrently with other plans' golden tasks. **ERP-D.6 is off this list as built (2026-08-02):** `edge-write.v1` writes only the non-chained `telemetry_events` table, so it moved no golden and needs no serialization slot. **Outstanding (2026-08-02):** NID-C.6 landed its runtime change without the golden token, so one golden-moving edit it owns is still unapplied — the `compile-source-digest.md` manifest text plus the `regenerate-capability-index` golden. The next holder of this plan's token should clear it; the exact edit and expected one-line diff are in NID-C.6's 2026-08-02 execution amendment.
9. **Execution order:** NID-A → NID-B → ERP-A → ERP-B → ERP-C → ERP-D → NID-C (NID-C.1/.2 may run any time; its golden tasks obey contract 8).
10. **Catalog↔Concept FK (v16):** `catalog_sources.work_id` is the sole
    catalog↔Concept join and references `concepts.concept_id` immediately as the
    bare work identity, with `ON UPDATE RESTRICT ON DELETE RESTRICT`. Its parent
    `concepts.path` is exactly the virtual `catalog/sources/<work_id>` rendering.
    `catalog_sources.concept_path` remains a normalized, non-identity read-scope
    alias: an omitted value defaults to that virtual rendering, while a valid
    nonblank v15 alias is preserved. It never keys an FK, mirror, edge, or verdict.
    NID-B.1 creates/backfills the parent before rebuilding the child table and
    before normal catalog upserts; it never silently accepts an identity collision.
    There is no current catalog-source deletion path. A future explicit delete
    operation must delete the catalog child first, never cascade a Concept deletion
    into catalog authority.
11. **Public roster activation:** ERP-A.1–.5 are one public activation boundary.
   They may be developed and tested task-by-task, but no PR may merge after
   A.1/.2 alone: A.3 converges every reader, A.4 makes the PI write paths
   accept the same verbs, and A.5 updates the dependent U3 acceptance text.
   Until that PR lands, `views.attention` may advertise only relations that
   the HTTP `curate-note-link` request and its worker can complete. After it
   lands, the served roster is exactly `edges.LINK_RELATIONS` (six verbs) and
   still excludes `tension`. This prevents a dead-vocabulary window while
   preserving `LINK_RELATIONS` as the one source of truth.
12. **Warrant adapter and ordering:** ERP-D.5 has only ERP-A's activated
    roster and ERP-B.2's `insert_concept_edge` as graph prerequisites; it may
    run before ERP-C and ERP-D.1–.4/.6. It owns the backend wire
    `payload.warrant → attributes_json.warrant`. U3-PLUG.5/.8 require that
    task and emit `warrant`, never the legacy `reason` alias; the modal must
    distinguish a `warrant` relation (a license-note edge) from Warrant text
    (an annotation on the selected edge).
13. **Execution order:** NID-A → NID-B → ERP-A.1–.5 (one public activation)
    → ERP-A.6 (identity-safe path projection) → ERP-B.2 → ERP-D.5 → remaining
    ERP-B → ERP-C → remaining ERP-D → NID-C
    (NID-C.1/.2 may run any time; its golden tasks obey contract 8).
    **Early-run exception — ERP-D.3a (2026-08-01):** the stage-machine
    recalibration may run at any point after ERP-A.1–.5, ahead of ERP-B,
    ERP-C, and the rest of ERP-D. Its only graph prerequisite is that
    activated roster, which is merged; it owns no schema version, writes no
    journal event, and regenerates no golden, so it carries none of contract
    8's serialization. It must land before ERP-D.3, whose finding hygiene
    edits the same `no-support`/`no-refutation` family.

### Fresh-install schema amendment — direct DDL, no compatibility ladder (2026-07-30)

There are no existing installations. This amendment replaces every executable
`MIGRATIONS`, v15→v16 re-key/backfill, legacy-schema fixture, and compatibility
branch in NID-B, ERP-A, and ERP-C. The detailed migration text below is retained
as historical provenance only and must not be replayed.

1. **NID-B.1 emits the v16 identity-safe schema directly.** It defines the
   `concepts.path`, FK-backed verdict/edge/catalog shape, nullable edge target,
   `target_path` key, and current runtime writers for a new vault. It does not
   inspect or transform a v15 database, expose `_rekey_concept_identity`, or
   preserve a legacy path-keyed row. New file Concepts use their frontmatter ULID
   immediately; catalog work Concepts use the bare `work_id` immediately.
2. **ERP-A.2 emits the v17 roster directly and ERP-C.3 emits the v18 consequence
   field directly.** Each task edits current DDL and fresh-vault tests only. Tests
   must not set an old `user_version`, synthesize an old table, or assert a data
   upgrade. A prior nonzero schema version is rejected by startup before mutation.
3. **The direct schema still has a version identity.** Each of v16, v17, and v18
   updates `SCHEMA_VERSION`, the trailing schema `PRAGMA`, and the current-schema
   assertions in one commit. This is an incompatibility declaration, not an
   upgrade mechanism.
4. **Path projection remains live.** After NID-B, raw identity columns remain
   storage-only; path-facing consumers use the `edges` projection family below.

### Historical path-projection record (2026-07-29)

The remaining path-projection guidance supersedes old pre-v16 reader snippets.
Its migration and legacy-fixture references are historical only. After NID-B,
`source_concept_id` and `target_concept_id` are identity keys (a source may be
a ULID and a target may be `NULL`); no consumer outside identity/storage work
may treat either as a vault-relative path.

1. **ERP-A.2 preserves the complete v16 shape.** Its fresh-schema SQL, legacy
   v16 fixture, `MIGRATIONS[16]` CREATE, and INSERT column lists are exactly:

   ```sql
   edge_id TEXT NOT NULL DEFAULT '',
   source_concept_id TEXT NOT NULL
       REFERENCES concepts(concept_id) ON UPDATE CASCADE ON DELETE CASCADE,
   relation_type TEXT NOT NULL CHECK (
       relation_type IN (
           'supports', 'contradicts', 'extends', 'tension',
           'warrant', 'qualifier', 'rebuttal'
       )
   ),
   target_concept_id TEXT
       REFERENCES concepts(concept_id) ON UPDATE CASCADE ON DELETE SET NULL,
   target_path TEXT NOT NULL DEFAULT '',
   attributes_json TEXT NOT NULL DEFAULT '{}',
   check_status TEXT NOT NULL
       CHECK (check_status IN ('unchecked', 'checked', 'quarantined')),
   source_path TEXT NOT NULL DEFAULT '',
   updated_at TEXT NOT NULL,
   PRIMARY KEY (source_concept_id, relation_type, target_path)
   ```

   The migration copies `target_path` and preserves a pending row
   (`target_concept_id IS NULL`, nonempty `target_path`) as-is; it recreates
   `idx_concept_edges_edge_id` and `idx_concept_edges_target`.  Replace the
   obsolete `target_concept_id TEXT NOT NULL` / target-id primary-key snippets,
   including the corresponding test fixture and survivor query.  The migrated
   v16 test seeds both a ULID source and a pending target, then asserts their
   path/NULL form survives alongside the expanded roster.  “Adapt if v16
   changed” is not an implementation instruction and is superseded.

2. **ERP-A.6 — one graph-owned path-projection family.** Add this task after
   the atomic ERP-A.1–.5 activation and before any R2 G, ERP-C, or path-facing
   structural consumer.  It adds two public, identity-safe functions in
   `runtime/subsystems/lib/edges.py`:

   ```python
   def concept_edge_path_pairs(
       vault: Path, *, checked_only: bool = True
   ) -> list[dict[str, str]]:
       """Checked graph edges projected to durable vault paths."""


   def concept_edge_path_records(
       vault: Path, *, checked_only: bool = True
   ) -> list[dict[str, Any]]:
       """Projected paths plus parsed edge attributes for graph consumers."""
   ```

   `concept_edge_path_pairs` returns deterministic rows with exactly
   `source_path`, `target_path`, and `relation_type`; it is the strict
   three-field public endpoint API used by R2 and propagation.  Its sibling
   `concept_edge_path_records` returns those durable paths and relation plus
   one parsed `attributes: dict[str, Any]` field for graph-internal consumers
   that need `warrant` or `addressed`.  A malformed or non-object
   `attributes_json` becomes `{}`.  Neither function emits raw identity IDs or
   `edge_id`.  The storage query joins a source identity through
   `concepts.path`; it derives a resolved target from `target concepts.path`
   and otherwise retains `concept_edges.target_path`.  Keep the shared query in
   `edges` with a function-local `state` import (or in `state` with a local
   import from `edges` after module initialization) so ERP-A.2's `state →
   edges` roster import never creates a module-import cycle.  `checked_only=True`
   filters on the edge's checked status; `False` is used only by graph-internal
   consumers that deliberately include unchecked/pending topology.

   Add `tests/test_edges.py` coverage that rebuilds the concept mirror with a
   ULID-keyed source at `notes/source.md`, creates one resolved edge and one
   checked pending target with attributes, then asserts the strict public rows
   are paths (`notes/source.md`, resolved target path, and pending
   `target_path`) and never contain the ULID.  Assert the record rows preserve
   only the corresponding parsed attributes and likewise expose no identity.
   A second test proves unchecked rows are absent by default and included only
   with `checked_only=False`.

3. **All path-facing graph consumers use that projection family.** ERP-C.1's
   closure, ERP-C.5 trigger routing, ERP-C.6's active-project adjacency, and
   all R2 G/E graph walks consume the strict
   `edges.concept_edge_path_pairs`; ERP-D.3/D.4 consume
   `concept_edge_path_records` only because their documented `warrant` and
   `addressed` behaviors need attributes.  Raw identity values stay confined to
   state migrations, FK mutations, and identity-keyed lookup.  The propagation
   tests seed identity rows through `state.replace_concept_edges`, include a
   ULID source and a pending target, and assert that an active-project
   slice/card routing still operates on path members.  When a marked result is
   identity-keyed, resolve it through the same graph projection/mirror before
   comparing it with a path slice; never compare an ID directly with a path.

4. **Downstream dependency.** R2 G begins only after ERP-A.6.  Its former raw
   endpoint fixtures and the nonexistent `state.active_project_slices` seam are
   superseded by the task-level R2 amendment below; `propagation.active_project_slices`
   is the sole project-slice provider once ERP-C.6 lands.

5. **ERP-B.2/B.4 retain v16 identity safely.** ERP-B.2's public
   `insert_concept_edge` accepts path references at its boundary, but resolves
   the source through `state.resolve_concept_id(conn, source_path)`, keeps a
   normalized `target_path` as the durable target, and looks up the optional
   `target_concept_id` through `concepts.path`.  Its insert/upsert key is
   `(source_concept_id, relation_type, target_path)`; `edge_id` is populated
   only if the target resolves.  It never normalizes an already-resolved ULID
   as though it were a path.  ERP-B.4 deletes/retracts by that same triple,
   never by `target_concept_id`.  Replace their pre-v16 SQL bodies and tests
   with ULID-mirror fixtures proving a resolved row, a retained pending
   `target_path`, and an idempotent delete without an FK failure.

6. **ERP-D.4 consumes metadata-safe paths, not storage IDs.** Its
   `substrate_edges` graph loop consumes
   `edges.concept_edge_path_records(vault, checked_only=False)`, including its
   `catalog/sources/*` bridge targets; it feeds only returned paths into
   `_edge_key`/the note resolver and reads `record["attributes"].get("addressed",
   True)` for the existing addressed filter.  A resolved ULID-source edge
   appears with its current path.  A pending target is retained by the
   projection but is skipped from the structural graph if no target note
   exists—never rendered as a fake ULID node or allowed to crash the resolver.
   Update D.4 fixtures to rebuild a ULID mirror, prove both resolved and pending
   cases, and remove every direct `state.concept_edges` endpoint normalization
   from that task.

7. **ERP-D.3 compares component paths only.** Its guarded warrant-absence
   helper consumes `concept_edge_path_records(vault, checked_only=False)`,
   compares the path-valued `component` solely with each record's
   `source_path`/`target_path`, and interprets warrant text only from
   `record["attributes"]`.  Its fixtures rebuild a ULID-keyed mirror and seed
   a resolved and a pending edge through the v16 trusted seam, proving that a
   component-local warrant suppresses the finding while an elsewhere warrant
   only supplies the vault-wide denominator.  The historical raw
   `source_concept_id`/`target_concept_id` comparisons are invalid after v16.

8. **ERP-D.5 tests the v16 writer boundary, not a path hash.** Its fixture
   rebuilds ULID-keyed source and target mirror rows before `curate_note_link`.
   It never calls `state.concept_edge_id` with paths or filters stored rows by
   raw endpoint IDs.  Instead it asserts that the upsert result returns a
   nonempty, stable `edge_id`, then finds one matching
   `concept_edge_path_records` row by `source_path`, `relation_type`, and
   `target_path` and asserts its `attributes["warrant"]`.  The second upsert
   keeps the returned `edge_id` stable and updates that projected attribute.

## PI ratification record (2026-07-30 — binding)

These are recorded PI **Y** decisions, not drafter rulings awaiting a future
merge. `Graph-` keeps this decision namespace distinct from the grounds
contract's unrelated R1–R4 labels. The R1–R8 wording below is the plan's
verbatim ruling text.

- **Graph-R1 — Y (2026-07-30; NID-B):** digests/fulltexts stay **path-keyed** (paths are pure functions of `work_id`) rather than bare-`work_id`-keyed — avoids PK collision with catalog works in the shared concepts namespace. Deviation from NODES §1.1's letter, preserving its intent.
- **Graph-R2 — Y (2026-07-30; NID-B):** file deletion keeps **tombstones** for verdict-carrying rows (prune only verdict-less; inbound edges revert to pending via ON DELETE SET NULL).
- **Graph-R3 — Y (2026-07-30; ERP-C):** `contradicts`/`tension` hops neither mark nor traverse (no consequence type exists for them by spec).
- **Graph-R4 — Y (2026-07-30; ERP-C):** new-relation edge direction = source is the license/bounding/exception note, target is the claim (mirrors `supports`).
- **Graph-R5 — Y (2026-07-30; ERP-C):** standing triggers fire only on transitions into {retracted, superseded}; archived is shelving.
- **Graph-R6 — Y (2026-07-30; ERP-C):** "active project's slice" = non-archived project note + thesis target + undirected edge reachability.
- **Graph-R7 — Y (2026-07-30; ERP-A):** structural-impact traversal widens to all six LINK_RELATIONS at roster convergence (not deferred to the §8 rewire).
- **Graph-R8 — Y (2026-07-30; ERP-B):** tension retraction verb = `state.delete_concept_edge` (no tombstone; existence-based semantics per spec); per-candidate tension prompt cards added as the minimal enabling surface.
- **Graph-R9 — Y (2026-07-30; NID-B / contract 10):** `catalog_sources.work_id` is the sole catalog↔Concept join, references `concepts.concept_id` as the bare work identity with `ON UPDATE RESTRICT ON DELETE RESTRICT`, and never uses `concept_path` as an FK, mirror, edge, or verdict identity. The parent must exist before the child is rebuilt or upserted; an identity collision fails rather than being accepted.
- **Graph-R10 — superseded by the clean-slate ruling (2026-07-30):** there are no
  existing installations. Remove the alpha.15 importer and `memoria migrate
  --from-alpha15` CLI path; do not normalize, copy through, preserve `x.alpha15`,
  or otherwise implement compatibility for legacy documents. A legacy workspace is
  outside the supported fresh-install contract and is not mutated by Memoria.
- **Graph-R11 — Y (2026-08-01; ERP-D): stage-role classification for the argument lens.**
  support = `{supports}`; challenge = `{contradicts, rebuttal, tension}`; structure =
  `{warrant, qualifier, extends}`. `argument_stage` is never `supported` without at
  least one `supports` edge; any challenge edge in the component stages `contested`;
  rebuttal-heavy projects get no new stage name. `mature_graph` remains connectivity
  (≥3), with `has_support`/`has_refutation` carrying the sides; `has_refutation` and
  displayed confidence read the challenge roster. **Qualifier is structure, not
  challenge** — spec §4 defines it as bounding scope/strength, and ERP-C's
  qualifier-regression semantics depend on that reading. Implemented by Task
  ERP-D.3a (closes #1624).

---
# Section NID-A — Concept-type registry + closed frontmatter validation

Implements NODES spec §2 (one seeded registry) and §3 (closed validation), plus the
EDGES spec §5 consequence-mark field registration that §3 explicitly folds in.
Repo: `/home/eranr/memoria-vault`, main @ 9c77ba61.

SPEC GAP: NODES §2 says "each of the six doc-type yamls must name a registry member
(validated at load)" but does not say WHICH member the two off-roster doc types map to
(`fulltext` and `code-artifact` are frontmatter types with no entry in the 10-value DB
roster — pinned by `tests/test_bundle_roots.py:45` `test_fulltext_is_not_a_db_concept_type`).
This section maps `fulltext → work` (grounded in shipped behavior: `runtime/indexing.py:112-151`
already resolves `fulltexts/<work_id>.md` passages to the catalog work concept
`catalog/sources/<work_id>`, and NODES §1.7 makes bare `work_id` the work's identity) and
`code-artifact → project` (the record lives inside the project bundle at
`projects/<slug>/code/<artifact>.md` per `runtime/code/records.py:31` and is DB-tracked in
`code_artifacts`, never as its own concepts row). PI may override either mapping; nothing
in this section's code depends on the specific choice — only on membership.

SPEC GAP: neither spec says whether the concept-mirror writers
(`trusted_writer.rebuild_concept_mirror_from_files` at `trusted_writer.py:608-629`, which
today inserts the raw frontmatter `type` and would violate the CHECK for a
fulltext/code-artifact file) are rewired to the new mapping in this slice or in the
identity re-key. This section does NOT rewire them (NODES §8 slice 1 is
"registry + validator rewire + parity test" only); NID-B's v16 re-key task must consume
`schema.concept_type_for(...)` when it rebuilds the mirror — recorded under
"constraints other sections must honor" in the manifest.

## Consumes (cross-plan)

Nothing from Plan 22 — this section touches no DB DDL and no `MIGRATIONS` entry. It
allocates none of this plan's schema versions (v16/v17/v18 remain for NID-B / ERP-A /
ERP-C). The parity test (NID-A.2) reads the shipped `schema.sql` text as-is at whatever
version is current when it runs (v12 today; v13-15 land in Plan 22 without touching the
`concepts.concept_type` CHECK).

## Ground rules for every task below

- Gate: `python scripts/verify` must pass before each PR; per-task loops use
  `python -m pytest tests/<file>.py::<test> -v`.
- Tasks A.1 and A.3 edit files under
  `src/memoria_vault/product/workspace_seed/.memoria/schemas/` — the seeded vault
  changes, so the floor goldens (`tests/fixtures/floor/goldens/*.json`, which hash every
  seeded-vault file per `tests/floor_lib.py:301-306,328`) drift and must be regenerated
  in the same commit:
  `MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest tests/test_floor_sweep_operations.py tests/test_floor_coverage.py -q`
  (refused in CI by design, `floor_lib.py:345`).
- Test vaults: disposable `tmp_path` vaults only.

### Binding clean-slate override — vault-local explicit concept registry (2026-07-30)

There are no pre-registry vaults to recover. This override supersedes the
NID-A.1 fallback and implicit-mapping snippets below; those snippets remain
historical drafting record only and must not be implemented or copied.

1. **One required local source.** Every supported fresh vault contains
   `.memoria/schemas/concept-types.yaml`. When a vault schema directory is
   supplied, `load_concept_types(schemas_dir)` reads exactly that file and
   raises a clear `ValueError` if it is missing and otherwise fails closed on
   malformed content. It must never
   fall back to `SCHEMAS_DIR`, a packaged seed copy, or a hard-coded roster.
   The no-argument product-resource read is allowed only for packaging/seed
   construction, never as runtime recovery for a vault.
2. **No inferred `concept_type`.** Every `types/<type>.yaml` explicitly names
   one nonblank `concept_type` that is a member of that same local registry.
   Missing, blank, or unknown values fail `load_types`; document `type` does
   not imply, default, or otherwise synthesize a Concept type. Mirror writers
   use the validated explicit mapping and reject an invalid contract before
   mutation.
3. **Required proofs.** NID-A.1 tests a missing local registry, a missing
   `concept_type`, a blank `concept_type`, and an unknown member as failures.
   Delete the historical `test_vault_schemas_dir_without_registry_falls_back_to_packaged_roster`
   and do not retain an equivalent recovery test. The runtime linter and
   pre-commit checker load a vault's local contract and fail closed when that
   directory or registry is absent; neither substitutes package schemas.

---

### Task NID-A.1: Seed `concept-types.yaml` registry + validator rewire + load-time membership check

**Files:**
- Create: `src/memoria_vault/product/workspace_seed/.memoria/schemas/concept-types.yaml`
- Modify: `src/memoria_vault/runtime/subsystems/lib/schema.py` (module docstring :2-14;
  `load_types` :50-56)
- Modify: all six `src/memoria_vault/product/workspace_seed/.memoria/schemas/types/*.yaml`
  (add one `concept_type:` line each, after the `category:` line — note.yaml:2,
  hub.yaml:2, project.yaml:2, digest.yaml:2, fulltext.yaml `category: fulltext` line,
  code-artifact.yaml `category: projects` line)
- Modify: `tests/test_schemas.py` (new tests; imports at :3-8)
- Modify: `tests/fixtures/floor/goldens/*.json` (regenerated — seed changed)

**Interfaces:**
- Consumes: `schema._schemas_dir(schemas_dir: Path | None) -> Path` (:46-47),
  `schema.SCHEMAS_DIR` (:35), `yaml.safe_load`.
- Produces:
  - `schema.load_concept_types(schemas_dir: Path | None = None) -> dict[str, str]` —
    `{concept type: one-line role}`, read from `<schemas_dir>/concept-types.yaml`,
    falling back to the packaged seed registry when a vault-local schemas dir predates
    the file (same pragmatism as `precommit_check.py:27-28`'s dir fallback).
  - `schema.load_types(schemas_dir: Path | None = None) -> dict[str, dict]` — unchanged
    signature; now raises `ValueError` at load when any `types/<type>.yaml` carries a
    `concept_type` that is not a registry member (or omits it).
  - Seed registry file shape: top-level `concept_types:` map of the 10 roster values →
    one-line role strings.
  - Doc-type → registry mapping (data): note→note, hub→hub, project→project,
    digest→digest, fulltext→work, code-artifact→project.

**Steps:**

- [x] Write the failing tests. Append to `tests/test_schemas.py` (file already imports
  `shutil`, `yaml`, and `schema`; add `import pytest` after the `import shutil` line at :3):

  ```python
  def test_concept_type_registry_is_seeded_and_every_doc_type_names_a_member():
      registry = schema.load_concept_types()
      assert set(registry) == {
          "work",
          "digest",
          "note",
          "hub",
          "project",
          "capability",
          "operation",
          "skill",
          "adapter",
          "workflow",
      }
      assert all(str(role).strip() for role in registry.values())
      for name, type_schema in schema.load_types().items():
          assert type_schema.get("concept_type") in registry, name


  def test_load_types_rejects_doc_type_outside_registry(tmp_path):
      shutil.copytree(schema.SCHEMAS_DIR, tmp_path / "schemas")
      rogue = tmp_path / "schemas/types/note.yaml"
      data = yaml.safe_load(rogue.read_text(encoding="utf-8"))
      data["concept_type"] = "gizmo"
      rogue.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
      with pytest.raises(ValueError, match="not in concept-types.yaml"):
          schema.load_types(tmp_path / "schemas")


  def test_vault_schemas_dir_without_registry_falls_back_to_packaged_roster(tmp_path):
      shutil.copytree(schema.SCHEMAS_DIR, tmp_path / "schemas")
      (tmp_path / "schemas/concept-types.yaml").unlink()
      assert set(schema.load_concept_types(tmp_path / "schemas")) == set(
          schema.load_concept_types()
      )
  ```

- [x] Run to verify failure:
  `python -m pytest tests/test_schemas.py::test_concept_type_registry_is_seeded_and_every_doc_type_names_a_member -v`
  — expected: `AttributeError: module ... has no attribute 'load_concept_types'`.

- [x] Create the seed registry
  `src/memoria_vault/product/workspace_seed/.memoria/schemas/concept-types.yaml`:

  ```yaml
  # The single source of the DB Concept-type roster (concepts.concept_type CHECK).
  # Read at runtime by the schema loader; tests/test_concept_type_registry.py holds
  # registry == CHECK parity. Each types/<type>.yaml names one member (concept_type:).
  concept_types:
    work: Catalog work record — the db-store row for one catalogued source.
    digest: Per-work machine digest Concept (file-store, digests/).
    note: Atomic claim/question/definition/work note (file-store, notes/).
    hub: Topic hub carrying human salience (file-store, hubs/).
    project: Output-driving project Concept (file-store, projects/).
    capability: Registered capability (db-store registry row).
    operation: Registered operation (db-store registry row).
    skill: Registered skill (db-store registry row).
    adapter: Registered external adapter (db-store registry row).
    workflow: Registered workflow (db-store registry row).
  ```

- [x] Add the mapping line to each of the six type yamls, directly after `category:`:
  - `types/note.yaml` (after :2 `category: notes`): `concept_type: note`
  - `types/hub.yaml` (after :2): `concept_type: hub`
  - `types/project.yaml` (after :2): `concept_type: project`
  - `types/digest.yaml` (after :2): `concept_type: digest`
  - `types/fulltext.yaml` (after `category: fulltext`): `concept_type: work`
  - `types/code-artifact.yaml` (after `category: projects`): `concept_type: project`

- [x] Rewire the loader in `src/memoria_vault/runtime/subsystems/lib/schema.py`.
  Insert after `load_types` (below :56), and replace `load_types`' body:

  ```python
  def load_concept_types(schemas_dir: Path | None = None) -> dict[str, str]:
      """Return {concept type: one-line role} from the seeded registry.

      concept-types.yaml is the single source of the DB Concept-type roster;
      the schema.sql CHECK is held to it by the registry parity test. A
      vault-local schemas dir that predates the registry falls back to the
      packaged seed copy.
      """
      registry_file = _schemas_dir(schemas_dir) / "concept-types.yaml"
      if not registry_file.is_file():
          registry_file = SCHEMAS_DIR / "concept-types.yaml"
      data = yaml.safe_load(registry_file.read_text(encoding="utf-8"))
      return {str(name): str(role) for name, role in data["concept_types"].items()}
  ```

  ```python
  def load_types(schemas_dir: Path | None = None) -> dict[str, dict]:
      """Return {document type: schema dict} for every types/<type>.yaml.

      Raises ValueError when a doc-type yaml names no concept-type registry
      member in its concept_type key (the NODES §2 load-time check).
      """
      registry = load_concept_types(schemas_dir)
      out: dict[str, dict] = {}
      for f in sorted((_schemas_dir(schemas_dir) / "types").glob("*.yaml")):
          data = yaml.safe_load(f.read_text(encoding="utf-8"))
          member = data.get("concept_type")
          if member not in registry:
              raise ValueError(
                  f"{f.name}: concept_type {member!r} is not in concept-types.yaml "
                  f"{sorted(registry)}"
              )
          out[data["type"]] = data
      return out
  ```

  Also extend the module docstring (:4-6) sentence listing schema files to mention
  `concept-types.yaml` (the roster) alongside `types/<type>.yaml` and `folders.yaml`.

- [x] Run to verify pass:
  `python -m pytest tests/test_schemas.py -v` — all pass (the three new tests plus the
  existing file; `test_concept_types_load` still passes because the six doc types are
  unchanged).

- [x] Regenerate floor goldens (seed changed):
  `MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest tests/test_floor_sweep_operations.py tests/test_floor_coverage.py -q`
  then review the drift is hash-only churn under `.memoria/schemas/` with `git diff --stat tests/fixtures/floor/goldens`.

- [x] Run the gate: `python scripts/verify` (the schema-doc drift check
  `scripts/checks/schema_doc_drift.py` is subset-direction per `_map_section_errors`
  :139-145, so the new `concept_type:` key in live yamls does not trip the docs).

- [x] Commit:

  ```
  git add src/memoria_vault/product/workspace_seed/.memoria/schemas/concept-types.yaml \
          src/memoria_vault/product/workspace_seed/.memoria/schemas/types/note.yaml \
          src/memoria_vault/product/workspace_seed/.memoria/schemas/types/hub.yaml \
          src/memoria_vault/product/workspace_seed/.memoria/schemas/types/project.yaml \
          src/memoria_vault/product/workspace_seed/.memoria/schemas/types/digest.yaml \
          src/memoria_vault/product/workspace_seed/.memoria/schemas/types/fulltext.yaml \
          src/memoria_vault/product/workspace_seed/.memoria/schemas/types/code-artifact.yaml \
          src/memoria_vault/runtime/subsystems/lib/schema.py \
          tests/test_schemas.py \
          tests/fixtures/floor/goldens
  git commit -m "feat(schema): seed concept-types.yaml registry; doc-type yamls name a registry member, checked at load (NODES §2)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task NID-A.2: Registry ↔ DB CHECK parity test

**Files:**
- Create: `tests/test_concept_type_registry.py`
- Modify: `tests/conftest.py` (`TEST_LEVELS` dict :18-…; insert alphabetically near
  `"test_schemas.py": "contract"` at :102 — nearest sibling level is `contract`)

**Interfaces:**
- Consumes: `schema.load_concept_types()` (NID-A.1);
  `importlib.resources.files("memoria_vault.runtime").joinpath("schema.sql")` (the load
  path `state.py:484-485` uses); the `concepts.concept_type` CHECK at `schema.sql:53-57`.
- Produces: `tests/test_concept_type_registry.py::test_registry_matches_db_check` — the
  drift-closure gate NODES §2 and §7 require ("fails on any roster drift"). No runtime
  interface.

**Steps:**

- [x] Write the test file `tests/test_concept_type_registry.py`:

  ```python
  """Drift closure: concept-types.yaml is the single source of the DB Concept roster.

  NODES spec §2 — the schema.sql CHECK must match the seeded registry exactly, the
  same pattern the F1 audit demanded for the actor vocabulary. Any migration that
  edits the concepts.concept_type CHECK must edit concept-types.yaml in the same
  commit, and vice versa.
  """

  from __future__ import annotations

  import re
  from importlib.resources import files

  from memoria_vault.runtime.subsystems.lib import schema


  def _check_roster() -> set[str]:
      sql = files("memoria_vault.runtime").joinpath("schema.sql").read_text(encoding="utf-8")
      match = re.search(r"concept_type TEXT NOT NULL\s*CHECK \(concept_type IN \(([^)]*)\)", sql)
      assert match, "concepts.concept_type CHECK not found in schema.sql"
      values = set(re.findall(r"'([a-z-]+)'", match.group(1)))
      assert values, "concepts.concept_type CHECK parsed empty"
      return values


  def test_registry_matches_db_check():
      registry = set(schema.load_concept_types())
      assert len(registry) == 10
      assert registry == _check_roster()
  ```

  (The regex is anchored on `concept_type TEXT NOT NULL` followed by `CHECK` — the only
  other `concept_type` column, `outputs.concept_type` at `schema.sql:82`, has no CHECK,
  so the first-match search cannot mis-bind.)

- [x] Register the file's level in `tests/conftest.py` `TEST_LEVELS`:
  `"test_concept_type_registry.py": "contract",` (alphabetical position, near
  `"test_capabilities.py"` :23).

- [x] Run: `python -m pytest tests/test_concept_type_registry.py -v` — expected: PASS
  immediately (the shipped v12 CHECK already equals the 10-value roster; this task adds
  the gate, not a behavior change). Sanity-check the parser really extracted the CHECK by
  running once with the `len(registry) == 10` assertion — a regex under-match fails there.

- [x] Commit:

  ```
  git add tests/test_concept_type_registry.py tests/conftest.py
  git commit -m "test(schema): registry == concepts.concept_type CHECK parity gate (NODES §2 drift closure)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task NID-A.3: Register the EDGES consequence-mark fields on note/hub/project/digest

Registers `stale: bool` + `consequence:` (enum of the four typed consequences, EDGES §5)
as optional fields so ERP-C's trusted-writer mark writes validate under the closed
validation NID-A.4 flips on. Done BEFORE the closure flip so every commit stays green in
either order of later consumers.

**Files:**
- Modify: `src/memoria_vault/product/workspace_seed/.memoria/schemas/types/note.yaml`
  (enums block :3-7, optional block :14-35)
- Modify: `src/memoria_vault/product/workspace_seed/.memoria/schemas/types/hub.yaml`
  (no enums block today; optional :10-16)
- Modify: `src/memoria_vault/product/workspace_seed/.memoria/schemas/types/project.yaml`
  (no enums block today; optional :9-18)
- Modify: `src/memoria_vault/product/workspace_seed/.memoria/schemas/types/digest.yaml`
  (no enums block today; optional :10-15)
- Modify: `tests/test_schemas.py`
- Modify: `tests/fixtures/floor/goldens/*.json` (regenerated — seed changed)

**Interfaces:**
- Consumes: `schema.validate_frontmatter` enum machinery (`_check_kind` `enum:` branch
  :104-107; `enums` lookup :171).
- Produces (data contract for ERP-C and the surfaces plan's R1NG.1 glyph column):
  - optional `stale: bool` and `consequence: enum:consequence` on the four KB doc types
    note/hub/project/digest;
  - `enums.consequence: [grounds-lost, warrant-lost, qualifier-regression, rebuttal-strengthened]`
    (exact strings and order — ERP-C must write these values verbatim).

**Steps:**

- [x] Write the failing test. Append to `tests/test_schemas.py`:

  ```python
  def test_consequence_mark_fields_registered_on_kb_doc_types():
      types = schema.load_types()
      enum = ["grounds-lost", "warrant-lost", "qualifier-regression", "rebuttal-strengthened"]
      for name in ("note", "hub", "project", "digest"):
          type_schema = types[name]
          optional = type_schema.get("optional") or {}
          assert optional.get("stale") == "bool", name
          assert optional.get("consequence") == "enum:consequence", name
          assert type_schema.get("enums", {}).get("consequence") == enum, name
      marked = {
          "id": "01KBN6V6KX0000000000000001",
          "type": "note",
          "title": "T",
          "tags": [],
          "links": {},
          "stale": True,
          "consequence": "grounds-lost",
      }
      assert schema.validate_frontmatter(marked, types["note"]) == []
      bad = schema.validate_frontmatter(dict(marked, consequence="vibes"), types["note"])
      assert any("not in enum consequence" in error for error in bad)
      bad_stale = schema.validate_frontmatter(dict(marked, stale="yes"), types["note"])
      assert any("stale: expected bool" in error for error in bad_stale)
  ```

- [x] Run to verify failure:
  `python -m pytest tests/test_schemas.py::test_consequence_mark_fields_registered_on_kb_doc_types -v`
  — expected: `AssertionError: note` on the `optional.get("stale")` line.

- [x] Edit the four yamls (exact additions; keep existing key order):
  - `note.yaml` — append to the `enums:` block (after :7 `item_type:` line):
    `  consequence: [grounds-lost, warrant-lost, qualifier-regression, rebuttal-strengthened]`
    and add to `optional:` (after :17 `archived: bool`): `  consequence: enum:consequence`
    and (after :31 `superseded: bool`): `  stale: bool`
  - `hub.yaml` — insert a new block after :2 `category: hubs` (and the NID-A.1
    `concept_type: hub` line):
    ```yaml
    enums:
      consequence: [grounds-lost, warrant-lost, qualifier-regression, rebuttal-strengthened]
    ```
    and add to `optional:` (after `archived: bool` :12): `  consequence: enum:consequence`,
    (after `salience: str` :14): `  stale: bool`
  - `project.yaml` — same new `enums:` block after `category: projects`/`concept_type:`;
    add to `optional:` (after `archived: bool` :11): `  consequence: enum:consequence`,
    (after `question: str` :16): `  stale: bool`
  - `digest.yaml` — same new `enums:` block after `category: digests`/`concept_type:`;
    add to `optional:` (after `archived: bool` :12): `  consequence: enum:consequence`,
    (after `description: str` :13): `  stale: bool`

- [x] Run to verify pass:
  `python -m pytest tests/test_schemas.py -v` — all pass
  (`test_frontmatter_has_no_verdict_or_standing_fields` :92-98 is unaffected — `stale`
  is a consequence mark, not a verdict field; `check_status`/`standing` stay banned).

- [x] Regenerate floor goldens (seed changed):
  `MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest tests/test_floor_sweep_operations.py tests/test_floor_coverage.py -q`

- [x] Run the gate: `python scripts/verify` (docs yaml examples are checked
  subset-direction, so new live optional fields cannot trip
  `scripts/checks/schema_doc_drift.py`).

- [x] Commit:

  ```
  git add src/memoria_vault/product/workspace_seed/.memoria/schemas/types/note.yaml \
          src/memoria_vault/product/workspace_seed/.memoria/schemas/types/hub.yaml \
          src/memoria_vault/product/workspace_seed/.memoria/schemas/types/project.yaml \
          src/memoria_vault/product/workspace_seed/.memoria/schemas/types/digest.yaml \
          tests/test_schemas.py \
          tests/fixtures/floor/goldens
  git commit -m "feat(schema): register stale/consequence mark fields on note/hub/project/digest (EDGES §5 substrate)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task NID-A.4: Close frontmatter validation (unknown fields rejected, `x:` hatch preserved)

**Files:**
- Modify: `src/memoria_vault/runtime/subsystems/lib/schema.py`
  (`validate_frontmatter` :161-209 — docstring open-acceptance sentence :166-168;
  insert the rejection loop after the `forbidden` loop :172-174)
- Modify: `tests/test_schemas.py`
  (flip `test_schema_accepts_undeclared_meaning_fields_during_root_layout_migration` :160-171)
- Modify: `docs/reference/data-model/frontmatter.md`
  (prose :41-43 currently documents the open behavior — "Unknown extra fields are
  accepted during the alpha migration")
- Modify: `src/memoria_vault/runtime/seeded_errors.py`,
  `src/memoria_vault/runtime/integrity.py`,
  `src/memoria_vault/runtime/knowledge.py`, and
  `src/memoria_vault/runtime/search_index.py` — migrate the legacy root
  `contradictions` shape to the canonical `links.contradicts` relation.
- Modify: `tests/test_integrity.py`, `tests/test_worker_integrity_jobs.py`,
  `tests/test_exploration_channel.py`, `tests/test_search_index.py`,
  `tests/test_trusted_writer.py`, `tests/test_precommit_schema.py`, and
  `tests/test_detectors.py` as the closure-boundary sweep requires.
- Do not add or retain an alpha.15 importer or any `memoria migrate` CLI path.
  If remnants exist, delete their code and tests as part of the clean-slate sweep.

**Interfaces:**
- Consumes: `schema.validate_frontmatter(fm, schema, vocabulary_terms=None) -> list[str]`
  (signature unchanged) and its callers — `validate_memoria_workspace` (schema.py:289),
  `trusted_writer._validate_concept` (trusted_writer.py:1031), the linter detectors, and
  the pre-commit check.
- Produces: closed validation — new error string shape
  `"<field>: unknown field; declare it in the type schema or nest under x:"`.
  `x: map` (already optional in every type yaml) remains the extension hatch; its nested
  keys are never inspected.

**Preflight closure determinations:**

- **Canonical contradiction relation — no additional PI choice.** Root
  `contradictions` is not a field in any type schema. Authored contradiction targets
  are exclusively `links.contradicts`; the seeded-error writer and all readers use
  that relation, with **no root-field fallback**. The public answer payload may
  retain its existing `contradictions` key. The digest-only contradiction checker
  owns this relation so generic link-target checking skips only a digest's
  `links.contradicts`; non-digest relations remain generically checked.
- **Clean-slate override — alpha.15 importer (supersedes Graph-R10).** Delete the
  `memoria migrate --from-alpha15` path and its tests. Do not normalize or import
  legacy typed documents, preserve `x.alpha15`, or provide a compatibility surface.

**Steps:**

- [x] Complete the fixture sweep before closing validation. All eight live disposable
  `test-vault` Concepts, four cassette-generated Concepts, and M0 strict-workspace
  fixtures have no unknown top-level fields. The seeded-error root `contradictions`
  exception was canonicalized in `4f370c04`; the Alpha15 importer is retired by the
  clean-slate ruling.

- [x] Write the failing test. In `tests/test_schemas.py`, replace
  `test_schema_accepts_undeclared_meaning_fields_during_root_layout_migration` (:160-171)
  with:

  ```python
  def test_schema_rejects_undeclared_fields_while_x_hatch_passes():
      note = schema.load_types()["note"]
      good = {
          "id": "01KBN6V6KX0000000000000001",
          "type": "note",
          "title": "T",
          "tags": [],
          "links": {},
          "x": {"local": "ok", "nested": {"deep": 1}},
      }
      assert schema.validate_frontmatter(good, note) == []
      errors = schema.validate_frontmatter(dict(good, surprise=True), note)
      assert any("surprise: unknown field" in error for error in errors)
      retired = schema.validate_frontmatter(dict(good, citations=[]), note)
      assert [error for error in retired if "citations" in error] == [
          "citations: field is retired"
      ]
  ```

- [x] Run to verify failure:
  `python -m pytest tests/test_schemas.py::test_schema_rejects_undeclared_fields_while_x_hatch_passes -v`
  — expected: the `surprise: unknown field` assertion fails (open validator returns `[]`).

- [x] Write the minimal implementation in
  `src/memoria_vault/runtime/subsystems/lib/schema.py`. Replace the docstring lines
  :166-168 with:

  ```python
      Returns a list of human-readable error strings (empty = valid).
      Validation is closed: fields not declared by the type schema are rejected
      (nest extension data under the declared `x:` map instead).
  ```

  and insert directly after the `forbidden` loop (:172-174):

  ```python
      known_fields = (
          set(schema.get("required") or {})
          | set(schema.get("optional") or {})
          | set(schema.get("forbidden") or [])
      )
      for field in sorted(set(fm) - known_fields):
          errors.append(f"{field}: unknown field; declare it in the type schema or nest under x:")
  ```

  (`forbidden` names are folded into `known_fields` so a retired field yields exactly its
  one "field is retired" error, never a second "unknown field" error.)

- [x] Run to verify pass:
  `python -m pytest tests/test_schemas.py -v`.

- [x] Add closure-boundary coverage: strict `stage_concept` rejects an undeclared
  root field and accepts nested `x:` data; pre-commit and linter report the same
  root field; seeded contradiction/error, integrity, exploration, and search fixtures
  use `links.contradicts` while the answer-query response remains compatible.

  *Landed 2026-08-01.* Three new boundary tests, one per closure layer, each
  asserting the exact `"<field>: unknown field; declare it in the type schema or
  nest under x:"` string and each proving the `x:` hatch produces no error in
  the same run:
  `tests/test_trusted_writer.py::test_stage_concept_rejects_undeclared_root_field_and_stages_nested_x`
  (also asserts nothing is staged on rejection, and that nested `x:` data
  survives verbatim rather than merely validating),
  `tests/test_precommit_schema.py::test_undeclared_root_field_blocks_while_x_hatch_passes`,
  and
  `tests/test_detectors.py::test_schema_check_flags_undeclared_root_field_but_not_the_x_hatch`.
  The last two check both files in one call and assert the full error/finding
  list, so a hatch-file false positive fails too. The `links.contradicts`
  half of this box was already satisfied by `4f370c04` and is verified, not
  rewritten: `seeded_errors.py:396` writes the relation,
  `tests/test_integrity.py:495-533` keeps a root-`contradictions:` document as
  a negative reader contract, `tests/test_exploration_channel.py:38` and
  `tests/test_search_index.py:340-375` seed the relation, and that last test
  pins the public `answer["contradictions"]` payload key as still populated.

- [x] Replace the root `contradictions` seeded error with
  `links: {contradicts: [<target>]}`, remove every active root-field reader, and
  remove the dead `type == "work"` branch from `check_contradiction_links`
  (`4f370c04`; independent review approved).

- [x] Update the docs prose `docs/reference/data-model/frontmatter.md:41-43` — replace
  the three lines beginning "Unknown extra fields are accepted during the alpha
  migration." with:

  ```markdown
  Validation is closed: fields a type schema does not declare are rejected. The
  `x:` map is the escape hatch for extension data, and `forbidden:` fields are
  reported as retired rather than unknown.
  ```

- [x] Run the gate: `python scripts/verify`.

- [x] Commit:

  ```
  git add src/memoria_vault/runtime/subsystems/lib/schema.py \
          tests/test_schemas.py \
          docs/reference/data-model/frontmatter.md
  git commit -m "feat(schema): close frontmatter validation — unknown fields rejected, x: hatch preserved (NODES §3)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```
# Section NID-B — v16 identity re-key, indexer path→id resolution, `memoria mv`

Implements NODES spec §1 (all 8 clauses) — `docs/superpowers/specs/2026-07-15-graph-nodes-identity-design.md:28-81` —
plus its §7 acceptance criteria and §8 slices 3–4. Schema version **16** per the
binding allocation (Plan 22 owns 13/14/15; ERP-A takes 17, ERP-C 18).

## Verified current state (read at main @ 9c77ba61)

All line refs below are at `9c77ba61` — **before** Plan 22's G1 + G2S1.1–.3 + S12.2
land. Those tasks touch `state.py`, `schema.sql`, `indexing.py`, and
`tests/test_query_substrate.py`; re-anchor by symbol name, not line number, when
executing.

- `schema.sql:51-59` `concepts(concept_id PK, concept_type CHECK 10-roster, store)`;
  `:60-63` `concept_verdicts(concept_id PK, check_status)`; `:64-71` `concept_flags`;
  `:72-79` `concept_status` view; `:240-250` `concept_edges` (v12 shape — Plan 22
  G2S1.2/.3 add `edge_id`, `attributes_json`, `idx_concept_edges_edge_id`,
  `idx_concept_edges_target` before this section runs); `:251-276` the three
  passage-cascade triggers with the `('catalog/sources/' || work_id)` /
  `('catalog/sources/' || NEW.work_id)` concatenation endpoints (`:258,267,275`);
  `:364-369` `derivations(input_id, output_id, actor)`; `:378` `PRAGMA user_version = 12`.
- `state.py:53` `SCHEMA_VERSION = 12`; `:472-481` `connect` already sets
  `PRAGMA foreign_keys = ON` (`:477`) — v16's real FKs will actually enforce;
  `:1047-1060` `set_concept_verdict`; `:1063-1072` `concept_check_status`;
  `:1092-1103` `rebuild_file_concept_mirror` (wipe-and-refill of `store='file'` rows);
  `:1106-1172` `record_file_output`; `:1175-1194` `mark_checked`;
  `:1197-1230` `record_observed_file_edit`; `:1295-1315` `set_concept_flag`;
  `:1318-1339` `concept_flags`; `:1342` `note_curation_status`;
  `:1510` `upsert_catalog_record` — its concept mirror rows at `:1598-1600` key works
  as `catalog/sources/<work_id>`; `:2026-2052` `replace_concept_edges` (G2S1.1/.2
  reshape it to upsert-and-prune with `edge_id`/`attributes_json` first);
  `:2055-2076` `concept_edges`; `:2406-2413` `_init` (G1 adds the MIGRATIONS loop);
  `:3353-3368` `_upsert_concept_mirror_conn`; `:3371-3385` `_set_concept_verdict_conn`;
  `:3388-3403` `_cascade_passage_check_status_conn` (mirrors the trigger predicate in
  Python, including the `'catalog/sources/' || work_id` concatenation);
  `:3420-3424` `_concept_edge_relation`.
- `indexing.py:34-38` `_rebuild_passage_index` (no concept-mirror reconcile);
  `:101-130` `_passage_row` — `concept_id` at `:114` is
  `f"catalog/sources/{work_id}"` for fulltexts else the path; `:133-136`
  `_concept_edges` stub (G2S1.1 replaces it with a links-derived version emitting
  `target_concept_id`).
- `knowledge.py:346-414` `curate_note_link` (the writer-flow template for
  `move_concept`); `:3036-3047` `_link_target`; `:3380-3388` `_note_rel`;
  `:3391-3403` `_concept_rel` (accepts `catalog/sources/`, `notes/`, `hubs/`,
  `digests/`, `fulltexts/` — **not** `projects/`); `:3427-3435` `_unique_note_rel`.
- `trusted_writer.py:238-249` `commit_writer_changes`; `:608-629`
  `rebuild_concept_mirror_from_files` — builds rows `{"concept_id": <path>,
  "concept_type": ...}`; sole production caller is `cli.py:1970`
  (`_cmd_workspace_rebuild`).
- `vaultio.py:107-120` `apply_universal_concept_frontmatter` mints `id` (ULID; digest/
  fulltext get `work_id`); `:123-134` `universal_concept_frontmatter_errors` already
  rejects non-ULID `id` for note/hub/project; `:144-145` `is_ulid`; `:148-153` `new_ulid`.
- **`hub.yaml:5` and `project.yaml:5` already carry `id: ulid`** (as does
  `note.yaml:10`) under `src/memoria_vault/product/workspace_seed/.memoria/schemas/types/`.
  Clause 1's "extend the requirement to hub/project types" is already shipped;
  NID-B.3 ratifies it with guard tests instead of re-editing the yamls.
- `worker.py:53-66` `PROTECTED_OPERATION_ACTORS`; `:303` `_run_operation_job` (flat
  `if operation_id ==` dispatch; `curate-note-link` branch at `:471-497`).
- `cli.py:259-265` `link` parser; `:1208-1221` `_cmd_link`; `:2087-2098`
  `_enqueue_and_run`; `:560` `_common`.
- `tests/test_schema_version.py:14-17` version pin (Plan 22 renames it along its
  chain to `test_schema_lands_at_user_version_15`); `:30-37`
  `test_source_has_no_private_migration_helpers` **bans the substring `_migrate_`
  anywhere under src/** — the v16 callable must not contain it in its name.
- `tests/test_query_substrate.py:31` version pin; module-level
  `rebuild_passage_index` wrapper at `:18-19`.
- `tests/test_runtime_state.py:259-300`
  `test_rebuild_concept_mirror_from_files_does_not_trust_frontmatter_status` asserts
  wipe-and-refill `deleted` counts — updated in NID-B.2.
- `tests/floor_lib.py` `OPERATION_REGISTRY` (~`:450`) must gain an entry for any new
  operation id (`tests/test_floor_coverage.py:37-42` fails otherwise);
  `tests/test_knowledge.py:69-73` `workspace(tmp_path)` helper (schemas + git).
- Operation ids are also listed in three published docs:
  `docs/reference/commands-and-transports/system-actions.md:26`,
  `docs/reference/commands-and-transports/system-actions-operations.md:17` (+ table
  row pattern at `:123`), `docs/reference/control-and-policy/control-plane.md:61`
  (pi-protected roster).

## Consumed from Plan 22 (must be merged before NID-B.1 starts)

- Plan 22's current fresh schema and fail-closed version gate. It deliberately
  provides no `MIGRATIONS` registry, migration helper, or compatibility path.
- `state.concept_edge_id(source_concept_id: str, relation_type: str, target_concept_id: str) -> str`
  — `sha256(f"{source}\0{relation}\0{target}")[:24]` (G2S1.2).
- `state.replace_concept_edges(vault, rows, *, paths=None) -> dict[str, int]` —
  upsert-and-prune sparing `relation_type = 'tension'` rows; edge rows carry
  `edge_id` + `attributes_json`, `attributes_json` preserved on conflict (G2S1.1/.2).
- `schema.py normalize_link_target(target: str) -> str` and
  `parse_links(links: object) -> list[tuple[str, str]]` (G2S1.1).
- The current fresh schema is at 15 with edge fields/indexes and the `grounds`
  enum. NID-B replaces it with current fresh schema v16; it does not transform a
  v15 database.

## SPEC GAPs

- **SPEC GAP (id collision):** clause 1 keys catalog works, digests, and fulltexts
  all by bare `work_id`, which collides in the `concepts`/`concept_verdicts` PKs
  (three concept rows per work). This section keys **catalog works by bare
  `work_id`** and keeps **digests/fulltexts keyed by their paths**
  (`digests/<work_id>.md` — a pure function of `work_id`, and their filenames are
  machine-fixed, so rename-reconciliation is moot for them), as ratified by
  Graph-R1. Uniform runtime rule used throughout: *DB key = frontmatter
  `id` when it is a ULID, else the concept's path; catalog works = bare `work_id`.*
- **SPEC GAP (deletion semantics):** the spec decides rename semantics, not what
  happens to id-keyed verdict rows when a concept file is deleted outright. This
  section keeps them (the mirror row persists as a tombstone; inbound edges revert
  to pending via `ON DELETE SET NULL`); prune removes only verdict-less rows.

## Constraints other sections must honor

- v16 copies the 10-value `concepts.concept_type` CHECK verbatim; the
  registry-derived CHECK (NODES §2, another section) lands in its own direct
  fresh-schema change.
- ERP-A's v17 relation-roster CHECK extends the **v16** `concept_edges` shape
  directly (nullable `target_concept_id`, `target_path` in the PK).
- `passages.concept_id` id-space changes at NID-B.4 (frontmatter id / bare work_id).
- New edge-row dict contract after NID-B.4: producers pass `target_path` (vault
  path or `catalog/sources/<work_id>` rendering), never a resolved id; resolution
  is `replace_concept_edges`'s job.

---

### Task NID-B.1: schema v16 — fresh identity safety floor

This task emits the v16 current schema and runtime floor directly for a new vault.
It does not open, inspect, re-key, or transform a v15 database. New file Concepts
use frontmatter ULIDs immediately, while catalog works use their bare work ids.
It implements NODES §1.1, §1.4, §1.6–.8 and preserves the G2 mirror contract.

**Files:**
- Modify: `src/memoria_vault/runtime/schema.sql` — v16 `concepts`,
  `concept_verdicts`, `concept_edges`, `catalog_sources`, triggers/view, and
  `PRAGMA user_version` definitions.
- Modify: `src/memoria_vault/runtime/state.py` — `SCHEMA_VERSION`, canonical
  ref/parent helpers, catalog upsert, file-mirror rebuild, verdict/status seams,
  and `replace_concept_edges`; do not add a migration or re-key helper.
- Create: `tests/test_schema_v16_identity.py`.
- Modify: current-schema tests in `tests/test_schema_version.py`,
  `tests/test_query_substrate.py`, `tests/test_runtime_state.py`, and
  `tests/conftest.py`; do not create old-schema fixtures.

**Interfaces:**
- Consumes: the Plan-22 fresh-schema gate, `concept_edge_id`, and G2
  upsert-and-prune edge seam; `schema.concept_type_for(document_type)` from NID-A.
- Produces: schema version 16; `concepts.path`; FK-backed verdicts, edges, and
  catalog parents; `resolve_concept_id(conn, ref) -> str` (read-only resolution);
  `ensure_concept_parent_conn(conn, ref, *, concept_type, store, path) -> str`
  (write-only parent creation); registry-normalizing
  `rebuild_file_concept_mirror`; and the v16 scoped-edge contract below.
- Contract: `catalog_sources.work_id` is the FK/identity; its parent is exactly
  `(work_id, 'work', 'db', 'catalog/sources/<work_id>')`. The separate
  `catalog_sources.concept_path` column is a normalized non-identity read-scope
  alias. Default an omitted value to `catalog/sources/<work_id>`; never use it to
  key a mirror, FK, edge, or verdict.

> **Execution replacement:** implement and test this contract from a fresh
> `state.connect(tmp_path)` vault only. Every later checklist item in this task
> that constructs v15 data, invokes a migration, or re-keys old rows is historical
> provenance and must not be executed.

**Steps:**

- [x] Write the failing v16 contract tests in `tests/test_schema_v16_identity.py`.
  Build a v15 fixture containing `concepts`, `concept_verdicts`, `concept_flags`,
  `concept_edges`, `derivations`, `passages`, and `catalog_sources`. Include:
  a catalog work with `concept_path='notes/alpha.md'`; both
  `catalog/sources/smith-2020`, `./catalog/sources/smith-2020`, and
  `./catalog/sources/smith-2020/source.md` legacy references;
  a path-keyed fulltext; a missing edge target; a direct tension row; and a
  verdict-bearing deleted file row. Assert after `state.connect(vault)` that:

  ```python
  assert parent == {
      "concept_id": "smith-2020",
      "concept_type": "work",
      "store": "db",
      "path": "catalog/sources/smith-2020",
  }
  assert catalog["concept_path"] == "notes/alpha.md"
  assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
  assert not any(str(row[0]).startswith(("./catalog/sources/", "catalog/sources/"))
                 for row in conn.execute("SELECT concept_id FROM concepts"))
  ```

  Add separate tests that (a) `PRAGMA foreign_key_list(catalog_sources)` reports
  `concepts` / `work_id` / `concept_id` / `RESTRICT` / `RESTRICT`, and an orphan
  catalog insert raises `sqlite3.IntegrityError`; (b) an unrelated legacy Concept
  collapsing to `smith-2020` raises `RuntimeError` and leaves the DB at user version
  15; (c) a fulltext remains keyed and pathed as `fulltexts/smith-2020.md` but has
  `concept_type == 'work'`; (d) `paths=[]` performs zero edge inserts/deletes and
  leaves direct tension rows untouched; (e) an absent verdictless file mirror row is
  pruned, while a verdict-bearing row survives and its inbound edge becomes pending;
  and (f) bare, rendered, `./`, and `/source.md` catalog forms update the same
  verdict, derivation endpoint, and edge endpoint without minting another parent;
  and (g) a normal catalog upsert defaults an omitted alias
  to its virtual rendering while preserving a supplied normalized alias without using
  either value as graph or verdict identity; and (h) `record_file_output` and
  `record_observed_file_edit` accept fulltext/code-artifact inputs only after mapping
  them to `work`/`project`, never exposing raw types to the v16 CHECK; and (i) a
  post-Plan-22, pre-B.4 `rebuild_passage_index` row with only
  `target_concept_id` (no `target_path`) persists and resolves under v16.

  > **Sub-clause (b), fresh-install reading (2026-07-31 review repair):** the
  > amendment retires *migrations*, not fresh-install correctness. The binding
  > half — an identity collision raises a descriptive `RuntimeError` instead of
  > being silently accepted (cross-section contract 10) — is implemented in
  > `ensure_concept_parent_conn` and covered by
  > `test_catalog_upsert_refuses_to_hijack_a_file_concept`,
  > `test_mirror_rebuild_refuses_to_hijack_a_catalog_work`, and
  > `test_two_identities_claiming_one_path_raise_a_descriptive_error`. Only the
  > "leaves the DB at user version 15" half is retired, there being no v15.

- [x] Run the new tests and confirm they fail before the v16 implementation:

  ```bash
  python -m pytest tests/test_schema_v16_identity.py -v
  ```

- [x] Define one normalizer in `state.py` and use it before every v15→v16 mapping or
  lookup. The migration and runtime resolver must share these semantics:

  ```python
  def _legacy_rel(value: str) -> str:
      raw = str(value or "").strip().replace("\\", "/")
      while raw.startswith("./"):
          raw = raw[2:]
      return normalize_path(raw)


  def _catalog_identity(ref: str, catalog_ids: set[str]) -> str:
      rel = _legacy_rel(ref)
      rendered = rel.removeprefix("catalog/sources/").removesuffix("/source.md")
      return rendered if rendered in catalog_ids else rel
  ```

  Apply it to concepts, verdicts, flags, edge endpoints and paths, derivation
  endpoints, and `passages.concept_id`. A catalog path is only rendered in a path
  column; its DB identity is the bare `work_id`.

- [ ] Replace `_rekey_concept_identity(conn)` with a collision-safe v16 migration.
  Snapshot all identity-bearing rows **and full `catalog_sources` rows** before
  dropping anything. Drop the old cascade triggers and `concept_status` view; create
  `concepts_v16`; seed one exact DB parent for each catalog work; then add normalized
  file parents using `schema.concept_type_for` (so `fulltext` becomes `work`). Do
  not use `INSERT OR IGNORE`, `INSERT OR REPLACE`, or `UPDATE OR REPLACE` where a
  collapsed canonical key could hide a conflict. A duplicate is valid only when its
  type/store/path/status are identical; otherwise raise a descriptive `RuntimeError`
  and let the migration transaction roll back.

  Rebuild in dependency order: parents; `catalog_sources_v16`; verdicts; flags;
  edges; derivations; then passage `concept_id`s. Define the catalog replacement with
  the current complete column list and this first column:

  ```sql
  work_id TEXT PRIMARY KEY
      REFERENCES concepts(concept_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  ```

  Copy every other catalog column verbatim, preserving a nonblank normalized
  `concept_path` and defaulting only an empty one to `catalog/sources/<work_id>`.
  Drop/rename the child only after every parent has been verified or backfilled.
  Rebuild verdicts and edges only after parents exist. For edges, create sources as
  needed, resolve but never create targets, preserve `target_path` for a missing
  target, set its id and `edge_id` to `NULL`/`''`, recompute resolved edge ids over
  canonical triples, and preserve `attributes_json`. Rewrite flags/derivations
  without collision-losing replacement; rewrite only `passages.concept_id` (not
  `path`, `work_id`, or `passage_id`). End with `PRAGMA foreign_key_check` and raise
  if it is nonempty; let the normal schema pass recreate indexes, triggers, and view.

- [x] Make the v16 runtime seams safe before NID-B.2. `upsert_catalog_record` first
  calls `ensure_concept_parent_conn(conn, stable_work_id, concept_type="work",
  store="db", path=f"catalog/sources/{stable_work_id}")`, then writes the catalog
  child and its verdict by that bare id. It retains the public `concept_path`
  parameter as the non-identity alias described above. For file rows,
  `rebuild_file_concept_mirror` maps document type through
  `schema.concept_type_for`, upserts normalized path-keyed rows, and prunes only
  absent `store='file'` rows with no verdict. Deleting a file Concept cascades its
  outgoing edges; inbound edges become pending through `ON DELETE SET NULL`.
  `record_file_output` and `record_observed_file_edit` apply the same registry
  mapping before their B.1 mirror/upsert or parent-ensure calls, so raw `fulltext`
  and `code-artifact` values can never reach the 10-value DB CHECK.

  `resolve_concept_id` never mints; `ensure_concept_parent_conn` is called before
  every FK-backed verdict/flag/status write and fails closed for an unknown type.
  Read-only `concept_check_status` resolves but does not mint. Catalog bare, rendered,
  and `./` forms resolve to the same bare parent.

- [x] Replace `replace_concept_edges(vault, rows, *, paths=None)` under this exact
  contract:

  ```python
  path_list = None if paths is None else list(paths)
  if path_list == []:
      return {"deleted": 0, "inserted": 0}
  ```

  Use `path_list` for the remainder of the function. `paths is None` alone means a full
  mirror; a nonempty scope may insert/update/prune only its normalized `source_path`s.
  Preserve the G2 producer contract until B.4: derive the path key from an old row as

  ```python
  catalog_ids = {str(row[0]) for row in conn.execute("SELECT work_id FROM catalog_sources")}
  raw_target = str(row.get("target_path") or row.get("target_concept_id") or "")
  canonical_target = _catalog_identity(raw_target, catalog_ids)
  target_path = (
      f"catalog/sources/{canonical_target}"
      if canonical_target in catalog_ids
      else _legacy_rel(raw_target)
  )
  ```

  where `catalog_ids` is the current bare work-id set. Thus old G2 rows still work,
  while `catalog/sources/<id>`, `./catalog/sources/<id>`, and
  `catalog/sources/<id>/source.md` share one virtual path key. New B.4 producers pass
  `target_path` directly and take the same path through this normalizer.
  Ignore incoming `relation_type == 'tension'` rows and exclude persisted tension
  rows from every prune query. Resolve or ensure sources, resolve but never create
  targets, key conflicts/prunes only by `(source_concept_id, relation_type,
  target_path)`, preserve `attributes_json`, and never clear a previously resolved
  target/edge id on a partial pass.

- [x] Run the focused migration/runtime suites, then the one correctness gate:

  ```bash
  python -m pytest tests/test_schema_v16_identity.py tests/test_schema_version.py tests/test_schema_v10.py tests/test_query_substrate.py tests/test_runtime_state.py -v
  python scripts/verify
  ```

  Expected: all focused tests pass; `verify: OK`.

- [x] Commit the atomic safety floor:

  ```bash
  git add src/memoria_vault/runtime/schema.sql src/memoria_vault/runtime/state.py \
          tests/test_schema_v16_identity.py tests/test_schema_version.py \
          tests/test_schema_v10.py tests/test_query_substrate.py \
          tests/test_runtime_state.py tests/conftest.py
  git commit -m "feat(schema): v16 identity re-key safety floor"
  ```

---

### Archived NID-B.1 drafting record (do not execute)

The following original draft is retained for historical comparison only. Its migration,
mirror, and B.2-boundary instructions are superseded by the revised NID-B.1 task above.
Do not execute its checkboxes or copy its code snippets.

One migration, per the binding allocation: 15→16. The DB re-keys to frontmatter
identity (clause 1), `path` becomes a unique updatable attribute, real FKs land
(clause 4), dangling links become pending rows (clause 6), the catalog triggers
lose their `'catalog/sources/' ||` concatenation (clause 7), and `edge_id` is
recomputed over the new triples carrying `attributes_json` (clause 8). The
migration is a **callable** (the mapping needs Python logic); it is deterministic
in-DB only — `catalog/sources/<work_id>` endpoints re-key to bare `work_id`; file
concepts keep their path as a provisional key that NID-B.2's mirror rebuild
re-keys to the frontmatter ULID (the DB cannot read frontmatter). This task also
adapts `replace_concept_edges`'s INSERT to the new column set so the gate stays
green; the id-space emission itself is NID-B.2/NID-B.4.

**Files:**
- Modify: `src/memoria_vault/runtime/schema.sql` — the `concepts` block (`:51-59` at
  9c77ba61), `concept_verdicts` (`:60-63`), `concept_status` view (`:72-79`), the
  `concept_edges` block as landed by G2S1.2/.3 (`:240-250` pre-Plan-22), the three
  cascade triggers (`:251-276`), `catalog_sources` rebuilt with its v16 FK, trailing
  pragma (`:378`, 15 → 16)
- Modify: `src/memoria_vault/runtime/state.py` — `SCHEMA_VERSION` (`:53`, 15 → 16);
  G1's `MIGRATIONS` dict (add key 15); new module function `_rekey_concept_identity`
  next to `_init` (`:2406` pre-Plan-22); `replace_concept_edges` (as landed by
  G2S1.1/.2) INSERT/prune keys; `concept_edges` SELECT column lists (`:2055-2076`
  pre-Plan-22); `_upsert_concept_mirror_conn` (`:3353-3368`) gains a `path` parameter;
  its three in-file callers (`:1097`, `:1124`, `:1206`) and the catalog caller
  (`:1598-1600`); catalog parent backfill/rebuild and parent-first normal upserts
- Modify: `tests/test_schema_version.py` (pin 15 → 16, rename
  `test_schema_lands_at_user_version_15` → `..._16`), `tests/test_query_substrate.py:31`
  (pin 15 → 16) and its G2S1.1 mirror test (new column keys)
- Create: `tests/test_schema_v16_identity.py`
- Modify: `tests/conftest.py` — register `"test_schema_v16_identity.py": "contract"`
  in `TEST_LEVELS` (nearest sibling `test_schema_version.py:101` is `"contract"`)

**Interfaces:**
- Consumes: `state.MIGRATIONS` (G1 shape above), `state.concept_edge_id` (G2S1.2),
  `state.replace_concept_edges` upsert-and-prune (G2S1.1), `state.DB_REL`,
  `normalize_path`, `now_iso`.
- Produces:
  - v16 DDL (below) — `concepts.path` (unique-when-nonblank), FK
    `concept_verdicts.concept_id → concepts` (`ON UPDATE CASCADE`), FKs
    `concept_edges.source_concept_id → concepts` (`ON UPDATE CASCADE ON DELETE CASCADE`)
    and `concept_edges.target_concept_id → concepts` (nullable,
    `ON UPDATE CASCADE ON DELETE SET NULL`), edge PK
    `(source_concept_id, relation_type, target_path)`, triggers with bare endpoints;
    immediate `catalog_sources.work_id → concepts.concept_id` with `ON UPDATE RESTRICT
    ON DELETE RESTRICT` and parent shape `work`/`db`/`catalog/sources/<work_id>`.
  - `MIGRATIONS[15] = (16, [_rekey_concept_identity])`;
    `state._rekey_concept_identity(conn: sqlite3.Connection) -> None`.
  - `state._upsert_concept_mirror_conn(conn, concept_id: str, concept_type: str,
    store: str, path: str) -> None` (signature change; module-private).
  - `state.replace_concept_edges(vault, rows, *, paths=None) -> dict[str, int]` —
    row contract gains `target_path` (falls back to the row's `target_concept_id`
    for G2S1.1-era producers); resolution is sticky (a NULL re-resolution never
    clears a previously resolved `target_concept_id`); pending rows carry
    `edge_id = ''`, resolved rows `edge_id = concept_edge_id(source, relation, target_id)`.
  - `state.concept_edges` rows now include `target_path` (plus the G2S1.2
    `edge_id`/`attributes_json` keys).

**Steps:**

- [ ] Create `tests/test_schema_v16_identity.py` with the failing shape/FK tests:

  ```python
  """Schema v16: concepts key by frontmatter identity; path is an attribute."""

  from __future__ import annotations

  import sqlite3
  from pathlib import Path

  import pytest

  from memoria_vault.runtime import state

  ULID_A = "01ARZ3NDEKTSV4RRFFQ69G5FAV"


  def test_v16_concepts_carry_path_attribute_and_real_fks(tmp_path: Path) -> None:
      with state.connect(tmp_path) as conn:
          concept_columns = {row["name"] for row in conn.execute("PRAGMA table_info(concepts)")}
          edge_columns = {
              row["name"]: dict(row) for row in conn.execute("PRAGMA table_info(concept_edges)")
          }
          verdict_fks = {
              (row["table"], row["from"], row["to"])
              for row in conn.execute("PRAGMA foreign_key_list(concept_verdicts)")
          }
          edge_fks = {
              (row["table"], row["from"], row["to"])
              for row in conn.execute("PRAGMA foreign_key_list(concept_edges)")
          }
      assert "path" in concept_columns
      assert "target_path" in edge_columns
      assert edge_columns["target_concept_id"]["notnull"] == 0
      assert ("concepts", "concept_id", "concept_id") in verdict_fks
      assert {
          ("concepts", "source_concept_id", "concept_id"),
          ("concepts", "target_concept_id", "concept_id"),
      } <= edge_fks


  def test_v16_fk_violations_are_impossible_to_insert(tmp_path: Path) -> None:
      with state.connect(tmp_path) as conn:
          with pytest.raises(sqlite3.IntegrityError):
              conn.execute(
                  "INSERT INTO concept_verdicts(concept_id, check_status)"
                  " VALUES ('no-such-concept', 'checked')"
              )
          with pytest.raises(sqlite3.IntegrityError):
              conn.execute(
                  "INSERT INTO concept_edges("
                  " edge_id, source_concept_id, relation_type, target_concept_id,"
                  " target_path, check_status, source_path, updated_at)"
                  " VALUES ('', 'no-such-concept', 'supports', NULL,"
                  " 'notes/x.md', 'unchecked', '', '2026-07-15T00:00:00Z')"
              )
  ```

- [ ] Run
  `python -m pytest tests/test_schema_v16_identity.py -v`
  — expect FAIL: `AssertionError: assert 'path' in {...}` (fresh `concepts` table has
  no `path` column) and `Failed: DID NOT RAISE <class 'sqlite3.IntegrityError'>`
  (no FKs yet). (If pytest errors with an unregistered-level message first, do the
  conftest step below and rerun.)
- [ ] Register the file in `tests/conftest.py` `TEST_LEVELS` (dict at `:18`,
  alphabetical position near `"test_schema_version.py": "contract"` at `:101`):

  ```python
      "test_schema_v16_identity.py": "contract",
  ```

- [ ] Append the failing migration test to `tests/test_schema_v16_identity.py`
  (legacy fixture is the v15 shape: v12 tables + G2S1.2's `edge_id`/`attributes_json`):

  ```python
  def _legacy_v15_db(vault: Path) -> Path:
      db = vault / state.DB_REL
      db.parent.mkdir(parents=True)
      with sqlite3.connect(db) as conn:
          conn.execute(
              "CREATE TABLE concepts ("
              " concept_id TEXT PRIMARY KEY,"
              " concept_type TEXT NOT NULL,"
              " store TEXT NOT NULL)"
          )
          conn.execute(
              "CREATE TABLE concept_verdicts ("
              " concept_id TEXT PRIMARY KEY,"
              " check_status TEXT NOT NULL)"
          )
          conn.execute(
              "CREATE TABLE concept_flags ("
              " concept_id TEXT NOT NULL,"
              " flag TEXT NOT NULL,"
              " reason TEXT NOT NULL DEFAULT '',"
              " trigger_id TEXT NOT NULL DEFAULT '',"
              " created_at TEXT NOT NULL,"
              " PRIMARY KEY (concept_id, flag))"
          )
          conn.execute(
              "CREATE TABLE concept_edges ("
              " edge_id TEXT NOT NULL DEFAULT '',"
              " source_concept_id TEXT NOT NULL,"
              " relation_type TEXT NOT NULL,"
              " target_concept_id TEXT NOT NULL,"
              " attributes_json TEXT NOT NULL DEFAULT '{}',"
              " check_status TEXT NOT NULL,"
              " source_path TEXT NOT NULL DEFAULT '',"
              " updated_at TEXT NOT NULL,"
              " PRIMARY KEY (source_concept_id, relation_type, target_concept_id))"
          )
          conn.execute(
              "CREATE TABLE derivations ("
              " input_id TEXT NOT NULL,"
              " output_id TEXT NOT NULL,"
              " actor TEXT NOT NULL,"
              " PRIMARY KEY (input_id, output_id))"
          )
          conn.execute(
              "INSERT INTO concepts VALUES"
              " ('catalog/sources/smith-2020', 'work', 'db'),"
              " ('notes/alpha.md', 'note', 'file')"
          )
          conn.execute(
              "INSERT INTO concept_verdicts VALUES"
              " ('catalog/sources/smith-2020', 'checked'),"
              " ('notes/alpha.md', 'checked')"
          )
          conn.execute(
              "INSERT INTO concept_edges VALUES"
              " ('deadbeefdeadbeefdeadbeef', 'notes/alpha.md', 'supports',"
              "  'catalog/sources/smith-2020', '{\"warrant\": \"w1\"}',"
              "  'checked', 'notes/alpha.md', '2026-07-15T00:00:00Z'),"
              " ('', 'notes/alpha.md', 'extends', 'notes/ghost.md', '{}',"
              "  'unchecked', 'notes/alpha.md', '2026-07-15T00:00:00Z')"
          )
          conn.execute(
              "INSERT INTO derivations VALUES"
              " ('catalog/sources/smith-2020', 'notes/alpha.md', 'operation')"
          )
          conn.execute("PRAGMA user_version = 15")
      return db


  def test_v16_rekeys_catalog_endpoints_and_recomputes_edge_ids(tmp_path: Path) -> None:
      _legacy_v15_db(tmp_path)
      with state.connect(tmp_path) as conn:
          version = conn.execute("PRAGMA user_version").fetchone()[0]
          work = conn.execute(
              "SELECT concept_id, path FROM concepts WHERE concept_type = 'work'"
          ).fetchone()
          verdicts = {
              row["concept_id"]: row["check_status"]
              for row in conn.execute("SELECT * FROM concept_verdicts")
          }
          resolved = conn.execute(
              "SELECT * FROM concept_edges WHERE relation_type = 'supports'"
          ).fetchone()
          pending = conn.execute(
              "SELECT * FROM concept_edges WHERE relation_type = 'extends'"
          ).fetchone()
          derivation = conn.execute("SELECT input_id FROM derivations").fetchone()

      assert version == state.SCHEMA_VERSION == 16
      # Catalog endpoints re-key to bare work_id; the old key becomes the path.
      assert work["concept_id"] == "smith-2020"
      assert work["path"] == "catalog/sources/smith-2020"
      assert verdicts["smith-2020"] == "checked"
      # File concepts keep the path as a provisional key (re-keyed by reindex).
      assert verdicts["notes/alpha.md"] == "checked"
      # Resolved edge: new id-space triple, edge_id recomputed, attributes carried.
      assert resolved["target_concept_id"] == "smith-2020"
      assert resolved["target_path"] == "catalog/sources/smith-2020"
      assert resolved["attributes_json"] == '{"warrant": "w1"}'
      assert resolved["edge_id"] == state.concept_edge_id(
          "notes/alpha.md", "supports", "smith-2020"
      )
      # Dangling target: pending form — target_id NULL, target_path retained.
      assert pending["target_concept_id"] is None
      assert pending["target_path"] == "notes/ghost.md"
      assert pending["edge_id"] == ""
      assert derivation["input_id"] == "smith-2020"


  def test_v16_triggers_use_bare_work_id_endpoints(tmp_path: Path) -> None:
      with state.connect(tmp_path) as conn:
          trigger_sql = " ".join(
              str(row["sql"])
              for row in conn.execute(
                  "SELECT sql FROM sqlite_master WHERE type = 'trigger'"
                  " AND name LIKE '%passage_cascade%'"
              )
          )
      assert "'catalog/sources/' ||" not in trigger_sql
  ```

- [ ] Run
  `python -m pytest tests/test_schema_v16_identity.py::test_v16_rekeys_catalog_endpoints_and_recomputes_edge_ids -v`
  — expect FAIL: `AssertionError` on `version == state.SCHEMA_VERSION == 16`
  (SCHEMA_VERSION is still 15 and no `MIGRATIONS[15]` path exists — with the strict
  G1 loop this surfaces as `RuntimeError: unsupported Memoria DB schema version: 15`
  only if SCHEMA_VERSION were already bumped; either failure mode is acceptable
  evidence).
- [ ] Update `src/memoria_vault/runtime/schema.sql`. Replace the `concepts` /
  `concept_verdicts` blocks (`:51-63` at 9c77ba61) with:

  ```sql
  CREATE TABLE IF NOT EXISTS concepts (
      concept_id TEXT PRIMARY KEY,
      concept_type TEXT NOT NULL
          CHECK (concept_type IN (
              'work', 'digest', 'note', 'hub', 'project', 'capability',
              'operation', 'skill', 'adapter', 'workflow'
          )),
      store TEXT NOT NULL CHECK (store IN ('db', 'file')),
      path TEXT NOT NULL DEFAULT ''
  );
  CREATE UNIQUE INDEX IF NOT EXISTS idx_concepts_path
      ON concepts(path) WHERE path != '';
  CREATE TABLE IF NOT EXISTS concept_verdicts (
      concept_id TEXT PRIMARY KEY
          REFERENCES concepts(concept_id) ON UPDATE CASCADE,
      check_status TEXT NOT NULL CHECK (check_status IN ('unchecked', 'checked', 'quarantined'))
  );
  ```

  Replace the `concept_status` view (`:72-79`) with (adds `path`):

  ```sql
  CREATE VIEW IF NOT EXISTS concept_status AS
  SELECT
      c.concept_id,
      c.concept_type,
      c.store,
      c.path,
      COALESCE(v.check_status, 'unchecked') AS check_status
  FROM concepts c
  LEFT JOIN concept_verdicts v ON v.concept_id = c.concept_id;
  ```

  Replace the `concept_edges` block (as landed by G2S1.2/.3) with:

  ```sql
  CREATE TABLE IF NOT EXISTS concept_edges (
      edge_id TEXT NOT NULL DEFAULT '',
      source_concept_id TEXT NOT NULL
          REFERENCES concepts(concept_id) ON UPDATE CASCADE ON DELETE CASCADE,
      relation_type TEXT NOT NULL CHECK (
          relation_type IN ('supports', 'contradicts', 'extends', 'tension')
      ),
      target_concept_id TEXT
          REFERENCES concepts(concept_id) ON UPDATE CASCADE ON DELETE SET NULL,
      target_path TEXT NOT NULL DEFAULT '',
      attributes_json TEXT NOT NULL DEFAULT '{}',
      check_status TEXT NOT NULL CHECK (check_status IN ('unchecked', 'checked', 'quarantined')),
      source_path TEXT NOT NULL DEFAULT '',
      updated_at TEXT NOT NULL,
      PRIMARY KEY (source_concept_id, relation_type, target_path)
  );
  CREATE UNIQUE INDEX IF NOT EXISTS idx_concept_edges_edge_id
      ON concept_edges(edge_id) WHERE edge_id != '';
  CREATE INDEX IF NOT EXISTS idx_concept_edges_target
      ON concept_edges(target_concept_id);
  ```

  Replace the two `concept_verdicts` cascade triggers (`:251-268`) with bare-endpoint
  bodies (clause 7 — same body for insert and update variants):

  ```sql
  CREATE TRIGGER IF NOT EXISTS concept_verdicts_passage_cascade_insert
  AFTER INSERT ON concept_verdicts
  BEGIN
      UPDATE passages
      SET check_status = NEW.check_status
      WHERE concept_id = NEW.concept_id
         OR work_id = NEW.concept_id
         OR path = (SELECT path FROM concepts WHERE concept_id = NEW.concept_id);
  END;
  CREATE TRIGGER IF NOT EXISTS concept_verdicts_passage_cascade_update
  AFTER UPDATE OF check_status ON concept_verdicts
  BEGIN
      UPDATE passages
      SET check_status = NEW.check_status
      WHERE concept_id = NEW.concept_id
         OR work_id = NEW.concept_id
         OR path = (SELECT path FROM concepts WHERE concept_id = NEW.concept_id);
  END;
  ```

  and the `catalog_sources` trigger (`:269-276`) with:

  ```sql
  CREATE TRIGGER IF NOT EXISTS catalog_sources_passage_cascade_update
  AFTER UPDATE OF check_status ON catalog_sources
  BEGIN
      UPDATE passages
      SET check_status = NEW.check_status
      WHERE work_id = NEW.work_id
         OR concept_id = NEW.work_id;
  END;
  ```

  Change the trailing pragma to `PRAGMA user_version = 16;`.
- [ ] In `src/memoria_vault/runtime/state.py`: set `SCHEMA_VERSION = 16`; add the
  migration callable directly above `_init` and register it. The name deliberately
  avoids the banned `_migrate_` substring
  (`tests/test_schema_version.py:30-37`):

  ```python
  def _rekey_concept_identity(conn: sqlite3.Connection) -> None:
      """v15 -> v16: concepts key by frontmatter identity; path is an attribute.

      Deterministic in-DB mapping only (a migration cannot read frontmatter):
      'catalog/sources/<work_id>' endpoints re-key to bare work_id; file concepts
      keep their path as a provisional key that the next concept-mirror rebuild
      re-keys to the frontmatter ULID (reconcile-by-path in
      _upsert_concept_mirror_conn). Recomputes edge_id over the new triples and
      carries attributes_json in the same transaction; dangling targets become
      pending rows (target_concept_id NULL, target_path retained).
      """

      def new_key(old: str) -> str:
          return old.removeprefix("catalog/sources/")

      def parent_shape(key: str, old: str) -> tuple[str, str]:
          prefixes = (
              ("notes/", "note"), ("hubs/", "hub"), ("projects/", "project"),
              ("digests/", "digest"), ("fulltexts/", "fulltext"),
              ("capabilities/operations/", "operation"),
              ("capabilities/skills/", "skill"),
              ("capabilities/adapters/", "adapter"),
              ("capabilities/workflows/", "workflow"),
              ("capabilities/", "capability"),
          )
          for prefix, concept_type in prefixes:
              if old.startswith(prefix):
                  return concept_type, "file"
          return "work", "db"

      concepts = conn.execute("SELECT concept_id, concept_type, store FROM concepts").fetchall()
      verdicts = conn.execute("SELECT concept_id, check_status FROM concept_verdicts").fetchall()
      edges = conn.execute("SELECT * FROM concept_edges").fetchall()

      conn.execute(
          """
          CREATE TABLE concepts_v16 (
              concept_id TEXT PRIMARY KEY,
              concept_type TEXT NOT NULL
                  CHECK (concept_type IN (
                      'work', 'digest', 'note', 'hub', 'project', 'capability',
                      'operation', 'skill', 'adapter', 'workflow'
                  )),
              store TEXT NOT NULL CHECK (store IN ('db', 'file')),
              path TEXT NOT NULL DEFAULT ''
          )
          """
      )
      mapping: dict[str, str] = {}
      for row in concepts:
          old_id = str(row["concept_id"])
          mapping[old_id] = new_key(old_id)
          conn.execute(
              "INSERT OR IGNORE INTO concepts_v16(concept_id, concept_type, store, path)"
              " VALUES (?, ?, ?, ?)",
              (mapping[old_id], str(row["concept_type"]), str(row["store"]), old_id),
          )
      conn.execute("DROP TABLE concepts")
      conn.execute("ALTER TABLE concepts_v16 RENAME TO concepts")

      def ensure_parent(old_id: str) -> str:
          if old_id in mapping:
              return mapping[old_id]
          key = new_key(old_id)
          mapping[old_id] = key
          concept_type, store = parent_shape(key, old_id)
          conn.execute(
              "INSERT OR IGNORE INTO concepts(concept_id, concept_type, store, path)"
              " VALUES (?, ?, ?, ?)",
              (key, concept_type, store, old_id),
          )
          return key

      conn.execute(
          """
          CREATE TABLE concept_verdicts_v16 (
              concept_id TEXT PRIMARY KEY
                  REFERENCES concepts(concept_id) ON UPDATE CASCADE,
              check_status TEXT NOT NULL
                  CHECK (check_status IN ('unchecked', 'checked', 'quarantined'))
          )
          """
      )
      for row in verdicts:
          conn.execute(
              "INSERT OR REPLACE INTO concept_verdicts_v16(concept_id, check_status)"
              " VALUES (?, ?)",
              (ensure_parent(str(row["concept_id"])), str(row["check_status"])),
          )
      conn.execute("DROP TABLE concept_verdicts")
      conn.execute("ALTER TABLE concept_verdicts_v16 RENAME TO concept_verdicts")

      conn.execute(
          """
          CREATE TABLE concept_edges_v16 (
              edge_id TEXT NOT NULL DEFAULT '',
              source_concept_id TEXT NOT NULL
                  REFERENCES concepts(concept_id) ON UPDATE CASCADE ON DELETE CASCADE,
              relation_type TEXT NOT NULL CHECK (
                  relation_type IN ('supports', 'contradicts', 'extends', 'tension')
              ),
              target_concept_id TEXT
                  REFERENCES concepts(concept_id) ON UPDATE CASCADE ON DELETE SET NULL,
              target_path TEXT NOT NULL DEFAULT '',
              attributes_json TEXT NOT NULL DEFAULT '{}',
              check_status TEXT NOT NULL
                  CHECK (check_status IN ('unchecked', 'checked', 'quarantined')),
              source_path TEXT NOT NULL DEFAULT '',
              updated_at TEXT NOT NULL,
              PRIMARY KEY (source_concept_id, relation_type, target_path)
          )
          """
      )
      for row in edges:
          source = ensure_parent(str(row["source_concept_id"]))
          old_target = str(row["target_concept_id"])
          target = new_key(old_target)
          resolved = conn.execute(
              "SELECT 1 FROM concepts WHERE concept_id = ?", (target,)
          ).fetchone()
          target_id = target if resolved else None
          edge_id = (
              concept_edge_id(source, str(row["relation_type"]), target) if resolved else ""
          )
          conn.execute(
              "INSERT OR REPLACE INTO concept_edges_v16("
              " edge_id, source_concept_id, relation_type, target_concept_id,"
              " target_path, attributes_json, check_status, source_path, updated_at)"
              " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (
                  edge_id,
                  source,
                  str(row["relation_type"]),
                  target_id,
                  old_target,
                  str(row["attributes_json"]),
                  str(row["check_status"]),
                  str(row["source_path"]),
                  str(row["updated_at"]),
              ),
          )
      conn.execute("DROP TABLE concept_edges")
      conn.execute("ALTER TABLE concept_edges_v16 RENAME TO concept_edges")

      for old_id, key in mapping.items():
          if key == old_id:
              continue
          conn.execute(
              "UPDATE OR REPLACE concept_flags SET concept_id = ? WHERE concept_id = ?",
              (key, old_id),
          )
          conn.execute(
              "UPDATE OR REPLACE derivations SET input_id = ? WHERE input_id = ?",
              (key, old_id),
          )
          conn.execute(
              "UPDATE OR REPLACE derivations SET output_id = ? WHERE output_id = ?",
              (key, old_id),
          )
          conn.execute(
              "UPDATE passages SET concept_id = ? WHERE concept_id = ?",
              (key, old_id),
          )
      # Old cascade triggers referenced the dropped tables' names with the
      # concatenation endpoints; drop them (and the view) so the idempotent
      # schema.sql pass recreates the v16 definitions.
      conn.execute("DROP TRIGGER IF EXISTS concept_verdicts_passage_cascade_insert")
      conn.execute("DROP TRIGGER IF EXISTS concept_verdicts_passage_cascade_update")
      conn.execute("DROP TRIGGER IF EXISTS catalog_sources_passage_cascade_update")
      conn.execute("DROP VIEW IF EXISTS concept_status")
  ```

  Register it inside the `MIGRATIONS` dict (G1 style, after the 14 entry):

  ```python
      15: (16, [_rekey_concept_identity]),
  ```

  (If G1 landed `MIGRATIONS` above the callable's definition point, register with a
  post-definition assignment `MIGRATIONS[15] = (16, [_rekey_concept_identity])`
  directly below the function instead — the dict identity is what matters.)
- [ ] Still in state.py, give `_upsert_concept_mirror_conn` (`:3353-3368`) the `path`
  attribute (reconcile logic arrives in NID-B.2 — this step is shape only):

  ```python
  def _upsert_concept_mirror_conn(
      conn: sqlite3.Connection,
      concept_id: str,
      concept_type: str,
      store: str,
      path: str,
  ) -> None:
      conn.execute(
          """
          INSERT INTO concepts(concept_id, concept_type, store, path)
          VALUES (?, ?, ?, ?)
          ON CONFLICT(concept_id) DO UPDATE SET
              concept_type = excluded.concept_type,
              store = excluded.store,
              path = excluded.path
          """,
          (concept_id, concept_type, store, path),
      )
  ```

  and update the four call sites to pass the path they already hold (keys stay in
  the old path space until NID-B.2 — the gate must stay green after this task
  alone): `:1097-1102` pass `path=normalize_path(row["concept_id"])` as the fifth
  argument, `:1124` and `:1206` pass `target`, `:1599` becomes

  ```python
          _upsert_concept_mirror_conn(
              conn, concept_id, "work", "db", f"catalog/sources/{stable_work_id}"
          )
  ```

- [ ] Still in state.py, adapt `replace_concept_edges` (the G2S1.1/.2 body) to the
  v16 column set — the prune key and conflict target move to
  `(source_concept_id, relation_type, target_path)`, unresolved targets insert as
  pending rows, and resolution is sticky:

  ```python
  def replace_concept_edges(
      vault: Path,
      rows: Iterable[dict[str, Any]],
      *,
      paths: Iterable[str] | None = None,
  ) -> dict[str, int]:
      """Upsert the links: mirror; durable 'tension' rows are never deleted."""
      rows = list(rows)
      target_paths = {normalize_path(str(path)) for path in paths or []}
      with connect(vault) as conn:
          prepared = []
          keep = set()
          for row in rows:
              source = resolve_concept_id(conn, str(row["source_concept_id"]))
              relation = _concept_edge_relation(str(row["relation_type"]))
              target_path = normalize_path(
                  str(row.get("target_path") or row.get("target_concept_id") or "")
              )
              keep.add((source, relation, target_path))
              prepared.append((row, source, relation, target_path))
          existing = conn.execute(
              """
              SELECT source_concept_id, relation_type, target_path, source_path
              FROM concept_edges
              WHERE relation_type != 'tension'
              """
          ).fetchall()
          deleted = 0
          for stale in existing:
              key = (
                  str(stale["source_concept_id"]),
                  str(stale["relation_type"]),
                  str(stale["target_path"]),
              )
              if key in keep:
                  continue
              if target_paths and str(stale["source_path"]) not in target_paths:
                  continue
              conn.execute(
                  """
                  DELETE FROM concept_edges
                  WHERE source_concept_id = ? AND relation_type = ? AND target_path = ?
                  """,
                  key,
              )
              deleted += 1
          for row, source, relation, target_path in prepared:
              target_row = conn.execute(
                  "SELECT concept_id FROM concepts WHERE path = ? OR concept_id = ?",
                  (target_path, target_path.removeprefix("catalog/sources/")),
              ).fetchone()
              target_id = str(target_row["concept_id"]) if target_row else None
              edge_id = concept_edge_id(source, relation, target_id) if target_id else ""
              conn.execute(
                  """
                  INSERT INTO concept_edges(
                      edge_id,
                      source_concept_id,
                      relation_type,
                      target_concept_id,
                      target_path,
                      attributes_json,
                      check_status,
                      source_path,
                      updated_at
                  )
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                  ON CONFLICT(source_concept_id, relation_type, target_path)
                  DO UPDATE SET
                      edge_id = CASE
                          WHEN excluded.edge_id != '' THEN excluded.edge_id
                          ELSE concept_edges.edge_id
                      END,
                      target_concept_id = COALESCE(
                          excluded.target_concept_id, concept_edges.target_concept_id
                      ),
                      check_status = excluded.check_status,
                      source_path = excluded.source_path,
                      updated_at = excluded.updated_at
                  """,
                  (
                      edge_id,
                      source,
                      relation,
                      target_id,
                      target_path,
                      str(row.get("attributes_json") or "{}"),
                      _check_status(str(row.get("check_status") or "unchecked")),
                      normalize_path(str(row.get("source_path") or "")),
                      now_iso(),
                  ),
              )
      return {"deleted": int(deleted), "inserted": len(rows)}
  ```

  (`attributes_json` stays absent from `DO UPDATE SET`, preserving G2S1.2's
  hung-attribute guarantee.) Add the minimal resolver it calls, next to
  `_concept_edge_relation`:

  ```python
  def resolve_concept_id(conn: sqlite3.Connection, ref: str) -> str:
      """Canonical concepts key for a path-or-id reference (v16 identity)."""
      rel = normalize_path(ref)
      row = conn.execute(
          "SELECT concept_id FROM concepts WHERE concept_id = ? OR path = ?",
          (rel, rel),
      ).fetchone()
      if row is not None:
          return str(row["concept_id"])
      return rel.removeprefix("catalog/sources/")
  ```

- [ ] Add `target_path` to both SELECT column lists in `state.concept_edges`
  (both branches; `:2055-2076` pre-Plan-22 numbering, post-G2S1.2 they already list
  `edge_id, attributes_json`).
- [ ] Update the G2S1.1 mirror test in `tests/test_query_substrate.py`
  (`test_concept_edges_mirror_links_and_persist_across_reindex`): the direct tension
  INSERT gains the `target_path` column —

  ```python
          conn.execute(
              "INSERT INTO concept_edges("
              " edge_id, source_concept_id, relation_type, target_concept_id,"
              " target_path, check_status, source_path, updated_at)"
              " VALUES ('', 'notes/alpha.md', 'tension', 'notes/beta.md',"
              " 'notes/beta.md', 'checked', '', '2026-07-15T00:00:00Z')"
          )
  ```

  and the triple assertions read the path key —

  ```python
      assert {
          (edge["source_concept_id"], edge["relation_type"], edge["target_path"])
          for edge in edges
      } == {
          ("notes/alpha.md", "supports", "notes/beta.md"),
          ("notes/alpha.md", "contradicts", "notes/gamma.md"),
      }
  ```

  (`notes/gamma.md` does not exist, so its row is now pending:
  `target_concept_id` NULL, `target_path` retained — clause 6 preserves G2S1.1's
  mirror-dangling acceptance under v16. Add one assertion making that explicit:
  `assert {e["target_path"]: e["target_concept_id"] for e in edges}["notes/gamma.md"] is None`.)
- [ ] Bump the version pins: `tests/test_schema_version.py` — rename
  `test_schema_lands_at_user_version_15` to `test_schema_lands_at_user_version_16`
  and change both `15`s to `16`; `tests/test_query_substrate.py:31`
  `state.SCHEMA_VERSION == 15` → `== 16`. (`tests/test_schema_v10.py` reads
  `state.SCHEMA_VERSION` after G2S1.2 — no change.)
- [ ] Run
  `python -m pytest tests/test_schema_v16_identity.py tests/test_schema_version.py tests/test_query_substrate.py tests/test_runtime_state.py -v`
  — expect PASS.
- [ ] Run `python scripts/verify` — expect PASS.
- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/schema.sql src/memoria_vault/runtime/state.py tests/test_schema_v16_identity.py tests/test_schema_version.py tests/test_query_substrate.py tests/conftest.py
  git commit -m "feat(schema): v16 identity re-key — concepts.path attribute, real FKs, pending edges, bare-endpoint triggers

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task NID-B.2: write file Concept identities from frontmatter ULIDs

> **Binding amendment from NID-B.1's review (2026-07-31) — implement before the rest of
> B.2.** B.1's `ensure_concept_parent_conn` collision guard conflates *identity collision*
> with *attribute update*. It refuses `ensure_concept_parent_conn(conn, <same ULID>,
> path="notes/new.md")` over a resident at `notes/old.md` — same identity, the requested
> path owned by nobody — which is a **rename**, not a collision. It likewise refuses an
> in-place `concept_type` change at an unchanged path, and one such row rolls back the
> entire `rebuild_file_concept_mirror` batch.
>
> Neither is reachable under B.1: `_validate_concept` (`trusted_writer.py:1203-1205`) ties
> every document type to its folder home, so `concept_type` is a function of the path; and
> file Concepts key by path, so id and path move together and a rename mints a new id.
> **B.2 destroys both properties** — decoupling id from path is its entire job — so B.2
> hits this on its first re-key. Add a "same resolved id, requested path unowned → update"
> allowance to the guard before anything else in this task.
>
> Related (Minor): `set_concept_flag` on an unmirrored ref fails with a bare
> `sqlite3.IntegrityError: FOREIGN KEY constraint failed`. Route it through the same
> descriptive-error wording while you are in there.

> **Binding amendment from NID-B.2's review (2026-07-31) — coordinator-authorized
> DDL exception, plus two guard rulings.** B.2's decoupling silently invalidated
> three `path == id` assumptions living outside its diff. All three close inside
> B.2; none may be deferred.
>
> 1. **The verdict→edge demotion trigger (DDL, authorized).**
>    `concept_verdicts_edge_demotion_insert`/`_update` demoted a Concept's outgoing
>    mirror edges with `WHERE source_path = NEW.concept_id` — a **path** column
>    compared against an **identity**. That held only while B.1 keyed file Concepts
>    by path; every ULID-keyed Concept demoted nothing, so in a real vault each
>    demotion or quarantine left its edges at `checked` — precisely the incremental
>    window (no full `rebuild_passage_index`) the trigger exists to close. The
>    predicate becomes `source_concept_id = NEW.concept_id`, keeping
>    `source_path != ''` as the mirrored-edge scope. **The coordinator authorizes
>    this one DDL change against B.2's "does not alter schema DDL" boundary:**
>    amend `schema.sql` in place within v16 on the unmerged branch — no
>    `SCHEMA_VERSION` bump, no `MIGRATIONS` entry, no backfill. Leaving a dead
>    safety trigger in the floor for a later task to trip over was the worse
>    option. Its test fixture must author a ULID: a fixture writing no `id` keys by
>    path and can no longer prove the trigger fires.
> 2. **Two files, one ULID (batch duplicate).** `cp` or Obsidian's "Make a copy"
>    duplicates the frontmatter `id`. Per call each row reads as *same id,
>    requested path unowned* — the rename the amendment above allows — so the
>    duplicate is visible only in the batch, where the survivor is decided by
>    directory order and the loser's PI verdict lands on unreviewed content.
>    `rebuild_file_concept_mirror` refuses a repeated `concept_id` within one
>    batch, naming both paths and the shared id. This is the dual of *two
>    identities claiming one path*, which the guard already refuses, and it costs
>    nothing in expressiveness.
> 3. **Path key → ULID is identity assignment, not collision.** The mirror
>    tolerantly observes an id-less file, which keys by its own path; when that
>    same path later authors a valid ULID, the Execution replacement's no-re-key
>    rule aborted the whole batch and left `memoria workspace rebuild` permanently
>    failing with no supported command able to move the row. **Ruling:** when the
>    resident row's `concept_id` equals its own `path` (a still-provisional B.1
>    key) and the incoming row claims that same path with a valid ULID nothing else
>    holds, the row takes that identity in place; the v16 FKs carry its verdict,
>    flags and edges. Every genuine collision still refuses.
>
> **Known interim regression (owner: ERP-A.6).** `graph_sql.neighborhood` joins
> `source_status.concept_id = edge.source_path`, mixing identity and path space, so
> from B.2 until ERP-A.6 ("identity-safe path projection") lands, `memoria explore`
> / the `explore.read` surface loses neighborhood expansion (`explore.py` →
> `explore_topic` → `engine/api.py`) and edge display (`explore._edges_by_concept`)
> for every ULID-keyed Concept. `graph_sql.filter_ids` carries the same defect with
> no `src/` caller yet. Deliberately deferred, not fixed here; both sites carry the
> in-source comment naming ERP-A.6.

B.2 consumes B.1's safe v16 floor. Beyond the one authorized demotion-trigger
predicate above it does not alter schema DDL, version pins,
catalog-parent setup, mirror-pruning/tombstone rules, catalog status/verdict
resolution, or scoped-edge semantics. Fresh file Concepts are keyed from their
frontmatter ULIDs on first write; it performs no path-key re-key or reconciliation.

**Files:**
- Modify: `src/memoria_vault/runtime/state.py` — `_concept_key_for_file` and the
  B.1 mirror upsert path; do not add `_rekey_concept_conn`.
- Modify: `src/memoria_vault/runtime/trusted_writer.py` — registry-aware contract
  load and id-carrying file-mirror rows.
- Modify: `tests/test_schema_v16_identity.py`, `tests/test_runtime_state.py`, and
  `tests/test_operation_context.py`.

**Interfaces:**
- Consumes: B.1 normalizer, parent helper, registry-normalizing safe mirror/pruning,
  and status/verdict resolution.
- Produces: `_concept_key_for_file(vault, path, payload_text="") -> str` and a
  direct identity-keyed mirror upsert. A valid ULID becomes the file Concept id;
  non-ULID identities remain their B.1 path keys. Catalog works remain bare ids.

> **Execution replacement:** create a new row with its final identity on first
> observation. All later path-key reconciliation and re-key checklist text is
> historical only and must not be executed.

**Steps:**

- [x] Add RED tests proving that a note/hub/project row keyed by its provisional path
  re-keys to its valid frontmatter ULID on observation, carries verdicts/flags/edges
  through their required update paths, and retains its path. Verdicts and edges carry
  through FK `ON UPDATE CASCADE`; `_rekey_concept_conn` moves flags manually because
  `concept_flags` intentionally has no FK. Test both `derivations.input_id` and
  `derivations.output_id` when each names the re-keyed Concept. A conflicting target
  path or collapsed flag/derivation raises rather than using `UPDATE OR REPLACE`. Add a test
  that every resolved incident edge receives the recomputed
  `concept_edge_id(source_concept_id, relation_type, target_concept_id)` after that
  cascade (a pending edge remains `edge_id == ''`). Add a test
  that a fulltext and code-artifact mirror uses `schema.concept_type_for` (`work` and
  `project`, respectively), while `strict_writer=False` remains tolerant enough to
  observe untrusted external files.

  Update `tests/test_operation_context.py` cases that currently assert a path-keyed
  `derivations.output_id` or a catalog `/source.md` input: first create the referenced
  catalog row with `state.upsert_catalog_record(..., work_id="source-a", ...)`, look
  up the staged note's canonical frontmatter ULID, and assert the derivation pair is
  `("source-a", note_ulid)`.

- [x] Run the focused tests and confirm the ULID row is absent before implementation:

  ```bash
  python -m pytest tests/test_schema_v16_identity.py tests/test_runtime_state.py tests/test_operation_context.py -v
  ```

- [x] Implement file-key derivation and collision-safe re-keying. A valid ULID wins;
  otherwise keep the normalized path. The in-transaction re-key must reject a
  conflicting target id, flag, or derivation before changing rows:

  ```python
  def _concept_key_for_file(vault: Path, path: str, payload_text: str = "") -> str:
      text = payload_text or safe_read(vault / path)
      frontmatter = parse_frontmatter(text)
      raw_id = str(frontmatter.get("id") or "")
      return raw_id if is_ulid(raw_id) else normalize_path(path)
  ```

  Extend B.1's `_upsert_concept_mirror_conn` to look up a different row with the same
  `path`: re-key a provisional path-keyed row, release a genuinely renamed row's path,
  then upsert the requested row. After the FK cascade, recompute `edge_id` for every
  resolved edge incident to the old or new id; leave pending edges at `''`. Do not
  restore a wipe-and-refill implementation. Before changing the parent id,
  `_rekey_concept_conn` checks for conflicting `(new_id, flag)` and collapsed
  derivation rows; it then moves `concept_flags` manually and rewrites **both**
  `derivations.input_id` and `derivations.output_id` occurrences. `outputs` and
  materialization-payload tables remain path keyed and are not derivation endpoints.

- [x] Make trusted-writer mirror inputs registry-aware. `_load_contract` uses
  `schema.load_types` / `schema.concept_type_for` rather than manually trusting the
  raw document `type`; mirror rows carry `concept_id`, mapped `concept_type`, and
  normalized `path`. Preserve `strict_writer=False` as tolerant observation behavior:
  it records an unchecked external file rather than treating that path as a valid
  authored write.

- [x] Route `record_file_output` and `record_observed_file_edit` through
  `_concept_key_for_file`; write/re-key **both** derivation endpoints through B.1's
  resolver, while keeping `outputs` and materialization payloads path-keyed. Do not move B.1's parent
  ensuring, pruning, catalog alias, or status semantics back into this task.

- [x] Run focused suites and the gate:

  ```bash
  python -m pytest tests/test_schema_v16_identity.py tests/test_runtime_state.py tests/test_operation_context.py -v
  python scripts/verify
  ```

  Expected: all tests pass and `verify: OK`.

- [x] Commit only ULID-reconciliation changes:

  ```bash
  git add src/memoria_vault/runtime/state.py src/memoria_vault/runtime/trusted_writer.py \
          tests/test_schema_v16_identity.py tests/test_runtime_state.py \
          tests/test_operation_context.py
  git commit -m "feat(state): reconcile file concepts by frontmatter identity"
  ```

---

### Archived NID-B.2 drafting record (do not execute)

The following original draft predates the B.1 safety-floor transfer. Its mirror-prune,
parent/status resolution, and catalog instructions now belong solely to revised NID-B.1;
only the revised B.2 task above is executable.

Runtime writers stop keying file concepts by path: the mirror carries the
frontmatter ULID (uniform rule: ULID when the `id` is one, else the path; catalog
works bare `work_id` — landed in NID-B.1), and every verdict/flag/status seam
resolves a path-or-id reference to the canonical key. Legacy path-keyed rows
(post-v16 provisional keys) re-key in place when the mirror observes the file —
FK `ON UPDATE CASCADE` carries verdicts and edges with them.

> **B.1 handoff (adopted):** B.1 owns mirror upsert-and-prune/tombstones, parent
> ensuring for FK-backed writes, canonical status/verdict resolution, and legacy
> `./` normalization. B.2 builds on those guarantees for ULID re-key and
> reconcile-by-path, without restoring wipe-and-refill or path-keyed catalog identities.

**Files:**
- Modify: `src/memoria_vault/runtime/state.py` — `_upsert_concept_mirror_conn`
  (NID-B.1 shape) gains reconcile-by-path; new `_rekey_concept_conn`; new
  `_concept_key_for_file`; `rebuild_file_concept_mirror` (`:1092-1103`) becomes
  upsert-and-prune; `set_concept_verdict` (`:1047-1060`), `concept_check_status`
  (`:1063-1072`), `mark_checked` (`:1175-1194`), `set_concept_flag` (`:1295-1315`),
  `concept_flags` (`:1318-1339`), `note_curation_status` (`:1342`) resolve their
  ref; `record_file_output` (`:1106-1172`) and `record_observed_file_edit`
  (`:1197-1230`) derive the frontmatter key; `_set_concept_verdict_conn`
  (`:3371-3385`) and `_cascade_passage_check_status_conn` (`:3388-3403`) use the
  resolved key and the bare-endpoint predicate; extend the vaultio import (`:36`)
  with `is_ulid, parse_frontmatter, safe_read`
- Modify: `src/memoria_vault/runtime/trusted_writer.py:608-629`
  (`rebuild_concept_mirror_from_files` rows carry id + path)
- Modify: `tests/test_runtime_state.py:259-300` (wipe-count assertions →
  upsert-and-prune counts)
- Test: `tests/test_schema_v16_identity.py`

**Interfaces:**
- Consumes: NID-B.1's DDL, `resolve_concept_id`, `_upsert_concept_mirror_conn(…, path)`;
  `vaultio.is_ulid` (`vaultio.py:144`), `vaultio.parse_frontmatter` (`:53`),
  `vaultio.safe_read` (`:37`); `tests.helpers.write_checked_concept`,
  `copy_memoria_dirs`.
- Produces:
  - `state._rekey_concept_conn(conn: sqlite3.Connection, old_id: str, new_id: str) -> None`
    — re-keys one concepts row; FK `ON UPDATE CASCADE` carries verdicts and edge
    endpoints; flags/derivations/passages re-keyed explicitly; affected edge rows
    get `edge_id = ''` for restamping at the next mirror pass.
  - `state._concept_key_for_file(vault: Path, target: str, payload_text: str = "") -> str`
    — frontmatter `id` when it is a ULID, else `target`.
  - `state.rebuild_file_concept_mirror(vault, rows) -> dict[str, int]` — rows are
    `{"concept_id": <id>, "concept_type": <type>, "path": <vault path>}`;
    upsert-and-prune; **prunes only `store='file'` rows with no verdict row**
    (verdict-carrying tombstones survive — SPEC GAP note above).
  - Resolution contract: every public verdict/flag/status function accepts a path,
    a `catalog/sources/<work_id>` rendering, or a canonical id, and canonicalizes
    via `resolve_concept_id`.

**Steps:**

- [ ] Append the failing tests to `tests/test_schema_v16_identity.py`:

  ```python
  from tests.helpers import copy_memoria_dirs, write_checked_concept


  def test_file_concepts_key_by_frontmatter_ulid(tmp_path: Path) -> None:
      copy_memoria_dirs(tmp_path, "schemas")
      write_checked_concept(
          tmp_path,
          "notes/alpha.md",
          f"type: note\nid: {ULID_A}\ntitle: Alpha\ntags: []\nlinks: {{}}\n",
      )
      with state.connect(tmp_path) as conn:
          row = conn.execute(
              "SELECT concept_id, path FROM concepts WHERE concept_id = ?", (ULID_A,)
          ).fetchone()
          verdict = conn.execute(
              "SELECT check_status FROM concept_verdicts WHERE concept_id = ?", (ULID_A,)
          ).fetchone()
      assert row["path"] == "notes/alpha.md"
      assert verdict["check_status"] == "checked"
      # Path references resolve to the id-keyed row.
      assert state.concept_check_status(tmp_path, "notes/alpha.md") == "checked"


  def test_legacy_path_keyed_row_rekeys_on_mirror_observation(tmp_path: Path) -> None:
      copy_memoria_dirs(tmp_path, "schemas")
      path = tmp_path / "notes/alpha.md"
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text(
          f"---\ntype: note\nid: {ULID_A}\ntitle: Alpha\ntags: []\nlinks: {{}}\n---\nBody.\n",
          encoding="utf-8",
      )
      # Simulate a post-v16 provisional row: keyed by path, verdict attached.
      with state.connect(tmp_path) as conn:
          conn.execute(
              "INSERT INTO concepts(concept_id, concept_type, store, path)"
              " VALUES ('notes/alpha.md', 'note', 'file', 'notes/alpha.md')"
          )
          conn.execute(
              "INSERT INTO concept_verdicts(concept_id, check_status)"
              " VALUES ('notes/alpha.md', 'checked')"
          )

      from memoria_vault.runtime.trusted_writer import rebuild_concept_mirror_from_files

      rebuild_concept_mirror_from_files(tmp_path)

      with state.connect(tmp_path) as conn:
          rows = conn.execute(
              "SELECT concept_id, path FROM concepts WHERE path = 'notes/alpha.md'"
          ).fetchall()
          verdict = conn.execute(
              "SELECT check_status FROM concept_verdicts WHERE concept_id = ?", (ULID_A,)
          ).fetchone()
      assert [str(row["concept_id"]) for row in rows] == [ULID_A]
      assert verdict["check_status"] == "checked"
  ```

- [ ] Run
  `python -m pytest tests/test_schema_v16_identity.py::test_file_concepts_key_by_frontmatter_ulid tests/test_schema_v16_identity.py::test_legacy_path_keyed_row_rekeys_on_mirror_observation -v`
  — expect FAIL: first test `AssertionError` because the concepts row for the ULID
  does not exist (`record_observed_file_edit` still keys by path — `row is None` →
  `TypeError: 'NoneType' object is not subscriptable`); second test finds
  `['notes/alpha.md']` instead of the ULID.
- [ ] In `src/memoria_vault/runtime/state.py`, extend the vaultio import (`:36`):

  ```python
  from memoria_vault.runtime.vaultio import is_ulid, parse_frontmatter, safe_read, write_text_durable
  ```

  Add next to `resolve_concept_id`:

  ```python
  def _concept_key_for_file(vault: Path, target: str, payload_text: str = "") -> str:
      """Canonical concepts key for a file concept: frontmatter ULID, else path."""
      text = payload_text or safe_read(Path(vault) / target)
      raw_id = str(parse_frontmatter(text).get("id") or "")
      return raw_id if is_ulid(raw_id) else target


  def _rekey_concept_conn(conn: sqlite3.Connection, old_id: str, new_id: str) -> None:
      """Re-key one concept; FK ON UPDATE CASCADE carries verdicts and edges."""
      if old_id == new_id:
          return
      conn.execute(
          "UPDATE concepts SET concept_id = ? WHERE concept_id = ?", (new_id, old_id)
      )
      conn.execute(
          "UPDATE OR REPLACE concept_flags SET concept_id = ? WHERE concept_id = ?",
          (new_id, old_id),
      )
      conn.execute(
          "UPDATE OR REPLACE derivations SET input_id = ? WHERE input_id = ?",
          (new_id, old_id),
      )
      conn.execute(
          "UPDATE OR REPLACE derivations SET output_id = ? WHERE output_id = ?",
          (new_id, old_id),
      )
      conn.execute(
          "UPDATE passages SET concept_id = ? WHERE concept_id = ?", (new_id, old_id)
      )
      # Endpoints moved under the edge rows via FK cascade; blank their edge_ids
      # so the next mirror pass restamps them over the new triple.
      conn.execute(
          "UPDATE concept_edges SET edge_id = ''"
          " WHERE source_concept_id = ? OR target_concept_id = ?",
          (new_id, new_id),
      )
  ```

  Extend `_upsert_concept_mirror_conn` with reconcile-by-path (insert before the
  INSERT statement):

  ```python
      stale = conn.execute(
          "SELECT concept_id FROM concepts WHERE path = ? AND concept_id != ?",
          (path, concept_id),
      ).fetchone()
      if stale is not None:
          if str(stale["concept_id"]) == path:
              # Post-v16 provisional row (keyed by its own path): re-key to the id.
              _rekey_concept_conn(conn, path, concept_id)
          else:
              # A different concept held this path (rename + reuse); release the
              # claim — its own upsert reconciles its path by id.
              conn.execute(
                  "UPDATE concepts SET path = '' WHERE concept_id = ?",
                  (str(stale["concept_id"]),),
              )
  ```

- [ ] Replace `rebuild_file_concept_mirror` (`:1092-1103`) with upsert-and-prune:

  ```python
  def rebuild_file_concept_mirror(vault: Path, rows: Iterable[dict[str, str]]) -> dict[str, int]:
      rows = list(rows)
      with connect(vault) as conn:
          keep = set()
          for row in rows:
              concept_id = str(row["concept_id"])
              keep.add(concept_id)
              _upsert_concept_mirror_conn(
                  conn,
                  concept_id,
                  str(row["concept_type"]),
                  "file",
                  normalize_path(str(row.get("path") or row["concept_id"])),
              )
          stale = conn.execute(
              """
              SELECT c.concept_id FROM concepts c
              LEFT JOIN concept_verdicts v ON v.concept_id = c.concept_id
              WHERE c.store = 'file' AND v.concept_id IS NULL
              """
          ).fetchall()
          deleted = 0
          for row in stale:
              concept_id = str(row["concept_id"])
              if concept_id in keep:
                  continue
              conn.execute("DELETE FROM concept_flags WHERE concept_id = ?", (concept_id,))
              conn.execute("DELETE FROM concepts WHERE concept_id = ?", (concept_id,))
              deleted += 1
      return {"deleted": int(deleted), "inserted": len(rows)}
  ```

  (Edge rows from a deleted source cascade away; inbound edges revert to pending
  via `ON DELETE SET NULL` — clause 6.)
- [ ] In `trusted_writer.py` `rebuild_concept_mirror_from_files` (`:608-629`),
  extend the vaultio import with `is_ulid` and build id-carrying rows — replace the
  `rows.append(...)` line (`:628`) with:

  ```python
              raw_id = str(frontmatter.get("id") or "")
              rows.append(
                  {
                      "concept_id": raw_id if is_ulid(raw_id) else target,
                      "concept_type": str(frontmatter["type"]),
                      "path": target,
                  }
              )
  ```

- [ ] Route the verdict/flag/status seams through resolution. In
  `_set_concept_verdict_conn` (`:3371-3385`) and
  `_cascade_passage_check_status_conn` (`:3388-3403`), resolve first and use the
  bare-endpoint predicate matching the v16 triggers:

  ```python
  def _set_concept_verdict_conn(
      conn: sqlite3.Connection,
      concept_id: str,
      check_status: str,
  ) -> None:
      target = resolve_concept_id(conn, concept_id)
      conn.execute(
          """
          INSERT INTO concept_verdicts(concept_id, check_status)
          VALUES (?, ?)
          ON CONFLICT(concept_id) DO UPDATE SET
              check_status = excluded.check_status
          """,
          (target, _check_status(check_status)),
      )
      _cascade_passage_check_status_conn(conn, target, check_status)


  def _cascade_passage_check_status_conn(
      conn: sqlite3.Connection,
      concept_id: str,
      check_status: str,
  ) -> None:
      status = _check_status(check_status)
      target = resolve_concept_id(conn, concept_id)
      conn.execute(
          """
          UPDATE passages
          SET check_status = ?
          WHERE concept_id = ?
             OR work_id = ?
             OR path = (SELECT path FROM concepts WHERE concept_id = ?)
          """,
          (status, target, target, target),
      )
  ```

  In `set_concept_verdict` (`:1047-1060`), `set_concept_flag` (`:1295-1315`),
  `concept_flags` (`:1318-1339`), and `note_curation_status` (`:1342`), replace
  `target = normalize_path(concept_id)` with a resolved key inside the connection
  block: `target = resolve_concept_id(conn, concept_id)` (for `concept_flags` and
  `note_curation_status`, which open their own connections, resolve after
  `connect`; for `set_concept_verdict`, resolve once and reuse for the outputs
  UPDATE and flag delete). In `concept_check_status` (`:1063-1072`) resolve inside
  the `with connect(...)` block before the SELECT. In `mark_checked` (`:1175-1194`)
  resolve for the verdict/flag statements while keeping the raw `target` for the
  `outputs`/`materialization_payloads` statements (outputs stay path-keyed).
- [ ] In `record_file_output` (`:1106-1172`): compute
  `key = _concept_key_for_file(vault, target, payload_text)` and pass it to the
  mirror upsert and verdict set —

  ```python
          key = _concept_key_for_file(vault, target, payload_text)
          _upsert_concept_mirror_conn(conn, key, concept_type, "file", target)
          _set_concept_verdict_conn(conn, key, _check_status(check_status))
  ```

  and resolve derivation inputs:
  `(resolve_concept_id(conn, input_id), target, context.actor)` in the derivations
  INSERT (`:1164-1172`). In `record_observed_file_edit` (`:1197-1230`) do the same
  with `key = _concept_key_for_file(vault, target)`.
- [ ] Update `tests/test_runtime_state.py:259-300`
  (`test_rebuild_concept_mirror_from_files_does_not_trust_frontmatter_status`):
  the two `rebuilt["deleted"]` assertions become `== 0` (upsert-and-prune never
  wipes; the forged note's `id: notes/forged` is not a ULID, so the row still keys
  as `notes/forged.md` and every existing lookup in the test keeps working). Keep
  all verdict assertions unchanged — they are the point of the test.
- [ ] Run
  `python -m pytest tests/test_schema_v16_identity.py tests/test_runtime_state.py -v`
  — expect PASS.
- [ ] Run `python scripts/verify` — expect PASS (this sweep exercises every
  verdict-writing flow against the FKs; any caller that sets a verdict without a
  mirror row is a genuine FK bug this task must fix at that call site by
  upserting the mirror first, not by relaxing the FK).
- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/state.py src/memoria_vault/runtime/trusted_writer.py tests/test_schema_v16_identity.py tests/test_runtime_state.py
  git commit -m "feat(state): concepts key by frontmatter identity — resolution seams + reconcile-by-path

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task NID-B.3: ratify the hub/project `id: ulid` requirement with guard tests (clause 1)

Verified at 9c77ba61: `hub.yaml:5` and `project.yaml:5` already require `id: ulid`
(alongside `note.yaml:10`), and `vaultio.universal_concept_frontmatter_errors`
(`vaultio.py:123-134`) already rejects non-ULID ids for all non-digest/fulltext
universal types. Clause 1's extension is shipped but nothing pins it — a yaml edit
could silently drop the requirement. This task adds the guard tests only.

**Files:**
- Test: `tests/test_schema_v16_identity.py`
- Consult (no modification expected):
  `src/memoria_vault/product/workspace_seed/.memoria/schemas/types/{note,hub,project}.yaml`

**Interfaces:**
- Consumes: `schema.load_types(schemas_dir=None)`
  (`subsystems/lib/schema.py:50-56`), `schema.validate_frontmatter`
  (`:161-209`), `vaultio.universal_concept_frontmatter_errors` (`vaultio.py:123`).
- Produces: guard test `test_ulid_identity_required_for_note_hub_project` — fails
  on any roster drift away from `id: ulid` in the three seeded type yamls.

**Steps:**

- [x] Append to `tests/test_schema_v16_identity.py`:

  ```python
  def test_ulid_identity_required_for_note_hub_project() -> None:
      from memoria_vault.runtime.subsystems.lib.schema import load_types, validate_frontmatter
      from memoria_vault.runtime.vaultio import universal_concept_frontmatter_errors

      types = load_types()
      for type_name in ("note", "hub", "project"):
          assert types[type_name]["required"]["id"] == "ulid", type_name
          errors = validate_frontmatter(
              {
                  "type": type_name,
                  "id": "not-a-ulid",
                  "title": "T",
                  "tags": [],
                  "links": {},
                  **({"tag": "t"} if type_name == "hub" else {}),
              },
              types[type_name],
          )
          assert any("expected ULID" in error for error in errors), type_name
      assert universal_concept_frontmatter_errors(
          {"type": "hub", "id": "not-a-ulid", "links": {}}, "hubs/x.md"
      ) == ["id must be a ULID"]
  ```

- [x] Run
  `python -m pytest tests/test_schema_v16_identity.py::test_ulid_identity_required_for_note_hub_project -v`
  — expected outcome: **PASS on first run** (the requirement is already seeded;
  this is a ratification guard, not new behavior). Verify it actually guards:
  temporarily change `hub.yaml:5` to `id: str`, rerun, confirm FAIL
  (`AssertionError: hub`), revert the yaml, rerun, confirm PASS.
- [x] Run `python scripts/verify` — expect PASS.
- [x] Commit:

  ```
  git add tests/test_schema_v16_identity.py
  git commit -m "test(schema): guard the seeded id:ulid requirement on note/hub/project types

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

**Post-merge amendment (review escape, closed):** the guard test above only ever
drove `universal_concept_frontmatter_errors` with `type: "hub"`; `note` and
`project` were pinned only through `schema.load_types`/`validate_frontmatter`,
never through the vaultio validator. That let a one-line widening of the
`{"digest", "fulltext"}` exclusion set (to include `"project"`, or to include
`"note"`) pass all 36 tests in the file — the linter/pre-commit-facing check
would silently stop requiring a ULID for that type while the schema-layer check
kept passing, and no other test in the repo references the function. Review
found the gap; `test_ulid_identity_required_for_note_hub_project` was widened
to loop `universal_concept_frontmatter_errors` over all three of
`note`/`hub`/`project`, not just `hub`. The negative-direction guard
(`test_digest_and_fulltext_accept_non_ulid_ids`) was unaffected and still
covers the dropped-exclusion-set mutation.

---

### Task NID-B.4: indexer path→id resolution + reconcile-by-id on rename (clause 3)

Reindex becomes the reconciliation pass the spec names: it rebuilds the concept
mirror first (so a renamed file's row reconciles its `path` by frontmatter-id
match before anything reads statuses), emits `passages.concept_id` in the new
id-space, and derives concept-edge rows whose source is the frontmatter id and
whose target is a `target_path` for `replace_concept_edges` to resolve.

> **Amendment — the reconcile also carries the `outputs` path key (2026-07-31,
> ruling recorded as issue #1584).** The three `indexing.py` edits below are not
> sufficient for this task's own acceptance test. Rebuilding the mirror first
> clears the identity-aware `state.concept_check_status` gate in
> `search_index.checked_search_universe` (`search_index.py:134`) but not the read
> barrier on the next line: `is_consumable_checked_file` → `state.output_record`
> (`read_barrier.py:19`) looks up the **path-keyed** `outputs` table at the file's
> **new** path, finds nothing after an out-of-band rename, and drops the renamed
> file from the passage universe — so no passage row and no mirrored edge is
> produced. Its refusal then enqueues `observe-pi-edits`, which
> `record_observed_file_edit` would use to demote the surviving verdict to
> `unchecked`. So the shipped behaviour was: an out-of-band rename strips a
> checked note from search and then un-checks it.
>
> **Resolution:** `state.rebuild_file_concept_mirror` reconciles the `outputs`
> path key alongside `concepts.path`, via `_reconcile_renamed_output_conn` — one
> `UPDATE OR REPLACE outputs SET output_id = ?, target_path = ?`, the same
> statement NID-B.5 issues in-band, applied to the out-of-band pass. Rationale:
> NODES §7 ("a rename leaves every DB row, edge, and verdict attached") is the
> product requirement, and §1.5 ("`memoria mv` is a convenience, not a correctness
> requirement") *reinforces* fixing it here — fixing only NID-B.5's in-band seam
> would satisfy `mv` while leaving the exact case §1.5 says must work broken.
> NID-B.2's "outputs stay path-keyed" constrains the **key shape**, not whether
> that key follows the file: updating a path key to the file's new path keeps the
> table path-keyed and does not re-key it to an identity. NID-B.5's in-band seam
> is untouched and still owns `output_id`.
>
> **The trust perimeter does not widen, and that is asserted.** The barrier's
> sha256 comparison still runs against the file at its new path, so a rename *and*
> edit landing in **one** reindex pass is still refused.
> `test_rename_reconciliation_still_refuses_edited_content` guards exactly that
> one-pass case, proven load-bearing by mutation (make the reconcile refresh
> `output_sha256` from the file at the new path — the laundering bug — and only
> that test fails).
>
> **Corrected 2026-07-31 — the claim above was originally written without the
> "one pass" qualifier, which overstated it.** A *two-pass* sequence (rename →
> reindex → edit → reindex) is not refused: `indexing._previously_indexed_documents`
> (`indexing.py:84-102`) re-indexes any path whose `concept_check_status` is
> `checked` **without** calling `is_consumable_checked_file`, so no sha256
> comparison happens. That bypass is pre-existing and identical on the pre-B.4
> baseline — B.4 restores a renamed file to exactly the standing of a never-renamed
> file, so the perimeter is genuinely unwidened; only the wording was too broad.
>
> **Two behavioural changes this task ships, recorded so they are not discovered
> later:** (1) reindex now hard-depends on `.memoria/schemas/concept-types.yaml`,
> because `rebuild_concept_mirror_from_files` calls `_load_contract` →
> `schema.load_types`, which raises
> `ValueError("missing required concept-types.yaml")` without it. (Corrected
> 2026-07-31: this note originally said the dependency was on the seeded
> `.memoria/schemas` tree as a whole. `search_index._bundle_roots`
> (`search_index.py:525-528`) already read `.memoria/schemas/folders.yaml`
> unconditionally before B.4, so the tree was already required; the registry file
> is the new part.) (2) `rebuild_file_concept_mirror`'s prune — deleting
> `store='file'` Concepts absent from the batch that carry no verdict — now runs on
> **every** reindex, not only on `memoria workspace rebuild`.
>
> **Defect fixed 2026-07-31 — `materialization_payloads` needed `ON UPDATE
> CASCADE`.** `_reconcile_renamed_output_conn` mutates the `outputs` primary key
> while `materialization_payloads.output_id` still references the old value. That
> FK (`schema.sql`) was declared `ON DELETE CASCADE` only, so its `ON UPDATE`
> default of `NO ACTION` plus `PRAGMA foreign_keys = ON` (`state.py`) made the
> reconcile raise `sqlite3.IntegrityError: FOREIGN KEY constraint failed` for any
> file Concept written through `state.record_file_output` — i.e. every
> machine-authored note, digest and hub, since `trusted_writer.stage_concept` is
> that write and nothing ever deletes the payload row. Reindex stayed dead until
> the file was renamed back, including `memoria workspace rebuild`, the repair verb
> itself. The whole rename suite missed it because `tests/helpers`'
> `write_checked_concept` builds its fixture through `record_observed_file_edit`,
> which writes an `outputs` row and no payload child — the one shape where the
> statement is safe. **Fix:** add `ON UPDATE CASCADE` to that FK. Fresh-schema-legal
> (v16 is NID-B's own allocation, no installations exist, and the 2026-07-30
> fresh-install amendment permits amending the current DDL in place), so no
> `SCHEMA_VERSION` bump and no migration. Guarded by
> `test_rename_reconciliation_carries_the_writer_materialization_payload`, whose
> fixture goes through `stage_concept` → `promote_checked` → `mark_materialized`.
> This also pre-fixes NID-B.5: its drafted `update_concept_path` issues the
> byte-identical `UPDATE OR REPLACE outputs …` and would have failed identically.
>
> **Also modified beyond the Files list:** `src/memoria_vault/runtime/span_refs.py`
> (`:51`). `resolve_span_ref` queried the fulltext passage by
> `concept_id = f"catalog/sources/{work_id}"`; the `_passage_row` re-key below makes
> that column the bare `work_id` (NODES §1.7, cross-section contract 10), so the
> reader had to follow the writer. A plan gap, not a scope violation.
>
> The Commit step's `git add` line below is therefore superseded: stage
> `src/memoria_vault/runtime/{indexing,state,span_refs}.py`,
> `tests/test_query_substrate.py`, and this plan file.

**Files:**
- Modify: `src/memoria_vault/runtime/indexing.py` — `_rebuild_passage_index`
  (`:34-38`), `_passage_row` (`:101-130`, `concept_id` at `:114`), `_concept_edges`
  (as landed by G2S1.1), imports (`:10-13`)
- Test: `tests/test_query_substrate.py`

**Interfaces:**
- Consumes: NID-B.1/B.2 (`resolve_concept_id`, mirror reconcile, pending-edge
  schema); `trusted_writer.rebuild_concept_mirror_from_files` (`:608`);
  `vaultio.is_ulid`; G2S1.1's `schema.parse_links`.
- Produces:
  - `passages.concept_id` id-space: bare `work_id` for `fulltexts/` rows,
    frontmatter ULID for ULID-typed concepts, else the path.
  - Edge-row dict contract v2 (supersedes G2S1.1's): keys `source_concept_id`
    (canonical id or path — resolved downstream), `relation_type`, `target_path`
    (vault path or `catalog/sources/<work_id>` rendering), `check_status`,
    `source_path`. Consumed by ERP tasks.
  - `rebuild_passage_index` result dict gains a `"concept_mirror"` key
    (`{"deleted": int, "inserted": int}`).

**Steps:**

- [x] Append the failing rename-reconciliation test to
  `tests/test_query_substrate.py` (this is the spec §7 acceptance scenario):

  ```python
  ULID_NOTE = "01BX5ZZKBKACTAV9WEVGEMMVRZ"


  def test_rename_out_of_band_reconciles_by_frontmatter_id(tmp_path: Path) -> None:
      vault = tmp_path
      copy_memoria_dirs(vault, "schemas")
      write_checked_concept(
          vault,
          "notes/alpha.md",
          f"type: note\nid: {ULID_NOTE}\ntitle: Alpha\ntags: []\n"
          'links:\n  supports: ["[[notes/beta]]"]\n',
      )
      write_checked_concept(
          vault, "notes/beta.md", "type: note\ntitle: Beta\ntags: []\nlinks: {}\n"
      )
      rebuild_passage_index(vault)
      with state.connect(vault) as conn:
          before = conn.execute(
              "SELECT concept_id, path FROM concepts WHERE concept_id = ?", (ULID_NOTE,)
          ).fetchone()
      assert before["path"] == "notes/alpha.md"

      # Rename out-of-band: no writer, no observer — just the file move.
      (vault / "notes/alpha.md").rename(vault / "notes/alpha-renamed.md")
      rebuild_passage_index(vault)

      with state.connect(vault) as conn:
          row = conn.execute(
              "SELECT path FROM concepts WHERE concept_id = ?", (ULID_NOTE,)
          ).fetchone()
          verdict = conn.execute(
              "SELECT check_status FROM concept_verdicts WHERE concept_id = ?",
              (ULID_NOTE,),
          ).fetchone()
          edges = conn.execute(
              "SELECT source_concept_id, relation_type, target_path FROM concept_edges"
          ).fetchall()
          passage = conn.execute(
              "SELECT concept_id FROM passages WHERE path = 'notes/alpha-renamed.md'"
          ).fetchone()
      # Every DB row survives id-keyed; the path column reconciled (spec §7).
      assert row["path"] == "notes/alpha-renamed.md"
      assert verdict["check_status"] == "checked"
      assert (ULID_NOTE, "supports", "notes/beta.md") in {
          (e["source_concept_id"], e["relation_type"], e["target_path"]) for e in edges
      }
      assert passage["concept_id"] == ULID_NOTE
  ```

- [x] Run
  `python -m pytest tests/test_query_substrate.py::test_rename_out_of_band_reconciles_by_frontmatter_id -v`
  — expect FAIL: `assert passage["concept_id"] == ULID_NOTE` never reached — the
  first block already fails on the edge assertion (`source_concept_id` is
  `'notes/alpha.md'`, not the ULID) because `_passage_row` still emits path-space
  ids; treat any of the id-space assertions failing as the expected failure.
- [x] In `src/memoria_vault/runtime/indexing.py`: extend the vaultio import
  (`:13`) to `from memoria_vault.runtime.vaultio import is_ulid, parse_frontmatter, safe_read`
  and the trusted_writer import (`:12`) to include
  `rebuild_concept_mirror_from_files`. Rebuild the mirror first in
  `_rebuild_passage_index` (`:34-38`):

  ```python
  def _rebuild_passage_index(vault: Path) -> dict[str, Any]:
      # Reconcile the concept mirror first: a rename missed by any rewriter
      # re-attaches by frontmatter id here, before statuses are read (NODES §1.3).
      mirror_result = rebuild_concept_mirror_from_files(vault)
      rows = _passage_rows(vault)
      passage_result = state.replace_indexed_passages(vault, rows)
      edge_result = state.replace_concept_edges(vault, _concept_edges(rows))
      return {
          "concept_mirror": mirror_result,
          "passages": passage_result,
          "concept_edges": edge_result,
      }
  ```

- [x] In `_passage_row` (`:101-130`), replace the `concept_id` line (`:114`) with
  the id-space rule:

  ```python
      raw_id = str(frontmatter.get("id") or "")
      concept_id = (
          work_id
          if path.startswith("fulltexts/")
          else (raw_id if is_ulid(raw_id) else path)
      )
  ```

  and use `"concept_id": concept_id,` in the returned dict. (Fulltext passages key
  to the work's bare `work_id` — they inherit the work's verdict, matching the v16
  `catalog_sources` trigger; digests key by path per the SPEC GAP resolution.)
- [x] Replace `_concept_edges` (the G2S1.1 body) so edges carry the source id and a
  `target_path` (resolution is `replace_concept_edges`'s job — single owner):

  ```python
  def _concept_edges(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
      """Mirror each concept's links: frontmatter into concept_edges rows."""
      edges = []
      for row in rows:
          if row.get("origin") != "file":
              continue
          for relation, target in parse_links(row.get("links")):
              target_path = (
                  target
                  if target.endswith(".md") or target.startswith("catalog/sources/")
                  else f"{target}.md"
              )
              edges.append(
                  {
                      "source_concept_id": row["concept_id"],
                      "relation_type": relation,
                      "target_path": target_path,
                      "check_status": row["check_status"],
                      "source_path": row["path"],
                  }
              )
      return edges
  ```

- [x] Run
  `python -m pytest tests/test_query_substrate.py -v`
  — expect PASS, including the updated G2S1.1 mirror test and the two v13/v14 shape
  tests. If `test_concept_edges_mirror_links_and_persist_across_reindex` fails on
  the tension row, the direct INSERT predates the mirror rows — its fixture already
  writes both notes first; re-check the INSERT's `target_path` column from NID-B.1.
- [x] Run `python scripts/verify` — expect PASS.
- [x] Commit:

  ```
  git add src/memoria_vault/runtime/indexing.py tests/test_query_substrate.py
  git commit -m "feat(index): reindex reconciles concepts by frontmatter id; passages and edges emit id-space keys

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task NID-B.5: `move_concept` — inbound-link rewrite + path update in one trusted-writer transaction

The runtime seam behind `memoria mv` (clause 3's CLI/editor-rename cover; clause 5:
a convenience, not a correctness requirement). Renames the file, rewrites inbound
`links:` entries in every concept that references the old path (preserving the
surface form — wikilink alias/anchor or bare path), updates the DB path columns in
one transaction, and commits everything through the trusted writer.

> **Note from NID-B.4 (2026-07-31) — the out-of-band reconcile is a strict subset,
> so do not let a shared helper inherit the short version.** B.4's
> `_reconcile_renamed_output_conn` moves `concepts.path` (via the mirror upsert)
> and `outputs.output_id`/`target_path`, and that is all. `update_concept_path`
> below moves those **plus** `concept_edges.target_path`/`source_path`,
> `passages.path` and `file_index_state.path`. The one observable residue of the
> difference: after an out-of-band rename a stale `file_index_state` row survives
> at the *old* path. A full `rebuild_passage_index` pass self-heals it —
> `replace_indexed_passages` with no `paths` argument wipes `file_index_state`
> wholesale (`state.py:2058-2059`) — but `refresh_stale_passages` does not, because
> it computes its `removed` set from `state.file_index_states` and only deletes the
> paths it names (`indexing.py:53-63`). If B.5 refactors the two seams onto one
> shared helper, the helper must be the **full** statement; regressing the in-band
> path to B.4's subset would leave `passages`/`concept_edges` stranded at the old
> path after `memoria mv`.

**Files:**
- Modify: `src/memoria_vault/runtime/state.py` — new `update_concept_path` next to
  `rebuild_file_concept_mirror` (`:1092`)
- Modify: `src/memoria_vault/runtime/knowledge.py` — new `move_concept` +
  `_movable_rel` + `_rewrite_inbound_links` + `_rewrite_link_value`, placed after
  `curate_note_link` (`:414`); reuses the module's existing imports
  (`split_frontmatter`, `write_frontmatter_doc`, `read_frontmatter`,
  `append_journal_event`, `commit_writer_changes`, `sha256_file`,
  `validate_operation_context`, `state`) — add `is_ulid` to its vaultio import
- Test: `tests/test_knowledge.py`

**Interfaces:**
- Consumes: NID-B.2 (`_rekey_concept_conn`, id-keyed mirror),
  `knowledge._link_values` (`:3028-3033`), `knowledge._link_target` (`:3036-3047`),
  `trusted_writer.commit_writer_changes` (`:238`), `vaultio.iter_markdown`,
  `tests/test_knowledge.py workspace()/_md()` fixtures (`:69-73`).
- Produces:
  - `state.update_concept_path(vault: Path, concept_id: str, old_path: str, new_path: str) -> None`
    — one transaction: `concepts.path`, `concept_edges.target_path`/`source_path`,
    `passages.path`, `file_index_state.path`, `outputs.output_id`/`target_path`;
    path-keyed concepts (non-ULID id) re-key to the new path via `_rekey_concept_conn`.
  - `knowledge.move_concept(vault: Path, old_path: str, new_path: str, *,
    context: OperationContext, reason: str = "") -> dict[str, Any]` — returns
    `{"old_path", "new_path", "rewritten": list[str], "event", "commit"}`; raises
    `FileNotFoundError` (missing source), `FileExistsError` (occupied destination),
    `ValueError` (outside `notes/`/`hubs/`/`projects/`, or cross-bundle).
  - `knowledge._rewrite_inbound_links(vault: Path, old_rel: str, new_rel: str) -> list[str]`
    (private) — rewritten inbound-linker rel paths, sorted.

> **Execution notes (2026-07-31) — four deviations from the drafted code below,
> each proven by a mutation that fails a shipped test.** Consumers NID-B.6/.7
> should read the shipped seam, not the draft.
>
> 1. **A checked linker's rewrite is re-signed, not written raw — and only if the
>    read barrier, not the verdict, says it is checked.** The draft's
>    `_rewrite_inbound_links` writes with `write_frontmatter_doc`, which changes a
>    `checked` file's bytes out of band: `is_consumable_checked_file` then fails the
>    sha256 comparison and every note that linked to the moved one silently drops
>    out of consumption. Shipped: `_write_link_rewrite` routes a checked linker
>    through `trusted_writer.mark_checked` — the same seam `curate_note_link` uses —
>    which re-validates *and* re-records the hash. The gate on that re-sign is
>    `is_consumable_checked_file(vault, rel, enqueue_scan=False)`, never the raw
>    `concept_check_status`: `mark_checked` re-validates the schema and nothing about
>    the content (unlike `promote_checked`), so gating on the verdict alone would
>    re-sign a linker whose bytes drifted out of band and launder the edit back into
>    consumption — N files found by a vault-wide scan, on an action having nothing to
>    do with them. A drifted linker falls to the raw write and stays exactly as
>    unconsumable as it already was; the move still proceeds. Consequence of the
>    re-sign: a linker carrying a retired frontmatter field refuses the move instead
>    of being rewritten, and the refusal names the rel path (the writer's own message
>    carries only the field, which is useless after a vault-wide scan).
> 2. **Plan-then-apply, with a byte-exact undo for the *files*.** The draft renames
>    first and then mutates while it scans, so a mid-scan failure strands a
>    half-applied move. Shipped: `_plan_inbound_link_rewrites` is pure reads and
>    replaces `_rewrite_inbound_links`; `move_concept` snapshots the files it will
>    touch and, on any exception, renames the file back *first*, then reverses
>    `update_concept_path`, then restores each written linker byte-for-byte
>    (`_restore_link_rewrite`). The rename goes first because it is the one step
>    nothing else can redo — a restore raising after the DB was reversed would leave
>    the row at the old path and the file at the new one. The **DB** reverse is not
>    byte-exact: `update_concept_path` moves `file_index_state` and `outputs` with
>    `UPDATE OR REPLACE`, which drops a conflicting row already at the destination,
>    and reversing the update cannot resurrect it.
> 3. **The path-key re-key is `_rekey_path_keyed_concept_conn`, not
>    `_rekey_concept_conn`.** NID-B.2's execution replacement did not add that
>    helper ("do not add `_rekey_concept_conn`"), and its shape (mirror-observation
>    re-key) is not this one. `update_concept_path` splits cleanly: the statements in
>    its own body are path space, and the helper is identity space — it re-keys
>    `concepts.concept_id` and hand-moves **every** table keyed by that identity with
>    no FK to carry it (`derivations.input_id`/`output_id`, `passages.concept_id`).
>    That enumeration lives in exactly one named place because the first pass at it
>    stopped one table short: `passages.concept_id` left at the vacated path lets the
>    verdict-cascade triggers (`WHERE concept_id = NEW.concept_id`) hand the *moved*
>    note's passages to the next file dropped there, while `concept_check_status`
>    still reads `checked`. It self-heals on a full `rebuild_passage_index`, never on
>    `refresh_stale_passages`. Verdicts, flags and edges ride the v16
>    `ON UPDATE CASCADE`. `edge_id` is left stale after a re-key — the next
>    `replace_concept_edges` pass recomputes it.
> 4. **`update_concept_path` calls `_reconcile_renamed_output_conn`,** never
>    re-issues it, and runs it *after* the re-key and *before* `concepts.path` moves,
>    since it reads the old path off the row. `move_concept` names the vacated path
>    to the writer only when git tracks it (`_committable`): `git add` exits 128 on a
>    pathspec matching nothing, which would kill every move of an uncommitted file.
>
> **Carried forward, with owners (review of `fe308225..aaf2bb3e`, 2026-07-31):**
>
> - **Journal residue on a rolled-back move — owner NID-B.6.** The `resolved`/
>   `moved_from` event and every per-linker `check-fired` event are appended before
>   `commit_writer_changes`, and the `except` block compensates none of them: a
>   refused move still journals as having happened. Append-only journals cannot be
>   rewound, so B.6 has to pick one — append the move event *after* the commit, or
>   emit a compensating event — before `memoria mv` puts this in a PI's hands.
> - **Digest linkers are mechanism-only — owner NID-B.7.** `_plan_inbound_link_rewrites`
>   scans `digests/` as the draft specified, so a checked digest linking to a moved
>   note is re-signed through `mark_checked` against the digest schema. The mechanism
>   is type-agnostic but only the note case has a test.
>   **Closed in B.7:** `test_move_concept_rewrites_and_re_signs_a_checked_digest_linker`
>   covers it; the mechanism was already correct, so this was a coverage gap and no
>   product code changed.
> - **Stale `edge_id` after a path-key re-key — owner NID-B.7.** Self-heals on the
>   next `replace_concept_edges` pass; B.7 is the task that touches edge resolution,
>   so it owns either recomputing it in the re-key or documenting the window for ERP
>   consumers.
>   **Closed in B.7 — it does *not* self-heal.** `edge_id` hashes the identity
>   triple and `idx_concept_edges_edge_id` is UNIQUE, so the next file dropped at
>   the vacated path recomputes the stale hash exactly and the whole mirror pass
>   dies on an IntegrityError (`test_move_concept_leaves_no_stale_edge_id_for_the_`
>   `vacated_path_to_collide_with` reproduces it). `_rekey_path_keyed_concept_conn`
>   now blanks `edge_id` on every edge touching the re-keyed identity — `''` is the
>   column's existing unresolved value and the partial index skips it — and B.7's
>   resolution pass recomputes it over the live triple. **The window ERP consumers
>   inherit** (widened 2026-08-01 — the `memoria mv` framing was too narrow): the
>   re-key runs from `update_concept_path` *and* from `_adopt_path_key_identity_conn`,
>   which `ensure_concept_parent_conn` reaches, so **any** write path that first
>   mirrors a file whose frontmatter now carries a ULID also leaves those rows at
>   `edge_id = ''` until the next `replace_concept_edges`. Blank, never wrong;
>   `attributes_json` and both endpoints are untouched throughout, and nothing in
>   `src/` reads `edge_id` today (`explore.py` never projects it, no golden pins it),
>   so the window is a contract only for the ERP consumers that will.

**Steps:**

- [x] Append the failing tests to `tests/test_knowledge.py` (reuse the module's
  `workspace`/`_md`/`_call` helpers; wrapper next to `curate_note_link`'s at `:47`):

  ```python
  def move_concept(vault: Path, *args, **kwargs):
      from memoria_vault.runtime.knowledge import move_concept as _move_concept

      return _call(_move_concept, vault, *args, **kwargs)


  def test_move_concept_rewrites_inbound_links_and_path_in_one_transaction(
      tmp_path: Path,
  ) -> None:
      vault = workspace(tmp_path)
      _md(
          vault / "notes/target.md",
          "type: note\ncheck_status: checked\ntitle: Target\nstatus: accepted\n",
      )
      _md(
          vault / "notes/wiki-linker.md",
          "type: note\ncheck_status: checked\ntitle: WikiLinker\nstatus: accepted\n"
          'links:\n  supports: ["[[notes/target|the target]]"]\n',
      )
      _md(
          vault / "notes/bare-linker.md",
          "type: note\ncheck_status: checked\ntitle: BareLinker\nstatus: accepted\n"
          'links:\n  extends: ["notes/target.md"]\n',
      )

      result = move_concept(
          vault, "notes/target.md", "notes/target-moved.md", actor="pi", machine="curator"
      )

      assert result["old_path"] == "notes/target.md"
      assert result["new_path"] == "notes/target-moved.md"
      assert result["rewritten"] == ["notes/bare-linker.md", "notes/wiki-linker.md"]
      assert not (vault / "notes/target.md").exists()
      assert (vault / "notes/target-moved.md").is_file()
      # Surface forms preserved: wikilink keeps its alias, bare path stays bare.
      wiki = read_frontmatter(vault / "notes/wiki-linker.md")
      assert wiki["links"]["supports"] == ["[[notes/target-moved|the target]]"]
      bare = read_frontmatter(vault / "notes/bare-linker.md")
      assert bare["links"]["extends"] == ["notes/target-moved.md"]
      with state.connect(vault) as conn:
          row = conn.execute(
              "SELECT concept_id FROM concepts WHERE path = 'notes/target-moved.md'"
          ).fetchone()
      assert row is not None
      # One trusted-writer commit carries the move and every rewrite.
      committed = set(
          git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines()
      )
      assert {
          "notes/target-moved.md",
          "notes/wiki-linker.md",
          "notes/bare-linker.md",
      } <= committed


  def test_move_concept_refuses_bad_targets(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      _md(
          vault / "notes/a.md",
          "type: note\ncheck_status: checked\ntitle: A\nstatus: accepted\n",
      )
      _md(
          vault / "notes/b.md",
          "type: note\ncheck_status: checked\ntitle: B\nstatus: accepted\n",
      )
      with pytest.raises(FileNotFoundError):
          move_concept(vault, "notes/missing.md", "notes/x.md", actor="pi", machine="m")
      with pytest.raises(FileExistsError):
          move_concept(vault, "notes/a.md", "notes/b.md", actor="pi", machine="m")
      with pytest.raises(ValueError, match="bundle"):
          move_concept(vault, "notes/a.md", "hubs/a.md", actor="pi", machine="m")
      with pytest.raises(ValueError, match="notes/, hubs/, and projects/"):
          move_concept(vault, "digests/a.md", "digests/b.md", actor="pi", machine="m")
  ```

- [x] Run
  `python -m pytest tests/test_knowledge.py::test_move_concept_rewrites_inbound_links_and_path_in_one_transaction tests/test_knowledge.py::test_move_concept_refuses_bad_targets -v`
  — expect FAIL: `ImportError: cannot import name 'move_concept' from
  'memoria_vault.runtime.knowledge'`.
- [x] Add `update_concept_path` to `src/memoria_vault/runtime/state.py` (below
  `rebuild_file_concept_mirror`):

  ```python
  def update_concept_path(vault: Path, concept_id: str, old_path: str, new_path: str) -> None:
      """Move one concept's path attribute; id-keyed rows keep every attachment."""
      old_rel = normalize_path(old_path)
      new_rel = normalize_path(new_path)
      with connect(vault) as conn:
          if concept_id == new_rel:
              # Path-keyed concept (non-ULID id): the path IS the key.
              _rekey_concept_conn(conn, old_rel, new_rel)
          conn.execute(
              "UPDATE concepts SET path = ? WHERE concept_id = ?", (new_rel, concept_id)
          )
          conn.execute(
              "UPDATE OR REPLACE concept_edges SET target_path = ? WHERE target_path = ?",
              (new_rel, old_rel),
          )
          conn.execute(
              "UPDATE OR REPLACE concept_edges SET source_path = ? WHERE source_path = ?",
              (new_rel, old_rel),
          )
          conn.execute("UPDATE passages SET path = ? WHERE path = ?", (new_rel, old_rel))
          conn.execute(
              "UPDATE OR REPLACE file_index_state SET path = ? WHERE path = ?",
              (new_rel, old_rel),
          )
          conn.execute(
              "UPDATE OR REPLACE outputs SET output_id = ?, target_path = ? WHERE output_id = ?",
              (new_rel, new_rel, old_rel),
          )
  ```

- [x] Add the move seam to `src/memoria_vault/runtime/knowledge.py` (after
  `curate_note_link`, `:414`); extend its vaultio import with `is_ulid`:

  ```python
  def move_concept(
      vault: Path,
      old_path: str,
      new_path: str,
      *,
      context: OperationContext,
      reason: str = "",
  ) -> dict[str, Any]:
      """Rename a concept file, rewriting inbound links in one writer transaction."""
      validate_operation_context(vault, context)
      vault = Path(vault)
      old_rel = _movable_rel(old_path)
      new_rel = _movable_rel(new_path)
      if old_rel.split("/", 1)[0] != new_rel.split("/", 1)[0]:
          raise ValueError(f"move must stay inside its bundle: {old_rel} -> {new_rel}")
      source = vault / old_rel
      if not source.is_file():
          raise FileNotFoundError(source)
      destination = vault / new_rel
      if destination.exists():
          raise FileExistsError(destination)
      raw_id = str(read_frontmatter(source).get("id") or "")
      concept_id = raw_id if is_ulid(raw_id) else new_rel
      destination.parent.mkdir(parents=True, exist_ok=True)
      source.rename(destination)
      rewritten = _rewrite_inbound_links(vault, old_rel, new_rel)
      state.update_concept_path(vault, concept_id, old_rel, new_rel)
      event = append_journal_event(
          vault,
          {
              "event": "resolved",
              "target_id": new_rel,
              "moved_from": old_rel,
              "target_sha256": sha256_file(destination),
              "reason": reason.strip(),
          },
          context=context,
      )
      commit = commit_writer_changes(
          vault,
          f"mv {old_rel} -> {new_rel}",
          [old_rel, new_rel, *rewritten],
          context=context,
      )
      return {
          "old_path": old_rel,
          "new_path": new_rel,
          "rewritten": rewritten,
          "event": event,
          "commit": commit,
      }


  def _movable_rel(path: str) -> str:
      rel = normalize_path(path)
      if not rel.endswith(".md"):
          rel += ".md"
      if not rel.startswith(("notes/", "hubs/", "projects/")):
          raise ValueError(f"memoria mv supports notes/, hubs/, and projects/ files: {rel}")
      return rel


  def _rewrite_inbound_links(vault: Path, old_rel: str, new_rel: str) -> list[str]:
      """Rewrite links: entries that target old_rel; returns rewritten rel paths."""
      rewritten = []
      for bundle in ("notes", "hubs", "projects", "digests"):
          base = vault / bundle
          if not base.is_dir():
              continue
          for path in sorted(base.rglob("*.md")):
              rel = path.relative_to(vault).as_posix()
              if rel == new_rel:
                  continue
              frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
              links = frontmatter.get("links")
              if not isinstance(links, dict):
                  continue
              changed = False
              for link_type, values in links.items():
                  if not isinstance(values, list):
                      continue
                  for index, raw in enumerate(values):
                      if _link_target(raw) != old_rel:
                          continue
                      values[index] = _rewrite_link_value(raw, old_rel, new_rel)
                      changed = True
              if changed:
                  frontmatter["links"] = links
                  write_frontmatter_doc(path, frontmatter, body)
                  rewritten.append(rel)
      return sorted(rewritten)


  def _rewrite_link_value(raw: Any, old_rel: str, new_rel: str) -> Any:
      """Swap the target while preserving the entry's surface form."""
      if not isinstance(raw, str):
          return raw
      value = raw.strip()
      old_stem = old_rel.removesuffix(".md")
      new_stem = new_rel.removesuffix(".md")
      if value.startswith("[[") and value.endswith("]]"):
          inner = value[2:-2]
          head, sep, tail = inner.partition("|")
          anchor_head, anchor_sep, anchor_tail = head.partition("#")
          target = new_stem if anchor_head.strip() in {old_stem, old_rel} else anchor_head
          return f"[[{target}{anchor_sep}{anchor_tail}{sep}{tail}]]"
      return new_rel if value.endswith(".md") else new_stem
  ```

- [x] Run
  `python -m pytest tests/test_knowledge.py::test_move_concept_rewrites_inbound_links_and_path_in_one_transaction tests/test_knowledge.py::test_move_concept_refuses_bad_targets -v`
  — expect PASS.
- [x] Run `python scripts/verify` — expect PASS.
- [x] Commit:

  ```
  git add src/memoria_vault/runtime/state.py src/memoria_vault/runtime/knowledge.py tests/test_knowledge.py
  git commit -m "feat(knowledge): move_concept — inbound-link rewrite + path update in one writer transaction

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task NID-B.6: `memoria mv` — operation card, worker dispatch, CLI, floor entry, docs

> **Inherited from NID-B.5's re-review (2026-07-31) — two path-space enumeration gaps
> and one sharpened characterisation.**
>
> 1. **`evidence_sets.block_ref` is path-prefixed and was NOT in B.5's moved table set
>    (Important).** `_movable_rel` admits `projects/`; `block_ref` is
>    `{draft_rel}#^blk-…`, joined with `startswith(draft_rel)` (`knowledge.py:2267`).
>    Probe: a `projects/` move succeeds and leaves `block_refs ==
>    ['projects/draft.md#^blk-1']` at the **vacated** path, so the moved draft reads as
>    having no evidence and raises a false `{"kind": "no-evidence-set", "severity":
>    "high"}`. `evidence_bindings` is immutable by trigger, so a later repair cannot
>    simply rewrite it. Loud false alarm, not a silent trust failure — but B.5's "full
>    table set" is one table short in **path** space.
>
> 2. **`file_baseline.subject_id` is path-keyed and does not move — and this is NOT
>    merely "a stale row".** Re-review sharpened B.5's own characterisation: the verdict
>    is safe (demotion and the read barrier both key off `outputs`/trace state, which
>    move correctly — a tampered moved file still demotes to `unchecked`), **but
>    `_reconcile_file_baselines` and the observe loop both take a `baseline is None`
>    early exit, so the foreign-edit finding is SUPPRESSED.** Probe: `findings: []` on a
>    tampered moved file, and the baseline silently adopts the tampered hash as truth.
>    The mirror case fires too — a newcomer at the vacated path inherits the stale
>    baseline and raises a **spurious** `foreign-edit`. So: one lost alert per moved
>    file, plus one false alert if the path is reoccupied. Alert-level, not
>    verdict-level.
>
> 3. **Journal residue on a rolled-back move (M5, from the first review).** The
>    `resolved`/`moved_from` event and the per-linker `check-fired` events land before
>    `commit_writer_changes` and are never compensated, so a refused move still journals
>    as having happened. Append-only journals cannot be rewound — either append the move
>    event after the commit, or emit a compensating event.

Wires NID-B.5 as the PI-protected `move-concept` operation and the `memoria mv`
CLI command, following the `curate-note-link` pattern end to end.

**Files:**
- Create: `src/memoria_vault/product/capabilities/operations/move-concept.md`
- Modify: `src/memoria_vault/runtime/worker.py` — `PROTECTED_OPERATION_ACTORS`
  (`:53-66`) and a dispatch branch in `_run_operation_job` (after the
  `curate-note-link` branch, `:471-497`)
- Modify: `src/memoria_vault/cli.py` — `mv` parser next to `link` (`:259-265`) and
  `_cmd_mv` next to `_cmd_link` (`:1208`)
- Modify: `tests/floor_lib.py` — `OPERATION_REGISTRY` entry
- Modify: `docs/reference/commands-and-transports/system-actions.md:26`,
  `docs/reference/commands-and-transports/system-actions-operations.md:17` + table,
  `docs/reference/control-and-policy/control-plane.md:61`
- Test: `tests/test_knowledge.py` (worker-level), `tests/test_floor_coverage.py`
  (existing, must stay green)

**Interfaces:**
- Consumes: `knowledge.move_concept` (NID-B.5), `worker.enqueue_operation`
  (`:123`), `cli._enqueue_and_run` (`:2087`), `cli._common` (`:560`),
  `operations.load_operation_policy` (`operations.py:103`, reads the packaged card).
- Produces:
  - Operation id `move-concept` — payload `{"old_path": str, "new_path": str,
    "reason": str}`; PI-protected (`PROTECTED_OPERATION_ACTORS["move-concept"] = "pi"`);
    result keys `commit`, `old_path`, `new_path`, `rewritten`.
  - CLI: `memoria mv <old_path> <new_path> [--reason]`.

**Steps:**

- [x] Write the failing worker-dispatch test in `tests/test_knowledge.py`:

  ```python
  def test_move_concept_operation_dispatches_via_worker(tmp_path: Path) -> None:
      from memoria_vault.runtime.worker import enqueue_operation, run_pending_jobs

      vault = workspace(tmp_path)
      _md(
          vault / "notes/mv-me.md",
          "type: note\ncheck_status: checked\ntitle: MvMe\nstatus: accepted\n",
      )
      enqueue_operation(
          vault,
          "move-concept",
          payload={"old_path": "notes/mv-me.md", "new_path": "notes/mv-done.md"},
          actor="pi",
      )
      run_pending_jobs(vault)
      request = state.list_requests(vault)[-1]
      assert request["status"] == "done", request.get("error")
      assert (vault / "notes/mv-done.md").is_file()
      assert not (vault / "notes/mv-me.md").exists()
  ```

  (If `state.list_requests` requires a status filter in its current signature,
  match the call shape used by the nearest existing worker test in this file.)
- [x] Run
  `python -m pytest tests/test_knowledge.py::test_move_concept_operation_dispatches_via_worker -v`
  — expect FAIL: the request errors with the missing-manifest/unknown-operation
  message from `load_operation_policy` (`request["status"] == "failed"`).
- [x] Create `src/memoria_vault/product/capabilities/operations/move-concept.md`
  (mirrors `curate-note-link.md`'s policy contract):

  ```markdown
  ---
  title: Move concept
  type: operation
  description: Rename a concept file, rewriting inbound links and the DB path attribute transactionally.
  operation_id: move-concept
  allowed_tools:
  - trusted_writer
  allowed_paths:
  - notes/
  - hubs/
  - projects/
  - digests/
  - .memoria/journal/
  allowed_network: []
  prompt_version: move-concept.v1
  io_schema:
    input: concept_move
    output: moved_concept
  risk_class: medium
  required_checks:
  - memoria-runtime
  tags:
  - alpha22
  - notes
  id: operations/move-concept
  links: {}
  ---

  # Operation

  Rename a note, hub, or project file. Inbound `links:` entries are rewritten in
  the same trusted-writer commit, and the concept's DB `path` attribute moves with
  it — identity (the frontmatter `id`) never changes, so verdicts and edges stay
  attached. A convenience over reconcile-by-id, not a correctness requirement.
  ```

- [x] In `src/memoria_vault/runtime/worker.py`: add
  `"move-concept": "pi",` to `PROTECTED_OPERATION_ACTORS` (after
  `"curate-note-link": "pi",`, `:58`) and the dispatch branch after the
  `curate-note-link` branch (`:497`):

  ```python
      if operation_id == "move-concept":
          from memoria_vault.runtime.knowledge import move_concept

          old_path = str(payload.get("old_path") or "").strip()
          new_path = str(payload.get("new_path") or "").strip()
          if not old_path:
              raise ValueError("move-concept requires old_path")
          if not new_path:
              raise ValueError("move-concept requires new_path")
          result = move_concept(
              vault,
              old_path,
              new_path,
              context=context,
              reason=str(payload.get("reason") or ""),
          )
          return {
              "commit": result["commit"],
              "old_path": result["old_path"],
              "new_path": result["new_path"],
              "rewritten": result["rewritten"],
          }
  ```

- [x] Run
  `python -m pytest tests/test_knowledge.py::test_move_concept_operation_dispatches_via_worker -v`
  — expect PASS.
- [x] Add the CLI command in `src/memoria_vault/cli.py`, after the `link` block
  (`:259-265`):

  ```python
      mv = sub.add_parser("mv")
      _common(mv)
      mv.add_argument("old_path")
      mv.add_argument("new_path")
      mv.add_argument("--reason", default="")
      mv.set_defaults(handler=_cmd_mv)
  ```

  and the handler next to `_cmd_link` (`:1208`):

  ```python
  def _cmd_mv(args: argparse.Namespace) -> int:
      return _emit(
          _enqueue_and_run(
              args,
              "move-concept",
              {
                  "old_path": args.old_path,
                  "new_path": args.new_path,
                  "reason": args.reason,
              },
          ),
          args,
      )
  ```

- [x] Register the floor entry in `tests/floor_lib.py` `OPERATION_REGISTRY`
  (alphabetical position; same deterministic-refusal pattern as `curate-note-link`
  — the sweep enqueues as `actor="agent"`, and `move-concept` is pi-protected):

  ```python
      # move-concept is PROTECTED_OPERATION_ACTORS "pi"-only (worker.py); the
      # agent-actor sweep is refused on actor authority before the move runs.
      "move-concept": {
          "payload": {
              "old_path": "notes/package-support.md",
              "new_path": "notes/package-support-moved.md",
          },
          "expect": "refused",
          "reason": "requires PI actor authority",
      },
  ```

- [x] Run
  `python -m pytest tests/test_floor_coverage.py -v`
  — expect PASS (`test_every_operation_has_a_floor_entry` now sees the card and the
  entry). Then run the floor sweep level the repo's harness prescribes for
  operation-catalog changes; if the seeded-vault goldens shift (new capability card
  in the seed), regenerate them exactly as the failing floor test's message
  instructs — never hand-edit goldens.
- [x] Update the three docs listings (the doc-claims gate checks these):
  add `move-concept` to the alphabetical operation id list at
  `docs/reference/commands-and-transports/system-actions.md:26`; to the pi-protected
  roster sentence at `docs/reference/commands-and-transports/system-actions-operations.md:17`
  and a table row following the `Curate note link` pattern (`:123`):

  ```markdown
  | Move concept | worker operation `move-concept` + runtime helper (`move_concept`) | Renames a note, hub, or project file, rewriting inbound `links:` entries and the concept's DB `path` attribute in one trusted-writer commit; identity is the frontmatter `id`, so verdicts and edges stay attached. |
  ```

  and to the `pi` row at `docs/reference/control-and-policy/control-plane.md:61`.
- [x] Run `python scripts/verify` — expect PASS.
- [x] Commit:

  ```
  git add src/memoria_vault/product/capabilities/operations/move-concept.md src/memoria_vault/runtime/worker.py src/memoria_vault/cli.py tests/floor_lib.py tests/test_knowledge.py docs/reference/commands-and-transports/system-actions.md docs/reference/commands-and-transports/system-actions-operations.md docs/reference/control-and-policy/control-plane.md
  git commit -m "feat(cli): memoria mv — pi-protected move-concept operation, worker dispatch, floor entry, docs

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task NID-B.7: pending-edge resolution — dangling links resolve at the reindex where the target appears (clause 6)

Forward/dangling links are legal Zettelkasten practice; the mirror keeps them as
pending rows and resolves them when the target materializes. NID-B.4's
`replace_concept_edges` already resolves rows it (re)inserts; this task adds the
in-DB resolution pass for **retained** pending rows — durable `tension` rows and
any pending row spared by a scoped prune — and proves the full lifecycle
end-to-end.

**Files:**
- Modify: `src/memoria_vault/runtime/state.py` — `replace_concept_edges`
  (NID-B.1 body) gains a resolution pass over retained pending rows
- Test: `tests/test_query_substrate.py`

**Interfaces:**
- Consumes: NID-B.1/B.4 (`replace_concept_edges`, pending schema,
  `concept_edge_id`), `write_checked_concept`, `copy_memoria_dirs`.
- Produces: resolution guarantee — after any `replace_concept_edges` run, no row
  has `target_concept_id IS NULL` while a concepts row exists whose `path` (or
  bare-`work_id` rendering) matches its `target_path`; resolved rows carry the
  recomputed `edge_id` over the id-space triple.

**Steps:**

- [x] Append the failing lifecycle test to `tests/test_query_substrate.py`:

  ```python
  def test_pending_edges_resolve_when_target_appears(tmp_path: Path) -> None:
      vault = tmp_path
      copy_memoria_dirs(vault, "schemas")
      write_checked_concept(
          vault,
          "notes/early.md",
          "type: note\ntitle: Early\ntags: []\n"
          'links:\n  supports: ["[[notes/future]]"]\n',
      )
      rebuild_passage_index(vault)
      # A durable tension row targeting the same future note, hung with attributes.
      with state.connect(vault) as conn:
          conn.execute(
              "INSERT INTO concept_edges("
              " edge_id, source_concept_id, relation_type, target_concept_id,"
              " target_path, attributes_json, check_status, source_path, updated_at)"
              " VALUES ('', 'notes/early.md', 'tension', NULL, 'notes/future.md',"
              " '{\"warrant\": \"w9\"}', 'checked', '', '2026-07-15T00:00:00Z')"
          )
          pending = conn.execute(
              "SELECT target_concept_id, edge_id FROM concept_edges"
              " WHERE target_path = 'notes/future.md' AND relation_type = 'supports'"
          ).fetchone()
      # Dangling link is modeled, not dropped (clause 6).
      assert pending["target_concept_id"] is None
      assert pending["edge_id"] == ""

      # The target appears; the next reindex resolves both rows to its id.
      write_checked_concept(
          vault, "notes/future.md", "type: note\ntitle: Future\ntags: []\nlinks: {}\n"
      )
      rebuild_passage_index(vault)

      with state.connect(vault) as conn:
          rows = {
              str(row["relation_type"]): dict(row)
              for row in conn.execute(
                  "SELECT relation_type, target_concept_id, edge_id, attributes_json"
                  " FROM concept_edges WHERE target_path = 'notes/future.md'"
              )
          }
      assert rows["supports"]["target_concept_id"] == "notes/future.md"
      assert rows["supports"]["edge_id"] == state.concept_edge_id(
          "notes/early.md", "supports", "notes/future.md"
      )
      # The retained tension row resolves too — attributes still hanging on it.
      assert rows["tension"]["target_concept_id"] == "notes/future.md"
      assert rows["tension"]["edge_id"] == state.concept_edge_id(
          "notes/early.md", "tension", "notes/future.md"
      )
      assert rows["tension"]["attributes_json"] == '{"warrant": "w9"}'
  ```

  (Neither note carries a ULID `id:`, so both key by path — keeps the assertion
  literals readable; the id-space variant is covered by NID-B.4's rename test.)
- [x] Run
  `python -m pytest tests/test_query_substrate.py::test_pending_edges_resolve_when_target_appears -v`
  — expect FAIL on the **tension** assertions:
  `assert rows["tension"]["target_concept_id"] == "notes/future.md"` sees `None` —
  the mirror pass re-resolves only rows it inserts, never retained tension rows.
- [x] In `state.replace_concept_edges` (NID-B.1 body), add the resolution pass at
  the end of the `with connect(vault) as conn:` block, after the insert loop:

  ```python
          # Resolve retained pending rows whose target has since appeared
          # (durable tension rows and scoped-prune survivors) — NODES §1.6.
          unresolved = conn.execute(
              "SELECT source_concept_id, relation_type, target_path FROM concept_edges"
              " WHERE target_concept_id IS NULL"
          ).fetchall()
          for row in unresolved:
              target_path = str(row["target_path"])
              target_row = conn.execute(
                  "SELECT concept_id FROM concepts WHERE path = ? OR concept_id = ?",
                  (target_path, target_path.removeprefix("catalog/sources/")),
              ).fetchone()
              if target_row is None:
                  continue
              target_id = str(target_row["concept_id"])
              conn.execute(
                  """
                  UPDATE concept_edges
                  SET target_concept_id = ?, edge_id = ?
                  WHERE source_concept_id = ? AND relation_type = ? AND target_path = ?
                  """,
                  (
                      target_id,
                      concept_edge_id(
                          str(row["source_concept_id"]),
                          str(row["relation_type"]),
                          target_id,
                      ),
                      str(row["source_concept_id"]),
                      str(row["relation_type"]),
                      target_path,
                  ),
              )
  ```

- [x] Run
  `python -m pytest tests/test_query_substrate.py -v`
  — expect PASS (the whole file: v13/v14 shape pins, G2S1.1 mirror test, NID-B.4
  rename test, this lifecycle test).
- [x] Run `python scripts/verify` — expect PASS.
- [x] Commit:

  ```
  git add src/memoria_vault/runtime/state.py tests/test_query_substrate.py
  git commit -m "feat(graph): resolve retained pending edges when their target appears at reindex

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```
# Section NID-C: Residual hygiene + hub Candidates block

Implements NODES spec §4 (residual hygiene) and §5 (hub Candidates block) —
`docs/superpowers/specs/2026-07-15-graph-nodes-identity-design.md:108-138` —
at main @ `9c77ba61`.

**SPEC GAP:** spec §4 counts "five" dead `"work"` filter sets, but a sixth
byte-identical dead literal exists at `integrity.py:1387`
(`_checked_tension_rows`); this section applies the same ratified prune to it
rather than leaving one dead literal standing (flagged, not new policy).
**SPEC GAP:** spec §5 does not fix `digest-related-works`' input shape; this
section chooses payload `{hub_path: str, k: int = 5}` — hub-centric, matching
the spec's own entry wording "this hub's works".
**SPEC GAP:** spec §5 does not define how a hub's work-set is derived; chosen:
the `work_id`s of `digests/*.md` whose slugified `tags` contain the hub's
`tag` — the exact linkage `compile-source-digest` writes today
(`operations.py:557` digest `tags`, `operations.py:595` hub `tag`).
**SPEC GAP:** spec §5 says "every entry carries run attribution" without a
format; chosen: a trailing `%%run=<run_id>%%` Obsidian comment per entry (the
delimiter line already carries the block-level `run=<run_id>`).

Section-wide constraints:

- **No schema migration in this section.** The binding version chain (v16
  NID-B, v17 ERP-A, v18 ERP-C) is untouched: `state.related_work_candidates`
  is read-only SQL over the existing `work_graph_edges` table
  (`schema.sql:171-186`), and the block writer reuses existing trusted-writer
  seams.
- **Ordering vs NID-B:** this section's code calls
  `state.concept_check_status(vault, <vault-relative path>)` and
  `state.set_concept_verdict(vault, <path>, ...)` as they exist at
  `9c77ba61` (path-keyed). NID-B's v16 re-key must either keep these
  path-accepting call signatures working (resolving path→id internally) or
  update these call sites; if NID-B lands first, re-verify
  `tests/test_hub_candidates.py` against its API.
- Consumes nothing from Plan 22's G2S1.1–.3 (`concept_edges` machinery);
  `work_graph_edges` is a different table and is not re-keyed by v16 (works
  keep `work_id` identity per NODES §0/§1.7).
- All vault-touching tests run against disposable `tmp_path` vaults only.

---

### Task NID-C.1: Prune the dead `"work"` frontmatter-type literals

**Files:**
- Modify: `src/memoria_vault/runtime/search_index.py:380`
- Modify: `src/memoria_vault/runtime/integrity.py:152`, `:606`, `:640`, `:1387`
  (spec cites 605/640/152; 605 has drifted to 606 at `9c77ba61`, and 1387 is
  the sixth site — see SPEC GAP above)
- Modify: `src/memoria_vault/cli.py:1065`
- Modify: `src/memoria_vault/runtime/knowledge.py:1287`
- Modify: `tests/test_identifier_renames.py` (new scan test; file is already
  registered in `tests/conftest.py` `TEST_LEVELS` at "contract")

**Interfaces:**
- Consumes: nothing new — pure deletion of unreachable branches. `"work"` is a
  DB-store concept type (`schema.sql:54-58`); no markdown type yaml exists for
  it (`product/workspace_seed/.memoria/schemas/types/` ships only
  note/digest/fulltext/hub/project/code-artifact), so
  `frontmatter.get("type")` can never be `"work"` on a validated file.
- Produces: no API change. Catalog-side `"work"` usages stay untouched:
  `engine/api.py:205` (`read_concepts(concept_type="work")` reads DB rows),
  `cli.py:158` (`--mode work` is a note *mode*), `cli.py:280`/`cli.py:3126`
  (concept listing types), `knowledge.py:98` (folder-term set).

> **Amendment — measured offender list and the `SEARCHABLE_TYPES` ruling
> (2026-08-01, applied).** Verified by content at `a582a510`, this task's
> Files list and its regex guard are both stale:
>
> 1. **`integrity.py:640` was already fixed** before this task ran — the site
>    (now `:641`) reads `!= "digest"`. Nothing to do there.
> 2. **`search_index.py:380` became the named constant `SEARCHABLE_TYPES`**
>    (`search_index.py:32`, consumed at `:146` and `:491`). The plan's
>    line-oriented regex `frontmatter\.get\("type"\)[^\n]*"work"` cannot see it,
>    so that guard would have gone green over the very literal this task
>    exists to remove.
> 3. **Ruling: the constant is in scope, not exempt.** `SEARCHABLE_TYPES` is
>    consumed only as `frontmatter.get("type") not in SEARCHABLE_TYPES`, so it
>    *is* a frontmatter type filter — the literal was hoisted, not retired.
>    Its sibling frontmatter rosters already exclude `"work"`
>    (`engine/api.py:34 CONCEPT_TYPES`, `vaultio.py:17
>    UNIVERSAL_CONCEPT_TYPES`), and the catalog work documents that make the
>    index searchable are generated by `_checked_work_documents`
>    (`search_index.py:536-552`) carrying `type: fulltext` and appended
>    *after* the filter — so `"work"` reaches no document either way. It is
>    dropped, leaving `frozenset({"digest", "note", "hub", "project"})`.
> 4. **The guard resolves operands instead of matching text.** It parses each
>    `src`/`scripts` module, finds `Compare` nodes whose left side is
>    `frontmatter.get("type")` (or a `str(... or "")` wrapper), and resolves a
>    bare `Name` operand against module-level string rosters collected across
>    every scanned module. Receiver-restricted to `frontmatter`/`fm` so that
>    DB-row filters (`row.get("type")`, `source.get("type")`) — where
>    `"work"` is live — stay untouched, honoring the Produces clause above.
> 5. **True measured list: seven filter sites, not six.** `cli.py:1573`,
>    `integrity.py:153`, `:607`, `:1393`, `knowledge.py:1504`, plus
>    `search_index.py:146` and `:491` through the constant.
> 6. **One extra test file:** `tests/test_search_index.py` gains
>    `test_search_universe_admits_every_declared_searchable_type`. The guard
>    only forbids a token; without this, narrowing `SEARCHABLE_TYPES` further
>    would break no test. The new test writes one checked concept of each
>    remaining member and asserts all four reach `checked_search_universe`.

Steps:

- [x] Write the failing test. Add to `tests/test_identifier_renames.py` —
  extend the existing imports (`from pathlib import Path` is present; add
  `import re` below `from __future__ import annotations`) and append:

  ```python
  def test_frontmatter_type_filters_carry_no_dead_work_literal() -> None:
      """NODES spec §4: "work" is a DB-store concept type (catalog rows);
      no markdown file carries `type: work` (no type yaml exists for it),
      so any frontmatter type filter naming "work" is dead code."""
      pattern = re.compile(r'frontmatter\.get\("type"\)[^\n]*"work"')
      offenders = []
      for root in (ROOT / "src", ROOT / "scripts"):
          for path in _text_files(root):
              if path.suffix != ".py":
                  continue
              lines = path.read_text(encoding="utf-8").splitlines()
              for line_no, line in enumerate(lines, start=1):
                  if pattern.search(line):
                      offenders.append(f"{path.relative_to(ROOT)}:{line_no}")

      assert offenders == []
  ```

- [x] Run test to verify it fails:
  `python -m pytest tests/test_identifier_renames.py::test_frontmatter_type_filters_carry_no_dead_work_literal -v`
  — expected failure: `AssertionError` listing exactly six offenders
  (`src/memoria_vault/runtime/search_index.py:380`,
  `src/memoria_vault/runtime/integrity.py:152`, `:606`, `:640`, `:1387`,
  `src/memoria_vault/cli.py:1065`,
  `src/memoria_vault/runtime/knowledge.py:1287`).
  *Measured: seven offenders, per the amendment above —* `cli.py:1573`,
  `integrity.py:153`, `:607`, `:1393`, `knowledge.py:1504`,
  `search_index.py:146`, `:491`.

- [x] Write minimal implementation — drop `"work"` from each filter
  (singleton sets become `!=` comparisons, matching surrounding style).
  *Applied at the current symbols:*
  - `search_index.py:32` (`SEARCHABLE_TYPES`, serving `:146`/`:491`):
    `frozenset({"digest", "note", "hub", "project"})`
  - `integrity.py:153`:
    `if frontmatter.get("type") not in {"digest", "note"}:`
  - `integrity.py:607`:
    `if frontmatter.get("type") != "note":`
  - `integrity.py:641`: already `!= "digest"` before this task — untouched.
  - `integrity.py:1393`:
    `if frontmatter.get("type") != "note":`
  - `cli.py:1573`:
    `if frontmatter.get("type") not in {"digest", "note"}:`
  - `knowledge.py:1504`:
    `if frontmatter.get("type") != "digest":`

- [x] Run test to verify it passes:
  `python -m pytest tests/test_identifier_renames.py -v`

- [x] Verify no behavior regression in the touched modules:
  `python -m pytest tests/test_integrity.py tests/test_knowledge.py tests/test_search_index.py tests/test_cli.py tests/test_cli_honesty.py -q`
  — all pass. Any historical `type: work` importer fixture is unsupported under
  the clean-slate ruling and must be deleted rather than rewritten by a CLI path.

- [ ] Commit:
  ```
  git add src/memoria_vault/runtime/search_index.py src/memoria_vault/runtime/integrity.py src/memoria_vault/cli.py src/memoria_vault/runtime/knowledge.py tests/test_identifier_renames.py
  git commit -m "refactor: prune dead 'work' frontmatter-type literals (NODES §4)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task NID-C.2: Correct the citation-survival operation doc (id stays)

**Files:**
- Modify: `src/memoria_vault/product/capabilities/operations/integrity-citation-survival-check.md`
  (description at lines 4-5, `io_schema.input` at line 20, body at lines 32-35)
- Modify: `docs/reference/commands-and-transports/system-actions-operations.md:140`
  (the "Check citation survival" table row repeats the stale claim)
- Modify: `tests/fixtures/floor/goldens/regenerate-capability-index.json`
  (regenerated — the rendered `.memoria/index/capability-index.json` embeds
  every manifest's sha256 (`capabilities.py:176`), so any manifest text edit
  drifts exactly this golden)

**Interfaces:**
- Consumes: shipped behavior
  `integrity.check_citation_survival(vault, *, context, shadow=True, commit=False)`
  at `integrity.py:564-587`: flags a missing/stale generated
  `bibliography.bib` projection via `capture.render_references_bib` /
  `capture.check_references_bib`.
- Produces: corrected doc only. **`operation_id:
  integrity-citation-survival-check` is unchanged** (operation ids are stable
  API — NODES §4); `prompt_version`, `allowed_*`, `required_checks`, `risk_class`
  unchanged. Worker dispatch (`worker.py:43-52` `INTEGRITY_FINDING_OPERATIONS`)
  and floor entry (`tests/floor_lib.py:827-830`) unchanged.

Steps:

- [x] Edit the manifest. Replace lines 4-5 (description) with:
  ```yaml
  description: Flag a missing or stale generated bibliography.bib projection for
    checked catalog sources.
  ```
  Replace line 20 (`  input: checked_keep_set`) with
  `  input: checked_catalog_sources`. Replace the body (lines 32-35) with:
  ```markdown
  # Operation

  Flag the vault-level `bibliography.bib` projection when it is missing or
  stale against checked catalog sources (the shipped `check_citation_survival`
  behavior). The operation id keeps its original citation-survival name:
  operation ids are stable API.
  ```

- [x] Edit `docs/reference/commands-and-transports/system-actions-operations.md:140`
  — replace the row's third cell so the full row reads:
  ```markdown
  | Check citation survival | runtime integrity helper (`check_citation_survival`) | Flags a missing or stale generated `bibliography.bib` projection for checked catalog sources; this is the vault-level bibliography staleness check, not a per-Concept citation-payload scan. |
  ```

- [x] Regenerate the one drifted golden and verify the sweep:
  `MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest "tests/test_floor_sweep_operations.py::test_operation[regenerate-capability-index]" -v`
  then re-run without the env var:
  `python -m pytest "tests/test_floor_sweep_operations.py::test_operation[regenerate-capability-index]" "tests/test_floor_sweep_operations.py::test_operation[integrity-citation-survival-check]" -v`
  — both pass; `git diff tests/fixtures/floor/goldens/` shows only the one
  capability-index file hash changing.

- [x] Verify gates: `python scripts/checks/doc_claims_gate.py` prints
  `doc-claims-gate: clean`; `python -m pytest tests/test_capabilities.py tests/test_integrity.py -q` passes.

- [x] Commit:
  ```
  git add src/memoria_vault/product/capabilities/operations/integrity-citation-survival-check.md docs/reference/commands-and-transports/system-actions-operations.md tests/fixtures/floor/goldens/regenerate-capability-index.json
  git commit -m "docs: describe citation-survival check as the shipped bibliography.bib staleness check (NODES §4)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

**Completion record (2026-07-17):** Implemented in `8006b641` and approved by
independent review. The authorized capability-index golden was regenerated;
both named floor operations, the documentation-claims gate, and the
capabilities/integrity suite (20 tests) passed. Branch-wide final verification
remains scheduled with the next behavioral batch.

> **Re-verification by content (2026-08-01).** `8006b641` is not an ancestor of
> `main` — it merged by squash — so the record above was re-checked against the
> files rather than the SHA, at `4bb36255`:
>
> 1. The manifest carries the prescribed `description`, `io_schema.input:
>    checked_catalog_sources`, and body verbatim, with `operation_id`,
>    `prompt_version`, `allowed_*`, `required_checks`, and `risk_class`
>    unchanged.
> 2. The reference row is the prescribed text; it has drifted from `:140` to
>    `:142`.
> 3. `tests/fixtures/floor/goldens/regenerate-capability-index.json` is current:
>    both named floor operations pass without `MEMORIA_FLOOR_UPDATE_GOLDENS`,
>    so **no golden moves for this task** (contract 8 unaffected).
> 4. `doc_claims_gate.py` prints `doc-claims-gate: clean`;
>    `tests/test_capabilities.py` and `tests/test_integrity.py` pass.
>
> Nothing was left to do. Every step above is ticked and the shipped files match
> them, so the task stands complete as recorded.

---

### Task NID-C.3: Hub Candidates block writer (delimited terminal section)

> **Binding clean-slate override (2026-07-30):** frontmatter containing a
> retired field is invalid and must fail closed without a write. Do not add an
> `allow_retired_input` parameter, a retired-field stripping normalizer, or any
> other admission path. The historical snippets below that pass
> `allow_retired_input=True`, import `RETIRED_FRONTMATTER_FIELDS`, or describe
> popped fields are non-executable; retain the normal checked-writer validation.

> **Amendment — measured deviations and the fail-closed proof (2026-08-01,
> applied).** Verified by content at `4bb36255`:
>
> 1. **The trusted-writer edit is already landed.** `mark_checked` gained
>    `body: str | None = None` (and a sibling `frontmatter` keyword) in
>    `31e3bc1a`, and its tail already calls `_write_checked` with
>    `current_body if body is None else body`. The Files entry and the
>    trusted-writer half of the implementation step are no-ops at HEAD; this
>    task creates `hub_candidates.py`, its tests, and the `conftest.py`
>    registration only. **No `src/` file other than the new module changed.**
> 2. **The fail-closed rule needed no new code either.** `_validate_concept`
>    already raises `retired frontmatter field is ignored: <field>` *before*
>    any byte is written, on both boundaries the writer uses — `stage_concept`
>    (validate, then write the staged file) and `_write_checked` (validate,
>    then journal, then write). `write_hub_candidates` passes the live
>    frontmatter through untouched and inherits that refusal. There is no
>    `allow_retired_input`, no stripping normalizer, and no admission path.
> 3. **Both directions are proved, and the refusal is proved to write
>    nothing.** `test_write_refuses_retired_frontmatter_field_on_unchecked_hub_without_writing`
>    and `..._on_checked_hub_without_writing` compare a whole-surface snapshot
>    across the raise — file bytes, `.memoria/staging/` presence,
>    `state.journal_head`, the journal JSONL exports, the verdict, and the
>    `outputs` row — and assert the offending field is still in the file.
>    Each fixture's frontmatter `check_status:` is deliberately *crossed*
>    against the database verdict the test installs (`check_status: checked` on
>    a DB-unchecked hub, `check_status: unchecked` on a DB-checked one), so
>    neither test can be satisfied by reading the wrong check-status source and
>    neither arm can be mistaken for the other.
>    `test_write_accepts_a_schema_valid_hub_carrying_no_retired_field` is the
>    other direction: valid frontmatter still writes, keeps its ULID, and gains
>    the terminal section.
> 4. **Every branch is fixtured by a producer state, not by a hand-built
>    value.** Verdicts are installed through the shipped observe-then-judge
>    route (`state.record_observed_file_edit` + `state.set_concept_verdict`,
>    the same pair `trusted_writer.observe_pi_edit` and `integrity` use), which
>    covers the checked arm, the registered-unchecked arm, the unregistered
>    (no-database) arm, and the quarantined refusal. The section splitter's
>    four branches each have a fixture: no section, section-only body,
>    unterminated section (kept as curated text), and a body that quotes an
>    opener earlier than the terminal one. Two writer edge branches that the
>    plan's snippet carries silently are fixtured too — a curated body missing
>    its final newline (normalized once, asserted across two writes) and a hub
>    with no curated body at all (no leading blank line).
> 5. **The quarantine guard earns its place.** Without it, `stage_concept` →
>    `record_file_output(check_status="unchecked")` rewrites the verdict row,
>    silently releasing quarantined content;
>    `test_write_refuses_quarantined_hub_without_writing` asserts the same
>    whole-surface snapshot as the retired-field tests.
> 6. **`checks` cannot be discriminated by a valid value** —
>    `SUPPORTED_PROMOTION_CHECKS` is the singleton `{"memoria-runtime"}` — so
>    the passthrough is proved in its fail-closed direction instead
>    (`test_write_forwards_promotion_checks_to_the_checked_writer`).
> 7. **Mutation-tested: 22 mutants, 21 killed, 1 equivalent.** The survivor is
>    dropping the `curated and` conjunct from the trailing-newline
>    normalization. It is unobservable, not untested: when `curated` is empty
>    the mutant sets it to `"\n"`, and `frontmatter_doc` (`vaultio.py`) prepends
>    a newline to a body only when the body does not already start with one, so
>    the extra newline is absorbed as the one that terminates the closing `---`
>    line on every write path (`stage_concept`, `materialize_unchecked`, and
>    `_write_checked` all render through `write_frontmatter_doc`). The conjunct
>    is kept anyway so the writer's own "normalized exactly once" contract holds
>    at its call site rather than depending on another module's incidental
>    absorption. `test_write_on_a_hub_with_no_curated_body_writes_only_the_section`
>    is named for what it actually asserts, not for that conjunct.
> 8. **The snippet's trailing `if __name__ == "__main__": print(__doc__)` is
>    dropped.** Two of the forty `runtime/*.py` modules carry a main guard, both
>    because they are runnable entry points; this one is not.
> 9. **NID-C.6 cannot run against its current fixture.** See the blocking
>    amendment in that task's section.

**Files:**
- Create: `src/memoria_vault/runtime/hub_candidates.py`
- Modify: `src/memoria_vault/runtime/trusted_writer.py:632-660` (`mark_checked`
  gains an optional `body` parameter)
- Create: `tests/test_hub_candidates.py`
- Modify: `tests/conftest.py` (`TEST_LEVELS` dict at line 18: insert
  `"test_hub_candidates.py": "contract",` alphabetically before the existing
  `"test_hub_handoff.py": "contract",` entry at line 60 — nearest sibling's
  level)

**Interfaces:**
- Consumes:
  - `trusted_writer.stage_concept(vault, target_path, content, *, context, inputs=(), schemas_dir=None) -> dict` (`trusted_writer.py:663`)
  - `trusted_writer.materialize_unchecked(vault, target_path, *, context) -> dict` (`trusted_writer.py:743`)
  - `trusted_writer._write_checked(...)` via the extended `mark_checked`, using
    the standard fail-closed frontmatter validation.
  - `state.concept_check_status(vault, concept_id) -> str` (`state.py:1063`, returns `"unchecked"` for unregistered concepts)
  - `content_security.neutralize_untrusted_markdown_fragment(fragment) -> str` (`content_security.py:130` — the CS1 seam; the writer's machine-written region routes all free text through it)
  - `vaultio.frontmatter_doc`, `vaultio.split_frontmatter`
- Produces:
  - `hub_candidates.CANDIDATES_HEADING = "## Candidates"`,
    `hub_candidates.CANDIDATES_OPEN_PREFIX = "%%candidates: run="`,
    `hub_candidates.CANDIDATES_END = "%%end-candidates%%"`
  - `hub_candidates.candidate_entry(target_rel: str, reason: str, run_id: str) -> str`
  - `hub_candidates.render_candidates_section(run_id: str, entries: Sequence[str]) -> str`
  - `hub_candidates.split_candidates_section(body: str) -> tuple[str, str]`
  - `hub_candidates.write_hub_candidates(vault: Path, hub_rel: str, entries: Sequence[str], *, context: OperationContext, checks: Iterable[str] | None = None, inputs: Iterable[str | dict[str, Any]] = ()) -> dict[str, Any]`
  - `trusted_writer.mark_checked(vault, target_path, *, context, check="memoria-runtime", checks=None, schemas_dir=None, body: str | None = None) -> dict` (extended, backward compatible)

Behavior contract (used by NID-C.5 and NID-C.6): the section is the file's
*terminal* region; regeneration replaces it wholesale; the curated body above
it is preserved byte-for-byte (a curated body missing its final newline is
normalized to end with one exactly once, on the first write — the same
normalization `frontmatter_doc` (`vaultio.py:88-93`) already applies to every
trusted write). Check status is preserved: a checked hub is re-written checked
(`mark_checked` path, journal-backed hash); any other live hub is re-staged and
materialized unchecked (`stage_concept` + `materialize_unchecked`, also
journal-backed). Frontmatter is re-serialized only after it passes the normal
trusted-writer validation; retired fields are not stripped or normalized. Only
the *body* carries the byte-identical guarantee, per the spec's acceptance
criterion.

Steps:

- [x] Write the failing tests. Create `tests/test_hub_candidates.py`:
  *Applied: the snippet below is the seed; the shipped file is 21 tests, adding
  the branch fixtures and the fail-closed pair listed in the amendment above.*

  ```python
  from __future__ import annotations

  from pathlib import Path

  import pytest

  from memoria_vault.runtime import state
  from memoria_vault.runtime.hub_candidates import (
      candidate_entry,
      render_candidates_section,
      split_candidates_section,
      write_hub_candidates,
  )
  from memoria_vault.runtime.vaultio import sha256_file, split_frontmatter
  from tests.helpers import call_with_context, copy_memoria_dirs, init_git

  HUB_TEXT = (
      "---\n"
      "type: hub\n"
      "id: 01KBN6V6KX0000000000000007\n"
      "title: Framing\n"
      "tag: framing\n"
      "tags: []\n"
      "links: {}\n"
      "---\n"
      "# Framing\n"
      "\n"
      "Human text.\n"
  )


  def workspace(tmp_path: Path) -> Path:
      copy_memoria_dirs(tmp_path, "schemas", "config")
      init_git(tmp_path, "hub-candidates@example.invalid", "Hub Candidates")
      return tmp_path


  def write_hub(vault: Path, rel: str = "hubs/framing.md", text: str = HUB_TEXT) -> Path:
      path = vault / rel
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text(text, encoding="utf-8")
      return path


  def test_candidate_entry_neutralizes_reason_and_carries_run_attribution() -> None:
      entry = candidate_entry("digests/x.md", "reason with `ticks`", "run-1")

      assert entry.startswith("- [[digests/x.md]] — ")
      assert entry.endswith(" %%run=run-1%%")
      assert "`" not in entry


  def test_render_and_split_roundtrip() -> None:
      section = render_candidates_section(
          "run-1", ["- [[digests/x.md]] — r %%run=run-1%%"]
      )
      body = "# Hub\n\nCurated.\n" + section

      curated, found = split_candidates_section(body)

      assert curated == "# Hub\n\nCurated.\n"
      assert found == section
      assert section == (
          "## Candidates\n"
          "%%candidates: run=run-1%%\n"
          "- [[digests/x.md]] — r %%run=run-1%%\n"
          "%%end-candidates%%\n"
      )


  def test_split_without_section_returns_body_unchanged() -> None:
      body = "# Hub\n\nCurated.\n"
      assert split_candidates_section(body) == (body, "")


  def test_write_replaces_wholesale_and_body_survives_100_regenerations(
      tmp_path: Path,
  ) -> None:
      vault = workspace(tmp_path)
      hub = write_hub(vault)
      curated_body = split_frontmatter(HUB_TEXT)[1]

      call_with_context(
          write_hub_candidates,
          vault,
          "hubs/framing.md",
          [candidate_entry("digests/a.md", "first", "run-a")],
          run_id="run-a",
      )
      assert "%%candidates: run=run-a%%" in hub.read_text(encoding="utf-8")

      for round_number in range(100):
          call_with_context(
              write_hub_candidates,
              vault,
              "hubs/framing.md",
              [candidate_entry("digests/b.md", f"round {round_number}", "run-b")],
              run_id="run-b",
          )

      final_body = split_frontmatter(hub.read_text(encoding="utf-8"))[1]
      curated, section = split_candidates_section(final_body)
      assert curated == curated_body
      assert section.count("%%candidates:") == 1
      assert "digests/a.md" not in section
      assert "digests/b.md" in section
      assert section.rstrip("\n").endswith("%%end-candidates%%")


  def test_write_on_checked_hub_stays_checked_and_journal_backed(
      tmp_path: Path,
  ) -> None:
      vault = workspace(tmp_path)
      hub = write_hub(vault)
      state.record_observed_file_edit(
          vault, output_id="hubs/framing.md", concept_type="hub",
          output_sha256=sha256_file(hub),
      )
      state.set_concept_verdict(vault, "hubs/framing.md", "checked")

      event = call_with_context(
          write_hub_candidates,
          vault,
          "hubs/framing.md",
          [candidate_entry("digests/a.md", "r", "run-a")],
          run_id="run-a",
      )

      assert state.concept_check_status(vault, "hubs/framing.md") == "checked"
      assert event["event"] == "check-fired"
      body = split_frontmatter(hub.read_text(encoding="utf-8"))[1]
      assert body.startswith("# Framing\n\nHuman text.\n")


  def test_write_refuses_non_hub_target(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      note = vault / "notes/claim.md"
      note.parent.mkdir(parents=True, exist_ok=True)
      note.write_text(
          "---\ntype: note\ntitle: Claim\ntags: []\nlinks: {}\n---\nBody.\n",
          encoding="utf-8",
      )

      with pytest.raises(ValueError, match="not a hub"):
          call_with_context(
              write_hub_candidates, vault, "notes/claim.md", [], run_id="run-x"
          )
  ```

  Add a contract test with a retired frontmatter field (for example,
  `check_status`) on the target hub: `write_hub_candidates` must raise the
  trusted-writer validation error, leave the file byte-identical, and emit no
  event. It proves the unchecked staging path cannot silently normalize legacy
  input; run the same assertion through the checked path if that writer has a
  distinct validation boundary.

  (If `sha256_file` is not exported by `vaultio` at implementation time, import
  it from where `tests/floor_lib.py:105` imports it and adjust the single
  import line — verify with `grep -n "sha256_file" tests/floor_lib.py`.)

- [x] Register the test level: in `tests/conftest.py` `TEST_LEVELS` (line 18),
  insert `"test_hub_candidates.py": "contract",` immediately before
  `"test_hub_handoff.py": "contract",`. *Applied; the sibling entry has drifted
  to line 79.*

- [x] Run tests to verify they fail:
  `python -m pytest tests/test_hub_candidates.py -v`
  — expected failure: `ModuleNotFoundError: No module named
  'memoria_vault.runtime.hub_candidates'`. *Measured exactly that.*

- [x] Write minimal implementation. *The `trusted_writer` half below is already
  landed at HEAD (amendment item 1) — do not re-apply it; only the new module
  was created.* First, extend
  `trusted_writer.mark_checked` (`trusted_writer.py:632`): add the keyword
  `body: str | None = None` after `schemas_dir`, extend the docstring with
  `With ``body``, rewrite the Concept's body in the same checked write;
  frontmatter still comes from the live file.`, and change the tail
  (`trusted_writer.py:649-660`) to the normal checked-writer call below. The
  historical `allow_retired_input=True` variant is non-executable:

  ```python
      frontmatter, current_body = split_frontmatter(output_path.read_text(encoding="utf-8"))
      return _write_checked(
          vault,
          target,
          output_path,
          frontmatter,
          current_body if body is None else body,
          promotion_checks,
          context,
          contract,
      )
  ```

  Then create `src/memoria_vault/runtime/hub_candidates.py`:

  ```python
  """Hub Candidates block: the machine half of the wiki-ZK bridge (NODES §5).

  Hub files end with a delimited, machine-owned terminal section:

      ## Candidates
      %%candidates: run=<run_id>%%
      - [[digests/x.md]] — reason %%run=<run_id>%%
      %%end-candidates%%

  Writers replace the section wholesale; the curated body above it is never
  touched. Revert = delete the section (it regenerates). Accept = the PI moves
  a line into the body — a plain edit, observed as a PI edit.
  """

  from __future__ import annotations

  from collections.abc import Iterable, Sequence
  from pathlib import Path
  from typing import Any

  from memoria_vault.runtime import state
  from memoria_vault.runtime.content_security import neutralize_untrusted_markdown_fragment
  from memoria_vault.runtime.trusted_writer import (
      OperationContext,
      mark_checked,
      materialize_unchecked,
      stage_concept,
  )
  from memoria_vault.runtime.vaultio import frontmatter_doc, split_frontmatter

  CANDIDATES_HEADING = "## Candidates"
  CANDIDATES_OPEN_PREFIX = "%%candidates: run="
  CANDIDATES_END = "%%end-candidates%%"


  def candidate_entry(target_rel: str, reason: str, run_id: str) -> str:
      """One Candidates line: wikilink target, neutralized reason, run attribution."""
      safe_reason = neutralize_untrusted_markdown_fragment(reason)
      return f"- [[{target_rel}]] — {safe_reason} %%run={run_id}%%"


  def render_candidates_section(run_id: str, entries: Sequence[str]) -> str:
      """Render the delimited terminal section for one run's entries."""
      lines = "".join(f"{entry}\n" for entry in entries)
      return f"{CANDIDATES_HEADING}\n{CANDIDATES_OPEN_PREFIX}{run_id}%%\n{lines}{CANDIDATES_END}\n"


  def split_candidates_section(body: str) -> tuple[str, str]:
      """Split a hub body into (curated part, terminal Candidates section)."""
      opener = f"{CANDIDATES_HEADING}\n{CANDIDATES_OPEN_PREFIX}"
      if body.startswith(opener):
          index = 0
      else:
          found = body.rfind(f"\n{opener}")
          if found == -1:
              return body, ""
          index = found + 1
      section = body[index:]
      if not section.rstrip("\n").endswith(CANDIDATES_END):
          return body, ""
      return body[:index], section


  def write_hub_candidates(
      vault: Path,
      hub_rel: str,
      entries: Sequence[str],
      *,
      context: OperationContext,
      checks: Iterable[str] | None = None,
      inputs: Iterable[str | dict[str, Any]] = (),
  ) -> dict[str, Any]:
      """Replace hub_rel's terminal Candidates section wholesale.

      The curated body above the section is preserved byte-for-byte (a missing
      final newline is normalized once, as every trusted write already does).
      A checked hub is re-written checked; any other live hub is re-staged and
      materialized unchecked, so the block write never changes trust status.
      """
      vault = Path(vault)
      path = vault / hub_rel
      frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
      if frontmatter.get("type") != "hub":
          raise ValueError(f"candidates block target is not a hub: {hub_rel}")
      curated, _stale = split_candidates_section(body)
      if curated and not curated.endswith("\n"):
          curated += "\n"
      new_body = curated + render_candidates_section(context.run_id, entries)
      status = state.concept_check_status(vault, hub_rel)
      if status == "quarantined":
          raise ValueError(f"cannot write candidates into quarantined hub: {hub_rel}")
      if status == "checked":
          return mark_checked(vault, hub_rel, context=context, checks=checks, body=new_body)
      # Keep frontmatter unchanged: stage_concept validates it and fails closed
      # if it carries a retired field.
      event = stage_concept(
          vault,
          hub_rel,
          frontmatter_doc(frontmatter, new_body),
          context=context,
          inputs=inputs,
      )
      materialize_unchecked(vault, hub_rel, context=context)
      return event


  if __name__ == "__main__":
      print(__doc__)
  ```

- [x] Run tests to verify they pass:
  `python -m pytest tests/test_hub_candidates.py -v` — 21 passed.

- [x] Verify no trusted-writer regression:
  `python -m pytest tests/test_trusted_writer.py -q` if that file exists, else
  `python -m pytest tests/test_journal_trust.py tests/test_operations.py -q`.
  *`tests/test_trusted_writer.py` exists; ran it and the fallback pair, then
  the full `python scripts/verify`.*

- [ ] Commit:
  ```
  git add src/memoria_vault/runtime/hub_candidates.py src/memoria_vault/runtime/trusted_writer.py tests/test_hub_candidates.py tests/conftest.py
  git commit -m "feat: hub Candidates block writer with wholesale-replace terminal section (NODES §5)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task NID-C.4: Deterministic co-citation ranking over `work_graph_edges`

**Files:**
- Modify: `src/memoria_vault/runtime/state.py` (new function after
  `replace_work_graph_edges`, i.e. after line 1837)
- Modify: `tests/test_hub_candidates.py` (ranking tests live with their consumer)

**Interfaces:**
- Consumes: `work_graph_edges` table exactly as shipped (`schema.sql:171-186`):
  columns `work_id TEXT`, `relation_type TEXT` (CHECK roster includes
  `'references'`), `target_id TEXT`, `target_title`, `target_doi`,
  `source_provider`, `raw_json`, `discovered_at`; PK
  `(work_id, relation_type, target_id)`. `state.connect`, `state._work_id`.
- Produces:
  `state.related_work_candidates(vault: Path, work_ids: Sequence[str], limit: int) -> list[dict[str, Any]]`
  — rows `{"work_id": str, "shared_references": int}`, ranked by count of
  distinct shared `references` targets with the given work set
  (co-citation / bibliographic coupling), descending, tie-broken by
  `work_id` ascending; deterministic; empty input or `limit <= 0` returns `[]`.

> **Amendment — the set binding and the six-test split (2026-08-01, applied).**
> Verified by content at `be6d317e`:
>
> 1. **The work-id set binds through `json_each(?)`, not generated `?`
>    placeholders.** The plan's `IN ({placeholders})` form is an f-string SQL
>    statement, which ruff's bandit rule `S608` flags; the repo carries no
>    `noqa: S608` anywhere and already has the idiom this needs —
>    `state.py`'s own `concept_id NOT IN (SELECT value FROM json_each(?))`
>    and five sites in `graph_sql.py`. The query is now static text with
>    three bound parameters (`_json(ids)`, `_json(ids)`, `limit`).
> 2. **One consequence to keep in mind:** with `json_each('[]')` the empty
>    work set already yields no rows, so the `not ids` half of the early
>    return is a short-circuit rather than a syntax-error guard. It stays —
>    it keeps "empty work set returns `[]`" a statement of this function and
>    avoids opening the database for a no-op read. The `limit <= 0` half is
>    load-bearing either way: SQLite reads `LIMIT -1` as *unlimited*.
> 3. **The plan's two tests became six, one branch each.** The plan's fixture
>    uses `references` edges only and a disjoint hub work set, so four
>    mutations of the shipped SQL survive it: dropping either side's
>    `relation_type = 'references'`, `COUNT(DISTINCT ...)` → `COUNT(...)`, and
>    the input `_work_id`/blank-id normalization. The shipped tests add a
>    mixed-relation graph, an overlapping hub work set, and a normalization
>    case, and split the plan's bundled `limit`/empty assertions into tests
>    named for what they exercise.
> 4. **Mutation-tested: 16 mutants, 10 killed, 6 equivalent survivors** —
>    dropping the `not ids` short-circuit, `limit <= 0` → `limit < 0`
>    (`LIMIT 0` returns nothing either way), `sorted(...)` and the set
>    comprehension around the id set (neither changes an `IN`-set result),
>    and the `str()`/`int()` row coercions (the columns are already `TEXT`
>    and a `COUNT`). All six are unobservable; the coercions match the
>    module's established row-projection style.

Steps:

- [x] Write the failing tests. Append to `tests/test_hub_candidates.py`:
  *Applied: the snippet below is the seed; the shipped set is six tests, per
  the amendment above.*

  ```python
  def _reference_edges(*targets: str) -> list[dict[str, str]]:
      return [{"relation_type": "references", "target_id": target} for target in targets]


  def test_related_work_candidates_ranks_by_shared_references(tmp_path: Path) -> None:
      vault = tmp_path
      state.replace_work_graph_edges(vault, "hub-work-1", _reference_edges("W1", "W2", "W3"))
      state.replace_work_graph_edges(vault, "hub-work-2", _reference_edges("W4"))
      state.replace_work_graph_edges(vault, "cand-strong", _reference_edges("W1", "W2", "W4"))
      state.replace_work_graph_edges(vault, "cand-weak", _reference_edges("W3"))
      state.replace_work_graph_edges(vault, "cand-none", _reference_edges("W9"))

      rows = state.related_work_candidates(vault, ["hub-work-1", "hub-work-2"], 5)

      assert rows == [
          {"work_id": "cand-strong", "shared_references": 3},
          {"work_id": "cand-weak", "shared_references": 1},
      ]
      assert state.related_work_candidates(vault, ["hub-work-1", "hub-work-2"], 1) == [
          {"work_id": "cand-strong", "shared_references": 3},
      ]
      assert state.related_work_candidates(vault, [], 5) == []
      assert state.related_work_candidates(vault, ["hub-work-1"], 0) == []


  def test_related_work_candidates_breaks_ties_by_work_id(tmp_path: Path) -> None:
      vault = tmp_path
      state.replace_work_graph_edges(vault, "hub-work-1", _reference_edges("W1"))
      state.replace_work_graph_edges(vault, "cand-b", _reference_edges("W1"))
      state.replace_work_graph_edges(vault, "cand-a", _reference_edges("W1"))

      rows = state.related_work_candidates(vault, ["hub-work-1"], 5)

      assert [row["work_id"] for row in rows] == ["cand-a", "cand-b"]
  ```

- [x] Run tests to verify they fail:
  `python -m pytest tests/test_hub_candidates.py -k related_work_candidates -v`
  — expected failure: `AttributeError: module 'memoria_vault.runtime.state'
  has no attribute 'related_work_candidates'`. *Measured exactly that, on all
  seven of the appended cases.*

- [x] Write minimal implementation. In `src/memoria_vault/runtime/state.py`,
  after `replace_work_graph_edges` (drifted to `:2102`), add the function
  below — with the `json_each(?)` set binding of the amendment above in place
  of the generated placeholders:

  ```python
  def related_work_candidates(
      vault: Path, work_ids: Sequence[str], limit: int
  ) -> list[dict[str, Any]]:
      """Rank other catalog works by shared 'references' targets with a work set."""
      ids = sorted({_work_id(work_id) for work_id in work_ids if str(work_id).strip()})
      if not ids or limit <= 0:
          return []
      placeholders = ",".join("?" for _ in ids)
      with connect(vault) as conn:
          rows = conn.execute(
              f"""
              SELECT other.work_id AS work_id,
                     COUNT(DISTINCT other.target_id) AS shared_references
              FROM work_graph_edges AS mine
              JOIN work_graph_edges AS other
                ON other.relation_type = 'references'
               AND other.target_id = mine.target_id
              WHERE mine.relation_type = 'references'
                AND mine.work_id IN ({placeholders})
                AND other.work_id NOT IN ({placeholders})
              GROUP BY other.work_id
              ORDER BY shared_references DESC, other.work_id ASC
              LIMIT ?
              """,
              (*ids, *ids, limit),
          ).fetchall()
      return [
          {"work_id": str(row["work_id"]), "shared_references": int(row["shared_references"])}
          for row in rows
      ]
  ```

  If `Sequence` is not already imported in `state.py`'s
  `collections.abc` import line, add it there (check with
  `grep -n "from collections.abc" src/memoria_vault/runtime/state.py`).
  *It was not; `Sequence` was appended to the existing
  `from collections.abc import Iterable, Mapping` line.*

- [x] Run tests to verify they pass:
  `python -m pytest tests/test_hub_candidates.py -v` — 28 passed.

- [ ] Commit:
  ```
  git add src/memoria_vault/runtime/state.py tests/test_hub_candidates.py
  git commit -m "feat: deterministic co-citation ranking over work_graph_edges (NODES §5)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task NID-C.5: `digest-related-works` operation (manifest, dispatch, floor)

**Files:**
- Create: `src/memoria_vault/product/capabilities/operations/digest-related-works.md`
- Modify: `src/memoria_vault/runtime/operations.py` (new
  `digest_related_works` + `_hub_work_ids` after `compile_source_digest`'s
  return, currently ending near line 645; extend the `vaultio` import block at
  lines 35-41 with `read_frontmatter`; add
  `from memoria_vault.runtime.hub_candidates import candidate_entry, write_hub_candidates`)
- Modify: `src/memoria_vault/runtime/worker.py` (new dispatch branch inserted
  after the `compile-source-digest` branch's return at line 405)
- Modify: `tests/floor_lib.py` (`OPERATION_REGISTRY` at line 450: new entry,
  alphabetically after the `curate-note-candidate` entry ending at line 742)
- Create: `tests/fixtures/floor/goldens/digest-related-works.json`
  (**golden addition** — generated, reviewed, committed)
- Modify: `tests/fixtures/floor/goldens/regenerate-capability-index.json`
  (regenerated — the new manifest changes the rendered capability index)
- Modify: `docs/reference/commands-and-transports/system-actions.md:26`
  (operation-manifest roster line, kept in sync by hand per that page's
  own header)
- Modify: `docs/reference/commands-and-transports/system-actions-operations.md`
  (new table row after the "Compile source digest" row at line 105)
- Modify: `tests/test_hub_candidates.py` (operation-level test)

**Interfaces:**
- Consumes:
  - `hub_candidates.candidate_entry` / `hub_candidates.write_hub_candidates` (NID-C.3)
  - `state.related_work_candidates` (NID-C.4)
  - `operations.load_operation_policy` (`operations.py:103`; the packaged
    reader injects `DEFAULT_RUNNER_POLICY` when a manifest omits `runner:` —
    `capabilities.py:157-163` — so the deterministic manifest declares none)
  - `operations._require_tool` (`operations.py:825`),
    `required_promotion_checks` (`operations.py:315`),
    `require_policy_path`/`normalize_path` (`policy/paths.py`),
    `operations._topic_slug` (`operations.py:849`)
  - `trusted_writer.append_journal_event`, `commit_writer_changes`,
    `validate_operation_context`
  - floor harness contract: `tests/floor_lib.py` `OPERATION_REGISTRY` +
    `tests/test_floor_coverage.py::test_every_operation_has_a_floor_entry`
    (manifest without floor entry fails) +
    `tests/test_capabilities.py::test_worker_operations_are_cataloged_and_policy_shaped`
    (manifest without worker dispatch fails, and vice versa)
- Produces:
  - `operations.digest_related_works(vault: Path, hub_path: str, *, context: OperationContext, k: int = 5, operation_id: str = "digest-related-works") -> dict[str, Any]`
    — returns `{"run_id": str, "hub_path": str, "candidates": list[dict], "started": dict, "finished": dict, "event": dict, "commit": str}`
  - `operations._hub_work_ids(vault: Path, hub_tag: str) -> list[str]`
  - worker payload contract: `{"hub_path": str (required), "k": int >= 1 (optional, default 5)}`;
    worker result `{"commit", "hub_path", "candidates"}`
  - operation id `digest-related-works` (agent-runnable; not added to
    `PROTECTED_OPERATION_ACTORS`)

> **Amendment — measured anchors, the extra tests, and the goldens
> (2026-08-01, applied).** Verified by content at `be6d317e`:
>
> 1. **Every anchor in the Files list had drifted; all were resolved by
>    content, not by line number.** `compile_source_digest`'s closing `return`
>    is near `:745` (not 645), the worker's `compile-source-digest` branch
>    returns at `:409` (not 405), the `curate-note-candidate` floor entry ends
>    at `:736` (not 742), and the "Compile source digest" docs row is at
>    `:114` (not 105). The code landed exactly as the plan writes it.
> 2. **The floor entry's comment is corrected on one fact.** The seed *does*
>    have a `digests/` directory (`memoria init` creates the bundle homes); it
>    is empty. Confirmed live on a real seeded vault: status `done`,
>    `candidates == []`, `hubs/floor-hub.md` still `unchecked`, and the
>    curated `Seed body.` intact above an empty delimited block.
> 3. **Goldens moved, as the plan predicts (contract 8).**
>    `tests/fixtures/floor/goldens/digest-related-works.json` is new, and
>    `regenerate-capability-index.json` moved by exactly one line — the
>    `.memoria/index/capability-index.json` hash, because the new manifest
>    joins the rendered index. No other golden changed.
> 4. **The operation test became eight, because one test leaves the
>    operation's own branches unfixtured.** Beyond the plan's ranked-block
>    test: the hub's work set is scanned off the filesystem, so a test
>    produces the messy `digests/` a PI edit can leave (a foreign `type:`, a
>    scalar `tags:`, a blank `tags:`, a blank `work_id:`, an off-tag digest)
>    and pins the resulting `inputs` list; three refusals are asserted as
>    whole-surface no-writes (non-hub target, a path outside `allowed_paths`,
>    an unbound request context) plus the honest `FileNotFoundError` for a
>    missing hub — `safe_read` returns `""` for a missing file, so without
>    that guard the type check would report "not a hub" about a file that
>    does not exist; and the worker payload contract (`k` honored, `k`
>    defaulting to five, `k` refused for `0`, `-1`, `True`, `"5"`) is run
>    through the real queue.
> 5. **Mutation-tested: 29 mutants, 23 killed, 6 survivors.** Survivors, all
>    judged: `if not hub_tag: return []` and `if not digests_dir.is_dir():
>    return []` (unobservable — `Path.glob` on a missing directory is already
>    empty, and a tagless hub matches no digest and then fails schema
>    validation at the write); `checks=promotion_checks` → `checks=None`
>    (equivalent while `required_checks` is the singleton `memoria-runtime`
>    that `normalize_promotion_checks` also defaults to); the top-of-function
>    `validate_operation_context` (defence in depth — `append_journal_event`
>    validates the same context before the first side effect, so the refusal
>    and the no-write both still hold); `_require_tool` (manifest-dependent,
>    unkillable without a fake manifest); and the worker's blank-`hub_path`
>    guard (the run is refused either way, with a less honest message).
>    `sorted(work_ids)` is killed only probabilistically: the mutant's
>    set-iteration order is per-process hash-randomized, so the `inputs`
>    assertion catches it on roughly half of runs.

Steps:

- [x] Write the failing catalog-parity state: create
  `src/memoria_vault/product/capabilities/operations/digest-related-works.md`:

  ```markdown
  ---
  title: Digest related works
  type: operation
  description: Deterministically rank co-cited catalog works for one hub and rewrite
    its machine Candidates block.
  operation_id: digest-related-works
  allowed_tools:
  - trusted_writer
  allowed_paths:
  - catalog/
  - digests/
  - hubs/
  - .memoria/journal/
  allowed_network: []
  prompt_version: digest-related-works.v1
  io_schema:
    input: hub_path
    output: hub_candidates_block
  risk_class: low
  required_checks:
  - memoria-runtime
  tags:
  - graph
  - hubs
  id: operations/digest-related-works
  links: {}
  ---

  # Operation

  Rank the top-k catalog works sharing `references` targets with this hub's
  works (`work_graph_edges` co-citation — no model judgment) and replace the
  hub's terminal machine Candidates block wholesale. The curated body above
  the block is never touched.
  ```

  And add the floor entry to `tests/floor_lib.py` `OPERATION_REGISTRY`,
  alphabetically after the `curate-note-candidate` entry (line 742):

  ```python
      # worker.py dispatch pops hub_path (required str) and optional k
      # (positive int, default 5), dispatching to
      # operations.py:digest_related_works — fully deterministic (SQL over
      # work_graph_edges, no model call, no network). The seed hub
      # (hubs/floor-hub.md, tag "floor-seed") has no digests tagged into it,
      # so its work set is empty and the run writes an empty, delimited
      # Candidates block and finishes "done"; the hub was created unchecked
      # (create-concept materializes without promotion), so the block write
      # takes the status-preserving unchecked path.
      "digest-related-works": {
          "payload": {"hub_path": "{hub}"},
          "expect": "done",
      },
  ```

- [x] Run tests to verify they fail:
  `python -m pytest tests/test_capabilities.py::test_worker_operations_are_cataloged_and_policy_shaped "tests/test_floor_sweep_operations.py::test_operation[digest-related-works]" -v`
  — expected failures: the capabilities parity test fails with
  `digest-related-works` in `catalog_ids` but not `worker_ids`; the floor
  sweep case fails with worker status `failed` /
  `unsupported operation: 'digest-related-works'` (`worker.py:1090`).
  *Measured both.*

- [x] Write the failing operation-level test. Append to
  `tests/test_hub_candidates.py` (add
  `from memoria_vault.runtime.operations import digest_related_works`
  to its imports — the plan's `as _digest_related_works` alias collides with
  nothing in that file, and `call_with_context` derives the operation id from
  `function.__name__`, which the alias does not change):

  ```python
  def test_digest_related_works_writes_ranked_candidates_block(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      hub = write_hub(vault)
      digest = vault / "digests/hub-work-1.md"
      digest.parent.mkdir(parents=True, exist_ok=True)
      digest.write_text(
          "---\ntype: digest\nid: hub-work-1\ntitle: Digest one\n"
          "tags: [Framing]\nlinks: {}\nwork_id: hub-work-1\n---\nBody.\n",
          encoding="utf-8",
      )
      state.replace_work_graph_edges(vault, "hub-work-1", _reference_edges("W1", "W2", "W3"))
      state.replace_work_graph_edges(vault, "cand-strong", _reference_edges("W1", "W2"))
      state.replace_work_graph_edges(vault, "cand-weak", _reference_edges("W3"))

      result = call_with_context(
          _digest_related_works, vault, "hubs/framing.md", run_id="rank-run"
      )

      assert [row["work_id"] for row in result["candidates"]] == [
          "cand-strong",
          "cand-weak",
      ]
      body = split_frontmatter(hub.read_text(encoding="utf-8"))[1]
      curated, section = split_candidates_section(body)
      assert curated == "# Framing\n\nHuman text.\n"
      assert "%%candidates: run=rank-run%%" in section
      assert (
          "- [[catalog/sources/cand-strong]] — co-cites 2 shared references "
          "with this hub's works %%run=rank-run%%"
      ) in section
      assert result["commit"]
  ```

  Run it to verify it fails:
  `python -m pytest tests/test_hub_candidates.py::test_digest_related_works_writes_ranked_candidates_block -v`
  — expected failure: `ImportError: cannot import name 'digest_related_works'`.
  *Measured exactly that (a collection error, since the import is at module
  scope). The shipped set is eight cases, per the amendment above.*

- [x] Write minimal implementation. In `operations.py`, add
  `read_frontmatter` to the `vaultio` import block (drifted to lines 38-45)
  and
  `from memoria_vault.runtime.hub_candidates import candidate_entry, write_hub_candidates`
  below the `content_security` import. After `compile_source_digest`'s
  closing `return`, add:

  ```python
  def _hub_work_ids(vault: Path, hub_tag: str) -> list[str]:
      """Work ids of digests whose slugified tags include the hub's tag."""
      if not hub_tag:
          return []
      digests_dir = vault / "digests"
      if not digests_dir.is_dir():
          return []
      work_ids = set()
      for path in sorted(digests_dir.glob("*.md")):
          frontmatter = read_frontmatter(path)
          if frontmatter.get("type") != "digest":
              continue
          tags = frontmatter.get("tags")
          if not isinstance(tags, list):
              continue
          if any(_topic_slug(str(tag)) == hub_tag for tag in tags):
              work_id = str(frontmatter.get("work_id") or "").strip()
              if work_id:
                  work_ids.add(work_id)
      return sorted(work_ids)


  def digest_related_works(
      vault: Path,
      hub_path: str,
      *,
      context: OperationContext,
      k: int = 5,
      operation_id: str = "digest-related-works",
  ) -> dict[str, Any]:
      """Refresh one hub's machine Candidates block from work-graph co-citation."""
      validate_operation_context(vault, context)
      vault = Path(vault)
      policy = load_operation_policy(vault, operation_id)
      _require_tool(policy, "trusted_writer")
      promotion_checks = required_promotion_checks(policy)
      hub_rel = normalize_path(hub_path)
      require_policy_path(policy, hub_rel)
      hub_file = vault / hub_rel
      if not hub_file.is_file():
          raise FileNotFoundError(hub_file)
      hub_frontmatter = read_frontmatter(hub_file)
      if hub_frontmatter.get("type") != "hub":
          raise ValueError(f"digest-related-works target is not a hub: {hub_rel}")

      started = append_journal_event(
          vault,
          {"event": "run", "workflow": operation_id, "status": "started"},
          context=context,
      )
      work_ids = _hub_work_ids(vault, str(hub_frontmatter.get("tag") or "").strip())
      ranked = state.related_work_candidates(vault, work_ids, k)
      entries = [
          candidate_entry(
              f"catalog/sources/{row['work_id']}",
              f"co-cites {row['shared_references']} shared references with this hub's works",
              context.run_id,
          )
          for row in ranked
      ]
      event = write_hub_candidates(
          vault,
          hub_rel,
          entries,
          context=context,
          checks=promotion_checks,
          inputs=[f"catalog/sources/{work_id}" for work_id in work_ids],
      )
      finished = append_journal_event(
          vault,
          {"event": "run", "workflow": operation_id, "status": "done", "outputs": [hub_rel]},
          context=context,
      )
      commit = commit_writer_changes(
          vault, f"digest related works {hub_rel}", [hub_rel], context=context
      )
      return {
          "run_id": context.run_id,
          "hub_path": hub_rel,
          "candidates": ranked,
          "started": started,
          "finished": finished,
          "event": event,
          "commit": commit,
      }
  ```

  In `worker.py`, insert after the `compile-source-digest` branch's `return`
  (drifted to `:409`), matching the surrounding if-chain style:

  ```python
      if operation_id == "digest-related-works":
          from memoria_vault.runtime.operations import digest_related_works

          hub_path = str(payload.get("hub_path") or "").strip()
          if not hub_path:
              raise ValueError("digest-related-works requires hub_path")
          limit = payload.get("k", 5)
          if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
              raise ValueError("digest-related-works k must be a positive integer")
          result = digest_related_works(vault, hub_path, context=context, k=limit)
          return {
              "commit": result["commit"],
              "hub_path": result["hub_path"],
              "candidates": result["candidates"],
          }
  ```

- [x] Run tests to verify they pass:
  `python -m pytest tests/test_hub_candidates.py tests/test_capabilities.py -v`
  — 40 + 12 passed.

- [x] Generate the new floor golden plus the drifted capability-index golden
  (**golden addition noted here in the manifest**, per the floor harness's
  opt-in update contract at `tests/floor_lib.py:331-355`):
  `MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest "tests/test_floor_sweep_operations.py::test_operation[digest-related-works]" "tests/test_floor_sweep_operations.py::test_operation[regenerate-capability-index]" -v`
  Review `git diff tests/fixtures/floor/goldens/` (one new file, one
  capability-index hash change), then re-run both without the env var and
  confirm they pass; also run
  `python -m pytest tests/test_floor_coverage.py -v`.
  *Measured exactly one new file and exactly one changed line — the
  `.memoria/index/capability-index.json` hash. Both re-run clean without the
  env var; `test_floor_coverage.py` passes.*

- [x] Update the hand-maintained docs. In
  `docs/reference/commands-and-transports/system-actions.md:26`, insert
  `` `digest-related-works` `` into the alphabetical roster (after
  `` `curate-note-link` ``, before `` `enrich-source` ``). In
  `docs/reference/commands-and-transports/system-actions-operations.md`, add
  after the "Compile source digest" row (drifted to `:114`):

  ```markdown
  | Digest related works | worker operation `digest-related-works` + runtime helper (`digest_related_works`) | Deterministically ranks co-cited catalog Works (shared `references` targets in `work_graph_edges`) against one hub's works and replaces the hub's terminal machine Candidates block wholesale; the curated body above the block is never touched. |
  ```

  Verify: `python scripts/checks/doc_claims_gate.py` prints
  `doc-claims-gate: clean`.

- [ ] Commit:
  ```
  git add src/memoria_vault/product/capabilities/operations/digest-related-works.md src/memoria_vault/runtime/operations.py src/memoria_vault/runtime/worker.py tests/floor_lib.py tests/fixtures/floor/goldens/digest-related-works.json tests/fixtures/floor/goldens/regenerate-capability-index.json docs/reference/commands-and-transports/system-actions.md docs/reference/commands-and-transports/system-actions-operations.md tests/test_hub_candidates.py
  git commit -m "feat: digest-related-works — deterministic co-citation Candidates for hubs (NODES §5)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task NID-C.6: Wire compile-source-digest's hub suggestions through the block writer

> **Amendment — the curated-hub fixture must be rewritten before this task runs
> (2026-08-01, blocking).** This task's fixture and NID-C.3's binding
> clean-slate override cannot both pass as written. The override (2026-07-30,
> and the newer text) makes frontmatter carrying a retired field invalid input
> that "must fail closed without a write" and forbids a retired-field stripping
> normalizer. This task's fixture keeps `check_status: checked` on
> `hubs/framing.md` "deliberately to exercise the writer's retired-field pop"
> and then asserts `"check_status" not in read_frontmatter(curated_hub)`.
>
> **There is no pop.** NID-C.3 shipped the override as written: the block write
> reaches `stage_concept` → `_validate_concept`, which raises `retired
> frontmatter field is ignored: check_status` before anything is written. So
> `compile_source_digest` aborts on the framing hub, no Candidates section is
> written, and `result["hub_suggestions"] == ["hubs/framing.md"]` is
> unreachable. C.3 is not weakened to keep this fixture alive.
>
> **Required rewrite, before this task's first step:**
>
> 1. Drop the `"check_status: checked\n"` line from `curated_text` — the
>    fixture becomes a schema-valid curated hub (`hub.yaml` still requires
>    `tag`, which it already carries).
> 2. Drop `assert "check_status" not in read_frontmatter(curated_hub)`. It
>    asserts a transform that no longer exists; with the field gone from the
>    fixture, the assertion is vacuous rather than wrong, which is worse.
> 3. Keep `assert "check_status" not in promoted_hub_fm` — `hubs/methods.md`
>    is created by this run and never carried the field, so that assertion is
>    about the writer's own output, not about admitting legacy input.
>
> The retired-field behavior this fixture meant to exercise is covered instead
> by `tests/test_hub_candidates.py`'s
> `test_write_refuses_retired_frontmatter_field_on_{unchecked,checked}_hub_without_writing`,
> which assert the refusal *and* that nothing was written on either writer
> boundary. Nothing else in this task changes.

> **Execution amendment — the doc half is split, and four assertions were added
> (2026-08-02, as landed).** Verified by content at `a1d815c9`:
>
> 1. **The runtime change landed whole; the manifest edit did not.** The wave's
>    floor-golden token (contract 8) was held by another session, so the two
>    steps that move `tests/fixtures/floor/goldens/` were deliberately not
>    executed. Measured, not assumed: with the manifest edit applied,
>    `test_operation[regenerate-capability-index]` drifts and
>    `test_operation[compile-source-digest]` stays green — exactly the split the
>    Files list predicts. The manifest edit was then reverted, and the landed
>    tree leaves `tests/fixtures/floor/goldens/` byte-identical with the full
>    `python scripts/verify` green.
>
>    **Remaining obligation for the next golden-token holder** (the whole of it;
>    no other file is involved): apply the two text replacements to
>    `src/memoria_vault/product/capabilities/operations/compile-source-digest.md`
>    exactly as the "Update the operation doc" step below writes them, then
>    `MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest
>    "tests/test_floor_sweep_operations.py::test_operation[regenerate-capability-index]"`.
>    The expected diff is one line: the `.memoria/index/capability-index.json`
>    hash. Until then the manifest's `description` and its Pattern tail still say
>    "curated hub changes stay as suggestions", which the code no longer does.
> 2. **The `docs/reference` half of that step *was* applied** — the
>    `system-actions-operations.md` row is a published-docs edit with no golden
>    coupling, so leaving it stale had no upside. The step below stays unticked
>    because only half of it ran.
> 3. **The fixture rewrite followed the 2026-08-01 blocking amendment, not the
>    Step-1 snippet.** `check_status: checked` is absent from `curated_text` and
>    the `assert "check_status" not in read_frontmatter(curated_hub)` line is
>    replaced by `assert read_frontmatter(curated_hub)["description"] ==
>    "Human curation."` — the curated *frontmatter* survives the block write,
>    which is the property that assertion was reaching for and which the
>    retired-field version could not state. The step's printed snippet is
>    non-executable; it is left verbatim so the amendment above still has
>    something to point at.
> 4. **`assert curated_hub.read_text(...) == curated_text` is gone.** The plan's
>    replacement block drops it silently; recorded here because it was the old
>    test's whole "curated hubs are not overwritten" claim, and it is now
>    carried by `curated_body == "# Framing\n\nHuman text.\n"` out of
>    `split_candidates_section` — a stronger statement, since it survives the
>    file being rewritten.
> 5. **Four assertions beyond the plan's, each added to kill a measured
>    survivor:** `events[4]["output_id"]`, the full `events[4]["inputs"]` rows
>    (both `id` *and* `sha256`, cross-checked against the digest's own check
>    event and the digest-stage event — the id-only projection let three
>    `hub_inputs` mutants live), `result["hub_events"][0]["output_id"]`, and
>    `len(result["hub_events"]) == 5`. `hub_events` has no reader outside
>    `operations.py`, so without the last two the block-write event could be
>    dropped from the result contract undetected.
> 6. **Reader audit of the changed field (per the recurring two-reader
>    divergence class, issue #1670): four readers, all checked before the writer
>    changed.** `hub_suggestions` leaves `compile_source_digest` by three routes
>    — the `run/done` journal event's `"suggestions"` key
>    (`operations.py`), the result dict, and the worker's result passthrough
>    (`worker.py`) — plus one indirect reader, `cli.py`'s generic result
>    summariser, which reads `container.get("suggestions")` for its **length
>    only** and so cannot observe the domain change. No reader interprets the
>    value as a staging id. The values additionally take on a **fourth role**
>    this task creates: they are now spliced into `commit_writer_changes`' path
>    list, so the domain had to move from staging id to vault-relative path for
>    that splice to be correct — the two are not interchangeable, which is why
>    `M08` (append a `.memoria/staging/...` shape) is a killed mutant rather
>    than a stylistic one.
> 7. **Mutation-tested: 22 mutants, 21 killed, 1 survivor.** The survivor is
>    `checks=promotion_checks` → `checks=None` on the `write_hub_candidates`
>    call — provably equivalent, and the same survivor NID-C.5 judged:
>    `required_promotion_checks` resolves this manifest's singleton
>    `required_checks` to `["memoria-runtime"]`, which is exactly what
>    `normalize_promotion_checks(None)` defaults to. It is doubly unobservable
>    here, because the fixture's curated hub is unchecked and `checks` reaches
>    only the `mark_checked` branch.

**Files:**
- Modify: `src/memoria_vault/runtime/operations.py:584-618` (the existing-hub
  branch of `compile_source_digest`'s hub loop) and `:631-633` (commit paths)
- Modify: `tests/test_operations.py:147-234`
  (`test_compile_source_digest_traces_model_call_and_stages_hub_suggestions`)
- Modify: `src/memoria_vault/product/capabilities/operations/compile-source-digest.md`
  (description lines 4-5 and Pattern body last sentence)
- Modify: `docs/reference/commands-and-transports/system-actions-operations.md:105`
  (row tail: "stages hub suggestions" claim)
- Modify: `tests/fixtures/floor/goldens/regenerate-capability-index.json`
  (regenerated — manifest text edit changes the rendered index; the
  `compile-source-digest.json` golden itself is stable because the floor
  seed has no pre-existing hubs matching the sweep's five topics)

**Interfaces:**
- Consumes: `hub_candidates.candidate_entry` / `write_hub_candidates`
  (NID-C.3), plus everything `compile_source_digest` already uses.
- Produces: changed `compile_source_digest` result contract —
  `result["hub_suggestions"]` becomes the list of **existing hub rels that
  received a Candidates block** (previously: staging ids of suggestion
  copies), and those hub rels are included in the operation's commit; the
  journal `run/done` event keeps its `"suggestions"` key with the new values.
  Worker passthrough (`worker.py:399-405`) is shape-compatible and unchanged.
  New hubs are created exactly as before (stage + promote, machine-owned
  body). No suggestion copy is left in `.memoria/staging/hubs/` anymore.

Steps:

- [x] Update the test first. In `tests/test_operations.py:159-165`, replace
  the curated-hub fixture text with a schema-valid curated hub (hub.yaml
  requires `tag`; the retired `check_status:` field is kept deliberately to
  exercise the writer's retired-field pop):

  ```python
      curated_hub = vault / "hubs/framing.md"
      curated_hub.parent.mkdir(parents=True)
      curated_text = (
          "---\ntype: hub\nid: 01KBN6V6KX0000000000000002\n"
          "check_status: checked\ntitle: Framing\ntag: framing\n"
          "tags: []\nlinks: {}\ndescription: Human curation.\n---\n"
          "# Framing\n\nHuman text.\n"
      )
      curated_hub.write_text(curated_text, encoding="utf-8")
  ```

  Then replace the suggestion assertions (`tests/test_operations.py:188-198`)
  with (add `from memoria_vault.runtime.vaultio import split_frontmatter` and
  `from memoria_vault.runtime.hub_candidates import split_candidates_section`
  to the file's imports):

  ```python
      assert result["hub_suggestions"] == ["hubs/framing.md"]
      hub_body = split_frontmatter(curated_hub.read_text(encoding="utf-8"))[1]
      curated_body, section = split_candidates_section(hub_body)
      assert curated_body == "# Framing\n\nHuman text.\n"
      assert "%%candidates: run=compile-alpha%%" in section
      assert (
          "- [[digests/source-alpha.md]] — suggested hub update from this digest "
          "%%run=compile-alpha%%"
      ) in section
      assert "check_status" not in read_frontmatter(curated_hub)

      staged_hub = vault / ".memoria/staging/hubs/framing.md"
      assert not staged_hub.exists()
      promoted_hub = vault / "hubs/methods.md"
      promoted_hub_fm = read_frontmatter(promoted_hub)
      assert "check_status" not in promoted_hub_fm
      assert promoted_hub_fm["tag"] == "methods"
      assert state.concept_check_status(vault, "hubs/methods.md") == "checked"
  ```

  Keep the event-sequence assertion at `tests/test_operations.py:201-216`
  unchanged (the framing hub's block write takes the unchecked path —
  `state.concept_check_status` returns `"unchecked"` for the hand-written
  file — so it still emits exactly one `derived` event in the same position),
  keep `events[-1]["suggestions"] == result["hub_suggestions"]`, and extend
  the committed-paths assertion at `tests/test_operations.py:227-234` to:

  ```python
      assert committed == {
          state.JOURNAL_HEAD_REL,
          "digests/source-alpha.md",
          "hubs/framing.md",
          "hubs/gaps.md",
          "hubs/impact.md",
          "hubs/methods.md",
          "hubs/outcomes.md",
      }
  ```

- [x] Run test to verify it fails:
  `python -m pytest tests/test_operations.py::test_compile_source_digest_traces_model_call_and_stages_hub_suggestions -v`
  — expected failure: `assert result["hub_suggestions"] == ["hubs/framing.md"]`
  (current code returns the staging id, and the curated hub file carries no
  Candidates section).

- [x] Write minimal implementation. In `operations.py:584-618`, replace the
  hub loop's existing-hub handling (imports were added in NID-C.5):

  ```python
      hub_suggestions: list[str] = []
      hub_stage_events = []
      hub_checks = []
      hub_paths = []
      for topic, safe_topic in zip(topics, safe_topics, strict=True):
          hub_rel = f"hubs/{_topic_slug(topic)}.md"
          hub_inputs = [
              {"id": digest_rel, "sha256": digest_check["output_sha256"]},
              {"id": source_ref, "sha256": _source_input_sha(vault, source_ref, source_fm)},
          ]
          if (vault / hub_rel).exists():
              entry = candidate_entry(
                  digest_rel, "suggested hub update from this digest", context.run_id
              )
              hub_stage_events.append(
                  write_hub_candidates(
                      vault,
                      hub_rel,
                      [entry],
                      context=context,
                      checks=promotion_checks,
                      inputs=hub_inputs,
                  )
              )
              hub_suggestions.append(hub_rel)
              continue
          hub_frontmatter = {
              "type": "hub",
              "title": safe_topic,
              "description": f"Machine suggestion from {safe_source_title}.",
              "tag": _topic_slug(topic),
              "tags": ["suggestion"],
              "links": {},
          }
          stage = stage_concept(
              vault,
              hub_rel,
              concept_text(
                  hub_frontmatter,
                  safe_topic,
                  f"Suggested update from `{digest_rel}`. Curated hubs are not overwritten.\n",
              ),
              context=context,
              inputs=hub_inputs,
          )
          hub_stage_events.append(stage)
          hub_checks.append(promote_checked(vault, hub_rel, checks=promotion_checks, context=context))
          hub_paths.append(hub_rel)
  ```

  And extend the commit call (`operations.py:631-633`) to include the
  block-written hubs:

  ```python
      commit = commit_writer_changes(
          vault,
          f"compile digest {work_id}",
          [digest_rel, *hub_paths, *hub_suggestions],
          context=context,
      )
  ```

  (The `run/done` journal event at `operations.py:620-630` keeps
  `"outputs": [digest_rel, *hub_paths]` and
  `"suggestions": hub_suggestions` — only the values change.)

- [x] Run test to verify it passes:
  `python -m pytest tests/test_operations.py -v`

- [ ] Update the operation doc. In
  `src/memoria_vault/product/capabilities/operations/compile-source-digest.md`,
  replace the description (lines 4-5) with:
  ```yaml
  description: Compile a checked Work into a machine-owned digest, new hubs, and
    machine Candidates blocks on existing hubs.
  ```
  and replace the Pattern body's last sentence
  ("The digest and new hubs are machine-owned; curated hub changes stay as
  suggestions.") with:
  "The digest and new hubs are machine-owned; an existing hub receives only
  the terminal machine Candidates block — the curated body above it is never
  touched."
  In `docs/reference/commands-and-transports/system-actions-operations.md:105`,
  change the row's final clause "and stages hub suggestions." to
  "and writes the machine Candidates block on existing hubs (wholesale
  replace; the curated body above the block is never touched)."

- [ ] Regenerate the one drifted golden and verify the sweep is otherwise
  stable:
  `MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest "tests/test_floor_sweep_operations.py::test_operation[regenerate-capability-index]" -v`
  then `python -m pytest tests/test_floor_sweep_operations.py -q` —
  `git diff tests/fixtures/floor/goldens/` shows only the capability-index
  hash line changing (`compile-source-digest.json` must be untouched: the
  sweep's five topic hubs never pre-exist in the seed).

- [x] Verify the other compile consumers still pass:
  `python -m pytest tests/test_content_security.py tests/test_integrity_cascade_rollback.py tests/test_worker_knowledge_cycle.py tests/test_runtime_gate_replay.py tests/test_cli_work_project.py -q`
  then the full gate: `python scripts/verify`.

- [ ] Commit:
  ```
  git add src/memoria_vault/runtime/operations.py tests/test_operations.py src/memoria_vault/product/capabilities/operations/compile-source-digest.md docs/reference/commands-and-transports/system-actions-operations.md tests/fixtures/floor/goldens/regenerate-capability-index.json
  git commit -m "feat: route compile-source-digest hub suggestions through the Candidates block writer (NODES §5)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```
# Section ERP-A — `edges.py` owner module, roster convergence, v17 activation migration

Implements EDGES spec §1 (one edge module, two rosters, one parser family) and
the roster parts of §4 (Toulmin activation: `warrant`/`qualifier`/`rebuttal`
enter both rosters; `backing` stays out; `tension` stays frontmatter-illegal),
plus slice 4's activation migration and the §4 plan-amendment notes.

**Cross-plan coordination (binding for this section):**

- Executes AFTER Plan 22's G1 + G2S1.1–.3 are merged. Plan 22 G2S1.1 Produces
  `schema.normalize_link_target(target: str) -> str` and
  `schema.parse_links(links: object) -> list[tuple[str, str]]` in
  `src/memoria_vault/runtime/subsystems/lib/schema.py`. **Chosen path: MOVE.**
  ERP-A.1 moves both functions (and `LINK_RELATIONS`) to the new
  `lib/edges.py` and leaves `schema.py` re-exporting all three names for one
  release (EDGES §1: "schema.py's constant survives one release as a
  re-export, then is removed by the sweep discipline"). Every G2S1.1 consumer
  (`indexing.py`, `_check_links`) keeps working through the re-export; ERP-A.3
  repoints `indexing.py` at `edges` directly. The alternative (consume-in-place
  from schema.py) was rejected: it leaves the roster owner split across two
  modules, failing §10's one-roster acceptance criterion.
- Version chain (binding): Plan 22 owns v13/v14/v15; this plan's NID-B owns
  v16 (identity re-key); **ERP-A owns v17** (relation-roster CHECK extension).
  ERP-A.2 therefore depends on NID-B being merged (`SCHEMA_VERSION == 16` when
  ERP-A.2 starts) and registers `MIGRATIONS[16] = (17, [...])` in G1's shape
  (`state.MIGRATIONS: dict[int, tuple[int, list[str | Callable]]]`, key =
  from-version, steps applied in `_init` before `executescript(_schema_sql())`,
  which stamps the final `user_version`).
- **Public activation is ERP-A.1–.5, in one PR.** A.1 widens frontmatter
  validation to six relations (via the `schema.py` re-export feeding
  `_check_links`) while the DB CHECK still rejects the three new values; A.2
  closes that first window, A.3 converges readers, A.4 makes the PI write
  paths accept the same verbs, and A.5 updates U3's served-roster tests and
  manual acceptance. The commits may be developed in that order and stay
  green individually, but none may reach `main` until the whole group is
  ready. This is the EDGES §4 same-release guard against a dead served verb.
- Line refs verified at `main @ 9c77ba61` (pre-Plan-22). Where Plan 22 or
  NID-B will have shifted a line, the step says so and gives the content
  anchor to re-locate by.
- Constraint on NID-B (other section must honor): ERP-A.2's table rebuild
  copies exactly the post-v13 `concept_edges` column list (`edge_id,
  source_concept_id, relation_type, target_concept_id, attributes_json,
  check_status, source_path, updated_at`). If NID-B's v16 adds, renames, or
  drops a `concept_edges` column, the v17 CREATE + INSERT…SELECT column lists
  in ERP-A.2 must be extended to match v16's landed shape (mechanical edit;
  the CHECK roster is the contract).
- No task here touches journal events or workspace seeds — no floor-golden
  regeneration.

**SPEC GAP:** EDGES §1 kills the `structural_impact_graph.py:14` two-value
roster but does not say whether structural-impact traversal widens in slice 1
or waits for §8's substrate rewire; ERP-A.3 widens it to `LINK_RELATIONS` now,
per §10's one-roster acceptance and §4's "the argument graph and propagation
read all activated types" (§8's rewire replaces this parser entirely later).

**Verified-reality note on the amendment targets:** the spec (§4) says "the
surfaces plan's U3-PLUG.5/.8 acceptance lines ('exactly the three server
verbs') are updated"; grep over
`docs/superpowers/plans/2026-07-15-surfaces-bootstrap-and-plugins.md` finds
exactly ONE literal "exactly the three" occurrence (line 9580, the U3-PLUG.11
manual click-through). The other roster pins are the two single-source pointer
lines naming `schema.py:39` (lines 21 and 7411). ERP-A.5 edits all three.

---

### Task ERP-A.1: `edges.py` owner module — two rosters + one parser family

> **Execution amendment (2026-08-01, as landed):** the module was written from
> the code as landed, not from the pre-G2S1.1 sketch in the snippet below.
>
> 1. **The private target normalizer moved with the public pair.** Landed
>    `normalize_link_target` is a two-line wrapper over
>    `_normalized_link_target(target) -> (target, reason)` (plus
>    `_LINK_TARGET_URI_RE`), and `_check_links` calls that private helper
>    directly for its `traversal` / `empty` / `invalid` reason codes. The
>    snippet's inline three-line body would have dropped URI, traversal,
>    `.md`-suffix, and unbalanced-brace rejection. Both private names therefore
>    moved to `edges.py` verbatim, and `schema.py` imports
>    `_normalized_link_target` back beside the three re-exports. Leaving the
>    normalizer in `schema.py` was rejected: `edges.py` must stay stdlib-only
>    (`state.py`, `cli.py`, `structural_impact_graph.py` import it), while
>    `schema.py` imports `yaml` and `vaultio` — the dependency can only run
>    schema → edges.
> 2. **`parse_links` moved with its landed guards** (`isinstance(relation, str)`,
>    `isinstance(targets, list)`, per-target `isinstance(target, str)`) rather
>    than the shorter body below. Two of those are redundant with a second
>    guard and no fixture can distinguish them: a non-`str` relation key already
>    fails `relation not in LINK_RELATIONS`, and a non-`str` target already
>    returns `""` from `normalize_link_target`'s own `isinstance` check. They
>    are verbatim-moved dead defence, deliberately left as escapes rather than
>    covered by a test that would credit the wrong branch.
> 3. **Tests beyond the six listed:** multi-target/multi-relation `parse_links`
>    ordering, the per-target skip that keeps a relation's usable siblings, the
>    non-map `links:` value, a whitespace-only typed-wikilink target, and a
>    multi-link body — the listed cases are all N=1 on at least one axis.

**Files:**
- Create: `src/memoria_vault/runtime/subsystems/lib/edges.py`
- Create: `tests/test_edges.py`
- Modify: `tests/conftest.py` (TEST_LEVELS dict, alphabetical slot after
  `"test_e2e_smoke_helpers.py"` at line 40 — register `"test_edges.py":
  "unit"`, matching nearest lib sibling `test_loudness.py`/`lib/loudness.py`
  at line 76)
- Modify: `src/memoria_vault/runtime/subsystems/lib/schema.py:39`
  (`LINK_RELATIONS` definition → re-export) and the G2S1.1-added
  `normalize_link_target` + `parse_links` function bodies (placed directly
  above `_check_links`, currently line 135, by G2S1.1 — delete both, covered
  by the same re-export)
- Modify: `src/memoria_vault/runtime/trusted_writer.py:48-49`
  (`ARGUMENT_EDGE_TYPES`, `TYPED_WIKILINK_RE` — the regex moves to `edges.py`
  verbatim; the trusted_writer call-site edit is ERP-A.3's, this task only
  relocates the definition and leaves `trusted_writer.py` untouched until
  A.3 — so: no trusted_writer edit in this task; the regex is *copied* into
  `edges.py` and A.3 deletes the original)

**Interfaces:**
- Consumes: Plan 22 G2S1.1's landed `schema.normalize_link_target` /
  `schema.parse_links` bodies (moved verbatim); `schema.LINK_RELATIONS`
  consumers `_check_links` (schema.py:141-142) and
  `indexing.py`'s `from memoria_vault.runtime.subsystems.lib.schema import
  parse_links` (G2S1.1 — served by the re-export until A.3).
- Produces (all in `memoria_vault.runtime.subsystems.lib.edges`; pure module,
  stdlib-only imports, safe for `state.py`, `cli.py`, and
  `structural_impact_graph.py` to import):
  - `EDGE_RELATIONS: frozenset[str]` — the full seven: `supports`,
    `contradicts`, `extends`, `tension`, `warrant`, `qualifier`, `rebuttal`.
    Governs `concept_edges.relation_type` (parity test in ERP-A.2).
  - `LINK_RELATIONS: frozenset[str]` — the six frontmatter-legal values
    (`EDGE_RELATIONS - {"tension"}`).
  - `normalize_link_target(target: str) -> str` — moved from schema.py,
    behavior identical.
  - `parse_links(links: object) -> list[tuple[str, str]]` — moved from
    schema.py, behavior identical except the roster is now six.
  - `TYPED_WIKILINK_RE: re.Pattern[str]` — moved from trusted_writer.py:49,
    pattern identical.
  - `parse_typed_wikilinks(body: str) -> list[tuple[str, str]]` —
    `(relation, target)` pairs for explicit `[[relation::target]]` body
    links, filtered to `LINK_RELATIONS` and non-blank targets; propose-only
    input (callers mint candidate prompts, never edge rows — EDGES §1).
  - `schema.LINK_RELATIONS` / `schema.normalize_link_target` /
    `schema.parse_links` remain importable as re-exports for one release.

**Steps:**

- [x] Write the failing test file `tests/test_edges.py`:

  ```python
  """Single owner of the concept-relation rosters and links parsing (EDGES spec section 1)."""

  from __future__ import annotations

  from memoria_vault.runtime.subsystems.lib import edges, schema


  def test_edge_relations_is_the_full_seven() -> None:
      assert edges.EDGE_RELATIONS == frozenset(
          {"supports", "contradicts", "extends", "tension", "warrant", "qualifier", "rebuttal"}
      )


  def test_link_relations_is_everything_except_tension() -> None:
      assert edges.LINK_RELATIONS == edges.EDGE_RELATIONS - {"tension"}


  def test_schema_reexports_the_moved_names() -> None:
      assert schema.LINK_RELATIONS is edges.LINK_RELATIONS
      assert schema.parse_links is edges.parse_links
      assert schema.normalize_link_target is edges.normalize_link_target


  def test_normalize_link_target_strips_wikilink_alias_and_anchor() -> None:
      assert edges.normalize_link_target("[[notes/a|Alias]]") == "notes/a"
      assert edges.normalize_link_target("[[notes/a#section]]") == "notes/a"
      assert edges.normalize_link_target(" notes/a ") == "notes/a"
      assert edges.normalize_link_target("[[ ]]") == ""


  def test_parse_links_accepts_the_six_and_skips_tension_and_junk() -> None:
      pairs = edges.parse_links(
          {
              "supports": ["[[notes/a]]"],
              "warrant": ["notes/w.md"],
              "qualifier": ["[[notes/q|Q]]"],
              "rebuttal": ["[[notes/r]]"],
              "tension": ["notes/t.md"],
              "related": ["notes/x.md"],
              "extends": "not-a-list",
          }
      )
      assert ("supports", "notes/a") in pairs
      assert ("warrant", "notes/w.md") in pairs
      assert ("qualifier", "notes/q") in pairs
      assert ("rebuttal", "notes/r") in pairs
      assert not [pair for pair in pairs if pair[0] in {"tension", "related", "extends"}]


  def test_parse_typed_wikilinks_filters_to_frontmatter_legal_relations() -> None:
      body = (
          "Typed [[supports::notes/a.md]] then [[rebuttal::notes/r.md|R]] then "
          "[[tension::notes/t.md]] then [[frob::notes/x.md]] and bare [[notes/b.md]]."
      )
      assert edges.parse_typed_wikilinks(body) == [
          ("supports", "notes/a.md"),
          ("rebuttal", "notes/r.md"),
      ]
  ```

- [x] Register the file in `tests/conftest.py` TEST_LEVELS (insert
  alphabetically, after `"test_e2e_smoke_helpers.py": "package",` at line 40):

  ```python
      "test_edges.py": "unit",
  ```

- [x] Run test to verify it fails:
  `python -m pytest tests/test_edges.py -v`
  Expected failure: `ImportError: cannot import name 'edges' from
  'memoria_vault.runtime.subsystems.lib'`.
- [x] Write `src/memoria_vault/runtime/subsystems/lib/edges.py` (the two
  function bodies are G2S1.1's, moved verbatim except `parse_links`' roster
  comment; the regex is trusted_writer.py:49's, moved verbatim):

  ```python
  #!/usr/bin/env python3
  """Single owner of the concept-relation rosters and links parsing.

  EDGE_RELATIONS governs concept_edges.relation_type: the DB CHECK mirrors it
  and tests/test_query_substrate.py holds the parity test. LINK_RELATIONS is
  the frontmatter-legal subset — everything except 'tension', which is
  machine-surfaced and PI-confirmed, never authored in links: frontmatter
  (docs/superpowers/specs/2026-07-15-graph-edges-roles-propagation-design.md,
  sections 1, 3, 4). Every roster and links-parser in the repo imports from
  here; a relation change is a one-file edit, never a hunt across hardcoded
  sets.
  """

  from __future__ import annotations

  import re

  EDGE_RELATIONS = frozenset(
      {"supports", "contradicts", "extends", "tension", "warrant", "qualifier", "rebuttal"}
  )
  LINK_RELATIONS = frozenset(EDGE_RELATIONS - {"tension"})

  TYPED_WIKILINK_RE = re.compile(r"\[\[([a-z][a-z0-9-]*)::([^\]\|]+)(?:\|[^\]]*)?\]\]")


  def normalize_link_target(target: str) -> str:
      """Strip wikilink braces, alias, and anchor from one links: target."""
      raw = str(target).strip()
      if raw.startswith("[[") and raw.endswith("]]"):
          raw = raw[2:-2].split("|", 1)[0].split("#", 1)[0].strip()
      return raw


  def parse_links(links: object) -> list[tuple[str, str]]:
      """(relation, normalized target) pairs from a links: frontmatter map.

      Single owner of links parsing: validation and edge derivation share the
      same six-relation roster and normalization.
      """
      pairs: list[tuple[str, str]] = []
      if not isinstance(links, dict):
          return pairs
      for relation, targets in links.items():
          if relation not in LINK_RELATIONS or not isinstance(targets, list):
              continue
          for target in targets:
              raw = normalize_link_target(target) if isinstance(target, str) else ""
              if raw:
                  pairs.append((str(relation), raw))
      return pairs


  def parse_typed_wikilinks(body: str) -> list[tuple[str, str]]:
      """(relation, target) pairs from explicit [[relation::target]] body links.

      Propose-only input: callers mint edge-candidate prompts, never edge rows.
      Non-roster relations and blank targets are skipped.
      """
      pairs: list[tuple[str, str]] = []
      for match in TYPED_WIKILINK_RE.finditer(body):
          relation = match.group(1).strip().lower()
          target = match.group(2).strip()
          if relation in LINK_RELATIONS and target:
              pairs.append((relation, target))
      return pairs
  ```

- [x] In `src/memoria_vault/runtime/subsystems/lib/schema.py`: delete the
  `LINK_RELATIONS = frozenset({"supports", "contradicts", "extends"})` line
  (line 39 at 9c77ba61) and the `normalize_link_target` + `parse_links`
  function definitions G2S1.1 placed directly above `_check_links` (re-locate
  by the def names); add to the import block (after the
  `from memoria_vault.runtime.vaultio import ...` import at line 24):

  ```python
  # Re-exports live one release for external importers, then die by the sweep
  # discipline (EDGES design, section 1). New code imports lib.edges directly.
  from memoria_vault.runtime.subsystems.lib.edges import (  # noqa: F401
      LINK_RELATIONS,
      normalize_link_target,
      parse_links,
  )
  ```

  `_check_links` (lines 141-142) and its error message (`sorted(LINK_RELATIONS)`)
  pick up the six-value roster with no further edit.
- [x] Run test to verify it passes:
  `python -m pytest tests/test_edges.py -v` — expect PASS (7 tests).
- [x] Run the schema-validation neighbors to prove the move changed nothing
  but the roster width:
  `python -m pytest tests/test_schemas.py tests/test_frontmatter_contract.py tests/test_query_substrate.py -v`
  — expect PASS (`links.related: unknown relation` still fires; `related` is
  in no roster).
- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/subsystems/lib/edges.py src/memoria_vault/runtime/subsystems/lib/schema.py tests/test_edges.py tests/conftest.py
  git commit -m "feat(graph): edges.py owns the relation rosters and links parsers

  EDGE_RELATIONS (7) + LINK_RELATIONS (6, no tension) + the parser family
  move to one module; schema.py re-exports for one release.

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task ERP-A.2: v17 direct DDL — `concept_edges.relation_type` CHECK extends to `EDGE_RELATIONS`

Must merge in the same PR as ERP-A.1 (see section preamble). It consumes the
current direct v16 schema from NID-B and emits the current v17 DDL. It must not
register or test a v16→v17 migration.

**Files:**
- Modify: `src/memoria_vault/runtime/schema.sql:240-250` at 9c77ba61 — the
  `concept_edges` CREATE block; post-G2S1.2 it also carries `edge_id`,
  `attributes_json`, and the `idx_concept_edges_edge_id` index — re-locate by
  `relation_type IN ('supports', 'contradicts', 'extends', 'tension')` and
  edit only that roster; trailing `PRAGMA user_version` (line 378 at
  9c77ba61, reading `= 16` after NID-B) → `= 17`
- Modify: `src/memoria_vault/runtime/state.py:53` (`SCHEMA_VERSION = 16` →
  `17`); `_concept_edge_relation`
  (lines 3420-3424 at 9c77ba61 — re-locate by def name); import block
  (after `from memoria_vault.runtime.policy.paths import normalize_path`,
  line 34)
- Modify: `tests/test_schema_version.py:14-17` at 9c77ba61 — the
  `user_version` pin test (named `test_schema_lands_at_user_version_16` after
  NID-B; re-locate by `PRAGMA user_version`), 16 → 17;
  `tests/test_query_substrate.py:31` at 9c77ba61 — the
  `state.SCHEMA_VERSION ==` pin, 16 → 17. (`tests/test_schema_v10.py:41` was
  rewritten to `== state.SCHEMA_VERSION` by G2S1.2 — verify, no edit.)
- Test: `tests/test_query_substrate.py` (registered `contract` — no conftest
  change)

**Interfaces:**
- Consumes: the Plan-22 fresh-schema gate; post-v13 `concept_edges` shape with `edge_id` +
  `attributes_json` (Plan 22 G2S1.2) and `idx_concept_edges_edge_id` /
  `idx_concept_edges_target` indexes (G2S1.2/.3); `edges.EDGE_RELATIONS` (ERP-A.1);
  `state.replace_concept_edges` upsert-and-prune sparing tension rows
  (Plan 22 G2S1.1).
- Produces:
  - Current v17 schema DDL whose `relation_type` CHECK admits the seven
    `EDGE_RELATIONS`; no old table is copied or upgraded.
  - `state._concept_edge_relation` accepts exactly `edges.EDGE_RELATIONS`
    (ERP-B's `insert_concept_edge` and ERP-C's consequence writers rely on
    this gate).
  - Parity guarantee: the live DB's `relation_type` CHECK roster ==
    `edges.EDGE_RELATIONS`, enforced by
    `test_concept_edges_relation_check_matches_edge_relations` on both the
    fresh schema.

> **Execution replacement:** assert the roster against a fresh v17 schema. All
> following v16 fixture, table-copy, and migration-entry instructions are historical
> only and must not be executed.

> **Execution amendment (2026-08-01, as landed):**
>
> 1. **The `legacy` arm of the parity test is one of the retired instructions.**
>    It hand-builds a v16-shaped `concept_edges`, stamps
>    `PRAGMA user_version = 16`, and then expects `state.connect` to return an
>    upgraded, row-preserving table — a migration assertion in test clothing.
>    `state._init` rejects any nonzero version other than `SCHEMA_VERSION`
>    before touching the file, so with v17 landed that arm asserts an upgrade
>    the product refuses to perform. Only the fresh-schema arm was written.
> 2. **`test_replace_concept_edges_accepts_activated_relations` asserts
>    `set(edges.LINK_RELATIONS)`, not `EDGE_RELATIONS`.** `replace_concept_edges`
>    skips `tension` rows by design (Plan 22 G2S1.1's tension sparing, pinned by
>    `test_replace_concept_edges_preserves_direct_tension_and_ignores_tension_mirror_rows`),
>    so feeding all seven lands exactly the six link relations; the snippet
>    below would fail against landed behaviour. A `pytest.raises` arm keeps the
>    gate's rejection of a non-roster relation pinned.
> 3. **No `MIGRATIONS` entry** — sub-step 3 of the `state.py` checkbox is
>    retired by the Execution replacement above, and
>    `tests/test_schema_version.py::test_state_has_no_schema_migration_ladder`
>    fails if one is added.
> 4. **A third version pin existed.** NID-B's `tests/test_schema_v16_identity.py`
>    carried its own literal `16`; it now compares the applied pragma to
>    `state.SCHEMA_VERSION` (its subject is the identity *shape*), leaving the
>    literal pin in `tests/test_schema_version.py` alone, at 17.
> 5. **Two consumer-behaviour tests were added for the widening**, because a
>    roster-equality assertion does not produce the state that changed:
>    `tests/test_schemas.py::test_note_links_accept_every_frontmatter_legal_relation_and_still_refuse_tension`
>    (`_check_links` now validates six relations and still refuses `tension`)
>    and
>    `tests/test_query_substrate.py::test_reindex_mirrors_the_activated_link_relations_from_frontmatter`
>    (`indexing._concept_edges` now mirrors authored `warrant` / `qualifier` /
>    `rebuttal` links into real edge rows).
> 6. **Docs still describe the three-relation roster**
>    (`docs/reference/data-model/frontmatter.md:40,149`;
>    `docs/reference/data-model/wikilink-and-link-conventions.md:24-46,76`).
>    A.1/.2 deliberately left them: the six-verb prose belongs with A.3–A.5,
>    which make the write paths and the served roster agree, and contract 11
>    forbids merging A.1/.2 without them.

**Steps:**

- [x] Write the failing tests at the end of `tests/test_query_substrate.py`
  (add `import re` to the file's stdlib imports and
  `from memoria_vault.runtime.subsystems.lib import edges` to its package
  imports):

  ```python
  def _relation_check_roster(conn: sqlite3.Connection) -> set[str]:
      sql = conn.execute(
          "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'concept_edges'"
      ).fetchone()[0]
      match = re.search(r"relation_type IN \(([^)]*)\)", sql)
      assert match is not None, sql
      return {part.strip().strip("'") for part in match.group(1).split(",")}


  def test_concept_edges_relation_check_matches_edge_relations(tmp_path: Path) -> None:
      with state.connect(tmp_path) as conn:
          assert _relation_check_roster(conn) == set(edges.EDGE_RELATIONS)

      legacy = tmp_path / "legacy"
      db = legacy / state.DB_REL
      db.parent.mkdir(parents=True)
      with sqlite3.connect(db) as conn:
          conn.execute(
              "CREATE TABLE concept_edges ("
              " edge_id TEXT NOT NULL DEFAULT '',"
              " source_concept_id TEXT NOT NULL,"
              " relation_type TEXT NOT NULL CHECK ("
              "  relation_type IN ('supports', 'contradicts', 'extends', 'tension')"
              " ),"
              " target_concept_id TEXT NOT NULL,"
              " attributes_json TEXT NOT NULL DEFAULT '{}',"
              " check_status TEXT NOT NULL,"
              " source_path TEXT NOT NULL DEFAULT '',"
              " updated_at TEXT NOT NULL,"
              " PRIMARY KEY (source_concept_id, relation_type, target_concept_id))"
          )
          conn.execute(
              "INSERT INTO concept_edges("
              " edge_id, source_concept_id, relation_type, target_concept_id,"
              " attributes_json, check_status, source_path, updated_at)"
              " VALUES ('', 'notes/a.md', 'supports', 'notes/b.md',"
              " '{}', 'checked', 'notes/a.md', '2026-07-15T00:00:00Z')"
          )
          conn.execute("PRAGMA user_version = 16")

      with state.connect(legacy) as conn:
          assert conn.execute("PRAGMA user_version").fetchone()[0] == state.SCHEMA_VERSION
          assert _relation_check_roster(conn) == set(edges.EDGE_RELATIONS)
          survivors = conn.execute(
              "SELECT source_concept_id, relation_type, target_concept_id FROM concept_edges"
          ).fetchall()
          assert [tuple(row) for row in survivors] == [("notes/a.md", "supports", "notes/b.md")]
          index_names = {
              row["name"]
              for row in conn.execute(
                  "SELECT name FROM sqlite_master WHERE type = 'index'"
              ).fetchall()
          }
          assert {"idx_concept_edges_edge_id", "idx_concept_edges_target"} <= index_names


  def test_replace_concept_edges_accepts_activated_relations(tmp_path: Path) -> None:
      state.replace_concept_edges(
          tmp_path,
          [
              {
                  "source_concept_id": "notes/a.md",
                  "relation_type": relation,
                  "target_concept_id": f"notes/{relation}.md",
                  "check_status": "checked",
                  "source_path": "notes/a.md",
              }
              for relation in sorted(edges.EDGE_RELATIONS)
          ],
      )
      rows = state.concept_edges(tmp_path, checked_only=True)
      assert {row["relation_type"] for row in rows} == set(edges.EDGE_RELATIONS)
  ```

  (NID-B shape caveat from the preamble: if v16 changed `concept_edges`
  columns, mirror v16's landed column list in the legacy CREATE + INSERT
  here and in the migration below.)
- [x] Run test to verify it fails:
  `python -m pytest "tests/test_query_substrate.py::test_concept_edges_relation_check_matches_edge_relations" "tests/test_query_substrate.py::test_replace_concept_edges_accepts_activated_relations" -v`
  Expected failures: the first asserts
  `{'supports', 'contradicts', 'extends', 'tension'} == {...seven...}`; the
  second raises `ValueError: unknown concept edge relation: qualifier` from
  `_concept_edge_relation`.
- [x] In `src/memoria_vault/runtime/schema.sql`, extend the roster inside the
  `concept_edges` CREATE (re-locate by content):

  ```sql
      relation_type TEXT NOT NULL CHECK (
          relation_type IN (
              'supports', 'contradicts', 'extends', 'tension',
              'warrant', 'qualifier', 'rebuttal'
          )
      ),
  ```

  and bump the trailing pragma to `PRAGMA user_version = 17;`.
- [x] In `src/memoria_vault/runtime/state.py`:
  1. Add to the import block:

     ```python
     from memoria_vault.runtime.subsystems.lib.edges import EDGE_RELATIONS
     ```

  2. Set `SCHEMA_VERSION = 17`.
  3. Add the migration entry to G1's `MIGRATIONS` dict (SQLite cannot ALTER a
     CHECK; rebuild-and-rename, per-statement steps in G1's shape):

     ```python
         16: (
             17,
             [
                 """
                 CREATE TABLE concept_edges_v17 (
                     edge_id TEXT NOT NULL DEFAULT '',
                     source_concept_id TEXT NOT NULL,
                     relation_type TEXT NOT NULL CHECK (
                         relation_type IN (
                             'supports', 'contradicts', 'extends', 'tension',
                             'warrant', 'qualifier', 'rebuttal'
                         )
                     ),
                     target_concept_id TEXT NOT NULL,
                     attributes_json TEXT NOT NULL DEFAULT '{}',
                     check_status TEXT NOT NULL CHECK (
                         check_status IN ('unchecked', 'checked', 'quarantined')
                     ),
                     source_path TEXT NOT NULL DEFAULT '',
                     updated_at TEXT NOT NULL,
                     PRIMARY KEY (source_concept_id, relation_type, target_concept_id)
                 )
                 """,
                 """
                 INSERT INTO concept_edges_v17(
                     edge_id, source_concept_id, relation_type, target_concept_id,
                     attributes_json, check_status, source_path, updated_at)
                 SELECT edge_id, source_concept_id, relation_type, target_concept_id,
                     attributes_json, check_status, source_path, updated_at
                 FROM concept_edges
                 """,
                 "DROP TABLE concept_edges",
                 "ALTER TABLE concept_edges_v17 RENAME TO concept_edges",
                 "CREATE UNIQUE INDEX IF NOT EXISTS idx_concept_edges_edge_id"
                 " ON concept_edges(edge_id) WHERE edge_id != ''",
                 "CREATE INDEX IF NOT EXISTS idx_concept_edges_target"
                 " ON concept_edges(target_concept_id)",
             ],
         ),
     ```

  4. Converge `_concept_edge_relation` onto the owner roster — replace its
     hardcoded set:

     ```python
     def _concept_edge_relation(value: str) -> str:
         relation = value.strip().lower().replace("_", "-")
         if relation not in EDGE_RELATIONS:
             raise ValueError(f"unknown concept edge relation: {value}")
         return relation
     ```

- [x] Bump the two version pins: in `tests/test_schema_version.py` rename the
  pin test to `test_schema_lands_at_user_version_17` and change both `16`s to
  `17`; in `tests/test_query_substrate.py` change the
  `state.SCHEMA_VERSION == 16` pin to `== 17`. Verify
  `tests/test_schema_v10.py` already compares against
  `state.SCHEMA_VERSION` (G2S1.2) — no edit.
- [x] Run test to verify it passes:
  `python -m pytest tests/test_query_substrate.py tests/test_schema_version.py tests/test_schema_v10.py tests/test_edges.py -v`
  — expect PASS.
- [x] Run `python scripts/verify` — expect PASS.
- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/schema.sql src/memoria_vault/runtime/state.py tests/test_query_substrate.py tests/test_schema_version.py
  git commit -m "feat(graph): activate warrant/qualifier/rebuttal in concept_edges (migration 17)

  relation_type CHECK now derives from edges.EDGE_RELATIONS with a parity
  test; table rebuild preserves rows, PK, and both indexes.

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task ERP-A.3: parser + roster convergence — the remaining hardcoded sites become imports

> **Execution amendment (2026-08-01, as landed):** the convergence itself landed
> exactly as the table below specifies. It also settled the dead-defence audit
> A.1 deferred and four review minors, because A.3 rewrites every one of those
> call sites and has no verbatim-move constraint to protect.
>
> 1. **The seven surviving defences, settled — deleted or pinned, no third
>    category.** *Deleted*, naming the producer state that cannot exist:
>    `parse_links`' `isinstance(relation, str)` (a non-`str` YAML mapping key
>    already fails `relation not in LINK_RELATIONS` and takes the same skip —
>    this answers A.1's deferred question: `parse_links` needs no tolerance of
>    its own); `parse_links`' per-target `isinstance(target, str)`
>    (`normalize_link_target` is already total over non-strings);
>    `parse_typed_wikilinks`' `.strip().lower()` on the relation capture (the
>    group is `([a-z][a-z0-9-]*)` — it can emit neither whitespace nor
>    uppercase); `state._concept_edge_relation`'s `.replace("_", "-")` (no
>    `EDGE_RELATIONS` value contains `-` or `_`, so it can flip no accept/reject
>    decision and alter no accepted value); and the redundant outer
>    `frozenset()` around `EDGE_RELATIONS - {"tension"}`. *Pinned*, naming the
>    producer state now created: `_normalized_link_target`'s two
>    bracket-rejection arms and its `empty` sentinel, all three through
>    `test_link_parser_and_validation_reject_invalid_local_targets`
>    (`[[notes/a[b]]`, `notes/a[1]`, `[[ ]]`) — that test asserts the *validator
>    message*, so it observes the reason code the public wrapper projects away,
>    and the `empty` arm is therefore pinned from `schema.py`'s side, the only
>    side that reads it; `normalize_link_target`'s `isinstance` guard, now the
>    family's only one (`test_normalize_link_target_is_total_over_non_strings`);
>    and `_concept_edge_relation`'s surviving `.strip().lower()`, through a
>    `" Supports "` row in `test_replace_concept_edges_accepts_activated_relations`.
> 2. **Review minors closed.** `tests/test_query_substrate.py`'s
>    `_relation_check_roster` — a fourth copy of the roster-reading regex — is
>    deleted in favour of `graph_sql.concept_edge_relations`, so the parity test
>    doubles as that reader's pin. `tests/test_schemas.py`'s six-relation fixture
>    no longer derives itself from `sorted(edges.LINK_RELATIONS)`: it names the
>    six verbs and the expected message list, so dropping one from the roster now
>    fails it. `tests/test_schema_v16_identity.py`'s
>    `user_version == SCHEMA_VERSION` assertion is deleted as a tautology of
>    `state._init`'s own raise.
> 3. **`parse_typed_wikilinks` gains its first production caller**
>    (`trusted_writer._write_edge_candidate_prompts`), which is what retires
>    `ARGUMENT_EDGE_TYPES` and `TYPED_WIKILINK_RE`.
> 4. **`knowledge._link_target` widens what it rejects.** Delegating to
>    `normalize_link_target` sends URI, traversal, non-`.md`-suffix, and
>    bracketed values to `""`, which reaches `_concept_rel("")` — that returns
>    the phantom `notes/.md` rather than raising. **Corrected 2026-08-01 (review
>    T2): that phantom is observable and the first draft of this item was wrong.**
>    `iter_markdown` yields a file named `.md` (`".md".endswith(".md")`), so
>    `notes/.md` is a legal key in the notes map, and the convergence had made the
>    phantom an *absorbing* state — every rejected target now collapses onto one
>    sink instead of a distinct unreachable one. `_link_target` therefore returns
>    `""` before `_concept_rel`, pinned by
>    `test_analyze_project_argument_never_synthesizes_an_edge_into_the_dot_md_note`.
>    The same guard lands in `graph_sql._link_target`, which has the same renderer.
> 5. **Correction to A.1's amendment, item 1.** Its counterfactual is loud, not
>    silent. Replacing the landed normalizer with the plan snippet's inline
>    three-line body fails existing tests immediately — 9 at A.1's tree (six of
>    them from the pre-existing parametrized
>    `test_link_parser_and_validation_reject_invalid_local_targets`), and 12 at
>    this one, nine of them from that same parametrized test. The deviation was
>    still necessary, but it was never an undetectable escape and the amendment
>    should not read as though it were.
> 6. **One accepted mutation survivor.** Pointing `indexing.py` back at
>    `lib.schema`'s `parse_links` re-export passes the whole suite, and must:
>    `test_schema_reexports_the_moved_names` asserts the re-export *is* the same
>    object, so no behavior can distinguish the two imports. The enforcement is
>    the sweep discipline that deletes the re-export next release — that deletion
>    turns a stale import into an `ImportError`, which is louder than any guard
>    test, so none was added. (A.1's item 2 is superseded by item 1 above: both
>    guards it left as declared escapes are now deleted.)
> 7. **Namespace split — the review's Critical, fixed 2026-08-01.** The table
>    below says the structural-impact stripper delegates to
>    `normalize_link_target`. It must not: `build_resolver` keys on **title, slug,
>    and stem** as well as path, so this reader's alphabet includes
>    `Toulmin: the warrant` (rejected as a URI scheme) and `Study 1.2` (rejected
>    as a foreign suffix). Delegating silently emptied them — a PI whose thesis
>    note carries a colon got `active_thesis: ''` and a `cold-start` gate index
>    with no error. `edges.py` now owns both operations with the domains named:
>    `strip_wikilink` (syntax only, namespace-free) for alias space, which
>    structural impact calls, and `normalize_link_target` (validating) for path
>    space. The unit pin asserts both sides — the stripper keeps a colon title,
>    the validator still rejects it — and the alias-side behavioural pins are
>    `test_build_edges_resolves_link_titles_that_are_not_path_shaped` and
>    `test_structural_impact_resolves_a_thesis_whose_title_carries_a_colon`.
>    **Detection rule, worth carrying into ERP-B/C/D:** when a refactor gives a
>    validator a second caller, enumerate the *second* caller's input alphabet.
>    Fixtures on both sides otherwise draw from the intersection (path-shaped
>    strings) and the helper looks total.
> 8. **Sibling readers (review T1), converged in part — ruling.**
>    `graph_sql._link_target` and `explore._link_target` were byte-identical
>    copies of the stripper this task deleted from `knowledge`, carrying the same
>    validator/reader disagreement (`notes/../thesis.md` resolved to a real note).
>    Both are path space, so both now call `normalize_link_target` — and
>    `explore`'s copy is deleted outright in favour of `graph_sql`'s, which it
>    already reaches into for `_active_project_slices`. Their `_link_targets`
>    keeps iterating the raw `links:` map with **no roster filter**, and the
>    reason is the retrieval contract, nothing else: `neighborhood` admits every
>    relation the live CHECK holds "so tensions remain first-class retrievable",
>    so filtering the fallback closure to `LINK_RELATIONS` would make it strictly
>    narrower than the substrate traversal it stands in for — a worse reader, not
>    a stricter one. The only defensible filter would be `EDGE_RELATIONS`, and
>    even that buys nothing a lenient reader needs. *Not* an argument for this,
>    though the mutation shows it: adding the filter breaks two `explore` tests
>    whose fixtures author `links: {related: […]}`, which `_check_links` rejects
>    outright — they pin behaviour over frontmatter no checked vault can hold, and
>    leaning on them would contradict this same task's "the reader and the
>    validator must agree" convergence. `edges.py`'s docstring is corrected to say
>    what is true: every *roster* imports from here, path-space normalization
>    comes from here, and retrieval closures walk the raw map by design.
> 9. **The counts roster is deleted, not narrowed (review T4).**
>    `analyze_project_argument`'s per-relation tally read only
>    `supports`/`contradicts`/`extends`, so iterating `sorted(LINK_RELATIONS)`
>    manufactured three zeros nothing read — a no-op convergence that survived
>    mutation. It is now `Counter(edge["type"] …)`: no roster at that site at all,
>    and no roster literal to guard. The payload keys stay the three this plan's
>    Produces list fixes; widening the per-verb breakdown belongs to whoever
>    widens `worker.py`'s mirror of them.
> 10. **Disclosure — the readiness state machine is now wrong for the three new
>    verbs (issue #1624; ERP-C/ERP-D own the fix, not this task).** A.3 widened
>    `_note_edges` to six relations, which widened `relation_count`, which drives
>    `_argument_stage` / `_argument_saturation_conditions` / `_argument_findings`
>    — branches that read **only** `counts["supports"]` and
>    `counts["contradicts"]`. Measured here, three checked notes each holding one
>    relation to the thesis:
>
>    | edges | `relation_count` | `argument_stage` | `mature_graph` | gap findings |
>    | --- | --- | --- | --- | --- |
>    | 3× `warrant`, pre-A.3 | 0 | `cold-start` | `False` | `structural`, `unstated-warrant` |
>    | 3× `warrant`, now | 3 | `supported` | `True` | `unstated-warrant` |
>    | 3× `rebuttal`, now | 3 | `supported` | `True` | `unstated-warrant` |
>    | 3× `qualifier`, now | 3 | `supported` | `True` | `unstated-warrant` |
>    | 3× `extends`, now and pre-A.3 | 3 | `supported` | `True` | `unstated-warrant` |
>
>    So a rebuttal-only project — every edge naming a condition under which the
>    thesis fails — reports `argument_stage: "supported"` and `mature_graph:
>    True`, and a warrant-only project still emits `unstated-warrant`.
>    `displayed_confidence` stays `below-threshold` in all three, so the
>    confidence number is not implicated. The hole is pre-existing (`extends`
>    already had it, last row) but A.3 tripled its blast radius and pulled in the
>    one relation whose answer is backwards. Recalibrating the machine is a
>    semantic decision about what each Toulmin role means for maturity — ERP-C's
>    consequence typing and ERP-D's finding hygiene own it. Nothing in the suite
>    asserts `argument_stage` for a single-relation project of any of the three;
>    that gap is deliberate here and belongs with the fix, so the tests encode one
>    definition of maturity rather than two.
> 11. **Disclosure — `thesis:` is read in two namespaces by three readers (issue
>    #1623).** `structural_impact_graph` resolves it through the alias table
>    (a title works), while `graph_sql._link_target`, `explore` (same object), and
>    `search_index._project_link` resolve it as a path (a title yields nothing).
>    The last of those is a third inline stripper this task did not converge; the
>    earlier sweep in this amendment classified `search_index` as display-only,
>    which is true of its contradiction items and false of `_project_link`. The
>    field's contract is not ERP-A's to set.

Mechanical convergence of the audit's parsers/rosters onto `edges.py`
(EDGES §1). Sites and exact refs (verified at 9c77ba61; `schema.py:39` died
in A.1, `state.py:3422` in A.2):

| Site | Ref | Edit |
| --- | --- | --- |
| structural-impact roster | `structural_impact_graph.py:14` | `RELATIONS = tuple(sorted(LINK_RELATIONS))` |
| structural-impact wikilink strip | `structural_impact_graph.py:57` (`_WIKI`), `:79-84` | delegate to `normalize_link_target` |
| argument-assembly roster (counts) | `knowledge.py:1698` | iterate `sorted(LINK_RELATIONS)` |
| argument-assembly roster (edges) | `knowledge.py:3004` | iterate `sorted(LINK_RELATIONS)` |
| argument-assembly wikilink strip | `knowledge.py:3041-3043` | delegate to `normalize_link_target` |
| typed body-wikilinks + edge-candidate prompts | `trusted_writer.py:48-49`, `:336-340` | delete both constants; use `parse_typed_wikilinks` |
| links mirror import | `indexing.py` (G2S1.1's `from ...lib.schema import parse_links`) | import from `...lib.edges` |

**Files:**
- Modify: `src/memoria_vault/runtime/subsystems/processing/project/structural_impact_graph.py:5,14,57,79-84`
- Modify: `src/memoria_vault/runtime/knowledge.py:34` (import block), `:1698`, `:3004`, `:3041-3043`
- Modify: `src/memoria_vault/runtime/trusted_writer.py:48-49`, `:336-340`
- Modify: `src/memoria_vault/runtime/indexing.py` (the G2S1.1 import line — re-locate by `import parse_links`)
- Test: `tests/test_project_structural_impact.py` (contract),
  `tests/test_trusted_writer.py` (runtime),
  `tests/test_project_knowledge.py` (runtime) — all registered, no conftest
  change

**Interfaces:**
- Consumes: `edges.LINK_RELATIONS`, `edges.normalize_link_target`,
  `edges.parse_typed_wikilinks`, `edges.parse_links` (ERP-A.1).
- Produces:
  - `structural_impact_graph.RELATIONS == tuple(sorted(edges.LINK_RELATIONS))`
    — `build_edges` now traverses all six frontmatter relations (SPEC GAP
    resolution in the preamble; ERP-C's consequence closure and §8's rewire
    build on this).
  - `knowledge._note_edges` emits edges for all six relations; the
    `analyze_project_argument` payload keys `supports_count` /
    `contradicts_count` / `extends_count` are unchanged, `relation_count`
    now counts all six (consumed by ERP-C's finding retargets).
  - Typed body-wikilinks in all six relations mint edge-candidate prompts
    (still propose-only, never rows).

**Steps:**

- [x] Write the failing tests. At the end of
  `tests/test_project_structural_impact.py`:

  ```python
  def test_build_edges_includes_activated_relations(tmp_path):
      write(
          tmp_path / "notes/a.md",
          "---\ntype: note\ntitle: A\nlinks:\n  rebuttal:\n    - notes/b\n---\nBody.\n",
      )
      write(tmp_path / "notes/b.md", "---\ntype: note\ntitle: B\n---\nBody.\n")

      notes = impact_graph.read_notes(tmp_path)
      resolver = impact_graph.build_resolver(notes)
      built = impact_graph.build_edges(notes, resolver)

      assert [(edge.source, edge.relation, edge.target) for edge in built] == [
          ("notes/a", "rebuttal", "notes/b")
      ]
  ```

  At the end of the edge-candidate block in `tests/test_trusted_writer.py`
  (after `test_commit_writer_extracts_typed_edge_candidates_without_mutating_links`,
  line 289):

  ```python
  def test_commit_writer_extracts_rebuttal_candidate_and_skips_tension(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      init_git(vault, "writer@example.invalid", "Trusted Writer")
      content = note_text().replace(
          "Alpha body.",
          "Typed [[rebuttal::notes/beta.md]] and [[tension::notes/gamma.md]].",
      )

      stage_concept(vault, "notes/alpha.md", content, machine="test-machine")
      promote_checked(vault, "notes/alpha.md", machine="test-machine")
      commit_writer_changes(vault, "trusted write alpha", ["notes/alpha.md"], machine="test-machine")

      prompts = sorted((vault / "inbox").glob("work-prompt-edge-candidate-*.md"))
      assert len(prompts) == 1
      prompt_text = prompts[0].read_text(encoding="utf-8")
      assert "rebuttal" in prompt_text
      assert "notes/beta.md" in prompt_text
      assert "notes/gamma.md" not in prompt_text
  ```

  At the end of `tests/test_project_knowledge.py`:

  ```python
  def test_analyze_project_argument_reads_activated_relation_links(tmp_path: Path) -> None:
      _md(
          tmp_path / "projects/project-alpha/project.md",
          "type: project\ncheck_status: checked\ntitle: Alpha project\n"
          "description: Project\nthesis: notes/thesis.md\n",
      )
      _md(
          tmp_path / "notes/thesis.md",
          "type: note\ncheck_status: checked\ntitle: Thesis\n",
      )
      _md(
          tmp_path / "notes/license.md",
          "type: note\ncheck_status: checked\ntitle: License\n"
          "links:\n  warrant:\n    - notes/thesis.md\n",
      )

      result = analyze_project_argument(tmp_path, "project-alpha")

      assert result["relation_count"] == 1
      assert result["supports_count"] == 0
      assert {node["path"] for node in result["nodes"]} == {
          "notes/thesis.md",
          "notes/license.md",
      }
  ```

- [x] Run tests to verify they fail:
  `python -m pytest "tests/test_project_structural_impact.py::test_build_edges_includes_activated_relations" "tests/test_trusted_writer.py::test_commit_writer_extracts_rebuttal_candidate_and_skips_tension" "tests/test_project_knowledge.py::test_analyze_project_argument_reads_activated_relation_links" -v`
  Expected failures: structural-impact assertion sees `[]` (rebuttal filtered
  out by the two-value `RELATIONS`); trusted-writer sees `len(prompts) == 0`
  (rebuttal not in `ARGUMENT_EDGE_TYPES`); knowledge sees
  `relation_count == 0` (warrant not in the hardcoded triple).
- [x] Edit `structural_impact_graph.py`:
  1. Add after the existing `from memoria_vault.runtime.vaultio import ...`
     imports (lines 11-12):

     ```python
     from memoria_vault.runtime.subsystems.lib.edges import LINK_RELATIONS, normalize_link_target
     ```

  2. Line 14: `RELATIONS = ("supports", "contradicts")` →

     ```python
     RELATIONS = tuple(sorted(LINK_RELATIONS))
     ```

  3. Delete the `_WIKI` regex (line 57) and replace `normalize_target`'s
     strip tail (lines 79-84):

     ```python
         match = _WIKI.match(value)
         if match:
             value = match.group("target")
         value = value.split("|", 1)[0].split("#", 1)[0].strip()
         if value.endswith(".md"):
             value = value[:-3]
     ```

     with

     ```python
         value = normalize_link_target(value).split("|", 1)[0].split("#", 1)[0].strip()
         if value.endswith(".md"):
             value = value[:-3]
     ```

     (Bare-string `|`/`#` splitting is preserved; for wikilinks the extra
     splits are no-ops after `normalize_link_target`.)
- [x] Edit `knowledge.py`:
  1. Add next to the `schema_lib` import (line 34):

     ```python
     from memoria_vault.runtime.subsystems.lib.edges import LINK_RELATIONS, normalize_link_target
     ```

  2. Line 1698: `for relation in ("supports", "contradicts", "extends")` →
     `for relation in sorted(LINK_RELATIONS)`.
  3. Line 3004: `for link_type in ("supports", "contradicts", "extends"):` →
     `for link_type in sorted(LINK_RELATIONS):`.
  4. Lines 3041-3043 in `_link_target`:

     ```python
         raw = value.strip()
         if raw.startswith("[[") and raw.endswith("]]"):
             raw = raw[2:-2].split("|", 1)[0].split("#", 1)[0].strip()
     ```

     → `raw = normalize_link_target(value)`.
- [x] Edit `trusted_writer.py`:
  1. Delete lines 48-49 (`ARGUMENT_EDGE_TYPES`, `TYPED_WIKILINK_RE`) and add
     to the import block (near the `lib import schema as schema_lib` import,
     line 27):

     ```python
     from memoria_vault.runtime.subsystems.lib.edges import parse_typed_wikilinks
     ```

  2. In `_write_edge_candidate_prompts`, replace lines 336-340:

     ```python
             for match in TYPED_WIKILINK_RE.finditer(body):
                 edge_type = match.group(1).strip().lower()
                 target = match.group(2).strip()
                 if edge_type not in ARGUMENT_EDGE_TYPES or not target:
                     continue
     ```

     with

     ```python
             for edge_type, target in parse_typed_wikilinks(body):
     ```

     (the loop body below, lines 341-364, is unchanged).
- [x] Edit `indexing.py`: change the G2S1.1 import line

  ```python
  from memoria_vault.runtime.subsystems.lib.schema import parse_links
  ```

  to

  ```python
  from memoria_vault.runtime.subsystems.lib.edges import parse_links
  ```

- [x] Run tests to verify they pass, plus the touched suites:
  `python -m pytest tests/test_project_structural_impact.py tests/test_trusted_writer.py tests/test_project_knowledge.py tests/test_query_substrate.py -v`
  — expect PASS.
- [x] Run `python scripts/verify` — expect PASS.
- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/subsystems/processing/project/structural_impact_graph.py src/memoria_vault/runtime/knowledge.py src/memoria_vault/runtime/trusted_writer.py src/memoria_vault/runtime/indexing.py tests/test_project_structural_impact.py tests/test_trusted_writer.py tests/test_project_knowledge.py
  git commit -m "refactor(graph): converge parsers and rosters onto lib/edges

  structural impact, argument assembly, typed body-wikilinks, and the links
  mirror all import the one roster; three hardcoded rosters die.

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task ERP-A.4: six-verb acceptance — validator, curate-note-link, CLI + vim round-trip

> **Execution amendment (2026-08-01, as landed):** the two production edits are
> the plan's (`curate_note_link`'s roster gate, `cli.py`'s `--rel` choices, both
> reading `edges.LINK_RELATIONS`). The test slice deviates in three places.
>
> 1. **No new `tests/test_schemas.py` case.** A.1 already landed the equivalent
>    (`test_note_links_accept_every_frontmatter_legal_relation_and_still_refuse_tension`),
>    and A.3 de-derived its fixture so it is a real roster pin. A second copy
>    would have pinned nothing further.
> 2. **The vim round-trip folded into A.2's landed mirror test** instead of
>    becoming a third fixture over the same three verbs:
>    `test_activated_links_round_trip_from_frontmatter_to_edge_rows` now reads
>    the authored frontmatter *back off disk* — the same bytes the mirror reads —
>    validates it, and then asserts the rows. That is a stronger round-trip than
>    the plan's hand-built frontmatter dict, in one fixture rather than two.
> 3. **The CLI gained a behavioural pin the plan's step list lacked**
>    (`test_cli_link_offers_every_served_relation_and_refuses_tension`, in
>    `tests/test_cli_work_project.py` beside the existing `link` coverage).
>    Without it the only proof of `choices` was the roster-literal guard, which a
>    widening to `tuple(sorted(EDGE_RELATIONS))` — serving `tension` from the
>    CLI — passes untouched.
>
> **Reader updates — deferred in the first draft on a false premise, landed
> 2026-08-01 (review T3/T6).** The deferral claimed that editing
> `src/memoria_vault/product/capabilities/operations/curate-note-link.md` forces a
> floor-golden regeneration because its body is hashed into
> `capability-index.json`. The hash is there, but `tests/floor_lib.py` redacts
> `\b[0-9a-f]{32,64}\b` to `<HASH>` before digesting, so a body edit changes
> nothing the golden records — measured, not assumed: the full gate is green with
> the manifest widened. Five readers now name the six verbs:
> `docs/how-to-guides/knowledge/link-checked-notes.md` (step 2 and the Verify
> list), `docs/reference/data-model/frontmatter.md` (the `links` kind row and the
> `links` section), the capability manifest, and — a fourth reader the first pass
> missed, and the only one that was *wrong* rather than understating —
> `docs/reference/control-and-policy/project-structural-impact.md`, which said the
> operation follows `links.supports` and `links.contradicts` after ERP-A.3 widened
> that traversal to all six. `docs/explanation/knowledge/note-body-structure.md`
> drops its roster-shaped list instead of extending it. No floor golden moved.

The EDGES §10 acceptance slice: writing a `rebuttal` (or `warrant`,
`qualifier`) link in vim round-trips — validator accepts, edge row appears at
reindex — and `curate-note-link`/`memoria link` accept the six and reject
`tension` (which stays machine-surfaced, §3). Finishes with the repo-wide
single-roster guard (§10: "grepping the repo finds exactly one
relation-roster definition").

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py:360-362` (`curate_note_link`
  roster gate)
- Modify: `src/memoria_vault/cli.py:263` (`--rel` choices) and the import
  block (after `from memoria_vault.runtime.paths import safe_filename`,
  line 27)
- Test: `tests/test_schemas.py` (contract), `tests/test_knowledge.py`
  (direct runtime), `tests/test_worker_product_jobs.py` (worker runtime),
  `tests/test_query_substrate.py` (contract), `tests/test_edges.py` (unit) —
  all registered, no conftest change

**Interfaces:**
- Consumes: `edges.LINK_RELATIONS` (already imported into `knowledge.py` by
  ERP-A.3); `schema.validate_frontmatter` / `schema.load_types`;
  `state.concept_edges`; `tests.helpers.ROOT`, `write_checked_concept`,
  `copy_memoria_dirs`; `enqueue_operation` / `run_next_job` and `write_note`
  in `tests/test_worker_product_jobs.py`; the `rebuild_passage_index` wrapper
  at `tests/test_query_substrate.py:18-19`.
- Produces:
  - `curate_note_link` accepts exactly `edges.LINK_RELATIONS`; error message
    `f"note link_type must be one of {', '.join(sorted(LINK_RELATIONS))}"`
    (ERP-B's `confirm-tension` outcome relies on `tension` staying rejected
    here; the relate control's served roster — `summary.link_relations` in
    the surfaces plan — serves these same six via `LINK_RELATIONS`).
  - `memoria link --rel` choices == `tuple(sorted(edges.LINK_RELATIONS))`.
  - Direct and worker acceptance both parameterize over
    `sorted(edges.LINK_RELATIONS)`, assert each matching `links.<relation>`
    write, and separately reject `tension`. This is the executable half of
    the public-roster activation guard: a reader may not advertise a verb
    unless both the direct PI path and queued worker path complete it.
  - Repo guard test: no `.py` file under `src/memoria_vault` except
    `lib/edges.py` contains a quoted `"supports", "contradicts"` roster
    literal.

**Steps:**

- [x] Write the failing tests. At the end of `tests/test_schemas.py` (mirrors
  `test_note_links_are_typed_maps`, line 174):

  ```python
  def test_note_links_accept_activated_toulmin_relations():
      note = schema.load_types()["note"]
      good = {
          "id": "01KBN6V6KX0000000000000001",
          "type": "note",
          "title": "T",
          "tags": [],
          "links": {
              "warrant": ["notes/license.md"],
              "qualifier": ["[[notes/bounds]]"],
              "rebuttal": ["[[notes/exception|Exception]]"],
          },
      }
      assert schema.validate_frontmatter(good, note) == []
      assert any(
          "links.tension: unknown relation" in e
          for e in schema.validate_frontmatter(
              dict(good, links={"tension": ["notes/other.md"]}), note
          )
      )
  ```

  At the end of `tests/test_knowledge.py` (mirrors
  `test_curate_note_link_records_typed_link_on_checked_note`, line 395), add
  `from memoria_vault.runtime.subsystems.lib.edges import LINK_RELATIONS` to
  the imports. Keep that existing one-case event/commit regression, then add
  this all-served direct-path proof plus the separate negative case:

  ```python
  @pytest.mark.parametrize("relation", sorted(LINK_RELATIONS))
  def test_curate_note_link_accepts_each_served_relation(
      tmp_path: Path, relation: str
  ) -> None:
      vault = workspace(tmp_path)
      _md(
          vault / "notes/source.md",
          "type: note\ncheck_status: checked\ntitle: Source\nstatus: accepted\n",
      )
      _md(
          vault / "notes/target.md",
          "type: note\ncheck_status: checked\ntitle: Target\nstatus: accepted\n",
      )

      result = curate_note_link(
          vault, "source", relation, "target", actor="pi", machine="curator"
      )

      assert result["link_type"] == relation
      source_fm = read_frontmatter(vault / "notes/source.md")
      assert source_fm["links"] == {relation: ["notes/target.md"]}


  def test_curate_note_link_rejects_tension(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      _md(vault / "notes/source.md", "type: note\ncheck_status: checked\ntitle: Source\nstatus: accepted\n")
      _md(vault / "notes/target.md", "type: note\ncheck_status: checked\ntitle: Target\nstatus: accepted\n")
      with pytest.raises(ValueError, match="link_type must be"):
          curate_note_link(vault, "source", "tension", "target", actor="pi", machine="curator")
  ```

  At the end of `tests/test_worker_product_jobs.py`, import
  `LINK_RELATIONS` from `runtime.subsystems.lib.edges` and add the matching
  queued-worker proof. Keep a fresh disposable vault per parameter value so
  the expected frontmatter is one relation at a time:

  ```python
  @pytest.mark.parametrize("relation", sorted(LINK_RELATIONS))
  def test_worker_runs_each_served_curate_note_link(
      tmp_path: Path, relation: str
  ) -> None:
      vault = workspace(tmp_path)
      source = write_note(vault, "source", "checked", "Source body.")
      target = write_note(vault, "target", "checked", "Target body.")
      queued = enqueue_operation(
          vault,
          "curate-note-link",
          payload={
              "source_note_path": source.relative_to(vault).as_posix(),
              "link_type": relation,
              "target_path": target.relative_to(vault).as_posix(),
          },
          idempotency_key=f"served-link-{relation}",
          actor="pi",
      )
      done = run_next_job(vault, machine="test-machine")

      assert queued["kind"] == "operation"
      assert done is not None and done["status"] == "done"
      assert done["link_type"] == relation
      assert read_frontmatter(source)["links"] == {relation: ["notes/target.md"]}


  def test_worker_rejects_tension_curate_note_link(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      source = write_note(vault, "source", "checked", "Source body.")
      target = write_note(vault, "target", "checked", "Target body.")
      enqueue_operation(
          vault,
          "curate-note-link",
          payload={
              "source_note_path": source.relative_to(vault).as_posix(),
              "link_type": "tension",
              "target_path": target.relative_to(vault).as_posix(),
          },
          idempotency_key="served-link-tension",
          actor="pi",
      )
      failed = run_next_job(vault, machine="test-machine")

      assert failed is not None and failed["status"] == "failed"
      assert "link_type must be" in str(failed["error"])
  ```

  At the end of `tests/test_query_substrate.py` (the vim round-trip;
  `edges` was imported in ERP-A.2 — add
  `from memoria_vault.runtime.subsystems.lib import schema as schema_lib` to
  the imports):

  ```python
  @pytest.mark.parametrize("relation", ["warrant", "qualifier", "rebuttal"])
  def test_activated_link_round_trips_to_edge_row(tmp_path: Path, relation: str) -> None:
      vault = tmp_path
      copy_memoria_dirs(vault, "schemas")
      write_checked_concept(
          vault,
          "notes/alpha.md",
          "type: note\ntitle: Alpha\ntags: []\n"
          f'links:\n  {relation}: ["[[notes/beta]]"]\n',
      )
      write_checked_concept(
          vault, "notes/beta.md", "type: note\ntitle: Beta\ntags: []\nlinks: {}\n"
      )

      note_schema = schema_lib.load_types()["note"]
      frontmatter = {
          "type": "note",
          "title": "Alpha",
          "tags": [],
          "links": {relation: ["[[notes/beta]]"]},
      }
      link_errors = [
          error
          for error in schema_lib.validate_frontmatter(frontmatter, note_schema)
          if error.startswith("links")
      ]
      assert link_errors == []

      rebuild_passage_index(vault)
      triples = {
          (edge["source_concept_id"], edge["relation_type"], edge["target_concept_id"])
          for edge in state.concept_edges(vault, checked_only=True)
      }
      assert ("notes/alpha.md", relation, "notes/beta.md") in triples
  ```

  At the end of `tests/test_edges.py` (the §10 one-roster guard; add
  `import re` and `from tests.helpers import ROOT` to its imports):

  ```python
  def test_single_roster_definition_repo_wide() -> None:
      roster_literal = re.compile(r"['\"]supports['\"]\s*,\s*['\"]contradicts['\"]")
      offenders = [
          path.relative_to(ROOT).as_posix()
          for path in (ROOT / "src/memoria_vault").rglob("*.py")
          if path.name != "edges.py" and roster_literal.search(path.read_text(encoding="utf-8"))
      ]
      assert offenders == []
  ```

- [x] Run tests to verify they fail:
  `python -m pytest tests/test_schemas.py::test_note_links_accept_activated_toulmin_relations tests/test_knowledge.py::test_curate_note_link_accepts_each_served_relation tests/test_knowledge.py::test_curate_note_link_rejects_tension tests/test_worker_product_jobs.py::test_worker_runs_each_served_curate_note_link tests/test_worker_product_jobs.py::test_worker_rejects_tension_curate_note_link tests/test_query_substrate.py::test_activated_link_round_trips_to_edge_row tests/test_edges.py::test_single_roster_definition_repo_wide -v`
  Expected: the schemas test PASSES already (the roster widened in A.1 —
  it pins the behavior); the direct and worker parameterized groups pass for
  the old three verbs and fail for `warrant`, `qualifier`, and `rebuttal` with
  `ValueError: note link_type must be supports, contradicts, or extends`;
  their `tension` cases still reject;
  the round-trip PASSES already (A.1 + A.2 + G2S1.1 — it pins §10's
  acceptance); the guard test fails listing `src/memoria_vault/cli.py` and
  `src/memoria_vault/runtime/knowledge.py`.
- [x] Edit `knowledge.py` `curate_note_link` (lines 360-362):

  ```python
      link_type = link_type.strip().lower()
      if link_type not in LINK_RELATIONS:
          raise ValueError(f"note link_type must be one of {', '.join(sorted(LINK_RELATIONS))}")
  ```

- [x] Edit `cli.py`: add the import after line 27
  (`from memoria_vault.runtime.paths import safe_filename`):

  ```python
  from memoria_vault.runtime.subsystems.lib.edges import LINK_RELATIONS
  ```

  and change line 263 to:

  ```python
      link.add_argument("--rel", required=True, choices=tuple(sorted(LINK_RELATIONS)))
  ```

- [x] Run tests to verify they pass, plus the touched suites:
  `python -m pytest tests/test_edges.py tests/test_schemas.py tests/test_knowledge.py tests/test_worker_product_jobs.py tests/test_query_substrate.py tests/test_cli.py -v`
  — expect PASS.
- [x] Run `python scripts/verify` — expect PASS.
- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/knowledge.py src/memoria_vault/cli.py tests/test_schemas.py tests/test_knowledge.py tests/test_worker_product_jobs.py tests/test_query_substrate.py tests/test_edges.py
  git commit -m "feat(graph): validator, curate-note-link, and CLI accept the six link relations

  warrant/qualifier/rebuttal round-trip from vim to concept_edges rows;
  repo-wide guard pins the single-roster acceptance criterion.

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task ERP-A.5: plan amendments — served-verbs acceptance + `claims.base` glyph column

> **Execution amendment (2026-08-01, as landed):** the surfaces-plan line-21 and
> line-9580 edits and the alpha.23 `claims.base` glyph amendment had already
> landed before this task ran; only the U3-PLUG.5/.8 "Relation-roster decision"
> paragraph remained. Its appended amendment states the served roster in cross-
> section contract 11's own terms — after this PR it is exactly
> `edges.LINK_RELATIONS`, six verbs, still excluding `tension` — so no acceptance
> text anywhere in the surfaces plan reads as a counted three.

> **Execution override:** The 2026-07-29 cross-section contracts above now
> own the surfaces changes, including the direct `edges.LINK_RELATIONS` import,
> all-six acceptance, and the U3 warrant wire. This task makes that owner
> migration executable by requiring the atomic U3-ENG.1/.2/.3 slice to start
> only after ERP-A.1–.5 and to import `LINK_RELATIONS` from `lib.edges` on its
> first implementation. Do not reapply the stale line-specific surface
> instructions below. This task still carries the independent Alpha23
> `claims.base` glyph amendment, re-anchored by its quoted context.

The two recorded amendments EDGES §4 and §5 direct at the surfaces and
alpha.23 plans. Docs only; no code, no tests, no verify-gated behavior (the
docs task still runs the gate because `scripts/verify` includes the
doc-claims check).

**Files:**
- Modify: `docs/superpowers/plans/2026-07-15-surfaces-bootstrap-and-plugins.md:21`
  (summary-payload contract line), `:7411` (the "Relation-roster decision
  (Task U3-PLUG.5/.8)" paragraph), `:9580` (U3-PLUG.11 manual click-through —
  the sole "exactly the three" occurrence; see the section preamble's
  verified-reality note)
- Modify: `docs/superpowers/plans/2026-07-15-alpha23-usable-loop.md:116`
  (insert directly after the R1NG.1 line "Honesty notes in force: H1, H2, H3,
  H4, H5, H6, H10, H11.", before `**Steps:**` — re-locate by that content)

**Interfaces:**
- Consumes: `edges.LINK_RELATIONS` as the served roster's source of truth
  (ERP-A.1); EDGES §5's four consequence types and the `stale` /
  `consequence` frontmatter fields (substrate owned by ERP-C).
- Produces: amended plan text other executors read; no code interface.

**Steps:**

- [x] In the surfaces plan, line 21, change

  `` `link_relations` from `schema.LINK_RELATIONS` ``

  to

  `` `link_relations` from `edges.LINK_RELATIONS` (moved from `schema.LINK_RELATIONS` by the graph-edges plan ERP-A.1; the `schema` re-export stays valid for one release) ``

- [x] In the surfaces plan, line 7411, change

  `` `LINK_RELATIONS` is defined once at `src/memoria_vault/runtime/subsystems/lib/schema.py:39` ``

  to

  `` `LINK_RELATIONS` is defined once at `src/memoria_vault/runtime/subsystems/lib/edges.py` (formerly `schema.py:39`; moved by the graph-edges plan ERP-A.1) ``

  and append this sentence to the end of the same paragraph:

  `` **Recorded amendment (EDGES §4, graph-edges plan ERP-A.5):** once `warrant`/`qualifier`/`rebuttal` activate, the served roster is six verbs; every acceptance here reads "exactly the served verbs" — never a counted three — and the control renders as a segmented control or dropdown accordingly. ``

- [x] In the surfaces plan, line 9580, change

  `Relation shows exactly the three server verbs as a segmented control`

  to

  `Relation shows exactly the served verbs (summary.link_relations — six once the graph-edges plan's roster activation lands) as a segmented control or dropdown`

- [x] In the alpha.23 plan, insert after the R1NG.1 "Honesty notes in force"
  line (line 116) and its trailing blank line:

  ```markdown
  > **Recorded amendment (EDGES §5, graph-edges plan ERP-A.5):** `claims.base`
  > additionally carries a glyph formula column rendering the typed-consequence
  > mark — the two optional frontmatter fields `stale: bool` and `consequence:`
  > (enum: `grounds-lost`, `warrant-lost`, `qualifier-regression`,
  > `rebuttal-strengthened`) written by the consequence engine — so consequence
  > labels are visible in any editor Bases reaches. Formula, mirroring
  > `inbox.base`'s `loudness_glyph` style:
  > `consequence_glyph: 'if(stale, "⚠ " + consequence, "")'`, added to the
  > `formulas:` block and as `formula.consequence_glyph` in the "By maturity"
  > view's `order:` list. If R1NG.1 executes before the consequence fields
  > exist, seed the column anyway (it renders blank until the fields appear);
  > if R1NG.1 already executed, apply this as a follow-up edit to the seeded
  > `claims.base` and its `test_claims_base_matches_the_design` assertions.
  ```

- [x] Run `python scripts/verify` — expect PASS (doc-claims gate covers the
  edited plans).
- [x] Commit:

  ```
  git add docs/superpowers/plans/2026-07-15-surfaces-bootstrap-and-plugins.md docs/superpowers/plans/2026-07-15-alpha23-usable-loop.md
  git commit -m "docs(plans): record EDGES roster amendments — served verbs + claims.base glyph column

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task ERP-A.6: Public identity-safe concept-edge path projections

> **Inherited debt from NID-B.2's identity adoption (recorded 2026-07-31, review finding R1)
> — ERP-C/ERP-D own the fix; ERP-A.6 owns the record.** NID-B.2 added
> `_adopt_path_key_identity_conn`, which lets a provisionally path-keyed Concept take the
> ULID its file later authors. That adoption is a **narrow, deliberately partial re-key**:
> FKs carry `concept_verdicts`, `concept_flags` and `concept_edges` endpoints, but two
> references are left pointing at the retired path key, because neither carries a foreign key:
>
> | table | stale value after adoption | goes live at |
> | --- | --- | --- |
> | `derivations.input_id` | keeps `'notes/hand.md'`, naming no Concept (`schema.sql:407-412`) | ERP-C/ERP-D walk the derivation DAG |
> | `concept_edges.edge_id` | keeps the pre-adoption digest, so `edge_id != concept_edge_id(source, relation, target)` | ERP-B/ERP-C/ERP-D consume `edge_id` |
>
> **Both rows are now closed — NID-B.7 (2026-08-01). ERP-A.6/ERP-C/ERP-D inherit
> nothing from this table; do not re-add either row.** `_adopt_path_key_identity_conn`
> no longer hand-writes its own one-statement re-key: it calls
> `_rekey_path_keyed_concept_conn`, the identity-space enumeration B.6 made the single
> home, so adoption carries `derivations.input_id`/`output_id` and `passages.concept_id`
> exactly as a rename does. That helper also blanks `edge_id` on every edge touching the
> re-keyed identity and B.7's resolution pass in `replace_concept_edges` recomputes it
> over the live triple. The claim below that `edge_id` "is recomputed by the next full
> `replace_concept_edges`" was **false for a durable `tension` row**, which the mirror
> pass skips by design, and worse than false for the rest: a stale digest is a valid
> UNIQUE key, so the next file dropped at the vacated path recomputes it exactly and
> kills the whole rebuild on an IntegrityError.
>
> **`passages.concept_id` was the third row and is now closed — narrowed by NID-B.4
> (2026-07-31), measured, not assumed.** This note previously claimed it was "rewritten on
> refresh"; that was only half true, because the pre-B.4 `_passage_row` re-emitted the
> *path* as `concept_id` unconditionally, so a refresh rewrote the row to the same retired
> value. B.4's id-space rule emits the frontmatter ULID, and both convergence routes were
> measured end to end: a full `rebuild_passage_index` wipes and reinserts every row, and the
> incremental `refresh_stale_passages` rewrites the adopting file, which necessarily changed
> when it gained its `id`. Do not re-add this row.
>
> Both remaining references are inert today (`derivations` is write-only in `src/`; `edge_id`
> is recomputed by the next full `replace_concept_edges`). Do not read NID-B.2's "no
> derivation, passage or edge_id rewriting" as restraint — it is an **incomplete re-key whose
> residue is deferred here**, and it must be closed before anything walks the derivation DAG
> or trusts `edge_id` as a stable digest.
>
> **Residual, not a regression:** adoption can still move a verdict onto content that did
> not earn it via *path reuse* — mirror an id-less `notes/old.md` as `checked`, rename the
> file away, drop a brand-new ULID-carrying file at `notes/old.md`, then `workspace
> rebuild`: the new file adopts the old row and reads `checked`. This is inherent to
> provisional path keys (a path-keyed Concept *is* identified by its path, so path reuse is
> identity reuse) and behaves identically under NID-B.1. The normal observe path demotes via
> `record_observed_file_edit`; only `workspace rebuild` skips that. Recorded rather than
> fixed — more machinery in B.2 is not the answer.

**Preconditions:** NID-B v16 and the atomic ERP-A.1–.5 activation are merged.
This task is the graph producer required by R2 G and every path-facing
propagation/structural consumer; it is not optional prose in the A-section
amendment.

> **Owns a live regression (from NID-B.2, 2026-07-31).** `graph_sql.neighborhood`
> and `explore._edges_by_concept` join identity against path, so `memoria explore`
> and the `explore.read` surface serve no neighbours and no edges for ULID-keyed
> Concepts until this task lands. `graph_sql.filter_ids` has the same defect and no
> `src/` caller yet. See NID-B.2's review amendment for the full statement.
>
> **Shape note from NID-B.4 (2026-07-31) — this is what the rewrite must target.**
> `indexing._concept_edges` now emits `source_concept_id` in **identity** space (the
> frontmatter ULID) while `source_path` stays in **path** space. The two columns
> therefore diverge for every ULID-keyed Concept, and `graph_sql.py:79`'s
> `source_status.concept_id = edge.source_path` join is NULL for exactly those rows.
> Join `concepts.path` to `source_path`, or `concepts.concept_id` to
> `source_concept_id` — never one against the other. NID-B.4 did not touch this join.

> **Execution amendment (2026-08-01, as landed): the consumers land here too.**
> The Files list and the step checkboxes below name only the producer
> (`edges.py` + `tests/test_edges.py`), but the two blockquotes above say the
> `explore` regression persists "until this task lands", and the in-source
> comments at all four defective sites name ERP-A.6 as the owner of the fix. A
> producer nobody reads would have left every measured symptom in place, so this
> task also rewires the consumers and adds
> `src/memoria_vault/runtime/graph_sql.py`,
> `src/memoria_vault/runtime/explore.py`, `tests/test_graph_sql.py` and
> `tests/test_explore.py` to its Files. R2's amendment already assigns this
> wiring to G.1/E.1, but both shipped before ERP-A.6 existed; nothing else in
> either plan comes back for them.
>
> 1. **Measured before, measured after.** One vault built twice — once with
>    id-less files (path keys) and once with frontmatter ULIDs — through
>    `record_observed_file_edit`/`replace_concept_edges`, then read through
>    `explore.explore_topic`. Before: the path-keyed arm returned 5 ids, 8
>    displayed edge entries and 1 tension; the ULID arm returned 3 ids, **0**
>    edge entries and **0** tensions,
>    `neighborhood` emitted a raw ULID into its path-space `ids`,
>    `degree_centrality` read 1/1 instead of 3/2, and `filter_ids` kept nothing
>    (`after: 0` of 2). After: the two arms are byte-identical.
> 2. **`explore._edges_by_concept` and `_tension_pairs` consume
>    `concept_edge_path_pairs`**, and `degree_centrality` builds its adjacency
>    from it. `state.concept_edges` now has no `src/` consumer at all.
> 3. **`neighborhood` keeps its own SQL for eligibility only; the endpoint rule
>    is one function, not a replica.** It cannot consume the strict projection:
>    R2's "solely from `edges.concept_edge_path_pairs`" would silently delete the
>    revoked-source gate, which needs the edge's own `source_path` (blank =
>    PI-owned, no verdict gates it) and the source Concept's verdict — two columns
>    the three-field API withholds and which no consumer can re-derive from a
>    projected triple, since two edge rows can project to the same one. So the
>    first query selects eligible rows with their source/target renderings, and
>    everything after it is `edges.projected_edge_endpoints`, the same call the
>    producer makes on every row it returns: normalize both, drop the edge if
>    either renders blank. The recursive walk then runs over that adjacency.
> 4. **A sanctioned replica inherits the claim, never the test — which is why the
>    endpoint rule stopped being a replica.** This is the failure the reviews
>    named twice: a mutation killed in `edges.py` surviving verbatim in the SQL
>    copy, because the fixtures attached to the named producer only. Two escapes
>    came out of it, both the same shape — one Concept with two ids in a single
>    path-space answer. **Blank endpoint:** unguarded, `''` enters the undirected
>    walk as a hub joining every blank-target edge's source to every other,
>    inflating the `neighbors` denominator R2 §4 requires be built where the set
>    is built. **Unnormalized endpoint:** a stored `./notes/x.md` sat beside the
>    `notes/x.md` every consumer holds; the producer normalized and the copy did
>    not, and *neither side was tested* — removing either `normalize_path` passed
>    the full suite. It is reachable because a PI-owned `tension` row is written
>    outside the mirror pass by design, so `_concept_edge_target_path` never keys
>    it; contract 4 binds ERP-B.2's `insert_concept_edge` to that function and
>    **ERP-B.3's confirm-tension writer must be bound to it too**. Collapsing the
>    two copies into one call is the fix that cannot drift again; both sides are
>    pinned anyway, at the producer (`tests/test_edges.py`, an unnormalized
>    durable `target_path` and an unnormalized `concepts.path`) and at the walk
>    (`tests/test_graph_sql.py`, the same stored row returned as the normalized
>    id). The `neighborhood` fixture carries the producer's whole endpoint
>    alphabet: ULID source, resolved target, pending target, resolved-but-pathless
>    target, blank source, blank target, unnormalized target. The same rule found
>    one more, one layer out: the checked gate in `_tension_pairs` was pinned only
>    through its sibling `_edges_by_concept`, whose fixture edge is an `extends`
>    row that `_tension_pairs` discards before reaching that gate; it now has an
>    unchecked *tension* between two displayed Concepts. And ordering is now
>    pinned on three rows rather than two — with two rows the scan order is either
>    the answer or its exact reverse, so no two-row fixture can tell a sort from a
>    `reverse()`.
> 5. **`filter_ids` is not an edge reader.** Its defect is the same namespace
>    error one table over: path-space ids matched against
>    `concept_status.concept_id`. It now looks a Concept up by `path` and keys
>    the result back under `path or concept_id`, the convention
>    `state.concept_check_statuses` already uses. The `concept_id` arm is
>    retained so a caller holding a db-store Concept that renders nowhere keeps
>    working; it is not a licence to pass a ULID.
> 6. **Not done, deliberately.** No consumer outside these two modules was
>    touched. `structural_impact_graph` reads frontmatter, not `concept_edges`,
>    and its rewire onto `concept_edge_path_records` stays ERP-D.4's.
>    `_tension_pairs`'s safe-endpoint gate is left in place **and is dead, with
>    nothing behind it**: for any `left`/`right`, the crossing gate two lines
>    below admits only edges with one endpoint in each, which implies membership
>    in `left ∪ right`, so no edge can reach one gate and fail the other — and
>    deleting it outright passes the full suite, `titles` lookups included.
>    Deleting it is the repo's stated preference; it is left only because it is
>    pre-existing code outside this task's defect, and it belongs to whoever
>    reworks the tension surface in ERP-B.3.

**Files:**

- Modify: `src/memoria_vault/runtime/subsystems/lib/edges.py`
- Modify: `tests/test_edges.py`
- Modify (2026-08-01 amendment): `src/memoria_vault/runtime/graph_sql.py`,
  `src/memoria_vault/runtime/explore.py`, `tests/test_graph_sql.py`,
  `tests/test_explore.py`

**Interfaces:**

- Consumes: v16 `concept_edges` (`source_concept_id` identity FK,
  nullable `target_concept_id`, durable `target_path`, checked status), and
  `concepts.path` from the identity mirror.
- Produces:

  ```python
  def concept_edge_path_pairs(
      vault: Path, *, checked_only: bool = True
  ) -> list[dict[str, str]]:
      """Deterministic graph edges projected to source/target paths."""


  def concept_edge_path_records(
      vault: Path, *, checked_only: bool = True
  ) -> list[dict[str, Any]]:
      """Deterministic projected paths plus parsed safe edge attributes."""
  ```

  `concept_edge_path_pairs` is the strict public endpoint API: every row has
  exactly `source_path`, `target_path`, and `relation_type`.
  `concept_edge_path_records` is its metadata-safe sibling for graph-internal
  consumers: every row has those path fields plus parsed `attributes`.
  Source comes from the source mirror's current `concepts.path`; target is the
  target mirror path when resolved, otherwise the durable pending
  `concept_edges.target_path`.  A malformed or non-object `attributes_json`
  yields `{}`.  `checked_only=True` filters on the edge row; `False`
  deliberately includes unchecked/pending topology.  Neither API exposes a
  concept ID or `edge_id`.

**Steps:**

- [x] Write failing tests in `tests/test_edges.py` (extend the existing module;
  no `TEST_LEVELS` change).  Seed the v16 mirror with a source whose
  `concept_id` is a ULID and whose `path` is `notes/source.md`, a resolved
  target at `notes/resolved.md`, and a checked pending target path
  `notes/pending.md`.  Insert the edge rows through the NID-B trusted state
  seam.  Assert the public result is deterministic and exactly:

  ```python
  [
      {
          "source_path": "notes/source.md",
          "target_path": "notes/pending.md",
          "relation_type": "extends",
      },
      {
          "source_path": "notes/source.md",
          "target_path": "notes/resolved.md",
          "relation_type": "supports",
      },
  ]
  ```

  Give the resolved row `{"warrant": "licensed"}` and the pending row
  `{"addressed": false}` attributes.  Assert neither serialized pair contains
  the source ULID, then assert the record API returns the same path/relation
  ordering with exactly those parsed attribute dictionaries and no identity
  keys.  Add an unchecked edge and prove it is absent by default and present
  only with `checked_only=False` in both projections.
- [x] Run the focused test red:

  ```bash
  python -m pytest tests/test_edges.py -q
  ```

  Expected: import/attribute failure for both path-projection functions.
- [x] Implement in `edges.py`.  Keep the `state` import inside the function so
  ERP-A.2's module-level `state → edges` roster import cannot cycle.  Implement
  `concept_edge_path_records` as the shared query: join the edge table to
  `concepts AS source` and left-join `concepts AS target`; select source
  `path`, `COALESCE(NULLIF(target.path, ''), edge.target_path)` as target path,
  relation type, and `attributes_json`.  Apply the checked predicate
  parametrically, normalize only the selected paths, parse a JSON object to
  `attributes` (otherwise `{}`), skip a corrupt blank endpoint, sort by source
  path, relation type, target path, and return plain dicts.  Implement
  `concept_edge_path_pairs` by mapping each record to a newly built dict with
  exactly its three public fields.  Do not select into, return, or normalize
  raw identity columns or `edge_id`.
- [x] Run the focused and dependent graph tests:

  ```bash
  python -m pytest tests/test_edges.py tests/test_query_substrate.py -q
  ```

- [x] Run `python scripts/verify` — expect PASS.
- [ ] Commit:

  ```bash
  git add src/memoria_vault/runtime/subsystems/lib/edges.py tests/test_edges.py \
    src/memoria_vault/runtime/graph_sql.py src/memoria_vault/runtime/explore.py \
    tests/test_graph_sql.py tests/test_explore.py \
    docs/superpowers/plans/2026-07-15-graph-substrate.md
  git commit -m "feat(graph): project identity-keyed edges to durable paths (ERP-A.6)"
  ```
# Section ERP-B — Catalog bridge fix + tension confirmation surface

Implements EDGES spec §2 (catalog-sources bridge: pointer-only, resolution
fixed) and §3 (tension confirmation surface), plus the retraction path the
spec rules ("existence = confirmation; no status column; retraction = row
delete"). Repo: `/home/eranr/memoria-vault`, main @ `9c77ba61`.

**SPEC GAP:** EDGES §3 says confirm-tension mints "from the prompt's
source/target payload", but at HEAD no per-candidate tension prompt exists —
`surface_tensions` writes only one aggregate degraded-mode card
(`integrity.py:837-850`) with no pair payload. ERP-B.3 adds the minimal
enabling surface (one `work-prompt` card per candidate, deduped by pair
digest, carrying a `payload: {source, target}` frontmatter map) because the
spec's flow is unimplementable without it. No other invention.

**Recorded decisions (spec-silent details, smallest honest reading):**

- Minted tension rows get `check_status='checked'` — the PI's confirmation IS
  the check; the row exists only because a human accepted it.
- Tension pair endpoints are stored lexicographically sorted
  (`sorted((left, right))`), so one unordered pair ⇒ exactly one row and one
  deterministic `edge_id` ("mints exactly one row", EDGES §10).
- Retraction verb (ERP-B.4): `state.delete_concept_edge` — a state-layer
  delete, symmetric with `insert_concept_edge`. Justification: the spec rules
  out tombstones/status columns, so row deletion is the *entire* retraction;
  the far more destructive `state.replace_concept_edges` already takes no
  context, so requiring an envelope only here would be ceremony; a
  documented-manual-sqlite path would bypass even the API seam and invite
  schema drift. Authority gating stays at operation seams (a future CLI/inbox
  unconfirm verb wraps this API in its own envelope — out of scope until a
  surface demands it).

**Cross-plan consumes (this plan executes AFTER Plan 22 G1 + G2S1.1–.3):**

- `state.replace_concept_edges` upsert-and-prune **sparing tension rows**
  (G2S1.1) — the reindex-survival tests in ERP-B.3/.4 depend on it; at
  `9c77ba61` the function still does `DELETE FROM concept_edges`
  (`state.py:2029`) and those tests would fail.
- `state.concept_edge_id(source: str, relation: str, target: str) -> str` —
  sha256 over the triple, `[:24]` (G2S1.2).
- `concept_edges` rows carrying `edge_id TEXT` + `attributes_json TEXT`
  (schema v13, G2S1.2); PK stays the
  `(source_concept_id, relation_type, target_concept_id)` triple.
- `state.MIGRATIONS` mechanism (G1) — **ERP-B allocates no schema version**:
  the v12 baseline CHECK already admits `tension` (`schema.sql:242-244`) and
  v13 supplies `edge_id`/`attributes_json`. v16/v17/v18 belong to
  NID-B/ERP-A/ERP-C per the binding allocation.

**Intra-plan consumes:** ERP-B.2 imports `EDGE_RELATIONS` from ERP-A's
`src/memoria_vault/runtime/subsystems/lib/edges.py` (roster owner module,
EDGES §1). **Ordering: ERP-A's roster task must land before ERP-B.2.**

**Scope boundary:** the `structural_impact` substrate rewire (EDGES §8,
slice 8) belongs to ERP-C. ERP-B.1 delivers the bridge fix plus the
argument-graph traversal proof that a work's retraction blast radius reaches
its dependent claims; ERP-C's rewired `structural_impact` inherits the same
bridge.

**Test registration:** every test lands in an already-registered file
(`tests/conftest.py` `TEST_LEVELS`: `test_knowledge.py`,
`test_project_knowledge.py`, `test_runtime_state.py`,
`test_integrity_surface_tensions.py` — all `runtime`). No conftest change.

**Floor goldens:** no seed files change; the new `confirm-tension` outcome
rides the existing `resolved` journal event and `disposition.v1` schema
shapes. Expected: no floor-golden regeneration. If `python scripts/verify`
floor sweeps disagree after ERP-B.3, regenerate per `tests/floor_lib.py`
procedure and include the regenerated goldens in that task's commit.

---

### Task ERP-B.1: Virtual catalog targets in `_checked_concept` + claim→work edges in `_note_edges`

> **Execution amendment (2026-08-01) — what ERP-B.1 landed.** Four deviations from
> the step text below, none of them contract changes.
> **(1) The drafted fixtures cannot run.** Every drafted note is written with
> `_md(..., "type: note\ncheck_status: checked\n…")`, but `check_status` is a
> **retired** frontmatter field (`vaultio.retired_frontmatter_field_errors`) and
> `curate_note_link`'s own write path refuses it — pinned by
> `test_curate_note_link_rejects_invalid_source_without_mutation`. The claim note is
> staged with this file's `checked_note(vault, name, title, <ULID>)` helper instead.
> The `tests/test_project_knowledge.py` fixtures are unaffected: nothing there passes
> a note through a writer seam.
> **(2) `_note_edges` iterates the roster, not three literals.** ERP-A's convergence
> already replaced the drafted `("supports", "contradicts", "extends")` tuple with
> `sorted(LINK_RELATIONS)`; only the target filter changes here. Likewise the
> drafted `thesis_rel` local is `thesis_path` at HEAD — `thesis_rel` is now the
> imported `edges.thesis_rel` function (issue #1623).
> **(3) A second, unchecked work.** The drafted bridge test has one work, which
> cannot tell the `works` filter from no filter at all, nor `catalog_sources`'
> default `checked_only=True` from `False`. The fixture carries an unchecked
> `source-beta` the support note also links, asserted absent from both `edges` and
> `nodes`, and asserts whole node records rather than the drafted `role` projection.
> **(4) No fourth pin on the check→write ordering.** `curate_note_link` validates the
> target through the one `_checked_concept` call for both branches, and ERP-D.5's
> `test_curate_note_link_refuses_an_unchecked_target_before_writing_the_edge`
> already pins that the warrant upsert sits behind it. The catalog branch reuses
> that call site, so a second ordering test would be a replica.

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py`
  (`_checked_concept` :3406-3415, `_note_edges` :3001-3009,
  `analyze_project_argument` :1672-1729 — edges call :1691, nodes render
  :1718-1725; caller `curate_note_link` :370 is exercised, not edited)
- Modify: `tests/test_knowledge.py` (append after
  `test_curate_note_link_records_typed_link_on_checked_note`, :395-428)
- Modify: `tests/test_project_knowledge.py` (append after
  `test_analyze_project_argument_reads_checked_note_links`, :60)

**Interfaces:**
- Consumes: `state.catalog_source(vault: Path, source_ref: str) -> dict[str, Any] | None`
  (`state.py:1603`), `state.catalog_sources(vault: Path, *, checked_only: bool = True) -> list[dict[str, Any]]`
  (`state.py:1615`), `capture.py:134`'s virtual
  `concept_path = f"catalog/sources/{work_id}"` convention.
- Produces:
  - `_checked_concept(vault: Path, relpath: str) -> dict[str, Any]` — now
    resolves `catalog/sources/*` via the DB row (no `is_file()` gate);
    returns `{"type": "work", "title": str, "work_id": str}` for works.
  - `_checked_catalog_source(vault: Path, relpath: str) -> dict[str, Any]` (private helper).
  - `_note_edges(notes: dict[str, dict[str, Any]], *, works: set[str] | frozenset[str] = frozenset()) -> list[dict[str, str]]`
    — keeps edges whose target is a checked catalog work rel.
  - `analyze_project_argument` result: `edges` may include
    `catalog/sources/<work_id>` targets; `nodes` entries for works carry
    `role: "work"` and `title = <work_id>`.

**Steps — cycle 1 (bridge resolution):**

- [x] Write the failing tests (append to `tests/test_knowledge.py`; `pytest`,
  `state`, `_md`, `read_frontmatter`, `capture_source`, `curate_note_link`,
  `workspace` all already imported/defined in this file):

  ```python
  def test_curate_note_link_accepts_checked_catalog_source_target(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      capture_source(
          vault,
          "source-alpha",
          "Alpha Source",
          "A fixture source.",
          "Alpha content about outcomes.",
          machine="capture-machine",
      )
      _md(
          vault / "notes/claim.md",
          "type: note\ncheck_status: checked\ntitle: Claim\nstatus: accepted\n",
      )

      result = curate_note_link(
          vault,
          "claim",
          "supports",
          "catalog/sources/source-alpha",
          actor="pi",
          reason="claim grounded in work",
          machine="curator",
      )

      assert result["target_path"] == "catalog/sources/source-alpha"
      assert result["changed"] is True
      source_fm = read_frontmatter(vault / "notes/claim.md")
      assert source_fm["links"] == {"supports": ["catalog/sources/source-alpha"]}


  def test_curate_note_link_rejects_unchecked_catalog_source_target(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      state.upsert_catalog_record(vault, work_id="source-beta", title="Beta Source")
      _md(
          vault / "notes/claim.md",
          "type: note\ncheck_status: checked\ntitle: Claim\nstatus: accepted\n",
      )

      with pytest.raises(ValueError, match="not checked"):
          curate_note_link(
              vault,
              "claim",
              "supports",
              "catalog/sources/source-beta",
              actor="pi",
              machine="curator",
          )


  def test_curate_note_link_missing_catalog_source_raises_file_not_found(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      _md(
          vault / "notes/claim.md",
          "type: note\ncheck_status: checked\ntitle: Claim\nstatus: accepted\n",
      )

      with pytest.raises(FileNotFoundError):
          curate_note_link(
              vault, "claim", "supports", "catalog/sources/missing", actor="pi", machine="curator"
          )
  ```

- [x] Run to verify failure:
  `python -m pytest "tests/test_knowledge.py::test_curate_note_link_accepts_checked_catalog_source_target" -v`
  — expected: `FileNotFoundError: .../catalog/sources/source-alpha` raised
  from `_checked_concept`'s `is_file()` gate (`knowledge.py:3408-3409`).
  (The other two may pass incidentally — the missing-source case already
  raises FileNotFoundError for the wrong reason; keep them as pinning tests.)

- [x] Write the minimal implementation. In
  `src/memoria_vault/runtime/knowledge.py` replace `_checked_concept`
  (:3406-3415) with:

  ```python
  def _checked_concept(vault: Path, relpath: str) -> dict[str, Any]:
      if relpath.startswith("catalog/sources/"):
          return _checked_catalog_source(vault, relpath)
      path = vault / relpath
      if not path.is_file():
          raise FileNotFoundError(path)
      frontmatter = read_frontmatter(path)
      if not _has_checked_verdict(vault, relpath):
          raise ValueError(f"{relpath} is not checked")
      if not _is_current_frontmatter(frontmatter):
          raise ValueError(f"{relpath} is not current")
      return frontmatter


  def _checked_catalog_source(vault: Path, relpath: str) -> dict[str, Any]:
      row = state.catalog_source(vault, relpath)
      if row is None:
          raise FileNotFoundError(vault / relpath)
      if str(row.get("check_status") or "") != "checked":
          raise ValueError(f"{relpath} is not checked")
      return {
          "type": "work",
          "title": str(row.get("title") or row["work_id"]),
          "work_id": str(row["work_id"]),
      }
  ```

- [x] Run to verify pass:
  `python -m pytest tests/test_knowledge.py -v -k catalog_source_target`
  — expected: 3 passed.

- [ ] Commit:
  `git add src/memoria_vault/runtime/knowledge.py tests/test_knowledge.py`
  then commit with message:

  ```
  feat(graph): resolve virtual catalog targets through the DB row, not is_file (EDGES §2)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
  ```

**Steps — cycle 2 (argument-graph claim→work traversal):**

- [x] Write the failing test (append to `tests/test_project_knowledge.py`;
  `state`, `_md`, `analyze_project_argument` already imported):

  ```python
  def test_analyze_project_argument_traverses_claim_to_work_bridge(tmp_path: Path) -> None:
      state.upsert_catalog_record(
          tmp_path, work_id="source-alpha", title="Alpha Source", check_status="checked"
      )
      _md(
          tmp_path / "projects/project-alpha/project.md",
          "type: project\ncheck_status: checked\ntitle: Alpha project\n"
          "description: Project\nthesis: notes/thesis.md\n",
      )
      _md(
          tmp_path / "notes/thesis.md",
          "type: note\ncheck_status: checked\ntitle: Thesis\n",
      )
      _md(
          tmp_path / "notes/support.md",
          "type: note\ncheck_status: checked\ntitle: Support\n"
          "links:\n  supports:\n    - notes/thesis.md\n    - catalog/sources/source-alpha\n",
      )

      result = analyze_project_argument(tmp_path, "projects/project-alpha/project.md")

      assert {
          "source": "notes/support.md",
          "target": "catalog/sources/source-alpha",
          "type": "supports",
      } in result["edges"]
      roles = {node["path"]: node["role"] for node in result["nodes"]}
      assert roles["catalog/sources/source-alpha"] == "work"
      # Retraction blast radius: a walk rooted at the WORK reaches every
      # transitively grounded claim through the bridge.
      neighbors: dict[str, set[str]] = {}
      for edge in result["edges"]:
          neighbors.setdefault(edge["source"], set()).add(edge["target"])
          neighbors.setdefault(edge["target"], set()).add(edge["source"])
      seen = {"catalog/sources/source-alpha"}
      queue = ["catalog/sources/source-alpha"]
      while queue:
          for neighbor in neighbors.get(queue.pop(), set()):
              if neighbor not in seen:
                  seen.add(neighbor)
                  queue.append(neighbor)
      assert {"notes/support.md", "notes/thesis.md"} <= seen
  ```

- [x] Run to verify failure:
  `python -m pytest "tests/test_project_knowledge.py::test_analyze_project_argument_traverses_claim_to_work_bridge" -v`
  — expected: AssertionError on the `in result["edges"]` membership
  (claim→work edge dropped by `_note_edges`' `target in notes` filter,
  `knowledge.py:3007`).

- [x] Write the minimal implementation in
  `src/memoria_vault/runtime/knowledge.py`:

  Replace `_note_edges` (:3001-3009) with:

  ```python
  def _note_edges(
      notes: dict[str, dict[str, Any]],
      *,
      works: set[str] | frozenset[str] = frozenset(),
  ) -> list[dict[str, str]]:
      edges = []
      for source, frontmatter in notes.items():
          for link_type in ("supports", "contradicts", "extends"):
              for raw in _link_values(frontmatter, link_type):
                  target = _link_target(raw)
                  if target != source and (target in notes or target in works):
                      edges.append({"source": source, "target": target, "type": link_type})
      return edges
  ```

  In `analyze_project_argument`, replace line 1691
  (`edges = _note_edges(notes)`) with:

  ```python
      works = {f"catalog/sources/{row['work_id']}" for row in state.catalog_sources(vault)}
      edges = _note_edges(notes, works=works)
  ```

  Replace the `nodes` list comprehension (:1718-1725) with:

  ```python
          "nodes": [
              {
                  "path": rel,
                  "title": (
                      str(notes[rel].get("title") or Path(rel).stem)
                      if rel in notes
                      else Path(rel).name
                  ),
                  "role": (
                      "thesis"
                      if rel == thesis_rel
                      else ("note" if rel in notes else "work")
                  ),
              }
              for rel in sorted(component)
          ],
  ```

  (`read_project_slice`'s call at :2422 keeps the default `works=frozenset()`
  — its member-path filter drops work targets by design; unchanged.)

- [x] Run to verify pass:
  `python -m pytest "tests/test_project_knowledge.py::test_analyze_project_argument_traverses_claim_to_work_bridge" tests/test_project_knowledge.py tests/test_knowledge.py tests/test_gap_analysis.py -v`
  — expected: all pass (gap analysis and existing argument tests guard
  against regressions from the `_note_edges` signature change).

- [ ] Commit:
  `git add src/memoria_vault/runtime/knowledge.py tests/test_project_knowledge.py`
  with message:

  ```
  feat(graph): argument graph keeps claim→work edges; retraction blast radius reaches claims (EDGES §2)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
  ```

---

### Task ERP-B.2: `state.insert_concept_edge` — single-row upsert

> **Execution override — v16 identity form:** Follow the 2026-07-29
> path-projection amendment, point 5.  The historical path-as-ID INSERT,
> target-id conflict key, and raw-ID fixtures below are superseded by the
> source-resolution / durable-`target_path` triple contract.

> **Binding constraint from NID-B.7 (2026-08-01) — `target_path` must be keyed by
> `state._concept_edge_target_path`, not `normalize_path`.** Point 5 above says only
> that `insert_concept_edge` "keeps a normalized `target_path`". That is not enough.
> `replace_concept_edges` keys its rows through `_concept_edge_target_path`
> (`state.py:2489`), which collapses the bare `work_id`, the rendered
> `catalog/sources/<work_id>`, the `./`-prefixed and the `/source.md` forms of a
> catalog reference onto **one** `target_path`; `normalize_path` collapses none of
> them. Two rows admitted under different `target_path` spellings are distinct PK
> triples, but they resolve to the same `target_concept_id`, so NID-B.7's
> `_resolve_pending_concept_edges_conn` computes `concept_edge_id(source, relation,
> target_id)` **twice** and the second `UPDATE` violates the UNIQUE
> `idx_concept_edges_edge_id`. That raises inside `with connect(vault) as conn:` in
> `replace_concept_edges`, so **the whole mirror pass rolls back** — the exact
> failure mode B.7 removed from the re-key path, reintroduced through a second
> producer, and it would take out `memoria index` vault-wide rather than the one bad
> row. `insert_concept_edge` must therefore call `_concept_edge_target_path` with the
> live `catalog_sources` id set (or an equivalent that is provably the same key
> function), and ERP-B.2's tests must include two spellings of one catalog work
> inserted through the public seam, followed by a `replace_concept_edges` pass that
> does not raise. **That test discriminates only if the work is already in
> `catalog_sources` at insert time** — `_concept_edge_target_path` collapses nothing
> for a work it does not know, so against an absent work both spellings stay pending
> under correct *and* incorrect code and the pass never raises. Seed the work first.
> ERP-B.4 deletes by the same triple, so it inherits the same key function. See also
> cross-section contract 4 for this function's call ordering.

> **Execution amendment (2026-08-01) — what ERP-B.2 landed.** Three deviations from
> the step text below, none of them contract changes.
> **(1) Placement.** `insert_concept_edge` sits after `_concept_edge_target_path`
> rather than literally adjacent to `replace_concept_edges`, so that function's
> private helpers stay beside their only caller; it is still the public single-row
> seam immediately before the public `concept_edges` reader.
> **(2) A settled target survives a spelling that stopped resolving.** When a stored
> row's `target_path` no longer resolves — its target moved out of band, so
> `concepts.path` left the durable key behind — the upsert keeps the
> `target_concept_id`/`edge_id` the row already holds instead of re-deriving NULL.
> That is the same defense `replace_concept_edges` carries in SQL
> (`COALESCE(excluded.target_concept_id, …)` / `CASE WHEN excluded.edge_id != ''`);
> dropping it here un-resolves a live edge and breaks ERP-D.5's stable-`edge_id`
> contract. Pinned by `test_insert_concept_edge_keeps_a_settled_target_whose_path_moved`.
> **(3) Six tests, not two.** The drafted pair cannot see v16 keying at all. It is
> joined by the four-spelling catalog fold this section's NID-B.7 blockquote
> requires; a pending-row test proving `edge_id` stays `''` until the target
> resolves and that **both** settlers — a re-upsert and B.7's resolution pass —
> settle it (asserting storage between them, because B.7's pass is an absorbing
> state that hides a re-upsert which resolved nothing); the out-of-band move above;
> and an unbound-`OperationContext` refusal for the `validate_operation_context`
> call the Interfaces list already required. The drafted body's local `source_id` is
> renamed `source_concept`: `tests/test_identifier_renames.py` forbids that token
> anywhere under `src/`.

**Files:**
- Modify: `src/memoria_vault/runtime/state.py` (insert the new function
  directly after `replace_concept_edges`, i.e. after :2052 at the `9c77ba61`
  baseline — after Plan 22's G2S1.1/.2 edits, after that function wherever it
  then ends; `concept_edges` reader at :2055 follows it)
- Modify: `tests/test_runtime_state.py` (append; `workspace` helper at :56,
  `state`/`json`/`pytest` already imported — add `operation_context` to the
  `tests.helpers` import at :29)

**Interfaces:**
- Consumes: `state.concept_edge_id(source, relation, target) -> str`
  (Plan 22 G2S1.2); `concept_edges.edge_id` + `attributes_json` columns
  (schema v13, G2S1.2); `EDGE_RELATIONS` from
  `memoria_vault.runtime.subsystems.lib.edges` (ERP-A roster task — must land
  first); `validate_operation_context` (`trusted_writer.py:139`, imported
  function-locally to avoid the module cycle);
  `normalize_path`, `connect`, `now_iso` (already module-level in state.py).
- Produces:
  `state.insert_concept_edge(vault: Path, *, source: str, relation_type: str, target: str, attributes: dict[str, Any] | None = None, context: OperationContext) -> dict[str, Any]`
  returning `{"edge_id": str, "created": bool, "attributes": dict[str, Any]}`.
  Contract: single-row upsert keyed on the PK triple; `edge_id` from
  `concept_edge_id` (deterministic); on conflict merges `attributes` over the
  existing `attributes_json` (None leaves existing attributes untouched) —
  this is the "upsert mode" EDGES §4 later uses for warrant text;
  `check_status='checked'`, `source_path=''` (no file owns the row); rejects
  relations outside `EDGE_RELATIONS` and self-loops.

**Steps:**

- [x] Write the failing tests (append to `tests/test_runtime_state.py`; first
  extend the import at :29 to
  `from tests.helpers import call_with_context, copy_memoria_dirs, git, init_git, operation_context`):

  ```python
  def test_insert_concept_edge_upserts_one_row_and_preserves_attributes(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      context = operation_context(vault)

      first = state.insert_concept_edge(
          vault,
          source="notes/left.md",
          relation_type="tension",
          target="notes/right.md",
          attributes={"warrant": "same trial, opposite outcomes"},
          context=context,
      )
      second = state.insert_concept_edge(
          vault,
          source="notes/left.md",
          relation_type="tension",
          target="notes/right.md",
          context=context,
      )

      assert first["created"] is True
      assert second["created"] is False
      assert first["edge_id"] == second["edge_id"]
      assert first["edge_id"] == state.concept_edge_id(
          "notes/left.md", "tension", "notes/right.md"
      )
      assert second["attributes"] == {"warrant": "same trial, opposite outcomes"}
      with state.connect(vault) as conn:
          rows = conn.execute(
              """
              SELECT edge_id, check_status, source_path, attributes_json
              FROM concept_edges
              WHERE source_concept_id = 'notes/left.md'
              """
          ).fetchall()
      assert len(rows) == 1
      assert rows[0]["edge_id"] == first["edge_id"]
      assert rows[0]["check_status"] == "checked"
      assert rows[0]["source_path"] == ""
      assert json.loads(rows[0]["attributes_json"]) == {
          "warrant": "same trial, opposite outcomes"
      }


  def test_insert_concept_edge_rejects_unknown_relation_and_self_loop(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      context = operation_context(vault)

      with pytest.raises(ValueError, match="relation"):
          state.insert_concept_edge(
              vault,
              source="notes/left.md",
              relation_type="refutes",
              target="notes/right.md",
              context=context,
          )
      with pytest.raises(ValueError, match="distinct"):
          state.insert_concept_edge(
              vault,
              source="notes/left.md",
              relation_type="tension",
              target="notes/left.md",
              context=context,
          )
  ```

- [x] Run to verify failure:
  `python -m pytest tests/test_runtime_state.py -v -k insert_concept_edge`
  — expected: `AttributeError: module 'memoria_vault.runtime.state' has no
  attribute 'insert_concept_edge'`.

- [x] Write the minimal implementation (after `replace_concept_edges` in
  `src/memoria_vault/runtime/state.py`):

  ```python
  def insert_concept_edge(
      vault: Path,
      *,
      source: str,
      relation_type: str,
      target: str,
      attributes: dict[str, Any] | None = None,
      context: OperationContext,
  ) -> dict[str, Any]:
      """Upsert one PI-confirmed concept edge without touching other rows.

      The single-row seam for edges that are never mirrored from frontmatter
      (tension confirmation; warrant text hung on a grounding edge). On
      conflict the given attributes merge over the stored attributes_json;
      passing None leaves stored attributes untouched.
      """
      from memoria_vault.runtime.subsystems.lib.edges import EDGE_RELATIONS
      from memoria_vault.runtime.trusted_writer import validate_operation_context

      validate_operation_context(vault, context)
      relation = str(relation_type).strip().lower().replace("_", "-")
      if relation not in EDGE_RELATIONS:
          raise ValueError(f"unknown concept edge relation: {relation_type}")
      source_id = normalize_path(str(source))
      target_id = normalize_path(str(target))
      if not source_id or not target_id or source_id == target_id:
          raise ValueError("concept edge requires two distinct endpoints")
      edge_id = concept_edge_id(source_id, relation, target_id)
      with connect(vault) as conn:
          row = conn.execute(
              """
              SELECT attributes_json FROM concept_edges
              WHERE source_concept_id = ? AND relation_type = ? AND target_concept_id = ?
              """,
              (source_id, relation, target_id),
          ).fetchone()
          existing = json.loads(row["attributes_json"] or "{}") if row is not None else {}
          merged = {**existing, **(attributes or {})}
          conn.execute(
              """
              INSERT INTO concept_edges(
                  edge_id,
                  source_concept_id,
                  relation_type,
                  target_concept_id,
                  check_status,
                  source_path,
                  attributes_json,
                  updated_at
              )
              VALUES (?, ?, ?, ?, 'checked', '', ?, ?)
              ON CONFLICT(source_concept_id, relation_type, target_concept_id) DO UPDATE SET
                  edge_id = excluded.edge_id,
                  attributes_json = excluded.attributes_json,
                  updated_at = excluded.updated_at
              """,
              (
                  edge_id,
                  source_id,
                  relation,
                  target_id,
                  json.dumps(merged, sort_keys=True),
                  now_iso(),
              ),
          )
      return {"edge_id": edge_id, "created": row is None, "attributes": merged}
  ```

  (If G2S1.2 landed `edge_id` as the PK instead of the triple, change the
  `ON CONFLICT` target to `(edge_id)` — same semantics, deterministic id over
  the same triple. `OperationContext` is already TYPE_CHECKING-imported at
  `state.py:49`.)

- [x] Run to verify pass:
  `python -m pytest tests/test_runtime_state.py -v -k insert_concept_edge`
  — expected: 2 passed.

- [ ] Commit:
  `git add src/memoria_vault/runtime/state.py tests/test_runtime_state.py`
  with message:

  ```
  feat(graph): state.insert_concept_edge single-row upsert with deterministic edge_id (EDGES §3)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
  ```

---

### Task ERP-B.3: `confirm-tension` outcome on resolve-attention + candidate prompt surface

> **Execution amendment (2026-08-01) — what ERP-B.3 landed.** Five deviations from
> the step text below, none of them contract changes.
> **(1) The drafted `_tension_rows` helper reads pre-v16 storage.** It selects
> `source_concept_id`/`target_concept_id` and compares them with paths, which after
> NID-B are identities. Endpoints are asserted through
> `edges.concept_edge_path_records(vault, checked_only=False)` (the 2026-07-29
> amendment's rule), and "exactly one row" / "no row" are asserted with a raw
> `COUNT(*)` — that projection drops a row whose endpoints render nowhere, so
> counting through it would let a bad row hide behind a lossy accessor.
> **(2) A pre-sorted fixture cannot see `sorted()`.** `_checked_tension_rows` walks
> `iter_markdown`, which sorts within a directory, so a flat `notes/a.md` +
> `notes/b.md` pair always arrives in lexical order and dropping the `sorted()` call
> survives. `_unsorted_pair_vault` puts one note in a subdirectory (`notes/zzz.md`
> beside `notes/aaa/x.md`), which `os.walk` yields in reverse lexical order, so
> contract 6's ordering is load-bearing in the payload assertion.
> **(3) Nine tests, not two.** The drafted refusal test reaches only the
> `prompt_kind` branch, so the payload-shape and blank-endpoint refusals are
> unpinned; they are one parametrization with a distinct fixture and message per
> branch. Added alongside: dedupe across sweeps (the `dedupe_slug` digest and the
> `prompt is not None` guard); a `commit=False` sweep writing nothing; an idempotent
> second confirmation ("mints exactly one row"); the check→journal ordering below;
> and `tension_edge` being absent for every other outcome, which is the key a caller
> tests for.
> **(4) The mint is ordered ahead of the journal, and that ordering is pinned.**
> `insert_concept_edge`, `append_journal_event` and `emit_disposition_event` each
> commit their own transaction, so a mint placed after them would leave an accepted
> `disposition.v1` standing for a confirmation that raised.
> `test_confirm_tension_refusal_precedes_the_disposition_it_would_record` reaches the
> write and asserts the journal stayed empty.
> **(5) No CLI verb, no key of its own.** `attention resolve` grows no
> `--confirm-tension` flag — the plan's Files list scopes this task to `inbox.py` and
> `integrity.py`, and the worker passes `payload["outcome"]` through unchanged, which
> is the surface the Interfaces name. `_confirm_tension_edge` hands **paths** to
> `insert_concept_edge` and derives no edge key at all, so cross-section contract 4's
> `_concept_edge_target_path` requirement is met by delegation rather than by a
> second copy of the fold. One consequence of the drafted commit restructure worth
> naming: a passing-gate `commit=True` sweep now produces a `surface tension
> candidates` commit where before it produced none.

**Files:**
- Modify: `src/memoria_vault/runtime/subsystems/lib/inbox.py`
  (`write_work_prompt` :116-172; imports :9-16)
- Modify: `src/memoria_vault/runtime/integrity.py`
  (`surface_tensions` result tail :822-869; `resolve_attention` :1127-1191 —
  outcome vocab :1141-1146, disposition map :1164-1173, return :1191;
  new private helper `_confirm_tension_edge`)
- Modify: `tests/test_integrity_surface_tensions.py` (append; add
  `import pytest`, `resolve_attention` wrapper, and
  `rebuild_passage_index_explicit` import)

**Interfaces:**
- Consumes: `state.insert_concept_edge` (ERP-B.2);
  `emit_disposition_event(vault, *, decision, item_type, item_id, context)`
  (`operations.py:146` — I1 `disposition.v1` seam; closed `DECISIONS` enum at
  `engine/empirical_events.py:32` is **unchanged**);
  `write_work_prompt` (`inbox.py:116`); `_sha256_text` (`integrity.py:1620`);
  Plan 22 G2S1.1 upsert-and-prune sparing tension rows (reindex survival);
  `rebuild_passage_index_explicit(vault, *, actor, machine)`
  (`indexing.py:25`); worker dispatch `worker.py:813-831` passes
  `payload["outcome"]` through unchanged — no worker edit.
- Produces:
  - `write_work_prompt(..., prompt_kind: str = "", payload: dict[str, Any] | None = None) -> Path | None`
    — optional structured frontmatter `payload:` map on the card.
  - `surface_tensions` result gains `"tension_prompts": list[str]` (rel paths
    of per-candidate cards; written only when `commit=True`, deduped by
    sorted-pair digest slug `tension-<sha12>`, `prompt_kind="tension-candidate"`,
    `payload={"source": <lexical-min>, "target": <lexical-max>}`).
  - `resolve_attention(..., resolution="resolved", outcome="confirm-tension", ...)`
    — new outcome riding `resolution=resolved`; outcome→decision map gains
    `confirm-tension → accept`; mints exactly one tension row from the target
    card's payload; result gains `"tension_edge": {"edge_id", "created", "attributes"}`
    when the outcome is confirm-tension.
  - `_confirm_tension_edge(vault: Path, target: str, *, context: OperationContext) -> dict[str, Any]`
    (private; rejects cards whose `prompt_kind != "tension-candidate"` or
    that lack a source/target payload).

**Steps — cycle 1 (candidate prompt surface):**

- [x] Write the failing test (append to
  `tests/test_integrity_surface_tensions.py`):

  ```python
  def test_surface_tensions_commit_writes_confirmable_tension_prompts(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      left = "notes/recall-up.md"
      right = "notes/recall-not-up.md"
      _stage_checked_note(vault, left, "Recall up", "The intervention improved recall.")
      _stage_checked_note(vault, right, "Recall not up", "The intervention did not improve recall.")

      result = surface_tensions(vault, commit=True, tier2=False, machine="integrity-machine")

      assert result["candidate_count"] == 1
      [prompt_rel] = result["tension_prompts"]
      frontmatter = read_frontmatter(vault / prompt_rel)
      assert frontmatter["prompt_kind"] == "tension-candidate"
      assert frontmatter["payload"] == {
          "source": "notes/recall-not-up.md",
          "target": "notes/recall-up.md",
      }
  ```

- [x] Run to verify failure:
  `python -m pytest "tests/test_integrity_surface_tensions.py::test_surface_tensions_commit_writes_confirmable_tension_prompts" -v`
  — expected: `KeyError: 'tension_prompts'`.

- [x] Write the minimal implementation.

  In `src/memoria_vault/runtime/subsystems/lib/inbox.py`: add
  `from typing import Any` to the imports (:11 block), extend the
  `write_work_prompt` signature (:127) with
  `payload: dict[str, Any] | None = None,` after `prompt_kind`, and after the
  `if prompt_kind:` block (:155-156) add:

  ```python
      if payload:
          frontmatter["payload"] = payload
  ```

  In `src/memoria_vault/runtime/integrity.py`: replace the result tail of
  `surface_tensions` (:822-855, from `attention_path = ""` through the
  degraded commit) with:

  ```python
      attention_path = ""
      tension_prompts: list[str] = []
      finding: dict[str, Any] | None = None
      commit_hash = ""
      commit_paths: list[str] = []
      if commit:
          for candidate in candidates:
              pair = sorted((candidate["left"], candidate["right"]))
              digest = _sha256_text("\0".join(pair))[:12]
              prompt = write_work_prompt(
                  vault,
                  f"Confirm tension: {candidate['left_title']} vs {candidate['right_title']}",
                  (
                      "Resolve this card with outcome confirm-tension to record "
                      "the tension edge, or reject it."
                  ),
                  candidate["warrant"],
                  "surface-tensions",
                  target=candidate["left"],
                  posture="co-pi",
                  loudness="notice",
                  dedupe_slug=f"tension-{digest}",
                  prompt_kind="tension-candidate",
                  payload={"source": pair[0], "target": pair[1]},
              )
              if prompt is not None:
                  rel = prompt.relative_to(vault).as_posix()
                  tension_prompts.append(rel)
                  commit_paths.append(rel)
      if not gate["passed"]:
          finding = record_integrity_check(
              vault,
              "knowledge",
              check="contradiction-tier1-hans",
              status="failed",
              reason="contradiction detection degraded: NLI below HANS bar",
              shadow=False,
              route="ask",
              context=context,
          )
          if commit:
              path = write_work_prompt(
                  vault,
                  "Contradiction detection degraded",
                  "Review lexical tension candidates before setting contradiction links.",
                  (
                      "Tier-1 contradiction detection did not pass the HANS-style "
                      "overlap-but-opposite gate, so lexical candidates require PI review."
                  ),
                  "surface-tensions",
                  target="knowledge",
                  posture="co-pi",
                  loudness="alert",
                  dedupe_slug="contradiction-detection-degraded",
              )
              attention_path = path.relative_to(vault).as_posix() if path else ""
              if attention_path:
                  commit_paths.append(attention_path)
      if commit and (commit_paths or finding):
          message = (
              "surface degraded contradiction detection"
              if not gate["passed"]
              else "surface tension candidates"
          )
          commit_hash = commit_writer_changes(vault, message, commit_paths, context=context)
  ```

  and add `"tension_prompts": tension_prompts,` to the return dict (:856-869,
  next to `"attention_path"`).

- [x] Run to verify pass:
  `python -m pytest tests/test_integrity_surface_tensions.py -v`
  — expected: all pass (existing degraded-path asserts only check
  `attention_path`, finding route, and untouched `links:` — preserved).

- [ ] Commit:
  `git add src/memoria_vault/runtime/subsystems/lib/inbox.py src/memoria_vault/runtime/integrity.py tests/test_integrity_surface_tensions.py`
  with message:

  ```
  feat(graph): per-candidate tension prompts carry a source/target payload (EDGES §3)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
  ```

**Steps — cycle 2 (confirm-tension outcome + reindex survival):**

- [x] Write the failing tests (append to
  `tests/test_integrity_surface_tensions.py`; extend the file's imports with
  `import pytest`, `from memoria_vault.runtime.indexing import rebuild_passage_index_explicit`,
  `from memoria_vault.runtime.integrity import resolve_attention as _resolve_attention`,
  and add the wrapper next to the existing ones):

  ```python
  def resolve_attention(vault: Path, *args, **kwargs):
      return call_with_context(_resolve_attention, vault, *args, **kwargs)


  def _tension_rows(vault: Path) -> list[tuple[str, str, str]]:
      with state.connect(vault) as conn:
          return [
              tuple(row)
              for row in conn.execute(
                  """
                  SELECT source_concept_id, relation_type, target_concept_id
                  FROM concept_edges
                  WHERE relation_type = 'tension'
                  ORDER BY source_concept_id, target_concept_id
                  """
              ).fetchall()
          ]


  def test_confirm_tension_outcome_mints_one_edge_row_surviving_reindex(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      left = "notes/recall-up.md"
      right = "notes/recall-not-up.md"
      _stage_checked_note(vault, left, "Recall up", "The intervention improved recall.")
      _stage_checked_note(vault, right, "Recall not up", "The intervention did not improve recall.")
      surfaced = surface_tensions(vault, commit=True, tier2=False, machine="integrity-machine")
      [prompt_rel] = surfaced["tension_prompts"]

      result = resolve_attention(
          vault,
          prompt_rel,
          resolution="resolved",
          outcome="confirm-tension",
          reason="PI confirmed the tension",
          actor="pi",
          machine="curator",
      )

      expected = [("notes/recall-not-up.md", "tension", "notes/recall-up.md")]
      assert result["tension_edge"]["created"] is True
      assert _tension_rows(vault) == expected
      with state.connect(vault) as conn:
          rows = conn.execute("SELECT payload_json FROM event_log ORDER BY event_id").fetchall()
      dispositions = [
          payload
          for payload in (json.loads(row["payload_json"]) for row in rows)
          if payload.get("schema") == "disposition.v1"
      ]
      assert [d["decision"] for d in dispositions] == ["accept"]

      # G2S1.1's upsert-and-prune spares tension rows: reindex must not eat it.
      rebuild_passage_index_explicit(vault, actor="operation", machine="reindex")

      assert _tension_rows(vault) == expected


  def test_confirm_tension_rejects_cards_without_tension_payload(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      (vault / "inbox").mkdir(parents=True, exist_ok=True)
      (vault / "inbox/work-prompt-other.md").write_text(
          "---\nprojection: attention\nattention_kind: work-prompt\n---\nBody.\n",
          encoding="utf-8",
      )

      with pytest.raises(ValueError, match="tension-candidate"):
          resolve_attention(
              vault,
              "inbox/work-prompt-other.md",
              resolution="resolved",
              outcome="confirm-tension",
              actor="pi",
              machine="curator",
          )
      assert _tension_rows(vault) == []
  ```

- [x] Run to verify failure:
  `python -m pytest tests/test_integrity_surface_tensions.py -v -k confirm_tension`
  — expected: `ValueError: unsupported attention outcome for resolved:
  'confirm-tension'` (from `integrity.py:1145-1146`).

- [x] Write the minimal implementation in
  `src/memoria_vault/runtime/integrity.py`:

  1. Outcome vocab (:1142-1144):

     ```python
         supported_outcomes = (
             {"acknowledged"}
             if resolution == "acknowledged"
             else {"apply", "reject", "defer", "confirm-tension"}
         )
     ```

  2. After `decided_at = now_iso()` (:1151), before the event dict, insert:

     ```python
         tension_edge: dict[str, Any] | None = None
         if resolution == "resolved" and outcome == "confirm-tension":
             tension_edge = _confirm_tension_edge(vault, target, context=context)
     ```

  3. Disposition map (:1169):

     ```python
                 decision={
                     "apply": "accept",
                     "reject": "reject",
                     "defer": "defer",
                     "confirm-tension": "accept",
                 }[outcome],
     ```

  4. Return (:1191):

     ```python
         result: dict[str, Any] = {"event": row, "commit": commit}
         if tension_edge is not None:
             result["tension_edge"] = tension_edge
         return result
     ```

  5. New helper directly after `resolve_attention`:

     ```python
     def _confirm_tension_edge(
         vault: Path, target: str, *, context: OperationContext
     ) -> dict[str, Any]:
         path = vault / target
         if not path.is_file():
             raise FileNotFoundError(path)
         frontmatter = read_frontmatter(path)
         if frontmatter.get("prompt_kind") != "tension-candidate":
             raise ValueError(f"confirm-tension requires a tension-candidate prompt: {target}")
         payload = frontmatter.get("payload")
         if not isinstance(payload, dict):
             raise ValueError(f"{target} is missing its tension payload")
         source = str(payload.get("source") or "").strip()
         edge_target = str(payload.get("target") or "").strip()
         if not source or not edge_target:
             raise ValueError(f"{target} tension payload must carry source and target")
         return state.insert_concept_edge(
             vault,
             source=source,
             relation_type="tension",
             target=edge_target,
             context=context,
         )
     ```

     (`read_frontmatter` is already imported in integrity.py — used at :885.)

- [x] Run to verify pass:
  `python -m pytest tests/test_integrity_surface_tensions.py tests/test_feedback_instrumentation.py tests/test_integrity.py -v`
  — expected: all pass (the parametrized disposition test at
  `test_feedback_instrumentation.py:22-49` is untouched; DECISIONS enum
  unchanged).

- [ ] Commit:
  `git add src/memoria_vault/runtime/integrity.py tests/test_integrity_surface_tensions.py`
  with message:

  ```
  feat(graph): confirm-tension outcome mints one PI-confirmed tension edge (EDGES §3)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
  ```

---

### Task ERP-B.4: Retraction = row delete — `state.delete_concept_edge`

> **Execution override — v16 identity form:** Follow the 2026-07-29
> path-projection amendment, point 5.  Retraction resolves the source path,
> normalizes the durable target path, and deletes the
> `(source_concept_id, relation_type, target_path)` triple; it never deletes by
> a nullable target ID.

> **Execution amendment (2026-08-01) — what ERP-B.4 landed.** Four deviations
> from the step text below, none of them contract changes.
> **(1) Both endpoint keys come from ERP-B.2's functions, not from
> `normalize_path`.** The drafted body keys `source` and `target` through
> `normalize_path` and deletes by `target_concept_id`; all three are superseded.
> The source resolves through `resolve_concept_id` (a ULID-mirrored note keys its
> row in identity space, so a path-spelled delete would retract nothing), and the
> durable target key comes from `_concept_edge_target_path` with the live
> `catalog_sources` id set — the binding constraint the NID-B.7 blockquote in
> ERP-B.2 states and this task inherits. `delete_concept_edge` is now the third
> caller of that one key function, not a second spelling of it.
> **(2) The relation goes through `_concept_edge_relation`,** not the drafted
> `.strip().lower().replace("_", "-")`. One roster rule across both writers: it
> normalizes the same and it refuses an out-of-roster verb the same, so a typo
> raises instead of returning `{"deleted": 0}` — indistinguishable from "already
> retracted".
> **(3) Five tests, not one.** The drafted test cannot see either key function.
> It is joined by the catalog fold (every pair crosses the bare `work_id`, the
> one spelling `normalize_path` returns unchanged, with the work seeded into
> `catalog_sources` first per ERP-B.2's lesson); an identity-space source test;
> an exact-triple test carrying one neighbour row per key column; and the
> relation-rule test above. The drafted reindex assertion also gained a real
> `supports` link on the source note, so "the tension row did not come back" is
> no longer equally true of a mirror pass that did nothing.
> **(4) No ordering pin for the roster refusal.** The refusal is ordered before
> the DELETE, but the schema CHECK on `concept_edges.relation_type`
> (`schema.sql:254-259`) means no stored row can carry an out-of-roster verb, so
> moving the refusal after the DELETE changes no row and the mutant survives.
> Its one real difference is that the check-first form refuses on a
> not-yet-a-vault path without `connect()` minting a database — a filesystem side
> effect, not this seam's contract, so nothing pins it. B.2's transaction trap
> does not reach this function.

**Files:**
- Modify: `src/memoria_vault/runtime/state.py` (insert directly after
  `insert_concept_edge` from ERP-B.2)
- Modify: `tests/test_runtime_state.py` (append)

**Interfaces:**
- Consumes: `connect`, `normalize_path` (state.py module-level);
  `rebuild_passage_index_explicit` (`indexing.py:25`) + Plan 22 G2S1.1 prune
  semantics (a deleted tension row has no frontmatter mirror, so nothing
  regenerates it — deletion is final).
- Produces:
  `state.delete_concept_edge(vault: Path, *, source: str, relation_type: str, target: str) -> dict[str, int]`
  returning `{"deleted": 0 | 1}`. Contract: exact-triple delete; idempotent;
  no tombstone, no journal ceremony (row absence IS the retraction — see the
  recorded decision at section top for the smallest-honest-verb rationale).

**Steps:**

- [x] Write the failing test (append to `tests/test_runtime_state.py`; add
  `from memoria_vault.runtime.indexing import rebuild_passage_index_explicit`
  to the imports):

  ```python
  def test_delete_concept_edge_retracts_confirmed_tension_row(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      context = operation_context(vault)
      state.insert_concept_edge(
          vault,
          source="notes/left.md",
          relation_type="tension",
          target="notes/right.md",
          context=context,
      )

      first = state.delete_concept_edge(
          vault, source="notes/left.md", relation_type="tension", target="notes/right.md"
      )
      second = state.delete_concept_edge(
          vault, source="notes/left.md", relation_type="tension", target="notes/right.md"
      )

      assert first == {"deleted": 1}
      assert second == {"deleted": 0}
      # Retraction is final: reindex must not resurrect the row (tension has
      # no frontmatter mirror to regenerate from).
      rebuild_passage_index_explicit(vault, actor="operation", machine="reindex")
      with state.connect(vault) as conn:
          count = conn.execute(
              "SELECT COUNT(*) FROM concept_edges WHERE relation_type = 'tension'"
          ).fetchone()[0]
      assert count == 0
  ```

- [x] Run to verify failure:
  `python -m pytest "tests/test_runtime_state.py::test_delete_concept_edge_retracts_confirmed_tension_row" -v`
  — expected: `AttributeError: module 'memoria_vault.runtime.state' has no
  attribute 'delete_concept_edge'`.
  *Measured: all five new tests failed with exactly that `AttributeError`.*

- [x] Write the minimal implementation (after `insert_concept_edge` in
  `src/memoria_vault/runtime/state.py`) — see amendment (1)/(2) above for the
  three key-function corrections to the block below:

  ```python
  def delete_concept_edge(
      vault: Path, *, source: str, relation_type: str, target: str
  ) -> dict[str, int]:
      """Retract one confirmed edge; row absence is the entire record.

      Tension rows carry no status column and no frontmatter mirror
      (existence = confirmation), so deleting the row is the whole
      retraction and reindex never regenerates it.
      """
      relation = str(relation_type).strip().lower().replace("_", "-")
      with connect(vault) as conn:
          deleted = conn.execute(
              """
              DELETE FROM concept_edges
              WHERE source_concept_id = ? AND relation_type = ? AND target_concept_id = ?
              """,
              (normalize_path(str(source)), relation, normalize_path(str(target))),
          ).rowcount
      return {"deleted": int(deleted)}
  ```

- [x] Run to verify pass:
  `python -m pytest "tests/test_runtime_state.py::test_delete_concept_edge_retracts_confirmed_tension_row" -v`
  — expected: 1 passed.
  *Measured: 33 passed in `tests/test_runtime_state.py` (5 new).*

- [x] Run the full gate: `python scripts/verify` — expected: green (lint,
  product gates, tests, offline smoke, syntax).
  *Measured: `verify: OK`.*

- [x] Mutation-test both key functions and the WHERE clause. *Measured: 13
  implementation mutants, 12 killed. The one survivor is the roster-refusal
  reordering, equivalent per amendment (4). Each of the five tests uniquely
  kills the mutant its name claims: the fold test alone kills the
  `normalize_path` target key and an emptied catalog id set; the source test
  alone kills a path-space-only source resolver; the triple test alone kills
  each of the three dropped WHERE conjuncts; the relation test alone kills both
  the dropped roster refusal and the dropped normalization; the retraction test
  alone kills a constant `rowcount`. Six test-direction mutants confirm each
  fixture choice is load-bearing: unseeding the catalog makes the fold test fail
  under correct **and** mutated code (no discrimination either way), pairing two
  `catalog/sources/...` renderings instead of crossing the bare `work_id` lets
  the `normalize_path` mutant survive, dropping the path spelling from the
  source test lets its mutant survive, and dropping the `supports` link makes
  the reindex assertion pass against a mirror pass that wrote nothing.*

- [ ] Commit:
  `git add src/memoria_vault/runtime/state.py tests/test_runtime_state.py`
  with message:

  ```
  feat(graph): tension retraction is a row delete — state.delete_concept_edge (EDGES §3)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
  ```
# Section ERP-C — Typed-consequence propagation engine (EDGES spec §5)

Implements EDGES §5 verbatim: derive-on-write typed consequences over the
grounding closure ∪ derivation DAG, marked as `stale:`/`consequence:`
frontmatter labels through the trusted writer, mirrored in the DB verdict row,
with the shipped `concept_flags` stale row kept for compatibility, and
attention cards raised only at alert/block loudness.

**Execution order within this section:** ERP-C.1 → C.2 → C.3 → C.4 → **C.6 →
C.5** (C.6's `route_consequence_cards` is a pure helper over a marks mapping;
C.5's engine orchestration consumes it, so loudness routing lands first —
task numbering follows the deliverable list, not execution order).

**Cross-plan Consumes (Plan 22, already landed when this plan executes):**
`state.MIGRATIONS: dict[int, tuple[int, list[str | Callable[[sqlite3.Connection], None]]]]`
(G1.1 — key = from_version, value = `(from_version + 1, ordered steps)`),
`state.replace_concept_edges` upsert-and-prune sparing tension rows (G2S1.1),
`state.concept_edge_id(source, relation, target)` sha256-triple `[:24]`
(G2S1.2), edge rows carrying `edge_id` + `attributes_json` (G2S1.2/.3),
`state.evidence_item_closure(rows_by_id: Mapping[str, Mapping[str, Any]], evidence_id: str) -> list[tuple[str, tuple[str, ...]]]`
(S35.3), `evidence_ref_kind(ref) -> "code-grounds" | "evidence-set" | "source-span"`
+ `parse_source_span_ref(ref) -> SourceSpanRef(work_id, page)` (S12.1),
`inbox.write_finding(..., dedupe_slug: str = "") -> Path | None` (Plan 21 task 21.1).

**Cross-section Consumes (this plan):** v16 (NID-B) and v17 (ERP-A) precede
v18 here; `edges.EDGE_RELATIONS` (ERP-A's seven-relation roster in
`src/memoria_vault/runtime/subsystems/lib/edges.py`) is consumed by C.2's
parity test; `stale: bool` + `consequence:` enum registered as optional
fields in the type yamls is owned by the NID closed-validation task (NODES
§3) — C.4 writes the fields and does not touch the yamls;
`state.insert_concept_edge(vault, *, source, relation_type, target, attributes=None, context)`
(EDGES §3, drafted in a sibling section) must call
`propagation.propagate_edge_change` — recorded in C.5 as an obligation on
that section, not wired here.

**SPEC GAP:** the spec assigns no consequence type to `contradicts`/`tension`
hops — the decision table routes them to no-mark/no-traverse rather than
inventing a fifth type (ERP-D's report can still count reach separately).
**SPEC GAP:** warrant/qualifier/rebuttal edge direction is not pinned in §5;
this section reads §4's semantics lines ("note W states the inference license
for claim C") as source = license/bounding/exception note, target = claim,
mirroring `supports`.
**SPEC GAP:** "catalog standing change" is undifferentiated in §5; the
standing seam fires on transitions into `{retracted, superseded}` only
(acceptance criteria name retraction; `archived` is shelving, not falsity).
**SPEC GAP:** "the active project's slice" has no deterministic definition in
the spec; C.6 defines it as: every `type: project` note whose frontmatter
`archived` is not `True`, its `thesis` target, plus undirected
`concept_edges` reachability from those seeds.

---

### Task ERP-C.1: The closure walk — grounding closure ∪ derivation DAG, one pure function

> **Execution override — ERP-C.1 as built (2026-08-01):** the Interfaces block
> below reads `state.concept_edges`; the 2026-07-29 path-projection amendment,
> point 3, supersedes it. `closure_inputs` consumes
> `edges.concept_edge_path_pairs(vault)`, and the pure walk reads that
> projection's `source_path` / `relation_type` / `target_path` fields, never
> `source_concept_id` / `target_concept_id`, so `ClosureInputs.grounding_edges`
> is `tuple[dict[str, str], ...]`. Five further deviations from the code block
> printed below, each because the printed line could not fail a test:
>
> 1. **The self-edge skip is dropped.** `if source == target: continue` cannot
>    change an answer: a self-hop's dependent is always either already marked or
>    a start, so the guard below absorbs it. The derivation DAG's real self-loop
>    — `observed_external_edit` records the edited file as its own `prior-head`
>    input — is covered by test instead.
> 2. **The `expanded` visited set is dropped.** Nothing is queued twice, because
>    a dependent is marked before it is queued. That leaves
>    `if dependent in marked or dependent in starts` as the one guard carrying
>    cycle safety, and removing it — or either half — is the only mutation in
>    this task that never terminates.
> 3. **`seed = depth == 0 and current not in marked` loses its first clause.**
>    Every queued node above depth 0 is already marked, so `depth == 0` could
>    not change the answer.
> 4. **The `try`/`except ValueError` around `evidence_ref_kind` is dropped.**
>    Every leaf `evidence_item_closure` returns has already parsed as one of the
>    three ref kinds, exactly as `knowledge._evidence_source_standing_findings`
>    reads them. The normalization that is live moved to `_journal_ref`, the one
>    boundary where free-form payload (`output_id`, `inputs[].id`) enters path
>    space; `block_ref` is normalized by `replace_evidence_sets` on write and is
>    not normalized again here.
> 5. **No `∪` in code prose.** ruff's RUF002 rejects that character in a
>    docstring, so the module and its tests say "grounding closure and
>    derivation DAG".
>
> `tests/conftest.py` registers `"test_propagation.py": "runtime"`. C.1 carries
> no schema change of its own: `consequence` storage stays with C.3, which takes
> `SCHEMA_VERSION + 1` per the 2026-08-01 amendment above — rung 18 went to the
> I1 plan's `telemetry_events` table.

**Files:**
- Create: `src/memoria_vault/runtime/propagation.py`
- Create: `tests/test_propagation.py`
- Modify: `tests/conftest.py` (`TEST_LEVELS` dict at line 18 — register the new file)

**Interfaces:**
- Consumes: `state.concept_edges(vault, *, checked_only=True) -> list[dict]` (state.py:2055-2076), `state.evidence_sets(vault) -> list[dict]` (state.py:2335-2347, rows carry `id`, `block_ref`, `items`), `state.evidence_item_closure(rows_by_id, evidence_id) -> list[tuple[str, tuple[str, ...]]]` (Plan 22 S35.3), `state.read_event_log(vault, *, event_types)` (state.py:930), `evidence_ref_kind` / `parse_source_span_ref` (evidence.py:64/:44; post-Plan-22 kinds `code-grounds`/`evidence-set`/`source-span`), `EVENT_DERIVED` / `EVENT_OBSERVED_EXTERNAL_EDIT` (trusted_writer.py:42-43), `normalize_path` (policy/paths.py:12). The walk mirrors the DAG inversion in `integrity._downstream_events` (integrity.py:1022-1048) — that function keeps walking only the DAG; this one is the union the spec says closes the gap.
- Produces:
  - `CONSEQUENCE_TYPES: tuple[str, ...] = ("grounds-lost", "warrant-lost", "qualifier-regression", "rebuttal-strengthened")` — the single roster, owned here.
  - `TRIGGERS: tuple[str, ...] = ("claim-changed", "claim-retracted", "edge-added", "edge-removed", "standing-changed", "decided-wrong")`
  - `HOP_EVIDENCE = "evidence"`, `HOP_DERIVED = "derived"` (non-edge hop kinds).
  - `consequence_closure(start_ids: Collection[str], *, trigger: str, grounding_edges: Iterable[Mapping[str, Any]], evidence_dependents: Mapping[str, Collection[str]], derivation_children: Mapping[str, Collection[str]], typer: Callable[..., str | None], initial_marks: Mapping[str, str] | None = None) -> dict[str, dict[str, Any]]` — pure, cycle-safe, deterministic; result maps concept_id → `{"consequence": str, "via": str, "depth": int}`; `typer(trigger, hop, *, seed)` returns a consequence type or `None` (None = no mark AND no traversal through that hop); `initial_marks` entries enter the result with `via="seed"`, `depth=0` and expand transitively.
  - `ClosureInputs` frozen dataclass: `grounding_edges: tuple[dict[str, Any], ...]`, `evidence_dependents: dict[str, tuple[str, ...]]`, `derivation_children: dict[str, tuple[str, ...]]`.
  - `closure_inputs(vault: Path) -> ClosureInputs` — builds the three inputs from checked `concept_edges` rows (all seven relation types), the evidence-set closure (span items resolved to `catalog/sources/<work_id>` → owning claim note, the §2 claim→work join), and the latest-derived DAG inverted to children.

**Steps:**

- [x] Register the test file. In `tests/conftest.py` `TEST_LEVELS` (line 18 dict), add alphabetically:

  ```python
      "test_propagation.py": "runtime",
  ```

- [x] Write the failing tests. Create `tests/test_propagation.py`:

  ```python
  from __future__ import annotations

  from pathlib import Path

  from memoria_vault.runtime import state
  from memoria_vault.runtime.propagation import (
      HOP_DERIVED,
      HOP_EVIDENCE,
      closure_inputs,
      consequence_closure,
  )
  from memoria_vault.runtime.trusted_writer import append_explicit_journal_event


  def _all_grounds_lost(trigger: str, hop: str, *, seed: bool) -> str | None:
      return "grounds-lost"


  def _edge(source: str, relation: str, target: str) -> dict[str, str]:
      return {
          "source_concept_id": source,
          "relation_type": relation,
          "target_concept_id": target,
      }


  def test_closure_walks_supports_forward_and_extends_reverse() -> None:
      marked = consequence_closure(
          ["notes/a.md"],
          trigger="claim-retracted",
          grounding_edges=[
              _edge("notes/a.md", "supports", "notes/b.md"),
              _edge("notes/c.md", "extends", "notes/a.md"),
              _edge("notes/z.md", "supports", "notes/a.md"),
          ],
          evidence_dependents={},
          derivation_children={},
          typer=_all_grounds_lost,
      )
      assert marked == {
          "notes/b.md": {"consequence": "grounds-lost", "via": "supports", "depth": 1},
          "notes/c.md": {"consequence": "grounds-lost", "via": "extends", "depth": 1},
      }


  def test_closure_unions_evidence_and_derivation_hops_transitively() -> None:
      marked = consequence_closure(
          ["catalog/sources/w1"],
          trigger="standing-changed",
          grounding_edges=[_edge("notes/claim.md", "supports", "notes/downstream.md")],
          evidence_dependents={"catalog/sources/w1": ["notes/claim.md"]},
          derivation_children={"catalog/sources/w1": ["digests/w1.md"]},
          typer=_all_grounds_lost,
      )
      assert marked["notes/claim.md"]["via"] == HOP_EVIDENCE
      assert marked["digests/w1.md"]["via"] == HOP_DERIVED
      assert marked["notes/downstream.md"] == {
          "consequence": "grounds-lost",
          "via": "supports",
          "depth": 2,
      }


  def test_closure_is_cycle_safe_and_never_marks_start_nodes() -> None:
      marked = consequence_closure(
          ["notes/a.md"],
          trigger="claim-retracted",
          grounding_edges=[
              _edge("notes/a.md", "supports", "notes/b.md"),
              _edge("notes/b.md", "supports", "notes/a.md"),
              _edge("notes/b.md", "supports", "notes/b.md"),
          ],
          evidence_dependents={},
          derivation_children={},
          typer=_all_grounds_lost,
      )
      assert marked == {
          "notes/b.md": {"consequence": "grounds-lost", "via": "supports", "depth": 1}
      }


  def test_closure_none_consequence_stops_marking_and_traversal() -> None:
      def contradicts_is_silent(trigger: str, hop: str, *, seed: bool) -> str | None:
          return None if hop == "contradicts" else "grounds-lost"

      marked = consequence_closure(
          ["notes/a.md"],
          trigger="claim-retracted",
          grounding_edges=[
              _edge("notes/a.md", "contradicts", "notes/b.md"),
              _edge("notes/b.md", "supports", "notes/c.md"),
          ],
          evidence_dependents={},
          derivation_children={},
          typer=contradicts_is_silent,
      )
      assert marked == {}


  def test_closure_initial_marks_seed_transitive_expansion() -> None:
      marked = consequence_closure(
          (),
          trigger="edge-removed",
          grounding_edges=[_edge("notes/b.md", "supports", "notes/c.md")],
          evidence_dependents={},
          derivation_children={},
          typer=_all_grounds_lost,
          initial_marks={"notes/b.md": "grounds-lost"},
      )
      assert marked["notes/b.md"] == {
          "consequence": "grounds-lost",
          "via": "seed",
          "depth": 0,
      }
      assert marked["notes/c.md"]["depth"] == 1


  def test_closure_inputs_builds_all_three_union_sources(tmp_path: Path) -> None:
      vault = tmp_path
      state.replace_concept_edges(
          vault,
          [
              {
                  "source_concept_id": "notes/claim.md",
                  "relation_type": "supports",
                  "target_concept_id": "notes/thesis.md",
                  "check_status": "checked",
              }
          ],
      )
      state.replace_evidence_sets(
          vault,
          [
              {
                  "id": "ev-11111111",
                  "block_ref": "notes/claim.md#^blk-11111111",
                  "items": ["w1#^p0001"],
                  "type": "single-span",
                  "state": "complete",
                  "review_required": False,
                  "block_text_sha256": "0" * 64,
              }
          ],
      )
      append_explicit_journal_event(
          vault,
          {
              "event": "derived",
              "output_id": "digests/w1.md",
              "output_sha256": "0" * 64,
              "inputs": [{"id": "catalog/sources/w1"}],
          },
          actor="operation",
          machine="test-machine",
      )

      inputs = closure_inputs(vault)

      assert [
          (edge["source_concept_id"], edge["relation_type"], edge["target_concept_id"])
          for edge in inputs.grounding_edges
      ] == [("notes/claim.md", "supports", "notes/thesis.md")]
      assert inputs.evidence_dependents == {
          "catalog/sources/w1": ("notes/claim.md",)
      }
      assert inputs.derivation_children == {
          "catalog/sources/w1": ("digests/w1.md",)
      }
  ```

- [x] Run to verify failure: `python -m pytest tests/test_propagation.py -v` — expected: `ModuleNotFoundError: No module named 'memoria_vault.runtime.propagation'`.

- [x] Write the minimal implementation. Create `src/memoria_vault/runtime/propagation.py`:

  ```python
  """Typed-consequence propagation over the grounding closure and derivation DAG."""

  from __future__ import annotations

  from collections import deque
  from collections.abc import Callable, Collection, Iterable, Mapping
  from dataclasses import dataclass
  from pathlib import Path
  from typing import Any

  from memoria_vault.runtime import state
  from memoria_vault.runtime.evidence import evidence_ref_kind, parse_source_span_ref
  from memoria_vault.runtime.policy.paths import normalize_path
  from memoria_vault.runtime.trusted_writer import (
      EVENT_DERIVED,
      EVENT_OBSERVED_EXTERNAL_EDIT,
  )

  CONSEQUENCE_TYPES = (
      "grounds-lost",
      "warrant-lost",
      "qualifier-regression",
      "rebuttal-strengthened",
  )
  TRIGGERS = (
      "claim-changed",
      "claim-retracted",
      "edge-added",
      "edge-removed",
      "standing-changed",
      "decided-wrong",
  )
  HOP_EVIDENCE = "evidence"
  HOP_DERIVED = "derived"


  @dataclass(frozen=True)
  class ClosureInputs:
      grounding_edges: tuple[dict[str, Any], ...]
      evidence_dependents: dict[str, tuple[str, ...]]
      derivation_children: dict[str, tuple[str, ...]]


  def consequence_closure(
      start_ids: Collection[str],
      *,
      trigger: str,
      grounding_edges: Iterable[Mapping[str, Any]],
      evidence_dependents: Mapping[str, Collection[str]],
      derivation_children: Mapping[str, Collection[str]],
      typer: Callable[..., str | None],
      initial_marks: Mapping[str, str] | None = None,
  ) -> dict[str, dict[str, Any]]:
      """Walk grounding closure ∪ derivation DAG from fallen nodes to dependents.

      ``extends`` dependency runs source→target (the extender depends on its
      base), every other relation target→source; ``typer(trigger, hop, seed=...)``
      returning None means no mark and no traversal through that hop.
      """
      if trigger not in TRIGGERS:
          raise ValueError(f"unknown propagation trigger: {trigger!r}")
      forward: dict[str, list[tuple[str, str]]] = {}
      for row in grounding_edges:
          source = normalize_path(str(row["source_concept_id"]))
          relation = str(row["relation_type"])
          target = normalize_path(str(row["target_concept_id"]))
          if source == target:
              continue
          if relation == "extends":
              forward.setdefault(target, []).append((relation, source))
          else:
              forward.setdefault(source, []).append((relation, target))

      starts = {normalize_path(str(node)) for node in start_ids}
      marked: dict[str, dict[str, Any]] = {}
      queue: deque[tuple[str, int]] = deque((node, 0) for node in sorted(starts))
      for node, consequence in sorted((initial_marks or {}).items()):
          rel = normalize_path(node)
          marked[rel] = {"consequence": consequence, "via": "seed", "depth": 0}
          queue.append((rel, 0))
      expanded: set[str] = set()
      while queue:
          current, depth = queue.popleft()
          if current in expanded:
              continue
          expanded.add(current)
          hops = list(forward.get(current, []))
          hops.extend(
              (HOP_EVIDENCE, normalize_path(str(dep)))
              for dep in evidence_dependents.get(current, ())
          )
          hops.extend(
              (HOP_DERIVED, normalize_path(str(dep)))
              for dep in derivation_children.get(current, ())
          )
          seed = depth == 0 and current not in marked
          for hop, dependent in sorted(hops, key=lambda pair: (pair[1], pair[0])):
              if dependent in marked or dependent in starts:
                  continue
              consequence = typer(trigger, hop, seed=seed)
              if consequence is None:
                  continue
              marked[dependent] = {
                  "consequence": consequence,
                  "via": hop,
                  "depth": depth + 1,
              }
              queue.append((dependent, depth + 1))
      return marked


  def closure_inputs(vault: Path) -> ClosureInputs:
      """Assemble the union traversal's inputs from the substrate."""
      vault = Path(vault)
      edges = tuple(dict(row) for row in state.concept_edges(vault, checked_only=True))

      rows_by_id = {str(row["id"]): row for row in state.evidence_sets(vault)}
      evidence_dependents: dict[str, set[str]] = {}
      for evidence_id, row in rows_by_id.items():
          claim_rel = normalize_path(str(row["block_ref"]).split("#", 1)[0])
          if not claim_rel:
              continue
          for item, _path in state.evidence_item_closure(rows_by_id, evidence_id):
              try:
                  kind = evidence_ref_kind(str(item))
              except ValueError:
                  continue
              if kind != "source-span":
                  continue
              work_ref = f"catalog/sources/{parse_source_span_ref(str(item)).work_id}"
              evidence_dependents.setdefault(work_ref, set()).add(claim_rel)

      latest: dict[str, dict[str, Any]] = {}
      for event in state.read_event_log(
          vault, event_types=(EVENT_DERIVED, EVENT_OBSERVED_EXTERNAL_EDIT)
      ):
          output_id = event.get("output_id")
          if isinstance(output_id, str):
              latest[normalize_path(output_id)] = event
      derivation_children: dict[str, set[str]] = {}
      for output_id, event in latest.items():
          for row in event.get("inputs") or []:
              input_id = row.get("id") if isinstance(row, dict) else None
              if isinstance(input_id, str):
                  derivation_children.setdefault(normalize_path(input_id), set()).add(
                      output_id
                  )

      return ClosureInputs(
          grounding_edges=edges,
          evidence_dependents={
              key: tuple(sorted(values))
              for key, values in sorted(evidence_dependents.items())
          },
          derivation_children={
              key: tuple(sorted(values))
              for key, values in sorted(derivation_children.items())
          },
      )
  ```

- [x] Run to verify pass: `python -m pytest tests/test_propagation.py -v`.
- [x] Run the gate: `python scripts/verify`.
- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/propagation.py tests/test_propagation.py tests/conftest.py
  git commit -m "feat(propagation): pure consequence-closure walk over grounding closure ∪ derivation DAG

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task ERP-C.2: Consequence typing rules — the trigger × hop decision table

> **Landing amendment (2026-08-01, ERP-C.2 as built).** The decision table is the
> printed one, cell for cell, and every cell is pinned. Three deviations, each
> because the printed line could not fail a test:
>
> 1. **`HOP_KINDS` is derived, not a second literal:**
>    `HOP_KINDS = tuple(_TRANSITIVE_CONSEQUENCE)`. Two literals can drift into a
>    roster the table cannot answer for (`unknown hop kind` mid-walk) or a table
>    row nothing reaches, and holding them in parity needs a test that reaches into
>    a private symbol. Deriving deletes the failure instead of checking for it
>    (AGENTS.md: deletion > mechanism > rule > checker). The published order is
>    therefore the table's declaration order — `supports, extends, warrant,
>    qualifier, rebuttal, contradicts, tension, evidence, derived` — not the
>    printed one; nothing consumes the order, and the test pins it as a literal.
> 2. **`test_hop_kinds_cover_the_edge_roster` used `⊆`, which is lossy.** A
>    `HOP_KINDS` truncated to just the seven verbs satisfies
>    `set(EDGE_RELATIONS) <= set(HOP_KINDS)` and survives. Replaced by set
>    equality against `EDGE_RELATIONS | {HOP_EVIDENCE, HOP_DERIVED}` plus a
>    duplicate check, which is what an eighth relation verb fails against.
> 3. **The dispatch keeps `hop in overrides`, never `overrides.get(hop) or …`.**
>    Every `edge-added` override is `None`, so the falsy-`or` form silently falls
>    through to the transitive answer and reports `grounds-lost` for an edge that
>    was *gained*. Written as `overrides = _SEED_OVERRIDES.get(trigger, {}) if seed
>    else {}` then `overrides[hop] if hop in overrides else _TRANSITIVE_CONSEQUENCE[hop]`.
>
> Four tests the printed body did not have, each named for the escape it closes:
> `test_the_decision_table_is_total_and_answers_only_rostered_consequences` (the
> whole TRIGGERS × HOP_KINDS × seed cartesian, with exact set equality both ways),
> `test_adding_an_edge_can_only_ever_strengthen_a_rebuttal` (the `edge-added` row
> read across the whole roster, so a verb missing from `_SEED_OVERRIDES` fails),
> `test_rebuttal_strengthened_is_reachable_only_as_a_seed`, and
> `test_hop_consequence_is_the_closure_typer_for_a_real_vault_walk` (the table
> wired into `consequence_closure` over `closure_inputs`, at seed and transitive
> depth). The printed `edge-removed` block was itself a lossy projection of its
> table row — it omitted the `evidence`/`derived` cells, and dropping the whole
> `edge-removed` override survived until those two assertions were added.
>
> The `Commit` step is left unticked: C.2 and C.3 were built together and the
> session was directed to leave both uncommitted.

**Files:**
- Modify: `src/memoria_vault/runtime/propagation.py` (created in C.1 — add table below `HOP_DERIVED`)
- Modify: `tests/test_propagation.py` (append)

**Interfaces:**
- Consumes: `edges.EDGE_RELATIONS` (ERP-A, `src/memoria_vault/runtime/subsystems/lib/edges.py` — the seven-relation roster) for the parity test only.
- Produces:
  - `HOP_KINDS: tuple[str, ...]` — the seven relations + `evidence` + `derived`.
  - `hop_consequence(trigger: str, hop: str, *, seed: bool) -> str | None` — the decision table; becomes `consequence_closure`'s documented standard `typer`.

  The table, encoding the spec's parentheticals (§5):

  | hop \ context | seed: falling trigger (`claim-retracted`, `standing-changed`, `decided-wrong`) | seed: `claim-changed` | seed: `edge-added` | seed: `edge-removed` | transitive (any trigger) |
  |---|---|---|---|---|---|
  | `supports` | grounds-lost ("a supporting source or note fell") | grounds-lost | None (grounds gained) | grounds-lost | grounds-lost |
  | `extends` (reverse) | grounds-lost | grounds-lost | None | grounds-lost | grounds-lost |
  | `warrant` | warrant-lost ("the licensing note fell") | warrant-lost | None | warrant-lost | warrant-lost |
  | `qualifier` | qualifier-regression ("a bounding note changed") | qualifier-regression | None | qualifier-regression | qualifier-regression |
  | `rebuttal` | None (a fallen exception note does not strengthen the rebuttal) | rebuttal-strengthened ("an exception note strengthened") | rebuttal-strengthened | None | None |
  | `contradicts` / `tension` | None (SPEC GAP ruling above) | None | None | None | None |
  | `evidence` / `derived` | grounds-lost | grounds-lost | n/a (never a seed hop) | n/a | grounds-lost |

**Steps:**

- [x] Write the failing tests. Append to `tests/test_propagation.py`:

  ```python
  def test_hop_consequence_encodes_spec_parentheticals() -> None:
      from memoria_vault.runtime.propagation import hop_consequence

      falling = ("claim-retracted", "standing-changed", "decided-wrong")
      for trigger in falling:
          assert hop_consequence(trigger, "supports", seed=True) == "grounds-lost"
          assert hop_consequence(trigger, "extends", seed=True) == "grounds-lost"
          assert hop_consequence(trigger, "warrant", seed=True) == "warrant-lost"
          assert (
              hop_consequence(trigger, "qualifier", seed=True)
              == "qualifier-regression"
          )
          assert hop_consequence(trigger, "rebuttal", seed=True) is None
          assert hop_consequence(trigger, "contradicts", seed=True) is None
          assert hop_consequence(trigger, "tension", seed=True) is None
      assert (
          hop_consequence("claim-changed", "rebuttal", seed=True)
          == "rebuttal-strengthened"
      )
      assert (
          hop_consequence("edge-added", "rebuttal", seed=True)
          == "rebuttal-strengthened"
      )
      assert hop_consequence("edge-added", "supports", seed=True) is None
      assert hop_consequence("edge-removed", "supports", seed=True) == "grounds-lost"
      assert hop_consequence("edge-removed", "warrant", seed=True) == "warrant-lost"
      assert hop_consequence("edge-removed", "rebuttal", seed=True) is None
      # Transitive hops are uniform falling semantics for every trigger.
      for trigger in ("claim-changed", "edge-added", "edge-removed", *falling):
          assert hop_consequence(trigger, "supports", seed=False) == "grounds-lost"
          assert hop_consequence(trigger, "warrant", seed=False) == "warrant-lost"
          assert hop_consequence(trigger, "evidence", seed=False) == "grounds-lost"
          assert hop_consequence(trigger, "derived", seed=False) == "grounds-lost"
          assert hop_consequence(trigger, "rebuttal", seed=False) is None


  def test_hop_consequence_rejects_unknown_trigger_and_hop() -> None:
      import pytest

      from memoria_vault.runtime.propagation import hop_consequence

      with pytest.raises(ValueError, match="unknown propagation trigger"):
          hop_consequence("made-up", "supports", seed=True)
      with pytest.raises(ValueError, match="unknown hop kind"):
          hop_consequence("claim-changed", "made-up", seed=True)


  def test_hop_kinds_cover_the_edge_roster() -> None:
      from memoria_vault.runtime.propagation import HOP_KINDS
      from memoria_vault.runtime.subsystems.lib.edges import EDGE_RELATIONS

      assert set(EDGE_RELATIONS) <= set(HOP_KINDS)
  ```

- [x] Run to verify failure: `python -m pytest tests/test_propagation.py::test_hop_consequence_encodes_spec_parentheticals -v` — expected: `ImportError: cannot import name 'hop_consequence'`.

- [x] Write the minimal implementation. In `src/memoria_vault/runtime/propagation.py`, below `HOP_DERIVED`:

  ```python
  HOP_KINDS = (
      "supports",
      "contradicts",
      "extends",
      "tension",
      "warrant",
      "qualifier",
      "rebuttal",
      HOP_EVIDENCE,
      HOP_DERIVED,
  )
  _TRANSITIVE_CONSEQUENCE: dict[str, str | None] = {
      "supports": "grounds-lost",
      "extends": "grounds-lost",
      "warrant": "warrant-lost",
      "qualifier": "qualifier-regression",
      "rebuttal": None,
      "contradicts": None,
      "tension": None,
      HOP_EVIDENCE: "grounds-lost",
      HOP_DERIVED: "grounds-lost",
  }
  _SEED_OVERRIDES: dict[str, dict[str, str | None]] = {
      "claim-changed": {"rebuttal": "rebuttal-strengthened"},
      "edge-added": {
          "supports": None,
          "extends": None,
          "warrant": None,
          "qualifier": None,
          "rebuttal": "rebuttal-strengthened",
          HOP_EVIDENCE: None,
          HOP_DERIVED: None,
      },
      "edge-removed": {HOP_EVIDENCE: None, HOP_DERIVED: None},
  }


  def hop_consequence(trigger: str, hop: str, *, seed: bool) -> str | None:
      """EDGES §5 decision table: which trigger+hop yields which consequence."""
      if trigger not in TRIGGERS:
          raise ValueError(f"unknown propagation trigger: {trigger!r}")
      if hop not in _TRANSITIVE_CONSEQUENCE:
          raise ValueError(f"unknown hop kind: {hop!r}")
      if seed and trigger in _SEED_OVERRIDES and hop in _SEED_OVERRIDES[trigger]:
          return _SEED_OVERRIDES[trigger][hop]
      return _TRANSITIVE_CONSEQUENCE[hop]
  ```

- [x] Run to verify pass: `python -m pytest tests/test_propagation.py -v`.
- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/propagation.py tests/test_propagation.py
  git commit -m "feat(propagation): trigger×hop consequence decision table per EDGES §5

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task ERP-C.3: Schema v18 direct DDL — `consequence` column on `concept_verdicts` + DB mirror helpers

> **Schema-rung amendment (2026-08-01, BINDING).** `18` here is **positional, not
> allocated**: it is "the next free rung", and it reads 18 only for as long as
> `SCHEMA_VERSION` on `main` is 17. The I1 plan's Task T.1 (`telemetry_events`) previously
> gated on `SCHEMA_VERSION == 18`, which pinned this task ahead of the whole telemetry
> tree for bookkeeping rather than dependency; that gate is now "current + 1" (I1 plan
> T.1, 2026-08-01), so I1 T.1 may claim 18 and this task 19. Neither task reads the
> other's storage, so either order is correct. **Before executing:** read
> `SCHEMA_VERSION`, take `current + 1`, and substitute it for every `18` in this task —
> the Files list, Produces, the DDL, the `PRAGMA user_version`, the renamed test
> functions and the three pinned assertions. Do **not** stop because the current value is
> not 17; stop only if a `MIGRATIONS` symbol has appeared, which would mean the
> fresh-schema rule above no longer holds.

> **Landing amendment (2026-08-01, ERP-C.3 as built).**
>
> 1. **The rung taken is 19.** `SCHEMA_VERSION` on `main` read 18 (I1 T.1's
>    `telemetry_events`), so `current + 1 = 19` per the binding amendment above.
>    No `MIGRATIONS` symbol exists —
>    `tests/test_schema_version.py::test_state_has_no_schema_migration_ladder`
>    asserts its absence — so the printed step 2 (`MIGRATIONS` entry), the printed
>    `test_v17_to_v18_adds_consequence_column`, and the printed "verify failure"
>    expectation (`unsupported Memoria DB schema version: 17`) are historical and
>    were not executed. The fresh schema is asserted instead, as the task's own
>    Execution replacement directs.
> 2. **The printed C.3 tests cannot run against the shipped schema, and the
>    printed negative case would have passed for the wrong reason.** Since v16
>    (NID-B) `concept_verdicts.concept_id` carries
>    `REFERENCES concepts(concept_id)`, and `state.connect` sets
>    `PRAGMA foreign_keys = ON`. Every printed fixture inserts a verdict for a
>    Concept with no `concepts` row: the positive inserts raise
>    `IntegrityError: FOREIGN KEY constraint failed`, and the printed
>    `pytest.raises(sqlite3.IntegrityError)` around the `'made-up'` value would
>    have been satisfied by that same FK rather than by the new CHECK. As built,
>    every fixture seeds its Concept parent (`state.rebuild_file_concept_mirror`,
>    `state.upsert_catalog_record`) and the negative case matches on
>    `"CHECK constraint failed"`.
> 3. **The mirror keys identity space, not path space.** The printed helper bodies
>    use `normalize_path`; as built both resolve through `resolve_concept_id`, the
>    way `set_concept_verdict` and `set_concept_flag` already do. `normalize_path`
>    returns a ULID and a bare `work_id` unchanged, so the printed body would fail
>    the FK for every ULID-identified file Concept and every catalog work reached
>    by its `catalog/sources/…` rendering — which is exactly what the propagation
>    walk hands it, since C.1 marks in path space.
> 4. **`set_concept_consequence` refuses a parentless Concept descriptively**, via
>    `_concept_missing_parent`, as `set_concept_flag` does. C.1 proved the walk
>    reaches unwritten notes (`test_the_walk_reaches_a_pending_target_that_owns_no_
>    concept_row`), so C.4 will meet this refusal and needs it to name the Concept.
> 5. **Parity is read out of `sqlite_master`, not shared between two literals.**
>    `tests/test_runtime_state.py::test_consequence_check_mirrors_the_propagation_roster`
>    parses the live `consequence IN (…)` CHECK back out of the stored DDL and
>    compares it to the imported `CONSEQUENCE_TYPES`, asserting `''` is in the
>    column's roster and out of the propagation one. The literal that pins what
>    the members actually *are* stays in
>    `tests/test_propagation.py::test_the_consequence_roster_is_the_four_spec_types`,
>    in a second file, because a parity test alone survives a rename applied to
>    both sides at once.
> 6. **A fourth pinned assertion exists that the Files list does not name:**
>    `tests/test_query_substrate.py` carries a literal `PRAGMA user_version`
>    assertion in `test_concept_edges_fresh_schema_exposes_reader_fields` as well
>    as the `state.SCHEMA_VERSION` one. `tests/test_schema_v10.py` needed no edit —
>    it now compares to `state.SCHEMA_VERSION` and is a consistency check, not a
>    pin. Literal pins therefore live in two files (`test_schema_version.py`,
>    `test_query_substrate.py`), which is what kills a mutant drifting the DDL and
>    the constant together.
> 7. **Goldens did not move.** `tests/floor_lib.py`'s `_DIGEST_TABLES` is a fixed
>    seven-table roster that does not include `concept_verdicts`, it stores
>    `COUNT(*)` rather than table shape, and the file digest skips `*.sqlite`. No
>    file under `tests/fixtures/floor/goldens/` changed.
>
> The `Commit` step is left unticked: the session was directed to leave the work
> uncommitted. The one-commit rule still binds whoever commits it — DDL, trailing
> `PRAGMA user_version`, `SCHEMA_VERSION` and the pinned assertions are one change.

**Direct DDL is needed:** the current verdict row is
`concept_verdicts(concept_id TEXT PRIMARY KEY, check_status TEXT NOT NULL CHECK(...))`
(schema.sql:60-63) — two columns, no JSON or spare column anywhere on the
table, so the spec's "mirrored in the DB verdict row" cannot land without
DDL. `concept_flags` (schema.sql:64-71) cannot absorb it either: its `flag`
CHECK admits only `'stale'` and the spec keeps that row as *compatibility*,
not as the queryable consequence record. Add the v18 field to the current
fresh schema; do not transform an older database.

**Files:**
- Modify: `src/memoria_vault/runtime/state.py` — `SCHEMA_VERSION` (line 53, will read 17 after NID-B/ERP-A), `set_concept_verdict` checked-clear block (lines 1056-1060), and new helpers after `concept_flags` (ends line 1339); do not add a migration entry.
- Modify: `src/memoria_vault/runtime/schema.sql` — `concept_verdicts` DDL (lines 60-63) + trailing `PRAGMA user_version` (line 378, will read 17)
- Modify: `tests/test_schema_version.py` (pinned assertion at lines 14-17, function renamed by the earlier version tasks — bump to 18), `tests/test_schema_v10.py` (lines 39-41), `tests/test_query_substrate.py` (line 31)
- Modify: `tests/test_runtime_state.py` (append fresh-schema + helper tests; already registered at level `runtime`, conftest.py line 96)

**Interfaces:**
- Consumes: the fresh-schema version gate, `state.connect` / `state.db_path` (state.py:460), `_set_concept_verdict_conn` (state.py:3371), `propagation.CONSEQUENCE_TYPES` (C.1) for the parity test.
- Produces:
  - Schema v18: `concept_verdicts.consequence TEXT NOT NULL DEFAULT '' CHECK (consequence IN ('', 'grounds-lost', 'warrant-lost', 'qualifier-regression', 'rebuttal-strengthened'))`.
  - `state.set_concept_consequence(vault: Path, concept_id: str, consequence: str) -> None` — upserts the verdict row's consequence, preserving an existing `check_status` (inserts as `'unchecked'` when no row exists).
  - `state.concept_consequence(vault: Path, concept_id: str) -> str` — `''` when unset/missing/no DB.
  - New contract on `state.set_concept_verdict`: setting `'checked'` clears `consequence` (alongside the existing stale-flag delete) — re-verification wipes the mark's DB mirror.

> **Execution replacement:** assert the `consequence` field from a fresh v18
> schema. All following v17 fixture and migration-entry instructions are historical
> only and must not be executed.

**Steps:**

- [x] Write the failing tests. Append to `tests/test_runtime_state.py`:

  ```python
  def test_v17_to_v18_adds_consequence_column(tmp_path: Path) -> None:
      db = tmp_path / state.DB_REL
      db.parent.mkdir(parents=True)
      with sqlite3.connect(db) as conn:
          conn.execute(
              "CREATE TABLE concept_verdicts ("
              "concept_id TEXT PRIMARY KEY, "
              "check_status TEXT NOT NULL CHECK "
              "(check_status IN ('unchecked', 'checked', 'quarantined')))"
          )
          conn.execute("INSERT INTO concept_verdicts VALUES ('notes/a.md', 'checked')")
          conn.execute("PRAGMA user_version = 17")

      with state.connect(tmp_path) as conn:
          assert conn.execute("PRAGMA user_version").fetchone()[0] == 18
          row = conn.execute(
              "SELECT check_status, consequence FROM concept_verdicts "
              "WHERE concept_id = 'notes/a.md'"
          ).fetchone()
      assert tuple(row) == ("checked", "")


  def test_consequence_check_constraint_matches_the_roster(tmp_path: Path) -> None:
      from memoria_vault.runtime.propagation import CONSEQUENCE_TYPES

      with state.connect(tmp_path) as conn:
          for value in CONSEQUENCE_TYPES:
              conn.execute(
                  "INSERT INTO concept_verdicts(concept_id, check_status, consequence)"
                  " VALUES (?, 'unchecked', ?)",
                  (f"notes/{value}.md", value),
              )
          with pytest.raises(sqlite3.IntegrityError):
              conn.execute(
                  "INSERT INTO concept_verdicts(concept_id, check_status, consequence)"
                  " VALUES ('notes/bogus.md', 'unchecked', 'made-up')"
              )


  def test_set_concept_consequence_upserts_and_recheck_clears(tmp_path: Path) -> None:
      state.set_concept_consequence(tmp_path, "notes/c.md", "grounds-lost")
      assert state.concept_consequence(tmp_path, "notes/c.md") == "grounds-lost"
      assert state.concept_check_status(tmp_path, "notes/c.md") == "unchecked"

      state.set_concept_verdict(tmp_path, "notes/c.md", "unchecked")
      assert state.concept_consequence(tmp_path, "notes/c.md") == "grounds-lost"

      state.set_concept_verdict(tmp_path, "notes/c.md", "checked")
      assert state.concept_consequence(tmp_path, "notes/c.md") == ""

      state.set_concept_verdict(tmp_path, "notes/c.md", "checked")
      state.set_concept_consequence(tmp_path, "notes/c.md", "warrant-lost")
      assert state.concept_check_status(tmp_path, "notes/c.md") == "checked"
      assert state.concept_consequence(tmp_path, "notes/c.md") == "warrant-lost"
  ```

- [x] Run to verify failure: `python -m pytest tests/test_runtime_state.py::test_v17_to_v18_adds_consequence_column -v` — expected: `RuntimeError: unsupported Memoria DB schema version: 17` (no registered 17→18 path yet).

- [x] Implement, all in one commit:
  1. `state.py` line 53: `SCHEMA_VERSION = 18`.
  2. Add to the `MIGRATIONS` dict:

     ```python
         17: (
             18,
             [
                 "ALTER TABLE concept_verdicts ADD COLUMN consequence TEXT NOT NULL"
                 " DEFAULT '' CHECK (consequence IN ('', 'grounds-lost',"
                 " 'warrant-lost', 'qualifier-regression', 'rebuttal-strengthened'))",
             ],
         ),
     ```

  3. `schema.sql` lines 60-63 become:

     ```sql
     CREATE TABLE IF NOT EXISTS concept_verdicts (
         concept_id TEXT PRIMARY KEY,
         check_status TEXT NOT NULL CHECK (check_status IN ('unchecked', 'checked', 'quarantined')),
         consequence TEXT NOT NULL DEFAULT '' CHECK (consequence IN ('', 'grounds-lost', 'warrant-lost', 'qualifier-regression', 'rebuttal-strengthened'))
     );
     ```

     and the trailing line becomes `PRAGMA user_version = 18;`.
  4. In `set_concept_verdict` (state.py:1047-1060), extend the `if status == "checked":` block with a second statement after the flag delete:

     ```python
             conn.execute(
                 "UPDATE concept_verdicts SET consequence = '' WHERE concept_id = ?",
                 (target,),
             )
     ```

  5. After `concept_flags` (line 1339), add:

     ```python
     def set_concept_consequence(vault: Path, concept_id: str, consequence: str) -> None:
         """Mirror a typed-consequence mark on the verdict row (EDGES §5 ruling A)."""
         target = normalize_path(concept_id)
         with connect(vault) as conn:
             conn.execute(
                 """
                 INSERT INTO concept_verdicts(concept_id, check_status, consequence)
                 VALUES (?, 'unchecked', ?)
                 ON CONFLICT(concept_id) DO UPDATE SET consequence = excluded.consequence
                 """,
                 (target, consequence),
             )


     def concept_consequence(vault: Path, concept_id: str) -> str:
         target = normalize_path(concept_id)
         if not db_path(vault).is_file():
             return ""
         with connect(vault) as conn:
             row = conn.execute(
                 "SELECT consequence FROM concept_verdicts WHERE concept_id = ?",
                 (target,),
             ).fetchone()
         return "" if row is None else str(row["consequence"])
     ```

  6. Bump the three pinned assertions from 17 to 18: `tests/test_schema_version.py` (assertion pair at lines 14-17, rename the test to `test_schema_lands_at_user_version_18`), `tests/test_schema_v10.py:39-41` (rename to `test_user_version_is_18`), `tests/test_query_substrate.py:31`.

- [x] Run to verify pass: `python -m pytest tests/test_runtime_state.py tests/test_schema_version.py tests/test_schema_v10.py tests/test_query_substrate.py -v`.
- [x] Run the gate: `python scripts/verify`.
- [ ] Commit (the version chain rule — MIGRATIONS entry, DDL + PRAGMA, SCHEMA_VERSION, pinned tests in ONE commit):

  ```
  git add src/memoria_vault/runtime/state.py src/memoria_vault/runtime/schema.sql \
      tests/test_runtime_state.py tests/test_schema_version.py \
      tests/test_schema_v10.py tests/test_query_substrate.py
  git commit -m "feat(state): schema v18 — consequence column on concept_verdicts + mirror helpers

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task ERP-C.4: The mark writer — `stale: true` + `consequence:` frontmatter, DB mirror, compat flag, idempotent

> **Landing amendment (2026-08-02, ERP-C.4 as built).** Four deviations from the
> printed body and tests, each because the printed line could not run or could
> not fail:
>
> 1. **Every printed fixture was parentless.** `set_concept_consequence` and
>    `set_concept_flag` are both FK-backed onto `concepts`, so
>    `mark_consequence(vault, "catalog/sources/w2", …)` on a vault with no `w2`
>    catalog row raises `_concept_missing_parent` before any rule below is
>    reached. Every fixture seeds its parent (`state.upsert_catalog_record` for
>    a work, `write_note` for a note), and `workspace()` is
>    `tests.helpers.worker_workspace` so the engine in C.5 has a commit to
>    build on.
> 2. **`mark_consequence` refuses nothing and skips the unmirrored.** C.1 proved
>    the walk legally reaches a pending edge's target, which has no `concepts`
>    row; letting the FK refusal out would abort a whole propagation run for one
>    dangling forward link. New guard: `if not state.concept_exists(vault,
>    target): return unchanged`. **New public reader
>    `state.concept_exists(vault, concept_id) -> bool`** — `resolve_concept_id`
>    answers with the normalized reference itself for an unknown Concept, so
>    nothing shipped could tell known from unknown.
> 3. **A third hash reader had to move with the file.** The printed body keeps
>    `rebuild_trace_state` current (the journal event) and the PI baseline
>    current, but not `outputs.output_sha256` — the hash
>    `read_barrier.is_consumable_checked_file` compares the file against. Without
>    it a labelled note stops being consumable as checked, every later reader
>    enqueues a scan for it, and that scan demotes it and cascades another
>    propagation; `curate_note_link` on a marked target raises outright. **New
>    narrow writer `state.refresh_output_sha256(vault, output_id, sha)`** — hash
>    only, no verdict, following `set_concept_consequence`'s "a label is not a
>    re-judgment" rule. `state.mark_checked` could not serve: it promotes to
>    `checked` and deletes the very `stale` flag this writer just wrote.
> 4. **The printed idempotence tests test one half of two conjunctions.** Both
>    the file branch (`stale is True and consequence == …`) and the DB branch
>    (`consequence == … and "stale" in flags`) now have a test per half, plus
>    the non-markdown and missing-file halves of `is_markdown`.
>
> `tests/conftest.py` registers `"test_propagation_engine.py": "runtime"`.

**Files:**
- Modify: `src/memoria_vault/runtime/propagation.py` (add `mark_consequence` + `_target_aliases`)
- Create: `tests/test_propagation_engine.py`
- Modify: `tests/conftest.py` (`TEST_LEVELS` — register at `runtime`)

**Interfaces:**
- Consumes: `write_frontmatter_doc` / `split_frontmatter` / `read_frontmatter` (vaultio.py:160/:70/:66), `sha256_file` / `EMPTY_SHA256` (policy/audit.py), `state.set_concept_consequence` + `state.concept_consequence` (C.3), `state.set_concept_flag` (state.py:1293-1315, the shipped compat row) / `state.concept_flags` (state.py:1318), `state.file_baseline` / `state.upsert_file_baseline` (baseline-refresh idiom mirrors trusted_writer.py:596-604), `EVENT_CHECK_FIRED` (trusted_writer.py:44; the event shape mirrors `integrity._flag_descendant`, integrity.py:1194-1222, so `rebuild_trace_state` — trusted_writer.py:837-853 — keeps `_known_current_hashes` current and the next scan does not read the mark as a foreign edit), `state.catalog_source` (state.py:1603) for `_target_aliases` (12 lines mirroring `integrity._trace_aliases`, integrity.py:1368-1379 — duplicated deliberately: importing integrity from propagation would create an import cycle once integrity imports propagation in C.5). The frontmatter fields' yaml registration is NID's closed-validation task (NODES §3) — this writer never validates against the contract, it labels.
- Produces: `propagation.mark_consequence(vault: Path, concept_id: str, *, consequence: str, trigger_id: str, reason: str, append_event: Callable[[dict[str, Any]], Any]) -> dict[str, Any]` — returns `{"concept_id": str, "consequence": str, "changed": bool, "path": str}` (`path` = the rel to commit, empty for DB-only targets or no-op re-marks). File targets get frontmatter `stale: True` + `consequence: <type>`; every target gets the v18 verdict mirror + the `concept_flags` stale compat row + one `typed-consequence` journal event; re-marking with the identical consequence is a full no-op (no write, no event). `propagation._target_aliases(vault: Path, target: str) -> set[str]`.

**Steps:**

- [x] Register the test file in `tests/conftest.py` `TEST_LEVELS`: `"test_propagation_engine.py": "runtime",`.
- [x] Write the failing tests. Create `tests/test_propagation_engine.py`:

  ```python
  from __future__ import annotations

  from pathlib import Path

  from memoria_vault.runtime import state
  from memoria_vault.runtime.policy.audit import sha256_file
  from memoria_vault.runtime.propagation import mark_consequence
  from memoria_vault.runtime.vaultio import read_frontmatter
  from tests.helpers import copy_memoria_dirs, init_git, write_note


  def workspace(tmp_path: Path) -> Path:
      copy_memoria_dirs(tmp_path, "schemas", "config")
      init_git(tmp_path, "propagation@example.invalid", "Propagation")
      return tmp_path


  def test_mark_consequence_labels_file_and_mirrors_db(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      write_note(vault, "claim", "checked", "A claim body.")
      events: list[dict] = []

      result = mark_consequence(
          vault,
          "notes/claim.md",
          consequence="grounds-lost",
          trigger_id="catalog/sources/w1",
          reason="work w1 retracted",
          append_event=events.append,
      )

      frontmatter = read_frontmatter(vault / "notes/claim.md")
      assert frontmatter["stale"] is True
      assert frontmatter["consequence"] == "grounds-lost"
      assert state.concept_consequence(vault, "notes/claim.md") == "grounds-lost"
      flags = state.concept_flags(vault, "notes/claim.md")
      assert flags["stale"]["trigger_id"] == "catalog/sources/w1"
      assert result == {
          "concept_id": "notes/claim.md",
          "consequence": "grounds-lost",
          "changed": True,
          "path": "notes/claim.md",
      }
      [event] = events
      assert event["check"] == "typed-consequence"
      assert event["consequence"] == "grounds-lost"
      assert event["route"] == "log"
      assert event["output_sha256"] == sha256_file(vault / "notes/claim.md")


  def test_mark_consequence_re_marking_is_idempotent(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      write_note(vault, "claim", "checked", "A claim body.")
      events: list[dict] = []
      mark_consequence(
          vault,
          "notes/claim.md",
          consequence="grounds-lost",
          trigger_id="catalog/sources/w1",
          reason="work w1 retracted",
          append_event=events.append,
      )
      before = sha256_file(vault / "notes/claim.md")

      again = mark_consequence(
          vault,
          "notes/claim.md",
          consequence="grounds-lost",
          trigger_id="catalog/sources/w1",
          reason="work w1 retracted",
          append_event=events.append,
      )

      assert again["changed"] is False and again["path"] == ""
      assert len(events) == 1
      assert sha256_file(vault / "notes/claim.md") == before


  def test_mark_consequence_db_only_for_virtual_targets(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      events: list[dict] = []

      result = mark_consequence(
          vault,
          "catalog/sources/w2",
          consequence="grounds-lost",
          trigger_id="catalog/sources/w1",
          reason="work w1 retracted",
          append_event=events.append,
      )

      assert result["changed"] is True and result["path"] == ""
      assert state.concept_consequence(vault, "catalog/sources/w2") == "grounds-lost"
      assert "stale" in state.concept_flags(vault, "catalog/sources/w2")


  def test_mark_consequence_refreshes_pi_file_baseline(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      write_note(vault, "claim", "checked", "A claim body.")
      state.upsert_file_baseline(
          vault,
          "notes/claim.md",
          human_sha256=sha256_file(vault / "notes/claim.md"),
          restriction_keys=["quote"],
      )

      mark_consequence(
          vault,
          "notes/claim.md",
          consequence="qualifier-regression",
          trigger_id="notes/bound.md",
          reason="bounding note changed",
          append_event=lambda event: event,
      )

      baseline = state.file_baseline(vault, "notes/claim.md")
      assert baseline["human_sha256"] == sha256_file(vault / "notes/claim.md")
      assert baseline["restriction_keys"] == ["quote"]
  ```

- [x] Run to verify failure: `python -m pytest tests/test_propagation_engine.py -v` — expected: `ImportError: cannot import name 'mark_consequence'`.

- [x] Write the minimal implementation. In `src/memoria_vault/runtime/propagation.py`, extend the imports:

  ```python
  from memoria_vault.runtime.policy.audit import EMPTY_SHA256, sha256_file
  from memoria_vault.runtime.vaultio import split_frontmatter, write_frontmatter_doc
  ```

  and add:

  ```python
  def _target_aliases(vault: Path, target: str) -> set[str]:
      # Mirrors integrity._trace_aliases; duplicated to avoid an import cycle.
      aliases = {target}
      row = state.catalog_source(vault, target)
      if row is None:
          return aliases
      work_id = str(row.get("work_id") or "").strip()
      concept_path = str(row.get("concept_path") or "").strip()
      if work_id:
          aliases.add(f"catalog/sources/{work_id}")
      if concept_path:
          aliases.add(normalize_path(concept_path))
      return aliases


  def mark_consequence(
      vault: Path,
      concept_id: str,
      *,
      consequence: str,
      trigger_id: str,
      reason: str,
      append_event: Callable[[dict[str, Any]], Any],
  ) -> dict[str, Any]:
      """Apply one typed-consequence mark: label, verdict mirror, compat flag."""
      if consequence not in CONSEQUENCE_TYPES:
          raise ValueError(f"unknown consequence type: {consequence!r}")
      vault = Path(vault)
      target = normalize_path(concept_id)
      trigger = normalize_path(trigger_id)
      path = vault / target
      is_markdown = target.endswith(".md") and path.is_file()
      unchanged = {
          "concept_id": target,
          "consequence": consequence,
          "changed": False,
          "path": "",
      }
      if is_markdown:
          frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
          if (
              frontmatter.get("stale") is True
              and frontmatter.get("consequence") == consequence
          ):
              return unchanged
          frontmatter["stale"] = True
          frontmatter["consequence"] = consequence
          write_frontmatter_doc(path, frontmatter, body)
      elif (
          state.concept_consequence(vault, target) == consequence
          and "stale" in state.concept_flags(vault, target)
      ):
          return unchanged
      state.set_concept_consequence(vault, target, consequence)
      state.set_concept_flag(vault, target, "stale", reason=reason, trigger_id=trigger)
      target_sha = sha256_file(path) if path.is_file() else EMPTY_SHA256
      append_event(
          {
              "event": EVENT_CHECK_FIRED,
              "check": "typed-consequence",
              "status": "failed",
              "reason": reason,
              "consequence": consequence,
              "target_id": target,
              "target_sha256": target_sha,
              "output_sha256": target_sha,
              "trigger_id": trigger,
              "shadow": False,
              "route": "log",
          }
      )
      if is_markdown:
          baseline = state.file_baseline(vault, target)
          if baseline is not None:
              state.upsert_file_baseline(
                  vault,
                  target,
                  human_sha256=target_sha,
                  restriction_keys=list(baseline["restriction_keys"]),
              )
      return {
          "concept_id": target,
          "consequence": consequence,
          "changed": True,
          "path": target if is_markdown else "",
      }
  ```

  and extend the trusted_writer import at the top with `EVENT_CHECK_FIRED`.
  Frontmatter label *clearing* is deliberately not implemented here: re-verification
  is lazy (spec §5 last bullet) — `state.set_concept_verdict(..., "checked")` clears
  the DB mirror (C.3) and the PI removing the two fields is an observed PI edit.

- [x] Run to verify pass: `python -m pytest tests/test_propagation_engine.py -v`.
- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/propagation.py tests/test_propagation_engine.py tests/conftest.py
  git commit -m "feat(propagation): consequence mark writer — frontmatter labels + v18 mirror + compat flag

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task ERP-C.6: Loudness routing — attention card only when the active project's slice is touched (executes BEFORE C.5)

> **Execution note (2026-08-02): C.5 landed first, so this task now has a third
> deliverable.** `propagation._propagate` holds the routing seat with a literal
> `cards: list[str] = []`; replacing that line with `route_consequence_cards(
> vault, consequences, trigger_id=target, reason=reason)` is what turns the
> engine's quiet tier back on. `tests/test_propagation_engine.py` already carries
> the workspace and `_work` helpers this task's fixtures need, and its
> `test_retraction_sweep_labels_every_reached_claim_and_commits_them` asserts
> `result["cards"] == []` — that assertion is this task's to flip, and it is the
> one place the deferral is visible from outside.

> **Landing amendment (2026-08-02, ERP-C.6 as built).**
>
> 1. **The printed `active_project_slices` carried two Criticals, both of the
>    namespace-conflation class, and neither is in the code that landed.** The
>    snippet builds its adjacency from `state.concept_edges` and normalizes
>    `source_concept_id` / `target_concept_id`. Those columns are **identity
>    space**: a file Concept that authored a ULID is keyed by that ULID, so
>    `normalize_path` returns the ULID and the member never joins the
>    path-space `marked` map the router intersects — the slice silently loses
>    it. And an unresolved target is SQL `NULL`, so `str(row[...])` is the
>    literal `"None"`, which every pending edge in the vault shares: one blank
>    hub fusing unrelated projects into each other's slices. Measured on the
>    landed fixture, the printed version returns
>    `{'projects/thesis-a.md': {'notes/thesis.md', '01JXAAA…1', 'None',
>    'notes/thesis-b.md', …}}` for *both* projects. The landed version consumes
>    `edges.concept_edge_path_pairs(vault, checked_only=False)` — cross-section
>    contract 3's strict projection, which is what that contract already told
>    this task to use.
> 2. **`thesis:` is normalized by `edges.thesis_rel`, not by hand.** The
>    snippet's `thesis if thesis.endswith(".md") else f"{thesis}.md"` is a
>    fourth copy of the rule issue #1623 collapsed into one function: it admits
>    a *title* (alias space) as `notes/Toulmin: the warrant.md`, a node no graph
>    contains, and skips the `CONCEPT_ROOTS` check. Pinned by
>    `test_a_thesis_that_is_not_path_space_seeds_nothing`.
> 3. **The slice is unchecked-inclusive, and that is now pinned.**
>    `checked_only=False`: a project's slice is its topology, not its verified
>    topology — an unconfirmed edge still says where a cascade would land, and
>    loudness asks where the blast is, not whether the graph is settled. The
>    fixture's second edge row is `check_status="unchecked"` for exactly this.
> 4. **The C.5 assertion was not flipped, because flipping it would have made
>    it false.** `test_retraction_sweep_labels_every_reached_claim_and_commits_them`
>    seeds no project, so `active_project_slices` is `{}` and `cards == []` is
>    now the *quiet-tier* assertion (marks outside every active slice route
>    nothing), not a deferral marker. Its comment says so. The alert tier is
>    carried by a new engine test,
>    `test_a_sweep_that_reaches_an_active_project_commits_its_alert_card`, which
>    also pins that the card rides the same trusted-writer commit as the labels
>    and that a settled re-run commits nothing.
> 5. **The printed fixtures do not run.** `_seed_active_project`'s
>    `replace_concept_edges` rows use `target_concept_id` and carry no
>    `source_path`; the landed shape is C.5's own `_edge_row`. The landed
>    fixture is also deliberately non-degenerate in three ways the printed one
>    was not: a ULID-keyed source, an unresolved target, and a second project
>    at the nested `projects/<slug>/project.md` home whose sort order and walk
>    order disagree (which is what makes the router's per-project ordering
>    observable at all).
> 6. **Handover consequence — `graph_sql.project_slice` and
>    `explore._vetted_project_slice_ids` switch providers the moment this task
>    lands, and 7 R2 tests fail on it.** Both duck-type
>    `getattr(propagation, "active_project_slices", None)` and prefer it over
>    their `links:`-frontmatter fallback, exactly as cross-section contract 4
>    ("the sole project-slice provider once ERP-C.6 lands") intends. The
>    failures are all one root cause: the R2 fixtures are hand-written
>    frontmatter that was never reindexed, so the edge mirror the new provider
>    reads is empty, and the slice now also contains the project file itself.
>    **This task did not converge them** — see the obligation written into R2
>    task G's section in `2026-07-17-r2-retrieval-modes.md`, which is where the
>    two rulings it needs belong (whether the project file is a slice member for
>    retrieval, and whether `explore`'s vetted-frontmatter traversal may be
>    replaced by a `checked_only=False` mirror read).
> 7. **Mutation:** 33 mutants over both new functions, the `_propagate` routing
>    line and ERP-D.1's helper; 33 killed, 0 survivors. Three survivors on the
>    first run were all real gaps and all fixed by strengthening assertions, not
>    by justification: an unasserted honesty sentence, an untyped evidence line,
>    and an unobservable project ordering.

**Files:**
- Modify: `src/memoria_vault/runtime/propagation.py` (add `active_project_slices` + `route_consequence_cards`)
- Modify: `tests/test_propagation_engine.py` (append)

**Interfaces:**
- Consumes: `inbox.write_finding(vault, card_type, title, finding, raised_by, agent_recommendation="issues-found", target="", citekey="", loudness="alert", evidence="", dedupe_slug="") -> Path | None` (inbox.py:75, post-Plan-21 — `dedupe_slug` makes the filename stable and returns None when the card already exists; `alert` renders as the top non-block band — Plan 21.5 removes the push tier, so no push routing applies; recorded amendment per `2026-07-16-i1-full-wiring-design.md` §3), `iter_markdown` / `read_frontmatter` (vaultio.py), `state.concept_edges(vault, checked_only=False)`, `inbox._slug`-compatible slugging is inbox's job (dedupe_slug is slugged internally).
- Produces:
  - `propagation.active_project_slices(vault: Path) -> dict[str, set[str]]` — the deterministic rule: one entry per `type: project` markdown file whose frontmatter `archived` is not `True`; the slice = {project rel} ∪ {normalized `thesis` target rel, if any} ∪ every concept reachable undirected over all `concept_edges` rows from those seeds.
  - `propagation.route_consequence_cards(vault: Path, marked: Mapping[str, str], *, trigger_id: str, reason: str) -> list[str]` — the loudness tier rule: marks intersecting an active project's slice ⇒ exactly ONE `flag` card per (trigger, project) at `loudness="alert"` (`dedupe_slug=f"consequence-{trigger_id}-{project_rel}"` — idempotent across re-runs), card `target` = the project rel, finding = per-consequence-type counts; marks outside every active slice ⇒ NO card (labels + journal only — quiet tier). This engine never emits `block` (reserved; flood mechanics beyond routing are O2's, spec §9). Returns vault-relative card paths for the caller's commit.

**Steps:**

- [x] Write the failing tests. Append to `tests/test_propagation_engine.py` (extend the import block with `from memoria_vault.runtime.propagation import active_project_slices, route_consequence_cards`):

  ```python
  def _seed_active_project(vault: Path) -> None:
      project = vault / "projects/thesis-a.md"
      project.parent.mkdir(parents=True, exist_ok=True)
      project.write_text(
          "---\ntype: project\ntitle: Thesis A\ntags: []\nlinks: {}\n"
          "thesis: notes/thesis.md\n---\nBody.\n",
          encoding="utf-8",
      )
      write_note(vault, "thesis", "checked", "Thesis body.")
      state.replace_concept_edges(
          vault,
          [
              {
                  "source_concept_id": f"notes/n{i}.md",
                  "relation_type": "supports",
                  "target_concept_id": "notes/thesis.md",
                  "check_status": "checked",
              }
              for i in (1, 2, 3)
          ],
      )


  def test_active_project_slice_reaches_thesis_neighborhood(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      _seed_active_project(vault)

      slices = active_project_slices(vault)

      assert set(slices) == {"projects/thesis-a.md"}
      assert {
          "projects/thesis-a.md",
          "notes/thesis.md",
          "notes/n1.md",
          "notes/n2.md",
          "notes/n3.md",
      } <= slices["projects/thesis-a.md"]


  def test_flood_of_marks_routes_at_most_one_card_per_project(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      _seed_active_project(vault)
      marked = {f"notes/n{i}.md": "grounds-lost" for i in (1, 2, 3)}
      marked.update({f"notes/off-slice-{i}.md": "grounds-lost" for i in range(5)})
      marked["notes/thesis.md"] = "warrant-lost"

      cards = route_consequence_cards(
          vault, marked, trigger_id="catalog/sources/w1", reason="work w1 retracted"
      )

      assert len(cards) == 1
      frontmatter = read_frontmatter(vault / cards[0])
      assert frontmatter["loudness"] == "alert"
      assert frontmatter["attention_kind"] == "flag"
      assert frontmatter["target"] == "projects/thesis-a.md"
      assert "grounds-lost: 3" in frontmatter["finding"]
      assert "warrant-lost: 1" in frontmatter["finding"]

      # Re-run: dedupe_slug keeps it to the same single card.
      again = route_consequence_cards(
          vault, marked, trigger_id="catalog/sources/w1", reason="work w1 retracted"
      )
      assert again == []
      assert len(list((vault / "inbox").glob("flag-*.md"))) == 1


  def test_marks_outside_every_active_slice_route_no_card(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      _seed_active_project(vault)

      cards = route_consequence_cards(
          vault,
          {"notes/elsewhere.md": "grounds-lost"},
          trigger_id="catalog/sources/w1",
          reason="work w1 retracted",
      )

      assert cards == []
      assert not list((vault / "inbox").glob("flag-*.md"))


  def test_archived_project_is_not_an_active_slice(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      _seed_active_project(vault)
      project = vault / "projects/thesis-a.md"
      project.write_text(
          project.read_text(encoding="utf-8").replace(
              "thesis: notes/thesis.md", "thesis: notes/thesis.md\narchived: true"
          ),
          encoding="utf-8",
      )

      assert active_project_slices(vault) == {}
  ```

- [x] Run to verify failure: `python -m pytest tests/test_propagation_engine.py::test_flood_of_marks_routes_at_most_one_card_per_project -v` — expected: `ImportError: cannot import name 'route_consequence_cards'`.
  *Measured: `ImportError: cannot import name 'active_project_slices'` at the module import.*

- [x] Write the minimal implementation. In `src/memoria_vault/runtime/propagation.py`, extend imports with `from collections import Counter, deque` (Counter joins the existing deque import), `from memoria_vault.runtime.subsystems.lib.inbox import write_finding`, `from memoria_vault.runtime.vaultio import iter_markdown, read_frontmatter`, then add:

  ```python
  def active_project_slices(vault: Path) -> dict[str, set[str]]:
      """Per active (non-archived) project: its undirected thesis neighborhood."""
      vault = Path(vault)
      adjacency: dict[str, set[str]] = {}
      for row in state.concept_edges(vault, checked_only=False):
          source = normalize_path(str(row["source_concept_id"]))
          target = normalize_path(str(row["target_concept_id"]))
          adjacency.setdefault(source, set()).add(target)
          adjacency.setdefault(target, set()).add(source)
      slices: dict[str, set[str]] = {}
      for path in iter_markdown(vault):
          frontmatter = read_frontmatter(path)
          if frontmatter.get("type") != "project" or frontmatter.get("archived") is True:
              continue
          rel = path.relative_to(vault).as_posix()
          seeds = {rel}
          thesis = str(frontmatter.get("thesis") or "").strip()
          if thesis:
              seeds.add(
                  normalize_path(thesis if thesis.endswith(".md") else f"{thesis}.md")
              )
          members = set(seeds)
          queue = deque(sorted(seeds))
          while queue:
              current = queue.popleft()
              for neighbor in sorted(adjacency.get(current, ())):
                  if neighbor not in members:
                      members.add(neighbor)
                      queue.append(neighbor)
          slices[rel] = members
      return slices


  def route_consequence_cards(
      vault: Path,
      marked: Mapping[str, str],
      *,
      trigger_id: str,
      reason: str,
  ) -> list[str]:
      """Alert-tier card per (trigger, active project) whose slice was touched.

      Marks outside every active slice stay quiet: labels + journal only. This
      engine never emits block loudness (flood mechanics beyond routing are
      out of scope, EDGES §9).
      """
      vault = Path(vault)
      cards: list[str] = []
      for project_rel, members in sorted(active_project_slices(vault).items()):
          hits = {
              concept_id: consequence
              for concept_id, consequence in marked.items()
              if concept_id in members
          }
          if not hits:
              continue
          counts = Counter(hits.values())
          summary = ", ".join(f"{name}: {count}" for name, count in sorted(counts.items()))
          card = write_finding(
              vault,
              "flag",
              f"Consequence cascade touches {Path(project_rel).stem}",
              (
                  f"{len(hits)} concept(s) in this project's slice were marked "
                  f"stale ({summary}) after: {reason}"
              ),
              "consequence-propagation",
              target=project_rel,
              loudness="alert",
              evidence="\n".join(
                  f"- `{concept_id}` — {consequence}"
                  for concept_id, consequence in sorted(hits.items())
              ),
              dedupe_slug=f"consequence-{trigger_id}-{project_rel}",
          )
          if card is not None:
              cards.append(card.relative_to(vault).as_posix())
      return cards
  ```

- [x] Run to verify pass: `python -m pytest tests/test_propagation_engine.py -v`.
  *Measured: 38 passed.*
- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/propagation.py tests/test_propagation_engine.py
  git commit -m "feat(propagation): loudness-routed consequence cards — alert only on active-project-slice impact

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task ERP-C.5: Engine orchestration + trigger seams (scan, curate/insert, standing sweep, disposition)

> **Landing amendment (2026-08-02, ERP-C.5 as built).**
>
> 1. **Card routing is deferred, not dropped — ERP-C.6 has not landed.** This
>    task's Consumes names `route_consequence_cards` (C.6), and the section's
>    execution order puts C.6 first, but C.5 was executed alone. `_propagate`
>    therefore holds the routing seat with `cards: list[str] = []` and a comment
>    naming C.6, so every run stays at the quiet tier the routing rule already
>    gives marks outside every active slice: labels and journal, no card. The
>    published return shape is unchanged — `cards` is a real key, always empty
>    until C.6. **Obligation on ERP-C.6:** besides its own two functions it must
>    replace that one line in `propagate._propagate` with the
>    `route_consequence_cards(vault, consequences, trigger_id=target,
>    reason=reason)` call, and re-point this task's engine test
>    (`test_retraction_sweep_labels_every_reached_claim_and_commits_them`
>    asserts `result["cards"] == []` today).
> 2. **`added=changed` was a bug in the printed curate seam.** `added=False` is
>    not "no edge event", it is the *removal* trigger, and
>    `hop_consequence("edge-removed", "supports", seed=True)` is `grounds-lost` —
>    so an idempotent re-curate of a link that already exists would have marked
>    the target as having lost its grounds. The seam is now guarded by
>    `if changed:` and always passes `added=True`; `curate_note_link(...)
>    ["propagation"]` is `{}` when nothing changed, mirroring the worker's `{}`
>    for a non-transition standing.
> 3. **`marked` is closure membership, not write receipts.** A dependent the
>    mirror never saw and a dependent already carrying this consequence are both
>    in `marked` and neither reaches the commit; only rels `mark_consequence`
>    actually rewrote do. That is what makes a re-run of a settled sweep return
>    the same `marked` with `commit == ""`.
> 4. **The two latest-derived folds stay two folds.** C.5 is where that was to be
>    revisited, and it resolves the *direction*, not the duplication: `integrity`
>    now imports `propagation` at module scope, so the import back is closed for
>    good and `propagation` keeps its own fold and its own `_target_aliases` copy.
>    Unifying the other way — `integrity._downstream_events` consuming
>    propagation's fold — was considered and refused: the two are not the same
>    function (propagation's `_journal_ref` drops a reference `normalize_path`
>    rejects, `integrity._latest_derived` propagates the `ValueError`), and it
>    would make a propagation edit able to move the shipped scan-demotion walk.
>    The new edge stays one-directional and shallow: integrity calls propagation
>    for the new consequence behavior only.
> 5. **No golden drift.** The floor suite passes against the committed goldens
>    unchanged — the fixtures exercise neither a scan demotion with graph
>    dependents nor an `update-work` transition into `{retracted, superseded}`,
>    so neither seam appends a `typed-consequence` event there. The regeneration
>    step below was not needed and was not run.
> 6. **Signature of record for ERP-D.1** (cross-section contract 3):
>    `propagation.compute_consequences(vault: Path, target_id: str, *, trigger:
>    str) -> dict[str, dict[str, Any]]`, mapping concept **path** →
>    `{"consequence": str, "via": str, "depth": int}`. Pure read, no writes; the
>    start target is alias-expanded and is never itself in the result. The typed
>    count D.1's report card wants is `Counter(mark["consequence"] for mark in
>    compute_consequences(...).values())`.

**Files:**
- Modify: `src/memoria_vault/runtime/propagation.py` (add `compute_consequences`, `_propagate`, `propagate_consequences`, `propagate_consequences_explicit`, `propagate_edge_change`)
- Modify: `src/memoria_vault/runtime/integrity.py` — `propagate_scan_demotion` (lines 911-925) and `propagate_scan_demotion_explicit` (lines 928-948); both funnel from the trusted-writer scan trigger (`_observe_pi_edits_from_status`, trusted_writer.py:550-572), so wiring the two wrappers covers claim edit/retract with no trusted_writer change
- Modify: `src/memoria_vault/runtime/knowledge.py` — `curate_note_link` (lines 346-414; ERP-A widens its roster check at line 361 to `LINK_RELATIONS` — this task only appends the seam call after the commit at lines 404-406)
- Modify: `src/memoria_vault/runtime/worker.py` — the `update-work` branch (lines 928-1032; prior standing read before the `memoria` dict is mutated at lines 944-949, seam call after the `commit_writer_changes` at lines 1021-1026)
- Modify: `tests/test_propagation_engine.py`, `tests/test_knowledge.py` (level `runtime`, conftest line 74), `tests/test_worker_product_jobs.py` (level `runtime`, conftest line 118) — append seam tests
- Modify: `tests/fixtures/floor/goldens/*.json` — regenerated (see last step)

**Interfaces:**
- Consumes: everything above, plus `OperationContext` / `validate_operation_context` / `append_journal_event` / `append_explicit_journal_event` / `commit_writer_changes` / `commit_explicit_writer_changes` (trusted_writer.py:53/:139/:193/:215/:238/:251), `route_consequence_cards` (C.6), `hop_consequence` (C.2), test idioms `enqueue_operation` + `run_next_job` (test_worker_product_jobs.py) and `_md` + `call_with_context` (test_knowledge.py).
- Produces:
  - `propagation.compute_consequences(vault: Path, target_id: str, *, trigger: str) -> dict[str, dict[str, Any]]` — pure-read closure computation (alias-expanded via `_target_aliases`); **this is ERP-D's blast-radius-report input** for `decided-wrong` (report card = counts by type over this dict; ERP-D then calls `propagate_consequences(..., trigger="decided-wrong")` for the labels — "no writes to affected notes beyond labels").
  - `propagation.propagate_consequences(vault: Path, target_id: str, *, trigger: str, reason: str, context: OperationContext) -> dict[str, Any]` — compute → mark (C.4) → route cards (C.6) → one trusted-writer commit of changed note rels + card rels; returns `{"target_id", "trigger", "marked": dict[str, str], "cards": list[str], "commit": str}`.
  - `propagation.propagate_consequences_explicit(vault: Path, target_id: str, *, trigger: str, reason: str, actor: str, machine: str) -> dict[str, Any]` — same, outside an operation envelope.
  - `propagation.propagate_edge_change(vault: Path, *, source: str, relation_type: str, target: str, added: bool, reason: str, context: OperationContext) -> dict[str, Any]` — the edge add/remove seam: seed-marks the dependent endpoint per the decision table (`extends` ⇒ dependent is the source; else the target), then expands transitively. **Obligation on the sibling section drafting `state.insert_concept_edge` (EDGES §3): call this with `added=True` after the row insert.** Reindex pruning in `replace_concept_edges` does NOT fire it — a pruned edge's originating file edit is already caught by the scan seam.
  - New keys on existing results: `propagate_scan_demotion(...)["consequences"]` / `..._explicit(...)["consequences"]` (integrity), `curate_note_link(...)["propagation"]` (knowledge), the `update-work` result's `"propagation"` (worker; `{}` when standing did not transition into `{retracted, superseded}`).

**Steps:**

- [x] Write the failing engine test. Append to `tests/test_propagation_engine.py` (extend imports with `from memoria_vault.runtime.propagation import propagate_consequences_explicit` and `from memoria_vault.runtime.trusted_writer import append_explicit_journal_event`):

  ```python
  def test_retraction_sweep_marks_transitive_claims_and_routes_bounded_cards(
      tmp_path: Path,
  ) -> None:
      vault = workspace(tmp_path)
      _seed_active_project(vault)
      write_note(vault, "c1", "checked", "Grounded claim.")
      write_note(vault, "c2", "checked", "Derived claim.")
      state.replace_evidence_sets(
          vault,
          [
              {
                  "id": "ev-22222222",
                  "block_ref": "notes/c1.md#^blk-22222222",
                  "items": ["w1#^p0001"],
                  "type": "single-span",
                  "state": "complete",
                  "review_required": False,
                  "block_text_sha256": "0" * 64,
              }
          ],
      )
      state.replace_concept_edges(
          vault,
          [
              {
                  "source_concept_id": "notes/c1.md",
                  "relation_type": "supports",
                  "target_concept_id": "notes/c2.md",
                  "check_status": "checked",
              },
              {
                  "source_concept_id": "notes/c2.md",
                  "relation_type": "supports",
                  "target_concept_id": "notes/thesis.md",
                  "check_status": "checked",
              },
          ],
      )

      result = propagate_consequences_explicit(
          vault,
          "catalog/sources/w1",
          trigger="standing-changed",
          reason="work w1 retracted",
          actor="integrity",
          machine="test-machine",
      )

      assert result["marked"] == {
          "notes/c1.md": "grounds-lost",
          "notes/c2.md": "grounds-lost",
          "notes/thesis.md": "grounds-lost",
      }
      for rel in result["marked"]:
          frontmatter = read_frontmatter(vault / rel)
          assert frontmatter["stale"] is True
          assert frontmatter["consequence"] == "grounds-lost"
          assert state.concept_consequence(vault, rel) == "grounds-lost"
      # N marks, at most the loudness-routed cards: one active project ⇒ one card.
      assert len(result["cards"]) == 1
      assert result["commit"]
      # Idempotent re-run: no new writes, no new cards, no commit.
      again = propagate_consequences_explicit(
          vault,
          "catalog/sources/w1",
          trigger="standing-changed",
          reason="work w1 retracted",
          actor="integrity",
          machine="test-machine",
      )
      assert again["cards"] == [] and again["commit"] == ""
  ```

- [x] Run to verify failure: `python -m pytest tests/test_propagation_engine.py::test_retraction_sweep_marks_transitive_claims_and_routes_bounded_cards -v` — expected: `ImportError: cannot import name 'propagate_consequences_explicit'`.

- [x] Implement the engine. In `src/memoria_vault/runtime/propagation.py`, extend the trusted_writer import with `OperationContext, append_explicit_journal_event, append_journal_event, commit_explicit_writer_changes, commit_writer_changes, validate_operation_context`, then add:

  ```python
  def compute_consequences(
      vault: Path, target_id: str, *, trigger: str
  ) -> dict[str, dict[str, Any]]:
      """Closure marks for one fallen target — ERP-D's blast-radius report input."""
      vault = Path(vault)
      inputs = closure_inputs(vault)
      return consequence_closure(
          sorted(_target_aliases(vault, normalize_path(target_id))),
          trigger=trigger,
          grounding_edges=inputs.grounding_edges,
          evidence_dependents=inputs.evidence_dependents,
          derivation_children=inputs.derivation_children,
          typer=hop_consequence,
      )


  def _propagate(
      vault: Path,
      target_id: str,
      *,
      trigger: str,
      reason: str,
      append_event: Callable[[dict[str, Any]], Any],
      commit: Callable[[str, list[str]], str],
      initial_marks: Mapping[str, str] | None = None,
  ) -> dict[str, Any]:
      vault = Path(vault)
      target = normalize_path(target_id)
      if initial_marks is None:
          marked = compute_consequences(vault, target, trigger=trigger)
      else:
          inputs = closure_inputs(vault)
          marked = consequence_closure(
              (),
              trigger=trigger,
              grounding_edges=inputs.grounding_edges,
              evidence_dependents=inputs.evidence_dependents,
              derivation_children=inputs.derivation_children,
              typer=hop_consequence,
              initial_marks=initial_marks,
          )
      consequences: dict[str, str] = {}
      changed_paths: list[str] = []
      for concept_id in sorted(marked):
          mark = marked[concept_id]
          result = mark_consequence(
              vault,
              concept_id,
              consequence=str(mark["consequence"]),
              trigger_id=target,
              reason=reason,
              append_event=append_event,
          )
          consequences[concept_id] = str(mark["consequence"])
          if result["path"]:
              changed_paths.append(str(result["path"]))
      cards = route_consequence_cards(
          vault, consequences, trigger_id=target, reason=reason
      )
      commit_paths = [*changed_paths, *cards]
      commit_hash = (
          commit(f"propagate typed consequences from {target}", commit_paths)
          if commit_paths
          else ""
      )
      return {
          "target_id": target,
          "trigger": trigger,
          "marked": consequences,
          "cards": cards,
          "commit": commit_hash,
      }


  def propagate_consequences(
      vault: Path,
      target_id: str,
      *,
      trigger: str,
      reason: str,
      context: OperationContext,
  ) -> dict[str, Any]:
      """Propagate typed consequences inside an operation envelope."""
      validate_operation_context(vault, context)
      return _propagate(
          vault,
          target_id,
          trigger=trigger,
          reason=reason,
          append_event=lambda event: append_journal_event(vault, event, context=context),
          commit=lambda message, paths: commit_writer_changes(
              vault, message, paths, context=context
          ),
      )


  def propagate_consequences_explicit(
      vault: Path,
      target_id: str,
      *,
      trigger: str,
      reason: str,
      actor: str,
      machine: str,
  ) -> dict[str, Any]:
      """Propagate typed consequences outside an operation envelope."""
      return _propagate(
          vault,
          target_id,
          trigger=trigger,
          reason=reason,
          append_event=lambda event: append_explicit_journal_event(
              vault, event, actor=actor, machine=machine
          ),
          commit=lambda message, paths: commit_explicit_writer_changes(
              vault, message, paths, actor=actor, machine=machine
          ),
      )


  def propagate_edge_change(
      vault: Path,
      *,
      source: str,
      relation_type: str,
      target: str,
      added: bool,
      reason: str,
      context: OperationContext,
  ) -> dict[str, Any]:
      """Edge add/remove trigger seam (curate + insert paths)."""
      validate_operation_context(vault, context)
      trigger = "edge-added" if added else "edge-removed"
      source_rel = normalize_path(source)
      target_rel = normalize_path(target)
      dependent = source_rel if relation_type == "extends" else target_rel
      seed = hop_consequence(trigger, relation_type, seed=True)
      if seed is None:
          return {
              "target_id": dependent,
              "trigger": trigger,
              "marked": {},
              "cards": [],
              "commit": "",
          }
      return _propagate(
          vault,
          dependent,
          trigger=trigger,
          reason=reason,
          append_event=lambda event: append_journal_event(vault, event, context=context),
          commit=lambda message, paths: commit_writer_changes(
              vault, message, paths, context=context
          ),
          initial_marks={dependent: seed},
      )
  ```

- [x] Run to verify the engine test passes: `python -m pytest tests/test_propagation_engine.py -v`.

- [x] Write the failing scan-seam test. Append to `tests/test_propagation_engine.py`:

  ```python
  def test_scan_demotion_wrappers_attach_grounding_consequences(tmp_path: Path) -> None:
      from memoria_vault.runtime.integrity import propagate_scan_demotion_explicit

      vault = workspace(tmp_path)
      write_note(vault, "edited", "checked", "Edited claim.")
      write_note(vault, "dependent", "checked", "Dependent claim.")
      state.replace_concept_edges(
          vault,
          [
              {
                  "source_concept_id": "notes/edited.md",
                  "relation_type": "supports",
                  "target_concept_id": "notes/dependent.md",
                  "check_status": "checked",
              }
          ],
      )

      result = propagate_scan_demotion_explicit(
          vault,
          "notes/edited.md",
          reason="scan observed unchecked edit: notes/edited.md",
          actor="integrity",
          machine="test-machine",
      )

      assert result["consequences"]["marked"] == {
          "notes/dependent.md": "grounds-lost"
      }
      assert read_frontmatter(vault / "notes/dependent.md")["stale"] is True
  ```

- [x] Run to verify failure: `python -m pytest tests/test_propagation_engine.py::test_scan_demotion_wrappers_attach_grounding_consequences -v` — expected: `KeyError: 'consequences'`.

- [x] Wire the scan seam. In `src/memoria_vault/runtime/integrity.py`, add the import `from memoria_vault.runtime import propagation` to the top-level import block (after line 15's `from memoria_vault.runtime import capture, state` — no cycle: propagation imports state/trusted_writer/inbox only). Then in `propagate_scan_demotion` (lines 911-925), replace the bare `return _propagate_scan_demotion(...)` with:

  ```python
      result = _propagate_scan_demotion(
          vault,
          target_id,
          reason=reason,
          append_event=lambda event: append_journal_event(vault, event, context=context),
      )
      result["consequences"] = propagation.propagate_consequences(
          vault, target_id, trigger="claim-changed", reason=reason, context=context
      )
      return result
  ```

  and in `propagate_scan_demotion_explicit` (lines 928-948) likewise:

  ```python
      result = _propagate_scan_demotion(
          vault,
          target_id,
          reason=reason,
          append_event=lambda event: append_explicit_journal_event(
              vault, event, actor=actor, machine=machine
          ),
      )
      result["consequences"] = propagation.propagate_consequences_explicit(
          vault,
          target_id,
          trigger="claim-changed",
          reason=reason,
          actor=actor,
          machine=machine,
      )
      return result
  ```

  `_propagate_scan_demotion` (lines 951-1019) and `_downstream_events` (lines 1022-1048) stay untouched — the DAG demote/flag behavior is preserved; the engine's union walk overlaps it only through idempotent marks. Both call sites in the trusted-writer scan trigger (trusted_writer.py:556-572) flow through these wrappers unchanged.

- [x] Run to verify pass: `python -m pytest tests/test_propagation_engine.py -v`.

- [x] Write the failing curate-seam test. Append to `tests/test_knowledge.py` (after `test_curate_note_link_records_typed_link_on_checked_note`, line 395 block; uses the file's existing `_md`, `workspace`, `curate_note_link` wrappers):

  ```python
  def test_curate_note_link_fires_edge_added_propagation(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      _md(
          vault / "notes/rebuttal.md",
          "type: note\ncheck_status: checked\ntitle: Rebuttal\nstatus: accepted\n",
      )
      _md(
          vault / "notes/claim.md",
          "type: note\ncheck_status: checked\ntitle: Claim\nstatus: accepted\n",
      )

      result = curate_note_link(
          vault,
          "rebuttal",
          "supports",
          "claim",
          actor="pi",
          reason="PI linked claims",
          machine="curator",
      )

      # supports edge-added is a grounds gain: no marks, but the seam reports.
      assert result["propagation"]["trigger"] == "edge-added"
      assert result["propagation"]["marked"] == {}
  ```

  (The rebuttal-relation positive case — `edge-added` + `rebuttal` ⇒ target marked
  `rebuttal-strengthened` — needs ERP-A's roster widening of `curate_note_link`
  line 361; the decision-table row is already covered at unit level in C.2, so
  this seam test intentionally uses `supports`.)

- [x] Run to verify failure: `python -m pytest tests/test_knowledge.py::test_curate_note_link_fires_edge_added_propagation -v` — expected: `KeyError: 'propagation'`.

- [x] Wire the curate seam. In `src/memoria_vault/runtime/knowledge.py` `curate_note_link`, after the `commit = commit_writer_changes(...)` call (lines 404-406) and before the return dict, add:

  ```python
      from memoria_vault.runtime.propagation import propagate_edge_change

      propagation_result = propagate_edge_change(
          vault,
          source=source_rel,
          relation_type=link_type,
          target=target_rel,
          added=changed,
          reason=reason.strip() or f"edge curated: {source_rel} {link_type} {target_rel}",
          context=context,
      )
  ```

  and add `"propagation": propagation_result,` to the returned dict (lines 407-414). (`added=changed`: re-curating an existing link is not an edge event. Lazy import matches the module's existing style for cross-runtime imports and keeps knowledge.py's import graph flat.)

- [x] Run to verify pass: `python -m pytest tests/test_knowledge.py -v`.

- [x] Write the failing standing-seam test. Append to `tests/test_worker_product_jobs.py` (uses the file's existing `workspace`, `enqueue_operation`, `run_next_job`, `write_note` imports; add `from memoria_vault.runtime.vaultio import read_frontmatter` if not already imported — it is, line 28):

  ```python
  def test_update_work_standing_retraction_sweeps_grounded_claims(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      state.upsert_catalog_record(
          vault,
          work_id="w9",
          title="Retractable",
          description="Soon retracted.",
          csl_json={"title": "Retractable"},
          check_status="checked",
      )
      write_note(vault, "grounded", "checked", "Claim grounded in w9.")
      state.replace_evidence_sets(
          vault,
          [
              {
                  "id": "ev-33333333",
                  "block_ref": "notes/grounded.md#^blk-33333333",
                  "items": ["w9#^p0001"],
                  "type": "single-span",
                  "state": "complete",
                  "review_required": False,
                  "block_text_sha256": "0" * 64,
              }
          ],
      )

      enqueue_operation(
          vault,
          "update-work",
          payload={"work_id": "w9", "standing": "retracted"},
          idempotency_key="retract-w9",
          actor="pi",
      )
      done = run_next_job(vault, machine="test-machine")

      assert done["status"] == "done"
      assert done["propagation"]["trigger"] == "standing-changed"
      assert done["propagation"]["marked"] == {"notes/grounded.md": "grounds-lost"}
      frontmatter = read_frontmatter(vault / "notes/grounded.md")
      assert frontmatter["stale"] is True
      assert frontmatter["consequence"] == "grounds-lost"


  def test_update_work_archiving_does_not_sweep(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      state.upsert_catalog_record(
          vault,
          work_id="w10",
          title="Shelved",
          description="Archived, not falsified.",
          csl_json={"title": "Shelved"},
          check_status="checked",
      )

      enqueue_operation(
          vault,
          "update-work",
          payload={"work_id": "w10", "standing": "archived"},
          idempotency_key="archive-w10",
          actor="pi",
      )
      done = run_next_job(vault, machine="test-machine")

      assert done["status"] == "done"
      assert done["propagation"] == {}
  ```

- [x] Run to verify failure: `python -m pytest tests/test_worker_product_jobs.py::test_update_work_standing_retraction_sweeps_grounded_claims -v` — expected: `KeyError: 'propagation'`.

- [x] Wire the standing seam. In `src/memoria_vault/runtime/worker.py`'s `update-work` branch: directly after the `memoria` dict is first built (line 944, before the `standing :=` walrus block at 946), capture the prior value:

  ```python
          prior_standing = str(memoria.get("standing") or "current")
  ```

  Then after the existing `commit = commit_writer_changes(...)` call (lines 1021-1026) and before the `return` dict (lines 1027-1032), add:

  ```python
          propagation_result: dict[str, Any] = {}
          new_standing = str(memoria.get("standing") or "current")
          if new_standing in {"retracted", "superseded"} and new_standing != prior_standing:
              from memoria_vault.runtime.propagation import propagate_consequences

              propagation_result = propagate_consequences(
                  vault,
                  f"catalog/sources/{source['work_id']}",
                  trigger="standing-changed",
                  reason=f"work standing changed to {new_standing}: {source['work_id']}",
                  context=context,
              )
  ```

  and add `"propagation": propagation_result,` to the return dict. (Archived is excluded per the SPEC GAP ruling at the section top. The disposition seam needs no wiring here: ERP-D's `decided-wrong` verb calls `compute_consequences` for its report card and `propagate_consequences(..., trigger="decided-wrong")` for the labels — both are this task's Produces.)

- [x] Run to verify pass: `python -m pytest tests/test_worker_product_jobs.py tests/test_propagation_engine.py tests/test_knowledge.py -v`.

- [x] **Regenerate floor goldens** — *not needed as built (2026-08-02): the floor suite passes against the committed goldens unchanged, because its fixtures exercise neither a scan demotion with graph dependents nor an `update-work` transition into `{retracted, superseded}`. The step below was run only as far as confirming that.* The step as drafted — the scan and update-work seams append `typed-consequence` journal events and write frontmatter on fixture files, and the goldens hash `.memoria/journal/*.jsonl` + `.memoria/journal-head`:

  ```
  MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest tests/test_floor_seed.py \
      tests/test_floor_sweep_operations.py tests/test_floor_sweep_reads.py \
      tests/test_floor_invariants.py tests/test_floor_coverage.py tests/test_floor_transports.py -v
  git status --porcelain tests/fixtures/floor/goldens/
  ```

  Review the drift with `git diff tests/fixtures/floor/goldens/` — only hash
  values may change; a shape change means a wiring bug.

- [x] Run the gate: `python scripts/verify`.
- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/propagation.py src/memoria_vault/runtime/integrity.py \
      src/memoria_vault/runtime/knowledge.py src/memoria_vault/runtime/worker.py \
      tests/test_propagation_engine.py tests/test_knowledge.py \
      tests/test_worker_product_jobs.py tests/fixtures/floor/goldens
  git commit -m "feat(propagation): consequence engine orchestration + scan/curate/standing trigger seams

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```
# Section ERP-D: decided-wrong + origin repair + finding hygiene + structural-impact rewire + warrant param + edge-write counters

Implements EDGES spec sections 4 (warrant write path), 6 (`decided-wrong` → report), 7
(origin-blindness repair), 8 (finding hygiene + `structural_impact` substrate rewire),
and the section-4 instrumentation line (I1 per-relation-type edge-write counts).
Executes AFTER Plan 22's G1 + G2S1.1–.3 and after this plan's ERP-A/ERP-B/ERP-C
sections. This section owns **no schema migration** (v16 = NID-B, v17 = ERP-A,
v18 = ERP-C per the binding version chain).

**SPEC GAP:** the EDGES spec names ERP-C's typed-consequence engine but not its symbol; this section assumes `memoria_vault.runtime.subsystems.integrity.consequences.derive_consequences(vault, target_id, *, trigger: str, context: OperationContext) -> dict` returning `{"consequences": [{"type": str, "target_id": str}, ...]}` — reconcile the import path at plan assembly if ERP-C names it differently.
**Reconciled bridge contract:** the claim→work bridge is not a second raw-row
accessor.  ERP-B's checked `catalog/sources/*` link is indexed into
`concept_edges`; ERP-A.6 projects it as a normal path record, so structural
impact consumes it through `concept_edge_path_records` with every other edge.
This prevents a second graph reader from leaking v16 identity keys.
**SPEC GAP:** the spec does not fix where the §4 absence-honesty threshold lives; this section registers it as `.memoria/config/edges.yaml` key `warrant_absence_threshold` (int ≥ 1; absent/malformed = disabled), following the shipped `feedback.yaml` fail-safe pattern (`runtime/feedback.py:9-27`).
**SPEC GAP:** whether reindex preserves a frontmatter link's `addressed`/`status` bit into `attributes_json` is Plan 22 G2S1.1/.2 territory; this section reads `attributes_json["addressed"]` defaulting to `True` when absent.

Repo gate: `python scripts/verify`. No new test files are created (every task extends an
existing registered file), so `tests/conftest.py` `TEST_LEVELS` (tests/conftest.py:18-121)
is untouched.

**Floor-golden manifest note:** Tasks ERP-D.1 and ERP-D.5 add journal events
(`disposition.v1` with `item_type="claim"` and `curate-note-link` events with `warrant`/`edge_id`
fields). ERP-D.6's `edge-write.v1` rows land in the non-chained `telemetry_events` table
(recorded amendment, `2026-07-16-i1-full-wiring-design.md` §1) — no journal writes and no
golden drift from D.6. After each of the journal-touching tasks passes locally, run the
floor suite once and regenerate goldens if they drift:
`MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest tests/test_floor_sweep_operations.py tests/test_floor_invariants.py -v`
(refused in CI by design, tests/floor_lib.py:331-354), review with `git diff
tests/fixtures/floor/goldens`, and include the regenerated goldens in that task's commit.

---

### Task ERP-D.1: `decided-wrong` claim disposition → blast-radius report card

> **Blocked, not started (2026-08-01) — this task needs ERP-C.2 and ERP-C.5.**
> Attempted alongside ERP-B.4 and stopped before any edit. The deliverable *is*
> the typed count (`grounds-lost: 2`, `warrant-lost: 1`), so the report cannot be
> written without a consequence **typer**. At this commit `runtime/propagation.py`
> holds only ERP-C.1: `consequence_closure` (which takes `typer` as a required
> argument), `closure_inputs`, `CONSEQUENCE_TYPES`, `TRIGGERS`, `HOP_EVIDENCE`,
> `HOP_DERIVED`. `hop_consequence` (ERP-C.2) and `compute_consequences`
> (ERP-C.5 — cross-section contract 3 names it as *this* task's report input,
> superseding the `consequences.derive_consequences` the Interfaces block below
> still assumes) are both absent, and `memoria_vault.runtime.subsystems.integrity`
> has no `consequences` module for the drafted `monkeypatch.setattr` target to
> resolve against. Supplying a local typer here would be a second copy of the
> §5 decision table living in `integrity.py` — the replica-exempt-invariant class
> ERP-A.6's review named — and it would collide with C.2 on landing. Landing only
> the `item_type`/`decided-wrong`→`override` half would also drift floor goldens
> ahead of its own report path, against contract 8's serialization. **Run this
> task after ERP-C.2 and ERP-C.5, and rewrite its Interfaces block and both
> drafted tests onto `propagation.compute_consequences` at that point.** No file
> was touched; the checkboxes below stay unchecked.

> **Landing amendment (2026-08-02, ERP-D.1 as built, unblocked by ERP-C.5).**
> The rewrite the block above asked for, done.
>
> 1. **Report input is `propagation.compute_consequences(vault, target_id, *,
>    trigger) -> dict[str, dict[str, Any]]`.** It takes **no `context`** — it is
>    a pure read, which is the whole point of "report, not act" — and it is
>    keyed concept **path** → `{"consequence", "via", "depth"}`, not a list of
>    `{"type", "target_id"}` rows. So the count is
>    `Counter(str(mark["consequence"]) for mark in marks.values())` and the
>    evidence iterates `sorted(marks.items())`. There is no
>    `runtime/subsystems/integrity/consequences` module and there never will be;
>    `integrity` already imports `propagation` at module scope (ERP-C.5
>    amendment 4), so the helper calls it directly with no local import and no
>    second copy of the decision table.
> 2. **No monkeypatch.** The drafted test stubs the very derivation whose typed
>    count is the deliverable — escape class 4, a test that proves the card can
>    format a dict someone handed it. The landed test **produces** the closure:
>    four real edges out of `notes/claim.md` (two `supports`, one `warrant`, one
>    `rebuttal`), and it asserts the `rebuttal` dependent is absent, because
>    `hop_consequence("decided-wrong", "rebuttal", …)` is a `None` cell. That
>    assertion is what kills a mutant swapping the trigger, which no stub could.
> 3. **"Report, not act" is asserted, not just printed.** For every note the
>    closure reached the test pins `concept_consequence == ""`, `concept_flags
>    == {}` and no `stale:` frontmatter — the observable difference from
>    `propagate_consequences`, which reaches the same set and labels all of it.
> 4. **`confirm-tension` was already in the outcome set** (ERP-B landed first),
>    so this task added only `"decided-wrong": "override"` to the decision map,
>    as the Interfaces block anticipated. The `item_type` roster is closed here
>    (`{"attention", "claim"}`) even though the disposition event schema takes
>    `item_type` as a free string: this seam is where it is decided, and a
>    third test pins that an off-roster value is refused before it can reach the
>    event.
> 5. **No golden drift, and none was regenerated.** The `disposition.v1` row
>    with `item_type="claim"` only exists on a path no floor fixture takes; the
>    floor suite passes against the committed goldens unchanged (63 passed).
>    The manifest note at the top of ERP-D listed this task as golden-touching —
>    it is not.

**Files:**
- Modify: `src/memoria_vault/runtime/integrity.py` (`resolve_attention`, lines 1127-1191; new private helper below it)
- Modify: `src/memoria_vault/runtime/worker.py` (attention operation handler, lines 813-831)
- Modify: `tests/test_feedback_instrumentation.py` (append after line 65)

**Interfaces:**
- Consumes: `operations.emit_disposition_event(vault, *, decision, item_type, item_id, context)` (`runtime/operations.py:146-164`; `item_type` is a free non-empty string per the I1 validator, `engine/empirical_events.py:148-165`, so `"claim"` needs no schema change); `DECISIONS` already contains `override` (`engine/empirical_events.py:32` — closed enum unchanged); `inbox.write_finding(vault, card_type, title, finding, raised_by, *, agent_recommendation, target, citekey, loudness, evidence) -> Path` (`runtime/subsystems/lib/inbox.py:75-113`); **ERP-C:** `consequences.derive_consequences(vault, target_id, *, trigger, context) -> dict` (see SPEC GAP); **ERP-B:** extends the same outcome→decision dict with `"confirm-tension": "accept"` — this task adds only its own row and must merge cleanly with ERP-B's edit of `integrity.py:1169`.
- Produces: `integrity.resolve_attention(vault, target_id, *, context, resolution, outcome=None, routing_class="ask", reason="", item_type="attention") -> dict` — `item_type` ∈ {"attention", "claim"}; outcome `decided-wrong` valid only for `resolution="resolved"` + `item_type="claim"`, maps to `decision="override"`, derives consequences (report, not act) and writes one `flag` card naming `cascade-rollback` as the escalation. Worker payload key `item_type` on `resolve-attention`.

**Steps:**

- [x] Write the failing test — append to `tests/test_feedback_instrumentation.py`:

```python
def test_decided_wrong_claim_emits_override_and_report_card(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    calls: list[tuple[str, str]] = []

    def fake_derive(vault, target_id, *, trigger, context):
        calls.append((target_id, trigger))
        return {
            "consequences": [
                {"type": "grounds-lost", "target_id": "notes/dependent.md"},
                {"type": "grounds-lost", "target_id": "notes/other.md"},
                {"type": "warrant-lost", "target_id": "notes/license.md"},
            ]
        }

    monkeypatch.setattr(
        "memoria_vault.runtime.subsystems.integrity.consequences.derive_consequences",
        fake_derive,
    )
    request = worker.enqueue_operation(
        workspace,
        "resolve-attention",
        actor="pi",
        idempotency_key="pi-decided-wrong",
        payload={
            "target_id": "notes/claim.md",
            "item_type": "claim",
            "outcome": "decided-wrong",
            "reason": "PI decided the claim is wrong",
        },
    )

    result = worker.run_request(workspace, request["job_id"], machine="PI laptop")

    assert result["status"] == "done"
    dispositions = _events_with_schema(workspace, "disposition.v1")
    assert len(dispositions) == 1
    assert dispositions[0]["decision"] == "override"
    assert dispositions[0]["item_type"] == "claim"
    assert dispositions[0]["item_id"] == "notes/claim.md"
    assert calls == [("notes/claim.md", "decided-wrong")]
    cards = sorted((workspace / "inbox").glob("flag-blast-radius-*.md"))
    assert len(cards) == 1
    text = cards[0].read_text(encoding="utf-8")
    assert "grounds-lost: 2" in text
    assert "warrant-lost: 1" in text
    assert "report, not an action" in text
    assert "cascade-rollback" in text
    assert "[[notes/dependent.md]]" in text
    assert "[[notes/license.md]]" in text


def test_decided_wrong_rejected_for_attention_item_type(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    request = worker.enqueue_operation(
        workspace,
        "resolve-attention",
        actor="pi",
        idempotency_key="pi-decided-wrong-attention",
        payload={
            "target_id": "inbox/attention/pi.md",
            "outcome": "decided-wrong",
            "reason": "wrong item_type",
        },
    )

    result = worker.run_request(workspace, request["job_id"], machine="PI laptop")

    assert result["status"] == "failed"
    assert "decided-wrong" in result["error"]
    assert _events_with_schema(workspace, "disposition.v1") == []
```

- [x] Run to verify both fail:
  `python -m pytest tests/test_feedback_instrumentation.py::test_decided_wrong_claim_emits_override_and_report_card tests/test_feedback_instrumentation.py::test_decided_wrong_rejected_for_attention_item_type -v`
  Expected: first fails with `assert result["status"] == "done"` (worker job failed:
  `unsupported attention outcome for resolved: 'decided-wrong'`); second fails because the
  error message check passes but the first assertion pattern differs — confirm both fail
  before implementing (the second may already pass on the error text; if it passes as-is,
  keep it as a pin).

- [x] Write minimal implementation in `src/memoria_vault/runtime/integrity.py`. Replace the signature and validation block at lines 1127-1148:

```python
def resolve_attention(
    vault: Path,
    target_id: str,
    *,
    context: OperationContext,
    resolution: str,
    outcome: str | None = None,
    routing_class: str = "ask",
    reason: str = "",
    item_type: str = "attention",
) -> dict[str, Any]:
    """Record a PI attention disposition through the worker-owned journal."""
    validate_operation_context(vault, context)
    if resolution not in {"acknowledged", "resolved"}:
        raise ValueError(f"unsupported attention resolution: {resolution!r}")
    if item_type not in {"attention", "claim"}:
        raise ValueError(f"unsupported attention item_type: {item_type!r}")
    outcome = outcome or resolution
    if resolution == "acknowledged":
        supported_outcomes = {"acknowledged"}
    else:
        supported_outcomes = {"apply", "reject", "defer"}
        if item_type == "claim":
            supported_outcomes |= {"decided-wrong"}
    if outcome not in supported_outcomes:
        raise ValueError(f"unsupported attention outcome for {resolution}: {outcome!r}")
```

  Extend the decision map at line 1169 (ERP-B adds its own `"confirm-tension": "accept"` row to this same dict):

```python
        emit_disposition_event(
            vault,
            decision={
                "apply": "accept",
                "reject": "reject",
                "defer": "defer",
                "decided-wrong": "override",
            }[outcome],
            item_type=item_type,
            item_id=target,
            context=context,
        )
```

  After the disposition emit and before the `touched` frontmatter block (line 1174), add the report path (report, not act — no writes to the claim or its descendants here):

```python
    touched: list[str] = []
    if resolution == "resolved" and outcome == "decided-wrong":
        touched.append(_write_blast_radius_report(vault, target, context=context))
```

  (Fold this into the existing `touched: list[str] = []` line so it is declared once.) Add the helper below `resolve_attention`:

```python
def _write_blast_radius_report(
    vault: Path, target: str, *, context: OperationContext
) -> str:
    """Report-not-act: derive typed consequences and write one inbox flag card."""
    from memoria_vault.runtime.subsystems.integrity.consequences import derive_consequences
    from memoria_vault.runtime.subsystems.lib import inbox

    consequences = list(
        derive_consequences(vault, target, trigger="decided-wrong", context=context).get(
            "consequences"
        )
        or []
    )
    counts: dict[str, int] = {}
    for row in consequences:
        kind = str(row.get("type") or "")
        counts[kind] = counts.get(kind, 0) + 1
    count_text = ", ".join(f"{kind}: {n}" for kind, n in sorted(counts.items())) or "none"
    finding = (
        f"PI decided {target} is wrong. Blast radius: {len(consequences)} affected "
        f"note(s) by typed consequence ({count_text}). This is a report, not an action; "
        "no note was demoted or quarantined. Escalation: the destructive path is the "
        f"explicitly invoked cascade-rollback operation on {target}."
    )
    evidence = "\n".join(
        f"- [[{row['target_id']}]] — {row['type']}" for row in consequences
    )
    path = inbox.write_finding(
        vault,
        "flag",
        f"Blast radius: {Path(target).stem}",
        finding,
        "resolve-attention",
        agent_recommendation="issues-found",
        target=target,
        loudness="alert",
        evidence=evidence,
    )
    return path.relative_to(vault).as_posix()
```

- [x] Wire the worker payload in `src/memoria_vault/runtime/worker.py` — inside the `resolve_attention(...)` call at lines 819-830 add one argument:

```python
            item_type=str(payload.get("item_type") or "attention"),
```

- [x] Run to verify both pass:
  `python -m pytest tests/test_feedback_instrumentation.py -v`
  (the three pre-existing parametrized `apply/reject/defer` cases must still pass — `item_type` defaults to `"attention"`).
  *Measured: 18 passed. Four new tests, not two: the drafted pair plus one pinning that a claim resolved any other way writes no report, and one pinning the closed `item_type` roster.*

- [ ] Regenerate floor goldens if drifted (see manifest note at top) and commit:
  `git add src/memoria_vault/runtime/integrity.py src/memoria_vault/runtime/worker.py tests/test_feedback_instrumentation.py tests/fixtures/floor/goldens`
  Message: `feat(integrity): decided-wrong claim disposition emits override + blast-radius report card (EDGES section 6)` ending with
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task ERP-D.2: origin-blindness repair — remove the scan-demotion PI branch

**Files:**
- Modify: `src/memoria_vault/runtime/integrity.py` (`_propagate_scan_demotion`, lines 951-1019; the PI branch to delete is lines 973-984)
- Modify: `tests/test_worker_product_jobs.py` (`test_observe_pi_edits_propagates_scan_side_demotion`, lines 760-839)

**Interfaces:**
- Consumes: nothing new. `cascade_rollback`'s PI flag-don't-quarantine branch (`integrity.py:1089-1100`) is **kept untouched** (write authority stays origin-gated, EDGES section 7); its pins in `tests/test_integrity_cascade_rollback.py` and `tests/test_worker_knowledge_cycle.py:290-293` must keep passing unmodified.
- Produces: `_propagate_scan_demotion` return dict keeps all four keys (`demoted`, `needs_human`, `stale`, `skipped`); `needs_human` is now always `[]` on this path (the key survives for shape stability — `trusted_writer.py:550-572` calls the wrapper for effect only).

**Steps:**

> **Amendment — the fixture needs a PI descendant at depth ≥ 2 too
> (2026-08-01, applied).** Deleting the branch changes *two* arms, not one: a
> PI descendant at depth 1 moves from `cascade-rollback`/`ask` to
> `scan-demotion-propagation`/`act`, and a PI descendant at depth ≥ 2 moves
> from `cascade-rollback`/`ask` to `scan-demotion-stale`/`log`. The fixture as
> written holds exactly one PI descendant, at depth 1, so a mutant restoring
> `if actor == "pi" and depth > 1:` would survive it. The test therefore also
> seeds `notes/pi-depth-two.md` — PI-authored, input `digests/direct.md` — and
> asserts it stays `checked` with a `stale` flag whose `trigger_id` is the
> scanned source, plus its `scan-demotion-stale`/`log` event.

- [x] Update the pinning test first (it pins the wrong behavior). In `tests/test_worker_product_jobs.py:818-839`, the PI-authored depth-1 descendant `pi_rel` must now receive the same epistemic mark as machine-derived ones. Replace lines 820 and 834-839:

```python
    assert state.concept_check_status(vault, pi_rel) == "unchecked"
    assert state.concept_check_status(vault, depth_two_rel) == "checked"
    assert state.concept_flags(vault, depth_two_rel)["stale"]["trigger_id"] == source_rel
```

  (line 820 `== "checked"` becomes `== "unchecked"`; keep the depth-two assertions), and replace the final `cascade-rollback` event assertion (lines 834-839) with:

```python
    assert any(
        event.get("check") == "scan-demotion-propagation"
        and event.get("target_id") == pi_rel
        and event.get("route") == "act"
        for event in event_log
    )
    assert not any(event.get("check") == "cascade-rollback" for event in event_log)
```

- [x] Run to verify it fails:
  `python -m pytest tests/test_worker_product_jobs.py::test_observe_pi_edits_propagates_scan_side_demotion -v`
  Expected: `AssertionError` at `state.concept_check_status(vault, pi_rel) == "unchecked"` (currently `"checked"` because of the PI branch).

- [x] Write minimal implementation — in `src/memoria_vault/runtime/integrity.py` delete lines 973-984 (the `actor = str(event.get("actor") or "")` read, the `if actor == "pi":` arm with its `_flag_descendant(check="cascade-rollback", route="ask")` call, and `needs_human.append(output_id)`), changing the `elif depth == 1:` to `if depth == 1:`. Keep `needs_human: list[str] = []` (line 961) and the return key (line 1016) so the result shape is stable. Epistemic marks are now origin-blind; `cascade_rollback` (lines 1051-1124) is not touched.

- [x] Run to verify it passes, plus the untouched authority-gate pins:
  `python -m pytest tests/test_worker_product_jobs.py tests/test_integrity_cascade_rollback.py tests/test_worker_knowledge_cycle.py tests/test_operation_context.py -v`
  *Measured: 190 passed. The branch was verbatim at `integrity.py:977-988` (the plan's 973-984 had drifted); `elif depth == 1:` became `if depth == 1:` and `needs_human` stays declared and returned, always `[]`.*

- [ ] Commit:
  `git add src/memoria_vault/runtime/integrity.py tests/test_worker_product_jobs.py`
  Message: `fix(integrity): scan-demotion marks are origin-blind — remove PI descendant exemption (EDGES section 7)` ending with
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task ERP-D.3a: stage-machine recalibration — implements Graph-R11, closes #1624

**Early-run exception (contract 13, 2026-08-01):** this task's only graph
prerequisite is ERP-A's activated roster, which is merged, so it runs ahead of
ERP-B, ERP-C, and the rest of ERP-D. It must land before ERP-D.3, which edits
the same `no-support`/`no-refutation` finding family.

**Verified current state (read by content at `a582a510`).** The shipped
`_argument_stage` (`knowledge.py:3269-3276`) is:

```python
def _argument_stage(counts: dict[str, int], relation_count: int) -> str:
    if relation_count == 0:
        return "cold-start"
    if relation_count < 3:
        return "developing"
    if counts["contradicts"] > 0:
        return "contested"
    return "supported"
```

It reads `counts["contradicts"]` and `relation_count` and nothing else — never
`supports`, `rebuttal`, `warrant`, or `qualifier`. So a component of three
`rebuttal` edges returns `supported` while `saturation_conditions` on the same
payload reports `{"mature_graph": True, "has_support": False,
"has_refutation": False}`. **This is not a side effect of ERP-A.3 widening
`relation_count`:** the machine never consulted a support count, so even the
pre-widening triple staged three `extends` edges as `supported`. ERP-A.3 only
enlarged the set of relations that can reach the threshold —
`_note_edges` (`knowledge.py:3374-3382`) now iterates `sorted(LINK_RELATIONS)`.
`_argument_confidence` (`:3306-3314`) is partially protected — it requires
`supports > 0` for `supported` — but it too treats only `contradicts` as
challenge, so three rebuttals render `below-threshold` rather than `contested`.

**Not in scope — the second `argument_stage` producer.**
`subsystems/processing/project/structural_impact.py` emits its own
`argument_stage` over a different vocabulary (`cold-start`/`developing`/
`mature`, `:276-285` and `:88-92`) with `READINESS_RELATION_THRESHOLD = 5`, and
its trace mode already requires `support_count >= 1 and contradict_count >= 1`.
It is a different lens, not a replica of `_argument_stage`, and Graph-R11 does
not rule on it. Do not rename its stages or import the rosters into it; if a
later task unifies the two lenses, that is its own ruling.

**Files:**
- Modify: `src/memoria_vault/runtime/subsystems/lib/edges.py` — add the three
  Graph-R11 role rosters beside `EDGE_RELATIONS`/`LINK_RELATIONS`. Contract 2
  makes `edges.py` the single roster owner, and `tests/test_edges.py:489`
  (`test_single_roster_definition_repo_wide`) is the guard; do not spell these
  sets as literals in `knowledge.py`.
- Modify: `src/memoria_vault/runtime/knowledge.py` — `_argument_stage`
  (`:3269-3276`), `_argument_confidence` (`:3306-3314`), and
  `_argument_saturation_conditions` (`:3292-3298`). The
  `analyze_project_argument` payload (`:1911-1927`) keeps its existing
  `supports_count`/`contradicts_count`/`extends_count` keys unchanged — this
  task changes classification, not the per-verb export.
- Modify: `tests/test_project_knowledge.py` (stage/confidence/saturation
  assertions, and the roster pin at `:505-535`).
- Modify: `tests/test_edges.py` (pin the three new rosters and their
  partition).

**Interfaces:**
- Consumes: `edges.EDGE_RELATIONS` / `edges.LINK_RELATIONS` (already merged);
  nothing from ERP-B, ERP-C, or ERP-D.1/.2.
- Produces: `edges.SUPPORT_RELATIONS = frozenset({"supports"})`,
  `edges.CHALLENGE_RELATIONS = frozenset({"contradicts", "rebuttal", "tension"})`,
  `edges.STRUCTURE_RELATIONS = frozenset({"warrant", "qualifier", "extends"})`.
  The three partition `EDGE_RELATIONS` exactly (disjoint, union equal) — pin
  that, so a seventh verb added to `EDGE_RELATIONS` without a role fails here
  instead of silently classifying as structure.
  `analyze_project_argument`'s `argument_stage` keeps its existing four values
  (`cold-start`, `developing`, `contested`, `supported`) — Graph-R11 forbids a
  new stage name.

**Derived value the ruling does not spell verbatim.** A component at or above
the connectivity threshold holding only structure edges (e.g. three
`qualifier`s: no `supports`, no challenge) cannot be `supported` (no support
edge) and gets no new name, so it is **`developing`**. Do not invent a fifth
stage for it.

**Fixture warning — `tension` cannot be produced at this seam.**
`LINK_RELATIONS = EDGE_RELATIONS - {"tension"}` and `_note_edges` iterates
`sorted(LINK_RELATIONS)`, so no frontmatter `links:` fixture can make a
`tension` edge reach `_argument_stage` today. `tension` is in the challenge
roster for the `concept_edges` consumers that ERP-B/D own. Prove the challenge
arm with `rebuttal` (frontmatter-legal, and the verb #1624 was filed about);
cover `tension` at the roster level in `tests/test_edges.py`, not with a
`knowledge.py` fixture that cannot exist.

**Steps:**

- [x] Write the failing tests first, in `tests/test_project_knowledge.py`.
  Each must mutate exactly one arm:
  - three `rebuttal` edges into the thesis component → `argument_stage ==
    "contested"`, `displayed_confidence == "contested"`,
    `saturation_conditions["has_refutation"] is True`,
    `saturation_conditions["has_support"] is False`. Today all four are wrong
    (`supported`, `below-threshold`, `False`, `False`).
  - three `qualifier` edges → `argument_stage == "developing"` (today
    `supported`); assert `has_support is False` and `has_refutation is False`
    in the same payload, so the qualifier-is-structure half of Graph-R11 is
    what the assertion observes and not the count.
  - one `supports` + two `extends` (threshold met, no challenge) →
    `argument_stage == "supported"` still, so the recalibration does not
    demote a genuinely supported component.
  - one `supports` + one `rebuttal` + one `extends` → `contested`, with
    `has_support is True` — the two sides coexist rather than one masking the
    other.
  Use N ≥ 3 distinct edges per fixture (the threshold is 3; an N=1 fixture
  only exercises the `developing` short-circuit and proves nothing about the
  roster).

- [x] Run to verify failure:
  `python -m pytest tests/test_project_knowledge.py -v` — expected: the
  rebuttal and qualifier cases fail with `argument_stage == "supported"`.

- [x] Add the rosters to `edges.py` and pin them in `tests/test_edges.py`,
  including the partition assertion against `EDGE_RELATIONS`.

- [x] Write the minimal implementation in `knowledge.py`: a private
  `_challenge_count(counts)`/`_support_count(counts)` pair summing the
  imported rosters, then
  - `_argument_stage`: below threshold → unchanged; challenge present →
    `contested`; support present → `supported`; otherwise `developing`.
  - `_argument_confidence`: challenge → `contested`; support → `supported`;
    otherwise `below-threshold`.
  - `_argument_saturation_conditions`: `has_refutation` becomes the challenge
    count; `has_support` and `mature_graph` are unchanged.
  Leave `_argument_findings`, `_argument_gap_findings`, and
  `_argument_advisories` alone — ERP-D.3 owns that family, and splitting the
  edit across two tasks is what the ordering note above prevents.

- [x] Re-check the callers that re-export the stage without recomputing it:
  `knowledge.py:788`, `worker.py:570`, `worker.py:606`. They pass the value
  through; confirm by content that none re-derives it, and if one does, fix it
  in this task rather than leaving a second stage machine.

- [x] Run to verify pass, including the surfaces that assert a stage string:
  `python -m pytest tests/test_project_knowledge.py tests/test_edges.py tests/test_gap_analysis.py tests/test_cli_work_project.py tests/test_worker_product_jobs.py tests/test_project_structural_impact.py -v`
  (the last file must pass **unmodified** — it pins the other lens).

- [x] Run the gate: `python scripts/verify`.

- [ ] Commit:
  `git add src/memoria_vault/runtime/subsystems/lib/edges.py src/memoria_vault/runtime/knowledge.py tests/test_project_knowledge.py tests/test_edges.py`
  Message: `fix(graph): stage-role classification for the argument lens (Graph-R11, closes #1624)` ending with
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task ERP-D.3: finding hygiene — `no-support` collapse + guarded `unstated-warrant` retarget

> **Execution override — identity-safe warrant analysis:** Follow the
> 2026-07-29 path-projection amendment, point 7.  The historical raw
> `state.concept_edges` endpoint loop, path-keyed edge fixture, and helper that
> parses `attributes_json` in `knowledge.py` are superseded by
> `edges.concept_edge_path_records(vault, checked_only=False)`.  This task may
> compare the argument component only with projected `source_path` and
> `target_path`; its only attribute input is the projection's parsed
> `record["attributes"]`.

> **Execution amendment (2026-08-02) — what ERP-D.3 landed.** The task's Files
> list is widened by the two inconsistencies ERP-D.3a disclosed and left, both
> reproduced by execution before any edit. **Four producers, not one.** D.3a
> converged `_argument_stage`/`_argument_confidence`/
> `_argument_saturation_conditions` on the Graph-R11 rosters but explicitly left
> the finding family to this task, so `_argument_findings` (`no-refutation`) and
> `_argument_advisories` (the "seek a counterargument" line) move onto
> `_challenge_count` here alongside `_argument_gap_findings`' `conflict` gate —
> otherwise a rebuttal-only component stages `contested` with
> `has_refutation: True` while the same payload asks for the counterargument it
> already has. **`_saturation_block` (`knowledge.py:956-989`) is the fourth**, and
> it is named in no plan section: it derived `has_support`/`has_counterpoint`
> from `supports_count`/`contradicts_count` and then re-exported
> `saturation_conditions` verbatim beside them, so the same block published
> `uncountered: 1` and `has_counterpoint: False` next to
> `conditions.has_refutation: True`. It cannot be repaired with a roster — the
> payload exports no per-role count for `rebuttal`/`tension`, and D.3a froze that
> export — so it now reads both sides off the conditions dict it already
> re-exports, which makes the contradiction unrepresentable rather than merely
> fixed. `structural_impact.py` is untouched, per D.3a's out-of-scope note.
>
> Three deviations from the snippets above. `_warrant_absence_gap` imports
> `concept_edge_path_records`/`warrant_absence_threshold` at module scope, not
> inside the function: `knowledge.py` already imports `lib.edges` at module
> scope, so the local import would guard a cycle that does not exist.
> `warrant_absence_threshold` catches `OSError` as well as `yaml.YAMLError`,
> because "unreadable" is in the contract the docstring states and
> `yaml.YAMLError` does not cover it. `edges.py` takes `import yaml` at module
> scope and its "stdlib-only at module scope" note becomes "no first-party
> imports at module scope" — that clause's stated reason is cycle avoidance,
> which a third-party leaf import cannot threaten. No seeded
> `.memoria/config/edges.yaml` template: the guard is disabled by default, so a
> seeded file would only be a place to accidentally enable it (and
> `tests/test_installer_skeleton.py:38` pins that roster).
>
> **`_argument_next_action("unstated-warrant")` is unreachable**, before and
> after the retarget in step (4). Its only caller takes `seed = advice or
> _argument_next_action(kind)`, every `gap_findings` row carries a non-empty
> `advice`, and `findings` never carries that kind — the same is already true of
> its `conflict`, `fragility` and `structural` branches. The line is retargeted
> as instructed rather than deleted (deleting the four dead branches is a
> different change than this task's), so its text is correct but unobserved; a
> mutation of it survives by construction. The `no-support` half of step (4) *is*
> reachable and is pinned in `tests/test_gap_analysis.py`, asserted across both
> `finding_source` values because the two cards share one `finding_kind`.
>
> Goldens did not move: no seeded file changed and no floor entry reads the
> argument lens. Mutation testing: 40 mutants at every roster and gate boundary,
> both directions, 37 killed; the 3 survivors are equivalent mutants (two
> respell `_support_count` as `counts["supports"]`, identical while
> `SUPPORT_RELATIONS` is a singleton and kept as the roster consumer for the day
> it is not; one is the unreachable branch above).
>
> **Amendment 2026-08-02 (issue #1681).** The four unreachable branches this note
> records — `unstated-warrant`, `conflict`, `fragility`, `structural` — are
> deleted. This note is the confirmation the issue asked for that no future caller
> was planned: it states the unreachability is structural, not a gap awaiting a
> producer. Their text was a verbatim copy of the corresponding `advice` on
> `_argument_gap_findings`' rows, so the deletion removes a duplicate rather than a
> behaviour, and the survivor this note counts as equivalent is gone with it.
> `_argument_next_action` now answers only `no-support` and `no-refutation` plus a
> fallback, which is exactly the advice-less roster `_argument_findings` and
> `_project_argument_empty` produce; both halves of that premise are pinned in
> `tests/test_project_knowledge.py`. Also fixed there: `_argument_gap_why("conflict")`
> and the matching `advice` said "contradiction" while Graph-R11 had widened the
> gate to `_challenge_count` (`contradicts`, `rebuttal`, `tension`); both now name
> the challenge roster, pinned against the rebuttal vault in
> `tests/test_gap_analysis.py`. Goldens still did not move.

**Files:**
- Modify: `src/memoria_vault/runtime/subsystems/lib/edges.py` (ERP-A's module; append the config loader)
- Modify: `src/memoria_vault/runtime/knowledge.py` (`_argument_gap_findings` lines 2943-2977, `_argument_next_action` lines 957-968, `analyze_project_argument` call site line 1716; new `_warrant_absence_gap` helper near `_note_edges` line 3001)
- Modify: `tests/test_project_knowledge.py` (append after line 121)

**Interfaces:**
- Consumes: **ERP-A.6:** `edges.concept_edge_path_records(vault, checked_only=False)` (durable endpoint paths plus parsed attributes, never raw identities); **ERP-A:** `edges.py` module exists with the converged roster, and schema v17's `relation_type` CHECK admits `warrant` so a warrant row can be seeded in tests.
- Produces: `edges.warrant_absence_threshold(vault: Path) -> int | None` (None = disabled; the default); `knowledge._argument_gap_findings(counts, relation_count, *, warrant_gap: dict[str, Any] | None = None) -> list[dict[str, Any]]`; the `supports == 0` gap row is now `kind="no-support"` (alias pair deleted); `unstated-warrant` means "grounded claim component with no warrant edge or edge-attribute", fires only when the vault-wide warrant count ≥ the configured threshold, and always carries `warrant_count` as denominator (absence-honesty guard, EDGES section 4).

**Steps:**

- [x] Write the failing tests — append to `tests/test_project_knowledge.py`:

```python
def _seed_argument(vault: Path) -> None:
    _md(
        vault / "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n"
        "description: Project\nthesis: notes/thesis.md\n",
    )
    _md(
        vault / "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\n",
    )
    _md(
        vault / "notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Support\n"
        "links:\n  supports:\n    - notes/thesis.md\n",
    )


def test_no_support_gap_replaces_unstated_warrant_alias(tmp_path: Path) -> None:
    _md(
        tmp_path / "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n"
        "description: Project\nthesis: notes/thesis.md\n",
    )
    _md(
        tmp_path / "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\n",
    )
    _md(
        tmp_path / "notes/refute.md",
        "type: note\ncheck_status: checked\ntitle: Refute\n"
        "links:\n  contradicts:\n    - notes/thesis.md\n",
    )

    result = analyze_project_argument(tmp_path, "project-alpha")

    kinds = [row["kind"] for row in result["gap_findings"]]
    assert "no-support" in kinds
    assert "unstated-warrant" not in kinds


def test_warrant_absence_finding_disabled_by_default(tmp_path: Path) -> None:
    _seed_argument(tmp_path)

    result = analyze_project_argument(tmp_path, "project-alpha")

    # Zero warrant edges vault-wide and no config: no ambient warrant-absence
    # finding may fire anywhere (EDGES acceptance criterion).
    assert "unstated-warrant" not in [row["kind"] for row in result["gap_findings"]]


def test_warrant_absence_finding_fires_above_threshold_with_denominator(
    tmp_path: Path,
) -> None:
    _seed_argument(tmp_path)
    config = tmp_path / ".memoria/config"
    config.mkdir(parents=True, exist_ok=True)
    (config / "edges.yaml").write_text("warrant_absence_threshold: 1\n", encoding="utf-8")
    state.replace_concept_edges(
        tmp_path,
        [
            {
                "source_concept_id": ULID_ELSEWHERE_LICENSE,
                "relation_type": "warrant",
                "target_concept_id": ULID_ELSEWHERE_CLAIM,
                "target_path": "notes/elsewhere-claim.md",
                "check_status": "checked",
                "source_path": "notes/elsewhere-license.md",
            }
        ],
    )

    result = analyze_project_argument(tmp_path, "project-alpha")

    rows = [row for row in result["gap_findings"] if row["kind"] == "unstated-warrant"]
    assert len(rows) == 1
    assert rows[0]["warrant_count"] == 1
    assert rows[0]["severity"] == "medium"
```

  **v16 fixture amendment:** `_seed_argument` and this test must write
  id-bearing checked concepts with fixed valid ULIDs, then call
  `trusted_writer.rebuild_concept_mirror_from_files(vault)` before inserting
  any edge.  Seed the elsewhere warrant as a resolved ULID-keyed edge with
  `source_concept_id=ULID_ELSEWHERE_LICENSE`,
  `target_concept_id=ULID_ELSEWHERE_CLAIM`, and the durable
  `source_path`/`target_path` values; do not use a path in either identity
  field.  Add the complementary local-warrant case: its projected
  `source_path` or `target_path` is in the component, so it suppresses the
  `unstated-warrant` finding.  The assertions must prove the behavior after
  the mirror re-keys paths to ULIDs rather than only in the provisional
  path-keyed state.

- [x] Run to verify they fail:
  `python -m pytest tests/test_project_knowledge.py::test_no_support_gap_replaces_unstated_warrant_alias tests/test_project_knowledge.py::test_warrant_absence_finding_disabled_by_default tests/test_project_knowledge.py::test_warrant_absence_finding_fires_above_threshold_with_denominator -v`
  Expected: first fails (`"unstated-warrant" in kinds` — the alias still fires); second fails
  the same way (the alias fires with zero warrant edges); third fails with no
  `unstated-warrant` row / `KeyError: 'warrant_count'`.

- [x] Write the config loader — append to `src/memoria_vault/runtime/subsystems/lib/edges.py` (add `import yaml` and `from pathlib import Path` to its imports if ERP-A's module does not already have them):

```python
EDGES_CONFIG = ".memoria/config/edges.yaml"


def warrant_absence_threshold(vault: Path) -> int | None:
    """Return the pre-registered warrant-absence threshold, or None when disabled.

    Absence-honesty guard (edges design, section 4): warrant/rebuttal absence is
    never an ambient finding until per-type usage crosses this threshold. Fails
    safe to None (disabled) on an absent, unreadable, malformed, or key-missing
    config.
    """
    path = Path(vault) / EDGES_CONFIG
    if not path.is_file():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    value = data.get("warrant_absence_threshold")
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None
    return value
```

- [x] Write the knowledge.py changes. (1) In `_argument_gap_findings` (lines 2943-2977) replace the `supports == 0` block (lines 2953-2960) and thread the guard:

```python
def _argument_gap_findings(
    counts: dict[str, int],
    relation_count: int,
    *,
    warrant_gap: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    if relation_count == 0:
        gaps.append(
            {
                "kind": "structural",
                "severity": "high",
                "advice": "seed checked notes around the thesis",
            }
        )
    if counts["supports"] == 0:
        gaps.append(
            {
                "kind": "no-support",
                "severity": "high",
                "advice": "add supporting evidence notes",
            }
        )
    elif counts["supports"] == 1 and relation_count >= 3:
        gaps.append(
            {
                "kind": "fragility",
                "severity": "medium",
                "advice": "add independent support",
            }
        )
    if warrant_gap is not None:
        gaps.append(
            {
                "kind": "unstated-warrant",
                "severity": "medium",
                "advice": "state the warrant on a grounding edge or link a warrant note",
                "warrant_count": warrant_gap["warrant_count"],
            }
        )
    if counts["contradicts"] > 0:
        gaps.append(
            {
                "kind": "conflict",
                "severity": "medium",
                "advice": "resolve or preserve the contradiction",
            }
        )
    return gaps
```

  (2) Add the guard helper near `_note_edges` (after line 3010):

```python
def _warrant_absence_gap(
    vault: Path, component: set[str], counts: dict[str, int]
) -> dict[str, Any] | None:
    """Guarded warrant-absence signal: grounded component, no warrant edge/attribute."""
    from memoria_vault.runtime.subsystems.lib.edges import (
        concept_edge_path_records,
        warrant_absence_threshold,
    )

    threshold = warrant_absence_threshold(vault)
    if threshold is None or counts["supports"] == 0:
        return None
    warrant_count = 0
    component_has_warrant = False
    for record in concept_edge_path_records(vault, checked_only=False):
        attributes = record["attributes"]
        if record["relation_type"] != "warrant" and not attributes.get("warrant"):
            continue
        warrant_count += 1
        if record["source_path"] in component or record["target_path"] in component:
            component_has_warrant = True
    if warrant_count < threshold or component_has_warrant:
        return None
    return {"warrant_count": warrant_count}
```

  (`json` is not needed by this task after the projection takes responsibility
  for safe attribute parsing.)
  (3) In `analyze_project_argument` change line 1716 to:

```python
        "gap_findings": _argument_gap_findings(
            counts, relation_count, warrant_gap=_warrant_absence_gap(vault, component, counts)
        ),
```

  (4) In `_argument_next_action` (lines 957-968) retarget the `unstated-warrant` line and cover `no-support`:

```python
    if finding_kind == "no-support":
        return "add supporting evidence notes"
    if finding_kind == "unstated-warrant":
        return "state the warrant on a grounding edge or link a warrant note"
```

  (`_argument_gap_why` already handles `no-support` at line 978; `_argument_gap_kind` maps both kinds to its default `argument-unsupported` — no change, the gap-card vocabulary is stable.)

- [x] Run to verify the three new tests pass and the existing lens pins hold:
  `python -m pytest tests/test_project_knowledge.py tests/test_gap_analysis.py -v`

- [ ] Commit:
  `git add src/memoria_vault/runtime/subsystems/lib/edges.py src/memoria_vault/runtime/knowledge.py tests/test_project_knowledge.py`
  Message: `feat(knowledge): collapse unstated-warrant alias into no-support; guarded warrant-absence finding with denominator (EDGES sections 4+8)` ending with
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task ERP-D.4: `structural_impact` rewires onto `concept_edges` + the bridge

> **Execution override — projected endpoints:** Follow the 2026-07-29
> path-projection amendment, point 6.  The historical raw
> `state.concept_edges` endpoint loop and path-ID fixtures are superseded by
> `edges.concept_edge_path_records(vault, checked_only=False)`.  The record
> projection is required here because `attributes["addressed"]` must survive
> the rewire; the strict three-field pair API cannot carry it.

> **Execution amendment (2026-08-02) — what ERP-D.4 landed.** Nine deviations
> from the step text below, none of them contract changes.
> **(1) `substrate_edges(vault, resolver)`, not `(vault, notes, resolver)`.** The
> drafted body never reads `notes` and neither does this one — the resolver is
> the whole map. A parameter no branch depends on cannot be mutated, so it is
> gone; `analyze`/`analyze_survey` still hold `notes` for their own reads.
> **(2) No `_edge_key`.** `build_resolver` already keys every note by its `.md`
> path *and* by that path with the suffix stripped, so the helper is a no-op on
> every value the projection can emit. Measured, not asserted: a mutant that
> applies a strict superset of `_edge_key` (`normalize_target`, i.e. wikilink
> strip + `.md` strip) to the projected target survives the whole file. Deleting
> it is the only way that line is pinned at all; the coupling it leaves behind is
> pinned instead, by a mutant that drops the `.md` alias from `build_resolver`.
> **(3) A bridge target reaches three note-keyed reads, not one.** The drafted
> guard covers `gap_taxonomy`'s `on_path_nodes` loop. `analyze`'s `scope_overlap`
> sum (`scope_terms(notes[key])`) and `gap_taxonomy`'s `contradicts` loop
> (`notes[edge.source]`/`notes[edge.target]`) index `notes` by a graph node too,
> and both raise `KeyError` on a `catalog/sources/*` node that reaches the thesis
> component — a crash the rewire introduces, since `build_edges` could only ever
> produce note-keyed nodes. All three are guarded and each is pinned separately.
> **(4) No `_EDGE_ROWS` accumulator.** `state.replace_concept_edges(...,
> paths=[source_path])` scopes each seed to the one note that authored it, so the
> fixtures are additive without module-level state that outlives a test.
> **(5) The fixture writes no `addressed` attribute by default.** The drafted
> `link_row` always wrote one, which leaves the projection's `True` default
> unfixtured. One test carries all four shapes — absent, `true`, `false`, and a
> non-bool — the last of which is what pins the `bool()` coercion.
> **(6) No `target_concept_id` in fixture rows.** `replace_concept_edges` reads
> it only as a fallback spelling for `target_path`, so a row carrying both has a
> dead field. The unresolved case is a `target_path` with no mirror row, which is
> what parks the pending row the step text asks for.
> **(7) Docs.** `docs/reference/control-and-policy/project-structural-impact.md`
> claimed the operation "follows every authored `links` relationship"; its Inputs
> section now names the substrate, the un-indexed-`links` consequence, the
> catalog bridge node and the unchecked traversal.
> **(8) Two live decisions this rewire exposes, neither taken here.**
> `find_thesis`'s `normalize_link` was excluded from the `thesis_rel`
> convergence (#1623) because it was shared with the alias-space `links:`
> traversal. That traversal is now deleted, so the tolerance's remaining
> co-tenant is the `project:` back-reference scan — genuinely alias space, so the
> exclusion still stands, but its stated reason no longer does and converging
> `thesis:` alone is now a strictly smaller change than it was. Separately,
> `RELATIONS` (`= LINK_RELATIONS`) now filters a *substrate* that may legally
> hold `tension` — `insert_concept_edge` writes it and `replace_concept_edges`
> preserves it — so the filter is a semantic choice about what counts as an
> argument relation, not the syntactic roster of what frontmatter may author.
> Kept as drafted and pinned by
> `test_a_confirmed_tension_row_is_outside_the_structural_roster`; roster
> convergence remains ERP-A's.
> **(9) `normalize_target` does not stay — it collapses into `normalize_link`.**
> The step text's closing note says it stays "for thesis/link resolution", and
> the reference half does. Its `addressed`/`status` half had exactly one reader,
> `build_descriptive_edges`; `normalize_link`, the only other caller, discards
> element `[1]`. Deleting the reader without it leaves dead producer state whose
> test (`test_normalize_target_extracts_dict_wikilink_and_status`) reads as
> coverage of live behavior — the escape this task was told to look for. The two
> functions are now one `normalize_link(raw) -> str`, and the substrate's
> `attributes["addressed"]` is the only addressed signal. Its blank/non-`str`
> pre-check went too: mutation-testing shows `strip_wikilink`'s documented
> totality over non-strings and whitespace already covers every arm of it, so the
> pre-check was a second copy of that rule and unkillable. Two adjacent dead
> reads are left alone because this task did not orphan them and removing them is
> not its call: `find_thesis`'s `active_thesis:` fallback (a field `project.yaml`
> now forbids) and `normalize_link`'s six-key dict chain, of which only the
> undeclared `project:` key can still deliver a dict at all.
> **Mutation proof:** 28 mutants across both files, 27 killed. The one survivor
> is provably equivalent: path-validating the projected *source* before the alias
> table. Every value `concept_edges` can render a source at is either an `.md`
> rel — which `normalize_link_target` returns unchanged, since it judges only the
> last segment's suffix — or a `catalog/sources/*` rel, which has no source-side
> bridge rescue and is dropped by the `not source` arm either way. It becomes
> killable only if the bridge is ever made symmetric.

**Files:**
- Modify: `src/memoria_vault/runtime/subsystems/processing/project/structural_impact_graph.py` (add `substrate_edges`; delete `build_edges`/`build_descriptive_edges`, lines 105-133)
- Modify: `src/memoria_vault/runtime/subsystems/processing/project/structural_impact.py` (imports lines 13-29; `analyze_survey` edge read line 79; `analyze` edge read line 262; `gap_taxonomy` non-note guard lines 166-167)
- Modify: `tests/test_project_structural_impact.py` (fixtures lines 10-90 and the edge seeding in every test)

**Interfaces:**
- Consumes: **ERP-A.6:** `edges.concept_edge_path_records(vault, checked_only=False)` (identity-safe source/target paths plus parsed attributes, including ERP-B's `catalog/sources/*` bridge targets). Test setup may use Plan 22's `state.replace_concept_edges(vault, rows)` after rebuilding a v16 mirror, but production code must never read raw state endpoints. Roster convergence of `RELATIONS` (`structural_impact_graph.py:14`) is **ERP-A's** — untouched here.
- Produces: `structural_impact_graph.substrate_edges(vault: Path, notes: dict[str, Note], resolver: dict[str, str]) -> list[Edge]` — the only edge source for structural impact (no frontmatter text parsing); `Edge.addressed` from projected `attributes["addressed"]`, defaulting to `True`. `impact.analyze` / `impact.run` signatures unchanged.

**Steps:**

- [x] Update the test fixtures to seed the substrate. In `tests/test_project_structural_impact.py` add after the imports (line 8):

```python
import json

from memoria_vault.runtime import state

_EDGE_ROWS: dict[str, list[dict]] = {}


def link_row(
    vault: Path, source: str, relation: str, target: str, *, addressed: bool = True
):
    with state.connect(vault) as conn:
        source_id = state.resolve_concept_id(conn, f"notes/{source}.md")
        target_id = state.resolve_concept_id(conn, f"notes/{target}.md")
    rows = _EDGE_ROWS.setdefault(str(vault), [])
    rows.append(
        {
            "source_concept_id": source_id,
            "relation_type": relation,
            "target_concept_id": target_id,
            "target_path": f"notes/{target}.md",
            "check_status": "checked",
            "source_path": f"notes/{source}.md",
            "attributes_json": json.dumps({"addressed": addressed}),
        }
    )
    state.replace_concept_edges(vault, rows)
```

  The fixture writes each note with a fixed valid ULID and rebuilds the v16
  concept mirror before the first `link_row` call.  Thus `resolve_concept_id`
  returns a ULID in the setup while the projection observed by the code under
  test returns only the note paths.  The unresolved-row test uses a ULID source,
  `target_concept_id=None`, and `target_path="notes/ghost.md"`; it must not use
  a path in an identity column.  Add one `addressed=False` row and assert it is
  absent from the addressed structural result, proving that metadata survived
  without a raw state read.

  and append `link_row(vault, name, relation, target)` as the last line of both the `claim()` helper (after line 63) and the `gap()` helper (after line 80). Every existing test seeds edges only through these two helpers, so no per-test edits are needed; the frontmatter `links:` blocks stay (they remain the PI-authored source of the substrate fill, and `find_thesis`/`normalize_target` still read frontmatter).

- [x] Add the failing rewire test — append to `tests/test_project_structural_impact.py`:

```python
def test_structural_impact_reads_substrate_not_file_text(tmp_path):
    seed_mature_graph(tmp_path)
    # Corrupt one frontmatter links block after the substrate rows exist: the
    # substrate, not file text, must be the edge source.
    path = tmp_path / "notes/a.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "  supports: ['[[notes/thesis]]']", "  supports: []"
        ),
        encoding="utf-8",
    )

    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert payload["relation_count"] == 5
    assert payload["supports_count"] == 3


def test_substrate_edges_skips_unresolved_and_bridge_targets_survive(tmp_path):
    seed_mature_graph(tmp_path)
    rows = _EDGE_ROWS[str(tmp_path)] + [
        {
            "source_concept_id": ULID_A,
            "relation_type": "supports",
            "target_concept_id": None,
            "target_path": "notes/ghost.md",
            "check_status": "checked",
            "source_path": "notes/a.md",
        }
    ]
    state.replace_concept_edges(tmp_path, rows)

    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    # The dangling target resolves to no note and is dropped, exactly like the
    # old resolver behavior.
    assert payload["relation_count"] == 5
```

- [x] Run to verify failure:
  `python -m pytest tests/test_project_structural_impact.py::test_structural_impact_reads_substrate_not_file_text -v`
  Expected: `AssertionError` on `relation_count == 5` (text path sees 4 after the corruption).

- [x] Write minimal implementation. (1) In `structural_impact_graph.py` replace `build_edges`/`build_descriptive_edges` (lines 105-133) with:

```python
def substrate_edges(
    vault: Path, notes: dict[str, Note], resolver: dict[str, str]
) -> list[Edge]:
    """Read edges from the concept_edges substrate plus the claim→work bridge."""
    from memoria_vault.runtime.subsystems.lib.edges import concept_edge_path_records

    edges: list[Edge] = []
    for record in concept_edge_path_records(vault, checked_only=False):
        source = resolver.get(_edge_key(record["source_path"]))
        target_raw = _edge_key(record["target_path"])
        target = resolver.get(target_raw)
        if target is None and target_raw.startswith("catalog/sources/"):
            target = target_raw  # virtual work node carried by the projection
        if not source or not target or source == target:
            continue
        edges.append(
            Edge(
                source=source,
                target=target,
                relation=record["relation_type"],
                addressed=bool(record["attributes"].get("addressed", True)),
            )
        )
    return edges


def _edge_key(path: str) -> str:
    return path[:-3] if path.endswith(".md") else path
```

  (2) In `structural_impact.py`: drop `build_descriptive_edges` and `build_edges` from the import block (lines 18-19), import `substrate_edges` instead; change line 79 to
  `edges = [edge for edge in substrate_edges(vault, notes, resolver) if edge.addressed]`
  and pass `vault` into `analyze_survey` (its signature becomes
  `analyze_survey(vault: Path, notes, resolver, project)`, updating the single call at line 253);
  change line 262 to
  `edges = [edge for edge in substrate_edges(vault, notes, resolver) if edge.relation in RELATIONS and edge.addressed]`.
  (3) Guard `gap_taxonomy` against virtual bridge nodes — at the top of the `for key in sorted(on_path_nodes):` loop (line 166) add:

```python
        if key not in notes:
            continue
```

- [x] Run the whole file to verify all pass:
  `python -m pytest tests/test_project_structural_impact.py -v`
  (`test_normalize_target_extracts_dict_wikilink_and_status` still passes — `normalize_target` stays for thesis/link resolution.)

- [ ] Commit:
  `git add src/memoria_vault/runtime/subsystems/processing/project/structural_impact_graph.py src/memoria_vault/runtime/subsystems/processing/project/structural_impact.py tests/test_project_structural_impact.py`
  Message: `refactor(structural-impact): read concept_edges substrate + claim→work bridge instead of file text (EDGES section 8)` ending with
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task ERP-D.5: `curate-note-link` warrant parameter → `attributes_json.warrant`

> **Execution override — v16 writer result:** Follow the 2026-07-29
> path-projection amendment, point 8.  The historical path-hash calculation,
> raw `state.concept_edges` filters, and path-keyed test fixture below are
> superseded by a rebuilt ULID mirror, the `insert_concept_edge` result, and
> `edges.concept_edge_path_records` assertions.

> **Execution amendment (2026-08-01) — what ERP-D.5 landed.** The test snippet below
> is stale twice over and was rewritten, not copied: `check_status:` is a retired
> frontmatter field `curate_note_link` now refuses outright
> (`test_curate_note_link_rejects_invalid_source_without_mutation`), so the ULID
> mirror is built with `tests/test_knowledge.py`'s own `checked_note` helper instead
> of `_md`. Three tests beyond the drafted round trip, each pinning a branch the
> round trip cannot: a blank `warrant` writes no edge row and no journal keys;
> whitespace-only text is blank while padded text is stripped, and the record it
> lands on is asserted **whole**, because an `attributes`-only assertion cannot tell
> a warrant hung on `extends` from one hung on `supports`; and a refused link writes
> no edge, since `insert_concept_edge` commits its own transaction and an edge
> written before the target check would survive the refusal that follows it. The
> worker payload wire is pinned in `tests/test_worker_product_jobs.py`, a file this
> task's Files list does not name — nothing else observes that line. Deliberately
> not done, as outside the task's Files list: no `memoria link --warrant` CLI flag,
> and the worker *result* dict is unchanged (the task specifies the input wire
> only). Floor goldens did not drift — no seeded file changed and the operation's
> floor entry is `expect: refused` on actor authority before the payload is read.

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py` (`curate_note_link`, lines 346-414)
- Modify: `src/memoria_vault/runtime/worker.py` (`curate-note-link` handler, lines 471-497)
- Modify: `tests/test_knowledge.py` (append after line 428)

**Interfaces:**
- Consumes: **ERP-A.6:** `edges.concept_edge_path_records(vault, checked_only=False)` for identity-safe postcondition checks; **ERP-B.2:** `state.insert_concept_edge(vault, *, source, relation_type, target, attributes=None, context) -> dict` with v16 path-boundary resolution, PK-triple upsert, and result `{"edge_id": str, "created": bool, "attributes": dict}`.  The writer supplies paths only; it never derives an edge id itself.
- Produces: `knowledge.curate_note_link(vault, source_note_path, link_type, target_path, *, context, reason="", warrant="") -> dict` — when `warrant` is non-blank the same trusted-writer transaction upserts `attributes_json.warrant` on the identity-keyed edge and the result/journal event carry `edge_id` and `warrant`; worker payload key `warrant` on `curate-note-link`. (EDGES section 4 write path: warrant *text* on a grounding edge — the lightweight Option-B form; the `warrant` *relation* itself is a plain `link_type` after ERP-A activates the roster.)

**Steps:**

- [x] Write the failing round-trip test — append to `tests/test_knowledge.py`:

```python
def test_curate_note_link_warrant_text_round_trips_to_edge_attribute(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    from memoria_vault.runtime.subsystems.lib.edges import concept_edge_path_records
    from memoria_vault.runtime.trusted_writer import rebuild_concept_mirror_from_files
    from memoria_vault.runtime.vaultio import new_ulid

    source_id, target_id = new_ulid(), new_ulid()
    _md(
        vault / "notes/source.md",
        f"type: note\nid: {source_id}\ncheck_status: checked\ntitle: Source\nstatus: accepted\n",
    )
    _md(
        vault / "notes/target.md",
        f"type: note\nid: {target_id}\ncheck_status: checked\ntitle: Target\nstatus: accepted\n",
    )
    rebuild_concept_mirror_from_files(vault)

    result = curate_note_link(
        vault,
        "source",
        "supports",
        "target",
        warrant="RCTs in this population license the inference",
        actor="pi",
        reason="PI linked claims",
        machine="curator",
    )

    edge_id = str(result["edge_id"])
    assert edge_id
    records = [
        record
        for record in concept_edge_path_records(vault, checked_only=False)
        if record["source_path"] == "notes/source.md"
        and record["relation_type"] == "supports"
        and record["target_path"] == "notes/target.md"
    ]
    assert records == [
        {
            "source_path": "notes/source.md",
            "target_path": "notes/target.md",
            "relation_type": "supports",
            "attributes": {"warrant": "RCTs in this population license the inference"},
        }
    ]
    assert source_id not in repr(records)
    assert target_id not in repr(records)
    event = list(iter_jsonl(vault / ".memoria/journal/curator.jsonl"))[-1]
    assert event["warrant"] == "RCTs in this population license the inference"
    assert event["edge_id"] == edge_id

    # Upsert: re-curating the same triple with new warrant text updates in place.
    updated = curate_note_link(
        vault,
        "source",
        "supports",
        "target",
        warrant="Updated license",
        actor="pi",
        machine="curator",
    )
    assert updated["changed"] is False
    assert updated["edge_id"] == edge_id
    records = [
        record
        for record in concept_edge_path_records(vault, checked_only=False)
        if record["source_path"] == "notes/source.md"
        and record["relation_type"] == "supports"
        and record["target_path"] == "notes/target.md"
    ]
    assert records[0]["attributes"]["warrant"] == "Updated license"
```

- [x] Run to verify it fails:
  `python -m pytest tests/test_knowledge.py::test_curate_note_link_warrant_text_round_trips_to_edge_attribute -v`
  Expected: `TypeError: curate_note_link() got an unexpected keyword argument 'warrant'`.

- [x] Write minimal implementation in `knowledge.py`. Add `warrant: str = ""` to the signature (line 353, after `reason`), normalize it beside `link_type` (line 360): `warrant = warrant.strip()`. After the `if changed:` block (line 389) and before the journal event (line 391) add:

```python
    edge_id = ""
    if warrant:
        edge = state.insert_concept_edge(
            vault,
            source=source_rel,
            relation_type=link_type,
            target=target_rel,
            attributes={"warrant": warrant},
            context=context,
        )
        edge_id = str(edge["edge_id"])
```

  Extend the journal event dict (lines 393-401): after `"reason": reason.strip(),` add

```python
            **({"warrant": warrant, "edge_id": edge_id} if warrant else {}),
```

  and add `"edge_id": edge_id,` to the returned dict (lines 407-414).

- [x] Wire the worker payload — in `worker.py` add to the `curate_note_link(...)` call (lines 483-490):

```python
            warrant=str(payload.get("warrant") or ""),
```

- [x] Run to verify it passes, plus the existing link pin:
  `python -m pytest tests/test_knowledge.py::test_curate_note_link_warrant_text_round_trips_to_edge_attribute tests/test_knowledge.py::test_curate_note_link_records_typed_link_on_checked_note -v`

- [ ] Regenerate floor goldens if drifted (manifest note at top) and commit:
  `git add src/memoria_vault/runtime/knowledge.py src/memoria_vault/runtime/worker.py tests/test_knowledge.py tests/fixtures/floor/goldens`
  Message: `feat(knowledge): curate-note-link warrant text upserts attributes_json.warrant on the identity-keyed edge (EDGES section 4)` ending with
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task ERP-D.6: I1 per-relation-type edge-write counters

**Recorded amendment (I1 full-wiring spec §1, storage-plane ruling):**
`edge-write.v1` is analytics-only — it lands in the non-chained
`telemetry_events` table, never the journal. **Cross-plan dependency:** this
task requires the I1 full-wiring plan's slice 1 (schema v19
`telemetry_events` + `runtime/telemetry.py` `record_telemetry_event`) — land
it first; check before starting:
`grep -n "telemetry_events" src/memoria_vault/runtime/state.py` must hit.

> **Execution amendment (2026-08-02) — what ERP-D.6 landed.**
>
> **The dependency check as printed is wrong and always will be.** The table is
> declared in `src/memoria_vault/runtime/schema.sql:434-443`, not in `state.py`,
> so the `grep` above misses on a repo that has fully satisfied the dependency.
> The honest check is `grep -n "telemetry_events" src/memoria_vault/runtime/schema.sql`
> plus `test -f src/memoria_vault/runtime/telemetry.py`. Both hold at v19; slice 1
> shipped in #7dc4718a (rung 18) and #8d432921. No schema change here.
>
> **Two seams, not one, and the emission is at the caller — not inside
> `insert_concept_edge`.** Contract 4's "final call order inside the function:
> insert → propagate → emit" is superseded, the same way ERP-C.5 already
> superseded its own half of it: the landed `propagate_edge_change` call sits in
> `knowledge.curate_note_link` (`knowledge.py:441-450`), not in
> `state.insert_concept_edge`. D.6 follows that precedent for a load-bearing
> reason, not for symmetry. `curate_note_link` *calls* `insert_concept_edge`
> whenever it hangs a warrant, so an emission inside the storage function counts
> one warranted curate twice — and `edge_write_counts` groups by `relation_type`
> alone, so the double would be invisible in the touch-budget number the beta.2
> gate reads. The counters therefore hang on the two *seams a PI can reach*:
> `knowledge.curate_note_link` emits `write_path="curate-note-link"`, and
> `integrity._confirm_tension_edge` — the ERP-B `confirm-tension` path, which is
> the only way `tension` ever enters the graph — emits
> `write_path="insert-concept-edge"`. `state.py` gains no dependency on
> `runtime.operations`. `write_path` names the seam the PI used, never the
> storage call underneath it; that sentence is now in the emitter's docstring.
>
> **Two deviations inside the printed snippets.** (1) `emit_edge_write_event`
> opens with `validate_operation_context(vault, context)`. As printed it accepted
> a `context` it never read, which is an unused parameter dressed as an authority
> gate; the sibling analytics emitter `operations.record_empirical_event` does
> validate, and a counter is a write. (2) `edge_write_counts` drops the printed
> `ORDER BY relation_type`. The function returns a `dict[str, int]`, and dict
> equality ignores order, so that clause was an unkillable mutant by
> construction — no test could ever distinguish it. `WHERE event_type = ?` is
> parameterized off `EDGE_WRITE_EVENT_SCHEMA` rather than repeating the literal.
>
> **Namespace (escape class 9).** `edge_write_counts` answers in **relation-type
> space** — the `EDGE_RELATIONS` roster — and in no other. It reads
> `telemetry_events.payload_json`, never `concept_edges`, so no path, no alias,
> and no Concept identity passes through it, and the `"None"`-fusion hazard
> ERP-C.6 measured cannot reach it. The counter payload is deliberately two
> closed enums and nothing else: no endpoint, no warrant text, no note path.
>
> **Obligations discharged for other tasks.** `runtime/telemetry.py:52` carried
> a `hasattr(schemas, "validate_edge_write_event")` guard and
> `tests/test_telemetry_events.py:294` pinned `not hasattr(...)`, both naming
> ERP-D.6 as their owner; the guard is now a plain dispatch on
> `EDGE_WRITE_EVENT_SCHEMA` and the test asserts the live routing.
> `engine/dashboard.py:68` already read this stream
> (`_telemetry_group_counts(vault, "edge-write.v1", "relation_type")`) against
> hand-inserted rows — it now has a real producer, and its query is unchanged.
> It and `edge_write_counts` are two readers of one stream (escape class 10);
> they are tested against different producers, hand-inserted rows there and
> `curate_note_link`/`confirm-tension` here, so neither inherits the other's
> claim.
>
> **Goldens did not move** — as the manifest note predicted, `edge-write.v1`
> writes only `telemetry_events`, which is not hash-chained and not hashed by
> the floor goldens. `git status tests/fixtures/floor/goldens` is empty.
>
> **Mutation testing: 37 mutants, 37 killed, 0 survivors.** Both directions at
> every roster and enum boundary (invert, delete, narrow to `LINK_RELATIONS`,
> narrow to `SUPPORT_RELATIONS`), the closed-field-set and required-field gates,
> both `_string_field` normalizations, the returned event's shape (drop a field,
> swap the two), the schema id spelling, both telemetry dispatch arms, the
> authority gate, all four clauses of the counter query (`WHERE`, `GROUP BY`,
> the `json_extract` path, `COUNT(*)`), all three forms of the
> `if changed or warrant:` trigger, and both seams' `relation_type`/`write_path`
> arguments including cross-mislabelling. The `changed or warrant` mutants are
> the ones the printed test could not have killed: it exercised only
> `changed=True, warrant=""`, so `if changed:` would have survived it.

**Files:**
- Modify: `src/memoria_vault/engine/empirical_events.py` (`EDGE_WRITE_EVENT_SCHEMA` beside `READ_EVENT_SCHEMA`, the two constants beside `READ_REQUIRED_FIELDS`, `validate_edge_write_event` after `validate_read_event`)
- Modify: `src/memoria_vault/runtime/operations.py` (`emit_edge_write_event` + `edge_write_counts` after `emit_disposition_event`)
- Modify: `src/memoria_vault/runtime/telemetry.py` (`_validated`: the `hasattr` guard becomes a plain dispatch arm)
- Modify: `src/memoria_vault/runtime/knowledge.py` (`curate_note_link`, emission after the journal event)
- Modify: `src/memoria_vault/runtime/integrity.py` (`_confirm_tension_edge`, emission after the insert)
- Modify: `tests/test_empirical_events.py`, `tests/test_knowledge.py`, `tests/test_telemetry_events.py`, `tests/test_integrity_surface_tensions.py` (append)

**Interfaces:**
- Consumes: the I1 skeleton server-side event shape (`validate_disposition_event` / `validate_read_event`, `engine/empirical_events.py:148-184`: closed field set, `schema` stamped by the emitter); **I1 full-wiring slice 1:** `record_telemetry_event(vault, event_type, payload) -> str` (`runtime/telemetry.py`) + the `telemetry_events` table (v19); **ERP-A:** `edges.EDGE_RELATIONS` (the seven-relation roster) as the `relation_type` enum; Task ERP-D.5's `warrant` param (emission point).
- Produces: `empirical_events.EDGE_WRITE_EVENT_SCHEMA = "edge-write.v1"`; `empirical_events.validate_edge_write_event(payload: dict) -> dict` (required: `relation_type` ∈ `EDGE_RELATIONS`, `write_path` ∈ {"curate-note-link", "insert-concept-edge"}); `operations.emit_edge_write_event(vault, *, relation_type: str, write_path: str, context) -> dict`; `operations.edge_write_counts(vault) -> dict[str, int]` (the beta.2 touch-budget gate's input, EDGES section 4 instrumentation line); both write/read the `telemetry_events` table — no journal event, no golden drift. **Constraint on ERP-B:** its `confirm-tension` / `insert_concept_edge` write path must call `emit_edge_write_event(..., write_path="insert-concept-edge")` — record this in the assembled plan if ERP-B's tasks are already frozen.

**Steps:**

- [x] Write the failing validator tests — append to `tests/test_empirical_events.py`:

```python
def test_edge_write_event_accepts_roster_relation() -> None:
    from memoria_vault.engine.empirical_events import validate_edge_write_event

    assert validate_edge_write_event(
        {"relation_type": "warrant", "write_path": "curate-note-link"}
    ) == {"relation_type": "warrant", "write_path": "curate-note-link"}


def test_edge_write_event_rejects_off_roster_relation_and_unknown_path() -> None:
    from memoria_vault.engine.empirical_events import validate_edge_write_event

    with pytest.raises(ValueError, match="relation_type must be one of"):
        validate_edge_write_event(
            {"relation_type": "backing", "write_path": "curate-note-link"}
        )
    with pytest.raises(ValueError, match="write_path must be one of"):
        validate_edge_write_event({"relation_type": "supports", "write_path": "vim"})
    with pytest.raises(ValueError, match="missing required fields"):
        validate_edge_write_event({"relation_type": "supports"})
```

  And the failing counter test — append to `tests/test_knowledge.py`:

```python
def test_curate_note_link_counts_edge_writes_per_relation_type(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    _md(
        vault / "notes/source.md",
        "type: note\ncheck_status: checked\ntitle: Source\nstatus: accepted\n",
    )
    _md(
        vault / "notes/target.md",
        "type: note\ncheck_status: checked\ntitle: Target\nstatus: accepted\n",
    )

    curate_note_link(vault, "source", "supports", "target", actor="pi", machine="curator")
    # Idempotent repeat: unchanged link writes no second counter event.
    curate_note_link(vault, "source", "supports", "target", actor="pi", machine="curator")

    from memoria_vault.runtime.operations import edge_write_counts

    assert edge_write_counts(vault) == {"supports": 1}
```

- [x] Run to verify they fail:
  `python -m pytest tests/test_empirical_events.py::test_edge_write_event_accepts_roster_relation tests/test_empirical_events.py::test_edge_write_event_rejects_off_roster_relation_and_unknown_path tests/test_knowledge.py::test_curate_note_link_counts_edge_writes_per_relation_type -v`
  Expected: `ImportError: cannot import name 'validate_edge_write_event'` / `cannot import name 'edge_write_counts'`.

- [x] Write minimal implementation. (1) `engine/empirical_events.py` — beside line 14 add:

```python
EDGE_WRITE_EVENT_SCHEMA = "edge-write.v1"
```

  beside `READ_REQUIRED_FIELDS` (line 101) add:

```python
EDGE_WRITE_REQUIRED_FIELDS = frozenset({"relation_type", "write_path"})
EDGE_WRITE_PATHS = frozenset({"curate-note-link", "insert-concept-edge"})
```

  and after `validate_read_event` (line 185) add:

```python
def validate_edge_write_event(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a normalized per-relation-type edge-write event or raise ``ValueError``."""
    from memoria_vault.runtime.subsystems.lib.edges import EDGE_RELATIONS

    if not isinstance(payload, dict):
        raise ValueError("edge-write event payload must be an object")
    unknown = sorted(set(payload) - EDGE_WRITE_REQUIRED_FIELDS)
    if unknown:
        raise ValueError(f"edge-write event contains unsupported fields: {', '.join(unknown)}")
    missing = sorted(field for field in EDGE_WRITE_REQUIRED_FIELDS if _missing(payload.get(field)))
    if missing:
        raise ValueError(f"edge-write event missing required fields: {', '.join(missing)}")
    relation_type = _string_field("relation_type", payload["relation_type"])
    if relation_type not in EDGE_RELATIONS:
        raise ValueError(f"relation_type must be one of: {', '.join(sorted(EDGE_RELATIONS))}")
    write_path = _string_field("write_path", payload["write_path"])
    if write_path not in EDGE_WRITE_PATHS:
        raise ValueError(f"write_path must be one of: {', '.join(sorted(EDGE_WRITE_PATHS))}")
    return {"relation_type": relation_type, "write_path": write_path}
```

  (2) `runtime/operations.py` — after `emit_disposition_event` (line 164) add:

```python
def emit_edge_write_event(
    vault: Path,
    *,
    relation_type: str,
    write_path: str,
    context: OperationContext,
) -> dict[str, Any]:
    """Record one per-relation-type edge-write counter row in telemetry (I1 touch-budget input)."""
    from memoria_vault.engine.empirical_events import (
        EDGE_WRITE_EVENT_SCHEMA,
        validate_edge_write_event,
    )
    from memoria_vault.runtime.telemetry import record_telemetry_event

    event = validate_edge_write_event(
        {"relation_type": relation_type, "write_path": write_path}
    )
    event_id = record_telemetry_event(vault, EDGE_WRITE_EVENT_SCHEMA, event)
    return {"event_id": event_id, **event}


def edge_write_counts(vault: Path) -> dict[str, int]:
    """Return telemetry edge-write counts per relation type (beta.2 touch-budget gate input)."""
    with state.connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT json_extract(payload_json, '$.relation_type') AS relation_type,
                   COUNT(*) AS n
            FROM telemetry_events
            WHERE event_type = 'edge-write.v1'
            GROUP BY relation_type
            ORDER BY relation_type
            """
        ).fetchall()
    return {str(row["relation_type"]): int(row["n"]) for row in rows}
```

  (3) `runtime/knowledge.py` `curate_note_link` — after the journal event append (line 403) and before `commit_writer_changes`:

```python
    if changed or warrant:
        from memoria_vault.runtime.operations import emit_edge_write_event

        emit_edge_write_event(
            vault, relation_type=link_type, write_path="curate-note-link", context=context
        )
```

- [x] Run to verify all pass:
  `python -m pytest tests/test_empirical_events.py tests/test_knowledge.py -v`

- [ ] Regenerate floor goldens if drifted (manifest note at top), run the full gate once for the section (`python scripts/verify`), and commit. *Gate run green 2026-08-02; goldens did not drift, so drop them from the `git add` and add `src/memoria_vault/runtime/telemetry.py`, `src/memoria_vault/runtime/integrity.py`, `tests/test_telemetry_events.py` and `tests/test_integrity_surface_tensions.py` per the amendment's Files list. Commit step left for the orchestrator.*
  `git add src/memoria_vault/engine/empirical_events.py src/memoria_vault/runtime/operations.py src/memoria_vault/runtime/knowledge.py tests/test_empirical_events.py tests/test_knowledge.py tests/fixtures/floor/goldens`
  Message: `feat(instrumentation): edge-write.v1 per-relation-type counters on curate/insert paths (EDGES section 4 instrumentation)` ending with
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`
