"""Contract checks for the contributor bootstrap."""

from pathlib import Path

import pytest

from tests.paths import ROOT

pytestmark = pytest.mark.static

SETUP = ROOT / "scripts/dev/setup.sh"
CONTRIBUTING = ROOT / "CONTRIBUTING.md"


def _single_spaced(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_dev_bootstrap_requests_mcp_extra_on_both_editable_install_paths() -> None:
    script = SETUP.read_text(encoding="utf-8")

    assert 'if "$PY" -m pip install --quiet -e ".[mcp]"; then' in script
    assert (
        "MCP SDK needed by local full verification is missing — "
        'run manually: $PY -m pip install -e \\".[mcp]\\"' in script
    )


def test_dev_bootstrap_describes_mcp_as_local_verification_support() -> None:
    script = _single_spaced(SETUP)

    assert "editable package and MCP SDK installed for local full verification" in script
    assert "does NOT install or run the Memoria product" in script


def test_contributor_setup_preserves_the_vault_runtime_install_boundary() -> None:
    guide = _single_spaced(CONTRIBUTING)

    assert "optional MCP SDK so `python scripts/verify` can exercise the MCP transport" in guide
    assert "does not install or run a vault-local Memoria runtime" in guide
