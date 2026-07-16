"""Server rendezvous state tests."""

from __future__ import annotations

import hashlib
import os
import stat
import sys
from pathlib import Path

import pytest

from memoria_vault.runtime import rendezvous


def test_vault_key_is_sha256_prefix_of_canonical_path(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    expected = hashlib.sha256(str(vault.resolve()).encode("utf-8")).hexdigest()[:16]

    assert rendezvous.vault_key(vault) == expected
    assert len(rendezvous.vault_key(vault)) == 16


def test_vault_key_distinguishes_case_on_case_sensitive_filesystems(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(rendezvous, "_case_insensitive_filesystem", lambda _path: False)
    upper = tmp_path / "VaultA"
    lower = tmp_path / "vaulta"
    upper.mkdir()
    lower.mkdir()

    assert rendezvous.vault_key(upper) != rendezvous.vault_key(lower)


def test_vault_key_casefolds_on_case_insensitive_filesystems(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(rendezvous, "_case_insensitive_filesystem", lambda _path: True)
    upper = tmp_path / "VaultA"
    upper.mkdir()

    assert rendezvous.vault_key(upper) == rendezvous.vault_key(tmp_path / "vaulta")


def test_case_probe_reports_case_sensitive_tmpdir(tmp_path: Path) -> None:
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    swapped = Path(str(probe_dir).swapcase())
    if swapped.exists():
        pytest.skip("temp filesystem is case-insensitive")

    assert rendezvous._case_insensitive_filesystem(probe_dir) is False


def test_state_root_linux_honors_xdg_state_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))

    assert rendezvous.state_root() == tmp_path / "state" / "memoria" / "vaults"


def test_state_root_linux_defaults_to_local_state(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))

    assert rendezvous.state_root() == tmp_path / ".local" / "state" / "memoria" / "vaults"


def test_state_root_darwin_uses_application_support(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setenv("HOME", str(tmp_path))

    expected = tmp_path / "Library" / "Application Support" / "Memoria" / "vaults"
    assert rendezvous.state_root() == expected


def test_state_root_windows_uses_localappdata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "AppData" / "Local"))

    assert rendezvous.state_root() == tmp_path / "AppData" / "Local" / "Memoria" / "vaults"


def test_vault_state_dir_is_keyed_and_private(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    state_dir = rendezvous.vault_state_dir(vault)

    assert state_dir == rendezvous.state_root() / rendezvous.vault_key(vault)
    assert state_dir.is_dir()
    if os.name == "posix":
        assert stat.S_IMODE(state_dir.stat().st_mode) == 0o700
