"""SQLite-backed working state for queue, journal, catalog, and barriers."""

from __future__ import annotations

import contextlib
import ctypes
import errno
import hashlib
import json
import os
import re
import sqlite3
import stat
import subprocess
import threading
import time
from collections import Counter
from collections.abc import Iterable, Mapping
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from memoria_vault.runtime.content_security import (
    classify_fenced_code_opening,
    fenced_code_closes,
)
from memoria_vault.runtime.evidence import (
    EvidenceMarker,
    evidence_ref_kind,
    parse_code_grounds_ref,
    parse_evidence_marker,
    parse_source_span_ref,
)
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.subsystems.lib.edges import EDGE_RELATIONS
from memoria_vault.runtime.time import now_iso
from memoria_vault.runtime.vaultio import is_ulid, parse_frontmatter, safe_read, write_text_durable

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback is exercised only on Windows.
    fcntl = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - POSIX path is exercised in CI.
    msvcrt = None

if TYPE_CHECKING:
    from memoria_vault.runtime.trusted_writer import OperationContext

DB_REL = ".memoria/memoria.sqlite"
JOURNAL_HEAD_REL = ".memoria/journal-head"
SCHEMA_VERSION = 18
ACTORS = frozenset({"pi", "agent", "operation", "integrity"})
REQUEST_STATUSES = frozenset({"pending", "running", "done", "failed", "cancelled"})
CHECK_STATUSES = frozenset({"unchecked", "checked", "quarantined"})
WORK_ASPECT_TYPES = frozenset(
    {"context", "key_idea", "method", "outcome", "limitation", "assumption"}
)
EVIDENCE_TYPES = frozenset({"single-span", "multi-span", "multi-hop", "implicit", "computed"})
_CONCEPT_TYPE_MAPS: dict[Path, dict[str, str]] = {}
_FOLDER_CONCEPT_TYPES: dict[Path, dict[str, str]] = {}
_DIRECT_EVIDENCE_MARKER_RE = re.compile(
    r"(?m)^(?![ \t>|\ufeff])(?!(?:[-+*]|\d+[.)]|:)[ \t]+)"
    r"(?P<prefix>[^\r\n]*\S)[ \t]+(?P<marker>%%ev:\s*[^\r\n]*?%%)"
    r"[ \t`\\*_~]*\r?$"
)
_RAW_EVIDENCE_MARKER_RE = re.compile(r"%%ev:\s*.*?%%")
_FENCED_DIV_RE = re.compile(r"^[ \t]{0,3}(?P<fence>:{3,})(?P<suffix>[^\r\n]*)$")
_QUOTED_FENCE_OPEN_RE = re.compile(
    r"^ {0,3}(?P<quote>(?:>[ \t]*)+)(?P<fence>`{3,}|~{3,})(?P<info>[^\r\n]*)(?:\r?\n)?$"
)
_QUOTED_LINE_RE = re.compile(r"^ {0,3}(?P<quote>(?:>[ \t]*)+)(?P<content>[^\r\n]*)(?:\r?\n)?$")
_LIST_FENCE_OPEN_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<marker>(?:[-+*]|\d{1,9}[.)]))(?P<spacing>[ \t]+)"
    r"(?P<fence>`{3,}|~{3,})(?P<info>[^\r\n]*)(?:\r?\n)?$"
)
_COMPOUND_LIST_QUOTE_FENCE_OPEN_RE = re.compile(
    r"^(?P<indent> *)(?P<marker>(?:[-+*]|\d{1,9}[.)]))(?P<spacing> +)"
    r"(?P<quote>> +)(?P<fence>`{3,}|~{3,})(?P<info>[^\r\n]*)(?:\r?\n)?$"
)
_LIST_ITEM_LINE_RE = re.compile(r"^[ \t]*(?:[-+*]|\d{1,9}[.)])[ \t]+")
_ATX_HEADING_LINE_RE = re.compile(r"^[ ]{0,3}#{1,6}(?:[ \t]+|$)")
_THEMATIC_BREAK_LINE_RE = re.compile(
    r"^[ \t]{0,3}(?:(?:\*[ \t]*){3,}|(?:_[ \t]*){3,}|(?:-[ \t]*){3,})(?:\r?\n)?$"
)
_SAFE_VISIBILITY_FENCE_INFO_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9+._-]*$")
_CITATION_TABLE_CONTAINER_PREFIX_RE = re.compile(
    r"^[ \t]*(?:(?:>[ \t]*)+|(?:[-+*]|\d{1,9}[.)])[ \t]+)"
)
_MARKDOWN_CONTAINER_RE = re.compile(
    r"^[ ]{0,3}(?:>[ \t]*|(?:[-+*~:]|\d+[.)]|"
    r"\((?:\d+|[IVXLCDMivxlcdm]+|@[^\s)]*|[A-Za-z#])\)|"
    r"@[^\s.)]*[.)]|[A-Za-z#][.)]|[IVXLCDMivxlcdm]+[.)])(?:[ \t]+|$))"
)
_MAX_YAML_FRONTMATTER_INDENT = 256
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

    def __exit__(self, *_exc_info: object) -> bool:
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

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    ntdll = ctypes.WinDLL("ntdll")
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
            raise failed(path, ctypes.get_last_error())
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
            raise failed(path, ctypes.get_last_error())
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
        lock_fd = msvcrt.open_osfhandle(
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


def db_path(vault: Path) -> Path:
    return Path(vault) / DB_REL


class _ClosingConnection(sqlite3.Connection):
    def __exit__(self, *exc_info: object) -> bool:
        try:
            return super().__exit__(*exc_info)
        finally:
            self.close()


def connect(vault: Path) -> sqlite3.Connection:
    path = db_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, factory=_ClosingConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = FULL")
    _init(conn)
    return conn


def _schema_sql() -> str:
    return files("memoria_vault.runtime").joinpath("schema.sql").read_text(encoding="utf-8")


def request_envelope(
    *,
    request_id: str,
    operation_id: str,
    args: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
    input_refs: Iterable[str | dict[str, Any]] = (),
    output_intents: Iterable[str | dict[str, Any]] = (),
    primary_target: str = "",
    precondition_hashes: dict[str, Any] | None = None,
    causal_refs: Iterable[str | dict[str, Any]] = (),
    actor: str,
    machine_authored: bool = False,
    provenance: dict[str, Any] | None = None,
    schedule_id: str | None = None,
) -> dict[str, Any]:
    operation = operation_id.strip()
    if not operation:
        raise ValueError("operation_id is required")
    actor = actor.strip()
    if actor not in ACTORS:
        raise ValueError(f"envelope actor must be one of {sorted(ACTORS)}, got: {actor!r}")
    return {
        "request_id": safe_filename(request_id),
        "operation_id": operation,
        "args": dict(args or {}),
        "idempotency_key": idempotency_key or request_id,
        "input_refs": _json_rows(input_refs),
        "output_intents": _json_rows(output_intents),
        "primary_target": normalize_path(primary_target) if primary_target else "",
        "precondition_hashes": dict(precondition_hashes or {}),
        "causal_refs": _json_rows(causal_refs),
        "actor": actor,
        # Authority (`actor`) is not authorship. A door authenticated as the PI can
        # still be posting a body a machine composed; that body must stay untrusted.
        "machine_authored": bool(machine_authored),
        "provenance": dict(provenance or {}),
        "schedule_id": schedule_id or None,
    }


def save_request(
    vault: Path,
    envelope: dict[str, Any],
    job: dict[str, Any],
    *,
    supersede_request_id: str | None = None,
) -> dict[str, Any]:
    created_at = str(job.get("created_at") or now_iso())
    job = json.loads(_json({**job, "request_envelope": envelope}))
    envelope = job["request_envelope"]
    payload = _json(job)
    idem = str(envelope.get("idempotency_key") or envelope["request_id"])
    kind = str(job.get("kind") or "operation")
    superseded_id = safe_filename(supersede_request_id or "")
    if superseded_id:
        if envelope["actor"] != "pi":
            raise ValueError("request supersession requires PI actor authority")
        if superseded_id == envelope["request_id"]:
            raise ValueError("request cannot supersede itself")
        provenance = envelope.get("provenance")
        bound_source = (
            safe_filename(str(provenance.get("supersedes_request_id") or ""))
            if isinstance(provenance, dict)
            else ""
        )
        if bound_source != superseded_id:
            raise ValueError("superseded request id must be bound in request provenance")
        causal_ids = {
            safe_filename(str(ref.get("id") or ""))
            for ref in envelope.get("causal_refs", [])
            if isinstance(ref, dict)
        }
        if superseded_id not in causal_ids:
            raise ValueError("superseded request id must be a causal reference")
    with connect(vault) as conn:
        # Serialize lookup and insertion so a concurrent retry cannot bypass the
        # request-identity comparison between a different actor or payload.
        conn.execute("BEGIN IMMEDIATE")
        existing = conn.execute(
            """
            SELECT kind, job_json
            FROM operation_requests
            WHERE request_id = ? OR idempotency_key = ?
            LIMIT 1
            """,
            (envelope["request_id"], idem),
        ).fetchone()
        if existing is not None:
            existing_job = json.loads(existing["job_json"])
            existing_kind = str(existing_job.get("kind") or existing["kind"])
            if (
                _json(existing_job.get("request_envelope")) != _json(envelope)
                or existing["kind"] != kind
                or existing_kind != kind
            ):
                raise ValueError("idempotency key is already bound to a different request")
            return existing_job
        superseded = None
        superseded_job: dict[str, Any] | None = None
        if superseded_id:
            superseded = conn.execute(
                "SELECT status, job_json FROM operation_requests WHERE request_id = ?",
                (superseded_id,),
            ).fetchone()
            if superseded is None:
                raise FileNotFoundError(f"request not found: {supersede_request_id}")
            if superseded["status"] == "running":
                raise ValueError("request amendment requires a non-running request")
            superseded_job = json.loads(superseded["job_json"])
            prior_successor = str(superseded_job.get("superseded_by_request_id") or "")
            if prior_successor and safe_filename(prior_successor) != envelope["request_id"]:
                raise ValueError(f"request already superseded by request {prior_successor}")
        conn.execute(
            """
            INSERT INTO operation_requests(
                request_id,
                operation_id,
                args_json,
                idempotency_key,
                input_refs_json,
                output_intents_json,
                primary_target,
                precondition_hashes_json,
                causal_refs_json,
                actor,
                provenance_json,
                schedule_id,
                status,
                created_at,
                kind,
                job_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
            """,
            (
                envelope["request_id"],
                envelope["operation_id"],
                _json(envelope["args"]),
                idem,
                _json(envelope["input_refs"]),
                _json(envelope["output_intents"]),
                envelope["primary_target"],
                _json(envelope["precondition_hashes"]),
                _json(envelope["causal_refs"]),
                envelope["actor"],
                _json(envelope["provenance"]),
                envelope["schedule_id"],
                created_at,
                kind,
                payload,
            ),
        )
        if superseded is not None and superseded_job is not None:
            superseded_job["superseded_by_request_id"] = envelope["request_id"]
            if superseded["status"] != "pending":
                conn.execute(
                    "UPDATE operation_requests SET job_json = ? WHERE request_id = ?",
                    (_json(superseded_job), superseded_id),
                )
            else:
                error = f"superseded by request {envelope['request_id']}"
                superseded_job.update({"status": "cancelled", "error": error})
                conn.execute(
                    """
                    UPDATE operation_requests
                    SET status = 'cancelled', completed_at = ?, job_json = ?, error = ?
                    WHERE request_id = ?
                    """,
                    (now_iso(), _json(superseded_job), error, superseded_id),
                )
    return job


def request_job(vault: Path, request_id: str) -> dict[str, Any] | None:
    with connect(vault) as conn:
        row = conn.execute(
            "SELECT job_json FROM operation_requests WHERE request_id = ?",
            (safe_filename(request_id),),
        ).fetchone()
    return json.loads(row["job_json"]) if row is not None else None


def request_row(vault: Path, request_id: str) -> Any | None:
    with connect(vault) as conn:
        return conn.execute(
            """
            SELECT *
            FROM operation_requests
            WHERE request_id = ?
            """,
            (safe_filename(request_id),),
        ).fetchone()


def request_summary(row: Any) -> dict[str, Any]:
    return {
        "request_id": row["request_id"],
        "operation_id": row["operation_id"],
        "status": row["status"],
        "created_at": row["created_at"],
        "completed_at": row["completed_at"],
        "error": row["error"],
    }


def request_detail(row: Any) -> dict[str, Any]:
    return {
        **request_summary(row),
        "args": json.loads(row["args_json"]),
        "idempotency_key": row["idempotency_key"],
        "input_refs": json.loads(row["input_refs_json"]),
        "output_intents": json.loads(row["output_intents_json"]),
        "primary_target": row["primary_target"],
        "precondition_hashes": json.loads(row["precondition_hashes_json"]),
        "causal_refs": json.loads(row["causal_refs_json"]),
        "actor": row["actor"],
        "provenance": json.loads(row["provenance_json"]),
        "schedule_id": row["schedule_id"],
        "kind": row["kind"],
        "job": json.loads(row["job_json"]),
    }


def next_pending_job(vault: Path) -> dict[str, Any] | None:
    with connect(vault) as conn:
        row = conn.execute(
            """
            SELECT job_json
            FROM operation_requests
            WHERE status = 'pending'
            ORDER BY created_at, request_id
            LIMIT 1
            """
        ).fetchone()
    return json.loads(row["job_json"]) if row is not None else None


def claim_request(vault: Path, request_id: str, job: dict[str, Any]) -> bool:
    """Mark one pending request running only if it has not been superseded."""
    request_id = safe_filename(request_id)
    now = now_iso()
    running = {**job, "status": "running"}
    with connect(vault) as conn:
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.execute(
            """
            UPDATE operation_requests
            SET status = 'running', started_at = ?, job_json = ?, error = ''
            WHERE request_id = ? AND status = 'pending'
            """,
            (now, _json(running), request_id),
        )
    return cursor.rowcount == 1


def set_request_running(vault: Path, request_id: str, job: dict[str, Any]) -> None:
    _set_request_state(vault, request_id, "running", {**job, "status": "running"})


def finish_request(vault: Path, request_id: str, status: str, job: dict[str, Any]) -> None:
    _set_request_state(vault, request_id, status, job)


def recover_running_requests(vault: Path) -> list[str]:
    if not db_path(vault).is_file():
        return []
    recovered: list[str] = []
    with connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT request_id, job_json
            FROM operation_requests
            WHERE status = 'running'
            ORDER BY created_at, request_id
            """
        ).fetchall()
        now = now_iso()
        for row in rows:
            job = json.loads(row["job_json"])
            job.update(
                {
                    "status": "failed",
                    "failed_at": now,
                    "error": "interrupted during workspace recovery; retry required",
                }
            )
            conn.execute(
                """
                UPDATE operation_requests
                SET status = 'failed',
                    completed_at = ?,
                    job_json = ?,
                    error = ?
                WHERE request_id = ?
                """,
                (now, _json(job), job["error"], row["request_id"]),
            )
            recovered.append(str(row["request_id"]))
    return recovered


def _append_journal_row(vault: Path, event: dict[str, Any], *, machine: str) -> None:
    """Store an already decorated journal event without provenance fallback."""
    row = dict(event)
    if row.get("machine") != machine:
        raise AssertionError("journal payload machine must match row machine")
    _insert_journal_row(vault, row, machine=machine)


def _insert_journal_row(vault: Path, row: dict[str, Any], *, machine: str) -> None:
    with connect(vault) as conn:
        conn.execute("BEGIN IMMEDIATE")
        _insert_journal_row_conn(conn, row, machine=machine)


def _insert_journal_row_conn(
    conn: sqlite3.Connection, row: dict[str, Any], *, machine: str
) -> None:
    """Insert one authoritative journal row using the caller's transaction."""
    timestamp = str(row.get("timestamp") or now_iso())
    event_type = str(row.get("event") or row.get("type") or "event")
    payload = _json(row)
    last = conn.execute(
        "SELECT event_id, row_hash FROM event_log ORDER BY event_id DESC LIMIT 1"
    ).fetchone()
    prev_hash = "GENESIS" if last is None else str(last["row_hash"])
    event_id = 1 if last is None else int(last["event_id"]) + 1
    row_hash = _journal_hash(event_id, timestamp, event_type, machine, payload, prev_hash)
    conn.execute(
        """
        INSERT INTO event_log(
            event_id, timestamp, event_type, machine, payload_json, prev_hash, row_hash
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (event_id, timestamp, event_type, machine, payload, prev_hash, row_hash),
    )


def journal_head(vault: Path) -> str:
    with connect(vault) as conn:
        row = conn.execute(
            "SELECT row_hash FROM event_log ORDER BY event_id DESC LIMIT 1"
        ).fetchone()
    return "" if row is None else str(row["row_hash"])


def journal_head_anchor(vault: Path) -> str:
    return journal_head(vault) or "GENESIS"


def write_journal_head_anchor(vault: Path) -> str:
    write_text_durable(Path(vault) / JOURNAL_HEAD_REL, journal_head_anchor(vault) + "\n")
    return JOURNAL_HEAD_REL


def verify_journal_chain(vault: Path) -> dict[str, Any]:
    """Verify the authoritative event chain and its tracked head anchor."""
    with connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT event_id, timestamp, event_type, machine,
                   payload_json, prev_hash, row_hash
            FROM event_log
            ORDER BY event_id
            """
        ).fetchall()

    previous = "GENESIS"
    row_hashes: set[str] = set()
    for row in rows:
        event_id = int(row["event_id"])
        try:
            event = json.loads(str(row["payload_json"]))
            if not isinstance(event, dict):
                raise ValueError("journal payload must be an object")
            expected = _journal_hash(
                event_id,
                str(row["timestamp"]),
                str(row["event_type"]),
                str(row["machine"]),
                str(row["payload_json"]),
                previous,
            )
        except (TypeError, ValueError, json.JSONDecodeError):
            return _journal_verification_failure(
                rows, error=f"journal chain has invalid payload JSON at event {event_id}"
            )
        payload_type = str(event.get("event") or event.get("type") or "event")
        if payload_type != str(row["event_type"]):
            return _journal_verification_failure(
                rows, error=f"journal event type conflicts with payload at event {event_id}"
            )
        if event.get("machine") != str(row["machine"]):
            return _journal_verification_failure(
                rows, error=f"journal machine conflicts with payload at event {event_id}"
            )
        if str(row["prev_hash"]) != previous or str(row["row_hash"]) != expected:
            return _journal_verification_failure(
                rows, error=f"journal chain broken at event {event_id}"
            )
        previous = str(row["row_hash"])
        row_hashes.add(previous)

    tip = previous
    anchor_path = Path(vault) / JOURNAL_HEAD_REL
    try:
        anchor = anchor_path.read_text(encoding="utf-8").strip() if anchor_path.is_file() else ""
    except (OSError, UnicodeError) as exc:
        return _journal_verification_failure(
            rows,
            tip=tip,
            error=f"journal-head anchor is unreadable: {exc}",
        )
    if rows and not anchor:
        return _journal_verification_failure(
            rows,
            tip=tip,
            error="journal-head anchor is missing for a nonempty chain",
        )
    if anchor and anchor != tip:
        return _journal_verification_failure(
            rows,
            tip=tip,
            anchor=anchor,
            error="journal-head anchor does not match chain tip",
        )
    committed_anchor = _committed_journal_head_anchor(Path(vault))
    if committed_anchor is not None and committed_anchor not in {"GENESIS", *row_hashes}:
        return _journal_verification_failure(
            rows,
            tip=tip,
            anchor=anchor,
            error="committed journal-head anchor is not a prefix of the live chain",
        )
    export_error = _journal_export_subset_error(Path(vault), rows)
    if export_error:
        return _journal_verification_failure(
            rows,
            tip=tip,
            anchor=anchor,
            error=export_error,
        )
    return {
        "ok": True,
        "events": len(rows),
        "tip": tip,
        "anchor": anchor,
        "error": "",
    }


def read_event_log(
    vault: Path,
    *,
    event_types: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Read authoritative journal payloads in event order."""
    selected = sorted({str(value) for value in event_types or ()})
    query = "SELECT event_type, machine, payload_json FROM event_log"
    params: tuple[str, ...] = ()
    if selected:
        query += f" WHERE event_type IN ({','.join('?' for _ in selected)})"
        params = tuple(selected)
    query += " ORDER BY event_id"
    with connect(vault) as conn:
        rows = conn.execute(query, params).fetchall()

    events: list[dict[str, Any]] = []
    for row in rows:
        try:
            event = json.loads(str(row["payload_json"]))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("event_log payload must be valid JSON") from exc
        if not isinstance(event, dict):
            raise ValueError("event_log payload must be a JSON object")
        if event.get("machine") != str(row["machine"]):
            raise ValueError("event_log payload machine does not match its row")
        payload_type = str(event.get("event") or event.get("type") or "event")
        if payload_type != str(row["event_type"]):
            raise ValueError("event_log payload type does not match its row")
        events.append(event)
    return events


def journal_export_complete_prefix(raw: bytes) -> bytes:
    """Return the complete CR/LF-delimited journal export records in ``raw``."""
    if not raw or raw.endswith((b"\n", b"\r")):
        return raw
    return raw[: max(raw.rfind(b"\n"), raw.rfind(b"\r")) + 1]


def _journal_export_subset_error(vault: Path, rows: list[Any]) -> str:
    authoritative: Counter[tuple[str, str]] = Counter()
    for row in rows:
        try:
            event = json.loads(str(row["payload_json"]))
        except (TypeError, ValueError, json.JSONDecodeError):
            return f"event_log contains invalid payload JSON at event {row['event_id']}"
        if not isinstance(event, dict):
            return f"event_log payload is not an object at event {row['event_id']}"
        machine = str(row["machine"])
        if event.get("machine") != machine:
            return f"event_log machine conflicts with payload at event {row['event_id']}"
        authoritative[(machine, _json(event))] += 1

    root = vault / ".memoria/journal"
    for path in sorted(root.glob("*.jsonl")):
        try:
            raw = path.read_bytes()
        except OSError as exc:
            return f"journal JSONL export is unreadable: {path.name}: {exc}"
        lines = journal_export_complete_prefix(raw).splitlines()
        machine = path.stem
        for line_number, raw_line in enumerate(lines, start=1):
            try:
                line = raw_line.decode("utf-8")
            except UnicodeDecodeError:
                return f"invalid UTF-8 in {path.name} at line {line_number}"
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                return f"invalid JSONL in {path.name} at line {line_number}"
            if not isinstance(event, dict):
                return f"invalid JSONL object in {path.name} at line {line_number}"
            if event.get("machine") != machine:
                return f"JSONL machine mismatch in {path.name} at line {line_number}"
            key = (machine, _json(event))
            if not authoritative[key]:
                return (
                    f"JSONL event in {path.name} at line {line_number} "
                    "has no authoritative event_log row"
                )
            authoritative[key] -= 1
    return ""


def _committed_journal_head_anchor(vault: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "show", f"HEAD:{JOURNAL_HEAD_REL}"],
            cwd=vault,
            check=False,
            text=True,
            capture_output=True,
        )
    except OSError:
        return None
    return None if proc.returncode else proc.stdout.strip()


def _journal_verification_failure(
    rows: list[Any],
    *,
    error: str,
    tip: str = "",
    anchor: str = "",
) -> dict[str, Any]:
    return {
        "ok": False,
        "events": len(rows),
        "tip": tip,
        "anchor": anchor,
        "error": error,
    }


def set_concept_verdict(vault: Path, concept_id: str, check_status: str) -> None:
    status = _check_status(check_status)
    with connect(vault) as conn:
        # One key space per identity: the verdict and its flags are both FK-backed
        # by concepts.concept_id, so resolve once and write both by that id.
        # `outputs` keeps its own path-keyed output_id space.
        target = resolve_concept_id(conn, concept_id)
        _set_concept_verdict_conn(conn, target, status)
        conn.execute(
            "UPDATE outputs SET check_status = ? WHERE output_id = ?",
            (status, normalize_path(concept_id)),
        )
        if status == "checked":
            conn.execute(
                "DELETE FROM concept_flags WHERE concept_id = ? AND flag = 'stale'",
                (target,),
            )


def concept_check_status(vault: Path, concept_id: str) -> str:
    if not db_path(vault).is_file():
        return "unchecked"
    with connect(vault) as conn:
        row = conn.execute(
            "SELECT check_status FROM concept_status WHERE concept_id = ?",
            (resolve_concept_id(conn, concept_id),),
        ).fetchone()
    return "unchecked" if row is None else str(row["check_status"])


def concept_check_statuses(vault: Path) -> dict[str, str]:
    """Return every Concept verdict keyed by its rendered path, id when it has none.

    v16 decouples the identity from the path, so this bulk projection keys by the
    path its one caller walks the vault by — the id-keyed map it used to return
    reads as ``unchecked`` for every ULID-keyed file Concept.
    """
    if not db_path(vault).is_file():
        return {}
    with connect(vault) as conn:
        rows = conn.execute("SELECT concept_id, path, check_status FROM concept_status").fetchall()
    return {str(row["path"] or row["concept_id"]): str(row["check_status"]) for row in rows}


def output_record(vault: Path, output_id: str) -> dict[str, Any] | None:
    target = normalize_path(output_id)
    if not db_path(vault).is_file():
        return None
    with connect(vault) as conn:
        row = conn.execute(
            """
            SELECT output_id, concept_type, store, target_path, check_status,
                   materialization_status, output_sha256
            FROM outputs
            WHERE output_id = ?
            """,
            (target,),
        ).fetchone()
    return None if row is None else dict(row)


def rebuild_file_concept_mirror(vault: Path, rows: Iterable[dict[str, str]]) -> dict[str, int]:
    """Rebuild identity-keyed file Concept parents, normalizing types through the registry.

    Each row carries its own ``concept_id`` and ``path``: v16 decouples the two, so
    a row whose ``id`` is a frontmatter ULID keeps that identity across a rename,
    and one without a ULID keeps its path key. Only absent file rows carrying no
    verdict are pruned: a verdict-bearing row is the PI's judgment and survives its
    file. Pruning a row cascades its outgoing edges and pends inbound ones through
    the v16 foreign keys. A reconciled rename also carries the path-keyed ``outputs``
    row to the new path, so the read barrier still finds the PI's checked record
    there (``_reconcile_renamed_output_conn``).
    """
    rows = list(rows)
    _refuse_duplicate_batch_identities(rows)
    with connect(vault) as conn:
        for row in rows:
            _reconcile_renamed_output_conn(
                conn,
                normalize_path(row["concept_id"]),
                normalize_path(str(row.get("path") or row["concept_id"])),
            )
        keep = [
            ensure_concept_parent_conn(
                conn,
                normalize_path(row["concept_id"]),
                concept_type=str(row["concept_type"]),
                store="file",
                path=normalize_path(str(row.get("path") or row["concept_id"])),
            )
            for row in rows
        ]
        deleted = conn.execute(
            """
            DELETE FROM concepts
            WHERE store = 'file'
              AND concept_id NOT IN (SELECT value FROM json_each(?))
              AND concept_id NOT IN (SELECT concept_id FROM concept_verdicts)
            """,
            (_json(keep),),
        ).rowcount
    return {"deleted": int(deleted), "inserted": len(rows)}


def update_concept_path(vault: Path, concept_id: str, old_path: str, new_path: str) -> None:
    """Move one Concept's path across every path-keyed table, in one transaction.

    The in-band seam behind ``memoria mv``. It is a strict superset of the
    out-of-band reconcile it calls (``_reconcile_renamed_output_conn``): that pass
    only has to keep the materialization ledger findable at the new path, while a
    move must also carry the edge mirror, the passage index and
    ``file_index_state`` — the row the out-of-band pass strands, and the one
    ``refresh_stale_passages`` computes its removed set from. The reconcile
    statement is *called*, never re-issued: it shipped a Critical once already
    (``materialization_payloads`` had no ``ON UPDATE CASCADE``) and a second copy
    is a second place for the next one to hide. For the same reason neither
    enumeration is written out here: ``_rekey_path_keyed_concept_conn`` is identity
    space and ``_rekey_path_space_conn`` is path space, one named home each.

    Nothing here touches ``output_sha256``. A rename does not change a byte, so
    the barrier keeps hashing the same content at the new path and edited content
    still cannot keep a ``checked`` verdict.
    """
    old_rel = normalize_path(old_path)
    new_rel = normalize_path(new_path)
    with connect(vault) as conn:
        if concept_id == new_rel:
            _rekey_path_keyed_concept_conn(conn, old_rel, new_rel)
        # Reads `concepts.path` for the old key, so it runs before that column moves.
        _reconcile_renamed_output_conn(conn, concept_id, new_rel)
        conn.execute("UPDATE concepts SET path = ? WHERE concept_id = ?", (new_rel, concept_id))
        _rekey_path_space_conn(conn, old_rel, new_rel)


def _rekey_path_space_conn(conn: sqlite3.Connection, old_rel: str, new_rel: str) -> None:
    """Move every row that references a Concept by its **path**, and this is the whole set.

    Identity space is ``_rekey_path_keyed_concept_conn`` and the materialization
    ledger is ``_reconcile_renamed_output_conn``; this is the third enumeration,
    and it lives in one named place because each of the first two shipped a defect
    by stopping one table short. Add here, never at a call site.

    The two tables the first path-space pass missed are the two that key no
    verdict, which is exactly why they hid. ``file_baseline`` keys the *alert*
    layer: leave its row at the vacated path and both ``_reconcile_file_baselines``
    and the observe loop take their ``baseline is None`` early exit, so a tampered
    moved file raises no ``foreign-edit`` and the baseline adopts the tampered
    bytes as truth — while a newcomer at the vacated path inherits the stale hash
    and raises a ``foreign-edit`` nobody caused. ``evidence_sets.block_ref`` is
    ``{path}#^blk-…`` and a draft's evidence is joined by prefix, so a stale prefix
    reads as a draft with no evidence at all; ``evidence_bindings`` is immutable by
    trigger, so the binding cannot simply be reissued afterwards.

    ``UPDATE OR REPLACE`` carries the caller's stated reverse limit: a row already
    sitting at the destination is dropped, and reversing the update cannot
    resurrect it.
    """
    conn.execute(
        "UPDATE OR REPLACE concept_edges SET target_path = ? WHERE target_path = ?",
        (new_rel, old_rel),
    )
    conn.execute(
        "UPDATE concept_edges SET source_path = ? WHERE source_path = ?", (new_rel, old_rel)
    )
    conn.execute("UPDATE passages SET path = ? WHERE path = ?", (new_rel, old_rel))
    conn.execute(
        "UPDATE OR REPLACE file_index_state SET path = ? WHERE path = ?", (new_rel, old_rel)
    )
    conn.execute(
        "UPDATE OR REPLACE file_baseline SET subject_id = ? WHERE subject_id = ?",
        (new_rel, old_rel),
    )
    # Exact-prefix rewrite, not LIKE: a path may hold `%` or `_`, which LIKE would
    # read as wildcards and match a sibling Concept's block refs.
    prefix = f"{old_rel}#"
    conn.execute(
        "UPDATE evidence_sets SET block_ref = ? || substr(block_ref, ?) "
        "WHERE substr(block_ref, 1, ?) = ?",
        (f"{new_rel}#", len(prefix) + 1, len(prefix), prefix),
    )


def _rekey_path_keyed_concept_conn(conn: sqlite3.Connection, old_id: str, new_id: str) -> None:
    """Move a path-keyed Concept's identity, and every row that keys by it without an FK.

    A Concept with no frontmatter ULID keys by its path, so a rename moves its
    identity too. Left behind, the next file dropped at the vacated path resolves
    onto this row and inherits the PI's verdict.

    ``concept_verdicts``, ``concept_flags`` and ``concept_edges``' endpoint ids all
    declare ``REFERENCES concepts(concept_id) ON UPDATE CASCADE``, so they ride the
    first statement. **Everything below keys by the same identity with no foreign
    key to carry it, and this is the whole enumeration** — the reason it lives in
    one named place is that the first pass at it stopped one table short and left
    ``passages.concept_id`` at the vacated path, where the verdict-cascade triggers
    (``WHERE concept_id = NEW.concept_id``) hand the *moved* Concept's passages to
    whatever lands there next while its verdict still reads ``checked``. Add here,
    never at a call site.

    A conflicting id raises and rolls the caller's whole move back, which is the
    refusal it wants.

    ``concept_edges.edge_id`` is a hash of the identity triple, so the cascade
    invalidates it on every edge touching this Concept. It is blanked here rather
    than recomputed in place: ``idx_concept_edges_edge_id`` is UNIQUE and checked
    per statement, so a row recomputed to a value another affected row is still
    carrying stale would raise mid-enumeration. ``''`` is already this column's
    unresolved value and the partial index skips it, so the next
    ``replace_concept_edges`` settles it over the live triple. A *stale* id instead
    survives as a plausible-looking hash that the next file dropped at the vacated
    path recomputes exactly — a UNIQUE violation that kills the whole mirror
    rebuild, which is the one failure "it self-heals next pass" cannot cover.
    """
    conn.execute("UPDATE concepts SET concept_id = ? WHERE concept_id = ?", (new_id, old_id))
    conn.execute("UPDATE derivations SET input_id = ? WHERE input_id = ?", (new_id, old_id))
    conn.execute("UPDATE derivations SET output_id = ? WHERE output_id = ?", (new_id, old_id))
    conn.execute("UPDATE passages SET concept_id = ? WHERE concept_id = ?", (new_id, old_id))
    conn.execute(
        "UPDATE concept_edges SET edge_id = ''"
        " WHERE source_concept_id = ? OR target_concept_id = ?",
        (new_id, new_id),
    )


def _reconcile_renamed_output_conn(
    conn: sqlite3.Connection, concept_id: str, new_path: str
) -> None:
    """Carry the path-keyed materialization ledger row along a reconciled rename.

    ``outputs`` stays path-keyed (NID-B.2), but its key is the *current* path: a
    rename that reconciles ``concepts.path`` must move it, or the read barrier
    reads no checked output record at the new path and refuses content the PI did
    check. The sha256 comparison in ``is_consumable_checked_file`` is untouched, so
    a rename *and* edit arriving in one reindex pass is still refused. An edit made
    after the rename has been indexed is a different case: ``indexing`` re-indexes
    any path already recorded ``checked`` without re-running the barrier, which it
    does for a never-renamed file too — this reconcile leaves a renamed file at
    exactly that standing, neither creating nor widening the gap.

    The FK to ``outputs`` from ``materialization_payloads`` is ``ON UPDATE
    CASCADE`` (``schema.sql``) so this key move carries the writer's payload child
    with it; without that the statement violates the constraint on any Concept
    staged through ``record_file_output``.
    """
    resident = conn.execute(
        "SELECT path FROM concepts WHERE concept_id = ?", (concept_id,)
    ).fetchone()
    old_path = str(resident["path"]) if resident is not None else ""
    if not old_path or not new_path or old_path == new_path:
        return
    conn.execute(
        "UPDATE OR REPLACE outputs SET output_id = ?, target_path = ? WHERE output_id = ?",
        (new_path, new_path, old_path),
    )


def _refuse_duplicate_batch_identities(rows: list[dict[str, str]]) -> None:
    """Refuse a mirror batch in which two files claim one Concept identity.

    Copying a file (``cp``, Obsidian's "Make a copy") duplicates its frontmatter
    ``id``. Per row that reads as *same identity, requested path unowned* — a
    rename, which the guard allows — so the batch is the only place the duplicate
    is visible. Left unchecked the later row moves the Concept's path onto content
    the PI never reviewed and hands it the verdict rendered over the original,
    with directory order deciding the survivor. This is the dual of two identities
    claiming one path, which ``ensure_concept_parent_conn`` already refuses.
    """
    seen: dict[str, str] = {}
    for row in rows:
        concept_id = normalize_path(str(row["concept_id"]))
        path = normalize_path(str(row.get("path") or row["concept_id"]))
        if concept_id in seen:
            raise RuntimeError(
                f"duplicate Concept identity in one mirror batch: concept_id={concept_id!r}"
                f" is claimed by both {seen[concept_id]!r} and {path!r}; give each file its"
                " own frontmatter id before mirroring"
            )
        seen[concept_id] = path


def record_file_output(
    vault: Path,
    *,
    output_id: str,
    concept_type: str,
    check_status: str,
    output_sha256: str,
    staging_id: str,
    payload_text: str,
    context: OperationContext,
    inputs: Iterable[dict[str, Any]],
) -> None:
    target = normalize_path(output_id)
    if not payload_text:
        raise ValueError("file materialization payload is required")
    if _sha256_text(payload_text) != output_sha256:
        raise ValueError(f"materialization payload hash mismatch for {target}")
    with connect(vault) as conn:
        # `outputs` and its materialization payload stay path-keyed; the Concept
        # parent, its verdict, and the derivation endpoints use the file identity.
        key = ensure_concept_parent_conn(
            conn,
            _concept_key_for_file(vault, target, payload_text),
            concept_type=concept_type,
            store="file",
            path=target,
        )
        _set_concept_verdict_conn(conn, key, _check_status(check_status))
        conn.execute(
            """
            INSERT INTO outputs(
                output_id,
                concept_type,
                store,
                target_path,
                staging_path,
                check_status,
                materialization_status,
                output_sha256
            )
            VALUES (?, ?, 'file', ?, ?, ?, 'pending', ?)
            ON CONFLICT(output_id) DO UPDATE SET
                concept_type = excluded.concept_type,
                store = excluded.store,
                target_path = excluded.target_path,
                staging_path = excluded.staging_path,
                check_status = excluded.check_status,
                materialization_status = 'pending',
                output_sha256 = excluded.output_sha256,
                failure_reason = NULL
            """,
            (target, concept_type, target, staging_id, check_status, output_sha256),
        )
        conn.execute(
            """
            INSERT INTO materialization_payloads(output_id, expected_sha256, payload_text)
            VALUES (?, ?, ?)
            ON CONFLICT(output_id) DO UPDATE SET
                expected_sha256 = excluded.expected_sha256,
                payload_text = excluded.payload_text
            """,
            (target, output_sha256, payload_text),
        )
        for row in inputs:
            input_id = row.get("id") if isinstance(row, dict) else None
            if isinstance(input_id, str) and input_id.strip():
                conn.execute(
                    """
                    INSERT INTO derivations(input_id, output_id, actor)
                    VALUES (?, ?, ?)
                    ON CONFLICT(input_id, output_id)
                    DO UPDATE SET actor = excluded.actor
                    """,
                    (resolve_concept_id(conn, input_id), key, context.actor),
                )


def mark_checked(vault: Path, output_id: str, output_sha256: str, payload_text: str = "") -> None:
    target = normalize_path(output_id)
    with connect(vault) as conn:
        conn.execute(
            "UPDATE outputs SET check_status = 'checked', output_sha256 = ? WHERE output_id = ?",
            (output_sha256, target),
        )
        # Same one-key-space rule as set_concept_verdict: the flag delete must use
        # the resolved identity, not the raw output path.
        concept_id = resolve_concept_id(conn, target)
        _set_concept_verdict_conn(conn, concept_id, "checked")
        conn.execute(
            "DELETE FROM concept_flags WHERE concept_id = ? AND flag = 'stale'",
            (concept_id,),
        )
        if payload_text:
            if _sha256_text(payload_text) != output_sha256:
                raise ValueError(f"checked payload hash mismatch for {target}")
            conn.execute(
                """
                UPDATE materialization_payloads
                SET expected_sha256 = ?, payload_text = ?
                WHERE output_id = ?
                """,
                (output_sha256, payload_text, target),
            )


def record_observed_file_edit(
    vault: Path,
    *,
    output_id: str,
    concept_type: str,
    output_sha256: str,
) -> None:
    target = normalize_path(output_id)
    with connect(vault) as conn:
        key = ensure_concept_parent_conn(
            conn,
            _concept_key_for_file(vault, target),
            concept_type=concept_type,
            store="file",
            path=target,
        )
        _set_concept_verdict_conn(conn, key, "unchecked")
        conn.execute(
            """
            INSERT INTO outputs(
                output_id,
                concept_type,
                store,
                target_path,
                check_status,
                materialization_status,
                output_sha256
            )
            VALUES (?, ?, 'file', ?, 'unchecked', 'materialized', ?)
            ON CONFLICT(output_id) DO UPDATE SET
                concept_type = excluded.concept_type,
                store = excluded.store,
                target_path = excluded.target_path,
                check_status = 'unchecked',
                materialization_status = 'materialized',
                output_sha256 = excluded.output_sha256,
                failure_reason = NULL
            """,
            (target, concept_type, target, output_sha256),
        )


def upsert_file_baseline(
    vault: Path,
    subject_id: str,
    *,
    human_sha256: str,
    restriction_keys: list[str],
) -> None:
    target = normalize_path(subject_id)
    keys = [str(key) for key in restriction_keys]
    with connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO file_baseline(subject_id, human_sha256, restriction_keys_json, observed_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(subject_id) DO UPDATE SET
                human_sha256 = excluded.human_sha256,
                restriction_keys_json = excluded.restriction_keys_json,
                observed_at = excluded.observed_at
            """,
            (target, human_sha256, _json(keys), now_iso()),
        )


def file_baseline(vault: Path, subject_id: str) -> dict[str, Any] | None:
    if not db_path(vault).is_file():
        return None
    target = normalize_path(subject_id)
    with connect(vault) as conn:
        row = conn.execute(
            """
            SELECT subject_id, human_sha256, restriction_keys_json
            FROM file_baseline
            WHERE subject_id = ?
            """,
            (target,),
        ).fetchone()
    if row is None:
        return None
    return {
        "subject_id": row["subject_id"],
        "human_sha256": row["human_sha256"],
        "restriction_keys": json.loads(row["restriction_keys_json"] or "[]"),
    }


def mark_materialized(vault: Path, output_id: str, *, commit: str = "") -> None:
    target = normalize_path(output_id)
    with connect(vault) as conn:
        conn.execute(
            """
            UPDATE outputs
            SET materialization_status = 'materialized',
                materialized_commit = ?,
                failure_reason = NULL
            WHERE output_id = ?
            """,
            (commit, target),
        )


def set_concept_flag(
    vault: Path,
    concept_id: str,
    flag: str,
    *,
    reason: str = "",
    trigger_id: str = "",
) -> None:
    if flag != "stale":
        raise ValueError(f"invalid concept flag: {flag!r}")
    with connect(vault) as conn:
        # v16 keys flags by the resolved Concept identity: the FK to
        # concepts(concept_id) rejects a flag on a Concept that does not exist and
        # cascades the row away when that Concept is pruned.
        target = resolve_concept_id(conn, concept_id)
        try:
            conn.execute(
                """
                INSERT INTO concept_flags(concept_id, flag, reason, trigger_id, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(concept_id, flag) DO UPDATE SET
                    reason = excluded.reason,
                    trigger_id = excluded.trigger_id,
                    created_at = excluded.created_at
                """,
                (target, flag, reason, normalize_path(trigger_id) if trigger_id else "", now_iso()),
            )
        except sqlite3.IntegrityError as exc:
            if "FOREIGN KEY" not in str(exc):
                raise
            raise _concept_missing_parent(concept_id, target, f"flag {flag!r}") from exc


def concept_flags(vault: Path, concept_id: str) -> dict[str, dict[str, str]]:
    if not db_path(vault).is_file():
        return {}
    with connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT flag, reason, trigger_id, created_at
            FROM concept_flags
            WHERE concept_id = ?
            ORDER BY flag
            """,
            (resolve_concept_id(conn, concept_id),),
        ).fetchall()
    return {
        str(row["flag"]): {
            "reason": str(row["reason"]),
            "trigger_id": str(row["trigger_id"]),
            "created_at": str(row["created_at"]),
        }
        for row in rows
    }


def note_curation_status(vault: Path, concept_id: str) -> str:
    """Return note-candidate lifecycle from journal events, not frontmatter."""
    target = normalize_path(concept_id)
    if not db_path(vault).is_file():
        return ""
    status = ""
    with connect(vault) as conn:
        rows = conn.execute("SELECT payload_json FROM event_log ORDER BY event_id").fetchall()
    # ponytail: journal scan is fine at current volume; project if candidate volume matters.
    for row in rows:
        try:
            payload = json.loads(row["payload_json"])
        except (TypeError, json.JSONDecodeError):
            continue
        if (
            payload.get("event") == "derived"
            and payload.get("operation") == "propose-note-candidates"
            and payload.get("output_id") == target
        ):
            status = "candidate"
        elif (
            payload.get("event") == "resolved"
            and payload.get("operation") == "curate-note-candidate"
            and payload.get("target_id") == target
        ):
            status = str(payload.get("resolution") or "").strip().lower()
    return status


def record_projection_output(
    vault: Path,
    *,
    output_id: str,
    output_sha256: str,
    payload_text: str,
) -> None:
    target = normalize_path(output_id)
    if _sha256_text(payload_text) != output_sha256:
        raise ValueError(f"projection payload hash mismatch for {target}")
    with connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO outputs(
                output_id,
                concept_type,
                store,
                target_path,
                check_status,
                materialization_status,
                output_sha256
            )
            VALUES (?, 'projection', 'file', ?, 'checked', 'pending', ?)
            ON CONFLICT(output_id) DO UPDATE SET
                concept_type = excluded.concept_type,
                store = excluded.store,
                target_path = excluded.target_path,
                check_status = excluded.check_status,
                materialization_status = 'pending',
                output_sha256 = excluded.output_sha256,
                failure_reason = NULL
            """,
            (target, target, output_sha256),
        )
        conn.execute(
            """
            INSERT INTO materialization_payloads(output_id, expected_sha256, payload_text)
            VALUES (?, ?, ?)
            ON CONFLICT(output_id) DO UPDATE SET
                expected_sha256 = excluded.expected_sha256,
                payload_text = excluded.payload_text
            """,
            (target, output_sha256, payload_text),
        )


def recover_pending_materializations(vault: Path) -> list[str]:
    vault = Path(vault)
    if not db_path(vault).is_file():
        return []
    restored: list[str] = []
    with connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT o.output_id, o.target_path, o.output_sha256, p.payload_text
            FROM outputs o
            LEFT JOIN materialization_payloads p ON p.output_id = o.output_id
            WHERE o.store = 'file'
              AND o.check_status = 'checked'
              AND o.materialization_status = 'pending'
            ORDER BY o.output_id
            """
        ).fetchall()
        for row in rows:
            target = Path(vault) / str(row["target_path"])
            expected = str(row["output_sha256"])
            commit = _committed_materialization_commit(vault, str(row["target_path"]), expected)
            if target.is_file() and sha256_file(target) == expected:
                if not commit:
                    conn.execute(
                        """
                        UPDATE outputs
                        SET materialization_status = 'failed',
                            failure_reason = 'materialization target is not committed'
                        WHERE output_id = ?
                        """,
                        (row["output_id"],),
                    )
                    continue
                conn.execute(
                    """
                    UPDATE outputs
                    SET materialization_status = 'materialized',
                        materialized_commit = ?,
                        failure_reason = NULL
                    WHERE output_id = ?
                    """,
                    (commit, row["output_id"]),
                )
                continue
            payload = row["payload_text"]
            if not isinstance(payload, str) or not payload:
                conn.execute(
                    """
                    UPDATE outputs
                    SET materialization_status = 'failed',
                        failure_reason = 'missing durable materialization payload'
                    WHERE output_id = ?
                    """,
                    (row["output_id"],),
                )
                continue
            if _sha256_text(payload) != expected:
                conn.execute(
                    """
                    UPDATE outputs
                    SET materialization_status = 'failed',
                        failure_reason = 'materialization payload hash mismatch'
                    WHERE output_id = ?
                    """,
                    (row["output_id"],),
                )
                continue
            if not commit:
                conn.execute(
                    """
                    UPDATE outputs
                    SET materialization_status = 'failed',
                        failure_reason = 'materialization target is not committed'
                    WHERE output_id = ?
                    """,
                    (row["output_id"],),
                )
                continue
            write_text_durable(target, payload, create_parent=True)
            conn.execute(
                """
                UPDATE outputs
                SET materialization_status = 'materialized',
                    materialized_commit = ?,
                    failure_reason = NULL
                WHERE output_id = ?
                """,
                (commit, row["output_id"]),
            )
            restored.append(str(row["target_path"]))
    return restored


def upsert_catalog_record(
    vault: Path,
    *,
    work_id: str,
    title: str,
    description: str = "",
    concept_path: str = "",
    doi: str | None = None,
    resource: str = "",
    item_type: str = "article",
    identifiers: dict[str, Any] | None = None,
    citekey: str = "",
    csl_json: dict[str, Any] | None = None,
    provider_coverage: str = "partial",
    text_status: str = "metadata-only",
    check_status: str = "unchecked",
    content_hash: str = "",
    raw_hash: str = "",
    content_path: str = "",
    raw_path: str = "",
) -> None:
    stable_work_id = _work_id(work_id)
    identifiers = dict(identifiers or {})
    csl_json = dict(csl_json or {})
    stable_doi = str(doi or identifiers.get("doi") or csl_json.get("DOI") or "").strip() or None
    with connect(vault) as conn:
        concept_id = ensure_concept_parent_conn(
            conn,
            stable_work_id,
            concept_type="work",
            store="db",
            path=f"catalog/sources/{stable_work_id}",
        )
        conn.execute(
            """
            INSERT INTO catalog_sources(
                work_id,
                concept_path,
                doi,
                title,
                description,
                resource,
                item_type,
                identifiers_json,
                citekey,
                csl_json,
                provider_coverage,
                text_status,
                check_status,
                content_hash,
                raw_hash,
                content_path,
                raw_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(work_id) DO UPDATE SET
                concept_path = excluded.concept_path,
                doi = excluded.doi,
                title = excluded.title,
                description = excluded.description,
                resource = excluded.resource,
                item_type = excluded.item_type,
                identifiers_json = excluded.identifiers_json,
                citekey = excluded.citekey,
                csl_json = excluded.csl_json,
                provider_coverage = excluded.provider_coverage,
                text_status = excluded.text_status,
                check_status = excluded.check_status,
                content_hash = excluded.content_hash,
                raw_hash = excluded.raw_hash,
                content_path = excluded.content_path,
                raw_path = excluded.raw_path
            """,
            (
                stable_work_id,
                normalize_path(concept_path)
                if concept_path
                else f"catalog/sources/{stable_work_id}",
                stable_doi,
                title or stable_work_id,
                description,
                resource,
                item_type or "article",
                _json(identifiers),
                citekey,
                _json(csl_json),
                provider_coverage,
                text_status,
                check_status,
                content_hash,
                raw_hash,
                normalize_path(content_path) if content_path else "",
                normalize_path(raw_path) if raw_path else "",
            ),
        )
        _set_concept_verdict_conn(conn, concept_id, _check_status(check_status))


def catalog_source(vault: Path, source_ref: str) -> dict[str, Any] | None:
    if not db_path(vault).is_file():
        return None
    work_id = _work_id(source_ref)
    with connect(vault) as conn:
        row = conn.execute(
            "SELECT * FROM catalog_sources WHERE work_id = ?",
            (work_id,),
        ).fetchone()
    return _source_row(row) if row is not None else None


def catalog_sources(vault: Path, *, checked_only: bool = True) -> list[dict[str, Any]]:
    if not db_path(vault).is_file():
        return []
    with connect(vault) as conn:
        if checked_only:
            rows = conn.execute(
                """
                SELECT *
                FROM catalog_sources
                WHERE check_status = 'checked'
                ORDER BY work_id
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT *
                FROM catalog_sources
                ORDER BY work_id
                """
            ).fetchall()
    return [_source_row(row) for row in rows]


def start_enrichment_run(
    vault: Path,
    *,
    run_id: str,
    work_id: str,
    required_provider_policy: dict[str, Any],
    request_id: str = "",
) -> None:
    with connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO enrichment_runs(
                run_id,
                work_id,
                enrichment_status,
                required_provider_policy_json,
                started_at,
                request_id
            )
            VALUES (?, ?, 'pending', ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                enrichment_status = 'pending',
                required_provider_policy_json = excluded.required_provider_policy_json,
                started_at = excluded.started_at,
                finished_at = NULL,
                request_id = excluded.request_id
            """,
            (run_id, _work_id(work_id), _json(required_provider_policy), now_iso(), request_id),
        )


def finish_enrichment_run(vault: Path, run_id: str, status: str) -> None:
    with connect(vault) as conn:
        conn.execute(
            """
            UPDATE enrichment_runs
            SET enrichment_status = ?, finished_at = ?
            WHERE run_id = ?
            """,
            (status, now_iso(), run_id),
        )


def store_provider_payload(
    vault: Path,
    *,
    run_id: str,
    provider: str,
    request_key: str,
    request_params_hash: str,
    status: str,
    raw_hash: str,
    raw_path: str,
    normalized: dict[str, Any],
    error: str = "",
    latency_ms: int = 0,
    retry_count: int = 0,
) -> None:
    with connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO provider_payloads(
                run_id,
                provider,
                request_key,
                request_params_hash,
                status,
                fetched_at,
                raw_hash,
                raw_path,
                normalized_json,
                error,
                latency_ms,
                retry_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                provider,
                request_key,
                request_params_hash,
                status,
                now_iso(),
                raw_hash,
                normalize_path(raw_path),
                _json(normalized),
                error,
                latency_ms,
                retry_count,
            ),
        )


