#!/usr/bin/env python3
"""Graded loudness routing helpers.

`loudness` is card metadata, but alert/block levels have routing semantics:
alert/block cards are push-worthy, and open block cards pause delegation and
review-gated promotion until the PI acknowledges them by resolving the card.
"""

from __future__ import annotations

import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from memoria.runtime.jsonl import append_jsonl
from memoria.runtime.time import now_iso
from memoria.runtime.vaultio import read_frontmatter

PUSH_LOUDNESS = frozenset({"alert", "block"})
BLOCK_LOUDNESS = "block"
OPEN_LIFECYCLE = "proposed"
PUSH_LOG_RELPATH = "system/logs/loudness-push.jsonl"
TELEGRAM_TOKEN_ENV = ("MEMORIA_TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ENV = ("MEMORIA_TELEGRAM_CHAT_ID", "TELEGRAM_CHAT_ID")
TELEGRAM_API_BASE_ENV = "MEMORIA_TELEGRAM_API_BASE"


def is_open_blocker(frontmatter: dict[str, Any]) -> bool:
    return (str(frontmatter.get("loudness") or "").lower() == BLOCK_LOUDNESS
            and str(frontmatter.get("lifecycle") or "").lower() == OPEN_LIFECYCLE)


def open_blockers(vault: Path) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    for path in sorted((vault / "inbox").glob("*.md")):
        fm = read_frontmatter(path)
        if is_open_blocker(fm):
            blockers.append({
                "path": str(path.relative_to(vault)).replace("\\", "/"),
                "title": str(fm.get("title") or path.stem),
                "type": str(fm.get("type") or "card"),
            })
    return blockers


def blocker_message(blockers: list[dict[str, str]]) -> str:
    if not blockers:
        return ""
    names = ", ".join(f"{b['path']} ({b['title']})" for b in blockers[:3])
    more = "" if len(blockers) <= 3 else f"; +{len(blockers) - 3} more"
    return f"open block-loudness card(s) require PI acknowledgement before dispatch/promotion: {names}{more}"


def should_push(loudness: str) -> bool:
    return loudness.lower() in PUSH_LOUDNESS


def _first_env(names: tuple[str, ...], env: dict[str, str]) -> str:
    for name in names:
        value = env.get(name, "").strip()
        if value:
            return value
    return ""


def _append_push_log(vault: Path, row: dict[str, Any]) -> None:
    append_jsonl(vault / PUSH_LOG_RELPATH, [row])


def push_card(vault: Path, card_path: Path, frontmatter: dict[str, Any], env: dict[str, str] | None = None) -> dict[str, Any]:
    """Push alert/block cards to Telegram when configured, and log push attempts.

    Missing Telegram config is a non-fatal `not-configured` routing record; card
    creation must never fail because the mobile push channel is absent. Quiet and
    notice cards return `pull-only` without writing the push log.
    """
    env = env or os.environ
    loudness = str(frontmatter.get("loudness") or "notice").lower()
    rel = str(card_path.relative_to(vault)).replace("\\", "/")
    row: dict[str, Any] = {
        "timestamp": now_iso(),
        "card": rel,
        "loudness": loudness,
        "title": str(frontmatter.get("title") or card_path.stem),
        "status": "pull-only",
    }
    if not should_push(loudness):
        return row

    token = _first_env(TELEGRAM_TOKEN_ENV, env)
    chat_id = _first_env(TELEGRAM_CHAT_ENV, env)
    if not (token and chat_id):
        row["status"] = "not-configured"
        _append_push_log(vault, row)
        return row

    base = env.get(TELEGRAM_API_BASE_ENV, "https://api.telegram.org").rstrip("/")
    url = f"{base}/bot{token}/sendMessage"
    text = f"Memoria {loudness}: {row['title']}\n{rel}"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
    try:
        with urllib.request.urlopen(url, data=data, timeout=5) as resp:
            row["status"] = "sent"
            row["http_status"] = getattr(resp, "status", None)
    except Exception as exc:  # Push is best-effort; the Inbox card is the durable signal.
        row["status"] = "failed"
        row["error"] = f"{type(exc).__name__}: {exc}"
    _append_push_log(vault, row)
    return row
