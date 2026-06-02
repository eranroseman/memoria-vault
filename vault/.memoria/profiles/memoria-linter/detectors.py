#!/usr/bin/env python3
"""Deterministic vault detectors (zero-LLM) for the Memoria Linter.

Reference implementation of the *self-contained* checks from structural-detectors.md and
the non-LLM toolkit -- the ones that need only the vault tree (no ~/.hermes
deploy, no design-repo git). All checks are REPORT-ONLY; none mutates the vault.

    python detectors.py --vault <path>     # run against a vault, print findings
    python detectors.py --self-test        # synthetic-fixture unit tests (no vault)
    python detectors.py --vault <path> --json

Detectors needing external context (profile-install-drift, skeleton-drift,
command-vocab-drift, plugin-config-drift, vault-hash-drift) are intentionally
out of scope here -- they require ~/.hermes, the docs/ tree, or git/audit-log
state and belong in the runtime Linter that has them.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

SKIP_DIRS = {".obsidian", ".git", ".memoria", "node_modules"}
TRANSIENT_PREFIXES = ("10-inbox/", "40-workbench/", "99-system/logs/")
# Scaffolding, not authored notes: skeleton folders, assets, and the note
# templates (raw notes full of placeholder [[links]]). Detectors that assert
# things about *real* notes (broken wikilinks, type schema) skip these. Templates
# moved 00-meta/ -> 99-system/templates/ in the 99-system refactor (c53486d);
# keep this the single source of truth so the skip can't drift from the move.
SCAFFOLD_PREFIXES = ("00-meta/", "90-assets/", "99-system/templates/")
LEFTOVER_PATTERNS = [
    re.compile(p) for p in (
        r".*\.tmp\..*", r".*\.OLD\..*", r".*\.lessOLD\..*", r".*\.bak$",
        r".*~$", r"\.#.*", r".*\.orig$", r".*\.rej$",
    )
]
# Per-type required frontmatter fields (minimal; extend as the schema firms up).
REQUIRED_FIELDS = {
    "claim-note": ["lifecycle", "maturity"],
    "paper-note": ["citekey"],
}
DATAVIEW_BUILTINS = {
    "file", "rows", "type", "tags", "tag", "true", "false", "null",
}
# Dataview query keywords -- not fields. (TABLE WITHOUT ID ..., FROM, WHERE, AS, ...)
DATAVIEW_KEYWORDS = {
    "without", "id", "from", "where", "as", "flatten", "group", "by", "sort",
    "limit", "asc", "desc", "table", "list", "task", "and", "or", "not", "reverse",
}
# Only queries over these folders read *note frontmatter*; queries over the board
# (cards) or 99-system logs/metrics (JSONL) drift on different schemas, not this one.
NOTE_FOLDERS = ("10-inbox", "20-sources", "30-synthesis", "40-workbench", "50-deliverables")
SEVERITY_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}


@dataclass
class Finding:
    detector: str
    severity: str
    path: str
    message: str
    timestamp: str = ""   # ISO-8601 UTC; stamped per lint pass in run_all()


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def iter_files(vault: Path):
    """Yield every file under vault, skipping SKIP_DIRS."""
    for p in vault.rglob("*"):
        if p.is_dir():
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(vault).parts):
            continue
        yield p


def iter_notes(vault: Path):
    for p in iter_files(vault):
        if p.suffix == ".md":
            yield p


def relpath(vault: Path, p: Path) -> str:
    return p.relative_to(vault).as_posix()


def parse_frontmatter(text: str) -> dict:
    """Minimal YAML-frontmatter parser -- top-level scalars and inline lists.

    Dependency-free on purpose so the detectors (and the self-test) run without
    PyYAML. Handles `key: value`, `key: [a, b]`, and quoted scalars; ignores
    nested mappings (no detector here needs them)."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm: dict = {}
    for line in text[3:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        if line[0] in " \t":          # nested key -- minimal parser skips it
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            fm[key] = [v.strip().strip("\"'") for v in inner.split(",") if v.strip()]
        else:
            fm[key] = val.strip("\"'")
    return fm


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ""


_FM_KEY = re.compile(r"^\s*([A-Za-z_][\w-]*)\s*:", re.M)


def all_frontmatter_keys(text: str) -> set[str]:
    """Every field name declared in the frontmatter at *any* nesting depth.

    Unlike parse_frontmatter (top-level only), this captures keys nested under
    blocks like `_proposed_classification:` -- which is where claim/paper notes
    keep `maturity`, `topic`, `methods`, `study_design`, etc."""
    if not text.startswith("---"):
        return set()
    end = text.find("\n---", 3)
    if end == -1:
        return set()
    return set(_FM_KEY.findall(text[3:end]))


_CODE_BLOCK = re.compile(r"```[a-zA-Z]*\n(.*?)```", re.S)


def template_field_names(text: str) -> set[str]:
    """Field names a template declares. Memoria templates are raw notes (leading
    frontmatter); the code-block scan is kept as a fallback for any template that
    still carries a ```yaml frontmatter example."""
    keys = all_frontmatter_keys(text)
    for block in _CODE_BLOCK.findall(text):
        if "type:" in block or "---" in block:      # a frontmatter example block
            keys |= set(_FM_KEY.findall(block))
    return keys


# --------------------------------------------------------------------------- #
# Detectors -- each takes the vault root and returns a list[Finding].
# --------------------------------------------------------------------------- #
def orphan_working_files(vault: Path) -> list[Finding]:
    out = []
    for p in iter_files(vault):
        rp = relpath(vault, p)
        if rp.startswith(TRANSIENT_PREFIXES):
            continue
        name = p.name
        for pat in LEFTOVER_PATTERNS:
            if pat.fullmatch(name):
                age_d = (time.time() - p.stat().st_mtime) / 86400
                out.append(Finding("orphan-working-files", "LOW", rp,
                                    f"leftover file (matches /{pat.pattern}/), {age_d:.0f}d old"))
                break
    return out


def stale_fleeting(vault: Path, days: int = 7) -> list[Finding]:
    out, cutoff = [], time.time() - days * 86400
    folder = vault / "10-inbox" / "01-fleeting"
    if not folder.is_dir():
        return out
    for p in folder.glob("*.md"):
        if p.stat().st_mtime < cutoff:
            age_d = (time.time() - p.stat().st_mtime) / 86400
            out.append(Finding("stale-fleeting", "LOW", relpath(vault, p),
                               f"fleeting note {age_d:.0f}d old (>{days}d); promote or discard"))
    return out


def stale_answer_drafts(vault: Path, days: int = 90) -> list[Finding]:
    """Flag unreviewed answer drafts in 10-inbox/02-answers/ older than `days`.

    REPORT-ONLY by design: the human decides keep / promote / discard in the
    weekly review. Never auto-archive -- the most useful drafts are often the
    ones not yet gotten to, so silent archival would hide them exactly when
    they're most likely to be needed. (Formerly proposed as ADR-3, answer-draft
    retention; realized here as a report-only check rather than a decision.)"""
    out, cutoff = [], time.time() - days * 86400
    folder = vault / "10-inbox" / "02-answers"
    if not folder.is_dir():
        return out
    for p in folder.glob("*.md"):
        if p.stat().st_mtime < cutoff:
            age_d = (time.time() - p.stat().st_mtime) / 86400
            out.append(Finding("stale-answer-drafts", "LOW", relpath(vault, p),
                               f"answer draft {age_d:.0f}d old (>{days}d); keep, promote, or discard"))
    return out


def extract_path_broken(vault: Path) -> list[Finding]:
    out = []
    papers = vault / "20-sources" / "01-papers"
    if not papers.is_dir():
        return out
    for p in papers.rglob("*.md"):
        fm = parse_frontmatter(read(p))
        ep = fm.get("extract_path", "")
        if not ep or not isinstance(ep, str):
            continue
        norm = ep.strip().lstrip("/").replace("\\", "/")
        norm = norm[2:] if norm.startswith("./") else norm
        if not (vault / norm).exists():
            out.append(Finding("extract-path-broken", "HIGH", relpath(vault, p),
                               f"extract_path '{ep}' does not resolve"))
    return out


def frontmatter_schema_check(vault: Path) -> list[Finding]:
    out = []
    for p in iter_notes(vault):
        rp = relpath(vault, p)
        if rp.startswith(SCAFFOLD_PREFIXES):   # skeleton/assets/templates aren't typed notes
            continue
        if "/" not in rp:                      # vault-root pages (home, troubleshooting,
            continue                           # research-focus) are navigation, not typed notes
        fm = parse_frontmatter(read(p))
        if not fm:
            continue
        ntype = fm.get("type")
        if not ntype:
            out.append(Finding("schema-check", "MEDIUM", rp, "missing required 'type' field"))
            continue
        for field in REQUIRED_FIELDS.get(ntype, []):
            if field not in fm:
                out.append(Finding("schema-check", "MEDIUM", rp,
                                   f"{ntype} missing required field '{field}'"))
    return out


def broken_wikilinks(vault: Path) -> list[Finding]:
    notes = list(iter_notes(vault))
    stems = {p.stem for p in notes}
    link_re = re.compile(r"\[\[([^\]|#]+)")
    out = []
    for p in notes:
        rp = relpath(vault, p)
        if rp.startswith(SCAFFOLD_PREFIXES):   # scaffolding: example/placeholder links
            continue
        for m in link_re.finditer(read(p)):
            # rstrip a trailing "\" so a table-escaped pipe resolves: inside a
            # markdown table cell an aliased link must be written [[note\|alias]],
            # and the regex captures "note\" -> strip the escape to get "note".
            target = m.group(1).strip().rstrip("\\")
            if not target:
                continue
            stem = Path(target).stem
            if stem not in stems:
                out.append(Finding("broken-wikilink", "MEDIUM", relpath(vault, p),
                                   f"wikilink [[{target}]] resolves to no note"))
    return out


_DV_FIELD_LINE = re.compile(r"^\s*(TABLE|SORT|GROUP BY|FLATTEN)\s+(.*)$", re.I)
_IDENT = re.compile(r"[A-Za-z_][\w-]*")


def dashboard_field_drift(vault: Path) -> list[Finding]:
    dash = vault / "00-meta" / "01-dashboards"
    tmpl = vault / "99-system" / "templates"
    if not dash.is_dir() or not tmpl.is_dir():
        return out_empty()
    known = set(DATAVIEW_BUILTINS)
    for t in tmpl.glob("*.md"):
        known |= template_field_names(read(t))
    out = []
    block_re = re.compile(r"```dataview\b(.*?)```", re.S | re.I)
    for d in dash.glob("*.md"):
        for block in block_re.findall(read(d)):
            frm = re.search(r'FROM\s+"([^"]+)"', block, re.I)
            if not (frm and frm.group(1).strip().startswith(NOTE_FOLDERS)):
                continue   # only note-folder queries can drift on note frontmatter fields
            for line in block.splitlines():
                m = _DV_FIELD_LINE.match(line)
                if not m:
                    continue
                # TABLE col1 AS "x", col2  -> leading identifier of each column
                cols = m.group(2).split(",") if m.group(1).upper() == "TABLE" else [m.group(2)]
                for col in cols:
                    col = re.split(r"\bAS\b", col, flags=re.I)[0]
                    ids = _IDENT.findall(col)
                    if not ids:
                        continue
                    field = ids[0]
                    if field in known or field.lower() in DATAVIEW_KEYWORDS:
                        continue
                    if re.search(rf"\b{re.escape(field)}\.", col):   # dotted built-in, e.g. file.mtime
                        continue
                    if re.search(rf"\.{re.escape(field)}\b", col):   # property access, e.g. rows.length
                        continue
                    if re.search(rf"\b{re.escape(field)}\s*\(", col): # function call, e.g. length(...)
                        continue
                    out.append(Finding("dashboard-field-drift", "HIGH", relpath(vault, d),
                                       f"query references field '{field}' not in any template"))
    return out


def graph_analyze(vault: Path) -> list[Finding]:
    """Knowledge-graph health: orphan synthesis notes (zero inlinks).

    Pure-stdlib graph metrics over the wikilink graph -- in-degree is simple dict
    arithmetic, so no networkx is needed (keeping detectors.py dependency-free).
    Reports claim / reference notes with no incoming wikilinks (excluding MOCs):
    they are unreachable in the graph until something links to them. A self-link
    counts as an inlink -- a minor false-negative accepted for v0.1.

    Hubs, clusters, and link-density are descriptive rather than actionable, so
    they are left out of the report to keep findings to things a human can act on;
    extend here if a graph-stats summary is wanted later."""
    notes = [p for p in iter_notes(vault)
             if not relpath(vault, p).startswith(("00-meta/", "90-assets/"))]
    indeg = {p.stem: 0 for p in notes}
    link_re = re.compile(r"\[\[([^\]|#]+)")
    for p in notes:
        for m in link_re.finditer(read(p)):
            tgt = Path(m.group(1).strip()).stem
            if tgt in indeg:
                indeg[tgt] += 1
    out = []
    synth = ("30-synthesis/01-claims/", "30-synthesis/02-reference/")
    for p in notes:
        rp = relpath(vault, p)
        if not rp.startswith(synth):
            continue
        if parse_frontmatter(read(p)).get("type") == "moc":
            continue
        if indeg.get(p.stem, 0) == 0:
            out.append(Finding("graph-analyze", "LOW", rp,
                               "orphan synthesis note (0 inlinks) -- link it or it stays unreachable"))
    return out


def fama_exposure(vault: Path) -> list[Finding]:
    """FAMA exposure -- a downstream note that wikilinks a *superseded* claim
    (lifecycle: archived, or carrying superseded_by). Reusing obsolete memory is
    the FAMA failure mode the supersession mechanism (ADR-10 / ADR-17) makes
    measurable -- the report's headline novelty turned into a deterministic check."""
    notes = list(iter_notes(vault))
    superseded: dict[str, str] = {}    # claim stem -> its relpath
    for p in notes:
        if not relpath(vault, p).startswith("30-synthesis/01-claims/"):
            continue
        fm = parse_frontmatter(read(p))
        sup = fm.get("superseded_by")
        archived = str(fm.get("lifecycle", "")).strip() == "archived"
        if archived or sup not in (None, "", [], "[]"):
            superseded[p.stem] = relpath(vault, p)
    if not superseded:
        return out_empty()
    link_re = re.compile(r"\[\[([^\]|#]+)")
    out = []
    for p in notes:
        rp = relpath(vault, p)
        # Exposure matters in downstream synthesis; skip scaffolding and the claim
        # graph itself (claim->claim links are the supersession / relations graph).
        if rp.startswith(("00-meta/", "90-assets/", "30-synthesis/01-claims/")):
            continue
        for m in link_re.finditer(read(p)):
            stem = Path(m.group(1).strip()).stem
            if stem in superseded:
                out.append(Finding("fama-exposure", "HIGH", rp,
                                   f"cites superseded claim [[{stem}]] ({superseded[stem]}) -- reuse of obsolete memory"))
    return out


def out_empty() -> list[Finding]:
    return []


DETECTORS = [
    orphan_working_files, stale_fleeting, stale_answer_drafts, extract_path_broken,
    frontmatter_schema_check, broken_wikilinks, dashboard_field_drift, graph_analyze,
    fama_exposure,
]


def run_all(vault: Path) -> list[Finding]:
    findings: list[Finding] = []
    for det in DETECTORS:
        findings += det(vault)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())   # one clock per pass
    for f in findings:
        f.timestamp = now
    return sorted(findings, key=lambda f: (-SEVERITY_RANK[f.severity], f.detector, f.path))


