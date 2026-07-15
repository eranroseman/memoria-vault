# Alpha.22 Substrate & Trust Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the schema/graph substrate (G1 migrations, G2 live concept edges, S1 hygiene), the full #1293 evidence-set/grounds contract (spec §12 slices 1–8), and model-call cost telemetry — everything that must precede a real corpus.

**Architecture:** G1 adds the minimal numbered-migration mechanism every later schema change rides; G2S1 brings the dead `concept_edges` join point to life and reshapes it promotion-ready; S12/S35/S68 implement the merged contract spec `docs/superpowers/specs/2026-07-14-evidence-set-grounds-contract-design.md` (rename sweep, marker grammar v2, unified R1–R4 derivation, transitive completeness with fail-closed cycles, disposition content-binding, staleness findings, journal mint events, docs); COST implements `docs/superpowers/specs/2026-07-15-model-call-cost-telemetry-design.md`.

**Tech Stack:** Python 3 / SQLite / pytest; `pydantic-ai-slim>=2.0` (already pinned; `genai-prices` transitive — no new dependencies).

## Global Constraints

- Correctness gate: `python scripts/verify`; PR + `verify`/`gitleaks`; squash merge; explicit-path staging only; disposable vaults only.
- Schema-before-corpus: every reshape here must land before any bulk import (consolidation §8).
- All line refs verified against main @ `d85d8799`; re-anchor by quoted context strings as earlier tasks shift lines.

## Cross-section contracts (BINDING — resolve seam assumptions)

1. **`MIGRATIONS` shape is G1's definition** (G1.1 Produces): `state.MIGRATIONS: dict[int, tuple[int, list[str | Callable[[sqlite3.Connection], None]]]]` — key = from_version, value = `(from_version + 1, ordered steps)`; applied sequentially in `_init` BEFORE `executescript(_schema_sql())`, each step list in one explicit `BEGIN`/`COMMIT` (no `with conn:`), `user_version` bumped per step; unregistered version (incl. future) raises. G2S1.2/.3 and S12.2 adapt their migration entries to THIS shape (their sections assumed variants; the mechanics are otherwise unchanged).
2. **Schema-version allocation (serialized):** G1 ships `MIGRATIONS` empty, `SCHEMA_VERSION` stays 12 → G2S1.2 takes 12→13 (edge_id/attributes) → G2S1.3 takes 13→14 (reverse indexes) → S12.2 takes **14→15** (purpose enum; renumber its written 13→14 accordingly, body unchanged) — G3/ULID work starts at 16. Each schema-touching task updates, in the same commit: its `MIGRATIONS` entry, the `schema.sql` DDL + trailing `PRAGMA user_version`, `SCHEMA_VERSION` in state.py, and the version-pinned tests (`tests/test_schema_version.py:14-17`, `tests/test_schema_v10.py:39-41`, `tests/test_query_substrate.py:31`).
3. **Closure helper:** S35.3's Produces additionally includes `state.evidence_item_closure(rows_by_id: Mapping[str, Mapping[str, Any]], evidence_id: str) -> list[tuple[str, tuple[str, ...]]]` — (item, path) pairs for non-set items reachable through nested sets, path = tuple of nested ev-ids (empty = direct), cycle-safe, unknown set refs yield nothing. This is the exact interface S68.2 consumes; it is a mechanical exposure of S35.3's DFS reachability.
4. **Execution order:** G1 → G2S1.1–.4 → S12.1–.7 → S35.1–.4 → S68.1–.6; COST.1–.5 is independent and may run any time EXCEPT COST.4 must not run concurrently with S68.3 (both regenerate journal-hashed floor goldens — land sequentially). G2S1.5 (graph-substrate design gate) may run in parallel with anything.
5. **Removed symbols** (S35 manifest) no task may reference after their removal: `_derived_evidence_type`, `_draft_evidence_type`, `_evidence_items_resolve`, `_disposed_evidence_ids`.

---
## G1 · Migration machinery

Consolidation spec §2 G1: minimal ALTER path so `state._init` stops hard-failing on any
on-disk `user_version` it can upgrade, plus the numbered migrations rule. Today
`_init` (src/memoria_vault/runtime/state.py:2406-2413) raises `RuntimeError` on any
`user_version` not in `{0, SCHEMA_VERSION}`; `SCHEMA_VERSION = 12` (state.py:53) and
`schema.sql` ends with `PRAGMA user_version = 12;` (schema.sql:378). G1 blocks every
schema-touching package (G2–G5, S1) — those packages ship their schema changes as
`MIGRATIONS` entries once this lands.

Design (smallest honest mechanism): a module-level `MIGRATIONS` registry,
`{from_version: (to_version, [SQL statement or callable(conn)])}`, applied sequentially
inside `_init` before the idempotent `executescript(_schema_sql())`. Each step must
target exactly `from_version + 1` (the numbered rule, enforced in code), runs in its own
explicit transaction, and bumps `user_version` as it commits. Any version with no
registered path — including versions newer than the installed package — still fails
closed with the existing `RuntimeError`. `MIGRATIONS` ships empty; the registry is
exercised by test-only entries via `monkeypatch`.

Assumes the plan-level worktree/branch for PLAN 22 already exists (AGENTS.md session
isolation); commits below stage explicit paths only.

### Task G1.1: MIGRATIONS registry + sequential application in `_init`

**Files:**
- Modify: `src/memoria_vault/runtime/state.py` — line 18 (`from collections.abc import Iterable`), line 53 (`SCHEMA_VERSION = 12`), lines 2406-2413 (`def _init`)
- Test: `tests/test_runtime_state.py` (already registered in `tests/conftest.py` `TEST_LEVELS` at level `runtime`, line 96 — no conftest change needed)

**Interfaces:**
- Consumes: `state.connect(vault: Path) -> sqlite3.Connection` (state.py:472, calls `_init`), `state._schema_sql() -> str` (state.py:484), `state.SCHEMA_VERSION: int` (state.py:53), `state.DB_REL: str` (state.py:51)
- Produces: `MIGRATIONS: dict[int, tuple[int, list[str | Callable[[sqlite3.Connection], None]]]]` — module-level in `memoria_vault.runtime.state`, empty in production; key is the on-disk `user_version` a step upgrades *from*, value is `(from_version + 1, ordered steps)`; a `str` step is executed via `conn.execute`, a callable step is invoked as `step(conn)`.
- Produces: `_init(conn: sqlite3.Connection) -> None` — unchanged signature; new contract: applies registered migrations sequentially until `user_version` reaches `SCHEMA_VERSION`, raises `RuntimeError("unsupported Memoria DB schema version: {v}")` for any version with no registered path, raises `RuntimeError` mentioning "must target" for a non-sequential `to_version`, then applies the idempotent `schema.sql`.

**Steps:**

- [ ] Write the failing happy-path test. Append to `tests/test_runtime_state.py`, directly after `test_sqlite_schema_rejects_legacy_user_version` (its `state.connect(tmp_path)` call ends at line 138):

  ```python
  def test_sqlite_migrations_apply_registered_steps_in_order(
      tmp_path: Path, monkeypatch: pytest.MonkeyPatch
  ) -> None:
      db = tmp_path / state.DB_REL
      db.parent.mkdir(parents=True)
      with sqlite3.connect(db) as conn:
          conn.execute(f"PRAGMA user_version = {state.SCHEMA_VERSION - 2}")

      seen_versions: list[int] = []

      def probe(conn: sqlite3.Connection) -> None:
          seen_versions.append(int(conn.execute("PRAGMA user_version").fetchone()[0]))

      monkeypatch.setattr(
          state,
          "MIGRATIONS",
          {
              state.SCHEMA_VERSION - 2: (
                  state.SCHEMA_VERSION - 1,
                  ["CREATE TABLE migration_probe (step INTEGER PRIMARY KEY)"],
              ),
              state.SCHEMA_VERSION - 1: (state.SCHEMA_VERSION, [probe]),
          },
      )

      with state.connect(tmp_path) as conn:
          assert conn.execute("PRAGMA user_version").fetchone()[0] == state.SCHEMA_VERSION
          assert conn.execute(
              "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'migration_probe'"
          ).fetchone()

      # The callable step ran after the first step's version bump committed.
      assert seen_versions == [state.SCHEMA_VERSION - 1]
  ```

- [ ] Run it and verify it fails:

  ```
  python -m pytest tests/test_runtime_state.py::test_sqlite_migrations_apply_registered_steps_in_order -v
  ```

  Expected failure: `AttributeError: <module 'memoria_vault.runtime.state' ...> has no attribute 'MIGRATIONS'` (raised by `monkeypatch.setattr`).

- [ ] Write the minimal implementation. Three edits to `src/memoria_vault/runtime/state.py`:

  1. Line 18 — extend the existing import:

  ```python
  from collections.abc import Callable, Iterable
  ```

  2. After `SCHEMA_VERSION = 12` (line 53) — add the registry:

  ```python
  # Numbered migrations: each entry upgrades an on-disk DB by exactly one version
  # step, {from_version: (from_version + 1, [SQL statement or callable(conn)])}.
  # _init refuses (fail-closed) any user_version with no registered path here.
  MIGRATIONS: dict[int, tuple[int, list[str | Callable[[sqlite3.Connection], None]]]] = {}
  ```

  3. Replace the body of `_init` (currently lines 2406-2413):

  ```python
  def _init(conn: sqlite3.Connection) -> None:
      current = int(conn.execute("PRAGMA user_version").fetchone()[0])
      while current not in {0, SCHEMA_VERSION}:
          if current not in MIGRATIONS:
              raise RuntimeError(f"unsupported Memoria DB schema version: {current}")
          to_version, steps = MIGRATIONS[current]
          if to_version != current + 1:
              raise RuntimeError(
                  f"migration from schema version {current} must target {current + 1}, "
                  f"not {to_version}"
              )
          for step in steps:
              if callable(step):
                  step(conn)
              else:
                  conn.execute(step)
          conn.execute(f"PRAGMA user_version = {to_version}")
          current = to_version
      conn.executescript(_schema_sql())
      applied = int(conn.execute("PRAGMA user_version").fetchone()[0])
      if applied != SCHEMA_VERSION:
          raise RuntimeError(f"Memoria DB schema initialization failed: {applied}")
  ```

  (Per-step transactions arrive in Task G1.2 — this step is deliberately the smallest
  green.)

- [ ] Run the new test plus the existing schema tests and verify they pass:

  ```
  python -m pytest tests/test_runtime_state.py::test_sqlite_migrations_apply_registered_steps_in_order tests/test_runtime_state.py::test_sqlite_schema_uses_wal_and_user_version tests/test_runtime_state.py::test_sqlite_schema_rejects_legacy_user_version -v
  ```

- [ ] Write the failing numbered-rule test. Append to `tests/test_runtime_state.py` after the test added above:

  ```python
  def test_sqlite_migrations_refuse_non_sequential_target(
      tmp_path: Path, monkeypatch: pytest.MonkeyPatch
  ) -> None:
      db = tmp_path / state.DB_REL
      db.parent.mkdir(parents=True)
      with sqlite3.connect(db) as conn:
          conn.execute(f"PRAGMA user_version = {state.SCHEMA_VERSION - 2}")

      monkeypatch.setattr(
          state,
          "MIGRATIONS",
          {state.SCHEMA_VERSION - 2: (state.SCHEMA_VERSION, [])},
      )

      with pytest.raises(RuntimeError, match="must target"):
          state.connect(tmp_path)
  ```

  Note: if the numbered-rule guard was already written in the implementation step above,
  this test passes immediately — run it either way; the red run only exists to prove the
  guard is load-bearing. If it passes on first run, delete the guard temporarily to
  watch it fail (`Failed: DID NOT RAISE`), then restore the guard.

- [ ] Run it and verify it passes:

  ```
  python -m pytest tests/test_runtime_state.py::test_sqlite_migrations_refuse_non_sequential_target -v
  ```

- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/state.py tests/test_runtime_state.py
  git commit -m "feat(state): numbered MIGRATIONS registry applied sequentially in _init

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

### Task G1.2: Fail-closed guarantees — per-step transaction rollback and future-version refusal

**Files:**
- Modify: `src/memoria_vault/runtime/state.py` — the `_init` migration loop written in Task G1.1 (the `for step in steps` block through the `PRAGMA user_version` bump)
- Test: `tests/test_runtime_state.py`

**Interfaces:**
- Consumes: `state.MIGRATIONS`, `state._init` (Task G1.1), `state.connect`, `state.DB_REL`, `state.SCHEMA_VERSION`
- Produces: hardened `_init` contract — each migration step list runs inside one explicit `BEGIN`/`COMMIT`; on any step failure the transaction is rolled back (no partial DDL, `user_version` unchanged) and the original exception propagates; a `user_version` greater than `SCHEMA_VERSION` raises `RuntimeError("unsupported Memoria DB schema version: {v}")`. No signature changes.

**Steps:**

- [ ] Write the failing rollback test. Append to `tests/test_runtime_state.py`:

  ```python
  def test_sqlite_migration_step_failure_rolls_back_and_keeps_version(
      tmp_path: Path, monkeypatch: pytest.MonkeyPatch
  ) -> None:
      db = tmp_path / state.DB_REL
      db.parent.mkdir(parents=True)
      with sqlite3.connect(db) as conn:
          conn.execute(f"PRAGMA user_version = {state.SCHEMA_VERSION - 1}")

      monkeypatch.setattr(
          state,
          "MIGRATIONS",
          {
              state.SCHEMA_VERSION - 1: (
                  state.SCHEMA_VERSION,
                  [
                      "CREATE TABLE migration_probe (step INTEGER PRIMARY KEY)",
                      "INSERT INTO missing_table VALUES (1)",
                  ],
              )
          },
      )

      with pytest.raises(sqlite3.OperationalError, match="missing_table"):
          state.connect(tmp_path)

      with sqlite3.connect(db) as conn:
          assert (
              conn.execute("PRAGMA user_version").fetchone()[0] == state.SCHEMA_VERSION - 1
          )
          assert not conn.execute(
              "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'migration_probe'"
          ).fetchone()
  ```

- [ ] Run it and verify it fails:

  ```
  python -m pytest tests/test_runtime_state.py::test_sqlite_migration_step_failure_rolls_back_and_keeps_version -v
  ```

  Expected failure: the second assertion — `migration_probe` exists, because the
  `CREATE TABLE` autocommitted before the failing `INSERT`.

- [ ] Write the minimal implementation. In `_init` (Task G1.1 version), wrap the step
  loop and version bump in an explicit transaction — replace:

  ```python
          for step in steps:
              if callable(step):
                  step(conn)
              else:
                  conn.execute(step)
          conn.execute(f"PRAGMA user_version = {to_version}")
          current = to_version
  ```

  with:

  ```python
          conn.execute("BEGIN")
          try:
              for step in steps:
                  if callable(step):
                      step(conn)
                  else:
                      conn.execute(step)
              conn.execute(f"PRAGMA user_version = {to_version}")
          except BaseException:
              conn.execute("ROLLBACK")
              raise
          conn.execute("COMMIT")
          current = to_version
  ```

  (`with conn:` cannot be used here — the `_ClosingConnection` factory, state.py:464,
  overrides `__exit__` to close the connection.)

- [ ] Run it and verify it passes:

  ```
  python -m pytest tests/test_runtime_state.py::test_sqlite_migration_step_failure_rolls_back_and_keeps_version tests/test_runtime_state.py::test_sqlite_migrations_apply_registered_steps_in_order -v
  ```

- [ ] Write the future-version pin. Append to `tests/test_runtime_state.py`:

  ```python
  def test_sqlite_schema_rejects_future_user_version(tmp_path: Path) -> None:
      db = tmp_path / state.DB_REL
      db.parent.mkdir(parents=True)
      with sqlite3.connect(db) as conn:
          conn.execute(f"PRAGMA user_version = {state.SCHEMA_VERSION + 1}")

      with pytest.raises(
          RuntimeError,
          match=f"unsupported Memoria DB schema version: {state.SCHEMA_VERSION + 1}",
      ):
          state.connect(tmp_path)
  ```

- [ ] Run it and verify it passes on first run — this is a deliberate behavior pin, not
  a red-green cycle: it fixes the guarantee that a DB written by a *newer* Memoria
  (no registered downgrade path) is never touched, so future refactors of the loop
  cannot silently weaken it. Also re-run the pre-existing legacy-version test, which
  must keep passing unchanged:

  ```
  python -m pytest tests/test_runtime_state.py::test_sqlite_schema_rejects_future_user_version tests/test_runtime_state.py::test_sqlite_schema_rejects_legacy_user_version -v
  ```

- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/state.py tests/test_runtime_state.py
  git commit -m "fix(state): per-step migration transactions; pin fail-closed on future schema versions

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

### Task G1.3: Document the numbered migrations rule in the published reference

**Files:**
- Modify: `docs/reference/system/on-disk-layout.md` — insert after line 86 (end of the `event_log` paragraph, inside the `## \`.memoria/\` - the runtime tooling layer` section that documents `memoria.sqlite`)
- Test: `python scripts/verify` (docs have no dedicated test; the one gate covers lint/link/spell checks)

Placement note: the task brief said "under `docs/reference/data-model/`", but no
data-model page covers the SQLite runtime schema (that directory documents markdown
frontmatter schemas, document types, vocabulary, links, glossary, OKF). The published
page that documents `memoria.sqlite` is `docs/reference/system/on-disk-layout.md`, so
the subsection lands there — flagged as a deviation for the plan assembler; move it
only if a dedicated data-model DB-schema page is created by another package.

**Interfaces:**
- Consumes: the Task G1.1/G1.2 `_init` + `MIGRATIONS` contract (the doc must describe exactly that behavior, nothing more)
- Produces: published subsection `### Schema versioning: numbered migrations` in `docs/reference/system/on-disk-layout.md` — the citable rule every schema-touching package (G2–G5, S1) follows

**Steps:**

- [ ] Insert the subsection. In `docs/reference/system/on-disk-layout.md`, after the
  paragraph ending `...and re-emits any missing export rows.` (line 86) and before the
  `Backups live outside this tree.` paragraph (line 88), add:

  ```markdown
  ### Schema versioning: numbered migrations

  `memoria.sqlite` carries its schema version in SQLite `PRAGMA user_version`
  (`SCHEMA_VERSION` in `memoria_vault.runtime.state`; the full schema is
  `memoria_vault/runtime/schema.sql`). Schema changes follow the numbered
  migrations rule:

  - Every schema change bumps `SCHEMA_VERSION` by exactly one and updates the
    `PRAGMA user_version` line at the end of `schema.sql` to match.
  - The same change registers one entry in `state.MIGRATIONS` —
    `{from_version: (from_version + 1, [SQL statements or callables])}` — that
    upgrades an existing database by exactly that one step. Multi-version jumps
    are refused.
  - On connect, registered migrations run sequentially, each step list in its
    own transaction, with `user_version` bumped as each step commits; a failed
    step rolls back cleanly and leaves the version unchanged.
  - A database whose version has no registered path — including one written by
    a newer Memoria — fails closed with an error instead of being touched.
  ```

- [ ] Run the gate and verify it passes (this also closes out G1.1/G1.2 code changes
  against the full roster):

  ```
  python scripts/verify
  ```

- [ ] Commit:

  ```
  git add docs/reference/system/on-disk-layout.md
  git commit -m "docs(reference): numbered migrations rule for the runtime SQLite schema

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```
# PLAN 22 — Package G2S1: graph substrate (G2) + schema hygiene (S1)

Scope: consolidation §2 G2 (`concept_edges-fill-and-persist`, `concept_edges-reshape`,
`reverse-traversal-indexes`) + the S1 units that are pure mechanical deletions today,
plus one process gate for everything in G2–G5/S1 that has no ratified mechanical spec.

## Verified current state (read 2026-07-15)

- `indexing._concept_edges` (src/memoria_vault/runtime/indexing.py:133-136) is a stub
  returning `[]`; `state.replace_concept_edges` (state.py:2026-2052) opens with
  `DELETE FROM concept_edges` — the table is wiped and refilled with nothing on every
  reindex. Confirmed exactly as the consolidation describes.
- `concept_edges` table (schema.sql:240-250): columns `source_concept_id`,
  `relation_type` (CHECK in supports/contradicts/extends/tension), `target_concept_id`,
  `check_status`, `source_path`, `updated_at`; PK is the
  (source_concept_id, relation_type, target_concept_id) triple. **No `edge_id`, no
  attributes column, no index on `target_concept_id`.**
- `work_graph_edges` (schema.sql:171-186): PK (work_id, relation_type, target_id);
  **no index on `target_id`.** The consolidation's named index columns are real:
  `concept_edges.target_concept_id` and `work_graph_edges.target_id`.
- The only shipped links parser is `schema.py` `_check_links`
  (src/memoria_vault/runtime/subsystems/lib/schema.py:135-158) with the roster
  `LINK_RELATIONS = frozenset({"supports", "contradicts", "extends"})` (line 39).
  Its wikilink normalization (`[[target|alias#anchor]]` → `target`) lives inline at
  lines 148-150. G2's single-edge-module doctrine: this is the parser to reuse.
- `links:` contract (docs/reference/data-model/frontmatter.md): "a map from
  `supports`, `contradicts`, or `extends` to lists of local Concept targets";
  required on most Concept types, empty map allowed.
- `state._init` (state.py:2406-2413) hard-fails on `user_version not in {0, 12}`;
  `SCHEMA_VERSION = 12` (state.py:53); schema.sql ends with `PRAGMA user_version = 12`
  (schema.sql:378). Migration machinery is G1's deliverable (this plan's G1 section).
