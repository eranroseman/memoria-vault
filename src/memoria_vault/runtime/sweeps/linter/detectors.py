"""Deterministic vault detectors (zero-LLM) for the Memoria Linter.

Reference implementation of the *self-contained* checks from structural-detectors.md and
the non-LLM toolkit -- the ones that need only the vault tree, not runtime host
state or design-repo git. All checks are REPORT-ONLY; none mutates the vault.

    python detectors.py --vault <path>     # run against a vault, print findings
    python detectors.py --vault <path> --json
    python detectors.py --vault <path> --jsonl-out system/logs/lint-findings.jsonl

The drift procedures in scope here, skeleton-drift and vault-hash-drift, need
only the vault tree and live here. Profile-install-drift and command-vocab-drift
are out of scope -- they are repo/package concerns, not vault-side linter checks.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.jsonl import append_jsonl
from memoria_vault.runtime.sweeps.linter.detectors_audit import (
    Finding,
    audit_log_size,
    audit_unpaired_writes,
    read,
    vault_hash_drift,
)
from memoria_vault.runtime.vaultio import parse_frontmatter, retired_frontmatter_field_errors
from memoria_vault.runtime.vocabulary import schema

# Host and tool state, not vault content. `memoria init` seeds .obsidian, .claude
# and .codex, so leaving any of them out means the linter flags the product's own
# output as a stray folder on every vault it creates. Also prunes the walk (see
# iter_files), which is why the list is worth keeping tight.
SKIP_DIRS = {".githooks", ".obsidian", ".claude", ".codex", ".git", ".memoria", "node_modules"}
# Only paths the walk can actually reach: `.memoria/` is in SKIP_DIRS, so
# prefixes under it filter nothing (test_walk_never_reaches_skipped_dirs pins
# that). `.memoria/staging/`, `.memoria/quarantine/` and a `.memoria/patterns/`
# scaffolding tuple used to be listed here and read as live protection.
TRANSIENT_PREFIXES = ("system/logs/", "inbox/")
# A typed document legitimately leaves its type-home only while it is work-in-flight
# (inbox/workbench/logs) or after it is archived; the misplaced-note detector
# skips both so it never flags those moves.
MISPLACED_SKIP_PREFIXES = TRANSIENT_PREFIXES


# Project working documents. They declare their own `type` so the whole tree
# stays OKF-conformant (design spec §12.3 counts them as Concept documents for
# export shape), but no per-type schema claims them and none ever becomes a
# knowledge-graph node, so the Concept detectors must not read them as Concepts.
PROJECT_WORKING_FILES = {"outline.md", "draft.md"}


def is_untyped_infra(rp: str) -> bool:
    """Infrastructure, navigation, attention, and project working docs are not Concepts.

    The working-doc exemption is scoped to `projects/<slug>/` deliberately: a
    note the PI happens to name `notes/draft.md` is still a Concept and must
    not silently drop out of the Concept detectors.
    """
    if rp.startswith(("system/", "inbox/")):
        return True
    parts = rp.split("/")
    return len(parts) == 3 and parts[0] == "projects" and parts[2] in PROJECT_WORKING_FILES


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
SEVERITY_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}


def _vault_schema_contract(
    vault: Path,
) -> tuple[tuple[dict, dict, dict[str, set[str]]] | None, str]:
    """Load the explicit schema contract for one vault without package fallback."""
    vault = Path(vault)
    schemas_dir = vault / ".memoria/schemas"
    if not schemas_dir.is_dir():
        return None, "missing required schema directory"
    try:
        types = schema.load_types(schemas_dir)
        folders = schema.load_folders(schemas_dir)
        vocabulary = schema.load_vocabulary(vault / "system/vocabulary.md", schemas_dir)
    except Exception as exc:  # noqa: BLE001 -- malformed vault contract must become a finding
        return None, str(exc) or exc.__class__.__name__
    return (types, folders, vocabulary), ""


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


def orphan_working_files(vault: Path) -> list[Finding]:
    out: list[Finding] = []
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
    out: list[Finding] = []
    cutoff = time.time() - days * 86400
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
    they're most likely to be needed."""
    out: list[Finding] = []
    cutoff = time.time() - days * 86400
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
    contract, error = _vault_schema_contract(vault)
    if contract is None:
        return [Finding("schema-check", "MEDIUM", ".memoria/schemas", error)]
    types, _folders, vocabulary_terms = contract
    out = []
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
        sc = types.get(ntype)
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
        for err in schema.validate_frontmatter(fm, sc, vocabulary_terms):
            out.append(Finding("schema-check", "MEDIUM", rp, f"{ntype}: {err}"))
    return out


_WIKI_VAL = re.compile(r"\[\[([^\]|#]+)")


