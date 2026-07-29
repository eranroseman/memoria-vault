"""Unit tests for the user-scope secrets file (bootstrap spec section 4b)."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from memoria_vault.runtime import secrets as secrets_module
from memoria_vault.runtime.secrets import (
    credential_report,
    load_secrets,
    read_secrets_file,
    secrets_path,
    write_secret,
)
from tests.cli_test_helpers import write_runner_provider_config

ALL_REGISTRY_NAMES = (
    "KILOCODE_API_KEY",
    "OPENALEX_API_KEY",
    "SEMANTIC_SCHOLAR_API_KEY",
    "PUBMED_API_KEY",
    "GITHUB_TOKEN",
    "NCBI_EMAIL",
)


def clear_registry_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ALL_REGISTRY_NAMES:
        monkeypatch.delenv(name, raising=False)


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


@pytest.mark.skipif(
    os.name != "posix" or not hasattr(os, "O_NOFOLLOW"),
    reason="POSIX no-follow semantics unavailable",
)
def test_read_secrets_file_refuses_symlink_target_without_loading_outside(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    target = secrets_path()
    target.parent.mkdir(parents=True)
    outside = tmp_path / "outside.env"
    outside.write_text("OPENALEX_API_KEY=outside-secret\n", encoding="utf-8")
    target.symlink_to(outside)

    values, warning = read_secrets_file()

    assert values == {}
    assert "outside-secret" not in warning
    assert "refusing to load" in warning
    assert outside.read_text(encoding="utf-8") == "OPENALEX_API_KEY=outside-secret\n"


@pytest.mark.skipif(
    os.name != "posix" or not hasattr(os, "O_NOFOLLOW"),
    reason="POSIX no-follow semantics unavailable",
)
def test_read_secrets_file_refuses_symlinked_memoria_parent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    target = secrets_path()
    target.parent.parent.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secrets.env").write_text("OPENALEX_API_KEY=outside-secret\n", encoding="utf-8")
    target.parent.symlink_to(outside, target_is_directory=True)

    values, warning = read_secrets_file()

    assert values == {}
    assert "outside-secret" not in warning
    assert "refusing to load" in warning


@pytest.mark.skipif(
    os.name != "posix" or not hasattr(os, "mkfifo"),
    reason="POSIX FIFO semantics unavailable",
)
def test_read_secrets_file_refuses_fifo_without_blocking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    target = secrets_path()
    target.parent.mkdir(parents=True)
    os.mkfifo(target)

    values, warning = read_secrets_file()

    assert values == {}
    assert "regular file" in warning


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


def test_credential_report_static_rows_without_workspace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    clear_registry_env(monkeypatch)

    rows = {row["name"]: row for row in credential_report(None)}

    assert rows["OPENALEX_API_KEY"] == {
        "name": "OPENALEX_API_KEY",
        "class": "enhancing",
        "status": "unset",
        "source": "",
        "effect_when_unset": "openalex keyless polite-pool mode (lower rate limits)",
    }
    assert rows["NCBI_EMAIL"]["class"] == "identity"
    assert rows["SEMANTIC_SCHOLAR_API_KEY"]["class"] == "enhancing"
    assert "KILOCODE_API_KEY" not in rows


def test_credential_report_skips_file_when_environment_resolves_static_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    clear_registry_env(monkeypatch)
    for name in ALL_REGISTRY_NAMES[1:]:
        monkeypatch.setenv(name, "env-value")

    def unexpected_file_read() -> tuple[dict[str, str], str]:
        pytest.fail("credential_report must not read a masked secrets file")

    monkeypatch.setattr(secrets_module, "read_secrets_file", unexpected_file_read)

    rows = credential_report(None)

    assert all(row["source"] == "env" for row in rows)


def test_credential_report_marks_equal_environment_value_as_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed_secrets_file(tmp_path, monkeypatch, "OPENALEX_API_KEY=file-key\n")
    clear_registry_env(monkeypatch)
    monkeypatch.setenv("OPENALEX_API_KEY", "file-key")

    report = load_secrets()
    rows = {row["name"]: row for row in credential_report(None, loaded_from_file=report["loaded"])}

    assert rows["OPENALEX_API_KEY"]["status"] == "set"
    assert rows["OPENALEX_API_KEY"]["source"] == "env"


def test_credential_report_marks_empty_environment_override_as_unset_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed_secrets_file(tmp_path, monkeypatch, "OPENALEX_API_KEY=file-key\n")
    clear_registry_env(monkeypatch)
    monkeypatch.setenv("OPENALEX_API_KEY", "")

    report = load_secrets()
    rows = {row["name"]: row for row in credential_report(None, loaded_from_file=report["loaded"])}

    assert rows["OPENALEX_API_KEY"]["status"] == "unset"
    assert rows["OPENALEX_API_KEY"]["source"] == "env"


def test_credential_report_marks_startup_loaded_file_as_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed_secrets_file(tmp_path, monkeypatch, "OPENALEX_API_KEY=file-key\n")
    clear_registry_env(monkeypatch)
    report = load_secrets()

    try:
        rows = {
            row["name"]: row for row in credential_report(None, loaded_from_file=report["loaded"])
        }
    finally:
        for name in report["loaded"]:
            os.environ.pop(name, None)

    assert rows["OPENALEX_API_KEY"]["status"] == "set"
    assert rows["OPENALEX_API_KEY"]["source"] == "file"


def test_credential_report_uses_load_snapshot_after_file_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = seed_secrets_file(tmp_path, monkeypatch, "OPENALEX_API_KEY=before-change\n")
    clear_registry_env(monkeypatch)
    report = load_secrets()

    try:
        path.write_text("OPENALEX_API_KEY=after-change\n", encoding="utf-8")
        rows = {
            row["name"]: row for row in credential_report(None, loaded_from_file=report["loaded"])
        }
    finally:
        for name in report["loaded"]:
            os.environ.pop(name, None)

    assert rows["OPENALEX_API_KEY"]["status"] == "set"
    assert rows["OPENALEX_API_KEY"]["source"] == "file"


def test_credential_report_derives_required_rows_from_workspace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    clear_registry_env(monkeypatch)
    write_runner_provider_config(tmp_path)

    rows = {row["name"]: row for row in credential_report(tmp_path)}

    required = rows["KILOCODE_API_KEY"]
    assert required["class"] == "required-for-operation"
    assert required["status"] == "unset"
    assert required["source"] == ""
    assert "refuse" in required["effect_when_unset"]
    assert "memoria secrets set KILOCODE_API_KEY" in required["effect_when_unset"]


def test_credential_report_tolerates_missing_provider_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    clear_registry_env(monkeypatch)

    rows = credential_report(tmp_path / "no-such-workspace")

    assert [row["name"] for row in rows] == [
        "OPENALEX_API_KEY",
        "SEMANTIC_SCHOLAR_API_KEY",
        "PUBMED_API_KEY",
        "GITHUB_TOKEN",
        "NCBI_EMAIL",
    ]


def test_credential_report_tolerates_malformed_provider_yaml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    clear_registry_env(monkeypatch)
    config = tmp_path / ".memoria/config/providers.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("runner_providers: [\n", encoding="utf-8")

    rows = credential_report(tmp_path, loaded_from_file=())

    assert [row["name"] for row in rows] == [
        "OPENALEX_API_KEY",
        "SEMANTIC_SCHOLAR_API_KEY",
        "PUBMED_API_KEY",
        "GITHUB_TOKEN",
        "NCBI_EMAIL",
    ]


def test_credential_report_hides_invalid_provider_key_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    clear_registry_env(monkeypatch)
    sentinel = "sk-live-pasted-secret"
    config = tmp_path / ".memoria/config/providers.yaml"
    config.parent.mkdir(parents=True)
    config.write_text(
        "\n".join(
            [
                "version: 1",
                "runner_providers:",
                "  local: {url: http://model.test/v1, key_env: null}",
                f"  gateway: {{url: https://gateway.test/v1, key_env: {sentinel}}}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    rows = credential_report(tmp_path, loaded_from_file=())

    assert [row["name"] for row in rows] == [
        "OPENALEX_API_KEY",
        "SEMANTIC_SCHOLAR_API_KEY",
        "PUBMED_API_KEY",
        "GITHUB_TOKEN",
        "NCBI_EMAIL",
    ]
    assert sentinel not in repr(rows)


def test_write_secret_creates_0600_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    path = write_secret("OPENALEX_API_KEY", "abc")

    assert path == secrets_path()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert path.read_text(encoding="utf-8") == "OPENALEX_API_KEY=abc\n"


def test_write_secret_upserts_and_repairs_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = seed_secrets_file(
        tmp_path,
        monkeypatch,
        "NCBI_EMAIL=old@example.test\nOPENALEX_API_KEY=keep\n",
        mode=0o644,
    )

    written = write_secret("NCBI_EMAIL", "new@example.test")

    assert written == path
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert path.read_text(encoding="utf-8") == (
        "NCBI_EMAIL=new@example.test\nOPENALEX_API_KEY=keep\n"
    )


@pytest.mark.parametrize(
    "value",
    ["   ", "two\nlines", "two\rlines", "two\u2028lines", "bad\0value"],
)
def test_write_secret_rejects_bad_names_and_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    with pytest.raises(ValueError, match="secret name must match"):
        write_secret("lower-case", "x")
    with pytest.raises(ValueError, match=r"non-empty|single line"):
        write_secret("GOOD_NAME", value)


def test_write_secret_rejects_invalid_name_without_echoing_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    invalid_name = "\x1b]8;;https://example.test\x1b\\"

    with pytest.raises(ValueError) as exc_info:
        write_secret(invalid_name, "value")

    assert invalid_name not in str(exc_info.value)


@pytest.mark.skipif(
    os.name != "posix" or not hasattr(os, "O_NOFOLLOW"),
    reason="POSIX no-follow semantics unavailable",
)
def test_write_secret_refuses_symlink_target_without_touching_outside(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    target = secrets_path()
    target.parent.mkdir(parents=True)
    outside = tmp_path / "outside.env"
    outside.write_text("OUTSIDE=unchanged\n", encoding="utf-8")
    target.symlink_to(outside)

    with pytest.raises(ValueError, match="must not redirect"):
        write_secret("OPENALEX_API_KEY", "new-value")

    assert outside.read_text(encoding="utf-8") == "OUTSIDE=unchanged\n"
    assert target.is_symlink()


@pytest.mark.skipif(
    os.name != "posix" or not hasattr(os, "O_NOFOLLOW"),
    reason="POSIX no-follow semantics unavailable",
)
def test_write_secret_refuses_symlinked_memoria_parent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    target = secrets_path()
    target.parent.parent.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    target.parent.symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="must not redirect"):
        write_secret("OPENALEX_API_KEY", "new-value")

    assert not (outside / "secrets.env").exists()


def test_write_secret_maps_platform_nofollow_errno_to_value_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    target = secrets_path()
    target.parent.mkdir(parents=True)
    real_open = os.open
    platform_eloop = 12345

    def nofollow_error(
        path: str | Path, flags: int, mode: int = 0o777, *, dir_fd: int | None = None
    ) -> int:
        if path == target.name and dir_fd is not None:
            raise OSError(platform_eloop, "simulated no-follow refusal")
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(secrets_module.errno, "ELOOP", platform_eloop)
    monkeypatch.setattr(secrets_module.os, "open", nofollow_error)

    with pytest.raises(ValueError, match="must not redirect"):
        write_secret("OPENALEX_API_KEY", "new-value")


def test_write_secret_refuses_nonregular_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    target = secrets_path()
    target.parent.mkdir(parents=True)
    target.mkdir()

    with pytest.raises(ValueError, match="regular file"):
        write_secret("OPENALEX_API_KEY", "new-value")


@pytest.mark.skipif(
    os.name != "posix" or not hasattr(os, "mkfifo"),
    reason="POSIX FIFO semantics unavailable",
)
def test_write_secret_refuses_fifo_without_blocking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    target = secrets_path()
    target.parent.mkdir(parents=True)
    os.mkfifo(target)

    with pytest.raises(ValueError, match="regular file"):
        write_secret("OPENALEX_API_KEY", "new-value")


def test_write_secret_retries_short_writes_and_stages_private_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = seed_secrets_file(tmp_path, monkeypatch, "OPENALEX_API_KEY=old-value\n", mode=0o644)
    real_write = os.write
    real_replace = secrets_module._replace_secret_atomically
    writes = 0

    def short_write(fd: int, body: bytes | memoryview) -> int:
        nonlocal writes
        writes += 1
        return real_write(fd, body[:1])

    def assert_private_stage(parent_fd: int, temp_name: str, target_name: str) -> None:
        assert stat.S_IMODE(os.stat(temp_name, dir_fd=parent_fd).st_mode) == 0o600
        real_replace(parent_fd, temp_name, target_name)

    monkeypatch.setattr(secrets_module.os, "write", short_write)
    monkeypatch.setattr(secrets_module, "_replace_secret_atomically", assert_private_stage)

    write_secret("OPENALEX_API_KEY", "new-value")

    assert writes > 1
    assert path.read_text(encoding="utf-8") == "OPENALEX_API_KEY=new-value\n"


@pytest.mark.parametrize("failure", ["write", "fsync", "replace"])
def test_write_secret_failure_keeps_prior_file_and_cleans_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    path = seed_secrets_file(tmp_path, monkeypatch, "OPENALEX_API_KEY=old-value\n", mode=0o644)

    def fail_write(_fd: int, _body: bytes | memoryview) -> int:
        raise OSError("disk full")

    def fail_fsync(_fd: int) -> None:
        raise OSError("sync failed")

    def fail_replace(*_args: object, **_kwargs: object) -> None:
        raise OSError("rename failed")

    if failure == "write":
        monkeypatch.setattr(secrets_module.os, "write", fail_write)
        expected = "disk full"
    elif failure == "fsync":
        monkeypatch.setattr(secrets_module.os, "fsync", fail_fsync)
        expected = "sync failed"
    else:
        monkeypatch.setattr(secrets_module.os, "replace", fail_replace)
        expected = "rename failed"

    with pytest.raises(OSError, match=expected):
        write_secret("OPENALEX_API_KEY", "later-value")

    assert path.read_text(encoding="utf-8") == "OPENALEX_API_KEY=old-value\n"
    assert not list(path.parent.glob(".secrets.*.tmp"))
