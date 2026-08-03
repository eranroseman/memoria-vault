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
    """Every rule that moved here from plugin_provenance_doctor still bites.

    The doctor's FORBIDDEN_REL / FORBIDDEN_GLOBS denylist folded into the live
    removed_surfaces.json contract. The roster below re-enumerates that whole
    set: the membership assertion fails if any rule is dropped from the
    contract, and a payload per rule is rebuilt in a scratch repo that the
    shipped contract must report — so neither a dropped rule nor a rule that
    no longer fires can pass. The first cut of this test built six payloads
    for ten rules, and review demonstrated five rules could be deleted with
    the suite green; deriving both assertions from one full roster closed that.
    """
    # (kind, contract needle, payload to create, expected violation)
    moved_rules = (
        (
            "path",
            "src/memoria_vault/product/workspace_seed/.memoria/plugins",
            "src/memoria_vault/product/workspace_seed/.memoria/plugins/keep",
            "forbidden path exists: src/memoria_vault/product/workspace_seed/.memoria/plugins",
        ),
        (
            "path",
            "src/memoria_vault/product/workspace_seed/system/scripts",
            "src/memoria_vault/product/workspace_seed/system/scripts/keep",
            "forbidden path exists: src/memoria_vault/product/workspace_seed/system/scripts",
        ),
        ("path", "src/.obsidian", "src/.obsidian/keep", "forbidden path exists: src/.obsidian"),
        (
            "path",
            "packages/obsidian-plugin",
            "packages/obsidian-plugin/keep",
            "forbidden path exists: packages/obsidian-plugin",
        ),
        (
            "path",
            "tests/test_memoria_inspector.py",
            "tests/test_memoria_inspector.py",
            "forbidden path exists: tests/test_memoria_inspector.py",
        ),
        (
            "glob",
            "src/**/agent_client*",
            "src/memoria_vault/runtime/agent_client.py",
            "forbidden glob match: src/memoria_vault/runtime/agent_client.py",
        ),
        (
            "glob",
            "src/**/obsidian_adapter*",
            "src/memoria_vault/obsidian_adapter.py",
            "forbidden glob match: src/memoria_vault/obsidian_adapter.py",
        ),
        (
            "glob",
            "src/**/obsidian_plugin*",
            "src/memoria_vault/runtime/obsidian_plugin.py",
            "forbidden glob match: src/memoria_vault/runtime/obsidian_plugin.py",
        ),
        (
            "glob",
            "tests/**/test_*agent_client*.py",
            "tests/test_probe_agent_client_reborn.py",
            "forbidden glob match: tests/test_probe_agent_client_reborn.py",
        ),
        (
            "glob",
            "tests/**/test_*obsidian_adapter*.py",
            "tests/test_probe_obsidian_adapter_reborn.py",
            "forbidden glob match: tests/test_probe_obsidian_adapter_reborn.py",
        ),
        (
            "glob",
            "tests/**/test_*obsidian_plugin*.py",
            "tests/test_probe_obsidian_plugin_reborn.py",
            "forbidden glob match: tests/test_probe_obsidian_plugin_reborn.py",
        ),
    )
    live = gate.load_contract(gate.CONTRACT)
    contract_needles = {(rule.kind, rule.needle) for rule in live.rules}
    assert {(kind, needle) for kind, needle, _, _ in moved_rules} <= contract_needles

    for root in live.search_roots:
        target = tmp_path / root
        if Path(root).suffix:  # file-type roots like AGENTS.md, .pre-commit-config.yaml
            target.write_text("", encoding="utf-8")
        else:
            target.mkdir(parents=True, exist_ok=True)
    for _, _, payload, _ in moved_rules:
        target = tmp_path / payload
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("", encoding="utf-8")

    violations = set(gate.find_violations(tmp_path, gate.CONTRACT))

    assert {expected for _, _, _, expected in moved_rules} <= violations


# Malformed-contract arms of load_contract (the two or->and survivors).

_VALID = {
    "search_roots": ["src"],
    "allow_text_files": [],
    "rules": [{"kind": "text", "needle": "gone_symbol", "owner": "#1", "reason": "removed"}],
}


def _contract(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_a_valid_contract_loads(tmp_path: Path) -> None:
    contract = gate.load_contract(_contract(tmp_path, _VALID))
    assert contract.rules[0].needle == "gone_symbol"


@pytest.mark.parametrize("bad_roots", ["src", ["src", 7]], ids=["not-a-list", "non-string"])
def test_search_roots_must_be_a_list_of_strings(tmp_path: Path, bad_roots) -> None:
    data = dict(_VALID, search_roots=bad_roots)

    with pytest.raises(ValueError, match="search_roots must be a list of strings"):
        gate.load_contract(_contract(tmp_path, data))


@pytest.mark.parametrize("missing", ["needle", "owner", "reason"])
def test_each_rule_field_is_required_alone(tmp_path: Path, missing: str) -> None:
    """or->and in the three-way check survives unless each field is dropped alone."""
    rule = dict(_VALID["rules"][0])
    rule[missing] = ""
    data = dict(_VALID, rules=[rule])

    with pytest.raises(ValueError, match="must include needle, owner, and reason"):
        gate.load_contract(_contract(tmp_path, data))
