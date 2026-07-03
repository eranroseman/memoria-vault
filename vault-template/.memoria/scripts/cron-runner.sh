#!/usr/bin/env bash
# Shared dispatcher for Memoria's deterministic scheduled jobs.
set -u

py="${MEMORIA_PYTHON:-}"
vault="${MEMORIA_VAULT:-}"
[ -n "$py" ] || py="{{PYTHON}}"
[ -n "$vault" ] || vault="{{VAULT_PATH}}"
export PYTHONPATH="$vault/.memoria:${PYTHONPATH:-}"
job="${1:-}"
status=0

run_py() {
  "$py" "$@" >/dev/null || status=1
}

case "$job" in
  sweeps)
    run_py -m memoria_vault.runtime.subsystems.cleanup.reconcile --vault "$vault"
    ;;
  worker)
    run_py -m memoria_vault.typer_cli workspace scan --workspace "$vault" --schedule-id worker-scan --json
    run_py -m memoria_vault.typer_cli workspace run --workspace "$vault" --schedule-id worker-drain --limit 10 --json
    ;;
  lint)
    run_py -m memoria_vault.runtime.subsystems.integrity.linter.detectors --vault "$vault" --jsonl-out "$vault/system/logs/lint-findings.jsonl"
    run_py -m memoria_vault.runtime.subsystems.integrity.linter.golden_restore --vault "$vault" check
    run_py -m memoria_vault.runtime.subsystems.integrity.linter.session_summary --vault "$vault"
    run_py -m memoria_vault.typer_cli workspace check --workspace "$vault" --schedule-id lint-integrity --json
    ;;
  eval)
    run_py -m memoria_vault.typer_cli eval run --workspace "$vault" --schedule-id eval-dispatch --json
    ;;
  retraction-refresh)
    run_py -m memoria_vault.runtime.subsystems.integrity.retraction.retraction --refresh
    run_py -m memoria_vault.runtime.subsystems.integrity.retraction.retraction --sweep --vault "$vault"
    ;;
  *)
    echo "unknown Memoria cron job: $job" >&2
    exit 2
    ;;
esac

exit "$status"
