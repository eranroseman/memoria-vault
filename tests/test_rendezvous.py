"""Server rendezvous state tests."""

from __future__ import annotations

import contextlib
import hashlib
import http.client
import json
import math
import os
import socket
import stat
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from http import HTTPStatus
from pathlib import Path

import pytest

from memoria_vault import __version__
from memoria_vault.runtime import http_transport, rendezvous
from memoria_vault.runtime.http_transport import (
    bind_http_server,
    host_allowed,
    make_http_server,
    origin_allowed,
    start_idle_monitor,
)
from tests.helpers import init_cli_workspace


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


def test_serve_lock_is_exclusive_and_released(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    state_dir = rendezvous.vault_state_dir(vault)

    with rendezvous.serve_lock(state_dir) as first:
        assert first is True
        with rendezvous.serve_lock(state_dir) as second:
            assert second is False
    with rendezvous.serve_lock(state_dir) as again:
        assert again is True


def test_serve_lock_falls_back_without_fcntl(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    state_dir = rendezvous.vault_state_dir(vault)
    monkeypatch.setattr(rendezvous, "fcntl", None)

    with rendezvous.serve_lock(state_dir) as locked:
        assert locked is True


def test_serve_lock_uses_msvcrt_when_fcntl_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeMsvcrt:
        LK_NBLCK = 1
        LK_UNLCK = 2

        def __init__(self) -> None:
            self.calls: list[tuple[int, int]] = []

        def locking(self, _fd: int, mode: int, count: int) -> None:
            self.calls.append((mode, count))

    vault = tmp_path / "vault"
    vault.mkdir()
    state_dir = rendezvous.vault_state_dir(vault)
    fake_msvcrt = FakeMsvcrt()
    monkeypatch.setattr(rendezvous, "fcntl", None)
    monkeypatch.setattr(rendezvous, "msvcrt", fake_msvcrt, raising=False)

    with rendezvous.serve_lock(state_dir) as locked:
        assert locked is True

    assert fake_msvcrt.calls == [(fake_msvcrt.LK_NBLCK, 1), (fake_msvcrt.LK_UNLCK, 1)]


def test_serve_lock_msvcrt_locks_beyond_eof_without_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeMsvcrt:
        LK_NBLCK = 1
        LK_UNLCK = 2

        def locking(self, _fd: int, _mode: int, _count: int) -> None:
            pass

    vault = tmp_path / "vault"
    vault.mkdir()
    state_dir = rendezvous.vault_state_dir(vault)
    monkeypatch.setattr(rendezvous, "fcntl", None)
    monkeypatch.setattr(rendezvous, "msvcrt", FakeMsvcrt(), raising=False)

    def unexpected_write(*_args: object) -> int:
        raise AssertionError("msvcrt locking must not write the locked byte first")

    monkeypatch.setattr(rendezvous.os, "write", unexpected_write)

    with rendezvous.serve_lock(state_dir) as locked:
        assert locked is True


def test_serve_lock_reports_a_busy_msvcrt_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeMsvcrt:
        LK_NBLCK = 1
        LK_UNLCK = 2

        def locking(self, _fd: int, mode: int, _count: int) -> None:
            if mode == self.LK_NBLCK:
                raise OSError("busy")

    vault = tmp_path / "vault"
    vault.mkdir()
    state_dir = rendezvous.vault_state_dir(vault)
    monkeypatch.setattr(rendezvous, "fcntl", None)
    monkeypatch.setattr(rendezvous, "msvcrt", FakeMsvcrt(), raising=False)

    with rendezvous.serve_lock(state_dir) as locked:
        assert locked is False


@pytest.mark.skipif(
    os.name != "posix" or not hasattr(os, "O_NOFOLLOW"),
    reason="POSIX no-follow semantics unavailable",
)
def test_serve_lock_refuses_a_symlinked_lock_file(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    state_dir = rendezvous.vault_state_dir(vault)
    outside = tmp_path / "outside.lock"
    outside.write_text("unchanged", encoding="utf-8")
    (state_dir / "serve.lock").symlink_to(outside)

    with pytest.raises(ValueError, match="must not redirect"):
        with rendezvous.serve_lock(state_dir):
            pass

    assert outside.read_text(encoding="utf-8") == "unchanged"


@pytest.mark.skipif(
    os.name != "posix" or not hasattr(os, "O_NOFOLLOW"),
    reason="POSIX no-follow semantics unavailable",
)
def test_serve_lock_refuses_a_symlinked_state_dir(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    redirected_state_dir = tmp_path / "redirected-state"
    redirected_state_dir.symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="must not redirect"):
        with rendezvous.serve_lock(redirected_state_dir):
            pass

    assert not (outside / "serve.lock").exists()


def test_serve_lock_refuses_a_junctioned_state_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    original_is_junction = Path.is_junction
    monkeypatch.setattr(
        Path,
        "is_junction",
        lambda path: path == state_dir or original_is_junction(path),
    )

    with pytest.raises(ValueError, match="must not redirect"):
        with rendezvous.serve_lock(state_dir):
            pass

    assert not (state_dir / "serve.lock").exists()


def test_gc_stale_entries_removes_dead_pid_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    alive_vault = tmp_path / "alive"
    dead_vault = tmp_path / "dead"
    alive_vault.mkdir()
    dead_vault.mkdir()
    alive_dir = rendezvous.vault_state_dir(alive_vault)
    dead_dir = rendezvous.vault_state_dir(dead_vault)
    rendezvous.write_runtime(alive_dir, _runtime_record(alive_vault, pid=111))
    rendezvous.write_runtime(dead_dir, _runtime_record(dead_vault, pid=222))
    monkeypatch.setattr(rendezvous, "pid_alive", lambda pid: pid == 111)

    removed = rendezvous.gc_stale_entries()

    assert removed == [dead_dir.name]
    assert rendezvous.read_runtime(alive_dir) is not None
    assert rendezvous.read_runtime(dead_dir) is None


def test_gc_stale_entries_tolerates_missing_root(tmp_path: Path) -> None:
    assert rendezvous.gc_stale_entries(tmp_path / "nowhere") == []


@pytest.mark.skipif(os.name != "posix", reason="POSIX symlink semantics")
def test_gc_stale_entries_ignores_symlinked_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "state"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    rendezvous.write_runtime(outside, _runtime_record(tmp_path, pid=222))
    (root / "not-a-key").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(rendezvous, "pid_alive", lambda _pid: False)

    assert rendezvous.gc_stale_entries(root) == []
    assert rendezvous.read_runtime(outside) is not None


@pytest.mark.skipif(os.name != "posix", reason="POSIX symlink semantics")
def test_gc_stale_entries_ignores_a_symlinked_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    entry_dir = outside / "dead-entry"
    entry_dir.mkdir()
    rendezvous.write_runtime(entry_dir, _runtime_record(tmp_path, pid=222))
    redirected_root = tmp_path / "redirected-root"
    redirected_root.symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(rendezvous, "pid_alive", lambda _pid: False)

    assert rendezvous.gc_stale_entries(redirected_root) == []
    assert rendezvous.read_runtime(entry_dir) is not None


def test_gc_stale_entries_ignores_a_junctioned_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "state"
    root.mkdir()
    entry_dir = root / "dead-entry"
    entry_dir.mkdir()
    rendezvous.write_runtime(entry_dir, _runtime_record(tmp_path, pid=222))
    original_is_junction = Path.is_junction
    monkeypatch.setattr(
        Path,
        "is_junction",
        lambda path: path == entry_dir or original_is_junction(path),
    )
    monkeypatch.setattr(rendezvous, "pid_alive", lambda _pid: False)

    assert rendezvous.gc_stale_entries(root) == []
    assert rendezvous.read_runtime(entry_dir) is not None


@pytest.fixture
def workspace(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> Path:
    return init_cli_workspace(tmp_path, capsys)


def _make_server(workspace: Path, **kwargs: object):
    try:
        return make_http_server(workspace, host="127.0.0.1", port=0, **kwargs)
    except PermissionError as exc:  # pragma: no cover - sandbox guard
        pytest.skip(f"loopback socket unavailable in this sandbox: {exc}")


@contextlib.contextmanager
def _running_server(
    workspace: Path, *, token: str = "test-token", boot_id: str = "boot-1"
) -> Iterator[tuple[object, int, threading.Thread]]:
    server = _make_server(workspace, token=token, boot_id=boot_id)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server, int(server.server_address[1]), thread
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def _request(
    port: int,
    method: str,
    path: str,
    *,
    token: str | None = None,
    host: str | None = None,
    origin: str | None = None,
) -> tuple[int, dict[str, object]]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    headers = {"Host": host or f"127.0.0.1:{port}"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    if origin is not None:
        headers["Origin"] = origin
    try:
        connection.request(method, path, headers=headers)
        response = connection.getresponse()
        return response.status, json.loads(response.read().decode("utf-8"))
    finally:
        connection.close()


def _raw_request(port: int, request: str) -> tuple[int, dict[str, object]]:
    with socket.create_connection(("127.0.0.1", port), timeout=5) as connection:
        connection.sendall(request.encode("ascii"))
        response = http.client.HTTPResponse(connection)
        response.begin()
        return response.status, json.loads(response.read().decode("utf-8"))


def test_v1_status_is_unauthenticated_and_never_resets_idle_timer(workspace: Path) -> None:
    with _running_server(workspace, boot_id="boot-status") as (server, port, _thread):
        server.last_authenticated = 41.0
        status, payload = _request(port, "GET", "/v1/status")

        assert status == 200
        assert payload == {
            "boot_id": "boot-status",
            "engine_version": __version__,
            "ok": True,
        }
        assert server.last_authenticated == 41.0


def test_v1_status_with_valid_token_never_resets_idle_timer(workspace: Path) -> None:
    with _running_server(workspace) as (server, port, _thread):
        server.last_authenticated = 42.0

        status, payload = _request(port, "GET", "/v1/status", token="test-token")

        assert status == 200
        assert payload["ok"] is True
        assert server.last_authenticated == 42.0


def test_authenticated_request_resets_idle_timer_and_unauthorized_does_not(
    workspace: Path,
) -> None:
    with _running_server(workspace) as (server, port, _thread):
        server.last_authenticated = 0.0
        status, payload = _request(port, "GET", "/status", token="test-token")
        assert status == 200
        assert payload["ok"] is True
        assert server.last_authenticated > 0.0

        marked = server.last_authenticated
        status, payload = _request(port, "GET", "/status")
        assert status == 401
        assert payload == {"ok": False, "error": "unauthorized"}
        assert server.last_authenticated == marked


def test_host_header_validation_rejects_dns_rebinding(workspace: Path) -> None:
    with _running_server(workspace) as (_server, port, _thread):
        forged, payload = _request(port, "GET", "/v1/status", host=f"evil.example:{port}")
        assert forged == 403
        assert payload == {"ok": False, "error": "forbidden host"}
        localhost_ok, _payload = _request(port, "GET", "/v1/status", host=f"localhost:{port}")
        assert localhost_ok == 200

    assert host_allowed("127.0.0.1:1234", 1234) is True
    assert host_allowed("localhost:1234", 1234) is True
    assert host_allowed("127.0.0.1:9999", 1234) is False
    assert host_allowed(None, 1234) is False


def test_host_header_validation_rejects_empty_and_missing_host(workspace: Path) -> None:
    with _running_server(workspace) as (_server, port, _thread):
        empty, empty_payload = _raw_request(
            port,
            "GET /v1/status HTTP/1.1\r\nHost: \r\nConnection: close\r\n\r\n",
        )
        missing, missing_payload = _raw_request(
            port,
            "GET /v1/status HTTP/1.1\r\nConnection: close\r\n\r\n",
        )

    assert empty == 403
    assert empty_payload == {"ok": False, "error": "forbidden host"}
    assert missing == 403
    assert missing_payload == {"ok": False, "error": "forbidden host"}


def test_duplicate_host_is_rejected_before_auth_and_never_touches_idle_timer(
    workspace: Path,
) -> None:
    with _running_server(workspace) as (server, port, _thread):
        server.last_authenticated = 43.0
        status, payload = _raw_request(
            port,
            "GET /status HTTP/1.1\r\n"
            f"Host: 127.0.0.1:{port}\r\n"
            f"Host: 127.0.0.1:{port}\r\n"
            "Authorization: Bearer test-token\r\n"
            "Connection: close\r\n"
            "\r\n",
        )

        assert status == 403
        assert payload == {"ok": False, "error": "forbidden host"}
        assert server.last_authenticated == 43.0


def test_origin_rejected_unless_obsidian_app(workspace: Path) -> None:
    with _running_server(workspace) as (_server, port, _thread):
        rejected, payload = _request(
            port, "GET", "/status", token="test-token", origin="https://evil.example"
        )
        assert rejected == 403
        assert payload == {"ok": False, "error": "forbidden origin"}
        allowed, _payload = _request(
            port, "GET", "/status", token="test-token", origin="app://obsidian.md"
        )
        assert allowed == 200

    assert origin_allowed(None) is True
    assert origin_allowed("app://obsidian.md") is True
    assert origin_allowed("https://evil.example") is False


def test_duplicate_origin_is_rejected_before_auth_and_never_touches_idle_timer(
    workspace: Path,
) -> None:
    with _running_server(workspace) as (server, port, _thread):
        server.last_authenticated = 44.0
        status, payload = _raw_request(
            port,
            "GET /status HTTP/1.1\r\n"
            f"Host: 127.0.0.1:{port}\r\n"
            "Origin: app://obsidian.md\r\n"
            "Origin: app://obsidian.md\r\n"
            "Authorization: Bearer test-token\r\n"
            "Connection: close\r\n"
            "\r\n",
        )

        assert status == 403
        assert payload == {"ok": False, "error": "forbidden origin"}
        assert server.last_authenticated == 44.0


def test_rejected_host_or_origin_with_valid_token_never_touches_idle_timer(
    workspace: Path,
) -> None:
    with _running_server(workspace) as (server, port, _thread):
        server.last_authenticated = 45.0
        host_status, host_payload = _request(
            port, "GET", "/status", token="test-token", host=f"evil.example:{port}"
        )
        assert host_status == 403
        assert host_payload == {"ok": False, "error": "forbidden host"}
        assert server.last_authenticated == 45.0

        server.last_authenticated = 46.0
        origin_status, origin_payload = _request(
            port, "GET", "/status", token="test-token", origin="https://evil.example"
        )
        assert origin_status == 403
        assert origin_payload == {"ok": False, "error": "forbidden origin"}
        assert server.last_authenticated == 46.0


def test_host_validation_precedes_origin_validation(workspace: Path) -> None:
    with _running_server(workspace) as (server, port, _thread):
        server.last_authenticated = 47.0
        status, payload = _request(
            port,
            "GET",
            "/status",
            token="test-token",
            host=f"evil.example:{port}",
            origin="https://evil.example",
        )

        assert status == 403
        assert payload == {"ok": False, "error": "forbidden host"}
        assert server.last_authenticated == 47.0


def test_shutdown_requires_auth_and_stops_server(workspace: Path) -> None:
    server = _make_server(workspace, token="test-token", boot_id="boot-1")
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        denied, payload = _request(port, "POST", "/v1/shutdown")
        assert denied == 401
        assert payload == {"ok": False, "error": "unauthorized"}
        wrong_method, _payload = _request(port, "GET", "/v1/shutdown", token="test-token")
        assert wrong_method == 405
        status, payload = _request(port, "POST", "/v1/shutdown", token="test-token")
        assert status == 200
        assert payload == {"ok": True, "stopping": True}
        thread.join(timeout=5)
        assert not thread.is_alive()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_idle_monitor_exits_despite_unauthenticated_probes(workspace: Path) -> None:
    server = _make_server(workspace, token="test-token", boot_id="boot-idle")
    port = int(server.server_address[1])
    serve_thread = threading.Thread(
        target=lambda: server.serve_forever(poll_interval=0.01), daemon=True
    )
    serve_thread.start()
    assert server.serve_forever_started.wait(timeout=5)
    monitor = start_idle_monitor(server, idle_exit_seconds=0.2, poll_interval=0.01)
    try:
        deadline = time.monotonic() + 0.1
        while time.monotonic() < deadline:
            status, _payload = _request(port, "GET", "/v1/status")
            assert status == 200
            time.sleep(0.01)

        serve_thread.join(timeout=5)
        assert not serve_thread.is_alive()
        monitor.join(timeout=5)
        assert not monitor.is_alive()
    finally:
        server.shutdown()
        serve_thread.join(timeout=5)
        monitor.join(timeout=5)
        server.server_close()


def test_idle_monitor_extends_on_authenticated_requests(workspace: Path) -> None:
    server = _make_server(workspace, token="test-token", boot_id="boot-live")
    port = int(server.server_address[1])
    serve_thread = threading.Thread(
        target=lambda: server.serve_forever(poll_interval=0.01), daemon=True
    )
    serve_thread.start()
    assert server.serve_forever_started.wait(timeout=5)
    monitor = start_idle_monitor(server, idle_exit_seconds=0.15, poll_interval=0.01)
    try:
        for _ in range(3):
            time.sleep(0.06)
            status, _payload = _request(port, "GET", "/status", token="test-token")
            assert status == 200

        assert serve_thread.is_alive()
        serve_thread.join(timeout=5)
        assert not serve_thread.is_alive()
        monitor.join(timeout=5)
        assert not monitor.is_alive()
    finally:
        server.shutdown()
        serve_thread.join(timeout=5)
        monitor.join(timeout=5)
        server.server_close()


@pytest.mark.parametrize(
    ("idle_exit_seconds", "poll_interval"),
    [
        (0.0, 0.01),
        (-1.0, 0.01),
        (math.inf, 0.01),
        (math.nan, 0.01),
        (0.01, 0.0),
        (0.01, -1.0),
        (0.01, math.inf),
        (0.01, math.nan),
        (True, 0.01),
        (0.01, True),
        ("0.01", 0.01),
        (0.01, "0.01"),
    ],
)
def test_idle_monitor_requires_finite_positive_durations(
    idle_exit_seconds: object, poll_interval: object
) -> None:
    with pytest.raises(ValueError, match="finite positive"):
        start_idle_monitor(
            object(),
            idle_exit_seconds=idle_exit_seconds,
            poll_interval=poll_interval,
        )


def test_idle_monitor_waits_for_serve_forever_before_shutdown(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    server = _make_server(workspace, token="test-token")
    server.last_authenticated = 0.0
    original_shutdown = server.shutdown
    shutdown_called = threading.Event()

    def shutdown() -> None:
        shutdown_called.set()
        original_shutdown()

    monkeypatch.setattr(server, "shutdown", shutdown)
    monitor = start_idle_monitor(server, idle_exit_seconds=0.01, poll_interval=0.01)
    serve_thread: threading.Thread | None = None
    try:
        assert not shutdown_called.wait(timeout=0.1)

        serve_thread = threading.Thread(
            target=lambda: server.serve_forever(poll_interval=0.01), daemon=True
        )
        serve_thread.start()
        assert shutdown_called.wait(timeout=5)
        serve_thread.join(timeout=5)
        assert not serve_thread.is_alive()
        monitor.join(timeout=5)
        assert not monitor.is_alive()
    finally:
        if serve_thread is None:
            serve_thread = threading.Thread(target=server.serve_forever, daemon=True)
            serve_thread.start()
        server.shutdown()
        serve_thread.join(timeout=5)
        monitor.join(timeout=5)
        server.server_close()


def test_idle_monitor_waits_for_an_authenticated_dispatch_to_finish(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    entered_dispatch = threading.Event()
    release_dispatch = threading.Event()

    def blocked_dispatch(*_args: object, **_kwargs: object) -> tuple[dict[str, object], HTTPStatus]:
        entered_dispatch.set()
        assert release_dispatch.wait(timeout=5)
        return {"ok": True}, HTTPStatus.OK

    monkeypatch.setattr(http_transport, "_dispatch", blocked_dispatch)
    server = _make_server(workspace, token="test-token")
    port = int(server.server_address[1])
    serve_thread = threading.Thread(
        target=lambda: server.serve_forever(poll_interval=0.01), daemon=True
    )
    serve_thread.start()
    assert server.serve_forever_started.wait(timeout=5)
    monitor = start_idle_monitor(server, idle_exit_seconds=0.03, poll_interval=0.01)
    response: dict[str, object] = {}

    def request() -> None:
        status, payload = _request(port, "GET", "/status", token="test-token")
        response.update(status=status, payload=payload)

    request_thread = threading.Thread(target=request, daemon=True)
    request_thread.start()
    try:
        assert entered_dispatch.wait(timeout=5)
        time.sleep(0.1)
        assert serve_thread.is_alive()
        assert monitor.is_alive()

        release_dispatch.set()
        request_thread.join(timeout=5)
        assert not request_thread.is_alive()
        assert response == {"status": 200, "payload": {"ok": True}}

        serve_thread.join(timeout=5)
        assert not serve_thread.is_alive()
        monitor.join(timeout=5)
        assert not monitor.is_alive()
    finally:
        release_dispatch.set()
        server.shutdown()
        request_thread.join(timeout=5)
        serve_thread.join(timeout=5)
        monitor.join(timeout=5)
        server.server_close()


def _free_loopback_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def test_bind_http_server_walks_past_occupied_port_to_next_candidate(workspace: Path) -> None:
    blocker = _make_server(workspace, token="blocker", boot_id="boot-a")
    occupied = int(blocker.server_address[1])
    available = _free_loopback_port()
    server = None
    try:
        server = bind_http_server(
            workspace,
            host="127.0.0.1",
            candidate_ports=[occupied, available],
            token="test-token",
            boot_id="boot-b",
        )

        assert int(server.server_address[1]) == available
        with pytest.raises(OSError):
            bind_http_server(
                workspace,
                host="127.0.0.1",
                candidate_ports=[occupied],
                token="test-token",
                boot_id="boot-c",
            )
    finally:
        if server is not None:
            server.server_close()
        blocker.server_close()


def test_bind_http_server_attempts_candidates_in_order_and_raises_last_error(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first_error = OSError("first candidate unavailable")
    last_error = OSError("last candidate unavailable")
    attempted: list[int] = []

    def fail_to_bind(
        _workspace: Path,
        *,
        host: str,
        port: int,
        token: str,
        read_scope: list[str] | None = None,
        boot_id: str = "",
    ) -> object:
        del host, token, read_scope, boot_id
        attempted.append(port)
        if port == 8765:
            raise first_error
        raise last_error

    monkeypatch.setattr(http_transport, "make_http_server", fail_to_bind)

    with pytest.raises(OSError) as exc_info:
        bind_http_server(
            workspace,
            host="127.0.0.1",
            candidate_ports=[8765, 8766],
            token="test-token",
            boot_id="boot-b",
        )

    assert attempted == [8765, 8766]
    assert exc_info.value is last_error
