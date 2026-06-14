# Naming & Diátaxis audit — alpha.3

**Companion to:** [open-issues-research.md](open-issues-research.md) (Issue 2 = naming scheme; Issue 3 = Diátaxis)
**Date:** 2026-06-14
**Scope:** (1) every folder/file/class/function/variable/test/skill name across `src/`, `scripts/`, `tests/`, `.claude/`; (2) every `docs/reference/` and `docs/explanation/` page for Diátaxis **work-vs-study** register.
**Method:** five parallel auditors, full enumeration (no sampling); every path verified live.

**Headline:** the codebase is already in good shape — no `utils.py`/`manager.py`/`Helper`/`do()`/`handle()`/`process()`, consistent PEP 8 casing, strong agent-skill and JS-script naming, and **0 wholly-misfiled doc pages**. The findings are (a) a handful of outright defects, (b) the cross-cutting `engines → Operations` rename surface, (c) generic shape-names and one cross-language casing inconsistency, and (d) Diátaxis register bleed — almost always a stray reference table inside an explanation page, or stray rationale inside a reference page (the tables/contracts themselves are solid).

---

## Part 1 — Naming

### 1.1 Outright defects (fix regardless of any rename)

These are not judgment calls — they're wrong today.

| # | Path | Defect | Fix |
|---|---|---|---|
| D-1 | `src/.memoria/engines/sweeps/reconcile.py:2` | Module docstring still says `"""sweeps.py …"""` (file was renamed from `sweeps.py`) | Update docstring to `reconcile.py` |
| D-2 | `tests/_util.py` (`TestHarness` class) | pytest **collects any `Test*` class** → emits a `PytestCollectionWarning` (the helper has `__init__`) | Rename `TestHarness` → `CheckHarness`/`SelfTestHarness` |
| D-3 | `scripts/refresh-retraction-watch.sh` | Breaks the `<job>-cron.sh` → `memoria-<job>.sh` scheme (no `-cron` suffix); installs as `memoria-refresh-rw.sh` (opaque `rw`) | `retraction-refresh-cron.sh` → `memoria-retraction-refresh.sh` |
| D-4 | `_papers/*.md:Zone.Identifier` | Windows alternate-data-stream cruft files tracked in the tree | gitignore + clean |

### 1.2 The `engines → Operations` rename surface (cross-cutting)

Adopting **Operations → Processing · Integrity · Cleanup · Telemetry** (companion Issue 2) is a structural rename. It must move as one atomic change because the path is hardcoded in several places:

| Path | What hardcodes `engines/` |
|---|---|
| `src/.memoria/engines/` (+ `ingest/ lib/ linter/ sweeps/`) | the layer itself → `src/.memoria/operations/{processing,integrity,cleanup,telemetry}/` |
| `tests/conftest.py:9-12` | `sys.path` entries for `engines/{lib,ingest,sweeps,linter}` |
| `scripts/test.sh:51,54,59` | self-test runner paths |
| `scripts/e2e-smoke.sh:33-98` | ~7 hardcoded `engines/...` paths |
| `scripts/install.sh:329,350,877` | installer copies `engines/`; golden + pre-commit paths |
| `tests/test_precommit_schema.py:48` | `engines/linter/pre-commit` |
| docs | `docs/explanation/engines/` (dir), `reference/system-actions.md`, ADR-46/48/49, ~6 how-to pages |

**Two exclusions for any find/replace** (false positives):

- `memoria-engineer` — an **agent profile/persona**, unrelated to the deterministic layer. Do not rename.
- qmd "search engine" (`install.sh:835`) — third-party, not the Operations layer.
- `PolicyEngine` (class in `policy_mcp.py`) — decide separately whether the *class* name tracks the rename; not required.

**Category misplacements to fix during the rename** (the current `sweeps/` folder spans three of the four categories — the single biggest structural inconsistency):

| Current | Actually | Move to |
|---|---|---|
| `engines/sweeps/reconcile.py`, `archive_inbox.py` | Cleanup | `operations/cleanup/` |
| `engines/sweeps/retraction.py` | Integrity | `operations/integrity/` |
| `engines/sweeps/eval_dispatch.py`, `eval_score.py` | Telemetry | `operations/telemetry/eval/` |
| `mcp/cluster_mcp.py` (holds the Cluster *engine*, no `engines/cluster/`) | Processing | extract logic → `operations/processing/cluster/`; keep a thin `cluster_mcp.py` façade (mirror `ingest_mcp.py`) |
| `mcp/board_export.py`, `mcp/metrics_aggregate.py` (not MCP servers) | Telemetry | `operations/telemetry/` |
| Search | Processing | no dir or file exists — document the gap / create `operations/processing/search/` when implemented |

### 1.3 Generic / shape names (the flagged anti-pattern)

