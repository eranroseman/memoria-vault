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
MIN_NODE_TESTS = 49
NODE_SUITE_FILES = (
    "test.mjs",
    "test-handshake.mjs",
    "test-pill.mjs",
    "test-relate.mjs",
    "test-viewspec.mjs",
)

# Byte-identical between the release package and the seed.
SEED_PARITY_ARTIFACTS = (
    "handshake.js",
    "main.js",
    "manifest.json",
    "pill.js",
    "relate.js",
    "schema.js",
    "styles.css",
    "viewspec.js",
)

# Loads every module the vault actually received, with `obsidian` stubbed
# because only the host provides it. Every *other* require -- `child_process`
# and the relative sibling modules -- resolves normally, so a module the vault
# did not receive raises MODULE_NOT_FOUND and this exits nonzero.
#
# It loads the whole seeded directory rather than only the entrypoint, because
# loading only the entrypoint proves whatever `main.js` happens to require this
# week: a module seeded one task before its consumer requires it (`relate.js`
# between U3-PLUG.5 and .8) would sit in the vault unproven, and a module
# dropped from `main.js`'s requires would silently take its proof with it.
_LOAD_PROBE = """
const fs = require("node:fs");
const path = require("node:path");
const Module = require("node:module");
const original = Module._load;
Module._load = (request, parent, isMain) =>
  request === "obsidian"
    ? new Proxy({}, { get: () => class HostStub {} })
    : original(request, parent, isMain);
const directory = process.argv[1];
const modules = fs.readdirSync(directory).filter((name) => name.endsWith(".js")).sort();
if (!modules.includes("main.js")) {
  throw new Error(`the seeded plugin has no entrypoint: ${modules.join(", ")}`);
}
for (const name of modules) {
  require(path.join(directory, name));
}
if (typeof require(path.join(directory, "main.js")) !== "function") {
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

    Stylesheets are covered by the same roster from
    `..._has_no_hardcoded_colors`, which pins the files its sweep read against
    this roster; extending the subset check here as well was measured and
    changed nothing.
    """
    assert {path.name for path in PLUGIN.glob("*.js")} <= set(SEED_PARITY_ARTIFACTS)


def test_memoria_obsidian_seeded_plugin_loads_every_module_it_requires(tmp_path: Path) -> None:
    """The vault gets a plugin that *runs*, not a file list that matches.

    Byte-equality between package and seed says nothing about whether the
    bundle writer ships the modules `main.js` requires: the seed directory can
    hold all eight while `bundles.BUNDLE_FILES["obsidian"]` copies four, and
    the vault then receives an entrypoint that throws MODULE_NOT_FOUND on the
    host's first load. So this runs the real writer and then really loads what
    it wrote.
    """
    workspace = tmp_path / "vault"
    workspace.mkdir()
    seed_bundles(workspace, bundle_names=["obsidian"])
    seeded = workspace / ".obsidian/plugins/memoria-obsidian"

    result = subprocess.run(
        ["node", "-e", _LOAD_PROBE, str(seeded)],
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

    Scanning the package alone covers the seeded copy too, and that is a chain
    rather than an omission: every `*.js` and `*.css` here is inside
    `SEED_PARITY_ARTIFACTS` (`..._parity_roster_covers_every_shipped_module`),
    and every entry of that roster is compared byte-for-byte against the seed
    (`..._seed_matches_release_artifacts`), so a color that reaches only the
    seeded copy breaks parity instead of hiding behind this sweep.
    """
    scanned = sorted(PLUGIN.glob("*.js")) + sorted(PLUGIN.glob("*.css"))

    # A sweep that reads no files reports no findings. Pin what it must have read.
    assert {path.name for path in scanned} == {
        name for name in SEED_PARITY_ARTIFACTS if name.endswith((".js", ".css"))
    }
    findings = [
        finding
        for path in scanned
        for finding in _hardcoded_colors(path.name, path.read_text(encoding="utf-8"))
    ]
    assert findings == []


def test_memoria_obsidian_registers_minimal_proof_commands() -> None:
    source = (PLUGIN / "main.js").read_text(encoding="utf-8")

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
    source = (PLUGIN / "main.js").read_text(encoding="utf-8")

    assert "fork-project-canvas" in source
    assert "/project/canvas/forks" in source
    assert "curate-note-link" in source
    assert "graduate:" in source
    assert "Memoria: Fork canvas to scratch" in source
    assert "Memoria: Graduate scratch canvas edges" in source
    assert "this.authedJson(" in source
    assert "this.forkBadge" in source


def test_memoria_obsidian_registers_the_canvas_commands() -> None:
    source = (PLUGIN / "main.js").read_text(encoding="utf-8")

    for command_id in ("fork-canvas", "graduate-scratch-edges"):
        assert f'id: "{command_id}"' in source
