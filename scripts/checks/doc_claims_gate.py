"""Fail when docs cite a memoria CLI path or operation id that doesn't exist.

Checks two claim surfaces docs frequently reference verbatim:
  - `memoria <...>` CLI command paths, walked from the real argparse tree
  - `<hyphenated-id>` operation ids, read from the capability manifest roster

Deliberately narrow: this is not general prose/symbol checking (docs/explanation
and docs/how-to-guides describe behavior in ordinary sentences that this script
has no way to verify). It only catches a doc citing a CLI path or operation id
that the shipped surface does not actually have.

In the reverse direction, the two roster pages (cli.md, system-actions.md) must
list the entire shipped surface — a command or manifest the docs omit fails the
same gate.
"""

from __future__ import annotations

import argparse
import contextlib
import re
import sys
from collections.abc import Iterator
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
CLI_DOC_REL = "docs/reference/commands-and-transports/cli.md"
CLI_ROSTER_HEADING = "## Complete command roster"
OPERATIONS_DOC_REL = "docs/reference/commands-and-transports/system-actions.md"
OPERATIONS_ROSTER_HEADING = "## Operation manifest roster"
CLI_ROSTER_ENTRY = re.compile(
    r"^- `memoria ((?:[a-z][a-z0-9_-]*)(?: [a-z][a-z0-9_-]*){0,3})`$", re.MULTILINE
)


@dataclass(frozen=True)
class Violation:
    file: str
    line: int
    kind: str
    claim: str


@contextlib.contextmanager
def _importable(source_root: Path) -> Iterator[None]:
    """Put `source_root` on `sys.path` for one import, then take it back off.

    Run standalone this is cosmetic -- the process exits. Under pytest it is
    not: `tests/test_doc_claims_gate.py` calls this with a `tmp_path` holding a
    stub `memoria_vault` package (an `__init__.py` and a fixture `cli.py`, no
    submodules). A permanent insert leaves those stubs ahead of the real
    package on the worker's `sys.path` for the rest of the session. The pytest
    process never notices, because it already holds `memoria_vault` in
    `sys.modules` -- but any process it spawns afterwards starts clean, imports
    the stub, and dies on a missing submodule with no signal beyond the
    parent's queue timing out (#1613). `sys.modules` is snapshotted and cleared
    of any `memoria_vault*` entries on entry and restored verbatim on exit, so a
    `memoria_vault` already imported for real elsewhere in the same process
    (e.g. by another test module collected in the same run) never shadows the
    stub the import inside this context is meant to resolve.
    """
    entry = str(source_root)
    snapshot = {
        name: module
        for name, module in sys.modules.items()
        if name == "memoria_vault" or name.startswith("memoria_vault.")
    }
    for name in snapshot:
        del sys.modules[name]
    sys.path.insert(0, entry)
    try:
        yield
    finally:
        with contextlib.suppress(ValueError):
            sys.path.remove(entry)
        for name in [
            name
            for name in sys.modules
            if name == "memoria_vault" or name.startswith("memoria_vault.")
        ]:
            del sys.modules[name]
        sys.modules.update(snapshot)


def _load_cli_paths(root: Path) -> frozenset[str]:
    with _importable(root / "src"):
        from memoria_vault.cli import _build_parser

    def walk(parser: argparse.ArgumentParser, prefix: tuple[str, ...] = ()) -> set[str]:
        paths = {prefix} if prefix else set()
        for action in parser._actions:  # noqa: SLF001 -- argparse parser-tree introspection.
            if isinstance(action, argparse._SubParsersAction):  # noqa: SLF001 -- argparse parser-tree introspection.
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


def _roster_section(text: str, heading: str, doc_rel: str) -> str:
    try:
        start = text.index(heading)
    except ValueError:
        raise SystemExit(f"doc-claims-gate: heading {heading!r} not found in {doc_rel}") from None
    end = text.find("\n## ", start + len(heading))
    return text[start : end if end != -1 else len(text)]


def _runnable_cli_paths(root: Path) -> frozenset[str]:
    """Every path the parser will run: a handler is set, or it is a leaf.

    Group parsers (`memoria journal`, bare `memoria seed`) exist only to hold
    subcommands — required subparsers, no handler — and are not roster entries.
    """
    with _importable(root / "src"):
        from memoria_vault.cli import _build_parser

    def walk(parser: argparse.ArgumentParser, prefix: tuple[str, ...] = ()) -> set[tuple[str, ...]]:
        subparser_actions = [
            action
            for action in parser._actions  # noqa: SLF001 -- argparse parser-tree introspection.
            if isinstance(action, argparse._SubParsersAction)  # noqa: SLF001 -- argparse parser-tree introspection.
        ]
        paths: set[tuple[str, ...]] = set()
        if prefix and (parser.get_default("handler") is not None or not subparser_actions):
            paths.add(prefix)
        for action in subparser_actions:
            for name, sub in action.choices.items():
                paths |= walk(sub, (*prefix, name))
        return paths

    return frozenset(" ".join(path) for path in walk(_build_parser()))


def roster_drift_errors(root: Path = ROOT) -> list[str]:
    """The reverse direction: the two roster pages must list the whole shipped surface."""
    root = Path(root).resolve()
    errors: list[str] = []

    cli_text = (root / CLI_DOC_REL).read_text(encoding="utf-8")
    documented = frozenset(
        match.group(1)
        for match in CLI_ROSTER_ENTRY.finditer(
            _roster_section(cli_text, CLI_ROSTER_HEADING, CLI_DOC_REL)
        )
    )
    runnable = _runnable_cli_paths(root)
    for missing in sorted(runnable - documented):
        errors.append(f"{CLI_DOC_REL}: roster is missing `memoria {missing}`")
    for stale in sorted(documented - runnable):
        errors.append(
            f"{CLI_DOC_REL}: roster lists `memoria {stale}`, which the argparse tree does not run"
        )

    operations_text = (root / OPERATIONS_DOC_REL).read_text(encoding="utf-8")
    documented_ids: set[str] = set()
    operations_section = _roster_section(
        operations_text, OPERATIONS_ROSTER_HEADING, OPERATIONS_DOC_REL
    )
    for line in operations_section.splitlines():
        if line.startswith("- "):
            documented_ids.update(re.findall(r"`([a-z][a-z0-9-]*)`", line))
    shipped_ids = _load_operation_ids(root)
    for missing in sorted(shipped_ids - documented_ids):
        errors.append(f"{OPERATIONS_DOC_REL}: roster is missing `{missing}`")
    for stale in sorted(documented_ids - shipped_ids):
        errors.append(
            f"{OPERATIONS_DOC_REL}: roster lists `{stale}`, which no shipped manifest declares"
        )
    return errors


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
    drift = roster_drift_errors(args.root)
    if violations or drift:
        print("doc-claims-gate: FAIL", file=sys.stderr)
        for v in violations:
            print(
                f"  {v.file}:{v.line}: {v.kind} '{v.claim}' not found in the shipped surface",
                file=sys.stderr,
            )
        for error in drift:
            print(f"  {error}", file=sys.stderr)
        return 1
    print("doc-claims-gate: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
