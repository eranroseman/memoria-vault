---
topic: tests
title: "Headless test plan"
status: draft
---

# Headless test plan — v0.1

The full **non-GUI** verification of the Memoria vault: every deterministic check that runs end-to-end with no Obsidian, no Hermes runtime, no Zotero, and no human eyeball. It is the suite **CI enforces** (the five required status checks) **plus** the schema-correctness checks that catch the silent dashboard/telemetry drift class. Run it after any change to the `.memoria/` tooling, the dashboards, the templates, or the docs — and as the **first gate when rebuilding the test vault**, before the GUI plan.

**Boundary — validated elsewhere.** Anything needing Obsidian (QuickAdd instantiation, Dataview rendering, the homepage), Hermes (profile dispatch, the live write-gate, cron), or Zotero is **out of scope here** — see the [GUI test plan](gui-test-plan.md) (backs **S5** / **G4**) and the [Hermes CLI test plan](hermes-cli-test-plan.md). This plan is the prerequisite both of those build on: if the headless gate is red, don't bother with the GUI.

**Where to run.** Repo root (`memoria-vault/`), any machine with Python 3.11+. Parts A/B/D/E need only Python; Part C additionally needs `shellcheck` and PowerShell + `PSScriptAnalyzer`. No vault runtime, no network except installing `requirements.txt`. The whole thing is scriptable — that's the point.

**How to read each step.** **Action** → **✓ Pass** (the exact observable) → **✗ If it fails** (first thing to check). Tick the boxes; fill the results table at the end.

---

## 0. Preconditions

- [ ] At the repo root, on the branch under test.
- [ ] Python 3.11+ on `PATH`.
- [ ] `python -m pip install -r vault/.memoria/mcp/requirements.txt` (mcp, PyYAML). `policy_mcp` degrades gracefully without PyYAML, but install it for the full suite.
- [ ] (Part C only) `shellcheck` on `PATH`; PowerShell with `Install-Module PSScriptAnalyzer -Scope CurrentUser`.

---

## Part A — Python self-tests (mirrors the `python-selftest` CI job)

The five tooling modules each ship a synthetic-fixture `--self-test` (no vault needed). **All must report 0 failures.**

**A1. Policy MCP.** `python vault/.memoria/mcp/policy_mcp.py --self-test`
- ✓ Pass: `OK: 0 failing check(s) [all suite].` (covers the glob matcher, the auto-fix classes, and every profile's write-wall — all 7 lanes' allow/deny contract).
- ✗ Fails: a policy decision changed — diff against the lane-override rules and the review-gated-zone / auto-fix-class logic.

