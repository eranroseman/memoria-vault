"""L1 component tests for retraction."""

from memoria_vault.runtime.subsystems.integrity.retraction import retraction as _m

Path = _m.Path
build_rw_index = _m.build_rw_index
check_doi = _m.check_doi
combine = _m.combine
crossref_retraction = _m.crossref_retraction
csv = _m.csv
open_retractions_verdict = _m.open_retractions_verdict
read_frontmatter = _m.read_frontmatter
rw_lookup = _m.rw_lookup
sweep = _m.sweep

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


def test_build_rw_index_severity_tie_break_keeps_retraction_over_concern():
    rows = [
        {
            "OriginalPaperDOI": "10.1/Twice",
            "RetractionNature": "Expression of Concern",
            "RetractionDate": "2020-02-02",
            "RetractionDOI": "10.1/rw-eoc2",
        },
        {
            "OriginalPaperDOI": "10.1/Twice",
            "RetractionNature": "Retraction",
            "RetractionDate": "2021-05-03",
            "RetractionDOI": "10.1/rw-ret2",
        },
    ]

    idx = build_rw_index(rows)
    idx_reversed = build_rw_index(list(reversed(rows)))

    assert idx["10.1/twice"]["retracted"] is True
    assert idx["10.1/twice"]["nature"] == "Retraction"
    assert idx["10.1/twice"]["retraction_doi"] == "10.1/rw-ret2"
    assert idx_reversed["10.1/twice"]["retracted"] is True
    assert idx_reversed["10.1/twice"]["nature"] == "Retraction"
    assert idx_reversed["10.1/twice"]["retraction_doi"] == "10.1/rw-ret2"


def test_sweep_flags_a_retracted_cited_source_with_an_inbox_alert(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    retracted_note = vault / "catalog" / "sources" / "smith2020" / "source.md"
    retracted_note.parent.mkdir(parents=True)
    retracted_note.write_text(
        "---\ntype: source\ncitekey: smith2020\ndoi: 10.1/Retracted\n---\nBody.\n",
        encoding="utf-8",
    )
    clean_note = vault / "catalog" / "sources" / "jones2021" / "source.md"
    clean_note.parent.mkdir(parents=True)
    clean_note.write_text(
        "---\ntype: source\ncitekey: jones2021\ndoi: 10.1/Clean\n---\nBody.\n",
        encoding="utf-8",
    )
    rw_csv = tmp_path / "rw.csv"
    with rw_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["OriginalPaperDOI", "RetractionNature", "RetractionDate", "RetractionDOI"],
        )
        w.writeheader()
        w.writerows(RW_ROWS)
    monkeypatch.setenv("MEMORIA_RW_CSV", str(rw_csv))
    _m._RW_INDEX = None
    try:
        result = sweep(vault, offline=True)
    finally:
        _m._RW_INDEX = None

    cards = sorted((vault / "inbox").glob("alert-*.md"))
    assert result == {"checked": 2, "retracted": 1}
    assert len(cards) == 1
    fm = read_frontmatter(cards[0])
    assert fm["attention_kind"] == "alert"
    assert fm["target"] == "catalog/sources/smith2020/source.md"
    assert fm["citekey"] == "smith2020"
    assert fm["raised_by"] == "sweep"
    assert fm["loudness"] == "alert"
    assert "10.1/Retracted is retracted" in str(fm["finding"])


def test_check_doi_offline_warns_once_when_rw_csv_is_missing(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("MEMORIA_RW_CSV", str(tmp_path / "missing.csv"))
    _m._RW_INDEX = None
    _m._warned_no_csv = False
    try:
        first = check_doi("10.1/x", offline=True)
        second = check_doi("10.1/y", offline=True)
    finally:
        _m._RW_INDEX = None
        _m._warned_no_csv = False

    err = capsys.readouterr().err
    assert err.count("Retraction Watch CSV not found") == 1
    assert first["retracted"] is None
    assert "UNKNOWN" in first["note"]
    assert second["retracted"] is None
