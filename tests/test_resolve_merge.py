"""L1 component test for resolve_merge — extracted from its former --self-test (ADR-44)."""
import resolve_merge as _m
globals().update({k: getattr(_m, k) for k in dir(_m) if not k.startswith("__")})


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
        }
        m = merge(parts)
        m0 = merge({"s2": {"found": False}, "openalex": {"found": False}, "crossref": {"found": False}})

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
            ("pmid/pmcid prefer openalex", m["pmid"] == "222" and m["pmcid"] == "PMC999"),
            ("all-missing -> empty merge", m0["title"] == "" and m0["references"] == [] and m0["authors"] == []
             and m0["s2_id"] == "" and m0["openalex_id"] == ""),
        ]
        bad = [name for name, ok in checks if not ok]
        for name, ok in checks:
            print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        print(f"\n{'OK' if not bad else f'{len(bad)} FAILING'}: resolve_merge merge-logic self-test")
        return 1 if bad else 0
    assert _run() == 0
