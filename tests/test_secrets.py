"""Unit tests for the user-scope secrets file (bootstrap spec section 4b)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from memoria_vault.runtime.secrets import (
    load_secrets,
    read_secrets_file,
    secrets_path,
)


def seed_secrets_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    text: str,
    mode: int = 0o600,
) -> Path:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    path = secrets_path()
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(mode)
    return path


def test_secrets_path_honors_xdg_config_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    assert secrets_path() == tmp_path / "config" / "memoria" / "secrets.env"


def test_secrets_path_defaults_to_home_dot_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))

    assert secrets_path() == tmp_path / ".config" / "memoria" / "secrets.env"


def test_secrets_path_rejects_relative_xdg_config_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", "relative-config")
    monkeypatch.setenv("HOME", str(tmp_path))

    assert secrets_path() == tmp_path / ".config" / "memoria" / "secrets.env"


def test_read_secrets_file_parses_env_lines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed_secrets_file(
        tmp_path,
        monkeypatch,
        "# comment\n"
        "OPENALEX_API_KEY=abc\n"
        'NCBI_EMAIL="pi@example.test"\n'
        "not a key value line\n"
        "lower_case=ignored\n",
    )

    values, warning = read_secrets_file()

    assert values == {"OPENALEX_API_KEY": "abc", "NCBI_EMAIL": "pi@example.test"}
    assert warning == ""


def test_read_secrets_file_refuses_world_readable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = seed_secrets_file(tmp_path, monkeypatch, "OPENALEX_API_KEY=abc\n", mode=0o644)

    values, warning = read_secrets_file()

    assert values == {}
    assert "world-readable" in warning
    assert str(path) in warning
    assert f"chmod 600 {path}" in warning


def test_read_secrets_file_absent_is_empty_and_quiet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    assert read_secrets_file() == ({}, "")


@pytest.mark.parametrize("payload", [None, b"OPENALEX_API_KEY=\xff\n"])
def test_read_secrets_file_refuses_nontext_or_nonregular_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, payload: bytes | None
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    path = secrets_path()
    path.parent.mkdir(parents=True)
    if payload is None:
        path.mkdir()
        path.chmod(0o700)
    else:
        path.write_bytes(payload)
        path.chmod(0o600)

    values, warning = read_secrets_file()

    assert values == {}
    assert str(path) in warning
    assert "refusing to load" in warning


def test_load_secrets_merges_under_process_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = seed_secrets_file(
        tmp_path,
        monkeypatch,
        "OPENALEX_API_KEY=from-file\nNCBI_EMAIL=file@example.test\n",
    )
    env = {"OPENALEX_API_KEY": ""}

    report = load_secrets(env)

    assert env == {
        "OPENALEX_API_KEY": "",
        "NCBI_EMAIL": "file@example.test",
    }
    assert report == {"path": str(path), "loaded": ["NCBI_EMAIL"], "warning": ""}


def test_load_secrets_skips_nul_values(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = seed_secrets_file(
        tmp_path,
        monkeypatch,
        "BROKEN=value\0with-nul\nNCBI_EMAIL=pi@example.test\n",
    )
    monkeypatch.delenv("BROKEN", raising=False)
    monkeypatch.delenv("NCBI_EMAIL", raising=False)

    report = load_secrets()

    assert os.environ["NCBI_EMAIL"] == "pi@example.test"
    assert "BROKEN" not in os.environ
    assert report == {"path": str(path), "loaded": ["NCBI_EMAIL"], "warning": ""}


def test_load_secrets_refused_file_loads_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed_secrets_file(tmp_path, monkeypatch, "OPENALEX_API_KEY=abc\n", mode=0o604)
    env: dict[str, str] = {}

    report = load_secrets(env)

    assert env == {}
    assert report["loaded"] == []
    assert "world-readable" in report["warning"]
