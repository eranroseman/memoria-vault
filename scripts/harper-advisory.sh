#!/usr/bin/env bash
# harper-advisory.sh — advisory grammar check via harper-cli.
#
# Runs harper-cli lint --no-spell-check on the passed files.
# Always exits 0 (advisory only — findings are informational, not blocking).
# Skips gracefully if harper-cli is not installed.

if ! command -v harper-cli >/dev/null 2>&1; then
  # Not installed — skip silently
  exit 0
fi

harper-cli lint --no-spell-check "$@" || true

exit 0
