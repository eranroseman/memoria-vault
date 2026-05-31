#!/usr/bin/env bash
# Memoria installer (macOS / Linux / WSL2) -- set up the seven Hermes profiles
# from this vault. POSIX port of install.ps1.
#
# Idempotent: always overwrites profile directories under
# ~/.hermes/profiles/memoria-*/ from the source in .memoria/profiles/. Preserves
# human-owned .env files. Gracefully skips profiles whose source is incomplete.
# Substitutes {{VAULT_PATH}} in each profile's mcp.json + config.yaml (the policy
# server command + the pre/post_tool_call hook command) before installing.
#
# Usage:
#   ./install.sh                            install all seven profiles
#   ./install.sh --only memoria-linter      install only the listed profiles (comma-separated)
#   ./install.sh --skip-hermes-check        skip the hermes-on-PATH check
#   ./install.sh --skip-python-check        skip the python check
#
# Honors $HERMES_HOME (default ~/.hermes), matching Hermes's own convention.
set -euo pipefail

# ---------------------------------------------------------------------------
# Args
# ---------------------------------------------------------------------------
ONLY=""
SKIP_HERMES=0
SKIP_PYTHON=0
while [ $# -gt 0 ]; do
  case "$1" in
    --only) ONLY="${2:-}"; shift 2 ;;
    --only=*) ONLY="${1#*=}"; shift ;;
    --skip-hermes-check) SKIP_HERMES=1; shift ;;
    --skip-python-check) SKIP_PYTHON=1; shift ;;
    -h|--help) sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
VAULT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MEMORIA_PATH="$VAULT_PATH/.memoria"
PROFILES_SRC="$MEMORIA_PATH/profiles"
MCP_REQS="$MEMORIA_PATH/mcp/requirements.txt"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
HERMES_PROFILES_DIR="$HERMES_HOME/profiles"

ALL_PROFILES="memoria-librarian memoria-mapper memoria-socratic memoria-writer memoria-verifier memoria-coder memoria-linter"
# Minimum file set hermes profile install requires.
REQUIRED_FILES="SOUL.md config.yaml mcp.json distribution.yaml"

# Resolve targets (explicit if/then -- a short-circuit && would trip `set -e`).
TARGETS=""
if [ -n "$ONLY" ]; then
  ONLY_LIST="$(echo "$ONLY" | tr ',' ' ')"
  for p in $ALL_PROFILES; do
    for o in $ONLY_LIST; do
      if [ "$p" = "$o" ]; then TARGETS="$TARGETS $p"; fi
    done
  done
else
  TARGETS="$ALL_PROFILES"
fi

echo "Memoria installer"
echo "  Vault path:  $VAULT_PATH"
echo "  Hermes home: $HERMES_PROFILES_DIR"
echo "  Targets:    $TARGETS"
echo

# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------
if [ "$SKIP_HERMES" -eq 0 ]; then
  if ! command -v hermes >/dev/null 2>&1; then
    echo "[X] Hermes not found on PATH." >&2
    echo "    Install: https://hermes-agent.nousresearch.com/docs/getting-started/installation" >&2
    echo "    If Hermes is installed but not on PATH, re-run with --skip-hermes-check." >&2
    exit 1
  fi
  echo "[OK] Hermes found at $(command -v hermes)"
fi

PYTHON=""
if command -v python3 >/dev/null 2>&1; then PYTHON=python3
elif command -v python >/dev/null 2>&1; then PYTHON=python; fi

if [ "$SKIP_PYTHON" -eq 0 ]; then
  if [ -z "$PYTHON" ]; then
    echo "[X] Python not found on PATH. Required for the MCP servers." >&2
    echo "    If you don't need MCP servers yet, re-run with --skip-python-check." >&2
    exit 1
  fi
  echo "[OK] Python found: $("$PYTHON" --version 2>&1)"
fi

