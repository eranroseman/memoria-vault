"""L1 component tests for retraction."""

import datetime

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.attention import lifecycle
from memoria_vault.runtime.capture import capture_source as _capture_source
from memoria_vault.runtime.sweeps.retraction import retraction as _m
from memoria_vault.runtime.vaultio import (
    frontmatter_doc,
    read_frontmatter,
    split_frontmatter,
)
from tests.helpers import call_with_context, copy_memoria_dirs, init_git

pytestmark = pytest.mark.contract

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


FINGERPRINT = "retraction:10.1/retracted"
SECOND_FINGERPRINT = "retraction:10.1/retracted2"
SECOND_RETRACTED_ROW = {
    "OriginalPaperDOI": "10.1/Retracted2",
    "RetractionNature": "Retraction",
    "RetractionDate": "2023-03-03",
    "RetractionDOI": "10.1/rw-ret2",
}


def _retraction_vault(tmp_path, monkeypatch):
    """One checked SQLite Work whose DOI the Retraction Watch fixture retracts."""
    vault = capture_workspace(tmp_path)
    state.upsert_catalog_record(
        vault,
        work_id="smith2020",
        title="Retracted Cited Work",
        doi="10.1/Retracted",
        identifiers={},
        citekey="smith2020",
        csl_json={"title": "Retracted Cited Work"},
        check_status="checked",
    )
    rw_csv = tmp_path / "rw.csv"
    with rw_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["OriginalPaperDOI", "RetractionNature", "RetractionDate", "RetractionDOI"],
        )
        w.writeheader()
        w.writerows([*RW_ROWS, SECOND_RETRACTED_ROW])
    monkeypatch.setenv("MEMORIA_RW_CSV", str(rw_csv))
    _m._RW_INDEX = None
    return vault


def _second_retracted_source(vault) -> None:
    state.upsert_catalog_record(
        vault,
        work_id="jones2021",
        title="Second Retracted Work",
        doi="10.1/Retracted2",
        identifiers={},
        citekey="jones2021",
        csl_json={"title": "Second Retracted Work"},
        check_status="checked",
    )


def _today() -> str:
    return datetime.date.today().isoformat()


def _alerts(vault) -> list:
    return sorted((vault / "inbox").glob("alert-*.md"))


def _edit(path, **fields) -> None:
    """Rewrite a card's frontmatter the way the PI's editor does: no operation, no journal."""
    frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
    frontmatter.update(fields)
    path.write_text(frontmatter_doc(frontmatter, body), encoding="utf-8")


def _attention_chain(vault, rel: str) -> list:
    """Return `(event, outcome)` for one `inbox/` path's whole journaled life, in order."""
    return [
        (str(event.get("event")), event.get("outcome"))
        for event in state.read_event_log(
            vault, event_types=("resolved", lifecycle.EVENT_ATTENTION_ARCHIVED)
        )
        if event.get("source") == "attention" and event.get("target_id") == rel
    ]


def test_sweep_keeps_one_standing_alert_per_retracted_doi(tmp_path, monkeypatch):
    """The sweep loops over sources, so the dedupe has to be per condition, not per run.

    With one retracted source every wrong answer looks the same. With two, a scan that
    matched any open attention card -- or a producer that fingerprinted the sweep
    rather than the DOI -- collapses the pair into one card and loses an alert
    permanently, which is the one failure mode worse than the duplication being fixed.
    """
    vault = _retraction_vault(tmp_path, monkeypatch)
    _second_retracted_source(vault)
    try:
        first = sweep(vault, offline=True)
        after_first = _alerts(vault)
        for card in after_first:
            _edit(card, last_seen="2020-01-01")

        second = sweep(vault, offline=True)
        after_second = _alerts(vault)
        fingerprints = sorted(read_frontmatter(card)["fingerprint"] for card in after_second)
        seen = {read_frontmatter(card)["last_seen"] for card in after_second}

        assert first == {"checked": 2, "retracted": 2}
        assert len(after_first) == 2
        assert second == {"checked": 2, "retracted": 2}
        assert after_second == after_first  # each DOI kept its own standing card
        assert fingerprints == [FINGERPRINT, SECOND_FINGERPRINT]
        assert seen == {_today()}  # both touched; neither absorbed the other
    finally:
        _m._RW_INDEX = None


