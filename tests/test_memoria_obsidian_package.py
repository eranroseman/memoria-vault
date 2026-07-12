from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "packages" / "memoria-obsidian"
SEED_PLUGIN = ROOT / "src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian"


def test_memoria_obsidian_package_has_obsidian_release_artifacts() -> None:
    manifest = json.loads((PLUGIN / "manifest.json").read_text(encoding="utf-8"))
    package = json.loads((PLUGIN / "package.json").read_text(encoding="utf-8"))

    assert manifest == {
        "id": "memoria-obsidian",
        "name": "Memoria",
        "version": "0.1.0-alpha.20",
        "minAppVersion": "1.5.0",
        "description": "Minimal local Memoria control surface and empirical-use recorder.",
        "author": "Memoria",
        "isDesktopOnly": False,
    }
    assert package["scripts"]["build"] == "node scripts/build.mjs"
    assert package["scripts"]["test"] == "node scripts/test.mjs"
    assert (PLUGIN / "main.js").is_file()
    assert (PLUGIN / "schema.js").is_file()
    assert (PLUGIN / "styles.css").is_file()


def test_memoria_obsidian_build_artifacts_are_current() -> None:
    result = subprocess.run(
        ["node", "scripts/build.mjs", "--check"],
        cwd=PLUGIN,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_memoria_obsidian_seed_matches_release_artifacts() -> None:
    for artifact in ("main.js", "schema.js", "manifest.json", "styles.css"):
        assert (SEED_PLUGIN / artifact).read_text(encoding="utf-8") == (
            PLUGIN / artifact
        ).read_text(encoding="utf-8")


def test_memoria_obsidian_event_schema_rejects_leaky_fields() -> None:
    result = subprocess.run(
        ["node", "scripts/test.mjs"],
        cwd=PLUGIN,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_memoria_obsidian_uses_memoria_operation_run_only() -> None:
    source = (PLUGIN / "src/main.ts").read_text(encoding="utf-8")

    assert "/operation/run" in source
    assert "requestUrl" in source
    assert "fetch(" not in source
    assert "setSecret" in source
    assert "getSecret" in source
    assert "empirical-event-record" in source
    assert "empirical-event:" in source
    assert "empirical_event.record" not in source
    assert "vault.create(" not in source
    assert "vault.modify(" not in source
    assert "vault.delete(" not in source
    assert "adapter.write(" not in source


def test_memoria_obsidian_registers_minimal_proof_commands() -> None:
    source = (PLUGIN / "src/main.ts").read_text(encoding="utf-8")

    for command_id in (
        "connect",
        "show-attention",
        "show-active-concept",
        "queue-operation",
        "start-session",
        "stop-session",
        "record-disposition",
        "record-fallback",
        "flush-events",
        "delete-events",
    ):
        assert f'id: "{command_id}"' in source
