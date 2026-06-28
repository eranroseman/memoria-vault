---
topic: tests
title: Headless test plan
status: draft
parent: Test plans
grand_parent: Testing
nav_order: 16
---

# Headless test plan — v0.1

The full **non-GUI** verification of the Memoria vault: every deterministic check that runs end-to-end with no Obsidian, no Hermes runtime, no Zotero, and no human eyeball. It is the suite **CI enforces** (the five required status checks) **plus** the schema-correctness checks that catch the silent dashboard/telemetry drift class. Run it after any change to the `.memoria/` tooling, the dashboards, the templates, or the docs — and as the **first gate when rebuilding the test vault**, before the GUI plan.

**Boundary — validated elsewhere.** Anything needing Obsidian (QuickAdd instantiation, Dataview rendering, the launch screen and left-pane rail), Hermes (profile dispatch, the live write-gate, cron), or Zotero is **out of scope here** — see the [GUI test plan](gui-test-plan.md) (backs **S5** / **G4**) and the [Hermes CLI test plan](hermes-cli-test-plan.md). This plan is the prerequisite both of those build on: if the headless gate is red, don't bother with the GUI.

**Where to run.** Repo root (`memoria-vault/`), any machine with Python 3.11+. Parts A/B/D/E need only Python; Part C additionally needs `shellcheck` and PowerShell + `PSScriptAnalyzer`. No vault runtime, no network except installing `requirements.txt`. The whole thing is scriptable — that's the point.

**How to read each step.** **Action** → **✓ Pass** (the exact observable) → **✗ If it fails** (first thing to check). Tick the boxes; fill the results table at the end.

---

## 0. Preconditions

- [ ] At the repo root, on the branch under test.
- [ ] Python 3.11+ on `PATH`.
- [ ] `python -m pip install -r requirements-dev.txt` (pytest + local static-check tooling).
- [ ] `python -m pip install -r src/.memoria/mcp/requirements.txt` (mcp, PyYAML). `policy_mcp` degrades gracefully without PyYAML, but install it for the full suite.
- [ ] (Part C only) `shellcheck` on `PATH`; PowerShell with `Install-Module PSScriptAnalyzer -Scope CurrentUser`.

---

## Part A — Component tests (mirrors the `python-selftest` CI job)

The component tests live in the repo-side `tests/` pytest tree ([Tests in the pytest tree](../../adr/44-tests-in-pytest-tree.md)) — synthetic fixtures, no vault needed. Run them all with `scripts/test.sh l1` (= `python3 -m pytest tests/ -q`); **all must pass.** To bisect a failure, run a single module:

**A1. Policy MCP.** `python3 -m pytest tests/test_policy_mcp.py -q`
- ✓ Pass: all pass (covers the glob matcher, the auto-fix classes, and every profile's write-wall — all lanes' allow/deny contract).
- ✗ Fails: a policy decision changed — diff against the lane-override rules and the review-gated-zone / auto-fix-class logic.

