#!/usr/bin/env python3
"""docs-doctor — structural linter for the Memoria docs/ tree.

Enforces the conventions from the mode-first refactor plan. These are all
*structural* checks; classifying a file by reading mode is a human concern and
deliberately out of scope (a linter cannot tell reference from explanation).

Checks:
  1. README presence  — every directory under docs/ has a README.md
                        (GitHub renders it as the folder's landing page).
  2. Link integrity   — every relative Markdown link resolves to a real file,
                        and every #anchor resolves to a heading in the target
                        (GitHub does not auto-heal links when files move).
  3. Frontmatter policy — no file still carries a dropped key (`mode:`, `audience:`).
  4. No wikilinks     — a [[wikilink]] that resolves to a docs file must be a
                        relative Markdown link (GitHub does not render wikilinks).

Exit 0 if clean, 1 if any error.
Usage: python scripts/docs-doctor.py [docs_root]   (default: docs)

One script, two triggers: run locally (pre-commit) and in CI (GitHub Actions).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

DROPPED_KEYS = ("mode", "audience")

# [text](target) — but NOT images ![alt](src). Reference-style/wikilinks unused.
LINK_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)]+)\)")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]*`")
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def read(path: Path) -> str:
    # Normalize newlines so frontmatter/regex behave the same on Windows and CI.
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def check_readmes(root: Path, errors: list[str]) -> None:
    if not (root / "README.md").exists():
        errors.append(f"{root}/: missing README.md")
    for d in sorted(p for p in root.rglob("*") if p.is_dir()):
        if not (d / "README.md").exists():
            errors.append(f"{d}/: missing README.md (folder landing page)")


def check_frontmatter(md: Path, errors: list[str]) -> None:
    m = FRONTMATTER_RE.match(read(md))
    if not m:
        return
    block = m.group(1)
    for key in DROPPED_KEYS:
        if re.search(rf"^{key}\s*:", block, re.MULTILINE):
            errors.append(f"{md}: frontmatter still carries dropped key '{key}:'")


_slug_cache: dict[Path, set[str]] = {}


def gh_slug(text: str) -> str:
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # link -> label
    text = text.replace("`", "").strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s", "-", text)
    return text


def heading_slugs(path: Path) -> set[str]:
    if path not in _slug_cache:
        s: set[str] = set()
        try:
            for ln in read(path).split("\n"):
                m = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", ln)
                if m:
                    s.add(gh_slug(m.group(1)))
        except OSError:
            pass
        _slug_cache[path] = s
    return _slug_cache[path]


def check_links(md: Path, errors: list[str]) -> None:
    text = read(md)
    text = FENCE_RE.sub("", text)       # ignore fenced code blocks
    text = INLINE_CODE_RE.sub("", text)  # ignore inline code
    for raw in LINK_RE.findall(text):
        target = raw.strip()
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        # same-file anchor
        if target.startswith("#"):
            anchor = target[1:].strip()
            if anchor and anchor not in heading_slugs(md):
                errors.append(f"{md}: broken anchor -> {target}")
            continue
        head, _, frag = target.partition("#")
        path_part = re.split(r"\s+", head.strip())[0]
        anchor = frag.split()[0] if frag.strip() else ""  # drop optional "title"
        if not path_part:
            continue
        tgt = (md.parent / path_part).resolve()
        if not tgt.exists():
            errors.append(f"{md}: broken relative link -> {target}")
            continue
        if anchor and tgt.suffix == ".md" and anchor not in heading_slugs(tgt):
            errors.append(f"{md}: broken anchor -> {target}")


def check_wikilinks(md: Path, errors: list[str], doc_md_names: set[str]) -> None:
    # Docs render on GitHub, where [[wikilinks]] do not resolve; the convention is
    # "relative Markdown links only." Flag a wikilink only when it resolves to a real
    # docs file (the signature of a cross-link that should be Markdown) — illustrative
    # tokens like [[citekey]] that match no doc are vault-syntax examples, left alone.
    text = read(md)
    text = FENCE_RE.sub("", text)
    text = INLINE_CODE_RE.sub("", text)
    for inner in WIKILINK_RE.findall(text):
        base = re.split(r"[|#]", inner)[0].strip().split("/")[-1]
        name = base if base.endswith(".md") else base + ".md"
        if name.lower() in doc_md_names:
            errors.append(f"{md}: wikilink [[{inner}]] -> use a relative Markdown link to {name}")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "docs")
    if not root.is_dir():
        print(f"docs-doctor: root '{root}' not found", file=sys.stderr)
        return 1

    errors: list[str] = []
    doc_md_names = {p.name.lower() for p in root.rglob("*.md")}
    check_readmes(root, errors)
    for md in sorted(root.rglob("*.md")):
        check_frontmatter(md, errors)
        check_links(md, errors)
        check_wikilinks(md, errors, doc_md_names)

    if errors:
        print(f"docs-doctor: {len(errors)} issue(s)\n")
        for e in errors:
            print(f"  ✗ {e}")
        return 1
    print("docs-doctor: clean ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
