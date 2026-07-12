# ExecPlan — Remove Compatibility Paths and Refactor Runtime Tooling

## 0. Metadata

- **Task:** Implement the refactor recommendations from the technical-debt scan, with no backward-compatibility or upgrade-path preservation.
- **Worktree / branch:** `/home/eranr/mv-refactor-no-compat` · `feat/refactor-no-compat`
- **Related ADRs:** ADR-27, ADR-28, ADR-44, ADR-55, ADR-69, ADR-76
- **Related issues / milestone:** v0.1.0-alpha.8 checkpoint
- **Started:** 2026-06-20 · **Last updated:** 2026-06-20

## 1. Purpose / big picture

This migration removes compatibility shims and upgrade/refresh behavior that keep old runtime layouts alive. The observable result is a simpler codebase: vault-side operations import through real packages, policy semantics have one implementation, the board exporter and linter detectors are split by responsibility, and installers describe fresh deployment rather than in-place upgrade reconciliation.

The user explicitly requested that there should be no backward compatibility or upgrade paths. That means stale profile pruning, legacy package fallbacks, old-field readers, and upgrade documentation are defects to remove rather than compatibility contracts to preserve.

## 2. Context and orientation

The packaged runtime lives under `memoria/`. The deployed vault image lives under `src/`, including `.memoria/mcp/`, `.memoria/operations/`, `.memoria/plugins/`, and `.memoria/profiles/`. Tests currently make vault-side modules importable by listing many loose directories in `pyproject.toml` under `tool.pytest.ini_options.pythonpath`.

The current technical debt clusters are:

- `src/.memoria/memoria_runtime/policy/` is a compatibility import path and duplicates `memoria/runtime/policy/paths.py`.
- Many runtime modules import bare names like `schema`, `inbox`, `runner`, and `detectors`, which depends on `sys.path` surgery and pytest `pythonpath`.
- `src/.memoria/mcp/board_export.py` combines Hermes board loading, cost joins, markdown projection, event diffing, and inbox prompt writing.
- `src/.memoria/operations/integrity/linter/detectors.py` combines shared parsing, all detector families, registry, and CLI.
- `scripts/install.sh`, `scripts/install.ps1`, docs, and tests still describe refresh, upgrade, golden reconciliation, stale-profile pruning, and legacy aliases.

## 3. Plan of work

First, make vault-side code importable as packages by adding package markers and converting internal imports to package-qualified imports. Keep executable entrypoints, but make them thin adapters over packages. Remove the `src/.memoria/memoria_runtime` fallback and update consumers to import `memoria.runtime.policy` directly.

Second, split the board exporter into small modules under a package while preserving `board_export.py` as the command entrypoint expected by cron wrappers. Split detectors the same way: common helpers and finding model, content/audit/design detector families, and a CLI/registry module.

Third, remove installer and documentation paths that exist only to refresh or upgrade older installs. Fresh install and profile deployment remain; in-place golden upgrade, stale deployed profile pruning, legacy skill-name prose, and compatibility tests are removed or rewritten.

Finally, run focused tests for each touched surface and then the full local gate if the environment permits.

## 4. Concrete steps

1. **Isolate the session.**

   ```bash
   git fetch origin
   git worktree add /home/eranr/mv-refactor-no-compat -b feat/refactor-no-compat origin/main
   cd /home/eranr/mv-refactor-no-compat
   ```

   Expected output: branch `feat/refactor-no-compat` checked out at `origin/main`.

2. **Inventory compatibility and loose imports.**

   ```bash
   rg -n "memoria_runtime|legacy|compatibility|upgrade|retired|sys\.path|pythonpath" pyproject.toml memoria src scripts tests docs
   ```

   Expected output: all compatibility paths to remove or update.

3. **Package runtime operations and remove policy duplication.**

   Convert loose imports to package imports, delete `src/.memoria/memoria_runtime/`, and trim `pyproject.toml` `pythonpath`.

4. **Split board export and detectors.**

   Move logic into package modules and leave CLI wrappers at existing paths.

5. **Remove installer upgrade paths and stale docs/tests.**

   Replace refresh/upgrade language with fresh deploy behavior and update tests to enforce the new contract.

