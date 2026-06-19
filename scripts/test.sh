#!/usr/bin/env bash
# Memoria local test runner — the bottom of the test pyramid (ADR-29).
#
#   L1  component tests — the pytest tree in tests/ (policy gate, hook, board,
#       metrics, ingest + verify MCP, detectors, ingest spine, repo tooling).
#       Synthetic fixtures, no vault runtime (ADR-44).
#   L0  static + schema — docs-doctor, vault links, test-ref drift, dashboard
#       schema-drift, installer lint, syntax sanity.
#
# This is the one-command local gate to run before pushing. CI runs the same
# checks as separate required jobs (lint [docs-doctor / docs-links / check-test-refs
# / ruff / status-doctor] + python-selftest); this mirrors them so a red push is
# caught locally. Higher layers need a runtime or a human — see docs/testing/
# (L2 agent wiring, L3 GUI, L4 golden-path, L5 eval).
#
# Usage: scripts/test.sh [l0|l1|check|all]   (default: all)   check = collect-only, no run
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2
P=src/.memoria
fail=0
run() { printf '→ %s\n' "$*"; if "$@" >/tmp/mt.$$ 2>&1; then sed 's/^/    /' /tmp/mt.$$ | tail -2; else sed 's/^/    /' /tmp/mt.$$; echo "    ✗ FAILED"; fail=1; fi; rm -f /tmp/mt.$$; }

l1() {
  echo "── L1: component tests (pytest) ──"
  # ADR-44: L1 tests live in tests/, run by pytest, instead of inline --self-test.
  if python3 -c "import pytest" >/dev/null 2>&1; then
    run env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -q
  else
    echo "→ pytest             ✗ NOT INSTALLED — python3 -m pip install -r requirements-dev.txt (L1 was NOT run)"
    fail=1
  fi
}

# `check` — collect the tests WITHOUT running them. Fast and CI-safe; a test that
# imports a renamed/moved module fails collection here before it bites at runtime.
check_paths() {
  echo "── check: L1 tests collect ──"
  if python3 -c "import pytest" >/dev/null 2>&1; then
    run env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ --co -q
  else
    echo "→ pytest --collect-only   (not installed — python3 -m pip install -r requirements-dev.txt)"
  fi
}

l0() {
  echo "── L0: static + schema ──"
  run ruff check memoria scripts src/.memoria .github/scripts tests
  run python3 scripts/docs_doctor.py docs
  run bash scripts/check-vault-links.sh
  run python3 scripts/agents_doctor.py
  run python3 scripts/github_doctor.py
  run python3 scripts/ruleset_doctor.py
  if [ -f scripts/check_test_refs.py ]; then run python3 scripts/check_test_refs.py
  else echo "→ check-test-refs    (not on this branch — skipped)"; fi
  run python3 -m py_compile scripts/test_env_harness.py memoria/*.py memoria/runtime/*.py memoria/runtime/policy/*.py
  run python3 -m py_compile "$P"/mcp/*.py "$P"/memoria_runtime/*.py "$P"/memoria_runtime/policy/*.py "$P"/operations/lib/schema.py "$P"/operations/lib/inbox.py "$P"/operations/lib/loudness.py "$P"/operations/lib/worklists.py "$P"/operations/integrity/linter/detectors.py "$P"/operations/integrity/linter/hub_handoff.py "$P"/operations/integrity/linter/golden_restore.py "$P"/operations/integrity/linter/session_summary.py "$P"/operations/integrity/linter/precommit_check.py "$P"/operations/processing/ingest/*.py "$P"/operations/processing/project/*.py "$P"/operations/integrity/retraction/*.py "$P"/operations/cleanup/*.py "$P"/operations/telemetry/eval/*.py
  run bash -n scripts/install.sh scripts/install/*.sh
  if command -v shellcheck >/dev/null 2>&1; then
    run shellcheck --severity=warning scripts/install.sh scripts/install/*.sh src/.memoria/operations/integrity/linter/pre-commit src/.githooks/post-commit "$P"/scripts/*.sh
  else echo "→ shellcheck         (absent — installer lint skipped; CI enforces it)"; fi
  # Vault lint over the live tree. dashboard-field-drift and design-system-drift are
  # GATED: dashboard field drift is a silent failure, and design drift means the
  # shipped vault no longer matches its visual source of truth.
  # content findings (broken wikilinks, schema-check) print but stay advisory.
  run python3 "$P/operations/integrity/linter/detectors.py" --vault src --gate dashboard-field-drift,design-system-drift
}

case "${1:-all}" in
  l1) l1 ;;
  l0) l0 ;;
  check) check_paths ;;
  all) l1; l0 ;;
  *) echo "usage: $0 [l0|l1|check|all]"; exit 2 ;;
esac

echo
if [ "$fail" -eq 0 ]; then echo "✅ ${1:-all} PASS"; else echo "❌ FAIL — fix the ✗ above"; exit 1; fi
