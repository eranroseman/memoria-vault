# Graph Substrate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the two merged graph-substrate specs — full ULID identity re-keying, the seeded concept-type registry with closed validation, the single edge module with Toulmin activation, the catalog bridge and tension surface, and typed-consequence propagation with the decided-wrong flow.

**Architecture:** Identity moves from paths to frontmatter ids at schema v16 with FKs and a pending-edge model; `edges.py` becomes the single owner of both relation rosters (v17 activates warrant/qualifier/rebuttal); a pure propagation engine walks the grounding closure ∪ derivation DAG and marks dependents with typed consequences as validated frontmatter + verdict rows (v18), loudness-routing cards. Specs of record: `docs/superpowers/specs/2026-07-15-graph-{nodes-identity,edges-roles-propagation}-design.md` (main @ 9c77ba61).

**Tech Stack:** Python 3 / SQLite / pytest; no new dependencies.

## Global Constraints

- Correctness gate: `python scripts/verify`; `main` needs PR + `verify`/`gitleaks`; squash merge; explicit-path staging only; disposable vaults only.
- **Executes AFTER Plan 22's G1 + G2S1.1–.3 (+S12.2) land** — this plan consumes their Produces (`MIGRATIONS` mechanism, `concept_edge_id`, upsert-and-prune sparing tension, edge_id/attributes columns). All line refs are main @ `9c77ba61` and WILL shift after Plan 22 — re-anchor by symbol, not line.
- **Version chain (binding):** v16 = NID-B identity re-key · v17 = ERP-A roster CHECK · v18 = ERP-C consequence storage. Each schema task updates its MIGRATIONS entry, schema.sql DDL + PRAGMA tail, SCHEMA_VERSION, and pinned version tests in one commit.

## Cross-section contracts (BINDING — manifest seam resolutions)

1. **Edge-table shape:** NID-B's v16 redefines `concept_edges` (adds `target_path`, target nullable ON DELETE SET NULL, PK `(source_concept_id, relation_type, target_path)`). ERP-A.2's v17 CREATE/INSERT column lists extend mechanically to this shape; ERP-B/C/D SQL is written against it.
2. **Roster ownership:** ERP-A resolves the Plan-22 handoff as MOVE — `parse_links`/`normalize_link_target` relocate to `edges.py`, `schema.py` re-exports for one release. New code imports from `lib.edges`; a repo-wide guard test forbids roster literals outside it.
3. **Consequence-engine symbols:** ERP-D consumes ERP-C's real names — `propagation.compute_consequences(vault, target_id, *, trigger) -> dict[str, dict]` for the report card and `propagate_consequences(..., trigger="decided-wrong")` for marks. ERP-D's assumed `derive_consequences`/`claim_work_edges` names are superseded: the structural-impact rewire reads `state.concept_edges(vault)` rows plus ERP-B's `_note_edges(notes, *, works=...)`.
4. **Insert hooks, no circularity:** ERP-B.2 lands `insert_concept_edge` bare; ERP-C.5 retrofits the `propagate_edge_change(..., added=True)` call; ERP-D.6 retrofits `emit_edge_write_event(..., write_path="insert-concept-edge")`. Final call order inside the function: insert → propagate → emit.
5. **Outcome→decision dict** (`integrity.py:1169`): ERP-B adds `"confirm-tension": "accept"`, ERP-D adds `"decided-wrong": "override"` — merge, never overwrite.
6. **Tension rows** store endpoints lexicographically sorted; ERP-C propagation and ERP-D counters must not assume direction.
7. **Consequence-mark fields** (`stale: bool`, `consequence:` enum) are registered in the type yamls by NID-A's closed-validation task; ERP-C writes them, never touches yamls.
8. **Floor-golden serialization:** NID-B.6, NID-C.2/.5/.6, ERP-D.1/.5/.6 regenerate goldens — land sequentially, never in parallel worktrees, and not concurrently with other plans' golden tasks.
9. **Execution order:** NID-A → NID-B → ERP-A → ERP-B → ERP-C → ERP-D → NID-C (NID-C.1/.2 may run any time; its golden tasks obey contract 8).

## Requires PI ratification at merge (drafter rulings that extend the specs)

- **R1 (NID-B):** digests/fulltexts stay **path-keyed** (paths are pure functions of `work_id`) rather than bare-`work_id`-keyed — avoids PK collision with catalog works in the shared concepts namespace. Deviation from NODES §1.1's letter, preserving its intent.
- **R2 (NID-B):** file deletion keeps **tombstones** for verdict-carrying rows (prune only verdict-less; inbound edges revert to pending via ON DELETE SET NULL).
- **R3 (ERP-C):** `contradicts`/`tension` hops neither mark nor traverse (no consequence type exists for them by spec).
- **R4 (ERP-C):** new-relation edge direction = source is the license/bounding/exception note, target is the claim (mirrors `supports`).
- **R5 (ERP-C):** standing triggers fire only on transitions into {retracted, superseded}; archived is shelving.
- **R6 (ERP-C):** "active project's slice" = non-archived project note + thesis target + undirected edge reachability.
- **R7 (ERP-A):** structural-impact traversal widens to all six LINK_RELATIONS at roster convergence (not deferred to the §8 rewire).
- **R8 (ERP-B):** tension retraction verb = `state.delete_concept_edge` (no tombstone; existence-based semantics per spec); per-candidate tension prompt cards added as the minimal enabling surface.

Merging this PR ratifies R1–R8 unless individually vetoed.

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

