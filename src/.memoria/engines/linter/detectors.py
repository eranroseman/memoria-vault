#!/usr/bin/env python3
"""Deterministic vault detectors (zero-LLM) for the Memoria Linter.

Reference implementation of the *self-contained* checks from structural-detectors.md and
the non-LLM toolkit -- the ones that need only the vault tree (no ~/.hermes
deploy, no design-repo git). All checks are REPORT-ONLY; none mutates the vault.

    python "${HERMES_SKILL_DIR}/scripts/detectors.py" --vault <path>     # run against a vault, print findings
    python "${HERMES_SKILL_DIR}/scripts/detectors.py" --vault <path> --json

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
TRANSIENT_PREFIXES = ("inbox/", "system/logs/", "system/board/")
# A typed note legitimately leaves its type-home only while it is work-in-flight
# (inbox/workbench/logs) or after it is archived; the misplaced-note detector
# skips both so it never flags those moves.
MISPLACED_SKIP_PREFIXES = TRANSIENT_PREFIXES
# Canonical type -> expected folder prefix (docs/explanation/architecture/vault.md,
# ADR-11/ADR-30). The entity rows mirror ENTITY_FOLDER in the Librarian's link.py.
TYPE_HOME = {
    "paper": "catalog/papers/",
    "person": "catalog/people/",
    "organization": "catalog/organizations/",
    "venue": "catalog/venues/",
    "dataset": "catalog/datasets/",
    "repository": "catalog/repositories/",
    "fleeting": "notes/fleeting/",
    "source": "notes/source/",
    "claim": "notes/claims/",
    "hub": "notes/hubs/",
    "index": "notes/index/",
    "candidate": "inbox/",
    "gap": "inbox/",
    "flag": "inbox/",
    "alert": "inbox/",
    "pattern": "system/patterns/",
}
# Top-level folders the vault schema permits; anything else at the root is stray.
KNOWN_TOP_DIRS = {
    "catalog", "notes", "projects", "inbox", "system",
}
# Scaffolding, not authored notes: skeleton folders, assets, and the note
# templates (raw notes full of placeholder [[links]]). Detectors that assert
# things about *real* notes (broken wikilinks, type schema) skip these. Templates
# templates live in system/templates/ (ADR-47);
# keep this the single source of truth so the skip can't drift from the move.
SCAFFOLD_PREFIXES = ("system/templates/", "system/dashboards/", "system/patterns/")


def is_untyped_infra(rp: str) -> bool:
    """system/ holds infrastructure documents, not typed knowledge — only
    system/patterns/ files carry a type schema (ADR-53)."""
    return rp.startswith("system/") and not rp.startswith("system/patterns/")
LEFTOVER_PATTERNS = [
    re.compile(p) for p in (
        r".*\.tmp\..*", r".*\.OLD\..*", r".*\.lessOLD\..*", r".*\.bak$",
        r".*~$", r"\.#.*", r".*\.orig$", r".*\.rej$",
    )
]
# Per-type required frontmatter fields (minimal; extend as the schema firms up).
REQUIRED_FIELDS = {
    "claim": ["lifecycle", "maturity"],
    "paper": ["citekey"],
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
# (cards) or system logs/metrics (JSONL) drift on different schemas, not this one.
NOTE_FOLDERS = ("catalog", "notes", "inbox", "projects")

# --------------------------------------------------------------------------- #
# Canonical schemas (ADR-49): when .memoria/schemas/ + PyYAML are available the
# constants above are *derived* from the one schema home; the hardcodes remain
# the dependency-free fallback so the engine still runs without PyYAML.
# --------------------------------------------------------------------------- #
TYPE_SCHEMAS: dict | None = None
_FOLDERS: dict | None = None
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
    import schema as _schema

    TYPE_SCHEMAS = _schema.load_types()
    _FOLDERS = _schema.load_folders()
    TYPE_HOME = {n: _schema.home_for(n, _FOLDERS).rstrip("/") + "/" for n in TYPE_SCHEMAS}
    KNOWN_TOP_DIRS = set(_FOLDERS["categories"])
except Exception:                                  # pragma: no cover - fallback path
    _schema = None

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
    """YAML frontmatter parser: PyYAML when available (full fidelity — nested
    maps and ints matter for schema validation), else the minimal hand parser
    (top-level scalars + inline lists) so the engine stays runnable without it."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    if _schema is not None:                       # PyYAML proven importable
        try:
            import yaml

            data = yaml.safe_load(text[3:end])
            return data if isinstance(data, dict) else {}
        except Exception:
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
    folder = vault / "notes" / "fleeting"
    if not folder.is_dir():
        return out
    for p in folder.rglob("*.md"):  # recursive: subfolders (e.g. chats/, the ACP-export home) count too
        if p.stat().st_mtime < cutoff:
            age_d = (time.time() - p.stat().st_mtime) / 86400
            out.append(Finding("stale-fleeting", "LOW", relpath(vault, p),
                               f"fleeting note {age_d:.0f}d old (>{days}d); promote or discard"))
    return out


