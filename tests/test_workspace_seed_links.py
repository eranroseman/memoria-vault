"""Seed link and frontmatter integrity — extracted from the retired docs-doctor.

`plugin_provenance_doctor` guards which files the shipped workspace seed
carries; this guards their *content* links, which nothing else covers: seed
references to published docs and vault wikilink discipline (link text is the
page title, and every [[note]] resolves to a real seed note).
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "src/memoria_vault/product/workspace_seed"

PAGES_URL = "https://eranroseman.github.io/memoria-vault"
LINK_TEXT_RE = re.compile(r"(?<!\!)\[([^\]]*)\]\(([^)]+)\)")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]*`")
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
SCRATCH_DIRS = {"tmp"}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _scratch(p: Path, base: Path) -> bool:
    return any(part in SCRATCH_DIRS for part in p.relative_to(base).parts)


def _link_is_internal(target: str) -> bool:
    t = target.strip().split()[0]
    return t.startswith(PAGES_URL) or not t.startswith(("http://", "https://", "mailto:"))


def _docs_target_exists(rel: str) -> bool:
    rel = rel.strip("/")
    stem = rel[:-5] if rel.endswith(".html") else rel
    return any(
        (ROOT / target).exists()
        for target in (f"docs/{stem}.md", f"docs/{rel}/index.md", f"docs/{rel}/README.md")
    )


def _pages_targets(text: str) -> list[str]:
    pattern = rf"{re.escape(PAGES_URL)}/[A-Za-z0-9/_-]+(?:\.html)?(?:#[A-Za-z0-9_.-]+)?"
    return sorted(set(re.findall(pattern, text)))


def _check_seed_docs_refs(errors: list[str]) -> None:
    for path in sorted(
        p
        for p in SEED.rglob("*")
        if p.is_file()
        and p.suffix in {".md", ".py", ".yaml", ".yml"}
        and ".obsidian" not in p.parts
    ):
        text = _read(path)
        for ref in sorted(set(re.findall(r"docs/[A-Za-z0-9/_.-]+\.md", text))):
            if not (ROOT / ref).is_file():
                errors.append(f"{path}: missing doc reference: {ref}")
        for url in _pages_targets(text):
            rel = url.removeprefix(f"{PAGES_URL}/").split("#", 1)[0].rstrip("/")
            if not _docs_target_exists(rel):
                errors.append(f"{path}: Pages URL with no docs target: {url}")
        if "github.com/eranroseman/memoria-vault/blob/main/docs/" in text:
            errors.append(f"{path}: uses a github blob URL for docs/ — use the Pages URL instead")


def _check_link_text(md: Path, errors: list[str]) -> None:
    text = INLINE_CODE_RE.sub("", FENCE_RE.sub("", _read(md)))
    for label, target in LINK_TEXT_RE.findall(text):
        lbl = label.strip().rstrip("/")
        if not lbl or not _link_is_internal(target):
            continue
        if lbl.endswith(".md"):
            errors.append(f"{md}: link text '{label.strip()}' is a filename — use the page title")
            continue
        t = target.strip().split()[0].split("#")[0].rstrip("/")
        base = t.split("/")[-1]
        stem = base[:-3] if base.endswith(".md") else base
        if lbl in (base, stem):
            errors.append(f"{md}: link text '{label.strip()}' restates the filename")


def _check_wikilink_aliases(md: Path, errors: list[str]) -> None:
    text = INLINE_CODE_RE.sub("", FENCE_RE.sub("", _read(md)))
    for inner in WIKILINK_RE.findall(text):
        clean = inner.replace("\\|", "|")
        if "|" in clean:
            continue
        tgt = clean.split("#")[0].strip()
        if "." in tgt.split("/")[-1] and not tgt.endswith(".md"):
            continue
        if tgt:
            errors.append(f"{md}: bare wikilink [[{inner}]] — alias it with the page title")


def _check_broken_wikilinks(md: Path, errors: list[str], vault_stems: set[str]) -> None:
    text = INLINE_CODE_RE.sub("", FENCE_RE.sub("", _read(md)))
    for inner in WIKILINK_RE.findall(text):
        tgt = inner.replace("\\|", "|").split("|")[0].split("#")[0].strip().rstrip("\\")
        if not tgt or tgt.startswith("system/extracts/"):
            continue
        if "." in tgt.split("/")[-1] and not tgt.endswith(".md"):
            continue
        if Path(tgt).stem.lower() not in vault_stems:
            errors.append(f"{md}: wikilink [[{inner}]] resolves to no vault note")


def _collect_errors() -> list[str]:
    errors: list[str] = []
    _check_seed_docs_refs(errors)

    if SEED.is_dir():
        vault_stems = {
            p.stem.lower()
            for p in SEED.rglob("*.md")
            if ".obsidian" not in p.parts and not _scratch(p, SEED)
        }
        for md in sorted(SEED.rglob("*.md")):
            if ".obsidian" in md.parts or "templates" in md.parts or _scratch(md, SEED):
                continue
            _check_link_text(md, errors)
            _check_wikilink_aliases(md, errors)
            _check_broken_wikilinks(md, errors, vault_stems)
    return errors


def test_workspace_seed_links_are_clean() -> None:
    errors = _collect_errors()
    assert errors == [], "\n".join(errors)


def test_wikilink_detectors_flag_bare_and_broken_links(tmp_path: Path) -> None:
    md = tmp_path / "note.md"
    md.write_text(
        "A [[Missing Note]] here.\n"
        "An [[absent-note|Absent Note]] there.\n"
        "A [[real-note|Real Note]] link that resolves.\n",
        encoding="utf-8",
    )

    alias_errors: list[str] = []
    _check_wikilink_aliases(md, alias_errors)
    broken_errors: list[str] = []
    _check_broken_wikilinks(md, broken_errors, {"real-note"})

    assert alias_errors == [f"{md}: bare wikilink [[Missing Note]] — alias it with the page title"]
    assert broken_errors == [
        f"{md}: wikilink [[Missing Note]] resolves to no vault note",
        f"{md}: wikilink [[absent-note|Absent Note]] resolves to no vault note",
    ]
