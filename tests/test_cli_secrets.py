"""CLI contract tests for the secrets seam and `memoria secrets` verbs (spec 4b)."""

from __future__ import annotations

import getpass
import io
import json
import os
import sys
from pathlib import Path

import pytest

from memoria_vault import cli as cli_module
from memoria_vault.cli import main
from tests.cli_test_helpers import write_runner_provider_config

REGISTRY_NAMES = (
    "KILOCODE_API_KEY",
    "OPENALEX_API_KEY",
    "SEMANTIC_SCHOLAR_API_KEY",
    "PUBMED_API_KEY",
    "GITHUB_TOKEN",
    "NCBI_EMAIL",
)


def clear_registry_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in REGISTRY_NAMES:
        monkeypatch.delenv(name, raising=False)


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


def test_cli_secrets_list_reports_names_and_sources_never_values(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    seed_secrets_file(tmp_path, monkeypatch, "OPENALEX_API_KEY=super-secret\n")
    clear_registry_env(monkeypatch)
    try:
        rc = main(["secrets", "list", "--json"])
        captured = capsys.readouterr()
    finally:
        os.environ.pop("OPENALEX_API_KEY", None)

    payload = json.loads(captured.out)
    assert rc == 0
    assert "super-secret" not in captured.out
    assert "super-secret" not in captured.err
    rows = {row["name"]: row for row in payload["credentials"]}
    assert rows["OPENALEX_API_KEY"]["status"] == "set"
    assert rows["OPENALEX_API_KEY"]["source"] == "file"
    assert rows["NCBI_EMAIL"]["status"] == "unset"
    assert payload["path"] == str(tmp_path / "config" / "memoria" / "secrets.env")


def test_cli_secrets_list_marks_equal_inherited_environment_value_as_env(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    seed_secrets_file(tmp_path, monkeypatch, "OPENALEX_API_KEY=same-secret\n")
    clear_registry_env(monkeypatch)
    monkeypatch.setenv("OPENALEX_API_KEY", "same-secret")

    rc = main(["secrets", "list", "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    rows = {row["name"]: row for row in payload["credentials"]}
    assert rc == 0
    assert rows["OPENALEX_API_KEY"]["status"] == "set"
    assert rows["OPENALEX_API_KEY"]["source"] == "env"
    assert "same-secret" not in captured.out
    assert "same-secret" not in captured.err


def test_cli_secrets_list_uses_startup_snapshot_after_file_changes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    path = seed_secrets_file(tmp_path, monkeypatch, "OPENALEX_API_KEY=before-change\n")
    clear_registry_env(monkeypatch)
    real_handler = cli_module._cmd_secrets_list

    def change_file_then_list(args: object) -> int:
        path.write_text("OPENALEX_API_KEY=after-change\n", encoding="utf-8")
        return real_handler(args)

    monkeypatch.setattr(cli_module, "_cmd_secrets_list", change_file_then_list)
    try:
        rc = main(["secrets", "list", "--json"])
        captured = capsys.readouterr()
    finally:
        os.environ.pop("OPENALEX_API_KEY", None)

    payload = json.loads(captured.out)
    rows = {row["name"]: row for row in payload["credentials"]}
    assert rc == 0
    assert rows["OPENALEX_API_KEY"]["status"] == "set"
    assert rows["OPENALEX_API_KEY"]["source"] == "file"


def test_cli_secrets_list_marks_empty_environment_override_as_unset_env(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    seed_secrets_file(tmp_path, monkeypatch, "OPENALEX_API_KEY=file-secret\n")
    clear_registry_env(monkeypatch)
    monkeypatch.setenv("OPENALEX_API_KEY", "")

    rc = main(["secrets", "list", "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    rows = {row["name"]: row for row in payload["credentials"]}
    assert rc == 0
    assert rows["OPENALEX_API_KEY"]["status"] == "unset"
    assert rows["OPENALEX_API_KEY"]["source"] == "env"
    assert "file-secret" not in captured.out
    assert "file-secret" not in captured.err


def test_cli_secrets_list_ignores_current_directory_provider_config(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    write_runner_provider_config(workspace)
    monkeypatch.chdir(workspace)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    clear_registry_env(monkeypatch)

    rc = main(["secrets", "list", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert "KILOCODE_API_KEY" not in {row["name"] for row in payload["credentials"]}


def test_cli_secrets_list_reports_refused_file_warning_without_secret(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    seed_secrets_file(
        tmp_path,
        monkeypatch,
        "OPENALEX_API_KEY=private-secret\n",
        mode=0o644,
    )
    clear_registry_env(monkeypatch)

    rc = main(["secrets", "list", "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert rc == 0
    assert "world-readable" in payload["warning"]
    assert "private-secret" not in captured.out
    assert "private-secret" not in captured.err