6. **Validate.**

   ```bash
   python -m ruff check . --cache-dir /tmp/memoria-ruff-cache
   PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_package_spine.py tests/test_runtime_policy.py tests/test_board_export.py tests/test_detectors.py tests/test_installer_skeleton.py -q
   bash -n scripts/install.sh scripts/install/*.sh
   git diff --check
   scripts/test.sh all
   ```

## 5. Validation and acceptance

- **Claim:** Given packaged vault operations, when tests import operation modules, then they do not require broad loose `pythonpath` entries.
  - **Prove with:** focused pytest and inspection of `pyproject.toml`.
- **Claim:** Given the policy package, when policy tests run, then there is one policy path implementation and no `src/.memoria/memoria_runtime` fallback.
  - **Prove with:** `tests/test_package_spine.py`, `tests/test_runtime_policy.py`, `tests/test_policy_mcp.py`, `tests/test_policy_hook.py`.
- **Claim:** Given fresh-install-only behavior, when installer tests inspect scripts/docs, then no upgrade/stale-profile compatibility path remains.
  - **Prove with:** `tests/test_installer_skeleton.py`, docs/status checks.
- **Claim:** Given split board and detector modules, when their focused tests run, then observable behavior is unchanged except intentionally removed compatibility.
  - **Prove with:** `tests/test_board_export.py`, `tests/test_detectors.py`, related linter tests.

## 6. Idempotence and recovery

- **Safe to re-run:** package/import changes are source edits; tests and lint can run repeatedly. Fresh-install docs are deterministic.
- **Rollback:** revert this branch or remove `/home/eranr/mv-refactor-no-compat` with `git worktree remove` if no changes should ship.

## 7. Progress

- [x] 2026-06-20 — Created isolated worktree and ExecPlan.
- [x] 2026-06-20 — Package vault operations and remove policy compatibility duplication.
- [x] 2026-06-20 — Split board exporter and detectors.
- [x] 2026-06-20 — Remove installer/docs upgrade paths.
- [x] 2026-06-20 — Run validation and update outcomes.

## 8. Execution log

- 2026-06-20 — Chose to keep existing executable filenames such as `board_export.py` and `detectors.py` as CLI wrappers while moving implementation into packages. This preserves cron/test entrypoints without keeping legacy behavior.
- 2026-06-20 — Removed fresh-vault refresh/golden-upgrade behavior from installers, deleted the upgrade how-to, and removed old skill aliases, cost token aliases, and the chat-export stamping sweep.

## 9. Surprises & discoveries

- The task worktree is outside the sandbox writable root, so write commands require explicit escalation even though the repo policy requires this worktree.

## 10. Interfaces & dependencies

- Python target: `requires-python = ">=3.11"` in `pyproject.toml`.
- Source-of-truth contracts: `.agents/system/source-of-truth-map.md`.
- Impact and tests: `.agents/system/change-impact-map.md` and `.agents/system/test-selection.md`.

## 11. Artifacts & notes

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPYCACHEPREFIX=/tmp/memoria-pycache python -m pytest tests/test_package_spine.py tests/test_runtime_policy.py tests/test_board_export.py tests/test_detectors.py tests/test_pipeline.py tests/test_project_structural_impact.py -q` → `38 passed`.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPYCACHEPREFIX=/tmp/memoria-pycache python -m pytest tests/ -q` → `433 passed`, with only the read-only `.pytest_cache` warning.
- `PYTHONPYCACHEPREFIX=/tmp/memoria-pycache python -m ruff check . --cache-dir /tmp/memoria-ruff-cache` → `All checks passed!`.
- `bash -n scripts/install.sh scripts/install/*.sh src/.memoria/scripts/*.sh` → pass.
- `bash scripts/e2e-smoke.sh` → all gates green after updating the smoke harness path setup to the package root.
- `python scripts/docs_doctor.py docs`, `python scripts/status_doctor.py`, `python scripts/agents_doctor.py`, and `bash scripts/check-vault-links.sh` → clean.

## 12. Outcomes & retrospective

- **Shipped:** Operation packages, split board/detector modules, deleted policy fallback, fresh-install-only bootstrap behavior, stage/check/restore-only golden copy, package-qualified tests/imports, and docs aligned to no upgrade/compatibility path.
- **Still open:** Nothing required for this task.
- **Routed to:** This working plan under `docs/releasing/0.1.0-alpha.8/tmp/`.
- **Lessons:** Removing the broad pytest `pythonpath` was a useful forcing function; it flushed out loose module imports that focused tests had not exercised.
