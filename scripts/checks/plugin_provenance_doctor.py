#!/usr/bin/env python3
"""Validate alpha.20 keeps plugin payloads out of the baseline package seed."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_REL = (
    Path("src/memoria_vault/product/workspace_seed/.obsidian"),
    Path("src/memoria_vault/product/workspace_seed/.memoria/plugins"),
    Path("src/memoria_vault/product/workspace_seed/system/scripts"),
    Path("src/.obsidian"),
    Path("packages/obsidian-plugin"),
    Path("tests/test_memoria_inspector.py"),
)
FORBIDDEN_GLOBS = (
    "src/**/agent_client*",
    "src/**/obsidian_adapter*",
    "src/**/obsidian_plugin*",
    "tests/**/test_*agent_client*.py",
    "tests/**/test_*obsidian_adapter*.py",
    "tests/**/test_*obsidian_plugin*.py",
)


def check(root: Path = ROOT) -> list[str]:
    root = root.resolve()
    findings: list[str] = []
    for rel in FORBIDDEN_REL:
        path = root / rel
        if path.exists():
            findings.append(f"{rel.as_posix()}: forbidden baseline-vault plugin payload")
    for pattern in FORBIDDEN_GLOBS:
        for path in sorted(root.glob(pattern)):
            if path.exists():
                findings.append(
                    f"{path.relative_to(root).as_posix()}: "
                    "Obsidian plugin or adapter implementation is excluded from core runtime"
                )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root to validate")
    args = parser.parse_args(argv)

    findings = check(args.root)
    if findings:
        print("plugin-provenance-doctor: FAIL", file=sys.stderr)
        for finding in findings:
            print(f"  - {finding}", file=sys.stderr)
        return 1
    print("plugin-provenance-doctor: clean (no forbidden Obsidian plugin payload)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
