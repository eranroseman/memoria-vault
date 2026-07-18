"""CLI contract tests for the secrets seam and `memoria secrets` verbs (spec 4b)."""

from __future__ import annotations

import json
import os
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
