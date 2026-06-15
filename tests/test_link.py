"""L1 component test for link — extracted from its former --self-test (ADR-44)."""
import link as _m

plan_cites = _m.plan_cites
plan_entities = _m.plan_entities


def test_link():
    def _run():
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
            ("venue note by ISSN", len(nt("venue")) == 1 and nt("venue")[0]["id"] == "2398-6352"),
            ("venue path is ID-keyed", nt("venue")[0]["path"] == "catalog/venues/2398-6352.md"),
            ("person notes only for ORCID authors (2 of 3)", len(nt("person")) == 2),
            ("ORCID kept bare (no URI)", all("/" not in e["id"] for e in nt("person"))),
            ("person path is ID-keyed (ORCID)", all(e["path"] == f"catalog/people/{e['id']}.md" for e in nt("person"))),
            ("org deduped by ROR (1, not 2)", len(nt("organization")) == 1),
            ("org path is ID-keyed (ROR)", nt("organization")[0]["path"] == "catalog/organizations/042nb2s44.md"),
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
    assert _run() == 0
