#!/usr/bin/env bash
# Fast local refresh for the disposable ~/Memoria-test sandbox.
# cspell:words pathlib
#
# This updates source-owned vault files from vault-template/ without doing a fresh install.
# It preserves runtime state (.git, venv, logs, exports, local Obsidian plugin
# secrets) and refreshes the golden copy so drift checks match the new source.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VAULT="$HOME/Memoria-test"
PROFILES="auto"
DRY_RUN=0

say() { printf '%s\n' "$*"; }
hdr() { printf '\n== %s ==\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<'EOF'
Usage: scripts/refresh-test-vault.sh [--vault DIR] [--profiles auto|always|never] [--dry-run]

Fast-refresh an existing disposable Memoria test vault from vault-template/.

Options:
  --vault DIR                 Target vault (default: ~/Memoria-test)
  --profiles auto|always|never
                              Redeploy Hermes profiles only when profile-owned
                              source changed, always, or never (default: auto)
  --dry-run                   Print the actions without writing
  -h, --help                  Show this help

This is for local UI/workflow iteration. Use scripts/install.sh for a fresh
installer validation.
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
  [ "$DRY_RUN" -eq 1 ] || "$@"
}

run_env() {
  local assignment="$1"
  shift
  printf '  + %s' "$assignment"
  printf ' %q' "$@"
  printf '\n'
  if [ "$DRY_RUN" -eq 0 ]; then
    env "$assignment" "$@"
  fi
}

need() {
  command -v "$1" >/dev/null 2>&1 || die "$1 is required on PATH"
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --vault)
      [ "$#" -ge 2 ] || die "--vault needs a directory"
      VAULT="$(expand_path "$2")"
      shift 2
      ;;
    --profiles)
      [ "$#" -ge 2 ] || die "--profiles needs auto, always, or never"
      PROFILES="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
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

case "$PROFILES" in
  auto|always|never) ;;
  *) die "--profiles must be auto, always, or never" ;;
esac

SRC="$ROOT/vault-template"
[ -d "$SRC/.memoria" ] || die "cannot find vault-template/.memoria under $ROOT"
[ -d "$VAULT/.memoria" ] || die "$VAULT is not an existing Memoria vault; run scripts/install.sh first"
need rsync

profiles_need_refresh=0
if [ "$PROFILES" = "always" ]; then
  profiles_need_refresh=1
elif [ "$PROFILES" = "auto" ]; then
  for rel in .memoria/profiles .memoria/lane-overrides .memoria/plugins .memoria/scripts; do
    if [ ! -e "$VAULT/$rel" ] || ! diff -qr "$SRC/$rel" "$VAULT/$rel" >/dev/null 2>&1; then
      profiles_need_refresh=1
      break
    fi
  done
fi

sync_dir() {
  local rel="$1"
  run mkdir -p "$VAULT/$rel"
  run rsync -a --delete "$SRC/$rel"/ "$VAULT/$rel"/
}

sync_file() {
  local rel="$1"
  run mkdir -p "$(dirname "$VAULT/$rel")"
  run rsync -a "$SRC/$rel" "$VAULT/$rel"
}

hdr "Refresh source-owned vault files"
# Runtime content is preserved by omission: this script never syncs system/logs,
# system/exports, notes, project content, catalog records, or inbox cards.
for rel in \
  .githooks \
  .memoria/lane-overrides \
  .memoria/mcp \
  .memoria/operations \
  .memoria/plugins \
  .memoria/profiles \
  .memoria/samples \
  .memoria/schemas \
  .memoria/scripts \
  spaces \
  system/dashboards \
  system/eval \
  system/patterns \
  system/scripts \
  system/templates \
  system/worklists
do
  sync_dir "$rel"
done

for rel in \
  .memoria/design-system.md \
  .memoria/project-hints.yaml.example \
  .memoria/tool-registry.yaml \
  .gitignore \
  AGENTS.md \
  home.md \
  _nav.md \
  research-focus.md \
  troubleshooting.md \
  catalog/catalog.base \
  inbox/inbox.base \
  notes/hubs/hubs.base \
  projects/projects.base \
  system/board/board.base \
  system/vocabulary.md
do
  sync_file "$rel"
done

run mkdir -p "$VAULT/.obsidian"
run rsync -a --delete \
  --exclude '/plugins/agent-client/data.json' \
  --exclude '/plugins/obsidian-local-rest-api/data.json' \
  --exclude '/plugins/obsidian-local-rest-api/*.crt' \
  --exclude '/plugins/obsidian-local-rest-api/*.key' \
  --exclude '/plugins/obsidian-local-rest-api/*.pem' \
  "$SRC/.obsidian"/ "$VAULT/.obsidian"/

hdr "Ensure empty-folder skeleton"
python_cmd="python3"
if [ -x "$VAULT/.memoria/.venv/bin/python" ]; then
  python_cmd="$VAULT/.memoria/.venv/bin/python"
fi
run "$python_cmd" - "$VAULT" <<'PY'
import sys
from pathlib import Path

import yaml

vault = Path(sys.argv[1])
folders = yaml.safe_load((vault / ".memoria/schemas/folders.yaml").read_text(encoding="utf-8"))
for rel in folders.get("skeleton", []):
    (vault / rel).mkdir(parents=True, exist_ok=True)
PY

hdr "Restage golden copy"
run "$python_cmd" "$VAULT/.memoria/operations/integrity/linter/golden_restore.py" --vault "$VAULT" stage

case "$PROFILES" in
  always)
    hdr "Redeploy profiles"
    run_env "MEMORIA_ENV=${MEMORIA_ENV:-test}" bash "$ROOT/scripts/install.sh" --profiles-only --yes --vault "$VAULT"
    ;;
  auto)
    if [ "$profiles_need_refresh" -eq 1 ]; then
      hdr "Redeploy profiles"
      run_env "MEMORIA_ENV=${MEMORIA_ENV:-test}" bash "$ROOT/scripts/install.sh" --profiles-only --yes --vault "$VAULT"
    else
      say "Profiles unchanged; skipping profiles-only redeploy."
    fi
    ;;
  never)
    say "Profile redeploy skipped by --profiles never."
    ;;
esac

hdr "Done"
say "Refreshed $VAULT from $SRC"
