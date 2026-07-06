#!/usr/bin/env python3
"""docs-doctor — structural linter for docs/ plus vault-template link text.

Enforces the conventions from the mode-first refactor plan. These are all
*structural* checks; classifying a file by reading mode is a human concern and
deliberately out of scope (a linter cannot tell reference from explanation).

Checks:
  1. README presence  — every docs directory with multiple pages has a README.md
                        landing page, except release-version folders where the
                        release plan is the landing document.
  2. Link integrity   — every relative Markdown link resolves to a real file,
                        and every #anchor resolves to a heading in the target
                        (GitHub does not auto-heal links when files move).
  3. Frontmatter policy — no file carries a disallowed key (`mode:`/`audience:`
                        dropped in the refactor; `tags:` unsanctioned). Enforced on
                        docs and on the vault note templates' fenced frontmatter.
  4. No wikilinks     — a [[wikilink]] that resolves to a docs file must be a
                        relative Markdown link (GitHub does not render wikilinks).
  5. Link text        — across docs/ and vault-template/, a link's visible text
                        must be the target's page title, not its filename; bare
                        [[wikilinks]] in vault notes must be aliased with the title.
  6. Vault wikilinks  — a vault [[note]]/[[note|alias]] must resolve to an existing
                        vault note (an aliased link to a missing note is otherwise
                        silent).
  7. ADR code links   — current published docs must avoid bare `(ADR-NN)` codes.

Exit 0 if clean, 1 if any error.
Usage: python scripts/checks/docs_doctor.py [docs_root]   (default: docs)

One script, two triggers: run locally (pre-commit) and in CI (GitHub Actions).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

DROPPED_KEYS = (
    "mode",
    "audience",
    "tags",
)  # mode/audience dropped in the refactor; tags unsanctioned (use the controlled topic/methods vocabularies)

# Scratch dirs: tracked in git so relative links resolve, but excluded from the
# published site (docs/_config.yml) and skipped by these structural checks —
# planning notes / generated reports under a tmp/ folder are not held to the
# published-docs bar.
SCRATCH_DIRS = {"tmp"}

DEFAULT_SITE_EXCLUDED_DIRS = {"releasing", "testing"}
_SITE_EXCLUDE_CACHE: dict[Path, set[str]] = {}


def _scratch(p: Path, base: Path) -> bool:
    # Match a scratch dir only *within* the scanned tree, not the absolute path — so a
    # repo checked out under /tmp (or a pytest tmp_path root) is not wholesale excluded.
    return any(part in SCRATCH_DIRS for part in p.relative_to(base).parts)


def _config_root(base: Path) -> Path:
    for candidate in (base, *base.parents):
        if (candidate / "_config.yml").is_file():
            return candidate
    return base


def _site_excluded_dirs(base: Path) -> set[str]:
    root = _config_root(base).resolve()
    if root in _SITE_EXCLUDE_CACHE:
        return _SITE_EXCLUDE_CACHE[root]
    config = root / "_config.yml"
    if not config.is_file():
        _SITE_EXCLUDE_CACHE[root] = set(DEFAULT_SITE_EXCLUDED_DIRS)
        return _SITE_EXCLUDE_CACHE[root]
    try:
        data = yaml.safe_load(read(config)) or {}
    except yaml.YAMLError:
        data = {}
    excludes: set[str] = set()
    for item in data.get("exclude") or []:
        if not isinstance(item, str):
            continue
        value = item.strip().strip("/")
        if value and "/" not in value and not re.search(r"[*?\[]", value):
            excludes.add(value)
    _SITE_EXCLUDE_CACHE[root] = excludes
    return excludes


def _site_excluded(p: Path, base: Path) -> bool:
    excluded = _site_excluded_dirs(base)
    if set(base.parts) & excluded:
        return True
    root = _config_root(base)
    try:
        parts = p.relative_to(root).parts
    except ValueError:
        parts = p.relative_to(base).parts
    return bool(set(parts) & excluded)


def _published(md: Path, root: Path) -> bool:
    # True if this docs page is part of the published GitHub Pages site. Pages under a
    # site-excluded dir or a scratch/tmp dir are repo-internal (read on github.com,
    # not the built site), so their out-of-site relative links are intentional.
    return not _site_excluded(md, root) and not _scratch(md, root)


# [text](target) — but NOT images ![alt](src). Reference-style/wikilinks unused.
LINK_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)]+)\)")
LINK_TEXT_RE = re.compile(r"(?<!\!)\[([^\]]*)\]\(([^)]+)\)")  # captures (text, target)
PAGES_URL = "https://eranroseman.github.io/memoria-vault"
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]*`")
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
YAML_FENCE_RE = re.compile(r"```ya?ml\n(.*?)```", re.DOTALL)
BARE_ADR_CODE_RE = re.compile(r"(?<!\[)\(ADR-\d+\)")
RELEASE_VERSION_DIR_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
COUNT_RE = re.compile(r"\b(\d+)\b")


def read(path: Path) -> str:
    # Normalize newlines so frontmatter/regex behave the same on Windows and CI.
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def check_readmes(root: Path, errors: list[str]) -> None:
    if not (root / "README.md").exists():
        errors.append(f"{root}/: missing README.md")
    for d in sorted(p for p in root.rglob("*") if p.is_dir() and not _scratch(p, root)):
        if _release_version_dir(d, root):
            continue
        md_files = [p for p in d.iterdir() if p.suffix == ".md" and p.name != "README.md"]
        if len(md_files) <= 1:
            continue  # single-file folders need no landing page; the file is its own landing
        if not (d / "README.md").exists():
            errors.append(f"{d}/: missing README.md (folder landing page)")


def _release_version_dir(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return False
    if len(parts) == 2 and parts[0] == "releasing":
        return bool(RELEASE_VERSION_DIR_RE.fullmatch(parts[1]))
    if root.name == "releasing" and len(parts) == 1:
        return bool(RELEASE_VERSION_DIR_RE.fullmatch(parts[0]))
    return False


def check_frontmatter(md: Path, errors: list[str]) -> None:
    m = FRONTMATTER_RE.match(read(md))
    if not m:
        return
    block = m.group(1)
    for key in DROPPED_KEYS:
        if re.search(rf"^{key}\s*:", block, re.MULTILINE):
            errors.append(
                f"{md}: frontmatter carries disallowed key '{key}:' (mode/audience dropped; tags unsanctioned)"
            )
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
                f'colon — quote it ("{value}") or Jekyll drops the page from the nav'
            )


_slug_cache: dict[Path, set[str]] = {}


def gh_slug(text: str) -> str:
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # link -> label
    text = text.replace("`", "").strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s", "-", text)


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
    text = FENCE_RE.sub("", text)  # ignore fenced code blocks
    text = INLINE_CODE_RE.sub("", text)  # ignore inline code
    for raw in LINK_RE.findall(text):
        target = raw.strip()
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        if "{{" in target:
            continue  # template placeholder such as `{{ #NN }}`, not a real link
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
                errors.append(
                    f"{md}: template frontmatter carries disallowed key '{key}:' (mode/audience dropped; tags unsanctioned)"
                )


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
            errors.append(
                f"{md}: link text '{label.strip()}' is a filename — use the target's page title"
            )
            continue
        t = target.strip().split()[0].split("#")[0].rstrip("/")
        base = t.split("/")[-1]
        stem = base[:-3] if base.endswith(".md") else base
        if lbl == base or lbl == stem:
            errors.append(
                f"{md}: link text '{label.strip()}' restates the filename — use the target's page title"
            )


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
            errors.append(
                f"{md}: bare wikilink [[{inner}]] shows the filename — alias it with the page title ([[{tgt}|…]])"
            )


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


def check_site_local_links(md: Path, root: Path, errors: list[str]) -> None:
    # A *published* docs page must not link to a file outside the published site (docs/).
    # The recurring case is a relative link into repository source: it resolves on disk
    # and on github.com, but paths such as vault-template/ and src/ are siblings of docs/
    # and are NOT part of the Jekyll site (docs/_config.yml). Use inline code for a
    # source path, or an absolute github.com/eranroseman/memoria-vault/blob/main/… URL
    # when a click is genuinely wanted.
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
            errors.append(
                f"{md}: relative link '{path_part}' leaves the published site (docs/) — "
                f"repo source paths are not on the Jekyll site; use inline code or an absolute github.com blob URL"
            )


def check_site_excluded_targets(md: Path, root: Path, errors: list[str]) -> None:
    if not _published(md, root):
        return
    text = INLINE_CODE_RE.sub("", FENCE_RE.sub("", read(md)))
    for raw in LINK_RE.findall(text):
        target = raw.strip()
        if target.startswith(("http://", "https://", "mailto:", "#")) or "{{" in target:
            continue
        path_part = re.split(r"\s+", target.partition("#")[0].strip())[0]
        if not path_part:
            continue
        tgt = (md.parent / path_part).resolve()
        if not tgt.exists():
            continue
        try:
            tgt.relative_to(_config_root(root))
        except ValueError:
            continue
        if _site_excluded(tgt, root) or _scratch(tgt, _config_root(root)):
            errors.append(
                f"{md}: link '{path_part}' targets a docs/_config.yml excluded page — "
                "use an absolute github.com blob URL or publish the target"
            )


def check_hidden_compatibility_page(md: Path, root: Path, errors: list[str]) -> None:
    if "adr" in md.relative_to(root).parts or md.name.startswith("_"):
        return
    match = FRONTMATTER_RE.match(read(md))
    if not match:
        return
    block = match.group(1)
    hidden = re.search(r"^nav_exclude:\s*true\s*$", block, re.MULTILINE)
    compatibility = re.search(
        r"^(permalink|redirect_from|redirect_to|aliases?):\s*",
        block,
        re.MULTILINE,
    )
    if hidden and compatibility:
        errors.append(
            f"{md}: hidden compatibility pages are forbidden; update links and delete the page"
        )


def _frontmatter_scalar(md: Path, key: str) -> str:
    match = FRONTMATTER_RE.match(read(md))
    if not match:
        return ""
    found = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", match.group(1), re.MULTILINE)
    if not found:
        return ""
    return found.group(1).strip().strip("\"'")


def _frontmatter_bool(md: Path, key: str) -> bool:
    return _frontmatter_scalar(md, key).lower() == "true"


def check_site_nav_hierarchy(root: Path, errors: list[str]) -> None:
    pages = [
        path
        for path in sorted(root.rglob("*.md"))
        if not _scratch(path, root) and not _site_excluded(path, root)
    ]
    by_title: dict[str, list[Path]] = {}
    for path in pages:
        title = _frontmatter_scalar(path, "title")
        if title:
            by_title.setdefault(title, []).append(path)

    def unique_container(
        title: str, child: Path, relation: str, parent_title: str = ""
    ) -> Path | None:
        matches = by_title.get(title, [])
        if parent_title:
            matches = [
                path for path in matches if _frontmatter_scalar(path, "parent") == parent_title
            ]
        if not matches:
            qualifier = f" under '{parent_title}'" if parent_title else ""
            errors.append(
                f"{child}: site nav {relation} '{title}'{qualifier} has no published page"
            )
            return None
        if len(matches) > 1:
            locations = ", ".join(str(path) for path in matches)
            errors.append(f"{child}: site nav {relation} '{title}' is ambiguous ({locations})")
            return None
        parent = matches[0]
        if not _frontmatter_bool(parent, "has_children"):
            errors.append(
                f"{child}: site nav {relation} '{title}' is not marked has_children: true"
            )
        return parent

    for path in pages:
        parent_title = _frontmatter_scalar(path, "parent")
        grand_parent_title = _frontmatter_scalar(path, "grand_parent")
        if grand_parent_title and not parent_title:
            errors.append(f"{path}: site nav grand_parent is set without parent")
            continue
        parent = (
            unique_container(parent_title, path, "parent", grand_parent_title)
            if parent_title
            else None
        )
        if not parent:
            continue
        parent_parent = _frontmatter_scalar(parent, "parent")
        if parent_parent and not grand_parent_title:
            errors.append(
                f"{path}: site nav child of '{parent_title}' must set grand_parent: {parent_parent}"
            )
        if grand_parent_title:
            parent_grand_parent = _frontmatter_scalar(parent, "grand_parent")
            unique_container(grand_parent_title, path, "grand_parent", parent_grand_parent)
            if parent_parent != grand_parent_title:
                errors.append(
                    f"{path}: site nav parent '{parent_title}' is not under grand_parent "
                    f"'{grand_parent_title}'"
                )


def check_bare_adr_codes(md: Path, root: Path, errors: list[str]) -> None:
    # Current public docs should describe the design-history entry, not cite a bare
    # retired ADR key. Repo-internal release/testing docs keep historical prose.
    if not _published(md, root) or "adr" in md.relative_to(root).parts:
        return
    text = INLINE_CODE_RE.sub("", FENCE_RE.sub("", read(md)))
    for line_no, line in enumerate(text.splitlines(), start=1):
        match = BARE_ADR_CODE_RE.search(line)
        if match:
            errors.append(
                f"{md}:{line_no}: bare ADR code {match.group(0)} — link to the design-history context"
            )


def _load_schema_types(repo: Path) -> dict[str, dict]:
    schema_dir = repo / "vault-template" / ".memoria" / "schemas" / "types"
    out: dict[str, dict] = {}
    for path in sorted(schema_dir.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (yaml.YAMLError, OSError):
            continue
        out[path.stem] = data
    return out


def _markdown_code_values(text: str) -> set[str]:
    text = FENCE_RE.sub("", text)
    return set(re.findall(r"`([^`]+)`", text))


def check_document_type_reference_mirror(repo: Path, errors: list[str]) -> None:
    doc = repo / "docs" / "reference" / "document-types.md"
    frontmatter = repo / "docs" / "reference" / "frontmatter.md"
    types = _load_schema_types(repo)
    if not types or not doc.is_file() or not frontmatter.is_file():
        return
    doc_text = read(doc)
    frontmatter_text = read(frontmatter)
    expected_count = len(types)
    for line_no, line in enumerate(doc_text.splitlines(), start=1):
        if " document types" not in line and " types group" not in line:
            continue
        m = COUNT_RE.search(line)
        if m and int(m.group(1)) != expected_count:
            errors.append(
                f"{doc}:{line_no}: document-type count mirror says {m.group(1)} but schemas define {expected_count}"
            )
    mentioned = _markdown_code_values(doc_text)
    missing = sorted(set(types) - mentioned)
    if missing:
        errors.append(f"{doc}: document-type mirror omits schema type(s): {', '.join(missing)}")
    frontmatter_mentions = _markdown_code_values(frontmatter_text)
    missing_frontmatter = sorted(set(types) - frontmatter_mentions)
    if missing_frontmatter:
        errors.append(
            f"{frontmatter}: per-type frontmatter mirror omits schema type(s): "
            f"{', '.join(missing_frontmatter)}"
        )


def _vocabulary_terms(path: Path) -> dict[str, set[str]]:
    text = read(path)
    out: dict[str, set[str]] = {"research_area": set(), "methodology": set()}
    current = ""
    for line in text.splitlines():
        if line.startswith(("## research_area", "### `research_area`")):
            current = "research_area"
            continue
        if line.startswith(("## methodology", "### `methodology`")):
            current = "methodology"
            continue
        if line.startswith(("## topics", "### `topics`")):
            current = ""
            continue
        if current:
            bullet = re.match(r"- ([a-z0-9-]+) —", line)
            table = re.match(r"\| `([^`]+)` \|", line)
            if bullet:
                out[current].add(bullet.group(1))
            elif table:
                out[current].add(table.group(1))
    return out


def check_vocabulary_reference_mirror(repo: Path, errors: list[str]) -> None:
    source = repo / "src" / "system" / "vocabulary.md"
    doc = repo / "docs" / "reference" / "vocabulary.md"
    if not source.is_file() or not doc.is_file():
        return
    source_terms = _vocabulary_terms(source)
    doc_terms = _vocabulary_terms(doc)
    for field in ("research_area", "methodology"):
        if source_terms[field] != doc_terms[field]:
            missing = sorted(source_terms[field] - doc_terms[field])
            extra = sorted(doc_terms[field] - source_terms[field])
            errors.append(
                f"{doc}: {field} vocabulary mirror differs from vault-template/system/vocabulary.md"
                f" (missing: {missing or 'none'}; extra: {extra or 'none'})"
            )


def check_reference_readme_index(repo: Path, errors: list[str]) -> None:
    index = repo / "docs" / "reference" / "README.md"
    reference_dir = index.parent
    if not index.is_file() or not reference_dir.is_dir():
        return
    linked = {
        Path(target.partition("#")[0]).name
        for target in re.findall(r"\]\(([^)]+\.md(?:#[^)]+)?)\)", read(index))
    }
    expected = sorted(path.name for path in reference_dir.glob("*.md") if path.name != "README.md")
    missing = [name for name in expected if name not in linked]
    if missing:
        errors.append(f"{index}: reference index omits page(s): {', '.join(missing)}")


def check_source_of_truth_mirrors(repo: Path, errors: list[str]) -> None:
    check_document_type_reference_mirror(repo, errors)
    check_vocabulary_reference_mirror(repo, errors)
    check_reference_readme_index(repo, errors)


def _docs_target_exists(repo: Path, rel: str) -> bool:
    rel = rel.strip("/")
    stem = rel[:-5] if rel.endswith(".html") else rel
    return any(
        (repo / target).exists()
        for target in (
            f"docs/{stem}.md",
            f"docs/{rel}/index.md",
            f"docs/{rel}/README.md",
        )
    )


def _pages_targets(text: str) -> list[str]:
    return sorted(
        set(
            re.findall(
                rf"{re.escape(PAGES_URL)}/[A-Za-z0-9/_-]+(?:\.html)?(?:#[A-Za-z0-9_.-]+)?",
                text,
            )
        )
    )


def check_vault_docs_refs(repo: Path, errors: list[str]) -> None:
    vault = repo / "vault-template"
    for path in sorted(
        p
        for p in vault.rglob("*")
        if p.is_file()
        and p.suffix in {".md", ".py", ".yaml", ".yml"}
        and ".obsidian" not in p.parts
    ):
        text = read(path)
        for ref in sorted(set(re.findall(r"docs/[A-Za-z0-9/_.-]+\.md", text))):
            if not (repo / ref).is_file():
                errors.append(f"{path}: missing doc reference: {ref}")
        for url in _pages_targets(text):
            rel = url.removeprefix(f"{PAGES_URL}/").split("#", 1)[0].rstrip("/")
            if not _docs_target_exists(repo, rel):
                errors.append(f"{path}: Pages URL with no docs target: {url}")
        if "github.com/eranroseman/memoria-vault/blob/main/docs/" in text:
            errors.append(f"{path}: uses a github blob URL for docs/ — use the Pages URL instead")


def check_doc_refs(repo: Path, files: list[str], errors: list[str]) -> None:
    excluded = re.compile(r"^docs/(?:contributing|releasing|testing)(?:/|$)")
    github_docs_re = re.compile(
        r"github\.com/eranroseman/memoria-vault/(?:blob|tree)/main/docs/[A-Za-z0-9/_.-]*"
    )
    for raw in files:
        raw_path = Path(raw)
        path = raw_path if raw_path.is_absolute() else repo / raw_path
        try:
            rel = path.relative_to(repo)
        except ValueError:
            rel = raw_path
        if (
            not path.is_file()
            or rel.parts[:1] == ("tests",)
            or path.resolve() == Path(__file__).resolve()
        ):
            continue
        text = read(path)
        for ref in sorted(set(re.findall(r"docs/[A-Za-z0-9/_.-]+\.md", text))):
            if not (repo / ref).is_file():
                errors.append(f"check-doc-refs: {raw} -> missing {ref}")
        for url in _pages_targets(text):
            rel = url.removeprefix(f"{PAGES_URL}/").split("#", 1)[0].rstrip("/")
            if not _docs_target_exists(repo, rel):
                errors.append(f"check-doc-refs: {raw} -> Pages URL with no docs target: {url}")
        for match in github_docs_re.findall(text):
            rel = match.split("/main/", 1)[1]
            if not excluded.match(rel):
                errors.append(
                    f"check-doc-refs: {raw} uses a github URL for a published docs/ path "
                    "— use the Pages URL instead"
                )
                break


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docs_root", nargs="?", default="docs")
    parser.add_argument(
        "--vault-links",
        action="store_true",
        help="validate vault-template references to published docs.",
    )
    parser.add_argument(
        "--doc-refs",
        nargs="*",
        metavar="PATH",
        help="validate docs references in the given files, for pre-commit.",
    )
    return parser.parse_args(argv)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except OSError:
        pass
    args = parse_args()
    repo = Path.cwd()
    if args.vault_links or args.doc_refs is not None:
        errors: list[str] = []
        if args.vault_links:
            check_vault_docs_refs(repo, errors)
        if args.doc_refs is not None:
            check_doc_refs(repo, args.doc_refs, errors)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print("docs-doctor: reference checks clean ✓")
        return 0

    root = Path(args.docs_root)
    if not root.is_dir():
        print(f"docs-doctor: root '{root}' not found", file=sys.stderr)
        return 1

    errors: list[str] = []
    doc_md_names = {p.name.lower() for p in root.rglob("*.md") if not _scratch(p, root)}
    check_readmes(root, errors)
    check_site_nav_hierarchy(root, errors)
    for md in sorted(p for p in root.rglob("*.md") if not _scratch(p, root)):
        check_frontmatter(md, errors)
        check_links(md, errors)
        check_site_local_links(md, root, errors)
        check_site_excluded_targets(md, root, errors)
        check_hidden_compatibility_page(md, root, errors)
        check_bare_adr_codes(md, root, errors)
        check_wikilinks(md, errors, doc_md_names)
        check_link_text(md, errors)

    # Guard the vault note templates too: their frontmatter lives in a ```yaml fence,
    # and a banned key there propagates to every note created from the template.
    tmpl_dir = root.parent / "vault-template" / "system" / "templates"
    if tmpl_dir.is_dir():
        for md in sorted(tmpl_dir.glob("*.md")):
            check_template_frontmatter(md, errors)

    # Link-text discipline extends to the vault notes: cross-links must use the page
    # title — markdown link text and wikilink aliases — never the bare filename.
    vault = root.parent / "vault-template"
    if vault.is_dir():
        vault_stems = {
            p.stem.lower()
            for p in vault.rglob("*.md")
            if ".obsidian" not in p.parts and not _scratch(p, vault)
        }
        for md in sorted(vault.rglob("*.md")):
            if ".obsidian" in md.parts or "templates" in md.parts or _scratch(md, vault):
                continue
            check_link_text(md, errors)
            check_wikilink_aliases(md, errors)
            check_broken_vault_wikilinks(md, errors, vault_stems)

    check_source_of_truth_mirrors(root.parent, errors)

    if errors:
        print(f"docs-doctor: {len(errors)} issue(s)\n")
        for e in errors:
            print(f"  ✗ {e}")
    else:
        print("docs-doctor: clean ✓")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