def stale_answer_drafts(vault: Path, days: int = 90) -> list[Finding]:
    """Flag unreviewed answer drafts older than `days` (folder retired in v0.1.1).

    REPORT-ONLY by design: the human decides keep / promote / discard in the
    weekly review. Never auto-archive -- the most useful drafts are often the
    ones not yet gotten to, so silent archival would hide them exactly when
    they're most likely to be needed. (Formerly proposed as ADR-3, answer-draft
    retention; realized here as a report-only check rather than a decision.)"""
    out, cutoff = [], time.time() - days * 86400
    folder = vault / "inbox" / "_answers"
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
    papers = vault / "catalog" / "papers"
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
        if is_untyped_infra(rp):               # system infra isn't typed knowledge
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
        if TYPE_SCHEMAS is not None:
            sc = TYPE_SCHEMAS.get(ntype)
            if sc is None:
                out.append(Finding("schema-check", "MEDIUM", rp,
                                   f"unknown type '{ntype}' (no schema in .memoria/schemas/types/)"))
                continue
            for err in _schema.validate_frontmatter(fm, sc):
                out.append(Finding("schema-check", "MEDIUM", rp, f"{ntype}: {err}"))
        else:
            for field in REQUIRED_FIELDS.get(ntype, []):
                if field not in fm:
                    out.append(Finding("schema-check", "MEDIUM", rp,
                                       f"{ntype} missing required field '{field}'"))
    return out


_WIKI_VAL = re.compile(r"\[\[([^\]|#]+)")


def frontmatter_link_check(vault: Path) -> list[Finding]:
    """Authored connections must resolve (ADR-52): every wikilink inside the
    `links:` map and the `entity` field points at a real note. Citekeys in
    `sources` are bibliographic, not note links -- checked by the sweeps, not here."""
    notes = list(iter_notes(vault))
    stems = {q.stem for q in notes}
    out = []
    for p in notes:
        rp = relpath(vault, p)
        if is_untyped_infra(rp) or "/" not in rp:
            continue
        fm = parse_frontmatter(read(p))
        targets: list[str] = []
        links = fm.get("links")
        if isinstance(links, dict):
            for vals in links.values():
                for v in vals if isinstance(vals, list) else [vals]:
                    if isinstance(v, str):
                        targets += _WIKI_VAL.findall(v) or ([v] if v else [])
        ent = fm.get("entity")
        if isinstance(ent, str) and ent:
            targets += _WIKI_VAL.findall(ent) or [ent]
        for tgt in targets:
            stem = Path(tgt.strip().rstrip("\\")).stem
            if stem and stem not in stems:
                out.append(Finding("frontmatter-link", "MEDIUM", rp,
                                   f"frontmatter link [[{tgt.strip()}]] resolves to no note"))
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
            last = target.split("/")[-1]
            if "." in last and not last.endswith(".md"):
                continue   # non-note target (.base/.canvas/image embed), not a wikilink
            stem = Path(target).stem
            if stem not in stems:
                out.append(Finding("broken-wikilink", "MEDIUM", relpath(vault, p),
                                   f"wikilink [[{target}]] resolves to no note"))
    return out


_DV_FIELD_LINE = re.compile(r"^\s*(TABLE|SORT|GROUP BY|FLATTEN)\s+(.*)$", re.I)
_IDENT = re.compile(r"[A-Za-z_][\w-]*")


