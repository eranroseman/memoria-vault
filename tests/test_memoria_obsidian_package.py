from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

from memoria_vault.runtime.bundles import seed_bundles
from tests.helpers import ROOT

pytestmark = pytest.mark.contract

PLUGIN = ROOT / "packages" / "memoria-obsidian"
SOURCE = PLUGIN / "src"
SEED_PLUGIN = ROOT / (
    "src/memoria_vault/product/workspace_seed/"
    ".obsidian/plugins/memoria-obsidian"
)
SOURCE_MODULES = (
    "handshake.js",
    "main.js",
    "pill.js",
    "relate.js",
    "schema.js",
    "viewspec.js",
)
RELEASE_ARTIFACTS = ("main.js", "manifest.json", "styles.css")

# `node --test` discovers files by name, and it exits 0 when it discovers none.
# So the exit code alone cannot tell a green suite from a suite that silently
# stopped running: rename a file out of the glob and every assertion in it
# disappears with the gate still green. These pin what must have run.
#
# Raise this in the same change that adds a suite -- slack here is exactly the
# room a gutted suite hides in. Measured 55 on both node 22 (mise.toml, CI) and
# node 24.
MIN_NODE_TESTS = 55
NODE_SUITE_FILES = (
    "test.mjs",
    "test-handshake.mjs",
    "test-pill.mjs",
    "test-relate.mjs",
    "test-viewspec.mjs",
)

