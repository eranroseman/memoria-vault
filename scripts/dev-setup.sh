#!/usr/bin/env bash
# Memoria dev bootstrap — run ONCE per fresh clone to wire the local quality gate.
#
#   bash scripts/dev-setup.sh                 # toolchain + repo-local Node tools + qmd index
#   bash scripts/dev-setup.sh --with-hooks    # also wire qmd auto-refresh git hooks
#
# This sets up the CONTRIBUTOR toolchain (the pre-commit hook + linters). It does
# NOT install or run the Memoria product — that is scripts/install.sh. Idempotent;
# safe to re-run. Python hook tools are pinned in requirements-dev.txt; Node hook
# tools are pinned in package-lock.json and installed with npm ci.
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
  if [ -f vault-template/.memoria/mcp/requirements.txt ]; then
    if "$PY" -m pip install --quiet -r vault-template/.memoria/mcp/requirements.txt; then
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
  HOOKS_PATH=$(git config --get core.hooksPath || true)
  DEFAULT_HOOKS=$(git rev-parse --git-path hooks)
  if [ -n "$HOOKS_PATH" ]; then
    if [ "$HOOKS_PATH" = "$DEFAULT_HOOKS" ] || [ "$HOOKS_PATH" = ".git/hooks" ]; then
      git config --unset-all core.hooksPath
      note "removed redundant core.hooksPath so pre-commit can manage hooks"
    else
      note "core.hooksPath is set to $HOOKS_PATH; unset it before installing pre-commit"
    fi
  fi
  if pre-commit install --install-hooks; then
    note "pre-commit hook and hook environments installed"
  else
    note "pre-commit install failed — fix the hooksPath/config issue above and rerun"
  fi
else
  note "pre-commit not found — install requirements-dev.txt, then run: pre-commit install --install-hooks"
fi

echo "==> Setting up repo-local Node dev tools and qmd index (needs Node >=22)"
NODE=$(command -v node || true)
NODE_MAJOR=0
if [ -n "$NODE" ]; then
  NODE_MAJOR=$("$NODE" -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)
fi
if [ -n "$NODE" ] && [ "${NODE_MAJOR:-0}" -ge 22 ] 2>/dev/null; then
  if command -v npm >/dev/null 2>&1 && npm ci --silent; then
    note "repo-local Node tools installed (qmd, cspell, markdownlint)"
    bash scripts/qmd-codebase-index.sh \
      || note "qmd index build skipped/failed — re-run: bash scripts/qmd-codebase-index.sh"
    if [ "$WITH_HOOKS" -eq 1 ]; then
      bash scripts/qmd-install-hooks.sh || note "qmd hook install skipped"
    else
      note "(auto-refresh hooks not wired — add them with: bash scripts/qmd-install-hooks.sh)"
    fi
  else
    note "npm ci failed — run it manually, then: bash scripts/qmd-codebase-index.sh"
  fi
else
  note "Node >=22 not found — repo Node tools and code search skipped."
  note "  fnm gives a standalone Node (independent of any runtime): https://github.com/Schniz/fnm"
  note "  then: fnm install 22 && npm ci && bash scripts/qmd-codebase-index.sh"
fi

echo "==> Local hook tools:"
for t in pre-commit no-commit-to-branch check-json ruff yamllint shellcheck cspell markdownlint; do
  if PATH="node_modules/.bin:$PATH" command -v "$t" >/dev/null 2>&1; then
    note "✓ $t"
  else
    note "– $t (missing; rerun this script after fixing the install error above)"
  fi
done

echo "==> Done. The pre-commit hook is active. Bypass a single block with: git commit --no-verify"
