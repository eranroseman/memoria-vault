"""Fast test-vault refresh repairs package-seeded files without a source scaffold."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "test_vault" / "refresh-test-vault.sh"


def _script() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_refresh_test_vault_helper_exists_and_is_executable():
    assert SCRIPT.is_file()
    assert SCRIPT.stat().st_mode & 0o111
    assert _script().startswith("#!/usr/bin/env bash\n")


def test_refresh_helper_preserves_runtime_state_by_repairing_seed_files():
    text = _script()
    assert ".memoria/.venv/bin/python" in text
    assert '-m pip install --quiet "$ROOT"' in text
    assert 'doctor --workspace "$VAULT" --repair' in text
    assert "rsync" not in text
    assert "vault-template" not in text
    assert "rm -rf" not in text


def test_refresh_helper_wires_only_the_git_hook():
    text = _script()
    assert ".git/hooks/pre-commit" in text
    assert ".githooks/pre-commit" in text
    for marker in (
        "system/dashboards",
        "system/incidents",
        "system/scripts",
        ".memoria/templates",
        "index.md",
        "bibliography.bib",
    ):
        assert marker not in text


def test_refresh_helper_has_no_profile_redeploy_mode():
    text = _script()
    assert "--profiles" not in text
    assert "--profiles-only" not in text
