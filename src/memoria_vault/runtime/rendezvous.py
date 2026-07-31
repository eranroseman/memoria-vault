"""Per-vault server rendezvous state helpers."""

from __future__ import annotations

import ctypes
import hashlib
import json
import math
import os
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX fallback.
    fcntl = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - POSIX test environment.
    msvcrt = None

STATE_KEY_LENGTH = 16
MAX_LIFECYCLE_RESPONSE_BYTES = 64 * 1024
RUNTIME_SCHEMA = "memoria-runtime.v1"
RUNTIME_FIELDS = (
    "schema",
    "vault_path",
    "vault_id",
    "port",
    "pid",
    "boot_id",
    "token",
    "engine_version",
    "started_at",
)
_REDIRECT_ERROR = "rendezvous state path must not redirect through a symlink or junction"


def canonical_vault_path(vault_path: Path) -> str:
    """Resolve a vault path, case-folding it on case-insensitive filesystems."""
    resolved = Path(vault_path).expanduser().resolve()
    text = str(resolved)
    if _case_insensitive_filesystem(resolved):
        return text.casefold()
    return text


def vault_key(vault_path: Path) -> str:
    """Return the stable, truncated SHA-256 key for one vault path."""
    canonical = canonical_vault_path(vault_path)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:STATE_KEY_LENGTH]


def state_root() -> Path:
    """Return the platform-specific root for per-vault runtime state."""
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(local) / "Memoria" / "vaults"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Memoria" / "vaults"
    state_home = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(state_home) / "memoria" / "vaults"


def vault_state_dir(vault_path: Path) -> Path:
    """Create and return the private state directory for one vault."""
    directory = state_root() / vault_key(vault_path)
    directory.mkdir(parents=True, exist_ok=True)
    if os.name == "posix":
        os.chmod(directory, 0o700)
    return directory


def _case_insensitive_filesystem(path: Path) -> bool:
    """Return whether ``path`` lives on a filesystem that ignores case."""
    probe = path if path.exists() else path.parent
    swapped = Path(str(probe).swapcase())
    if str(swapped) == str(probe):
        return False
    try:
        return swapped.exists() and probe.exists() and os.path.samefile(probe, swapped)
    except OSError:
        return False


def runtime_path(state_dir: Path) -> Path:
    """Return the rendezvous entry path within one vault state directory."""
    return Path(state_dir) / "runtime.json"


def write_runtime(state_dir: Path, record: dict[str, Any]) -> Path:
    """Atomically publish an owner-only rendezvous entry."""
    entry = {**record, "schema": RUNTIME_SCHEMA}
    missing = [field for field in RUNTIME_FIELDS if field not in entry]
    if missing:
        raise ValueError(f"runtime record missing fields: {', '.join(missing)}")
    target = runtime_path(state_dir)
    body = json.dumps(entry, ensure_ascii=False, sort_keys=True).encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix="runtime.", suffix=".tmp", dir=state_dir)
    temp = Path(temporary)
    try:
        try:
            if os.name == "posix":
                os.fchmod(fd, 0o600)
            remaining = memoryview(body)
            while remaining:
                written = os.write(fd, remaining)
                if written <= 0:
                    raise OSError("failed to write runtime record")
                remaining = remaining[written:]
        finally:
            os.close(fd)
        os.replace(temp, target)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise
    return target


