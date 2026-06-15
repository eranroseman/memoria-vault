#!/usr/bin/env bash
# lint-cron.sh — the Linter engine's daily sweep (ADR-49: gates at commit,
# monitors between). Runs the structural detectors over the vault, the
# golden-copy drift check, and the per-session digests (ADR-25); findings
# surface in the vault's drift dashboards.
# The installer substitutes {{PYTHON}} and {{VAULT_PATH}} when it copies this
# to ~/.hermes/scripts/memoria-lint.sh.
set -u
# shellcheck disable=SC2288  # {{PYTHON}} is a template placeholder, substituted at install time
"{{PYTHON}}" "{{VAULT_PATH}}/.memoria/operations/integrity/linter/detectors.py" --vault "{{VAULT_PATH}}" --jsonl-out "{{VAULT_PATH}}/system/logs/lint-findings.jsonl" >/dev/null || true
# shellcheck disable=SC2288
"{{PYTHON}}" "{{VAULT_PATH}}/.memoria/operations/integrity/linter/golden_restore.py" --vault "{{VAULT_PATH}}" check >/dev/null || true
# shellcheck disable=SC2288
"{{PYTHON}}" "{{VAULT_PATH}}/.memoria/operations/integrity/linter/session_summary.py" --vault "{{VAULT_PATH}}" >/dev/null || true
