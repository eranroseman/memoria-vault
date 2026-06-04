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

import json
import sys
from pathlib import Path


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
            print("[link] PyYAML not installed; frontmatter parsing disabled",
                  file=sys.stderr)
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
    for folder in ("20-sources/01-papers", "20-sources/02-items"):
        d = vault / folder
        if not d.is_dir():
            continue
        for md in d.glob("*.md"):
            fm = read_frontmatter(md)
            ck = (fm.get("citekey") or md.stem)
            for key in ("doi", "arxiv_id"):
                v = str(fm.get(key) or "").strip().lower()
                if v:
                    idx[v] = ck
    return idx


# entity note_type -> its folder under 20-sources/03-entities/
ENTITY_FOLDER = {"person-note": "01-people", "organization-note": "02-organizations",
                 "venue-note": "03-venues"}


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
            rec = {"note_type": note_type, "id_type": idtype, "id": idval, "name": name or "",
                   "path": f"20-sources/03-entities/{ENTITY_FOLDER[note_type]}/{idval}.md"}
            by_key[key] = rec
            entities.append(rec)
        return True

    if not add("venue-note", "issn", merged.get("issn", ""), merged.get("venue", "")):
        if merged.get("venue"):
            by_name["venues"].append(merged["venue"])

    for a in merged.get("authors", []) or []:
        if not add("person-note", "orcid", a.get("orcid", ""), a.get("name", "")):
            if a.get("name"):
                by_name["authors"].append(a["name"])
        if not add("organization-note", "ror", a.get("ror", ""), a.get("affiliation", "")):
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
            out.append({"to": ck, "via": "doi" if doi in vault_index else "arxiv",
                        "ref_doi": doi, "ref_arxiv": arx, "sources": r.get("sources", [])})
    return out


def plan_links(merged: dict, vault: Path) -> dict:
    idx = index_vault(vault)
    ent = plan_entities(merged)
    cites = plan_cites(merged, idx)
    return {
        "entities": ent["entities"],
        "recorded_by_name": ent["recorded_by_name"],
        "cites": cites,            # worker applies bidirectionally (this.cites + X.cited_by)
        "vault_indexed": len(idx),
        "summary": {"entities": len(ent["entities"]), "cites": len(cites),
                    "by_name_authors": len(ent["recorded_by_name"]["authors"])},
    }


# --------------------------------------------------------------------------- #
def _self_test() -> int:
    merged = {
        "venue": "npj Digital Medicine", "issn": "2398-6352",
        "authors": [
            {"name": "Alice A", "orcid": "https://orcid.org/0000-0002-1825-0097",
             "affiliation": "MIT", "ror": "https://ror.org/042nb2s44"},
            {"name": "Bob B", "orcid": "", "affiliation": "Acme Lab", "ror": ""},
            {"name": "Carol C", "orcid": "0000-0001-2345-6789", "affiliation": "MIT",
             "ror": "https://ror.org/042nb2s44"},  # same org id -> dedup to one org note
        ],
        "references": [
            {"doi": "10.1/in-vault", "arxiv": "", "sources": ["s2", "crossref"]},
            {"doi": "10.1/not-in-vault", "arxiv": "", "sources": ["crossref"]},
            {"doi": "", "arxiv": "2401.00001", "sources": ["s2"]},  # arXiv ref, in vault
            {"doi": "10.1/in-vault", "arxiv": "", "sources": ["s2"]},  # dup -> deduped
        ],
    }
    vidx = {"10.1/in-vault": "smith2020Paper", "2401.00001": "lee2024Pre"}
    ep = plan_entities(merged)
    cites = plan_cites(merged, vidx)
    ents = ep["entities"]
    nt = lambda t: [e for e in ents if e["note_type"] == t]
    checks = [
        ("venue note by ISSN", len(nt("venue-note")) == 1 and nt("venue-note")[0]["id"] == "2398-6352"),
        ("venue path is ID-keyed", nt("venue-note")[0]["path"] == "20-sources/03-entities/03-venues/2398-6352.md"),
        ("person notes only for ORCID authors (2 of 3)", len(nt("person-note")) == 2),
        ("ORCID kept bare (no URI)", all("/" not in e["id"] for e in nt("person-note"))),
        ("person path is ID-keyed (ORCID)", all(e["path"] == f"20-sources/03-entities/01-people/{e['id']}.md" for e in nt("person-note"))),
        ("org deduped by ROR (1, not 2)", len(nt("organization-note")) == 1),
        ("org path is ID-keyed (ROR)", nt("organization-note")[0]["path"] == "20-sources/03-entities/02-organizations/042nb2s44.md"),
        ("no-ORCID author recorded by name", ep["recorded_by_name"]["authors"] == ["Bob B"]),
        ("no-ROR affiliation recorded by name", "Acme Lab" in ep["recorded_by_name"]["orgs"]),
        ("cites matched + deduped (2 edges)", len(cites) == 2),
        ("cites via doi and via arxiv", {c["via"] for c in cites} == {"doi", "arxiv"}),
        ("cites point at vault citekeys", {c["to"] for c in cites} == {"smith2020Paper", "lee2024Pre"}),
    ]
    bad = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {n}")
    print(f"\n{'OK' if not bad else f'{len(bad)} FAILING'}: link.py self-test")
    return 1 if bad else 0


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Tier-1 deterministic linking (ADR-30)")
    ap.add_argument("--merged", help="path to a resolve_merge JSON ('-' for stdin)")
    ap.add_argument("--vault", help="vault root (for cites matching)")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return _self_test()
    if not a.merged or not a.vault:
        ap.error("provide --merged and --vault (or --self-test)")
    raw = sys.stdin.read() if a.merged == "-" else Path(a.merged).read_text(encoding="utf-8")
    obj = json.loads(raw)
    merged = obj.get("merged", obj)  # accept either the full resolve output or just `merged`
    print(json.dumps(plan_links(merged, Path(a.vault)), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
