"""Cross-process workspace lock (one writer per vault)."""

from __future__ import annotations

import contextlib
import ctypes
import errno
import os
import stat
import threading
import time
from pathlib import Path
from types import ModuleType
from typing import Any, Literal

fcntl: ModuleType | None
try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback is exercised only on Windows.
    fcntl = None

msvcrt: ModuleType | None
try:
    import msvcrt
except ImportError:  # pragma: no cover - POSIX path is exercised in CI.
    msvcrt = None

_WORKSPACE_LOCKS_GUARD = threading.Lock()
_WORKSPACE_LOCKS: dict[str, threading.RLock] = {}
_WORKSPACE_LOCK_DEPTH = threading.local()
_WORKSPACE_LOCK_PID = os.getpid()


def _workspace_lock_key(vault: Path) -> str:
    return str(Path(vault).resolve() / ".memoria/locks/worker.lock")


class _WindowsLockFile:
    """Keep no-delete directory handles alive with the Windows lock file."""

    def __init__(self, lock_file: Any, directory_handles: list[int], close_handle: Any) -> None:
        self._lock_file = lock_file
        self._directory_handles = directory_handles
        self._close_handle = close_handle
        self._closed = False

    def __enter__(self) -> _WindowsLockFile:
        return self

    def __exit__(self, *_exc_info: object) -> Literal[False]:
        self.close()
        return False

    def __getattr__(self, name: str) -> Any:
        return getattr(self._lock_file, name)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._lock_file.close()
        finally:
            for handle in reversed(self._directory_handles):
                self._close_handle(handle)
            self._directory_handles.clear()


