"""User-scope secrets file loading and the credentials registry (spec section 4b)."""

from __future__ import annotations

import os
import re
import stat
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

_NAME_RE = re.compile(r"[A-Z][A-Z0-9_]*")


def secrets_path() -> Path:
    config_home = os.environ.get("XDG_CONFIG_HOME", "").strip()
    root = (
        Path(config_home)
        if config_home and Path(config_home).is_absolute()
        else Path.home() / ".config"
    )
    return root / "memoria" / "secrets.env"


def read_secrets_file(path: Path | None = None) -> tuple[dict[str, str], str]:
    target = path or secrets_path()
    try:
        fd = os.open(target, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
    except FileNotFoundError:
        return {}, ""
    except OSError:
        return {}, f"secrets file {target} could not be opened; refusing to load it"
    try:
        mode = os.fstat(fd).st_mode
        if not stat.S_ISREG(mode):
            return {}, f"secrets file {target} is not a regular file; refusing to load it"
        if mode & stat.S_IROTH:
            return {}, (
                f"secrets file {target} is world-readable; refusing to load it - "
                f"run: chmod 600 {target}"
            )
        with os.fdopen(fd, "r", encoding="utf-8") as source:
            fd = None
            return _parse_env_text(source.read()), ""
    except (OSError, UnicodeDecodeError):
        return {}, f"secrets file {target} could not be read; refusing to load it"
    finally:
        if fd is not None:
            os.close(fd)


def load_secrets(environ: MutableMapping[str, str] | None = None) -> dict[str, Any]:
    env = os.environ if environ is None else environ
    path = secrets_path()
    values, warning = read_secrets_file(path)
    loaded = [name for name in sorted(values) if name not in env]
    for name in loaded:
        env[name] = values[name]
    return {"path": str(path), "loaded": loaded, "warning": warning}


def _parse_env_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, _, value = stripped.partition("=")
        name = name.strip()
        if not _NAME_RE.fullmatch(name):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if "\0" in value:
            continue
        values[name] = value
    return values