def replace_field_provenance(
    vault: Path,
    work_id: str,
    rows: Iterable[dict[str, Any]],
) -> None:
    stable_work_id = _work_id(work_id)
    with connect(vault) as conn:
        conn.execute("DELETE FROM field_provenance WHERE work_id = ?", (stable_work_id,))
        for row in rows:
            conn.execute(
                """
                INSERT INTO field_provenance(
                    work_id,
                    field_path,
                    value_hash,
                    winning_provider,
                    evidence_payload_id,
                    alternatives_json,
                    confidence,
                    conflict_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    stable_work_id,
                    str(row["field_path"]),
                    str(row["value_hash"]),
                    str(row["winning_provider"]),
                    str(row.get("evidence_payload_id") or ""),
                    _json(row.get("alternatives") or []),
                    str(row.get("confidence") or "high"),
                    str(row.get("conflict_status") or "none"),
                ),
            )


def replace_external_ids(vault: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows = list(rows)
    owner_keys = {
        (str(row["owner_type"]), str(row["owner_id"]))
        for row in rows
        if row.get("owner_type") and row.get("owner_id")
    }
    with connect(vault) as conn:
        for owner_type, owner_id in owner_keys:
            conn.execute(
                "DELETE FROM external_ids WHERE owner_type = ? AND owner_id = ?",
                (owner_type, owner_id),
            )
        for row in rows:
            conn.execute(
                """
                INSERT INTO external_ids(
                    owner_type,
                    owner_id,
                    namespace,
                    value,
                    source_provider,
                    confidence,
                    verified_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(row["owner_type"]),
                    str(row["owner_id"]),
                    str(row["namespace"]),
                    str(row["value"]),
                    str(row.get("source_provider") or ""),
                    str(row.get("confidence") or "high"),
                    now_iso(),
                ),
            )