- `state.concept_edges` (state.py:2055-2076) has **zero callers in src/** — SELECT
  shape changes are safe.
- Nothing writes `relation_type = 'tension'` yet (only `_concept_edge_relation`,
  state.py:3420-3424, accepts it). Pre-corpus, existing vaults have empty
  `concept_edges` — migration backfill is a no-op in practice.

## S1 already-shipped ledger (verified by grep — record, do not re-plan)

- **`delete-survival-copies` — already shipped.** `citations`, `evidence_set`,
  `citekey`, `project` are `forbidden:` (retired-field rejection) in
  note.yaml:46, digest.yaml:16, hub.yaml:17 under
  `src/memoria_vault/product/workspace_seed/.memoria/schemas/types/`. No runtime
  writer emits them to frontmatter (enrichment.py:975's `citations` is catalog
  metadata, not a frontmatter survival copy). No task.
- **`delete-dead-migration` — already shipped.** `_migrate_v4_to_v5` does not exist
  anywhere under src/; tests/test_schema_version.py::test_source_has_no_private_migration_helpers
  already guards the regression. No task.
- **`prune-dead-schema` — still live, task below.** `UNIVERSAL_LIFECYCLE`
  (schema.py:37), `required_any` handling (schema.py:187-189), and
  `promotion_gate`/`promoted_at` handling (schema.py:197-199) survive in code while
  **no type yaml uses any of them** (verified across all six
  `workspace_seed/.memoria/schemas/types/*.yaml`; only note.yaml declares `enums:`,
  and only mode/question_status/certainty/item_type). `VOCABULARY_FIELDS['source']`
  and `enums.lifecycle`/`enums.check_status` are already gone.
- Incidental observations for the process gate: note.yaml `mode` enum is already the
  4-value roster (claim/question/definition/work), `certainty` already carries
  `hypothesized`, `required_when:` grammar already ships, and the type roster is
  already down to 6 files — several S1 units the consolidation marks pending appear
  partially or fully shipped by the alpha ponytail passes. The G2S1.5 brainstorm must
  reconcile the ledger instead of inventing work.

## Consumed from G1 (this plan's G1 section — assumption other sections must honor)

- `state.MIGRATIONS: dict[int, str]` — target `user_version` → SQL script. `_init`
  applies `MIGRATIONS[v]` via `conn.executescript` for each `v` in
  `range(current + 1, SCHEMA_VERSION + 1)` when `0 < current < SCHEMA_VERSION`, then
  runs `conn.executescript(_schema_sql())` (whose trailing
  `PRAGMA user_version = <SCHEMA_VERSION>` stamps the final version). Migration
  scripts therefore do **not** contain their own `user_version` pragma. If G1's landed
  shape differs (scripts self-stamp, different dict name), adapt the two MIGRATIONS
  entries below mechanically — the ALTER/CREATE INDEX statements are the contract.
- **G2S1 claims schema versions 13 and 14.** G1 leaves `SCHEMA_VERSION` at 12 with an
  empty ladder. Any other package adding a migration must take 15+.
- Ordering: G2S1.2 and G2S1.3 depend on G1's machinery being merged. G2S1.1, G2S1.4,
  and G2S1.5 have no dependency on G1 and can land first.

Version-pinned tests that G2S1.2/G2S1.3 must bump (all three verified current):
tests/test_schema_version.py:14-17, tests/test_schema_v10.py:39-41,
tests/test_query_substrate.py:31.

---

### Task G2S1.1: concept_edges-fill-and-persist

Derive `concept_edges` rows from checked concepts' `links:` frontmatter using the
existing schema.py parser (single-edge-module doctrine: one owner of normalization),
and replace the wipe-on-reindex with upsert-and-prune that never touches durable
`tension` rows.

**Files:**
- Modify: `src/memoria_vault/runtime/subsystems/lib/schema.py` (add
  `normalize_link_target` + `parse_links` after `_check_links`, refactor
  `_check_links` lines 148-150 to share the normalizer)
- Modify: `src/memoria_vault/runtime/indexing.py:101-136` (`_passage_row` carries the
  parsed `links` map; `_concept_edges` stub becomes the derivation; import added)
- Modify: `src/memoria_vault/runtime/state.py:2026-2052` (`replace_concept_edges`
  upsert-and-prune)
- Test: `tests/test_query_substrate.py` (contract level; file already registered in
  tests/conftest.py TEST_LEVELS — no conftest change)

**Interfaces:**
- Consumes: `schema.LINK_RELATIONS` (schema.py:39); passage-row dicts from
  `indexing._passage_rows` (named-key access in `state.replace_indexed_passages`,
  state.py:1891-1937, tolerates the extra `links` key — verified);
  `tests.helpers.write_checked_concept(workspace, rel, frontmatter, *, body=...)`,
  `copy_memoria_dirs`, `call_with_context`.
- Produces:
  - `schema.normalize_link_target(target: str) -> str` — strips `[[...]]`, `|alias`,
    `#anchor`; returns `""` for junk.
  - `schema.parse_links(links: object) -> list[tuple[str, str]]` — `(relation,
    normalized_target)` pairs; skips non-roster relations and non-list values.
  - `state.replace_concept_edges(vault: Path, rows: Iterable[dict[str, Any]], *,
    paths: Iterable[str] | None = None) -> dict[str, int]` — upserts mirror rows,
    prunes stale non-tension rows (scoped to `paths` when given), **never deletes
    `relation_type = 'tension'` rows**. Returns `{"deleted": int, "inserted": int}`.
  - Edge-row dict contract (consumed by G2S1.2 and by any R1 `incremental-indexing`
    task): keys `source_concept_id`, `relation_type`, `target_concept_id`,
    `check_status`, `source_path`. IDs are vault-relative `.md` paths
    (`notes/alpha.md`), matching `passages.concept_id`'s id-space.

**Steps:**

- [ ] Write the failing test at the end of `tests/test_query_substrate.py`:

  ```python
  def test_concept_edges_mirror_links_and_persist_across_reindex(tmp_path: Path) -> None:
      vault = tmp_path
      copy_memoria_dirs(vault, "schemas")
      write_checked_concept(
          vault,
          "notes/alpha.md",
          "type: note\ntitle: Alpha\ntags: []\n"
          'links:\n  supports: ["[[notes/beta]]"]\n  contradicts: ["[[notes/gamma|Gamma]]"]\n',
      )
      write_checked_concept(
          vault, "notes/beta.md", "type: note\ntitle: Beta\ntags: []\nlinks: {}\n"
      )

      rebuild_passage_index(vault)
      edges = state.concept_edges(vault, checked_only=True)

      assert {
          (edge["source_concept_id"], edge["relation_type"], edge["target_concept_id"])
          for edge in edges
      } == {
          ("notes/alpha.md", "supports", "notes/beta.md"),
          ("notes/alpha.md", "contradicts", "notes/gamma.md"),
      }

      with state.connect(vault) as conn:
          conn.execute(
              "INSERT INTO concept_edges("
              " source_concept_id, relation_type, target_concept_id,"
              " check_status, source_path, updated_at)"
              " VALUES ('notes/alpha.md', 'tension', 'notes/beta.md',"
              " 'checked', '', '2026-07-15T00:00:00Z')"
          )

      rebuild_passage_index(vault)
      edges = state.concept_edges(vault, checked_only=True)

      assert len(edges) == 3
      assert {edge["relation_type"] for edge in edges} == {
          "supports",
          "contradicts",
          "tension",
      }
  ```

  (Reuses the module-level `rebuild_passage_index` wrapper already defined at
  tests/test_query_substrate.py:18-19.)
- [ ] Run `python -m pytest tests/test_query_substrate.py::test_concept_edges_mirror_links_and_persist_across_reindex -v`
  — expect FAIL: `AssertionError: assert set() == {('notes/alpha.md', ...)}` (stub
  returns `[]`, so the first edge assertion sees an empty table).
- [ ] In `src/memoria_vault/runtime/subsystems/lib/schema.py`, add after
  `_check_links` (below line 158):

  ```python
  def normalize_link_target(target: str) -> str:
      """Strip wikilink braces, alias, and anchor from one links: target."""
      raw = str(target).strip()
      if raw.startswith("[[") and raw.endswith("]]"):
          raw = raw[2:-2].split("|", 1)[0].split("#", 1)[0].strip()
      return raw


  def parse_links(links: object) -> list[tuple[str, str]]:
      """(relation, normalized target) pairs from a links: frontmatter map.

      Single owner of links parsing (G2 single-edge-module): validation and
      edge derivation share the same roster and normalization.
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
  ```

- [ ] In the same file, refactor `_check_links` lines 148-150 to reuse the
  normalizer — replace

  ```python
              raw = target.strip()
              if raw.startswith("[[") and raw.endswith("]]"):
                  raw = raw[2:-2].split("|", 1)[0].split("#", 1)[0].strip()
  ```

  with

  ```python
              raw = normalize_link_target(target)
  ```

  (`normalize_link_target` must therefore be defined above `_check_links` or the
  refactor keeps the call late-bound at call time — module-level order is fine
  either way in Python; place the two new functions directly **above**
  `_check_links` for readability.)
- [ ] In `src/memoria_vault/runtime/indexing.py`, add the import (after line 11):

  ```python
  from memoria_vault.runtime.subsystems.lib.schema import parse_links
  ```

  In `_passage_row` (lines 109-130), add one key to the returned dict, after
  `"question_status": ...`:

  ```python
          "links": frontmatter.get("links") if isinstance(frontmatter.get("links"), dict) else {},
  ```

  Replace the `_concept_edges` stub (lines 133-136) with:

  ```python
  def _concept_edges(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
      """Mirror each concept's links: frontmatter into concept_edges rows."""
      edges = []
      for row in rows:
          if row.get("origin") != "file":
              continue
          for relation, target in parse_links(row.get("links")):
              edges.append(
                  {
                      "source_concept_id": row["path"],
                      "relation_type": relation,
                      "target_concept_id": target if target.endswith(".md") else f"{target}.md",
                      "check_status": row["check_status"],
                      "source_path": row["path"],
                  }
              )
      return edges
  ```

- [ ] In `src/memoria_vault/runtime/state.py`, replace `replace_concept_edges`
  (lines 2026-2052) with the upsert-and-prune form:

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
      keep = {
          (
              normalize_path(str(row["source_concept_id"])),
              _concept_edge_relation(str(row["relation_type"])),
              normalize_path(str(row["target_concept_id"])),
          )
          for row in rows
      }
      with connect(vault) as conn:
          existing = conn.execute(
              """
              SELECT source_concept_id, relation_type, target_concept_id, source_path
              FROM concept_edges
              WHERE relation_type != 'tension'
              """
          ).fetchall()
          deleted = 0
          for stale in existing:
              key = (
                  str(stale["source_concept_id"]),
                  str(stale["relation_type"]),
                  str(stale["target_concept_id"]),
              )
              if key in keep:
                  continue
              if target_paths and str(stale["source_path"]) not in target_paths:
                  continue
              conn.execute(
                  """
                  DELETE FROM concept_edges
                  WHERE source_concept_id = ? AND relation_type = ? AND target_concept_id = ?
                  """,
                  key,
              )
              deleted += 1
          for row in rows:
              conn.execute(
                  """
                  INSERT INTO concept_edges(
                      source_concept_id,
                      relation_type,
                      target_concept_id,
                      check_status,
                      source_path,
                      updated_at
                  )
                  VALUES (?, ?, ?, ?, ?, ?)
                  ON CONFLICT(source_concept_id, relation_type, target_concept_id)
                  DO UPDATE SET
                      check_status = excluded.check_status,
                      source_path = excluded.source_path,
                      updated_at = excluded.updated_at
                  """,
                  (
                      normalize_path(str(row["source_concept_id"])),
                      _concept_edge_relation(str(row["relation_type"])),
                      normalize_path(str(row["target_concept_id"])),
                      _check_status(str(row.get("check_status") or "unchecked")),
                      normalize_path(str(row.get("source_path") or "")),
                      now_iso(),
                  ),
              )
      return {"deleted": int(deleted), "inserted": len(rows)}
  ```

  (No call-site changes: `_rebuild_passage_index` at indexing.py:37 and
  `refresh_stale_passages` at indexing.py:58 both pass the full-vault row set, so
  `paths=None` full-mirror reconciliation is correct for both.)
- [ ] Run `python -m pytest tests/test_query_substrate.py::test_concept_edges_mirror_links_and_persist_across_reindex -v`
  — expect PASS.
- [ ] Run `python -m pytest tests/test_query_substrate.py tests/test_schemas.py tests/test_frontmatter_contract.py -v`
  — expect all PASS (`_check_links` refactor must not change validation behavior).
- [ ] Run `python scripts/verify` — expect PASS.
- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/subsystems/lib/schema.py src/memoria_vault/runtime/indexing.py src/memoria_vault/runtime/state.py tests/test_query_substrate.py
  git commit -m "feat(graph): mirror links frontmatter into concept_edges, stop wiping on reindex

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task G2S1.2: concept_edges-reshape — edge_id + attributes_json (migration 13)

Promotion-ready edges per the warrant-ontology-brief interim ruling (Option B): a
warrant reference can hang on an edge, so later node reification stays cheap.
`edge_id` is deterministic (hash of the triple) so it survives mirror rebuilds;
`attributes_json` is preserved on upsert conflict so durable edge attributes are not
lost to reindex. Depends on: G1 migration machinery merged; G2S1.1 merged.

**Files:**
- Modify: `src/memoria_vault/runtime/schema.sql:240-250` (concept_edges CREATE gains
  two columns + unique partial index) and `:378` (`PRAGMA user_version = 12` → `13`)
- Modify: `src/memoria_vault/runtime/state.py:53` (`SCHEMA_VERSION = 12` → `13`);
  G1's `MIGRATIONS` dict (add key 13); `replace_concept_edges` insert (as landed by
  G2S1.1); `concept_edges` SELECTs (state.py:2055-2076 pre-G2S1.1 numbering); new
  `concept_edge_id` helper next to `_concept_edge_relation` (state.py:3420)
- Modify: `tests/test_schema_version.py:14-17`, `tests/test_schema_v10.py:39-41`,
  `tests/test_query_substrate.py:31` (version pins 12 → 13)
- Test: `tests/test_query_substrate.py`

**Interfaces:**
- Consumes: `state.MIGRATIONS: dict[int, str]` (G1 section — shape assumption in the
  package header); `hashlib` (already imported, state.py:8); `state.DB_REL`.
- Produces:
  - `state.concept_edge_id(source_concept_id: str, relation_type: str,
    target_concept_id: str) -> str` — deterministic 24-hex-char id,
    `sha256(f"{source}\0{relation}\0{target}")[:24]`, stable across reindex.
  - `MIGRATIONS[13]` — SQL adding `concept_edges.edge_id` (TEXT, unique-indexed where
    nonblank — "PRIMARY-KEY-ish"; SQLite cannot ALTER in a real PK) and
    `concept_edges.attributes_json` (TEXT, default `'{}'`).
  - `state.concept_edges` rows now include `edge_id` and `attributes_json` keys
    (consumed by G4 warrant work and any R2 graph-primitive task).

**Steps:**

- [ ] Write the failing test at the end of `tests/test_query_substrate.py`:

  ```python
  def test_concept_edges_reshape_adds_edge_id_and_attributes(tmp_path: Path) -> None:
      with state.connect(tmp_path) as conn:
          columns = {row["name"] for row in conn.execute("PRAGMA table_info(concept_edges)")}
      assert {"edge_id", "attributes_json"}.issubset(columns)

      legacy = tmp_path / "legacy"
      db = legacy / state.DB_REL
      db.parent.mkdir(parents=True)
      with sqlite3.connect(db) as conn:
          conn.execute(
              "CREATE TABLE concept_edges ("
              " source_concept_id TEXT NOT NULL,"
              " relation_type TEXT NOT NULL,"
              " target_concept_id TEXT NOT NULL,"
              " check_status TEXT NOT NULL,"
              " source_path TEXT NOT NULL DEFAULT '',"
              " updated_at TEXT NOT NULL,"
              " PRIMARY KEY (source_concept_id, relation_type, target_concept_id))"
          )
          conn.execute("PRAGMA user_version = 12")
      with state.connect(legacy) as conn:
          columns = {row["name"] for row in conn.execute("PRAGMA table_info(concept_edges)")}
          version = conn.execute("PRAGMA user_version").fetchone()[0]
      assert {"edge_id", "attributes_json"}.issubset(columns)
      assert version == state.SCHEMA_VERSION

      expected = state.concept_edge_id("notes/a.md", "supports", "notes/b.md")
      assert len(expected) == 24
      assert expected == state.concept_edge_id("notes/a.md", "supports", "notes/b.md")
  ```

- [ ] Run `python -m pytest tests/test_query_substrate.py::test_concept_edges_reshape_adds_edge_id_and_attributes -v`
  — expect FAIL: `AssertionError: assert {'edge_id', 'attributes_json'}.issubset({...})`
  (fresh table lacks both columns).
- [ ] In `src/memoria_vault/runtime/schema.sql`, replace the concept_edges block
  (lines 240-250) with:

  ```sql
  CREATE TABLE IF NOT EXISTS concept_edges (
      edge_id TEXT NOT NULL DEFAULT '',
      source_concept_id TEXT NOT NULL,
      relation_type TEXT NOT NULL CHECK (
          relation_type IN ('supports', 'contradicts', 'extends', 'tension')
      ),
      target_concept_id TEXT NOT NULL,
      attributes_json TEXT NOT NULL DEFAULT '{}',
      check_status TEXT NOT NULL CHECK (check_status IN ('unchecked', 'checked', 'quarantined')),
      source_path TEXT NOT NULL DEFAULT '',
      updated_at TEXT NOT NULL,
      PRIMARY KEY (source_concept_id, relation_type, target_concept_id)
  );
  CREATE UNIQUE INDEX IF NOT EXISTS idx_concept_edges_edge_id
      ON concept_edges(edge_id) WHERE edge_id != '';
  ```

  and change the trailing pragma (line 378) to `PRAGMA user_version = 13;`.
- [ ] In `src/memoria_vault/runtime/state.py`: set `SCHEMA_VERSION = 13` (line 53);
  add to G1's `MIGRATIONS`:

  ```python
  MIGRATIONS[13] = """
  ALTER TABLE concept_edges ADD COLUMN edge_id TEXT NOT NULL DEFAULT '';
  ALTER TABLE concept_edges ADD COLUMN attributes_json TEXT NOT NULL DEFAULT '{}';
  CREATE UNIQUE INDEX IF NOT EXISTS idx_concept_edges_edge_id
      ON concept_edges(edge_id) WHERE edge_id != '';
  """
  ```

  (written as a literal `13: """...\n"""` entry inside the dict, matching G1's style);
  add next to `_concept_edge_relation` (below state.py:3424):

  ```python
  def concept_edge_id(source_concept_id: str, relation_type: str, target_concept_id: str) -> str:
      """Deterministic edge id: stable across reindex so refs can hang on an edge."""
      key = f"{source_concept_id}\0{relation_type}\0{target_concept_id}"
      return hashlib.sha256(key.encode()).hexdigest()[:24]
  ```

- [ ] Still in state.py, extend the `replace_concept_edges` insert (as landed by
  G2S1.1) to write both columns while preserving `attributes_json` on conflict:

  ```python
              source = normalize_path(str(row["source_concept_id"]))
              relation = _concept_edge_relation(str(row["relation_type"]))
              target = normalize_path(str(row["target_concept_id"]))
              conn.execute(
                  """
                  INSERT INTO concept_edges(
                      edge_id,
                      source_concept_id,
                      relation_type,
                      target_concept_id,
                      attributes_json,
                      check_status,
                      source_path,
                      updated_at
                  )
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                  ON CONFLICT(source_concept_id, relation_type, target_concept_id)
                  DO UPDATE SET
                      edge_id = excluded.edge_id,
                      check_status = excluded.check_status,
                      source_path = excluded.source_path,
                      updated_at = excluded.updated_at
                  """,
                  (
                      str(row.get("edge_id") or concept_edge_id(source, relation, target)),
                      source,
                      relation,
                      target,
                      str(row.get("attributes_json") or "{}"),
                      _check_status(str(row.get("check_status") or "unchecked")),
                      normalize_path(str(row.get("source_path") or "")),
                      now_iso(),
                  ),
              )
  ```

  (`attributes_json` deliberately absent from `DO UPDATE SET`: a reindex refreshes
  the mirror without clobbering attributes hung on the edge.)
- [ ] Add `edge_id, attributes_json` to both SELECT column lists in
  `state.concept_edges` (both branches, state.py:2060-2075 pre-task numbering).
- [ ] Bump the three version pins: tests/test_schema_version.py — rename
  `test_schema_lands_at_user_version_12` to `test_schema_lands_at_user_version_13`
  and change both `12`s to `13`; tests/test_schema_v10.py:41 `== 12` → `== state.SCHEMA_VERSION`;
  tests/test_query_substrate.py:31 `state.SCHEMA_VERSION == 12` → `== 13`.
- [ ] Run `python -m pytest tests/test_query_substrate.py tests/test_schema_version.py tests/test_schema_v10.py -v`
  — expect PASS (including the G2S1.1 mirror test: edge_ids now populated).
- [ ] Run `python scripts/verify` — expect PASS.
- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/schema.sql src/memoria_vault/runtime/state.py tests/test_query_substrate.py tests/test_schema_version.py tests/test_schema_v10.py
  git commit -m "feat(graph): promotion-ready concept edges — edge_id + attributes_json (migration 13)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task G2S1.3: reverse-traversal-indexes (migration 14)

The two indexes the consolidation names, on the verified real columns:
`concept_edges(target_concept_id)` and `work_graph_edges(target_id)` — reverse
traversal ("what points at this concept/work") currently full-scans both tables.
Depends on: G2S1.2 (takes version 14 after 13).

**Files:**
- Modify: `src/memoria_vault/runtime/schema.sql` (two CREATE INDEX statements after
  the concept_edges block landed by G2S1.2 and after the work_graph_edges block,
  lines 171-186; trailing pragma → 14)
- Modify: `src/memoria_vault/runtime/state.py` (`SCHEMA_VERSION` 13 → 14; add
  `MIGRATIONS[14]`)
- Modify: `tests/test_schema_version.py` (pin 13 → 14),
  `tests/test_query_substrate.py:31` (pin 13 → 14)
- Test: `tests/test_query_substrate.py`

**Interfaces:**
- Consumes: `state.MIGRATIONS` (G1), version 13 shape (G2S1.2).
- Produces: indexes `idx_concept_edges_target` and `idx_work_graph_edges_target`
  (names follow the existing `idx_<table>_<suffix>` convention, cf.
  `idx_passages_path_status`, schema.sql:217) — R2 `graph-sql-primitives` may rely
  on these names existing.

**Steps:**

- [ ] Write the failing test at the end of `tests/test_query_substrate.py`:

  ```python
  def test_reverse_traversal_indexes_exist(tmp_path: Path) -> None:
      with state.connect(tmp_path) as conn:
          names = {
              row["name"]
              for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'index'")
          }
      assert "idx_concept_edges_target" in names
      assert "idx_work_graph_edges_target" in names
  ```

- [ ] Run `python -m pytest tests/test_query_substrate.py::test_reverse_traversal_indexes_exist -v`
  — expect FAIL: `AssertionError: assert 'idx_concept_edges_target' in {...}`.
- [ ] In `src/memoria_vault/runtime/schema.sql`: after the
  `idx_concept_edges_edge_id` index add

  ```sql
  CREATE INDEX IF NOT EXISTS idx_concept_edges_target
      ON concept_edges(target_concept_id);
  ```

  after the work_graph_edges CREATE TABLE (closing `);` of the block at lines
  171-186) add

  ```sql
  CREATE INDEX IF NOT EXISTS idx_work_graph_edges_target
      ON work_graph_edges(target_id);
  ```

  and change the trailing pragma to `PRAGMA user_version = 14;`.
- [ ] In `src/memoria_vault/runtime/state.py`: `SCHEMA_VERSION = 14`; add

  ```python
  MIGRATIONS[14] = """
  CREATE INDEX IF NOT EXISTS idx_concept_edges_target
      ON concept_edges(target_concept_id);
  CREATE INDEX IF NOT EXISTS idx_work_graph_edges_target
      ON work_graph_edges(target_id);
  """
  ```

- [ ] Bump the two version pins: tests/test_schema_version.py (13 → 14, rename the
  test to `test_schema_lands_at_user_version_14`); tests/test_query_substrate.py:31
  (13 → 14). (tests/test_schema_v10.py already reads `state.SCHEMA_VERSION` after
  G2S1.2 — no change.)
- [ ] Run `python -m pytest tests/test_query_substrate.py tests/test_schema_version.py tests/test_schema_v10.py -v`
  — expect PASS.
- [ ] Run `python scripts/verify` — expect PASS.
- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/schema.sql src/memoria_vault/runtime/state.py tests/test_query_substrate.py tests/test_schema_version.py
  git commit -m "perf(graph): reverse-traversal indexes on edge targets (migration 14)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task G2S1.4: prune-dead-schema (S1)

Pure deletion. Grep-verified: no type yaml declares `required_any`, `promotion_gate`,
`promoted_at`, or `lifecycle`; `UNIVERSAL_LIFECYCLE` has zero references outside its
own definition; no test exercises any of them. Independent of G1/G2 tasks.

**Files:**
- Modify: `src/memoria_vault/runtime/subsystems/lib/schema.py` (delete line 37
  `UNIVERSAL_LIFECYCLE`, lines 187-189 `required_any` block, lines 197-199
  `promotion_gate` block, and the docstring sentence at lines 12-13 that documents
  `required_any`; line numbers pre-G2S1.1 — re-locate by content after it lands)
- Test: `tests/test_schemas.py` (contract level; already registered in TEST_LEVELS)

**Interfaces:**
- Consumes: `schema` module import already present in tests/test_schemas.py:8.
- Produces: nothing — removals only. `validate_frontmatter(fm, schema, vocabulary_terms=None)
  -> list[str]` signature and all live behavior (required/optional/required_when/
  forbidden/enums/links/vocabulary) unchanged.

**Steps:**

- [ ] Write the failing test at the end of `tests/test_schemas.py` (style precedent:
  `test_type_schemas_do_not_ship_dead_gated_keys`, line 83):

  ```python
  def test_schema_module_carries_no_dead_validation_machinery():
      assert not hasattr(schema, "UNIVERSAL_LIFECYCLE")
      source = Path(schema.__file__).read_text(encoding="utf-8")
      assert "required_any" not in source
      assert "promotion_gate" not in source
  ```

- [ ] Run `python -m pytest tests/test_schemas.py::test_schema_module_carries_no_dead_validation_machinery -v`
  — expect FAIL: `AssertionError: assert not hasattr(schema, 'UNIVERSAL_LIFECYCLE')`.
- [ ] In `src/memoria_vault/runtime/subsystems/lib/schema.py` delete these exact
  fragments:
  - line 37: `UNIVERSAL_LIFECYCLE = ["proposed", "provisional", "current", "retracted", "archived"]`
  - lines 187-189:

    ```python
        any_of = schema.get("required_any") or []
        if any_of and not any(fm.get(f) not in (None, "") for f in any_of):
            errors.append(f"at least one of {any_of} is required")
    ```

  - lines 197-199:

    ```python
        gate = schema.get("promotion_gate")
        if gate and fm.get("lifecycle") == gate and fm.get("promoted_at") in (None, ""):
            errors.append(f"lifecycle {gate!r} requires promoted_at promotion provenance")
    ```

  - docstring line 12, the sentence `` `required_any` lists field names of which at
    least one must be present.`` (keep the `required_when`/`forbidden` sentence on
    line 13).
- [ ] Run `python -m pytest tests/test_schemas.py tests/test_frontmatter_contract.py tests/test_precommit_schema.py -v`
  — expect PASS (nothing shipped ever produced these error paths).
- [ ] Run `python scripts/verify` — expect PASS.
- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/subsystems/lib/schema.py tests/test_schemas.py
  git commit -m "refactor(schema): prune dead validation machinery no type uses (S1 prune-dead-schema)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task G2S1.5: graph-substrate design gate (process task — no code)

Everything in G2–G5/S1 not mechanically specified today goes through the repo's
mandated design gate before any implementation task exists. Deliverable is a spec,
produced by the superpowers brainstorming skill — not code, not a placeholder.

**Files:**
- Create: `docs/superpowers/specs/2026-07-15-graph-substrate-design.md` (output of
  the brainstorm; `docs/superpowers/` is tracked, not published)
- Test: none — acceptance is the spec's existence and coverage checklist below.

**Interfaces:**
- Consumes (named inputs, all read into the session before brainstorming):
  - `docs/superpowers/specs/2026-07-12-beta.1-consolidation.md` §2, packages G2–G5
    and S1 (lines 140-147) plus §6 item 2 (warrant ontology RESOLVED: Option B) and
    the §"Schema-before-corpus" ruling (line 354).
  - `docs/superpowers/specs/data-structure-analysis.md` — at minimum the
    `concept_edges` section (~line 2795), the work_graph_edges/entity-resolution
    sections (~lines 1700-1880, 2699-2790), and Part-2 G0/G3/G4 findings
    (~lines 995, 1143-1160, 1164-1176).
  - `docs/superpowers/specs/warrant-ontology-brief.md` — the interim ruling
    ("What is already decided") and the pre-registered evidence gate.
  - This plan's already-shipped ledger (header above) — reconcile before proposing.
- Produces: the spec file, with a decision record (chosen option + rejected
  alternatives + migration/version claim) per agenda item. Follow-up implementation
  tasks are cut from the spec in a later plan, never from this one.

**Steps:**

- [ ] Confirm G2S1.1-.4 are merged (the brainstorm designs on top of the landed
  substrate): `git log --oneline -10` shows the four commits above.
- [ ] Invoke the brainstorming skill with the agenda and inputs inline:
  `Skill(skill="superpowers:brainstorming", args="Graph-substrate design for beta.1 consolidation G2-G5/S1. Inputs: docs/superpowers/specs/2026-07-12-beta.1-consolidation.md §2 G2-G5+S1, docs/superpowers/specs/data-structure-analysis.md, docs/superpowers/specs/warrant-ontology-brief.md interim ruling (Option B, do not relitigate). Output: docs/superpowers/specs/2026-07-15-graph-substrate-design.md")`
- [ ] Drive the session through this fixed agenda, one decision record each:
  1. **single-edge-module (G2, full consolidation)** — one owner for the relation
     roster + all edge parsing; today's substrates to reconcile: schema.py
     `LINK_RELATIONS`/`_check_links`/`parse_links`, state.py
     `_concept_edge_relation` roster (state.py:3420), schema.sql `relation_type`
     CHECK constraints (concept_edges + work_graph_edges), enrichment.py
     work_graph_edges relation writes (enrichment.py:975).
  2. **catalog-sources-bridge (G2)** — how claim→work edges resolve across the
     concept-id / work-id id-space boundary.
  3. **tension-edge-primitive / tension-relation-write-path (G2)** — the
     `surface_tensions` PI-confirmation write path onto the (now persistent)
     `tension` rows; edge existence is the confirmation signal.
  4. **links-mirror semantics beyond fill (G2)** — dangling-target policy,
     unchecked-source visibility, `.md` id-space normalization ratified or revised.
  5. **mode-collapse 6→4 (S1)** — note.yaml already ships the 4-mode enum; audit
     remaining 6-mode substrates (search/index/CLI) and either record as shipped or
     spec the residue.
  6. **concept-type-roster 15→10 (S1)** — roster is already 6 type files; reconcile
     the consolidation's 15→10 against reality and record the delta.
  7. **ULID keys + rename map (G3)** — ULID internal / path OKF-facing, rename
     tracking, real FKs; `work-id-rename`, `source→published_in`,
     `journal_events→event_log`, `source_type→item_type`; claims schema versions 15+.
  8. **six-role argument graph (G4)** — roles via typed relations, earn-each-type;
     within the warrant-brief interim ruling only (node reification stays deferred
     to the beta.2 evidence gate — do not relitigate).
  9. **typed propagation / blast-radius (G5)** — derive-and-propagate on write,
     typed consequences, origin-blind epistemics (integrity.py:915-925/999-1003).
- [ ] Write the spec to `docs/superpowers/specs/2026-07-15-graph-substrate-design.md`
  with one `## Decision:` section per agenda item, each carrying: inputs cited,
  options with pros/cons, the recommendation, and what it consumes from the landed
  G2S1 substrate (`parse_links`, `concept_edge_id`, edge-row contract, versions
  13-14).
- [ ] Acceptance check: all nine agenda items have a decision record; no code was
  written; already-shipped items are marked as such, not re-specified.
- [ ] Commit:

  ```
  git add docs/superpowers/specs/2026-07-15-graph-substrate-design.md
  git commit -m "docs(specs): graph-substrate design record for G2-G5/S1 (beta.1 consolidation)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```
# PLAN 22 — #1293 slices 1–2 (package S12)

Governing spec: `docs/superpowers/specs/2026-07-14-evidence-set-grounds-contract-design.md`
(§2 terminology ruling, §3 marker grammar v2, §12 slices). Rename manifest (authoritative
file:line sweep list): `docs/superpowers/specs/2026-07-14-warrant-grounds-rename-manifest.md`.

**Adjudications baked into this section (do not re-litigate):** manifest conflicts
§1.5 ("executable warrant(s)" / "computed-warrants", all 8 sites) and §1.6 ("checks
passed and warrants resolve", all sites incl. `states.md:75`) resolve to **grounds**;
§1.7 ("stale, under-warranted, needing re-confirmation", both sites) resolves to
**under-grounded**. The manifest §4 DO-NOT-TOUCH list is honored verbatim — S12.9's
grep audit enforces it.

**Ordering constraint:** Task S12.2 rides AFTER G1 lands (G1 introduces the numbered
DB-migration mechanism). Every other S12 task is independent of G1. Within the
package: S12.1 → S12.5 → S12.6 → S12.7 must run in that order (S12.7's fixtures use
the `code-grounds:` prefix from S12.1 and the v2 grammar from S12.5); S12.2, S12.3,
S12.4 can run at any point after S12.1.

**Session isolation (AGENTS.md):** before the first edit, run
`git worktree add .worktrees/1293-s12 -b wip/1293-s12 origin/main`, then
`EnterWorktree(path: ".worktrees/1293-s12")`. Stage explicit paths only — the git
index is shared per checkout; never `git add -A`.

**Line numbers in Modify: entries were verified against `main` @ d85d8799 on
2026-07-15.** Several drift from the 2026-07-14 manifest (e.g. `knowledge.py:3318`,
not `:3321`; `test_gap_analysis.py:73-140,570-572`, not `:107-174,604-606`;
`data-structure-analysis.md:2513`, not `:2497`). The refs below are the current ones.

---

## Slice 1 — warrant → grounds rename sweep (manifest-driven)

### Task S12.1: `code-warrant` → `code-grounds` identifier family (code tier, manifest §1.2)

**Files:**
- Modify: `src/memoria_vault/runtime/evidence.py:16-19` (`_CODE_WARRANT_RE`), `:29-32` (`CodeWarrantRef`), `:52-61` (`parse_code_warrant_ref`), `:64-67` (`evidence_ref_kind`)
- Modify: `src/memoria_vault/runtime/state.py:28` (import), `:2632`, `:2650-2651`, `:2664-2673` (`_code_warrant_resolves`)
- Modify: `src/memoria_vault/runtime/code/runs.py:26` (`code_warrant_complete` def)
- Modify: `src/memoria_vault/runtime/knowledge.py:3318` (detection regex)
- Modify: `tests/test_code_artifacts.py:64` (fixture marker item text)
- Modify: `CHANGELOG.md` (Unreleased → Changed)
- Test: `tests/test_evidence_markers.py` (registered `unit` in `tests/conftest.py:44`; no registration change needed)

**Interfaces:**
- Consumes: `evidence_ref_kind(ref: str) -> str` (existing), `state.code_run(vault, run_id)` (existing, unchanged)
- Produces: `CodeGroundsRef(run_id: str, artifact_id: str, output_sha256: str)` frozen dataclass in `evidence.py`; `parse_code_grounds_ref(ref: str) -> CodeGroundsRef`; `evidence_ref_kind(ref: str) -> str` now returns `"code-grounds" | "evidence-set" | "source-span"`; `code_grounds_complete(vault: Path, *, run_id: str, artifact_id: str, output_sha256: str) -> bool` in `code/runs.py`; on-disk item-ref prefix `code-grounds:` (no back-compat alias — spec §2: no vault exists, rename lands outright)

**Steps:**

- [ ] Write the failing tests. Append to `tests/test_evidence_markers.py` (and extend the import block at lines 5–15 with `CodeGroundsRef,` and `parse_code_grounds_ref,` in alphabetical position):

  ```python
  def test_evidence_ref_kind_recognizes_code_grounds_refs() -> None:
      ref = "code-grounds:run-1:analysis:sha256:" + "0" * 64

      assert evidence_ref_kind(ref) == "code-grounds"
      assert parse_code_grounds_ref(ref) == CodeGroundsRef(
          "run-1", "analysis", "sha256:" + "0" * 64
      )


  def test_retired_code_warrant_prefix_fails_closed() -> None:
      old = "code-warrant:run-1:analysis:sha256:" + "0" * 64

      with pytest.raises(ValueError, match="invalid code-grounds ref"):
          parse_code_grounds_ref(old)
      with pytest.raises(ValueError, match="invalid source-span ref"):
          evidence_ref_kind(old)
  ```

- [ ] Run to verify they fail: `python -m pytest tests/test_evidence_markers.py -v` — expect `ImportError: cannot import name 'CodeGroundsRef' from 'memoria_vault.runtime.evidence'`.
- [ ] Rename in `src/memoria_vault/runtime/evidence.py`. Lines 16–19 become:

  ```python
  _CODE_GROUNDS_RE = re.compile(
      r"^code-grounds:(?P<run_id>[A-Za-z0-9._:-]+):(?P<artifact_id>[A-Za-z0-9._-]+):"
      r"(?P<output_sha256>sha256:[0-9a-f]{64})$"
  )
  ```

  Lines 28–32 (dataclass) become `class CodeGroundsRef:` (fields unchanged). Lines 52–61 become:

  ```python
  def parse_code_grounds_ref(ref: str) -> CodeGroundsRef:
      value = ref.strip()
      match = _CODE_GROUNDS_RE.fullmatch(value)
      if not match:
          raise ValueError(f"invalid code-grounds ref: {ref!r}")
      return CodeGroundsRef(
          match.group("run_id"),
          match.group("artifact_id"),
          match.group("output_sha256"),
      )
  ```

  In `evidence_ref_kind` (lines 64–67): `if _CODE_GROUNDS_RE.fullmatch(value): return "code-grounds"`.
- [ ] Rename in `src/memoria_vault/runtime/state.py`. Line 28 import: `parse_code_grounds_ref,`. Line 2632: `if any(evidence_ref_kind(item) == "code-grounds" for item in items):`. Lines 2650–2651: `if kind == "code-grounds":` / `if not _code_grounds_resolves(vault, item):`. Lines 2664–2673 become:

  ```python
  def _code_grounds_resolves(vault: Path, item: str) -> bool:
      from memoria_vault.runtime.code.runs import code_grounds_complete

      grounds = parse_code_grounds_ref(item)
      return code_grounds_complete(
          vault,
          run_id=grounds.run_id,
          artifact_id=grounds.artifact_id,
          output_sha256=grounds.output_sha256,
      )
  ```

- [ ] Rename in `src/memoria_vault/runtime/code/runs.py:26`: `def code_grounds_complete(` (signature body unchanged).
- [ ] Update the durable-format reader in `src/memoria_vault/runtime/knowledge.py:3318` (it scans draft content for the marker prefix, so it renames in lockstep — manifest §3d):

  ```python
      if re.search(r"\b(analysis-computed|analysis code|code-grounds)\b", content, re.I):
  ```

- [ ] Update the on-disk fixture in `tests/test_code_artifacts.py:64`: `f"review=false items=code-grounds:run-1:analysis:{output_hash}%%\n",` (the `type=`/`state=`/`review=` fields on lines 63–64 stay for now; S12.7 strips them).
- [ ] Run the new tests and every suite that exercises the renamed seam: `python -m pytest tests/test_evidence_markers.py tests/test_evidence_sets.py tests/test_code_artifacts.py -v` — expect all pass.
- [ ] Add to `CHANGELOG.md` under `## [Unreleased]` (create a `### Changed` heading there if absent):

  ```markdown
  - Renamed the evidence-set code-item marker prefix `code-warrant:` to
    `code-grounds:` (`CodeGroundsRef`, `parse_code_grounds_ref`,
    `code_grounds_complete`, ref-kind `"code-grounds"`), per the #1293
    grounds-terminology ruling. No back-compat alias: old-prefix items fail
    closed as invalid source-span refs.
  ```

- [ ] Commit:

  ```bash
  git commit -m "refactor(evidence): rename code-warrant item family to code-grounds (#1293)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" \
    src/memoria_vault/runtime/evidence.py src/memoria_vault/runtime/state.py \
    src/memoria_vault/runtime/code/runs.py src/memoria_vault/runtime/knowledge.py \
    tests/test_evidence_markers.py tests/test_code_artifacts.py CHANGELOG.md
  ```

### Task S12.2: code-artifact `purpose` enum `warrant` → `grounds` + numbered DB migration (manifest §1.1; AFTER G1)

**Files:**
- Modify: `src/memoria_vault/runtime/code/records.py:20` (`purpose: str = "warrant"` default)
- Modify: `src/memoria_vault/runtime/schema.sql:301` (CHECK constraint), `:378` (`PRAGMA user_version`)
- Modify: `src/memoria_vault/runtime/state.py:53` (`SCHEMA_VERSION`), `:3429` (`_code_purpose` validation set), plus the `MIGRATIONS` dict G1 added (location fixed by G1; adjacent to `SCHEMA_VERSION`)
- Modify: `tests/test_schema_version.py` (version-pin test G1 adjusted; today `:14-17` asserts 12)
- Modify: `CHANGELOG.md` (Unreleased → Changed)
- Test: `tests/test_schema_version.py` (registered `contract` in `tests/conftest.py:100`), `tests/test_code_artifacts.py` (registered `runtime` in `tests/conftest.py:30`)

**Interfaces:**
- Consumes: **G1's migration mechanism — assumed exact shape:** `MIGRATIONS: dict[int, tuple[int, list[str]]]` in `state.py`, mapping `from_version -> (to_version, steps)`, where `steps` is an ordered list of SQL statements the G1 runner executes inside one transaction with `PRAGMA foreign_keys = OFF`, setting `PRAGMA user_version = to_version` on success and chain-walking until `SCHEMA_VERSION`. Also assumed: G1 lands at `SCHEMA_VERSION == 13`. If either differs when this task executes, keep the migration body identical and renumber `13 -> N`, `14 -> N + 1`, reconciling with G1's actual runner contract before writing code.
- Produces: `purpose` enum value `"grounds"` (frontmatter default, SQLite CHECK, validation set); `MIGRATIONS[13] = (14, [...])` rebuilding `code_artifacts` with the new CHECK and rewriting `'warrant'` rows to `'grounds'`; `SCHEMA_VERSION = 14`

**Steps:**

- [ ] Write the failing migration test. Append to `tests/test_schema_version.py` (it already imports `sqlite3`, `Path`, `pytest`, `state`):

  ```python
  _V13_CODE_ARTIFACTS_SQL = """
      CREATE TABLE code_artifacts (
          artifact_id TEXT PRIMARY KEY,
          project_path TEXT NOT NULL,
          record_path TEXT NOT NULL UNIQUE,
          source_dir TEXT NOT NULL,
          output_dir TEXT NOT NULL,
          purpose TEXT NOT NULL CHECK (purpose IN ('warrant', 'deliverable', 'both')),
          approved_command_json TEXT NOT NULL DEFAULT '[]',
          declared_inputs_json TEXT NOT NULL DEFAULT '[]',
          declared_outputs_json TEXT NOT NULL DEFAULT '[]',
          dependency_notes TEXT NOT NULL DEFAULT '',
          status TEXT NOT NULL CHECK (status IN ('draft', 'ready', 'failed', 'retired')),
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
      )
  """


  def test_migration_rewrites_code_artifact_purpose_warrant_to_grounds(
      tmp_path: Path,
  ) -> None:
      with state.connect(tmp_path):
          pass  # mint a current-version DB, then downgrade it to v13 shape
      with sqlite3.connect(tmp_path / state.DB_REL) as conn:
          conn.execute("PRAGMA foreign_keys = OFF")
          conn.execute("DROP TABLE code_artifacts")
          conn.execute(_V13_CODE_ARTIFACTS_SQL)
          conn.execute(
              "INSERT INTO code_artifacts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (
                  "analysis",
                  "projects/project-alpha/project-alpha.md",
                  "projects/project-alpha/code/analysis.md",
                  "projects/project-alpha/code/analysis/src",
                  "projects/project-alpha/code/analysis/outputs",
                  "warrant",
                  "[]",
                  "[]",
                  "[]",
                  "",
                  "draft",
                  "2026-07-15T00:00:00Z",
                  "2026-07-15T00:00:00Z",
              ),
          )
          conn.execute("PRAGMA user_version = 13")

      with state.connect(tmp_path) as conn:
          purpose = conn.execute(
              "SELECT purpose FROM code_artifacts WHERE artifact_id = 'analysis'"
          ).fetchone()["purpose"]
          version = conn.execute("PRAGMA user_version").fetchone()[0]

      assert purpose == "grounds"
      assert version == state.SCHEMA_VERSION == 14
  ```

- [ ] Write the failing default-purpose test. Append to `tests/test_code_artifacts.py` (it already imports `create_code_artifact`):

  ```python
  def test_code_artifact_purpose_defaults_to_grounds(tmp_path: Path) -> None:
      artifact = create_code_artifact(
          tmp_path,
          "project-alpha",
          "analysis",
          approved_command=["python3", "main.py"],
      )

      assert artifact["purpose"] == "grounds"
  ```

- [ ] Run both to verify they fail: `python -m pytest tests/test_schema_version.py::test_migration_rewrites_code_artifact_purpose_warrant_to_grounds tests/test_code_artifacts.py::test_code_artifact_purpose_defaults_to_grounds -v` — expect `assert purpose == "grounds"` failing with `'warrant'` in both.
- [ ] Edit `src/memoria_vault/runtime/schema.sql:301`:

  ```sql
      purpose TEXT NOT NULL CHECK (purpose IN ('grounds', 'deliverable', 'both')),
  ```

  and `:378`: `PRAGMA user_version = 14;`
- [ ] Edit `src/memoria_vault/runtime/state.py:53`: `SCHEMA_VERSION = 14`, and `:3429`: `if purpose not in {"grounds", "deliverable", "both"}:`
- [ ] Add the migration entry to G1's `MIGRATIONS` dict in `state.py` (SQLite cannot ALTER a CHECK and the old CHECK rejects `UPDATE ... SET purpose='grounds'`, so this is the standard create-copy-drop-rename rebuild; the G1 runner's `foreign_keys = OFF` keeps `code_runs`' `REFERENCES code_artifacts ON DELETE CASCADE` from firing on the DROP):

  ```python
      13: (
          14,
          [
              """
              CREATE TABLE code_artifacts_v14 (
                  artifact_id TEXT PRIMARY KEY,
                  project_path TEXT NOT NULL,
                  record_path TEXT NOT NULL UNIQUE,
                  source_dir TEXT NOT NULL,
                  output_dir TEXT NOT NULL,
                  purpose TEXT NOT NULL CHECK (purpose IN ('grounds', 'deliverable', 'both')),
                  approved_command_json TEXT NOT NULL DEFAULT '[]',
                  declared_inputs_json TEXT NOT NULL DEFAULT '[]',
                  declared_outputs_json TEXT NOT NULL DEFAULT '[]',
                  dependency_notes TEXT NOT NULL DEFAULT '',
                  status TEXT NOT NULL CHECK (status IN ('draft', 'ready', 'failed', 'retired')),
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
              )
              """,
              """
              INSERT INTO code_artifacts_v14
              SELECT artifact_id, project_path, record_path, source_dir, output_dir,
                     CASE WHEN purpose = 'warrant' THEN 'grounds' ELSE purpose END,
                     approved_command_json, declared_inputs_json, declared_outputs_json,
                     dependency_notes, status, created_at, updated_at
              FROM code_artifacts
              """,
              "DROP TABLE code_artifacts",
              "ALTER TABLE code_artifacts_v14 RENAME TO code_artifacts",
          ],
      ),
  ```

- [ ] Edit `src/memoria_vault/runtime/code/records.py:20`: `purpose: str = "grounds",`
- [ ] Update the version-pin test in `tests/test_schema_version.py` to the new landing version: rename `test_schema_lands_at_user_version_13` to `test_schema_lands_at_user_version_14` and change both literals in its body from `13` to `14` (today, pre-G1, that test is `test_schema_lands_at_user_version_12` at lines 14–17 asserting `12`; G1 will have moved it to 13 — align whatever literal G1 left to 14).
- [ ] Run to verify both pass: `python -m pytest tests/test_schema_version.py tests/test_code_artifacts.py -v`
- [ ] Add to `CHANGELOG.md` under `## [Unreleased]` → `### Changed`:

  ```markdown
  - Renamed the code-artifact `purpose` enum value `warrant` to `grounds`
    (frontmatter default, SQLite CHECK, validation set); DB migration 13→14
    rewrites existing rows.
  ```

- [ ] Commit:

  ```bash
  git commit -m "feat(state): rename code-artifact purpose 'warrant' to 'grounds' with 13->14 migration (#1293)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" \
    src/memoria_vault/runtime/schema.sql src/memoria_vault/runtime/state.py \
    src/memoria_vault/runtime/code/records.py tests/test_schema_version.py \
    tests/test_code_artifacts.py CHANGELOG.md
  ```

### Task S12.3: `under-warranted` → `under-grounded` gap kind (manifest §1.3 + §1.7 adjudication)

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py:60` (GAP_KINDS member), `:486` (kind assignment), `:489-491` (`why` text)
- Modify: `tests/test_gap_analysis.py:73-74` (fixture note slug/title/tag), `:132` (topic set), `:138-140` (assertions), `:570,572` (assertions)
- Modify: `tests/test_worker_knowledge_cycle.py:90` (assertion)
- Modify: `docs/explanation/knowledge/document-types.md:53`, `docs/reference/commands-and-transports/system-actions-operations.md:124`, `docs/explanation/knowledge/consequence-propagation.md:38`, `docs/superpowers/plans/2026-07-12-docs-migration.md:236` (prose echoes; the last two are the §1.7 pair — same sentence, changed identically)
- Modify: `CHANGELOG.md` (Unreleased → Changed)
- Test: `tests/test_gap_analysis.py` (registered `runtime`, `tests/conftest.py:56`), `tests/test_worker_knowledge_cycle.py` (registered `runtime`, `tests/conftest.py:116`)

**Interfaces:**
- Consumes: `analyze_gaps(vault, ...)` gap payload contract (`gap_type` field; unchanged shape)
- Produces: `GAP_KINDS` member and `analyze-gaps` output literal `"under-grounded"` (replaces `"under-warranted"`; CLI/API-visible — no compatibility alias, changelog entry required per manifest tier c). NOT touched: the `unstated-warrant` finding kind (`knowledge.py:964,2956`) — Toulmin-correct, manifest §4.

**Steps:**

- [ ] Make the tests fail first — flip the expectations. In `tests/test_gap_analysis.py` lines 73–74:

  ```python
              tmp_path / f"notes/grounds-{idx}.md",
              f"type: note\ncheck_status: checked\ntitle: Grounds {idx}\ntags: [grounds]\n",
  ```

  line 132: `assert set(gaps) == {"sleep", "grounds", "new area"}`; lines 138–140:

  ```python
      assert gaps["grounds"]["gap_type"] == "under-grounded"
      assert gaps["grounds"]["note_count"] == 2
      _assert_gap_contract(gaps["grounds"], "under-grounded")
  ```

  lines 570 and 572: replace `"under-warranted"` with `"under-grounded"`. In `tests/test_worker_knowledge_cycle.py:90`: `] == "under-grounded"`.
- [ ] Run to verify they fail: `python -m pytest tests/test_gap_analysis.py tests/test_worker_knowledge_cycle.py -v` — expect assertions failing with observed `gap_type == "under-warranted"` (and `_assert_gap_contract` rejecting the unknown expected kind).
- [ ] Implement in `src/memoria_vault/runtime/knowledge.py`. Line 60 (inside `GAP_KINDS`): `"under-grounded",`. Lines 486–491:

  ```python
          elif note_count >= dense_threshold and source_count == 0:
              kind = "under-grounded"
              seed = "capture or link supporting sources"
              why = (
                  f"{note_count} checked note(s) mention this topic, "
                  "but no checked sources or digests ground it."
              )
  ```

- [ ] Run to verify they pass: `python -m pytest tests/test_gap_analysis.py tests/test_worker_knowledge_cycle.py -v`
- [ ] Update the four prose echoes:
  - `docs/explanation/knowledge/document-types.md:53`: `absent; \`under-grounded\` means notes exist without enough source support.`
  - `docs/reference/commands-and-transports/system-actions-operations.md:124`: `Reports topic, digest, grounds, and project argument gaps from checked state;` (rest of cell unchanged)
  - `docs/explanation/knowledge/consequence-propagation.md:38` **and** `docs/superpowers/plans/2026-07-12-docs-migration.md:236` (identical sentence, identical edit): `computed and affected nodes are marked — stale, under-grounded, needing` (line 25 of `consequence-propagation.md`, the formal "Warrant lost" consequence type, stays — manifest §4)
- [ ] Add to `CHANGELOG.md` under `## [Unreleased]` → `### Changed`:

  ```markdown
  - Renamed the `analyze-gaps` gap kind `under-warranted` to `under-grounded`
    (breaking for scripts that branch on `gap_type`; no compatibility alias).
  ```

- [ ] Commit:

  ```bash
  git commit -m "refactor(knowledge): rename under-warranted gap kind to under-grounded (#1293)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" \
    src/memoria_vault/runtime/knowledge.py tests/test_gap_analysis.py \
    tests/test_worker_knowledge_cycle.py docs/explanation/knowledge/document-types.md \
    docs/reference/commands-and-transports/system-actions-operations.md \
    docs/explanation/knowledge/consequence-propagation.md \
    docs/superpowers/plans/2026-07-12-docs-migration.md CHANGELOG.md
  ```

### Task S12.4: docs prose sweep — remaining warrant → grounds sites (manifest §1.4 + adjudicated §1.5–1.6), with DO-NOT-TOUCH audit

**Files:**
- Modify (published docs): `docs/reference/control-and-policy/evidence-sets.md:10,45,65,67`; `docs/explanation/rationale/boundaries/why-deterministic-methods.md:50`; `docs/explanation/rationale/boundaries/why-write-half-is-bounded.md:56`; `docs/explanation/rationale/foundations/design-principles.md:41,81`; `docs/explanation/rationale/foundations/what-memoria-is.md:32`; `docs/explanation/rationale/boundaries/why-review-gate-is-structural.md:17,65`; `docs/explanation/execution/control-plane/states.md:75`; `docs/reference/evidence-and-integrations/pattern-provenance.md:74`; `docs/explanation/rationale/evidence/literature-pushback.md:14`
- Modify (specs/plans): `docs/superpowers/specs/0.1.0-beta.1-design.md:169,179,234,278,282,380,401,648,700,701`; `docs/superpowers/specs/0.1.0-beta.1-requirements.md:81,374,377,391`; `docs/superpowers/specs/0.1.0-beta.2-scope.md:42`; `docs/superpowers/specs/2026-07-12-beta.1-consolidation.md:56,159,164,225`; `docs/superpowers/specs/data-structure-analysis.md:2513`
- Test: none (docs-only word swaps; `python scripts/verify` runs the docs/lint gates)

**Interfaces:**
- Consumes: manifest §1.4–§1.7 rows and §4 DO-NOT-TOUCH list (verbatim)
- Produces: docs vocabulary "grounds" for the evidence-set concept; a clean grep audit whose only remaining "warrant" hits are the manifest §4 (Toulmin-correct) and §5 (general-English) sites

**Steps:**

- [ ] Apply the published-docs word swaps (each edit replaces only the quoted phrase on the cited line):

  | File:line | Old phrase | New phrase |
  |---|---|---|
  | `evidence-sets.md:10` | `draft-time warrant contract` | `draft-time grounds contract` |
  | `evidence-sets.md:45` | `` `code-warrant:<run_id>:<artifact_id>:<sha256>` `` | `` `code-grounds:<run_id>:<artifact_id>:<sha256>` `` |
  | `evidence-sets.md:65` | `` a `code-warrant` item `` | `` a `code-grounds` item `` |
  | `evidence-sets.md:67` | `Running code warrants the output provenance` | `Running code grounds the output provenance` |
  | `why-deterministic-methods.md:50` | `code-warrant` | `code-grounds` |
  | `why-write-half-is-bounded.md:56` | `Computed warrants can prove` | `Computed grounds can prove` |
  | `design-principles.md:41` | `warrants pass` | `grounds pass` |
  | `design-principles.md:81` | `required checks and warrants passed` | `required checks and grounds passed` |
  | `what-memoria-is.md:32` | `required checks and warrants passed` | `required checks and grounds passed` |
  | `why-review-gate-is-structural.md:17` | `the required warrants resolve` | `the required grounds resolve` |
  | `why-review-gate-is-structural.md:65` | `required checks and warrants exist` | `required checks and grounds exist` |
  | `states.md:75` | `checks passed and warrants resolve` | `checks passed and grounds resolve` |
  | `pattern-provenance.md:74` | `recorded warrant` | `recorded grounds` |
  | `literature-pushback.md:14` | `verbatim warrants` | `verbatim grounds` |

  (`design-principles.md:84-85` — the "planned Toulmin warrant graph" callout directly below line 81 — stays, per manifest §4. `evidence-sets.md:14`'s v1 grammar example is slice 8's v2-grammar doc rewrite, not this sweep.)
- [ ] Apply the specs/plans word swaps (§1.5 sites all → grounds, per adjudication):

  | File:line | Old phrase | New phrase |
  |---|---|---|
  | `0.1.0-beta.1-design.md:169` | `**Warrant = an evidence-*set*, typed.**` | `**Grounds = an evidence-*set*, typed.**` |
  | `0.1.0-beta.1-design.md:179` | `warrant) — and never asserts it.` | `grounds) — and never asserts it.` |
  | `0.1.0-beta.1-design.md:234` | `evidence-incomplete warrants` | `evidence-incomplete grounds` |
  | `0.1.0-beta.1-design.md:278` | `into an executable warrant` | `into executable grounds` |
  | `0.1.0-beta.1-design.md:282` | `executable warrants,` | `executable grounds,` |
  | `0.1.0-beta.1-design.md:380` | `implicit/multi-hop warrants are flagged` | `implicit/multi-hop grounds are flagged` |
  | `0.1.0-beta.1-design.md:401` | `not produce executable warrants` | `not produce executable grounds` |
  | `0.1.0-beta.1-design.md:648` | `or an executable warrant.` | `or executable grounds.` |
  | `0.1.0-beta.1-design.md:700` | `Computed/code-warrant evidence` / `` `code-warrant` evidence items `` / `executable warrants` / `computed/code-warrant review` (four swaps, one table row) | `Computed/code-grounds evidence` / `` `code-grounds` evidence items `` / `executable grounds` / `computed/code-grounds review` |
  | `0.1.0-beta.1-design.md:701` | `broken-warrant export refusal` | `broken-grounds export refusal` |
  | `0.1.0-beta.1-requirements.md:81` | `executable warrants` | `executable grounds` |
  | `0.1.0-beta.1-requirements.md:374` | `implicit warrants` | `implicit grounds` |
  | `0.1.0-beta.1-requirements.md:377` | `executable warrants` | `executable grounds` |
  | `0.1.0-beta.1-requirements.md:391` | `multi-hop/implicit warrants` | `multi-hop/implicit grounds` |
  | `0.1.0-beta.2-scope.md:42` | `executable warrants)` | `executable grounds)` |
  | `2026-07-12-beta.1-consolidation.md:56` | `code-execution warrant substrate` | `code-execution grounds substrate` |
  | `2026-07-12-beta.1-consolidation.md:159` | `` `warrant-evidence-set` `` | `` `grounds-evidence-set` `` |
  | `2026-07-12-beta.1-consolidation.md:164` | `executable warrants are B2` | `executable grounds are B2` |
  | `2026-07-12-beta.1-consolidation.md:225` | `` executable `computed`-warrants `` | `` executable `computed`-grounds `` |
  | `data-structure-analysis.md:2513` | `multi-hop warrant;` | `multi-hop grounds;` |

- [ ] Run the DO-NOT-TOUCH audit — after the sweep, the only remaining "warrant"-family hits under `docs/`, `src/`, `tests/` must be the manifest §4 (Toulmin/six-role graph, `unstated-warrant`, NLI-judge `warrant` field, `unwarranted-claim` seeded errors, "Warrant lost" consequence, `warrant-ontology-brief.md`, `docs-migration.md:60,62,151,183,223,566`, `0.1.0-beta.2-scope.md:56-67`, `2026-07-12-beta.1-consolidation.md:110,137,142,143,226,304,306,308,341,375`, `design-principles.md:84-85`, etc.) and §5 (general-English) sites, plus the manifest and governing spec themselves:

  ```bash
  grep -rniE "warrant" docs/ src/ tests/ \
    --exclude=2026-07-14-warrant-grounds-rename-manifest.md \
    --exclude=2026-07-14-evidence-set-grounds-contract-design.md \
    --exclude=warrant-ontology-brief.md
  ```

  Diff the hit list against manifest §4 + §5. Any hit not on those lists is a missed sweep site (fix it); any §4 line that changed is an overreach (revert it).
- [ ] Run the gate: `python scripts/verify` — expect pass (docs edits only; cspell already accepts "grounds").
- [ ] Commit:

  ```bash
  git commit -m "docs: sweep evidence-set 'warrant' prose to 'grounds' per #1293 manifest

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" \
    docs/reference/control-and-policy/evidence-sets.md \
    docs/explanation/rationale/boundaries/why-deterministic-methods.md \
    docs/explanation/rationale/boundaries/why-write-half-is-bounded.md \
    docs/explanation/rationale/foundations/design-principles.md \
    docs/explanation/rationale/foundations/what-memoria-is.md \
    docs/explanation/rationale/boundaries/why-review-gate-is-structural.md \
    docs/explanation/execution/control-plane/states.md \
    docs/reference/evidence-and-integrations/pattern-provenance.md \
    docs/explanation/rationale/evidence/literature-pushback.md \
    docs/superpowers/specs/0.1.0-beta.1-design.md \
    docs/superpowers/specs/0.1.0-beta.1-requirements.md \
    docs/superpowers/specs/0.1.0-beta.2-scope.md \
    docs/superpowers/specs/2026-07-12-beta.1-consolidation.md \
    docs/superpowers/specs/data-structure-analysis.md
  ```

---

## Slice 2 — marker grammar v2: `items=` is the sole authoritative field (spec §3)

### Task S12.5: v2 parser/serializer — `EvidenceMarker` drops `evidence_type`/`state`/`review_required`

**Files:**
- Modify: `src/memoria_vault/runtime/evidence.py:10-11` (delete `EVIDENCE_TYPES`/`EVIDENCE_STATES` — after this task nothing in the module reads them; grep confirms no external importer), `:35-41` (dataclass), `:74-111` (`parse_evidence_marker`), `:114-128` (`serialize_evidence_marker`), `:154-160` (delete `_parse_review`, now dead)
- Modify: `tests/test_evidence_markers.py:18-47` (rewrite the two grammar tests; the S12.1 tests and lines 50–64 stand)
- Modify: `CHANGELOG.md` (Unreleased → Changed)
- Test: `tests/test_evidence_markers.py` (`unit` level, already registered)

**Interfaces:**
- Consumes: `evidence_ref_kind(ref: str) -> str` (from S12.1 — item classification is unchanged and still fails the record closed on an unclassifiable item)
- Produces: `EvidenceMarker(evidence_id: str, items: tuple[str, ...])` frozen dataclass (fields `evidence_type`, `state`, `review_required` REMOVED); `parse_evidence_marker(marker: str) -> EvidenceMarker` accepting only `%%ev: ev-<8hex> items=a|b%%` with `items=` empty or omitted meaning no items, and rejecting `type=`/`state=`/`review=` as unknown fields (fail-closed, spec §3); `serialize_evidence_marker(marker: EvidenceMarker) -> str` emitting exactly `%%ev: <id> items=<a|b>%%`

**Steps:**

- [ ] Rewrite the grammar tests in `tests/test_evidence_markers.py` (replace `test_evidence_marker_round_trips_canonical_form` at lines 18–33 and `test_extract_evidence_markers_from_draft_text` at lines 36–47 with the following; imports need no change beyond S12.1's):

  ```python
  def test_evidence_marker_round_trips_canonical_v2_form() -> None:
      marker = EvidenceMarker(
          evidence_id="ev-deadbeef",
          items=("source-alpha#^p0001", "ev-feedcafe"),
      )

      text = serialize_evidence_marker(marker)

      assert text == "%%ev: ev-deadbeef items=source-alpha#^p0001|ev-feedcafe%%"
      assert parse_evidence_marker(text) == marker


  def test_empty_and_omitted_items_both_parse_as_no_items() -> None:
      assert parse_evidence_marker("%%ev: ev-deadbeef items=%%").items == ()
      assert parse_evidence_marker("%%ev: ev-deadbeef%%").items == ()


  def test_parser_rejects_retired_v1_fields_as_unknown() -> None:
      with pytest.raises(ValueError, match="unknown evidence marker field"):
          parse_evidence_marker(
              "%%ev: ev-deadbeef type=single-span state=complete "
              "review=false items=source-alpha#^p0001%%"
          )


  def test_parser_fails_closed_on_an_unclassifiable_item() -> None:
      with pytest.raises(ValueError, match="invalid source-span ref"):
          parse_evidence_marker("%%ev: ev-deadbeef items=@smith2024#^p0001%%")


  def test_extract_evidence_markers_from_draft_text() -> None:
      text = (
          "Claim one. %%ev: ev-11111111 items=work-a#^p0001%%\n"
          "Claim two. %%ev: ev-22222222 items=%%"
      )

      markers = extract_evidence_markers(text)

      assert [marker.evidence_id for marker in markers] == ["ev-11111111", "ev-22222222"]
      assert evidence_ids_in_text(text) == {"ev-11111111", "ev-22222222"}
  ```

- [ ] Run to verify they fail: `python -m pytest tests/test_evidence_markers.py -v` — expect `TypeError: EvidenceMarker.__init__() missing 3 required positional arguments` on the round-trip test and `ValueError: invalid evidence type: ''` (not the unknown-field error) from `test_empty_and_omitted_items_both_parse_as_no_items`.
- [ ] Implement in `src/memoria_vault/runtime/evidence.py`. Delete lines 10–11 (`EVIDENCE_TYPES`, `EVIDENCE_STATES`). Replace the dataclass (lines 35–41) with:

  ```python
  @dataclass(frozen=True)
  class EvidenceMarker:
      evidence_id: str
      items: tuple[str, ...]
  ```

  Replace `parse_evidence_marker` (lines 74–111) with:

  ```python
  def parse_evidence_marker(marker: str) -> EvidenceMarker:
      value = marker.strip()
      match = _EV_MARKER_RE.fullmatch(value)
      if not match:
          raise ValueError(f"invalid evidence marker: {marker!r}")
      parts = match.group("body").split()
      if not parts or not _EV_ID_RE.fullmatch(parts[0]):
          raise ValueError(f"invalid evidence marker id: {marker!r}")

      fields: dict[str, str] = {}
      for part in parts[1:]:
          if "=" not in part:
              raise ValueError(f"invalid evidence marker field: {part!r}")
          key, raw = part.split("=", 1)
          fields[key] = raw

      unknown = set(fields) - {"items"}
      if unknown:
          raise ValueError(f"unknown evidence marker field(s): {sorted(unknown)}")

      items = tuple(item for item in fields.get("items", "").split("|") if item)
      for item in items:
          evidence_ref_kind(item)

      return EvidenceMarker(evidence_id=parts[0], items=items)
  ```

  Replace `serialize_evidence_marker` (lines 114–128) with:

  ```python
  def serialize_evidence_marker(marker: EvidenceMarker) -> str:
      if not _EV_ID_RE.fullmatch(marker.evidence_id):
          raise ValueError(f"invalid evidence id: {marker.evidence_id!r}")
      for item in marker.items:
          evidence_ref_kind(item)
      return f"%%ev: {marker.evidence_id} items={'|'.join(marker.items)}%%"
  ```

  Delete `_parse_review` (lines 154–160).
- [ ] Run to verify the unit suite passes: `python -m pytest tests/test_evidence_markers.py -v` — expect all pass. (The runtime suites that construct `EvidenceMarker` or carry v1 fixture markers — `test_draft_compose.py`, `test_evidence_sets.py`, `test_mc_hash_binding.py`, `test_code_artifacts.py` — go red here and are restored by S12.6–S12.7; the full gate runs at the end of S12.7.)
- [ ] Add to `CHANGELOG.md` under `## [Unreleased]` → `### Changed`:

  ```markdown
  - Marker grammar v2: `%%ev: ev-<8hex> items=a|b%%`. The `type=`, `state=`,
    and `review=` fields are removed from markers and rejected as unknown
    (fail-closed); type, state, and review-required are always re-derived
    from `items=`, the sole authoritative field.
  ```

- [ ] Commit:

  ```bash
  git commit -m "feat(evidence): marker grammar v2 - id + items only, derived fields rejected (#1293)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" \
    src/memoria_vault/runtime/evidence.py tests/test_evidence_markers.py CHANGELOG.md
  ```

### Task S12.6: chase `EvidenceMarker` constructors/consumers in `knowledge.py`

Every constructor/consumer of the dropped fields, located by
`grep -rn "EvidenceMarker(\|\.evidence_type\|\.review_required\|marker\.state" src/ tests/`:
`knowledge.py:2014-2020` (sole production constructor, compose path),
`knowledge.py:2103-2105` (sole production consumer of the dropped fields,
`read_project_draft` payload), `evidence.py` internals (done in S12.5), and test
constructors/fixtures (S12.5/S12.7). `state.py` consumes only `.evidence_id`/`.items`
(`:2612,2617,2620` via `_derived_evidence_row`) — no change needed there.

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py:2008-2020` (compose marker construction), `:2100-2109` (`read_project_draft` marker payload)
- Test: `tests/test_draft_compose.py` (registered `runtime`, `tests/conftest.py:36`) — existing tests are the spec; no new test file

**Interfaces:**
- Consumes: `EvidenceMarker(evidence_id: str, items: tuple[str, ...])` and `serialize_evidence_marker` from S12.5; `state.rebuild_evidence_sets_from_markers(vault, run_id=...)` (unchanged — type/state/review derivation already lives there, in `_derived_evidence_row`)
- Produces: compose writes v2 markers (`%%ev: <id> items=...%%`) into drafts; `read_project_draft(vault: Path, project_path: str) -> dict[str, Any]` whose `evidence_markers` entries are now `{"id": str, "items": list[str]}` (dropped keys `type`/`state`/`review_required` — derived status stays available in the same payload's `evidence_sets` rows, per spec §3 "status lives in verify/preview surfaces, never in the marker"). `_draft_evidence_type` (`knowledge.py:3216`) becomes uncalled but is NOT deleted here — slice 3 owns its deletion (spec §12.3).

**Steps:**

- [ ] Run the already-failing consumer tests to capture the failure: `python -m pytest tests/test_draft_compose.py -v` — expect `TypeError: EvidenceMarker.__init__() got an unexpected keyword argument 'evidence_type'` from the compose path.
- [ ] Fix the compose constructor. `src/memoria_vault/runtime/knowledge.py` lines 2008–2020 currently read:

  ```python
          frontmatter, body = split_frontmatter((vault / note_rel).read_text(encoding="utf-8"))
          evidence_id = mint_evidence_id(allocated_ids)
          allocated_ids.add(evidence_id)
          items = _draft_evidence_items(vault, frontmatter)
          evidence_type = _draft_evidence_type(items)
          state_value = "complete" if items else "evidence-incomplete"
          marker = EvidenceMarker(
              evidence_id=evidence_id,
              evidence_type=evidence_type,
              state=state_value,
              review_required=evidence_type in {"implicit", "multi-hop"},
              items=tuple(items),
          )
  ```

  Replace with:

  ```python
          frontmatter, body = split_frontmatter((vault / note_rel).read_text(encoding="utf-8"))
          evidence_id = mint_evidence_id(allocated_ids)
          allocated_ids.add(evidence_id)
          items = _draft_evidence_items(vault, frontmatter)
          marker = EvidenceMarker(evidence_id=evidence_id, items=tuple(items))
  ```

- [ ] Fix the `read_project_draft` payload. Lines 2100–2109 currently read:

  ```python
          "evidence_markers": [
              {
                  "id": marker.evidence_id,
                  "type": marker.evidence_type,
                  "state": marker.state,
                  "review_required": marker.review_required,
                  "items": list(marker.items),
              }
              for marker in markers
          ],
  ```

  Replace with:

  ```python
          "evidence_markers": [
              {
                  "id": marker.evidence_id,
                  "items": list(marker.items),
              }
              for marker in markers
          ],
  ```

  (Verified consumers: `tests/test_draft_verification.py:337,360,877,991`, `tests/test_draft_compose.py:89`, `tests/test_cli_work_project.py:785,910`, and `worker.py:659` read only `"id"`/list length; `test_draft_compose.py:85` reads `review_required` from the `evidence_sets` DB rows, which keep it.)
- [ ] Run to verify the compose path passes: `python -m pytest tests/test_draft_compose.py tests/test_draft_verification.py -v` — expect all pass (compose now writes v2 markers; `test_draft_compose.py:73`'s regex `\^blk-[0-9a-f]{8} %%ev: ev-[0-9a-f]{8} ` matches the v2 form).
- [ ] Commit:

  ```bash
  git commit -m "refactor(knowledge): compose and read_project_draft use items-only v2 markers (#1293)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" \
    src/memoria_vault/runtime/knowledge.py
  ```

### Task S12.7: rewrite old-grammar fixtures; full gate

**Files:**
- Modify: `tests/test_evidence_sets.py:54-65` (five-marker draft fixture)
- Modify: `tests/test_mc_hash_binding.py:13` (`_MARKER` constant), `:527-534` (nonbinding-marker-text parametrize pair)
- Modify: `tests/test_code_artifacts.py:63-64` (computed-evidence fixture; `code-grounds:` prefix already applied by S12.1)
- Test: the modified files themselves (`test_evidence_sets.py` `runtime` @ `tests/conftest.py:45`, `test_mc_hash_binding.py` `runtime` @ `:65`, `test_code_artifacts.py` `runtime` @ `:30`) plus `tests/test_content_security.py` (`runtime` @ `:32`; carries no literal `%%ev:` fixtures — verified by grep — so it must pass unmodified, which is the content-security regression check spec §3 names)

**Interfaces:**
- Consumes: v2 grammar from S12.5; `state.rebuild_evidence_sets_from_markers` derivation (unchanged: DB rows still expose `type`/`state`/`review_required`, so the row-shape assertions in these tests keep their expected values)
- Produces: a green `python scripts/verify` for slices 1–2; zero v1-grammar marker text anywhere in `src/` or `tests/`

**Steps:**

- [ ] Run the failing suites to capture the failure mode: `python -m pytest tests/test_evidence_sets.py tests/test_mc_hash_binding.py tests/test_code_artifacts.py -v` — expect failures like `assert result == {"deleted": 0, "inserted": 5}` observing `inserted: 0` (the v2 parser rejects the v1 fixtures' `type=`/`state=`/`review=` fields, so rebuild skips every marker — the fail-closed behavior working as specified, against stale fixtures).
- [ ] Rewrite the draft fixture in `tests/test_evidence_sets.py:54-65`:

  ```python
      note.write_text(
          "Single span. %%ev: ev-11111111 items=source-alpha#^p0001%%\n"
          "Missing span. %%ev: ev-22222222 items=source-missing#^p0001%%\n"
          "Multi hop. %%ev: ev-33333333 items=ev-11111111%%\n"
          "Implicit. %%ev: ev-44444444 items=%%\n"
          "Missing anchor. %%ev: ev-55555555 items=source-beta#^p0001%%\n",
          encoding="utf-8",
      )
  ```

  (Row assertions below it are untouched: `type`/`state`/`review_required` are DB-derived from items, and the v1 fixture's deliberately-wrong inline `type=` values never influenced them.)
- [ ] Rewrite the marker constant in `tests/test_mc_hash_binding.py:13`:

  ```python
  _MARKER = "%%ev: ev-11111111 items=%%"
  ```

  and the second parametrize pair at lines 531–534 (two valid markers for the same id differing only in nonbinding marker text — items now carry the difference, since `review=` no longer exists):

  ```python
          (
              "%%ev: ev-22222222 items=%%",
              "%%ev: ev-22222222 items=ev-33333333%%",
          ),
  ```

- [ ] Rewrite the computed-evidence fixture in `tests/test_code_artifacts.py:62-66`:

  ```python
      draft.write_text(
          f"Computed. %%ev: ev-11111111 items=code-grounds:run-1:analysis:{output_hash}%%\n",
          encoding="utf-8",
      )
  ```

- [ ] Run to verify they pass: `python -m pytest tests/test_evidence_sets.py tests/test_mc_hash_binding.py tests/test_code_artifacts.py tests/test_content_security.py -v` — expect all pass, `test_content_security.py` unmodified.
- [ ] Confirm zero v1 marker fields remain anywhere: `grep -rn "%%ev:" src/ tests/ | grep -E "type=|state=|review="` — expect no output.
- [ ] Run the full gate: `python scripts/verify` — expect pass.
- [ ] Commit:

  ```bash
  git commit -m "test(evidence): move all marker fixtures to items-only v2 grammar (#1293)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" \
    tests/test_evidence_sets.py tests/test_mc_hash_binding.py tests/test_code_artifacts.py
  ```
# PLAN 22 — #1293-spec slices 3–5 (package S35)

Governing spec: `docs/superpowers/specs/2026-07-14-evidence-set-grounds-contract-design.md`
§4 (type rules R1–R4), §5 (transitive resolution + fail-closed cycles),
§7 (disposition content binding), §12 (slice list — this section covers slices 3, 4, 5).

All line references verified against `main` at d85d8799.

**Slice-2 coordination (applies to every marker literal in this section).** Slice 2
(marker grammar v2) reduces markers to `id + items` only. Every test fixture below is
written in the CURRENT grammar, which requires `type=`, `state=`, and `review=` fields to
parse. If slice 2 has already landed when a task here is executed, apply one mechanical
substitution to each marker literal in that task's test code:
`%%ev: <id> type=<t> state=<s> review=<r> items=<items>%%` → `%%ev: <id> items=<items>%%`.
Nothing else in the tests changes — every assertion in this section is against the
DERIVED rows returned by `state.evidence_sets(vault)` after
`state.rebuild_evidence_sets_from_markers(...)`, never against declared marker fields.
Likewise, slice 1's rename sweep may have renamed `code-warrant:` refs to `code-grounds:`;
if so, substitute the prefix in the two code-item fixtures (S35.1) and keep the 64-hex
digest shape.

No new test files are created: `tests/test_evidence_sets.py` (level `runtime`),
`tests/test_evidence_markers.py` (level `unit`), and `tests/test_draft_verification.py`
(level `runtime`) are already registered in `tests/conftest.py` `TEST_LEVELS`, so no
conftest change is needed anywhere in this package.

---

### Task S35.1: Unified grounds-type derivation R1–R4 in state.py (spec §4)

**Files:**
- Modify: `src/memoria_vault/runtime/state.py:2629-2636` (replace `_derived_evidence_type`
  with public `derive_evidence_type`) and `src/memoria_vault/runtime/state.py:2613`
  (call site inside `_derived_evidence_row`)
- Test: `tests/test_evidence_sets.py` (append after
  `test_rebuild_evidence_sets_derives_rows_from_markers`, which ends at line 89)

**Interfaces:**
- Consumes: `evidence_ref_kind(ref: str) -> str` and
  `parse_source_span_ref(ref: str) -> SourceSpanRef` (already imported in state.py at
  lines 25–31); `state.rebuild_evidence_sets_from_markers(vault: Path, *, run_id: str = "") -> dict[str, Any]`;
  `state.evidence_sets(vault: Path) -> list[dict[str, Any]]`;
  `state.upsert_catalog_record(vault, *, work_id, title, check_status, content_path)`.
- Produces: **`state.derive_evidence_type(items: list[str]) -> str`** — public, pure;
  first-match R1–R4 over the record's own items; raises `ValueError` on any
  unclassifiable item (fail closed, via `evidence_ref_kind`). This is the ONE derivation;
  Task S35.2 wires compose to it, and the slice-6 section may import it for findings.

**Steps:**

- [ ] Write the failing tests. Append to `tests/test_evidence_sets.py` (after line 89):

  ```python
  def _seed_source(vault: Path, work_id: str, text: str) -> None:
      state.upsert_catalog_record(
          vault,
          work_id=work_id,
          title=work_id,
          check_status="checked",
          content_path=f".memoria/blobs/source-content/{work_id}.md",
      )
      path = vault / f".memoria/blobs/source-content/{work_id}.md"
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text(text, encoding="utf-8")


  def _write_marker_note(vault: Path, body: str) -> None:
      note = vault / "notes" / "draft.md"
      note.parent.mkdir(parents=True, exist_ok=True)
      note.write_text(body, encoding="utf-8")


  def test_cross_work_two_span_marker_derives_multi_hop_and_requires_review(
      tmp_path: Path,
  ) -> None:
      vault = tmp_path
      _seed_source(vault, "source-alpha", "Alpha span. ^p0001\n")
      _seed_source(vault, "source-beta", "Beta span. ^p0001\n")
      _write_marker_note(
          vault,
          "Cross-work claim. %%ev: ev-aaaa0001 type=multi-span state=complete "
          "review=false items=source-alpha#^p0001|source-beta#^p0001%%\n",
      )

      state.rebuild_evidence_sets_from_markers(vault, run_id="compose-1")
      [row] = state.evidence_sets(vault)

      assert row["type"] == "multi-hop"
      assert row["review_required"] is True
      assert row["state"] == "complete"


  def test_code_and_span_mix_derives_multi_hop(tmp_path: Path) -> None:
      vault = tmp_path
      _seed_source(vault, "source-alpha", "Alpha span. ^p0001\n")
      digest = "0" * 64
      _write_marker_note(
          vault,
          "Mixed-kind claim. %%ev: ev-aaaa0002 type=computed state=complete "
          f"review=false items=code-warrant:run-1:artifact-1:sha256:{digest}"
          "|source-alpha#^p0001%%\n",
      )

      state.rebuild_evidence_sets_from_markers(vault, run_id="compose-1")
      [row] = state.evidence_sets(vault)

      assert row["type"] == "multi-hop"
      assert row["review_required"] is True


  def test_same_work_two_span_marker_stays_multi_span(tmp_path: Path) -> None:
      vault = tmp_path
      _seed_source(vault, "source-alpha", "Alpha one. ^p0001\n\nAlpha two. ^p0002\n")
      _write_marker_note(
          vault,
          "Same-work claim. %%ev: ev-aaaa0003 type=multi-span state=complete "
          "review=false items=source-alpha#^p0001|source-alpha#^p0002%%\n",
      )

      state.rebuild_evidence_sets_from_markers(vault, run_id="compose-1")
      [row] = state.evidence_sets(vault)

      assert row["type"] == "multi-span"
      assert row["review_required"] is False
      assert row["state"] == "complete"


  def test_pure_code_items_derive_computed(tmp_path: Path) -> None:
      vault = tmp_path
      digest = "0" * 64
      _write_marker_note(
          vault,
          "Computed claim. %%ev: ev-aaaa0004 type=computed state=complete "
          f"review=false items=code-warrant:run-1:artifact-1:sha256:{digest}"
          f"|code-warrant:run-2:artifact-2:sha256:{digest}%%\n",
      )

      state.rebuild_evidence_sets_from_markers(vault, run_id="compose-1")
      [row] = state.evidence_sets(vault)

      assert row["type"] == "computed"
      assert row["review_required"] is False
      assert row["state"] == "evidence-incomplete"
  ```

  The last two tests are the machine-routed regression controls the spec's R3/R4 pins
  demand (they pass before AND after the change — they pin that R2 does not overreach).

- [ ] Run the tests to verify the two new-behavior tests fail:

  ```
  python -m pytest tests/test_evidence_sets.py -v -k "cross_work or code_and_span or same_work or pure_code"
  ```

  Expected: `test_cross_work_two_span_marker_derives_multi_hop_and_requires_review` FAILS
  with `AssertionError: assert 'multi-span' == 'multi-hop'` (current derivation never
  counts works) and `test_code_and_span_mix_derives_multi_hop` FAILS with
  `AssertionError: assert 'computed' == 'multi-hop'` (any code item currently masks the
  mix). `test_same_work_two_span_marker_stays_multi_span` and
  `test_pure_code_items_derive_computed` PASS (controls).

- [ ] Write the minimal implementation. In `src/memoria_vault/runtime/state.py`, replace
  lines 2629–2636 (`_derived_evidence_type`) with:

  ```python
  def derive_evidence_type(items: list[str]) -> str:
      """Derive the grounds type from a record's own items (spec §4, rules R1-R4)."""
      if not items:
          return "implicit"
      kinds = [evidence_ref_kind(item) for item in items]
      span_works = {
          parse_source_span_ref(item).work_id
          for item, kind in zip(items, kinds, strict=True)
          if kind == "source-span"
      }
      has_code = "code-warrant" in kinds
      if "evidence-set" in kinds or len(span_works) >= 2 or (has_code and span_works):
          return "multi-hop"
      if has_code:
          return "computed"
      return "single-span" if len(items) == 1 else "multi-span"
  ```

  Then update the single call site at line 2613 inside `_derived_evidence_row`:

  ```python
      evidence_type = derive_evidence_type(items)
  ```

  Spec pins honored: distinct-work comparison happens after
  `parse_source_span_ref` normalization (`.work_id` of the parsed ref); counts are over
  the items multiset (`len(items)` — two identical spans are `multi-span`); an
  unclassifiable item raises inside `evidence_ref_kind` (fails the record closed); R3's
  "all code" guard is expressed as "code AND no span AND no set", which is equivalent to
  first-match order R2-before-R3 and cannot recreate the masking bug.
  If slice 1's rename sweep has landed, the kind strings here follow it
  (`code-warrant` → whatever `evidence_ref_kind` then returns for code refs); check
  `evidence_ref_kind` in `src/memoria_vault/runtime/evidence.py:64-71` and match it.

- [ ] Run the tests to verify they pass, plus the neighbors that exercise the rebuild path:

  ```
  python -m pytest tests/test_evidence_sets.py tests/test_evidence_markers.py tests/test_draft_verification.py -v
  ```

  Expected: all pass. (`test_rebuild_evidence_sets_derives_rows_from_markers` already
  asserts `single-span`, nested-set → `multi-hop`, and `implicit` rows — those
  expectations are unchanged under R1–R4.)

- [ ] Run the full gate:

  ```
  python scripts/verify
  ```

  Expected: exit 0.

- [ ] Commit (explicit paths only — the git index is shared per checkout):

  ```
  git add src/memoria_vault/runtime/state.py tests/test_evidence_sets.py
  git commit -m "feat(evidence): derive grounds type by spec rules R1-R4" -m "Cross-work spans and code+non-code mixes now route to multi-hop (PI review); pure code stays computed. One derivation, owned by state.py (#1293 slice 3, spec §4)." -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task S35.2: Compose delegates to `derive_evidence_type`; delete `_draft_evidence_type`; fix the wrong marker fixture

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py:2012` (call site in
  `compose_project_draft`) and `src/memoria_vault/runtime/knowledge.py:3216-3219`
  (delete `_draft_evidence_type`)
- Modify: `tests/test_evidence_markers.py:18-33`
  (`test_evidence_marker_round_trips_canonical_form` declares `multi-span` for a
  span+set item mix — under R2 that shape is `multi-hop`)
- Test: existing suites `tests/test_draft_verification.py`, `tests/test_draft_compose.py`,
  `tests/test_evidence_markers.py` (this is a deletion/refactor task; behavior for every
  input compose can produce — zero items or spans of a single work, since the retired
  `evidence_set:` frontmatter field is `forbidden` in the note schema — is identical, and
  the R1–R4 rules themselves gained their tests in S35.1)

**Interfaces:**
- Consumes: `state.derive_evidence_type(items: list[str]) -> str` (from S35.1;
  `knowledge.py` already has `from memoria_vault.runtime import state` at line 20).
- Produces: none new. `_draft_evidence_type` ceases to exist — no other section may
  reference it.

**Steps:**

- [ ] Fix the wrong fixture. In `tests/test_evidence_markers.py`, line 21, change:

  ```python
          evidence_type="multi-span",
  ```

  to:

  ```python
          evidence_type="multi-hop",
  ```

  and in the expected serialization at line 30, change `"type=multi-span"` to
  `"type=multi-hop"`:

  ```python
      assert text == (
          "%%ev: ev-deadbeef type=multi-hop state=complete "
          "review=true items=source-alpha#^p0001|ev-feedcafe%%"
      )
  ```

  (Slice-2 coordination: if slice 2 landed first, this test already has no
  `evidence_type` field or `type=` output — in that case there is nothing to fix here;
  record that in the commit message and skip these two edits.)

- [ ] Run the fixture test to verify it still passes:

  ```
  python -m pytest tests/test_evidence_markers.py::test_evidence_marker_round_trips_canonical_form -v
  ```

  Expected: PASS (serializer round-trips any declared type; the fix makes the fixture
  spec-truthful so slice 2's derivation-aware grammar work inherits a correct example).

- [ ] Write the minimal implementation. In `src/memoria_vault/runtime/knowledge.py`:

  Change line 2012 from:

  ```python
          evidence_type = _draft_evidence_type(items)
  ```

  to:

  ```python
          evidence_type = state.derive_evidence_type(items)
  ```

  Delete lines 3216–3219 entirely:

  ```python
  def _draft_evidence_type(items: list[str]) -> str:
      if not items:
          return "implicit"
      return "single-span" if len(items) == 1 else "multi-span"
  ```

- [ ] Verify no reference to the deleted function survives:

  ```
  grep -rn "_draft_evidence_type" src tests
  ```

  Expected: no output.

- [ ] Run the affected suites:

  ```
  python -m pytest tests/test_draft_compose.py tests/test_draft_verification.py tests/test_evidence_markers.py tests/test_evidence_sets.py -v
  ```

  Expected: all pass.

- [ ] Run the full gate:

  ```
  python scripts/verify
  ```

  Expected: exit 0.

- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/knowledge.py tests/test_evidence_markers.py
  git commit -m "refactor(evidence): compose delegates type derivation to state.derive_evidence_type" -m "Deletes the divergent _draft_evidence_type; fixes the round-trip fixture that declared multi-span for a span+set mix (#1293 slice 3, spec §4 'one derivation, one owner')." -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task S35.3: Transitive nested-set completeness with fail-closed cycles (spec §5)

**Files:**
- Modify: `src/memoria_vault/runtime/state.py:2562-2578` (rebuild wiring in
  `_evidence_marker_rows`), `src/memoria_vault/runtime/state.py:2603-2626`
  (`_derived_evidence_row` signature), `src/memoria_vault/runtime/state.py:2639-2661`
  (delete presence-only `_evidence_items_resolve`, add `_evidence_set_states`)
  — these are the pre-S35.1 line anchors; after S35.1 lands they shift by ~+2 lines
  (locate by function name).
- Test: `tests/test_evidence_sets.py` (append after the S35.1 tests)

**Interfaces:**
- Consumes: `_code_warrant_resolves(vault: Path, item: str) -> bool` (state.py:2664,
  kept as-is), `_source_span_pages(vault: Path) -> dict[str, set[str]]` (state.py:2676),
  `evidence_ref_kind`, `parse_source_span_ref`.
- Produces:
  - **`_evidence_set_states(vault: Path, items_by_id: dict[str, tuple[str, ...]], *, source_spans: dict[str, set[str]]) -> dict[str, str]`**
    (private to state.py) — maps every marker id to `"complete"` /
    `"evidence-incomplete"`; DFS over the nested-set reference graph, memoized,
    back-edge ⇒ every member of the cycle path lands `evidence-incomplete` (fail
    closed); a set item resolves iff the target id exists in `items_by_id` AND its
    computed state is `"complete"`.
  - **Changed private signature:** `_derived_evidence_row(vault: Path, rel: str, marker: EvidenceMarker, *, state_value: str, run_id: str) -> dict[str, Any]`
    (drops `marker_ids` and `source_spans` — state is now computed by the caller).
  - `_evidence_items_resolve` ceases to exist — no other section may reference it.

**Steps:**

- [ ] Write the failing tests. Append to `tests/test_evidence_sets.py`:

  ```python
  def test_nested_incomplete_child_flips_parent_incomplete(tmp_path: Path) -> None:
      vault = tmp_path
      _write_marker_note(
          vault,
          "Child. %%ev: ev-bbbb0001 type=single-span state=complete "
          "review=false items=source-missing#^p0001%%\n"
          "Parent. %%ev: ev-bbbb0002 type=multi-hop state=complete "
          "review=true items=ev-bbbb0001%%\n",
      )

      state.rebuild_evidence_sets_from_markers(vault, run_id="compose-1")
      rows = {row["id"]: row for row in state.evidence_sets(vault)}

      assert rows["ev-bbbb0001"]["state"] == "evidence-incomplete"
      assert rows["ev-bbbb0002"]["state"] == "evidence-incomplete"


  def test_mutually_referencing_sets_are_both_incomplete(tmp_path: Path) -> None:
      vault = tmp_path
      _write_marker_note(
          vault,
          "One. %%ev: ev-cccc0001 type=multi-hop state=complete "
          "review=true items=ev-cccc0002%%\n"
          "Two. %%ev: ev-cccc0002 type=multi-hop state=complete "
          "review=true items=ev-cccc0001%%\n",
      )

      state.rebuild_evidence_sets_from_markers(vault, run_id="compose-1")
      rows = {row["id"]: row for row in state.evidence_sets(vault)}

      assert rows["ev-cccc0001"]["state"] == "evidence-incomplete"
      assert rows["ev-cccc0002"]["state"] == "evidence-incomplete"


  def test_self_referencing_set_is_incomplete(tmp_path: Path) -> None:
      vault = tmp_path
      _write_marker_note(
          vault,
          "Loop. %%ev: ev-dddd0001 type=multi-hop state=complete "
          "review=true items=ev-dddd0001%%\n",
      )

      state.rebuild_evidence_sets_from_markers(vault, run_id="compose-1")
      [row] = state.evidence_sets(vault)

      assert row["state"] == "evidence-incomplete"


  def test_healthy_nested_chain_stays_complete(tmp_path: Path) -> None:
      vault = tmp_path
      _seed_source(vault, "source-alpha", "Alpha span. ^p0001\n")
      _write_marker_note(
          vault,
          "Leaf. %%ev: ev-eeee0001 type=single-span state=complete "
          "review=false items=source-alpha#^p0001%%\n"
          "Chain. %%ev: ev-eeee0002 type=multi-hop state=complete "
          "review=true items=ev-eeee0001%%\n",
      )

      state.rebuild_evidence_sets_from_markers(vault, run_id="compose-1")
      rows = {row["id"]: row for row in state.evidence_sets(vault)}

      assert rows["ev-eeee0001"]["state"] == "complete"
      assert rows["ev-eeee0002"]["state"] == "complete"
      assert rows["ev-eeee0002"]["type"] == "multi-hop"
  ```

- [ ] Run the tests to verify the three cycle/nesting tests fail:

  ```
  python -m pytest tests/test_evidence_sets.py -v -k "nested_incomplete or mutually_referencing or self_referencing or healthy_nested"
  ```

  Expected: `test_nested_incomplete_child_flips_parent_incomplete` FAILS
  (`assert 'complete' == 'evidence-incomplete'` for `ev-bbbb0002` — presence-only check),
  `test_mutually_referencing_sets_are_both_incomplete` FAILS (both derive `complete`
  today with zero source spans between them), `test_self_referencing_set_is_incomplete`
  FAILS (id is in `marker_ids`, so it "resolves" against itself).
  `test_healthy_nested_chain_stays_complete` PASSES (control).

- [ ] Write the minimal implementation in `src/memoria_vault/runtime/state.py`.

  (a) Replace `_evidence_items_resolve` (currently lines 2639–2661; locate by name) with:

  ```python
  def _evidence_set_states(
      vault: Path,
      items_by_id: dict[str, tuple[str, ...]],
      *,
      source_spans: dict[str, set[str]],
  ) -> dict[str, str]:
      """Resolve completeness bottom-up over nested sets; cycles fail closed (spec §5)."""
      states: dict[str, str] = {}

      def visit(evidence_id: str, visiting: frozenset[str]) -> str:
          known = states.get(evidence_id)
          if known is not None:
              return known
          if evidence_id in visiting:
              return "evidence-incomplete"
          visiting = visiting | {evidence_id}
          items = items_by_id.get(evidence_id) or ()
          complete = bool(items)
          for item in items:
              kind = evidence_ref_kind(item)
              if kind == "code-warrant":
                  resolved = _code_warrant_resolves(vault, item)
              elif kind == "evidence-set":
                  resolved = item in items_by_id and visit(item, visiting) == "complete"
              else:
                  source = parse_source_span_ref(item)
                  resolved = source.page in source_spans.get(source.work_id, set())
              if not resolved:
                  complete = False
                  break
          states[evidence_id] = "complete" if complete else "evidence-incomplete"
          return states[evidence_id]

      for evidence_id in sorted(items_by_id):
          visit(evidence_id, frozenset())
      return states
  ```

  Correctness note for the reviewer: a back-edge hit (`evidence_id in visiting`) returns
  `evidence-incomplete` WITHOUT memoizing the probed node; the verdict then propagates
  and memoizes along the unwind, so every node on the cycle path lands incomplete —
  never fixpoint-guessed. Memoized verdicts are path-independent: only genuine cycle
  members ever see themselves in `visiting`, and cycle members are genuinely incomplete,
  so cross-path reuse is sound. Recursive DFS is the smallest honest mechanism; drafts
  are human-scale documents, nowhere near recursion limits.

  (b) In `_evidence_marker_rows`, replace lines 2562–2578 (from `marker_ids = ...`
  through the loop body; locate by the `marker_ids` assignment) with:

  ```python
      items_by_id = {
          marker.evidence_id: tuple(marker.items)
          for _rel, marker, _bind, _prior in selected
      }
      source_spans = _source_span_pages(vault)
      states = _evidence_set_states(vault, items_by_id, source_spans=source_spans)
      rows = []
      for rel, marker, bind, prior_block_ref in selected:
          row = _derived_evidence_row(
              vault,
              rel,
              marker,
              state_value=states[marker.evidence_id],
              run_id=run_id,
          )
          if prior_block_ref is not None:
              row["block_ref"] = prior_block_ref
              row["block_text_sha256"] = _block_text_sha256(vault, prior_block_ref)
          row["bind"] = bind
          rows.append(row)
      return rows, duplicate_ids
  ```

  (c) Replace `_derived_evidence_row` (currently lines 2603–2626; locate by name) with:

  ```python
  def _derived_evidence_row(
      vault: Path,
      rel: str,
      marker: EvidenceMarker,
      *,
      state_value: str,
      run_id: str,
  ) -> dict[str, Any]:
      items = list(marker.items)
      evidence_type = derive_evidence_type(items)
      block_ref = _evidence_block_ref(rel, marker.evidence_id)
      return {
          "id": marker.evidence_id,
          "block_ref": block_ref,
          "items": items,
          "type": evidence_type,
          "state": state_value,
          "review_required": evidence_type in {"implicit", "multi-hop"},
          "run_id": run_id,
          "block_text_sha256": _block_text_sha256(vault, block_ref),
      }
  ```

  Keep `_code_warrant_resolves` (state.py:2664–2673) unchanged — it is still the code
  leaf of resolution.

- [ ] Verify no reference to the deleted function survives:

  ```
  grep -rn "_evidence_items_resolve" src tests
  ```

  Expected: no output.

- [ ] Run the tests to verify they pass, plus the rebuild-path neighbors:

  ```
  python -m pytest tests/test_evidence_sets.py tests/test_draft_verification.py tests/test_code_artifacts.py -v
  ```

  Expected: all pass. (The existing `ev-33333333` expectation — nested set over a
  complete child stays `complete` — is exactly the healthy-chain case.)

- [ ] Run the full gate:

  ```
  python scripts/verify
  ```

  Expected: exit 0.

- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/state.py tests/test_evidence_sets.py
  git commit -m "feat(evidence): transitive nested-set completeness with fail-closed cycles" -m "Nested set items resolve iff the target exists and is itself complete, computed bottom-up; cycle members (including self-reference) derive evidence-incomplete. Replaces the presence-only check (#1293 slice 4, spec §5)." -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task S35.4: PI dispositions bound to items content (spec §7)

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py:2268-2297` (`resolve_evidence_review`:
  look up the record, journal `items_sha256`), `src/memoria_vault/runtime/knowledge.py:2187`
  (`disposed = _disposed_evidence_ids(vault)` in `verify_project_draft`'s finding loop),
  `src/memoria_vault/runtime/knowledge.py:2224-2225` (the `if row["id"] in disposed:
  continue` suppression site), `src/memoria_vault/runtime/knowledge.py:3241-3251`
  (`_disposed_evidence_ids` becomes `_disposed_evidence_digests`) — pre-S35.2 anchors;
  after S35.2's deletion the `~3241` block shifts up by 6 lines (locate by name).
- Test: `tests/test_draft_verification.py` (append after
  `test_evidence_review_disposition_clears_draft_gate`, which ends at line 343)

**Interfaces:**
- Consumes: `state.evidence_sets(vault: Path) -> list[dict[str, Any]]`;
  `append_explicit_journal_event(vault, event, *, actor, machine) -> dict[str, Any]`
  (trusted_writer.py:215); `hashlib` (already imported in knowledge.py, line 5).
- Produces:
  - **`_evidence_items_sha256(items: Iterable[str]) -> str`** (private to knowledge.py) —
    hex SHA-256 over the UTF-8 bytes of the ordered items joined by `"|"` (the exact
    serialized `items=` form; empty items ⇒ digest of the empty string).
  - **`_disposed_evidence_digests(vault: Path) -> dict[str, str]`** (private; REPLACES
    `_disposed_evidence_ids` — the set-returning function ceases to exist) — latest
    disposition per evidence id wins; legacy events without `items_sha256` are omitted
    (inert, fail closed).
  - `resolve_evidence_review` keeps its signature
    `(vault: Path, evidence_id: str, *, actor: str, machine: str, decision: str, reason: str = "") -> dict[str, Any]`
    but (1) raises `ValueError("unknown evidence id: …")` when no evidence-set record
    exists for the id, and (2) the returned/journaled event gains an `items_sha256` key.
    Slice-7's `evidence-minted` section and any CLI/docs section must honor both.

**Steps:**

- [ ] Write the failing tests. In `tests/test_draft_verification.py`, add `import hashlib`
  after line 4 (`from pathlib import Path`), then append after line 343:

  ```python
  def test_disposition_event_records_items_digest(tmp_path: Path) -> None:
      vault = tmp_path
      _project(vault)
      write_checked_concept(
          vault,
          "notes/thesis.md",
          "type: note\ncheck_status: checked\ntitle: Thesis\nid: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
          "note",
          body="This implicit claim gets a content-bound disposition.",
      )
      _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — Thesis\n")
      result = compose_project_draft(vault, "project-alpha")
      evidence_id = result["evidence_markers"][0]["id"]

      event = resolve_evidence_review(vault, evidence_id, decision="accept", reason="PI accepted")

      assert event["items_sha256"] == hashlib.sha256(b"").hexdigest()


  def test_editing_items_voids_prior_disposition(tmp_path: Path) -> None:
      vault = tmp_path
      _project(vault)
      write_checked_concept(
          vault,
          "notes/thesis.md",
          "type: note\ncheck_status: checked\ntitle: Thesis\nid: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
          "note",
          body="This implicit claim was accepted, then its grounds changed.",
      )
      _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — Thesis\n")
      result = compose_project_draft(vault, "project-alpha")
      evidence_id = result["evidence_markers"][0]["id"]
      resolve_evidence_review(vault, evidence_id, decision="accept", reason="PI accepted")
      assert verify_project_draft(vault, "project-alpha")["ready"] is True

      draft = vault / "projects/project-alpha/draft.md"
      draft.write_text(
          draft.read_text(encoding="utf-8").replace(
              "items=%%",
              "items=source-missing#^p0001%%",
          ),
          encoding="utf-8",
      )
      verification = verify_project_draft(vault, "project-alpha")

      assert verification["ready"] is False
      assert "evidence-incomplete" in {
          finding["kind"] for finding in verification["findings"]
      }


  def test_disposition_requires_matching_evidence_record(tmp_path: Path) -> None:
      with pytest.raises(ValueError, match="unknown evidence id"):
          resolve_evidence_review(tmp_path, "ev-deadbeef", decision="accept", reason="none")
  ```

  Two load-bearing facts make the void test honest: `verify_project_draft` rebuilds
  evidence rows itself (knowledge.py:2162), so no manual rebuild call is needed after the
  edit; and `_block_text_sha256_from_text` (state.py:2705–2754) excises both the anchor
  and the marker from the canonical block text before hashing, so editing `items=` inside
  the marker does NOT trip `evidence-text-drift` — the finding that returns is exactly the
  disposition-voided `evidence-incomplete` hold, nothing else masking it. The
  accept-clears-findings case is already pinned by
  `test_evidence_review_disposition_clears_draft_gate` (line 325) and must stay green.
  (Slice-2 coordination: `"items=%%"` is the tail of the composed implicit marker in both
  grammars, so the replace target is stable.)

- [ ] Run the tests to verify they fail:

  ```
  python -m pytest tests/test_draft_verification.py -v -k "items_digest or voids_prior or matching_evidence_record"
  ```

  Expected: `test_disposition_event_records_items_digest` FAILS with
  `KeyError: 'items_sha256'`; `test_editing_items_voids_prior_disposition` FAILS at
  `assert verification["ready"] is False` (an accepted id is currently suppressed
  forever, regardless of item edits); `test_disposition_requires_matching_evidence_record`
  FAILS with `DID NOT RAISE`.

- [ ] Write the minimal implementation in `src/memoria_vault/runtime/knowledge.py`.

  (a) Immediately before `_disposed_evidence_ids` (currently line 3241; locate by name),
  add:

  ```python
  def _evidence_items_sha256(items: Iterable[str]) -> str:
      return hashlib.sha256("|".join(items).encode("utf-8")).hexdigest()
  ```

  (b) Replace `_disposed_evidence_ids` (lines 3241–3251) with:

  ```python
  def _disposed_evidence_digests(vault: Path) -> dict[str, str]:
      """Map disposed evidence ids to the items digest each disposition bound (spec §7)."""
      with state.connect(vault) as conn:
          rows = conn.execute(
              """
              SELECT json_extract(payload_json, '$.evidence_id') AS evidence_id,
                     json_extract(payload_json, '$.items_sha256') AS items_sha256
              FROM event_log
              WHERE json_extract(payload_json, '$.operation') = 'resolve-evidence-review'
                AND json_extract(payload_json, '$.decision') IN ('accept', 'reject')
              ORDER BY rowid
              """
          ).fetchall()
      return {
          str(row["evidence_id"]): str(row["items_sha256"])
          for row in rows
          if row["evidence_id"] and row["items_sha256"]
      }
  ```

  (`ORDER BY rowid` + dict overwrite ⇒ the latest disposition per id wins; pre-binding
  events have `items_sha256 = NULL` and are dropped — the journal keeps them, they are
  simply inert, exactly the spec's voiding semantics.)

  (c) In `verify_project_draft`'s finding loop, change line 2187 from:

  ```python
      disposed = _disposed_evidence_ids(vault)
  ```

  to:

  ```python
      disposed = _disposed_evidence_digests(vault)
  ```

  and lines 2224–2225 from:

  ```python
          if row["id"] in disposed:
              continue
  ```

  to:

  ```python
          if disposed.get(row["id"]) == _evidence_items_sha256(row["items"]):
              continue
  ```

  (d) In `resolve_evidence_review` (lines 2268–2297), after the decision validation
  (line 2285) and before the `return append_explicit_journal_event(...)`, insert:

  ```python
      record = next(
          (row for row in state.evidence_sets(Path(vault)) if row["id"] == evidence_id),
          None,
      )
      if record is None:
          raise ValueError(f"unknown evidence id: {evidence_id}")
  ```

  and add the digest to the event payload dict (after the `"decision"` entry):

  ```python
              "decision": decision,
              "reason": reason.strip(),
              "items_sha256": _evidence_items_sha256(record["items"]),
  ```

  The CLI already refuses ids outside the current draft
  (`src/memoria_vault/cli.py:1133-1138`), so the new `ValueError` only hardens direct
  runtime callers — same contract, now enforced at the seam that journals.

- [ ] Verify no reference to the replaced function survives:

  ```
  grep -rn "_disposed_evidence_ids" src tests
  ```

  Expected: no output.

- [ ] Run the tests to verify they pass, including the pre-existing disposition tests:

  ```
  python -m pytest tests/test_draft_verification.py -v
  ```

  Expected: all pass — in particular
  `test_evidence_review_disposition_clears_draft_gate` (accept still clears: the digest
  recorded at disposition matches the unchanged row) and
  `test_draft_text_drift_overrides_pi_disposition_and_refuses_export` (drift remains a
  permanent block a disposition never touches).

- [ ] Run the full gate:

  ```
  python scripts/verify
  ```

  Expected: exit 0.

- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/knowledge.py tests/test_draft_verification.py
  git commit -m "feat(evidence): bind PI dispositions to the items content digest" -m "resolve-evidence-review journals items_sha256 (sha256 of ordered items joined by '|'); verification honors a disposition only while the record's current items digest matches, so editing the grounds voids the acceptance (#1293 slice 5, spec §7)." -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```
# PLAN 22 — #1293 spec slices 6–8 (package S68)

Governing spec: `docs/superpowers/specs/2026-07-14-evidence-set-grounds-contract-design.md`
§6 (findings and export refusal), §8 (mint durability), §12 (slices 6–8).

Sequencing: this package lands **after** S35 (slices 3–5: unified derivation,
transitive resolution/closure, disposition `items_sha256`) and after the
slice-1/2 rename+grammar package. All line refs below are against `main @
d85d8799` (pre-S35); every Modify: entry quotes enough surrounding text to
re-anchor by grep if earlier packages shifted lines.

Cross-package interfaces this section consumes (S35 must produce exactly these
— see the manifest at the end):

- `state.evidence_item_closure(rows_by_id: Mapping[str, Mapping[str, Any]], evidence_id: str) -> list[tuple[str, tuple[str, ...]]]`
  (S35 slice 4). Each element is `(item, path)`: `item` is a non-set item
  string (source-span or code ref) reachable from the record's **own** items
  transitively through nested `ev-` refs resolved against `rows_by_id`;
  `path` is the tuple of nested evidence ids traversed, in order (empty tuple
  = the record's own direct item); a set id already on the current path is
  not re-entered (cycle-safe); a set ref absent from `rows_by_id` yields
  nothing (its incompleteness is slice 4's resolution concern, not closure's).
- `knowledge.resolve_evidence_review(vault, evidence_id, *, actor, machine, decision, reason="")`
  keeps its public signature after S35 slice 5 (it computes `items_sha256`
  internally from the current record; callers do not pass it).
- Marker grammar is v2 after slice 2: `%%ev: ev-<8hex> items=<item>|<item>%%`
  — hand-written test drafts below use v2 and parse only post-slice-2.

Test registration: all new tests go into `tests/test_draft_verification.py`
(already `"runtime"` in `tests/conftest.py` `TEST_LEVELS`, line 37) and the
existing `tests/test_evidence_sets.py` (`"runtime"`, line 44). No conftest
change is needed in this package.

---

### Task S68.1: Name the empty-draft refusal — `no-evidence-set` blocking finding

Today a draft with zero evidence sets silently computes
`ok = not findings and bool(draft["evidence_sets"])` (knowledge.py:2249) —
`ready` is `False` but `missing` can be empty and no finding says why. Spec §6
names it: `no-evidence-set`, severity high, permanent block.

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py:2173-2186` (append finding
  after the `evidence-id-duplicate` list comprehension), `:2249` (the
  `ok = not findings and bool(...)` line).
- Test: `tests/test_draft_verification.py` (new test appended after
  `test_analysis_keyword_number_requires_declared_evidence`, i.e. after
  line 322).

**Interfaces:**
- Consumes: `verify_project_draft(vault, project_path, *, context, max_findings=20) -> dict[str, Any]` (existing, knowledge.py:2114).
- Produces: new finding shape `{"kind": "no-evidence-set", "severity": "high"}`
  in `verify_project_draft(...)["findings"]` whenever
  `draft["evidence_sets"]` is empty; `ready`/`ok` semantics unchanged
  (still `False` for that draft), `missing` now names it.

**Steps:**

- [ ] Write the failing test. Append to `tests/test_draft_verification.py`
  (uses the file's existing `_project` helper and `verify_project_draft`
  wrapper):

  ```python
  def test_draft_with_zero_evidence_sets_reports_no_evidence_set_finding(
      tmp_path: Path,
  ) -> None:
      vault = tmp_path
      _project(vault)
      draft = vault / "projects/project-alpha/draft.md"
      draft.parent.mkdir(parents=True, exist_ok=True)
      draft.write_text(
          "---\ntype: draft\nproject: projects/project-alpha/project.md\n---\n\n"
          "# Alpha project\n\nA claim with no evidence marker at all.\n",
          encoding="utf-8",
      )

      verification = verify_project_draft(vault, "project-alpha")

      assert verification["ready"] is False
      assert verification["ok"] is False
      assert [finding["kind"] for finding in verification["findings"]] == [
          "no-evidence-set",
          "missing-structural-reference",
      ]
      assert verification["missing"] == [
          "no-evidence-set",
          "missing-structural-reference",
      ]
  ```

  (The hand-written draft has no `Source note:` line, so
  `missing-structural-reference` is expected alongside — asserting the full
  ordered list pins the insertion point.)
- [ ] Run to verify it fails:
  `python -m pytest tests/test_draft_verification.py::test_draft_with_zero_evidence_sets_reports_no_evidence_set_finding -v`
  — expected failure: findings list is `["missing-structural-reference"]`
  (no `no-evidence-set` entry).
- [ ] Write the minimal implementation. In
  `src/memoria_vault/runtime/knowledge.py`, directly after the
  `evidence-id-duplicate` findings comprehension (after the line
  `for evidence_id in sorted(duplicate_ids & draft_occurrence_ids)` and its
  closing `]`, currently line 2186), insert:

  ```python
      if not draft["evidence_sets"]:
          findings.append({"kind": "no-evidence-set", "severity": "high"})
  ```

  Then replace line 2249:

  ```python
      ok = not findings and bool(draft["evidence_sets"])
  ```

  with:

  ```python
      ok = not findings
  ```

  (`bool(draft["evidence_sets"])` is now redundant: the empty case always
  contributes the named blocking finding, so `ok` semantics are unchanged and
  `missing` is honest.)
- [ ] Run to verify it passes:
  `python -m pytest tests/test_draft_verification.py::test_draft_with_zero_evidence_sets_reports_no_evidence_set_finding -v`
- [ ] Run the neighbors to catch regressions:
  `python -m pytest tests/test_draft_verification.py tests/test_draft_compose.py tests/test_evidence_sets.py -q`
- [ ] Commit:

  ```bash
  git add src/memoria_vault/runtime/knowledge.py tests/test_draft_verification.py
  git commit -m "feat(verify): name the empty-draft refusal as a no-evidence-set finding (#1293 slice 6a)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task S68.2: Live catalog-standing findings — `evidence-source-stale` (blocking) and `evidence-source-archived` (advisory)

Spec §6: any work in a record's item closure with standing
`retracted`/`superseded` raises `evidence-source-stale` (high, permanent
block, **not** PI-disposable, carries `{work_id, path}`); standing `archived`
raises `evidence-source-archived` (medium, advisory, must never flip
`ready`). Standing is joined live at verify time; unset standing is
`current` by contract. Advisory findings must be excluded from the readiness
predicate, so this task introduces an honest blocking/advisory split.

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py:765-770`
  (`_is_current_catalog_source` — split a `_catalog_source_standing` reader
  out of it), `:2244-2257` (append standing findings; replace the
  truncate-then-`ok` block with a blocking-aware one), `:2591`
  (`render_project_draft_export_markdown` refusal reasons must not list
  advisories).
- Test: `tests/test_draft_verification.py` (four new tests + one local
  helper).

**Interfaces:**
- Consumes: `state.evidence_item_closure(rows_by_id, evidence_id) -> list[tuple[str, tuple[str, ...]]]`
  (S35 slice 4 Produces — exact contract in the package preamble);
  `state.catalog_sources(vault, *, checked_only=True) -> list[dict[str, Any]]`
  (state.py:1615, called with `checked_only=False`);
  `evidence_ref_kind(ref) -> str` and `parse_source_span_ref(ref) -> SourceSpanRef`
  (`memoria_vault/runtime/evidence.py:64,44`, imported lazily per this file's
  existing pattern at knowledge.py:1975/3329);
  `resolve_evidence_review(...)` (knowledge.py:2268, post-S35 signature per
  preamble).
- Produces:
  - `_catalog_source_standing(source: dict[str, Any]) -> str` (knowledge.py,
    module-private) — returns the PI-curated standing string; unset/blank
    maps to `"current"` by contract.
  - `_evidence_source_standing_findings(vault: Path, draft_rows: list[dict[str, Any]]) -> list[dict[str, Any]]`
    (knowledge.py, module-private) — finding dicts
    `{"kind", "severity", "evidence_id", "block_ref", "work_id", "path"}`
    with `path: list[str]` (empty = direct, non-empty = the nested ev-id
    chain).
  - Module constants `_ADVISORY_FINDING_KINDS = frozenset({"evidence-source-archived"})`
    and `_STALE_STANDINGS = frozenset({"retracted", "superseded"})`.
  - Contract for every later consumer: `verify_project_draft(...)["ready"]`
    / `["ok"]` / `["missing"]` are computed from **blocking** findings only
    (`kind not in _ADVISORY_FINDING_KINDS`); advisory findings still appear
    in `["findings"]`.

**Steps:**

- [ ] Add the standing-flip helper to `tests/test_draft_verification.py`
  (next to `_source_span`, after line 966):

  ```python
  def _set_source_standing(vault: Path, work_id: str, standing: str) -> None:
      state.upsert_catalog_record(
          vault,
          work_id=work_id,
          title=f"{work_id} title",
          check_status="checked",
          content_path=f".memoria/blobs/source-content/{work_id}.md",
          csl_json={"memoria": {"standing": standing}},
      )
  ```

- [ ] Write the failing tests (all four, appended to
  `tests/test_draft_verification.py`):

  ```python
  @pytest.mark.parametrize("standing", ["retracted", "superseded"])
  def test_stale_source_blocks_draft_and_pi_disposition_cannot_clear_it(
      tmp_path: Path, standing: str
  ) -> None:
      _draft, evidence_id = _compose_source_backed_draft(
          tmp_path, body="Claim over a source that later loses standing."
      )
      [bound] = state.evidence_sets(tmp_path)
      assert verify_project_draft(tmp_path, "project-alpha")["ready"] is True

      _set_source_standing(tmp_path, "source-alpha", standing)
      verification = verify_project_draft(tmp_path, "project-alpha")

      assert verification["ready"] is False
      stale = [
          finding
          for finding in verification["findings"]
          if finding["kind"] == "evidence-source-stale"
      ]
      assert stale == [
          {
              "kind": "evidence-source-stale",
              "severity": "high",
              "evidence_id": evidence_id,
              "block_ref": bound["block_ref"],
              "work_id": "source-alpha",
              "path": [],
          }
      ]
      assert f"evidence-source-stale:{evidence_id}" in verification["missing"]

      resolve_evidence_review(
          tmp_path, evidence_id, decision="accept", reason="PI cannot clear staleness"
      )
      after = verify_project_draft(tmp_path, "project-alpha")

      assert after["ready"] is False
      assert any(
          finding["kind"] == "evidence-source-stale" for finding in after["findings"]
      )
      with pytest.raises(ValueError, match="evidence-source-stale"):
          write_project_export(tmp_path, "project-alpha", draft=True)


  def test_stale_taint_propagates_through_nested_sets_with_path(tmp_path: Path) -> None:
      vault = tmp_path
      state.upsert_catalog_record(
          vault,
          work_id="source-alpha",
          title="Alpha Source",
          check_status="checked",
          content_path=".memoria/blobs/source-content/source-alpha.md",
      )
      _source_span(vault, "source-alpha")
      _project(vault)
      draft = vault / "projects/project-alpha/draft.md"
      draft.parent.mkdir(parents=True, exist_ok=True)
      draft.write_text(
          "---\ntype: draft\nproject: projects/project-alpha/project.md\n---\n\n"
          "# Alpha project\n\n"
          "Direct claim. ^blk-aaaa1111 %%ev: ev-aaaa1111 items=source-alpha#^p0001%%\n\n"
          "Nested claim. ^blk-bbbb2222 %%ev: ev-bbbb2222 items=ev-aaaa1111%%\n",
          encoding="utf-8",
      )
      _set_source_standing(vault, "source-alpha", "retracted")

      verification = verify_project_draft(vault, "project-alpha")

      stale = sorted(
          (finding["evidence_id"], finding["work_id"], finding["path"])
          for finding in verification["findings"]
          if finding["kind"] == "evidence-source-stale"
      )
      assert stale == [
          ("ev-aaaa1111", "source-alpha", []),
          ("ev-bbbb2222", "source-alpha", ["ev-aaaa1111"]),
      ]
      assert verification["ready"] is False


  def test_archived_source_is_advisory_and_never_blocks_export(tmp_path: Path) -> None:
      _compose_source_backed_draft(tmp_path, body="Claim over an archived source.")
      _set_source_standing(tmp_path, "source-alpha", "archived")

      verification = verify_project_draft(tmp_path, "project-alpha")

      assert verification["ready"] is True
      assert verification["ok"] is True
      assert verification["missing"] == []
      archived = [
          finding
          for finding in verification["findings"]
          if finding["kind"] == "evidence-source-archived"
      ]
      assert [finding["severity"] for finding in archived] == ["medium"]
      assert archived[0]["work_id"] == "source-alpha"
      assert archived[0]["path"] == []
      exported = write_project_export(tmp_path, "project-alpha", draft=True)
      assert "%%ev:" not in exported["content"]


  def test_unset_standing_is_current_and_raises_no_standing_finding(
      tmp_path: Path,
  ) -> None:
      _compose_source_backed_draft(tmp_path, body="Claim over a source without standing.")

      verification = verify_project_draft(tmp_path, "project-alpha")

      assert verification["ready"] is True
      assert not any(
          finding["kind"].startswith("evidence-source-")
          for finding in verification["findings"]
      )
  ```

  (The nested-path test writes v2 markers by hand — it parses only after the
  slice-2 grammar package, which precedes this one.)
- [ ] Run to verify they fail:
  `python -m pytest tests/test_draft_verification.py -k "stale or archived or unset_standing" -v`
  — expected: the stale/archived tests fail with `ready is True` after the
  standing flip and empty `stale`/`archived` filtered lists; the
  unset-standing control may already pass (it pins existing behavior).
- [ ] Write the implementation, part 1 — standing reader split. Replace
  `src/memoria_vault/runtime/knowledge.py:765-770`:

  ```python
  def _is_current_catalog_source(source: dict[str, Any]) -> bool:
      csl = source.get("csl_json") if isinstance(source.get("csl_json"), dict) else {}
      memoria = csl.get("memoria") if isinstance(csl.get("memoria"), dict) else {}
      standing = str(memoria.get("standing") or "")
      return standing not in {"archived", "retracted", "superseded"}
  ```

  with:

  ```python
  def _catalog_source_standing(source: dict[str, Any]) -> str:
      csl = source.get("csl_json") if isinstance(source.get("csl_json"), dict) else {}
      memoria = csl.get("memoria") if isinstance(csl.get("memoria"), dict) else {}
      # Unset standing is `current` by contract: standing is PI-curated catalog
      # state and the PI is the standing authority (2026-07-14 spec §6).
      return str(memoria.get("standing") or "") or "current"


  def _is_current_catalog_source(source: dict[str, Any]) -> bool:
      return _catalog_source_standing(source) not in {"archived", "retracted", "superseded"}
  ```

- [ ] Write the implementation, part 2 — module constants and the findings
  helper. Add next to the other module constants (after the `GAP_KINDS`
  block, knowledge.py:57-63):

  ```python
  _STALE_STANDINGS = frozenset({"retracted", "superseded"})
  _ADVISORY_FINDING_KINDS = frozenset({"evidence-source-archived"})
  ```

  Add the helper directly after `_disposed_evidence_ids`
  (knowledge.py:3241-3251):

  ```python
  def _evidence_source_standing_findings(
      vault: Path,
      draft_rows: list[dict[str, Any]],
  ) -> list[dict[str, Any]]:
      """Live-standing findings for every work in each record's item closure."""
      from memoria_vault.runtime.evidence import evidence_ref_kind, parse_source_span_ref

      standings = {
          str(source["work_id"]): _catalog_source_standing(source)
          for source in state.catalog_sources(vault, checked_only=False)
      }
      rows_by_id = {str(row["id"]): row for row in state.evidence_sets(vault)}
      findings: list[dict[str, Any]] = []
      for row in draft_rows:
          seen: set[tuple[str, str, tuple[str, ...]]] = set()
          for item, path in state.evidence_item_closure(rows_by_id, str(row["id"])):
              if evidence_ref_kind(item) != "source-span":
                  continue
              work_id = parse_source_span_ref(item).work_id
              standing = standings.get(work_id, "current")
              if standing in _STALE_STANDINGS:
                  kind, severity = "evidence-source-stale", "high"
              elif standing == "archived":
                  kind, severity = "evidence-source-archived", "medium"
              else:
                  continue
              key = (kind, work_id, path)
              if key in seen:
                  continue
              seen.add(key)
              findings.append(
                  {
                      "kind": kind,
                      "severity": severity,
                      "evidence_id": row["id"],
                      "block_ref": row["block_ref"],
                      "work_id": work_id,
                      "path": list(path),
                  }
              )
      return findings
  ```

  Deliberate placement notes (record in the commit message body if useful):
  the helper runs over `draft_rows` **outside** the per-row loop that honors
  `_disposed_evidence_ids` — that is what makes `evidence-source-stale`
  undisposable; and `rows_by_id` is built from all of
  `state.evidence_sets(vault)`, not just the draft's rows, so nested refs
  that live outside the draft file still taint.
- [ ] Write the implementation, part 3 — wire into
  `_verify_project_draft_snapshot`. After the per-row loop and before
  `findings.extend(_draft_structural_reference_findings(...))`
  (knowledge.py:2244), insert:

  ```python
      findings.extend(_evidence_source_standing_findings(vault, draft["evidence_sets"]))
  ```

  Replace the truncate-then-`ok` block (knowledge.py:2246-2249, as amended
  by Task S68.1):

  ```python
      total_findings = len(findings)
      max_findings = max(1, int(max_findings))
      findings = findings[:max_findings]
      ok = not findings
  ```

  with:

  ```python
      total_findings = len(findings)
      max_findings = max(1, int(max_findings))
      blocking = [
          finding for finding in findings if finding["kind"] not in _ADVISORY_FINDING_KINDS
      ]
      findings = findings[:max_findings]
      ok = not blocking
  ```

  (Readiness is computed over the **untruncated** blocking list — a
  `max_findings=1` truncation that happens to keep only an advisory must not
  flip `ready`.) Then replace the `missing` line (knowledge.py:2257):

  ```python
              "missing": [] if ok else _verification_finding_labels(findings),
  ```

  with:

  ```python
              "missing": [] if ok else _verification_finding_labels(blocking[:max_findings]),
  ```

- [ ] Write the implementation, part 4 — export refusal reasons must not
  list advisories. In `render_project_draft_export_markdown`
  (knowledge.py:2591), replace:

  ```python
          reasons = ", ".join(_verification_finding_labels(verification["findings"]))
  ```

  with:

  ```python
          reasons = ", ".join(verification["missing"])
  ```

  (`missing` is exactly the blocking labels; the existing drift/unbound
  refusal tests keep matching because label format is unchanged.)
- [ ] Run to verify the new tests pass:
  `python -m pytest tests/test_draft_verification.py -k "stale or archived or unset_standing" -v`
- [ ] Run the full neighbors:
  `python -m pytest tests/test_draft_verification.py tests/test_gap_analysis.py tests/test_knowledge.py tests/test_evidence_sets.py -q`
  (gap analysis consumes `_is_current_catalog_source`; behavior for it is
  unchanged by the split).
- [ ] Commit:

  ```bash
  git add src/memoria_vault/runtime/knowledge.py tests/test_draft_verification.py
  git commit -m "feat(verify): live standing findings — evidence-source-stale blocks, archived advises (#1293 slice 6b-d)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task S68.3: Journal `evidence-minted` events at first binding

Spec §8: the `evidence_bindings` mint-once ledger lives only in SQLite; a
folder-copied bundle silently loses every anti-tamper guarantee. At first
binding, append an `evidence-minted` journal event carrying
`{evidence_id, block_ref, block_text_sha256}`.

**Seam choice (documented per plan brief):** the bind itself happens inside
`state.replace_evidence_sets` (the `INSERT INTO evidence_bindings ... ON
CONFLICT(id) DO NOTHING` at state.py:2283-2290, fed by
`_evidence_marker_rows`'s `bind` flag at state.py:2556/2577). `state.py` has
no `OperationContext` anywhere — context validation lives in
`trusted_writer.py` — so state cannot call
`append_journal_event(vault, payload, context=...)` itself. The only
**production** rebuild call sites are `compose_project_draft`
(knowledge.py:2039) and `_verify_project_draft_snapshot` (knowledge.py:2162),
both of which run under a validated `OperationContext` (grep-verified: no
other non-test caller of `rebuild_evidence_sets_from_markers` /
`replace_evidence_sets`). Therefore: **state detects the mint** (it alone
knows whether the insert was a first insert, via `cursor.rowcount` on the
ON-CONFLICT insert) and reports it in its result dict; **the context-holding
knowledge.py callers emit the journal event**, mirroring how
compose already calls `append_journal_event(vault, {...}, context=context)`
at knowledge.py:2047. Direct state-level rebuilds (tests only) bind without
journaling — the same trust boundary as today; every production mint
journals.

**Files:**
- Modify: `src/memoria_vault/runtime/state.py:2277-2332`
  (`replace_evidence_sets` — collect `minted`, return it),
  `src/memoria_vault/runtime/knowledge.py` (new `_journal_minted_evidence_events`
  helper; call it after the rebuild at :2039-2042 in
  `compose_project_draft` and after :2162-2165 in
  `_verify_project_draft_snapshot`),
  `tests/test_evidence_sets.py:71` (exact-dict assertion on the rebuild
  result gains the `minted` key).
- Test: `tests/test_draft_verification.py` (new test).

**Interfaces:**
- Consumes: `append_journal_event(vault, event, *, context) -> dict[str, Any]`
  (trusted_writer.py:193; already imported in knowledge.py:38);
  `state.read_event_log(vault, *, event_types=None) -> list[dict[str, Any]]`
  (state.py:930, for the test).
- Produces:
  - `state.replace_evidence_sets(vault: Path, rows: Iterable[dict[str, Any]]) -> dict[str, Any]`
    — return value gains `"minted": list[dict[str, Any]]` (each
    `{"evidence_id": str, "block_ref": str, "block_text_sha256": str | None}`),
    present **only when non-empty** (same convention as `duplicate_ids` at
    state.py:2354-2355). `rebuild_evidence_sets_from_markers` passes it
    through unchanged.
  - `knowledge._journal_minted_evidence_events(vault: Path, rebuild: dict[str, Any], *, context: OperationContext) -> None`
    (module-private emission seam).
  - Journal event contract: `event_type == "evidence-minted"`, payload keys
    `evidence_id`, `block_ref`, `block_text_sha256` plus the standard
    context/provenance decoration. Task S68.4 replays exactly this.

**Steps:**

- [ ] Write the failing test. Append to `tests/test_draft_verification.py`:

  ```python
  def test_first_binding_journals_one_evidence_minted_event(tmp_path: Path) -> None:
      _compose_source_backed_draft(tmp_path, body="A minted claim enters the journal.")
      [bound] = state.evidence_sets(tmp_path)

      events = state.read_event_log(tmp_path, event_types=["evidence-minted"])

      assert [
          (event["evidence_id"], event["block_ref"], event["block_text_sha256"])
          for event in events
      ] == [(bound["id"], bound["block_ref"], bound["block_text_sha256"])]

      verify_project_draft(tmp_path, "project-alpha")
      events_after = state.read_event_log(tmp_path, event_types=["evidence-minted"])

      assert len(events_after) == 1
  ```

  (The re-verify rebuild must **not** re-emit: the binding already exists,
  so the ON-CONFLICT insert is a no-op and `minted` stays empty —
  mint-once durability, not an event per rebuild.)
- [ ] Run to verify it fails:
  `python -m pytest tests/test_draft_verification.py::test_first_binding_journals_one_evidence_minted_event -v`
  — expected failure: `events == []`.
- [ ] Write the state half. In `src/memoria_vault/runtime/state.py`, replace
  the head and tail of `replace_evidence_sets` (lines 2277-2296 and 2332).
  Head — replace:

  ```python
  def replace_evidence_sets(vault: Path, rows: Iterable[dict[str, Any]]) -> dict[str, int]:
      rows = list(rows)
      with connect(vault) as conn:
          for row in rows:
              if not bool(row.get("bind", True)):
                  continue
              conn.execute(
                  """
                  INSERT INTO evidence_bindings(id, block_text_sha256)
                  VALUES (?, ?)
                  ON CONFLICT(id) DO NOTHING
                  """,
                  (str(row["id"]), row.get("block_text_sha256")),
              )
  ```

  with:

  ```python
  def replace_evidence_sets(vault: Path, rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
      rows = list(rows)
      minted: list[dict[str, Any]] = []
      with connect(vault) as conn:
          for row in rows:
              if not bool(row.get("bind", True)):
                  continue
              cursor = conn.execute(
                  """
                  INSERT INTO evidence_bindings(id, block_text_sha256)
                  VALUES (?, ?)
                  ON CONFLICT(id) DO NOTHING
                  """,
                  (str(row["id"]), row.get("block_text_sha256")),
              )
              if cursor.rowcount:
                  minted.append(
                      {
                          "evidence_id": str(row["id"]),
                          "block_ref": normalize_path(str(row["block_ref"])),
                          "block_text_sha256": row.get("block_text_sha256"),
                      }
                  )
  ```

  Tail — replace line 2332:

  ```python
      return {"deleted": int(deleted), "inserted": len(rows)}
  ```

  with:

  ```python
      result: dict[str, Any] = {"deleted": int(deleted), "inserted": len(rows)}
      if minted:
          result["minted"] = minted
      return result
  ```

- [ ] Write the knowledge half. In `src/memoria_vault/runtime/knowledge.py`,
  add directly after `verify_project_draft` (after line 2128):

  ```python
  def _journal_minted_evidence_events(
      vault: Path,
      rebuild: dict[str, Any],
      *,
      context: OperationContext,
  ) -> None:
      """Journal first-time evidence bindings so mint history travels with the vault."""
      for minted in rebuild.get("minted", []):
          append_journal_event(
              vault,
              {
                  "event": "evidence-minted",
                  "evidence_id": minted["evidence_id"],
                  "block_ref": minted["block_ref"],
                  "block_text_sha256": minted["block_text_sha256"],
              },
              context=context,
          )
  ```

  Call it at both production rebuild sites. In `compose_project_draft`,
  after the rebuild (knowledge.py:2039-2042):

  ```python
      rebuild = state.rebuild_evidence_sets_from_markers(
          vault,
          run_id=context.run_id,
      )
      _journal_minted_evidence_events(vault, rebuild, context=context)
  ```

  In `_verify_project_draft_snapshot`, after the rebuild
  (knowledge.py:2162-2165):

  ```python
      rebuild = state.rebuild_evidence_sets_from_markers(
          vault,
          run_id=context.run_id,
      )
      _journal_minted_evidence_events(vault, rebuild, context=context)
  ```

- [ ] Update the exact-dict rebuild assertion at
  `tests/test_evidence_sets.py:71` (five direct markers all mint there).
  Replace:

  ```python
      assert result == {"deleted": 0, "inserted": 5}
  ```

  with:

  ```python
      assert (result["deleted"], result["inserted"]) == (0, 5)
      assert {minted["evidence_id"] for minted in result["minted"]} == {
          "ev-11111111",
          "ev-22222222",
          "ev-33333333",
          "ev-44444444",
          "ev-55555555",
      }
  ```

  (`tests/test_mc_hash_binding.py:142` asserts `{"deleted": 0, "inserted": 0}`
  with zero rows — no mint, no `minted` key, unchanged.)
- [ ] Run to verify it passes:
  `python -m pytest tests/test_draft_verification.py::test_first_binding_journals_one_evidence_minted_event tests/test_evidence_sets.py tests/test_mc_hash_binding.py -v`
- [ ] Run the journal-trust neighbors (the event rides the hash chain):
  `python -m pytest tests/test_journal_trust.py tests/test_draft_compose.py -q`
- [ ] Commit:

  ```bash
  git add src/memoria_vault/runtime/state.py src/memoria_vault/runtime/knowledge.py tests/test_draft_verification.py tests/test_evidence_sets.py
  git commit -m "feat(evidence): journal evidence-minted events at first binding (#1293 slice 7a)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task S68.4: Rebuild the bindings ledger from the journal

Spec §8: the bindings table becomes rebuildable by replaying mint events, so
a vault whose `.memoria` SQLite state is lost (folder-copied bundle) regains
its anti-tamper guarantees from the journal.

**Files:**
- Modify: `src/memoria_vault/runtime/state.py` (new function directly after
  `rebuild_evidence_sets_from_markers`, i.e. after line 2356).
- Test: `tests/test_draft_verification.py` (new test — it needs the compose
  + verify harness to prove tamper stays detected end-to-end).

**Interfaces:**
- Consumes: the `evidence-minted` journal contract from Task S68.3
  (`event_type = "evidence-minted"`, payload keys `evidence_id`,
  `block_text_sha256`); the `event_log` table shape
  (state.py:806-814).
- Produces: `state.rebuild_evidence_bindings_from_journal(vault: Path) -> dict[str, int]`
  — replays `evidence-minted` events in `event_id` order into
  `evidence_bindings` with first-event-wins (ON CONFLICT DO NOTHING);
  returns `{"replayed": <events seen>, "inserted": <rows actually written>}`.

**Steps:**

- [ ] Write the failing test. Append to `tests/test_draft_verification.py`:

  ```python
  def test_deleted_bindings_ledger_rebuilds_from_journal_and_tamper_stays_detected(
      tmp_path: Path,
  ) -> None:
      draft, _evidence_id = _compose_source_backed_draft(
          tmp_path, body="The journal preserves this exact claim text."
      )
      [bound] = state.evidence_sets(tmp_path)
      assert bound["block_text_sha256"]

      with state.connect(tmp_path) as conn:
          conn.execute("DELETE FROM evidence_bindings")

      result = state.rebuild_evidence_bindings_from_journal(tmp_path)

      assert result == {"replayed": 1, "inserted": 1}
      with state.connect(tmp_path) as conn:
          restored = conn.execute(
              "SELECT id, block_text_sha256 FROM evidence_bindings"
          ).fetchall()
      assert [(row["id"], row["block_text_sha256"]) for row in restored] == [
          (bound["id"], bound["block_text_sha256"])
      ]

      draft.write_text(
          draft.read_text(encoding="utf-8").replace(
              "The journal preserves this exact claim text.",
              "Tampered claim text after ledger loss.",
          ),
          encoding="utf-8",
      )
      verification = verify_project_draft(tmp_path, "project-alpha")

      assert verification["ready"] is False
      assert any(
          finding["kind"] == "evidence-text-drift"
          for finding in verification["findings"]
      )
  ```

  (Without the replay, the verify rebuild would re-mint the **tampered**
  hash as a fresh first binding and the drift would be blessed — the replay
  restoring the original SHA is exactly what keeps tamper detected.)
- [ ] Run to verify it fails:
  `python -m pytest tests/test_draft_verification.py::test_deleted_bindings_ledger_rebuilds_from_journal_and_tamper_stays_detected -v`
  — expected failure: `AttributeError: module 'memoria_vault.runtime.state'
  has no attribute 'rebuild_evidence_bindings_from_journal'`.
- [ ] Write the minimal implementation. In
  `src/memoria_vault/runtime/state.py`, after
  `rebuild_evidence_sets_from_markers` (line 2356), add:

  ```python
  def rebuild_evidence_bindings_from_journal(vault: Path) -> dict[str, int]:
      """Replay evidence-minted journal events into the mint-once bindings ledger."""
      replayed = 0
      inserted = 0
      with connect(vault) as conn:
          rows = conn.execute(
              """
              SELECT json_extract(payload_json, '$.evidence_id') AS evidence_id,
                     json_extract(payload_json, '$.block_text_sha256') AS block_text_sha256
              FROM event_log
              WHERE event_type = 'evidence-minted'
              ORDER BY event_id
              """
          ).fetchall()
          for row in rows:
              evidence_id = str(row["evidence_id"] or "")
              if not evidence_id:
                  continue
              replayed += 1
              cursor = conn.execute(
                  """
                  INSERT INTO evidence_bindings(id, block_text_sha256)
                  VALUES (?, ?)
                  ON CONFLICT(id) DO NOTHING
                  """,
                  (evidence_id, row["block_text_sha256"]),
              )
              inserted += cursor.rowcount
      return {"replayed": replayed, "inserted": inserted}
  ```

- [ ] Run to verify it passes:
  `python -m pytest tests/test_draft_verification.py::test_deleted_bindings_ledger_rebuilds_from_journal_and_tamper_stays_detected -v`
- [ ] Run the correctness gate: `python scripts/verify`
- [ ] Commit:

  ```bash
  git add src/memoria_vault/runtime/state.py tests/test_draft_verification.py
  git commit -m "feat(evidence): rebuild the bindings ledger from evidence-minted journal events (#1293 slice 7b)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task S68.5: Patch `0.1.0-beta.1-design.md` §1.4 — type names, `computed`, pointer to the governing spec

Spec §12(8) and the spec header both mandate this: where §1.4 and the
2026-07-14 spec disagree, the 2026-07-14 spec governs and §1.4 gets a pointer
patch. Three payloads: (a) `single-sentence / multi-sentence` →
`single-span / multi-span`; (b) `computed` joins the derivation list; (c) a
pointer line to the governing spec. Docs task — no failing test; the gate is
`python scripts/verify` (docs lint + product gates).

**Files:**
- Modify: `docs/superpowers/specs/0.1.0-beta.1-design.md:169-191` (§1.4
  grounding bullets).

**Interfaces:**
- Consumes: nothing programmatic.
- Produces: nothing programmatic — prose only. Trust order (AGENTS.md) puts
  docs last, so no code may cite this file as authority; the pointer makes
  the deference explicit.

**Steps:**

- [ ] Edit 1 — type-name wording (lines 169-171). The rename-sweep package
  (slice 1) owns the `Warrant =` → `Grounds =` lead-in; if it has already
  landed, match `Grounds` in old_string instead of `Warrant` — the payload
  of THIS edit is only the type list. Replace:

  ```text
  - **Warrant = an evidence-*set*, typed.** Each drafted claim carries its
    evidence set with type single-sentence / multi-sentence / multi-hop /
    **implicit**. Claims that need project computation or future software work are
  ```

  with:

  ```text
  - **Warrant = an evidence-*set*, typed.** Each drafted claim carries its
    evidence set with type single-span / multi-span / multi-hop / **implicit** /
    **computed**. Claims that need project computation or future software work are
  ```

- [ ] Edit 2 — derivation list gains `computed` and `implicit` gets its
  ratified trigger (lines 177-179). Replace:

  ```text
    **derives** the `type` from the items — *single-span* (one span), *multi-span*
    (>1 span, one work), *multi-hop* (>1 works), *implicit* (no resolvable
    warrant) — and never asserts it.
  ```

  with:

  ```text
    **derives** the `type` from the items — *single-span* (one span), *multi-span*
    (>1 span, one work), *multi-hop* (>1 works, any nested set, or a mixed
    code+text combination), *implicit* (no items), *computed* (all items are
    code-grounds refs) — and never asserts it.
  ```

- [ ] Edit 3 — pointer line. After the bullet's closing sentence
  `…§4.1's citation/number checks and §8 Q2's routing measurement run on.`
  (line 191), append to the same bullet:

  ```text
    **Governing contract:** the ratified
    [2026-07-14 evidence-set / grounds contract](2026-07-14-evidence-set-grounds-contract-design.md)
    supersedes this sketch wherever they disagree — in particular, marker
    grammar v2 serializes `items=` only; `type=`, `state=`, and `review=` are
    derived at read time, never stored in the marker.
  ```

- [ ] Run the gate: `python scripts/verify`
- [ ] Commit:

  ```bash
  git add docs/superpowers/specs/0.1.0-beta.1-design.md
  git commit -m "docs(specs): point beta.1-design §1.4 at the ratified grounds contract (#1293 slice 8a)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task S68.6: Rewrite `docs/reference/control-and-policy/evidence-sets.md` to v2 grammar and the three-class findings table

Published reference page (GitHub Pages, Diátaxis reference quadrant). Keep
its voice, its fail-closed eligibility paragraphs, its front matter, and its
Related links; replace the v1 marker example, the field table, the findings
prose, and the disposition section. Do **not** link
`docs/superpowers/specs/` from this page — that tree is tracked but not
published, so the link would 404 on Pages. This rewrite assumes the slice-1
rename (`code-warrant:` → `code-grounds:`, warrant→grounds prose) has landed;
the page below is written post-rename.

**Files:**
- Modify: `docs/reference/control-and-policy/evidence-sets.md` (full-file
  replacement, 91 lines today).

**Interfaces:**
- Consumes: finding names/severities/classes exactly as produced by Tasks
  S68.1/S68.2 and by S35 (`evidence-incomplete`, `review-required`,
  disposition `items_sha256` binding).
- Produces: nothing programmatic.

**Steps:**

- [ ] Replace the entire file content with:

  ````markdown
  ---
  title: Evidence sets
  parent: Control and policy
  nav_order: 3
  grand_parent: Reference
  ---

  # Evidence sets

  Evidence sets are the draft-time grounds contract for composed project
  prose. The durable source is the inline marker on a draft claim. The marker
  carries the mint-once id and the ordered `items=` list — nothing else:

  ```text
  %%ev: ev-1234abcd items=source-alpha#^p0001|source-alpha#^p0002%%
  ```

  `type`, `state`, and `review_required` are always derived from the items
  and never serialized: a stored copy of a derived value can only be
  redundant or wrong. Human-readable status lives in the verify report,
  never in the marker.

  Only a plain, top-level Markdown paragraph claim can establish a new binding.
  Markers and block anchors inside Markdown code, headings, HTML comments or
  elements, frontmatter, title metadata, reference definitions, fenced Divs,
  multiline inline constructs, tables, line blocks, blockquote, list, or
  definition-list containers cannot mint a new evidence ID. If they repeat an
  existing ID, Memoria retains them as unbound and blocks draft export.
  A duplicate group containing a direct visible marker or an ID already in the
  immutable ledger is unbound and blocks export for every draft that contains it.
  Hidden-only, never-bound occurrences stay nonbinding and cannot mint an ID.

  Memoria fails closed when renderer syntax can make a line ambiguous: raw HTML
  elements, raw TeX or math syntax, Pandoc attributes, footnote definitions,
  initial MultiMarkdown-style metadata, abbreviation definitions, and table
  syntax make the whole draft ineligible to mint a new binding. This conservative
  rule also applies when the syntax appears in otherwise literal code. Ordinary
  literal-code delimiters do not taint unrelated visible prose, but controls
  inside code are never direct evidence. These rules avoid giving a hidden
  renderer construct an evidence binding that only visible prose may establish.

  ## Items and derived fields

  | Field | Meaning |
  | --- | --- |
  | `id` | Mint-once `ev-<8hex>` identifier. |
  | `items` | Ordered `\|`-separated list: `work_id#^pNNNN` source-span refs, nested `ev-<8hex>` set refs, or `code-grounds:<run_id>:<artifact_id>:sha256:<64hex>` refs. Empty or omitted means no items. An item matching no grammar fails the record closed at parse. |
  | `type` | Derived from the record's own items (see the table below), never asserted. |
  | `state` | `complete` only when every item resolves; `implicit` is always `evidence-incomplete`. |
  | `review_required` | `true` exactly when the type is `implicit` or `multi-hop`. |
  | `block_text_sha256` | The mint-once SHA-256 binding copied from the immutable `evidence_bindings` ledger; nullable only to represent an unbound, fail-closed row. |

  Type derivation is first-match over the record's own items:

  | Items shape | Type | Routed |
  | --- | --- | --- |
  | No items | `implicit` | PI review |
  | Any nested set ref, spans naming two or more distinct works, or a code ref mixed with any non-code item | `multi-hop` | PI review |
  | Code refs only | `computed` | Machine |
  | Spans in one work, exactly one | `single-span` | Machine |
  | Spans in one work, two or more | `multi-span` | Machine |

  A span resolves through the work's extracted content anchor. A code ref
  resolves only while the recorded run exists, succeeded, and the pinned
  output hash still matches; verification never executes code. A nested set
  ref resolves only if the referenced set exists and is itself `complete` —
  completeness is transitive, and every member of a reference cycle is
  `evidence-incomplete`, fail-closed. Running code grounds the output
  provenance; it does not make the research claim true.

  ## The mint-once ledger and the journal

  The marker owns the ordered `items=` list. SQLite table `evidence_sets` is
  derived active state rebuilt from those markers. A separate
  `evidence_bindings` ledger records the first observed appearance of each
  evidence ID: its anchored claim hash when resolvable, or `null` when it is
  not. The ledger survives marker removal, so a reappearing ID always retains
  its original binding.

  The hash covers the Markdown paragraph or block containing the matching
  `^blk-<8hex>` anchor. Before hashing, Memoria removes that anchor and its
  `%%ev: ... %%` control marker, then trims outer whitespace. The first observed
  ID records that hash, or `null` if the block cannot resolve. Later rebuilds,
  including removal and reappearance of the marker, never refresh that value.
  Changing the claim therefore cannot silently bless the edit with a new binding.

  At first binding, Memoria also appends an `evidence-minted` journal event
  carrying the evidence ID, block reference, and claim hash. The bindings
  ledger is rebuildable by replaying mint events, so tamper history travels
  with the vault rather than living only in local SQLite state.

  Source-span refs use stable `work_id`, never citekeys. Citekeys are rendered
  only during export.

  ## Verification findings

  Findings fall in three classes; the class, not the finding, defines what a
  PI disposition may do. A draft exports only when no permanent block attaches
  and every hold is cleared by a matching disposition. Advisories never
  refuse export.

  Permanent blocks — no disposition clears them; the cure is editing the
  draft or the grounds:

  | Finding | Severity | Trigger |
  | --- | --- | --- |
  | `evidence-text-drift` | high | Claim block hash differs from the stored mint-once binding. |
  | `evidence-text-unbound` | high | Stored binding missing, or the anchored block cannot resolve. |
  | `evidence-id-duplicate` | high | One ID bound by more than one occurrence. |
  | `evidence-source-stale` | high | Any work in the record's item closure has catalog standing `retracted` or `superseded`. Carries `work_id` and `path` — empty path is a direct item, non-empty is inherited through nested sets. |
  | `no-evidence-set` | high | The draft contains zero evidence sets. |

  PI-clearable holds — block until a disposition for this exact record:

  | Finding | Severity | Trigger |
  | --- | --- | --- |
  | `evidence-incomplete` | high | Any item fails to resolve, or the set is `implicit`. |
  | `review-required` | medium | The derived type is `implicit` or `multi-hop`. |

  Advisories — surfaced, never blocking:

  | Finding | Severity | Trigger |
  | --- | --- | --- |
  | `evidence-source-archived` | medium | Any closure work has standing `archived`. |

  Catalog standing is joined live at verify time, never cached into the
  record: a source retracted years after a claim was written still blocks.
  An unset standing is `current` by design — standing is PI-curated catalog
  state, and the PI is the standing authority. `evidence-source-stale` is not
  PI-disposable: if the claim is about the retraction itself, re-ground it on
  the retraction notice cataloged as its own work.

  ## Dispositions

  Only the PI can record a disposition:

  ```bash
  memoria project resolve-evidence <project> --evidence-id ev-1234abcd --decision accept
  ```

  The disposition is journal provenance; it does not edit the marker or assert
  that the claim is true. It is bound to content: the event records a digest
  of the record's ordered items, and verification honors the disposition only
  while the current items match. Editing the items voids the disposition (the
  journal keeps it; it is simply inert) and the record re-routes to review.
  A disposition can clear `evidence-incomplete` and `review-required`; it can
  never clear a permanent block.

  ## Related

  - Where markers are minted and resolved during drafting: [Compose a draft](../../how-to-guides/project/compose-a-draft.md)
  - How resolved markers become citations at export, and what blocks export: [Export routes and formats](../pipelines-and-io/export.md)
  - Why the engine may verify markers but not decide a claim is true: [Why the write half is bounded](../../explanation/rationale/boundaries/why-write-half-is-bounded.md)
  - The principle behind the immutable binding ledger: [Design principles](../../explanation/rationale/foundations/design-principles.md) (Provenance everywhere)
  ````

- [ ] Run the gate: `python scripts/verify`
  (docs lint and any doc-link product gates run here; fix only what the gate
  reports on this file).
- [ ] Commit:

  ```bash
  git add docs/reference/control-and-policy/evidence-sets.md
  git commit -m "docs(reference): evidence sets — v2 marker grammar and three-class findings table (#1293 slice 8b)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```
# Section 22 — Model-call usage/cost telemetry

Implements `docs/superpowers/specs/2026-07-15-model-call-cost-telemetry-design.md`.

> **Header note — PI confirmation required first.** The spec's design decisions
> are explicitly marked "confirm at review" in its own header (`## Design
> decisions (made here; confirm at review)`). Task COST.1 step 0 is a one-line
> PI confirmation checkpoint; do not start coding until it is checked.

**Execution context (repo facts):**
- Work in an isolated worktree per AGENTS.md: `git worktree add
  .worktrees/cost-telemetry -b wip/cost-telemetry origin/main`, then
  `EnterWorktree(path: ".worktrees/cost-telemetry")`.
- Correctness gate: `python scripts/verify`. Tests live in
  `tests/test_operations.py`, already registered in `tests/conftest.py`
  `TEST_LEVELS` as `"contract"` (line 77) — **no conftest change needed**.
- Stage explicit paths only; never `git add -A` (shared-index rule).
- No new dependencies (`genai-prices` ships with the pinned
  `pydantic-ai-slim>=2.0`; installed pydantic-ai is 2.9.1 and its `RunUsage`
  carries exactly `input_tokens`/`output_tokens`/`cache_read_tokens`/
  `cache_write_tokens`; `ModelResponse.cost()` raises `LookupError` on
  unpriced models — both verified against the repo venv). No
  `SCHEMA_VERSION` bump: this is an additive journal-event payload change,
  and no JSON schema constrains `model_call` event fields (verified — no
  `model_call` reference anywhere under `schemas/`).

**Verified line-number corrections vs. the spec** (spec cites slightly stale
ranges; the refs below are the real, current ones):

| Spec says | Actual current code |
|---|---|
| `_pydantic_ai_chat` :951-984 | `src/memoria_vault/runtime/operations.py:951-984` (correct) |
| `_run_prompt_model` :801-808 | `operations.py:801-808` (correct) |
| `_run_digest_model` :896-917 | `operations.py:896-917` (correct) |
| prompt-op `model_call` dict :361-379 / :369-379 | `operations.py:368-388` (dict literal :370-386; caller binding :367) |
| `run_operation_model_text` dict :438-473 / :441-456 | `operations.py:454-475` (dict literal :456-473; caller binding :453; function :439-476) |
| digest `model_call` dict :527-542 | `operations.py:526-546` (dict literal :528-544; caller binding :525) |
| caller `integrity.py:1466` | `integrity.py:1466-1477` — reads `call["output"]`; **no change needed** because `run_operation_model_text`'s return shape (`{"output": str, "model_call": dict}`) is unchanged |

**Two call sites the spec does not mention, resolved during code reading:**
- `src/memoria_vault/cli.py:3064` (`_runner_status --live`) calls
  `_pydantic_ai_chat` and **discards the return value** — the return-shape
  change is transparent to it; no edit.
- `tests/helpers.py:362-393` `patch_pydantic_ai` fakes `run_sync` with
  `SimpleNamespace(output=output)` — after COST.1 the fake must also provide
  `usage()` and `response.cost()` or three `test_cli_doctor_eval.py` tests
  break. COST.1 upgrades the fake (backward-compatibly).

**Deliberate scope boundaries (assumptions other sections must honor):**
- Only the **three `operations.py` `model_call` literals** gain the new keys.
  The other two `model_call` literals in the repo —
  `src/memoria_vault/runtime/knowledge.py:211` (propose-note-candidates: no
  model is actually called; hashes candidate rows) and
  `src/memoria_vault/runtime/integrity.py:1579` (`_record_tier2_model_call`,
  the tier-2 deterministic-fixture-only recorder) — are **not** extended, per
  the spec's "Add three keys to each of the three existing `model_call` dict
  literals."
- `cost_usd` is stored as `float(cost.total_price)` — `genai-prices` returns
  a `Decimal`, and `append_journal_event` serializes with plain `json.dumps`
  (`jsonl.py:36`), which rejects `Decimal`. The cast is load-bearing.
- Floor goldens (`tests/fixtures/floor/goldens/*.json`) hash journal `.jsonl`
  files, so COST.4 (the event-dict change) **will** cause golden drift; the
  fixture path's `usage: null / cost_usd: null / elapsed_s: 0.0` is fully
  deterministic, so regenerated goldens stay stable. Regeneration is part of
  COST.4, gated by `MEMORIA_FLOOR_UPDATE_GOLDENS=1`.
- New doc terms `cost_usd` / `elapsed_s` pass cspell against the repo config
  (verified via `npx cspell stdin`) — no `project-words.txt` change.

---

### Task COST.1: `_pydantic_ai_chat` returns `{text, usage, cost_usd, elapsed_s}`

**Files:**
- Modify: `src/memoria_vault/runtime/operations.py:951-984` (`_pydantic_ai_chat`) and `operations.py:5-12` (stdlib import block — add `import time`)
- Modify: `tests/helpers.py:362-393` (`patch_pydantic_ai` — fake `run_sync` result gains `usage()` and `response.cost()`)
- Test: `tests/test_operations.py`

**Interfaces:**
- Consumes: `AgentRunResult.usage() -> RunUsage` (fields `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`); `AgentRunResult.response.cost() -> genai_prices PriceCalculation` (`.total_price: Decimal`; raises `LookupError` when the model/provider is not in the local price snapshot); `time.monotonic()`.
- Produces: `_pydantic_ai_chat(policy: dict[str, Any], runner: dict[str, Any], prompt: str) -> dict[str, Any]` with keys `text: str` (non-empty), `usage: dict[str, int]` (always populated on a real call), `cost_usd: float | None`, `elapsed_s: float`.
- Produces: `patch_pydantic_ai(monkeypatch: Any, *, output: str = "", seen: dict[str, Any] | None = None, total_price: Any | None = None) -> dict[str, Any]` — fake result's `usage()` returns fixed counts 17/5/2/1; `response.cost()` raises `LookupError` when `total_price is None`, else returns an object with `.total_price`.

**Steps:**

- [ ] **Step 0 — PI confirmation checkpoint:** confirm with the PI that the spec's "Design decisions (made here; confirm at review)" block stands as written (extend `model_call`, plain-dict return, nullable `cost_usd`, no content capture, fixture nulls, no new dep / no `SCHEMA_VERSION` bump). No code.

- [ ] **Upgrade the test fake** — replace `patch_pydantic_ai` in `tests/helpers.py:362-393` with (only `run_sync` and the signature change; existing `seen` behavior is preserved, so current callers in `test_cli_doctor_eval.py:698,743,778` and `test_runtime_gate_replay.py:351` keep passing):

```python
def patch_pydantic_ai(
    monkeypatch: Any,
    *,
    output: str = "",
    seen: dict[str, Any] | None = None,
    total_price: Any | None = None,
) -> dict[str, Any]:
    seen = seen if seen is not None else {}

    class FakeProvider:
        def __init__(self, **kwargs: Any) -> None:
            seen["provider_kwargs"] = kwargs

    class FakeModel:
        def __init__(self, model_name: str, *, provider: object) -> None:
            seen["model_name"] = model_name
            seen["provider"] = provider

    class FakeAgent:
        def __init__(self, model: object) -> None:
            seen["model"] = model
            seen.setdefault("models", []).append(model)

        def run_sync(self, prompt: str, *, model_settings: dict[str, Any]) -> SimpleNamespace:
            seen["prompt"] = prompt
            seen["model_settings"] = model_settings

            def usage() -> SimpleNamespace:
                return SimpleNamespace(
                    input_tokens=17,
                    output_tokens=5,
                    cache_read_tokens=2,
                    cache_write_tokens=1,
                )

            def cost() -> SimpleNamespace:
                if total_price is None:
                    raise LookupError("model not present in local price snapshot")
                return SimpleNamespace(total_price=total_price)

            return SimpleNamespace(
                output=output,
                usage=usage,
                response=SimpleNamespace(cost=cost),
            )

    monkeypatch.setattr(
        "memoria_vault.runtime.operations._load_pydantic_ai_openai",
        lambda: (FakeAgent, FakeModel, FakeProvider),
    )
    return seen
```

- [ ] **Write the failing tests** — in `tests/test_operations.py`: add `from decimal import Decimal` to the stdlib imports (after `from copy import deepcopy`, line 6), add `_pydantic_ai_chat` to the first `memoria_vault.runtime.operations` import block (line 14-21, alphabetically first: `_pydantic_ai_chat,` before `_source_interviews,`), then append at end of file:

```python
def chat_runner(model: str = "gpt-test") -> dict[str, object]:
    return {
        "mode": "test",
        "runner": "pydantic-ai",
        "provider": "local",
        "model": model,
        "base_url": "http://model.test/v1",
        "key_env": None,
        "params": {"temperature": 0},
    }


CHAT_POLICY = {"operation_id": "chat-test", "allowed_network": ["http://model.test/v1"]}


def test_pydantic_ai_chat_returns_text_usage_cost_and_timing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = patch_pydantic_ai(monkeypatch, output="model text", total_price=Decimal("0.0125"))

    result = _pydantic_ai_chat(CHAT_POLICY, chat_runner(), "prompt body")

    assert result["text"] == "model text"
    assert result["usage"] == {
        "input_tokens": 17,
        "output_tokens": 5,
        "cache_read_tokens": 2,
        "cache_write_tokens": 1,
    }
    assert isinstance(result["cost_usd"], float)
    assert result["cost_usd"] == pytest.approx(0.0125)
    assert isinstance(result["elapsed_s"], float)
    assert result["elapsed_s"] >= 0.0
    assert seen["prompt"] == "prompt body"


def test_pydantic_ai_chat_unpriced_model_yields_null_cost_with_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_pydantic_ai(monkeypatch, output="model text")

    result = _pydantic_ai_chat(CHAT_POLICY, chat_runner(), "prompt body")

    assert result["cost_usd"] is None
    assert result["usage"] == {
        "input_tokens": 17,
        "output_tokens": 5,
        "cache_read_tokens": 2,
        "cache_write_tokens": 1,
    }


def test_pydantic_ai_chat_still_rejects_empty_output(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_pydantic_ai(monkeypatch, output="")

    with pytest.raises(RuntimeError, match="pydantic-ai model returned no message content"):
        _pydantic_ai_chat(CHAT_POLICY, chat_runner(), "prompt body")
```

- [ ] **Run tests to verify they fail:**
  `python -m pytest "tests/test_operations.py::test_pydantic_ai_chat_returns_text_usage_cost_and_timing" "tests/test_operations.py::test_pydantic_ai_chat_unpriced_model_yields_null_cost_with_usage" "tests/test_operations.py::test_pydantic_ai_chat_still_rejects_empty_output" -v`
  Expected: the first two fail with `TypeError: string indices must be integers, not 'str'` (current `_pydantic_ai_chat` returns a bare `str`, so `result["text"]` is a string index). The third **passes already** — it pins the empty-output `RuntimeError` that must survive the change.

- [ ] **Write minimal implementation** — in `src/memoria_vault/runtime/operations.py`, add `import time` after `import re` (line 8), and replace `_pydantic_ai_chat` (lines 951-984) with:

```python
def _pydantic_ai_chat(
    policy: dict[str, Any], runner: dict[str, Any], prompt: str
) -> dict[str, Any]:
    base_url = str(runner["base_url"])
    require_allowed_network(policy, base_url)
    key_env = runner.get("key_env")
    if isinstance(key_env, str) and key_env:
        api_key = os.environ.get(key_env)
    else:
        api_key = (
            os.environ.get("MEMORIA_MODEL_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("KILOCODE_API_KEY")
        )
    Agent, OpenAIChatModel, OpenAIProvider = _load_pydantic_ai_openai()
    provider_kwargs = {"base_url": base_url}
    if api_key:
        provider_kwargs["api_key"] = api_key
    model = OpenAIChatModel(runner["model"], provider=OpenAIProvider(**provider_kwargs))
    agent = Agent(model)
    params = runner.get("params") if isinstance(runner.get("params"), dict) else {}
    settings = {
        "temperature": params.get("temperature", 0),
        "max_tokens": int(
            params.get("max_tokens", os.environ.get("MEMORIA_MODEL_MAX_TOKENS", 2048))
        ),
        "timeout": float(params.get("timeout", os.environ.get("MEMORIA_MODEL_TIMEOUT", 90))),
    }
    started_at = time.monotonic()
    try:
        result = agent.run_sync(prompt, model_settings=settings)
    except Exception as exc:
        raise RuntimeError(f"pydantic-ai model request failed: {exc}") from exc
    elapsed_s = time.monotonic() - started_at
    text = str(getattr(result, "output", "") or "").strip()
    if not text:
        raise RuntimeError("pydantic-ai model returned no message content")
    run_usage = result.usage()
    usage = {
        "input_tokens": run_usage.input_tokens,
        "output_tokens": run_usage.output_tokens,
        "cache_read_tokens": run_usage.cache_read_tokens,
        "cache_write_tokens": run_usage.cache_write_tokens,
    }
    try:
        cost_usd: float | None = float(result.response.cost().total_price)
    except LookupError:
        cost_usd = None
    return {"text": text, "usage": usage, "cost_usd": cost_usd, "elapsed_s": elapsed_s}
```

  Notes baked into this block: the empty-output check runs on `text` before the return dict is built (spec §1); `float(...)` converts `genai-prices`' `Decimal` so the journal row stays `json.dumps`-serializable; `elapsed_s` brackets only `run_sync`.

- [ ] **Run tests to verify they pass:**
  `python -m pytest "tests/test_operations.py::test_pydantic_ai_chat_returns_text_usage_cost_and_timing" "tests/test_operations.py::test_pydantic_ai_chat_unpriced_model_yields_null_cost_with_usage" "tests/test_operations.py::test_pydantic_ai_chat_still_rejects_empty_output" -v`
  Expected: 3 passed.

- [ ] **Guard the fake's existing consumers:**
  `python -m pytest tests/test_cli_doctor_eval.py tests/test_runtime_gate_replay.py -v`
  Expected: all pass (`_runner_status` at `cli.py:3064` discards the return; the fake stays output-compatible). Known transient state, resolved by COST.2/COST.3 in this same branch: `_run_prompt_model`/`_run_digest_model`'s `pydantic-ai` branches now forward a dict where their callers still expect `str` — no gate-level test reaches those branches (operation tests use the `deterministic-fixture` model, which short-circuits before `_pydantic_ai_chat`; `tests/test_live_runner.py` skips without `MEMORIA_MODEL_BASE_URL`).

- [ ] **Commit:**

```bash
git add src/memoria_vault/runtime/operations.py tests/helpers.py tests/test_operations.py
git commit -m "$(cat <<'EOF'
feat(operations): return usage/cost/timing from _pydantic_ai_chat

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task COST.2: thread the dict through `_run_prompt_model` and both prompt-path callers

**Files:**
- Modify: `src/memoria_vault/runtime/operations.py:801-808` (`_run_prompt_model`), `operations.py:367` (`run_prompt_operation` binding), `operations.py:453` (`run_operation_model_text` binding) — line refs are pre-COST.1 numbering; after COST.1 they shift by +1 (`import time`). Anchor by code, not line.
- Modify: `tests/test_operations.py:245-248` (existing `_run_prompt_model` monkeypatch in `test_prompt_operation_neutralizes_model_output_before_staging` must return the dict shape)
- Test: `tests/test_operations.py`

**Interfaces:**
- Consumes: `_pydantic_ai_chat(policy, runner, prompt) -> dict[str, Any]` (COST.1); `_prompt_fixture_body(policy: dict[str, Any], input_text: str) -> str` (unchanged, `operations.py:811-822`).
- Produces: `_run_prompt_model(policy: dict[str, Any], runner: dict[str, Any], prompt: str, input_text: str) -> dict[str, Any]` — same four keys; `deterministic-fixture` branch returns `usage=None, cost_usd=None, elapsed_s=0.0`.
- Produces (unchanged contract, reasserted): `run_operation_model_text(vault, policy, runner, prompt, *, context, input_text, call_id, route, purpose) -> dict[str, Any]` still returns `{"output": str, "model_call": dict}` — the `integrity.py:1466` caller keeps working untouched.

**Steps:**

- [ ] **Write the failing test** — append to `tests/test_operations.py` (add `_run_prompt_model` to the first operations import block, alphabetically after `_pydantic_ai_chat,`):

```python
def test_run_prompt_model_fixture_branch_returns_null_telemetry() -> None:
    policy = compile_policy()
    runner = chat_runner(model="deterministic-fixture")

    result = _run_prompt_model(policy, runner, "prompt body", "input body")

    assert result["usage"] is None
    assert result["cost_usd"] is None
    assert result["elapsed_s"] == 0.0
    assert result["text"].startswith(f"## {policy['title']}")
```

- [ ] **Run test to verify it fails:**
  `python -m pytest "tests/test_operations.py::test_run_prompt_model_fixture_branch_returns_null_telemetry" -v`
  Expected: `TypeError: string indices must be integers, not 'str'` (fixture branch currently returns a bare `str`).

- [ ] **Write minimal implementation** — replace `_run_prompt_model` (anchored at `def _run_prompt_model(`):

```python
def _run_prompt_model(
    policy: dict[str, Any], runner: dict[str, Any], prompt: str, input_text: str
) -> dict[str, Any]:
    if runner["model"] == "deterministic-fixture":
        return {
            "text": _prompt_fixture_body(policy, input_text),
            "usage": None,
            "cost_usd": None,
            "elapsed_s": 0.0,
        }
    if runner["runner"] == "pydantic-ai":
        return _pydantic_ai_chat(policy, runner, prompt)
    raise ValueError(f"unsupported operation runner: {runner['runner']}")
```

  Then update both callers to unpack `text` while keeping the full dict for COST.4. In `run_prompt_operation` (anchored at the line after the `started = append_journal_event(...)` call), replace:

```python
    output = _run_prompt_model(policy, runner, prompt, input_text)
```

  with:

```python
    result = _run_prompt_model(policy, runner, prompt, input_text)
    output = result["text"]
```

  In `run_operation_model_text` (anchored at the line after `validate_operation_context(vault, context)`), apply the identical two-line replacement. Everything downstream in both functions (`_sha256_text(output)` in the event dicts, `neutralize_untrusted_markdown(output)` at staging, `return {"output": output, "model_call": model_call}`) is untouched — `output` is still the plain string.

- [ ] **Update the existing monkeypatch** at `tests/test_operations.py:245-248` (in `test_prompt_operation_neutralizes_model_output_before_staging`) to the new shape — populated telemetry values are chosen here so COST.4 can assert them flowing into the journal event:

```python
    monkeypatch.setattr(
        "memoria_vault.runtime.operations._run_prompt_model",
        lambda _policy, _runner, _prompt, _input: {
            "text": raw_output,
            "usage": {
                "input_tokens": 17,
                "output_tokens": 5,
                "cache_read_tokens": 2,
                "cache_write_tokens": 1,
            },
            "cost_usd": 0.0125,
            "elapsed_s": 0.25,
        },
    )
```

- [ ] **Run tests to verify they pass:**
  `python -m pytest tests/test_operations.py -v`
  Expected: all pass, including `test_run_prompt_model_fixture_branch_returns_null_telemetry` and the updated neutralization test (its `output_hash` assertion still hashes `raw_output`).

- [ ] **Commit:**

```bash
git add src/memoria_vault/runtime/operations.py tests/test_operations.py
git commit -m "$(cat <<'EOF'
feat(operations): thread model telemetry through _run_prompt_model

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task COST.3: thread the dict through `_run_digest_model` and the digest caller

**Files:**
- Modify: `src/memoria_vault/runtime/operations.py:896-917` (`_run_digest_model`; pre-COST.1 numbering) and `operations.py:525` (`compile_source_digest` binding)
- Modify: `tests/test_operations.py:287-290` and `:343-348` (the two `_run_digest_model` monkeypatch lambdas must return the dict shape)
- Test: `tests/test_operations.py`

**Interfaces:**
- Consumes: `_pydantic_ai_chat(...) -> dict[str, Any]` (COST.1); `_validate_digest_output(text: str, content: str, topics: list[str], interviews: list[dict[str, Any]]) -> str` — **still takes plain text**, unchanged (`operations.py:997-1014`); `_digest_body(...) -> str` (unchanged).
- Produces: `_run_digest_model(policy: dict[str, Any], runner: dict[str, Any], source_fm: dict[str, Any], content: str, topics: list[str], interviews: list[dict[str, Any]]) -> dict[str, Any]` — same four keys, `text` is the **validated** digest text; fixture branch returns `usage=None, cost_usd=None, elapsed_s=0.0`.

**Steps:**

- [ ] **Write the failing test** — append to `tests/test_operations.py` (add `_run_digest_model` to the first operations import block, after `_pydantic_ai_chat,`):

```python
def test_run_digest_model_fixture_branch_returns_null_telemetry() -> None:
    policy = compile_policy()
    runner = chat_runner(model="deterministic-fixture")
    source_fm = {"title": "Alpha Source", "description": "A fixture source."}

    result = _run_digest_model(
        policy,
        runner,
        source_fm,
        "Alpha content about framing, methods, outcomes, gaps, and impact.",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        [],
    )

    assert result["usage"] is None
    assert result["cost_usd"] is None
    assert result["elapsed_s"] == 0.0
    assert "## Synthesis" in result["text"]
    assert "## Hub suggestions" in result["text"]
```

- [ ] **Run test to verify it fails:**
  `python -m pytest "tests/test_operations.py::test_run_digest_model_fixture_branch_returns_null_telemetry" -v`
  Expected: `TypeError: string indices must be integers, not 'str'` (`_run_digest_model` currently returns the validated `str`).

- [ ] **Write minimal implementation** — replace `_run_digest_model` (anchored at `def _run_digest_model(`); `_validate_digest_output` keeps receiving plain text and the validated text is swapped back into the dict, per spec §2:

```python
def _run_digest_model(
    policy: dict[str, Any],
    runner: dict[str, Any],
    source_fm: dict[str, Any],
    content: str,
    topics: list[str],
    interviews: list[dict[str, Any]],
) -> dict[str, Any]:
    if runner["model"] == "deterministic-fixture":
        result: dict[str, Any] = {
            "text": _digest_body(source_fm, content, topics, interviews),
            "usage": None,
            "cost_usd": None,
            "elapsed_s": 0.0,
        }
    else:
        _require_untrusted_fields(
            str(policy.get("operation_id") or "<unknown>"),
            policy,
            ["source_text", "pi_interview_notes"],
        )
        prompt = _digest_prompt(source_fm, content, topics, interviews)
        if runner["runner"] == "pydantic-ai":
            result = _pydantic_ai_chat(policy, runner, prompt)
        else:
            raise ValueError(f"unsupported operation runner: {runner['runner']}")
    result["text"] = _validate_digest_output(result["text"], content, topics, interviews)
    return result
```

  Then update the caller in `compile_source_digest` (anchored at the line between `digest_prompt = _digest_prompt(...)` and the `model_call = append_journal_event(` call), replacing:

```python
    digest_text = _run_digest_model(policy, runner, source_fm, content, topics, interviews)
```

  with:

```python
    digest_result = _run_digest_model(policy, runner, source_fm, content, topics, interviews)
    digest_text = digest_result["text"]
```

  Downstream uses of `digest_text` (`_sha256_text(digest_text)` in the event dict, `neutralize_untrusted_markdown(digest_text)`) are untouched.

- [ ] **Update the two existing monkeypatch lambdas.** At `tests/test_operations.py:287-290` (in `test_digest_and_hub_apply_neutralize_source_model_and_topic_text`):

```python
    monkeypatch.setattr(
        "memoria_vault.runtime.operations._run_digest_model",
        lambda _policy, _runner, _source, _content, _topics, _interviews: {
            "text": raw_digest,
            "usage": None,
            "cost_usd": None,
            "elapsed_s": 0.0,
        },
    )
```

  At `tests/test_operations.py:343-348` (in `test_digest_and_hub_render_composed_fenced_fragments_inert`):

```python
    monkeypatch.setattr(
        "memoria_vault.runtime.operations._run_digest_model",
        lambda _policy, _runner, _source, _content, _topics, _interviews: {
            "text": "## Synthesis\n\nModel digest.\n\n## Hub suggestions\n\n- Framing\n",
            "usage": None,
            "cost_usd": None,
            "elapsed_s": 0.0,
        },
    )
```

- [ ] **Run tests to verify they pass:**
  `python -m pytest tests/test_operations.py -v`
  Expected: all pass.

- [ ] **Commit:**

```bash
git add src/memoria_vault/runtime/operations.py tests/test_operations.py
git commit -m "$(cat <<'EOF'
feat(operations): thread model telemetry through _run_digest_model

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task COST.4: three `model_call` event dicts gain `usage` / `cost_usd` / `elapsed_s`; refresh floor goldens

**Files:**
- Modify: `src/memoria_vault/runtime/operations.py` — the three `model_call` dict literals, each anchored by its `"output_hash":` line (pre-change refs: prompt-operation `:370-386`, `run_operation_model_text` `:456-473`, digest-compile `:528-544`; after COST.1-3 each shifts by a few lines — anchor by the literal's unique `"output_hash"` expression)
- Modify: `tests/test_operations.py` — extend `test_prompt_operation_neutralizes_model_output_before_staging` (event assertions currently at `:264-267`) and `test_compile_source_digest_traces_model_call_and_stages_hub_suggestions` (event assertions currently at `:217-222`); add one new test covering the `run_operation_model_text` call site (the `integrity.py:1466` seam) plus the no-content-capture posture
- Modify: `tests/fixtures/floor/goldens/*.json` (regenerated — they hash `.memoria/journal/*.jsonl` and `.memoria/journal-head`, which now carry three extra deterministic keys per `model_call` row)
- Test: `tests/test_operations.py`, `tests/test_floor_sweep_operations.py`

**Interfaces:**
- Consumes: `result` / `digest_result` locals bound in COST.2/COST.3; `append_journal_event(vault, event, *, context) -> dict[str, Any]` (unchanged seam); `call_with_context(function, vault, *args, **kwargs)` and `iter_jsonl` (existing test helpers/imports).
- Produces: `model_call` journal events at all three `operations.py` call sites carry `usage: dict[str, int] | None`, `cost_usd: float | None`, `elapsed_s: float` — additive keys only; every pre-existing key is unchanged.

**Steps:**

- [ ] **Write the failing tests.** In `tests/test_operations.py`: add `import json` to the stdlib imports (after `import hashlib`, line 3), add `run_operation_model_text` to the first operations import block (alphabetically between `resolve_operation_runner,` and `validate_operation_policy,`).

  (a) Extend `test_prompt_operation_neutralizes_model_output_before_staging` — after the existing `assert events[1]["output_hash"] == (...)` block (currently `:265-267`), add:

```python
    assert events[1]["usage"] == {
        "input_tokens": 17,
        "output_tokens": 5,
        "cache_read_tokens": 2,
        "cache_write_tokens": 1,
    }
    assert events[1]["cost_usd"] == pytest.approx(0.0125)
    assert events[1]["elapsed_s"] == pytest.approx(0.25)
```

  (b) Extend `test_compile_source_digest_traces_model_call_and_stages_hub_suggestions` — after `assert events[1]["prompt_hash"].startswith("sha256:")` (currently `:222`), add (fixture path — spec's null/zero contract):

```python
    assert events[1]["usage"] is None
    assert events[1]["cost_usd"] is None
    assert events[1]["elapsed_s"] == 0.0
```

  (c) Append the new test for the `run_operation_model_text` call site (the seam `integrity.py:1466` consumes), which also pins the no-content-capture posture:

```python
def test_run_operation_model_text_records_telemetry_without_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = workspace(tmp_path)
    policy = compile_policy()
    monkeypatch.setattr(
        "memoria_vault.runtime.operations._run_prompt_model",
        lambda _policy, _runner, _prompt, _input: {
            "text": "tier-two verdict text",
            "usage": {
                "input_tokens": 17,
                "output_tokens": 5,
                "cache_read_tokens": 2,
                "cache_write_tokens": 1,
            },
            "cost_usd": 0.0125,
            "elapsed_s": 0.25,
        },
    )

    call = call_with_context(
        run_operation_model_text,
        vault,
        policy,
        chat_runner(),
        "tier-two prompt body",
        input_text="left excerpt\n\nright excerpt",
        call_id="surface-tensions:tier2:testcall",
        route="surface-tensions-tier2",
        purpose="surface-tensions",
        machine="tier2-machine",
    )

    assert call["output"] == "tier-two verdict text"
    events = list(iter_jsonl(vault / ".memoria/journal/tier2-machine.jsonl"))
    model_call = next(event for event in events if event["event"] == "model_call")
    assert model_call["usage"] == {
        "input_tokens": 17,
        "output_tokens": 5,
        "cache_read_tokens": 2,
        "cache_write_tokens": 1,
    }
    assert model_call["cost_usd"] == pytest.approx(0.0125)
    assert model_call["elapsed_s"] == pytest.approx(0.25)
    # No content capture: counts, cost, and timing only — never prompt or output text.
    serialized = json.dumps(model_call)
    assert "tier-two prompt body" not in serialized
    assert "tier-two verdict text" not in serialized
    assert "left excerpt" not in serialized
    assert all(isinstance(value, int) for value in model_call["usage"].values())
    assert isinstance(model_call["cost_usd"], float)
    assert isinstance(model_call["elapsed_s"], float)
```

- [ ] **Run tests to verify they fail:**
  `python -m pytest "tests/test_operations.py::test_prompt_operation_neutralizes_model_output_before_staging" "tests/test_operations.py::test_compile_source_digest_traces_model_call_and_stages_hub_suggestions" "tests/test_operations.py::test_run_operation_model_text_records_telemetry_without_content" -v`
  Expected: all three fail with `KeyError: 'usage'` (the journal rows do not carry the new keys yet).

- [ ] **Write minimal implementation** — exactly the spec §3 three-key addition, one per literal, inserted immediately after each literal's `"output_hash"` line. In `run_prompt_operation` (literal anchored by `"route": "prompt-operation",`), after `"output_hash": _sha256_text(output),`:

```python
            "usage": result["usage"],
            "cost_usd": result["cost_usd"],
            "elapsed_s": result["elapsed_s"],
```

  In `run_operation_model_text` (literal anchored by `"call_id": call_id,`), after `"output_hash": _sha256_text(output),` — identical three lines:

```python
            "usage": result["usage"],
            "cost_usd": result["cost_usd"],
            "elapsed_s": result["elapsed_s"],
```

  In `compile_source_digest` (literal anchored by `"purpose": "digest_compile",`), after `"output_hash": _sha256_text(digest_text),`:

```python
            "usage": digest_result["usage"],
            "cost_usd": digest_result["cost_usd"],
            "elapsed_s": digest_result["elapsed_s"],
```

  No other change to those dicts; `context`, `append_journal_event`, and `commit_writer_changes` plumbing untouched.

- [ ] **Run tests to verify they pass:**
  `python -m pytest tests/test_operations.py -v`
  Expected: all pass.

- [ ] **Regenerate floor goldens** (journal hashes changed; the new fixture-path values are deterministic so the refreshed goldens are stable):

```bash
MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest tests/test_floor_sweep_operations.py -v
git status --porcelain tests/fixtures/floor/goldens/
git diff tests/fixtures/floor/goldens/
```

  Review: every hunk must touch only `.memoria/journal/*.jsonl` / `.memoria/journal-head` hash lines (and `db` counts must be unchanged). Then verify the refreshed goldens pass cleanly:
  `python -m pytest tests/test_floor_sweep_operations.py tests/test_floor_coverage.py -v`
  Expected: all pass with the env var **unset**.

- [ ] **Commit:**

```bash
git add src/memoria_vault/runtime/operations.py tests/test_operations.py tests/fixtures/floor/goldens
git commit -m "$(cat <<'EOF'
feat(operations): record usage/cost_usd/elapsed_s on model_call events

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task COST.5: docs — extend the `model_call` row description; full gate

**Files:**
- Modify: `docs/reference/commands-and-transports/prompt-operations.md:96-97`
- Test: `python scripts/verify` (the one correctness gate — lint, product gates, full roster including the static docs checks, offline smoke, syntax)

**Interfaces:**
- Consumes: the field semantics fixed by COST.1-COST.4 (`usage` counts, nullable best-effort `cost_usd`, `elapsed_s` seconds).
- Produces: reference prose naming the three new `model_call` fields. Per spec §4, `docs/explanation/architecture/telemetry-architecture.md` needs **no** prose change ("cost" is already named there as a tracked dimension — this change makes the claim true).

**Steps:**

- [ ] **Edit the doc.** In `docs/reference/commands-and-transports/prompt-operations.md`, replace lines 96-97:

```markdown
`model_call` rows include resolved
mode/provider/model/params, a prompt hash, and the hash of the raw model output.
```

  with:

```markdown
`model_call` rows include resolved
mode/provider/model/params, a prompt hash, the hash of the raw model output,
token `usage` counts, a best-effort `cost_usd` (null when the model has no
entry in the bundled local price snapshot, and always null on the
deterministic-fixture path), and `elapsed_s` wall-clock seconds.
```

- [ ] **Confirm no edit to telemetry-architecture.md:** `git diff --stat docs/explanation/architecture/telemetry-architecture.md` — expected: empty output (spec §4 says no prose change there).

- [ ] **Run the full gate:** `python scripts/verify`
  Expected: passes end to end (cspell accepts `cost_usd`/`elapsed_s` — verified against the repo config during planning; floor goldens were refreshed in COST.4).

- [ ] **Commit:**

```bash
git add docs/reference/commands-and-transports/prompt-operations.md
git commit -m "$(cat <<'EOF'
docs: document model_call usage/cost_usd/elapsed_s fields

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
EOF
)"
```
