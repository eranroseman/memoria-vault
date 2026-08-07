"""The mermaid fence gate: parse published diagrams before readers see them.

Just the Docs renders mermaid client-side, so a malformed fence produces no
build error and no failing test -- only an error box on the published page.
`docs/` carries the only ungated authored surface otherwise: prose has
markdownlint, cspell, and vale; diagrams had nothing.

The config tests below need no Node. They are the ones that matter most: a gate
parsing a different mermaid version than the site renders is worse than no gate,
so the hook's pin and `docs/_config.yml`'s pin are asserted equal here.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from tests.paths import ROOT

pytestmark = pytest.mark.static

GATE = ROOT / "scripts/checks/mermaid_parse.mjs"
PRECOMMIT = ROOT / ".pre-commit-config.yaml"
SITE_CONFIG = ROOT / "docs/_config.yml"

VALID = """# Page

```mermaid
flowchart LR
    a["Start"] --> b["End"]
```
"""

# `-->` with no target: mermaid rejects this, a human skimming may not.
BROKEN = """# Page

```mermaid
flowchart LR
    a["Start"] -->
```
"""


def _hook() -> dict:
    config = yaml.safe_load(PRECOMMIT.read_text(encoding="utf-8"))
    hooks = [h for repo in config["repos"] for h in repo["hooks"] if h["id"] == "mermaid-parse"]
    assert len(hooks) == 1, "expected exactly one mermaid-parse pre-commit hook"
    return hooks[0]


def _pinned_mermaid() -> str:
    for dep in _hook()["additional_dependencies"]:
        if dep.startswith("mermaid@"):
            return dep.split("@", 1)[1]
    raise AssertionError("mermaid-parse hook pins no mermaid version")


def _run(*paths: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["node", str(GATE), *[str(p) for p in paths]],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


def _deps_installed() -> bool:
    if shutil.which("node") is None:
        return False
    probe = subprocess.run(
        ["node", "--input-type=module", "-e", "import('mermaid');import('jsdom')"],
        capture_output=True,
        cwd=ROOT,
    )
    return probe.returncode == 0


needs_deps = pytest.mark.skipif(
    not _deps_installed(), reason="mermaid/jsdom not installed outside the pre-commit env"
)


def test_hook_is_wired_and_pins_its_dependencies() -> None:
    hook = _hook()
    assert hook["language"] == "node"
    assert all("@" in dep for dep in hook["additional_dependencies"]), (
        "every node dependency must be version-pinned, as the other node hooks are"
    )


def test_gate_parses_the_same_mermaid_version_the_site_renders() -> None:
    """The gate's whole value depends on this. Drift here makes it lie."""
    site = yaml.safe_load(SITE_CONFIG.read_text(encoding="utf-8"))["mermaid"]["version"]

    assert _pinned_mermaid() == site, (
        f"hook pins mermaid {_pinned_mermaid()}, docs/_config.yml renders {site}; "
        "a gate that parses a different version than the site renders is worse than none"
    )


@needs_deps
def test_gate_accepts_a_valid_fence(tmp_path: Path) -> None:
    page = tmp_path / "ok.md"
    page.write_text(VALID, encoding="utf-8")

    result = _run(page)

    assert result.returncode == 0, result.stdout + result.stderr


@needs_deps
def test_gate_rejects_a_malformed_fence_and_names_the_file(tmp_path: Path) -> None:
    page = tmp_path / "broken.md"
    page.write_text(BROKEN, encoding="utf-8")

    result = _run(page)

    assert result.returncode == 1
    assert "broken.md" in result.stdout + result.stderr


@needs_deps
def test_gate_parses_every_published_diagram_in_the_repo() -> None:
    """The gate doing its day job against the real corpus."""
    pages = [
        path
        for path in sorted((ROOT / "docs").rglob("*.md"))
        if "superpowers" not in path.parts and "```mermaid" in path.read_text(encoding="utf-8")
    ]
    assert pages, "expected published pages carrying mermaid fences"

    result = _run(*pages)

    assert result.returncode == 0, result.stdout + result.stderr
