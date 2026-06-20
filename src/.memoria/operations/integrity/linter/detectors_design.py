#!/usr/bin/env python3
"""Design-system detector family for the Memoria Linter."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

SKIP_DIRS = {".obsidian", ".git", ".memoria", "node_modules"}
_HEX_COLOR = re.compile(r"#[0-9A-Fa-f]{3,8}\b")
_PX_VALUE = re.compile(r"font(?:-size)?\s*:[^;\n]*?\b(\d+(?:\.\d+)?)px\b", re.I)
_CALLOUT_LINE = re.compile(r"^\s*>\s*\[!([^\]|\n]+)(?:\|([^\]\n]+))?\]", re.I | re.M)
_BANNED_TITLE_CHARS = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")
_TERM_DRIFT = re.compile(
    r"\b(?:Claim Note|claimnote|Paper Note|paper note|permanent note|knowledge base)\b"
)
_DESIGN_SCAN_PREFIXES = (
    "home.md",
    "research-focus.md",
    "troubleshooting.md",
    "AGENTS.md",
    "system/",
    "notes/",
    "catalog/",
    "inbox/",
    "projects/",
    "spaces/",
    ".obsidian/snippets/",
)
_DESIGN_SCAN_SUFFIXES = (".md", ".css", ".html")
_ALLOWED_CALLOUTS = {"brief", "suggestions", "verification"}


@dataclass
class Finding:
    detector: str
    severity: str
    path: str
    message: str
    timestamp: str = ""


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ""


def relpath(vault: Path, p: Path) -> str:
    return p.relative_to(vault).as_posix()


def iter_files(vault: Path):
    for dirpath, dirnames, filenames in os.walk(vault):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in sorted(filenames):
            yield Path(dirpath) / name


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    try:
        import yaml

        data = yaml.safe_load(text[3:end])
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _design_spec(vault: Path) -> str:
    return read(vault / ".memoria" / "design-system.md")


def _hex_colors(text: str) -> set[str]:
    colors = set()
    for m in _HEX_COLOR.finditer(text):
        color = m.group(0).lower()
        if len(color) == 4 and color[1:].isdigit():
            continue
        colors.add(color)
    return colors


def _allowed_design_colors(spec: str) -> set[str]:
    return _hex_colors(spec)


def _px_number(value: str) -> str:
    number = float(value)
    return str(int(number)) if number.is_integer() else str(number)


def _allowed_font_sizes(spec: str) -> set[str]:
    return {_px_number(m.group(1)) for m in re.finditer(r"\b(\d+(?:\.\d+)?)px\s*/", spec)}


def _design_consumer_files(vault: Path):
    for p in iter_files(vault):
        rp = relpath(vault, p)
        if not rp.endswith(_DESIGN_SCAN_SUFFIXES):
            continue
        if rp.startswith(("system/logs/", "system/board/")):
            continue
        if any(rp == prefix or rp.startswith(prefix) for prefix in _DESIGN_SCAN_PREFIXES):
            yield p, rp
    snippets = vault / ".obsidian" / "snippets"
    if snippets.is_dir():
        for p in sorted(snippets.rglob("*.css")):
            yield p, relpath(vault, p)


def _has_frontmatter_title_emoji(text: str) -> bool:
    fm = parse_frontmatter(text)
    for key in ("title", "name"):
        value = fm.get(key)
        if isinstance(value, str) and _BANNED_TITLE_CHARS.search(value):
            return True
    return False


def design_system_drift(vault: Path) -> list[Finding]:
    """Report visual-style drift against `.memoria/design-system.md`."""
    spec = _design_spec(vault)
    if not spec:
        return []
    allowed_colors = _allowed_design_colors(spec)
    allowed_sizes = _allowed_font_sizes(spec)
    out: list[Finding] = []
    for p, rp in _design_consumer_files(vault):
        text = read(p)
        if not text:
            continue
        for color in sorted(_hex_colors(text)):
            if color not in allowed_colors:
                out.append(
                    Finding(
                        "design-system-drift",
                        "MEDIUM",
                        rp,
                        f"off-palette color {color} not declared in .memoria/design-system.md",
                    )
                )
        for size in {m.group(1) for m in _PX_VALUE.finditer(text)}:
            canonical = _px_number(size)
            if allowed_sizes and canonical not in allowed_sizes:
                out.append(
                    Finding(
                        "design-system-drift",
                        "MEDIUM",
                        rp,
                        f"font-size {size}px is outside the design-system scale",
                    )
                )
        title_has_emoji = _BANNED_TITLE_CHARS.search(Path(rp).stem) or _has_frontmatter_title_emoji(
            text
        )
        if title_has_emoji:
            out.append(
                Finding(
                    "design-system-drift",
                    "LOW",
                    rp,
                    "emoji in note title or filename; keep emoji in the body, not titles",
                )
            )
        for callout, variant in _CALLOUT_LINE.findall(text):
            c = callout.strip().lower()
            v = variant.strip().lower()
            if c in _ALLOWED_CALLOUTS and not v:
                continue
            out.append(
                Finding(
                    "design-system-drift",
                    "LOW",
                    rp,
                    f"rainbow/ad-hoc callout [!{callout}{'|' + variant if variant else ''}] "
                    "outside the fixed Memoria callout palette",
                )
            )
        term = _TERM_DRIFT.search(text)
        if term:
            out.append(
                Finding(
                    "design-system-drift",
                    "LOW",
                    rp,
                    f"terminology/capitalization drift: use design-system term instead of {term.group(0)!r}",
                )
            )
    return out