_LOAD_PROBE = """
import { createRequire } from "node:module";
import path from "node:path";
const require = createRequire(import.meta.url);
const Module = require("node:module");
class Plugin {
  constructor() {
    this.app = {
      vault: { adapter: { basePath: "/tmp/memoria-plugin-test" } },
      workspace: { onLayoutReady() {} },
    };
  }
  async loadData() { return null; }
  addStatusBarItem() {
    return { empty() {}, createEl() { return {}; }, setText() {} };
  }
  addSettingTab() {}
  addCommand() {}
  register() {}
  registerView() {}
}
const original = Module._load;
Module._load = (request, parent, isMain) =>
  request === "obsidian"
    ? {
        Plugin,
        AbstractInputSuggest: class {},
        ItemView: class {},
        Modal: class {},
        Notice: class {},
        PluginSettingTab: class {},
        Setting: class {},
        requestUrl: async () => ({}),
      }
    : original(request, parent, isMain);
const directory = process.argv[1];
const PluginClass = require(path.join(directory, "main.js"));
if (typeof PluginClass !== "function") {
  throw new Error("plugin entrypoint did not export a class");
}
await new PluginClass().onload();
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
        ["node", "--test", "--experimental-test-isolation=none", "--test-reporter=tap"],
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
    assert package["scripts"] == {
        "build": "node scripts/build.mjs",
        "check": "node scripts/build.mjs --check",
        "test": "node --test",
    }
    assert {path.name for path in SOURCE.glob("*.js")} == set(SOURCE_MODULES)
    assert {path.name for path in SEED_PLUGIN.iterdir() if path.is_file()} == set(RELEASE_ARTIFACTS)


def test_memoria_obsidian_committed_release_artifact_is_current() -> None:
    result = subprocess.run(
        ["npm", "run", "check"],
        cwd=PLUGIN,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_memoria_obsidian_seeded_release_artifact_loads_without_sibling_modules(tmp_path: Path) -> None:
    workspace = tmp_path / "vault"
    workspace.mkdir()
    seed_bundles(workspace, bundle_names=["obsidian"])
    seeded = workspace / ".obsidian/plugins/memoria-obsidian"
    assert {path.name for path in seeded.iterdir() if path.is_file()} == set(RELEASE_ARTIFACTS)
    assert 'require("./' not in (seeded / "main.js").read_text(encoding="utf-8")

    result = subprocess.run(
        ["node", "--input-type=module", "-e", _LOAD_PROBE, str(seeded)],
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

    present = sorted(path.name for path in (PLUGIN / "scripts").glob("test*.mjs"))
    assert set(NODE_SUITE_FILES) <= set(present), present
    # A suite named outside the runner's glob never runs and never complains.
    assert [name for name in present if not _is_discoverable(name)] == []


def _plugin_js_source() -> str:
    return "\n".join((SOURCE / name).read_text(encoding="utf-8") for name in SOURCE_MODULES)


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
    # The relate modal's help, pinned to the substance the 2026-07-29 amendment
    # fixed: a `warrant` relation and Warrant text are different things, and a
    # PI told otherwise writes request prose where promotion-ready edge data
    # belongs. The wording is the product, so it is pinned as a literal.
    assert (
        "A `warrant` relation links a license note; Warrant text annotates the selected edge."
    ) in source


_COLOR_LITERAL = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")


def _hardcoded_colors(name: str, text: str) -> list[str]:
    """Report every hardcoded color literal in `text`, one line per hit."""
    return [
        f"{name}:{number}: hardcoded color {match.group(0)!r}"
        for number, line in enumerate(text.splitlines(), 1)
        if (match := _COLOR_LITERAL.search(line))
    ]


def test_memoria_obsidian_color_detector_reports_every_forbidden_literal() -> None:
    """The sweep below runs over clean sources, so the detector must be shown to bite.

    `findings == []` over files that contain no colors passes just as happily
    with a pattern that can never match anything: the theme-breaking palette
    this gate exists to stop would walk straight past a typo in the regex, and
    nothing in the repository would notice. So the detector is exercised on the
    forms U3 §9 forbids, against the theme variables it must leave alone, with
    the reported line numbers pinned -- a lint that names the wrong line costs
    the reader the search it was supposed to save. Line 2 is why the pattern
    ends its hex run on a word boundary: no CSS color is longer than eight hex
    digits, so a longer `#` token is an id or a JS private field and reporting
    a prefix of it would be a false positive.
    """
    source = (
        "  color: var(--text-muted);\n"
        "#deadbeefcafe { border-color: var(--interactive-accent); }\n"
        "  background-color: transparent;\n"
        "  color: #fff;\n"
        "  border-color: #1A2b3C;\n"
        "  outline-color: #aabbccdd;\n"
        "  color: rgb(0, 0, 0);\n"
        "  background: rgba(0, 0, 0, 0.5);\n"
        "  color: hsl(210, 40%, 50%);\n"
        "  background: hsla(210, 40%, 50%, 0.5);\n"
        'const dot = element.createSpan({ cls: "memoria-pill-dot" });\n'
    )

    assert _hardcoded_colors("styles.css", source) == [
        "styles.css:4: hardcoded color '#fff'",
        "styles.css:5: hardcoded color '#1A2b3C'",
        "styles.css:6: hardcoded color '#aabbccdd'",
        "styles.css:7: hardcoded color 'rgb('",
        "styles.css:8: hardcoded color 'rgba('",
        "styles.css:9: hardcoded color 'hsl('",
        "styles.css:10: hardcoded color 'hsla('",
    ]


def test_memoria_obsidian_has_no_hardcoded_colors() -> None:
    """U3 acceptance: the plugin contains zero hardcoded colors (theme vars only).

    The sweep reads every canonical source module plus the package stylesheet.
    """
    scanned = [(SOURCE / name) for name in SOURCE_MODULES] + [PLUGIN / "styles.css"]

    # A sweep that reads no files reports no findings. Pin what it must have read.
    assert {path.name for path in scanned} == set(SOURCE_MODULES) | {"styles.css"}
    findings = [
        finding
        for path in scanned
        for finding in _hardcoded_colors(path.name, path.read_text(encoding="utf-8"))
    ]
    assert findings == []


def test_memoria_obsidian_registers_minimal_proof_commands() -> None:
    source = (SOURCE / "main.js").read_text(encoding="utf-8")

    for command_id in (
        "open-attention",
        "open-evidence-review",
        "relate",
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


def test_memoria_obsidian_canvas_surface_is_enqueue_and_read_only() -> None:
    """The canvas surface adds two commands and one read, and writes nothing.

    Behaviour lives in the node suite; this pins the shape the seed ships —
    the two operation ids the commands enqueue, the one read route the badge
    polls, and the per-edge idempotency prefix that makes a re-run coalesce
    instead of duplicating edges. The no-file-write claims are already swept
    over every plugin module by `..._uses_memoria_operation_run_only`.
    """
    source = (SOURCE / "main.js").read_text(encoding="utf-8")

    assert "fork-project-canvas" in source
    assert "/project/canvas/forks" in source
    assert "curate-note-link" in source
    assert "graduate:" in source
    assert "Memoria: Fork canvas to scratch" in source
    assert "Memoria: Graduate scratch canvas edges" in source
    assert "this.authedJson(" in source
    assert "this.forkBadge" in source


def test_memoria_obsidian_registers_the_canvas_commands() -> None:
    source = (SOURCE / "main.js").read_text(encoding="utf-8")

    for command_id in ("fork-canvas", "graduate-scratch-edges"):
        assert f'id: "{command_id}"' in source


def test_schema_js_enums_stay_a_subset_of_the_engine_roster() -> None:
    """No plugin enum value may be one the engine would reject.

    `schema.js` is a hand-authored narrowing of the engine's empirical-event
    roster, not a generated mirror: it drops what an Obsidian client cannot
    legitimately submit (`SURFACES` is `obsidian` alone; `WORKFLOWS` omits
    `attention`, which only the server-authored `read-observed.v1` telemetry
    emits). Nothing pinned that relationship, so an engine-side rename would
    leave the plugin validating against a value the engine no longer accepts --
    and the plugin's own validator would still pass it, so the break would
    surface only when a real user's event is rejected over the wire. Subset,
    never equality: widening the engine roster must stay free.
    """
    from memoria_vault.engine import empirical_events as engine

    source = (SOURCE / "schema.js").read_text(encoding="utf-8")

    for name in ("SURFACES", "WORKFLOWS", "DECISIONS", "OUTCOMES", "REASON_CODES"):
        match = re.search(rf"const {name} = new Set\(\[(.*?)\]\)", source, re.S)
        assert match, f"{name} not found in schema.js"
        plugin_values = set(re.findall(r'"([^"]+)"', match.group(1)))
        assert plugin_values, f"{name} parsed empty -- the regex, not the roster, is wrong"
        unknown = sorted(plugin_values - set(getattr(engine, name)))
        assert not unknown, f"schema.js {name} has values the engine rejects: {unknown}"