def _open_workspace_lock_file_windows(
    _vault: Path, lock_path: Path
):  # pragma: no cover - runs only on Windows.
    """Open a lock without resolving Windows symlinks or junctions.

    The vault root is opened with ``FILE_FLAG_OPEN_REPARSE_POINT``. Every later
    component is opened relative to its parent handle with ``NtCreateFile`` and
    ``FILE_OPEN_REPARSE_POINT``. Parent handles therefore anchor traversal even
    if another process changes a directory's reparse attributes after it is
    checked. The lock file retries a competing worker after the owner closes it.
    """
    if msvcrt is None:  # pragma: no cover - Windows always provides msvcrt.
        raise RuntimeError("Windows workspace locking is unavailable")

    from ctypes import wintypes

    win_dll = ctypes.WinDLL  # type: ignore[attr-defined]  # Windows-only ctypes API.
    get_last_error = ctypes.get_last_error  # type: ignore[attr-defined]  # Windows-only ctypes API.
    kernel32 = win_dll("kernel32", use_last_error=True)
    ntdll = win_dll("ntdll")
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [wintypes.HANDLE]
    close_handle.restype = wintypes.BOOL
    get_info = kernel32.GetFileInformationByHandleEx
    get_info.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    get_info.restype = wintypes.BOOL
    nt_create_file = ntdll.NtCreateFile
    rtl_nt_status_to_dos_error = ntdll.RtlNtStatusToDosError

    class FileAttributeTagInfo(ctypes.Structure):
        _fields_ = [("attributes", wintypes.DWORD), ("reparse_tag", wintypes.DWORD)]

    class UnicodeString(ctypes.Structure):
        _fields_ = [
            ("length", wintypes.USHORT),
            ("maximum_length", wintypes.USHORT),
            ("buffer", wintypes.LPWSTR),
        ]

    class ObjectAttributes(ctypes.Structure):
        _fields_ = [
            ("length", wintypes.ULONG),
            ("root_directory", wintypes.HANDLE),
            ("object_name", ctypes.POINTER(UnicodeString)),
            ("attributes", wintypes.ULONG),
            ("security_descriptor", ctypes.c_void_p),
            ("security_quality_of_service", ctypes.c_void_p),
        ]

    class IoStatusValue(ctypes.Union):
        _fields_ = [  # noqa: RUF012 - ctypes declares layouts with mutable lists.
            ("status", wintypes.LONG),
            ("pointer", ctypes.c_void_p),
        ]

    class IoStatusBlock(ctypes.Structure):
        _anonymous_ = ("value",)
        _fields_ = [("value", IoStatusValue), ("information", ctypes.c_size_t)]

    nt_create_file.argtypes = [
        ctypes.POINTER(wintypes.HANDLE),
        wintypes.DWORD,
        ctypes.POINTER(ObjectAttributes),
        ctypes.POINTER(IoStatusBlock),
        ctypes.c_void_p,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.ULONG,
        ctypes.c_void_p,
        wintypes.ULONG,
    ]
    nt_create_file.restype = wintypes.LONG
    rtl_nt_status_to_dos_error.argtypes = [wintypes.LONG]
    rtl_nt_status_to_dos_error.restype = wintypes.ULONG

    generic_read = 0x80000000
    generic_write = 0x40000000
    synchronize = 0x00100000
    file_read_attributes = 0x00000080
    file_traverse = 0x00000020
    directory_access = file_read_attributes | file_traverse | synchronize
    file_share_read = 0x00000001
    open_existing = 3
    file_open_if = 3
    file_attribute_normal = 0x00000080
    file_attribute_directory = 0x00000010
    file_attribute_reparse_point = 0x00000400
    file_flag_backup_semantics = 0x02000000
    file_flag_open_reparse_point = 0x00200000
    file_directory_file = 0x00000001
    file_synchronous_io_nonalert = 0x00000020
    file_non_directory_file = 0x00000040
    file_open_reparse_point = 0x00200000
    obj_case_insensitive = 0x00000040
    error_sharing_violation = 32
    file_attribute_tag_info = 9
    invalid_handle = ctypes.c_void_p(-1).value
    redirect_error = "workspace lock path must not redirect through a symlink or junction"

    def close(handle: int) -> None:
        close_handle(handle)

    def failed(path: Path, error: int) -> OSError:
        return OSError(error, "unable to open workspace lock path", str(path))

    def attributes(handle: int, path: Path) -> int:
        info = FileAttributeTagInfo()
        if not get_info(handle, file_attribute_tag_info, ctypes.byref(info), ctypes.sizeof(info)):
            raise failed(path, get_last_error())
        return int(info.attributes)

    def open_root_directory(path: Path) -> int:
        flags = file_flag_backup_semantics | file_flag_open_reparse_point
        handle = create_file(
            str(path),
            directory_access,
            file_share_read,
            None,
            open_existing,
            flags,
            None,
        )
        if handle == invalid_handle:
            raise failed(path, get_last_error())
        try:
            value = attributes(handle, path)
            if value & file_attribute_reparse_point:
                raise ValueError(redirect_error)
            if not value & file_attribute_directory:
                raise ValueError("workspace lock path must be a directory")
            return int(handle)
        except BaseException:
            close(handle)
            raise

    def open_relative(parent: int, name: str, path: Path, *, directory: bool) -> int:
        name_buffer = ctypes.create_unicode_buffer(name)
        name_length = len(name.encode("utf-16-le"))
        object_name = UnicodeString(
            name_length,
            name_length + ctypes.sizeof(wintypes.WCHAR),
            ctypes.cast(name_buffer, wintypes.LPWSTR),
        )
        object_attributes = ObjectAttributes(
            ctypes.sizeof(ObjectAttributes),
            wintypes.HANDLE(parent),
            ctypes.pointer(object_name),
            obj_case_insensitive,
            None,
            None,
        )
        io_status = IoStatusBlock()
        handle = wintypes.HANDLE()
        options = file_open_reparse_point | file_synchronous_io_nonalert
        options |= file_directory_file if directory else file_non_directory_file
        desired_access = directory_access
        if not directory:
            desired_access = generic_read | generic_write | synchronize
        status = nt_create_file(
            ctypes.byref(handle),
            desired_access,
            ctypes.byref(object_attributes),
            ctypes.byref(io_status),
            None,
            0 if directory else file_attribute_normal,
            file_share_read,
            file_open_if,
            options,
            None,
            0,
        )
        if status < 0:
            error = int(rtl_nt_status_to_dos_error(status))
            raise failed(path, error)
        if handle.value is None:
            raise OSError("NtCreateFile returned no handle")
        opened = int(handle.value)
        try:
            value = attributes(opened, path)
            if value & file_attribute_reparse_point:
                raise ValueError(redirect_error)
            if directory != bool(value & file_attribute_directory):
                kind = "a directory" if directory else "a regular file"
                raise ValueError(f"workspace lock path must be {kind}")
            return opened
        except BaseException:
            close(opened)
            raise

    def open_lock_file(parent: int, path: Path) -> int:
        while True:
            try:
                return open_relative(parent, path.name, path, directory=False)
            except OSError as exc:
                if exc.errno != error_sharing_violation:
                    raise
                time.sleep(0.05)

    directory_handles: list[int] = []
    lock_handle: int | None = None
    lock_fd: int | None = None
    try:
        root = lock_path.parent.parent.parent
        runtime = root / ".memoria"
        locks = runtime / "locks"
        directory_handles.append(open_root_directory(root))
        directory_handles.append(
            open_relative(directory_handles[-1], runtime.name, runtime, directory=True)
        )
        directory_handles.append(
            open_relative(directory_handles[-1], locks.name, locks, directory=True)
        )
        lock_handle = open_lock_file(directory_handles[-1], lock_path)
        open_osfhandle = msvcrt.open_osfhandle
        lock_fd = open_osfhandle(
            lock_handle,
            os.O_RDWR | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOINHERIT", 0),
        )
        lock_handle = None
        lock_file = os.fdopen(lock_fd, "a+b")
        lock_fd = None
        result = _WindowsLockFile(lock_file, directory_handles, close)
        directory_handles = []
        return result
    except BaseException:
        if lock_fd is not None:
            os.close(lock_fd)
        if lock_handle is not None:
            close(lock_handle)
        for handle in reversed(directory_handles):
            close(handle)
        raise


