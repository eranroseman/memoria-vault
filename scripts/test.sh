#!/usr/bin/env bash
# Memoria local test runner — the bottom of the test pyramid (ADR-29).
#
#   static   formatting, lint, schema, docs refs, ADR index, workflow safety.
#   unit     deterministic Python behavior.
#   contract CLI, operations, manifests, templates, projections.
#   package  build/install/smoke tests (full artifact gate lives in scripts/verify).
#   runtime  worker loops, recovery, idempotence, long local checks.
#   live     external providers; opt-in only.
#
# This is the direct Source Gate runner. Prefer `scripts/verify pr` before
# pushing; it calls this script and writes a JSON evidence bundle. CI runs the
# same L0/L1 source gates through required jobs; this mirrors them so a red push
# is caught locally. Higher gates need a runtime or a human.
#
# Usage: scripts/test.sh [static|unit|contract|source|package|runtime|live|l0|l1|check|all]
#        default: source; check = collect-only, no run
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2
P=vault-template/.memoria
fail=0
run() { printf '→ %s\n' "$*"; if "$@" >/tmp/mt.$$ 2>&1; then sed 's/^/    /' /tmp/mt.$$ | tail -2; else sed 's/^/    /' /tmp/mt.$$; echo "    ✗ FAILED"; fail=1; fi; rm -f /tmp/mt.$$; }

pytest_level() {
  label="$1"
  expr="$2"
  echo "── $label (pytest: $expr) ──"
  # ADR-44: L1 tests live in tests/, run by pytest, instead of inline --self-test.
  if python3 -c "import pytest" >/dev/null 2>&1; then
    run env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -q -m "$expr"
  else
    echo "→ pytest             ✗ NOT INSTALLED — python3 -m pip install -r requirements-dev.txt ($label was NOT run)"
    fail=1
  fi
}

unit() { pytest_level "unit" "unit"; }
contract() { pytest_level "contract" "contract"; }
package_tests() { pytest_level "package" "package"; }
runtime_tests() { pytest_level "runtime" "runtime"; }

l1() {
  echo "── L1/source: unit + contract ──"
  pytest_level "unit + contract" "unit or contract"
}

live_tests() {
  echo "── live (pytest: live) ──"
  if ! python3 -c "import pytest" >/dev/null 2>&1; then
    echo "→ pytest             ✗ NOT INSTALLED — python3 -m pip install -r requirements-dev.txt (live was NOT run)"
    fail=1
    return
  fi
  env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -q -m live >/tmp/mt.$$ 2>&1
  code=$?
  if [ "$code" -eq 5 ]; then
    echo "→ pytest -m live     (no live tests collected)"
  elif [ "$code" -eq 0 ]; then
    sed 's/^/    /' /tmp/mt.$$ | tail -2
  else
    sed 's/^/    /' /tmp/mt.$$
    echo "    ✗ FAILED"
    fail=1
  fi
  rm -f /tmp/mt.$$
}

# `check` — collect the tests WITHOUT running them. Fast and CI-safe; a test that
# imports a renamed/moved module fails collection here before it bites at runtime.
check_paths() {
  echo "── check: tests collect ──"
  if python3 -c "import pytest" >/dev/null 2>&1; then
    run env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ --co -q
  else
    echo "→ pytest --collect-only   (not installed — python3 -m pip install -r requirements-dev.txt)"
  fi
}

l0() {
  echo "── static: format + schema + docs + workflow checks ──"
  run ruff check src/memoria_vault scripts vault-template/.memoria .github/scripts tests
  run ruff format --check src/memoria_vault scripts vault-template/.memoria .github/scripts tests
  run python3 scripts/docs_doctor.py docs
  run python3 scripts/alpha14_negative_gate.py
  run python3 scripts/checked_terminology_gate.py
  run python3 scripts/gen_reference_refs.py --check
  run python3 scripts/docs_doctor.py --vault-links
  run python3 scripts/status_doctor.py
  run python3 scripts/adr_code_doctor.py
  run python3 scripts/agents_doctor.py
  run python3 scripts/github_doctor.py
  run python3 scripts/ruleset_doctor.py
  run python3 scripts/plugin_provenance_doctor.py
  run python3 scripts/gen_adr_index.py --check
  if python3 -c "import pytest" >/dev/null 2>&1; then
    run env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -q -m static
  else
    echo "→ pytest -m static   ✗ NOT INSTALLED — python3 -m pip install -r requirements-dev.txt"
    fail=1
  fi
  mapfile -t runtime_py < <(find src/memoria_vault -name '*.py' | sort)
  run python3 -m py_compile scripts/verify scripts/test_env_harness.py scripts/alpha15_dogfood_checkpoint.py "${runtime_py[@]}"
  run bash -n scripts/install.sh scripts/install/*.sh scripts/refresh-test-vault.sh scripts/install-test-vault-local-llm.sh
  if command -v shellcheck >/dev/null 2>&1; then
    run shellcheck --severity=warning scripts/install.sh scripts/install/*.sh scripts/refresh-test-vault.sh vault-template/.githooks/pre-commit "$P"/scripts/*.sh
  else echo "→ shellcheck         (absent — installer lint skipped; CI enforces it)"; fi
  # Vault lint over the live tree. dashboard-field-drift and design-system-drift are
  # GATED: dashboard field drift is a silent failure, and design drift means the
  # shipped vault no longer matches its visual source of truth.
  # content findings (broken wikilinks, schema-check) print but stay advisory.
  run env PYTHONPATH=src python3 -m memoria_vault.runtime.subsystems.integrity.linter.detectors --vault vault-template --gate dashboard-field-drift,design-system-drift
}

source_gate() {
  l0
  l1
}

case "${1:-source}" in
  static|l0) l0 ;;
  unit) unit ;;
  contract) contract ;;
  source|all) source_gate ;;
  package) package_tests ;;
  runtime) runtime_tests ;;
  live) live_tests ;;
  l1) l1 ;;
  check) check_paths ;;
  *) echo "usage: $0 [static|unit|contract|source|package|runtime|live|l0|l1|check|all]"; exit 2 ;;
esac

echo
if [ "$fail" -eq 0 ]; then echo "✅ ${1:-source} PASS"; else echo "❌ FAIL — fix the ✗ above"; exit 1; fi