| Path | Issue | Suggested |
|---|---|---|
| `engines/ingest/pipeline.py` | "pipeline" = a *shape*, not a responsibility; it's the ingest orchestrator | `runner.py` (or `ingest.py`/`catalog.py` per content) |
| `engines/lib/` | generic folder; holds the card writer + schema loader | retire; rename `inbox.py`→`inbox_cards.py`, `schema.py`→`type_schemas.py` and place them with their owners |
| `engines/linter/golden.py` | "golden" is an adjective, not a responsibility | `golden_restore.py` |
| `engines/lib/schema.py` (`import schema`) | shadows the common 3rd-party `schema` package | `type_schemas.py` |
| `mcp/_shared.py` | borderline ("shared" = a relationship); small + scoped, low priority | `mcp_io.py` (optional) |
| `scripts/test.sh` | "test of what?" — it's the L1 self-test runner | `run-selftests.sh` |
| `scripts/harper-advisory.sh` | noun-only (no verb) | `run-harper-advisory.sh` |

**Already clean:** no `utils/manager/helpers/common/misc` modules; verbs are specific (`resolve`, `merge`, `assemble`, `decide`, `dispatch`); classes are clear (`Finding`, `LanePolicy`, `Decision`). Vague-locals are minor (`m`/`r`/`d` in the merge fetchers; `agr`→`agreement`; `rp`→`relpath`).

### 1.4 Cross-language casing inconsistency (the one real cross-cutting defect)

`scripts/*.py` are **kebab-case** (`docs-doctor.py`, `gen-adr-index.py`, `status-doctor.py`, `check-test-refs.py`) — non-importable and against PEP 8, which is *why* `tests/_util.py` carries a `load_script()` hack. Everything else is correct (Python snake_case; shell + docs + JS kebab-case).

**Fix:** rename the four to snake_case and retire `load_script()`. **Caution:** `docs-doctor.py` is referenced by pre-commit, CI (`lint.yml`), `test.sh`, and the docs-review playbook — sweep all references together, don't rename piecemeal.

### 1.5 Obsidian-side & skills

| Area | Finding | Suggested |
|---|---|---|
| QuickAdd commands (`.obsidian/plugins/quickadd/data.json`) | `workspace Desk/Library/Studio` break the verb-first lowercase pattern; articles inconsistent ("a task"/"the corpus"/none) | `open Desk workspace`; normalize — drop all articles (`delegate task`, `link claim`, `catalog source`) |
| Folder pluralization | `notes/source/`, `notes/index/` singular vs `notes/claims/`, `catalog/*` plural | `notes/sources/`, `notes/indexes/` |
| Co-PI skills | `explain-the-system`, `explore-branch-framings`, `delegate-route-task` break the `verb-noun(-noun)` no-article pattern the other 22 skills follow | `explain-system`, `explore-framings`, `route-task` (or `delegate-task`, matching `delegate-task.js`) |
| Non-developer jargon | `fleet-health` (worth changing), `board-state`/`board/`, `drift-watch`, `work-prompt`, `hubs`/`index` (term-of-art — document) | `fleet-health`→`agent-health`; `system/board/`→`board-tasks/`; `system/eval/`→`eval-tasks/` (disambiguates from `metrics/eval/` results) |

**Cleanest areas (no change):** the 12 JS command scripts (all verb-noun kebab); the 17 templates (each matches its `type:`); librarian/writer/peer-reviewer skills (`<domain>-<verb>-<noun>`); base names; the two Claude-Code skills.

### 1.6 Tests

The suite is mid-migration: ~85% follow `test_<behavior>` (exemplary — they read as specs), but **18 legacy files** have a single module-named function (`def test_link`, `def test_pipeline`, …) wrapping an inner `_run()` + `CheckHarness`. Split these into granular `test_<behavior>` functions. No vague `test1`/`test_basic` anywhere; file↔module mapping is strong (only `test_schemas.py`↔`schema` singular/plural nit).

### 1.7 Repo top-level

The `_notes/ _papers/` underscore convention ("local scratch, not shipped") is consistent but **undocumented** — add a one-line gloss in README/AGENTS.md. `src/` is the shipped vault skeleton (not generic source) — a one-line clarification helps newcomers.

---

## Part 2 — Diátaxis (work vs study)

**The rule:** Reference = consult *while working* (neutral facts, tables, schemas, commands — no rationale, no steps). Explanation = study *away from* the work (the "why" — no lookup tables, no procedures). The split is on the reader's *stance*, not the subject.

### 2.1 Reference pages (`docs/reference/`, 29 audited)

- **CLEAN: 14** (incl. `system-actions.md` — clean *by design* as a catalog/map).
- **MIXED: 14** (12 leak explanation/rationale; 3 leak how-to; 2 both).
- **Misfiled content: 1** — `reference/ingest.md` documents the ingest engine **and** the sweeps engine.

Highest-impact:

