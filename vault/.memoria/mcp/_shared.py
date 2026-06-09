"""Shared utilities for the Memoria MCP + detector tooling.

Dependency-free (stdlib only) so every module that imports this can still run and
self-test without PyYAML, ``mcp``, or any other optional runtime dependency.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


# --------------------------------------------------------------------------- #
# Timestamps
# --------------------------------------------------------------------------- #
def now_iso() -> str:
    """UTC now as ISO-8601 with trailing ``Z``."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s: str) -> datetime | None:
    """Parse an ISO-8601 timestamp string, or ``None`` on failure."""
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


# --------------------------------------------------------------------------- #
# Filesystem helpers
# --------------------------------------------------------------------------- #
def safe_filename(s: str) -> str:
    """Replace non-alnum chars (except ``._-``) with underscores."""
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in str(s))


def resolve_vault(arg: str | None, *env_vars: str) -> Path:
    """Resolve a vault root from a CLI arg or environment variables.

    Falls back through *env_vars* in order (default: ``MEMORIA_VAULT_PATH``).
    Exits with an error if no path is found or the path is not a directory.
    """
    raw = arg
    if not raw:
        for var in env_vars or ("MEMORIA_VAULT_PATH",):
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


# --------------------------------------------------------------------------- #
# JSONL I/O
# --------------------------------------------------------------------------- #
def iter_jsonl(path: Path):
    """Yield parsed dicts from a JSONL file, skipping blanks and bad lines."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def append_jsonl(path: Path, rows: list[dict]) -> None:
    """Append JSON objects as lines to a JSONL file."""
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
