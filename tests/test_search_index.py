from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.search_index import (
    _bm25,
    _tokens,
    answer_query,
    checked_concepts,
    evaluate_bm25,
    filter_checked_results,
    rebuild_checked_qmd_source,
)
from tests.helpers import copy_memoria_dirs


def workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas")
    return tmp_path


def note(
    vault: Path,
    name: str,
    status: str,
    body: str,
    extra: str = "",
    *,
    db_status: str | None = "",
) -> Path:
    path = vault / "knowledge" / "notes" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\ntype: note\ncheck_status: {status}\ntitle: {name}\n{extra}---\n{body}\n",
        encoding="utf-8",
    )
    if db_status is not None:
        set_db_status(vault, path, "note", "unchecked")
        if db_status or status != "unchecked":
            state.set_concept_verdict(
                vault, path.relative_to(vault).as_posix(), db_status or status
            )
    return path


def set_db_status(vault: Path, path: Path, concept_type: str, status: str) -> None:
    state.record_observed_file_edit(
        vault,
        output_id=path.relative_to(vault).as_posix(),
        concept_type=concept_type,
        output_sha256=sha256_file(path),
    )
    state.set_concept_verdict(vault, path.relative_to(vault).as_posix(), status)


def mark_note_candidate(vault: Path, path: Path) -> None:
    state.append_journal_event(
        vault,
        {
            "event": "derived",
            "operation": "propose-note-candidates",
            "output_id": path.relative_to(vault).as_posix(),
        },
    )


