"""Alpha.20 allows only the standalone Obsidian proof-adapter package."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scripts.checks import plugin_provenance_doctor as doctor

ROOT = Path(__file__).resolve().parent.parent


def test_plugin_scope_doctor_accepts_standalone_repo():
    assert doctor.check(ROOT) == []


def test_plugin_scope_doctor_allows_memoria_obsidian_package(tmp_path):
    root = tmp_path / "repo"
    (root / "packages/memoria-obsidian").mkdir(parents=True)

    assert doctor.check(root) == []


def test_plugin_scope_doctor_flags_removed_payloads(tmp_path):
    root = tmp_path / "repo"
    (root / "src/memoria_vault/product/workspace_seed/.obsidian").mkdir(parents=True)
    (root / "src/memoria_vault/product/workspace_seed/.memoria/plugins").mkdir(parents=True)
    (root / "src/memoria_vault/product/workspace_seed/system/scripts").mkdir(parents=True)
    (root / "src/.obsidian").mkdir(parents=True)
    (root / "packages/obsidian-plugin").mkdir(parents=True)
    (root / "src/memoria_vault/obsidian_adapter").mkdir(parents=True)
    (root / "src/memoria_vault/runtime/agent_client.py").parent.mkdir(parents=True)
    (root / "src/memoria_vault/runtime/agent_client.py").write_text("", encoding="utf-8")
    (root / "tests").mkdir(parents=True)
    (root / "tests/test_memoria_inspector.py").write_text("", encoding="utf-8")
    (root / "tests/test_obsidian_plugin.py").write_text("", encoding="utf-8")

    findings = doctor.check(root)

    assert {finding.split(":", 1)[0] for finding in findings} == {
        "packages/obsidian-plugin",
        "src/memoria_vault/obsidian_adapter",
        "src/memoria_vault/product/workspace_seed/.memoria/plugins",
        "src/memoria_vault/product/workspace_seed/.obsidian",
        "src/memoria_vault/product/workspace_seed/system/scripts",
        "src/memoria_vault/runtime/agent_client.py",
        "src/.obsidian",
        "tests/test_memoria_inspector.py",
        "tests/test_obsidian_plugin.py",
    }
