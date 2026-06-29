"""Markdown helpers shared by vault operations."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

DEFAULT_SKIP_DIRS = frozenset({".git", ".memoria", ".obsidian", "node_modules"})


def safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def parse_frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    raw = text[3:end]
    try:
        import yaml
    except ImportError:
        return _parse_frontmatter_minimal(raw)
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def read_frontmatter(path: Path) -> dict[str, Any]:
    return parse_frontmatter(safe_read(path))


def strip_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    return text[end + 4 :].lstrip("\n")


def iter_markdown(
    vault: Path, skip_dirs: set[str] | frozenset[str] | None = None
) -> Iterator[Path]:
    skipped = set(DEFAULT_SKIP_DIRS if skip_dirs is None else skip_dirs)
    for dirpath, dirnames, filenames in os.walk(vault):
        dirnames[:] = sorted(name for name in dirnames if name not in skipped)
        for name in sorted(filenames):
            if name.endswith(".md"):
                yield Path(dirpath) / name


def _parse_frontmatter_minimal(raw: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        if line.startswith((" ", "\t")):
            continue
        key, _, value = line.partition(":")
        value = value.strip().strip("\"'")
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key.strip()] = [
                item.strip().strip("\"'") for item in inner.split(",") if item.strip()
            ]
        else:
            data[key.strip()] = value
    return data
