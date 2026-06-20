#!/usr/bin/env python3
"""link.py — Tier-1 deterministic linking (ADR-30).

From a merged record (resolve_merge.py output) + the vault, plan the knowledge
graph: entity find-or-create (ID-keyed) and cites edges (references matched
against the vault by DOI/arXiv). ID-keyed, idempotent, no LLM — this is where a
script is exact and an LLM fabricates.

ADR-30 rules:
  - find-or-create venue (ISSN) / person (ORCID) / organization (ROR), keyed on
    the stable ID so same-named entities never merge.
  - entities WITHOUT a stable ID are *recorded by name*, never node-created and
    never name-merged.
  - cites/cited-by by local DOI/arXiv match of the merged reference union; the
    worker applies each edge bidirectionally (this.cites += X, X.cited_by += this).

This does NOT write to the vault; it returns the link plan for the gated worker.
Reads (only) are local and un-gated.
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

LINKAGE_RELPATH = "system/logs/linkage.jsonl"


def _bare(uri: str) -> str:
    """ORCID/ROR may arrive as full URIs; keep the bare id."""
    return (uri or "").rstrip("/").rsplit("/", 1)[-1].strip()


_yaml_warned = False


def read_frontmatter(md: Path) -> dict:
    global _yaml_warned
    try:
        import yaml
    except ImportError:
        if not _yaml_warned:
            print("[link] PyYAML not installed; frontmatter parsing disabled", file=sys.stderr)
            _yaml_warned = True
        return {}
    text = md.read_text(encoding="utf-8", errors="ignore")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    try:
        d = yaml.safe_load(text[3:end])
        return d if isinstance(d, dict) else {}
    except yaml.YAMLError as exc:
        print(f"[link] YAML parse error in {md}: {exc}", file=sys.stderr)
        return {}


def index_vault(vault: Path) -> dict:
    """Map DOI / arXiv-id (lowercased) -> citekey for existing source notes."""
    idx = {}
    for folder in ("catalog/papers", "catalog/datasets", "catalog/repositories"):
        d = vault / folder
        if not d.is_dir():
            continue
        for md in d.glob("*.md"):
            fm = read_frontmatter(md)
            ck = fm.get("citekey") or md.stem
            for key in ("doi", "arxiv_id"):
                v = str(fm.get(key) or "").strip().lower()
                if v:
                    idx[v] = ck
    return idx


# entity type -> its Catalog home (ADR-47)
ENTITY_FOLDER = {
    "person": "catalog/people",
    "organization": "catalog/organizations",
    "venue": "catalog/venues",
}


def plan_entities(merged: dict) -> dict:
    entities, by_key = [], {}
    by_name = {"authors": [], "venues": [], "orgs": []}

    def add(note_type, idtype, idval, name):
        idval = _bare(idval)
        if not idval:
            return False
        key = (note_type, idval)
        if key not in by_key:
            # path is keyed on the stable id (not the name) so find-or-create is
            # idempotent — same ORCID/ROR/ISSN always resolves to the same file.
            rec = {
                "note_type": note_type,
                "id_type": idtype,
                "id": idval,
                "name": name or "",
                "path": f"{ENTITY_FOLDER[note_type]}/{idval}.md",
            }
            by_key[key] = rec
            entities.append(rec)
        return True

    if not add("venue", "issn", merged.get("issn", ""), merged.get("venue", "")):
        if merged.get("venue"):
            by_name["venues"].append(merged["venue"])

    for a in merged.get("authors", []) or []:
        if not add("person", "orcid", a.get("orcid", ""), a.get("name", "")):
            if a.get("name"):
                by_name["authors"].append(a["name"])
        if not add("organization", "ror", a.get("ror", ""), a.get("affiliation", "")):
            if a.get("affiliation"):
                by_name["orgs"].append(a["affiliation"])

    # de-dup recorded-by-name lists, preserve order
    for k in by_name:
        by_name[k] = list(dict.fromkeys(x for x in by_name[k] if x))
    return {"entities": entities, "recorded_by_name": by_name}


def plan_cites(merged: dict, vault_index: dict) -> list:
    out, seen = [], set()
    for r in merged.get("references", []) or []:
        doi = str(r.get("doi") or "").lower()
        arx = str(r.get("arxiv") or "").lower()
        ck = vault_index.get(doi) or (vault_index.get(arx) if arx else None)
        if ck and ck not in seen:
            seen.add(ck)
            out.append(
                {
                    "to": ck,
                    "via": "doi" if doi in vault_index else "arxiv",
                    "ref_doi": doi,
                    "ref_arxiv": arx,
                    "sources": r.get("sources", []),
                }
            )
    return out


def plan_links(merged: dict, vault: Path) -> dict:
    idx = index_vault(vault)
    ent = plan_entities(merged)
    cites = plan_cites(merged, idx)
    return {
        "entities": ent["entities"],
        "recorded_by_name": ent["recorded_by_name"],
        "cites": cites,  # worker applies bidirectionally (this.cites + X.cited_by)
        "vault_indexed": len(idx),
        "summary": {
            "entities": len(ent["entities"]),
            "cites": len(cites),
            "by_name_authors": len(ent["recorded_by_name"]["authors"]),
        },
    }


def append_by_name_audit(vault: Path, citekey: str, plan: dict) -> dict | None:
    """Record the no-stable-ID names the linker refused to merge.

    This is the cheap ADR-59 trigger signal: by-name clusters are not merged or
    blocked here, only counted so a later Fellegi-Sunter-style dedup slice can
    know when enough collisions have accumulated.
    """
    by_name = plan.get("recorded_by_name") or {}
    counts = {k: len(v or []) for k, v in by_name.items()}
    total = sum(counts.values())
    if total == 0:
        return None
    record = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stage": "link",
        "citekey": citekey,
        "event": "recorded_by_name",
        "counts": counts,
        "total": total,
        "recorded_by_name": by_name,
        "source": "link.py",
    }
    log = Path(vault) / LINKAGE_RELPATH
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


# --------------------------------------------------------------------------- #
def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Tier-1 deterministic linking (ADR-30)")
    ap.add_argument("--merged", help="path to a resolve_merge JSON ('-' for stdin)")
    ap.add_argument("--vault", help="vault root (for cites matching)")
    a = ap.parse_args()
    if not a.merged or not a.vault:
        ap.error("provide --merged and --vault")
    raw = sys.stdin.read() if a.merged == "-" else Path(a.merged).read_text(encoding="utf-8")
    obj = json.loads(raw)
    merged = obj.get("merged", obj)  # accept either the full resolve output or just `merged`
    print(json.dumps(plan_links(merged, Path(a.vault)), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
