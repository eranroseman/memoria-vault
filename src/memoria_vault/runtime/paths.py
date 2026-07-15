"""Small path helpers shared by runtime scripts."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_filename(value: str) -> str:
    """Replace characters outside ``[A-Za-z0-9._-]`` with underscores."""
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in str(value))


def resolve_vault(arg: str | None) -> Path:
    """Resolve a vault root from an argument or environment variables."""
    raw = arg
    candidates = ("MEMORIA_VAULT_PATH", "OBSIDIAN_VAULT_PATH")
    if not raw:
        for var in candidates:
            raw = os.environ.get(var)
            if raw:
                break
    if not raw:
        names = " or ".join(candidates)
        sys.exit(f"no vault path: pass --vault <path> or set {names}")
    vault = Path(raw).expanduser().resolve()
    if not vault.is_dir():
        sys.exit(f"not a directory: {vault}")
    return vault
