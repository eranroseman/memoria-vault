#!/usr/bin/env python3
"""Graded loudness routing helpers.

`loudness` is card metadata. Open block cards pause delegation and review-gated
promotion until the PI acknowledges them by resolving the card.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from memoria_vault.runtime.vaultio import read_frontmatter

BLOCK_LOUDNESS = "block"
ATTENTION_PROJECTION = "attention"
OPEN_ATTENTION_STATUS = "open"


def is_open_blocker(frontmatter: dict[str, Any]) -> bool:
    return (
        str(frontmatter.get("projection") or "").lower() == ATTENTION_PROJECTION
        and str(frontmatter.get("attention_status") or "").lower() == OPEN_ATTENTION_STATUS
        and str(frontmatter.get("loudness") or "").lower() == BLOCK_LOUDNESS
    )


def open_blockers(vault: Path) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    for path in sorted((vault / "inbox").glob("*.md")):
        fm = read_frontmatter(path)
        if is_open_blocker(fm):
            blockers.append(
                {
                    "path": str(path.relative_to(vault)).replace("\\", "/"),
                    "title": str(fm.get("title") or path.stem),
                    "type": str(fm.get("attention_kind") or fm.get("type") or "card"),
                }
            )
    return blockers


def blocker_message(blockers: list[dict[str, str]]) -> str:
    if not blockers:
        return ""
    names = ", ".join(f"{b['path']} ({b['title']})" for b in blockers[:3])
    more = "" if len(blockers) <= 3 else f"; +{len(blockers) - 3} more"
    return f"open block-loudness card(s) require PI acknowledgement before dispatch/promotion: {names}{more}"
