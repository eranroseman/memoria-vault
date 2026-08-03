"""Tests for the removed-surface negative gate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.checks import removed_surface_gate as gate

pytestmark = pytest.mark.static


def write_contract(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "search_roots": ["docs"],
                "allow_text_files": ["docs/allowed.md"],
                "rules": [
                    {
                        "kind": "path",
                        "needle": "old/package",
                        "owner": "tests",
                        "reason": "retired package surface",
                    },
                    {
                        "kind": "text",
                        "needle": "OldSurface",
                        "owner": "tests",
                        "reason": "retired prose reference",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


def test_reports_removed_paths_and_text_from_contract(tmp_path: Path) -> None:
    contract = tmp_path / "removed_surfaces.json"
    write_contract(contract)
    (tmp_path / "old" / "package").mkdir(parents=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "bad.md").write_text("OldSurface\n", encoding="utf-8")
    (tmp_path / "docs" / "allowed.md").write_text("OldSurface\n", encoding="utf-8")

    assert gate.find_violations(tmp_path, contract) == [
        "forbidden path exists: old/package",
        "docs/bad.md: contains OldSurface",
    ]


def test_scans_file_type_search_roots(tmp_path: Path) -> None:
    contract = tmp_path / "removed_surfaces.json"
    contract.write_text(
        json.dumps(
            {
                "search_roots": ["NOTES.md"],
                "allow_text_files": [],
                "rules": [
                    {
                        "kind": "text",
                        "needle": "OldSurface",
                        "owner": "tests",
                        "reason": "retired prose reference",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "NOTES.md").write_text("intro\nOldSurface\n", encoding="utf-8")

    assert gate.find_violations(tmp_path, contract) == ["NOTES.md: contains OldSurface"]


def test_missing_search_root_is_a_hard_failure(tmp_path: Path) -> None:
    contract = tmp_path / "removed_surfaces.json"
    write_contract(contract)  # search root "docs" — deliberately not created

    assert gate.find_violations(tmp_path, contract) == ["missing search root: docs"]


def test_glob_rules_flag_pattern_matches(tmp_path: Path) -> None:
    contract = tmp_path / "removed_surfaces.json"
    contract.write_text(
        json.dumps(
            {
                "search_roots": ["docs"],
                "allow_text_files": [],
                "rules": [
                    {
                        "kind": "glob",
                        "needle": "src/**/agent_client*",
                        "owner": "tests",
                        "reason": "retired module pattern",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "src/pkg").mkdir(parents=True)
    (tmp_path / "src/pkg/agent_client.py").write_text("", encoding="utf-8")

    assert gate.find_violations(tmp_path, contract) == [
        "forbidden glob match: src/pkg/agent_client.py"
    ]


def test_live_contract_flags_the_retired_plugin_payloads(tmp_path: Path) -> None:
    """The rules that moved here from plugin_provenance_doctor still bite.

    The doctor's FORBIDDEN_REL / FORBIDDEN_GLOBS denylist folded into the
    live removed_surfaces.json contract; this rebuilds those payloads in a
    scratch repo and asserts the shipped contract reports every one, so the
    consolidation cannot have silently dropped a tombstone.
    """
    contract = gate.CONTRACT
    live = gate.load_contract(contract)
    for root in live.search_roots:
        target = tmp_path / root
        if Path(root).suffix:  # file-type roots like AGENTS.md, .pre-commit-config.yaml
            target.write_text("", encoding="utf-8")
        else:
            target.mkdir(parents=True, exist_ok=True)
    payloads = (
        "src/memoria_vault/product/workspace_seed/.memoria/plugins/keep",
        "src/.obsidian/keep",
        "packages/obsidian-plugin/keep",
    )
    for payload in payloads:
        (tmp_path / payload).mkdir(parents=True)
    (tmp_path / "tests/test_memoria_inspector.py").write_text("", encoding="utf-8")
    (tmp_path / "src/memoria_vault/runtime").mkdir(parents=True)
    (tmp_path / "src/memoria_vault/runtime/agent_client.py").write_text("", encoding="utf-8")
    (tmp_path / "tests/test_obsidian_plugin.py").write_text("", encoding="utf-8")

    violations = set(gate.find_violations(tmp_path, contract))

    assert {
        "forbidden path exists: src/memoria_vault/product/workspace_seed/.memoria/plugins",
        "forbidden path exists: src/.obsidian",
        "forbidden path exists: packages/obsidian-plugin",
        "forbidden path exists: tests/test_memoria_inspector.py",
        "forbidden glob match: src/memoria_vault/runtime/agent_client.py",
        "forbidden glob match: tests/test_obsidian_plugin.py",
    } <= violations
