from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_vault.runtime import knowledge, state
from memoria_vault.runtime.knowledge import (
    analyze_project_argument,
    read_project_slice,
    render_project_export_markdown,
)
from memoria_vault.runtime.knowledge import (
    frame_project_paper as _frame_project_paper,
)
from memoria_vault.runtime.knowledge import (
    write_project_argument_canvas as _write_project_argument_canvas,
)
from memoria_vault.runtime.knowledge import (
    write_project_export as _write_project_export,
)
from memoria_vault.runtime.knowledge import (
    write_project_outline as _write_project_outline,
)
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.trusted_writer import append_explicit_journal_event
from memoria_vault.runtime.vaultio import read_frontmatter
from tests.helpers import _md, call_with_context, copy_memoria_dirs, git, init_git


def frame_project_paper(vault: Path, *args, **kwargs):
    return call_with_context(_frame_project_paper, vault, *args, **kwargs)


def write_project_argument_canvas(vault: Path, *args, **kwargs):
    return call_with_context(_write_project_argument_canvas, vault, *args, **kwargs)


def write_project_export(vault: Path, *args, **kwargs):
    return call_with_context(_write_project_export, vault, *args, **kwargs)


def write_project_outline(vault: Path, *args, **kwargs):
    return call_with_context(_write_project_outline, vault, *args, **kwargs)


def workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas", "config")
    init_git(tmp_path, "knowledge@example.invalid", "Knowledge")
    return tmp_path


def _checked(vault: Path, rel: str, concept_type: str) -> None:
    state.record_observed_file_edit(
        vault,
        output_id=rel,
        concept_type=concept_type,
        output_sha256=sha256_file(vault / rel),
    )
    state.set_concept_verdict(vault, rel, "checked")


def test_analyze_project_argument_reads_checked_note_links(tmp_path: Path) -> None:
    _md(
        tmp_path / "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n"
        "description: Project\nthesis: notes/thesis.md\n",
    )
    _md(
        tmp_path / "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\n",
    )
    _md(
        tmp_path / "notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Support\n"
        "links:\n  supports:\n    - notes/thesis.md\n",
    )
    _md(
        tmp_path / "notes/refute.md",
        "type: note\ncheck_status: checked\ntitle: Refute\n"
        "links:\n  contradicts:\n    - notes/thesis.md\n",
    )
    candidate = tmp_path / "notes/candidate.md"
    _md(
        candidate,
        "type: note\ncheck_status: checked\ntitle: Candidate\n"
        "links:\n  supports:\n    - notes/thesis.md\n",
    )
    append_explicit_journal_event(
        tmp_path,
        {
            "event": "derived",
            "operation": "propose-note-candidates",
            "output_id": candidate.relative_to(tmp_path).as_posix(),
        },
        actor="operation",
        machine="test-fixture",
    )

    result = analyze_project_argument(tmp_path, "project-alpha")

    assert result["project_path"] == "projects/project-alpha/project.md"
    assert result["thesis_path"] == "notes/thesis.md"
    assert result["argument_stage"] == "developing"
    assert result["relation_count"] == 2
    assert result["supports_count"] == 1
    assert result["contradicts_count"] == 1
    assert result["extends_count"] == 0
    assert result["evidence_saturation"] == "unsaturated"
    assert result["displayed_confidence"] == "below-threshold"
    assert result["saturation_conditions"] == {
        "mature_graph": False,
        "has_support": True,
        "has_refutation": True,
    }
    assert {node["path"] for node in result["nodes"]} == {
        "notes/thesis.md",
        "notes/support.md",
        "notes/refute.md",
    }
    assert result["findings"] == [{"kind": "thin-argument", "severity": "medium"}]
    assert [row["kind"] for row in result["gap_findings"]] == ["conflict"]
    assert [row["kind"] for row in result["advisories"]] == ["structural"]


def test_read_project_slice_uses_outline_order_and_computed_edges(tmp_path: Path) -> None:
    _md(
        tmp_path / "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n"
        "description: Project\nthesis: notes/thesis.md\n",
    )
    _md(
        tmp_path / "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\nid: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
    )
    _md(
        tmp_path / "notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Support\nid: 01ARZ3NDEKTSV4RRFFQ69G5FA2\n"
        "links:\n  supports:\n    - notes/thesis.md\n",
    )
    _md(
        tmp_path / "notes/outside.md",
        "type: note\ncheck_status: checked\ntitle: Outside\nid: 01ARZ3NDEKTSV4RRFFQ69G5FA3\n"
        "links:\n  supports:\n    - notes/thesis.md\n",
    )
    outline = tmp_path / "projects/project-alpha/outline.md"
    outline.write_text(
        "- 01ARZ3NDEKTSV4RRFFQ69G5FA2 — Lead with the support\n"
        "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — Then state the thesis\n"
        "- 01ARZ3NDEKTSV4RRFFQ69G5FZZ — Missing member\n",
        encoding="utf-8",
    )

    result = read_project_slice(tmp_path, "project-alpha")

    assert [member["path"] for member in result["members"]] == [
        "notes/support.md",
        "notes/thesis.md",
    ]
    assert [member["reasoning"] for member in result["members"]] == [
        "Lead with the support",
        "Then state the thesis",
    ]
    assert result["edges"] == [
        {"source": "notes/support.md", "target": "notes/thesis.md", "type": "supports"}
    ]
    assert result["missing"] == [{"id": "01ARZ3NDEKTSV4RRFFQ69G5FZZ", "line": 3}]

    canvas_result = write_project_argument_canvas(tmp_path, "project-alpha")
    canvas = json.loads((tmp_path / canvas_result["canvas_path"]).read_text(encoding="utf-8"))
    assert {node["file"] for node in canvas["nodes"]} == {
        "notes/support.md",
        "notes/thesis.md",
    }


