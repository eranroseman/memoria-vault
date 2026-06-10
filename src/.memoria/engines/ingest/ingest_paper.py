#!/usr/bin/env python3
"""ingest_paper.py — the deterministic ingest spine (ADR-30).

Tier 0 (this file, so far): from the local Better BibTeX `.bib` alone — no
network, no PDF, no ML — resolve a citekey to an identity-complete note and
route it by type. Produces the assembled note *content*; it does NOT write to
the vault (the Librarian worker performs the gated write — ADR-30 §"Where code
runs"). Tiers 1-2 (merge/extract/tag/link, the two LLM judgments) land next.

Usage:
    ingest_paper.py --citekey <key> [--bib PATH] [--json]

Exit codes: 0 ok · 2 citekey not found · 3 bad bib · 4 usage.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

SCHEMA_VERSION = 1

# entry-type → (note_type, folder, source_type). ADR-30: ~17% of the corpus is
# non-paper; route it, don't force it into the paper-note shape.
TYPE_ROUTING = {
    # bib entry type -> (vault type, catalog home, source_type hint)  [ADR-47/49]
    "article": ("paper", "catalog/papers", "paper"),
    "inproceedings": ("paper", "catalog/papers", "paper"),
    "conference": ("paper", "catalog/papers", "paper"),
    "proceedings": ("paper", "catalog/papers", "paper"),
    "incollection": ("paper", "catalog/papers", "chapter"),
    "inbook": ("paper", "catalog/papers", "chapter"),
    "online": ("paper", "catalog/papers", "preprint"),
    "misc": ("paper", "catalog/papers", "preprint"),
    "techreport": ("paper", "catalog/papers", "report"),
    "report": ("paper", "catalog/papers", "report"),
    "phdthesis": ("paper", "catalog/papers", "thesis"),
    "mastersthesis": ("paper", "catalog/papers", "thesis"),
    "book": ("paper", "catalog/papers", "book"),
    "software": ("repository", "catalog/repositories", "software"),
    "dataset": ("dataset", "catalog/datasets", "dataset"),
}
DEFAULT_ROUTE = ("paper", "catalog/papers", "paper")


# --------------------------------------------------------------------------- #
# Self-contained BibTeX parsing (Tier 0 must have no external deps)
# --------------------------------------------------------------------------- #
def _find_entry(text: str, citekey: str):
    """Return (entry_type, body_text) for `citekey`, or None. Brace-aware."""
    needle = "{" + citekey + ","
    i = 0
    while True:
        at = text.find("@", i)
        if at == -1:
            return None
        brace = text.find("{", at)
        if brace == -1:
            return None
        etype = text[at + 1:brace].strip().lower()
        # match the citekey immediately after the opening brace
        head = text[brace:brace + len(needle)]
        if head.lower() == needle.lower():
            # read to the matching close brace
            depth, j = 0, brace
            while j < len(text):
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            inner = text[brace + 1:j]
            after_key = inner.split(",", 1)[1] if "," in inner else ""
            return etype, after_key
        i = brace + 1


def _parse_fields(body: str) -> dict:
    """Parse `name = {value} | "value" | bare,` fields. Brace/quote-aware."""
    fields, i, n = {}, 0, len(body)
    while i < n:
        # field name
        while i < n and (body[i].isspace() or body[i] == ","):
            i += 1
        start = i
        while i < n and (body[i].isalnum() or body[i] in "_-"):
            i += 1
        name = body[start:i].strip().lower()
        if not name:
            break
        while i < n and body[i].isspace():
            i += 1
        if i >= n or body[i] != "=":
            break
        i += 1
        while i < n and body[i].isspace():
            i += 1
        if i >= n:
            break
        if body[i] == "{":
            depth, j = 0, i
            while j < n:
                if body[j] == "{":
                    depth += 1
                elif body[j] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            val = body[i + 1:j]
            i = j + 1
        elif body[i] == '"':
            j = i + 1
            while j < n and body[j] != '"':
                j += 1
            val = body[i + 1:j]
            i = j + 1
        else:
            j = i
            while j < n and body[j] != ",":
                j += 1
            val = body[i:j]
            i = j
        fields[name] = _clean(val)
    return fields


def _clean(v: str) -> str:
    return " ".join(v.replace("{", "").replace("}", "").replace("\n", " ").split()).strip()


def _authors(raw: str) -> list[str]:
    """`Last, First and ...` / `First Last and ...` → ['First Last', ...]."""
    out = []
    for part in raw.split(" and "):
        part = part.strip()
        if not part:
            continue
        if "," in part:
            last, first = (s.strip() for s in part.split(",", 1))
            out.append(f"{first} {last}".strip())
        else:
            out.append(part)
    return out


# --------------------------------------------------------------------------- #
# Tier 0 — assemble the captured note
# --------------------------------------------------------------------------- #
def assemble(citekey: str, etype: str, f: dict) -> dict:
    note_type, folder, source_type = TYPE_ROUTING.get(etype, DEFAULT_ROUTE)
    now = datetime.date.today().isoformat()
    year = ""
    for k in ("year", "date"):
        if f.get(k):
            m = "".join(c for c in f[k] if c.isdigit())[:4]
            if m:
                year = int(m)
                break
    doi = f.get("doi", "")
    arxiv = f.get("eprint", "") if (f.get("archiveprefix", "").lower() == "arxiv" or "arxiv" in f.get("eprint", "").lower()) else ""
    if not arxiv and doi.lower().startswith("10.48550/arxiv."):
        arxiv = doi.split("arxiv.", 1)[-1]
    fm = {
        "title": f.get("title", ""),
        "type": note_type,
        "lifecycle": "current",             # entities are current from creation (ADR-50)
        "citekey": citekey,
        "name": f.get("title", ""),         # dataset/repository records key on name
        "authors": _authors(f.get("author", "") or f.get("editor", "")),
        "year": year,
        "venue": f.get("journal", "") or f.get("booktitle", "") or f.get("publisher", ""),
        "doi": doi,
        "url": f.get("url", ""),
        "relationships": {},                # given edges; Tier-1 link builds them (ADR-52)
        "research_area": [],
        "methodology": [],
        "source_type": source_type,
        "zotero_uri": "",
        "pdf_uri": "",
        "extract_path": "",
        "openalex_id": "",
        "semantic_scholar_id": "",
        "pmid": "",
        "arxiv_id": arxiv,
        "pmcid": f.get("pmcid", ""),
        "isbn": f.get("isbn", ""),
        "pub_status": "active",
        "ingest_status": "tier0",           # captured but not yet enriched (ADR-30)
        "full_text_reviewed": False,
        "created": now,
        "updated": now,
        "enriched_date": "",
        "schema_version": SCHEMA_VERSION,
        "_proposed_classification": {"research_area": [], "methodology": []},
    }
    body_lines = [f"# {fm['title'] or citekey}", ""]
    if fm["venue"]:
        body_lines += [f"*{fm['venue']}*" + (f" ({year})" if year else ""), ""]
    if f.get("abstract"):
        body_lines += ["## Abstract", "", f["abstract"], ""]
    body_lines += ["> [!note] Captured — not yet ingested",
                   "> Identity from the local `.bib`. Enrichment (full text, relationships, "
                   "classification) runs in Tier 1; `ingest_status: tier0` marks the floor.", ""]
    return {
        "citekey": citekey, "entry_type": etype, "note_type": note_type,
        "path": f"{folder}/{citekey}.md", "frontmatter": fm, "body": "\n".join(body_lines),
    }


def render(note: dict) -> str:
    import yaml
    fm = yaml.safe_dump(note["frontmatter"], sort_keys=False, allow_unicode=True, default_flow_style=False)
    return f"---\n{fm}---\n\n{note['body']}"


# --------------------------------------------------------------------------- #
def ingest_text(citekey: str, bib_text: str) -> dict:
    found = _find_entry(bib_text, citekey)
    if not found:
        raise KeyError(citekey)
    etype, body = found
    return assemble(citekey, etype, _parse_fields(body))


def ingest(citekey: str, bib_path: Path) -> dict:
    return ingest_text(citekey, bib_path.read_text(encoding="utf-8", errors="ignore"))


# A small self-contained fixture so the tests need no external library.
_FIXTURE = r"""
@article{smith2024Example,
  title = {An Example Article With a PMCID},
  author = {Smith, Jane Q. and Doe, John},
  year = {2024},
  doi = {10.1000/example.2024},
  pmcid = {PMC1234567},
  journal = {Journal of Examples},
  abstract = {A short abstract.},
}
@online{lee2025Preprint,
  title = {A Preprint on arXiv},
  author = {Lee, Kai},
  date = {2025-03-01},
  doi = {10.48550/arXiv.2503.20201},
  eprint = {2503.20201},
  archiveprefix = {arXiv},
}
@software{2025tool,
  title = {acme/cool-tool},
  date = {2025},
  url = {https://github.com/acme/cool-tool},
}
@book{brown2009Book,
  title = {A Book With an ISBN},
  author = {Brown, Alice},
  year = {2009},
  isbn = {978-0-13-468599-1},
  publisher = {Some Press},
}
@incollection{green2018Chapter,
  title = {A Chapter},
  author = {Green, Bob and White, Carol},
  year = {2018},
  booktitle = {Handbook of Things},
}
"""

_EXPECT = [
    ("smith2024Example", "paper", "paper", {"authors": 2, "pmcid": "PMC1234567"}),
    ("lee2025Preprint", "paper", "preprint", {"authors": 1, "arxiv_id": "2503.20201"}),
    ("2025tool", "repository", "software", {"authors": 0}),
    ("brown2009Book", "paper", "book", {"authors": 1, "isbn": "978-0-13-468599-1"}),
    ("green2018Chapter", "paper", "chapter", {"authors": 2}),
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic ingest spine (ADR-30, Tier 0)")
    ap.add_argument("--citekey")
    ap.add_argument("--bib", help="path to memoria.bib (Better BibTeX export)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not a.citekey or not a.bib:
        ap.error("provide --citekey and --bib")
    bib = Path(a.bib)
    if not bib.is_file():
        print(f"bib not found: {bib}", file=sys.stderr)
        return 3
    try:
        note = ingest(a.citekey, bib)
    except KeyError:
        print(f"citekey not found: {a.citekey}", file=sys.stderr)
        return 2
    print(json.dumps(note, ensure_ascii=False, indent=2) if a.json else render(note))
    return 0


if __name__ == "__main__":
    sys.exit(main())
