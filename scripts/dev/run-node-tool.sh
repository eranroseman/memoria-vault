#!/usr/bin/env bash
set -eu

if [ "$#" -lt 1 ]; then
  printf 'usage: %s <tool> [args...]\n' "$0" >&2
  exit 2
fi

tool=$1
shift
bin="node_modules/.bin/$tool"

if [ ! -x "$bin" ]; then
  case "$tool" in
    cspell) skip_hint="SKIP=cspell" ;;
    markdownlint) skip_hint="SKIP=markdownlint-structural" ;;
    *) skip_hint="SKIP=<hook-id>" ;;
  esac
  printf 'error: missing %s in this worktree.\n' "$bin" >&2
  printf 'Run npm ci in this worktree; do not use %s.\n' "$skip_hint" >&2
  exit 127
fi

exec "$bin" "$@"
