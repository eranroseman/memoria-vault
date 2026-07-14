from __future__ import annotations

import json
import shutil
from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.capture import capture_source as _capture_source
from memoria_vault.runtime.knowledge import analyze_gaps as _analyze_gaps
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.search_index import (
    rebuild_checked_search_index as _rebuild_checked_search_index,
)
from memoria_vault.runtime.trusted_writer import append_explicit_journal_event
from memoria_vault.runtime.vaultio import read_frontmatter
from tests.helpers import WORKSPACE_SEED, call_with_context, copy_memoria_dirs, git, init_git


def capture_source(vault: Path, *args, **kwargs):
    return call_with_context(_capture_source, vault, *args, **kwargs)


def analyze_gaps(vault: Path, *args, **kwargs):
    return call_with_context(_analyze_gaps, vault, *args, **kwargs)


def rebuild_checked_search_index(vault: Path, *args, **kwargs):
    return call_with_context(_rebuild_checked_search_index, vault, *args, **kwargs)


def workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas", "config")
    init_git(tmp_path, "knowledge@example.invalid", "Knowledge")
    return tmp_path


def _assert_gap_contract(gap: dict[str, object], kind: str) -> None:
    assert gap["kind"] == kind
    assert gap["gap_type"] == kind
    assert gap["severity"] in {"high", "medium", "low"}
    assert gap["impact"] in {0, 1, 2}
    assert gap["confidence"] in {0, 1, 2}
    assert gap["actionability"] in {0, 1, 2}
    assert gap["score"] == gap["impact"] * gap["confidence"] * gap["actionability"]
    assert isinstance(gap["why"], str) and gap["why"]
    assert isinstance(gap["next_actions"], list)
    assert isinstance(gap["candidate_work_ids"], list)


def _checked(vault: Path, rel: str, concept_type: str) -> None:
    state.record_observed_file_edit(
        vault,
        output_id=rel,
        concept_type=concept_type,
        output_sha256=sha256_file(vault / rel),
    )
    state.set_concept_verdict(vault, rel, "checked")


def _md(path: Path, frontmatter: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}---\nBody.\n", encoding="utf-8")
    fm = read_frontmatter(path)
    status = fm.get("check_status")
    if status in state.CHECK_STATUSES:
        vault = _vault_root(path)
        rel = path.relative_to(vault).as_posix()
        state.record_observed_file_edit(
            vault,
            output_id=rel,
            concept_type=str(fm.get("type") or "note"),
            output_sha256=sha256_file(path),
        )
        state.set_concept_verdict(vault, rel, str(status))


def _vault_root(path: Path) -> Path:
    for parent in path.parents:
        if parent.name in {
            "notes",
            "hubs",
            "projects",
            "digests",
            "fulltext",
            "capabilities",
        }:
            return parent.parent
    return path.parent


