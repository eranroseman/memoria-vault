#!/usr/bin/env bash
# Fast local refresh for the disposable ~/memoria-vault/sandbox/vault workspace.
# cspell:words pathlib
#
# This updates source-owned vault files from vault-template/ without doing a fresh install.
# It preserves runtime state (.git, venv, logs, exports) and refreshes the golden
# copy so drift checks match the new source.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VAULT="$HOME/memoria-vault/sandbox/vault"
DRY_RUN=0

say() { printf '%s\n' "$*"; }
hdr() { printf '\n== %s ==\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<'EOF'
Usage: scripts/refresh-test-vault.sh [--vault DIR] [--dry-run]

Fast-refresh an existing disposable Memoria test vault from vault-template/.

Options:
  --vault DIR                 Target vault (default: ~/memoria-vault/sandbox/vault)
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

SRC="$ROOT/vault-template"
[ -d "$SRC/.memoria" ] || die "cannot find vault-template/.memoria under $ROOT"
[ -d "$VAULT/.memoria" ] || die "$VAULT is not an existing Memoria vault; run scripts/install.sh first"
need rsync

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
  .memoria/plugins \
  .memoria/schemas \
  .memoria/scripts \
  spaces \
  system/dashboards \
  system/eval \
  system/patterns \
  system/templates
do
  sync_dir "$rel"
done

for rel in \
  .memoria/design-system.md \
  .gitignore \
  AGENTS.md \
  home.md \
  _nav.md \
  index.md \
  steering.md \
  troubleshooting.md \
  catalog/index.md \
  knowledge/index.md \
  knowledge/_views/index.md \
  references.bib \
  system/vocabulary.md
do
  sync_file "$rel"
done

hdr "Remove dropped standalone baseline payloads"
run rm -rf "$VAULT/.obsidian" "$VAULT/system/scripts" "$VAULT/catalog/catalog.base"

hdr "Wire git hook"
if [ -d "$VAULT/.git" ] && [ -f "$VAULT/.githooks/pre-commit" ]; then
  run mkdir -p "$VAULT/.git/hooks"
  run cp "$VAULT/.githooks/pre-commit" "$VAULT/.git/hooks/pre-commit"
  run chmod +x "$VAULT/.git/hooks/pre-commit"
fi

hdr "Ensure empty-folder skeleton"
python_cmd="python3"
if [ -x "$VAULT/.memoria/.venv/bin/python" ]; then
  python_cmd="$VAULT/.memoria/.venv/bin/python"
fi
PYTHONPATH_VALUE="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
run env PYTHONPATH="$PYTHONPATH_VALUE" "$python_cmd" - "$VAULT" <<'PY'
import sys
from pathlib import Path

import yaml

vault = Path(sys.argv[1])
folders = yaml.safe_load((vault / ".memoria/schemas/folders.yaml").read_text(encoding="utf-8"))
for rel in folders.get("skeleton", []):
    (vault / rel).mkdir(parents=True, exist_ok=True)
PY

hdr "Done"
say "Refreshed $VAULT from $SRC"
