#!/usr/bin/env python3
"""Deterministic vault detectors (zero-LLM) for the Memoria Linter.

Reference implementation of the *self-contained* checks from structural-detectors.md and
the non-LLM toolkit -- the ones that need only the vault tree, not runtime host
state or design-repo git. All checks are REPORT-ONLY; none mutates the vault.

    python detectors.py --vault <path>     # run against a vault, print findings
    python detectors.py --vault <path> --json
    python detectors.py --vault <path> --jsonl-out system/logs/lint-findings.jsonl

The drift procedures in scope here (ADR-67): skeleton-drift and vault-hash-drift
need only the vault tree and live here. Profile-install-drift and
command-vocab-drift are out of scope -- they are repo/package concerns, not
vault-side linter checks.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.jsonl import append_jsonl
from memoria_vault.runtime.subsystems.integrity.linter.detectors_audit import (
    audit_log_size,
    audit_unpaired_writes,
    vault_hash_drift,
)
from memoria_vault.runtime.subsystems.integrity.linter.detectors_design import design_system_drift
from memoria_vault.runtime.vaultio import parse_frontmatter, retired_frontmatter_field_errors

SKIP_DIRS = {".githooks", ".obsidian", ".git", ".memoria", "node_modules"}
TRANSIENT_PREFIXES = (".memoria/staging/", ".memoria/quarantine/", "system/logs/", "inbox/")
# A typed document legitimately leaves its type-home only while it is work-in-flight
# (inbox/workbench/logs) or after it is archived; the misplaced-note detector
# skips both so it never flags those moves.
MISPLACED_SKIP_PREFIXES = TRANSIENT_PREFIXES
TYPE_HOME = {
    "source": "catalog/sources/",
    "person": "catalog/entities/",
    "organization": "catalog/entities/",
    "venue": "catalog/entities/",
    "work": "knowledge/works/",
    "note": "knowledge/notes/",
    "hub": "knowledge/hubs/",
    "project": "knowledge/projects/",
}
# Top-level folders the vault schema permits; anything else at the root is stray.
KNOWN_TOP_DIRS = {"catalog", "knowledge", "spaces", "system", "inbox"}
# Scaffolding, not authored documents: skeleton folders, assets, and the
# templates (raw Markdown full of placeholder [[links]]). Detectors that assert
# things about *real* documents (broken wikilinks, type schema) skip these.
# Templates live in system/templates/ (ADR-47);
# keep this the single source of truth so the skip can't drift from the move.
SCAFFOLD_PREFIXES = ("system/templates/", "system/dashboards/", "system/patterns/")


def is_untyped_infra(rp: str) -> bool:
    """Infrastructure, navigation, and attention projections are not Concepts."""
    return rp.startswith(("catalog/", "spaces/", "system/", "inbox/"))


LEFTOVER_PATTERNS = [
    re.compile(p)
    for p in (
        r".*\.tmp\..*",
        r".*\.OLD\..*",
        r".*\.lessOLD\..*",
        r".*\.bak$",
        r".*~$",
        r"\.#.*",
        r".*\.orig$",
        r".*\.rej$",
    )
]
REQUIRED_FIELDS = {
    "work": ["id", "title", "tags", "links", "work_id"],
    "note": ["id", "title", "tags", "links"],
    "hub": ["id", "title", "tags", "links", "tag"],
    "project": ["id", "title", "tags", "links"],
}
DATAVIEW_BUILTINS = {
    "file",
    "rows",
    "type",
    "tags",
    "tag",
    "true",
    "false",
    "null",
}
# Dataview query keywords -- not fields. (TABLE WITHOUT ID ..., FROM, WHERE, AS, ...)
DATAVIEW_KEYWORDS = {
    "without",
    "id",
    "from",
    "where",
    "as",
    "flatten",
    "group",
    "by",
    "sort",
    "limit",
    "asc",
    "desc",
    "table",
    "list",
    "task",
    "and",
    "or",
    "not",
    "reverse",
}
# Only queries over these folders read *note frontmatter*; queries over the board
# (cards) or system logs/metrics (JSONL) drift on different schemas, not this one.
NOTE_FOLDERS = ("catalog", "knowledge")
# Canonical schemas (ADR-122): when .memoria/schemas/ + PyYAML are available the
# constants above are *derived* from the one schema home; the hardcodes remain
# the dependency-free fallback so the operation still runs without PyYAML.
TYPE_SCHEMAS: dict | None = None
_FOLDERS: dict | None = None
_VOCABULARY_BY_VAULT: dict[Path, dict[str, set[str]]] = {}
try:
    from memoria_vault.runtime.subsystems.lib import schema as _schema

    TYPE_SCHEMAS = _schema.load_types()
    _FOLDERS = _schema.load_folders()
    TYPE_HOME = {n: _schema.home_for(n, _FOLDERS).rstrip("/") + "/" for n in TYPE_SCHEMAS}
    KNOWN_TOP_DIRS = set(_FOLDERS["bundle_roots"])
    KNOWN_TOP_DIRS |= {str(path).split("/", 1)[0] for path in _FOLDERS.get("skeleton") or []}
    KNOWN_TOP_DIRS |= {
        str(path).strip("/").split("/", 1)[0]
        for path in _FOLDERS.get("transient_prefixes") or []
        if str(path).strip("/")
    }
    KNOWN_TOP_DIRS.add("spaces")
except Exception:  # noqa: BLE001 -- dependency-free fallback when schemas cannot load
    _schema = None

SEVERITY_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}


@dataclass
class Finding:
    detector: str
    severity: str
    path: str
    message: str
    timestamp: str = ""  # ISO-8601 UTC; stamped per lint pass in run_all()


def iter_files(vault: Path):
    """Yield every file under vault, skipping SKIP_DIRS.

    Prunes skipped directories DURING the walk (os.walk dirnames surgery)
    rather than filtering rglob output afterwards: rglob still stats every
    file inside .memoria/.venv and .git, which on a Windows-mounted vault
    (WSL 9p) turns the daily lint cron into a minutes-long crawl."""
    import os

    for dirpath, dirnames, filenames in os.walk(vault):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in sorted(filenames):
            yield Path(dirpath) / name


def iter_notes(vault: Path):
    for p in iter_files(vault):
        if p.suffix == ".md":
            yield p


def relpath(vault: Path, p: Path) -> str:
    return p.relative_to(vault).as_posix()


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ""


_FM_KEY = re.compile(r"^\s*([A-Za-z_][\w-]*)\s*:", re.M)


def all_frontmatter_keys(text: str) -> set[str]:
    """Every field name declared in the frontmatter at *any* nesting depth.

    Unlike parse_frontmatter (top-level only), this captures keys nested under
    blocks like `_proposed_classification:` -- which is where source and note
    Concepts keep `topics`, `research_area`, `methodology`, etc."""
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
        if "type:" in block or "---" in block:  # a frontmatter example block
            keys |= set(_FM_KEY.findall(block))
    return keys


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
                out.append(
                    Finding(
                        "orphan-working-files",
                        "LOW",
                        rp,
                        f"leftover file (matches /{pat.pattern}/), {age_d:.0f}d old",
                    )
                )
                break
    return out


def stale_fleeting(vault: Path, days: int = 7) -> list[Finding]:
    out, cutoff = [], time.time() - days * 86400
    folder = vault / "notes" / "fleeting"
    if not folder.is_dir():
        return out
    for p in folder.rglob(
        "*.md"
    ):  # recursive: subfolders (e.g. chats/, the ACP-export home) count too
        if p.stat().st_mtime < cutoff:
            age_d = (time.time() - p.stat().st_mtime) / 86400
            out.append(
                Finding(
                    "stale-fleeting",
                    "LOW",
                    relpath(vault, p),
                    f"fleeting note {age_d:.0f}d old (>{days}d); promote or discard",
                )
            )
    return out


def stale_answer_drafts(vault: Path, days: int = 90) -> list[Finding]:
    """Flag unreviewed answer drafts older than `days` (folder retired in v0.1.0-alpha.2).

    REPORT-ONLY by design: the human decides keep / promote / discard in the
    weekly review. Never auto-archive -- the most useful drafts are often the
    ones not yet gotten to, so silent archival would hide them exactly when
    they're most likely to be needed. (Formerly proposed as ADR-128, answer-draft
    retention; realized here as a report-only check rather than a decision.)"""
    out, cutoff = [], time.time() - days * 86400
    folder = vault / "inbox" / "_answers"
    if not folder.is_dir():
        return out
    for p in folder.glob("*.md"):
        if p.stat().st_mtime < cutoff:
            age_d = (time.time() - p.stat().st_mtime) / 86400
            out.append(
                Finding(
                    "stale-answer-drafts",
                    "LOW",
                    relpath(vault, p),
                    f"answer draft {age_d:.0f}d old (>{days}d); keep, promote, or discard",
                )
            )
    return out


def frontmatter_schema_check(vault: Path) -> list[Finding]:
    out = []
    vocabulary_terms = None
    if _schema is not None:
        vocabulary_terms = _VOCABULARY_BY_VAULT.setdefault(
            vault, _schema.load_vocabulary(vault / "system" / "vocabulary.md")
        )
    for p in iter_notes(vault):
        rp = relpath(vault, p)
        if is_untyped_infra(rp):  # system infra isn't typed knowledge
            continue
        if "/" not in rp:  # vault-root pages are navigation, not typed documents
            continue
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
                out.append(
                    Finding(
                        "schema-check",
                        "MEDIUM",
                        rp,
                        f"unknown type '{ntype}' (no schema in .memoria/schemas/types/)",
                    )
                )
                continue
            for err in retired_frontmatter_field_errors(fm):
                out.append(Finding("schema-check", "LOW", rp, err))
            for err in _schema.validate_frontmatter(fm, sc, vocabulary_terms):
                out.append(Finding("schema-check", "MEDIUM", rp, f"{ntype}: {err}"))
        else:
            for field in REQUIRED_FIELDS.get(ntype, []):
                if field not in fm:
                    out.append(
                        Finding(
                            "schema-check",
                            "MEDIUM",
                            rp,
                            f"{ntype} missing required field '{field}'",
                        )
                    )
    return out


_WIKI_VAL = re.compile(r"\[\[([^\]|#]+)")


def frontmatter_link_check(vault: Path) -> list[Finding]:
    """Authored connections must resolve (ADR-126): every wikilink inside the
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
                out.append(
                    Finding(
                        "frontmatter-link",
                        "MEDIUM",
                        rp,
                        f"frontmatter link [[{tgt.strip()}]] resolves to no note",
                    )
                )
    return out


