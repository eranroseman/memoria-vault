#!/usr/bin/env bash
# e2e-smoke.sh — the offline end-to-end gate. It keeps the historic CI entrypoint
# while naming the checks by the clean testing-system behavior they prove:
# vault-assembly -> commit-gate -> offline-ingest -> workflow-replay -> final-integrity.
# Pure-local: no Hermes, no network. The cluster-graph step runs only if networkx is installed.
#
# Usage: bash scripts/e2e-smoke.sh   (exit 0 = gate green)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
V="$(mktemp -d "${TMPDIR:-/tmp}/memoria-e2e-XXXXXXXX")"
# Teardown must not fail the gate: git's background `gc --auto` can still be
# writing into "$V/.git" when the EXIT trap fires, making `rm -rf` exit non-zero
# ("Directory not empty") even after all gates pass. The temp dir is ephemeral,
# so swallow cleanup errors rather than failing the run under `set -e`.
trap 'rm -rf "$V" 2>/dev/null || true' EXIT
PY="${PYTHON:-python3}"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
fail() { echo "e2e-smoke: FAIL — $1" >&2; exit 1; }
HELPER="$ROOT/scripts/e2e_smoke.py"
stage() { "$PY" "$HELPER" stage-label "$1"; }

require_git() {
  command -v git >/dev/null 2>&1 || fail "git is required for vault-assembly and commit-gate checks"
}

assert_executable() {
  "$PY" "$HELPER" executable "$1" "$2" || fail "$2 is missing or not executable: $1"
}

vault_assembly() {
  echo "== $(stage vault-assembly-1) =="
  require_git
  if command -v rsync >/dev/null; then rsync -a --exclude '.git' "$ROOT/vault-template/" "$V/"; else cp -R "$ROOT/vault-template/." "$V/"; fi
  "$PY" "$HELPER" vault-skeleton "$ROOT" "$V"

  echo "== $(stage vault-assembly-2) =="
  "$PY" -m memoria_vault.runtime.subsystems.integrity.linter.golden_restore --vault "$V" stage
  git -C "$V" init -q
  git -C "$V" config user.email "e2e@example.invalid"
  git -C "$V" config user.name "Memoria E2E Smoke"
  git -C "$V" rev-parse --is-inside-work-tree >/dev/null || fail "disposable vault is not a git repository"
  cp "$V/.githooks/pre-commit" "$V/.git/hooks/pre-commit" && chmod +x "$V/.git/hooks/pre-commit"
  assert_executable "$V/.git/hooks/pre-commit" "pre-commit hook"
  "$PY" "$HELPER" no-obsidian-bundle "$V"

  echo "== $(stage vault-assembly-3) =="
  "$PY" -m memoria_vault.runtime.subsystems.integrity.linter.detectors --vault "$V" | tail -1 | grep -q "PASS" || fail "detectors not clean on the fresh vault"
  "$PY" -m memoria_vault.runtime.subsystems.integrity.linter.golden_restore --vault "$V" check || fail "golden drift on a fresh vault"
}

commit_gate() {
  echo "== $(stage commit-gate) =="
  git -C "$V" rev-parse --is-inside-work-tree >/dev/null || fail "commit-gate requires a git repository"
  assert_executable "$V/.git/hooks/pre-commit" "pre-commit hook"
  git -C "$V" add -A
  git -C "$V" -c user.email=e2e@ci -c user.name=e2e commit -qm init || fail "baseline commit blocked"
  printf -- '---\ntype: note\ntitle: "Bad"\n---\nx\n' > "$V/knowledge/notes/bad.md"
  git -C "$V" add knowledge/notes/bad.md
  if git -C "$V" -c user.email=e2e@ci -c user.name=e2e commit -qm bad 2>/dev/null; then
    fail "the gate let a malformed note through"
  fi
  echo "   malformed note blocked at commit"
  git -C "$V" reset -q HEAD knowledge/notes/bad.md && rm "$V/knowledge/notes/bad.md"
  printf -- '---\ntype: note\nid: 01ARZ3NDEKTSV4RRFFQ69G5FAV\ntags: []\nlinks: {}\ntitle: "Good"\n---\nBody.\n' > "$V/knowledge/notes/good.md"
  git -C "$V" add knowledge/notes/good.md
  git -C "$V" -c user.email=e2e@ci -c user.name=e2e commit -qm good || fail "valid note blocked"
  echo "   valid note passes"
}

offline_ingest() {
  echo "== $(stage offline-ingest-1) =="
  "$PY" "$HELPER" offline-ingest "$ROOT" "$V"

  echo "== $(stage offline-ingest-2) =="
  "$PY" "$HELPER" typed-graph "$ROOT" "$V"
}

workflow_replay() {
  echo "== $(stage workflow-replay) =="
  "$PY" "$ROOT/scripts/test_env_harness.py" replay --root "$ROOT" --vault "$V" >/dev/null \
    || fail "test-env harness replay failed"
  "$PY" "$HELPER" workflow-artifacts "$V"
  echo "   cassette replay reached the model-free package-gate path"
}

final_integrity() {
  echo "== $(stage final-integrity) =="
  verdict=$("$PY" -m memoria_vault.runtime.subsystems.integrity.linter.detectors --vault "$V" | tail -1)
  echo "   $verdict"
  "$PY" "$HELPER" final-verdict "$verdict" || fail "worked vault verdict: $verdict"
  "$PY" -m memoria_vault.runtime.subsystems.integrity.linter.golden_restore --vault "$V" check || fail "golden drift after the loop"
}

vault_assembly
commit_gate
offline_ingest
workflow_replay
final_integrity

echo "e2e-smoke: ✅ all gates green"
