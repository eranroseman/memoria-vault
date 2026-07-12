from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "test_vault" / "install-test-vault-local-llm.sh"


def _script() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_local_llm_full_install_harness_exists_and_is_executable() -> None:
    assert SCRIPT.is_file()
    assert SCRIPT.stat().st_mode & 0o111
    assert _script().startswith("#!/usr/bin/env bash\n")


def test_harness_uses_test_vault_as_root_and_refuses_unsafe_wipes() -> None:
    text = _script()
    assert 'TEST_ROOT="${MEMORIA_TEST_ROOT:-$HOME/memoria-vault/test-vault}"' in text
    assert 'VAULT="${MEMORIA_TEST_VAULT:-$TEST_ROOT}"' in text
    assert "--vault may not be above --root" in text
    assert 'rm -rf "$VAULT"' in text


def test_harness_runs_standalone_installer_without_profile_adapter() -> None:
    text = _script()
    for marker in (
        "MEMORIA_ENV=test",
        'bash "$ROOT/scripts/install.sh" --vault "$VAULT" --yes',
        "--check-local-llm",
        "does not install external agent profiles",
    ):
        assert marker in text
    for stale in (
        "--with-hermes",
        "--no-apps",
        "hermes profile list",
        "hermes cron list",
    ):
        assert stale not in text


def test_harness_initializes_git_before_install_and_exercises_commit_gate() -> None:
    text = _script()
    assert text.index('git -C "$VAULT" init -q') < text.index('bash "$ROOT/scripts/install.sh"')
    assert 'git -C "$VAULT" add -A' in text
    assert 'git -C "$VAULT" diff --cached --quiet' in text
    assert "baseline already committed by installer" in text
    assert 'git -C "$VAULT" commit -qm "Initial Memoria test workspace"' in text


def test_harness_runs_integrity_and_cli_doctor_checks() -> None:
    text = _script()
    for marker in (
        "memoria_vault.cli doctor bundle",
        "detectors",
        "verdict: PASS",
        "Disposable Memoria standalone install verified",
    ):
        assert marker in text
