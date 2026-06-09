#!/usr/bin/env bash
# Memoria local test runner — the bottom of the test pyramid (ADR-29).
#
#   L1  component self-tests — the vault `--self-test` modules (policy gate, hook,
#       board, metrics, ingest + verify MCP, detectors, ingest spine). Synthetic
#       fixtures, no vault runtime.
#   L0  static + schema — docs-doctor, vault links, test-ref drift, dashboard
#       schema-drift, installer lint, syntax sanity.
#
# This is the one-command local gate to run before pushing. CI runs the same
# checks as separate required jobs (lint [docs-doctor / docs-links / check-test-refs
# / ruff / status-doctor] + python-selftest); this mirrors them so a red push is
# caught locally. Higher layers need a runtime or a human — see project/test/
# (L2 agent wiring, L3 GUI, L4 golden-path, L5 eval).
#
# Usage: scripts/test.sh [l0|l1|check|all]   (default: all)   check = paths-only, no run
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2
P=vault/.memoria
fail=0
run() { printf '→ %s\n' "$*"; if "$@" >/tmp/mt.$$ 2>&1; then sed 's/^/    /' /tmp/mt.$$ | tail -2; else sed 's/^/    /' /tmp/mt.$$; echo "    ✗ FAILED"; fail=1; fi; rm -f /tmp/mt.$$; }

# The L1 self-test modules (vault Python tooling), one path per line, no `.py`.
# Single source for l1() and `check`. Keep in sync with python-selftest.yml —
# CI is the authoritative list.
L1_MODULES="mcp/policy_mcp mcp/policy_hook mcp/board_export mcp/metrics_aggregate mcp/ingest_mcp mcp/verify_mcp
profiles/memoria-linter/skills/structural-detectors/scripts/detectors
profiles/memoria-librarian/skills/obsidian-paper-note/scripts/ingest_paper
profiles/memoria-librarian/skills/obsidian-paper-note/scripts/resolve_merge
profiles/memoria-librarian/skills/obsidian-paper-note/scripts/link
profiles/memoria-librarian/skills/obsidian-paper-note/scripts/extract
profiles/memoria-librarian/skills/obsidian-paper-note/scripts/pipeline
profiles/memoria-librarian/skills/obsidian-paper-note/scripts/sweeps"

l1() {
  echo "── L1: component self-tests ──"
  # shellcheck disable=SC2086  # intentional word-split of the module list
  for s in $L1_MODULES; do
    run python3 "$P/$s.py" --self-test
  done
}

# `check` — verify every L1 module path resolves WITHOUT running it. Fast and
# CI-safe; catches a renamed/moved module before it bites (the #284 drift that
# slipped past CI because test.sh itself isn't run there).
check_paths() {
  echo "── check: L1 module paths resolve ──"
  # shellcheck disable=SC2086  # intentional word-split of the module list
  for s in $L1_MODULES; do
    if [ -f "$P/$s.py" ]; then printf '  ✓ %s.py\n' "$s"
    else printf '  ✗ MISSING  %s.py\n' "$P/$s"; fail=1; fi
  done
}

l0() {
  echo "── L0: static + schema ──"
  run python3 scripts/docs-doctor.py docs
  run bash scripts/check-vault-links.sh
  if [ -f scripts/check-test-refs.py ]; then run python3 scripts/check-test-refs.py
  else echo "→ check-test-refs    (not on this branch — skipped)"; fi
  run python3 -m py_compile "$P"/mcp/*.py "$P/profiles/memoria-linter/skills/structural-detectors/scripts/detectors.py" "$P/profiles/memoria-librarian/skills/obsidian-paper-note/scripts/ingest_paper.py" "$P/profiles/memoria-librarian/skills/obsidian-paper-note/scripts/resolve_merge.py" "$P/profiles/memoria-librarian/skills/obsidian-paper-note/scripts/link.py" "$P/profiles/memoria-librarian/skills/obsidian-paper-note/scripts/extract.py" "$P/profiles/memoria-librarian/skills/obsidian-paper-note/scripts/pipeline.py" "$P/profiles/memoria-librarian/skills/obsidian-paper-note/scripts/sweeps.py"
  run bash -n scripts/install.sh
  if command -v shellcheck >/dev/null 2>&1; then
    run shellcheck --severity=warning scripts/install.sh "$P"/scripts/*.sh
  else echo "→ shellcheck         (absent — installer lint skipped; CI enforces it)"; fi
  # Vault lint over the live tree. dashboard-field-drift is GATED (a dashboard
  # querying a field no template emits is a silent failure — CI gates it too);
  # content findings (broken wikilinks, schema-check) print but stay advisory.
  run python3 "$P/profiles/memoria-linter/skills/structural-detectors/scripts/detectors.py" --vault vault --gate dashboard-field-drift
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