def replace_work_graph_edges(vault: Path, work_id: str, rows: Iterable[dict[str, Any]]) -> None:
    stable_work_id = _work_id(work_id)
    with connect(vault) as conn:
        conn.execute("DELETE FROM work_graph_edges WHERE work_id = ?", (stable_work_id,))
        for row in rows:
            conn.execute(
                """
                INSERT INTO work_graph_edges(
                    work_id,
                    relation_type,
                    target_id,
                    target_title,
                    target_doi,
                    source_provider,
                    raw_json,
                    discovered_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    stable_work_id,
                    str(row["relation_type"]),
                    str(row["target_id"]),
                    str(row.get("target_title") or ""),
                    str(row.get("target_doi") or ""),
                    str(row.get("source_provider") or ""),
                    _json(row.get("raw") or {}),
                    now_iso(),
                ),
            )


def replace_work_aspects(vault: Path, source_ref: str, rows: Iterable[dict[str, Any]]) -> None:
    work_id = _work_id(source_ref)
    with connect(vault) as conn:
        conn.execute("DELETE FROM work_aspects WHERE work_id = ?", (work_id,))
        for row in rows:
            aspect_text = str(row.get("aspect_text") or "").strip()
            if not aspect_text:
                continue
            aspect_type = _work_aspect_type(str(row.get("aspect_type") or ""))
            conn.execute(
                """
                INSERT INTO work_aspects(
                    work_id,
                    aspect_type,
                    aspect_text,
                    anchor_text,
                    check_status,
                    source_provider,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    work_id,
                    aspect_type,
                    aspect_text,
                    str(row.get("anchor_text") or "").strip(),
                    _check_status(str(row.get("check_status") or "unchecked")),
                    str(row.get("source_provider") or "deterministic"),
                    now_iso(),
                ),
            )


