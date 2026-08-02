# `src/` and `tests/` structure — Audit and staged migration plan

Date: 2026-08-02. Status: **audit complete, nothing executed**. Scope was
re-decided mid-session against the evidence; see §3.

Method: static analysis of the whole package (AST import graph over 90
modules, fan-in/fan-out, `__init__.py` coverage), twelve parallel agents
(one per oversized module, plus taxonomy, blast radius, tests mapping, and
two adversarial critiques), then direct verification of every load-bearing
claim against the working tree at `c03d9556`. Both critiques returned
**unsound** against the first taxonomy; this document records what survived
that pass, not what was originally proposed.

---

## 1. Verdict

**The tree is not disorganised in the way its shape suggests.** It is 45
flat modules one level under `runtime/` — flat, but findable and, apart from
the items in §2, uncontested. The genuine defects are four, and they are
specific. A wholesale repackaging is not what the evidence supports.

The dominant finding is not a structural defect at all. It is that **the one
gate cannot see packaging failures**, which is why the structural defects
survived (§2.0).

---

## 2. The defects, in priority order

### 2.0 Packaging failures are invisible to `scripts/verify` — the meta-defect

`scripts/verify` never builds an artifact (no `build`, `wheel`, or `sdist`
in the `GATES` roster at `scripts/verify:48`). `pyproject.toml:57-62` puts
`src` on `pythonpath` so pytest imports from the source tree, and
`.github/workflows/verify.yml` installs with `pip install -e`. Nothing in
the repo ever exercises a built wheel.

Consequences, all of which ship green today:

- A dropped namespace package (§2.1).
- A stale `runtime/*.sql` package-data glob (`pyproject.toml:30`).
- A dotted package-data key pointing at a moved directory.
- `files("memoria_vault.runtime").joinpath("schema.sql")`
  (`runtime/state.py:514`) resolving in-tree but not in the wheel.

This is the named, expensive, recurring failure AGENTS.md asks any addition
to justify itself against. It is also the reason §2.1 went unnoticed
indefinitely. **It must be fixed before anything moves**, or every
subsequent step is unverified.

### 2.1 Seven `subsystems/` directories have no `__init__.py`

Every directory under `runtime/subsystems/` is an implicit namespace
package, while every sibling (`engine/`, `runtime/`, `policy/`, `code/`,
`product/`) has an `__init__.py`. They ship only because setuptools'
pyproject `[tool.setuptools.packages.find]` defaults `namespaces = true`.
Switching to an explicit package list, setting `namespaces = false`, or
moving these directories drops them from the wheel silently.

### 2.2 `integrity` names two unrelated concepts

`runtime/integrity.py` (2,282 LOC) coexists with
`runtime/subsystems/integrity/{linter,retraction}/`. Verified: they share
**zero code in either direction** and touch disjoint data. `integrity.py`
owns journal-recorded checks against a claim's grounds and cascade rollback
through the derivation DAG; the linter walks the file tree, is zero-LLM and
report-only, and every module ships a `main()`. One word, two concepts.

### 2.3 One true module-level layer inversion

`runtime/subsystems/telemetry/eval/eval_dispatch.py:29` imports
`memoria_vault.engine.api` at module level (column 0,
`from memoria_vault.engine import api as engine_api`) and calls
`run_operation`, while `runtime/worker.py:866` imports `eval_dispatch` —
deferred, inside the `eval-run` branch. A surface-layer module is a
dependency of a domain module. Verified by AST over all 90 modules: this is
the only module-level instance. (`runtime/decision_rules.py:313` imports
`engine.dashboard.assemble_dashboard` but defers it.)

### 2.4 Four modules exceed what fits in one context

`runtime/state.py` 5,202 LOC / 203 symbols · `runtime/knowledge.py` 4,500 ·
`cli.py` 4,517 · `runtime/integrity.py` 2,282. Also `runtime/worker.py`
1,710, `engine/api.py` 1,609, `runtime/backup.py` 1,510. All seven have
defensible internal seams (§5); none was rated high-risk.

---

## 3. Scope decisions taken in session

| Decision | Ruling |
| --- | --- |
| Original scope | Full repackaging + mega-file splits + `tests/` mirroring `src/` |
| Re-decided after audit | **Write the spec, execute nothing** |
| Shipped githook break, if `precommit_check` is ever renamed | **Accept the break, record it** — CHANGELOG entry plus a `doctor` message. Not a silent absorption, not a shim. |

Two premises from early in the session were wrong and are retracted here so
they do not resurface:

