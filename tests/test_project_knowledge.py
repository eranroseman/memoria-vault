from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from memoria_vault.runtime import knowledge, projections, state
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
from memoria_vault.runtime.trusted_writer import append_explicit_journal_event
from memoria_vault.runtime.vaultio import read_frontmatter
from tests.helpers import (
    _md,
    call_with_context,
    copy_memoria_dirs,
    git,
    init_git,
    mark_file_status,
)


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


def test_analyze_project_argument_traverses_claim_to_work_bridge(tmp_path: Path) -> None:
    """A claim grounded in a checked work stays connected to it in the argument graph.

    Two works, one checked and one not: the bridge admits catalog targets, and the
    filter it admits them through is `catalog_sources`' own checked scope, not the
    mere shape of a `catalog/sources/*` string.
    """
    state.upsert_catalog_record(
        tmp_path, work_id="source-alpha", title="Alpha Source", check_status="checked"
    )
    state.upsert_catalog_record(
        tmp_path, work_id="source-beta", title="Beta Source", check_status="unchecked"
    )
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
        "links:\n  supports:\n    - notes/thesis.md\n"
        "    - catalog/sources/source-alpha\n"
        "    - catalog/sources/source-beta\n",
    )

    result = analyze_project_argument(tmp_path, "projects/project-alpha/project.md")

    assert {
        "source": "notes/support.md",
        "target": "catalog/sources/source-alpha",
        "type": "supports",
    } in result["edges"]
    assert "catalog/sources/source-beta" not in {edge["target"] for edge in result["edges"]} | {
        node["path"] for node in result["nodes"]
    }
    # Whole node record: a role assertion alone cannot tell a work rendered by its
    # work_id from one rendered as a blank or as its store path.
    assert {
        "path": "catalog/sources/source-alpha",
        "title": "source-alpha",
        "role": "work",
    } in result["nodes"]
    assert {"path": "notes/thesis.md", "title": "Thesis", "role": "thesis"} in result["nodes"]
    assert {"path": "notes/support.md", "title": "Support", "role": "note"} in result["nodes"]
    # Retraction blast radius: a walk rooted at the WORK reaches every
    # transitively grounded claim through the bridge.
    neighbors: dict[str, set[str]] = {}
    for edge in result["edges"]:
        neighbors.setdefault(edge["source"], set()).add(edge["target"])
        neighbors.setdefault(edge["target"], set()).add(edge["source"])
    seen = {"catalog/sources/source-alpha"}
    queue = ["catalog/sources/source-alpha"]
    while queue:
        for neighbor in neighbors.get(queue.pop(), set()):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    assert {"notes/support.md", "notes/thesis.md"} <= seen


