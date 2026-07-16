"""Per-vault server rendezvous state helpers."""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

STATE_KEY_LENGTH = 16


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