def read_runtime(state_dir: Path) -> dict[str, Any] | None:
    """Return a valid rendezvous entry, or None when it is absent or invalid."""
    try:
        data = json.loads(runtime_path(state_dir).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("schema") != RUNTIME_SCHEMA:
        return None
    if any(field not in data for field in RUNTIME_FIELDS):
        return None
    if type(data.get("port")) is not int or type(data.get("pid")) is not int:
        return None
    return data


def clear_runtime(state_dir: Path) -> None:
    """Remove a rendezvous entry when present."""
    runtime_path(state_dir).unlink(missing_ok=True)


def _is_windows() -> bool:
    return os.name == "nt"


def pid_alive(pid: int) -> bool:
    """Return whether the operating system reports a process as live."""
    if pid <= 0:
        return False
    if _is_windows():
        return _windows_pid_alive(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _windows_pid_alive(pid: int) -> bool:
    """Query Windows process state without sending it a signal."""
    from ctypes import wintypes

    process_query_limited_information = 0x1000
    error_access_denied = 5
    still_active = 259
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    open_process = kernel32.OpenProcess
    open_process.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    open_process.restype = wintypes.HANDLE
    get_exit_code = kernel32.GetExitCodeProcess
    get_exit_code.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    get_exit_code.restype = wintypes.BOOL
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [wintypes.HANDLE]
    close_handle.restype = wintypes.BOOL

    handle = open_process(process_query_limited_information, False, pid)
    if not handle:
        return ctypes.get_last_error() == error_access_denied
    try:
        exit_code = wintypes.DWORD()
        if not get_exit_code(handle, ctypes.byref(exit_code)):
            return True
        return exit_code.value == still_active
    finally:
        close_handle(handle)


def _path_redirects(path: Path) -> bool:
    return path.is_symlink() or path.is_junction()


def _open_serve_lock_file(state_dir: Path) -> int:
    """Open a regular serve lock without following direct reparse points."""
    state_dir = Path(state_dir)
    lock_path = state_dir / "serve.lock"
    if _path_redirects(state_dir) or _path_redirects(lock_path):
        raise ValueError(_REDIRECT_ERROR)

    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    if os.name == "posix" and hasattr(os, "O_NOFOLLOW"):
        directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        state_fd = os.open(state_dir, directory_flags)
        try:
            fd = os.open("serve.lock", flags, 0o600, dir_fd=state_fd)
        finally:
            os.close(state_fd)
    else:
        fd = os.open(lock_path, flags, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError("rendezvous serve lock must be a regular file")
    except BaseException:
        os.close(fd)
        raise
    return fd


@contextmanager
def serve_lock(state_dir: Path) -> Iterator[bool]:
    """Yield True when this holder owns the exclusive server-admission lock."""
    fd = _open_serve_lock_file(state_dir)
    try:
        if os.name == "posix":
            os.fchmod(fd, 0o600)
        if fcntl is None:
            if msvcrt is not None:
                os.lseek(fd, 0, os.SEEK_SET)
                try:
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                except OSError:
                    yield False
                    return
                try:
                    yield True
                finally:
                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                return
            yield False
            return
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            yield False
            return
        try:
            yield True
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def gc_stale_entries(root: Path | None = None) -> list[str]:
    """Delete rendezvous entries whose recorded pid is dead; return removed keys."""
    base = Path(root) if root is not None else state_root()
    removed: list[str] = []
    if _path_redirects(base) or not base.is_dir():
        return removed
    for entry_dir in sorted(
        path for path in base.iterdir() if not _path_redirects(path) and path.is_dir()
    ):
        record = read_runtime(entry_dir)
        if record is None:
            continue
        if not pid_alive(int(record["pid"])):
            clear_runtime(entry_dir)
            removed.append(entry_dir.name)
    return removed


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Fail lifecycle requests rather than following a redirected endpoint."""

    def http_error_302(
        self,
        request: urllib.request.Request,
        response: Any,
        status: int,
        message: str,
        headers: Any,
    ) -> None:
        response.close()
        raise urllib.error.HTTPError(request.full_url, status, message, headers, response)

    http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302


def _open_lifecycle_request(request: urllib.request.Request, *, timeout: float) -> Any:
    """Open a loopback lifecycle request without ambient proxy or redirect policy."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    return opener.open(request, timeout=timeout)


def _read_lifecycle_json(response: Any) -> dict[str, Any] | None:
    """Read one bounded JSON response from a lifecycle endpoint."""
    body = response.read(MAX_LIFECYCLE_RESPONSE_BYTES + 1)
    if len(body) > MAX_LIFECYCLE_RESPONSE_BYTES:
        return None
    data = json.loads(body.decode("utf-8"))
    return data if isinstance(data, dict) else None


def post_shutdown(
    port: int, token: str, boot_id: str, timeout: float = 2.0
) -> dict[str, Any] | None:
    """POST the authenticated shutdown request, returning None when unreachable."""
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/shutdown",
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Memoria-Boot-Id": boot_id,
        },
        data=b"",
    )
    try:
        with _open_lifecycle_request(request, timeout=timeout) as response:
            return _read_lifecycle_json(response)
    except (OSError, ValueError, urllib.error.HTTPError):
        return None


def probe_boot_id(port: int, timeout: float = 1.0) -> str | None:
    """Return the unauthenticated status endpoint's non-empty boot ID."""
    request = urllib.request.Request(f"http://127.0.0.1:{port}/v1/status", method="GET")
    try:
        with _open_lifecycle_request(request, timeout=timeout) as response:
            data = _read_lifecycle_json(response)
    except (OSError, ValueError, urllib.error.HTTPError):
        return None
    boot_id = data.get("boot_id") if isinstance(data, dict) else None
    return boot_id if isinstance(boot_id, str) and boot_id else None


def live_coordinates(state_dir: Path, *, probe_timeout: float = 1.0) -> dict[str, Any] | None:
    """Return a matching live entry, removing only records with dead PIDs."""
    record = read_runtime(state_dir)
    if record is None:
        return None
    if not pid_alive(int(record["pid"])):
        clear_runtime(state_dir)
        return None
    if probe_boot_id(int(record["port"]), timeout=probe_timeout) != record["boot_id"]:
        return None
    return record


class HandshakeError(RuntimeError):
    """Raised when no live server can be reached or spawned."""


def handshake(
    vault_path: Path,
    *,
    spawn: bool = False,
    timeout: float = 5.0,
    spawn_command: list[str] | None = None,
) -> dict[str, Any]:
    """Connect to a live server, or spawn and wait for one when requested."""
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or not math.isfinite(timeout)
        or timeout <= 0
    ):
        raise HandshakeError("handshake timeout must be finite positive seconds")
    vault = Path(vault_path).expanduser().resolve()
    state_dir = vault_state_dir(vault)
    gc_stale_entries()
    record = live_coordinates(state_dir)
    if record is None and not spawn:
        raise HandshakeError("no memoria server is running for this vault (rerun with --spawn)")
    if record is None:
        record = _spawn_and_wait(vault, state_dir, timeout=timeout, spawn_command=spawn_command)
    return {
        "port": int(record["port"]),
        "token": str(record["token"]),
        "engine_version": str(record["engine_version"]),
        "boot_id": str(record["boot_id"]),
        "pid": int(record["pid"]),
    }