- **Churn analysis is meaningless in this repo.** All 1,345 commits are plan
  implementations, not maintenance. `backup.py`'s 5 commits mean it was
  finished early, not that it is stable. No prioritisation may be derived
  from git history.
- **The `TEST_LEVELS` conftest dict no longer exists.** It was deleted in
  `cc55c40f` during this session. `tests/conftest.py` is 75 lines; all 149
  test files carry their own `pytestmark`; `tests/test_testing_levels.py`
  already enforces exactly one registered level per file. Any plan premised
  on deleting that dict describes work already done.

---

## 4. What constrains any move

### 4.1 `runtime/subsystems/…` is a published interface, not an internal path

**23 documented `python -m` call sites across 8 modules.** These modules are
terminal in the import graph, so a rename looks free from the import graph
and is not. There is no link checker; a stale doc is the only signal.

| Surface | Sites |
| --- | --- |
| `…integrity.linter.detectors` | 4 docs + `e2e_smoke.py:312` + `install-test-vault-local-llm.sh:149` |
| `…telemetry.eval.eval_score` | 5 docs |
| `…integrity.retraction.retraction` | 2 docs |
| `…processing.project.structural_impact` | 2 docs |
| `runtime.diagnostics` | 2 docs |
| `…integrity.linter.hub_handoff` / `.session_summary` | 1 doc each |
| `…lib.worklists` | 1 doc |

### 4.2 The shipped git hook — a product decision, ruled in §3

`product/workspace_seed/.githooks/pre-commit:19` pins
`python -m memoria_vault.runtime.subsystems.integrity.linter.precommit_check`
and is **copied into every user vault at `memoria init`**. `.githooks` is in
`SEED_TREES` (`cli.py:47`), so `memoria doctor --repair` reseeds it — but an
installed vault's commit gate is broken until the PI runs repair.

### 4.3 `schema.sql` is pinned in four places that must move atomically

`pyproject.toml:30` (`memoria_vault = ["runtime/*.sql"]`) ·
`runtime/state.py:514` (`files("memoria_vault.runtime")`) ·
`tests/test_package_spine.py:31` (exact-list assertion) · `:76`
(`files()` call). Two further tests read `state.py` **as text**
(`test_package_spine.py:77,85`, `test_schema_version.py:33`) and raise
`FileNotFoundError` the moment it stops being a file at that path.

### 4.4 `cli.py` binds three separate mechanisms

1. `[project.scripts] memoria = "memoria_vault.cli:main"` — baked into every
   installed venv's entry-point metadata.
2. `python -m memoria_vault.cli` at `runtime/rendezvous.py:422` (spawns the
   on-demand server), `e2e_smoke.py:330` (runs in the gate),
   `install-test-vault-local-llm.sh:149`.
3. Six symbols imported from `memoria_vault.cli` repo-wide, including
   `_build_parser` from `scripts/checks/doc_claims_gate.py:68`.

If `cli.py` ever becomes a package it must be `cli/__init__.py` — **not**
`cli/cli.py` — plus a new `cli/__main__.py`, or all three break.

### 4.5 The policy facade is an asserted interface

`test_package_spine.py:91-99` spawns a subprocess asserting
`from memoria_vault.runtime.policy import normalize_path` works with only
`PYTHONPATH=src`. Nine live import sites total (two in `src`:
`policy/hook.py:344,408`). Per AGENTS.md's trust order (schema → tests →
code → docs), the facade is a contract, not an accident.

### 4.6 Tests are coupled to their own depth

- **`tests/test_testing_levels.py:45,53` use non-recursive `glob`.** Move any
  test into a subdirectory and the level gate iterates zero paths and passes
  **vacuously** — silently losing the only mechanism enforcing that each test
  declares a level. This is the same undetectable-half-migration failure mode
  that produced `subsystems/`.
- **18 files compute the repo root as `Path(__file__).resolve().parent.parent`**,
  including `tests/floor_lib.py:19` — after a one-level move its goldens
  resolve to `tests/tests/fixtures/floor/goldens`.
- **97 dotted-string monkeypatch literals across 31 files** fail *late*, not
  at collection. `test_onboarding_steps.py:167` does
  `monkeypatch.setitem(sys.modules, "memoria_vault.runtime.telemetry", None)`
  — after a move this poisons a key nothing imports and the test passes while
  exercising nothing.
- **128 of 155 test files** import `memoria_vault.runtime.*` directly.

### 4.7 Other path-coupled gates