def broken_wikilinks(vault: Path) -> list[Finding]:
    notes = list(iter_notes(vault))
    stems = {p.stem for p in notes}
    link_re = re.compile(r"\[\[([^\]|#]+)")
    out = []
    for p in notes:
        rp = relpath(vault, p)
        if rp.startswith(SCAFFOLD_PREFIXES):  # scaffolding: example/placeholder links
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
                continue  # non-note target (.base/.canvas/image embed), not a wikilink
            stem = Path(target).stem
            if stem not in stems:
                out.append(
                    Finding(
                        "broken-wikilink",
                        "MEDIUM",
                        relpath(vault, p),
                        f"wikilink [[{target}]] resolves to no note",
                    )
                )
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
                continue  # only note-folder queries can drift on note frontmatter fields
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
                    if re.search(
                        rf"\b{re.escape(field)}\.", col
                    ):  # dotted built-in, e.g. file.mtime
                        continue
                    if re.search(
                        rf"\.{re.escape(field)}\b", col
                    ):  # property access, e.g. rows.length
                        continue
                    if re.search(
                        rf"\b{re.escape(field)}\s*\(", col
                    ):  # function call, e.g. length(...)
                        continue
                    out.append(
                        Finding(
                            "dashboard-field-drift",
                            "HIGH",
                            relpath(vault, d),
                            f"query references field '{field}' not in any template",
                        )
                    )
    return out


