#!/usr/bin/env bash
# Opt-in live Hermes L2 smoke. This is intentionally outside required PR CI.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE="memoria-writer"
ARTIFACT="projects/l2-smoke/live-dispatch.md"
MODEL_PROVIDER="${MEMORIA_L2_MODEL_PROVIDER:-kilocode}"
MODEL_BASE_URL="${MEMORIA_L2_MODEL_BASE_URL:-${MEMORIA_MODEL_BASE_URL:-https://api.kilo.ai/api/gateway}}"
MODEL_NAME="${MEMORIA_L2_MODEL_NAME:-${MEMORIA_MODEL_NAME:-meta-llama/llama-4-scout}}"
MODEL_CONTEXT_LENGTH="${MEMORIA_L2_MODEL_CONTEXT_LENGTH:-${MEMORIA_MODEL_CONTEXT_LENGTH:-65536}}"
USE_SMOKE_MODEL="${MEMORIA_L2_USE_SMOKE_MODEL:-1}"
KEEP_TMP=0
RUN_LIVE=1

usage() {
  cat <<'EOF'
Usage: scripts/test-l2.sh [--help] [--preflight-only] [--keep-tmp]

Opt-in live Hermes L2 smoke for Memoria agent wiring. This is a manual/nightly
runtime check, not a required PR CI gate.

Prerequisites:
  - hermes on PATH with MCP support
  - Python runtime deps installed (src/.memoria/mcp/requirements.txt)
  - git on PATH
  - Kilo Code model access, an OpenAI-compatible endpoint override, or the
    built-in deterministic smoke endpoint used by default

Model defaults:
  MEMORIA_L2_USE_SMOKE_MODEL=1      # starts a local deterministic endpoint
  MEMORIA_L2_MODEL_PROVIDER=kilocode  # used when MEMORIA_L2_USE_SMOKE_MODEL=0
  MEMORIA_L2_MODEL_BASE_URL=https://api.kilo.ai/api/gateway
  MEMORIA_L2_MODEL_NAME=meta-llama/llama-4-scout
  MEMORIA_L2_MODEL_CONTEXT_LENGTH=65536

The smoke creates a disposable vault and temporary HERMES_HOME, installs a
minimal writer profile, replaces Obsidian's HTTPS MCP with a filesystem-backed
stdio shim, deploys the real memoria-policy-gate plugin, runs one
`hermes chat -q` dispatch, then asserts the written artifact and audit row.
Set MEMORIA_L2_USE_SMOKE_MODEL=0, or pass --real-model, to use Kilo or your
explicit endpoint override instead of the deterministic smoke backend.

Exit codes:
  0   passed
  1   failed after prerequisites were available
  77  skipped because runtime prerequisites were unavailable
EOF
}

skip() {
  printf 'SKIP: %s\n' "$*" >&2
  exit 77
}

while [ $# -gt 0 ]; do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --preflight-only) RUN_LIVE=0; shift ;;
    --keep-tmp) KEEP_TMP=1; shift ;;
    --real-model) USE_SMOKE_MODEL=0; shift ;;
    *) printf 'unknown option: %s\n\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

command -v hermes >/dev/null 2>&1 || skip "hermes is not on PATH"
command -v git >/dev/null 2>&1 || skip "git is not on PATH"
PYTHON_BIN="${PYTHON:-$(command -v python3 || command -v python || true)}"
[ -n "$PYTHON_BIN" ] || skip "python3/python is not on PATH"
"$PYTHON_BIN" - <<'PY' || skip "missing Python runtime deps; run python -m pip install -r src/.memoria/mcp/requirements.txt"
import mcp.server.fastmcp  # noqa: F401
import yaml  # noqa: F401
PY
TMPDIR_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/memoria-l2-smoke-XXXXXXXX")"
if [ "$KEEP_TMP" -eq 0 ]; then
  trap 'rm -rf "$TMPDIR_ROOT"' EXIT
else
  printf 'Keeping temp dir: %s\n' "$TMPDIR_ROOT"
fi