def replace_indexed_passages(
    vault: Path,
    rows: Iterable[dict[str, Any]],
    *,
    paths: Iterable[str] | None = None,
) -> dict[str, int]:
    rows = [dict(row) for row in rows]
    target_paths = {normalize_path(path) for path in paths or []}
    now = now_iso()
    with connect(vault) as conn:
        if target_paths:
            for path in sorted(target_paths):
                conn.execute("DELETE FROM passages WHERE path = ?", (path,))
                conn.execute("DELETE FROM file_index_state WHERE path = ?", (path,))
        else:
            conn.execute("DELETE FROM passages")
            conn.execute("DELETE FROM file_index_state")
        for row in rows:
            text = str(row["text"])
            path = normalize_path(str(row["path"]))
            check_status = _check_status(str(row.get("check_status") or "unchecked"))
            text_sha256 = str(row.get("text_sha256") or _sha256_text(text))
            passage_id = str(row.get("passage_id") or _passage_id(path, text_sha256))
            vector = row.get("vector")
            conn.execute(
                """
                INSERT INTO passages(
                    passage_id,
                    origin,
                    concept_id,
                    work_id,
                    path,
                    anchor,
                    page,
                    byte_start,
                    byte_end,
                    text_sha256,
                    text,
                    check_status,
                    mode,
                    question_status,
                    source_mtime_ns,
                    indexed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    passage_id,
                    str(row.get("origin") or "file"),
                    normalize_path(str(row.get("concept_id") or path)),
                    str(row.get("work_id") or ""),
                    path,
                    str(row.get("anchor") or ""),
                    str(row.get("page") or ""),
                    int(row.get("byte_start") or 0),
                    int(row.get("byte_end") or len(text.encode())),
                    text_sha256,
                    text,
                    check_status,
                    str(row.get("mode") or ""),
                    str(row.get("question_status") or ""),
                    int(row.get("source_mtime_ns") or 0),
                    now,
                ),
            )
            if isinstance(vector, list) and vector:
                conn.execute(
                    """
                    INSERT INTO passage_vec(
                        passage_id,
                        text_sha256,
                        embedding_model_id,
                        vector_dim,
                        vector_json,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        passage_id,
                        text_sha256,
                        str(row.get("embedding_model_id") or "memoria-hash-test-v1"),
                        int(row.get("vector_dim") or len(vector)),
                        _json(vector),
                        now,
                    ),
                )
            conn.execute(
                """
                INSERT INTO file_index_state(
                    path,
                    source_mtime_ns,
                    source_sha256,
                    check_status,
                    indexed_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    source_mtime_ns = excluded.source_mtime_ns,
                    source_sha256 = excluded.source_sha256,
                    check_status = excluded.check_status,
                    indexed_at = excluded.indexed_at
                """,
                (
                    path,
                    int(row.get("source_mtime_ns") or 0),
                    text_sha256,
                    check_status,
                    now,
                ),
            )
    return {"inserted": len(rows), "paths": len({str(row["path"]) for row in rows})}


def indexed_passages(vault: Path, *, checked_only: bool = False) -> list[dict[str, Any]]:
    if not db_path(vault).is_file():
        return []
    with connect(vault) as conn:
        if checked_only:
            rows = conn.execute(
                """
                SELECT *
                FROM passages
                WHERE check_status = 'checked'
                ORDER BY path, passage_id
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT *
                FROM passages
                ORDER BY path, passage_id
                """
            ).fetchall()
    return [dict(row) for row in rows]


def file_index_states(vault: Path) -> dict[str, dict[str, Any]]:
    if not db_path(vault).is_file():
        return {}
    with connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT path, source_mtime_ns, source_sha256, check_status, indexed_at
            FROM file_index_state
            ORDER BY path
            """
        ).fetchall()
    return {str(row["path"]): dict(row) for row in rows}


def replace_concept_edges(
    vault: Path,
    rows: Iterable[dict[str, Any]],
    *,
    paths: Iterable[str] | None = None,
) -> dict[str, int]:
    """Reconcile the links mirror without changing PI-owned tension rows.

    Rows key by the v16 scoped triple ``(source_concept_id, relation_type,
    target_path)``, so the bare, rendered, ``./``, and ``/source.md`` catalog
    forms share one edge. Sources are resolved or ensured; targets are resolved
    but never created, and an unresolved target parks the edge as a pending row.
    ``paths=None`` is a full mirror pass; an empty scope is a no-op.
    """
    path_list = None if paths is None else list(paths)
    if path_list == []:
        return {"deleted": 0, "inserted": 0}
    target_paths = (
        None
        if path_list is None
        else {normalize_path(str(path)) for path in path_list if normalize_path(str(path))}
    )

    with connect(vault) as conn:
        catalog_ids = {
            str(row["work_id"]) for row in conn.execute("SELECT work_id FROM catalog_sources")
        }
        prepared = []
        for value in rows:
            row = dict(value)
            relation = _concept_edge_relation(str(row["relation_type"]))
            if relation == "tension":
                continue
            source_path = normalize_path(str(row.get("source_path") or ""))
            if target_paths is not None and source_path not in target_paths:
                continue
            source = _resolve_or_ensure_concept_conn(
                conn, normalize_path(str(row["source_concept_id"]))
            )
            target_path = _concept_edge_target_path(
                str(row.get("target_path") or row.get("target_concept_id") or ""), catalog_ids
            )
            prepared.append((row, source, relation, target_path, source_path))

        keep = {(source, relation, path) for _row, source, relation, path, _ in prepared}
        existing = conn.execute(
            """
            SELECT source_concept_id, relation_type, target_path, source_path
            FROM concept_edges
            WHERE relation_type != 'tension'
            """
        ).fetchall()
        deleted = 0
        for stale in existing:
            key = (
                str(stale["source_concept_id"]),
                str(stale["relation_type"]),
                str(stale["target_path"]),
            )
            if key in keep:
                continue
            if target_paths is not None and str(stale["source_path"]) not in target_paths:
                continue
            conn.execute(
                """
                DELETE FROM concept_edges
                WHERE source_concept_id = ? AND relation_type = ? AND target_path = ?
                """,
                key,
            )
            deleted += 1
        for row, source, relation, target_path, source_path in prepared:
            target_id = _lookup_concept_id(conn, target_path)
            conn.execute(
                """
                INSERT INTO concept_edges(
                    edge_id,
                    source_concept_id,
                    relation_type,
                    target_concept_id,
                    target_path,
                    attributes_json,
                    check_status,
                    source_path,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_concept_id, relation_type, target_path)
                DO UPDATE SET
                    edge_id = CASE
                        WHEN excluded.edge_id != '' THEN excluded.edge_id
                        ELSE concept_edges.edge_id
                    END,
                    target_concept_id = COALESCE(
                        excluded.target_concept_id, concept_edges.target_concept_id
                    ),
                    check_status = excluded.check_status,
                    source_path = excluded.source_path,
                    updated_at = excluded.updated_at
                """,
                (
                    concept_edge_id(source, relation, target_id) if target_id else "",
                    source,
                    relation,
                    target_id,
                    target_path,
                    str(row.get("attributes_json") or "{}"),
                    _check_status(str(row.get("check_status") or "unchecked")),
                    source_path,
                    now_iso(),
                ),
            )
        # After the loop, not before: this pass's own inserts can mint the Concept a
        # retained row has been waiting for. Running it first is not a corruption --
        # those rows just wait one more reindex -- which is why nothing pins the
        # ordering.
        _resolve_pending_concept_edges_conn(conn)
    return {"deleted": int(deleted), "inserted": len(prepared)}


def _resolve_pending_concept_edges_conn(conn: sqlite3.Connection) -> None:
    """Settle every retained edge row the upsert loop above never reached (NODES §1.6).

    A forward link to a note that does not exist yet is legal Zettelkasten practice,
    so the mirror parks it as a pending row instead of dropping it. The loop
    re-resolves only the rows it (re)inserts, which leaves two kinds behind: a
    PI-owned ``tension`` row, which the loop skips by design and no reindex ever
    rewrites, and any pending row a scoped pass spared. Both have to resolve at the
    reindex where their target materializes, or a dangling link stays dangling for
    the life of the vault.

    The same pass recomputes a blank ``edge_id``, which is what an identity re-key
    leaves behind (``_rekey_path_keyed_concept_conn``). Resolution and recomputation
    are one pass because they answer one question — does this row's stored identity
    still agree with the id space — and write the answer the same way.
    ``_lookup_concept_id`` is the module's one resolver, so a catalog reference
    resolves here exactly as it does at insert.

    **This pass is graph-wide and ignores the caller's ``paths`` scope.** That is
    deliberate — the rows it settles are exactly the ones a scoped pass spared, so
    scoping it would re-create the leak — but it does mean a scoped
    ``replace_concept_edges`` can write rows outside the requested scope, while an
    empty scope still short-circuits before reaching here. ``indexing.py`` is the
    only caller today and passes ``paths=None``; a future scoped caller has to
    accept that asymmetry or move the pass out of this function.
    """
    unsettled = conn.execute(
        "SELECT source_concept_id, relation_type, target_path, target_concept_id"
        " FROM concept_edges WHERE target_concept_id IS NULL OR edge_id = ''"
    ).fetchall()
    for row in unsettled:
        target_path = str(row["target_path"])
        target_id = row["target_concept_id"] or _lookup_concept_id(conn, target_path)
        if not target_id:
            continue
        source = str(row["source_concept_id"])
        relation = str(row["relation_type"])
        conn.execute(
            """
            UPDATE concept_edges
            SET target_concept_id = ?, edge_id = ?
            WHERE source_concept_id = ? AND relation_type = ? AND target_path = ?
            """,
            (
                target_id,
                concept_edge_id(source, relation, str(target_id)),
                source,
                relation,
                target_path,
            ),
        )


def _resolve_or_ensure_concept_conn(conn: sqlite3.Connection, ref: str) -> str:
    """Return an edge endpoint's parent id, minting a registry-shaped one if absent."""
    resolved = _lookup_concept_id(conn, ref)
    if resolved is not None:
        return resolved
    concept_type, store, path = _concept_parent_shape(ref)
    return ensure_concept_parent_conn(conn, ref, concept_type=concept_type, store=store, path=path)


def _concept_edge_target_path(raw_target: str, catalog_ids: set[str]) -> str:
    """Return the v16 edge path key: catalog references collapse to one rendering."""
    rel = normalize_path(raw_target)
    rendered = rel.removeprefix("catalog/sources/").removesuffix("/source.md")
    return f"catalog/sources/{rendered}" if rendered in catalog_ids else rel


def insert_concept_edge(
    vault: Path,
    *,
    source: str,
    relation_type: str,
    target: str,
    attributes: dict[str, Any] | None = None,
    context: OperationContext,
) -> dict[str, Any]:
    """Upsert one PI-confirmed concept edge without touching any other row.

    The single-row seam for edges no frontmatter mirrors — a confirmed
    ``tension``, or warrant text hung on a grounding edge. On conflict the given
    attributes merge over the stored ``attributes_json``; ``None`` leaves the
    stored attributes untouched, and the row's ``check_status``/``source_path``
    stay as written so hanging an attribute on a mirrored edge never takes that
    edge out of the demotion triggers' scope.

    Both endpoints resolve through the exact functions ``replace_concept_edges``
    uses, because this is the second writer into one keyspace. ``source`` may be
    spelled as a path or as an identity and resolves to one ``concepts`` key,
    minting nothing: an unmirrored source is a foreign-key refusal, not a new
    Concept. ``target`` is path space, and its durable key **must** come from
    ``_concept_edge_target_path`` rather than a bare ``normalize_path`` — that is
    the function folding the bare ``work_id``, the rendered
    ``catalog/sources/<work_id>``, the ``./`` form and the ``/source.md`` form of
    one catalog work onto one ``target_path``. Admitted as distinct PK triples
    those spellings still resolve to one ``target_concept_id``, so they mint one
    deterministic ``edge_id`` twice and violate the UNIQUE
    ``idx_concept_edges_edge_id`` — inside ``replace_concept_edges``' single
    transaction, which rolls the whole mirror pass back and takes out `memoria
    index` vault-wide instead of the one bad row.
    """
    from memoria_vault.runtime.trusted_writer import validate_operation_context

    validate_operation_context(vault, context)
    relation = _concept_edge_relation(str(relation_type))
    with connect(vault) as conn:
        catalog_ids = {
            str(row["work_id"]) for row in conn.execute("SELECT work_id FROM catalog_sources")
        }
        source_concept = resolve_concept_id(conn, str(source))
        target_path = _concept_edge_target_path(str(target), catalog_ids)
        target_id = _lookup_concept_id(conn, target_path)
        if not source_concept or not target_path or source_concept == (target_id or target_path):
            raise ValueError("concept edge requires two distinct endpoints")
        stored = conn.execute(
            """
            SELECT edge_id, target_concept_id, attributes_json FROM concept_edges
            WHERE source_concept_id = ? AND relation_type = ? AND target_path = ?
            """,
            (source_concept, relation, target_path),
        ).fetchone()
        if stored is not None and target_id is None:
            # A settled row whose spelling stopped resolving — its target moved out
            # of band, so `concepts.path` left this `target_path` behind — keeps the
            # identity it already holds, the same call the mirror pass's COALESCE
            # makes. Re-deriving NULL here would un-resolve a live edge and blank an
            # edge_id every caller was promised is stable.
            target_id = stored["target_concept_id"]
        merged = {
            **(json.loads(stored["attributes_json"] or "{}") if stored is not None else {}),
            **(attributes or {}),
        }
        edge_id = concept_edge_id(source_concept, relation, str(target_id)) if target_id else ""
        conn.execute(
            """
            INSERT INTO concept_edges(
                edge_id,
                source_concept_id,
                relation_type,
                target_concept_id,
                target_path,
                attributes_json,
                check_status,
                source_path,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 'checked', '', ?)
            ON CONFLICT(source_concept_id, relation_type, target_path) DO UPDATE SET
                edge_id = excluded.edge_id,
                target_concept_id = excluded.target_concept_id,
                attributes_json = excluded.attributes_json,
                updated_at = excluded.updated_at
            """,
            (
                edge_id,
                source_concept,
                relation,
                target_id,
                target_path,
                json.dumps(merged, sort_keys=True),
                now_iso(),
            ),
        )
    return {"edge_id": edge_id, "created": stored is None, "attributes": merged}


def concept_edges(vault: Path, *, checked_only: bool = True) -> list[dict[str, Any]]:
    if not db_path(vault).is_file():
        return []
    with connect(vault) as conn:
        if checked_only:
            rows = conn.execute(
                """
                SELECT edge_id, source_concept_id, relation_type, target_concept_id,
                       target_path, attributes_json, check_status, source_path
                FROM concept_edges
                WHERE check_status = 'checked'
                ORDER BY source_concept_id, relation_type, target_path
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT edge_id, source_concept_id, relation_type, target_concept_id,
                       target_path, attributes_json, check_status, source_path
                FROM concept_edges
                ORDER BY source_concept_id, relation_type, target_path
                """
            ).fetchall()
    return [dict(row) for row in rows]


def upsert_code_artifact(
    vault: Path,
    *,
    artifact_id: str,
    project_path: str,
    record_path: str,
    source_dir: str,
    output_dir: str,
    purpose: str,
    approved_command: Iterable[str],
    declared_inputs: Iterable[str] = (),
    declared_outputs: Iterable[str] = (),
    dependency_notes: str = "",
    status: str = "draft",
) -> dict[str, Any]:
    now = now_iso()
    artifact = safe_filename(artifact_id).strip("._-")
    if not artifact:
        raise ValueError("artifact_id is required")
    with connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO code_artifacts(
                artifact_id,
                project_path,
                record_path,
                source_dir,
                output_dir,
                purpose,
                approved_command_json,
                declared_inputs_json,
                declared_outputs_json,
                dependency_notes,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(artifact_id) DO UPDATE SET
                project_path = excluded.project_path,
                record_path = excluded.record_path,
                source_dir = excluded.source_dir,
                output_dir = excluded.output_dir,
                purpose = excluded.purpose,
                approved_command_json = excluded.approved_command_json,
                declared_inputs_json = excluded.declared_inputs_json,
                declared_outputs_json = excluded.declared_outputs_json,
                dependency_notes = excluded.dependency_notes,
                status = excluded.status,
                updated_at = excluded.updated_at
            """,
            (
                artifact,
                normalize_path(project_path),
                normalize_path(record_path),
                normalize_path(source_dir),
                normalize_path(output_dir),
                _code_purpose(purpose),
                _json([str(part) for part in approved_command]),
                _json([normalize_path(path) for path in declared_inputs]),
                _json([normalize_path(path) for path in declared_outputs]),
                dependency_notes,
                _code_artifact_status(status),
                now,
                now,
            ),
        )
    artifact_row = code_artifact(vault, artifact)
    if artifact_row is None:
        raise RuntimeError(f"code artifact was not stored: {artifact}")
    return artifact_row


def code_artifact(vault: Path, artifact_id: str) -> dict[str, Any] | None:
    if not db_path(vault).is_file():
        return None
    artifact = safe_filename(artifact_id).strip("._-")
    with connect(vault) as conn:
        row = conn.execute(
            """
            SELECT *
            FROM code_artifacts
            WHERE artifact_id = ?
            """,
            (artifact,),
        ).fetchone()
    return None if row is None else _code_artifact_row(row)


def record_code_run(
    vault: Path,
    *,
    run_id: str,
    artifact_id: str,
    command: Iterable[str],
    cwd: str,
    sanitized_env: Iterable[str] = (),
    input_hashes: dict[str, str] | None = None,
    output_hashes: dict[str, str] | None = None,
    stdout_sha256: str = "",
    stderr_sha256: str = "",
    stdout_path: str = "",
    stderr_path: str = "",
    exit_status: int | None = None,
    timeout_result: str = "",
    sandbox_backend: str = "",
    sandbox_profile_hash: str = "",
    run_state: str = "pending",
    started_at: str | None = None,
    ended_at: str | None = None,
) -> dict[str, Any]:
    run = safe_filename(run_id).strip("._-")
    if not run:
        raise ValueError("run_id is required")
    with connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO code_runs(
                run_id,
                artifact_id,
                command_json,
                cwd,
                sanitized_env_json,
                input_hashes_json,
                output_hashes_json,
                stdout_sha256,
                stderr_sha256,
                stdout_path,
                stderr_path,
                exit_status,
                timeout_result,
                sandbox_backend,
                sandbox_profile_hash,
                state,
                started_at,
                ended_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                command_json = excluded.command_json,
                cwd = excluded.cwd,
                sanitized_env_json = excluded.sanitized_env_json,
                input_hashes_json = excluded.input_hashes_json,
                output_hashes_json = excluded.output_hashes_json,
                stdout_sha256 = excluded.stdout_sha256,
                stderr_sha256 = excluded.stderr_sha256,
                stdout_path = excluded.stdout_path,
                stderr_path = excluded.stderr_path,
                exit_status = excluded.exit_status,
                timeout_result = excluded.timeout_result,
                sandbox_backend = excluded.sandbox_backend,
                sandbox_profile_hash = excluded.sandbox_profile_hash,
                state = excluded.state,
                ended_at = excluded.ended_at
            """,
            (
                run,
                safe_filename(artifact_id).strip("._-"),
                _json([str(part) for part in command]),
                normalize_path(cwd),
                _json([str(name) for name in sanitized_env]),
                _json(input_hashes or {}),
                _json(output_hashes or {}),
                stdout_sha256,
                stderr_sha256,
                normalize_path(stdout_path) if stdout_path else "",
                normalize_path(stderr_path) if stderr_path else "",
                exit_status,
                timeout_result,
                sandbox_backend,
                sandbox_profile_hash,
                _code_run_state(run_state),
                started_at or now_iso(),
                ended_at,
            ),
        )
    run_row = code_run(vault, run)
    if run_row is None:
        raise RuntimeError(f"code run was not stored: {run}")
    return run_row


