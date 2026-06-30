#!/usr/bin/env bash
# Disposable full-install smoke for the local Memoria test vault.
#
# The target root may contain tool-managed mounts, so the actual vault defaults
# to ~/Memoria-test/vault and that subdirectory is wiped on every run.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_ROOT="${MEMORIA_TEST_ROOT:-$HOME/Memoria-test}"
VAULT="${MEMORIA_TEST_VAULT:-$TEST_ROOT/vault}"
BASE_URL="${MEMORIA_TEST_LLM_BASE_URL:-http://127.0.0.1:11434/v1}"
MODEL="${MEMORIA_TEST_LLM_MODEL:-memoria-qwen2.5:7b-64k}"
CONTEXT="${MEMORIA_TEST_LLM_CONTEXT:-65536}"
RUN_LIVE_LLM=1
CRON_IDS_TO_RESUME=""

say() { printf '%s\n' "$*"; }
hdr() { printf '\n== %s ==\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<'EOF'
Usage: scripts/install-test-vault-local-llm.sh [options]

Rebuild the disposable Memoria test vault, wire Hermes profiles to a local
OpenAI-compatible LLM endpoint, and run the package/golden/detector/L2 checks.

Options:
  --root DIR        Disposable test root (default: ~/Memoria-test)
  --vault DIR       Actual vault path; must be below --root (default: DIR/vault)
  --base-url URL    OpenAI-compatible endpoint (default: http://127.0.0.1:11434/v1)
  --model NAME      Local model name (default: memoria-qwen2.5:7b-64k)
  --context N       Model context length (default: 65536)
  --skip-live-llm   Rebuild and verify the install, but skip the real-model L2 smoke
  -h, --help        Show this help

Environment overrides mirror the flags:
  MEMORIA_TEST_ROOT, MEMORIA_TEST_VAULT, MEMORIA_TEST_LLM_BASE_URL,
  MEMORIA_TEST_LLM_MODEL, MEMORIA_TEST_LLM_CONTEXT
EOF
}

expand_path() {
  case "$1" in
    "~") printf '%s\n' "$HOME" ;;
    "~"/*) printf '%s/%s\n' "$HOME" "${1#~/}" ;;
    *) printf '%s\n' "$1" ;;
  esac
}

run() {
  printf '  +'
  printf ' %q' "$@"
  printf '\n'
  "$@"
}

need() {
  command -v "$1" >/dev/null 2>&1 || die "$1 is required on PATH"
}

pause_memoria_crons() {
  command -v hermes >/dev/null 2>&1 || return 0
  CRON_IDS_TO_RESUME="$(
    hermes cron list 2>/dev/null | awk '
      /^[[:space:]]+[0-9a-f]+ \[active\]/ { id = $1; active = 1; next }
      /^[[:space:]]+[0-9a-f]+ \[/ { id = ""; active = 0; next }
      /^[[:space:]]+Name:[[:space:]]+memoria-/ && active { print id }
    '
  )" || return 0
  [ -n "$CRON_IDS_TO_RESUME" ] || return 0
  hdr "Pause Memoria crons"
  local id
  for id in $CRON_IDS_TO_RESUME; do
    run hermes cron pause "$id" || true
  done
}

resume_memoria_crons() {
  [ -n "$CRON_IDS_TO_RESUME" ] || return 0
  hdr "Resume Memoria crons"
  local id
  for id in $CRON_IDS_TO_RESUME; do
    run hermes cron resume "$id" || true
  done
  CRON_IDS_TO_RESUME=""
}

models_url() {
  case "$BASE_URL" in
    */v1) printf '%s/models\n' "$BASE_URL" ;;
    */v1/) printf '%smodels\n' "$BASE_URL" ;;
    *) printf '%s/v1/models\n' "${BASE_URL%/}" ;;
  esac
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --root)
      [ "$#" -ge 2 ] || die "--root needs a directory"
      TEST_ROOT="$(expand_path "$2")"
      if [ -z "${MEMORIA_TEST_VAULT:-}" ]; then
        VAULT="$TEST_ROOT/vault"
      fi
      shift 2
      ;;
    --vault)
      [ "$#" -ge 2 ] || die "--vault needs a directory"
      VAULT="$(expand_path "$2")"
      shift 2
      ;;
    --base-url)
      [ "$#" -ge 2 ] || die "--base-url needs a URL"
      BASE_URL="$2"
      shift 2
      ;;
    --model)
      [ "$#" -ge 2 ] || die "--model needs a model name"
      MODEL="$2"
      shift 2
      ;;
    --context)
      [ "$#" -ge 2 ] || die "--context needs a value"
      CONTEXT="$2"
      shift 2
      ;;
    --skip-live-llm)
      RUN_LIVE_LLM=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

