"""L1 component tests for retraction (ADR-44)."""

from memoria_vault.runtime.subsystems.integrity.retraction import retraction as _m

Path = _m.Path
build_rw_index = _m.build_rw_index
combine = _m.combine
crossref_retraction = _m.crossref_retraction
csv = _m.csv
open_retractions_verdict = _m.open_retractions_verdict
rw_lookup = _m.rw_lookup

RW_ROWS = [
    {
        "OriginalPaperDOI": "10.1/Retracted",
        "RetractionNature": "Retraction",
        "RetractionDate": "2021-05-03",
        "RetractionDOI": "10.1/rw-ret",
    },
    {
        "OriginalPaperDOI": "10.1/Concern",
        "RetractionNature": "Expression of Concern",
        "RetractionDate": "2022-01-01",
        "RetractionDOI": "10.1/rw-eoc",
    },
]


def test_build_rw_index_distinguishes_retractions_from_concerns():
    idx = build_rw_index(RW_ROWS)

    assert idx["10.1/retracted"]["retracted"] is True
    assert idx["10.1/concern"]["retracted"] is False


def test_rw_lookup_loads_csv_case_insensitively_and_handles_missing_data(tmp_path):
    p = tmp_path / "rw.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["OriginalPaperDOI", "RetractionNature", "RetractionDate", "RetractionDOI"],
        )
        w.writeheader()
        w.writerows(RW_ROWS)

    _m._RW_INDEX = None
    hit = rw_lookup("10.1/RETRACTED", p)
    _m._RW_INDEX = None
    miss = rw_lookup("10.1/unknown", p)
    _m._RW_INDEX = None
    absent = rw_lookup("10.1/x", tmp_path / "nope.csv")
    _m._RW_INDEX = None

    assert hit and hit["retracted"] is True and hit["date"] == "2021-05-03"
    assert miss is not None and miss["retracted"] is False
    assert absent is None


def test_crossref_retraction_reads_update_to_relation_and_clean_records():
    update_to = {
        "update-to": [
            {"type": "retraction", "DOI": "10.1/cr", "updated": {"date-parts": [[2021, 5, 3]]}}
        ]
    }
    relation = {"relation": {"is-retracted-by": [{"id-type": "doi", "id": "10.1/rb"}]}}

    assert crossref_retraction(update_to)["retracted"] is True
    assert crossref_retraction(update_to)["date"] == "2021-05-03"
    assert crossref_retraction(relation)["via"] == "relation"
    assert crossref_retraction({"title": ["Fine"]})["retracted"] is False


def test_open_retractions_verdict_maps_http_statuses():
    assert open_retractions_verdict(404, None)["retracted"] is False
    assert (
        open_retractions_verdict(200, {"retracted": True, "retractions": [{"date": "2020-01-01"}]})[
            "retracted"
        ]
        is True
    )
    assert open_retractions_verdict(0, None)["retracted"] is None


def test_combine_reports_agreement_disagreement_and_missing_data():
    all_clean = combine(
        "10.1/x",
        {
            "retraction_watch": {"retracted": False},
            "crossref": {"retracted": False},
            "open_retractions": {"retracted": False},
        },
        {},
    )
    rw_only_disagrees = combine(
        "10.1/x",
        {
            "retraction_watch": {"retracted": True, "retraction_doi": "10.1/rw"},
            "crossref": {"retracted": False},
            "open_retractions": {"retracted": False},
        },
        {},
    )
    all_retracted = combine(
        "10.1/x",
        {
            "retraction_watch": {"retracted": True},
            "crossref": {"retracted": True},
            "open_retractions": {"retracted": True},
        },
        {},
    )
    no_data = combine(
        "10.1/x", {"retraction_watch": None, "crossref": None, "open_retractions": None}, {}
    )
    single_clean = combine(
        "10.1/x",
        {"retraction_watch": {"retracted": False}, "crossref": None, "open_retractions": None},
        {},
    )

    assert all_clean["retracted"] is False and all_clean["agreement"] == "agree"
    assert rw_only_disagrees["retracted"] is True
    assert rw_only_disagrees["agreement"] == "disagree"
    assert rw_only_disagrees["retraction_doi"] == "10.1/rw"
    assert all_retracted["retracted"] is True and all_retracted["agreement"] == "agree"
    assert no_data["retracted"] is None and no_data["agreement"] == "no-data"
    assert single_clean["retracted"] is False and single_clean["agreement"] == "single-source"
