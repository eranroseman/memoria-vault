#!/usr/bin/env bash
# Disposable standalone-install smoke for the local Memoria test workspace.
#
# The target root may contain tool-managed mounts, so the actual workspace
# defaults to ~/memoria-vault/sandbox/vault and that child directory is wiped on every run.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_ROOT="${MEMORIA_TEST_ROOT:-$HOME/memoria-vault/sandbox}"
VAULT="${MEMORIA_TEST_VAULT:-$TEST_ROOT/vault}"
BASE_URL="${MEMORIA_TEST_LLM_BASE_URL:-http://127.0.0.1:11434/v1}"
MODEL="${MEMORIA_TEST_LLM_MODEL:-memoria-qwen2.5:7b-64k}"
CHECK_LOCAL_LLM=0

say() { printf '%s\n' "$*"; }
hdr() { printf '\n== %s ==\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<'EOF'
Usage: scripts/sandbox/install-test-vault-local-llm.sh [options]

Rebuild the disposable Memoria test workspace and run the standalone installer,
package, detector, and CLI doctor checks. The optional local-LLM
check only verifies that an OpenAI-compatible endpoint is reachable; alpha.15
does not install Hermes profiles or drive a Hermes dispatch.

Options:
  --root DIR          Disposable test root (default: ~/memoria-vault/sandbox)
  --vault DIR         Actual workspace path; must be below --root (default: DIR/vault)
  --check-local-llm   Check the configured OpenAI-compatible endpoint
  --base-url URL      Endpoint used by --check-local-llm (default: http://127.0.0.1:11434/v1)
  --model NAME        Model label printed with --check-local-llm
  -h, --help          Show this help

Environment overrides mirror the flags:
  MEMORIA_TEST_ROOT, MEMORIA_TEST_VAULT, MEMORIA_TEST_LLM_BASE_URL,
  MEMORIA_TEST_LLM_MODEL
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
    --check-local-llm)
      CHECK_LOCAL_LLM=1
      shift
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
[ "$VAULT" != "$HOME" ] || die "refusing to use HOME as the disposable workspace"
[ "$VAULT" != "/" ] || die "refusing to use / as the disposable workspace"

need git

if [ "$CHECK_LOCAL_LLM" -eq 1 ]; then
  need curl
  hdr "Local LLM preflight"
  say "  endpoint: $BASE_URL"
  say "  model: $MODEL"
  run curl -fsS --max-time 5 "$(models_url)" >/dev/null
fi

hdr "Rebuild disposable workspace"
run mkdir -p "$TEST_ROOT"
run rm -rf "$VAULT"
run mkdir -p "$VAULT"
run git -C "$VAULT" init -q
run git -C "$VAULT" branch -M main
run git -C "$VAULT" config user.email memoria-test@example.invalid
run git -C "$VAULT" config user.name "Memoria Test"

hdr "Standalone installer"
run env MEMORIA_ENV=test bash "$ROOT/scripts/install.sh" --vault "$VAULT" --yes

hdr "Baseline commit"
run git -C "$VAULT" add -A
run git -C "$VAULT" commit -qm "Initial Memoria test workspace"

PY="$VAULT/.memoria/.venv/bin/python"
[ -x "$PY" ] || die "installed venv python not found: $PY"

hdr "Install checks"
run "$PY" -c "import memoria_vault; print(memoria_vault.__version__)"
run "$PY" -m memoria_vault.cli doctor bundle --workspace "$VAULT" --json
verdict="$("$PY" -m memoria_vault.runtime.subsystems.integrity.linter.detectors --vault "$VAULT" | tail -1)"
say "  detectors: $verdict"
case "$verdict" in
  *"verdict: PASS"*) ;;
  *) die "fresh installed workspace detectors were not clean: $verdict" ;;
esac

hdr "Done"
say "Disposable Memoria standalone install verified at $VAULT"
