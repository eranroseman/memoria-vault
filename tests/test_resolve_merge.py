"""L1 component test for resolve_merge — extracted from its former --self-test (ADR-44)."""
from operations.processing.ingest import resolve_merge as _m
from operations.processing.ingest import resolve_merge_logic as _logic

_get = _m._get
agreement = _m.agreement
merge = _m.merge
urllib = _m.urllib


def test_union_refs_dedupes_by_doi_and_keeps_source_provenance():
    refs = _logic.union_refs(
        {
            "s2": {
                "refs": [
                    {"doi": "10.1/a", "arxiv": "", "title": "A"},
                    {"doi": "", "arxiv": "2401.00001", "title": "ArXiv"},
                ]
            },
            "crossref": {
                "refs": [
                    {"doi": "10.1/a", "arxiv": "", "title": "A duplicate"},
                    {"doi": "", "arxiv": "", "title": "no stable id"},
                ]
            },
            "openalex": {"referenced_works": ["W1"]},
        }
    )

    assert refs == [
        {"doi": "10.1/a", "arxiv": "", "title": "A", "sources": ["s2", "crossref"]},
        {"doi": "", "arxiv": "2401.00001", "title": "ArXiv", "sources": ["s2"]},
    ]


def test_resolve_merge():
    def _run():
        """No-network test of the merge logic (fetchers are validated by --diagnose)."""
        parts = {
            "s2": {"found": True, "title": "S2 Title", "year": 2020, "s2_id": "S2PAPER1",
                   "pmid": "111", "pmcid": "",
                   "authors": [{"name": "A", "orcid": ""}, {"name": "B", "orcid": ""}],
                   "orcid_count": 0, "tldr": "a tldr", "fields_of_study": ["Computer Science"],
                   "publication_types": ["JournalArticle"], "citation_count": 5,
                   "refs": [{"doi": "10.1/a", "arxiv": "", "title": ""},
                            {"doi": "10.1/b", "arxiv": "", "title": ""}], "refs_returned": 2},
            "openalex": {"found": True, "title": "OA Title", "year": 2020,
                         "openalex_id": "W123", "pmid": "222", "pmcid": "PMC999",
                         "authors": [{"name": "Alice", "orcid": "x"}, {"name": "Bob", "orcid": "y"}],
                         "orcid_count": 2, "venue": "Some Venue", "issn": "1234-5678",
                         "topics": ["Topic A"], "referenced_works": ["W1", "W2"]},
            "crossref": {"found": True, "title": "CR Title", "year": 2019,
                         "authors": [{"name": "A", "orcid": ""}], "orcid_count": 0,
                         "venue": "CR Venue", "issn": "9999",
                         "refs": [{"doi": "10.1/b", "arxiv": "", "title": ""},
                                  {"doi": "10.1/c", "arxiv": "", "title": ""}]},
            "pubmed": {"found": True, "title": "PM Title", "year": 2020,
                       "pmid": "333", "pmcid": "PMC333",
                       "authors": [{"name": "Alice A", "orcid": ""}], "orcid_count": 0,
                       "venue": "PubMed Journal", "publication_types": ["Journal Article"],
                       "mesh_terms": ["Telemedicine"]},
        }
        m = merge(parts)
        m0 = merge({"s2": {"found": False}, "openalex": {"found": False},
                    "crossref": {"found": False}, "pubmed": {"found": False}})

        # _get must retry a 429 then succeed, rather than silently dropping the source
        _calls = [0]

        class _Resp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return b'{"ok": true}'

        def _fake(req, timeout=25):
            _calls[0] += 1
            if _calls[0] == 1:
                raise urllib.error.HTTPError(req.full_url, 429, "Too Many Requests", {"Retry-After": "0"}, None)
            return _Resp()

        _orig = urllib.request.urlopen
        urllib.request.urlopen = _fake
        try:
            _retried = _get("https://example/x")
        finally:
            urllib.request.urlopen = _orig

        checks = [
            ("429 retried then succeeded", _retried == {"ok": True} and _calls[0] == 2),
            ("authors<-openalex (most ORCIDs)", m["provenance"]["authors"] == "openalex" and len(m["authors"]) == 2),
            ("title<-crossref (precedence)", m["title"] == "CR Title" and m["provenance"]["title"] == "crossref"),
            ("venue<-openalex", m["venue"] == "Some Venue" and m["provenance"]["venue"] == "openalex"),
            ("tldr<-s2", m["tldr"] == "a tldr"),
            ("fields<-s2, topics<-openalex", m["fields_of_study"] == ["Computer Science"] and m["topics"] == ["Topic A"]),
            ("refs union deduped by DOI = 3", len(m["references"]) == 3),
            ("shared ref tagged both sources", any(set(r["sources"]) == {"s2", "crossref"} for r in m["references"])),
            ("stable IDs surfaced (s2/openalex)", m["s2_id"] == "S2PAPER1" and m["openalex_id"] == "W123"),
            ("pmid/pmcid prefer pubmed", m["pmid"] == "333" and m["pmcid"] == "PMC333"),
            ("mesh/pub types<-pubmed", m["mesh_terms"] == ["Telemedicine"]
             and m["publication_types"] == ["Journal Article"]),
            ("all-missing -> empty merge", m0["title"] == "" and m0["references"] == [] and m0["authors"] == []
             and m0["s2_id"] == "" and m0["openalex_id"] == ""),
        ]
        bad = [name for name, ok in checks if not ok]
        for name, ok in checks:
            print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        print(f"\n{'OK' if not bad else f'{len(bad)} FAILING'}: resolve_merge merge-logic self-test")
        return 1 if bad else 0
    assert _run() == 0