def code_run(vault: Path, run_id: str) -> dict[str, Any] | None:
    if not db_path(vault).is_file():
        return None
    run = safe_filename(run_id).strip("._-")
    with connect(vault) as conn:
        row = conn.execute(
            """
            SELECT *
            FROM code_runs
            WHERE run_id = ?
            """,
            (run,),
        ).fetchone()
    return None if row is None else _code_run_row(row)


def replace_evidence_sets(vault: Path, rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    with connect(vault) as conn:
        return _replace_evidence_sets_conn(conn, rows)


def _replace_evidence_sets_conn(
    conn: sqlite3.Connection, rows: Iterable[dict[str, Any]]
) -> dict[str, Any]:
    """Replace active evidence sets using an existing transaction."""
    rows = list(rows)
    minted: list[dict[str, Any]] = []
    for row in rows:
        if not bool(row.get("bind", True)):
            continue
        cursor = conn.execute(
            """
            INSERT INTO evidence_bindings(id, block_text_sha256)
            VALUES (?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (str(row["id"]), row.get("block_text_sha256")),
        )
        if cursor.rowcount:
            minted.append(
                {
                    "evidence_id": str(row["id"]),
                    "block_ref": normalize_path(str(row["block_ref"])),
                    "block_text_sha256": row.get("block_text_sha256"),
                }
            )
    existing_bindings = {
        row["id"]: row["block_text_sha256"]
        for row in conn.execute("SELECT id, block_text_sha256 FROM evidence_bindings")
    }
    deleted = conn.execute("DELETE FROM evidence_sets").rowcount
    for row in rows:
        evidence_id = str(row["id"])
        items = [str(item) for item in row.get("items", [])]
        bind = bool(row.get("bind", True))
        block_text_sha256 = (
            existing_bindings[evidence_id]
            if bind and evidence_id in existing_bindings
            else row.get("block_text_sha256")
            if bind
            else None
        )
        conn.execute(
            """
            INSERT INTO evidence_sets(
                id,
                block_ref,
                items_json,
                type,
                state,
                review_required,
                run_id,
                block_text_sha256
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence_id,
                normalize_path(str(row["block_ref"])),
                _json(items),
                str(row["type"]),
                str(row["state"]),
                1 if bool(row.get("review_required")) else 0,
                str(row.get("run_id") or ""),
                block_text_sha256,
            ),
        )
    result: dict[str, Any] = {"deleted": int(deleted), "inserted": len(rows)}
    if minted:
        result["minted"] = minted
    return result


def evidence_sets(vault: Path) -> list[dict[str, Any]]:
    if not db_path(vault).is_file():
        return []
    with connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT id, block_ref, items_json, type, state, review_required, run_id,
                   block_text_sha256
            FROM evidence_sets
            ORDER BY block_ref, id
            """
        ).fetchall()
    return [_evidence_set_row(row) for row in rows]


def rebuild_evidence_sets_from_markers(vault: Path, *, run_id: str = "") -> dict[str, Any]:
    vault = Path(vault)
    marker_rows, duplicate_ids = _evidence_marker_rows(vault, run_id=run_id)
    result = replace_evidence_sets(vault, marker_rows)
    if duplicate_ids:
        result["duplicate_ids"] = duplicate_ids
    return result


def rebuild_evidence_bindings_from_journal(vault: Path) -> dict[str, int]:
    """Replay verified first-time evidence mints into the immutable bindings ledger."""
    vault = Path(vault)
    with workspace_lock(vault):
        verification = verify_journal_chain(vault)
        if not verification["ok"]:
            raise ValueError(
                "cannot rebuild evidence bindings: journal chain is invalid: "
                f"{verification['error']}"
            )
        mints = [
            _evidence_mint_event_binding(event)
            for event in read_event_log(vault, event_types=("evidence-minted",))
        ]
        replayed = 0
        inserted = 0
        with connect(vault) as conn:
            conn.execute("BEGIN IMMEDIATE")
            for evidence_id, block_text_sha256 in mints:
                replayed += 1
                cursor = conn.execute(
                    """
                    INSERT INTO evidence_bindings(id, block_text_sha256)
                    VALUES (?, ?)
                    ON CONFLICT(id) DO NOTHING
                    """,
                    (evidence_id, block_text_sha256),
                )
                inserted += cursor.rowcount
    return {"replayed": replayed, "inserted": inserted}


def _evidence_mint_event_binding(event: Mapping[str, Any]) -> tuple[str, str | None]:
    """Validate the canonical payload used to restore one immutable binding."""
    evidence_id = event.get("evidence_id")
    block_ref = event.get("block_ref")
    block_text_sha256 = event.get("block_text_sha256")
    actor = event.get("actor")
    valid_provenance = (
        isinstance(actor, str)
        and actor in ACTORS
        and isinstance(event.get("request_provenance"), dict)
        and all(
            isinstance(event.get(field), str) and event[field].strip()
            for field in ("run_id", "request_id", "operation", "machine", "timestamp")
        )
    )
    if (
        event.get("event") != "evidence-minted"
        or not isinstance(evidence_id, str)
        or re.fullmatch(r"ev-[0-9a-f]{8}", evidence_id) is None
        or not isinstance(block_ref, str)
        or not valid_provenance
        or (
            block_text_sha256 is not None
            and (
                not isinstance(block_text_sha256, str)
                or re.fullmatch(r"sha256:[0-9a-f]{64}", block_text_sha256) is None
            )
        )
    ):
        raise ValueError("invalid evidence-minted journal event")
    try:
        rel, separator, _anchor = block_ref.partition("#^")
        canonical_block_ref = _evidence_block_ref(rel, evidence_id)
    except ValueError as exc:
        raise ValueError("invalid evidence-minted journal event") from exc
    if not separator or not rel.strip() or block_ref != canonical_block_ref:
        raise ValueError("invalid evidence-minted journal event")
    return evidence_id, block_text_sha256


def work_aspects(vault: Path, source_ref: str) -> list[dict[str, Any]]:
    if not db_path(vault).is_file():
        return []
    work_id = _work_id(source_ref)
    with connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT work_id, aspect_type, aspect_text, anchor_text, check_status,
                   source_provider, updated_at
            FROM work_aspects
            WHERE work_id = ?
            ORDER BY aspect_type
            """,
            (work_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def compact_citation(vault: Path, source_ref: str) -> dict[str, Any]:
    if not db_path(vault).is_file():
        return {}
    work_id = _work_id(source_ref)
    with connect(vault) as conn:
        row = conn.execute(
            "SELECT * FROM catalog_sources WHERE work_id = ?",
            (work_id,),
        ).fetchone()
    if row is None:
        return {}
    source = _source_row(row)
    csl = source.get("csl_json") if isinstance(source.get("csl_json"), dict) else {}
    identifiers = source.get("identifiers") if isinstance(source.get("identifiers"), dict) else {}
    citation: dict[str, Any] = {
        "work_id": f"catalog/sources/{work_id}",
        "title": source["title"],
        "authors": _csl_authors(csl),
        "issued": _csl_issued(csl),
    }
    if doi := str(identifiers.get("doi") or csl.get("DOI") or "").strip():
        citation["doi"] = doi
    elif url := str(source.get("resource") or csl.get("URL") or "").strip():
        citation["url"] = url
    else:
        citation["citekey"] = str(source.get("citekey") or work_id)
    return citation


def _init(conn: sqlite3.Connection) -> None:
    current = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if current not in {0, SCHEMA_VERSION}:
        raise RuntimeError(f"unsupported Memoria DB schema version: {current}")
    conn.executescript(_schema_sql())
    applied = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if applied != SCHEMA_VERSION:
        raise RuntimeError(f"Memoria DB schema initialization failed: {applied}")


def _set_request_state(vault: Path, request_id: str, status: str, job: dict[str, Any]) -> None:
    if status not in REQUEST_STATUSES:
        raise ValueError(f"unknown request status: {status}")
    request_id = safe_filename(request_id)
    now = now_iso()
    with connect(vault) as conn:
        conn.execute(
            """
            UPDATE operation_requests
            SET status = ?,
                started_at = COALESCE(started_at, ?),
                completed_at = CASE
                    WHEN ? IN ('done', 'failed', 'cancelled') THEN ?
                    ELSE completed_at
                END,
                job_json = ?,
                error = ?
            WHERE request_id = ?
            """,
            (
                status,
                now,
                status,
                now,
                _json(job),
                str(job.get("error") or ""),
                request_id,
            ),
        )


def _source_row(row: sqlite3.Row) -> dict[str, Any]:
    csl_json = json.loads(row["csl_json"] or "{}")
    return {
        "work_id": row["work_id"],
        "concept_path": row["concept_path"],
        "doi": row["doi"],
        "title": row["title"],
        "description": row["description"],
        "resource": row["resource"],
        "item_type": row["item_type"],
        "identifiers": json.loads(row["identifiers_json"] or "{}"),
        "citekey": row["citekey"],
        "csl_json": csl_json,
        "provider_coverage": row["provider_coverage"],
        "text_status": row["text_status"],
        "check_status": row["check_status"],
        "normalized_text_sha256": row["content_hash"],
        "raw_text_sha256": row["raw_hash"],
        "content_path": row["content_path"],
        "raw_path": row["raw_path"],
    }


def _evidence_set_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "block_ref": row["block_ref"],
        "items": json.loads(row["items_json"] or "[]"),
        "type": row["type"],
        "state": row["state"],
        "review_required": bool(row["review_required"]),
        "run_id": row["run_id"],
        "block_text_sha256": row["block_text_sha256"],
    }


def _code_artifact_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "artifact_id": row["artifact_id"],
        "project_path": row["project_path"],
        "record_path": row["record_path"],
        "source_dir": row["source_dir"],
        "output_dir": row["output_dir"],
        "purpose": row["purpose"],
        "approved_command": json.loads(row["approved_command_json"] or "[]"),
        "declared_inputs": json.loads(row["declared_inputs_json"] or "[]"),
        "declared_outputs": json.loads(row["declared_outputs_json"] or "[]"),
        "dependency_notes": row["dependency_notes"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _code_run_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "run_id": row["run_id"],
        "artifact_id": row["artifact_id"],
        "command": json.loads(row["command_json"] or "[]"),
        "cwd": row["cwd"],
        "sanitized_env": json.loads(row["sanitized_env_json"] or "[]"),
        "input_hashes": json.loads(row["input_hashes_json"] or "{}"),
        "output_hashes": json.loads(row["output_hashes_json"] or "{}"),
        "stdout_sha256": row["stdout_sha256"],
        "stderr_sha256": row["stderr_sha256"],
        "stdout_path": row["stdout_path"],
        "stderr_path": row["stderr_path"],
        "exit_status": row["exit_status"],
        "timeout_result": row["timeout_result"],
        "sandbox_backend": row["sandbox_backend"],
        "sandbox_profile_hash": row["sandbox_profile_hash"],
        "state": row["state"],
        "started_at": row["started_at"],
        "ended_at": row["ended_at"],
    }


def _evidence_marker_rows(
    vault: Path,
    *,
    run_id: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    occurrences_by_id: dict[str, list[tuple[str, EvidenceMarker, bool]]] = {}
    bound_ids = _evidence_binding_ids(vault)
    for path in sorted(vault.rglob("*.md")):
        if _skip_evidence_scan_path(path.relative_to(vault)):
            continue
        rel = normalize_path(path.relative_to(vault).as_posix())
        text = path.read_text(encoding="utf-8")
        for marker, is_direct in _evidence_marker_occurrences_from_markdown(text):
            occurrences_by_id.setdefault(marker.evidence_id, []).append((rel, marker, is_direct))

    prior_block_refs = _evidence_set_block_refs(vault)
    selected: list[tuple[str, EvidenceMarker, bool, str | None]] = []
    duplicate_ids: list[str] = []
    for evidence_id in sorted(occurrences_by_id):
        occurrences = occurrences_by_id[evidence_id]
        direct = [occurrence for occurrence in occurrences if occurrence[2]]
        if not direct and evidence_id not in bound_ids:
            continue
        rel, marker, _is_direct = direct[0] if direct else occurrences[0]
        bind = bool(direct) and len(occurrences) == 1
        if len(occurrences) > 1:
            duplicate_ids.append(evidence_id)
        prior_block_ref = None if direct else prior_block_refs.get(evidence_id)
        selected.append((rel, marker, bind, prior_block_ref))

    items_by_id = {
        marker.evidence_id: tuple(marker.items) for _rel, marker, _bind, _prior in selected
    }
    source_spans = _source_span_pages(vault)
    states = _evidence_set_states(vault, items_by_id, source_spans=source_spans)
    rows = []
    for rel, marker, bind, prior_block_ref in selected:
        row = _derived_evidence_row(
            vault,
            rel,
            marker,
            state_value=states[marker.evidence_id],
            run_id=run_id,
        )
        if prior_block_ref is not None:
            row["block_ref"] = prior_block_ref
            row["block_text_sha256"] = _block_text_sha256(vault, prior_block_ref)
        row["bind"] = bind
        rows.append(row)
    return rows, duplicate_ids


def _skip_evidence_scan_path(rel: Path) -> bool:
    return any(part in {".git", ".memoria"} for part in rel.parts)


def _evidence_binding_ids(vault: Path) -> set[str]:
    if not db_path(vault).is_file():
        return set()
    with connect(vault) as conn:
        return {str(row["id"]) for row in conn.execute("SELECT id FROM evidence_bindings")}


def _evidence_set_block_refs(vault: Path) -> dict[str, str]:
    if not db_path(vault).is_file():
        return {}
    with connect(vault) as conn:
        return {
            str(row["id"]): str(row["block_ref"])
            for row in conn.execute("SELECT id, block_ref FROM evidence_sets")
        }


def _derived_evidence_row(
    vault: Path,
    rel: str,
    marker: EvidenceMarker,
    *,
    state_value: str,
    run_id: str,
) -> dict[str, Any]:
    items = list(marker.items)
    evidence_type = derive_evidence_type(items)
    block_ref = _evidence_block_ref(rel, marker.evidence_id)
    return {
        "id": marker.evidence_id,
        "block_ref": block_ref,
        "items": items,
        "type": evidence_type,
        "state": state_value,
        "review_required": evidence_type in {"implicit", "multi-hop"},
        "run_id": run_id,
        "block_text_sha256": _block_text_sha256(vault, block_ref),
    }


def derive_evidence_type(items: list[str]) -> str:
    """Derive the grounds type from a record's own items (spec §4, rules R1-R4)."""
    if not items:
        return "implicit"
    kinds = [evidence_ref_kind(item) for item in items]
    span_works = {
        parse_source_span_ref(item).work_id
        for item, kind in zip(items, kinds, strict=True)
        if kind == "source-span"
    }
    has_code = "code-grounds" in kinds
    if "evidence-set" in kinds or len(span_works) >= 2 or (has_code and span_works):
        return "multi-hop"
    if has_code:
        return "computed"
    return "single-span" if len(items) == 1 else "multi-span"


def _evidence_set_states(
    vault: Path,
    items_by_id: dict[str, tuple[str, ...]],
    *,
    source_spans: dict[str, set[str]],
) -> dict[str, str]:
    """Resolve completeness bottom-up over nested sets; cycles fail closed."""
    states: dict[str, str] = {}

    def visit(evidence_id: str, visiting: frozenset[str]) -> str:
        known = states.get(evidence_id)
        if known is not None:
            return known
        if evidence_id in visiting:
            return "evidence-incomplete"

        items = items_by_id.get(evidence_id) or ()
        complete = bool(items)
        visiting = visiting | {evidence_id}
        for item in items:
            kind = evidence_ref_kind(item)
            if kind == "code-grounds":
                resolved = _code_grounds_resolves(vault, item)
            elif kind == "evidence-set":
                resolved = item in items_by_id and visit(item, visiting) == "complete"
            else:
                source = parse_source_span_ref(item)
                resolved = source.page in source_spans.get(source.work_id, set())
            if not resolved:
                complete = False
                break

        states[evidence_id] = "complete" if complete else "evidence-incomplete"
        return states[evidence_id]

    for evidence_id in sorted(items_by_id):
        visit(evidence_id, frozenset())
    return states


def evidence_item_closure(
    rows_by_id: Mapping[str, Mapping[str, Any]], evidence_id: str
) -> list[tuple[str, tuple[str, ...]]]:
    """Return non-set evidence leaves with their nested evidence-set paths."""
    leaves: list[tuple[str, tuple[str, ...]]] = []

    def visit(current_id: str, path: tuple[str, ...], visiting: frozenset[str]) -> None:
        row = rows_by_id.get(current_id)
        if row is None:
            return
        for item in row.get("items", ()):
            if evidence_ref_kind(item) != "evidence-set":
                leaves.append((item, path))
                continue
            if item in visiting or item not in rows_by_id:
                continue
            visit(item, (*path, item), visiting | {item})

    visit(evidence_id, (), frozenset({evidence_id}))
    return leaves


def _code_grounds_resolves(vault: Path, item: str) -> bool:
    from memoria_vault.runtime.code.runs import code_grounds_complete

    grounds = parse_code_grounds_ref(item)
    return code_grounds_complete(
        vault,
        run_id=grounds.run_id,
        artifact_id=grounds.artifact_id,
        output_sha256=grounds.output_sha256,
    )


def _source_span_pages(vault: Path) -> dict[str, set[str]]:
    spans: dict[str, set[str]] = {}
    for source in catalog_sources(vault, checked_only=False):
        work_id = str(source["work_id"])
        content_path = Path(vault) / normalize_path(str(source.get("content_path") or ""))
        if not content_path.is_file():
            spans[work_id] = set()
            continue
        text = content_path.read_text(encoding="utf-8")
        spans[work_id] = set(re.findall(r"\^p\d{4,}", text))
    return {work_id: {page.removeprefix("^") for page in pages} for work_id, pages in spans.items()}


def _evidence_block_ref(rel: str, evidence_id: str) -> str:
    return f"{normalize_path(rel)}#^blk-{evidence_id.removeprefix('ev-')}"


def _block_text_sha256(vault: Path, block_ref: str) -> str | None:
    rel, separator, anchor = str(block_ref).partition("#^")
    if not separator or not rel or not anchor:
        return None
    try:
        path = Path(vault) / normalize_path(rel)
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError):
        return None
    return _block_text_sha256_from_text(text, block_ref)


def _block_canonical_text_from_text(text: str, block_ref: str) -> str | None:
    _rel, separator, anchor = str(block_ref).partition("#^")
    if not separator or not anchor:
        return None
    evidence_id = _evidence_id_for_block_anchor(anchor)
    if evidence_id is None:
        return None

    anchor_token = f"^{anchor}"
    anchor_pattern = rf"(?<!\S){re.escape(anchor_token)}(?=\s|$)"
    visible = _markdown_control_text(text)
    original_blocks = re.split(r"\n[ \t]*\n+", text)
    visible_blocks = re.split(r"\n[ \t]*\n+", visible)
    if len(original_blocks) != len(visible_blocks):
        return None

    blocks = [
        (original, control)
        for original, control in zip(original_blocks, visible_blocks, strict=True)
        if re.search(anchor_pattern, control)
    ]
    if len(blocks) != 1:
        return None

    block, control = blocks[0]
    matching_markers = [
        (match, marker)
        for match, marker in _direct_evidence_marker_matches(control)
        if marker.evidence_id == evidence_id
    ]
    if len(matching_markers) != 1:
        return None
    marker_match, _marker = matching_markers[0]
    anchor_matches = [
        match
        for match in re.finditer(anchor_pattern, control)
        if "\n" not in control[match.end() : marker_match.start("marker")]
        and not control[match.end() : marker_match.start("marker")].strip()
    ]
    if len(anchor_matches) != 1:
        return None

    canonical = block
    for start, end in sorted(
        (anchor_matches[0].span(), marker_match.span("marker")),
        reverse=True,
    ):
        canonical = canonical[:start] + canonical[end:]
    return canonical.strip()


def _block_text_sha256_from_text(text: str, block_ref: str) -> str | None:
    canonical = _block_canonical_text_from_text(text, block_ref)
    if canonical is None:
        return None
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _evidence_id_for_block_anchor(anchor: str) -> str | None:
    if not anchor.startswith("blk-"):
        return None
    evidence_id = f"ev-{anchor.removeprefix('blk-')}"
    return evidence_id if re.fullmatch(r"ev-[0-9a-f]{8}", evidence_id) else None


def _mask_markdown_code(value: str) -> str:
    return re.sub(r"\S", "x", value)


def _markdown_lines(text: str) -> list[str]:
    """Split only physical Markdown LF lines, preserving offsets and endings."""
    return [line for line in re.findall(r"[^\n]*(?:\n|$)", text) if line]


def _is_markdown_blank_line(line: str) -> bool:
    """Return whether a physical line is blank in Markdown's ASCII sense."""
    return not line.rstrip("\r\n").strip(" \t")


def _mask_html_comments(text: str) -> str:
    """Mask HTML comments without changing offsets or line boundaries."""
    masked: list[str] = []
    copied_until = 0
    cursor = 0
    while cursor < len(text):
        start = text.find("<!--", cursor)
        if start < 0:
            break
        end = text.find("-->", start + 4)
        end = len(text) if end < 0 else end + 3
        masked.append(text[copied_until:start])
        masked.append(_mask_markdown_code(text[start:end]))
        copied_until = end
        cursor = end
    masked.append(text[copied_until:])
    return "".join(masked)


def _html_tag_at(text: str, start: int) -> tuple[str, bool, int] | None:
    """Return an HTML tag's name, shape, and end offset when one starts at *start*."""
    index = start + 1
    closing = index < len(text) and text[index] == "/"
    if closing:
        index += 1
    if index >= len(text) or text[index].isspace() or text[index] in "/!?><":
        return None
    name_start = index
    while index < len(text) and not text[index].isspace() and text[index] not in "/><":
        index += 1
    name = text[name_start:index].lower()
    quote = ""
    while index < len(text):
        character = text[index]
        if quote:
            if character == quote:
                quote = ""
        elif character in {'"', "'"}:
            quote = character
        elif character == "<":
            return None
        elif character == ">":
            return name, closing, index + 1
        index += 1
    return None


def _has_raw_html_element(text: str) -> bool:
    """Return whether *text* contains an unescaped raw HTML element."""
    cursor = 0
    while cursor < len(text):
        start = text.find("<", cursor)
        if start < 0:
            return False
        if _preceding_backslash_count(text, start) % 2:
            cursor = start + 1
            continue
        if text.startswith("</", start):
            return True
        tag = _html_tag_at(text, start)
        if tag is not None:
            return True
        cursor = start + 1
    return False


def _mask_html_declarations(text: str) -> str:
    """Mask processing instructions and declarations without moving offsets."""
    masked: list[str] = []
    copied_until = 0
    cursor = 0
    while cursor < len(text):
        processing_start = text.find("<?", cursor)
        declaration_start = text.find("<!", cursor)
        starts = [start for start in (processing_start, declaration_start) if start >= 0]
        if not starts:
            break
        start = min(starts)
        if start == declaration_start and text.startswith("<!--", start):
            cursor = start + 4
            continue
        if text.startswith("<![CDATA[", start):
            end = text.find("]]>", start + len("<![CDATA["))
            end = len(text) if end < 0 else end + 3
        elif start == processing_start:
            end = text.find("?>", start + 2)
            end = len(text) if end < 0 else end + 2
        else:
            end = text.find(">", start + 2)
            end = len(text) if end < 0 else end + 1
        masked.append(text[copied_until:start])
        masked.append(_mask_markdown_code(text[start:end]))
        copied_until = end
        cursor = end
    masked.append(text[copied_until:])
    return "".join(masked)


def _yaml_frontmatter_bounds(text: str) -> tuple[int, int, int] | None:
    """Return the body and closing offsets for closed initial YAML frontmatter."""
    opening = re.match(r"\A\ufeff?(?:[ \t]*\r?\n)*---[ \t]*(?:\r?\n)", text)
    if opening is None:
        return None
    closing = re.search(r"(?m)^(?:---|\.\.\.)[ \t]*(?:\r?\n|$)", text[opening.end() :])
    if closing is None:
        return None
    body_end = opening.end() + closing.start()
    end = opening.end() + closing.end()
    return opening.end(), body_end, end


def _mask_yaml_frontmatter(text: str) -> str:
    """Mask a closed YAML frontmatter block at the beginning of a Markdown file."""
    bounds = _yaml_frontmatter_bounds(text)
    if bounds is None:
        return text
    _body_start, _body_end, end = bounds
    return _mask_markdown_code(text[:end]) + text[end:]


def _mask_yaml_mapping_frontmatter(text: str) -> str | None:
    """Mask initial YAML mappings, or return ``None`` when they fail closed."""
    bounds = _yaml_frontmatter_bounds(text)
    if bounds is None:
        return text
    body_start, body_end, end = bounds
    body = text[body_start:body_end]
    if any(
        len(line) - len(line.lstrip(" \t")) > _MAX_YAML_FRONTMATTER_INDENT
        for line in _markdown_lines(body)
    ):
        return None
    try:
        frontmatter = yaml.safe_load(body)
    except RecursionError:
        return None
    except yaml.YAMLError:
        return text
    if not isinstance(frontmatter, dict):
        return text
    return _mask_markdown_code(text[:end]) + text[end:]


def _has_mmd_title_field(text: str) -> bool:
    """Return whether an initial mmd_title_block field could hide a control."""
    return re.match(r"\A\ufeff?[ \t]*[\w-][\w \t-]*:", text) is not None


def _has_abbreviation_syntax(text: str) -> bool:
    """Return whether an abbreviation definition could hide a control."""
    return re.search(r"(?m)^\*\[", text) is not None


def _mask_markdown_containers(text: str) -> str:
    """Mask container blocks so only top-level prose can establish a binding."""
    masked: list[str] = []
    in_container = False
    for line in _markdown_lines(text):
        body = line.rstrip("\r\n")
        if _is_markdown_blank_line(line):
            in_container = False
            masked.append(line)
        elif in_container or _MARKDOWN_CONTAINER_RE.match(body):
            in_container = True
            masked.append(_mask_markdown_code(line))
        else:
            masked.append(line)
    return "".join(masked)


def _mask_definition_terms(text: str) -> str:
    """Mask a definition-list term when its marker line follows it."""
    lines = _markdown_lines(text)
    for index, line in enumerate(lines):
        body = line.rstrip("\r\n")
        if not index or not re.match(r"^[ ]{0,3}[:~][ \t]+", body):
            continue
        term_index = index - 1
        if _is_markdown_blank_line(lines[term_index]):
            term_index -= 1
        if term_index >= 0 and not _is_markdown_blank_line(lines[term_index]):
            lines[term_index] = _mask_markdown_code(lines[term_index])
    return "".join(lines)


def _mask_markdown_headings(text: str) -> str:
    """Mask ATX and Setext headings, which are not direct prose claims."""
    lines = _markdown_lines(text)
    for index, line in enumerate(lines):
        body = line.rstrip("\r\n")
        if heading := re.match(r"^[ ]{0,3}#{1,6}(?:[ \t]+|$)", body):
            lines[index] = line[: heading.end()] + _mask_markdown_code(line[heading.end() :])
        if index and re.match(r"^[ ]{0,3}(?:=+|-+)[ \t]*$", body):
            if not _is_markdown_blank_line(lines[index - 1]):
                lines[index - 1] = _mask_markdown_code(lines[index - 1])
    return "".join(lines)


def _mask_markdown_ranges(text: str, ranges: list[tuple[int, int]]) -> str:
    """Mask sorted or overlapping ranges without changing text offsets."""
    if not ranges:
        return text
    masked: list[str] = []
    copied_until = 0
    for start, end in sorted(ranges):
        if end <= copied_until:
            continue
        start = max(start, copied_until)
        masked.append(text[copied_until:start])
        masked.append(_mask_markdown_code(text[start:end]))
        copied_until = end
    masked.append(text[copied_until:])
    return "".join(masked)


def _mask_multiline_delimited_constructs(text: str, opener: str, closer: str) -> str:
    """Mask multiline balanced constructs with one delimiter pass."""
    starts: list[int] = []
    ranges: list[tuple[int, int]] = []
    last_line_break = -1
    index = 0
    while index < len(text):
        character = text[index]
        if character == "\\":
            index += 2
            continue
        if character in "\r\n":
            last_line_break = index
        elif character == opener:
            starts.append(index)
        elif character == closer and starts:
            start = starts.pop()
            if last_line_break > start:
                ranges.append((start, index + 1))
        index += 1
    if starts and last_line_break > starts[0]:
        ranges.append((starts[0], len(text)))
    return _mask_markdown_ranges(text, ranges)


def _mask_multiline_bracket_constructs(text: str) -> str:
    """Mask multiline Markdown inline constructs before accepting controls."""
    return _mask_multiline_delimited_constructs(text, "[", "]")


def _mask_multiline_parenthesized_constructs(text: str) -> str:
    """Mask multiline Markdown destinations and titles before accepting controls."""
    return _mask_multiline_delimited_constructs(text, "(", ")")


def _reference_definition_header_end(text: str, start: int) -> int | None:
    """Return the end of a reference-definition header beginning at *start*."""
    index = start
    while index < len(text) and index - start < 3 and text[index] == " ":
        index += 1
    if index >= len(text) or text[index] != "[":
        return None
    index += 1
    while index < len(text):
        character = text[index]
        if character == "\\":
            index += 2
            continue
        if character in "\r\n":
            next_line = index + (2 if text.startswith("\r\n", index) else 1)
            if next_line >= len(text) or text[next_line] in "\r\n":
                return None
            index = next_line
            continue
        if character == "]":
            probe = index + 1
            while probe < len(text) and text[probe] in " \t":
                probe += 1
            if probe < len(text) and text[probe] == ":":
                return probe + 1
        index += 1
    return None


def _line_end(text: str, start: int) -> int:
    newline = text.find("\n", start)
    return len(text) if newline < 0 else newline + 1


def _mask_reference_definitions(text: str) -> str:
    """Mask reference and footnote definitions, including multiline labels."""
    masked: list[str] = []
    copied_until = 0
    cursor = 0
    while cursor < len(text):
        header_end = _reference_definition_header_end(text, cursor)
        if header_end is None:
            cursor = _line_end(text, cursor)
            continue
        end = _line_end(text, header_end)
        while end < len(text) and not _is_markdown_blank_line(text[end : _line_end(text, end)]):
            end = _line_end(text, end)
        masked.append(text[copied_until:cursor])
        masked.append(_mask_markdown_code(text[cursor:end]))
        copied_until = end
        cursor = end
    masked.append(text[copied_until:])
    return "".join(masked)


def _mask_fenced_divs(text: str) -> str:
    """Mask Pandoc fenced Divs, including nested attributed Divs."""
    masked: list[str] = []
    fences: list[int] = []
    for line in _markdown_lines(text):
        body = line.rstrip("\r\n")
        divider = _FENCED_DIV_RE.match(body)
        if not fences:
            if divider is None:
                masked.append(line)
                continue
            fences.append(len(divider["fence"]))
            masked.append(_mask_markdown_code(line))
            continue

        masked.append(_mask_markdown_code(line))
        if divider is None:
            continue
        fence_length = len(divider["fence"])
        if divider["suffix"].strip(" \t"):
            fences.append(fence_length)
        elif fence_length >= fences[-1]:
            fences.pop()
    return "".join(masked)


def _has_tex_math_pair(
    text: str,
    opener: str,
    closer: str,
    *,
    active_closer_required: bool,
) -> bool:
    """Return whether a Pandoc single-backslash TeX-math pair is active."""
    opened = False
    index = 0
    while index < len(text):
        if text[index] != "\\":
            index += 1
            continue
        run_start = index
        while index < len(text) and text[index] == "\\":
            index += 1
        if index == len(text):
            break
        delimiter = text[index]
        run_length = index - run_start
        if delimiter == opener and run_length % 2:
            opened = True
        elif opened and delimiter == closer and (not active_closer_required or run_length % 2):
            return True
        index += 1
    return False


def _has_raw_tex_syntax(text: str) -> bool:
    """Return whether active raw TeX syntax can affect draft visibility."""
    for match in re.finditer(r"\\(.)", text, flags=re.DOTALL):
        if _preceding_backslash_count(text, match.start()) % 2 == 0 and match[1].isalpha():
            return True
    if _has_tex_math_pair(text, "[", "]", active_closer_required=False):
        return True
    if _has_tex_math_pair(text, "(", ")", active_closer_required=True):
        return True
    for match in re.finditer(r"\$", text):
        if _preceding_backslash_count(text, match.start()) % 2 == 0:
            return True
    for match in re.finditer(r"(?m)^[ \t]{0,3}%", text):
        if _preceding_backslash_count(text, match.end() - 1) % 2 == 0:
            return True
    return False


def _has_pandoc_attribute_syntax(text: str) -> bool:
    """Return whether active Pandoc attribute syntax can affect draft visibility."""
    for match in re.finditer(r"\{\s*(?:=|[#.]|[^{}\s=]+[ \t]*=)", text):
        if _preceding_backslash_count(text, match.start()) % 2 == 0:
            return True
    return False


def _has_footnote_definition(text: str) -> bool:
    """Return whether a footnote definition makes direct binding ambiguous."""
    return re.search(r"(?m)^[ \t]*\[\^[^\]\r\n]+\]:", text) is not None


def _has_pandoc_table_syntax(text: str) -> bool:
    """Return whether Pandoc table syntax makes direct claim binding ambiguous."""
    if re.search(
        r"(?m)^[ \t]*[|+]?[ \t]*:?-+:?[ \t]*(?:[|+][ \t]*:?-+:?[ \t]*)+[|+]?[ \t]*$",
        text,
    ):
        return True
    if re.search(r"(?m)^[ \t]*\+(?:[-=]+\+)+[ \t]*$", text):
        return True
    if re.search(r"(?m)^[ \t]*:?-+:?(?:[ \t]+:?-+:?)+[ \t]*$", text):
        return True
    if re.search(r"(?m)^[ \t]+:?-+:?[ \t]*$", text):
        return True
    return len(re.findall(r"(?m)^[ \t]*-+[ \t]*$", text)) >= 2


def _table_container_text(text: str) -> str:
    """Flatten quote/list prefixes before fail-closed table visibility checks."""
    lines: list[str] = []
    for line in _markdown_lines(text):
        while match := _CITATION_TABLE_CONTAINER_PREFIX_RE.match(line):
            line = line[match.end() :]
        lines.append(line)
    return "".join(lines)


def _has_ambiguous_pandoc_table_syntax(text: str) -> bool:
    """Return whether table grammar can change Markdown visibility in a container."""
    return _has_pandoc_table_syntax(text) or _has_pandoc_table_syntax(_table_container_text(text))


def markdown_citation_visibility_is_ambiguous(text: str) -> bool:
    """Return whether table grammar can change visible raw citation boundaries."""
    return _has_ambiguous_pandoc_table_syntax(text)


def _backtick_run_end(text: str, start: int) -> int:
    end = start
    while end < len(text) and text[end] == "`":
        end += 1
    return end


def _preceding_backslash_count(text: str, index: int) -> int:
    count = 0
    index -= 1
    while index >= 0 and text[index] == "\\":
        count += 1
        index -= 1
    return count


def _inline_code_interior_lines(content: str) -> list[str]:
    """Return complete physical lines strictly between inline-code delimiters."""
    if "\n" not in content:
        return []
    lines = _markdown_lines(content)[1:]
    return lines if content.endswith("\n") else lines[:-1]


def _inline_code_span_is_definite(content: str, *, opener_line: str, closer_line: str) -> bool:
    """Return whether a multiline backtick pair avoids known block boundaries."""
    if re.search(r"\r(?!\n)", content):
        return False
    if _QUOTED_LINE_RE.match(opener_line) or _LIST_ITEM_LINE_RE.match(opener_line):
        return False
    if _QUOTED_LINE_RE.match(closer_line) or _LIST_ITEM_LINE_RE.match(closer_line):
        return False
    return not any(
        _is_markdown_blank_line(line)
        or re.fullmatch(r"[ \t]*-+[ \t]*(?:\r?\n)?", line)
        or re.match(r"^[ \t]{0,3}[:~][ \t]+", line)
        or _QUOTED_LINE_RE.match(line)
        or _LIST_ITEM_LINE_RE.match(line)
        or _has_ambiguous_pandoc_table_syntax(line)
        for line in _inline_code_interior_lines(content)
    )


def _mask_inline_code_spans(text: str, *, conservative: bool = False) -> str:
    """Mask inline-code delimiter runs using an indexed linear scan.

    Visibility checks can require a stricter multiline interpretation: masking a
    span that Pandoc parses as blocks would hide a live citation from the export
    gate.
    """
    runs: list[tuple[int, int]] = []
    index = 0
    while index < len(text):
        if text[index] != "`":
            index += 1
            continue
        run_end = _backtick_run_end(text, index)
        runs.append((index, run_end))
        index = run_end

    choices: list[tuple[tuple[int, int] | None, tuple[int, int] | None]] = [(None, None)] * len(
        runs
    )
    next_closer_by_length: dict[int, int] = {}
    for run_index in range(len(runs) - 1, -1, -1):
        start, end = runs[run_index]
        length = end - start
        full_choice = None
        for delimiter_length in range(length, 0, -1):
            if closer_start := next_closer_by_length.get(delimiter_length):
                full_choice = (delimiter_length, closer_start)
                break
        suffix_choice = None
        for delimiter_length in range(length - 1, 0, -1):
            if closer_start := next_closer_by_length.get(delimiter_length):
                suffix_choice = (delimiter_length, closer_start)
                break
        choices[run_index] = (full_choice, suffix_choice)
        next_closer_by_length[length] = start

    runs_by_start = {start: (run_index, end) for run_index, (start, end) in enumerate(runs)}
    masked: list[str] = []
    copied_until = 0
    index = 0
    while index < len(text):
        if text[index] != "`":
            index += 1
            continue
        run_index, opener_end = runs_by_start[index]
        escaped = _preceding_backslash_count(text, index) % 2
        choice = choices[run_index][1 if escaped else 0]
        if choice is None:
            index = opener_end
            continue
        delimiter_length, closer_start = choice
        span_start = opener_end - delimiter_length
        closer_end = closer_start + delimiter_length
        opener_line_start = text.rfind("\n", 0, span_start) + 1
        closer_line_end = text.find("\n", closer_start)
        closer_line_end = len(text) if closer_line_end == -1 else closer_line_end
        if conservative and not _inline_code_span_is_definite(
            text[opener_end:closer_start],
            opener_line=text[opener_line_start:opener_end],
            closer_line=text[closer_start:closer_line_end],
        ):
            index = runs_by_start[closer_start][1]
            continue
        masked.append(text[copied_until:span_start])
        masked.append(_mask_markdown_code(text[span_start:closer_end]))
        copied_until = closer_end
        index = closer_end
    masked.append(text[copied_until:])
    return "".join(masked)


def _container_fence_opening(
    fence: str, info: str, plain_lines: list[str]
) -> tuple[str, int] | None:
    """Return one accepted nested fence's delimiter, if its header is trustworthy."""
    if (
        fence.startswith("`")
        and info.strip()
        and not _SAFE_VISIBILITY_FENCE_INFO_RE.fullmatch(info.strip())
    ):
        return None
    opening, literalize = classify_fenced_code_opening(f"{fence}{info}", plain_lines)
    if opening is None:
        return None
    if literalize:
        info = info.strip()
        boundary_opening, boundary_literalize = classify_fenced_code_opening(fence, plain_lines)
        if (
            fence.startswith("~")
            and re.fullmatch(r"[^\s`{}]+", info)
            and boundary_opening is not None
            and not boundary_literalize
        ):
            return fence[0], len(fence)
        return None
    fence = opening.group("fence")
    return fence[0], len(fence)


def _quoted_fence_closes(line: str, character: str, length: int, quote_depth: int) -> bool:
    """Return whether a blockquote fence closes on this physical line."""
    if fenced_code_closes(line, character, length):
        return True
    match = re.match(r"^ {0,3}(?P<quote>(?:>[ \t]*)+)(?P<content>[^\r\n]*)(?:\r?\n)?$", line)
    return bool(
        match
        and match["quote"].count(">") <= quote_depth
        and fenced_code_closes(match["content"], character, length)
    )


def _quoted_fence_contains(line: str) -> bool:
    """Return whether a physical line remains inside a blockquote container."""
    return _QUOTED_LINE_RE.match(line) is not None


def _list_fence_closes(line: str, character: str, length: int, indentation: int) -> bool:
    """Return whether a list-contained fence closes on this physical line."""
    if fenced_code_closes(line, character, length):
        return True
    prefix = line[:indentation]
    return bool(
        len(prefix) == indentation
        and all(prefix_character in " \t" for prefix_character in prefix)
        and fenced_code_closes(line[indentation:], character, length)
    )


def _list_fence_contains(line: str, indentation: int) -> bool:
    """Return whether a physical line remains an indented list continuation."""
    prefix = line[:indentation]
    return len(prefix) == indentation and all(
        prefix_character in " \t" for prefix_character in prefix
    )


def _quote_list_fence_opening(
    line: str, quote_context: list[str]
) -> tuple[str, int, str, int] | None:
    """Return a narrow quote-to-list fence only when its outer context is safe."""
    quote = _QUOTED_LINE_RE.match(line)
    if quote is None or quote["quote"].count(">") != 1:
        return None
    quote_prefix = line[: quote.start("content")]
    if "\t" in quote_prefix:
        return None
    list_item = _LIST_FENCE_OPEN_RE.match(quote["content"])
    if (
        list_item is None
        or list_item["indent"]
        or "\t" in list_item["spacing"]
        or (fence := _container_fence_opening(list_item["fence"], list_item["info"], quote_context))
        is None
    ):
        return None
    return *fence, quote_prefix, list_item.start("fence")


def _list_quote_fence_opening(
    line: str, list_context: list[str]
) -> tuple[str, int, str, int] | None:
    """Return a narrow list-to-quote fence only when its outer context is safe."""
    match = _COMPOUND_LIST_QUOTE_FENCE_OPEN_RE.match(line)
    if (
        match is None
        or (fence := _container_fence_opening(match["fence"], match["info"], list_context)) is None
    ):
        return None
    return *fence, match["quote"], match.start("quote")


def _quote_list_fence_inner_line(line: str, quote_prefix: str, indentation: int) -> str | None:
    """Return the virtual list-content line under an exact outer quote prefix."""
    if not line.startswith(quote_prefix):
        return None
    inner = line[len(quote_prefix) :]
    prefix = inner[:indentation]
    if len(prefix) != indentation or prefix != " " * indentation:
        return None
    return inner[indentation:]


def _quote_list_fence_closes(
    line: str, character: str, length: int, quote_prefix: str, indentation: int
) -> bool:
    """Return whether a strict quote-to-list fence closes on this line."""
    if fenced_code_closes(line, character, length):
        return True
    if not line.startswith(quote_prefix):
        return False
    after_quote = line[len(quote_prefix) :]
    if fenced_code_closes(after_quote, character, length):
        return True
    inner = _quote_list_fence_inner_line(line, quote_prefix, indentation)
    return inner is not None and fenced_code_closes(inner, character, length)


def _list_quote_fence_inner_line(line: str, quote_prefix: str, indentation: int) -> str | None:
    """Return the virtual quote-content line under an exact list continuation."""
    prefix = line[:indentation]
    if len(prefix) != indentation or prefix != " " * indentation:
        return None
    inner = line[indentation:]
    if not inner.startswith(quote_prefix):
        return None
    return inner[len(quote_prefix) :]


def _list_quote_fence_closes(
    line: str, character: str, length: int, quote_prefix: str, indentation: int
) -> bool:
    """Return whether a strict list-to-quote fence closes on this line."""
    if fenced_code_closes(line, character, length):
        return True
    inner = _list_quote_fence_inner_line(line, quote_prefix, indentation)
    return inner is not None and fenced_code_closes(inner, character, length)


def _quote_fence_context(
    quote_depth: int,
    quote_block_boundaries: dict[int, bool],
    plain_block_boundary: bool,
) -> list[str]:
    """Return a fail-closed context for a quote-contained fence opener."""
    if quote_depth in quote_block_boundaries:
        return [] if quote_block_boundaries[quote_depth] else ["prose"]
    if not quote_block_boundaries:
        return [] if plain_block_boundary else ["prose"]
    return (
        []
        if all(quote_block_boundaries.get(depth, False) for depth in range(1, quote_depth))
        else ["prose"]
    )


def _remember_container_plain_line(
    line: str,
    quote_block_boundaries: dict[int, bool],
    list_item_active: bool,
    plain_block_boundary: bool,
) -> tuple[bool, bool]:
    """Retain the immediate context needed to classify a later container fence."""
    starts_at_block_boundary = plain_block_boundary
    quote = _QUOTED_LINE_RE.match(line)
    plain_heading = quote is None and starts_at_block_boundary and _ATX_HEADING_LINE_RE.match(line)
    list_item = (
        quote is None and _LIST_ITEM_LINE_RE.match(line) and not _THEMATIC_BREAK_LINE_RE.match(line)
    )
    if _is_markdown_blank_line(line):
        list_item_active = False
    elif list_item:
        list_item_active = list_item_active or starts_at_block_boundary
    if _is_markdown_blank_line(line):
        plain_block_boundary = True
    elif plain_heading or (list_item and list_item_active):
        plain_block_boundary = True
    else:
        plain_block_boundary = False
    if quote is None:
        quote_block_boundaries.clear()
        return list_item_active, plain_block_boundary
    quote_depth = quote["quote"].count(">")
    quote_ancestors_at_boundary = bool(quote_block_boundaries) or starts_at_block_boundary
    quote_ancestors_at_boundary &= all(
        quote_block_boundaries.get(depth, True) for depth in range(1, quote_depth)
    )
    quote_starts_at_boundary = quote_ancestors_at_boundary and quote_block_boundaries.get(
        quote_depth, starts_at_block_boundary if not quote_block_boundaries else True
    )
    for depth in range(1, quote_depth):
        quote_block_boundaries[depth] = False
    for depth in list(quote_block_boundaries):
        if depth > quote_depth:
            del quote_block_boundaries[depth]
    quote_content = quote["content"]
    quote_boundary = quote_ancestors_at_boundary and (
        _is_markdown_blank_line(quote_content)
        or bool(_THEMATIC_BREAK_LINE_RE.match(quote_content))
        or bool(quote_starts_at_boundary and _ATX_HEADING_LINE_RE.match(quote_content))
    )
    quote_block_boundaries[quote_depth] = quote_boundary
    return list_item_active, plain_block_boundary


def _mask_container_fenced_code_literals(text: str) -> str:
    """Mask only paired blockquote/list fences without hiding later prose."""
    lines: list[str] = []
    pending: list[str] = []
    quote_block_boundaries: dict[int, bool] = {}
    kind = ""
    fence_character = ""
    fence_length = 0
    quote_depth = 0
    list_indentation = 0
    compound_prefix = ""
    compound_indentation = 0
    list_item_active = False
    plain_block_boundary = True
    table_rule_pending = False
    for line in _markdown_lines(text):
        if kind:
            if kind == "quote":
                closes = _quoted_fence_closes(line, fence_character, fence_length, quote_depth)
            elif kind == "list":
                list_prefix = line[:list_indentation]
                closes = "\t" not in list_prefix and _list_fence_closes(
                    line, fence_character, fence_length, list_indentation
                )
            elif kind == "quote-list":
                closes = _quote_list_fence_closes(
                    line,
                    fence_character,
                    fence_length,
                    compound_prefix,
                    compound_indentation,
                )
            else:
                closes = _list_quote_fence_closes(
                    line,
                    fence_character,
                    fence_length,
                    compound_prefix,
                    compound_indentation,
                )
            if closes:
                pending.append(line)
                lines.extend(_mask_markdown_code(pending_line) for pending_line in pending)
                pending.clear()
                quote_block_boundaries.clear()
                plain_block_boundary = True
                table_rule_pending = False
                kind = ""
                fence_character = ""
                fence_length = 0
                quote_depth = 0
                list_indentation = 0
                compound_prefix = ""
                compound_indentation = 0
                continue
            if kind == "quote":
                contains = _quoted_fence_contains(line)
            elif kind == "list":
                list_prefix = line[:list_indentation]
                contains = "\t" not in list_prefix and _list_fence_contains(line, list_indentation)
            elif kind == "quote-list":
                contains = (
                    _quote_list_fence_inner_line(line, compound_prefix, compound_indentation)
                    is not None
                )
            else:
                contains = (
                    _list_quote_fence_inner_line(line, compound_prefix, compound_indentation)
                    is not None
                )
            if contains:
                pending.append(line)
                continue
            lines.extend(pending)
            for pending_line in pending:
                list_item_active, plain_block_boundary = _remember_container_plain_line(
                    pending_line,
                    quote_block_boundaries,
                    list_item_active,
                    plain_block_boundary,
                )
                table_rule_pending = not _is_markdown_blank_line(pending_line) and (
                    table_rule_pending or _has_ambiguous_pandoc_table_syntax(pending_line)
                )
            pending.clear()
            kind = ""
            fence_character = ""
            fence_length = 0
            quote_depth = 0
            list_indentation = 0
            compound_prefix = ""
            compound_indentation = 0

        quote = _QUOTED_FENCE_OPEN_RE.match(line)
        quote_context = (
            ["prose"]
            if list_item_active
            else _quote_fence_context(
                quote["quote"].count(">"), quote_block_boundaries, plain_block_boundary
            )
            if quote
            else []
        )
        if (
            not table_rule_pending
            and quote
            and (fence := _container_fence_opening(quote["fence"], quote["info"], quote_context))
        ):
            kind = "quote"
            fence_character, fence_length = fence
            quote_depth = quote["quote"].count(">")
            quote_block_boundaries.clear()
            list_item_active = False
            plain_block_boundary = True
            table_rule_pending = False
            pending.append(line)
            continue

        list_item = _LIST_FENCE_OPEN_RE.match(line)
        list_context = [] if list_item_active or plain_block_boundary else ["prose"]
        if (
            not table_rule_pending
            and list_item
            and "\t" not in list_item["indent"] + list_item["spacing"]
            and (
                fence := _container_fence_opening(
                    list_item["fence"], list_item["info"], list_context
                )
            )
        ):
            kind = "list"
            fence_character, fence_length = fence
            list_indentation = list_item.start("fence")
            quote_block_boundaries.clear()
            list_item_active = True
            plain_block_boundary = True
            table_rule_pending = False
            pending.append(line)
            continue

        compound_quote_context = (
            ["prose"]
            if list_item_active
            else _quote_fence_context(1, quote_block_boundaries, plain_block_boundary)
        )
        if not table_rule_pending and (
            compound := _quote_list_fence_opening(line, compound_quote_context)
        ):
            kind = "quote-list"
            fence_character, fence_length, compound_prefix, compound_indentation = compound
            quote_block_boundaries.clear()
            list_item_active = False
            plain_block_boundary = True
            table_rule_pending = False
            pending.append(line)
            continue

        compound_list_context = [] if list_item_active or plain_block_boundary else ["prose"]
        if not table_rule_pending and (
            compound := _list_quote_fence_opening(line, compound_list_context)
        ):
            kind = "list-quote"
            fence_character, fence_length, compound_prefix, compound_indentation = compound
            quote_block_boundaries.clear()
            list_item_active = True
            plain_block_boundary = True
            table_rule_pending = False
            pending.append(line)
            continue

        lines.append(line)
        list_item_active, plain_block_boundary = _remember_container_plain_line(
            line,
            quote_block_boundaries,
            list_item_active,
            plain_block_boundary,
        )
        table_rule_pending = not _is_markdown_blank_line(line) and (
            table_rule_pending or _has_ambiguous_pandoc_table_syntax(line)
        )
    lines.extend(pending)
    return "".join(lines)


def _mask_top_level_code_literals(text: str) -> str:
    """Mask top-level fenced code while preserving the shared fence semantics."""
    lines: list[str] = []
    plain_lines: list[str] = []
    fence_char = ""
    fence_length = 0
    literal_tilde_fence_length = 0
    for line in _markdown_lines(text):
        if fence_char:
            lines.append(_mask_markdown_code(line))
            if fenced_code_closes(line, fence_char, fence_length):
                fence_char = ""
                fence_length = 0
            continue

        if literal_tilde_fence_length:
            if fenced_code_closes(line, "~", literal_tilde_fence_length):
                literal_tilde_fence_length = 0
            plain_lines.append(line)
            lines.append(_mask_markdown_code(line) if re.match(r"^(?: {4}|\t)", line) else line)
            continue

        opening, literalize = classify_fenced_code_opening(line, plain_lines)
        if opening is not None and not literalize:
            fence = opening.group("fence")
            fence_char = fence[0]
            fence_length = len(fence)
            lines.append(_mask_markdown_code(line))
            plain_lines.clear()
            continue

        if literalize and opening is not None:
            if opening.group("fence").startswith("~"):
                literal_tilde_fence_length = len(opening.group("fence"))
        plain_lines.append(line)
        lines.append(_mask_markdown_code(line) if re.match(r"^(?: {4}|\t)", line) else line)

    return "".join(lines)


def _visibility_fenced_code_opening(
    line: str, at_block_boundary: bool
) -> tuple[re.Match[str] | None, bool]:
    """Classify only fence headers whose visible-code semantics are definite."""
    opening, literalize = classify_fenced_code_opening(line, [] if at_block_boundary else ["prose"])
    if opening is None or literalize:
        return opening, literalize
    info = line[opening.end() :].rstrip("\r\n").strip(" \t")
    if info and not _SAFE_VISIBILITY_FENCE_INFO_RE.fullmatch(info):
        return None, False
    return opening, False


def _mask_visibility_top_level_code_literals(text: str) -> str:
    """Mask only definite top-level code without recreating Pandoc's containers."""
    lines: list[str] = []
    pending_fence: list[str] = []
    fence_char = ""
    fence_length = 0
    literal_tilde_fence_length = 0
    indented_code = False
    at_block_boundary = True
    seen_nonblank = False
    table_rule_pending = False
    for line in _markdown_lines(text):
        if fence_char:
            pending_fence.append(line)
            if fenced_code_closes(line, fence_char, fence_length):
                lines.extend(_mask_markdown_code(pending_line) for pending_line in pending_fence)
                pending_fence.clear()
                fence_char = ""
                fence_length = 0
                at_block_boundary = True
                seen_nonblank = True
                table_rule_pending = False
            continue

        if indented_code:
            if re.match(r"^(?: {4}|\t)", line):
                lines.append(_mask_markdown_code(line))
                continue
            if _is_markdown_blank_line(line):
                lines.append(line)
                continue
            indented_code = False
            at_block_boundary = True
            seen_nonblank = True

        if literal_tilde_fence_length:
            if fenced_code_closes(line, "~", literal_tilde_fence_length):
                literal_tilde_fence_length = 0
            lines.append(line)
            if _is_markdown_blank_line(line):
                at_block_boundary = True
            else:
                at_block_boundary = False
                seen_nonblank = True
            table_rule_pending = not _is_markdown_blank_line(line) and (
                table_rule_pending or _has_ambiguous_pandoc_table_syntax(line)
            )
            continue

        if re.match(r"^(?: {4}|\t)", line) and not seen_nonblank:
            lines.append(_mask_markdown_code(line))
            indented_code = True
            continue

        opening, literalize = _visibility_fenced_code_opening(line, at_block_boundary)
        if not table_rule_pending and opening is not None and not literalize:
            fence = opening.group("fence")
            fence_char = fence[0]
            fence_length = len(fence)
            pending_fence.append(line)
            continue

        if literalize and opening is not None and opening.group("fence").startswith("~"):
            literal_tilde_fence_length = len(opening.group("fence"))
        lines.append(line)
        if _is_markdown_blank_line(line):
            at_block_boundary = True
        else:
            at_block_boundary = bool(at_block_boundary and _ATX_HEADING_LINE_RE.match(line))
            seen_nonblank = True
        table_rule_pending = not _is_markdown_blank_line(line) and (
            table_rule_pending or _has_ambiguous_pandoc_table_syntax(line)
        )

    lines.extend(pending_fence)
    return "".join(lines)


def markdown_code_literals_masked(text: str) -> str:
    """Mask Markdown code literals while preserving source offsets and visible prose.

    This deliberately leaves headings and other rendered Markdown intact for
    callers that need to inspect direct Markdown controls.
    """
    fenced = _mask_top_level_code_literals(text)
    fenced = _mask_container_fenced_code_literals(fenced)
    return _mask_inline_code_spans(fenced)


def markdown_visible_code_literals_masked(text: str) -> str:
    """Mask only definite code literals before checking rendered Markdown syntax.

    Unlike :func:`markdown_code_literals_masked`, this does not treat every
    four-space or tab-prefixed physical line as code: indented code cannot
    interrupt a paragraph, so doing so could hide a visible Pandoc citation.
    """
    fenced = _mask_visibility_top_level_code_literals(text)
    fenced = _mask_container_fenced_code_literals(fenced)
    return _mask_inline_code_spans(fenced, conservative=True)


def _markdown_control_text(text: str) -> str:
    """Mask non-rendering syntax so only direct Markdown controls can bind evidence."""

    yaml_for_table = _mask_yaml_mapping_frontmatter(text)
    if yaml_for_table is None:
        return _mask_markdown_code(text)
    if (
        "\r" in text
        or _has_raw_html_element(text)
        or _has_pandoc_attribute_syntax(text)
        or _has_raw_tex_syntax(text)
        or _has_footnote_definition(text)
        or _has_mmd_title_field(text)
        or _has_abbreviation_syntax(text)
        or _has_ambiguous_pandoc_table_syntax(yaml_for_table)
    ):
        return _mask_markdown_code(text)
    nonbinding = _mask_html_comments(text)
    nonbinding = _mask_html_declarations(nonbinding)
    nonbinding = _mask_yaml_frontmatter(nonbinding)
    nonbinding = _mask_definition_terms(nonbinding)
    nonbinding = _mask_markdown_headings(nonbinding)
    nonbinding = _mask_markdown_containers(nonbinding)
    nonbinding = _mask_reference_definitions(nonbinding)
    nonbinding = _mask_multiline_bracket_constructs(nonbinding)
    nonbinding = _mask_multiline_parenthesized_constructs(nonbinding)
    nonbinding = _mask_fenced_divs(nonbinding)
    return markdown_code_literals_masked(nonbinding)


def _direct_evidence_marker_matches(text: str) -> list[tuple[re.Match[str], EvidenceMarker]]:
    """Return evidence markers in direct Markdown claim lines from control text."""
    matches: list[tuple[re.Match[str], EvidenceMarker]] = []
    for match in _DIRECT_EVIDENCE_MARKER_RE.finditer(text):
        try:
            marker = parse_evidence_marker(match["marker"])
        except ValueError:
            continue
        matches.append((match, marker))
    return matches


def _evidence_marker_occurrences_from_markdown(
    text: str,
) -> list[tuple[EvidenceMarker, bool]]:
    """Return raw evidence markers and whether each is a direct visible occurrence."""
    direct_spans = {span for span, _marker in direct_evidence_marker_spans_from_markdown(text)}
    occurrences: list[tuple[EvidenceMarker, bool]] = []
    for match in _RAW_EVIDENCE_MARKER_RE.finditer(text):
        try:
            marker = parse_evidence_marker(match.group(0))
        except ValueError:
            continue
        occurrences.append((marker, match.span() in direct_spans))
    return occurrences


def direct_evidence_marker_spans_from_markdown(
    text: str,
) -> list[tuple[tuple[int, int], EvidenceMarker]]:
    """Return source spans and markers that appear on direct, visible claim lines."""
    control_text = _markdown_control_text(text)
    return [
        (match.span("marker"), marker)
        for match, marker in _direct_evidence_marker_matches(control_text)
    ]


def evidence_markers_from_markdown(text: str) -> list[EvidenceMarker]:
    """Return markers that appear on direct, visible Markdown claim lines."""
    return [marker for _span, marker in direct_evidence_marker_spans_from_markdown(text)]


def resolve_concept_id(conn: sqlite3.Connection, ref: str) -> str:
    """Return the canonical ``concepts`` key for a reference, minting nothing.

    v16 identity: a catalog work keys by its bare ``work_id`` while its
    ``concepts.path`` renders as ``catalog/sources/<work_id>``, so the bare,
    rendered, ``./``-prefixed, and ``/source.md`` forms all resolve to one
    parent. An unknown reference resolves to its normalized self.
    """
    rel = normalize_path(ref)
    return _lookup_concept_id(conn, rel) or rel


def _concept_key_for_file(vault: Path, path: str, payload_text: str = "") -> str:
    """Return the identity a file Concept is created with on first observation.

    A valid frontmatter ULID is the identity; any other ``id`` (a catalog
    ``work_id``, a blank, a hand-written slug) leaves the Concept on its B.1 path
    key. ``payload_text`` is the staged content for a file that is not on disk yet.
    """
    text = payload_text or safe_read(Path(vault) / path)
    raw_id = str(parse_frontmatter(text).get("id") or "")
    return raw_id if is_ulid(raw_id) else normalize_path(path)


def ensure_concept_parent_conn(
    conn: sqlite3.Connection,
    ref: str,
    *,
    concept_type: str,
    store: str,
    path: str,
) -> str:
    """Create or refresh the FK parent row for one Concept and return its id.

    Never silently accepts an identity collision (contract 10), while still
    letting one identity update its own attributes. v16 decouples the id from the
    path, so *same resolved id, requested path owned by nobody else* is a rename
    (or an in-place ``concept_type`` change), not a collision, and it updates.
    Two refusals remain, each a descriptive ``RuntimeError`` naming both shapes:
    a reference resolving onto a row of a different ``store`` — the line between
    a db catalog work and a mirrored file Concept, which is the hijack contract 10
    forbids — and two distinct ids claiming one path, caught below by
    ``idx_concepts_path`` so the message names the resident owner.
    """
    concept_id = _lookup_concept_id(conn, ref) or _canonical_concept_ref(ref)
    if not concept_id:
        raise ValueError("concept reference is required")
    wanted = (_registry_concept_type(concept_type), store, normalize_path(path))
    resident = conn.execute(
        "SELECT concept_type, store, path FROM concepts WHERE concept_id = ?",
        (concept_id,),
    ).fetchone()
    if resident is not None and str(resident["store"]) != wanted[1]:
        found = (str(resident["concept_type"]), str(resident["store"]), str(resident["path"]))
        raise _concept_shape_collision(ref, concept_id, found, concept_id, wanted)
    if resident is None:
        _adopt_path_key_identity_conn(conn, concept_id, wanted)
    try:
        conn.execute(
            """
            INSERT INTO concepts(concept_id, concept_type, store, path)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(concept_id) DO UPDATE SET
                concept_type = excluded.concept_type,
                store = excluded.store,
                path = excluded.path
            """,
            (concept_id, *wanted),
        )
    except sqlite3.IntegrityError as exc:
        # idx_concepts_path: a different identity already renders at this path.
        if "concepts.path" not in str(exc):
            raise
        owner = conn.execute(
            "SELECT concept_id, concept_type, store, path FROM concepts WHERE path = ?",
            (wanted[2],),
        ).fetchone()
        found = (
            (str(owner["concept_type"]), str(owner["store"]), str(owner["path"]))
            if owner is not None
            else wanted
        )
        owner_id = str(owner["concept_id"]) if owner is not None else "<unknown>"
        raise _concept_shape_collision(ref, owner_id, found, concept_id, wanted) from exc
    return concept_id


def _adopt_path_key_identity_conn(
    conn: sqlite3.Connection,
    concept_id: str,
    wanted: tuple[str, str, str],
) -> None:
    """Let the still-provisional row at one path take the ULID its file now carries.

    v16 mirrors an id-less file — hand-written, externally dropped — under its own
    path as a provisional key, so the moment that file authors a ULID the same path
    presents a new identity. That is this Concept's first real identity, not a
    second Concept claiming the path: the row takes it in place and the v16 foreign
    keys carry its verdict, flags and edges along. Every genuine collision is left
    to the caller's ``idx_concepts_path`` refusal — a resident that is already
    id-keyed, a non-ULID claim, a different ``store``, or an incoming identity that
    already lives at another path (which would merge two Concepts).

    The re-key itself is ``_rekey_path_keyed_concept_conn``, never a second copy of
    its statement: adoption moves the same identity a rename moves, so it owes the
    same tables. Only the path is unchanged, and the path is exactly what the
    identity-space enumeration does not touch.
    """
    _concept_type, store, path = wanted
    if not path or not is_ulid(concept_id):
        return
    owner = conn.execute(
        "SELECT concept_id, store FROM concepts WHERE path = ?", (path,)
    ).fetchone()
    if owner is None or str(owner["concept_id"]) != path or str(owner["store"]) != store:
        return
    if conn.execute("SELECT 1 FROM concepts WHERE concept_id = ?", (concept_id,)).fetchone():
        return
    _rekey_path_keyed_concept_conn(conn, path, concept_id)


def _concept_shape_collision(
    ref: str,
    found_id: str,
    found: tuple[str, str, str],
    wanted_id: str,
    wanted: tuple[str, str, str],
) -> RuntimeError:
    """Return the descriptive refusal for a v16 Concept identity collision."""

    def shape(concept_id: str, values: tuple[str, str, str]) -> str:
        return (
            f"(concept_id={concept_id!r}, concept_type={values[0]!r},"
            f" store={values[1]!r}, path={values[2]!r})"
        )

    return RuntimeError(
        f"concept identity collision for {ref!r}: {shape(found_id, found)}"
        f" already exists; refusing to rewrite it as {shape(wanted_id, wanted)}"
    )


def _concept_missing_parent(ref: str, concept_id: str, subject: str) -> RuntimeError:
    """Return the descriptive refusal for an FK-backed write with no Concept parent."""
    return RuntimeError(
        f"unknown Concept for {subject}: {ref!r} resolves to concept_id={concept_id!r},"
        " which has no concepts row; mirror the Concept before writing to it"
    )


def _lookup_concept_id(conn: sqlite3.Connection, ref: str) -> str | None:
    """Return the existing concepts key for a reference, or None."""
    rel = normalize_path(ref)
    if not rel:
        return None
    candidates = [rel]
    rendered = _canonical_concept_ref(rel)
    if rendered and rendered != rel:
        candidates.append(rendered)
    for candidate in candidates:
        row = conn.execute(
            "SELECT concept_id FROM concepts WHERE concept_id = ? OR path = ?",
            (candidate, candidate),
        ).fetchone()
        if row is not None:
            return str(row["concept_id"])
    return None


def _canonical_concept_ref(ref: str) -> str:
    """Return the identity a reference would mint: catalog renderings go bare."""
    rel = normalize_path(ref)
    if rel.startswith("catalog/sources/"):
        return rel.removeprefix("catalog/sources/").removesuffix("/source.md")
    return rel


def _concept_parent_shape(rel: str) -> tuple[str, str, str]:
    """Return the (concept_type, store, path) to mint for an unmirrored reference."""
    if rel.startswith("catalog/sources/"):
        return "work", "db", f"catalog/sources/{_canonical_concept_ref(rel)}"
    return _folder_concept_types().get(rel.split("/", 1)[0], "note"), "file", rel


def _registry_concept_type(value: str) -> str:
    """Map a document type onto its Concept-type registry member, failing closed.

    Deliberately a superset of the named Consumes seam
    ``schema.concept_type_for(document_type)``, which accepts document types only
    and re-reads every types/*.yaml per call. The v16 parent-ensure seam is on the
    hot path of every mirror rebuild and edge pass, and its callers pass registry
    members (``work``, ``note``) as often as document types (``fulltext``,
    ``code-artifact``), so this maps both domains over one cached table. For the
    document-type domain it returns exactly what ``concept_type_for`` returns —
    `tests/test_concept_types.py` pins that equivalence.
    """
    name = str(value).strip()
    mapped = _concept_type_map().get(name)
    if mapped is None:
        raise ValueError(f"unknown concept type: {value!r}")
    return mapped


def _concept_type_map() -> dict[str, str]:
    """Return {document or concept type: registry concept type} from the seed."""
    from memoria_vault.runtime.subsystems.lib import schema as schema_lib

    schemas_dir = Path(schema_lib.SCHEMAS_DIR)
    cached = _CONCEPT_TYPE_MAPS.get(schemas_dir)
    if cached is None:
        cached = {str(name): str(name) for name in schema_lib.load_concept_types(schemas_dir)}
        cached.update(
            {
                str(name): str(data["concept_type"])
                for name, data in schema_lib.load_types(schemas_dir).items()
            }
        )
        _CONCEPT_TYPE_MAPS[schemas_dir] = cached
    return cached


def _folder_concept_types() -> dict[str, str]:
    """Return {bundle folder: registry concept type} from the seeded folder homes."""
    from memoria_vault.runtime.subsystems.lib import schema as schema_lib

    schemas_dir = Path(schema_lib.SCHEMAS_DIR)
    cached = _FOLDER_CONCEPT_TYPES.get(schemas_dir)
    if cached is None:
        homes = schema_lib.load_folders(schemas_dir).get("homes") or {}
        cached = {
            str(folder): _registry_concept_type(str(document_type))
            for document_type, folder in homes.items()
        }
        _FOLDER_CONCEPT_TYPES[schemas_dir] = cached
    return cached


def _set_concept_verdict_conn(
    conn: sqlite3.Connection,
    concept_id: str,
    check_status: str,
) -> None:
    target = resolve_concept_id(conn, concept_id)
    conn.execute(
        """
        INSERT INTO concept_verdicts(concept_id, check_status)
        VALUES (?, ?)
        ON CONFLICT(concept_id) DO UPDATE SET
            check_status = excluded.check_status
        """,
        (target, _check_status(check_status)),
    )
    _cascade_passage_check_status_conn(conn, target, check_status)


def _cascade_passage_check_status_conn(
    conn: sqlite3.Connection,
    concept_id: str,
    check_status: str,
) -> None:
    status = _check_status(check_status)
    conn.execute(
        """
        UPDATE passages
        SET check_status = ?
        WHERE concept_id = ?
           OR work_id = ?
           OR path = (SELECT path FROM concepts WHERE concept_id = ?)
        """,
        (status, concept_id, concept_id, concept_id),
    )


def _check_status(check_status: str) -> str:
    status = check_status.strip()
    if status not in CHECK_STATUSES:
        raise ValueError(f"invalid check_status: {check_status!r}")
    return status


def _work_aspect_type(value: str) -> str:
    aspect_type = value.strip().lower().replace("-", "_")
    if aspect_type not in WORK_ASPECT_TYPES:
        raise ValueError(f"unknown work aspect type: {value}")
    return aspect_type


def _concept_edge_relation(value: str) -> str:
    relation = value.strip().lower()
    if relation not in EDGE_RELATIONS:
        raise ValueError(f"unknown concept edge relation: {value}")
    return relation


def concept_edge_id(source_concept_id: str, relation_type: str, target_concept_id: str) -> str:
    """Return the deterministic id for a normalized concept-edge triple."""
    key = f"{source_concept_id}\0{relation_type}\0{target_concept_id}"
    return hashlib.sha256(key.encode()).hexdigest()[:24]


def _code_purpose(value: str) -> str:
    purpose = value.strip().lower()
    if purpose not in {"grounds", "deliverable", "both"}:
        raise ValueError(f"invalid code artifact purpose: {value!r}")
    return purpose


def _code_artifact_status(value: str) -> str:
    status = value.strip().lower()
    if status not in {"draft", "ready", "failed", "retired"}:
        raise ValueError(f"invalid code artifact status: {value!r}")
    return status


def _code_run_state(value: str) -> str:
    run_state = value.strip().lower()
    if run_state not in {"pending", "running", "succeeded", "failed", "unavailable"}:
        raise ValueError(f"invalid code run state: {value!r}")
    return run_state


def _passage_id(path: str, text_sha256: str) -> str:
    return hashlib.sha256(f"{path}\0{text_sha256}".encode()).hexdigest()[:24]


def _work_id(value: str) -> str:
    rel = normalize_path(value)
    rel = rel.removeprefix("catalog/sources/").removesuffix("/source.md")
    work_id = safe_filename(rel.strip("/")).strip("._-")
    if not work_id:
        raise ValueError("work_id is required")
    return work_id


def _csl_authors(csl: dict[str, Any]) -> list[str]:
    rows = csl.get("author")
    if not isinstance(rows, list):
        return []
    authors = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if literal := str(row.get("literal") or "").strip():
            authors.append(literal)
            continue
        family = str(row.get("family") or "").strip()
        given = str(row.get("given") or "").strip()
        if family and given:
            authors.append(f"{given} {family}")
        elif family:
            authors.append(family)
    return authors


def _csl_issued(csl: dict[str, Any]) -> str:
    issued = csl.get("issued")
    if not isinstance(issued, dict):
        return ""
    parts = issued.get("date-parts")
    if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0]:
        return "-".join(str(part) for part in parts[0])
    return str(issued.get("raw") or "")


def _json_rows(values: Iterable[str | dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for value in values:
        rows.append(dict(value) if isinstance(value, dict) else {"id": normalize_path(str(value))})
    return rows


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _committed_materialization_commit(vault: Path, relpath: str, expected_sha256: str) -> str:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=vault,
        check=False,
        text=True,
        capture_output=True,
    )
    if head.returncode:
        return ""
    commit = head.stdout.strip()
    blob = subprocess.run(
        ["git", "show", f"{commit}:{normalize_path(relpath)}"],
        cwd=vault,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if blob.returncode:
        return ""
    if "sha256:" + hashlib.sha256(blob.stdout).hexdigest() != expected_sha256:
        return ""
    return commit


def _journal_hash(
    event_id: int,
    timestamp: str,
    event_type: str,
    machine: str,
    payload_json: str,
    prev_hash: str,
) -> str:
    payload = {
        "event_id": event_id,
        "timestamp": timestamp,
        "event_type": event_type,
        "machine": machine,
        "payload": json.loads(payload_json),
        "prev_hash": prev_hash,
    }
    return hashlib.sha256(_json(payload).encode("utf-8")).hexdigest()