def dashboard_field_drift(vault: Path) -> list[Finding]:
    dash = vault / "system" / "dashboards"
    tmpl = vault / "system" / "templates"
    if not dash.is_dir() or not tmpl.is_dir():
        return []
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
             if not relpath(vault, p).startswith(("system/",))]
    indeg = {p.stem: 0 for p in notes}
    link_re = re.compile(r"\[\[([^\]|#]+)")
    for p in notes:
        for m in link_re.finditer(read(p)):
            tgt = Path(m.group(1).strip()).stem
            if tgt in indeg:
                indeg[tgt] += 1
    out = []
    synth = ("notes/claims/", "notes/hubs/")
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
        if not relpath(vault, p).startswith("notes/claims/"):
            continue
        fm = parse_frontmatter(read(p))
        sup = fm.get("superseded_by")
        archived = str(fm.get("lifecycle", "")).strip() == "archived"
        if archived or sup not in (None, "", [], "[]"):
            superseded[p.stem] = relpath(vault, p)
    if not superseded:
        return []
    link_re = re.compile(r"\[\[([^\]|#]+)")
    out = []
    for p in notes:
        rp = relpath(vault, p)
        # Exposure matters in downstream synthesis; skip scaffolding and the claim
        # graph itself (claim->claim links are the supersession / relations graph).
        if rp.startswith(("system/", "notes/claims/")):
            continue
        for m in link_re.finditer(read(p)):
            stem = Path(m.group(1).strip()).stem
            if stem in superseded:
                out.append(Finding("fama-exposure", "HIGH", rp,
                                   f"cites superseded claim [[{stem}]] ({superseded[stem]}) -- reuse of obsolete memory"))
    return out


def misplaced_note(vault: Path) -> list[Finding]:
    """A typed note (or stray top-level folder) outside its schema home.

    Report-only, mirroring fama-exposure / broken-wikilinks discipline -- never
    auto-move; the human decides. Skips scaffolding (templates/assets/skeleton),
    vault-root nav pages, and the work-in-flight / archive zones where a note
    legitimately lives outside its type-home (see MISPLACED_SKIP_PREFIXES)."""
    out = []
    for p in iter_notes(vault):
        rp = relpath(vault, p)
        if is_untyped_infra(rp) or "/" not in rp:
            continue
        if rp.startswith(MISPLACED_SKIP_PREFIXES):
            continue
        ntype = parse_frontmatter(read(p)).get("type")
        home = TYPE_HOME.get(ntype)
        if home and not rp.startswith(home):
            out.append(Finding("misplaced-note", "MEDIUM", rp,
                               f"{ntype} should live under {home}"))
    # Stray top-level folders: any vault-root dir outside the numbered schema set.
    for d in vault.iterdir():
        if d.is_dir() and d.name not in SKIP_DIRS and d.name not in KNOWN_TOP_DIRS:
            out.append(Finding("misplaced-note", "LOW", relpath(vault, d),
                               "stray top-level folder not in the vault schema"))
    return out


DETECTORS = [
    orphan_working_files, stale_fleeting, stale_answer_drafts, extract_path_broken,
    frontmatter_schema_check, frontmatter_link_check, broken_wikilinks,
    dashboard_field_drift, graph_analyze, fama_exposure, misplaced_note,
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
# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", type=Path, help="vault root to lint")
    ap.add_argument("--json", action="store_true", help="emit findings as JSON")
    ap.add_argument("--gate", metavar="DETECTORS",
                    help="comma-separated detector names that MUST be zero; exit 1 if any "
                         "such finding exists (e.g. dashboard-field-drift). All other "
                         "findings stay advisory — printed, not fatal.")
    args = ap.parse_args()

    if not args.vault:
        ap.error("provide --vault <path>")
    if not args.vault.is_dir():
        sys.exit(f"not a directory: {args.vault}")

    findings = run_all(args.vault)
    if args.json:
        print(json.dumps([f.__dict__ for f in findings], indent=2))
    else:
        for f in findings:
            print(f"  [{f.severity:8s}] {f.detector:22s} {f.path}\n             {f.message}")
        print(f"\n  {len(findings)} finding(s) -- verdict: {verdict(findings)}")

    # --gate: only the named detectors block; content findings remain advisory.
    if args.gate:
        gated_names = {n.strip() for n in args.gate.split(",") if n.strip()}
        blocking = [f for f in findings if f.detector in gated_names]
        if blocking:
            print(f"\n  GATE FAIL: {len(blocking)} finding(s) from "
                  f"{{{', '.join(sorted(gated_names))}}} must be zero.")
            sys.exit(1)
        print(f"\n  gate clean ✓ ({', '.join(sorted(gated_names))})")
    sys.exit(0)


if __name__ == "__main__":
    main()
