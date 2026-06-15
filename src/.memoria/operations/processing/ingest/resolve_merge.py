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
by the code that will rely on it. Needs S2_API_KEY / OPENALEX_API_KEY / NCBI_EMAIL
in the environment (read from ~/.hermes/.env if not already exported).

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
import xml.etree.ElementTree as ET
from pathlib import Path

import ingest_paper  # sibling module — reuse the .bib parser

S2_BASE = "https://api.semanticscholar.org/graph/v1"
OA_BASE = "https://api.openalex.org"
CR_BASE = "https://api.crossref.org"
NCBI_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
S2_FIELDS = ("title,year,externalIds,referenceCount,citationCount,tldr,"
             "s2FieldsOfStudy,publicationTypes,authors.name,authors.externalIds,"
             "references.externalIds,references.title")
_S2_LAST = [0.0]  # crude ~1 req/s throttle for S2


def _env(key: str) -> str:
    v = os.environ.get(key, "")
    if v:
        return v
    envf = Path.home() / ".hermes" / ".env"
    if envf.is_file():
        for line in envf.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip()
    return ""


def _get(url: str, headers: dict | None = None, data: bytes | None = None, retries: int = 3):
    """GET/POST JSON. Retries on HTTP 429 (rate limit) with Retry-After / backoff so
    a single burst-throttle doesn't silently drop a co-primary source (S2 is the
    chief offender). Other errors return None (treated as not-found by callers)."""
    req = urllib.request.Request(url, headers=headers or {}, data=data)
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries:
                ra = (e.headers or {}).get("Retry-After", "")
                wait = float(ra) if ra.isdigit() else min(2 ** attempt, 8)
                time.sleep(wait + random.random())
                continue
            if e.code not in (404, 429):
                print(f"[resolve_merge] HTTP {e.code} {e.reason} from {url}", file=sys.stderr)
            return None
        except Exception as exc:
            print(f"[resolve_merge] {type(exc).__name__} fetching {url}: {exc}",
                  file=sys.stderr)
            return None
    return None


