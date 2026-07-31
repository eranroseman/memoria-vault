"""L1 component tests for retraction."""

from memoria_vault.runtime import state
from memoria_vault.runtime.capture import capture_source as _capture_source
from memoria_vault.runtime.subsystems.integrity.retraction import retraction as _m
from memoria_vault.runtime.vaultio import read_frontmatter
from tests.helpers import call_with_context, copy_memoria_dirs, init_git

Path = _m.Path
build_rw_index = _m.build_rw_index
check_doi = _m.check_doi
combine = _m.combine
crossref_retraction = _m.crossref_retraction
csv = _m.csv
open_retractions_verdict = _m.open_retractions_verdict
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


def capture_source(vault, *args, **kwargs):
    return call_with_context(_capture_source, vault, *args, **kwargs)


def capture_workspace(tmp_path):
    copy_memoria_dirs(tmp_path, "schemas")
    init_git(tmp_path, "retraction@example.invalid", "Retraction")
    return tmp_path


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


def test_sweep_flags_checked_sqlite_retraction_without_legacy_fallback(tmp_path, monkeypatch):
    vault = capture_workspace(tmp_path)
    retracted = capture_source(
        vault,
        "smith2020",
        "Retracted SQLite Work",
        "A retracted fixture source.",
        "Retracted fixture text.\n",
        raw_bytes=b"retracted fixture bytes",
        raw_filename="smith2020.txt",
        identifiers={"doi": "10.1/Retracted"},
        citekey="smith2020",
        csl_json={"title": "Retracted SQLite Work"},
        machine="retraction-test",
        run_id="capture-retracted",
    )
    clean = capture_source(
        vault,
        "jones2021",
        "Clean SQLite Work",
        "A clean fixture source.",
        "Clean fixture text.\n",
        raw_bytes=b"clean fixture bytes",
        raw_filename="jones2021.txt",
        citekey="jones2021",
        csl_json={"title": "Clean SQLite Work", "DOI": "10.1/Clean"},
        machine="retraction-test",
        run_id="capture-clean",
    )
    for captured in (retracted, clean):
        assert captured["check_status"] == "checked"
        assert (vault / captured["content_path"]).is_file()
        assert (vault / captured["raw_path"]).is_file()
        assert not (vault / captured["source_path"] / "source.md").exists()
    state.upsert_catalog_record(
        vault,
        work_id="unchecked2022",
        title="Unchecked Retracted SQLite Work",
        identifiers={"doi": "10.1/Unchecked"},
        citekey="unchecked2022",
        csl_json={"title": "Unchecked Retracted SQLite Work"},
        check_status="unchecked",
    )
    state.upsert_catalog_record(
        vault,
        work_id="quarantined2023",
        title="Quarantined Retracted SQLite Work",
        identifiers={"doi": "10.1/Quarantined"},
        citekey="quarantined2023",
        csl_json={"title": "Quarantined Retracted SQLite Work"},
        check_status="quarantined",
    )
    retracted_rows = [
        *RW_ROWS,
        {
            "OriginalPaperDOI": "10.1/Unchecked",
            "RetractionNature": "Retraction",
            "RetractionDate": "2021-05-03",
            "RetractionDOI": "10.1/rw-unchecked",
        },
        {
            "OriginalPaperDOI": "10.1/Quarantined",
            "RetractionNature": "Retraction",
            "RetractionDate": "2021-05-03",
            "RetractionDOI": "10.1/rw-quarantined",
        },
    ]
    rw_csv = tmp_path / "rw.csv"
    with rw_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["OriginalPaperDOI", "RetractionNature", "RetractionDate", "RetractionDOI"],
        )
        w.writeheader()
        w.writerows(retracted_rows)
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
    assert fm["title"] == "Retraction: Retracted SQLite Work"
    assert fm["target"] == "catalog/sources/smith2020"
    assert fm["citekey"] == "smith2020"
    assert fm["raised_by"] == "sweep"
    assert fm["loudness"] == "alert"
    assert "10.1/Retracted is retracted" in str(fm["finding"])


def test_sweep_checks_canonical_doi_column_and_alerts_on_retraction(tmp_path, monkeypatch):
    vault = capture_workspace(tmp_path)
    state.upsert_catalog_record(
        vault,
        work_id="column-doi-work",
        title="Canonical DOI Column Work",
        doi="10.1/ColumnOnly",
        identifiers={},
        csl_json={"title": "Canonical DOI Column Work"},
        check_status="checked",
    )
    rw_csv = tmp_path / "rw.csv"
    with rw_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["OriginalPaperDOI", "RetractionNature", "RetractionDate", "RetractionDOI"],
        )
        w.writeheader()
        w.writerow(
            {
                "OriginalPaperDOI": "10.1/ColumnOnly",
                "RetractionNature": "Retraction",
                "RetractionDate": "2021-05-03",
                "RetractionDOI": "10.1/rw-column-only",
            }
        )
    monkeypatch.setenv("MEMORIA_RW_CSV", str(rw_csv))
    _m._RW_INDEX = None
    try:
        result = sweep(vault, offline=True)
    finally:
        _m._RW_INDEX = None

    cards = list((vault / "inbox").glob("alert-*.md"))
    assert result == {"checked": 1, "retracted": 1}
    assert len(cards) == 1
    fm = read_frontmatter(cards[0])
    assert fm["title"] == "Retraction: Canonical DOI Column Work"
    assert "10.1/ColumnOnly is retracted" in str(fm["finding"])


def test_sweep_does_not_read_legacy_doi_fields(tmp_path, monkeypatch):
    vault = capture_workspace(tmp_path)
    state.upsert_catalog_record(
        vault,
        work_id="legacy-doi-work",
        title="Legacy DOI Work",
        identifiers={"doi": "10.1/LegacyOnly"},
        csl_json={"title": "Legacy DOI Work", "DOI": "10.1/LegacyOnly"},
        check_status="checked",
    )
    with state.connect(vault) as conn:
        conn.execute(
            "UPDATE catalog_sources SET doi = NULL WHERE work_id = ?", ("legacy-doi-work",)
        )
    rw_csv = tmp_path / "rw.csv"
    with rw_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["OriginalPaperDOI", "RetractionNature", "RetractionDate", "RetractionDOI"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "OriginalPaperDOI": "10.1/LegacyOnly",
                "RetractionNature": "Retraction",
                "RetractionDate": "2021-05-03",
                "RetractionDOI": "10.1/rw-legacy-only",
            }
        )
    monkeypatch.setenv("MEMORIA_RW_CSV", str(rw_csv))
    _m._RW_INDEX = None
    try:
        result = sweep(vault, offline=True)
    finally:
        _m._RW_INDEX = None

    assert result == {"checked": 0, "retracted": 0}
    assert list((vault / "inbox").glob("alert-*.md")) == []


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
