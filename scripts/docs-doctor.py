#!/usr/bin/env python3
"""docs-doctor — structural linter for the Memoria docs/ tree (+ src/ link text).

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
  5. Link text        — across docs/ AND src/, a link's visible text must be the
                        target's page title, not its filename; bare [[wikilinks]] in
                        vault notes must be aliased with the title.
  6. Vault wikilinks  — a vault [[note]]/[[note|alias]] must resolve to an existing
                        vault note (an aliased link to a missing note is otherwise
                        silent).

Exit 0 if clean, 1 if any error.
Usage: python scripts/docs-doctor.py [docs_root]   (default: docs)

One script, two triggers: run locally (pre-commit) and in CI (GitHub Actions).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

DROPPED_KEYS = ("mode", "audience", "tags")  # mode/audience dropped in the refactor; tags unsanctioned (use the controlled topic/methods vocabularies)

# Scratch dirs: tracked in git so relative links resolve, but excluded from the
# published site (docs/_config.yml) and skipped by these structural checks —
# planning notes / generated reports under a tmp/ folder are not held to the
# published-docs bar.
SCRATCH_DIRS = {"tmp"}

# docs/ dirs kept in the repo for relative linking / github.com browsing but NOT
# published to the Jekyll site (docs/_config.yml `exclude:`). A page in one of these
# is read on github.com, where a relative link out to src/ still resolves — so the
# "stay inside the site" rule below applies only to *published* pages.
SITE_EXCLUDED_DIRS = {"contributing", "releasing", "testing"}


def _scratch(p: Path, base: Path) -> bool:
    # Match a scratch dir only *within* the scanned tree, not the absolute path — so a
    # repo checked out under /tmp (or a pytest tmp_path root) is not wholesale excluded.
    return any(part in SCRATCH_DIRS for part in p.relative_to(base).parts)


def _published(md: Path, root: Path) -> bool:
    # True if this docs page is part of the published GitHub Pages site. Pages under a
    # site-excluded dir or a scratch/tmp dir are repo-internal (read on github.com,
    # not the built site), so their out-of-site relative links are intentional.
    parts = set(md.relative_to(root).parts)
    return not (parts & SITE_EXCLUDED_DIRS) and not _scratch(md, root)

# [text](target) — but NOT images ![alt](src). Reference-style/wikilinks unused.
LINK_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)]+)\)")
LINK_TEXT_RE = re.compile(r"(?<!\!)\[([^\]]*)\]\(([^)]+)\)")  # captures (text, target)
PAGES_URL = "https://eranroseman.github.io/memoria-vault"
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
    for d in sorted(p for p in root.rglob("*") if p.is_dir() and not _scratch(p, root)):
        md_files = [p for p in d.iterdir() if p.suffix == ".md" and p.name != "README.md"]
        if len(md_files) <= 1:
            continue  # single-file folders need no landing page; the file is its own landing
        if not (d / "README.md").exists():
            errors.append(f"{d}/: missing README.md (folder landing page)")


def check_thin_folders(root: Path, warnings: list[str]) -> None:
    # Advisory: flag folders thin enough to consider flattening into their parent.
    # Does not affect exit code — the human decides whether to act.
    for d in sorted(p for p in root.rglob("*") if p.is_dir() and not _scratch(p, root)):
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
        if "{{" in target:
            continue  # template placeholder (e.g. release-plan-template `{{ #NN }}`), not a real link
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


def _link_is_internal(target: str) -> bool:
    t = target.strip().split()[0]
    return t.startswith(PAGES_URL) or not t.startswith(("http://", "https://", "mailto:"))


def check_link_text(md: Path, errors: list[str]) -> None:
    # A link's visible text must be the target's page title, not its filename. Flag text
    # that restates the target's own filename/stem (internal targets only) — prose with a
    # stray hyphen/slash and external links are left alone.
    text = INLINE_CODE_RE.sub("", FENCE_RE.sub("", read(md)))
    for label, target in LINK_TEXT_RE.findall(text):
        lbl = label.strip().rstrip("/")
        if not lbl or not _link_is_internal(target):
            continue
        if lbl.endswith(".md"):
            errors.append(f"{md}: link text '{label.strip()}' is a filename — use the target's page title")
            continue
        t = target.strip().split()[0].split("#")[0].rstrip("/")
        base = t.split("/")[-1]
        stem = base[:-3] if base.endswith(".md") else base
        if lbl == base or lbl == stem:
            errors.append(f"{md}: link text '{label.strip()}' restates the filename — use the target's page title")


def check_wikilink_aliases(md: Path, errors: list[str]) -> None:
    # Vault only: a bare [[note]] renders the kebab filename; require [[note|Page Title]].
    text = INLINE_CODE_RE.sub("", FENCE_RE.sub("", read(md)))
    for inner in WIKILINK_RE.findall(text):
        clean = inner.replace("\\|", "|")
        if "|" in clean:
            continue
        tgt = clean.split("#")[0].strip()
        if "." in tgt.split("/")[-1] and not tgt.endswith(".md"):
            continue  # non-note target (.base/.canvas/image embed) — not a note wikilink
        if tgt:
            errors.append(f"{md}: bare wikilink [[{inner}]] shows the filename — alias it with the page title ([[{tgt}|…]])")


def check_broken_vault_wikilinks(md: Path, errors: list[str], vault_stems: set[str]) -> None:
    # Vault only: a [[note]]/[[note|alias]] must resolve to an existing vault note.
    # check_wikilink_aliases catches a *missing alias*, but an aliased link to a
    # missing note ([[ghost|Title]]) passes it silently — this closes that gap,
    # mirroring the Linter's broken_wikilinks detector. Asset paths are not notes.
    text = INLINE_CODE_RE.sub("", FENCE_RE.sub("", read(md)))
    for inner in WIKILINK_RE.findall(text):
        tgt = inner.replace("\\|", "|").split("|")[0].split("#")[0].strip().rstrip("\\")
        if not tgt or tgt.startswith("system/extracts/"):
            continue
        if "." in tgt.split("/")[-1] and not tgt.endswith(".md"):
            continue  # non-note target (.base/.canvas/image embed)
        if Path(tgt).stem.lower() not in vault_stems:
            errors.append(f"{md}: wikilink [[{inner}]] resolves to no vault note")


def check_site_local_links(md: Path, root: Path, warnings: list[str]) -> None:
    # A *published* docs page must not link to a file outside the published site (docs/).
    # The recurring case is a relative link into src/: it resolves on disk and on
    # github.com, but src/ is a sibling of docs/ and is NOT part of the Jekyll site
    # (docs/_config.yml), so the link 404s on the live site at *any* path depth — fixing
    # the number of ../ never helps. Use inline code for a source path (`src/…`), or an
    # absolute github.com/eranroseman/memoria-vault/blob/main/… URL when a click is
    # genuinely wanted. Advisory for now; promote to an error once the existing links
    # are swept, to stop the rule from regressing.
    if not _published(md, root):
        return
    site = root.resolve()
    text = INLINE_CODE_RE.sub("", FENCE_RE.sub("", read(md)))
    for raw in LINK_RE.findall(text):
        target = raw.strip()
        if target.startswith(("http://", "https://", "mailto:", "#")) or "{{" in target:
            continue
        path_part = re.split(r"\s+", target.partition("#")[0].strip())[0]
        if not path_part:
            continue
        tgt = (md.parent / path_part).resolve()
        try:
            tgt.relative_to(site)
        except ValueError:
            warnings.append(
                f"{md}: relative link '{path_part}' leaves the published site (docs/) — "
                f"src/ is not on the Jekyll site; use inline code or an absolute github.com blob URL"
            )


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
    doc_md_names = {p.name.lower() for p in root.rglob("*.md") if not _scratch(p, root)}
    check_readmes(root, errors)
    check_thin_folders(root, warnings)
    for md in sorted(p for p in root.rglob("*.md") if not _scratch(p, root)):
        check_frontmatter(md, errors)
        check_links(md, errors)
        check_site_local_links(md, root, warnings)
        check_wikilinks(md, errors, doc_md_names)
        check_link_text(md, errors)

    # Guard the vault note templates too: their frontmatter lives in a ```yaml fence,
    # and a banned key there propagates to every note created from the template.
    tmpl_dir = root.parent / "src" / "system" / "templates"
    if tmpl_dir.is_dir():
        for md in sorted(tmpl_dir.glob("*.md")):
            check_template_frontmatter(md, errors)

    # Link-text discipline extends to the vault notes: cross-links must use the page
    # title — markdown link text and wikilink aliases — never the bare filename.
    vault = root.parent / "src"
    if vault.is_dir():
        vault_stems = {p.stem.lower() for p in vault.rglob("*.md") if ".obsidian" not in p.parts and not _scratch(p, vault)}
        for md in sorted(vault.rglob("*.md")):
            if ".obsidian" in md.parts or "templates" in md.parts or _scratch(md, vault):
                continue
            check_link_text(md, errors)
            check_wikilink_aliases(md, errors)
            check_broken_vault_wikilinks(md, errors, vault_stems)

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