def _argument_vault(tmp_path: Path, thesis: str) -> Path:
    _md(
        tmp_path / "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n"
        f"description: Project\nthesis: {thesis}\n",
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
    return tmp_path


@pytest.mark.parametrize(
    ("label", "thesis", "expected_path", "expected_nodes"),
    [
        ("canonical path", "notes/thesis.md", "notes/thesis.md", 2),
        # The shape structural impact's own fixture writes. `_concept_rel` ran on
        # the raw value here and raised `unsupported note link target:
        # [[notes/thesis]].md` straight out of the lens (issue #1623).
        ("wikilink-wrapped path", "'[[notes/thesis]]'", "notes/thesis.md", 2),
        ("bare stem", "thesis", "notes/thesis.md", 2),
        # Path space refuses a title, so the lens reports a miss instead of
        # naming a phantom `notes/Toulmin: the warrant.md` it never found.
        ("title carrying a colon", "'Toulmin: the warrant'", "", 0),
        ("traversal", "notes/../thesis.md", "", 0),
    ],
)
def test_analyze_project_argument_reads_thesis_in_one_path_space(
    tmp_path: Path, label: str, thesis: str, expected_path: str, expected_nodes: int
) -> None:
    vault = _argument_vault(tmp_path, thesis)

    result = analyze_project_argument(vault, "project-alpha")

    assert result["thesis_path"] == expected_path, label
    assert result["node_count"] == expected_nodes, label


def test_project_slice_query_reads_thesis_in_the_same_path_space(tmp_path: Path) -> None:
    """The retrieval-query builder is its own `thesis:` reader (issue #1623).

    Its `except ValueError` swallowed the wikilink shape and fell back to the
    raw text, so the thesis note's own terms never reached the query. A value
    path space refuses is still kept as a term: that is a schema error to
    report, not a reason to narrow the slice with nothing.
    """
    vault = _argument_vault(tmp_path, "'[[notes/thesis]]'")
    project = knowledge._checked_frontmatter(vault, "projects/project-alpha/project.md", "project")

    def query(frontmatter: dict) -> str:
        return knowledge._project_slice_query(
            vault, "projects/project-alpha/project.md", frontmatter, "seed"
        )

    assert "Thesis" in query(project)
    assert "[[notes/thesis]]" not in query(project)
    assert "Toulmin: the warrant" in query({**project, "thesis": "Toulmin: the warrant"})
    # `active_thesis:` is retired: no reader falls back to it any more.
    assert "Thesis" not in query({"active_thesis": "notes/thesis.md"})


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
    assert {node["file"] for node in canvas["nodes"] if node.get("type") == "file"} == {
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
    assert {node["file"] for node in canvas["nodes"] if node.get("type") == "file"} == {
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
        allow_unready=True,
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
                allow_unready=True,
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
    mark_file_status(tmp_path, "projects/project-alpha/project.md", "project")

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

    rendered = write_project_export(tmp_path, "project-alpha", allow_unready=True)

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
    mark_file_status(vault, "projects/project-alpha/project.md", "project")

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


def test_non_draft_export_gate_enforced_by_default(tmp_path: Path) -> None:
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
    with pytest.raises(ValueError, match="project is not export-ready"):
        write_project_export(vault, "project-alpha")

    escaped = write_project_export(vault, "project-alpha", allow_unready=True)
    assert escaped["readiness"]["ready"] is False
    assert "# Alpha project" in escaped["content"]

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
    mark_file_status(vault, "projects/project-alpha/project.md", "project")
    _md(
        vault / "notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Support\n"
        "links:\n  supports:\n    - notes/thesis.md\n",
    )

    result = write_project_export(vault, "project-alpha")

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
            allow_unready=True,
        )

    assert not output_root.exists()


def test_analyze_project_argument_reads_activated_relation_links(tmp_path: Path) -> None:
    """`_note_edges` builds edges from every frontmatter-legal relation, not the old triple.

    That roster — the only one left in this report — is what this test pins:
    `relation_count` and the component both grow by the `warrant` edge. The per-verb
    payload keys stay `supports`/`contradicts`/`extends` by design, so a `warrant`
    edge must move `relation_count` while leaving `supports_count` at zero.
    """
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
        tmp_path / "notes/license.md",
        "type: note\ncheck_status: checked\ntitle: License\n"
        "links:\n  warrant:\n    - notes/thesis.md\n",
    )

    result = analyze_project_argument(tmp_path, "project-alpha")

    assert result["relation_count"] == 1
    assert result["supports_count"] == 0
    assert {node["path"] for node in result["nodes"]} == {
        "notes/thesis.md",
        "notes/license.md",
    }


def _staged_argument_vault(tmp_path: Path, relations: list[str]) -> Path:
    """Wire one checked note per entry of `relations` into the thesis component.

    One edge per note, so the component's relation tally is exactly `relations`.
    Callers pass three or more: the stage threshold is three, and a shorter
    fixture only exercises the `developing` short-circuit and says nothing about
    which role the verb carries.
    """
    _md(
        tmp_path / "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n"
        "description: Project\nthesis: notes/thesis.md\n",
    )
    _md(
        tmp_path / "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\n",
    )
    for index, relation in enumerate(relations):
        _md(
            tmp_path / f"notes/edge-{index}.md",
            f"type: note\ncheck_status: checked\ntitle: Edge {index}\n"
            f"links:\n  {relation}:\n    - notes/thesis.md\n",
        )
    return tmp_path


def test_a_rebuttal_only_component_stages_contested_and_never_supported(
    tmp_path: Path,
) -> None:
    """Three rebuttals are a challenged thesis, not a supported one (Graph-R11).

    `rebuttal` is the challenge verb this seam can actually produce — `tension` is
    outside `LINK_RELATIONS`, so no frontmatter fixture reaches the lens with one.
    Before the recalibration this component reported `supported` /
    `below-threshold` / `has_refutation: False`, all three at once.
    """
    vault = _staged_argument_vault(tmp_path, ["rebuttal", "rebuttal", "rebuttal"])

    result = analyze_project_argument(vault, "project-alpha")

    assert result["relation_count"] == 3
    assert result["argument_stage"] == "contested"
    assert result["displayed_confidence"] == "contested"
    assert result["saturation_conditions"] == {
        "mature_graph": True,
        "has_support": False,
        "has_refutation": True,
    }
    assert result["evidence_saturation"] == "unsaturated"


def test_a_qualifier_only_component_stages_developing_as_structure_not_challenge(
    tmp_path: Path,
) -> None:
    """`qualifier` bounds scope, so it neither supports nor challenges (Graph-R11).

    The stage is read alongside both saturation sides in one payload: a component
    that merely counted three edges would be indistinguishable from one whose
    qualifiers were classified as challenge, and only `has_refutation is False`
    separates them. `developing` is the derived value — no support edge, no
    challenge edge, and the ruling forbids a fifth stage name.
    """
    vault = _staged_argument_vault(tmp_path, ["qualifier", "qualifier", "qualifier"])

    result = analyze_project_argument(vault, "project-alpha")

    assert result["relation_count"] == 3
    assert result["argument_stage"] == "developing"
    assert result["displayed_confidence"] == "below-threshold"
    assert result["saturation_conditions"] == {
        "mature_graph": True,
        "has_support": False,
        "has_refutation": False,
    }


def test_a_genuinely_supported_component_is_not_demoted_by_the_recalibration(
    tmp_path: Path,
) -> None:
    """One `supports` plus structure at threshold stays `supported`.

    The regression guard for the other direction: requiring a support edge must
    not turn every mixed component into `developing`.
    """
    vault = _staged_argument_vault(tmp_path, ["supports", "extends", "extends"])

    result = analyze_project_argument(vault, "project-alpha")

    assert result["relation_count"] == 3
    assert result["argument_stage"] == "supported"
    assert result["displayed_confidence"] == "supported"
    assert result["saturation_conditions"] == {
        "mature_graph": True,
        "has_support": True,
        "has_refutation": False,
    }


def test_support_and_a_rebuttal_coexist_as_contested_without_masking_the_support(
    tmp_path: Path,
) -> None:
    """Challenge wins the stage, but the support side stays visible in saturation.

    Neither roster absorbs the other: `contested` is the stage and
    `has_support` stays True, which is what makes this component `saturated`
    while the rebuttal-only one above is not.
    """
    vault = _staged_argument_vault(tmp_path, ["supports", "rebuttal", "extends"])

    result = analyze_project_argument(vault, "project-alpha")

    assert result["relation_count"] == 3
    assert result["argument_stage"] == "contested"
    assert result["displayed_confidence"] == "contested"
    assert result["saturation_conditions"] == {
        "mature_graph": True,
        "has_support": True,
        "has_refutation": True,
    }
    assert result["evidence_saturation"] == "saturated"


def test_analyze_project_argument_ignores_a_link_target_that_escapes_its_folder(
    tmp_path: Path,
) -> None:
    """The report follows only normalized local targets — `notes/../thesis.md` is not one.

    Before the parsers converged on `lib.edges`, this note's link resolved back to
    `notes/thesis.md` and counted as an edge, while the validator rejected the same
    string as escaping the workspace.
    """
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
        tmp_path / "notes/escaping.md",
        "type: note\ncheck_status: checked\ntitle: Escaping\n"
        "links:\n  supports:\n    - notes/../thesis.md\n",
    )

    result = analyze_project_argument(tmp_path, "project-alpha")

    assert result["relation_count"] == 0
    assert {node["path"] for node in result["nodes"]} == {"notes/thesis.md"}


