#!/usr/bin/env python3
"""Validate that alpha.15 ships no Obsidian plugin implementation payload."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FORBIDDEN_REL = (
    Path("vault-template/.obsidian"),
    Path("vault-template/system/scripts"),
    Path("src/.obsidian"),
    Path("packages/obsidian-plugin"),
    Path("packages/memoria-obsidian"),
    Path("tests/test_memoria_inspector.py"),
)


@dataclass(frozen=True)
class Finding:
    path: str
    message: str

    def format(self) -> str:
        return f"{self.path}: {self.message}"


def check(root: Path = ROOT) -> list[Finding]:
    root = root.resolve()
    findings: list[Finding] = []
    for rel in FORBIDDEN_REL:
        path = root / rel
        if path.exists():
            findings.append(Finding(rel.as_posix(), "not shipped in alpha.15"))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root to validate")
    args = parser.parse_args(argv)

    findings = check(args.root)
    if findings:
        print("plugin-provenance-doctor: FAIL", file=sys.stderr)
        for finding in findings:
            print(f"  - {finding.format()}", file=sys.stderr)
        return 1
    print("plugin-provenance-doctor: clean (no Obsidian plugin implementation payload)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
