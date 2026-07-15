#!/usr/bin/env python3
"""Fail when docs cite a memoria CLI path or operation id that doesn't exist.

Checks two claim surfaces docs frequently reference verbatim:
  - `memoria <...>` CLI command paths, walked from the real argparse tree
  - `<hyphenated-id>` operation ids, read from the capability manifest roster

Deliberately narrow: this is not general prose/symbol checking (docs/explanation
and docs/how-to-guides describe behavior in ordinary sentences that this script
has no way to verify). It only catches a doc citing a CLI path or operation id
that the shipped surface does not actually have.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP_DIRS = {"docs/superpowers", "design-history/archive"}
CLI_PATTERN = re.compile(r"`memoria((?: [a-z][a-z0-9_-]*){1,3})`")
# Only counts as an operation-id claim when "operation" sits immediately
# before the backticked id -- the doc corpus's actual citation convention
# (e.g. "worker operation `create-concept`"). A bare hyphenated backticked
# token elsewhere on the line is commonly a check name, journal-event name,
# or enum value, not an operation-id claim.
OPERATION_ID_PATTERN = re.compile(r"operation `([a-z][a-z0-9]*(?:-[a-z][a-z0-9]*){1,5})`")


@dataclass(frozen=True)
class Violation:
    file: str
    line: int
    kind: str
    claim: str


def _load_cli_paths(root: Path) -> frozenset[str]:
    sys.path.insert(0, str(root / "src"))
    from memoria_vault.cli import _build_parser

    def walk(parser: argparse.ArgumentParser, prefix: tuple[str, ...] = ()) -> set[str]:
        paths = {prefix} if prefix else set()
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                for name, sub in action.choices.items():
                    paths |= walk(sub, (*prefix, name))
        return paths

    return frozenset(" ".join(path) for path in walk(_build_parser()))


def _load_operation_ids(root: Path) -> frozenset[str]:
    operations_dir = root / "src/memoria_vault/product/capabilities/operations"
    ids = set()
    for path in sorted(operations_dir.glob("*.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("operation_id:"):
                ids.add(line.split(":", 1)[1].strip())
                break
    return frozenset(ids)


def _iter_docs(root: Path) -> list[Path]:
    docs = []
    for path in sorted((root / "docs").rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        if any(rel == skip or rel.startswith(skip + "/") for skip in SKIP_DIRS):
            continue
        docs.append(path)
    return docs


def find_violations(root: Path = ROOT) -> list[Violation]:
    root = Path(root).resolve()
    cli_paths = _load_cli_paths(root)
    operation_ids = _load_operation_ids(root)
    violations: list[Violation] = []

    for path in _iter_docs(root):
        rel = path.relative_to(root).as_posix()
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for match in CLI_PATTERN.finditer(line):
                claim = match.group(1).strip()
                if claim not in cli_paths:
                    violations.append(Violation(rel, line_no, "cli-path", f"memoria {claim}"))
            for match in OPERATION_ID_PATTERN.finditer(line):
                claim = match.group(1)
                if claim not in operation_ids:
                    violations.append(Violation(rel, line_no, "operation-id", claim))
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root to validate")
    args = parser.parse_args(argv)

    violations = find_violations(args.root)
    if violations:
        print("doc-claims-gate: FAIL", file=sys.stderr)
        for v in violations:
            print(
                f"  {v.file}:{v.line}: {v.kind} '{v.claim}' not found in the shipped surface",
                file=sys.stderr,
            )
        return 1
    print("doc-claims-gate: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