def test_analyze_project_argument_never_synthesizes_an_edge_into_the_dot_md_note(
    tmp_path: Path,
) -> None:
    """A rejected target must resolve to nothing, not to a real note named `.md`.

    `iter_markdown` yields a file literally named `.md`, so `notes/.md` is a legal
    key in the notes map — and every validator-rejected target normalizes to the
    empty string, which `_concept_rel` renders as exactly that path. Without the
    empty guard, junk targets become one absorbing edge sink.
    """
    _md(
        tmp_path / "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n"
        "description: Project\nthesis: notes/thesis.md\n",
    )
    _md(tmp_path / "notes/thesis.md", "type: note\ncheck_status: checked\ntitle: Thesis\n")
    _md(
        tmp_path / "notes/.md",
        "type: note\ncheck_status: checked\ntitle: Dot\n"
        "links:\n  supports:\n    - notes/thesis.md\n",
    )
    _md(
        tmp_path / "notes/escaping.md",
        "type: note\ncheck_status: checked\ntitle: Escaping\n"
        "links:\n  supports:\n    - notes/../thesis.md\n",
    )

    result = analyze_project_argument(tmp_path, "project-alpha")

    assert result["relation_count"] == 1
    assert {node["path"] for node in result["nodes"]} == {"notes/thesis.md", "notes/.md"}