def graph_analyze(vault: Path) -> list[Finding]:
    """Knowledge-graph health: orphan synthesis notes (zero inlinks).

    Pure-stdlib graph metrics over the wikilink graph -- in-degree is simple dict
    arithmetic, so no networkx is needed (keeping detectors.py dependency-free).
    Reports knowledge records with no incoming wikilinks: they are
    unreachable in the graph until something links to them. A self-link
    counts as an inlink -- a minor false-negative accepted for v0.1.

    Hubs, clusters, and link-density are descriptive rather than actionable, so
    they are left out of the report to keep findings to things a human can act on;
    extend here if a graph-stats summary is wanted later."""
    notes = [p for p in iter_notes(vault) if not relpath(vault, p).startswith(("system/",))]
    indeg = {p.stem: 0 for p in notes}
    link_re = re.compile(r"\[\[([^\]|#]+)")
    for p in notes:
        for m in link_re.finditer(read(p)):
            tgt = Path(m.group(1).strip()).stem
            if tgt in indeg:
                indeg[tgt] += 1
    out = []
    synth = ("knowledge/works/", "knowledge/notes/", "knowledge/hubs/")
    for p in notes:
        rp = relpath(vault, p)
        if not rp.startswith(synth):
            continue
        if indeg.get(p.stem, 0) == 0:
            out.append(
                Finding(
                    "graph-analyze",
                    "LOW",
                    rp,
                    "orphan synthesis note (0 inlinks) -- link it or it stays unreachable",
                )
            )
    return out