# ---------------------------------------------------------------------------
# MCP dependencies (skipped gracefully if requirements.txt isn't present)
# ---------------------------------------------------------------------------
if [ -f "$MCP_REQS" ]; then
  if [ -n "$PYTHON" ]; then
    echo
    echo "Installing MCP server dependencies from .memoria/mcp/requirements.txt..."
    if "$PYTHON" -m pip install --quiet -r "$MCP_REQS"; then
      echo "[OK] MCP dependencies installed"
    else
      echo "[X] pip install failed." >&2
      exit 1
    fi
  else
    echo "[!] Python unavailable; skipped MCP dependency install." >&2
  fi
else
  echo
  echo "[!] No requirements.txt at $MCP_REQS -- MCP install skipped." >&2
fi

# ---------------------------------------------------------------------------
# Stage + install each target profile
# ---------------------------------------------------------------------------
STAGING="$(mktemp -d "${TMPDIR:-/tmp}/memoria-staging-XXXXXXXX")"
cleanup() { rm -rf "$STAGING"; }
trap cleanup EXIT

installed=""
skipped=""

for p in $TARGETS; do
  src="$PROFILES_SRC/$p"
  if [ ! -d "$src" ]; then
    skipped="$skipped
    [-] $p: source directory missing at $src"
    continue
  fi

  missing=""
  for f in $REQUIRED_FILES; do
    if [ ! -f "$src/$f" ]; then missing="$missing $f"; fi
  done
  if [ -n "$missing" ]; then
    skipped="$skipped
    [-] $p: incomplete source -- missing:$missing"
    continue
  fi

  echo
  echo "Staging $p..."
  dst="$STAGING/$p"
  cp -R "$src" "$dst"

  # Substitute {{VAULT_PATH}} in the files that reference the vault by absolute
  # path: mcp.json (MCP server commands) and config.yaml (policy-gate hook).
  # On POSIX the path is already forward-slash, so no conversion is needed.
  for fname in mcp.json config.yaml; do
    f="$dst/$fname"
    if [ -f "$f" ]; then
      sed "s|{{VAULT_PATH}}|$VAULT_PATH|g" "$f" > "$f.tmp" && mv "$f.tmp" "$f"
    fi
  done

  echo "Installing $p..."
  if hermes profile install "$dst" --alias "$p" --force --yes; then
    installed="$installed $p"
    # Bootstrap .env from .env.EXAMPLE on first install only (never clobber creds).
    envExample="$HERMES_PROFILES_DIR/$p/.env.EXAMPLE"
    envFile="$HERMES_PROFILES_DIR/$p/.env"
    if [ -f "$envExample" ] && [ ! -f "$envFile" ]; then
      cp "$envExample" "$envFile"
      echo "  Created .env from .env.EXAMPLE (fill in real values)"
    fi
  else
    skipped="$skipped
    [-] $p: hermes profile install failed"
  fi
done

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
count=0
for p in $installed; do count=$((count + 1)); done

echo
echo "=== Install summary ==="
echo "  Installed: $count"
for p in $installed; do echo "    [+] $p"; done
if [ -n "$skipped" ]; then
  echo "  Skipped:$skipped"
fi

if [ "$count" -eq 0 ]; then
  echo
  echo "No profiles installed. Ensure each profile ships SOUL.md + config.yaml +"
  echo "mcp.json + distribution.yaml, then re-run."
  exit 0
fi

first="$(echo "$installed" | awk '{print $1}')"
echo
echo "Next steps:"
echo "  1. Fill in credentials in each installed profile's .env file:"
for p in $installed; do echo "       $HERMES_PROFILES_DIR/$p/.env"; done
echo "  2. Open this folder in Obsidian as your vault:"
echo "       $VAULT_PATH"
echo "  3. Try a session:"
echo "       hermes -p $first chat"
echo
echo "Re-run after 'git pull' to refresh installed profiles. Author-owned files"
echo "(SOUL.md, config.yaml, mcp.json, skills/, cron/) are overwritten; .env is preserved."