def test_write_project_outline_proposes_bm25_slice_and_computes_edges(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    _md(
        vault / "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n"
        "description: Sleep plasticity project\nthesis: notes/thesis.md\n",
    )
    _md(
        vault / "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Sleep plasticity thesis\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
    )
    _md(
        vault / "notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Sleep plasticity support\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FA2\n"
        "links:\n  supports:\n    - notes/thesis.md\n",
    )
    _md(
        vault / "notes/outside.md",
        "type: note\ncheck_status: checked\ntitle: Unrelated archive\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FA3\n",
    )

    result = write_project_outline(
        vault,
        "project-alpha",
        query="sleep plasticity ![query](http://beacon.example/query.png)",
        limit=2,
    )

    assert result["retrieval_engine"] == "bm25"
    assert result["outline_path"] == "projects/project-alpha/outline.md"
    assert {member["path"] for member in result["members"]} == {
        "notes/support.md",
        "notes/thesis.md",
    }
    outline = (vault / "projects/project-alpha/outline.md").read_text(encoding="utf-8")
    assert "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — BM25 score " in outline
    assert "- 01ARZ3NDEKTSV4RRFFQ69G5FA2 — BM25 score " in outline
    assert "![query]" not in outline
    assert "`http://beacon.example/query.png`" in outline
    assert result["edges"] == [
        {"source": "notes/support.md", "target": "notes/thesis.md", "type": "supports"}
    ]


def test_write_project_argument_canvas_projects_checked_note_links(tmp_path: Path) -> None:
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

    result = write_project_argument_canvas(tmp_path, "project-alpha")

    assert result["canvas_path"] == "projects/project-alpha/argument.canvas"
    assert result["node_count"] == 2
    assert result["edge_count"] == 1
    canvas = json.loads((tmp_path / result["canvas_path"]).read_text(encoding="utf-8"))
    assert {node["file"] for node in canvas["nodes"]} == {
        "notes/thesis.md",
        "notes/support.md",
    }
    assert canvas["edges"][0]["label"] == "supports"


def test_write_project_export_renders_checked_project_markdown(tmp_path: Path) -> None:
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
        tmp_path / "hubs/alpha-hub.md",
        "type: hub\ncheck_status: checked\ntitle: Alpha hub\n"
        "description: Curated project context\nproject: projects/project-alpha/project.md\n",
    )
    (tmp_path / "bibliography.bib").write_text("@article{alpha,title={Alpha}}\n", encoding="utf-8")

    result = write_project_export(
        tmp_path,
        "project-alpha",
        output_path="exports/project-alpha.md",
    )

    assert result["project_path"] == "projects/project-alpha/project.md"
    assert result["format"] == "markdown"
    assert result["output_path"] == "exports/project-alpha.md"
    assert result["content"] == ""
    text = (tmp_path / result["output_path"]).read_text(encoding="utf-8")
    assert "# Alpha project" in text
    assert "## Argument Snapshot" in text
    assert "- Thesis: `notes/thesis.md`" in text
    assert "- Support --supports--> Thesis" in text
    assert "- Alpha hub: `hubs/alpha-hub.md` -- Curated project context" in text
    assert "```bibtex\n@article{alpha,title={Alpha}}\n```" in text


@pytest.mark.parametrize("export_format", ["markdown", "docx"])
def test_write_project_export_does_not_replace_read_only_external_target(
    tmp_path: Path, export_format: str
) -> None:
    vault = tmp_path / "vault"
    _md(
        vault / "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n"
        "description: Project\nthesis: notes/thesis.md\n",
    )
    _md(
        vault / "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\nstatus: accepted\n",
    )
    suffix = "md" if export_format == "markdown" else export_format
    target = tmp_path / f"read-only-export.{suffix}"
    target.write_text("keep\n", encoding="utf-8")
    target.chmod(0o444)

    try:
        with pytest.raises(PermissionError):
            write_project_export(
                vault,
                "project-alpha",
                export_format=export_format,
                output_path=str(target),
            )
    finally:
        target.chmod(0o600)

    assert target.read_text(encoding="utf-8") == "keep\n"


