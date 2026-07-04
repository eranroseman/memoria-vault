"""L1 component tests for the classify stage (D21/ADR-54).

Classification is AUTOMATED in the ingest path, AUDITED (one JSONL line per
decision in system/logs/classify.jsonl), and never a gate: a clear winner
applies silently, genuine ambiguity leaves the field unset and requests ONE
Inbox flag. Offline: enrichment is stubbed with fixture payloads — no network.
"""

import json

from ingest_fixtures import BIB
from ingest_fixtures import merged_record as _merged
from ingest_fixtures import run_enriched_pipeline as _run_pipeline
from ingest_fixtures import topic as _topic

from memoria_vault.runtime.subsystems.processing.ingest import classify, runner


def _audit_lines(vault):
    log = vault / "system" / "logs" / "classify.jsonl"
    if not log.is_file():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]


def _write_vocabulary(vault):
    (vault / "system").mkdir(parents=True, exist_ok=True)
    (vault / "system/vocabulary.md").write_text(
        "# Vocabulary\n\n"
        "## research_area\n\n"
        "- mobile-health — Mobile health.\n\n"
        "## methodology\n\n"
        "- review — Review.\n"
        "- meta-analysis — Meta-analysis.\n\n"
        "## topics\n",
        encoding="utf-8",
    )


def test_candidates_roll_up_to_subfield_best_score():
    m = _merged(
        [
            _topic("mHealth Apps", 0.97, "Health Informatics"),
            _topic("Telemonitoring", 0.91, "Health Informatics"),
            _topic("HCI Theory", 0.40, "Human-Computer Interaction"),
        ]
    )
    cands = classify.candidates(m)
    assert cands[0] == ("Health Informatics", 0.97)  # max, not double-counted
    assert len(cands) == 2


def test_below_floor_is_ambiguous():
    d = classify.decide(_merged([_topic("T", 0.30, "Area A")]), floor=0.6, margin=0.15)
    assert d["status"] == "ambiguous" and d["research_area"] == []
    assert "floor" in d["reason"]


def test_methodology_facet_from_publication_types():
    d = classify.decide(
        _merged(
            [_topic("T", 0.95, "Area A")],
            publication_types=["JournalArticle", "Review", "MetaAnalysis"],
        )
    )
    assert d["methodology"] == ["review", "meta-analysis"]  # venue-ish types unmapped


def test_flag_payload_is_honest_no_verdict():
    d = classify.decide(_merged([_topic("T1", 0.80, "Area A"), _topic("T2", 0.78, "Area B")]))
    f = classify.flag_payload("x2024Test", d)
    assert f["citekey"] == "x2024Test"
    assert "Area A (0.80)" in f["finding"] and "Area B (0.78)" in f["finding"]
    assert "left unset" in f["finding"]  # what was ambiguous, no verdict


def test_clear_winner_applies_and_audits(monkeypatch, tmp_path):
    _write_vocabulary(tmp_path)
    m = _merged(
        [
            _topic("mHealth Apps", 0.97, "mobile-health"),
            _topic("HCI Theory", 0.40, "Human-Computer Interaction"),
        ],
        publication_types=["Review"],
    )
    b = _run_pipeline(monkeypatch, tmp_path, m)
    fm = b["frontmatter"]
    assert fm["research_area"] == ["mobile-health"]
    assert fm["methodology"] == ["review"]
    assert b["classify"]["status"] == "applied"
    assert "classify_flag_needed" not in b
    lines = _audit_lines(tmp_path)
    assert len(lines) == 1
    rec = lines[0]
    assert rec["decision"] == "applied" and rec["citekey"] == "x2024Test"
    assert rec["research_area"] == ["mobile-health"]
    assert rec["candidates"][0]["name"] == "mobile-health"
    assert rec["confidence_floor"] == 0.6 and rec["near_tie_margin"] == 0.15
    assert rec["source"] == "openalex.topics"
    assert rec["timestamp"].endswith("Z") and rec["run_id"]


def test_off_vocabulary_winner_flags_and_leaves_unset(monkeypatch, tmp_path):
    _write_vocabulary(tmp_path)
    m = _merged([_topic("mHealth Apps", 0.97, "Health Informatics")], publication_types=["Review"])

    b = _run_pipeline(monkeypatch, tmp_path, m)

    assert b["frontmatter"]["research_area"] == []
    assert b["frontmatter"]["methodology"] == ["review"]
    assert b["classify"]["status"] == "ambiguous"
    assert "outside the research_area vocabulary" in b["classify"]["reason"]
    assert "outside the research_area vocabulary" in b["classify_flag_needed"]["finding"]
    assert _audit_lines(tmp_path)[0]["miss_kind"] == "off_vocabulary"


def test_near_tie_flags_audits_and_leaves_unset(monkeypatch, tmp_path):
    m = _merged([_topic("T1", 0.90, "Area A"), _topic("T2", 0.85, "Area B")])
    b = _run_pipeline(monkeypatch, tmp_path, m)
    assert b["frontmatter"]["research_area"] == []  # left unset
    assert b["classify"]["status"] == "ambiguous"
    flag = b["classify_flag_needed"]  # ONE flag request
    assert flag["title"] == "Ambiguous classification for x2024Test"
    assert "near-tie" in flag["finding"]
    lines = _audit_lines(tmp_path)
    assert len(lines) == 1 and lines[0]["decision"] == "ambiguous"
    assert lines[0]["research_area"] == []
    assert lines[0]["classify_miss"] is True
    assert lines[0]["miss_kind"] == "near_tie"


def test_calibration_thresholds_read_from_vault(tmp_path):
    schemas = tmp_path / ".memoria" / "schemas"
    schemas.mkdir(parents=True)
    (schemas / "calibration.yaml").write_text(
        "classify:\n  confidence_floor: 0.9\n  near_tie_margin: 0.05\n", encoding="utf-8"
    )
    assert classify.thresholds(tmp_path) == (0.9, 0.05)
    assert classify.thresholds(None) == (classify.DEFAULT_FLOOR, classify.DEFAULT_MARGIN)


def test_no_topic_data_is_a_noop(monkeypatch, tmp_path):
    b = _run_pipeline(monkeypatch, tmp_path, _merged([]))
    assert b["frontmatter"]["research_area"] == []
    assert b["classify"]["status"] == "no_data"
    assert "classify_flag_needed" not in b
    assert _audit_lines(tmp_path) == []  # a no-op is not a decision


def test_no_enrichment_no_op(tmp_path):
    b = runner.run("x2024Test", BIB, tmp_path, enrich=False)
    assert "classify" not in b  # classify never ran
    assert b["frontmatter"]["research_area"] == []
    assert _audit_lines(tmp_path) == []
