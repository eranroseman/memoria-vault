#!/usr/bin/env bash
# Memoria dev bootstrap — run ONCE per fresh clone to wire the local quality gate.
#
#   bash scripts/dev-setup.sh
#
# This sets up the CONTRIBUTOR toolchain (the pre-commit gate + linters). It does
# NOT install or run the Memoria product — that is scripts/install.sh. Idempotent;
# safe to re-run. Optional system tools (shellcheck, node/npx) are reported, not
# auto-installed (they need a package manager); the pre-commit hook skips them
# gracefully when absent, and CI enforces them regardless.
set -eu

unset CDPATH
cd "$(dirname -- "$0")/.." || exit 1

note() { printf '  %s\n' "$1"; }

echo "==> Installing Python dev tooling + MCP self-test deps"
PY=$(command -v python3 || command -v python || true)
if [ -n "$PY" ]; then
  if "$PY" -m pip install --quiet -r requirements-dev.txt; then
    note "dev tooling installed from requirements-dev.txt"
  else
    note "pip install failed — install requirements-dev.txt manually for local lint parity"
  fi
  if [ -f src/.memoria/mcp/requirements.txt ]; then
    if "$PY" -m pip install --quiet -r src/.memoria/mcp/requirements.txt; then
      note "MCP deps installed (self-tests will run)"
    else
      note "MCP requirements not installed — the .py --self-tests may skip deps"
    fi
  fi
else
  note "python not found — install Python 3 first"
fi

echo "==> Installing pre-commit hooks (git won't do this on clone — it's local config)"
if command -v pre-commit >/dev/null 2>&1; then
  pre-commit install
  note "pre-commit hooks installed"
else
  note "pre-commit not found — install requirements-dev.txt, then run: pre-commit install"
fi

echo "==> Optional system tools the hook uses if present (not auto-installed):"
for t in shellcheck npx; do
  if command -v "$t" >/dev/null 2>&1; then
    note "✓ $t"
  else
    note "– $t (missing; install via your OS package manager for full local parity)"
  fi
done

echo "==> Done. The pre-commit gate is active. Bypass a single block with: git commit --no-verify"
