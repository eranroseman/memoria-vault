#!/usr/bin/env python3
"""Fail if checked/read-barrier wording claims approval or trust."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = ("docs", "src/memoria_vault", "scripts", "vault-template")
SKIP_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "docs/adr",
    "scratch",
    "scripts/checks/checked_terminology_gate.py",
}
SUFFIXES = {".md", ".py", ".sh", ".ps1", ".yaml", ".yml"}
BAD_WORD = r"(?:approved|approval|verified|trusted(?![- ]writer))"
PATTERNS = (
    re.compile(rf"\b(?:checked|check_status)\b.{{0,100}}\b{BAD_WORD}\b", re.I),
    re.compile(rf"\b{BAD_WORD}\b.{{0,100}}\b(?:checked|check_status)\b", re.I),
)


def _skip(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    return any(rel == part or rel.startswith(part + "/") for part in SKIP_PARTS)


def errors() -> list[str]:
    out: list[str] = []
    for root_name in SCAN_ROOTS:
        root = ROOT / root_name
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.suffix not in SUFFIXES or _skip(path):
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for line_no, line in enumerate(lines, start=1):
                if any(pattern.search(line) for pattern in PATTERNS):
                    rel = path.relative_to(ROOT).as_posix()
                    out.append(f"{rel}:{line_no}: checked must not mean approved/verified/trusted")
    return out


def main() -> int:
    findings = errors()
    if findings:
        print("checked-terminology-gate: FAIL", file=sys.stderr)
        print("\n".join(findings), file=sys.stderr)
        return 1
    print("checked-terminology-gate: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
