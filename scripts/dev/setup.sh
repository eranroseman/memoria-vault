#!/usr/bin/env bash
# Memoria dev bootstrap — run ONCE per fresh clone to wire the local quality gate.
#
#   bash scripts/dev/setup.sh                 # Python tooling + pre-commit hooks
#
# This sets up the CONTRIBUTOR toolchain (the pre-commit hook + linters). It does
# NOT install or run the Memoria product — that is scripts/install.sh. Idempotent;
# safe to re-run. Hook environments are pinned in .pre-commit-config.yaml.
set -eu

unset CDPATH
cd "$(dirname -- "$0")/../.." || exit 1

note() { printf '  %s\n' "$1"; }
fail() {
  printf '  error: %s\n' "$1" >&2
  exit 1
}

if command -v mise >/dev/null 2>&1; then
  echo "==> Installing pinned language runtimes with mise"
  if mise install; then
    note "mise runtimes installed"
  else
    fail "mise install failed"
  fi
fi

echo "==> Installing Python dev tooling"
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

echo "==> Local hook tools:"
for t in python3 pre-commit; do
  if command -v "$t" >/dev/null 2>&1; then
    note "✓ $t"
  else
    note "– $t (missing; rerun this script after fixing the install error above)"
  fi
done
note "ruff, yamllint, shellcheck, gitleaks, cspell, and markdownlint are supplied by pinned pre-commit hook environments"

echo "==> Done. The pre-commit hook is active. Bypass a single block with: git commit --no-verify"
