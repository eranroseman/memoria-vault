from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from memoria_vault.runtime.bundles import seed_bundles

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "packages" / "memoria-obsidian"
SEED_PLUGIN = ROOT / "src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian"

# `node --test` discovers files by name, and it exits 0 when it discovers none.
# So the exit code alone cannot tell a green suite from a suite that silently
# stopped running: rename a file out of the glob and every assertion in it
# disappears with the gate still green. These pin what must have run.
MIN_NODE_TESTS = 42
NODE_SUITE_FILES = ("test.mjs", "test-handshake.mjs", "test-pill.mjs", "test-viewspec.mjs")

# Byte-identical between the release package and the seed. `relate.js` joins
# when U3-PLUG.5 creates it.
SEED_PARITY_ARTIFACTS = (
    "handshake.js",
    "main.js",
    "manifest.json",
    "pill.js",
    "schema.js",
    "styles.css",
    "viewspec.js",
)

# Loads the plugin entrypoint for real, with `obsidian` stubbed because only
# the host provides it. Every *other* require -- `child_process` and the
# relative sibling modules -- resolves normally, so a module the vault did not
# receive raises MODULE_NOT_FOUND and this exits nonzero.
_LOAD_PROBE = """
const Module = require("node:module");
const original = Module._load;
Module._load = (request, parent, isMain) =>
  request === "obsidian"
    ? new Proxy({}, { get: () => class HostStub {} })
    : original(request, parent, isMain);
const plugin = require(process.argv[1]);
if (typeof plugin !== "function") {
  throw new Error("plugin entrypoint did not export a class");
}
"""


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
        "description": (
            "Memoria attention pane, status pill, and relate control — "
            "a thin renderer over the local engine."
        ),
        "author": "Memoria",
        "isDesktopOnly": True,
    }
    assert package["scripts"]["test"] == "node --test"
    assert (PLUGIN / "main.js").is_file()
    assert (PLUGIN / "schema.js").is_file()
    assert (PLUGIN / "styles.css").is_file()


def test_memoria_obsidian_seed_matches_release_artifacts() -> None:
    for artifact in SEED_PARITY_ARTIFACTS:
        assert (SEED_PLUGIN / artifact).read_text(encoding="utf-8") == (
            PLUGIN / artifact
        ).read_text(encoding="utf-8")


def test_memoria_obsidian_parity_roster_covers_every_shipped_module() -> None:
    """The roster above is a pin, so it has to be a *complete* pin.

    An eighth module added to the package and copied to the seed would sit
    outside `SEED_PARITY_ARTIFACTS` and drift with nothing to notice, exactly
    as `viewspec.js` did between U3-PLUG.4 and here. Enumerating the package
    rather than the seed is deliberate: the package is where a new module is
    authored, so this fails on the change that creates the gap.
    """
    assert {path.name for path in PLUGIN.glob("*.js")} <= set(SEED_PARITY_ARTIFACTS)


def test_memoria_obsidian_seeded_plugin_loads_every_module_it_requires(tmp_path: Path) -> None:
    """The vault gets a plugin that *runs*, not a file list that matches.

    Byte-equality between package and seed says nothing about whether the
    bundle writer ships the modules `main.js` requires: the seed directory can
    hold all seven while `bundles.BUNDLE_FILES["obsidian"]` copies four, and
    the vault then receives an entrypoint that throws MODULE_NOT_FOUND on the
    host's first load. So this runs the real writer and then really loads what
    it wrote.
    """
    workspace = tmp_path / "vault"
    workspace.mkdir()
    seed_bundles(workspace, bundle_names=["obsidian"])
    entrypoint = workspace / ".obsidian/plugins/memoria-obsidian/main.js"

    result = subprocess.run(
        ["node", "-e", _LOAD_PROBE, str(entrypoint)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


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


def _plugin_js_source() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in sorted(PLUGIN.glob("*.js")))


def test_memoria_obsidian_uses_memoria_operation_run_only() -> None:
    source = _plugin_js_source()

    assert '"/operation/run"' in source
    assert '"/v1/status"' in source
    assert '"/v1/views/attention"' in source
    assert "child_process" in source
    assert "requestUrl" in source
    assert "handshake" in source
    assert "fetch(" not in source
    assert "settings.serverUrl" not in source
    assert "settings.hasToken" not in source
    assert "secretStorage" not in source
    assert "setSecret" not in source
    assert ".getJson(" not in source
    assert ".updateStatus(" not in source
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
        "open-attention",
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