def fama_exposure(vault: Path) -> list[Finding]:
    """FAMA exposure: a downstream note wikilinks a superseded note."""
    notes = list(iter_notes(vault))
    superseded: dict[str, str] = {}
    for p in notes:
        if not relpath(vault, p).startswith("knowledge/notes/"):
            continue
        fm = parse_frontmatter(read(p))
        sup = fm.get("superseded_by")
        status = str(fm.get("status", "")).strip()
        if status == "superseded" or sup not in (None, "", [], "[]"):
            superseded[p.stem] = relpath(vault, p)
    if not superseded:
        return []
    link_re = re.compile(r"\[\[([^\]|#]+)")
    out = []
    for p in notes:
        rp = relpath(vault, p)
        if rp.startswith(("system/", "knowledge/notes/")):
            continue
        for m in link_re.finditer(read(p)):
            stem = Path(m.group(1).strip()).stem
            if stem in superseded:
                out.append(
                    Finding(
                        "fama-exposure",
                        "HIGH",
                        rp,
                        f"cites superseded note [[{stem}]] ({superseded[stem]})",
                    )
                )
    return out


def misplaced_note(vault: Path) -> list[Finding]:
    """A typed document (or stray top-level folder) outside its schema home.

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
            out.append(Finding("misplaced-note", "MEDIUM", rp, f"{ntype} should live under {home}"))
    # Stray top-level folders: any vault-root dir outside the numbered schema set.
    for d in vault.iterdir():
        if d.is_dir() and d.name not in SKIP_DIRS and d.name not in KNOWN_TOP_DIRS:
            out.append(
                Finding(
                    "misplaced-note",
                    "LOW",
                    relpath(vault, d),
                    "stray top-level folder not in the vault schema",
                )
            )
    return out


def hub_threshold(vault: Path, threshold: int = 15) -> list[Finding]:
    """A topic crossed the hub-creation threshold with no hub (ADR-126 Tier 1).

    Report-only: counts catalog Works and notes per topic/tag term and flags
    any term with >= `threshold` records that no existing hub already covers.
    Never auto-creates -- the finding suggests the PI consider a hub."""
    counts: dict[str, int] = {}
    label: dict[str, str] = {}  # lowercased term -> display form
    hubbed: set[str] = set()
    for p in iter_notes(vault):
        rp = relpath(vault, p)
        if rp.startswith(SCAFFOLD_PREFIXES):
            continue
        fm = parse_frontmatter(read(p))
        if fm.get("type") == "hub":
            for v in (fm.get("title"), *(fm.get("tags") or [])):
                if isinstance(v, str) and v.strip():
                    hubbed.add(v.strip().lower())
            continue
        if not rp.startswith("knowledge/notes/"):
            continue
        terms: list[str] = []
        for field in ("topics", "tags", "research_area"):
            v = fm.get(field)
            if isinstance(v, list):
                terms += [t for t in v if isinstance(t, str)]
            elif isinstance(v, str):
                terms.append(v)
        for t in {t.strip() for t in terms if t.strip()}:
            key = t.lower()
            counts[key] = counts.get(key, 0) + 1
            label.setdefault(key, t)
    for source in state.catalog_sources(vault):
        for term in _catalog_source_terms(source):
            key = term.lower()
            counts[key] = counts.get(key, 0) + 1
            label.setdefault(key, term)
    out = []
    for key in sorted(counts):
        if counts[key] >= threshold and key not in hubbed:
            out.append(
                Finding(
                    "hub-threshold",
                    "LOW",
                    "knowledge/hubs/",
                    f"topic '{label[key]}' has {counts[key]} notes "
                    f"(threshold {threshold}) and no hub -- consider creating one",
                )
            )
    return out


def _catalog_source_terms(source: dict[str, object]) -> list[str]:
    csl = source.get("csl_json") if isinstance(source.get("csl_json"), dict) else {}
    memoria = csl.get("memoria") if isinstance(csl.get("memoria"), dict) else {}
    out = []
    for field in ("tags", "topics", "research_area"):
        value = memoria.get(field)
        if isinstance(value, list):
            out.extend(term for term in value if isinstance(term, str) and term.strip())
        elif isinstance(value, str) and value.strip():
            out.append(value)
    return sorted(set(out))


def skeleton_drift(vault: Path) -> list[Finding]:
    """A folder from the installer skeleton is missing from the vault.

    Verifies the `skeleton` list of `.memoria/schemas/folders.yaml` exists as
    directories in the vault. The fix is mechanical -- re-run the installer or create the dir --
    so the finding is MEDIUM, not CRITICAL. Needs the schema home + PyYAML;
    without them (the dependency-free fallback path) the check is skipped.

    Only meaningful for an *installed* vault: the repo's src/ tree deliberately
    ships no empty dirs, so the check keys on the vault Git repo the installer
    creates -- absent `.git`, no skeleton was ever scaffolded, and the check is skipped."""
    if _FOLDERS is None:
        return []
    if not (vault / ".git").is_dir():
        return []
    out = []
    for d in _FOLDERS.get("skeleton") or []:
        if not (vault / d).is_dir():
            out.append(
                Finding(
                    "skeleton-drift",
                    "MEDIUM",
                    d,
                    "skeleton folder missing -- re-run the installer "
                    "(idempotent) or create the directory",
                )
            )
    return out


DETECTORS = [
    orphan_working_files,
    stale_fleeting,
    stale_answer_drafts,
    frontmatter_schema_check,
    frontmatter_link_check,
    broken_wikilinks,
    dashboard_field_drift,
    graph_analyze,
    fama_exposure,
    misplaced_note,
    audit_unpaired_writes,
    vault_hash_drift,
    design_system_drift,
    audit_log_size,
    hub_threshold,
    skeleton_drift,
]


def run_all(vault: Path) -> list[Finding]:
    findings: list[Finding] = []
    for det in DETECTORS:
        findings += det(vault)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())  # one clock per pass
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


def append_findings_jsonl(path: Path, findings: list[Finding]) -> None:
    """Append one row per finding and create the file for clean no-data runs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    append_jsonl(path, [finding.__dict__ for finding in findings])


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--vault", type=Path, help="vault root to lint")
    ap.add_argument("--json", action="store_true", help="emit findings as JSON")
    ap.add_argument(
        "--jsonl-out",
        type=Path,
        help="append findings as JSONL to this file; creates an empty file when clean",
    )
    ap.add_argument(
        "--gate",
        metavar="DETECTORS",
        help="comma-separated detector names that MUST be zero; exit 1 if any "
        "such finding exists (e.g. dashboard-field-drift). All other "
        "findings stay advisory — printed, not fatal.",
    )
    args = ap.parse_args()

    if not args.vault:
        ap.error("provide --vault <path>")
    if not args.vault.is_dir():
        sys.exit(f"not a directory: {args.vault}")

    findings = run_all(args.vault)
    if args.jsonl_out:
        append_findings_jsonl(args.jsonl_out, findings)
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
            print(
                f"\n  GATE FAIL: {len(blocking)} finding(s) from "
                f"{{{', '.join(sorted(gated_names))}}} must be zero."
            )
            sys.exit(1)
        print(f"\n  gate clean ✓ ({', '.join(sorted(gated_names))})")
    sys.exit(0)


if __name__ == "__main__":
    main()
