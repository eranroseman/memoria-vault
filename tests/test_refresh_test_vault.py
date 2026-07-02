"""Fast Memoria-test refresh helper keeps runtime state out of the blast radius."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "refresh-test-vault.sh"


def _script() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def _refresh_entries(sync_call: str) -> set[str]:
    match = re.search(
        rf"for rel in \\\n(?P<body>.*?)\ndo\n  {sync_call} \"\$rel\"", _script(), re.S
    )
    assert match, f"{sync_call} loop not found"
    return {
        line.strip().removesuffix("\\").strip()
        for line in match.group("body").splitlines()
        if line.strip()
    }


def test_refresh_test_vault_helper_exists_and_is_executable():
    assert SCRIPT.is_file()
    assert SCRIPT.stat().st_mode & 0o111
    assert _script().startswith("#!/usr/bin/env bash\n")


def test_refresh_helper_preserves_runtime_only_state():
    text = _script()
    for marker in (
        ".memoria/.venv/bin/python",
        "system/logs",
        "system/exports",
    ):
        assert marker in text
    assert 'rsync -a --delete "$SRC"/ "$VAULT"/' not in text


def test_refresh_helper_updates_source_owned_surfaces_and_golden_copy():
    text = _script()
    for marker in (
        "system/dashboards",
        "system/scripts",
        "system/templates",
        "capabilities",
        "spaces",
        "index.md",
        "catalog/catalog.base",
        "catalog/index.md",
        "knowledge/index.md",
        "knowledge/_views/index.md",
        "capabilities/index.md",
        "references.bib",
        "golden_restore",
        "stage",
    ):
        assert marker in text


def test_refresh_helper_removes_dropped_obsidian_payloads():
    text = _script()
    assert 'rm -rf "$VAULT/.obsidian" "$VAULT/system/scripts"' in text
    assert '"$SRC/.obsidian"/' not in text
    assert "obsidian-local-rest-api" not in text


def test_refresh_helper_has_no_profile_redeploy_mode():
    text = _script()
    assert "--profiles" not in text
    assert "--profiles-only" not in text
