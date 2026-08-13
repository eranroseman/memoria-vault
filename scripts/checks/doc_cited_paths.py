"""Fail when a published doc cites a repo path that no longer exists.

Docs name repo files as inline code -- `src/memoria_vault/cli.py`,
`scripts/verify`, `tests/test_cli.py`, `docs/reference/...`. Code moves and the
citation rots silently: nothing links the prose to the file, so the page keeps
pointing at an address that stopped existing several refactors ago.

Deliberately narrow, so the gate stays a fact check and never a style opinion:

  - Only inline code spans (single backticks) count. A fenced block shows
    commands and their output, not citations, and is exempt entirely.
  - Only the four repo roots `src/`, `scripts/`, `tests/`, `docs/` count.
    Anything else in backticks is a vault path, a config key, or prose.
  - A trailing `::symbol` is stripped first (the repo cites `file.py::function`;
    only the file part is checkable) and so is a trailing `/` (a directory
    citation). What is left must exist in the working tree -- file or directory.
  - Spans holding a space or a glob/placeholder metacharacter (`*`, `?`, `<`,
    `>`, `{`, `}`) are examples, not citations. The anchored character class
    below is what rejects them: none of those characters are in it.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS_REL = "docs"
# Working specs and plans, excluded from the published site by docs/_config.yml.
SKIP_DIRS = {"docs/superpowers"}
# Single-backtick spans only: a doubled backtick on either side is a different
# construct (a span that itself contains a backtick) and is left alone.
INLINE_CODE = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")
CITATION = re.compile(r"(?:src|scripts|tests|docs)/[A-Za-z0-9._/-]+")


@dataclass(frozen=True)
class Violation:
    file: str
    line: int
    path: str


def cited_path(span: str) -> str | None:
    """The repo path a code span cites, or None when it cites none.

    Stripping happens before matching, not after: `:` is not in the citation
    character class, so a `file.py::function` span would fail the match outright
    if it were tested verbatim.
    """
    candidate = span.split("::", 1)[0].rstrip("/")
    return candidate if CITATION.fullmatch(candidate) else None


def iter_published_docs(root: Path) -> list[Path]:
    docs = []
    for path in sorted((root / DOCS_REL).rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        if any(rel == skip or rel.startswith(skip + "/") for skip in SKIP_DIRS):
            continue
        docs.append(path)
    return docs


def page_violations(text: str, rel: str, root: Path) -> list[Violation]:
    violations: list[Violation] = []
    in_fence = False
    for line_no, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in INLINE_CODE.finditer(line):
            cited = cited_path(match.group(1))
            if cited is not None and not (root / cited).exists():
                violations.append(Violation(rel, line_no, cited))
    return violations


def find_violations(root: Path = ROOT) -> list[Violation]:
    root = Path(root).resolve()
    violations: list[Violation] = []
    for path in iter_published_docs(root):
        rel = path.relative_to(root).as_posix()
        violations.extend(page_violations(path.read_text(encoding="utf-8"), rel, root))
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root to validate")
    args = parser.parse_args(argv)

    violations = find_violations(args.root)
    if violations:
        for violation in violations:
            print(f"{violation.file}:{violation.line}: cited path does not exist: {violation.path}")
        return 1
    print("doc-cited-paths: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
