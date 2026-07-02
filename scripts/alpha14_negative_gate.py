#!/usr/bin/env python3
"""Fail when dropped alpha.14 runtime package homes reappear."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FORBIDDEN_PATHS = (
    "vault-template/.memoria/operations",
    "vault-template/.memoria/mcp",
    "vault-template/.memoria/profiles",
    "vault-template/.memoria/lane-overrides",
    "vault-template/.memoria/tool-registry.yaml",
)
FORBIDDEN_TEXT = (
    "vault-template/.memoria/operations",
    ".memoria/operations/",
    "vault-template/.memoria/mcp",
    ".memoria/mcp/",
)
SEARCH_ROOTS = (
    ".agents",
    ".github",
    ".pre-commit-config.yaml",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "docs",
    "scripts",
    "src",
    "tests",
    "vault-template",
)
SKIP_PARTS = {
    ".git",
    ".qmd",
    ".venv",
    "__pycache__",
}
SKIP_SUFFIXES = {".pyc", ".sqlite", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf"}
ALLOW_TEXT_FILES = {"scripts/alpha14_negative_gate.py"}


def iter_files(root: Path):
    if root.is_file():
        yield root
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = set(path.relative_to(ROOT).parts)
        rel = path.relative_to(ROOT).as_posix()
        if rel in ALLOW_TEXT_FILES or rel.startswith("docs/adr/"):
            continue
        if rel_parts & SKIP_PARTS:
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        yield path


def main() -> int:
    errors: list[str] = []
    for rel in FORBIDDEN_PATHS:
        if (ROOT / rel).exists():
            errors.append(f"forbidden path exists: {rel}")
    for rel in SEARCH_ROOTS:
        root = ROOT / rel
        if not root.exists():
            continue
        for path in iter_files(root):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for needle in FORBIDDEN_TEXT:
                if needle in text:
                    errors.append(f"{path.relative_to(ROOT).as_posix()}: contains {needle}")
    if errors:
        print("alpha14-negative-gate: FAIL", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    print("alpha14-negative-gate: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