def _spawn_and_wait(
    vault: Path,
    state_dir: Path,
    *,
    timeout: float,
    spawn_command: list[str] | None,
) -> dict[str, Any]:
    _spawn_server(vault, state_dir, spawn_command)
    record = _wait_for_live(state_dir, timeout=timeout)
    if record is None:
        raise HandshakeError(
            f"server did not publish rendezvous within {timeout:.0f}s; see {state_dir / 'serve.log'}"
        )
    return record


def _spawn_server(vault: Path, state_dir: Path, spawn_command: list[str] | None) -> None:
    """Start a detached on-demand server and direct output to its private log."""
    command = spawn_command or [
        sys.executable,
        "-m",
        "memoria_vault.cli",
        "serve",
        "--workspace",
        str(vault),
        "--http",
        "--on-demand",
        "--ephemeral",
        "--quiet",
    ]
    log_path = Path(state_dir) / "serve.log"
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    popen_kwargs: dict[str, Any] = {
        "stdin": subprocess.DEVNULL,
        "stderr": subprocess.STDOUT,
        "close_fds": True,
        "cwd": str(Path(__file__).resolve().parents[2]),
        "env": environment,
    }
    if os.name == "posix":
        popen_kwargs["start_new_session"] = True
    elif os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    try:
        if _path_redirects(state_dir) or _path_redirects(log_path):
            raise ValueError(_REDIRECT_ERROR)
        with log_path.open("ab") as log_file:
            subprocess.Popen(command, stdout=log_file, **popen_kwargs)
    except (OSError, ValueError) as exc:
        raise HandshakeError(f"could not spawn memoria server; see {log_path}: {exc}") from exc


def _wait_for_live(state_dir: Path, *, timeout: float) -> dict[str, Any] | None:
    """Return a PID-live published record before the finite wait expires."""
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or not math.isfinite(timeout)
        or timeout <= 0
    ):
        return None
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        record = live_coordinates(state_dir, probe_timeout=min(0.5, remaining))
        if record is not None:
            pid = record.get("pid")
            if type(pid) is int and pid > 0 and pid_alive(pid):
                return record
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        time.sleep(min(0.1, remaining))
