#!/usr/bin/env python3
"""Fail when a published docs page links somewhere that isn't real or isn't published.

`jekyll-relative-links` rewrites `foo.md` links into site routes but never
checks that anything is there; CONTRIBUTING's authoring conventions state the
topology in prose ("inside `docs/`, use relative links following the target's
Pages route... Never relative-link into `src/`"). This gate mechanizes that:

  - absolute URLs (`http`, `https`, `mailto`) are somebody else's problem
  - an absolute filesystem path is always wrong -- it is not a Pages route
  - a relative target must exist, and must land inside the published set
    (unpublished targets -- root files, `design-history/`, `src/` -- get a
    GitHub blob URL instead, which the first rule already permits)
  - a `#fragment` must match a heading or an explicit HTML anchor

Anchors are matched tolerantly: both kramdown-style and GitHub-style slugs are
computed for every heading and either may match, so a slug-algorithm edge case
cannot fail a link that the real site serves.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

CONFIG_NAME = "_config.yml"

# The link's target only. The corpus wraps long links so that `](target)` can
# start a line with its `[text` on the previous one -- matching the whole
# `[text](target)` form would skip those.
LINK = re.compile(r"\]\(([^)\s]*)(?:\s+\"[^\"]*\")?\)")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$")
# Kramdown's explicit header id: `### Name {#custom-id}` (or the IAL spelling,
# `{: #custom-id}`). It replaces the generated slug, so the id is authoritative.
HEADER_ID = re.compile(r"\s*\{:?\s*#([\w-]+)[^}]*\}$")
HTML_ANCHOR = re.compile(r"""<[^>]*\b(?:id|name)\s*=\s*["']([^"']+)["']""")
EXTERNAL = ("http://", "https://", "mailto:")
INDEX_NAMES = ("README.md", "index.md")


def unpublished_dirs(docs_dir: Path) -> frozenset[str]:
    """Directory names `docs/_config.yml` keeps off the site.

    Read rather than restated: the exclude list grows (`agents/` arrived after
    this gate was written), and a stale copy here would keep passing links to
    pages that 404. Entries are Jekyll globs -- `superpowers/`, `**/tmp/` --
    and only their directory name matters for this check.
    """
    config = docs_dir / CONFIG_NAME
    if not config.is_file():
        return frozenset()
    parsed = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
    excluded = parsed.get("exclude") or []
    return frozenset(entry.strip("/").removeprefix("**/") for entry in excluded if "." not in entry)


def published_pages(docs_dir: Path) -> list[Path]:
    """Every markdown page the site actually publishes, in a stable order."""
    unpublished = unpublished_dirs(docs_dir)
    return [
        path
        for path in sorted(docs_dir.rglob("*.md"))
        if not unpublished.intersection(path.relative_to(docs_dir).parts[:-1])
    ]


def anchor_definitions(text: str) -> set[str]:
    """Every fragment this page answers to: heading slugs plus explicit HTML ids.

    Both slug dialects are emitted for each heading (see `slug_candidates`), and
    `<a id="...">` counts because the bibliography's citation anchors are a
    documented convention rather than generated ids.
    """
    anchors: set[str] = set()
    for line in _uncoded_lines(text):
        heading = HEADING.match(line)
        if heading:
            title = heading.group(1)
            explicit = HEADER_ID.search(title)
            if explicit:
                anchors.add(explicit.group(1).lower())
                title = title[: explicit.start()]
            anchors |= slug_candidates(title)
        anchors.update(anchor.lower() for anchor in HTML_ANCHOR.findall(line))
    return anchors


def slug_candidates(heading: str) -> set[str]:
    """Kramdown- and GitHub-style slugs for one heading, plus collapsed variants.

    GitHub drops punctuation and keeps the resulting double hyphens ("A -- B"
    becomes `a----b`); kramdown additionally strips leading non-letters. Rather
    than bet on one dialect, offer all of them and let any one match.
    """
    text = heading.replace("`", "")
    github = re.sub(r"[^\w\- ]", "", text).strip().lower().replace(" ", "-")
    kramdown = re.sub(r"^[^a-zA-Z]+", "", text)
    kramdown = re.sub(r"[^a-zA-Z0-9 -]", "", kramdown).strip().lower().replace(" ", "-")
    candidates = {github, kramdown}
    candidates |= {re.sub(r"-{2,}", "-", slug).strip("-") for slug in candidates}
    return {slug for slug in candidates if slug}


def check_doc_links(docs_dir: Path) -> list[str]:
    docs_dir = docs_dir.resolve()
    unpublished = unpublished_dirs(docs_dir)
    anchors: dict[Path, set[str]] = {}
    errors: list[str] = []
    for page in published_pages(docs_dir):
        text = page.read_text(encoding="utf-8")
        for line_no, line in enumerate(_uncoded_lines(text), start=1):
            for match in LINK.finditer(line):
                error = _target_error(match.group(1), page, docs_dir, anchors, unpublished)
                if error:
                    errors.append(f"{_rel(page, docs_dir)}:{line_no}: {error}")
    return errors


def _target_error(
    target: str,
    page: Path,
    docs_dir: Path,
    anchors: dict[Path, set[str]],
    unpublished: frozenset[str],
) -> str | None:
    if target.startswith(EXTERNAL):
        return None
    if target.startswith("/"):
        return f"absolute filesystem path: {target!r} -- use a relative link or a full URL"
    path_part, _, fragment = target.partition("#")
    if not path_part and not fragment:
        return f"empty link target: {target!r}"

    resolved = page
    if path_part:
        resolved = Path(os.path.normpath(page.parent / path_part))
        if not _inside(resolved, docs_dir):
            return f"link target leaves docs/: {target!r}"
        if unpublished.intersection(resolved.relative_to(docs_dir).parts):
            return f"link target is not published: {target!r}"
        if resolved.is_dir():
            resolved = _index_page(resolved) or resolved
        if not resolved.is_file():
            return f"link target does not exist: {target!r}"

    if not fragment or resolved.suffix != ".md":
        return None
    if resolved not in anchors:
        anchors[resolved] = anchor_definitions(resolved.read_text(encoding="utf-8"))
    if fragment.lower() not in anchors[resolved]:
        return f"no heading or anchor {fragment!r} in {_rel(resolved, docs_dir)}"
    return None


def _index_page(directory: Path) -> Path | None:
    """A directory target is a section route; the site serves its index page."""
    return next((directory / name for name in INDEX_NAMES if (directory / name).is_file()), None)


def _uncoded_lines(text: str) -> list[str]:
    """The text with fenced code blocks blanked out, line numbering preserved.

    Blanking rather than dropping keeps every line's index, so reported line
    numbers stay true, and it makes fences opaque to both readers here: a
    `[link](gone.md)` in a sample is not a link, and a `# comment` in a shell
    block is not a heading.
    """
    lines = []
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            lines.append("")
            continue
        lines.append("" if fenced else line)
    return lines


def _inside(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def _rel(path: Path, docs_dir: Path) -> str:
    return path.relative_to(docs_dir.parent).as_posix()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", type=Path, default=ROOT / "docs")
    args = parser.parse_args(argv)

    errors = check_doc_links(args.docs)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("doc-link-targets: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
