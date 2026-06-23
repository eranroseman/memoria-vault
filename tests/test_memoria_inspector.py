"""Read-only Memoria Inspector plugin contract."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OBSIDIAN = ROOT / "src" / ".obsidian"
PLUGIN = OBSIDIAN / "plugins" / "memoria-inspector"
MAIN = PLUGIN / "main.js"


def test_memoria_inspector_is_enabled_and_declared():
    manifest = json.loads((PLUGIN / "manifest.json").read_text(encoding="utf-8"))
    enabled = json.loads((OBSIDIAN / "community-plugins.json").read_text(encoding="utf-8"))

    assert manifest["id"] == "memoria-inspector"
    assert manifest["name"] == "Memoria Inspector"
    assert "memoria-inspector" in enabled


def test_memoria_inspector_reads_only_operational_sources():
    text = MAIN.read_text(encoding="utf-8")

    for marker in (
        "system/logs/board-state.jsonl",
        "system/logs/audit.jsonl",
        "system/metrics/lint-verdict-",
        "system/metrics/lane-",
        "system/dashboards/board-state",
        "system/dashboards/audit-log",
        "spaces/maintenance#Drift watch",
        "system/dashboards/fleet-health",
        "registerView",
        "getRightLeaf",
        "adapter.read",
        "openLinkText",
    ):
        assert marker in text

    for forbidden in (
        ".vault.modify",
        ".vault.create",
        ".vault.delete",
        ".adapter.write",
        "requestUrl",
        "fetch(",
        "child_process",
        'require("fs")',
        "require('fs')",
    ):
        assert forbidden not in text