def test_argument_renderer_neutralizes_exported_beacons(tmp_path: Path) -> None:
    project = tmp_path / "projects/project-alpha/project.md"
    project.parent.mkdir(parents=True, exist_ok=True)
    project.write_text(
        "---\ntype: project\ncheck_status: checked\ntitle: Alpha project\n---\n"
        "![argument](http://beacon.example/argument.png) "
        "<script>signal()</script> http://beacon.example/bare\n",
        encoding="utf-8",
    )
    _checked(tmp_path, "projects/project-alpha/project.md", "project")

    rendered = render_project_export_markdown(tmp_path, "project-alpha")

    content = rendered["content"]
    assert "![argument]" not in content
    assert "<script>" not in content
    assert "](http://beacon.example" not in content
    assert "`http://beacon.example/argument.png`" in content
    assert "`http://beacon.example/bare`" in content


def test_export_writer_neutralizes_unsafe_renderer_content_at_final_choke(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _md(
        tmp_path / "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n",
    )
    monkeypatch.setattr(
        knowledge,
        "render_project_export_markdown",
        lambda _vault, _project: {
            "project_path": "projects/project-alpha/project.md",
            "format": "markdown",
            "content": "![final](http://beacon.example/final.png)\n",
            "node_count": 0,
            "edge_count": 0,
            "relation_count": 0,
        },
    )

    rendered = write_project_export(tmp_path, "project-alpha")

    assert "![final]" not in rendered["content"]
    assert "`http://beacon.example/final.png`" in rendered["content"]


def _valid_paper_plan() -> dict[str, object]:
    return {
        "target": "Journal of Testable Systems",
        "audience": "local-first tool builders",
        "research_question": "Can Memoria support standalone CLI research?",
        "central_contribution": "A checked CLI loop can produce usable evidence.",
        "gap_statement": "Existing PKM loops lack local checked export.",
        "claim_evidence_map": {"CLI loop works": "notes/support.md"},
        "figure_plan": {"Figure 1": "CLI loop stages"},
        "limitations": "Single-corpus dogfood run.",
    }


def test_frame_project_paper_records_plan_and_leaves_project_unchecked(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    project = vault / "projects/project-alpha/project.md"
    project.parent.mkdir(parents=True)
    project.write_text(
        "---\n"
        "type: project\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FAV\n"
        "title: Alpha project\n"
        "tags: []\n"
        "links: {}\n"
        "paper_plan: {}\n"
        "outcome_frame: {}\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    _checked(vault, "projects/project-alpha/project.md", "project")

    result = frame_project_paper(
        vault,
        "project-alpha",
        paper_plan=_valid_paper_plan(),
        machine="frame-test",
        run_id="frame-run",
    )

    assert result["project_path"] == "projects/project-alpha/project.md"
    assert result["check_status"] == "unchecked"
    frontmatter = read_frontmatter(project)
    assert frontmatter["paper_plan"]["research_question"].startswith("Can Memoria")
    assert frontmatter["outcome_frame"] == {
        "kind": "paper",
        "target": "Journal of Testable Systems",
        "audience": "local-first tool builders",
        "research_question": "Can Memoria support standalone CLI research?",
        "status": "framed",
    }
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL, "projects/project-alpha/project.md"}


def test_ready_only_export_requires_paper_plan_and_checked_support(tmp_path: Path) -> None:
    vault = tmp_path
    _md(
        vault / "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n"
        "description: Project\nthesis: notes/thesis.md\n",
    )
    _md(
        vault / "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\n",
    )
    with pytest.raises(ValueError, match="target"):
        write_project_export(vault, "project-alpha", ready_only=True)

    project = vault / "projects/project-alpha/project.md"
    frontmatter, body = project.read_text(encoding="utf-8").split("---\n", 2)[1:]
    project.write_text(
        "---\n"
        + frontmatter
        + "paper_plan:\n"
        + "  target: Journal of Testable Systems\n"
        + "  audience: local-first tool builders\n"
        + "  research_question: Can Memoria support standalone CLI research?\n"
        + "  central_contribution: A checked CLI loop can produce usable evidence.\n"
        + "  gap_statement: Existing PKM loops lack local checked export.\n"
        + "  claim_evidence_map:\n"
        + "    CLI loop works: notes/support.md\n"
        + "  figure_plan:\n"
        + "    Figure 1: CLI loop stages\n"
        + "  limitations: Single-corpus dogfood run.\n"
        + "---\n"
        + body,
        encoding="utf-8",
    )
    _checked(vault, "projects/project-alpha/project.md", "project")
    _md(
        vault / "notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Support\n"
        "links:\n  supports:\n    - notes/thesis.md\n",
    )

    result = write_project_export(vault, "project-alpha", ready_only=True)

    assert result["readiness"]["ready"] is True
    assert result["readiness"]["status"] == "export-ready"
    assert "# Alpha project" in result["content"]
    assert "## Paper Plan" in result["content"]


def test_write_project_export_requires_pandoc_for_non_markdown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _md(
        tmp_path / "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n",
    )
    monkeypatch.setattr("memoria_vault.runtime.knowledge.shutil.which", lambda _name: None)
    output_root = tmp_path / "exports"

    with pytest.raises(RuntimeError, match="Pandoc is required"):
        write_project_export(
            tmp_path,
            "project-alpha",
            export_format="docx",
            output_path="exports/project-alpha.docx",
        )

    assert not output_root.exists()
