#!/usr/bin/env bash
# Shared dispatcher for Memoria's deterministic Hermes cron jobs.
set -u

py="${MEMORIA_PYTHON:-}"
vault="${MEMORIA_VAULT:-}"
[ -n "$py" ] || py="{{PYTHON}}"
[ -n "$vault" ] || vault="{{VAULT_PATH}}"
job="${1:-}"
status=0

run_py() {
  "$py" "$@" >/dev/null || status=1
}

case "$job" in
  board-export)
    run_py "$vault/.memoria/mcp/board_export.py" --vault "$vault"
    heartbeat="memoria-board-export"
    ;;
  sweeps)
    run_py "$vault/.memoria/operations/cleanup/reconcile.py" --vault "$vault"
    heartbeat="memoria-sweeps"
    ;;
  worker)
    run_py -m memoria_vault.runtime.worker --vault "$vault" observe-pi-edits
    run_py -m memoria_vault.runtime.worker --vault "$vault" run-pending --limit 10
    heartbeat="memoria-worker"
    ;;
  lint)
    run_py "$vault/.memoria/operations/integrity/linter/detectors.py" --vault "$vault" --jsonl-out "$vault/system/logs/lint-findings.jsonl"
    run_py "$vault/.memoria/operations/integrity/linter/golden_restore.py" --vault "$vault" check
    run_py "$vault/.memoria/operations/integrity/linter/session_summary.py" --vault "$vault"
    run_py -m memoria_vault.runtime.worker --vault "$vault" integrity-sweep
    heartbeat="memoria-lint"
    ;;
  metrics)
    run_py "$vault/.memoria/mcp/metrics_aggregate.py" --vault "$vault"
    heartbeat="memoria-metrics"
    ;;
  eval)
    run_py "$vault/.memoria/operations/telemetry/eval/eval_score.py" --vault "$vault" --quarter previous
    run_py "$vault/.memoria/operations/telemetry/eval/eval_dispatch.py" --vault "$vault"
    heartbeat="memoria-eval"
    ;;
  retraction-refresh)
    run_py "$vault/.memoria/operations/integrity/retraction/retraction.py" --refresh
    run_py "$vault/.memoria/operations/integrity/retraction/retraction.py" --sweep --vault "$vault"
    heartbeat="memoria-retraction-refresh"
    ;;
  *)
    echo "unknown Memoria cron job: $job" >&2
    exit 2
    ;;
esac

if [ "$status" -eq 0 ]; then
  "$py" "$vault/.memoria/mcp/cron_heartbeat.py" --vault "$vault" --job "$heartbeat" >/dev/null || true
fi
exit "$status"
