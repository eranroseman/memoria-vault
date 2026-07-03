"""Tolerant JSONL I/O helpers."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from memoria_vault.runtime.vaultio import append_text_durable


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    """Yield JSON objects from ``path``, skipping missing files and bad lines."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            yield row


def append_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    """Append JSON objects to ``path``, creating parent directories."""
    rows = list(rows)
    if not rows:
        return
    text = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    append_text_durable(path, text, create_parent=True)
