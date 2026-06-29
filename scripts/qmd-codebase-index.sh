#!/usr/bin/env bash
# Build/refresh the repo-local qmd code-search index for coding agents.
#
#   bash scripts/qmd-codebase-index.sh           # BM25 index (instant); skips the embed
#   bash scripts/qmd-codebase-index.sh --embed    # also build vector embeddings (GPU if available)
#
# This indexes THIS repo into a PROJECT-LOCAL index at ./.qmd/ (gitignored) — it is a
# DEV tool, separate from the runtime/vault qmd (which the installer wires for ~/Memoria).
# Idempotent; safe to re-run. Uses the repo-pinned qmd from node_modules (run `npm install`
# first, or `bash scripts/dev-setup.sh`). Needs Node >=22.
#
# GPU: qmd auto-detects CUDA/Metal/Vulkan. Leave QMD_LLAMA_GPU unset for auto-selection.
# On Linux/WSL with an NVIDIA card you need the CUDA 13 runtime (libcudart.so.13 +
# libcublas.so.13); without it qmd prints "running on CPU (slow)" and still works.
set -eu

unset CDPATH
cd "$(dirname -- "$0")/.." || exit 1
ROOT="$PWD"
export XDG_CONFIG_HOME="$ROOT/.qmd/config"
export XDG_CACHE_HOME="$ROOT/.qmd/cache"
mkdir -p "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME"

note() { printf '  %s\n' "$1"; }
hdr()  { printf '\n==> %s\n' "$1"; }

EMBED=0
[ "${1:-}" = "--embed" ] && EMBED=1

# Resolve the REPO-LOCAL qmd (never the global/Hermes one): node_modules first, then npx.
if [ -x "$ROOT/node_modules/.bin/qmd" ]; then
  QMD="$ROOT/node_modules/.bin/qmd"
elif command -v npx >/dev/null 2>&1; then
  QMD="npx --no-install qmd"
else
  note "qmd not found — run 'npm install' (or scripts/dev-setup.sh) first. Skipping."
  exit 0
fi

# Collections: (name<TAB>path<TAB>glob-mask). The main tree skips hidden dirs by default,
# so the agent/CI guidance under .agents and .github are indexed as their own collections.
CODE_MASK='**/*.{md,py,sh,ps1,ts,tsx,js,jsx,yaml,yml,toml}'
COLLECTIONS="repo	.	$CODE_MASK
repo-agents	.agents	**/*.md
repo-github	.github	**/*.{md,yml,yaml}"

hdr "qmd repo code-search index (project-local ./.qmd/)"

# Project-local index: keep both qmd config and cache out of the global runtime stores.
if [ ! -f "$ROOT/.qmd/index.sqlite" ]; then
  $QMD init >/dev/null && note "initialized project-local index (./.qmd/)"
fi

# Serialize concurrent runs (manual invocations and the git hooks) so they never collide.
# Non-blocking: if a refresh is already in flight, skip — it already covers the current tree.
# A crash leaves the dir; clear a stale lock with: rmdir .qmd/.refresh.lock
LOCK="$ROOT/.qmd/.refresh.lock"
if ! mkdir "$LOCK" 2>/dev/null; then
  note "a refresh is already running — skipping (clear a stale lock: rmdir .qmd/.refresh.lock)"
  exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT INT TERM

existing="$($QMD collection list 2>/dev/null || true)"
printf '%s\n' "$COLLECTIONS" | while IFS="$(printf '\t')" read -r name path mask; do
  [ -n "$name" ] || continue
  [ -e "$ROOT/$path" ] || { note "skip $name ($path absent)"; continue; }
  if printf '%s' "$existing" | grep -q "^$name\b\|^$name "; then
    note "collection '$name' exists (refreshed below)"
  else
    $QMD collection add "$path" --name "$name" --mask "$mask" >/dev/null \
      && note "added collection '$name' ($path)"
  fi
done

hdr "Re-indexing (BM25, instant)"
$QMD update >/dev/null && note "BM25 index up to date"

if [ "$EMBED" -eq 1 ]; then
  hdr "Embedding vectors (GPU if available; first run downloads ~2GB of models)"
  $QMD embed --chunk-strategy auto || note "embed failed — re-run: bash scripts/qmd-codebase-index.sh --embed"
else
  note "(skipped vector embed — BM25 search works now; add --embed for semantic 'qmd query')"
fi

hdr "Ready"
note "keyword:  XDG_CONFIG_HOME=.qmd/config XDG_CACHE_HOME=.qmd/cache qmd search \"<terms>\""
note "semantic: XDG_CONFIG_HOME=.qmd/config XDG_CACHE_HOME=.qmd/cache qmd query \"<intent>\"   (needs --embed once)"
note "open:     XDG_CONFIG_HOME=.qmd/config XDG_CACHE_HOME=.qmd/cache qmd get <file>"
note "rebuild:  bash scripts/qmd-codebase-index.sh --embed"