def _get_text(url: str, retries: int = 3) -> str | None:
    """GET text/XML with the same 429 retry behavior as _get."""
    req = urllib.request.Request(url)
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read().decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries:
                ra = (e.headers or {}).get("Retry-After", "")
                wait = float(ra) if ra.isdigit() else min(2 ** attempt, 8)
                time.sleep(wait + random.random())
                continue
            if e.code != 404:
                print(f"[resolve_merge] HTTP {e.code} {e.reason} from {url}", file=sys.stderr)
            return None
        except Exception as exc:
            print(f"[resolve_merge] {type(exc).__name__} fetching {url}: {exc}",
                  file=sys.stderr)
            return None
    return None


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
        out.append({
            "doi": (ext.get("DOI") or "").lower(),
            "arxiv": (ext.get("ArXiv") or "").lower(),
            "title": r.get("title") or "",
        })
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
    d = _get(f"{S2_BASE}/paper/{urllib.parse.quote(sid)}?fields={S2_FIELDS}",
             {"x-api-key": key} if key else {})
    if not d or not d.get("paperId"):
        return {"source": "s2", "found": False}
    authors = [{"name": a.get("name", ""),
                "orcid": (a.get("externalIds") or {}).get("ORCID", "")}
               for a in d.get("authors") or []]
    refs = _norm_refs_s2(d.get("references"))
    ext = d.get("externalIds") or {}
    return {
        "source": "s2", "found": True,
        "s2_id": d.get("paperId", ""),
        "pmid": str(ext.get("PubMed") or ""), "pmcid": str(ext.get("PubMedCentral") or ""),
        "title": d.get("title", ""), "year": d.get("year"),
        "authors": authors, "orcid_count": sum(1 for a in authors if a["orcid"]),
        "tldr": (d.get("tldr") or {}).get("text", ""),
        "fields_of_study": [f.get("category") for f in d.get("s2FieldsOfStudy") or []],
        "publication_types": d.get("publicationTypes") or [],
        "ref_count_reported": d.get("referenceCount"),
        "refs": refs, "refs_returned": len(refs),
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
    authors = [{"name": a.get("author", {}).get("display_name", ""),
                "orcid": (a.get("author", {}).get("orcid") or ""),
                "affiliation": (a.get("institutions") or [{}])[0].get("display_name", "")
                if a.get("institutions") else "",
                "ror": (a.get("institutions") or [{}])[0].get("ror", "")
                if a.get("institutions") else ""}
               for a in d.get("authorships") or []]
    src = (d.get("primary_location") or {}).get("source") or {}
    oaids = d.get("ids") or {}
    return {
        "source": "openalex", "found": True,
        "openalex_id": (d.get("id") or "").rsplit("/", 1)[-1],
        "pmid": (oaids.get("pmid") or "").rsplit("/", 1)[-1],
        "pmcid": (oaids.get("pmcid") or "").rsplit("/", 1)[-1],
        "title": d.get("title", ""), "year": d.get("publication_year"),
        "authors": authors, "orcid_count": sum(1 for a in authors if a["orcid"]),
        "venue": src.get("display_name", ""), "issn": (src.get("issn_l") or ""),
        "topics": [t.get("display_name") for t in d.get("topics") or []],
        # scored topics feed the classify stage (D21/ADR-54) — keep the OpenAlex
        # score and the subfield/field/domain rollup, no extra network call needed
        "topics_scored": [
            {"name": t.get("display_name", ""),
             "score": float(t.get("score") or 0.0),
             "subfield": ((t.get("subfield") or {}).get("display_name", "")),
             "field": ((t.get("field") or {}).get("display_name", "")),
             "domain": ((t.get("domain") or {}).get("display_name", ""))}
            for t in d.get("topics") or []],
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
    authors = [{"name": " ".join(x for x in (a.get("given"), a.get("family")) if x),
                "orcid": (a.get("ORCID") or "").rsplit("/", 1)[-1] if a.get("ORCID") else ""}
               for a in m.get("author") or []]
    return {
        "source": "crossref", "found": True,
        "title": (m.get("title") or [""])[0],
        "year": (m.get("issued", {}).get("date-parts", [[None]]) or [[None]])[0][0],
        "authors": authors, "orcid_count": sum(1 for a in authors if a["orcid"]),
        "venue": (m.get("container-title") or [""])[0],
        "issn": (m.get("ISSN") or [""])[0],
        "refs": refs, "ref_count_reported": m.get("reference-count"),
    }


def _article_text(article: ET.Element, path: str) -> str:
    node = article.find(path)
    return "".join(node.itertext()).strip() if node is not None else ""


def _pubmed_year(article: ET.Element):
    for path in (
        ".//JournalIssue/PubDate/Year",
        ".//ArticleDate/Year",
        ".//PubMedPubDate[@PubStatus='pubmed']/Year",
        ".//PubMedPubDate/Year",
    ):
        text = _article_text(article, path)
        if text.isdigit():
            return int(text)
    return None


def parse_pubmed(xml: str) -> dict:
    """Normalize PubMed efetch XML into the partial-record shape."""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return {"source": "pubmed", "found": False}
    article = root.find(".//PubmedArticle")
    if article is None:
        return {"source": "pubmed", "found": False}
    ids = {}
    for node in article.findall(".//ArticleId"):
        kind = (node.attrib.get("IdType") or "").lower()
        if kind:
            ids[kind] = (node.text or "").strip()
    medline = article.find(".//MedlineCitation")
    pmid = _article_text(article, ".//MedlineCitation/PMID")
    title = _article_text(article, ".//Article/ArticleTitle")
    venue = _article_text(article, ".//Journal/Title")
    authors = []
    for a in article.findall(".//AuthorList/Author"):
        collective = _article_text(a, "CollectiveName")
        if collective:
            authors.append({"name": collective, "orcid": ""})
            continue
        name = " ".join(x for x in (_article_text(a, "ForeName"),
                                    _article_text(a, "LastName")) if x)
        orcid = ""
        for ident in a.findall("Identifier"):
            if (ident.attrib.get("Source") or "").upper() == "ORCID":
                orcid = (ident.text or "").rsplit("/", 1)[-1]
        if name:
            authors.append({"name": name, "orcid": orcid})
    pub_types = [_article_text(p, ".") for p in article.findall(".//PublicationTypeList/PublicationType")]
    mesh = [_article_text(m, "DescriptorName") for m in article.findall(".//MeshHeadingList/MeshHeading")]
    return {
        "source": "pubmed", "found": True,
        "pmid": pmid or ids.get("pubmed", ""), "pmcid": ids.get("pmc", ""),
        "doi": ids.get("doi", ""), "title": title, "year": _pubmed_year(article),
        "authors": authors, "orcid_count": sum(1 for a in authors if a["orcid"]),
        "venue": venue,
        "publication_types": [p for p in pub_types if p],
        "mesh_terms": [m for m in mesh if m],
        "nlm_unique_id": _article_text(medline, "MedlineJournalInfo/NlmUniqueID") if medline is not None else "",
    }


def _pubmed_id(ids: dict, email: str, api_key: str) -> str:
    if ids.get("pmid"):
        return ids["pmid"]
    if not ids.get("doi"):
        return ""
    params = {"db": "pubmed", "retmode": "json", "term": f"{ids['doi']}[doi]",
              "email": email}
    if api_key:
        params["api_key"] = api_key
    d = _get(f"{NCBI_EUTILS}/esearch.fcgi?{urllib.parse.urlencode(params)}")
    ids_found = (((d or {}).get("esearchresult") or {}).get("idlist") or [])
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


# --------------------------------------------------------------------------- #
# Merge — per-field best-source, references union deduped by DOI
# --------------------------------------------------------------------------- #
def _pick(parts: dict, field: str, order: list[str]):
    for s in order:
        v = parts.get(s, {}).get(field)
        if v:
            return v, s
    return "", ""


def union_refs(parts: dict) -> list[dict]:
    seen, out = {}, []
    for s in ("s2", "crossref"):  # both expose ref DOIs; OpenAlex refs are W-ids (skipped)
        for r in parts.get(s, {}).get("refs") or []:
            key = r.get("doi") or ("arxiv:" + r["arxiv"] if r.get("arxiv") else None)
            if not key:
                continue
            if key not in seen:
                seen[key] = {"doi": r.get("doi", ""), "arxiv": r.get("arxiv", ""),
                             "title": r.get("title", ""), "sources": [s]}
                out.append(seen[key])
            else:
                seen[key]["sources"].append(s)
    return out



def _norm_title(s: str) -> str:
    return "".join(c for c in (s or "").lower() if c.isalnum())


def agreement(parts: dict) -> tuple[float, list[str]]:
    """Cross-source identity agreement in [0,1] + the disagreements (ADR-56).

    The merge is per-field best-source-wins, which silently papers over a source
    that resolved a *different work*. Score: title agreement (normalized exact
    across found sources) and year agreement. One source found = trusted (1.0) —
    nothing to disagree with; zero found = 0.0.
    """
    found = [s for s in ("crossref", "openalex", "pubmed", "s2") if parts.get(s, {}).get("found")]
    if not found:
        return 0.0, ["no source resolved this work"]
    if len(found) == 1:
        return 1.0, []
    disagreements: list[str] = []
    titles = {s: _norm_title(parts[s].get("title", "")) for s in found if parts[s].get("title")}
    if len(set(titles.values())) > 1:
        disagreements.append("title differs across sources: "
                             + "; ".join(f"{s}={parts[s].get('title','')!r}" for s in titles))
    years = {s: parts[s].get("year") for s in found if parts[s].get("year")}
    if len({y for y in years.values() if y}) > 1:
        disagreements.append("year differs across sources: "
                             + "; ".join(f"{s}={y}" for s, y in years.items()))
    score = 1.0 - 0.5 * len(disagreements)
    return max(score, 0.0), disagreements


def merge(parts: dict) -> dict:
    # authors: prefer the source carrying the most ORCIDs (OpenAlex, per the spike)
    auth_src = max(("openalex", "pubmed", "s2", "crossref"),
                   key=lambda s: parts.get(s, {}).get("orcid_count", -1)
                   if parts.get(s, {}).get("found") else -1)
    authors = parts.get(auth_src, {}).get("authors") or []
    title, t_src = _pick(parts, "title", ["crossref", "openalex", "pubmed", "s2"])
    year, y_src = _pick(parts, "year", ["crossref", "openalex", "pubmed", "s2"])
    venue, v_src = _pick(parts, "venue", ["openalex", "crossref", "pubmed"])
    refs = union_refs(parts)
    return {
        "title": title, "year": year, "venue": venue,
        "issn": parts.get("openalex", {}).get("issn") or parts.get("crossref", {}).get("issn", ""),
        "s2_id": parts.get("s2", {}).get("s2_id", ""),
        "openalex_id": parts.get("openalex", {}).get("openalex_id", ""),
        "pmid": (parts.get("pubmed", {}).get("pmid") or parts.get("openalex", {}).get("pmid")
                 or parts.get("s2", {}).get("pmid", "")),
        "pmcid": (parts.get("pubmed", {}).get("pmcid") or parts.get("openalex", {}).get("pmcid")
                  or parts.get("s2", {}).get("pmcid", "")),
        "authors": authors,
        "tldr": parts.get("s2", {}).get("tldr", ""),
        "fields_of_study": parts.get("s2", {}).get("fields_of_study") or [],
        "topics": parts.get("openalex", {}).get("topics") or [],
        "topics_scored": parts.get("openalex", {}).get("topics_scored") or [],
        "publication_types": (parts.get("pubmed", {}).get("publication_types")
                              or parts.get("s2", {}).get("publication_types") or []),
        "mesh_terms": parts.get("pubmed", {}).get("mesh_terms") or [],
        "references": refs,
        "citation_count": parts.get("s2", {}).get("citation_count"),
        "provenance": {"title": t_src, "year": y_src, "venue": v_src, "authors": auth_src},
        "agreement": dict(zip(("score", "disagreements"), agreement(parts), strict=True)),
    }


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
    agg = {"n": 0, "s2": 0, "oa": 0, "cr": 0, "pm": 0, "any": 0,
           "auth_match": 0, "auth_both": 0, "orcid_s2": 0, "orcid_oa": 0,
           "ref_union": 0, "ref_s2": 0, "ref_cr": 0, "oa_refs_wid": 0, "no_id": 0}
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
        agg["any"] += (s2f or oaf or crf or pmf)
        if s2f and oaf:
            agg["auth_both"] += 1
            agg["auth_match"] += (len(p["s2"]["authors"]) == len(p["openalex"]["authors"]))
        agg["orcid_s2"] += p["s2"].get("orcid_count", 0) if s2f else 0
        agg["orcid_oa"] += p["openalex"].get("orcid_count", 0) if oaf else 0
        agg["ref_s2"] += p["s2"].get("refs_returned", 0) if s2f else 0
        agg["ref_cr"] += len(p["crossref"].get("refs") or []) if crf else 0
        agg["oa_refs_wid"] += len(p["openalex"].get("referenced_works") or []) if oaf else 0
        agg["ref_union"] += len(m["references"])
        flags = []
        if s2f and oaf and len(p["s2"]["authors"]) != len(p["openalex"]["authors"]):
            flags.append(f"authors {len(p['s2']['authors'])}/{len(p['openalex']['authors'])}")
        print(f"  {ck[:30]:30} S2={'Y' if s2f else '.'} OA={'Y' if oaf else '.'} "
              f"CR={'Y' if crf else '.'} PM={'Y' if pmf else '.'} | refs U={len(m['references'])} "
              f"(s2={p['s2'].get('refs_returned',0)} cr={len(p['crossref'].get('refs') or [])}) "
              f"| auth<-{m['provenance']['authors']}" + (f"  ! {','.join(flags)}" if flags else ""))
    a, dt = agg, time.monotonic() - t0
    nz = max(a["n"], 1)
    print(f"\n=== merge diagnostics (n={a['n']}, {dt:.0f}s) ===")
    print(f"  coverage:  any={a['any']}/{a['n']}  S2={a['s2']}  OpenAlex={a['oa']}  "
          f"Crossref={a['cr']}  PubMed={a['pm']}  no-resolvable-id={a['no_id']}")
    print(f"  authors:   both-present={a['auth_both']}  count-agree={a['auth_match']}/{max(a['auth_both'],1)}")
    print(f"  ORCID:     total from S2={a['orcid_s2']}  vs OpenAlex={a['orcid_oa']}  "
          f"(merge takes authors from the higher-ORCID source)")
    print(f"  refs:      avg union={a['ref_union']/nz:.1f}  (S2 avg={a['ref_s2']/nz:.1f}, "
          f"Crossref avg={a['ref_cr']/nz:.1f}; OpenAlex W-id refs avg={a['oa_refs_wid']/nz:.1f} — "
          f"different keyspace, not merged)")
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
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.json
          else json.dumps(r["merged"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
