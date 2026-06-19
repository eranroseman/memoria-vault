#!/usr/bin/env bash
# Memoria dev bootstrap — run ONCE per fresh clone to wire the local quality gate.
#
#   bash scripts/dev-setup.sh                 # toolchain + repo-local qmd index
#   bash scripts/dev-setup.sh --with-hooks    # also wire qmd auto-refresh git hooks
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

WITH_HOOKS=0
[ "${1:-}" = "--with-hooks" ] && WITH_HOOKS=1

echo "==> Installing Python dev tooling + MCP self-test deps"
PY=$(command -v python3 || command -v python || true)
if [ -n "$PY" ]; then
  if "$PY" -m pip install --quiet -r requirements-dev.txt; then
    note "dev tooling installed from requirements-dev.txt"
  else
    note "pip install failed — install requirements-dev.txt manually for local lint parity"
  fi
  if "$PY" -m pip install --quiet -e .; then
    note "Memoria package installed editable"
  else
    note "editable install failed — run manually: $PY -m pip install -e ."
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

echo "==> Setting up the repo-local qmd code-search index (needs Node >=22)"
NODE=$(command -v node || true)
NODE_MAJOR=0
if [ -n "$NODE" ]; then
  NODE_MAJOR=$("$NODE" -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)
fi
if [ -n "$NODE" ] && [ "${NODE_MAJOR:-0}" -ge 22 ] 2>/dev/null; then
  if command -v npm >/dev/null 2>&1 && npm install --silent; then
    note "repo-local qmd installed (node_modules/)"
    bash scripts/qmd-codebase-index.sh \
      || note "qmd index build skipped/failed — re-run: bash scripts/qmd-codebase-index.sh"
    if [ "$WITH_HOOKS" -eq 1 ]; then
      bash scripts/qmd-install-hooks.sh || note "qmd hook install skipped"
    else
      note "(auto-refresh hooks not wired — add them with: bash scripts/qmd-install-hooks.sh)"
    fi
  else
    note "npm install failed — run it manually, then: bash scripts/qmd-codebase-index.sh"
  fi
else
  note "Node >=22 not found — repo code search skipped (not required for the commit gate)."
  note "  fnm gives a standalone Node (independent of any runtime): https://github.com/Schniz/fnm"
  note "  then: fnm install 22 && npm install && bash scripts/qmd-codebase-index.sh"
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
