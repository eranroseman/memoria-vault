"""Fast Memoria-test refresh helper keeps runtime state out of the blast radius."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "refresh-test-vault.sh"


def _script() -> str:
    return SCRIPT.read_text(encoding="utf-8")


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
        "plugins/agent-client/data.json",
        "plugins/obsidian-local-rest-api/data.json",
    ):
        assert marker in text
    assert 'rsync -a --delete "$SRC"/ "$VAULT"/' not in text


def test_refresh_helper_updates_source_owned_surfaces_and_golden_copy():
    text = _script()
    for marker in (
        "system/dashboards",
        "system/scripts",
        "system/templates",
        "spaces",
        "catalog/catalog.base",
        "inbox/inbox.base",
        "notes/hubs/hubs.base",
        "projects/projects.base",
        ".obsidian",
        "golden_restore.py",
        "stage",
    ):
        assert marker in text


def test_refresh_helper_redeploys_profiles_only_when_needed_by_default():
    text = _script()
    assert "--profiles auto|always|never" in text
    assert 'PROFILES="auto"' in text
    assert "diff -qr" in text
    assert "--profiles-only --yes --vault" in text
    assert "Profiles unchanged; skipping profiles-only redeploy." in text
