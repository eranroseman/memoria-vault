"""Per-vault server rendezvous state helpers."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

STATE_KEY_LENGTH = 16
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
    temp = target.with_suffix(".json.tmp")
    body = json.dumps(entry, ensure_ascii=False, sort_keys=True).encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(temp, flags, 0o600)
    try:
        if os.name == "posix":
            os.fchmod(fd, 0o600)
        os.write(fd, body)
    finally:
        os.close(fd)
    os.replace(temp, target)
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


def pid_alive(pid: int) -> bool:
    """Return whether the operating system reports a process as live."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True
