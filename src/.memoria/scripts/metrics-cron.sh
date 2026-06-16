#!/usr/bin/env bash
# metrics-cron.sh — the weekly metrics aggregator (fleet health). Rolls the
# policy audit log, the Hermes board, and lint findings into per-lane metric
# notes under system/metrics/ that the fleet-health dashboard reads.
# The installer substitutes {{PYTHON}} and {{VAULT_PATH}} when it copies this
# to ~/.hermes/scripts/memoria-metrics.sh.
set -u
# shellcheck disable=SC2288  # {{PYTHON}} is a template placeholder, substituted at install time
if "{{PYTHON}}" "{{VAULT_PATH}}/.memoria/mcp/metrics_aggregate.py" --vault "{{VAULT_PATH}}" >/dev/null; then
  # shellcheck disable=SC2288
  "{{PYTHON}}" "{{VAULT_PATH}}/.memoria/mcp/cron_heartbeat.py" --vault "{{VAULT_PATH}}" --job memoria-metrics >/dev/null || true
fi