def _open_workspace_lock_file(vault: Path, lock_path: Path):
    redirect_error = "workspace lock path must not redirect through a symlink or junction"
    if os.name != "nt" and not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("workspace lock requires no-follow file opens")
    if os.name == "nt":
        return _open_workspace_lock_file_windows(vault, lock_path)

    directory_fds: list[int] = []
    lock_fd: int | None = None
    try:
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        directory_fds.append(os.open(Path(vault).resolve(), flags))
        for component in (".memoria", "locks"):
            try:
                os.mkdir(component, mode=0o700, dir_fd=directory_fds[-1])
            except FileExistsError:
                pass
            directory_fds.append(os.open(component, flags, dir_fd=directory_fds[-1]))
        lock_flags = os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        lock_fd = os.open(
            "worker.lock",
            lock_flags,
            0o600,
            dir_fd=directory_fds[-1],
        )
        if not stat.S_ISREG(os.fstat(lock_fd).st_mode):
            raise ValueError("workspace lock path must be a regular file")
        lock_file = os.fdopen(lock_fd, "a+b")
        lock_fd = None
        return lock_file
    except OSError as exc:
        if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
            raise ValueError(redirect_error) from exc
        raise
    finally:
        if lock_fd is not None:
            os.close(lock_fd)
        for directory_fd in reversed(directory_fds):
            os.close(directory_fd)


def _workspace_thread_lock(key: str) -> threading.RLock:
    global _WORKSPACE_LOCK_DEPTH, _WORKSPACE_LOCK_PID
    with _WORKSPACE_LOCKS_GUARD:
        if _WORKSPACE_LOCK_PID != os.getpid():
            _WORKSPACE_LOCKS.clear()
            _WORKSPACE_LOCK_DEPTH = threading.local()
            _WORKSPACE_LOCK_PID = os.getpid()
        return _WORKSPACE_LOCKS.setdefault(key, threading.RLock())


@contextlib.contextmanager
def workspace_lock(vault: Path):
    """Serialize one workspace while allowing same-thread nested calls."""
    lock_key = _workspace_lock_key(vault)
    thread_lock = _workspace_thread_lock(lock_key)
    with thread_lock:
        depths = getattr(_WORKSPACE_LOCK_DEPTH, "depths", None)
        if depths is None:
            depths = {}
            _WORKSPACE_LOCK_DEPTH.depths = depths
        depth = int(depths.get(lock_key, 0))
        if depth:
            depths[lock_key] = depth + 1
            try:
                yield
            finally:
                depths[lock_key] = depth
            return

        lock_path = Path(lock_key)
        with _open_workspace_lock_file(Path(vault), lock_path) as lock_file:
            if fcntl is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                try:
                    depths[lock_key] = 1
                    yield
                finally:
                    depths.pop(lock_key, None)
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                return
            if msvcrt is not None:
                lock_file.write(b"\0")
                lock_file.flush()
                lock_file.seek(0)
                while True:
                    try:
                        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                        break
                    except OSError:
                        time.sleep(0.05)
                try:
                    depths[lock_key] = 1
                    yield
                finally:
                    depths.pop(lock_key, None)
                    lock_file.seek(0)
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                return
            depths[lock_key] = 1
            try:
                yield
            finally:
                depths.pop(lock_key, None)
