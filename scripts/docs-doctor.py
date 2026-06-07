#!/usr/bin/env python3
"""docs-doctor — structural linter for the Memoria docs/ tree (+ vault/ link text).

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
  5. Link text        — across docs/ AND vault/, a link's visible text must be the
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
        if not tgt or tgt.startswith("90-assets/"):
            continue
        if Path(tgt).stem.lower() not in vault_stems:
            errors.append(f"{md}: wikilink [[{inner}]] resolves to no vault note")


def _self_test() -> int:
    """Synthetic-fixture unit tests for every check function."""
    import tempfile

    failures = 0

    def check(name, ok):
        nonlocal failures
        if not ok:
            failures += 1
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")

    # --- gh_slug ---
    check("gh_slug: basic heading",
          gh_slug("Install requirements") == "install-requirements")
    check("gh_slug: strips backticks",
          gh_slug("`code` in heading") == "code-in-heading")
    check("gh_slug: strips link syntax",
          gh_slug("[text](url) heading") == "text-heading")
    check("gh_slug: removes punctuation",
          gh_slug("What's new?") == "whats-new")

    # --- check_readmes ---
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # root missing README -> error
        (root / "sub").mkdir()
        (root / "sub" / "a.md").write_text("# A\n")
        (root / "sub" / "b.md").write_text("# B\n")
        errs: list[str] = []
        check_readmes(root, errs)
        check("check_readmes: missing root README flagged",
              any("missing README.md" in e for e in errs))
        check("check_readmes: missing sub README flagged (multi-file dir)",
              any("sub/" in e and "missing README.md" in e for e in errs))

        # single-file folder needs no README
        (root / "single").mkdir()
        (root / "single" / "only.md").write_text("# Only\n")
        errs2: list[str] = []
        (root / "README.md").write_text("# Root\n")
        check_readmes(root, errs2)
        check("check_readmes: single-file folder not flagged",
              not any("single/" in e for e in errs2))

    # --- check_frontmatter ---
    with tempfile.TemporaryDirectory() as td:
        # disallowed key
        bad = Path(td) / "bad.md"
        bad.write_text("---\nmode: reference\ntitle: X\n---\n# X\n")
        errs = []
        check_frontmatter(bad, errs)
        check("check_frontmatter: disallowed 'mode:' flagged", len(errs) == 1)

        # unquoted colon in value
        bad2 = Path(td) / "bad2.md"
        bad2.write_text("---\ntitle: Linter: detectors\n---\n# X\n")
        errs2 = []
        check_frontmatter(bad2, errs2)
        check("check_frontmatter: unquoted colon in value flagged", len(errs2) == 1)

        # clean frontmatter
        good = Path(td) / "good.md"
        good.write_text("---\ntitle: \"Clean: title\"\nstatus: draft\n---\n# X\n")
        errs3: list[str] = []
        check_frontmatter(good, errs3)
        check("check_frontmatter: clean file passes", len(errs3) == 0)

        # no frontmatter at all -> no error
        nofm = Path(td) / "nofm.md"
        nofm.write_text("# Just a heading\n")
        errs4: list[str] = []
        check_frontmatter(nofm, errs4)
        check("check_frontmatter: no frontmatter -> no error", len(errs4) == 0)

    # --- check_links ---
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "target.md").write_text("# Real heading\n## Sub section\n")
        # good link
        good = root / "good.md"
        good.write_text("[link](target.md)\n[anchor](target.md#sub-section)\n")
        errs = []
        check_links(good, errs)
        check("check_links: valid relative link + anchor pass", len(errs) == 0)

        # broken link
        bad = root / "bad.md"
        bad.write_text("[link](nonexistent.md)\n")
        errs2 = []
        check_links(bad, errs2)
        check("check_links: broken relative link flagged", len(errs2) == 1)

        # broken anchor
        bad2 = root / "bad2.md"
        bad2.write_text("[link](target.md#no-such-anchor)\n")
        errs3 = []
        check_links(bad2, errs3)
        check("check_links: broken anchor flagged", len(errs3) == 1)

        # link inside fenced code block -> ignored
        code = root / "code.md"
        code.write_text("```\n[link](nonexistent.md)\n```\n")
        errs4: list[str] = []
        check_links(code, errs4)
        check("check_links: link in fenced code ignored", len(errs4) == 0)

        # same-file anchor
        self_anchor = root / "self.md"
        self_anchor.write_text("# Top\n## Details\n[jump](#details)\n[bad](#nope)\n")
        errs5: list[str] = []
        check_links(self_anchor, errs5)
        check("check_links: same-file anchor valid passes, broken flagged", len(errs5) == 1)

    # --- check_wikilinks ---
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # a wikilink that resolves to a known doc -> error
        md = root / "test.md"
        md.write_text("See [[policy-mcp]] for details.\n")
        doc_names = {"policy-mcp.md", "readme.md"}
        errs = []
        check_wikilinks(md, errs, doc_names)
        check("check_wikilinks: resolving wikilink flagged", len(errs) == 1)

        # wikilink that does NOT resolve to any doc -> allowed (vault syntax)
        md2 = root / "test2.md"
        md2.write_text("See [[someCitekey]] here.\n")
        errs2 = []
        check_wikilinks(md2, errs2, doc_names)
        check("check_wikilinks: non-resolving wikilink allowed", len(errs2) == 0)

        # wikilink inside inline code -> ignored
        md3 = root / "test3.md"
        md3.write_text("Use `[[policy-mcp]]` syntax.\n")
        errs3: list[str] = []
        check_wikilinks(md3, errs3, doc_names)
        check("check_wikilinks: wikilink in inline code ignored", len(errs3) == 0)

    # --- check_link_text ---
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # link text that IS the filename -> error
        md = root / "test.md"
        md.write_text("[policy-mcp.md](policy-mcp.md)\n")
        errs = []
        check_link_text(md, errs)
        check("check_link_text: filename as link text flagged", len(errs) == 1)

        # link text that IS the stem -> error
        md2 = root / "test2.md"
        md2.write_text("[policy-mcp](policy-mcp.md)\n")
        errs2 = []
        check_link_text(md2, errs2)
        check("check_link_text: stem as link text flagged", len(errs2) == 1)

        # proper link text -> no error
        md3 = root / "test3.md"
        md3.write_text("[Policy MCP reference](policy-mcp.md)\n")
        errs3: list[str] = []
        check_link_text(md3, errs3)
        check("check_link_text: proper title text passes", len(errs3) == 0)

        # external link -> not checked
        md4 = root / "test4.md"
        md4.write_text("[policy-mcp](https://example.com/policy-mcp.md)\n")
        errs4: list[str] = []
        check_link_text(md4, errs4)
        check("check_link_text: external link not checked", len(errs4) == 0)

    # --- check_wikilink_aliases ---
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # bare wikilink -> error
        md = root / "test.md"
        md.write_text("See [[some-note]] for info.\n")
        errs = []
        check_wikilink_aliases(md, errs)
        check("check_wikilink_aliases: bare wikilink flagged", len(errs) == 1)

        # aliased wikilink -> ok
        md2 = root / "test2.md"
        md2.write_text("See [[some-note|Some Note]] for info.\n")
        errs2 = []
        check_wikilink_aliases(md2, errs2)
        check("check_wikilink_aliases: aliased wikilink passes", len(errs2) == 0)

        # anchor-only wikilink with no target -> not flagged (empty target after split)
        md3 = root / "test3.md"
        md3.write_text("See [[#heading]] here.\n")
        errs3: list[str] = []
        check_wikilink_aliases(md3, errs3)
        check("check_wikilink_aliases: anchor-only wikilink passes", len(errs3) == 0)

    # --- check_broken_vault_wikilinks ---
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        stems = {"real-note", "good"}
        # aliased link to a MISSING note -> error (the gap check_wikilink_aliases misses)
        md = root / "test.md"
        md.write_text("See [[ghost-note|A Title]] here.\n")
        errs = []
        check_broken_vault_wikilinks(md, errs, stems)
        check("check_broken_vault_wikilinks: aliased link to missing note flagged", len(errs) == 1)

        # aliased link to an EXISTING note -> ok
        md2 = root / "test2.md"
        md2.write_text("See [[real-note|A Title]] here.\n")
        errs2 = []
        check_broken_vault_wikilinks(md2, errs2, stems)
        check("check_broken_vault_wikilinks: aliased link to existing note passes", len(errs2) == 0)

        # bare link to existing note (with #anchor) -> ok
        md3 = root / "test3.md"
        md3.write_text("See [[good#section]] here.\n")
        errs3: list[str] = []
        check_broken_vault_wikilinks(md3, errs3, stems)
        check("check_broken_vault_wikilinks: link with anchor to existing note passes", len(errs3) == 0)

        # asset path -> not a note, ignored
        md4 = root / "test4.md"
        md4.write_text("![[90-assets/img.png]]\n")
        errs4: list[str] = []
        check_broken_vault_wikilinks(md4, errs4, stems)
        check("check_broken_vault_wikilinks: asset path ignored", len(errs4) == 0)

        # wikilink inside inline code -> ignored
        md5 = root / "test5.md"
        md5.write_text("Use `[[ghost-note]]` syntax.\n")
        errs5: list[str] = []
        check_broken_vault_wikilinks(md5, errs5, stems)
        check("check_broken_vault_wikilinks: wikilink in inline code ignored", len(errs5) == 0)

    # --- check_template_frontmatter ---
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # disallowed key inside yaml fence
        md = root / "tmpl.md"
        md.write_text("# Template\n\n```yaml\ntitle: X\nmode: reference\n```\n")
        errs = []
        check_template_frontmatter(md, errs)
        check("check_template_frontmatter: disallowed key in fence flagged", len(errs) == 1)

        # clean template
        md2 = root / "tmpl2.md"
        md2.write_text("# Template\n\n```yaml\ntitle: X\nstatus: draft\n```\n")
        errs2 = []
        check_template_frontmatter(md2, errs2)
        check("check_template_frontmatter: clean fence passes", len(errs2) == 0)

    # --- check_thin_folders (advisory) ---
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "README.md").write_text("# Root\n")
        (root / "thin").mkdir()
        (root / "thin" / "only.md").write_text("# Only\n")
        warns: list[str] = []
        check_thin_folders(root, warns)
        check("check_thin_folders: single-file folder flagged as advisory",
              any("thin/" in w for w in warns))

    # --- heading_slugs ---
    with tempfile.TemporaryDirectory() as td:
        md = Path(td) / "h.md"
        md.write_text("# Top Level\n## Sub Heading\n<a id=\"custom-anchor\"></a>\n")
        slugs = heading_slugs(md)
        check("heading_slugs: top-level heading",
              "top-level" in slugs)
        check("heading_slugs: sub heading",
              "sub-heading" in slugs)
        check("heading_slugs: HTML id attribute",
              "custom-anchor" in slugs)

    print(f"\n{'FAILED' if failures else 'OK'}: {failures} failing check(s) — docs-doctor self-test")
    return failures


def main() -> int:
    if "--self-test" in sys.argv:
        sys.exit(1 if _self_test() else 0)

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
        check_link_text(md, errors)

    # Guard the vault note templates too: their frontmatter lives in a ```yaml fence,
    # and a banned key there propagates to every note created from the template.
    tmpl_dir = root.parent / "vault" / "99-system" / "templates"
    if tmpl_dir.is_dir():
        for md in sorted(tmpl_dir.glob("*.md")):
            check_template_frontmatter(md, errors)

    # Link-text discipline extends to the vault notes: cross-links must use the page
    # title — markdown link text and wikilink aliases — never the bare filename.
    vault = root.parent / "vault"
    if vault.is_dir():
        vault_stems = {p.stem.lower() for p in vault.rglob("*.md") if ".obsidian" not in p.parts}
        for md in sorted(vault.rglob("*.md")):
            if ".obsidian" in md.parts or "templates" in md.parts:
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