- [ ] Write the failing tests. Append to `tests/test_schemas.py` (file already imports
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

- [ ] Run to verify failure:
  `python -m pytest tests/test_schemas.py::test_concept_type_registry_is_seeded_and_every_doc_type_names_a_member -v`
  — expected: `AttributeError: module ... has no attribute 'load_concept_types'`.

- [ ] Create the seed registry
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

- [ ] Add the mapping line to each of the six type yamls, directly after `category:`:
  - `types/note.yaml` (after :2 `category: notes`): `concept_type: note`
  - `types/hub.yaml` (after :2): `concept_type: hub`
  - `types/project.yaml` (after :2): `concept_type: project`
  - `types/digest.yaml` (after :2): `concept_type: digest`
  - `types/fulltext.yaml` (after `category: fulltext`): `concept_type: work`
  - `types/code-artifact.yaml` (after `category: projects`): `concept_type: project`

- [ ] Rewire the loader in `src/memoria_vault/runtime/subsystems/lib/schema.py`.
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

- [ ] Run to verify pass:
  `python -m pytest tests/test_schemas.py -v` — all pass (the three new tests plus the
  existing file; `test_concept_types_load` still passes because the six doc types are
  unchanged).

- [ ] Regenerate floor goldens (seed changed):
  `MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest tests/test_floor_sweep_operations.py tests/test_floor_coverage.py -q`
  then review the drift is hash-only churn under `.memoria/schemas/` with `git diff --stat tests/fixtures/floor/goldens`.

- [ ] Run the gate: `python scripts/verify` (the schema-doc drift check
  `scripts/checks/schema_doc_drift.py` is subset-direction per `_map_section_errors`
  :139-145, so the new `concept_type:` key in live yamls does not trip the docs).

- [ ] Commit:

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

- [ ] Write the test file `tests/test_concept_type_registry.py`:

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

- [ ] Register the file's level in `tests/conftest.py` `TEST_LEVELS`:
  `"test_concept_type_registry.py": "contract",` (alphabetical position, near
  `"test_capabilities.py"` :23).

- [ ] Run: `python -m pytest tests/test_concept_type_registry.py -v` — expected: PASS
  immediately (the shipped v12 CHECK already equals the 10-value roster; this task adds
  the gate, not a behavior change). Sanity-check the parser really extracted the CHECK by
  running once with the `len(registry) == 10` assertion — a regex under-match fails there.

- [ ] Commit:

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

- [ ] Write the failing test. Append to `tests/test_schemas.py`:

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

- [ ] Run to verify failure:
  `python -m pytest tests/test_schemas.py::test_consequence_mark_fields_registered_on_kb_doc_types -v`
  — expected: `AssertionError: note` on the `optional.get("stale")` line.

- [ ] Edit the four yamls (exact additions; keep existing key order):
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

- [ ] Run to verify pass:
  `python -m pytest tests/test_schemas.py -v` — all pass
  (`test_frontmatter_has_no_verdict_or_standing_fields` :92-98 is unaffected — `stale`
  is a consequence mark, not a verdict field; `check_status`/`standing` stay banned).

- [ ] Regenerate floor goldens (seed changed):
  `MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest tests/test_floor_sweep_operations.py tests/test_floor_coverage.py -q`

- [ ] Run the gate: `python scripts/verify` (docs yaml examples are checked
  subset-direction, so new live optional fields cannot trip
  `scripts/checks/schema_doc_drift.py`).

- [ ] Commit:

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
- Modify: FIXTURE SWEEP RESULTS PENDING

**Interfaces:**
- Consumes: `schema.validate_frontmatter(fm, schema, vocabulary_terms=None) -> list[str]`
  (signature unchanged) and its callers — `validate_memoria_workspace` (schema.py:289),
  `trusted_writer._validate_concept` (trusted_writer.py:1031), the linter detectors, and
  the pre-commit check.
- Produces: closed validation — new error string shape
  `"<field>: unknown field; declare it in the type schema or nest under x:"`.
  `x: map` (already optional in every type yaml) remains the extension hatch; its nested
  keys are never inspected.

**Steps:**

- [ ] FIXTURE SWEEP RESULTS PENDING

- [ ] Write the failing test. In `tests/test_schemas.py`, replace
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

- [ ] Run to verify failure:
  `python -m pytest tests/test_schemas.py::test_schema_rejects_undeclared_fields_while_x_hatch_passes -v`
  — expected: the `surprise: unknown field` assertion fails (open validator returns `[]`).

- [ ] Write the minimal implementation in
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

- [ ] Run to verify pass:
  `python -m pytest tests/test_schemas.py -v`.

- [ ] Update the docs prose `docs/reference/data-model/frontmatter.md:41-43` — replace
  the three lines beginning "Unknown extra fields are accepted during the alpha
  migration." with:

  ```markdown
  Validation is closed: fields a type schema does not declare are rejected. The
  `x:` map is the escape hatch for extension data, and `forbidden:` fields are
  reported as retired rather than unknown.
  ```

- [ ] FIXTURE SWEEP RESULTS PENDING

- [ ] Run the gate: `python scripts/verify`.

- [ ] Commit:

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

- `state.MIGRATIONS: dict[int, tuple[int, list[str | Callable[[sqlite3.Connection], None]]]]`
  — key = from_version, value = `(from_version + 1, ordered steps)`; str steps run
  via `conn.execute`, callables as `step(conn)`, each step list in one explicit
  `BEGIN`/`COMMIT`, `user_version` stamped by the loop (entries do **not** self-stamp)
  (Plan 22 header contract 1, G1.1/G1.2).
- `state.concept_edge_id(source_concept_id: str, relation_type: str, target_concept_id: str) -> str`
  — `sha256(f"{source}\0{relation}\0{target}")[:24]` (G2S1.2).
- `state.replace_concept_edges(vault, rows, *, paths=None) -> dict[str, int]` —
  upsert-and-prune sparing `relation_type = 'tension'` rows; edge rows carry
  `edge_id` + `attributes_json`, `attributes_json` preserved on conflict (G2S1.1/.2).
- `schema.py normalize_link_target(target: str) -> str` and
  `parse_links(links: object) -> list[tuple[str, str]]` (G2S1.1).
- Schema chain at 15 (`SCHEMA_VERSION = 15`, v13 edge reshape, v14 reverse indexes,
  v15 purpose enum). **This section takes exactly 15→16.**

## SPEC GAPs

- **SPEC GAP (id collision):** clause 1 keys catalog works, digests, and fulltexts
  all by bare `work_id`, which collides in the `concepts`/`concept_verdicts` PKs
  (three concept rows per work). This section keys **catalog works by bare
  `work_id`** and keeps **digests/fulltexts keyed by their paths**
  (`digests/<work_id>.md` — a pure function of `work_id`, and their filenames are
  machine-fixed, so rename-reconciliation is moot for them). PI to ratify or supply
  distinct id forms. Uniform runtime rule used throughout: *DB key = frontmatter
  `id` when it is a ULID, else the concept's path; catalog works = bare `work_id`.*
- **SPEC GAP (deletion semantics):** the spec decides rename semantics, not what
  happens to id-keyed verdict rows when a concept file is deleted outright. This
  section keeps them (the mirror row persists as a tombstone; inbound edges revert
  to pending via `ON DELETE SET NULL`); prune removes only verdict-less rows.

## Constraints other sections must honor

- v16 copies the 10-value `concepts.concept_type` CHECK verbatim; the
  registry-derived CHECK (NODES §2, another section) must ride its **own** migration.
- ERP-A's v17 relation-roster CHECK extension must rebuild/extend the **v16**
  `concept_edges` shape (nullable `target_concept_id`, `target_path` in the PK).
- `passages.concept_id` id-space changes at NID-B.4 (frontmatter id / bare work_id).
- New edge-row dict contract after NID-B.4: producers pass `target_path` (vault
  path or `catalog/sources/<work_id>` rendering), never a resolved id; resolution
  is `replace_concept_edges`'s job.

---

### Task NID-B.1: schema v16 — identity re-key migration (concepts.path, FKs, pending-edge form, bare-endpoint triggers, edge_id recompute)

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
  cascade triggers (`:251-276`), trailing pragma (`:378`, 15 → 16)
- Modify: `src/memoria_vault/runtime/state.py` — `SCHEMA_VERSION` (`:53`, 15 → 16);
  G1's `MIGRATIONS` dict (add key 15); new module function `_rekey_concept_identity`
  next to `_init` (`:2406` pre-Plan-22); `replace_concept_edges` (as landed by
  G2S1.1/.2) INSERT/prune keys; `concept_edges` SELECT column lists (`:2055-2076`
  pre-Plan-22); `_upsert_concept_mirror_conn` (`:3353-3368`) gains a `path` parameter;
  its three in-file callers (`:1097`, `:1124`, `:1206`) and the catalog caller
  (`:1598-1600`)
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
    `(source_concept_id, relation_type, target_path)`, triggers with bare endpoints.
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

### Task NID-B.2: trusted-writer state paths key by frontmatter identity (resolution + reconcile-by-path)

Runtime writers stop keying file concepts by path: the mirror carries the
frontmatter ULID (uniform rule: ULID when the `id` is one, else the path; catalog
works bare `work_id` — landed in NID-B.1), and every verdict/flag/status seam
resolves a path-or-id reference to the canonical key. Legacy path-keyed rows
(post-v16 provisional keys) re-key in place when the mirror observes the file —
FK `ON UPDATE CASCADE` carries verdicts and edges with them.

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

- [ ] Append to `tests/test_schema_v16_identity.py`:

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

- [ ] Run
  `python -m pytest tests/test_schema_v16_identity.py::test_ulid_identity_required_for_note_hub_project -v`
  — expected outcome: **PASS on first run** (the requirement is already seeded;
  this is a ratification guard, not new behavior). Verify it actually guards:
  temporarily change `hub.yaml:5` to `id: str`, rerun, confirm FAIL
  (`AssertionError: hub`), revert the yaml, rerun, confirm PASS.
- [ ] Run `python scripts/verify` — expect PASS.
- [ ] Commit:

  ```
  git add tests/test_schema_v16_identity.py
  git commit -m "test(schema): guard the seeded id:ulid requirement on note/hub/project types

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task NID-B.4: indexer path→id resolution + reconcile-by-id on rename (clause 3)

Reindex becomes the reconciliation pass the spec names: it rebuilds the concept
mirror first (so a renamed file's row reconciles its `path` by frontmatter-id
match before anything reads statuses), emits `passages.concept_id` in the new
id-space, and derives concept-edge rows whose source is the frontmatter id and
whose target is a `target_path` for `replace_concept_edges` to resolve.

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

- [ ] Append the failing rename-reconciliation test to
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

- [ ] Run
  `python -m pytest tests/test_query_substrate.py::test_rename_out_of_band_reconciles_by_frontmatter_id -v`
  — expect FAIL: `assert passage["concept_id"] == ULID_NOTE` never reached — the
  first block already fails on the edge assertion (`source_concept_id` is
  `'notes/alpha.md'`, not the ULID) because `_passage_row` still emits path-space
  ids; treat any of the id-space assertions failing as the expected failure.
- [ ] In `src/memoria_vault/runtime/indexing.py`: extend the vaultio import
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

- [ ] In `_passage_row` (`:101-130`), replace the `concept_id` line (`:114`) with
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
- [ ] Replace `_concept_edges` (the G2S1.1 body) so edges carry the source id and a
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

- [ ] Run
  `python -m pytest tests/test_query_substrate.py -v`
  — expect PASS, including the updated G2S1.1 mirror test and the two v13/v14 shape
  tests. If `test_concept_edges_mirror_links_and_persist_across_reindex` fails on
  the tension row, the direct INSERT predates the mirror rows — its fixture already
  writes both notes first; re-check the INSERT's `target_path` column from NID-B.1.
- [ ] Run `python scripts/verify` — expect PASS.
- [ ] Commit:

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

**Steps:**

- [ ] Append the failing tests to `tests/test_knowledge.py` (reuse the module's
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

- [ ] Run
  `python -m pytest tests/test_knowledge.py::test_move_concept_rewrites_inbound_links_and_path_in_one_transaction tests/test_knowledge.py::test_move_concept_refuses_bad_targets -v`
  — expect FAIL: `ImportError: cannot import name 'move_concept' from
  'memoria_vault.runtime.knowledge'`.
- [ ] Add `update_concept_path` to `src/memoria_vault/runtime/state.py` (below
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

- [ ] Add the move seam to `src/memoria_vault/runtime/knowledge.py` (after
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

- [ ] Run
  `python -m pytest tests/test_knowledge.py::test_move_concept_rewrites_inbound_links_and_path_in_one_transaction tests/test_knowledge.py::test_move_concept_refuses_bad_targets -v`
  — expect PASS.
- [ ] Run `python scripts/verify` — expect PASS.
- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/state.py src/memoria_vault/runtime/knowledge.py tests/test_knowledge.py
  git commit -m "feat(knowledge): move_concept — inbound-link rewrite + path update in one writer transaction

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task NID-B.6: `memoria mv` — operation card, worker dispatch, CLI, floor entry, docs

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

- [ ] Write the failing worker-dispatch test in `tests/test_knowledge.py`:

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
- [ ] Run
  `python -m pytest tests/test_knowledge.py::test_move_concept_operation_dispatches_via_worker -v`
  — expect FAIL: the request errors with the missing-manifest/unknown-operation
  message from `load_operation_policy` (`request["status"] == "failed"`).
- [ ] Create `src/memoria_vault/product/capabilities/operations/move-concept.md`
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

- [ ] In `src/memoria_vault/runtime/worker.py`: add
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

- [ ] Run
  `python -m pytest tests/test_knowledge.py::test_move_concept_operation_dispatches_via_worker -v`
  — expect PASS.
- [ ] Add the CLI command in `src/memoria_vault/cli.py`, after the `link` block
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

- [ ] Register the floor entry in `tests/floor_lib.py` `OPERATION_REGISTRY`
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

- [ ] Run
  `python -m pytest tests/test_floor_coverage.py -v`
  — expect PASS (`test_every_operation_has_a_floor_entry` now sees the card and the
  entry). Then run the floor sweep level the repo's harness prescribes for
  operation-catalog changes; if the seeded-vault goldens shift (new capability card
  in the seed), regenerate them exactly as the failing floor test's message
  instructs — never hand-edit goldens.
- [ ] Update the three docs listings (the doc-claims gate checks these):
  add `move-concept` to the alphabetical operation id list at
  `docs/reference/commands-and-transports/system-actions.md:26`; to the pi-protected
  roster sentence at `docs/reference/commands-and-transports/system-actions-operations.md:17`
  and a table row following the `Curate note link` pattern (`:123`):

  ```markdown
  | Move concept | worker operation `move-concept` + runtime helper (`move_concept`) | Renames a note, hub, or project file, rewriting inbound `links:` entries and the concept's DB `path` attribute in one trusted-writer commit; identity is the frontmatter `id`, so verdicts and edges stay attached. |
  ```

  and to the `pi` row at `docs/reference/control-and-policy/control-plane.md:61`.
- [ ] Run `python scripts/verify` — expect PASS.
- [ ] Commit:

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

- [ ] Append the failing lifecycle test to `tests/test_query_substrate.py`:

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
- [ ] Run
  `python -m pytest tests/test_query_substrate.py::test_pending_edges_resolve_when_target_appears -v`
  — expect FAIL on the **tension** assertions:
  `assert rows["tension"]["target_concept_id"] == "notes/future.md"` sees `None` —
  the mirror pass re-resolves only rows it inserts, never retained tension rows.
- [ ] In `state.replace_concept_edges` (NID-B.1 body), add the resolution pass at
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

- [ ] Run
  `python -m pytest tests/test_query_substrate.py -v`
  — expect PASS (the whole file: v13/v14 shape pins, G2S1.1 mirror test, NID-B.4
  rename test, this lifecycle test).
- [ ] Run `python scripts/verify` — expect PASS.
- [ ] Commit:

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

Steps:

- [ ] Write the failing test. Add to `tests/test_identifier_renames.py` —
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

- [ ] Run test to verify it fails:
  `python -m pytest tests/test_identifier_renames.py::test_frontmatter_type_filters_carry_no_dead_work_literal -v`
  — expected failure: `AssertionError` listing exactly six offenders
  (`src/memoria_vault/runtime/search_index.py:380`,
  `src/memoria_vault/runtime/integrity.py:152`, `:606`, `:640`, `:1387`,
  `src/memoria_vault/cli.py:1065`,
  `src/memoria_vault/runtime/knowledge.py:1287`).

- [ ] Write minimal implementation — drop `"work"` from each filter
  (singleton sets become `!=` comparisons, matching surrounding style):
  - `search_index.py:380`:
    `if frontmatter.get("type") not in {"digest", "note", "hub", "project"}:`
  - `integrity.py:152`:
    `if frontmatter.get("type") not in {"digest", "note"}:`
  - `integrity.py:606`:
    `if frontmatter.get("type") != "note":`
  - `integrity.py:640`:
    `if frontmatter.get("type") != "digest" or not _is_checked_concept(vault, rel):`
  - `integrity.py:1387`:
    `if frontmatter.get("type") != "note":`
  - `cli.py:1065`:
    `if frontmatter.get("type") not in {"digest", "note"}:`
  - `knowledge.py:1287`:
    `if frontmatter.get("type") != "digest":`

- [ ] Run test to verify it passes:
  `python -m pytest tests/test_identifier_renames.py -v`

- [ ] Verify no behavior regression in the touched modules:
  `python -m pytest tests/test_integrity.py tests/test_knowledge.py tests/test_search_index.py tests/test_cli.py tests/test_cli_honesty.py -q`
  — all pass (the branches were unreachable; `tests/test_cli.py:518-527`'s
  `type: work` fixture is alpha15-migration *input* that `memoria migrate`
  rewrites to `digest` before any filter sees it).

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

- [ ] Edit the manifest. Replace lines 4-5 (description) with:
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

- [ ] Edit `docs/reference/commands-and-transports/system-actions-operations.md:140`
  — replace the row's third cell so the full row reads:
  ```markdown
  | Check citation survival | runtime integrity helper (`check_citation_survival`) | Flags a missing or stale generated `bibliography.bib` projection for checked catalog sources; this is the vault-level bibliography staleness check, not a per-Concept citation-payload scan. |
  ```

- [ ] Regenerate the one drifted golden and verify the sweep:
  `MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest "tests/test_floor_sweep_operations.py::test_operation[regenerate-capability-index]" -v`
  then re-run without the env var:
  `python -m pytest "tests/test_floor_sweep_operations.py::test_operation[regenerate-capability-index]" "tests/test_floor_sweep_operations.py::test_operation[integrity-citation-survival-check]" -v`
  — both pass; `git diff tests/fixtures/floor/goldens/` shows only the one
  capability-index file hash changing.

- [ ] Verify gates: `python scripts/checks/doc_claims_gate.py` prints
  `doc-claims-gate: clean`; `python -m pytest tests/test_capabilities.py tests/test_integrity.py -q` passes.

- [ ] Commit:
  ```
  git add src/memoria_vault/product/capabilities/operations/integrity-citation-survival-check.md docs/reference/commands-and-transports/system-actions-operations.md tests/fixtures/floor/goldens/regenerate-capability-index.json
  git commit -m "docs: describe citation-survival check as the shipped bibliography.bib staleness check (NODES §4)

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task NID-C.3: Hub Candidates block writer (delimited terminal section)

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
  - `trusted_writer._write_checked(...)` via the extended `mark_checked` (`trusted_writer.py:1038`, `allow_retired_input=True` pops retired fields such as a hand-written `check_status:`)
  - `state.concept_check_status(vault, concept_id) -> str` (`state.py:1063`, returns `"unchecked"` for unregistered concepts)
  - `content_security.neutralize_untrusted_markdown_fragment(fragment) -> str` (`content_security.py:130` — the CS1 seam; the writer's machine-written region routes all free text through it)
  - `vaultio.RETIRED_FRONTMATTER_FIELDS`, `vaultio.frontmatter_doc`, `vaultio.split_frontmatter`
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
journal-backed). Frontmatter is re-serialized by the trusted writer (retired
fields popped, missing universal fields defaulted) — only the *body* carries
the byte-identical guarantee, per the spec's acceptance criterion.

Steps:

- [ ] Write the failing tests. Create `tests/test_hub_candidates.py`:

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

  (If `sha256_file` is not exported by `vaultio` at implementation time, import
  it from where `tests/floor_lib.py:105` imports it and adjust the single
  import line — verify with `grep -n "sha256_file" tests/floor_lib.py`.)

- [ ] Register the test level: in `tests/conftest.py` `TEST_LEVELS` (line 18),
  insert `"test_hub_candidates.py": "contract",` immediately before
  `"test_hub_handoff.py": "contract",`.

- [ ] Run tests to verify they fail:
  `python -m pytest tests/test_hub_candidates.py -v`
  — expected failure: `ModuleNotFoundError: No module named
  'memoria_vault.runtime.hub_candidates'`.

- [ ] Write minimal implementation. First, extend
  `trusted_writer.mark_checked` (`trusted_writer.py:632`): add the keyword
  `body: str | None = None` after `schemas_dir`, extend the docstring with
  `With ``body``, rewrite the Concept's body in the same checked write;
  frontmatter still comes from the live file.`, and change the tail
  (`trusted_writer.py:649-660`) to:

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
          allow_retired_input=True,
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
  from memoria_vault.runtime.vaultio import (
      RETIRED_FRONTMATTER_FIELDS,
      frontmatter_doc,
      split_frontmatter,
  )

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
      for field in RETIRED_FRONTMATTER_FIELDS:
          frontmatter.pop(field, None)
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

- [ ] Run tests to verify they pass:
  `python -m pytest tests/test_hub_candidates.py -v`

- [ ] Verify no trusted-writer regression:
  `python -m pytest tests/test_trusted_writer.py -q` if that file exists, else
  `python -m pytest tests/test_journal_trust.py tests/test_operations.py -q`.

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

Steps:

- [ ] Write the failing tests. Append to `tests/test_hub_candidates.py`:

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

- [ ] Run tests to verify they fail:
  `python -m pytest tests/test_hub_candidates.py::test_related_work_candidates_ranks_by_shared_references tests/test_hub_candidates.py::test_related_work_candidates_breaks_ties_by_work_id -v`
  — expected failure: `AttributeError: module 'memoria_vault.runtime.state'
  has no attribute 'related_work_candidates'`.

- [ ] Write minimal implementation. In `src/memoria_vault/runtime/state.py`,
  after `replace_work_graph_edges` (line 1837), add:

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

- [ ] Run tests to verify they pass:
  `python -m pytest tests/test_hub_candidates.py -v`

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

Steps:

- [ ] Write the failing catalog-parity state: create
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

- [ ] Run tests to verify they fail:
  `python -m pytest tests/test_capabilities.py::test_worker_operations_are_cataloged_and_policy_shaped "tests/test_floor_sweep_operations.py::test_operation[digest-related-works]" -v`
  — expected failures: the capabilities parity test fails with
  `digest-related-works` in `catalog_ids` but not `worker_ids`; the floor
  sweep case fails with worker status `failed` /
  `unsupported operation: 'digest-related-works'` (`worker.py:1090`).

- [ ] Write the failing operation-level test. Append to
  `tests/test_hub_candidates.py` (add
  `from memoria_vault.runtime.operations import digest_related_works as _digest_related_works`
  to its imports):

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

- [ ] Write minimal implementation. In `operations.py`, add
  `read_frontmatter` to the `vaultio` import block (lines 35-41) and
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
  (line 405), matching the surrounding if-chain style:

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

- [ ] Run tests to verify they pass:
  `python -m pytest tests/test_hub_candidates.py tests/test_capabilities.py -v`

- [ ] Generate the new floor golden plus the drifted capability-index golden
  (**golden addition noted here in the manifest**, per the floor harness's
  opt-in update contract at `tests/floor_lib.py:331-355`):
  `MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest "tests/test_floor_sweep_operations.py::test_operation[digest-related-works]" "tests/test_floor_sweep_operations.py::test_operation[regenerate-capability-index]" -v`
  Review `git diff tests/fixtures/floor/goldens/` (one new file, one
  capability-index hash change), then re-run both without the env var and
  confirm they pass; also run
  `python -m pytest tests/test_floor_coverage.py -v`.

- [ ] Update the hand-maintained docs. In
  `docs/reference/commands-and-transports/system-actions.md:26`, insert
  `` `digest-related-works` `` into the alphabetical roster (after
  `` `curate-note-link` ``, before `` `enrich-source` ``). In
  `docs/reference/commands-and-transports/system-actions-operations.md`, add
  after the "Compile source digest" row (line 105):

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

- [ ] Update the test first. In `tests/test_operations.py:159-165`, replace
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

- [ ] Run test to verify it fails:
  `python -m pytest tests/test_operations.py::test_compile_source_digest_traces_model_call_and_stages_hub_suggestions -v`
  — expected failure: `assert result["hub_suggestions"] == ["hubs/framing.md"]`
  (current code returns the staging id, and the curated hub file carries no
  Candidates section).

- [ ] Write minimal implementation. In `operations.py:584-618`, replace the
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

- [ ] Run test to verify it passes:
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

- [ ] Verify the other compile consumers still pass:
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
- **Merge ERP-A.1 and ERP-A.2 in the same PR.** A.1 widens frontmatter
  validation to six relations (via the `schema.py` re-export feeding
  `_check_links`) while the DB CHECK still rejects the three new values; A.2
  closes that window. Neither commit may reach `main` without the other.
  ERP-A.3/.4 execute after A.2; ERP-A.5 (docs) any time after A.2.
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

- [ ] Write the failing test file `tests/test_edges.py`:

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

- [ ] Register the file in `tests/conftest.py` TEST_LEVELS (insert
  alphabetically, after `"test_e2e_smoke_helpers.py": "package",` at line 40):

  ```python
      "test_edges.py": "unit",
  ```

- [ ] Run test to verify it fails:
  `python -m pytest tests/test_edges.py -v`
  Expected failure: `ImportError: cannot import name 'edges' from
  'memoria_vault.runtime.subsystems.lib'`.
- [ ] Write `src/memoria_vault/runtime/subsystems/lib/edges.py` (the two
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

- [ ] In `src/memoria_vault/runtime/subsystems/lib/schema.py`: delete the
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
- [ ] Run test to verify it passes:
  `python -m pytest tests/test_edges.py -v` — expect PASS (7 tests).
- [ ] Run the schema-validation neighbors to prove the move changed nothing
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

### Task ERP-A.2: v17 activation migration — `concept_edges.relation_type` CHECK extends to `EDGE_RELATIONS`

Must merge in the same PR as ERP-A.1 (see section preamble). Depends on:
Plan 22 G1 + G2S1.2/.3 (v13/v14) and this plan's NID-B (v16) merged, so
`SCHEMA_VERSION == 16` at task start.

**Files:**
- Modify: `src/memoria_vault/runtime/schema.sql:240-250` at 9c77ba61 — the
  `concept_edges` CREATE block; post-G2S1.2 it also carries `edge_id`,
  `attributes_json`, and the `idx_concept_edges_edge_id` index — re-locate by
  `relation_type IN ('supports', 'contradicts', 'extends', 'tension')` and
  edit only that roster; trailing `PRAGMA user_version` (line 378 at
  9c77ba61, reading `= 16` after NID-B) → `= 17`
- Modify: `src/memoria_vault/runtime/state.py:53` (`SCHEMA_VERSION = 16` →
  `17`); G1's `MIGRATIONS` dict (add key 16); `_concept_edge_relation`
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
- Consumes: `state.MIGRATIONS: dict[int, tuple[int, list[str | Callable]]]`
  (Plan 22 G1.1); post-v13 `concept_edges` shape with `edge_id` +
  `attributes_json` (Plan 22 G2S1.2) and `idx_concept_edges_edge_id` /
  `idx_concept_edges_target` indexes (G2S1.2/.3 — dropped with the table,
  recreated by the migration); `edges.EDGE_RELATIONS` (ERP-A.1);
  `state.replace_concept_edges` upsert-and-prune sparing tension rows
  (Plan 22 G2S1.1).
- Produces:
  - `MIGRATIONS[16] = (17, [...])` — SQLite table rebuild extending the
    `relation_type` CHECK to the seven `EDGE_RELATIONS` (SQLite cannot ALTER
    a CHECK), preserving all rows, PK, and both indexes.
  - `state._concept_edge_relation` accepts exactly `edges.EDGE_RELATIONS`
    (ERP-B's `insert_concept_edge` and ERP-C's consequence writers rely on
    this gate).
  - Parity guarantee: the live DB's `relation_type` CHECK roster ==
    `edges.EDGE_RELATIONS`, enforced by
    `test_concept_edges_relation_check_matches_edge_relations` on both the
    fresh-schema and the migrated-legacy paths.

**Steps:**

- [ ] Write the failing tests at the end of `tests/test_query_substrate.py`
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
- [ ] Run test to verify it fails:
  `python -m pytest "tests/test_query_substrate.py::test_concept_edges_relation_check_matches_edge_relations" "tests/test_query_substrate.py::test_replace_concept_edges_accepts_activated_relations" -v`
  Expected failures: the first asserts
  `{'supports', 'contradicts', 'extends', 'tension'} == {...seven...}`; the
  second raises `ValueError: unknown concept edge relation: qualifier` from
  `_concept_edge_relation`.
- [ ] In `src/memoria_vault/runtime/schema.sql`, extend the roster inside the
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
- [ ] In `src/memoria_vault/runtime/state.py`:
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

- [ ] Bump the two version pins: in `tests/test_schema_version.py` rename the
  pin test to `test_schema_lands_at_user_version_17` and change both `16`s to
  `17`; in `tests/test_query_substrate.py` change the
  `state.SCHEMA_VERSION == 16` pin to `== 17`. Verify
  `tests/test_schema_v10.py` already compares against
  `state.SCHEMA_VERSION` (G2S1.2) — no edit.
- [ ] Run test to verify it passes:
  `python -m pytest tests/test_query_substrate.py tests/test_schema_version.py tests/test_schema_v10.py tests/test_edges.py -v`
  — expect PASS.
- [ ] Run `python scripts/verify` — expect PASS.
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

- [ ] Write the failing tests. At the end of
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

- [ ] Run tests to verify they fail:
  `python -m pytest "tests/test_project_structural_impact.py::test_build_edges_includes_activated_relations" "tests/test_trusted_writer.py::test_commit_writer_extracts_rebuttal_candidate_and_skips_tension" "tests/test_project_knowledge.py::test_analyze_project_argument_reads_activated_relation_links" -v`
  Expected failures: structural-impact assertion sees `[]` (rebuttal filtered
  out by the two-value `RELATIONS`); trusted-writer sees `len(prompts) == 0`
  (rebuttal not in `ARGUMENT_EDGE_TYPES`); knowledge sees
  `relation_count == 0` (warrant not in the hardcoded triple).
- [ ] Edit `structural_impact_graph.py`:
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
- [ ] Edit `knowledge.py`:
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
- [ ] Edit `trusted_writer.py`:
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
- [ ] Edit `indexing.py`: change the G2S1.1 import line

  ```python
  from memoria_vault.runtime.subsystems.lib.schema import parse_links
  ```

  to

  ```python
  from memoria_vault.runtime.subsystems.lib.edges import parse_links
  ```

- [ ] Run tests to verify they pass, plus the touched suites:
  `python -m pytest tests/test_project_structural_impact.py tests/test_trusted_writer.py tests/test_project_knowledge.py tests/test_query_substrate.py -v`
  — expect PASS.
- [ ] Run `python scripts/verify` — expect PASS.
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
  (runtime), `tests/test_query_substrate.py` (contract), `tests/test_edges.py`
  (unit) — all registered, no conftest change

**Interfaces:**
- Consumes: `edges.LINK_RELATIONS` (already imported into `knowledge.py` by
  ERP-A.3); `schema.validate_frontmatter` / `schema.load_types`;
  `state.concept_edges`; `tests.helpers.ROOT`, `write_checked_concept`,
  `copy_memoria_dirs`; the `rebuild_passage_index` wrapper at
  `tests/test_query_substrate.py:18-19`.
- Produces:
  - `curate_note_link` accepts exactly `edges.LINK_RELATIONS`; error message
    `f"note link_type must be one of {', '.join(sorted(LINK_RELATIONS))}"`
    (ERP-B's `confirm-tension` outcome relies on `tension` staying rejected
    here; the relate control's served roster — `summary.link_relations` in
    the surfaces plan — serves these same six via `LINK_RELATIONS`).
  - `memoria link --rel` choices == `tuple(sorted(edges.LINK_RELATIONS))`.
  - Repo guard test: no `.py` file under `src/memoria_vault` except
    `lib/edges.py` contains a quoted `"supports", "contradicts"` roster
    literal.

**Steps:**

- [ ] Write the failing tests. At the end of `tests/test_schemas.py` (mirrors
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
  `test_curate_note_link_records_typed_link_on_checked_note`, line 395):

  ```python
  def test_curate_note_link_accepts_rebuttal_and_rejects_tension(tmp_path: Path) -> None:
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
          vault, "source", "rebuttal", "target", actor="pi", machine="curator"
      )

      assert result["link_type"] == "rebuttal"
      source_fm = read_frontmatter(vault / "notes/source.md")
      assert source_fm["links"] == {"rebuttal": ["notes/target.md"]}

      with pytest.raises(ValueError, match="link_type must be one of"):
          curate_note_link(vault, "source", "tension", "target", actor="pi", machine="curator")
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

- [ ] Run tests to verify they fail:
  `python -m pytest tests/test_schemas.py::test_note_links_accept_activated_toulmin_relations "tests/test_knowledge.py::test_curate_note_link_accepts_rebuttal_and_rejects_tension" "tests/test_query_substrate.py::test_activated_link_round_trips_to_edge_row" tests/test_edges.py::test_single_roster_definition_repo_wide -v`
  Expected: the schemas test PASSES already (the roster widened in A.1 —
  it pins the behavior); the knowledge test fails with
  `ValueError: note link_type must be supports, contradicts, or extends`;
  the round-trip PASSES already (A.1 + A.2 + G2S1.1 — it pins §10's
  acceptance); the guard test fails listing `src/memoria_vault/cli.py` and
  `src/memoria_vault/runtime/knowledge.py`.
- [ ] Edit `knowledge.py` `curate_note_link` (lines 360-362):

  ```python
      link_type = link_type.strip().lower()
      if link_type not in LINK_RELATIONS:
          raise ValueError(f"note link_type must be one of {', '.join(sorted(LINK_RELATIONS))}")
  ```

- [ ] Edit `cli.py`: add the import after line 27
  (`from memoria_vault.runtime.paths import safe_filename`):

  ```python
  from memoria_vault.runtime.subsystems.lib.edges import LINK_RELATIONS
  ```

  and change line 263 to:

  ```python
      link.add_argument("--rel", required=True, choices=tuple(sorted(LINK_RELATIONS)))
  ```

- [ ] Run tests to verify they pass, plus the touched suites:
  `python -m pytest tests/test_edges.py tests/test_schemas.py tests/test_knowledge.py tests/test_query_substrate.py tests/test_cli.py -v`
  — expect PASS.
- [ ] Run `python scripts/verify` — expect PASS.
- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/knowledge.py src/memoria_vault/cli.py tests/test_schemas.py tests/test_knowledge.py tests/test_query_substrate.py tests/test_edges.py
  git commit -m "feat(graph): validator, curate-note-link, and CLI accept the six link relations

  warrant/qualifier/rebuttal round-trip from vim to concept_edges rows;
  repo-wide guard pins the single-roster acceptance criterion.

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task ERP-A.5: plan amendments — served-verbs acceptance + `claims.base` glyph column

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

- [ ] In the surfaces plan, line 21, change

  `` `link_relations` from `schema.LINK_RELATIONS` ``

  to

  `` `link_relations` from `edges.LINK_RELATIONS` (moved from `schema.LINK_RELATIONS` by the graph-edges plan ERP-A.1; the `schema` re-export stays valid for one release) ``

- [ ] In the surfaces plan, line 7411, change

  `` `LINK_RELATIONS` is defined once at `src/memoria_vault/runtime/subsystems/lib/schema.py:39` ``

  to

  `` `LINK_RELATIONS` is defined once at `src/memoria_vault/runtime/subsystems/lib/edges.py` (formerly `schema.py:39`; moved by the graph-edges plan ERP-A.1) ``

  and append this sentence to the end of the same paragraph:

  `` **Recorded amendment (EDGES §4, graph-edges plan ERP-A.5):** once `warrant`/`qualifier`/`rebuttal` activate, the served roster is six verbs; every acceptance here reads "exactly the served verbs" — never a counted three — and the control renders as a segmented control or dropdown accordingly. ``

- [ ] In the surfaces plan, line 9580, change

  `Relation shows exactly the three server verbs as a segmented control`

  to

  `Relation shows exactly the served verbs (summary.link_relations — six once the graph-edges plan's roster activation lands) as a segmented control or dropdown`

- [ ] In the alpha.23 plan, insert after the R1NG.1 "Honesty notes in force"
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

- [ ] Run `python scripts/verify` — expect PASS (doc-claims gate covers the
  edited plans).
- [ ] Commit:

  ```
  git add docs/superpowers/plans/2026-07-15-surfaces-bootstrap-and-plugins.md docs/superpowers/plans/2026-07-15-alpha23-usable-loop.md
  git commit -m "docs(plans): record EDGES roster amendments — served verbs + claims.base glyph column

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
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

- [ ] Write the failing tests (append to `tests/test_knowledge.py`; `pytest`,
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

- [ ] Run to verify failure:
  `python -m pytest "tests/test_knowledge.py::test_curate_note_link_accepts_checked_catalog_source_target" -v`
  — expected: `FileNotFoundError: .../catalog/sources/source-alpha` raised
  from `_checked_concept`'s `is_file()` gate (`knowledge.py:3408-3409`).
  (The other two may pass incidentally — the missing-source case already
  raises FileNotFoundError for the wrong reason; keep them as pinning tests.)

- [ ] Write the minimal implementation. In
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

- [ ] Run to verify pass:
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

- [ ] Write the failing test (append to `tests/test_project_knowledge.py`;
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

- [ ] Run to verify failure:
  `python -m pytest "tests/test_project_knowledge.py::test_analyze_project_argument_traverses_claim_to_work_bridge" -v`
  — expected: AssertionError on the `in result["edges"]` membership
  (claim→work edge dropped by `_note_edges`' `target in notes` filter,
  `knowledge.py:3007`).

- [ ] Write the minimal implementation in
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

- [ ] Run to verify pass:
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

- [ ] Write the failing tests (append to `tests/test_runtime_state.py`; first
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

- [ ] Run to verify failure:
  `python -m pytest tests/test_runtime_state.py -v -k insert_concept_edge`
  — expected: `AttributeError: module 'memoria_vault.runtime.state' has no
  attribute 'insert_concept_edge'`.

- [ ] Write the minimal implementation (after `replace_concept_edges` in
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

- [ ] Run to verify pass:
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

- [ ] Write the failing test (append to
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

- [ ] Run to verify failure:
  `python -m pytest "tests/test_integrity_surface_tensions.py::test_surface_tensions_commit_writes_confirmable_tension_prompts" -v`
  — expected: `KeyError: 'tension_prompts'`.

- [ ] Write the minimal implementation.

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

- [ ] Run to verify pass:
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

- [ ] Write the failing tests (append to
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

- [ ] Run to verify failure:
  `python -m pytest tests/test_integrity_surface_tensions.py -v -k confirm_tension`
  — expected: `ValueError: unsupported attention outcome for resolved:
  'confirm-tension'` (from `integrity.py:1145-1146`).

- [ ] Write the minimal implementation in
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

- [ ] Run to verify pass:
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

- [ ] Write the failing test (append to `tests/test_runtime_state.py`; add
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

- [ ] Run to verify failure:
  `python -m pytest "tests/test_runtime_state.py::test_delete_concept_edge_retracts_confirmed_tension_row" -v`
  — expected: `AttributeError: module 'memoria_vault.runtime.state' has no
  attribute 'delete_concept_edge'`.

- [ ] Write the minimal implementation (after `insert_concept_edge` in
  `src/memoria_vault/runtime/state.py`):

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

- [ ] Run to verify pass:
  `python -m pytest "tests/test_runtime_state.py::test_delete_concept_edge_retracts_confirmed_tension_row" -v`
  — expected: 1 passed.

- [ ] Run the full gate: `python scripts/verify` — expected: green (lint,
  product gates, tests, offline smoke, syntax).

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

- [ ] Register the test file. In `tests/conftest.py` `TEST_LEVELS` (line 18 dict), add alphabetically:

  ```python
      "test_propagation.py": "runtime",
  ```

- [ ] Write the failing tests. Create `tests/test_propagation.py`:

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

- [ ] Run to verify failure: `python -m pytest tests/test_propagation.py -v` — expected: `ModuleNotFoundError: No module named 'memoria_vault.runtime.propagation'`.

- [ ] Write the minimal implementation. Create `src/memoria_vault/runtime/propagation.py`:

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

- [ ] Run to verify pass: `python -m pytest tests/test_propagation.py -v`.
- [ ] Run the gate: `python scripts/verify`.
- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/propagation.py tests/test_propagation.py tests/conftest.py
  git commit -m "feat(propagation): pure consequence-closure walk over grounding closure ∪ derivation DAG

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task ERP-C.2: Consequence typing rules — the trigger × hop decision table

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

- [ ] Write the failing tests. Append to `tests/test_propagation.py`:

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

- [ ] Run to verify failure: `python -m pytest tests/test_propagation.py::test_hop_consequence_encodes_spec_parentheticals -v` — expected: `ImportError: cannot import name 'hop_consequence'`.

- [ ] Write the minimal implementation. In `src/memoria_vault/runtime/propagation.py`, below `HOP_DERIVED`:

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

- [ ] Run to verify pass: `python -m pytest tests/test_propagation.py -v`.
- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/propagation.py tests/test_propagation.py
  git commit -m "feat(propagation): trigger×hop consequence decision table per EDGES §5

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task ERP-C.3: Schema v18 — `consequence` column on `concept_verdicts` + DB mirror helpers

**Migration IS needed (the honest read):** the current verdict row is
`concept_verdicts(concept_id TEXT PRIMARY KEY, check_status TEXT NOT NULL CHECK(...))`
(schema.sql:60-63) — two columns, no JSON or spare column anywhere on the
table, so the spec's "mirrored in the DB verdict row" cannot land without
DDL. `concept_flags` (schema.sql:64-71) cannot absorb it either: its `flag`
CHECK admits only `'stale'` and the spec keeps that row as *compatibility*,
not as the queryable consequence record. v18 it is.

**Files:**
- Modify: `src/memoria_vault/runtime/state.py` — `SCHEMA_VERSION` (line 53, will read 17 after NID-B/ERP-A), the `MIGRATIONS` dict (Plan 22 G1.1; entries 12→13/13→14/14→15 from Plan 22, 15→16/16→17 from NID-B/ERP-A), `set_concept_verdict` checked-clear block (lines 1056-1060), new helpers after `concept_flags` (ends line 1339)
- Modify: `src/memoria_vault/runtime/schema.sql` — `concept_verdicts` DDL (lines 60-63) + trailing `PRAGMA user_version` (line 378, will read 17)
- Modify: `tests/test_schema_version.py` (pinned assertion at lines 14-17, function renamed by the earlier version tasks — bump to 18), `tests/test_schema_v10.py` (lines 39-41), `tests/test_query_substrate.py` (line 31)
- Modify: `tests/test_runtime_state.py` (append migration + helper tests; already registered at level `runtime`, conftest.py line 96)

**Interfaces:**
- Consumes: `state.MIGRATIONS` mechanism (Plan 22 G1.1), `state.connect` / `state.db_path` (state.py:460), `_set_concept_verdict_conn` (state.py:3371), `propagation.CONSEQUENCE_TYPES` (C.1) for the parity test.
- Produces:
  - Schema v18: `concept_verdicts.consequence TEXT NOT NULL DEFAULT '' CHECK (consequence IN ('', 'grounds-lost', 'warrant-lost', 'qualifier-regression', 'rebuttal-strengthened'))`.
  - `state.set_concept_consequence(vault: Path, concept_id: str, consequence: str) -> None` — upserts the verdict row's consequence, preserving an existing `check_status` (inserts as `'unchecked'` when no row exists).
  - `state.concept_consequence(vault: Path, concept_id: str) -> str` — `''` when unset/missing/no DB.
  - New contract on `state.set_concept_verdict`: setting `'checked'` clears `consequence` (alongside the existing stale-flag delete) — re-verification wipes the mark's DB mirror.

**Steps:**

- [ ] Write the failing tests. Append to `tests/test_runtime_state.py`:

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

- [ ] Run to verify failure: `python -m pytest tests/test_runtime_state.py::test_v17_to_v18_adds_consequence_column -v` — expected: `RuntimeError: unsupported Memoria DB schema version: 17` (no registered 17→18 path yet).

- [ ] Implement, all in one commit:
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

- [ ] Run to verify pass: `python -m pytest tests/test_runtime_state.py tests/test_schema_version.py tests/test_schema_v10.py tests/test_query_substrate.py -v`.
- [ ] Run the gate: `python scripts/verify`.
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

**Files:**
- Modify: `src/memoria_vault/runtime/propagation.py` (add `mark_consequence` + `_target_aliases`)
- Create: `tests/test_propagation_engine.py`
- Modify: `tests/conftest.py` (`TEST_LEVELS` — register at `runtime`)

**Interfaces:**
- Consumes: `write_frontmatter_doc` / `split_frontmatter` / `read_frontmatter` (vaultio.py:160/:70/:66), `sha256_file` / `EMPTY_SHA256` (policy/audit.py), `state.set_concept_consequence` + `state.concept_consequence` (C.3), `state.set_concept_flag` (state.py:1293-1315, the shipped compat row) / `state.concept_flags` (state.py:1318), `state.file_baseline` / `state.upsert_file_baseline` (baseline-refresh idiom mirrors trusted_writer.py:596-604), `EVENT_CHECK_FIRED` (trusted_writer.py:44; the event shape mirrors `integrity._flag_descendant`, integrity.py:1194-1222, so `rebuild_trace_state` — trusted_writer.py:837-853 — keeps `_known_current_hashes` current and the next scan does not read the mark as a foreign edit), `state.catalog_source` (state.py:1603) for `_target_aliases` (12 lines mirroring `integrity._trace_aliases`, integrity.py:1368-1379 — duplicated deliberately: importing integrity from propagation would create an import cycle once integrity imports propagation in C.5). The frontmatter fields' yaml registration is NID's closed-validation task (NODES §3) — this writer never validates against the contract, it labels.
- Produces: `propagation.mark_consequence(vault: Path, concept_id: str, *, consequence: str, trigger_id: str, reason: str, append_event: Callable[[dict[str, Any]], Any]) -> dict[str, Any]` — returns `{"concept_id": str, "consequence": str, "changed": bool, "path": str}` (`path` = the rel to commit, empty for DB-only targets or no-op re-marks). File targets get frontmatter `stale: True` + `consequence: <type>`; every target gets the v18 verdict mirror + the `concept_flags` stale compat row + one `typed-consequence` journal event; re-marking with the identical consequence is a full no-op (no write, no event). `propagation._target_aliases(vault: Path, target: str) -> set[str]`.

**Steps:**

- [ ] Register the test file in `tests/conftest.py` `TEST_LEVELS`: `"test_propagation_engine.py": "runtime",`.
- [ ] Write the failing tests. Create `tests/test_propagation_engine.py`:

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

- [ ] Run to verify failure: `python -m pytest tests/test_propagation_engine.py -v` — expected: `ImportError: cannot import name 'mark_consequence'`.

- [ ] Write the minimal implementation. In `src/memoria_vault/runtime/propagation.py`, extend the imports:

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

- [ ] Run to verify pass: `python -m pytest tests/test_propagation_engine.py -v`.
- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/propagation.py tests/test_propagation_engine.py tests/conftest.py
  git commit -m "feat(propagation): consequence mark writer — frontmatter labels + v18 mirror + compat flag

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task ERP-C.6: Loudness routing — attention card only when the active project's slice is touched (executes BEFORE C.5)

**Files:**
- Modify: `src/memoria_vault/runtime/propagation.py` (add `active_project_slices` + `route_consequence_cards`)
- Modify: `tests/test_propagation_engine.py` (append)

**Interfaces:**
- Consumes: `inbox.write_finding(vault, card_type, title, finding, raised_by, agent_recommendation="issues-found", target="", citekey="", loudness="alert", evidence="", dedupe_slug="") -> Path | None` (inbox.py:75, post-Plan-21 — `dedupe_slug` makes the filename stable and returns None when the card already exists; `alert` is in `PUSH_LOUDNESS`, loudness.py:21, so the card is push-routed), `iter_markdown` / `read_frontmatter` (vaultio.py), `state.concept_edges(vault, checked_only=False)`, `inbox._slug`-compatible slugging is inbox's job (dedupe_slug is slugged internally).
- Produces:
  - `propagation.active_project_slices(vault: Path) -> dict[str, set[str]]` — the deterministic rule: one entry per `type: project` markdown file whose frontmatter `archived` is not `True`; the slice = {project rel} ∪ {normalized `thesis` target rel, if any} ∪ every concept reachable undirected over all `concept_edges` rows from those seeds.
  - `propagation.route_consequence_cards(vault: Path, marked: Mapping[str, str], *, trigger_id: str, reason: str) -> list[str]` — the loudness tier rule: marks intersecting an active project's slice ⇒ exactly ONE `flag` card per (trigger, project) at `loudness="alert"` (`dedupe_slug=f"consequence-{trigger_id}-{project_rel}"` — idempotent across re-runs), card `target` = the project rel, finding = per-consequence-type counts; marks outside every active slice ⇒ NO card (labels + journal only — quiet tier). This engine never emits `block` (reserved; flood mechanics beyond routing are O2's, spec §9). Returns vault-relative card paths for the caller's commit.

**Steps:**

- [ ] Write the failing tests. Append to `tests/test_propagation_engine.py` (extend the import block with `from memoria_vault.runtime.propagation import active_project_slices, route_consequence_cards`):

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

- [ ] Run to verify failure: `python -m pytest tests/test_propagation_engine.py::test_flood_of_marks_routes_at_most_one_card_per_project -v` — expected: `ImportError: cannot import name 'route_consequence_cards'`.

- [ ] Write the minimal implementation. In `src/memoria_vault/runtime/propagation.py`, extend imports with `from collections import Counter, deque` (Counter joins the existing deque import), `from memoria_vault.runtime.subsystems.lib.inbox import write_finding`, `from memoria_vault.runtime.vaultio import iter_markdown, read_frontmatter`, then add:

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

- [ ] Run to verify pass: `python -m pytest tests/test_propagation_engine.py -v`.
- [ ] Commit:

  ```
  git add src/memoria_vault/runtime/propagation.py tests/test_propagation_engine.py
  git commit -m "feat(propagation): loudness-routed consequence cards — alert only on active-project-slice impact

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

---

### Task ERP-C.5: Engine orchestration + trigger seams (scan, curate/insert, standing sweep, disposition)

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

- [ ] Write the failing engine test. Append to `tests/test_propagation_engine.py` (extend imports with `from memoria_vault.runtime.propagation import propagate_consequences_explicit` and `from memoria_vault.runtime.trusted_writer import append_explicit_journal_event`):

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

- [ ] Run to verify failure: `python -m pytest tests/test_propagation_engine.py::test_retraction_sweep_marks_transitive_claims_and_routes_bounded_cards -v` — expected: `ImportError: cannot import name 'propagate_consequences_explicit'`.

- [ ] Implement the engine. In `src/memoria_vault/runtime/propagation.py`, extend the trusted_writer import with `OperationContext, append_explicit_journal_event, append_journal_event, commit_explicit_writer_changes, commit_writer_changes, validate_operation_context`, then add:

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

- [ ] Run to verify the engine test passes: `python -m pytest tests/test_propagation_engine.py -v`.

- [ ] Write the failing scan-seam test. Append to `tests/test_propagation_engine.py`:

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

- [ ] Run to verify failure: `python -m pytest tests/test_propagation_engine.py::test_scan_demotion_wrappers_attach_grounding_consequences -v` — expected: `KeyError: 'consequences'`.

- [ ] Wire the scan seam. In `src/memoria_vault/runtime/integrity.py`, add the import `from memoria_vault.runtime import propagation` to the top-level import block (after line 15's `from memoria_vault.runtime import capture, state` — no cycle: propagation imports state/trusted_writer/inbox only). Then in `propagate_scan_demotion` (lines 911-925), replace the bare `return _propagate_scan_demotion(...)` with:

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

- [ ] Run to verify pass: `python -m pytest tests/test_propagation_engine.py -v`.

- [ ] Write the failing curate-seam test. Append to `tests/test_knowledge.py` (after `test_curate_note_link_records_typed_link_on_checked_note`, line 395 block; uses the file's existing `_md`, `workspace`, `curate_note_link` wrappers):

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

- [ ] Run to verify failure: `python -m pytest tests/test_knowledge.py::test_curate_note_link_fires_edge_added_propagation -v` — expected: `KeyError: 'propagation'`.

- [ ] Wire the curate seam. In `src/memoria_vault/runtime/knowledge.py` `curate_note_link`, after the `commit = commit_writer_changes(...)` call (lines 404-406) and before the return dict, add:

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

- [ ] Run to verify pass: `python -m pytest tests/test_knowledge.py -v`.

- [ ] Write the failing standing-seam test. Append to `tests/test_worker_product_jobs.py` (uses the file's existing `workspace`, `enqueue_operation`, `run_next_job`, `write_note` imports; add `from memoria_vault.runtime.vaultio import read_frontmatter` if not already imported — it is, line 28):

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

- [ ] Run to verify failure: `python -m pytest tests/test_worker_product_jobs.py::test_update_work_standing_retraction_sweeps_grounded_claims -v` — expected: `KeyError: 'propagation'`.

- [ ] Wire the standing seam. In `src/memoria_vault/runtime/worker.py`'s `update-work` branch: directly after the `memoria` dict is first built (line 944, before the `standing :=` walrus block at 946), capture the prior value:

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

- [ ] Run to verify pass: `python -m pytest tests/test_worker_product_jobs.py tests/test_propagation_engine.py tests/test_knowledge.py -v`.

- [ ] **Regenerate floor goldens** — the scan and update-work seams append `typed-consequence` journal events and write frontmatter on fixture files, and the goldens hash `.memoria/journal/*.jsonl` + `.memoria/journal-head`:

  ```
  MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest tests/test_floor_seed.py \
      tests/test_floor_sweep_operations.py tests/test_floor_sweep_reads.py \
      tests/test_floor_invariants.py tests/test_floor_coverage.py tests/test_floor_transports.py -v
  git status --porcelain tests/fixtures/floor/goldens/
  ```

  Review the drift with `git diff tests/fixtures/floor/goldens/` — only hash
  values may change; a shape change means a wiring bug.

- [ ] Run the gate: `python scripts/verify`.
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
**SPEC GAP:** the spec names ERP-B's §2 claim→work bridge but not its accessor; this section assumes `memoria_vault.runtime.subsystems.lib.edges.claim_work_edges(vault: Path) -> list[dict]` with rows shaped like `state.concept_edges` rows (`source_concept_id`, `relation_type`, `target_concept_id`, `attributes_json`) — reconcile at assembly.
**SPEC GAP:** the spec does not fix where the §4 absence-honesty threshold lives; this section registers it as `.memoria/config/edges.yaml` key `warrant_absence_threshold` (int ≥ 1; absent/malformed = disabled), following the shipped `feedback.yaml` fail-safe pattern (`runtime/feedback.py:9-27`).
**SPEC GAP:** whether reindex preserves a frontmatter link's `addressed`/`status` bit into `attributes_json` is Plan 22 G2S1.1/.2 territory; this section reads `attributes_json["addressed"]` defaulting to `True` when absent.

Repo gate: `python scripts/verify`. No new test files are created (every task extends an
existing registered file), so `tests/conftest.py` `TEST_LEVELS` (tests/conftest.py:18-121)
is untouched.

**Floor-golden manifest note:** Tasks ERP-D.1, ERP-D.5, and ERP-D.6 add journal events
(`disposition.v1` with `item_type="claim"`, `curate-note-link` events with `warrant`/`edge_id`
fields, and the new `edge-write.v1` events). After each of those tasks passes locally, run the
floor suite once and regenerate goldens if they drift:
`MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest tests/test_floor_sweep_operations.py tests/test_floor_invariants.py -v`
(refused in CI by design, tests/floor_lib.py:331-354), review with `git diff
tests/fixtures/floor/goldens`, and include the regenerated goldens in that task's commit.

---

### Task ERP-D.1: `decided-wrong` claim disposition → blast-radius report card

**Files:**
- Modify: `src/memoria_vault/runtime/integrity.py` (`resolve_attention`, lines 1127-1191; new private helper below it)
- Modify: `src/memoria_vault/runtime/worker.py` (attention operation handler, lines 813-831)
- Modify: `tests/test_feedback_instrumentation.py` (append after line 65)

**Interfaces:**
- Consumes: `operations.emit_disposition_event(vault, *, decision, item_type, item_id, context)` (`runtime/operations.py:146-164`; `item_type` is a free non-empty string per the I1 validator, `engine/empirical_events.py:148-165`, so `"claim"` needs no schema change); `DECISIONS` already contains `override` (`engine/empirical_events.py:32` — closed enum unchanged); `inbox.write_finding(vault, card_type, title, finding, raised_by, *, agent_recommendation, target, citekey, loudness, evidence) -> Path` (`runtime/subsystems/lib/inbox.py:75-113`); **ERP-C:** `consequences.derive_consequences(vault, target_id, *, trigger, context) -> dict` (see SPEC GAP); **ERP-B:** extends the same outcome→decision dict with `"confirm-tension": "accept"` — this task adds only its own row and must merge cleanly with ERP-B's edit of `integrity.py:1169`.
- Produces: `integrity.resolve_attention(vault, target_id, *, context, resolution, outcome=None, routing_class="ask", reason="", item_type="attention") -> dict` — `item_type` ∈ {"attention", "claim"}; outcome `decided-wrong` valid only for `resolution="resolved"` + `item_type="claim"`, maps to `decision="override"`, derives consequences (report, not act) and writes one `flag` card naming `cascade-rollback` as the escalation. Worker payload key `item_type` on `resolve-attention`.

**Steps:**

- [ ] Write the failing test — append to `tests/test_feedback_instrumentation.py`:

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

- [ ] Run to verify both fail:
  `python -m pytest tests/test_feedback_instrumentation.py::test_decided_wrong_claim_emits_override_and_report_card tests/test_feedback_instrumentation.py::test_decided_wrong_rejected_for_attention_item_type -v`
  Expected: first fails with `assert result["status"] == "done"` (worker job failed:
  `unsupported attention outcome for resolved: 'decided-wrong'`); second fails because the
  error message check passes but the first assertion pattern differs — confirm both fail
  before implementing (the second may already pass on the error text; if it passes as-is,
  keep it as a pin).

- [ ] Write minimal implementation in `src/memoria_vault/runtime/integrity.py`. Replace the signature and validation block at lines 1127-1148:

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

- [ ] Wire the worker payload in `src/memoria_vault/runtime/worker.py` — inside the `resolve_attention(...)` call at lines 819-830 add one argument:

```python
            item_type=str(payload.get("item_type") or "attention"),
```

- [ ] Run to verify both pass:
  `python -m pytest tests/test_feedback_instrumentation.py -v`
  (the three pre-existing parametrized `apply/reject/defer` cases must still pass — `item_type` defaults to `"attention"`).

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

- [ ] Update the pinning test first (it pins the wrong behavior). In `tests/test_worker_product_jobs.py:818-839`, the PI-authored depth-1 descendant `pi_rel` must now receive the same epistemic mark as machine-derived ones. Replace lines 820 and 834-839:

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

- [ ] Run to verify it fails:
  `python -m pytest tests/test_worker_product_jobs.py::test_observe_pi_edits_propagates_scan_side_demotion -v`
  Expected: `AssertionError` at `state.concept_check_status(vault, pi_rel) == "unchecked"` (currently `"checked"` because of the PI branch).

- [ ] Write minimal implementation — in `src/memoria_vault/runtime/integrity.py` delete lines 973-984 (the `actor = str(event.get("actor") or "")` read, the `if actor == "pi":` arm with its `_flag_descendant(check="cascade-rollback", route="ask")` call, and `needs_human.append(output_id)`), changing the `elif depth == 1:` to `if depth == 1:`. Keep `needs_human: list[str] = []` (line 961) and the return key (line 1016) so the result shape is stable. Epistemic marks are now origin-blind; `cascade_rollback` (lines 1051-1124) is not touched.

- [ ] Run to verify it passes, plus the untouched authority-gate pins:
  `python -m pytest tests/test_worker_product_jobs.py tests/test_integrity_cascade_rollback.py tests/test_worker_knowledge_cycle.py tests/test_operation_context.py -v`

- [ ] Commit:
  `git add src/memoria_vault/runtime/integrity.py tests/test_worker_product_jobs.py`
  Message: `fix(integrity): scan-demotion marks are origin-blind — remove PI descendant exemption (EDGES section 7)` ending with
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task ERP-D.3: finding hygiene — `no-support` collapse + guarded `unstated-warrant` retarget

**Files:**
- Modify: `src/memoria_vault/runtime/subsystems/lib/edges.py` (ERP-A's module; append the config loader)
- Modify: `src/memoria_vault/runtime/knowledge.py` (`_argument_gap_findings` lines 2943-2977, `_argument_next_action` lines 957-968, `analyze_project_argument` call site line 1716; new `_warrant_absence_gap` helper near `_note_edges` line 3001)
- Modify: `tests/test_project_knowledge.py` (append after line 121)

**Interfaces:**
- Consumes: **Plan 22 G2S1.2:** `state.concept_edges(vault, checked_only=False)` rows carrying `attributes_json` (`runtime/state.py:2055-2076` post-reshape); **ERP-A:** `edges.py` module exists with the converged roster, and schema v17's `relation_type` CHECK admits `warrant` so a warrant row can be seeded in tests.
- Produces: `edges.warrant_absence_threshold(vault: Path) -> int | None` (None = disabled; the default); `knowledge._argument_gap_findings(counts, relation_count, *, warrant_gap: dict[str, Any] | None = None) -> list[dict[str, Any]]`; the `supports == 0` gap row is now `kind="no-support"` (alias pair deleted); `unstated-warrant` means "grounded claim component with no warrant edge or edge-attribute", fires only when the vault-wide warrant count ≥ the configured threshold, and always carries `warrant_count` as denominator (absence-honesty guard, EDGES section 4).

**Steps:**

- [ ] Write the failing tests — append to `tests/test_project_knowledge.py`:

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
                "source_concept_id": "notes/elsewhere-license.md",
                "relation_type": "warrant",
                "target_concept_id": "notes/elsewhere-claim.md",
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

- [ ] Run to verify they fail:
  `python -m pytest tests/test_project_knowledge.py::test_no_support_gap_replaces_unstated_warrant_alias tests/test_project_knowledge.py::test_warrant_absence_finding_disabled_by_default tests/test_project_knowledge.py::test_warrant_absence_finding_fires_above_threshold_with_denominator -v`
  Expected: first fails (`"unstated-warrant" in kinds` — the alias still fires); second fails
  the same way (the alias fires with zero warrant edges); third fails with no
  `unstated-warrant` row / `KeyError: 'warrant_count'`.

- [ ] Write the config loader — append to `src/memoria_vault/runtime/subsystems/lib/edges.py` (add `import yaml` and `from pathlib import Path` to its imports if ERP-A's module does not already have them):

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

- [ ] Write the knowledge.py changes. (1) In `_argument_gap_findings` (lines 2943-2977) replace the `supports == 0` block (lines 2953-2960) and thread the guard:

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
    from memoria_vault.runtime.subsystems.lib.edges import warrant_absence_threshold

    threshold = warrant_absence_threshold(vault)
    if threshold is None or counts["supports"] == 0:
        return None
    warrant_count = 0
    component_has_warrant = False
    for row in state.concept_edges(vault, checked_only=False):
        attributes = _concept_edge_attributes(row)
        if row["relation_type"] != "warrant" and not attributes.get("warrant"):
            continue
        warrant_count += 1
        if row["source_concept_id"] in component or row["target_concept_id"] in component:
            component_has_warrant = True
    if warrant_count < threshold or component_has_warrant:
        return None
    return {"warrant_count": warrant_count}


def _concept_edge_attributes(row: dict[str, Any]) -> dict[str, Any]:
    raw = row.get("attributes_json")
    if not isinstance(raw, str) or not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}
```

  (`json` is already imported at the top of `knowledge.py`; verify, add if not.)
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

- [ ] Run to verify the three new tests pass and the existing lens pins hold:
  `python -m pytest tests/test_project_knowledge.py tests/test_gap_analysis.py -v`

- [ ] Commit:
  `git add src/memoria_vault/runtime/subsystems/lib/edges.py src/memoria_vault/runtime/knowledge.py tests/test_project_knowledge.py`
  Message: `feat(knowledge): collapse unstated-warrant alias into no-support; guarded warrant-absence finding with denominator (EDGES sections 4+8)` ending with
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task ERP-D.4: `structural_impact` rewires onto `concept_edges` + the bridge

**Files:**
- Modify: `src/memoria_vault/runtime/subsystems/processing/project/structural_impact_graph.py` (add `substrate_edges`; delete `build_edges`/`build_descriptive_edges`, lines 105-133)
- Modify: `src/memoria_vault/runtime/subsystems/processing/project/structural_impact.py` (imports lines 13-29; `analyze_survey` edge read line 79; `analyze` edge read line 262; `gap_taxonomy` non-note guard lines 166-167)
- Modify: `tests/test_project_structural_impact.py` (fixtures lines 10-90 and the edge seeding in every test)

**Interfaces:**
- Consumes: **Plan 22 G2S1.1/.2:** `state.replace_concept_edges(vault, rows)` (upsert-and-prune sparing tension rows) and edge rows with `edge_id` + `attributes_json` via `state.concept_edges(vault, checked_only=False)`; **ERP-B:** `edges.claim_work_edges(vault) -> list[dict]` (see SPEC GAP; claim→work rows whose targets are `catalog/sources/*` virtual paths). Roster convergence of `RELATIONS` (`structural_impact_graph.py:14`) is **ERP-A's** — untouched here.
- Produces: `structural_impact_graph.substrate_edges(vault: Path, notes: dict[str, Note], resolver: dict[str, str]) -> list[Edge]` — the only edge source for structural impact (no frontmatter text parsing); `Edge.addressed` from `attributes_json["addressed"]` defaulting `True`. `impact.analyze` / `impact.run` signatures unchanged.

**Steps:**

- [ ] Update the test fixtures to seed the substrate. In `tests/test_project_structural_impact.py` add after the imports (line 8):

```python
from memoria_vault.runtime import state

_EDGE_ROWS: dict[str, list[dict]] = {}


def link_row(vault: Path, source: str, relation: str, target: str):
    rows = _EDGE_ROWS.setdefault(str(vault), [])
    rows.append(
        {
            "source_concept_id": f"notes/{source}.md",
            "relation_type": relation,
            "target_concept_id": f"notes/{target}.md",
            "check_status": "checked",
            "source_path": f"notes/{source}.md",
        }
    )
    state.replace_concept_edges(vault, rows)
```

  and append `link_row(vault, name, relation, target)` as the last line of both the `claim()` helper (after line 63) and the `gap()` helper (after line 80). Every existing test seeds edges only through these two helpers, so no per-test edits are needed; the frontmatter `links:` blocks stay (they remain the PI-authored source of the substrate fill, and `find_thesis`/`normalize_target` still read frontmatter).

- [ ] Add the failing rewire test — append to `tests/test_project_structural_impact.py`:

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
            "source_concept_id": "notes/a.md",
            "relation_type": "supports",
            "target_concept_id": "notes/ghost.md",
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

- [ ] Run to verify failure:
  `python -m pytest tests/test_project_structural_impact.py::test_structural_impact_reads_substrate_not_file_text -v`
  Expected: `AssertionError` on `relation_count == 5` (text path sees 4 after the corruption).

- [ ] Write minimal implementation. (1) In `structural_impact_graph.py` replace `build_edges`/`build_descriptive_edges` (lines 105-133) with:

```python
def substrate_edges(
    vault: Path, notes: dict[str, Note], resolver: dict[str, str]
) -> list[Edge]:
    """Read edges from the concept_edges substrate plus the claim→work bridge."""
    import json

    from memoria_vault.runtime import state
    from memoria_vault.runtime.subsystems.lib.edges import claim_work_edges

    edges: list[Edge] = []
    for row in state.concept_edges(vault, checked_only=False) + claim_work_edges(vault):
        source = resolver.get(_edge_key(str(row["source_concept_id"])))
        target_raw = _edge_key(str(row["target_concept_id"]))
        target = resolver.get(target_raw)
        if target is None and target_raw.startswith("catalog/sources/"):
            target = target_raw  # virtual work node from the bridge
        if not source or not target or source == target:
            continue
        addressed = True
        raw = row.get("attributes_json")
        if isinstance(raw, str) and raw.strip():
            try:
                attributes = json.loads(raw)
            except json.JSONDecodeError:
                attributes = {}
            if isinstance(attributes, dict) and "addressed" in attributes:
                addressed = bool(attributes["addressed"])
        edges.append(
            Edge(
                source=source,
                target=target,
                relation=str(row["relation_type"]),
                addressed=addressed,
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

- [ ] Run the whole file to verify all pass:
  `python -m pytest tests/test_project_structural_impact.py -v`
  (`test_normalize_target_extracts_dict_wikilink_and_status` still passes — `normalize_target` stays for thesis/link resolution.)

- [ ] Commit:
  `git add src/memoria_vault/runtime/subsystems/processing/project/structural_impact_graph.py src/memoria_vault/runtime/subsystems/processing/project/structural_impact.py tests/test_project_structural_impact.py`
  Message: `refactor(structural-impact): read concept_edges substrate + claim→work bridge instead of file text (EDGES section 8)` ending with
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task ERP-D.5: `curate-note-link` warrant parameter → `attributes_json.warrant`

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py` (`curate_note_link`, lines 346-414)
- Modify: `src/memoria_vault/runtime/worker.py` (`curate-note-link` handler, lines 471-497)
- Modify: `tests/test_knowledge.py` (append after line 428)

**Interfaces:**
- Consumes: **Plan 22 G2S1.2:** `state.concept_edge_id(source, relation, target) -> str` (sha256 triple `[:24]` — deterministic, so pre-reindex addressing is sound); **ERP-B:** `state.insert_concept_edge(vault, *, source, relation_type, target, attributes=None, context) -> dict` with upsert mode keyed on the deterministic `edge_id` (result dict includes `"edge_id"`).
- Produces: `knowledge.curate_note_link(vault, source_note_path, link_type, target_path, *, context, reason="", warrant="") -> dict` — when `warrant` is non-blank the same trusted-writer transaction upserts `attributes_json.warrant` on the deterministic edge and the result/journal event carry `edge_id` and `warrant`; worker payload key `warrant` on `curate-note-link`. (EDGES section 4 write path: warrant *text* on a grounding edge — the lightweight Option-B form; the `warrant` *relation* itself is a plain `link_type` after ERP-A activates the roster.)

**Steps:**

- [ ] Write the failing round-trip test — append to `tests/test_knowledge.py`:

```python
def test_curate_note_link_warrant_text_round_trips_to_edge_attribute(
    tmp_path: Path,
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
        vault,
        "source",
        "supports",
        "target",
        warrant="RCTs in this population license the inference",
        actor="pi",
        reason="PI linked claims",
        machine="curator",
    )

    edge_id = state.concept_edge_id("notes/source.md", "supports", "notes/target.md")
    assert result["edge_id"] == edge_id
    rows = [
        row
        for row in state.concept_edges(vault, checked_only=False)
        if row["source_concept_id"] == "notes/source.md"
        and row["target_concept_id"] == "notes/target.md"
    ]
    assert len(rows) == 1
    import json as _json

    attributes = _json.loads(rows[0]["attributes_json"])
    assert attributes["warrant"] == "RCTs in this population license the inference"
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
    rows = [
        row
        for row in state.concept_edges(vault, checked_only=False)
        if row["source_concept_id"] == "notes/source.md"
        and row["target_concept_id"] == "notes/target.md"
    ]
    assert len(rows) == 1
    assert _json.loads(rows[0]["attributes_json"])["warrant"] == "Updated license"
```

- [ ] Run to verify it fails:
  `python -m pytest tests/test_knowledge.py::test_curate_note_link_warrant_text_round_trips_to_edge_attribute -v`
  Expected: `TypeError: curate_note_link() got an unexpected keyword argument 'warrant'`.

- [ ] Write minimal implementation in `knowledge.py`. Add `warrant: str = ""` to the signature (line 353, after `reason`), normalize it beside `link_type` (line 360): `warrant = warrant.strip()`. After the `if changed:` block (line 389) and before the journal event (line 391) add:

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

- [ ] Wire the worker payload — in `worker.py` add to the `curate_note_link(...)` call (lines 483-490):

```python
            warrant=str(payload.get("warrant") or ""),
```

- [ ] Run to verify it passes, plus the existing link pin:
  `python -m pytest tests/test_knowledge.py::test_curate_note_link_warrant_text_round_trips_to_edge_attribute tests/test_knowledge.py::test_curate_note_link_records_typed_link_on_checked_note -v`

- [ ] Regenerate floor goldens if drifted (manifest note at top) and commit:
  `git add src/memoria_vault/runtime/knowledge.py src/memoria_vault/runtime/worker.py tests/test_knowledge.py tests/fixtures/floor/goldens`
  Message: `feat(knowledge): curate-note-link warrant text upserts attributes_json.warrant on the deterministic edge (EDGES section 4)` ending with
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task ERP-D.6: I1 per-relation-type edge-write counters

**Files:**
- Modify: `src/memoria_vault/engine/empirical_events.py` (append after `validate_read_event`, line 185; new constants beside `READ_EVENT_SCHEMA`, line 14)
- Modify: `src/memoria_vault/runtime/operations.py` (append after `emit_disposition_event`, line 164)
- Modify: `src/memoria_vault/runtime/knowledge.py` (`curate_note_link`, emission after the journal event)
- Modify: `tests/test_empirical_events.py` (append after line 85), `tests/test_knowledge.py` (append)

**Interfaces:**
- Consumes: the I1 skeleton server-side event shape (`validate_disposition_event` / `validate_read_event`, `engine/empirical_events.py:148-184`: closed field set, `schema` stamped by the emitter, journaled via `append_journal_event`); **ERP-A:** `edges.EDGE_RELATIONS` (the seven-relation roster) as the `relation_type` enum; Task ERP-D.5's `warrant` param (emission point).
- Produces: `empirical_events.EDGE_WRITE_EVENT_SCHEMA = "edge-write.v1"`; `empirical_events.validate_edge_write_event(payload: dict) -> dict` (required: `relation_type` ∈ `EDGE_RELATIONS`, `write_path` ∈ {"curate-note-link", "insert-concept-edge"}); `operations.emit_edge_write_event(vault, *, relation_type: str, write_path: str, context) -> dict`; `operations.edge_write_counts(vault) -> dict[str, int]` (the beta.2 touch-budget gate's input, EDGES section 4 instrumentation line). **Constraint on ERP-B:** its `confirm-tension` / `insert_concept_edge` write path must call `emit_edge_write_event(..., write_path="insert-concept-edge")` — record this in the assembled plan if ERP-B's tasks are already frozen.

**Steps:**

- [ ] Write the failing validator tests — append to `tests/test_empirical_events.py`:

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

- [ ] Run to verify they fail:
  `python -m pytest tests/test_empirical_events.py::test_edge_write_event_accepts_roster_relation tests/test_empirical_events.py::test_edge_write_event_rejects_off_roster_relation_and_unknown_path tests/test_knowledge.py::test_curate_note_link_counts_edge_writes_per_relation_type -v`
  Expected: `ImportError: cannot import name 'validate_edge_write_event'` / `cannot import name 'edge_write_counts'`.

- [ ] Write minimal implementation. (1) `engine/empirical_events.py` — beside line 14 add:

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
    """Append one per-relation-type edge-write counter event (I1 touch-budget input)."""
    from memoria_vault.engine.empirical_events import (
        EDGE_WRITE_EVENT_SCHEMA,
        validate_edge_write_event,
    )

    event = validate_edge_write_event(
        {"relation_type": relation_type, "write_path": write_path}
    )
    journal_event = {"event": "edge-write", "schema": EDGE_WRITE_EVENT_SCHEMA, **event}
    return append_journal_event(vault, journal_event, context=context)


def edge_write_counts(vault: Path) -> dict[str, int]:
    """Return journal edge-write counts per relation type (beta.2 touch-budget gate input)."""
    with state.connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT json_extract(payload_json, '$.relation_type') AS relation_type,
                   COUNT(*) AS n
            FROM event_log
            WHERE json_extract(payload_json, '$.schema') = 'edge-write.v1'
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

- [ ] Run to verify all pass:
  `python -m pytest tests/test_empirical_events.py tests/test_knowledge.py -v`

- [ ] Regenerate floor goldens if drifted (manifest note at top), run the full gate once for the section (`python scripts/verify`), and commit:
  `git add src/memoria_vault/engine/empirical_events.py src/memoria_vault/runtime/operations.py src/memoria_vault/runtime/knowledge.py tests/test_empirical_events.py tests/test_knowledge.py tests/fixtures/floor/goldens`
  Message: `feat(instrumentation): edge-write.v1 per-relation-type counters on curate/insert paths (EDGES section 4 instrumentation)` ending with
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`
