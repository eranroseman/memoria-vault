"""L1 component tests for the ADR-15 project-membership proposal.

When an optional `.memoria/project-hints.yaml` exists, the classify step scores
each project's `primary_topics` against the paper's OpenAlex topic signals by
simple overlap and PROPOSES the matching project(s) in
`_proposed_classification.projects` — human-confirmed at triage, never applied
to the `projects` frontmatter field. Absent file = silent no-op; malformed
file = warn-once + manual (the pipeline never crashes). Offline: enrichment is
stubbed with fixture payloads — no network.
"""

import json

import classify
import pipeline

# --------------------------------------------------------------------------- #
# fixtures (the test_classify.py shapes)
# --------------------------------------------------------------------------- #
BIB = ("@article{x2024Test,\n  title = {A Test},\n  author = {Doe, Jane},\n"
       "  year = {2024},\n  doi = {10.1/x},\n  journal = {J Tests},\n}\n")

HINTS_YAML = """\
projects:
  - id: phd-dissertation
    description: HCI + digital health.
    primary_topics: [jitai, health-coaching, mhealth]
  - id: scoping-review
    description: Scoping review.
    primary_topics: [mhealth]
"""


def _merged(topics_scored, publication_types=()):
    """A minimal resolve_merge-shaped merged record."""
    return {
        "title": "A Test", "year": 2024, "venue": "J Tests", "issn": "",
        "s2_id": "S2X", "openalex_id": "W1", "pmid": "", "pmcid": "",
        "authors": [{"name": "Jane Doe"}], "tldr": "", "fields_of_study": [],
        "topics": [t["name"] for t in topics_scored],
        "topics_scored": topics_scored,
        "publication_types": list(publication_types),
        "references": [], "citation_count": 1,
        "provenance": {"title": "openalex"},
        "agreement": {"score": 1.0, "disagreements": []},
    }


def _topic(name, score, subfield=""):
    return {"name": name, "score": score, "subfield": subfield,
            "field": "F", "domain": "D"}


def _run_pipeline(monkeypatch, vault, merged):
    """Run the enriched pipeline offline: stub the network stages."""
    monkeypatch.setattr(pipeline.resolve_merge, "resolve", lambda ck, bib: {
        "citekey": ck, "ids": {}, "merged": merged,
        "parts": {"s2": {"found": True}, "openalex": {"found": True},
                  "crossref": {"found": False}}})
    monkeypatch.setattr(pipeline.extract, "extract", lambda ids, pdf, email, api_key="": {
        "source": "none", "chars": 0, "degraded": True, "text": ""})
    return pipeline.run("x2024Test", BIB, vault, enrich=True)


def _write_hints(vault, text=HINTS_YAML):
    d = vault / ".memoria"
    d.mkdir(parents=True, exist_ok=True)
    (d / "project-hints.yaml").write_text(text, encoding="utf-8")


def _audit_lines(vault, stage=None):
    log = vault / "system" / "logs" / "classify.jsonl"
    if not log.is_file():
        return []
    lines = [json.loads(line) for line in
             log.read_text(encoding="utf-8").splitlines()]
    return [r for r in lines if stage is None or r["stage"] == stage]


MHEALTH_TOPICS = [_topic("mHealth Apps", 0.97, "Health Informatics"),
                  _topic("Health Coaching", 0.55, "Health Informatics")]


# --------------------------------------------------------------------------- #
# load_project_hints() — absent silent, malformed loud-but-safe
# --------------------------------------------------------------------------- #
def test_absent_hints_file_loads_empty_and_silent(tmp_path, capsys):
    assert classify.load_project_hints(tmp_path) == []
    assert classify.load_project_hints(None) == []
    assert capsys.readouterr().err == ""       # absent is the opt-out, no warning


def test_valid_hints_load(tmp_path):
    _write_hints(tmp_path)
    hints = classify.load_project_hints(tmp_path)
    assert [p["id"] for p in hints] == ["phd-dissertation", "scoping-review"]
    assert hints[0]["primary_topics"] == ["jitai", "health-coaching", "mhealth"]