MODEL_PID=""
if [ "$USE_SMOKE_MODEL" -eq 1 ]; then
  MODEL_PROVIDER="custom"
  MODEL_NAME="memoria-l2-smoke"
  PORT_FILE="$TMPDIR_ROOT/model-url"
  "$PYTHON_BIN" "$ROOT/scripts/l2_openai_smoke_server.py" --port-file "$PORT_FILE" >"$TMPDIR_ROOT/model.log" 2>&1 &
  MODEL_PID="$!"
  for _ in 1 2 3 4 5; do
    [ -s "$PORT_FILE" ] && break
    sleep 0.2
  done
  [ -s "$PORT_FILE" ] || skip "deterministic smoke model endpoint did not start"
  MODEL_BASE_URL="$(cat "$PORT_FILE")"
fi

cleanup() {
  if [ -n "$MODEL_PID" ]; then
    kill "$MODEL_PID" >/dev/null 2>&1 || true
  fi
  if [ "$KEEP_TMP" -eq 0 ]; then
    rm -rf "$TMPDIR_ROOT"
  fi
}
trap cleanup EXIT

"$PYTHON_BIN" - "$MODEL_BASE_URL" <<'PY' || skip "model endpoint is unavailable: $MODEL_BASE_URL"
import sys
import urllib.error
import urllib.request

base = sys.argv[1].rstrip("/")
try:
    with urllib.request.urlopen(base + "/models", timeout=5) as response:
        if response.status >= 400:
            raise SystemExit(1)
except (OSError, urllib.error.URLError, TimeoutError):
    raise SystemExit(1)
PY

if [ "$RUN_LIVE" -eq 0 ]; then
  echo "L2 preflight passed"
  exit 0
fi

VAULT="$TMPDIR_ROOT/vault"
HERMES_TMP="$TMPDIR_ROOT/hermes"
PROFILE_STAGE="$TMPDIR_ROOT/profile"

"$PYTHON_BIN" "$ROOT/scripts/l2_smoke.py" prepare-vault --root "$ROOT" --vault "$VAULT"
git -C "$VAULT" init -q
git -C "$VAULT" config user.email "l2-smoke@example.invalid"
git -C "$VAULT" config user.name "Memoria L2 Smoke"
git -C "$VAULT" add .
git -C "$VAULT" commit -q -m "seed disposable vault"

"$PYTHON_BIN" "$ROOT/scripts/l2_smoke.py" write-profile \
  --profile-src "$ROOT/src/.memoria/profiles/memoria-writer" \
  --profile-stage "$PROFILE_STAGE" \
  --repo-root "$ROOT" \
  --vault "$VAULT" \
  --python "$PYTHON_BIN" \
  --provider "$MODEL_PROVIDER" \
  --model "$MODEL_NAME" \
  --base-url "$MODEL_BASE_URL" \
  --context-length "$MODEL_CONTEXT_LENGTH"

mkdir -p "$HERMES_TMP"
HERMES_HOME="$HERMES_TMP" hermes profile install "$PROFILE_STAGE" --name "$PROFILE" --force --yes >/dev/null
PROFILE_DIR="$HERMES_TMP/profiles/$PROFILE"
"$PYTHON_BIN" "$ROOT/scripts/l2_smoke.py" deploy-policy-plugin \
  --root "$ROOT" \
  --profile-dir "$PROFILE_DIR" \
  --profile "$PROFILE" \
  --vault "$VAULT"

AUDIT_BEFORE="$("$PYTHON_BIN" "$ROOT/scripts/l2_smoke.py" count-audit --vault "$VAULT")"
PROMPT=$(cat <<EOF
Use the Obsidian MCP tool to write exactly one file at $ARTIFACT.
The file content must be:
---
type: project
l2_live_smoke: true
---

# L2 live smoke

Hermes live dispatch reached the filesystem-backed Obsidian MCP shim.

Do not write any other files. After the tool call, reply only with L2_SMOKE_DONE.
EOF
)

echo "Running live Hermes dispatch with $MODEL_PROVIDER/$MODEL_NAME at $MODEL_BASE_URL"
OPENAI_API_KEY="${MEMORIA_L2_API_KEY:-dummy}" \
HERMES_HOME="$HERMES_TMP" \
PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" \
  hermes -p "$PROFILE" chat --quiet --provider "$MODEL_PROVIDER" --model "$MODEL_NAME" \
    --max-turns 8 -q "$PROMPT"

"$PYTHON_BIN" "$ROOT/scripts/l2_smoke.py" assert-smoke \
  --vault "$VAULT" \
  --artifact "$ARTIFACT" \
  --audit-before "$AUDIT_BEFORE"

echo "L2 live Hermes smoke PASS"