`scripts/verify:75-92` (compileall hard-codes `src/memoria_vault`) ·
`checked_terminology_gate.py:11` · `doc_claims_gate.py:67-68,82` ·
`plugin_provenance_doctor.py:12-13,26` · `schema_doc_drift.py:169` ·
`removed_surface_gate.py` (a missing search root is a hard failure) ·
`.pre-commit-config.yaml:38,42` (ruff `files:` regex — lint silently stops
covering anything moved outside `src/memoria_vault/`) ·
`docs/reference/_sources.yml` (14 `owner:` keys pointing at src paths) ·
`test_edges.py:560-571` (keyed on the **file name** `edges.py`).

`design-history/` and `docs/superpowers/` cite src paths but sit outside
every gate's search root — they go stale, they break nothing.

---

## 5. Verified module seams

Every seam below was independently re-verified by an adversarial reviewer
against the real code. All are **medium** risk; none is high.

The general finding that makes these cheap: **turning a module into a
package whose `__init__.py` re-exports the moved symbols leaves every read
call site unedited.** `grep "from memoria_vault.runtime.state import"`
returns zero hits repo-wide — all 107 importers use
`from memoria_vault.runtime import state` plus attribute access. The real
cost is monkeypatch retargeting, not imports.

### 5.1 `runtime/state.py` → highest value, lowest risk

Two blocks reference **zero module-level names defined outside their own
ranges**:

| Extract | LOC | Content |
| --- | --- | --- |
| `state/markdown.py` | 1,215 | Pure Markdown masking + evidence-marker extraction. Zero SQLite. |
| `state/workspace_lock.py` | 385 | Cross-process workspace lock, including the Windows reparse-safe opener. |

**31% of the file leaves with no query-layer risk and no read-call-site
edits.** This is the single highest-value change identified, and it is worth
doing *even if everything else here is abandoned*.

Caution: budget ~8-10 monkeypatch retargets, and verify each retargeted
assertion still **fails** when the behaviour it guards is broken —
`state.safe_filename` (`test_runtime_state.py:596`) and `state.read_event_log`
(`test_attention_lifecycle.py:476`) would otherwise pass vacuously.

Remaining seams: `db.py` (70), `requests.py` (331), `journal.py` (284),
`concepts.py` (394), `outputs.py` (692), `catalog.py` (510). `db.py` is not
optional — without it, submodules would import `connect`/`_json` from the
facade that imports them.

### 5.2 `runtime/knowledge.py`

No mutable module-level state; every module-level binding is an immutable
constant. Acyclic as proposed: `concept_refs` ← `{note_curation,
discovery_channel, project_argument}` ← `project_slice` ← `project_draft` ←
`project_export` ← `gap_analysis`. Eight modules, ~150 symbols each assigned
exactly once. The obstacle is ~110 private helpers shared across concerns
and tests bound to internals — not data flow.

### 5.3 `cli.py`

Today: `main()` → `_build_parser()` creates one parser, registers ~14
commands inline, delegates the rest to 12 group registrars. Proposed:
`cli/__init__.py` (entry point + registry, ~175) · `_common.py` (250) ·
`read.py` (300) · `catalog.py` (600) · `project.py` (650) · `requests.py`
(570) · `workspace_setup.py` (900) · `maintenance.py` (730). Subject to §4.4.

### 5.4 `runtime/worker.py`

A 924-line `if/elif` chain over 40 operation ids. Every branch already takes
`(vault, payload, context)` and returns a dict — **the handler interface
exists implicitly; the split names it rather than inventing it.** Keep
`worker.py` as a ~110 LOC facade: the single biggest blast-radius reduction
available.

### 5.5 `runtime/integrity.py`

Direction ruled: the top-level module **absorbs** `subsystems/integrity/`,
not the reverse — a filing decision, not a code one. Eight modules, with
`integrity/__init__.py` as a compatibility facade.

### 5.6 `runtime/backup.py`

Verdict on the framing question: backup and restore are **not** two
concerns, and the correct first cut is **horizontal, not vertical**.
Publication literally depends on the restore staging pipeline —
`_is_restorable_backup` (1396-1404) performs a full trial restore via
`_stage_restore_source`. A naive backup-vs-restore split fails.

### 5.7 `engine/api.py`

**Must survive as a module, not become a package of equals.**
`runtime/mcp_transport.py:102` does
`getattr(engine_api, engine_name)(workspace, **kwargs)`, dispatching on
`SURFACE_ACTIONS[*]["engine"]` — every registry `engine` string pins the flat
namespace.

