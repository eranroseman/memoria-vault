from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "install-test-vault-local-llm.sh"


def _script() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_local_llm_full_install_harness_exists_and_is_executable() -> None:
    assert SCRIPT.is_file()
    assert SCRIPT.stat().st_mode & 0o111
    assert _script().startswith("#!/usr/bin/env bash\n")


def test_harness_uses_child_vault_and_refuses_unsafe_wipes() -> None:
    text = _script()
    assert 'TEST_ROOT="${MEMORIA_TEST_ROOT:-$HOME/Memoria-test}"' in text
    assert 'VAULT="${MEMORIA_TEST_VAULT:-$TEST_ROOT/vault}"' in text
    assert "--vault must be below --root; refusing to wipe $VAULT" in text
    assert "--vault must be a child of --root" in text
    assert 'rm -rf "$VAULT"' in text


def test_harness_runs_real_installer_with_local_model_overlay() -> None:
    text = _script()
    for marker in (
        "MEMORIA_ENV=test",
        "MEMORIA_MODEL_PROVIDER=custom",
        'MEMORIA_MODEL_BASE_URL="$BASE_URL"',
        'MEMORIA_MODEL_NAME="$MODEL"',
        'MEMORIA_MODEL_CONTEXT_LENGTH="$CONTEXT"',
        'bash "$ROOT/scripts/install.sh" --with-hermes --vault "$VAULT" --no-apps --yes',
    ):
        assert marker in text


def test_harness_initializes_git_before_install_and_exercises_commit_gate() -> None:
    text = _script()
    assert text.index('git -C "$VAULT" init -q') < text.index('bash "$ROOT/scripts/install.sh"')
    assert 'git -C "$VAULT" add -A' in text
    assert 'git -C "$VAULT" commit -qm "Initial Memoria test vault"' in text
    assert text.index('\npause_memoria_crons\n\nhdr "Rebuild disposable vault"') < text.index(
        'rm -rf "$VAULT"'
    )
    assert text.index(
        '\nresume_memoria_crons\n\nPY="$VAULT/.memoria/.venv/bin/python"'
    ) > text.index('commit -qm "Initial Memoria test vault"')


def test_harness_runs_integrity_and_live_l2_smoke() -> None:
    text = _script()
    for marker in (
        "golden_restore.py",
        "detectors.py",
        "hermes profile list",
        "hermes cron list",
        "MEMORIA_L2_USE_SMOKE_MODEL=0",
        'bash "$ROOT/scripts/test-l2.sh" --real-model',
        "L2 real-model smoke failed once; retrying.",
        "--skip-live-llm",
    ):
        assert marker in text
