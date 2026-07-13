from __future__ import annotations

import re
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.knowledge import compose_project_draft as _compose_project_draft
from memoria_vault.runtime.knowledge import read_project_draft
from tests.helpers import call_with_context, write_checked_concept


def compose_project_draft(vault: Path, *args, **kwargs):
    return call_with_context(_compose_project_draft, vault, *args, **kwargs)


def test_compose_project_draft_writes_markers_and_rebuilds_evidence_sets(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    state.upsert_catalog_record(
        vault,
        work_id="source-alpha",
        title="Alpha Source",
        check_status="checked",
        content_path=".memoria/blobs/source-content/source-alpha.md",
    )
    _source_span(vault, "source-alpha")
    write_checked_concept(
        vault,
        "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\nthesis: notes/thesis.md\n",
        "project",
    )
    write_checked_concept(
        vault,
        "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\nid: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
        "note",
        body="The thesis claim needs human evidence review.",
    )
    write_checked_concept(
        vault,
        "notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Support\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FA2\n"
        "work_id: catalog/sources/source-alpha\n"
        "links:\n  supports:\n    - notes/thesis.md\n",
        "note",
        body="The supporting claim is warranted by the catalog source.",
    )
    outline = vault / "projects/project-alpha/outline.md"
    outline.write_text(
        "- 01ARZ3NDEKTSV4RRFFQ69G5FA2 — Support first\n"
        "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — Thesis second\n",
        encoding="utf-8",
    )

    result = compose_project_draft(vault, "project-alpha", token_budget=400)

    assert result["draft_path"] == "projects/project-alpha/draft.md"
    assert result["member_count"] == 2
    assert result["evidence_set_count"] == 2
    content = (vault / "projects/project-alpha/draft.md").read_text(encoding="utf-8")
    assert "## Support" in content
    assert "Source note: `notes/support.md`" in content
    assert re.search(r"\^blk-[0-9a-f]{8} %%ev: ev-[0-9a-f]{8} ", content)

    rows = {row["id"]: row for row in state.evidence_sets(vault)}
    complete = [row for row in rows.values() if row["items"] == ["source-alpha#^p0001"]]
    implicit = [row for row in rows.values() if not row["items"]]
    assert len(complete) == 1
    assert complete[0]["type"] == "single-span"
    assert complete[0]["state"] == "complete"
    assert complete[0]["review_required"] is False
    assert len(implicit) == 1
    assert implicit[0]["type"] == "implicit"
    assert implicit[0]["state"] == "evidence-incomplete"
    assert implicit[0]["review_required"] is True

    readback = read_project_draft(vault, "project-alpha")
    assert len(readback["evidence_markers"]) == 2
    assert len(readback["evidence_sets"]) == 2


def test_compose_project_draft_requires_outline_members(tmp_path: Path) -> None:
    vault = tmp_path
    write_checked_concept(
        vault,
        "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n",
        "project",
    )

    with pytest.raises(ValueError, match="outline has no checked members"):
        compose_project_draft(vault, "project-alpha")


def _source_span(vault: Path, work_id: str) -> None:
    path = vault / f".memoria/blobs/source-content/{work_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{work_id} source span. ^p0001\n", encoding="utf-8")
