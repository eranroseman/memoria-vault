"""Pure merge and agreement helpers for resolve_merge."""

from __future__ import annotations


def _pick(parts: dict, field: str, order: list[str]):
    for source in order:
        value = parts.get(source, {}).get(field)
        if value:
            return value, source
    return "", ""


def union_refs(parts: dict) -> list[dict]:
    seen, out = {}, []
    for source in ("s2", "crossref"):  # both expose ref DOIs; OpenAlex refs are W-ids.
        for ref in parts.get(source, {}).get("refs") or []:
            key = ref.get("doi") or ("arxiv:" + ref["arxiv"] if ref.get("arxiv") else None)
            if not key:
                continue
            if key not in seen:
                seen[key] = {
                    "doi": ref.get("doi", ""),
                    "arxiv": ref.get("arxiv", ""),
                    "title": ref.get("title", ""),
                    "sources": [source],
                }
                out.append(seen[key])
            else:
                seen[key]["sources"].append(source)
    return out


def _norm_title(value: str) -> str:
    return "".join(char for char in (value or "").lower() if char.isalnum())


def agreement(parts: dict) -> tuple[float, list[str]]:
    """Cross-source identity agreement in [0,1] + disagreements (ADR-56)."""
    found = [
        source
        for source in ("crossref", "openalex", "pubmed", "s2")
        if parts.get(source, {}).get("found")
    ]
    if not found:
        return 0.0, ["no source resolved this work"]
    if len(found) == 1:
        return 1.0, []
    disagreements: list[str] = []
    titles = {
        source: _norm_title(parts[source].get("title", ""))
        for source in found
        if parts[source].get("title")
    }
    if len(set(titles.values())) > 1:
        disagreements.append(
            "title differs across sources: "
            + "; ".join(f"{source}={parts[source].get('title', '')!r}" for source in titles)
        )
    years = {source: parts[source].get("year") for source in found if parts[source].get("year")}
    if len({year for year in years.values() if year}) > 1:
        disagreements.append(
            "year differs across sources: "
            + "; ".join(f"{source}={year}" for source, year in years.items())
        )
    # 0.5 penalty per disagreement: two disagreements (title + year) floors to 0.0.
    score = 1.0 - 0.5 * len(disagreements)
    return max(score, 0.0), disagreements


def merge(parts: dict) -> dict:
    # authors: prefer the source carrying the most ORCIDs (OpenAlex, per the spike)
    auth_src = max(
        ("openalex", "pubmed", "s2", "crossref"),
        key=lambda source: (
            parts.get(source, {}).get("orcid_count", -1)
            if parts.get(source, {}).get("found")
            else -1
        ),
    )
    authors = parts.get(auth_src, {}).get("authors") or []
    title, title_src = _pick(parts, "title", ["crossref", "openalex", "pubmed", "s2"])
    year, year_src = _pick(parts, "year", ["crossref", "openalex", "pubmed", "s2"])
    venue, venue_src = _pick(parts, "venue", ["openalex", "crossref", "pubmed"])
    refs = union_refs(parts)
    return {
        "title": title,
        "year": year,
        "venue": venue,
        "issn": parts.get("openalex", {}).get("issn") or parts.get("crossref", {}).get("issn", ""),
        "s2_id": parts.get("s2", {}).get("s2_id", ""),
        "openalex_id": parts.get("openalex", {}).get("openalex_id", ""),
        "pmid": (
            parts.get("pubmed", {}).get("pmid")
            or parts.get("openalex", {}).get("pmid")
            or parts.get("s2", {}).get("pmid", "")
        ),
        "pmcid": (
            parts.get("pubmed", {}).get("pmcid")
            or parts.get("openalex", {}).get("pmcid")
            or parts.get("s2", {}).get("pmcid", "")
        ),
        "authors": authors,
        "tldr": parts.get("s2", {}).get("tldr", ""),
        "fields_of_study": parts.get("s2", {}).get("fields_of_study") or [],
        "topics": parts.get("openalex", {}).get("topics") or [],
        "topics_scored": parts.get("openalex", {}).get("topics_scored") or [],
        "publication_types": (
            parts.get("pubmed", {}).get("publication_types")
            or parts.get("s2", {}).get("publication_types")
            or []
        ),
        "mesh_terms": parts.get("pubmed", {}).get("mesh_terms") or [],
        "references": refs,
        "citation_count": parts.get("s2", {}).get("citation_count"),
        "provenance": {
            "title": title_src,
            "year": year_src,
            "venue": venue_src,
            "authors": auth_src,
        },
        "agreement": dict(zip(("score", "disagreements"), agreement(parts), strict=True)),
    }
