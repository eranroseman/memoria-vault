from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "packages" / "memoria-obsidian"
SEED_PLUGIN = ROOT / "src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian"

# `node --test` discovers files by name, and it exits 0 when it discovers none.
# So the exit code alone cannot tell a green suite from a suite that silently
# stopped running: rename a file out of the glob and every assertion in it
# disappears with the gate still green. These pin what must have run.
MIN_NODE_TESTS = 41
NODE_SUITE_FILES = ("test.mjs", "test-handshake.mjs", "test-pill.mjs", "test-viewspec.mjs")


def _is_discoverable(name: str) -> bool:
    """Whether `node --test` runs this file (its documented name patterns)."""
    stem = name.removesuffix(".mjs")
    return stem == "test" or stem.startswith("test-") or stem.endswith((".test", "-test", "_test"))


def _run_node_suite() -> subprocess.CompletedProcess[str]:
    """Run the plugin's node suite with a reporter whose totals are parseable.

    The default reporter differs by node major (tap on 22, spec on 24), so the
    count assertion pins `--test-reporter=tap` rather than guessing the format.
    Discovery is unaffected: this runs the same files as `npm test`.
    """
    return subprocess.run(
        ["node", "--test", "--test-reporter=tap"],
        cwd=PLUGIN,
        text=True,
        capture_output=True,
        check=False,
    )


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
    assert package["scripts"]["test"] == "node --test"
    assert (PLUGIN / "main.js").is_file()
    assert (PLUGIN / "schema.js").is_file()
    assert (PLUGIN / "styles.css").is_file()


def test_memoria_obsidian_seed_matches_release_artifacts() -> None:
    for artifact in ("main.js", "schema.js", "manifest.json", "styles.css"):
        assert (SEED_PLUGIN / artifact).read_text(encoding="utf-8") == (
            PLUGIN / artifact
        ).read_text(encoding="utf-8")


def test_memoria_obsidian_event_schema_rejects_leaky_fields() -> None:
    result = _run_node_suite()

    assert result.returncode == 0, result.stdout + result.stderr


def test_memoria_obsidian_node_suite_still_discovers_every_file() -> None:
    result = _run_node_suite()

    counted = re.search(r"^# tests (\d+)$", result.stdout, re.MULTILINE)
    assert counted is not None, result.stdout + result.stderr
    assert int(counted.group(1)) >= MIN_NODE_TESTS, result.stdout

    present = sorted(path.name for path in (PLUGIN / "scripts").glob("*.mjs"))
    assert set(NODE_SUITE_FILES) <= set(present), present
    # A suite named outside the runner's glob never runs and never complains.
    assert [name for name in present if not _is_discoverable(name)] == []


def test_memoria_obsidian_uses_memoria_operation_run_only() -> None:
    source = (PLUGIN / "main.js").read_text(encoding="utf-8")

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
    source = (PLUGIN / "main.js").read_text(encoding="utf-8")

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