def test_analyze_gaps_names_mismatches_and_seed_terms(tmp_path: Path) -> None:
    state.upsert_catalog_record(
        tmp_path,
        work_id="source-alpha",
        title="Alpha",
        check_status="checked",
        text_status="full-text",
        csl_json={"memoria": {"tags": ["sleep"]}},
    )
    _md(
        tmp_path / "digests/source-alpha.md",
        "type: digest\ncheck_status: checked\nid: source-alpha\ntitle: Alpha digest\n"
        "description: Alpha\nwork_id: source-alpha\ntags: [sleep]\nlinks: {}\n",
    )
    for idx in range(2):
        _md(
            tmp_path / f"notes/warrant-{idx}.md",
            f"type: note\ncheck_status: checked\ntitle: Warrant {idx}\ntags: [warrant]\n",
        )
    state.upsert_catalog_record(
        tmp_path,
        work_id="balanced",
        title="Balanced",
        check_status="checked",
        text_status="full-text",
        csl_json={"memoria": {"tags": ["balanced"]}},
    )
    _md(
        tmp_path / "notes/balanced.md",
        "type: note\ncheck_status: checked\ntitle: Balanced note\ntags: [balanced]\n",
    )
    state.upsert_catalog_record(
        tmp_path,
        work_id="thin",
        title="Thin",
        check_status="checked",
        text_status="full-text",
        csl_json={"memoria": {"tags": ["thin"]}},
    )
    state.upsert_catalog_record(
        tmp_path,
        work_id="unchecked",
        title="Unchecked",
        check_status="unchecked",
        text_status="full-text",
        csl_json={"memoria": {"tags": ["unchecked-only"]}},
    )
    state.upsert_catalog_record(
        tmp_path,
        work_id="retracted",
        title="Retracted",
        check_status="checked",
        text_status="full-text",
        csl_json={"memoria": {"tags": ["stale-only"], "standing": "retracted"}},
    )
    for idx in range(2):
        path = tmp_path / f"notes/candidate-{idx}.md"
        _md(
            path,
            f"type: note\ncheck_status: checked\ntitle: Candidate {idx}\ntags: [candidate-only]\n",
        )
        append_explicit_journal_event(
            tmp_path,
            {
                "event": "derived",
                "operation": "propose-note-candidates",
                "output_id": path.relative_to(tmp_path).as_posix(),
            },
            actor="operation",
            machine="test-fixture",
        )

    result = analyze_gaps(tmp_path, seed_terms=["new area"], dense_threshold=2)

    gaps = {gap["topic"]: gap for gap in result["gaps"]}
    assert set(gaps) == {"sleep", "warrant", "new area"}
    assert gaps["sleep"]["gap_type"] == "undigested"
    assert gaps["sleep"]["source_count"] == 1
    assert gaps["sleep"]["digest_count"] == 1
    assert gaps["sleep"]["note_count"] == 0
    _assert_gap_contract(gaps["sleep"], "undigested")
    assert gaps["warrant"]["gap_type"] == "under-warranted"
    assert gaps["warrant"]["note_count"] == 2
    _assert_gap_contract(gaps["warrant"], "under-warranted")
    assert gaps["new area"]["gap_type"] == "new-topic"
    _assert_gap_contract(gaps["new area"], "new-topic")
    assert result["summary"]["total"] == 3
    assert result["summary"]["by_severity"]["high"] == 2
    assert result["saturation"]["ready"] is False
    assert result["checked_topics"] == 5


def test_analyze_gaps_counts_checked_sqlite_catalog_source_terms(tmp_path: Path) -> None:
    state.upsert_catalog_record(
        tmp_path,
        work_id="db-alpha",
        title="DB Alpha",
        text_status="full-text",
        check_status="checked",
        csl_json={"memoria": {"research_area": ["catalog-only"]}},
    )
    state.upsert_catalog_record(
        tmp_path,
        work_id="db-archived",
        title="DB Archived",
        text_status="full-text",
        check_status="checked",
        csl_json={"memoria": {"research_area": ["archived-only"], "standing": "archived"}},
    )
    state.upsert_catalog_record(
        tmp_path,
        work_id="db-unchecked",
        title="DB Unchecked",
        text_status="full-text",
        check_status="unchecked",
        csl_json={"memoria": {"research_area": ["unchecked-only"]}},
    )
    state.replace_work_graph_edges(
        tmp_path,
        "db-alpha",
        [
            {
                "relation_type": "topic",
                "target_id": "https://openalex.org/T1",
                "source_provider": "openalex",
                "raw": {"subfield": {"display_name": "Graph-only Topic"}},
            },
            {
                "relation_type": "keyword",
                "target_id": "https://openalex.org/K1",
                "target_title": "Graph-only Keyword",
                "source_provider": "openalex",
            },
        ],
    )
    state.replace_work_graph_edges(
        tmp_path,
        "db-archived",
        [
            {
                "relation_type": "topic",
                "target_id": "https://openalex.org/T2",
                "source_provider": "openalex",
                "raw": {"subfield": {"display_name": "Archived graph"}},
            }
        ],
    )

    result = analyze_gaps(tmp_path, dense_threshold=1)

    gaps = {gap["topic"]: gap for gap in result["gaps"]}
    assert set(gaps) == {"Graph-only Keyword", "Graph-only Topic", "catalog-only"}
    assert gaps["catalog-only"]["gap_type"] == "undigested"
    assert gaps["catalog-only"]["source_count"] == 1
    assert gaps["catalog-only"]["digest_count"] == 0
    assert gaps["catalog-only"]["note_count"] == 0
    assert gaps["Graph-only Topic"]["gap_type"] == "undigested"
    assert gaps["Graph-only Topic"]["source_count"] == 1
    assert gaps["Graph-only Topic"]["digest_count"] == 0
    assert gaps["Graph-only Topic"]["note_count"] == 0
    assert gaps["Graph-only Keyword"]["gap_type"] == "undigested"
    assert gaps["Graph-only Keyword"]["source_count"] == 1
    assert gaps["Graph-only Keyword"]["digest_count"] == 0
    assert gaps["Graph-only Keyword"]["note_count"] == 0