**A2. Policy hook (the gate's pre/post).** `python vault/.memoria/mcp/policy_hook.py --self-test`
- ✓ Pass: `OK: 0 failing check(s).` (32 checks)
- ✗ Fails: the obsidian-tool→policy-action mapping or the fail-closed behavior regressed.

**A3. Board export.** `python vault/.memoria/mcp/board_export.py --self-test`
- ✓ Pass: `OK: 0 failing check(s).` (26 checks)
- ✗ Fails: the card-markdown schema (`card_markdown` `fm_keys`) or the jsonl snapshot/transition/disposition/cost logic changed.

**A4. Metrics aggregate.** `python vault/.memoria/mcp/metrics_aggregate.py --self-test`
- ✓ Pass: `OK: 0 failing check(s).` (includes the `lint-verdict` rollup)
- ✗ Fails: trust-score math, ISO-week `period` handling, or the `lint-verdict` note changed.

**A5. Linter detectors.** `python vault/.memoria/profiles/memoria-linter/skills/structural-detectors/scripts/detectors.py --self-test`
- ✓ Pass: `N/N detector checks passed.` (each detector fires on a planted defect and ignores scaffolding/valid links).
- ✗ Fails: a detector regressed — the line names which (`dashboard-field-drift`, `broken-wikilink`, `fama-exposure`, …).

---

## Part B — Doc + repo integrity (mirrors `docs-doctor` + `docs-links` CI)

**B1. docs-doctor.** `python scripts/docs-doctor.py docs`
- ✓ Pass: `docs-doctor: clean ✓` (page-title link text, internal links, template-field references).
- ✗ Fails: it prints `file:line` + the rule — fix the link text / path it names.

**B2. Vault link resolution.** `bash scripts/check-vault-links.sh`
- ✓ Pass: exit 0 — every in-vault `[[wikilink]]` and website URL resolves (the no-slash GitHub-Pages URL form).
- ✗ Fails: it names the unresolved reference and its `file:line`.

---

## Part C — Installer lint (mirrors `lint-installers` CI — both are required checks)

**C1. shellcheck.** `shellcheck --severity=warning scripts/install.sh vault/.memoria/scripts/*.sh`
- ✓ Pass: no output, exit 0.
- ✗ Fails: `SCxxxx` at a `file:line` — fix it, or scope a `# shellcheck disable=SCxxxx`. (The cron *template* `board-export-cron.sh` carries `{{PYTHON}}` placeholders that read as a brace command → `SC2288` is disabled on that line by design.)

**C2. PSScriptAnalyzer** (PowerShell). `Invoke-ScriptAnalyzer -Path scripts/install.ps1 -Severity Warning,Error -Settings ./scripts/PSScriptAnalyzerSettings.psd1`
- ✓ Pass: returns no results.
- ✗ Fails: e.g. `PSUseBOMForUnicodeEncodedFile` → keep `install.ps1` ASCII-only (no em-dashes / smart quotes) or add a UTF-8 BOM.

---

## Part D — Schema-correctness (beyond CI — catches the silent dashboard/telemetry drift class)

A dashboard that queries a field **no writer emits** doesn't error — it shows an empty table forever. These checks catch that. Run against a real vault tree (`vault/`, or the rebuilt test vault).

**D1. dashboard-field-drift on the real vault.** `python vault/.memoria/profiles/memoria-linter/skills/structural-detectors/scripts/detectors.py --vault vault`
- ✓ Pass: no `dashboard-field-drift` findings — every field a dashboard queries **over a note folder** exists in some template.
- ✗ Fails: it names the dashboard, the query block, and the missing field — add the field to a template or fix the query. (This covers note-folder queries only; D2 covers the non-note feeds it can't see.)

**D2. Dashboard ↔ writer-schema audit (non-note sources).** For every dashboard query over `99-system/board`, `99-system/metrics`, or a `99-system/logs/*.jsonl`, confirm each field it reads is produced by the writer. Derive the schemas from the code (don't trust prose):

| Source | Schema is defined by | Fields |
| --- | --- | --- |
| `99-system/board/<id>.md` (card notes) | `board_export.py` → `card_markdown` `fm_keys` | `task_id, status, assignee, review_status, retry_count, reason, last_updated` (+ `type: board-card`) |
| `board-state.jsonl` | `board_export.py` snapshot dict | `timestamp, lanes{…}, totals{running,ready,blocked,review_queue}` — **counts only, no card identity** |
| `99-system/metrics/lane-*.md` | `metrics_aggregate.py` → `lane_note` | `type:lane-metric, lane, period, trust_score, band, …, samples, success_rate` |
| `99-system/metrics/lint-verdict-*.md` | `metrics_aggregate.py` → `lint_verdict_note` | `type:lint-verdict, period, verdict, finding_count, critical_count, high_count, medium_count, …` |
| `lint-findings.jsonl` | `detectors.py` → `Finding` dataclass | `timestamp, detector, severity, path, message` |
| `audit.jsonl` | `policy_mcp.py` audit writer | `timestamp, profile, action, path, task_id, decision, policy_rule, before_hash, after_hash` |

- ✓ Pass: every DQL column / `WHERE` / `SORT` field and every `dataviewjs` `e.<field>` / `dv.pages(...).<field>` resolves to a field above. **And** every `.jsonl` feed is read with `dataviewjs` + `dv.io.load(...)` — never a DQL `FROM "…/x.jsonl"` (DQL queries note folders, not jsonl).
- ✗ Fails: a field or mechanism mismatch → fix the dashboard query; or, where the data already exists in the writer's projection, serialize it from the writer. Canonical schemas: [docs/reference/telemetry.md](../../../docs/reference/telemetry.md).

> **Rule of thumb.** "No results to show" / "✅ All clear" on a fed dashboard is *only* trustworthy once D1+D2 are green — otherwise it's the failure mode, not success.

---

## Part E — Quick syntax sanity (pre-commit)

**E1. Python compiles.** `python -m py_compile vault/.memoria/mcp/*.py vault/.memoria/profiles/memoria-linter/skills/structural-detectors/scripts/detectors.py`
- ✓ Pass: exit 0, no output.

**E2. Shell parses.** `bash -n scripts/install.sh`
- ✓ Pass: exit 0.

---

## One-shot runner — `scripts/test.sh`

The maintained runner for this gate (don't copy-paste a loop that drifts). From the repo root:

```bash
scripts/test.sh        # everything (default)
scripts/test.sh l1     # Part A only — the five component self-tests
scripts/test.sh l0     # Parts B + C + E, plus the D1 informational run
```

It exits nonzero if any **gated** check fails, so it doubles as a pre-push hook, and it mirrors the CI jobs — green here means green in CI. In [ADR-29](../../adr/29-testing-framework.md) terms these are the bottom two layers: **L1** = Part A (component self-tests), **L0** = Parts B/C/E (static + schema). The runner also runs Part **D1** (`detectors --vault`) as an **informational, non-gating** footer — review its findings by eye; a nonzero count never reddens the verdict here (vault-content quality is L5, not L0).

Caveats it can't fully cover on its own: Part **C2** (PSScriptAnalyzer) needs PowerShell, and shellcheck (C1) is skipped with a notice when absent (CI still enforces both); the Part **D2** schema audit carries judgment — run it separately.

---

## Results

| Part | Check | Pass? |
| --- | --- | --- |
| A1 | `policy_mcp --self-test` (34) | ☐ |
| A2 | `policy_hook --self-test` (32) | ☐ |
| A3 | `board_export --self-test` (26) | ☐ |
| A4 | `metrics_aggregate --self-test` (+ lint-verdict) | ☐ |
| A5 | `detectors --self-test` (15/15) | ☐ |
| B1 | `docs-doctor` | ☐ |
| B2 | `check-vault-links` | ☐ |
| C1 | shellcheck (installers) | ☐ |
| C2 | PSScriptAnalyzer (`install.ps1`) | ☐ |
| D1 | dashboard-field-drift (`--vault`) | ☐ |
| D2 | dashboard ↔ writer-schema audit | ☐ |
| E1/E2 | Python + shell syntax | ☐ |

**Green criteria.** Parts **A + B + C** all pass (this *is* the CI gate — the five required status checks), and Part **D** shows no schema drift. Only then is the [GUI plan](gui-test-plan.md) (S5 / G4) worth running.

---

## Related

- Human / GUI validation (S5, G4): [gui-test-plan.md](gui-test-plan.md)
- Hermes CLI checks: [hermes-cli-test-plan.md](hermes-cli-test-plan.md)
- The template these plans share: [test-plan-template.md](../test-plan-template.md)
- CI that enforces A/B/C: `.github/workflows/{python-selftest,docs-doctor,docs-links,lint-installers}.yml`
- Canonical telemetry schemas (for D2): [docs/reference/telemetry.md](../../../docs/reference/telemetry.md)