**A2. Policy hook (the gate's pre/post).** `python3 -m pytest tests/test_policy_hook.py -q`
- ✓ Pass: all pass.
- ✗ Fails: the obsidian-tool→policy-action mapping or the fail-closed behavior regressed.

**A3. Board export.** `python3 -m pytest tests/test_board_export.py -q`
- ✓ Pass: all pass.
- ✗ Fails: the card-markdown schema (`card_markdown` `fm_keys`) or the jsonl snapshot/transition/disposition/cost logic changed.

**A4. Metrics aggregate.** `python3 -m pytest tests/test_metrics_aggregate.py -q`
- ✓ Pass: all pass (includes the `lint-verdict` rollup).
- ✗ Fails: trust-score math, ISO-week `period` handling, or the `lint-verdict` note changed.

**A5. Linter detectors.** `python3 -m pytest tests/test_detectors.py -q`
- ✓ Pass: all pass (each detector fires on a planted defect and ignores scaffolding/valid links).
- ✗ Fails: a detector regressed — the test names which (`dashboard-field-drift`, `broken-wikilink`, `fama-exposure`, …).

---

## Part B — Doc + repo integrity (mirrors `docs-doctor` + `docs-links` CI)

**B1. docs-doctor.** `python scripts/docs_doctor.py docs`
- ✓ Pass: `docs-doctor: clean ✓` (page-title link text, internal links, template-field references).
- ✗ Fails: it prints `file:line` + the rule — fix the link text / path it names.

**B2. Vault link resolution.** `bash scripts/check-vault-links.sh`
- ✓ Pass: exit 0 — every in-vault `[[wikilink]]` and website URL resolves (the no-slash GitHub-Pages URL form).
- ✗ Fails: it names the unresolved reference and its `file:line`.

---

## Part C — Installer lint (mirrors `lint-installers` CI — both are required checks)

**C1. shellcheck.** `shellcheck --severity=warning scripts/install.sh scripts/install/*.sh src/.memoria/operations/integrity/linter/pre-commit src/.memoria/scripts/*.sh`
- ✓ Pass: no output, exit 0.
- ✗ Fails: `SCxxxx` at a `file:line` — fix it, or scope a `# shellcheck disable=SCxxxx`. (The cron *template* `board-export-cron.sh` carries `{{PYTHON}}` placeholders that read as a brace command → `SC2288` is disabled on that line by design.)

**C2. PSScriptAnalyzer** (PowerShell). `Invoke-ScriptAnalyzer -Path scripts/install.ps1 -Severity Warning,Error -Settings ./scripts/PSScriptAnalyzerSettings.psd1`
- ✓ Pass: returns no results.
- ✗ Fails: e.g. `PSUseBOMForUnicodeEncodedFile` → keep `install.ps1` ASCII-only (no em-dashes / smart quotes) or add a UTF-8 BOM.

---

## Part D — Schema-correctness (beyond CI — catches the silent dashboard/telemetry drift class)

A dashboard that queries a field **no writer emits** doesn't error — it shows an empty table forever. These checks catch that. Run against the repo source tree (`src/`) and, when validating an installed candidate, the rebuilt test vault.

**D1. dashboard-field-drift + design-system-drift on the repo source.** `python src/.memoria/operations/integrity/linter/detectors.py --vault src --gate dashboard-field-drift,design-system-drift`
- ✓ Pass: no `dashboard-field-drift` or `design-system-drift` findings — dashboard fields resolve to templates, and shipped visual consumers stay inside `.memoria/design-system.md`.
- ✗ Fails: it names the dashboard, the query block, and the missing field — add the field to a template or fix the query. (This covers note-folder queries only; D2 covers the non-note feeds it can't see.)

**D2. Dashboard ↔ writer-schema audit (non-note sources).** For every dashboard query over `system/board`, `system/metrics`, or a `system/logs/*.jsonl`, confirm each field it reads is produced by the writer. Derive the schemas from the code (don't trust prose):

| Source | Schema is defined by | Fields |
| --- | --- | --- |
| `system/board/<id>.md` (card notes) | `board_export.py` → `card_markdown` frontmatter | `title, type: worker-card, lifecycle, task_id, lane, status, review_status, retry_count, reason, as_of, created, expected_outputs` |
| `board-state.jsonl` | `board_export.py` snapshot dict | `timestamp, lanes{…}, totals{running,ready,blocked,review_queue}` — **counts only, no card identity** |
| `system/metrics/lane-*.md` | `metrics_aggregate.py` → `lane_note` | `type:lane-metric, lane, period, trust_score, band, …, samples, success_rate` |
| `system/metrics/lint-verdict-*.md` | `metrics_aggregate.py` → `lint_verdict_note` | `type:lint-verdict, period, verdict, finding_count, critical_count, high_count, medium_count, …` |
| `lint-findings.jsonl` | `detectors.py` → `Finding` dataclass | `timestamp, detector, severity, path, message` |
| `audit.jsonl` | `policy_mcp.py` audit writer | `timestamp, profile, action, path, task_id, decision, policy_rule, before_hash, after_hash` |
| `system/metrics/eval/runs.jsonl` | `eval_score.py` → `score_run` | `timestamp, quarter, k, tasks[{task,workflow,lane,status,metrics{recall_at_k,support_rate,fama_clean,fama_exposed},self_score}], aggregate{<metric>{mean,n}, tasks_total, tasks_scored, tasks_reported, tasks_unscored}` |

- ✓ Pass: every DQL column / `WHERE` / `SORT` field and every `dataviewjs` `e.<field>` / `dv.pages(...).<field>` resolves to a field above. **And** every `.jsonl` feed is read with `dataviewjs` + `dv.io.load(...)` — never a DQL `FROM "…/x.jsonl"` (DQL queries note folders, not jsonl).
- ✗ Fails: a field or mechanism mismatch → fix the dashboard query; or, where the data already exists in the writer's projection, serialize it from the writer. Canonical schemas: [Telemetry & logs](../../reference/telemetry.md).

> **Rule of thumb.** "No results to show" / "✅ All clear" on a fed dashboard is *only* trustworthy once D1+D2 are green — otherwise it's the failure mode, not success.

---

## Part E — Quick syntax sanity (pre-commit)

**E1. Python compiles.** `python -m py_compile src/.memoria/mcp/*.py src/.memoria/operations/integrity/linter/detectors.py`
- ✓ Pass: exit 0, no output.

**E2. Shell parses.** `bash -n scripts/install.sh`
- ✓ Pass: exit 0.

---

## One-shot runner

The maintained PR entrypoint is `scripts/verify pr`; it runs this Source Gate and
writes a JSON evidence bundle. `scripts/test.sh` remains the direct runner for
bisecting this gate. From the repo root:

```bash
scripts/verify pr     # Source Gate, with evidence
scripts/test.sh        # everything (default)
scripts/test.sh l1     # Part A only — the pytest component suite
scripts/test.sh l0     # Parts B + C + E, plus the D1 informational run
```

It exits nonzero if any **gated** check fails, so it doubles as a pre-push hook, and it mirrors the CI jobs — green here means green in CI. In [ADR-29](../../adr/29-testing-framework.md) terms these are the bottom two layers: **L1** = Part A (pytest component suite), **L0** = Parts B/C/E plus D1 (static + schema + dashboard-field drift). Broader vault-content findings remain L5 and are not part of this local gate.

Caveats it can't fully cover on its own: Part **C2** (PSScriptAnalyzer) needs PowerShell, and shellcheck (C1) is skipped with a notice when absent (CI still enforces both); the Part **D2** schema audit carries judgment — run it separately.

---

## Results

| Part | Check | Pass? |
| --- | --- | --- |
| A1 | `pytest tests/test_policy_mcp.py` | ☐ |
| A2 | `pytest tests/test_policy_hook.py` | ☐ |
| A3 | `pytest tests/test_board_export.py` | ☐ |
| A4 | `pytest tests/test_metrics_aggregate.py` | ☐ |
| A5 | `pytest tests/test_detectors.py` | ☐ |
| B1 | `docs-doctor` | ☐ |
| B2 | `check-vault-links` | ☐ |
| C1 | shellcheck (installers) | ☐ |
| C2 | PSScriptAnalyzer (`install.ps1`) | ☐ |
| D1 | dashboard-field-drift + design-system-drift (`--vault`) | ☐ |
| D2 | dashboard ↔ writer-schema audit | ☐ |
| E1/E2 | Python + shell syntax | ☐ |

**Green criteria.** Parts **A + B + C** all pass (this *is* the CI gate — the five required status checks), and Part **D** shows no schema drift. Only then is the [GUI plan](gui-test-plan.md) (S5 / G4) worth running.

---

## Related

- Human / GUI validation (S5, G4): [GUI test plan — v0.1 (S5 + G4)](gui-test-plan.md)
- Hermes CLI checks: [Hermes CLI test plan](hermes-cli-test-plan.md)
- The template these plans share: [{{Subject}} test plan](../test-plan-template.md)
- CI that enforces A/B/C: `.github/workflows/{python-selftest,docs-doctor,docs-links,lint-installers}.yml`
- Canonical telemetry schemas (for D2): [Telemetry & logs](../../reference/telemetry.md)