def test_analyze_gaps_ignores_retired_topics_from_untouched_catalog_work(tmp_path: Path) -> None:
    state.upsert_catalog_record(
        tmp_path,
        work_id="legacy-work",
        title="Legacy Work",
        check_status="checked",
        text_status="full-text",
        csl_json={
            "memoria": {
                "topics": ["legacy-only"],
                "research_area": ["current-area"],
            }
        },
    )

    result = analyze_gaps(tmp_path, dense_threshold=1)

    assert {gap["topic"] for gap in result["gaps"]} == {"current-area"}


def test_analyze_gaps_uses_search_graph_for_discovery_candidates(tmp_path: Path) -> None:
    vault = workspace(tmp_path / "vault")
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "rare alpha full text for checked search gap analysis",
        machine="capture-machine",
    )
    state.replace_work_graph_edges(
        vault,
        "source-alpha",
        [
            {
                "relation_type": "references",
                "target_id": "https://openalex.org/W999",
                "target_title": "Beta Work",
                "target_doi": "10.1000/beta",
                "source_provider": "openalex",
            }
        ],
    )
    rebuild_checked_search_index(vault)

    result = analyze_gaps(
        vault,
        seed_terms=["rare alpha"],
        dense_threshold=1,
        machine="gap-machine",
    )

    gap = {row["topic"]: row for row in result["gaps"]}["rare alpha"]
    assert gap["gap_type"] == "undigested"
    _assert_gap_contract(gap, "undigested")
    assert gap["retrieval_engine"] == "bm25"
    assert gap["retrieval_sources"][0]["path"] == "fulltexts/source-alpha.md"
    citation_gap = {row["topic"]: row for row in result["gaps"]}[
        "Citation neighborhood: Alpha Source"
    ]
    _assert_gap_contract(citation_gap, "citation-neighborhood")
    assert citation_gap["candidate_work_ids"] == ["https://openalex.org/W999"]
    assert result["citation_neighborhood_gap_count"] == 1
    assert result["discovery_candidate_paths"] == [
        "inbox/candidate-work-source-alpha-references-https___openalex.org_W999.md"
    ]
    candidate = vault / result["discovery_candidate_paths"][0]
    fm = read_frontmatter(candidate)
    assert fm["attention_kind"] == "candidate"
    assert fm["raised_by"] == "analyze-gaps"
    assert fm["discovered_work_id"] == "https://openalex.org/W999"
    assert "check_status" not in fm
    assert state.catalog_source(vault, "https://openalex.org/W999") is None
    committed = set(
        git(vault, "show", "--name-only", "--format=", result["discovery_commit"]).splitlines()
    )
    assert committed == {
        "inbox/candidate-work-source-alpha-references-https___openalex.org_W999.md",
        state.JOURNAL_HEAD_REL,
    }


def test_analyze_gaps_emits_unchecked_tag_candidate_attention(tmp_path: Path) -> None:
    vault = workspace(tmp_path / "vault")
    (vault / "system").mkdir()
    shutil.copyfile(WORKSPACE_SEED / "system/vocabulary.md", vault / "system/vocabulary.md")
    work_rel = "digests/source-alpha.md"
    work = vault / work_rel
    work.parent.mkdir(parents=True, exist_ok=True)
    work.write_text(
        "---\n"
        "type: digest\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FC0\n"
        "title: Retrieval practice digest\n"
        "tags: []\n"
        "links: {}\n"
        "work_id: source-alpha\n"
        "work_id: catalog/sources/source-alpha\n"
        "---\n"
        "Neural retrieval improves durable memory systems.\n"
        "Neural retrieval also changes review timing.\n"
        "Personal informatics covers behavior data.\n"
        "Personal informatics supports reflection.\n",
        encoding="utf-8",
    )
    _checked(vault, work_rel, "digest")

    result = analyze_gaps(vault, machine="gap-machine")

    assert result["tag_candidate_paths"] == ["inbox/candidate-tag-neural-retrieval.md"]
    candidate = vault / result["tag_candidate_paths"][0]
    fm = read_frontmatter(candidate)
    assert fm["attention_kind"] == "candidate"
    assert fm["attention_status"] == "open"
    assert fm["candidate_tag"] == "neural retrieval"
    assert fm["target"] == work_rel
    assert "check_status" not in fm
    assert read_frontmatter(work)["tags"] == []
    committed = set(
        git(vault, "show", "--name-only", "--format=", result["tag_candidate_commit"]).splitlines()
    )
    assert committed == {result["tag_candidate_paths"][0], state.JOURNAL_HEAD_REL}