def test_rebuild_checked_qmd_source_copies_only_checked_concepts(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    note(vault, "checked", "checked", "alpha beta")
    note(vault, "unchecked", "unchecked", "poison alpha")
    note(vault, "quarantined", "quarantined", "poison beta")
    note(vault, "forged", "checked", "forged alpha", db_status=None)
    candidate = note(vault, "candidate", "checked", "candidate alpha")
    stale = note(vault, "superseded", "checked", "stale alpha")
    mark_note_candidate(vault, candidate)
    state.set_concept_flag(
        vault, stale.relative_to(vault).as_posix(), "stale", reason="test", trigger_id="test"
    )
    capability = vault / "capabilities/operations/checked-operation.md"
    capability.parent.mkdir(parents=True)
    capability.write_text(
        "---\n"
        "type: operation\n"
        "check_status: checked\n"
        "title: Checked operation\n"
        "description: Not Ask content.\n"
        "---\n"
        "alpha operation\n",
        encoding="utf-8",
    )

    manifest = rebuild_checked_qmd_source(vault)

    assert manifest["mode"] == "bm25"
    assert manifest["embeddings"] is False
    assert [row["path"] for row in manifest["documents"]] == [
        "knowledge/notes/checked.md",
        "knowledge/notes/superseded.md",
    ]
    assert (vault / ".memoria/index/qmd/checked/knowledge/notes/checked.md").is_file()
    assert (vault / ".memoria/index/qmd/checked/knowledge/notes/superseded.md").is_file()
    assert not (vault / ".memoria/index/qmd/checked/capabilities").exists()
    assert not (vault / ".memoria/index/qmd/checked/knowledge/notes/candidate.md").exists()
    assert not (vault / ".memoria/index/qmd/checked/knowledge/notes/unchecked.md").exists()
    assert not (vault / ".memoria/index/qmd/checked/knowledge/notes/quarantined.md").exists()
    assert not (vault / ".memoria/index/qmd/checked/knowledge/notes/forged.md").exists()
    assert manifest["qmd_commands"][-1] == "qmd update"


def test_checked_search_refuses_tampered_checked_file_and_enqueues_scan(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    path = note(vault, "checked", "checked", "alpha beta")
    rel = path.relative_to(vault).as_posix()
    path.write_text(
        "---\ntype: note\ncheck_status: checked\ntitle: checked\n---\ntampered alpha\n",
        encoding="utf-8",
    )

    assert checked_concepts(vault) == []
    assert answer_query(vault, "tampered alpha")["sources"] == []
    assert state.concept_check_status(vault, rel) == "checked"
    with state.connect(vault) as conn:
        row = conn.execute(
            """
            SELECT operation_id, status, schedule_id, args_json
            FROM operation_requests
            WHERE operation_id = 'observe-pi-edits'
            """
        ).fetchone()
    assert row is not None
    assert row["operation_id"] == "observe-pi-edits"
    assert row["status"] == "pending"
    assert row["schedule_id"] == "read-guard"
    assert json.loads(row["args_json"])["target_path"] == rel


def test_rebuild_checked_qmd_source_records_embedding_mode(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    note(vault, "checked", "checked", "alpha beta")

    manifest = rebuild_checked_qmd_source(vault, embeddings=True)

    assert manifest["mode"] == "hybrid"
    assert manifest["embeddings"] is True
    assert manifest["qmd_commands"][-1] == "qmd embed --chunk-strategy auto"
    stored = vault / ".memoria/index/qmd/manifest.json"
    assert '"mode": "hybrid"' in stored.read_text(encoding="utf-8")


def test_rebuild_checked_qmd_source_includes_checked_work_text_and_graph(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    note(vault, "checked", "checked", "alpha context without graph target")
    content = vault / ".memoria/blobs/source-content/source-alpha/full-text/alpha.txt"
    content.parent.mkdir(parents=True)
    content.write_text("full text rarealpha retrieval token", encoding="utf-8")
    state.upsert_catalog_record(
        vault,
        source_id="source-alpha",
        title="Alpha Work",
        doi="10.1000/alpha",
        identifiers={"doi": "10.1000/alpha"},
        citekey="alpha2026",
        csl_json={"id": "alpha2026", "title": "Alpha Work", "DOI": "10.1000/alpha"},
        provider_coverage="full",
        text_status="full-text",
        check_status="checked",
        content_path=content.relative_to(vault).as_posix(),
    )
    state.replace_work_graph_edges(
        vault,
        "source-alpha",
        [
            {
                "relation_type": "references",
                "target_id": "https://openalex.org/W999",
                "target_title": "Beta Work",
                "source_provider": "openalex",
            },
            {
                "relation_type": "topic",
                "target_id": "https://openalex.org/T123",
                "target_title": "Machine Learning",
                "source_provider": "openalex",
                "raw": {
                    "subfield": {"display_name": "Artificial Intelligence"},
                    "field": {"display_name": "Computer Science"},
                    "domain": {"display_name": "Physical Sciences"},
                    "score": 0.82,
                },
            },
            {
                "relation_type": "authorship",
                "target_id": "https://openalex.org/A123",
                "target_title": "Ada River",
                "source_provider": "openalex",
            },
            {
                "relation_type": "institution",
                "target_id": "https://ror.org/03yrm5c26",
                "target_title": "Example University",
                "source_provider": "openalex",
            },
            {
                "relation_type": "source",
                "target_id": "1234-5678",
                "target_title": "Journal of Testable Systems",
                "source_provider": "openalex",
            },
        ],
    )
    state.replace_work_aspects(
        vault,
        "source-alpha",
        [
            {
                "aspect_type": "method",
                "aspect_text": "coordination-aspect interviews",
                "check_status": "checked",
            }
        ],
    )

    manifest = rebuild_checked_qmd_source(vault)

    assert [row["path"] for row in manifest["documents"]] == [
        "graph-neighborhoods/source-alpha.md",
        "knowledge/notes/checked.md",
        "works/source-alpha.md",
    ]
    work = vault / ".memoria/index/qmd/checked/works/source-alpha.md"
    graph = vault / ".memoria/index/qmd/checked/graph-neighborhoods/source-alpha.md"
    assert "full text rarealpha" in work.read_text(encoding="utf-8")
    assert "coordination-aspect interviews" in work.read_text(encoding="utf-8")
    assert '"doi": "10.1000/alpha"' in work.read_text(encoding="utf-8")
    graph_text = graph.read_text(encoding="utf-8")
    assert "Ada River" in graph_text
    assert "Beta Work" in graph_text
    assert "Example University" in graph_text
    assert "Journal of Testable Systems" in graph_text
    assert "Artificial Intelligence" in graph_text
    assert "field: Computer Science" in graph_text
    assert "domain: Physical Sciences" in graph_text
    assert "score: 0.82" in graph_text
    assert filter_checked_results(vault, [{"file": graph.as_posix()}]) == [
        {"file": graph.as_posix()}
    ]
    assert answer_query(vault, "rarealpha")["sources"][0]["path"] == "works/source-alpha.md"
    assert (
        answer_query(vault, "coordination-aspect")["sources"][0]["path"] == "works/source-alpha.md"
    )
    concept_only = [
        (path.relative_to(vault).as_posix(), _tokens(path.read_text(encoding="utf-8")))
        for path in checked_concepts(vault)
    ]
    assert _bm25(concept_only, "Beta Work") == []
    assert (
        answer_query(vault, "Beta Work")["sources"][0]["path"]
        == "graph-neighborhoods/source-alpha.md"
    )
    assert (
        answer_query(vault, "Artificial Intelligence")["sources"][0]["path"]
        == "graph-neighborhoods/source-alpha.md"
    )
    assert answer_query(vault, "Ada River")["sources"][0]["path"] == (
        "graph-neighborhoods/source-alpha.md"
    )


def test_filter_checked_results_applies_read_barrier_to_qmd_rows(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    checked = note(vault, "checked", "checked", "alpha beta")
    note(vault, "unchecked", "unchecked", "poison alpha")
    rows = [
        {"file": "qmd://vault/knowledge/notes/unchecked.md", "title": "Unchecked"},
        {"file": checked.as_posix(), "title": "Checked absolute"},
        {"file": "qmd://vault/missing.md", "title": "Missing"},
    ]

    assert filter_checked_results(vault, rows) == [rows[1]]


def test_bm25_eval_harness_uses_only_checked_concepts(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    note(vault, "checked", "checked", "alpha beta")
    note(vault, "unchecked", "unchecked", "poison alpha")

    result = evaluate_bm25(
        vault,
        [
            {"query": "alpha", "relevant": ["knowledge/notes/checked.md"]},
            {"query": "poison", "relevant": ["knowledge/notes/unchecked.md"]},
        ],
    )

    assert result["documents"] == 1
    assert result["queries"] == 2
    assert result["hits"] == 1
    assert result["recall_at_k"] == 0.5
    assert result["results"][0]["hits"] == ["knowledge/notes/checked.md"]
    assert result["results"][1]["hits"] == []


def test_answer_query_contract_reports_sources_unknowns_and_contradictions(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    note(
        vault,
        "checked",
        "checked",
        "alpha beta",
        "contradictions:\n  - knowledge/notes/tension.md\n",
    )
    stale = note(vault, "superseded", "checked", "alpha stale")
    candidate = note(vault, "candidate", "checked", "alpha candidate")
    state.set_concept_flag(
        vault, stale.relative_to(vault).as_posix(), "stale", reason="test", trigger_id="test"
    )
    mark_note_candidate(vault, candidate)

    answer = answer_query(vault, "alpha")

    assert answer["engine"] == "bm25"
    assert answer["unknowns"] == []
    assert [source["path"] for source in answer["sources"]] == [
        "knowledge/notes/superseded.md",
        "knowledge/notes/checked.md",
    ]
    assert answer["staleness"] == [
        {
            "path": "knowledge/notes/superseded.md",
            "field": "stale",
            "value": True,
        }
    ]
    assert answer["contradictions"] == [
        {
            "path": "knowledge/notes/checked.md",
            "contradiction": "knowledge/notes/tension.md",
        }
    ]

    stale_answer = answer_query(vault, "candidate stale", include_stale=True, k=3)
    assert [source["path"] for source in stale_answer["sources"]] == [
        "knowledge/notes/candidate.md",
        "knowledge/notes/superseded.md",
    ]
    assert stale_answer["staleness"] == [
        {
            "path": "knowledge/notes/candidate.md",
            "field": "note_curation_status",
            "value": "candidate",
        },
        {
            "path": "knowledge/notes/superseded.md",
            "field": "stale",
            "value": True,
        },
    ]

    missing = answer_query(vault, "absent")
    assert missing["sources"] == []
    assert missing["unknowns"] == ["No checked current sources matched: absent"]


def test_answer_query_carries_project_context(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    project = vault / "knowledge/projects/project-alpha.md"
    project.parent.mkdir(parents=True, exist_ok=True)
    project.write_text(
        "---\n"
        "type: project\n"
        "check_status: checked\n"
        "title: Framing project\n"
        "thesis: knowledge/notes/thesis.md\n"
        "---\n"
        "Project body.\n",
        encoding="utf-8",
    )
    set_db_status(vault, project, "project", "checked")
    note(vault, "thesis", "checked", "methods caveat")

    answer = answer_query(vault, "what matters", project_id="project-alpha")

    assert answer["project_context"] == {
        "project_id": "knowledge/projects/project-alpha",
        "project_path": "knowledge/projects/project-alpha.md",
        "title": "Framing project",
        "thesis_path": "knowledge/notes/thesis.md",
    }
    assert [source["path"] for source in answer["sources"]][:1] == [
        "knowledge/projects/project-alpha.md"
    ]


def test_answer_query_uses_qmd_after_rebuild(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = workspace(tmp_path / "vault")
    qmd_log = _fake_qmd_query(tmp_path, monkeypatch)
    note(vault, "checked", "checked", "alpha beta")
    note(vault, "unchecked", "unchecked", "poison alpha")
    rebuild_checked_qmd_source(vault)

    answer = answer_query(vault, "alpha")

    assert answer["engine"] == "qmd"
    assert [source["path"] for source in answer["sources"]] == ["knowledge/notes/checked.md"]
    qmd_env = f"{vault}/.memoria/index/qmd/config|{vault}/.memoria/index/qmd/index.sqlite"
    assert qmd_log.read_text(encoding="utf-8").strip() == (
        f"query lex: alpha\nvec: alpha --no-rerank --format json -n 15 -c memoria-checked|{qmd_env}"
    )


def test_project_answer_expands_qmd_query_with_project_and_thesis_terms(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = workspace(tmp_path / "vault")
    qmd_log = _fake_qmd_query(tmp_path, monkeypatch)
    project = vault / "knowledge/projects/project-alpha.md"
    project.parent.mkdir(parents=True, exist_ok=True)
    project.write_text(
        "---\n"
        "type: project\n"
        "check_status: checked\n"
        "title: Framing project\n"
        "thesis: knowledge/notes/thesis.md\n"
        "scope_topics: [sensemaking]\n"
        "facets:\n"
        "  methodology: [qualitative]\n"
        "---\n"
        "Project body.\n",
        encoding="utf-8",
    )
    set_db_status(vault, project, "project", "checked")
    note(
        vault,
        "thesis",
        "checked",
        "Thesis body.",
        "topics: [patient-generated-data]\n",
    )
    rebuild_checked_qmd_source(vault)

    answer = answer_query(vault, "status", project_id="project-alpha")

    assert answer["engine"] == "qmd"
    assert answer["project_context"]["retrieval_terms"] == [
        "patient-generated-data",
        "qualitative",
        "sensemaking",
    ]
    assert "status Framing project project-alpha thesis" in qmd_log.read_text(encoding="utf-8")
    assert "patient-generated-data qualitative sensemaking" in qmd_log.read_text(encoding="utf-8")


def _fake_qmd_query(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    npm_root = tmp_path / "npm-global"
    npm_bin = npm_root / "bin"
    npm_bin.mkdir(parents=True)
    qmd_log = tmp_path / "qmd.log"
    npm = bin_dir / "npm"
    npm.write_text(f"#!{sys.executable}\nprint({str(npm_root)!r})\n", encoding="utf-8")
    qmd = npm_bin / "qmd"
    qmd.write_text(
        f"#!{sys.executable}\n"
        "import json, os, pathlib, sys\n"
        "pathlib.Path(os.environ['QMD_LOG']).write_text(\n"
        "    ' '.join(sys.argv[1:]) + '|' + os.environ.get('QMD_CONFIG_DIR', '')\n"
        "    + '|' + os.environ.get('INDEX_PATH', '')\n"
        "    + '\\n',\n"
        "    encoding='utf-8',\n"
        ")\n"
        "print(json.dumps([\n"
        "    {'file': 'qmd://memoria-checked/knowledge/notes/unchecked.md', 'score': 9},\n"
        "    {'file': 'qmd://memoria-checked/knowledge/notes/checked.md', 'score': 8},\n"
        "]))\n",
        encoding="utf-8",
    )
    npm.chmod(0o755)
    qmd.chmod(0o755)
    monkeypatch.setenv("QMD_LOG", str(qmd_log))
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    return qmd_log
