"""Fast sandbox refresh helper keeps runtime state out of the blast radius."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "sandbox" / "refresh-test-vault.sh"


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
        "corpus roots",
        "active inbox projections",
    ):
        assert marker in text
    assert 'rsync -a --delete "$SRC"/ "$VAULT"/' not in text


def test_refresh_helper_updates_source_owned_surfaces():
    text = _script()
    for marker in (
        "system/dashboards",
        "system/incidents",
        "system/metrics",
        "system/scripts",
        "system/templates",
        ".git/hooks/pre-commit",
        "PYTHONPATH_VALUE",
        "index.md",
        "bibliography.bib",
    ):
        assert marker in text


def test_refresh_helper_removes_dropped_obsidian_payloads():
    text = _script()
    assert '"$VAULT/catalog" "$VAULT/knowledge" "$VAULT/spaces" "$VAULT/references.bib"' in text
    assert '"$SRC/.obsidian"/' not in text
    assert "obsidian-local-rest-api" not in text


def test_refresh_helper_has_no_profile_redeploy_mode():
    text = _script()
    assert "--profiles" not in text
    assert "--profiles-only" not in text
