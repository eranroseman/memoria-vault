"""Server rendezvous state tests."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from memoria_vault import __version__
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


def _runtime_record(
    vault: Path,
    *,
    port: int = 43210,
    pid: int | None = None,
    boot_id: str = "boot-1",
    token: str = "test-token",
) -> dict[str, object]:
    return {
        "vault_path": str(vault),
        "vault_id": "vault-1",
        "port": port,
        "pid": os.getpid() if pid is None else pid,
        "boot_id": boot_id,
        "token": token,
        "engine_version": __version__,
        "started_at": "2026-07-15T00:00:00Z",
    }


def test_runtime_roundtrip_is_atomic_and_private(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    state_dir = rendezvous.vault_state_dir(vault)

    written = rendezvous.write_runtime(state_dir, _runtime_record(vault))

    assert written == state_dir / "runtime.json"
    if os.name == "posix":
        assert stat.S_IMODE(written.stat().st_mode) == 0o600
    assert not list(state_dir.glob("*.tmp"))
    record = rendezvous.read_runtime(state_dir)
    assert record is not None
    assert record["schema"] == "memoria-runtime.v1"
    assert record["port"] == 43210
    assert record["boot_id"] == "boot-1"
    assert record["token"] == "test-token"


def test_write_runtime_rejects_missing_fields(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    state_dir = rendezvous.vault_state_dir(vault)

    with pytest.raises(ValueError, match="missing fields"):
        rendezvous.write_runtime(state_dir, {"port": 1})


def test_write_runtime_ignores_a_legacy_temp_file(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    state_dir = rendezvous.vault_state_dir(vault)
    legacy = rendezvous.runtime_path(state_dir).with_suffix(".json.tmp")
    legacy.write_text("old", encoding="utf-8")
    legacy.chmod(0o644)

    written = rendezvous.write_runtime(state_dir, _runtime_record(vault))

    assert legacy.read_text(encoding="utf-8") == "old"
    if os.name == "posix":
        assert stat.S_IMODE(written.stat().st_mode) == 0o600


@pytest.mark.skipif(
    os.name != "posix" or not hasattr(os, "O_NOFOLLOW"),
    reason="POSIX no-follow semantics unavailable",
)
def test_write_runtime_ignores_a_legacy_symlinked_temp_file(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    state_dir = rendezvous.vault_state_dir(vault)
    outside = tmp_path / "outside.json"
    outside.write_text("unchanged", encoding="utf-8")
    legacy = rendezvous.runtime_path(state_dir).with_suffix(".json.tmp")
    legacy.symlink_to(outside)

    written = rendezvous.write_runtime(state_dir, _runtime_record(vault))

    assert rendezvous.read_runtime(state_dir) is not None
    assert written.is_file()
    assert outside.read_text(encoding="utf-8") == "unchanged"


def test_write_runtime_retries_short_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    state_dir = rendezvous.vault_state_dir(vault)
    real_write = os.write
    calls = 0

    def short_write(fd: int, body: bytes | memoryview) -> int:
        nonlocal calls
        calls += 1
        return real_write(fd, body[:1])

    monkeypatch.setattr(rendezvous.os, "write", short_write)

    rendezvous.write_runtime(state_dir, _runtime_record(vault))

    assert calls > 1
    assert rendezvous.read_runtime(state_dir) is not None


def test_write_runtime_cleans_temp_after_write_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    state_dir = rendezvous.vault_state_dir(vault)

    def failed_write(_fd: int, _body: bytes | memoryview) -> int:
        raise OSError("disk full")

    monkeypatch.setattr(rendezvous.os, "write", failed_write)

    with pytest.raises(OSError, match="disk full"):
        rendezvous.write_runtime(state_dir, _runtime_record(vault))

    assert not list(state_dir.glob("*.tmp"))


def test_read_runtime_rejects_bad_payloads(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    state_dir = rendezvous.vault_state_dir(vault)

    assert rendezvous.read_runtime(state_dir) is None

    (state_dir / "runtime.json").write_text("not json", encoding="utf-8")
    assert rendezvous.read_runtime(state_dir) is None

    rendezvous.write_runtime(state_dir, _runtime_record(vault))
    tampered = json.loads((state_dir / "runtime.json").read_text(encoding="utf-8"))
    tampered["schema"] = "something-else"
    (state_dir / "runtime.json").write_text(json.dumps(tampered), encoding="utf-8")
    assert rendezvous.read_runtime(state_dir) is None

    rendezvous.write_runtime(state_dir, _runtime_record(vault))
    tampered = json.loads((state_dir / "runtime.json").read_text(encoding="utf-8"))
    del tampered["token"]
    (state_dir / "runtime.json").write_text(json.dumps(tampered), encoding="utf-8")
    assert rendezvous.read_runtime(state_dir) is None

    rendezvous.write_runtime(state_dir, _runtime_record(vault))
    tampered = json.loads((state_dir / "runtime.json").read_text(encoding="utf-8"))
    tampered["port"] = "not-a-port"
    (state_dir / "runtime.json").write_text(json.dumps(tampered), encoding="utf-8")
    assert rendezvous.read_runtime(state_dir) is None

    rendezvous.write_runtime(state_dir, _runtime_record(vault))
    tampered = json.loads((state_dir / "runtime.json").read_text(encoding="utf-8"))
    tampered["port"] = True
    (state_dir / "runtime.json").write_text(json.dumps(tampered), encoding="utf-8")
    assert rendezvous.read_runtime(state_dir) is None

    rendezvous.write_runtime(state_dir, _runtime_record(vault))
    tampered = json.loads((state_dir / "runtime.json").read_text(encoding="utf-8"))
    tampered["pid"] = True
    (state_dir / "runtime.json").write_text(json.dumps(tampered), encoding="utf-8")
    assert rendezvous.read_runtime(state_dir) is None


def test_clear_runtime_is_idempotent(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    state_dir = rendezvous.vault_state_dir(vault)

    rendezvous.clear_runtime(state_dir)
    rendezvous.write_runtime(state_dir, _runtime_record(vault))
    rendezvous.clear_runtime(state_dir)

    assert not (state_dir / "runtime.json").exists()


def test_pid_alive_detects_live_and_dead_processes() -> None:
    assert rendezvous.pid_alive(os.getpid()) is True
    finished = subprocess.Popen([sys.executable, "-c", "pass"])
    finished.wait(timeout=30)
    assert rendezvous.pid_alive(finished.pid) is False
    assert rendezvous.pid_alive(0) is False
    assert rendezvous.pid_alive(-1) is False


def test_pid_alive_uses_a_non_destructive_windows_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queried: list[int] = []

    def windows_query(pid: int) -> bool:
        queried.append(pid)
        return True

    def kill_must_not_run(_pid: int, _signal: int) -> None:
        pytest.fail("Windows liveness checks must not call os.kill")

    monkeypatch.setattr(rendezvous, "_is_windows", lambda: True)
    monkeypatch.setattr(rendezvous, "_windows_pid_alive", windows_query)
    monkeypatch.setattr(rendezvous.os, "kill", kill_must_not_run)

    assert rendezvous.pid_alive(12345) is True
    assert rendezvous.pid_alive(0) is False
    assert queried == [12345]


def test_windows_pid_alive_checks_the_process_exit_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeFunction:
        def __init__(self, callback):
            self.callback = callback
            self.argtypes = None
            self.restype = None

        def __call__(self, *args):
            return self.callback(*args)

    class Kernel32:
        def __init__(self) -> None:
            self.exit_code = 259
            self.handle = 123
            self.opened: list[tuple[int, bool, int]] = []
            self.closed: list[int] = []
            self.OpenProcess = FakeFunction(self.open_process)
            self.GetExitCodeProcess = FakeFunction(self.get_exit_code)
            self.CloseHandle = FakeFunction(self.close_handle)

        def open_process(self, access: int, inherit: bool, pid: int) -> int:
            self.opened.append((access, inherit, pid))
            return self.handle

        def get_exit_code(self, _handle: int, output: object) -> int:
            output._obj.value = self.exit_code  # type: ignore[attr-defined]
            return 1

        def close_handle(self, handle: int) -> int:
            self.closed.append(handle)
            return 1

    kernel32 = Kernel32()
    monkeypatch.setattr(
        rendezvous.ctypes, "WinDLL", lambda *_args, **_kwargs: kernel32, raising=False
    )

    assert rendezvous._windows_pid_alive(12345) is True
    kernel32.exit_code = 0
    assert rendezvous._windows_pid_alive(12345) is False
    kernel32.handle = 0
    monkeypatch.setattr(rendezvous.ctypes, "get_last_error", lambda: 5, raising=False)
    assert rendezvous._windows_pid_alive(12345) is True
    monkeypatch.setattr(rendezvous.ctypes, "get_last_error", lambda: 87, raising=False)
    assert rendezvous._windows_pid_alive(12345) is False
    assert kernel32.opened == [(0x1000, False, 12345)] * 4
    assert kernel32.closed == [123, 123]
