"""L1 component test for verify_mcp — extracted from its former --self-test (ADR-44)."""
import retraction as _m
globals().update({k: getattr(_m, k) for k in dir(_m) if not k.startswith("__")})


def test_retraction_verdicts():
    def _run():
        import tempfile
        global _RW_INDEX

        # Retraction Watch CSV fixture
        rw_rows = [
            {"OriginalPaperDOI": "10.1/Retracted", "RetractionNature": "Retraction",
             "RetractionDate": "2021-05-03", "RetractionDOI": "10.1/rw-ret"},
            {"OriginalPaperDOI": "10.1/Concern", "RetractionNature": "Expression of Concern",
             "RetractionDate": "2022-01-01", "RetractionDOI": "10.1/rw-eoc"},
        ]
        idx = build_rw_index(rw_rows)

        cr_upd = {"update-to": [{"type": "retraction", "DOI": "10.1/cr",
                                 "updated": {"date-parts": [[2021, 5, 3]]}}]}
        cr_rel = {"relation": {"is-retracted-by": [{"id-type": "doi", "id": "10.1/rb"}]}}
        cr_clean = {"title": ["Fine"]}

        # CSV file round-trip for load/lookup
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "rw.csv"
            with p.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["OriginalPaperDOI", "RetractionNature", "RetractionDate", "RetractionDOI"])
                w.writeheader()
                w.writerows(rw_rows)
            _m._RW_INDEX = None
            hit = rw_lookup("10.1/RETRACTED", p)         # case-insensitive match
            _m._RW_INDEX = None
            miss = rw_lookup("10.1/unknown", p)
            _m._RW_INDEX = None
            absent = rw_lookup("10.1/x", Path(td) / "nope.csv")
        _m._RW_INDEX = None

        checks = [
            ("rw index: retraction indexed", idx["10.1/retracted"]["retracted"] is True),
            ("rw index: EoC not a retraction", idx["10.1/concern"]["retracted"] is False),
            ("rw lookup: case-insensitive hit", hit and hit["retracted"] is True and hit["date"] == "2021-05-03"),
            ("rw lookup: known-clean DOI → not retracted", miss is not None and miss["retracted"] is False),
            ("rw lookup: absent CSV → None (unavailable)", absent is None),
            ("crossref update-to → retracted + date", crossref_retraction(cr_upd)["retracted"] is True
             and crossref_retraction(cr_upd)["date"] == "2021-05-03"),
            ("crossref relation → retracted", crossref_retraction(cr_rel)["via"] == "relation"),
            ("crossref clean → not retracted", crossref_retraction(cr_clean)["retracted"] is False),
            ("open-retractions 404 → not retracted", open_retractions_verdict(404, None)["retracted"] is False),
            ("open-retractions 200 → retracted", open_retractions_verdict(200, {"retracted": True, "retractions": [{"date": "2020-01-01"}]})["retracted"] is True),
            ("open-retractions error → unknown", open_retractions_verdict(0, None)["retracted"] is None),
            ("combine all-clean → False/agree",
             (lambda r: r["retracted"] is False and r["agreement"] == "agree")(
                 combine("10.1/x", {"retraction_watch": {"retracted": False}, "crossref": {"retracted": False}, "open_retractions": {"retracted": False}}, {}))),
            ("combine RW-retracted others-clean → True/disagree",
             (lambda r: r["retracted"] is True and r["agreement"] == "disagree" and r["retraction_doi"] == "10.1/rw")(
                 combine("10.1/x", {"retraction_watch": {"retracted": True, "retraction_doi": "10.1/rw"}, "crossref": {"retracted": False}, "open_retractions": {"retracted": False}}, {}))),
            ("combine all-retracted → True/agree",
             (lambda r: r["retracted"] is True and r["agreement"] == "agree")(
                 combine("10.1/x", {"retraction_watch": {"retracted": True}, "crossref": {"retracted": True}, "open_retractions": {"retracted": True}}, {}))),
            ("combine no-data → None/no-data",
             (lambda r: r["retracted"] is None and r["agreement"] == "no-data")(
                 combine("10.1/x", {"retraction_watch": None, "crossref": None, "open_retractions": None}, {}))),
            ("combine single-source clean → False/single-source",
             (lambda r: r["retracted"] is False and r["agreement"] == "single-source")(
                 combine("10.1/x", {"retraction_watch": {"retracted": False}, "crossref": None, "open_retractions": None}, {}))),
        ]
        bad = [n for n, ok in checks if not ok]
        for n, ok in checks:
            print(f"  {'PASS' if ok else 'FAIL'}  {n}")
        print(f"\n{'OK' if not bad else f'{len(bad)} FAILING'}: retraction.py self-test ({len(checks)} checks)")
        return 1 if bad else 0
    assert _run() == 0
