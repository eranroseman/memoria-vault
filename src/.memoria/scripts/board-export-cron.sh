#!/usr/bin/env bash
# Board-export telemetry cron (G5). Projects the live Hermes kanban board to the
# vault and appends the six-signal telemetry logs (board-state / board-transitions
# / disposition / cost under system/logs/, plus system/board/<task_id>.md).
#
# Deterministic — no LLM. Wired by the installer via:
#   hermes cron create '* * * * *' --script memoria-board-export.sh --no-agent \
#     --name memoria-board-export --deliver local
# It fires whenever the Hermes scheduler is running (the gateway runs it; or
# `hermes cron tick` on demand). stdout is discarded so the cron stays silent —
# the telemetry is the files it writes, not its output.
#
# The installer substitutes {{PYTHON}} (the vault venv interpreter) and
# {{VAULT_PATH}} when it copies this to ~/.hermes/scripts/memoria-board-export.sh.
# shellcheck disable=SC2288  # {{PYTHON}} is a template placeholder, substituted at install time
if "{{PYTHON}}" "{{VAULT_PATH}}/.memoria/mcp/board_export.py" --vault "{{VAULT_PATH}}" >/dev/null; then
  # shellcheck disable=SC2288
  "{{PYTHON}}" "{{VAULT_PATH}}/.memoria/mcp/cron_heartbeat.py" --vault "{{VAULT_PATH}}" --job memoria-board-export >/dev/null || true
fi
