#!/usr/bin/env python3
"""pipeline.py — the deterministic ingest orchestrator (ADR-30).

Chains the four deterministic stages into a single **draft bundle** that the
Librarian worker completes (the two LLM judgments) and writes (gated):

    Tier-0  ingest_paper  -> identity + route + captured frontmatter
    Tier-1  resolve_merge -> S2+OpenAlex+Crossref merged metadata + ref union
            extract       -> full text (PMC / local PDF), gatekept by coherence
            link          -> entity find-or-create plan + cites edges

Output (`--json`): the assembled paper-note **with two holes** —
`_proposed_classification` (classify, LLM #1) and the `[!brief]` body (LLM #2) —
plus the link plan and the extract. The worker fills the two holes and performs
the gated writes; this script writes nothing.

`--enrich` runs the network stages; without it, only Tier-0 (offline floor).
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import extract
import ingest_paper
import link
import resolve_merge


def _env(k: str) -> str:
    return resolve_merge._env(k)


def _bib_local_pdf(citekey: str, bib_text: str) -> tuple[str, str]:
    """From the bib `file` field, recover (wsl_pdf_path, zotero_storage_key).

    Better BibTeX exports the local attachment path (e.g.
    `C:\\Users\\me\\Zotero\\storage\\ABCD1234\\paper.pdf`). The storage folder is the
    Zotero attachment key (→ `pdf_uri`), and the Windows path maps to its WSL mount
    (→ a real path the extractor can read). Both `""` if absent."""
    entry = ingest_paper._find_entry(bib_text, citekey)
    if not entry:
        return "", ""
    m = re.search(r"\bfile\s*=\s*\{([^}]*)\}", entry[1], re.IGNORECASE)
    if not m:
        return "", ""
    # take the first .pdf among ';'-separated attachments; drop a trailing mime type
    raw = m.group(1)
    first = next((p for p in raw.split(";") if p.strip().lower().endswith(".pdf")),
                 raw.split(";")[0]).strip().strip(":")
    if first.lower().endswith("application/pdf"):
        first = first.rsplit(":", 1)[0]
    key_m = re.search(r"[/\\]storage[/\\]([A-Za-z0-9]{8})[/\\]", first)
    key = key_m.group(1) if key_m else ""
    win = re.match(r"^([A-Za-z]):[\\/](.*)$", first)
    wsl = f"/mnt/{win.group(1).lower()}/" + win.group(2).replace("\\", "/") if win else first
    return wsl, key


def run(citekey: str, bib_text: str, vault: Path | None = None,
        pdf_path: str | None = None, enrich: bool = True) -> dict:
    # Tier 0 — always
    note = ingest_paper.ingest_text(citekey, bib_text)
    fm = note["frontmatter"]
    bundle = {
        "citekey": citekey, "note_type": note["note_type"], "path": note["path"],
        "lifecycle": "captured", "ingest_status": "tier0",
        "frontmatter": fm, "body_abstract": "", "extract": None, "link_plan": None,
        "holes": ["_proposed_classification", "brief"],
        "provenance": {}, "degraded": [],
    }
    if not enrich:
        return bundle

    ids = resolve_merge.bib_ids(citekey, bib_text)
    r = resolve_merge.resolve(citekey, bib_text)
    m = r["merged"]
    bundle["provenance"] = m.get("provenance", {})

    # promote merged metadata into the frontmatter (agent namespace = _enrichment)
    if m.get("title"):
        fm["title"] = m["title"]
    if m.get("year"):
        fm["year"] = m["year"]
    if m.get("venue"):
        fm["venue"] = m["venue"]
    fm["authors"] = [a.get("name", "") for a in m.get("authors", [])] or fm["authors"]
    fm["_enrichment"] = {
        "citation_count": m.get("citation_count"),
        "tldr": m.get("tldr", ""),
        "fields_of_study": m.get("fields_of_study", []),
        "topics": m.get("topics", []),
        "reference_count_union": len(m.get("references", [])),
        "sources_found": [s for s in ("s2", "openalex", "crossref")
                          if r["parts"].get(s, {}).get("found")],
    }
    # promote stable IDs the APIs resolved (only if the bib didn't already set them)
    for fld, mkey in (("semantic_scholar_id", "s2_id"), ("openalex_id", "openalex_id"),
                      ("pmid", "pmid"), ("pmcid", "pmcid")):
        if not fm.get(fld) and m.get(mkey):
            fm[fld] = m[mkey]
    fm["enriched_date"] = date.today().isoformat()
    fm["ingest_status"] = "enriched"
    bundle["ingest_status"] = "enriched"
    bundle["lifecycle"] = "captured"   # still captured until classify (LLM #1) lands -> proposed

    # local Zotero PDF from the bib `file` field — recover pdf_uri + feed extraction
    if not pdf_path:
        wsl_pdf, zkey = _bib_local_pdf(citekey, bib_text)
        if zkey and not fm.get("pdf_uri"):
            fm["pdf_uri"] = f"zotero://open-pdf/library/items/{zkey}"
        if wsl_pdf and Path(wsl_pdf).is_file():
            pdf_path = wsl_pdf

    # extract (full text) — use the enrichment-resolved PMCID/PMID when the bib lacked them
    ex_ids = {**ids, "pmcid": ids.get("pmcid") or m.get("pmcid", ""),
              "pmid": ids.get("pmid") or m.get("pmid", "")}
    ex = extract.extract(ex_ids, pdf_path, _env("NCBI_EMAIL"))
    # carry the text so the caller can persist it (90-assets is outside the agent's
    # write lane, so the ingest tool writes the extract file, not the worker)
    bundle["extract"] = {"source": ex["source"], "chars": ex["chars"],
                         "degraded": ex["degraded"], "text": ex.get("text", "")}
    if ex["degraded"]:
        bundle["degraded"].append("extract")
    fm["extract_path"] = f"90-assets/extracts/{citekey}.md" if ex["chars"] else ""

    # link plan (entities + cites) — needs the vault for cites matching
    if vault is not None:
        bundle["link_plan"] = link.plan_links(m, vault)

    # neighbours for the brief are selected downstream (qmd); leave the hole.
    bundle["body_abstract"] = m.get("tldr", "")
    return bundle


def _self_test() -> int:
    """Offline test of the assembly: Tier-0 only (no network)."""
    fixture = ("@article{x2024Test,\n  title = {A Test},\n  author = {Doe, Jane},\n"
               "  year = {2024},\n  doi = {10.1/x},\n  journal = {J Tests},\n}\n")
    b = run("x2024Test", fixture, enrich=False)
    checks = [
        ("tier0 captured", b["lifecycle"] == "captured" and b["ingest_status"] == "tier0"),
        ("routes to paper-note", b["note_type"] == "paper-note"),
        ("two holes declared", b["holes"] == ["_proposed_classification", "brief"]),
        ("frontmatter has identity", b["frontmatter"]["title"] == "A Test"
         and b["frontmatter"]["doi"] == "10.1/x"),
        ("no enrichment without --enrich", b["extract"] is None and b["link_plan"] is None),
    ]
    pdf, key = _bib_local_pdf(
        "y2024Pdf",
        "@article{y2024Pdf,\n  title = {P},\n"
        "  file = {C:\\Users\\me\\Zotero\\storage\\ABCD1234\\My Paper - 2024.pdf},\n}\n")
    checks.append(("bib file -> wsl path + zotero storage key",
                   key == "ABCD1234"
                   and pdf == "/mnt/c/Users/me/Zotero/storage/ABCD1234/My Paper - 2024.pdf"))
    bad = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {n}")
    print(f"\n{'OK' if not bad else f'{len(bad)} FAILING'}: pipeline.py self-test")
    return 1 if bad else 0


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Deterministic ingest orchestrator (ADR-30)")
    ap.add_argument("--citekey")
    ap.add_argument("--bib", help="default <vault>/.memoria/memoria.bib")
    ap.add_argument("--vault", help="default $OBSIDIAN_VAULT_PATH from ~/.hermes/.env")
    ap.add_argument("--pdf")
    ap.add_argument("--enrich", action="store_true", help="run the Tier-1 network stages")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return _self_test()
    # Resolve the vault root from the documented OBSIDIAN_VAULT_PATH convention so a
    # dispatched worker (whose cwd is a scratch workspace) needn't know the path.
    vault_str = a.vault or _env("OBSIDIAN_VAULT_PATH")
    if not a.citekey or not vault_str:
        ap.error("provide --citekey and --vault (or set OBSIDIAN_VAULT_PATH; or --self-test)")
    vault = Path(vault_str)
    bib = Path(a.bib) if a.bib else vault / ".memoria" / "memoria.bib"
    if not bib.is_file():
        print(f"bib not found: {bib}", file=sys.stderr)
        return 3
    try:
        b = run(a.citekey, bib.read_text(encoding="utf-8", errors="ignore"),
                vault, a.pdf, enrich=a.enrich)
    except KeyError:
        print(f"citekey not found: {a.citekey}", file=sys.stderr)
        return 2
    print(json.dumps(b, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
