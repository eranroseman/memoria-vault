"""L1 component tests for link (ADR-44)."""

import json

from operations.processing.ingest import link as _m

append_by_name_audit = _m.append_by_name_audit
plan_cites = _m.plan_cites
plan_entities = _m.plan_entities
plan_links = _m.plan_links


MERGED = {
    "venue": "npj Digital Medicine",
    "issn": "2398-6352",
    "authors": [
        {
            "name": "Alice A",
            "orcid": "https://orcid.org/0000-0002-1825-0097",
            "affiliation": "MIT",
            "ror": "https://ror.org/042nb2s44",
        },
        {"name": "Bob B", "orcid": "", "affiliation": "Acme Lab", "ror": ""},
        {
            "name": "Carol C",
            "orcid": "0000-0001-2345-6789",
            "affiliation": "MIT",
            "ror": "https://ror.org/042nb2s44",
        },
    ],
    "references": [
        {"doi": "10.1/in-vault", "arxiv": "", "sources": ["s2", "crossref"]},
        {"doi": "10.1/not-in-vault", "arxiv": "", "sources": ["crossref"]},
        {"doi": "", "arxiv": "2401.00001", "sources": ["s2"]},
        {"doi": "10.1/in-vault", "arxiv": "", "sources": ["s2"]},
    ],
}


def _entities(note_type):
    return [e for e in plan_entities(MERGED)["entities"] if e["note_type"] == note_type]


def test_plan_entities_creates_id_keyed_venue_note():
    venues = _entities("venue")

    assert len(venues) == 1
    assert venues[0]["id"] == "2398-6352"
    assert venues[0]["path"] == "catalog/entities/venue-2398-6352.md"


def test_plan_entities_creates_id_keyed_person_notes_only_for_orcid_authors():
    people = _entities("person")

    assert len(people) == 2
    assert all("/" not in e["id"] for e in people)
    assert all(e["path"] == f"catalog/entities/person-{e['id']}.md" for e in people)


def test_plan_entities_dedupes_orgs_by_ror_and_records_names_without_ids():
    plan = plan_entities(MERGED)
    orgs = [e for e in plan["entities"] if e["note_type"] == "organization"]

    assert len(orgs) == 1
    assert orgs[0]["path"] == "catalog/entities/organization-042nb2s44.md"
    assert plan["recorded_by_name"]["authors"] == ["Bob B"]
    assert "Acme Lab" in plan["recorded_by_name"]["orgs"]


def test_plan_cites_matches_and_dedupes_doi_and_arxiv_edges():
    vidx = {"10.1/in-vault": "smith2020Paper", "2401.00001": "lee2024Pre"}

    cites = plan_cites(MERGED, vidx)

    assert len(cites) == 2
    assert {c["via"] for c in cites} == {"doi", "arxiv"}
    assert {c["to"] for c in cites} == {"smith2020Paper", "lee2024Pre"}


def test_recorded_by_name_audit_logs_collision_counter(tmp_path):
    plan = plan_links(MERGED, tmp_path)

    rec = append_by_name_audit(tmp_path, "x2024Test", plan)
    rows = (tmp_path / "system" / "logs" / "linkage.jsonl").read_text(encoding="utf-8").splitlines()
    logged = json.loads(rows[0])

    assert rec["event"] == "recorded_by_name"
    assert rec["total"] == 2
    assert rec["counts"] == {"authors": 1, "venues": 0, "orgs": 1}
    assert logged["citekey"] == "x2024Test"