def verdict(findings: list[Finding]) -> str:
    sev = {f.severity for f in findings}
    if "CRITICAL" in sev:
        return "FAIL"
    if "HIGH" in sev or "MEDIUM" in sev:
        return "REVIEW"
    return "PASS"


# --------------------------------------------------------------------------- #
# Self-test -- builds a throwaway vault, asserts each detector fires correctly.
# --------------------------------------------------------------------------- #
def self_test() -> int:
    import tempfile

    failures = 0
    checks_run = 0

    def check(name, cond):
        nonlocal failures, checks_run
        checks_run += 1
        failures += not cond
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")

    with tempfile.TemporaryDirectory() as td:
        v = Path(td)
        # folder skeleton
        for d in ("10-inbox/01-fleeting", "20-sources/01-papers",
                  "30-synthesis/01-claims", "00-meta/01-dashboards",
                  "99-system/templates", "90-assets/extracts"):
            (v / d).mkdir(parents=True, exist_ok=True)

        # clean claim note (no findings)
        (v / "30-synthesis/01-claims/good.md").write_text(
            "---\ntype: claim-note\nlifecycle: current\nmaturity: seedling\n---\nA claim. [[good]]\n",
            encoding="utf-8")
        # claim note missing 'maturity' -> schema finding
        (v / "30-synthesis/01-claims/bad.md").write_text(
            "---\ntype: claim-note\nlifecycle: current\n---\nClaim with a [[ghost]] link.\n",
            encoding="utf-8")
        # leftover file outside transient zone -> orphan finding
        (v / "30-synthesis/01-claims/notes.md.bak").write_text("x", encoding="utf-8")
        # stale fleeting note (8 days old) -> stale finding
        fl = v / "10-inbox/01-fleeting/old.md"
        fl.write_text("idea", encoding="utf-8")
        old = time.time() - 8 * 86400
        import os
        os.utime(fl, (old, old))
        # stale answer draft (100 days old) -> stale-answer-drafts finding
        ad = v / "10-inbox/02-answers/old-answer.md"
        ad.parent.mkdir(parents=True, exist_ok=True)
        ad.write_text("draft answer", encoding="utf-8")
        old_ad = time.time() - 100 * 86400
        os.utime(ad, (old_ad, old_ad))
        # paper note with broken extract_path -> extract finding
        (v / "20-sources/01-papers/p.md").write_text(
            "---\ntype: paper-note\ncitekey: smith2020\nextract_path: 90-assets/extracts/missing.md\n---\n",
            encoding="utf-8")
        # superseded claim + a draft that cites it -> fama-exposure finding
        (v / "30-synthesis/01-claims/oldclaim.md").write_text(
            "---\ntype: claim-note\nlifecycle: archived\nsuperseded_by: newclaim\n---\nOld claim.\n",
            encoding="utf-8")
        dft = v / "40-workbench/proj/04-drafts/draft.md"
        dft.parent.mkdir(parents=True, exist_ok=True)
        dft.write_text("---\ntype: draft\n---\nWe still rely on [[oldclaim]] here.\n", encoding="utf-8")
        # template + dashboard referencing an unknown field -> dashboard finding.
        # The template body carries a placeholder [[link]] (templates are raw notes):
        # broken-wikilink must ignore it now that templates live in 99-system/.
        (v / "99-system/templates/claim-note.md").write_text(
            "---\ntype: claim-note\nlifecycle: current\nmaturity: seedling\n---\n"
            "Example link: [[placeholder-target]]\n", encoding="utf-8")
        # vault-root navigation page: has frontmatter, no type -> NOT a typed note
        (v / "home.md").write_text(
            "---\ncreated: 2026-01-01\ncssclasses:\n  - dashboard\n---\n# Home\n", encoding="utf-8")
        # a real note with a table-escaped aliased link to an existing note ([[good]]):
        # the "\|" must resolve, not read as a broken "good\" target.
        (v / "30-synthesis/01-claims/tablelink.md").write_text(
            "---\ntype: claim-note\nlifecycle: current\nmaturity: seedling\n---\n"
            "| col | [[good\\|Good]] |\n", encoding="utf-8")
        (v / "00-meta/01-dashboards/d.md").write_text(
            "```dataview\nTABLE maturity, projct\nFROM \"30-synthesis\"\nSORT file.mtime DESC\n```\n",
            encoding="utf-8")

        f = run_all(v)
        by = lambda name: [x for x in f if x.detector == name]

        check("orphan-working-files fires on .bak", any("notes.md.bak" in x.path for x in by("orphan-working-files")))
        check("stale-fleeting fires on 8d note", any("old.md" in x.path for x in by("stale-fleeting")))
        check("stale-answer-drafts fires on 100d draft", any("old-answer.md" in x.path for x in by("stale-answer-drafts")))
        check("extract-path-broken fires", any("p.md" in x.path for x in by("extract-path-broken")))
        check("schema-check flags missing maturity", any("bad.md" in x.path for x in by("schema-check")))
        check("schema-check clean note not flagged", not any("good.md" in x.path for x in by("schema-check")))
        check("broken-wikilink flags [[ghost]]", any("ghost" in x.message for x in by("broken-wikilink")))
        check("broken-wikilink ignores valid [[good]]", not any("[[good]]" in x.message for x in by("broken-wikilink")))
        check("broken-wikilink ignores template placeholder link", not any("placeholder-target" in x.message for x in by("broken-wikilink")))
        check("broken-wikilink resolves a table-escaped alias [[good\\|Good]]", not any("tablelink.md" in x.path for x in by("broken-wikilink")))
        check("schema-check exempts vault-root nav page (home.md)", not any("home.md" in x.path for x in by("schema-check")))
        check("dashboard-field-drift flags 'projct'", any("projct" in x.message for x in by("dashboard-field-drift")))
        check("dashboard-field-drift ignores 'maturity'", not any("'maturity'" in x.message for x in by("dashboard-field-drift")))
        check("graph-analyze flags orphan bad.md", any("bad.md" in x.path for x in by("graph-analyze")))
        check("graph-analyze ignores linked good.md", not any("good.md" in x.path for x in by("graph-analyze")))
        check("fama-exposure flags draft citing superseded claim", any("oldclaim" in x.message for x in by("fama-exposure")))
        check("fama-exposure ignores live claim good", not any("good" in x.message for x in by("fama-exposure")))
        check("verdict is REVIEW (HIGH+MEDIUM, no CRITICAL)", verdict(f) == "REVIEW")

    print(f"\n{checks_run - failures}/{checks_run} detector checks passed.")
    return failures


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", type=Path, help="vault root to lint")
    ap.add_argument("--self-test", action="store_true", help="run synthetic-fixture unit tests")
    ap.add_argument("--json", action="store_true", help="emit findings as JSON")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(1 if self_test() else 0)
    if not args.vault:
        ap.error("provide --vault <path> or --self-test")
    if not args.vault.is_dir():
        sys.exit(f"not a directory: {args.vault}")

    findings = run_all(args.vault)
    if args.json:
        print(json.dumps([f.__dict__ for f in findings], indent=2))
    else:
        for f in findings:
            print(f"  [{f.severity:8s}] {f.detector:22s} {f.path}\n             {f.message}")
        print(f"\n  {len(findings)} finding(s) -- verdict: {verdict(findings)}")
    sys.exit(0)


if __name__ == "__main__":
    main()