TEST_ROOT="$(expand_path "$TEST_ROOT")"
VAULT="$(expand_path "$VAULT")"

[ -d "$ROOT/vault-template/.memoria" ] || die "cannot find vault-template/.memoria under $ROOT"
case "$VAULT" in
  "$TEST_ROOT"/*) ;;
  *) die "--vault must be below --root; refusing to wipe $VAULT" ;;
esac
[ "$VAULT" != "$TEST_ROOT" ] || die "--vault must be a child of --root, not the root itself"
[ "$VAULT" != "$HOME" ] || die "refusing to use HOME as the disposable vault"
[ "$VAULT" != "/" ] || die "refusing to use / as the disposable vault"

need curl
need git
trap resume_memoria_crons EXIT

if [ "$RUN_LIVE_LLM" -eq 1 ]; then
  hdr "Local LLM preflight"
  run curl -fsS --max-time 5 "$(models_url)" >/dev/null
fi

pause_memoria_crons

hdr "Rebuild disposable vault"
run mkdir -p "$TEST_ROOT"
run rm -rf "$VAULT"
run mkdir -p "$VAULT"
run git -C "$VAULT" init -q
run git -C "$VAULT" branch -M main
run git -C "$VAULT" config user.email memoria-test@example.invalid
run git -C "$VAULT" config user.name "Memoria Test"

hdr "Full installer"
run env \
  MEMORIA_ENV=test \
  MEMORIA_MODEL_PROVIDER=custom \
  MEMORIA_MODEL_BASE_URL="$BASE_URL" \
  MEMORIA_MODEL_NAME="$MODEL" \
  MEMORIA_MODEL_CONTEXT_LENGTH="$CONTEXT" \
  bash "$ROOT/scripts/install.sh" --vault "$VAULT" --no-apps --yes

hdr "Baseline commit"
run git -C "$VAULT" add -A
run git -C "$VAULT" commit -qm "Initial Memoria test vault"
resume_memoria_crons

PY="$VAULT/.memoria/.venv/bin/python"
[ -x "$PY" ] || die "installed venv python not found: $PY"

hdr "Install checks"
run "$PY" -c "import memoria_vault; print(memoria_vault.__version__)"
run "$PY" "$VAULT/.memoria/operations/integrity/linter/golden_restore.py" --vault "$VAULT" check
verdict="$("$PY" "$VAULT/.memoria/operations/integrity/linter/detectors.py" --vault "$VAULT" | tail -1)"
say "  detectors: $verdict"
case "$verdict" in
  *"verdict: PASS"*) ;;
  *) die "fresh installed vault detectors were not clean: $verdict" ;;
esac

hdr "Profile checks"
run hermes profile list
run hermes cron list

if [ "$RUN_LIVE_LLM" -eq 1 ]; then
  hdr "L2 real-model smoke"
  l2_smoke() {
    run env \
      MEMORIA_L2_USE_SMOKE_MODEL=0 \
      MEMORIA_L2_MODEL_PROVIDER=custom \
      MEMORIA_L2_MODEL_BASE_URL="$BASE_URL" \
      MEMORIA_L2_MODEL_NAME="$MODEL" \
      MEMORIA_L2_MODEL_CONTEXT_LENGTH="$CONTEXT" \
      OPENAI_API_KEY="${OPENAI_API_KEY:-dummy}" \
      bash "$ROOT/scripts/test-l2.sh" --real-model
  }
  if ! l2_smoke; then
    say "  L2 real-model smoke failed once; retrying."
    l2_smoke
  fi
fi

hdr "Done"
say "Disposable Memoria install verified at $VAULT"