---

## 6. Candidate target taxonomy — recorded, not endorsed

A full 18-package taxonomy was produced and is preserved in the session
record. It deletes `runtime/` outright (the name "contrasts with nothing").
It is **not carried into the plan below**, for reasons both critiques
raised independently:

- No expensive, recurring failure is named for it. The other ~40 flat
  modules under `runtime/` are flat, findable, and have caused no incident.
- Two of its packages are grab-bags **by its own stated standard**:
  `vaultfile/` ("stdlib only" is a dependency-weight description, not a
  subject) and `assessment/` (assembled from a negative cross-cutting
  property — the exact reasoning it rejects elsewhere for `projections/`).
- Its accompanying **layer rule is a checker that catches one edge**
  (§2.3) and is then permanently green, bypassable by moving an import into
  a function body — an idiom the repo already uses for 43 cross-package
  edges. AGENTS.md ranks deletion > mechanism > rule > checker.
- Three within-layer package cycles survive it (`trust ↔ attention`,
  `trust ↔ operations`, `catalog ↔ grounding`). Harmless while every
  `__init__.py` stays docstring-only; hard `ImportError`s the day any grows
  a re-export.
- `product/` was omitted from it entirely — the subtree with the most
  external path coupling.

If it is ever revisited, it needs a named failure with an incident behind
it, and `product/` explicitly ruled out of scope.

---

## 7. Staged plan, if execution is ever authorised

Each stage is independently mergeable and green under `python scripts/verify`
on its own. **No stage may leave a module reachable at two dotted paths** —
that coexistence is precisely what produced `subsystems/`.

| # | Stage | Moves? | Why it is ordered here |
| --- | --- | --- | --- |
| 1 | **Wheel/sdist build gate.** Add to `scripts/verify` GATES; assert every package and `schema.sql` are present in the artifact. Mirror the gate string in `test_verify_script.py`. | No | Nothing later is verified without it (§2.0). |
| 2 | **Close the namespace hole.** `__init__.py` in all 7 `subsystems/` directories, plus a test asserting every directory containing a `.py` has one. | No | Stage 1 now proves they ship explicitly. |
| 3 | **Fix the inversion** (§2.3). Parameterise `eval_dispatch`'s run seam. One file plus its test. | No | Independently valuable and revertible. |
| 4 | **Test-suite position independence.** Centralise the 18 `__file__` root constants; `glob`→`rglob` + a non-zero-count assert in `test_testing_levels.py:45,53`; add a collection-time guard resolving every `^memoria_vault\.` string literal via `find_spec`. | No | Converts 97 silent late failures into collection errors. Prerequisite for *any* later move. |
| 5 | **`state.py` extractions** — `markdown.py` + `workspace_lock.py` (§5.1). | Internal | Highest value, lowest risk, independent of taxonomy. |
| 6 | **Resolve the `integrity` collision** (§2.2). Carries in the same commit: the module moves, 52 `tests/` references, `e2e_smoke.py:308-316`, `test_env_harness.py`, `install-test-vault-local-llm.sh:148-150`, all 23 `-m` doc call sites, the CHANGELOG entry and `doctor` message for §4.2. **No shim at the old path.** | Yes | The only naming problem with a demonstrated cost. |
| 7+ | Remaining seams (§5.2-5.7), one module per PR, largest blast radius last. | Internal | Only after 1-5 land. |

**Never staged together:** a package move and a mega-file split. The split
retargets ~10 monkeypatch sites and re-exports ~17 de-facto-public underscore
symbols; inside a rename, every one of those edits is indistinguishable from
a path rewrite in review.

**Not recommended at all:** the `tests/` mirror. It de-fangs the gate in
§4.6, deletes nothing, and the mapping's own confidence field admits a fifth
of the files have no clear home. `tests/` being flat is not a named,
expensive, recurring failure. If it is ever revisited, stage 4 must land
first and the mapping must be regenerated from the post-move tree.

---

## 8. Open questions

1. Is stage 1 (the build gate) authorised on its own? It is a strict
   improvement independent of every structural question here, and it is the
   only item that makes the others verifiable.
2. Is stage 5 (`state.py` extraction, 1,600 LOC, zero call-site edits)
   authorised on its own? It does not depend on any taxonomy decision.
3. Does the `integrity` collision (§2.2) justify stage 6's blast radius —
   23 doc call sites plus an accepted break to installed vaults' commit
   gates — or is the name collision tolerable?
