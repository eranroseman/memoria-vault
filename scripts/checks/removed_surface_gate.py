#!/usr/bin/env python3
"""Fail when retired package/runtime surfaces reappear."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = Path(__file__).with_name("removed_surfaces.json")
SKIP_PARTS = {".git", ".venv", "__pycache__"}
SKIP_SUFFIXES = {".pyc", ".sqlite", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf"}


@dataclass(frozen=True)
class Rule:
    kind: str
    needle: str
    owner: str
    reason: str


@dataclass(frozen=True)
class Contract:
    search_roots: tuple[str, ...]
    allow_text_files: frozenset[str]
    rules: tuple[Rule, ...]


def _require_strings(data: Any, key: str) -> tuple[str, ...]:
    values = data.get(key)
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise ValueError(f"{key} must be a list of strings")
    return tuple(values)


def load_contract(path: Path = CONTRACT) -> Contract:
    data = json.loads(path.read_text(encoding="utf-8"))
    rules: list[Rule] = []
    for index, raw in enumerate(data.get("rules", []), start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"rules[{index}] must be an object")
        rule = Rule(
            kind=str(raw.get("kind", "")),
            needle=str(raw.get("needle", "")),
            owner=str(raw.get("owner", "")),
            reason=str(raw.get("reason", "")),
        )
        if rule.kind not in {"path", "text"}:
            raise ValueError(f"rules[{index}].kind must be path or text")
        if not rule.needle or not rule.owner or not rule.reason:
            raise ValueError(f"rules[{index}] must include needle, owner, and reason")
        rules.append(rule)
    return Contract(
        search_roots=_require_strings(data, "search_roots"),
        allow_text_files=frozenset(_require_strings(data, "allow_text_files")),
        rules=tuple(rules),
    )


def iter_files(repo: Path, root: Path, allow_text_files: frozenset[str]):
    if root.is_file():
        rel = root.relative_to(repo).as_posix()
        if rel not in allow_text_files:
            yield root
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(repo).as_posix()
        if rel in allow_text_files:
            continue
        if set(path.relative_to(repo).parts) & SKIP_PARTS:
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        yield path


def find_violations(repo: Path = ROOT, contract_path: Path = CONTRACT) -> list[str]:
    repo = repo.resolve()
    contract = load_contract(contract_path)
    path_rules = [rule for rule in contract.rules if rule.kind == "path"]
    text_rules = [rule for rule in contract.rules if rule.kind == "text"]
    errors: list[str] = []

    for rule in path_rules:
        if (repo / rule.needle).exists():
            errors.append(f"forbidden path exists: {rule.needle}")

    for rel in contract.search_roots:
        root = repo / rel
        if not root.exists():
            continue
        for path in iter_files(repo, root, contract.allow_text_files):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for rule in text_rules:
                if rule.needle in text:
                    errors.append(f"{path.relative_to(repo).as_posix()}: contains {rule.needle}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root to validate")
    parser.add_argument("--contract", type=Path, default=CONTRACT, help="removed-surface contract")
    args = parser.parse_args(argv)

    errors = find_violations(args.root, args.contract)
    if errors:
        print("removed-surface-gate: FAIL", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    print("removed-surface-gate: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
