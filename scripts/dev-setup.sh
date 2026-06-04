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

echo "==> Activating the pre-commit hook (git won't do this on clone — it's local config)"
git config core.hooksPath .githooks
note "core.hooksPath = $(git config --local core.hooksPath)"

echo "==> Installing Python dev tooling (ruff, yamllint) + MCP self-test deps"
PY=$(command -v python3 || command -v python || true)
if [ -n "$PY" ]; then
  if "$PY" -m pip install --quiet ruff yamllint; then
    note "ruff + yamllint installed"
  else
    note "pip install failed — install 'ruff' and 'yamllint' manually for local lint parity"
  fi
  if [ -f vault/.memoria/mcp/requirements.txt ]; then
    if "$PY" -m pip install --quiet -r vault/.memoria/mcp/requirements.txt; then
      note "MCP deps installed (self-tests will run)"
    else
      note "MCP requirements not installed — the .py --self-tests may skip deps"
    fi
  fi
else
  note "python not found — install Python 3 first"
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
