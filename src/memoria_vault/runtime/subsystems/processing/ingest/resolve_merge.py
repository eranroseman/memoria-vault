#!/usr/bin/env python3
"""resolve_merge.py — Tier-1 resolve + multi-source merge (ADR-30).

Fetch a paper from the open-access fallback chain (Semantic Scholar + OpenAlex
co-primary; Crossref for non-arXiv DOIs; PubMed/NCBI for biomedical identifiers)
and merge **per-field, best-source-wins with provenance** — the merge contract
grounded by the ADR-30 spike (sources disagree and are each incomplete):

  authors + ORCID + affiliations  <- OpenAlex
  tldr / embedding / intents / influence / contexts / fields-of-study  <- S2
  references = union across sources, deduped by DOI (the keyspace the vault stores)
  canonical scalar metadata (title/year/venue)  <- Crossref / OpenAlex / PubMed / S2

`--diagnose --bib PATH --sample N` runs the build-time merge spike: it resolves a
random sample of the library and reports coverage, author/ORCID alignment, and
reference-union/dedup stats — the empirical gate the red-team asked for, emitted
by the code that will rely on it. Needs S2_API_KEY / OPENALEX_API_KEY /
NCBI_EMAIL in the environment.

This does NOT write to the vault; it returns merged metadata for the worker.
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from memoria_vault.runtime.diagnostics import record_event
from memoria_vault.runtime.subsystems.processing.ingest import ingest_paper
from memoria_vault.runtime.subsystems.processing.ingest.resolve_merge_logic import (
    agreement as agreement,
)
from memoria_vault.runtime.subsystems.processing.ingest.resolve_merge_logic import merge
from memoria_vault.runtime.subsystems.processing.ingest.resolve_merge_logic import (
    union_refs as union_refs,
)
from memoria_vault.runtime.subsystems.processing.ingest.resolve_merge_pubmed import parse_pubmed

S2_BASE = "https://api.semanticscholar.org/graph/v1"
OA_BASE = "https://api.openalex.org"
CR_BASE = "https://api.crossref.org"
NCBI_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
S2_FIELDS = (
    "title,year,externalIds,referenceCount,citationCount,tldr,"
    "s2FieldsOfStudy,publicationTypes,authors.name,authors.externalIds,"
    "references.externalIds,references.title"
)
_S2_LAST = [0.0]  # crude ~1 req/s throttle for S2


def _diagnose(level: str, code: str, **details) -> None:
    try:
        record_event(
            component="ingest.resolve_merge",
            level=level,
            code=code,
            details=details,
        )
    except Exception:  # noqa: BLE001
        return


def _env(key: str) -> str:
    return os.environ.get(key, "")


def _http_retry(req: urllib.request.Request, read_fn, *, retries: int = 3):
    """Run read_fn(response) with 429 backoff. Returns None on error."""
    url = req.full_url
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return read_fn(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries:
                ra = (e.headers or {}).get("Retry-After", "")
                wait = float(ra) if ra.isdigit() else min(2**attempt, 8)
                time.sleep(wait + random.random())
                continue
            if e.code != 404:
                print(f"[resolve_merge] HTTP {e.code} {e.reason} from {url}", file=sys.stderr)
                _diagnose("warn", "http_error", status=e.code, reason=e.reason, url=url)
            return None
        except (OSError, ValueError) as exc:
            print(f"[resolve_merge] {type(exc).__name__} fetching {url}: {exc}", file=sys.stderr)
            _diagnose("warn", "fetch_exception", exception_type=type(exc).__name__, url=url)
            return None
    return None


def _get(url: str, headers: dict | None = None, data: bytes | None = None, retries: int = 3):
    """GET/POST JSON. S2 is the chief 429 offender; _http_retry handles backoff."""
    return _http_retry(
        urllib.request.Request(url, headers=headers or {}, data=data),
        json.load,
        retries=retries,
    )


def _get_text(url: str, retries: int = 3) -> str | None:
    """GET text/XML."""
    return _http_retry(
        urllib.request.Request(url),
        lambda r: r.read().decode("utf-8", errors="ignore"),
        retries=retries,
    )


# --------------------------------------------------------------------------- #
# Identifiers from the .bib note
# --------------------------------------------------------------------------- #
def bib_ids(citekey: str, bib_text: str) -> dict:
    fm = ingest_paper.ingest_text(citekey, bib_text)["frontmatter"]
    doi = (fm.get("doi") or "").strip()
    arxiv = (fm.get("arxiv_id") or "").strip()
    return {
        "doi": doi,
        "is_arxiv_doi": doi.lower().startswith("10.48550/arxiv."),
        "arxiv": arxiv,
        "pmcid": (fm.get("pmcid") or "").strip(),
        "pmid": (fm.get("pmid") or "").strip(),
        "title": fm.get("title", ""),
    }


def _s2_id(ids: dict) -> str | None:
    if ids["doi"]:
        return "DOI:" + ids["doi"]
    if ids["arxiv"]:
        return "ARXIV:" + ids["arxiv"]
    if ids["pmid"]:
        return "PMID:" + ids["pmid"]
    return None


def _norm_refs_s2(refs) -> list[dict]:
    out = []
    for r in refs or []:
        ext = r.get("externalIds") or {}
        out.append(
            {
                "doi": (ext.get("DOI") or "").lower(),
                "arxiv": (ext.get("ArXiv") or "").lower(),
                "title": r.get("title") or "",
            }
        )
    return out


# --------------------------------------------------------------------------- #
# Source fetchers -> normalized partial records
# --------------------------------------------------------------------------- #
def fetch_s2(ids: dict, key: str) -> dict:
    sid = _s2_id(ids)
    if not sid:
        return {"source": "s2", "found": False}
    wait = 1.05 - (time.monotonic() - _S2_LAST[0])
    if wait > 0:
        time.sleep(wait)
    _S2_LAST[0] = time.monotonic()
    d = _get(
        f"{S2_BASE}/paper/{urllib.parse.quote(sid)}?fields={S2_FIELDS}",
        {"x-api-key": key} if key else {},
    )
    if not d or not d.get("paperId"):
        return {"source": "s2", "found": False}
    authors = [
        {"name": a.get("name", ""), "orcid": (a.get("externalIds") or {}).get("ORCID", "")}
        for a in d.get("authors") or []
    ]
    refs = _norm_refs_s2(d.get("references"))
    ext = d.get("externalIds") or {}
    return {
        "source": "s2",
        "found": True,
        "s2_id": d.get("paperId", ""),
        "pmid": str(ext.get("PubMed") or ""),
        "pmcid": str(ext.get("PubMedCentral") or ""),
        "title": d.get("title", ""),
        "year": d.get("year"),
        "authors": authors,
        "orcid_count": sum(1 for a in authors if a["orcid"]),
        "tldr": (d.get("tldr") or {}).get("text", ""),
        "fields_of_study": [f.get("category") for f in d.get("s2FieldsOfStudy") or []],
        "publication_types": d.get("publicationTypes") or [],
        "ref_count_reported": d.get("referenceCount"),
        "refs": refs,
        "refs_returned": len(refs),
        "citation_count": d.get("citationCount"),
    }


def fetch_openalex(ids: dict, key: str, email: str) -> dict:
    sel = None
    if ids["doi"]:
        sel = "doi:" + ids["doi"]
    elif ids["arxiv"]:
        sel = "doi:10.48550/arXiv." + ids["arxiv"]
    if not sel:
        return {"source": "openalex", "found": False}
    q = f"?mailto={email}"
    hdrs = {"Authorization": f"Bearer {key}"} if key else {}
    d = _get(f"{OA_BASE}/works/{urllib.parse.quote(sel, safe=':')}{q}", headers=hdrs)
    if not d or not d.get("id"):
        return {"source": "openalex", "found": False}
    authors = [
        {
            "name": a.get("author", {}).get("display_name", ""),
            "orcid": (a.get("author", {}).get("orcid") or ""),
            "affiliation": (a.get("institutions") or [{}])[0].get("display_name", "")
            if a.get("institutions")
            else "",
            "ror": (a.get("institutions") or [{}])[0].get("ror", "")
            if a.get("institutions")
            else "",
        }
        for a in d.get("authorships") or []
    ]
    src = (d.get("primary_location") or {}).get("source") or {}
    oaids = d.get("ids") or {}
    return {
        "source": "openalex",
        "found": True,
        "openalex_id": (d.get("id") or "").rsplit("/", 1)[-1],
        "pmid": (oaids.get("pmid") or "").rsplit("/", 1)[-1],
        "pmcid": (oaids.get("pmcid") or "").rsplit("/", 1)[-1],
        "title": d.get("title", ""),
        "year": d.get("publication_year"),
        "authors": authors,
        "orcid_count": sum(1 for a in authors if a["orcid"]),
        "venue": src.get("display_name", ""),
        "issn": (src.get("issn_l") or ""),
        "topics": [t.get("display_name") for t in d.get("topics") or []],
        # scored topics feed the classify stage (D21/ADR-54) — keep the OpenAlex
        # score and the subfield/field/domain rollup, no extra network call needed
        "topics_scored": [
            {
                "name": t.get("display_name", ""),
                "score": float(t.get("score") or 0.0),
                "subfield": ((t.get("subfield") or {}).get("display_name", "")),
                "field": ((t.get("field") or {}).get("display_name", "")),
                "domain": ((t.get("domain") or {}).get("display_name", "")),
            }
            for t in d.get("topics") or []
        ],
        "referenced_works": d.get("referenced_works") or [],  # OpenAlex W-ids (different keyspace)
        "ror_count": sum(1 for a in authors if a.get("ror")),
    }


def fetch_crossref(ids: dict, email: str) -> dict:
    # arXiv DOIs are DataCite, not Crossref -> skip
    if not ids["doi"] or ids["is_arxiv_doi"]:
        return {"source": "crossref", "found": False}
    d = _get(f"{CR_BASE}/works/{urllib.parse.quote(ids['doi'])}?mailto={email}")
    if not d or d.get("status") != "ok":
        return {"source": "crossref", "found": False}
    m = d.get("message", {})
    refs = []
    for r in m.get("reference") or []:
        doi = (r.get("DOI") or "").lower()
        if doi:
            refs.append({"doi": doi, "arxiv": "", "title": r.get("article-title", "")})
    authors = [
        {
            "name": " ".join(x for x in (a.get("given"), a.get("family")) if x),
            "orcid": (a.get("ORCID") or "").rsplit("/", 1)[-1] if a.get("ORCID") else "",
        }
        for a in m.get("author") or []
    ]
    return {
        "source": "crossref",
        "found": True,
        "title": (m.get("title") or [""])[0],
        "year": (m.get("issued", {}).get("date-parts", [[None]]) or [[None]])[0][0],
        "authors": authors,
        "orcid_count": sum(1 for a in authors if a["orcid"]),
        "venue": (m.get("container-title") or [""])[0],
        "issn": (m.get("ISSN") or [""])[0],
        "refs": refs,
        "ref_count_reported": m.get("reference-count"),
    }


def _pubmed_id(ids: dict, email: str, api_key: str) -> str:
    if ids.get("pmid"):
        return ids["pmid"]
    if not ids.get("doi"):
        return ""
    params = {"db": "pubmed", "retmode": "json", "term": f"{ids['doi']}[doi]", "email": email}
    if api_key:
        params["api_key"] = api_key
    d = _get(f"{NCBI_EUTILS}/esearch.fcgi?{urllib.parse.urlencode(params)}")
    ids_found = ((d or {}).get("esearchresult") or {}).get("idlist") or []
    return str(ids_found[0]) if ids_found else ""


def fetch_pubmed(ids: dict, email: str, api_key: str) -> dict:
    pmid = _pubmed_id(ids, email, api_key)
    if not pmid:
        return {"source": "pubmed", "found": False}
    params = {"db": "pubmed", "id": pmid, "retmode": "xml", "email": email}
    if api_key:
        params["api_key"] = api_key
    xml = _get_text(f"{NCBI_EUTILS}/efetch.fcgi?{urllib.parse.urlencode(params)}")
    if not xml:
        return {"source": "pubmed", "found": False}
    return parse_pubmed(xml)


def resolve(citekey: str, bib_text: str) -> dict:
    ids = bib_ids(citekey, bib_text)
    parts = {
        "s2": fetch_s2(ids, _env("S2_API_KEY")),
        "openalex": fetch_openalex(ids, _env("OPENALEX_API_KEY"), _env("NCBI_EMAIL")),
        "crossref": fetch_crossref(ids, _env("NCBI_EMAIL")),
        "pubmed": fetch_pubmed(ids, _env("NCBI_EMAIL"), _env("NCBI_API_KEY")),
    }
    return {"citekey": citekey, "ids": ids, "parts": parts, "merged": merge(parts)}


# --------------------------------------------------------------------------- #
# --diagnose — the build-time merge spike, emitted by the merge code itself
# --------------------------------------------------------------------------- #
def diagnose(bib_path: Path, n: int, seed: int = 13) -> int:
    import re

    text = bib_path.read_text(encoding="utf-8", errors="ignore")
    keys = re.findall(r"^@[a-z]+\{([^,]+),", text, re.M | re.I)
    random.seed(seed)
    sample = random.sample(keys, min(n, len(keys)))
    agg = {
        "n": 0,
        "s2": 0,
        "oa": 0,
        "cr": 0,
        "pm": 0,
        "any": 0,
        "auth_match": 0,
        "auth_both": 0,
        "orcid_s2": 0,
        "orcid_oa": 0,
        "ref_union": 0,
        "ref_s2": 0,
        "ref_cr": 0,
        "oa_refs_wid": 0,
        "no_id": 0,
    }
    t0 = time.monotonic()
    for ck in sample:
        try:
            r = resolve(ck, text)
        except KeyError:
            continue
        agg["n"] += 1
        p, m = r["parts"], r["merged"]
        if not _s2_id(r["ids"]) and not r["ids"]["doi"]:
            agg["no_id"] += 1
        s2f, oaf, crf = p["s2"]["found"], p["openalex"]["found"], p["crossref"]["found"]
        pmf = p["pubmed"]["found"]
        agg["s2"] += s2f
        agg["oa"] += oaf
        agg["cr"] += crf
        agg["pm"] += pmf
        agg["any"] += s2f or oaf or crf or pmf
        if s2f and oaf:
            agg["auth_both"] += 1
            agg["auth_match"] += len(p["s2"]["authors"]) == len(p["openalex"]["authors"])
        agg["orcid_s2"] += p["s2"].get("orcid_count", 0) if s2f else 0
        agg["orcid_oa"] += p["openalex"].get("orcid_count", 0) if oaf else 0
        agg["ref_s2"] += p["s2"].get("refs_returned", 0) if s2f else 0
        agg["ref_cr"] += len(p["crossref"].get("refs") or []) if crf else 0
        agg["oa_refs_wid"] += len(p["openalex"].get("referenced_works") or []) if oaf else 0
        agg["ref_union"] += len(m["references"])
        flags = []
        if s2f and oaf and len(p["s2"]["authors"]) != len(p["openalex"]["authors"]):
            flags.append(f"authors {len(p['s2']['authors'])}/{len(p['openalex']['authors'])}")
        print(
            f"  {ck[:30]:30} S2={'Y' if s2f else '.'} OA={'Y' if oaf else '.'} "
            f"CR={'Y' if crf else '.'} PM={'Y' if pmf else '.'} | refs U={len(m['references'])} "
            f"(s2={p['s2'].get('refs_returned', 0)} cr={len(p['crossref'].get('refs') or [])}) "
            f"| auth<-{m['provenance']['authors']}" + (f"  ! {','.join(flags)}" if flags else "")
        )
    a, dt = agg, time.monotonic() - t0
    nz = max(a["n"], 1)
    print(f"\n=== merge diagnostics (n={a['n']}, {dt:.0f}s) ===")
    print(
        f"  coverage:  any={a['any']}/{a['n']}  S2={a['s2']}  OpenAlex={a['oa']}  "
        f"Crossref={a['cr']}  PubMed={a['pm']}  no-resolvable-id={a['no_id']}"
    )
    print(
        f"  authors:   both-present={a['auth_both']}  count-agree={a['auth_match']}/{max(a['auth_both'], 1)}"
    )
    print(
        f"  ORCID:     total from S2={a['orcid_s2']}  vs OpenAlex={a['orcid_oa']}  "
        f"(merge takes authors from the higher-ORCID source)"
    )
    print(
        f"  refs:      avg union={a['ref_union'] / nz:.1f}  (S2 avg={a['ref_s2'] / nz:.1f}, "
        f"Crossref avg={a['ref_cr'] / nz:.1f}; OpenAlex W-id refs avg={a['oa_refs_wid'] / nz:.1f} — "
        f"different keyspace, not merged)"
    )
    return 0


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Tier-1 resolve+merge (ADR-30)")
    ap.add_argument("--citekey")
    ap.add_argument("--bib")
    ap.add_argument("--diagnose", action="store_true")
    ap.add_argument("--sample", type=int, default=60)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not a.bib:
        ap.error("--bib required")
    bib = Path(a.bib)
    if not bib.is_file():
        print(f"bib not found: {bib}", file=sys.stderr)
        return 3
    if a.diagnose:
        return diagnose(bib, a.sample)
    if not a.citekey:
        ap.error("provide --citekey (or --diagnose)")
    r = resolve(a.citekey, bib.read_text(encoding="utf-8", errors="ignore"))
    print(
        json.dumps(r, ensure_ascii=False, indent=2)
        if a.json
        else json.dumps(r["merged"], ensure_ascii=False, indent=2)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