# JSON Canvas 1.0 (https://jsoncanvas.org/spec/1.0/) — the format Obsidian opens.
# Encoded from the spec, never from this writer's output: a canvas that reads
# fine in a fixture but omits a required node key is one Obsidian refuses, and
# nothing else in the suite would notice.
_CANVAS_REQUIRED_NODE_KEYS = {"id", "type", "x", "y", "width", "height"}
_CANVAS_TYPE_REQUIRED_KEY = {"text": "text", "file": "file", "link": "url", "group": ""}
_CANVAS_COLOR_PRESETS = {"1", "2", "3", "4", "5", "6"}


def assert_json_canvas_conformant(canvas: dict) -> None:
    """Assert `canvas` satisfies JSON Canvas 1.0's required shape."""
    ids: set[str] = set()
    for node in canvas["nodes"]:
        assert _CANVAS_REQUIRED_NODE_KEYS <= set(node), node
        assert node["type"] in _CANVAS_TYPE_REQUIRED_KEY, node
        required = _CANVAS_TYPE_REQUIRED_KEY[node["type"]]
        assert not required or isinstance(node.get(required), str), node
        for dimension in ("x", "y", "width", "height"):
            assert isinstance(node[dimension], int), node
        if "color" in node:
            assert node["color"] in _CANVAS_COLOR_PRESETS or node["color"].startswith("#"), node
        assert node["id"] not in ids, node["id"]
        ids.add(node["id"])
    for edge in canvas["edges"]:
        assert {"id", "fromNode", "toNode"} <= set(edge), edge
        assert edge["fromNode"] in ids, edge
        assert edge["toNode"] in ids, edge
        assert edge["id"] not in ids, edge["id"]
        ids.add(edge["id"])


def test_generated_canvas_carries_banner_and_stable_node_ids(tmp_path: Path) -> None:
    """Four members, so the banner cannot hide a layout or ordering regression.

    The grid wraps every third file node; a banner counted into that index would
    move all of them, and a two-node fixture never reaches the wrap.
    """
    _md(
        tmp_path / "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n"
        "description: Project\nthesis: notes/thesis.md\n",
    )
    _md(
        tmp_path / "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\n",
    )
    for name in ("support", "extend", "refute"):
        _md(
            tmp_path / f"notes/{name}.md",
            f"type: note\ncheck_status: checked\ntitle: {name.title()}\n"
            "links:\n  supports:\n    - notes/thesis.md\n",
        )

    result = write_project_argument_canvas(tmp_path, "project-alpha")
    canvas = json.loads((tmp_path / result["canvas_path"]).read_text(encoding="utf-8"))
    assert_json_canvas_conformant(canvas)

    assert canvas["nodes"][0]["id"] == "memoria-banner"
    banner = canvas["nodes"][0]
    assert banner["type"] == "text"
    assert "read-only" in banner["text"]
    assert "regenerated" in banner["text"]
    assert "fork-project-canvas" in banner["text"]
    # Entirely above the member grid, which starts at y=0: a banner sitting on
    # top of the first note is a banner nobody reads.
    assert banner["y"] + banner["height"] <= 0

    file_nodes = [node for node in canvas["nodes"] if node.get("type") == "file"]
    assert len(canvas["nodes"]) == 5
    assert result["node_count"] == len(file_nodes) == 4
    for node in file_nodes:
        assert node["id"] == "n-" + hashlib.sha256(node["file"].encode()).hexdigest()[:12]
    # Nodes are sorted by path, so the fourth is the one that wraps the grid.
    assert [(node["x"], node["y"]) for node in file_nodes] == [
        (0, 0),
        (360, 0),
        (720, 0),
        (0, 240),
    ]

    rerendered = knowledge.render_project_argument_canvas(tmp_path, "project-alpha")
    assert {node["id"] for node in rerendered["nodes"]} == {node["id"] for node in canvas["nodes"]}
    assert projections.render_tracked_projection(tmp_path, result["canvas_path"]) == (
        tmp_path / result["canvas_path"]
    ).read_text(encoding="utf-8")


