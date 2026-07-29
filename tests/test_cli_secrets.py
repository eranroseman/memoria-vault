"""CLI contract tests for the secrets seam and `memoria secrets` verbs (spec 4b)."""

from __future__ import annotations

import getpass
import io
import json
import os
import sys
from pathlib import Path

import pytest

from memoria_vault.cli import main


def seed_secrets_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    text: str,
    mode: int = 0o600,
) -> Path:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    path = tmp_path / "config" / "memoria" / "secrets.env"
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(mode)
    return path


def test_main_loads_secrets_file_under_process_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    seed_secrets_file(tmp_path, monkeypatch, "MEMORIA_TEST_SENTINEL_KEY=from-file\n")
    monkeypatch.delenv("MEMORIA_TEST_SENTINEL_KEY", raising=False)

    try:
        result = main(["init", "--workspace", str(tmp_path / "ws"), "--yes", "--json"])
        captured = capsys.readouterr()

        assert result == 0
        assert os.environ["MEMORIA_TEST_SENTINEL_KEY"] == "from-file"
        assert captured.err == ""
        assert json.loads(captured.out)["ok"] is True
    finally:
        os.environ.pop("MEMORIA_TEST_SENTINEL_KEY", None)


def test_main_process_env_wins_over_secrets_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed_secrets_file(tmp_path, monkeypatch, "MEMORIA_TEST_SENTINEL_KEY=from-file\n")
    monkeypatch.setenv("MEMORIA_TEST_SENTINEL_KEY", "from-env")

    result = main(["init", "--workspace", str(tmp_path / "ws"), "--yes", "--json"])

    assert result == 0
    assert os.environ["MEMORIA_TEST_SENTINEL_KEY"] == "from-env"


def test_main_warns_and_refuses_world_readable_secrets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    seed_secrets_file(
        tmp_path,
        monkeypatch,
        "MEMORIA_TEST_SENTINEL_KEY=from-file\n",
        mode=0o644,
    )
    monkeypatch.delenv("MEMORIA_TEST_SENTINEL_KEY", raising=False)

    result = main(["init", "--workspace", str(tmp_path / "ws"), "--yes", "--json"])
    captured = capsys.readouterr()

    assert result == 0
    assert "memoria: secrets file" in captured.err
    assert "world-readable" in captured.err
    assert "MEMORIA_TEST_SENTINEL_KEY" not in os.environ


def test_cli_secrets_set_creates_0600_file_and_never_echoes_value(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setattr(sys, "stdin", io.StringIO("secret-value\n"))

    rc = main(["secrets", "set", "OPENALEX_API_KEY", "--json"])

    captured = capsys.readouterr()
    path = tmp_path / "config" / "memoria" / "secrets.env"
    assert rc == 0
    assert json.loads(captured.out) == {
        "ok": True,
        "name": "OPENALEX_API_KEY",
        "path": str(path),
    }
    assert "secret-value" not in captured.out
    assert "secret-value" not in captured.err
    assert (path.stat().st_mode & 0o777) == 0o600
    assert path.read_text(encoding="utf-8") == "OPENALEX_API_KEY=secret-value\n"


def test_cli_secrets_set_rejects_invalid_name_without_echoing_value(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setattr(sys, "stdin", io.StringIO("secret-value\n"))

    rc = main(["secrets", "set", "lower-case", "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 2
    assert payload["ok"] is False
    assert "secret name must match" in payload["error"]
    assert "secret-value" not in captured.out
    assert "secret-value" not in captured.err


def test_cli_secrets_set_rejects_terminal_control_name_before_prompt(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    invalid_name = "\x1b]8;;https://example.test\x1b\\"
    prompts: list[str] = []

    class TtyInput:
        def isatty(self) -> bool:
            return True

    def unexpected_prompt(prompt: str) -> str:
        prompts.append(prompt)
        return "secret-value"

    monkeypatch.setattr(sys, "stdin", TtyInput())
    monkeypatch.setattr(getpass, "getpass", unexpected_prompt)

    rc = main(["secrets", "set", invalid_name, "--json"])

    captured = capsys.readouterr()
    assert rc == 2
    assert prompts == []
    assert invalid_name not in captured.out
    assert invalid_name not in captured.err
