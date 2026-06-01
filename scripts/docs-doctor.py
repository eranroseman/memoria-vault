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
  3. Frontmatter policy — no file carries a disallowed key (`mode:`/`audience:`
                        dropped in the refactor; `tags:` unsanctioned). Enforced on
                        docs and on the vault note templates' fenced frontmatter.
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

DROPPED_KEYS = ("mode", "audience", "tags")  # mode/audience dropped in the refactor; tags unsanctioned (use the controlled topic/methods vocabularies)

# [text](target) — but NOT images ![alt](src). Reference-style/wikilinks unused.
LINK_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)]+)\)")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]*`")
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
YAML_FENCE_RE = re.compile(r"```ya?ml\n(.*?)```", re.DOTALL)


def read(path: Path) -> str:
    # Normalize newlines so frontmatter/regex behave the same on Windows and CI.
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def check_readmes(root: Path, errors: list[str]) -> None:
    if not (root / "README.md").exists():
        errors.append(f"{root}/: missing README.md")
    for d in sorted(p for p in root.rglob("*") if p.is_dir()):
        md_files = [p for p in d.iterdir() if p.suffix == ".md" and p.name != "README.md"]
        if len(md_files) <= 1:
            continue  # single-file folders need no landing page; the file is its own landing
        if not (d / "README.md").exists():
            errors.append(f"{d}/: missing README.md (folder landing page)")


def check_thin_folders(root: Path, warnings: list[str]) -> None:
    # Advisory: flag folders thin enough to consider flattening into their parent.
    # Does not affect exit code — the human decides whether to act.
    for d in sorted(p for p in root.rglob("*") if p.is_dir()):
        md_files = [p for p in d.iterdir() if p.suffix == ".md" and p.name != "README.md"]
        has_readme = (d / "README.md").exists()
        if len(md_files) == 1 and not has_readme:
            warnings.append(f"{d}/: single-file folder (no README) — consider flattening into parent")
        elif len(md_files) == 1 and has_readme:
            warnings.append(f"{d}/: README + one file — consider flattening into parent")


def check_frontmatter(md: Path, errors: list[str]) -> None:
    m = FRONTMATTER_RE.match(read(md))
    if not m:
        return
    block = m.group(1)
    for key in DROPPED_KEYS:
        if re.search(rf"^{key}\s*:", block, re.MULTILINE):
            errors.append(f"{md}: frontmatter carries disallowed key '{key}:' (mode/audience dropped; tags unsanctioned)")
    # Unquoted colon-space in a scalar value breaks Jekyll's YAML loader, which
    # silently drops the page from the nav (it parses as a nested mapping).
    # e.g.  title: Linter: detectors  →  must be  title: "Linter: detectors"
    for ln in block.split("\n"):
        m2 = re.match(r"^(\w[\w-]*):\s+(.*)$", ln)
        if not m2:
            continue
        value = m2.group(2).strip()
        if value.startswith(('"', "'")):
            continue  # already quoted — safe
        if re.search(r":\s", value):
            errors.append(
                f"{md}: frontmatter value for '{m2.group(1)}:' contains an unquoted "
                f"colon — quote it (\"{value}\") or Jekyll drops the page from the nav"
            )


_slug_cache: dict[Path, set[str]] = {}


def gh_slug(text: str) -> str:
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # link -> label
    text = text.replace("`", "").strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s", "-", text)
    return text


ID_ATTR_RE = re.compile(r"""<[a-zA-Z][^>]*\bid\s*=\s*["']([^"']+)["']""")


def heading_slugs(path: Path) -> set[str]:
    if path not in _slug_cache:
        s: set[str] = set()
        try:
            content = read(path)
            for ln in content.split("\n"):
                m = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", ln)
                if m:
                    s.add(gh_slug(m.group(1)))
            # Explicit HTML anchors. GitHub honors <a id="x"> (and any id= attribute)
            # as a #x link target, so a doc that gives list items per-entry anchors
            # — e.g. the bibliography's one-<a id>-per-reference — links correctly.
            # The slug is the literal id value, not gh_slug'd.
            s.update(ID_ATTR_RE.findall(content))
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


def check_template_frontmatter(md: Path, errors: list[str]) -> None:
    # A note template documents its frontmatter inside a ```yaml fence rather than as
    # the file's own leading frontmatter, so check_frontmatter (leading-only) misses
    # it. Scan the fenced YAML for disallowed keys — a banned key here propagates to
    # every note created from the template.
    for block in YAML_FENCE_RE.findall(read(md)):
        for key in DROPPED_KEYS:
            if re.search(rf"^\s*{key}\s*:", block, re.MULTILINE):
                errors.append(f"{md}: template frontmatter carries disallowed key '{key}:' (mode/audience dropped; tags unsanctioned)")


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
    warnings: list[str] = []
    doc_md_names = {p.name.lower() for p in root.rglob("*.md")}
    check_readmes(root, errors)
    check_thin_folders(root, warnings)
    for md in sorted(root.rglob("*.md")):
        check_frontmatter(md, errors)
        check_links(md, errors)
        check_wikilinks(md, errors, doc_md_names)

    # Guard the vault note templates too: their frontmatter lives in a ```yaml fence,
    # and a banned key there propagates to every note created from the template.
    tmpl_dir = root.parent / "vault" / "00-meta" / "03-templates"
    if tmpl_dir.is_dir():
        for md in sorted(tmpl_dir.glob("*.md")):
            check_template_frontmatter(md, errors)

    if errors:
        print(f"docs-doctor: {len(errors)} issue(s)\n")
        for e in errors:
            print(f"  ✗ {e}")
    else:
        print("docs-doctor: clean ✓")

    if warnings:
        print(f"\ndocs-doctor: {len(warnings)} advisory warning(s)")
        for w in warnings:
            print(f"  ⚠ {w}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