def test_canvas_node_ids_hash_the_raw_member_path() -> None:
    """The id is `n-sha256(raw path)[:12]` — the path as handed in, unnormalized.

    A fixture drawn only from already-normalized paths cannot tell the two
    apart, so this one hands in a path a normalizer would rewrite and pins the
    literal id the raw bytes produce.
    """
    canvas, _ = knowledge._canvas_from_nodes_edges([{"path": "notes/./thesis.md"}], [])

    assert canvas["nodes"][1]["id"] == "n-93378973d8a1"
    assert "n-93378973d8a1" == "n-" + hashlib.sha256(b"notes/./thesis.md").hexdigest()[:12]
    assert "n-93378973d8a1" != "n-" + hashlib.sha256(b"notes/thesis.md").hexdigest()[:12]


def test_canvas_generator_quarantines_dangling_edges_instead_of_silent_drop() -> None:
    """Every way an endpoint can miss the node set, in one pass, alongside a hit.

    A one-node/one-edge fixture proves nothing about which rows survive, which
    are quarantined, or the order they come back in. The third row is the shape
    the raw-path id scheme actually produces: `notes/./thesis.md` and
    `notes/thesis.md` hash differently, so a normalized edge over a raw member
    dangles even though both name the same file.
    """
    canvas, quarantined = knowledge._canvas_from_nodes_edges(
        [{"path": "notes/thesis.md"}, {"path": "notes/support.md"}, {"path": "notes/./raw.md"}],
        [
            {"source": "notes/support.md", "target": "notes/thesis.md", "type": "supports"},
            {"source": "notes/ghost.md", "target": "notes/thesis.md", "type": "supports"},
            {"source": "notes/raw.md", "target": "notes/thesis.md", "type": "extends"},
            {"source": "notes/thesis.md", "target": "notes/ghost.md", "type": "contradicts"},
            {"source": "notes/ghost.md", "target": "notes/phantom.md", "type": "refines"},
        ],
    )

    assert [edge["label"] for edge in canvas["edges"]] == ["supports"]
    assert (
        canvas["edges"][0]["fromNode"]
        == "n-" + hashlib.sha256(b"notes/support.md").hexdigest()[:12]
    )
    assert quarantined == [
        {
            "source": "notes/ghost.md",
            "target": "notes/thesis.md",
            "type": "supports",
            "reason": "edge endpoint is not a canvas node",
        },
        {
            "source": "notes/raw.md",
            "target": "notes/thesis.md",
            "type": "extends",
            "reason": "edge endpoint is not a canvas node",
        },
        {
            "source": "notes/thesis.md",
            "target": "notes/ghost.md",
            "type": "contradicts",
            "reason": "edge endpoint is not a canvas node",
        },
        {
            "source": "notes/ghost.md",
            "target": "notes/phantom.md",
            "type": "refines",
            "reason": "edge endpoint is not a canvas node",
        },
    ]


def test_render_project_argument_canvas_report_is_clean_on_the_analyze_branch(
    tmp_path: Path,
) -> None:
    """The no-outline branch pre-filters, so its report must be an empty list.

    Naming the state that produces `quarantined_edges == []` keeps the default
    from being an untested fallback, and pins that the wrapper still hands back
    a bare canvas.
    """
    _md(
        tmp_path / "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n"
        "description: Project\nthesis: notes/thesis.md\n",
    )
    _md(tmp_path / "notes/thesis.md", "type: note\ncheck_status: checked\ntitle: Thesis\n")
    _md(
        tmp_path / "notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Support\n"
        "links:\n  supports:\n    - notes/thesis.md\n",
    )

    report = knowledge.render_project_argument_canvas_report(tmp_path, "project-alpha")

    assert report["quarantined_edges"] == []
    assert len(report["canvas"]["edges"]) == 1
    assert knowledge.render_project_argument_canvas(tmp_path, "project-alpha") == report["canvas"]


