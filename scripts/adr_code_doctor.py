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
        name="ADR-55 golden restore has no shipped upgrade command",
        adr="docs/adr/55-src-scaffold-populate-golden-copy.md",
        required_paths=(
            "vault-template/.memoria/operations/integrity/linter/golden_restore.py",
            "tests/test_golden_restore.py",
        ),
        required_text=(
            "test_upgrade_command_is_not_shipped",
            "There is no shipped in-place release-upgrade reconcile",
        ),
        forbidden_text=("golden_restore.py upgrade --source",),
        forbidden_regex=(r"three-way\s+reconcile\s+in\s+`golden_restore\.py\s+upgrade",),
    ),
    Check(
        name="ADR-41 review gate names the write mechanism, not board motion",
        adr="docs/adr/41-configurable-review-gate-mode.md",
        required_paths=("src/memoria_vault/runtime/policy/decision.py",),
        required_text=("src/memoria_vault/runtime/policy/decision.py", "hard stop is at the write"),
        forbidden_text=(
            "dispatch refuses to advance a card",
            "vault-template/.memoria/mcp/decision.py",
        ),
    ),
    Check(
        name="ADR-76 policy core path matches the package root",
        adr="docs/adr/76-versioned-vault-release-reconciling-installer.md",
        required_paths=(
            "src/memoria_vault/runtime/policy/__init__.py",
            "src/memoria_vault/runtime/policy/decision.py",
        ),
        required_text=("src/memoria_vault/runtime/policy/",),
        forbidden_text=("vault-template/.memoria/memoria_runtime/policy/",),
    ),
    Check(
        name="ADR-10 supersession default query filter is implemented",
        adr="docs/adr/10-claim-supersession.md",
        required_paths=(
            "vault-template/.memoria/mcp/qmd_filter_mcp.py",
            "tests/test_qmd_filter_mcp.py",
        ),
        required_text=("qmd_filter_mcp.py", "include_superseded: true"),
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
