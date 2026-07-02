from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.search_index import (
    _bm25,
    _tokens,
    answer_query,
    checked_concepts,
    evaluate_bm25,
    filter_checked_results,
    rebuild_checked_qmd_source,
)

ROOT = Path(__file__).resolve().parent.parent


def workspace(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "vault-template/.memoria/schemas", tmp_path / ".memoria/schemas")
    return tmp_path


def note(vault: Path, name: str, status: str, body: str, extra: str = "") -> Path:
    path = vault / "knowledge" / "notes" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\ntype: note\ncheck_status: {status}\ntitle: {name}\n{extra}---\n{body}\n",
        encoding="utf-8",
    )
    return path


def test_rebuild_checked_qmd_source_copies_only_checked_concepts(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    note(vault, "checked", "checked", "alpha beta")
    note(vault, "unchecked", "unchecked", "poison alpha")
    note(vault, "quarantined", "quarantined", "poison beta")
    note(vault, "candidate", "checked", "candidate alpha", "status: candidate\n")
    note(vault, "superseded", "checked", "stale alpha", "status: superseded\n")
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
    assert [row["path"] for row in manifest["documents"]] == ["knowledge/notes/checked.md"]
    assert (vault / ".memoria/index/qmd/checked/knowledge/notes/checked.md").is_file()
    assert not (vault / ".memoria/index/qmd/checked/capabilities").exists()
    assert not (vault / ".memoria/index/qmd/checked/knowledge/notes/candidate.md").exists()
    assert not (vault / ".memoria/index/qmd/checked/knowledge/notes/unchecked.md").exists()
    assert not (vault / ".memoria/index/qmd/checked/knowledge/notes/quarantined.md").exists()
    assert not (vault / ".memoria/index/qmd/checked/knowledge/notes/superseded.md").exists()
    assert manifest["qmd_commands"][-1] == "qmd update"


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
        metadata_status="verified",
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

    manifest = rebuild_checked_qmd_source(vault)

    assert [row["path"] for row in manifest["documents"]] == [
        "graph-neighborhoods/source-alpha.md",
        "knowledge/notes/checked.md",
        "works/source-alpha.md",
    ]
    work = vault / ".memoria/index/qmd/checked/works/source-alpha.md"
    graph = vault / ".memoria/index/qmd/checked/graph-neighborhoods/source-alpha.md"
    assert "full text rarealpha" in work.read_text(encoding="utf-8")
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
    note(vault, "superseded", "checked", "alpha stale", "status: superseded\n")
    note(vault, "candidate", "checked", "alpha candidate", "status: candidate\n")

    answer = answer_query(vault, "alpha")

    assert answer["engine"] == "bm25"
    assert answer["unknowns"] == []
    assert [source["path"] for source in answer["sources"]] == ["knowledge/notes/checked.md"]
    assert answer["staleness"] == []
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
            "field": "status",
            "value": "candidate",
        },
        {
            "path": "knowledge/notes/superseded.md",
            "field": "status",
            "value": "superseded",
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
