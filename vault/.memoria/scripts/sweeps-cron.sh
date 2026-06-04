#!/usr/bin/env bash
# Re-ingest sweeps cron (ADR-30). Runs the two deterministic backstops:
#   (a) reconcile — capture-intake.jsonl entries with no note on disk
#   (b) retry     — `captured` notes stuck at ingest_status: tier0
# Each is a detector that enqueues an *idempotent* re-ingest card
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
# shellcheck disable=SC2288  # {{PYTHON}} is a template placeholder, substituted at install time
"{{PYTHON}}" "{{VAULT_PATH}}/.memoria/profiles/memoria-librarian/skills/obsidian-paper-note/scripts/sweeps.py" --vault "{{VAULT_PATH}}" >/dev/null || true
