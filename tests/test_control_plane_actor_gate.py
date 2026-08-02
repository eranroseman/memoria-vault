"""Tests for the Actor Authority Guard doc-drift gate (#1594)."""

from __future__ import annotations

import pytest

from scripts.checks import control_plane_actor_gate as gate

pytestmark = pytest.mark.static


def test_live_table_matches_the_shipped_roster() -> None:
    text = (gate.ROOT / gate.DOC_REL).read_text(encoding="utf-8")
    assert gate.drift_errors(gate.documented_rosters(text), gate.shipped_rosters()) == []


def test_gate_names_a_missing_and_a_stale_operation() -> None:
    documented = {"pi": {"mark-checked", "retired-op"}, "integrity": {"trace-integrity-scan"}}
    shipped = {"pi": {"mark-checked", "update-work"}, "integrity": {"trace-integrity-scan"}}
    errors = gate.drift_errors(documented, shipped)
    assert any("missing `update-work`" in error for error in errors)
    assert any("lists `retired-op`" in error for error in errors)


def test_parser_reads_only_the_guard_section() -> None:
    text = (
        "## Current Commands\n\n| `memoria` | `not-an-actor-row` |\n\n"
        "## Actor Authority Guard\n\n"
        "| Required actor | Operations |\n| --- | --- |\n"
        "| `pi` | `mark-checked`, `update-work` |\n"
        "| `integrity` | `trace-integrity-scan` |\n\n"
        "## WIP Limits\n\n| `pi` | `spurious-after-section` |\n"
    )
    assert gate.documented_rosters(text) == {
        "pi": {"mark-checked", "update-work"},
        "integrity": {"trace-integrity-scan"},
    }
