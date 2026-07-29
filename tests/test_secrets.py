"""Unit tests for the user-scope secrets file (bootstrap spec section 4b)."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from memoria_vault.runtime import secrets as secrets_module
from memoria_vault.runtime.secrets import (
    load_secrets,
    read_secrets_file,
    secrets_path,
    write_secret,
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
