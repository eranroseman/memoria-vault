#!/usr/bin/env python3
"""adr-code-doctor — pin high-risk ADR mechanism claims to code evidence."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Check:
    name: str
    adr: str
    required_paths: tuple[str, ...] = ()
    required_text: tuple[str, ...] = ()
    forbidden_text: tuple[str, ...] = ()
    forbidden_regex: tuple[str, ...] = ()


CHECKS = (
    Check(
        name="ADR-128 review gate names the write mechanism, not board motion",
        adr="docs/adr/128-no-write-time-correctness-oracle.md",
        required_paths=("src/memoria_vault/runtime/policy/decision.py",),
        required_text=("src/memoria_vault/runtime/policy/decision.py", "hard stop is at the write"),
        forbidden_text=("dispatch refuses to advance a card",),
    ),
    Check(
        name="ADR-129 supersession default query filter is implemented",
        adr="docs/adr/129-layered-machine-judgment.md",
        required_paths=(
            "src/memoria_vault/runtime/search_index.py",
            "tests/test_search_index.py",
        ),
        required_text=("memoria_vault.runtime.search_index", "include_stale=True"),
    ),
    Check(
        name="ADR-130 alpha.15 direct surface is CLI/read-API, not Obsidian UI",
        adr="docs/adr/130-read-api-surfaces-and-copi.md",
        required_paths=(
            "src/memoria_vault/engine/api.py",
            "src/memoria_vault/cli.py",
            "src/memoria_vault/runtime/http_transport.py",
            "src/memoria_vault/runtime/mcp_transport.py",
        ),
        required_text=(
            "direct-access surface is the CLI plus the read-API transports",
            "needs its own ADR before it is scheduled.",
        ),
        forbidden_text=(
            "plugin's ephemeral per-launch HTTP token",
            "the plugin's backend",
            "the Obsidian Inspector's read",
            "The CLI does not count as the direct-access surface",
        ),
    ),
)


def check(root: Path) -> list[str]:
    errors: list[str] = []
    for item in CHECKS:
        adr = root / item.adr
        if not adr.is_file():
            errors.append(f"{item.name}: missing ADR file {item.adr}")
            continue
        text = adr.read_text(encoding="utf-8")
        for rel in item.required_paths:
            if not (root / rel).exists():
                errors.append(f"{item.name}: missing mechanism path {rel}")
        for needle in item.required_text:
            if needle not in text:
                errors.append(f"{item.name}: ADR missing text `{needle}`")
        for needle in item.forbidden_text:
            if needle in text:
                errors.append(f"{item.name}: ADR still contains stale text `{needle}`")
        for pattern in item.forbidden_regex:
            if re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL):
                errors.append(f"{item.name}: ADR still matches stale pattern `{pattern}`")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    errors = check(args.root)
    if errors:
        print(f"adr-code-doctor: {len(errors)} issue(s)\n")
        for error in errors:
            print(f"  ✗ {error}")
        return 1
    print(f"adr-code-doctor: clean ✓ ({len(CHECKS)} ADR mechanism check(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