def frontmatter_link_check(vault: Path) -> list[Finding]:
    """Authored connections must resolve: every wikilink inside the
    `links:` map points at a real note. Citekeys in `sources` are
    bibliographic, not note links -- checked by the sweeps, not here."""
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
    out = []
    for p in notes:
        for m in _WIKI_VAL.finditer(read(p)):
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
    for p in notes:
        for m in _WIKI_VAL.finditer(read(p)):
            tgt = Path(m.group(1).strip()).stem
            if tgt in indeg:
                indeg[tgt] += 1
    out = []
    synth = ("notes/", "hubs/", "projects/", "digests/", "fulltexts/")
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
        if not relpath(vault, p).startswith("notes/"):
            continue
        fm = parse_frontmatter(read(p))
        sup = fm.get("superseded_by")
        status = str(fm.get("status", "")).strip()
        if status == "superseded" or sup not in (None, "", [], "[]"):
            superseded[p.stem] = relpath(vault, p)
    if not superseded:
        return []
    out = []
    for p in notes:
        rp = relpath(vault, p)
        if rp.startswith(("system/", "notes/")):
            continue
        for m in _WIKI_VAL.finditer(read(p)):
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
    contract, _error = _vault_schema_contract(vault)
    if contract is None:
        return []
    types, folders, _vocabulary = contract
    type_home = {
        type_name: str(home).rstrip("/") + "/"
        for type_name in types
        if (home := schema.home_for(type_name, folders))
    }
    known_top_dirs = set(folders.get("bundle_roots") or [])
    known_top_dirs |= {str(path).split("/", 1)[0] for path in folders.get("skeleton") or []}
    known_top_dirs |= {
        str(path).strip("/").split("/", 1)[0]
        for path in folders.get("transient_prefixes") or []
        if str(path).strip("/")
    }
    out = []
    for p in iter_notes(vault):
        rp = relpath(vault, p)
        if is_untyped_infra(rp) or "/" not in rp:
            continue
        if rp.startswith(MISPLACED_SKIP_PREFIXES):
            continue
        ntype = parse_frontmatter(read(p)).get("type")
        home = type_home.get(ntype)
        if home and not rp.startswith(home):
            out.append(Finding("misplaced-note", "MEDIUM", rp, f"{ntype} should live under {home}"))
    # Stray top-level folders: any vault-root dir outside the numbered schema set.
    for d in vault.iterdir():
        if d.is_dir() and d.name not in SKIP_DIRS and d.name not in known_top_dirs:
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
    """A topic crossed the hub-creation threshold with no hub.

    Report-only: counts catalog Works and notes per topic/tag term and flags
    any term with >= `threshold` records that no existing hub already covers.
    Never auto-creates -- the finding suggests the PI consider a hub."""
    counts: dict[str, int] = {}
    label: dict[str, str] = {}  # lowercased term -> display form
    hubbed: set[str] = set()
    for p in iter_notes(vault):
        rp = relpath(vault, p)
        fm = parse_frontmatter(read(p))
        if fm.get("type") == "hub":
            for v in (fm.get("title"), *(fm.get("tags") or [])):
                if isinstance(v, str) and v.strip():
                    hubbed.add(v.strip().lower())
            continue
        if not rp.startswith("notes/"):
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
                    "hubs/",
                    f"topic '{label[key]}' has {counts[key]} notes "
                    f"(threshold {threshold}) and no hub -- consider creating one",
                )
            )
    return out


def _catalog_source_terms(source: dict[str, object]) -> list[str]:
    csl = source.get("csl_json")
    if not isinstance(csl, dict):
        csl = {}
    memoria = csl.get("memoria")
    if not isinstance(memoria, dict):
        memoria = {}
    out: list[str] = []
    for field in ("tags", "topics", "research_area"):
        value = memoria.get(field)
        if isinstance(value, list):
            out.extend(term for term in value if isinstance(term, str) and term.strip())
        elif isinstance(value, str) and value.strip():
            out.append(value)
    return sorted(set(out))


def skeleton_drift(vault: Path) -> list[Finding]:
    """A folder from the schema skeleton is missing from the vault.

    Verifies the `skeleton` list of `.memoria/schemas/folders.yaml` exists as
    directories in the vault. The fix is mechanical -- re-run the installer or create the dir --
    so the finding is MEDIUM, not CRITICAL. A missing schema contract is reported
    by frontmatter_schema_check; this derived check then stays silent.

    Only meaningful for an *installed* vault: the repo's src/ tree deliberately
    ships no empty dirs, so the check keys on the vault Git repo the installer
    creates -- absent `.git`, no skeleton was ever scaffolded, and the check is skipped."""
    if not (vault / ".git").is_dir():
        return []
    contract, _error = _vault_schema_contract(vault)
    if contract is None:
        return []
    _types, folders, _vocabulary = contract
    out = []
    for d in folders.get("skeleton") or []:
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
    graph_analyze,
    fama_exposure,
    misplaced_note,
    audit_unpaired_writes,
    vault_hash_drift,
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
        "such finding exists (for example, vault-hash-drift). All other "
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
