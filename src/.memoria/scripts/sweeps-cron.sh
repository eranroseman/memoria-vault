#!/usr/bin/env bash
# Re-ingest sweeps cron (ADR-30). Runs the deterministic backstops:
#   (a) reconcile — capture-intake.jsonl entries with no note on disk
#   (b) retry     — `captured` notes stuck at ingest_status: tier0
#   (c) archive   — resolved inbox cards (lifecycle current/retracted with a
#                   `resolved:` stamp) older than inbox.archive_after_days flip
#                   to lifecycle: archived, so the inbox converges to empty (#338)
# (a) and (b) are detectors that enqueue an *idempotent* re-ingest card
# (hermes kanban create --idempotency-key reingest:<citekey>); the board provides
# serialization, dedup, and the failure circuit-breaker (the needs-human floor).
#
# Deterministic — no LLM. Wired by the installer via:
#   hermes cron create '*/15 * * * *' --script memoria-sweeps.sh --no-agent \
#     --name memoria-sweeps --deliver local
# stdout is discarded so the cron stays silent — its effect is the cards it queues.
#
# The installer substitutes {{PYTHON}} (the vault venv interpreter) and
# {{VAULT_PATH}} when it copies this to ~/.hermes/scripts/memoria-sweeps.sh.
status=0
# shellcheck disable=SC2288  # {{PYTHON}} is a template placeholder, substituted at install time
"{{PYTHON}}" "{{VAULT_PATH}}/.memoria/operations/cleanup/reconcile.py" --vault "{{VAULT_PATH}}" >/dev/null || status=1
# shellcheck disable=SC2288  # {{PYTHON}} is a template placeholder, substituted at install time
"{{PYTHON}}" "{{VAULT_PATH}}/.memoria/operations/cleanup/archive_inbox.py" --vault "{{VAULT_PATH}}" >/dev/null || status=1
if [ "$status" -eq 0 ]; then
  # shellcheck disable=SC2288
  "{{PYTHON}}" "{{VAULT_PATH}}/.memoria/mcp/cron_heartbeat.py" --vault "{{VAULT_PATH}}" --job memoria-sweeps >/dev/null || true
fi
