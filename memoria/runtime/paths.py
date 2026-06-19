"""Small path helpers shared by runtime scripts."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def safe_filename(value: str) -> str:
    """Replace characters outside ``[A-Za-z0-9._-]`` with underscores."""
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in str(value))


def resolve_vault(arg: str | None, *env_vars: str) -> Path:
    """Resolve a vault root from an argument or environment variables."""
    raw = arg
    if not raw:
        for var in env_vars or ("MEMORIA_VAULT_PATH", "OBSIDIAN_VAULT_PATH"):
            raw = os.environ.get(var)
            if raw:
                break
    if not raw:
        names = " or ".join(env_vars) if env_vars else "MEMORIA_VAULT_PATH"
        sys.exit(f"no vault path: pass --vault <path> or set {names}")
    vault = Path(raw).expanduser().resolve()
    if not vault.is_dir():
        sys.exit(f"not a directory: {vault}")
    return vault