def test_analyze_gaps_proposes_candidates_from_sqlite_source_gaps_without_search_index(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path / "vault")
    state.upsert_catalog_record(
        vault,
        work_id="db-alpha",
        title="DB Alpha",
        text_status="full-text",
        check_status="checked",
        csl_json={"memoria": {"research_area": ["catalog-only"]}},
    )
    state.replace_work_graph_edges(
        vault,
        "db-alpha",
        [
            {
                "relation_type": "related",
                "target_id": "https://openalex.org/W777",
                "target_title": "Gamma Work",
                "target_doi": "10.1000/gamma",
                "source_provider": "openalex",
            }
        ],
    )

    result = analyze_gaps(vault, dense_threshold=1, machine="gap-machine")

    gap = {row["topic"]: row for row in result["gaps"]}["catalog-only"]
    _assert_gap_contract(gap, "undigested")
    assert gap["work_ids"] == ["db-alpha"]
    assert gap["discovery_candidate_paths"] == [
        "inbox/candidate-work-db-alpha-related-https___openalex.org_W777.md"
    ]
    citation_gap = {row["topic"]: row for row in result["gaps"]}["Citation neighborhood: DB Alpha"]
    _assert_gap_contract(citation_gap, "citation-neighborhood")
    assert citation_gap["candidate_work_ids"] == ["https://openalex.org/W777"]
    assert result["citation_neighborhood_gap_count"] == 1
    assert result["discovery_candidate_paths"] == gap["discovery_candidate_paths"]
    candidate = vault / result["discovery_candidate_paths"][0]
    fm = read_frontmatter(candidate)
    assert fm["raised_by"] == "analyze-gaps"
    assert fm["discovered_work_id"] == "https://openalex.org/W777"
    assert "check_status" not in fm
    assert state.catalog_source(vault, "https://openalex.org/W777") is None


def test_analyze_gaps_ranks_discovery_candidates_against_steering(tmp_path: Path) -> None:
    vault = workspace(tmp_path / "vault")
    (vault / "steering.md").write_text(
        "Prioritize neural retrieval evaluation.\n", encoding="utf-8"
    )
    state.upsert_catalog_record(
        vault,
        work_id="db-alpha",
        title="DB Alpha",
        text_status="full-text",
        check_status="checked",
        csl_json={"memoria": {"research_area": ["catalog-only"]}},
    )
    state.replace_work_graph_edges(
        vault,
        "db-alpha",
        [
            {
                "relation_type": "related",
                "target_id": "https://openalex.org/W111",
                "target_title": "Unrelated Work",
                "source_provider": "openalex",
            },
            {
                "relation_type": "related",
                "target_id": "https://openalex.org/W999",
                "target_title": "Neural Retrieval Evaluation",
                "source_provider": "openalex",
            },
        ],
    )

    result = analyze_gaps(vault, dense_threshold=1, machine="gap-machine")

    assert result["discovery_candidate_paths"] == [
        "inbox/candidate-work-db-alpha-related-https___openalex.org_W999.md",
        "inbox/candidate-work-db-alpha-related-https___openalex.org_W111.md",
    ]
    assert result["discovery_candidate_channels"] == {"ranked": 1, "exploration": 1}
    ranked = read_frontmatter(vault / result["discovery_candidate_paths"][0])
    exploration = read_frontmatter(vault / result["discovery_candidate_paths"][1])
    assert ranked["discovery_relevance_channel"] == "ranked"
    assert ranked["discovery_relevance_score"] > exploration["discovery_relevance_score"]
    assert ranked["discovery_relevance_factors"]["title_overlap"] == [
        "evaluation",
        "neural",
        "retrieval",
    ]
    assert exploration["discovery_relevance_channel"] == "exploration"