def test_resolve_merge_http_errors_emit_content_light_diagnostic(monkeypatch, tmp_path):
    monkeypatch.setenv("MEMORIA_DIAGNOSTICS_DIR", str(tmp_path / "diagnostics"))

    def _fake(req, timeout=25):
        raise urllib.error.HTTPError(req.full_url, 500, "Server leaked title", {}, None)

    monkeypatch.setattr(urllib.request, "urlopen", _fake)

    assert _get("https://example.test/private-title") is None
    log = next((tmp_path / "diagnostics").glob("diagnostics-*.jsonl"))
    text = log.read_text(encoding="utf-8")

    assert "http_error" in text
    assert "private-title" not in text
    assert "Server leaked title" not in text


def test_agreement_confidence_d51():
    """ADR-56: cross-source identity disagreement scores below the floor."""
    one = {"crossref": {"found": True, "title": "Same Work", "year": 2024}}
    score, dis = agreement(one)
    assert score == 1.0 and dis == []

    agree = {"crossref": {"found": True, "title": "Same Work", "year": 2024},
             "openalex": {"found": True, "title": "Same Work!", "year": 2024}}
    score, dis = agreement(agree)   # punctuation-insensitive
    assert score == 1.0 and dis == []

    clash = {"crossref": {"found": True, "title": "Work A", "year": 2024},
             "openalex": {"found": True, "title": "Entirely Different Work", "year": 2019}}
    score, dis = clash and agreement(clash)
    assert score == 0.0 and len(dis) == 2

    nothing = {"crossref": {"found": False}}
    score, dis = agreement(nothing)
    assert score == 0.0 and dis


def test_pubmed_parse_and_fetch(monkeypatch):
    xml = """<?xml version="1.0"?>
    <PubmedArticleSet><PubmedArticle>
      <MedlineCitation><PMID>12345</PMID>
        <Article>
          <Journal><Title>Journal of Tests</Title><JournalIssue><PubDate><Year>2024</Year></PubDate></JournalIssue></Journal>
          <ArticleTitle>A PubMed Only Work</ArticleTitle>
          <AuthorList><Author><ForeName>Jane</ForeName><LastName>Doe</LastName><Identifier Source="ORCID">https://orcid.org/0000-0001</Identifier></Author></AuthorList>
          <PublicationTypeList><PublicationType>Journal Article</PublicationType><PublicationType>Clinical Trial</PublicationType></PublicationTypeList>
        </Article>
        <MeshHeadingList><MeshHeading><DescriptorName>Telemedicine</DescriptorName></MeshHeading></MeshHeadingList>
      </MedlineCitation>
      <PubmedData><ArticleIdList><ArticleId IdType="doi">10.1/x</ArticleId><ArticleId IdType="pmc">PMC123</ArticleId></ArticleIdList></PubmedData>
    </PubmedArticle></PubmedArticleSet>"""
    parsed = _m.parse_pubmed(xml)
    assert parsed["found"] is True
    assert parsed["pmid"] == "12345"
    assert parsed["pmcid"] == "PMC123"
    assert parsed["title"] == "A PubMed Only Work"
    assert parsed["year"] == 2024
    assert parsed["authors"][0]["orcid"] == "0000-0001"
    assert parsed["publication_types"] == ["Journal Article", "Clinical Trial"]
    assert parsed["mesh_terms"] == ["Telemedicine"]

    seen = {}

    def fake_get(url, *a, **k):
        seen["esearch"] = url
        return {"esearchresult": {"idlist": ["12345"]}}

    def fake_text(url, *a, **k):
        seen["efetch"] = url
        return xml

    monkeypatch.setattr(_m, "_get", fake_get)
    monkeypatch.setattr(_m, "_get_text", fake_text)
    got = _m.fetch_pubmed({"doi": "10.1/x", "pmid": ""}, "pi@example.test", "KEY")
    assert got["found"] is True
    assert "10.1%2Fx%5Bdoi%5D" in seen["esearch"]
    assert "api_key=KEY" in seen["efetch"]
