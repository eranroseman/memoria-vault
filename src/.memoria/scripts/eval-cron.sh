#!/usr/bin/env bash
# eval-cron.sh — the quarterly vault-eval dispatch (ADR-11: diagnostic, never
# gating). Fans the gold set in system/eval/ out as one idempotent kanban card
# per task, routed to the lane that owns the workflow; the dispatch record is
# written to system/eval/last-run.md.
# The installer substitutes {{PYTHON}} and {{VAULT_PATH}} when it copies this
# to ~/.hermes/scripts/memoria-eval.sh.
set -u
# shellcheck disable=SC2288  # {{PYTHON}} is a template placeholder, substituted at install time
"{{PYTHON}}" "{{VAULT_PATH}}/.memoria/engines/sweeps/eval_dispatch.py" --vault "{{VAULT_PATH}}" >/dev/null || true