def test_analyze_gaps_reports_missing_full_text(tmp_path: Path) -> None:
    vault = workspace(tmp_path / "vault")
    state.upsert_catalog_record(
        vault,
        work_id="unchecked-metadata",
        title="Unchecked Metadata",
        text_status="metadata-only",
        check_status="unchecked",
    )
    state.upsert_catalog_record(
        vault,
        work_id="metadata-only",
        title="Metadata Only",
        text_status="metadata-only",
        check_status="checked",
    )

    result = analyze_gaps(vault, machine="gap-machine")

    assert result["full_text_gap_count"] == 1
    gap = result["gaps"][0]
    _assert_gap_contract(gap, "full-text-missing")
    assert gap["work_id"] == "metadata-only"
    assert "unchecked-metadata" not in json.dumps(result["gaps"])
    assert result["full_text_attention_paths"] == ["inbox/flag-gap-full-text-metadata-only.md"]
    attention = vault / result["full_text_attention_paths"][0]
    fm = read_frontmatter(attention)
    assert fm["attention_kind"] == "flag"
    assert fm["raised_by"] == "analyze-gaps"
    assert fm["target"] == "catalog/sources/metadata-only"
    committed = set(
        git(
            vault,
            "show",
            "--name-only",
            "--format=",
            result["full_text_attention_commit"],
        ).splitlines()
    )
    assert committed == {
        "inbox/flag-gap-full-text-metadata-only.md",
        state.JOURNAL_HEAD_REL,
    }


def test_analyze_gaps_adds_project_argument_health(tmp_path: Path) -> None:
    _md(
        tmp_path / "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n"
        "description: Project\nthesis: notes/thesis.md\n",
    )
    _md(
        tmp_path / "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\nstatus: accepted\n",
    )
    _md(
        tmp_path / "notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Support\nstatus: accepted\n"
        "links:\n  supports:\n    - notes/thesis.md\n",
    )
    _md(
        tmp_path / "notes/refute.md",
        "type: note\ncheck_status: checked\ntitle: Refute\nstatus: accepted\n"
        "links:\n  contradicts:\n    - notes/thesis.md\n",
    )

    result = analyze_gaps(tmp_path, project_path="project-alpha")

    assert result["project_path"] == "projects/project-alpha/project.md"
    assert result["thesis_path"] == "notes/thesis.md"
    assert result["argument_stage"] == "developing"
    assert result["argument_gap_count"] == 2
    assert result["paper_readiness_gap_count"] == 1
    gaps = {gap["finding_kind"]: gap for gap in result["gaps"] if "finding_kind" in gap}
    _assert_gap_contract(gaps["thin-argument"], "argument-unsupported")
    assert gaps["thin-argument"]["note_count"] == 3
    _assert_gap_contract(gaps["conflict"], "argument-fragile")
    assert gaps["conflict"]["advice"] == "resolve or preserve the contradiction"
    paper_gap = next(gap for gap in result["gaps"] if gap["kind"] == "paper-readiness")
    assert "target" in paper_gap["missing"]
    assert result["saturation"] == {
        "claims": 1,
        "saturated": 1,
        "unsupported": 0,
        "uncountered": 0,
        "ready": True,
        "claim_saturation": [
            {
                "claim": "notes/thesis.md",
                "has_support": True,
                "has_counterpoint": True,
                "saturated": True,
            }
        ],
        "conditions": {
            "mature_graph": False,
            "has_support": True,
            "has_refutation": True,
        },
        "evidence_saturation": "unsaturated",
    }


def test_analyze_gaps_seeds_project_scope_and_thesis_terms(tmp_path: Path) -> None:
    _md(
        tmp_path / "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n"
        "description: Project\nthesis: notes/thesis.md\n"
        "scope_topics: [sensemaking]\n"
        "facets:\n"
        "  methodology: [qualitative]\n",
    )
    _md(
        tmp_path / "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\nstatus: accepted\n"
        "keywords: [patient-generated-data]\n"
        "facets:\n"
        "  topics: [care coordination]\n",
    )

    result = analyze_gaps(tmp_path, project_path="project-alpha", dense_threshold=1)

    gaps = {gap["topic"]: gap for gap in result["gaps"]}
    assert gaps["sensemaking"]["gap_type"] == "new-topic"
    assert gaps["qualitative"]["gap_type"] == "new-topic"
    assert gaps["patient-generated-data"]["gap_type"] == "under-warranted"
    assert gaps["patient-generated-data"]["note_count"] == 1
    assert gaps["care coordination"]["gap_type"] == "under-warranted"
