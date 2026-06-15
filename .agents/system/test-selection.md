# Test selection

Choose tests by risk and blast radius. Focused tests provide fast diagnosis; the
full gate proves repository integration.

## Baseline

For every change:

```bash
git diff --check
```

Run the nearest focused tests for the changed contract. Before PR handoff, run:

```bash
scripts/test.sh all
```

If the environment lacks pytest or another required dependency, report that
explicitly; do not describe an unrun check as passing.
Install contributor Python tooling from `requirements-dev.txt`; runtime MCP
dependencies remain in `src/.memoria/mcp/requirements.txt`.

## Selection table

| Changed paths | Focused checks |
|---|---|
| `src/.memoria/schemas/**` | `python -m pytest tests/test_schemas.py tests/test_templates.py tests/test_bases.py tests/test_precommit_schema.py tests/test_installer_skeleton.py` |
| `src/.memoria/lane-overrides/**` | `python -m pytest tests/test_profiles.py tests/test_policy_mcp.py tests/test_policy_hook.py tests/test_tasks_mcp.py tests/test_skill_lifecycle_dashboard.py` |
| `src/.memoria/tool-registry.yaml` | `python -m pytest tests/test_profiles.py tests/test_skill_lifecycle_dashboard.py` |
| `src/.memoria/profiles/**` | `python -m pytest tests/test_profiles.py tests/test_skill_lifecycle_dashboard.py` |
| `src/.memoria/mcp/policy_*` or policy plugin | `python -m pytest tests/test_policy_mcp.py tests/test_policy_hook.py tests/test_schemas.py` |
| `src/.memoria/mcp/tasks_mcp.py` | `python -m pytest tests/test_tasks_mcp.py tests/test_profiles.py tests/test_quickadd.py` |
| `src/.memoria/mcp/ingest_mcp.py` | `python -m pytest tests/test_ingest_mcp.py tests/test_pipeline.py tests/test_inbox_cards.py` |
| `src/.memoria/operations/processing/ingest/**` | Run `test_pipeline.py` plus the matching component tests: classify, extract, ingest_paper, link, project_hints, or resolve_merge |
| `src/.memoria/operations/integrity/linter/**` | `python -m pytest tests/test_detectors.py tests/test_precommit_schema.py tests/test_golden_restore.py tests/test_session_summary.py` |
| `src/.memoria/operations/**` | Run the matching `test_sweeps_*.py` or eval tests |
| `src/system/templates/**` | `python -m pytest tests/test_templates.py tests/test_schemas.py tests/test_bases.py` |
| `src/system/scripts/**` | `python -m pytest tests/test_quickadd.py` plus the workflow-specific test |
| `src/.obsidian/**` | Run workspace, QuickAdd, Bases, or installer tests matching the changed configuration |
| `scripts/install.sh` or `scripts/install/**` | `bash -n scripts/install.sh scripts/install/*.sh`; dry-run; installer tests; disposable-vault end-to-end when behavior changes |
| `scripts/install.ps1` | `Invoke-ScriptAnalyzer -Path scripts/install.ps1 -Severity Warning,Error -Settings ./scripts/PSScriptAnalyzerSettings.psd1` when `pwsh` is available; CI enforces otherwise |
| `scripts/docs_doctor.py` | `python -m pytest tests/test_docs_doctor.py`; run the doctor over `docs/` |
| `scripts/status_doctor.py` | `python -m pytest tests/test_status_doctor.py`; run the doctor |
| `scripts/github_doctor.py` or `.github/ISSUE_TEMPLATE/**` or `.github/dependabot.yml` | `python -m pytest tests/test_github_doctor.py`; `python scripts/github_doctor.py` |
| `.github/scripts/pr_policy.py` | `python -m pytest tests/test_pr_policy.py` |
| `.github/workflows/**` | actionlint when available; run tests for invoked local scripts; inspect permissions and triggers |
| `.github/ruleset-contract.yaml` or `scripts/ruleset_doctor.py` | `python scripts/ruleset_doctor.py`; `python -m pytest tests/test_ruleset_doctor.py` |
| `.pre-commit-config.yaml`, `.github/workflows/cspell.yml`, or `project-words.txt` | Run the gate as the workflow does (scope and exclusions live in `cspell.json`): `npx --yes cspell@8.19.4 lint --no-progress --no-must-find-files --gitignore "**/*.md"` |
| `requirements-dev.txt`, `scripts/dev-setup.sh`, or Python dependency workflow installs | Install from `requirements-dev.txt` in a disposable venv when practical; run affected lint/test workflows locally |
| `docs/**` | `python scripts/docs_doctor.py docs`; `bash scripts/check-vault-links.sh`; `python scripts/status_doctor.py` for contributing/testing/releasing |
| `.agents/**`, `.codex/**`, `.kilo/**`, `AGENTS.md` | `python scripts/agents_doctor.py`; Markdown lint when available |

## Full-gate triggers

Always run `scripts/test.sh all` when a change:

- Touches a shared schema, policy, profile, installer, or CI contract
- Affects more than one runtime subsystem
- Changes generated or deployed vault structure
- Fixes a regression not previously covered
- Is ready for PR handoff

## Runtime-dependent verification

The full local gate does not prove Hermes, Obsidian, Windows PowerShell, Zotero,
or network-backed scholarly APIs. Use the relevant disposable or attended test
plan and state the limitation when those environments are unavailable.