| Page | Problem | Fix |
|---|---|---|
| `reference/ingest.md` | `:78-95` documents `reconcile.py`/`retraction.py` (the *sweeps*, not ingest); rationale bleed at `:21,35,39,43-44,58,73` | Split sweeps → `reference/sweeps.md`; move the "why" (uncertainty floor, automated-not-gated) to explanation; keep the tables |
| `reference/linter.md` | `:8,23,55` design-philosophy framing ("gates at commit, monitors between"; *why* the golden copy exists) | Move "why" to explanation; keep the detector/command tables |
| `reference/frontmatter.md` | `:8,69,123` rationale (single-source design; lifecycle-vs-status teaching) | Trim to field tables; rationale → explanation |
| `reference/policy-mcp.md`, `profiles.md`, `dashboards.md`, `computational-toolbox.md`, `kanban-board.md`, `linking.md`, `installer.md`, `obsidian-callouts.md`, `obsidian-command-palette.md`, `obsidian-workspaces.md`, `telemetry.md` | A few rationale/how-to lines each (details in the per-page findings) | Lift the stray lines; `linking.md:130` (tag-rename procedure) → a how-to guide |

Most MIXED pages need only a few lines trimmed — the contracts and tables are solid. Many already carry correct "for the rationale see [explanation]" deferrals; the violations are the spots that *state* the rationale instead of deferring it.

### 2.2 Explanation pages (`docs/explanation/`, 70 audited)

- **CLEAN: 57** (~6 carry only the secondary "engine" vocabulary flag, no register violation).
- **MIXED: 13.**
- **Misfiled (whole page): 0** — every MIXED page has a genuine explanation spine; the fix is to *lift an embedded reference table/command out*, not relocate the page.

Highest-impact:

| Page | Problem | Fix |
|---|---|---|
| `explanation/engines/README.md` | `:19-25` the "five engines" table (`Engine \| What it does \| Invocation`) + `:27-33` source-path/symbol catalog are **reference**; whole page built on retired "engine"/"deterministic apps" vocab | Move the table + source catalog to a `reference/operations.md`; keep the *why-not-agents* spine; primary target for the Operations rename |
| `kanban-board/card-schema.md` | `:19-23`, `:30-34` field-definition tables (+ enum values) are **reference** | Move tables → `reference/frontmatter.md` (page already links there); keep the honesty-card rationale |
| `deployment/{deployment-options,distribution-model,bootstrap-installer}.md` | reference-style tables (deployment patterns, repo-parts, multi-vault knobs `OBSIDIAN_MCP_PORT`/`HERMES_HOME`) + install steps | Lift tables → `reference/`; lift steps → how-to |
| `dashboards/.../{audit-log,eval-trend,skill-lifecycle,drift-watch,loose-ends}.md` | exact view/column specs, thresholds, config-field names, a `lint:restore` command | Lift the specs → `reference/dashboards.md`; keep the "what this surface is for" |
| `knowledge/{note-types,note-body-structure}.md`, `profiles/README.md` | entity/card-type catalogs + profile index tables (reference) | Trim to the principle; defer the catalog to reference |

**Dominant pattern:** explanation pages stay correctly oriented to "why" but embed a reference-style lookup table (deployment patterns, card fields, dashboard column specs, profile index, note-type catalog) or a stray command. The fix is consistent: **lift the table/command to reference (or how-to); keep the rationale.**

### 2.3 Diátaxis ↔ the engines split (they interact)

`explanation/engines/README.md` is both the #1 Diátaxis offender (reference table embedded) *and* the #1 doc target for the Operations rename. Do them together: when you split that table out to `reference/operations.md`, name it with the new vocabulary (Operations → Processing/Integrity/Cleanup/Telemetry), and give each operation its reference page + explanation page (the per-operation split from companion Issue 3a).

---

## Part 3 — Prioritized fix list

**Now (cheap, no decision needed) — [FIX]:**

1. D-1…D-4 defects (reconcile docstring, `TestHarness` rename, retraction-cron name, Zone.Identifier cruft).
2. Document the `_notes/_papers` convention; one-line `src/` clarification.
3. Co-PI skill renames; QuickAdd article/verb normalization; `notes/source→sources`, `notes/index→indexes`.
4. Lift the easy Diátaxis strays: split sweeps out of `reference/ingest.md`; move the field tables out of `kanban-board/card-schema.md` and the five-engine table out of `explanation/engines/README.md`.

**Needs a decision — [ADR]:**

5. Adopt **Operations → Processing/Integrity/Cleanup/Telemetry** (companion Issue 2) → then the atomic rename in §1.2/§1.3 (incl. `pipeline.py`, `lib/`, `golden.py`, `sweeps/` split, `cluster` rehome).
6. Snake-case the `scripts/*.py` + retire `load_script()` (§1.4).
7. Per-operation Diátaxis split (reference + explanation per operation), naming the new reference page with the Operations vocab.

**Sequencing (critical):**

- Do the **source-link convention** (main report §8 / companion Issue 3c) **before** the Operations path rename, so doc links aren't pinned to paths about to move.
- Do the Operations rename as **one atomic change** across all the §1.2 hardcoded paths + docs; re-run `docs-doctor` and the test suite after.
- Split the `scripts/*.py` rename from the Operations rename (different blast radius; both touch CI).