def test_render_project_argument_canvas_report_quarantines_on_the_analyze_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A project with no outline takes the other branch — it must report too.

    The lens pre-filters its own component edges today, so only a stub can
    reach this arm. Without it, dropping the analyze branch's rows on the floor
    is invisible, and that arm is the one every outline-less project takes.
    """
    _md(
        tmp_path / "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n"
        "description: Project\nthesis: notes/thesis.md\n",
    )
    monkeypatch.setattr(
        knowledge,
        "analyze_project_argument",
        lambda _vault, _project: {
            "nodes": [{"path": "notes/thesis.md"}],
            "edges": [
                {"source": "notes/ghost.md", "target": "notes/thesis.md", "type": "supports"}
            ],
        },
    )

    report = knowledge.render_project_argument_canvas_report(tmp_path, "project-alpha")

    assert report["canvas"]["edges"] == []
    assert report["quarantined_edges"] == [
        {
            "source": "notes/ghost.md",
            "target": "notes/thesis.md",
            "type": "supports",
            "reason": "edge endpoint is not a canvas node",
        }
    ]


def _dirty_slice_vault(tmp_path: Path) -> Path:
    vault = workspace(tmp_path)
    _md(
        vault / "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n"
        "description: Project\nthesis: notes/thesis.md\n",
    )
    _md(vault / "notes/thesis.md", "type: note\ncheck_status: checked\ntitle: Thesis\n")
    outline = vault / "projects/project-alpha/outline.md"
    outline.write_text("- 01ARZ3NDEKTSV4RRFFQ69G5FZZ -- Thesis\n", encoding="utf-8")
    return vault


def _slice_with_edges(edges: list[dict[str, str]]):
    def read_slice(_vault: Path, _project: str) -> dict:
        return {
            "project_path": "projects/project-alpha/project.md",
            "outline_path": "projects/project-alpha/outline.md",
            "members": [{"path": "notes/thesis.md"}],
            "edges": edges,
            "missing": [],
        }

    return read_slice


def _canvas_run_event(vault: Path) -> dict:
    journal = (vault / ".memoria/journal/test-machine.jsonl").read_text(encoding="utf-8")
    rows = [json.loads(line) for line in journal.splitlines() if line]
    return next(row for row in rows if row.get("workflow") == "render-project-argument-canvas")


def test_write_project_argument_canvas_journals_quarantined_edges(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = _dirty_slice_vault(tmp_path)
    monkeypatch.setattr(
        knowledge,
        "read_project_slice",
        _slice_with_edges(
            [
                {"source": "notes/ghost.md", "target": "notes/thesis.md", "type": "supports"},
                {"source": "notes/thesis.md", "target": "notes/phantom.md", "type": "extends"},
            ]
        ),
    )

    result = write_project_argument_canvas(vault, "project-alpha", commit=True)

    assert result["quarantined_edge_count"] == 2
    assert result["edge_count"] == 0
    assert _canvas_run_event(vault)["quarantined_edges"] == [
        {
            "source": "notes/ghost.md",
            "target": "notes/thesis.md",
            "type": "supports",
            "reason": "edge endpoint is not a canvas node",
        },
        {
            "source": "notes/thesis.md",
            "target": "notes/phantom.md",
            "type": "extends",
            "reason": "edge endpoint is not a canvas node",
        },
    ]


def test_write_project_argument_canvas_omits_the_quarantine_field_when_clean(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The clean run is the floor seed's own state — it must add no event field.

    Every golden hashes the journal, so a `quarantined_edges: []` emitted here
    would rewrite all 35 of them for a row that says nothing.
    """
    vault = _dirty_slice_vault(tmp_path)
    monkeypatch.setattr(knowledge, "read_project_slice", _slice_with_edges([]))

    result = write_project_argument_canvas(vault, "project-alpha", commit=True)

    assert result["quarantined_edge_count"] == 0
    assert "quarantined_edges" not in _canvas_run_event(vault)
