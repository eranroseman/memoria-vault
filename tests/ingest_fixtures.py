"""Shared ingest-pipeline fixtures for component tests."""

from __future__ import annotations

from memoria_vault.runtime.subsystems.processing.ingest import runner

BIB = (
    "@article{x2024Test,\n  title = {A Test},\n  author = {Doe, Jane},\n"
    "  year = {2024},\n  doi = {10.1/x},\n  journal = {J Tests},\n}\n"
)


def merged_record(topics_scored, publication_types=()):
    """A minimal resolve_merge-shaped merged record."""
    return {
        "title": "A Test",
        "year": 2024,
        "venue": "J Tests",
        "issn": "",
        "s2_id": "S2X",
        "openalex_id": "W1",
        "pmid": "",
        "pmcid": "",
        "authors": [{"name": "Jane Doe"}],
        "tldr": "",
        "fields_of_study": [],
        "topics": [t["name"] for t in topics_scored],
        "topics_scored": topics_scored,
        "publication_types": list(publication_types),
        "references": [],
        "citation_count": 1,
        "provenance": {"title": "openalex"},
        "agreement": {"score": 1.0, "disagreements": []},
    }


def topic(name, score, subfield=""):
    return {"name": name, "score": score, "subfield": subfield, "field": "F", "domain": "D"}


def run_enriched_pipeline(monkeypatch, vault, merged):
    """Run the enriched pipeline offline: stub the network stages."""
    monkeypatch.setattr(
        runner.resolve_merge,
        "resolve",
        lambda ck, bib: {
            "citekey": ck,
            "ids": {},
            "merged": merged,
            "parts": {
                "s2": {"found": True},
                "openalex": {"found": True},
                "crossref": {"found": False},
            },
        },
    )
    monkeypatch.setattr(
        runner.extract,
        "extract",
        lambda ids, pdf, email, api_key="": {
            "source": "none",
            "chars": 0,
            "degraded": True,
            "text": "",
        },
    )
    return runner.run("x2024Test", BIB, vault, enrich=True)
