"""PubMed XML normalization for resolve_merge."""

from __future__ import annotations

import xml.etree.ElementTree as ET


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
        root = ET.fromstring(xml)  # noqa: S314
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
    for author in article.findall(".//AuthorList/Author"):
        collective = _article_text(author, "CollectiveName")
        if collective:
            authors.append({"name": collective, "orcid": ""})
            continue
        name = " ".join(
            value
            for value in (
                _article_text(author, "ForeName"),
                _article_text(author, "LastName"),
            )
            if value
        )
        orcid = ""
        for ident in author.findall("Identifier"):
            if (ident.attrib.get("Source") or "").upper() == "ORCID":
                orcid = (ident.text or "").rsplit("/", 1)[-1]
        if name:
            authors.append({"name": name, "orcid": orcid})
    pub_types = [
        _article_text(pub_type, ".")
        for pub_type in article.findall(".//PublicationTypeList/PublicationType")
    ]
    mesh = [
        _article_text(heading, "DescriptorName")
        for heading in article.findall(".//MeshHeadingList/MeshHeading")
    ]
    return {
        "source": "pubmed",
        "found": True,
        "pmid": pmid or ids.get("pubmed", ""),
        "pmcid": ids.get("pmc", ""),
        "doi": ids.get("doi", ""),
        "title": title,
        "year": _pubmed_year(article),
        "authors": authors,
        "orcid_count": sum(1 for author in authors if author["orcid"]),
        "venue": venue,
        "publication_types": [pub_type for pub_type in pub_types if pub_type],
        "mesh_terms": [heading for heading in mesh if heading],
        "nlm_unique_id": (
            _article_text(medline, "MedlineJournalInfo/NlmUniqueID") if medline is not None else ""
        ),
    }