def test_sweep_touches_a_standing_alert_and_reraises_once_the_pi_resolves_it(tmp_path, monkeypatch):
    """The first three states of the card's life, sampled one sweep at a time.

    Open, re-observed, and resolved-but-still-in-`inbox/`. The third is the one an
    existence dedupe gets wrong and the one the defect lives in: before this change
    every sweep left another copy of the same standing alert, and after a naive fix
    no sweep would ever raise it again.
    """
    vault = _retraction_vault(tmp_path, monkeypatch)
    try:
        first = sweep(vault, offline=True)
        [standing] = _alerts(vault)
        opened = read_frontmatter(standing)

        _edit(standing, last_seen="2020-01-01")
        second = sweep(vault, offline=True)
        after_second = _alerts(vault)
        reobserved = read_frontmatter(standing)

        _edit(standing, attention_status="resolved", last_seen="2020-01-01")
        third = sweep(vault, offline=True)
        after_third = _alerts(vault)
        resolved = read_frontmatter(standing)

        assert first == {"checked": 1, "retracted": 1}
        assert opened["fingerprint"] == FINGERPRINT  # the sweep normalizes the DOI itself
        assert opened["attention_status"] == "open"
        assert opened["last_seen"] == _today()

        assert second == {"checked": 1, "retracted": 1}
        assert after_second == [standing]  # touched in place, not duplicated
        assert reobserved["last_seen"] == _today()
        assert reobserved["created"] == opened["created"]
        assert reobserved["attention_status"] == "open"

        assert third == {"checked": 1, "retracted": 1}
        assert len(after_third) == 2  # the recurrence re-raises past the PI's resolution
        [reraised] = [card for card in after_third if card != standing]
        assert read_frontmatter(reraised)["attention_status"] == "open"
        assert read_frontmatter(reraised)["fingerprint"] == FINGERPRINT
        # the resolved card is left exactly as the PI left it -- only compaction may
        # touch it, because only compaction journals what it does to it
        assert resolved["last_seen"] == "2020-01-01"
    finally:
        _m._RW_INDEX = None


def test_sweep_reraises_onto_the_archived_cards_freed_path_and_the_journal_records_both(
    tmp_path, monkeypatch
):
    """The rest of the life: archived, re-raised onto the freed name, standing again, closed.

    An `inbox/` filename is reusable now, so the re-raised card lands on the archived
    card's exact path -- and the journal has to read that as a second card with its own
    decision, not as one already disposed of. The two hand-closes carry different
    outcomes so a run that journals the first card twice cannot produce this chain.
    """
    vault = _retraction_vault(tmp_path, monkeypatch)
    try:
        sweep(vault, offline=True)
        [first] = _alerts(vault)
        rel = first.relative_to(vault).as_posix()

        _edit(first, attention_status="resolved", resolution_outcome="reject")
        compacted = lifecycle.compact_resolved_cards(vault, machine="test-machine")
        after_archive = _alerts(vault)
        digest = (vault / compacted["digests"][0]).read_text(encoding="utf-8")

        third = sweep(vault, offline=True)
        [reraised] = _alerts(vault)
        fresh = read_frontmatter(reraised)

        _edit(reraised, last_seen="2020-01-01")
        fourth = sweep(vault, offline=True)
        after_fourth = _alerts(vault)
        standing_again = read_frontmatter(reraised)

        _edit(reraised, attention_status="resolved", resolution_outcome="apply")
        again = lifecycle.compact_resolved_cards(vault, machine="test-machine")

        assert compacted["archived"] == [rel]
        assert after_archive == []
        # after archival the fingerprint survives only in the digest, which carries no
        # frontmatter and lives below a directory no `inbox/` reader descends into
        assert f"- fingerprint: {FINGERPRINT}" in digest

        assert third == {"checked": 1, "retracted": 1}
        assert reraised == first  # the collision loop took the freed name back
        assert fresh["attention_status"] == "open"
        assert fresh["fingerprint"] == FINGERPRINT
        assert fresh["created"] == _today()

        assert fourth == {"checked": 1, "retracted": 1}
        assert after_fourth == [reraised]  # standing again: touched, not duplicated
        assert standing_again["last_seen"] == _today()

        assert again["archived"] == [rel]
        assert _attention_chain(vault, rel) == [
            ("resolved", "reject"),
            (lifecycle.EVENT_ATTENTION_ARCHIVED, None),
            ("resolved", "apply"),
            (lifecycle.EVENT_ATTENTION_ARCHIVED, None),
        ]
    finally:
        _m._RW_INDEX = None


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