def test_malformed_hints_warn_once_and_load_empty(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(classify, "_warned_hints", False)
    _write_hints(tmp_path, "projects: [this is not: a project list\n")
    assert classify.load_project_hints(tmp_path) == []
    assert classify.load_project_hints(tmp_path) == []     # second call: quiet
    err = capsys.readouterr().err
    assert err.count("WARNING") == 1 and "project-hints.yaml" in err


def test_entries_missing_id_or_topics_are_dropped(tmp_path, monkeypatch):
    monkeypatch.setattr(classify, "_warned_hints", False)
    _write_hints(tmp_path, "projects:\n"
                           "  - id: ok\n    primary_topics: [mhealth]\n"
                           "  - id: no-topics\n    primary_topics: []\n"
                           "  - description: no id\n")
    # an entry without primary_topics is dropped; one without `id` raises
    # KeyError inside the loader -> the whole file degrades to [] (warn-once)
    assert classify.load_project_hints(tmp_path) == []


# --------------------------------------------------------------------------- #
# propose_projects() — the pure overlap rule
# --------------------------------------------------------------------------- #
def test_overlap_scores_and_ranks_projects():
    hints = [
        {"id": "phd-dissertation",
         "primary_topics": ["jitai", "health-coaching", "mhealth"]},
        {"id": "scoping-review", "primary_topics": ["mhealth"]},
        {"id": "unrelated", "primary_topics": ["quantum-computing"]},
    ]
    pp = classify.propose_projects(_merged(MHEALTH_TOPICS), hints)
    assert pp["status"] == "proposed"
    # phd-dissertation overlaps 2 hint topics, scoping-review 1, unrelated 0
    assert pp["projects"] == ["phd-dissertation", "scoping-review"]
    assert pp["candidates"][0] == {"id": "phd-dissertation", "score": 2,
                                   "matched": ["health-coaching", "mhealth"]}
    assert pp["candidates"][1]["score"] == 1
    assert "phd-dissertation (2" in pp["reason"]


def test_matching_normalizes_case_and_kebab():
    # hint "mhealth" matches topic "mHealth Apps" (token subset after kebab);
    # hint "Health Coaching" (spaces, caps) matches subfield-less exact topic
    hints = [{"id": "p", "primary_topics": ["MHEALTH", "Health Coaching"]}]
    pp = classify.propose_projects(_merged(MHEALTH_TOPICS), hints)
    assert pp["status"] == "proposed"
    assert pp["candidates"][0]["score"] == 2


def test_zero_overlap_is_no_match():
    hints = [{"id": "p", "primary_topics": ["quantum-computing"]}]
    pp = classify.propose_projects(_merged(MHEALTH_TOPICS), hints)
    assert pp["status"] == "no_match" and pp["projects"] == []


def test_no_topic_signals_is_no_data():
    hints = [{"id": "p", "primary_topics": ["mhealth"]}]
    pp = classify.propose_projects(_merged([]), hints)
    assert pp["status"] == "no_data" and pp["projects"] == []


# --------------------------------------------------------------------------- #
# the pipeline integration — proposal only, audited, never crashes
# --------------------------------------------------------------------------- #
def test_proposal_lands_in_proposed_classification_not_projects(monkeypatch, tmp_path):
    _write_hints(tmp_path)
    b = _run_pipeline(monkeypatch, tmp_path, _merged(MHEALTH_TOPICS))
    fm = b["frontmatter"]
    assert fm["_proposed_classification"]["projects"] == \
        ["phd-dissertation", "scoping-review"]
    assert "projects" not in fm                # PROPOSED, never auto-applied
    assert b["project_proposal"]["status"] == "proposed"
    rec, = _audit_lines(tmp_path, stage="project_hints")
    assert rec["decision"] == "proposed" and rec["citekey"] == "x2024Test"
    assert rec["projects_proposed"] == ["phd-dissertation", "scoping-review"]
    assert rec["candidates"][0]["matched"] == ["health-coaching", "mhealth"]
    assert rec["source"] == "project-hints.yaml x openalex.topics"
    assert rec["timestamp"].endswith("Z") and rec["run_id"]


def test_absent_hints_file_is_a_noop(monkeypatch, tmp_path):
    b = _run_pipeline(monkeypatch, tmp_path, _merged(MHEALTH_TOPICS))
    assert b["frontmatter"]["_proposed_classification"]["projects"] == []
    assert "project_proposal" not in b
    assert _audit_lines(tmp_path, stage="project_hints") == []


def test_no_match_is_audited(monkeypatch, tmp_path):
    _write_hints(tmp_path, "projects:\n  - id: p\n"
                           "    primary_topics: [quantum-computing]\n")
    b = _run_pipeline(monkeypatch, tmp_path, _merged(MHEALTH_TOPICS))
    assert b["frontmatter"]["_proposed_classification"]["projects"] == []
    assert b["project_proposal"]["status"] == "no_match"
    rec, = _audit_lines(tmp_path, stage="project_hints")
    assert rec["decision"] == "no_match" and rec["projects_proposed"] == []


def test_malformed_hints_do_not_crash_the_pipeline(monkeypatch, tmp_path):
    monkeypatch.setattr(classify, "_warned_hints", False)
    _write_hints(tmp_path, "projects: {broken: [yaml\n")
    b = _run_pipeline(monkeypatch, tmp_path, _merged(MHEALTH_TOPICS))
    assert b["frontmatter"]["_proposed_classification"]["projects"] == []
    assert "project_proposal" not in b         # degraded to manual
    assert _audit_lines(tmp_path, stage="project_hints") == []


def test_shipped_example_parses_when_copied_into_place(tmp_path):
    from pathlib import Path
    example = (Path(__file__).resolve().parent.parent
               / "src" / ".memoria" / "project-hints.yaml.example")
    _write_hints(tmp_path, example.read_text(encoding="utf-8"))
    hints = classify.load_project_hints(tmp_path)
    assert [p["id"] for p in hints] == ["phd-dissertation", "scoping-review"]
