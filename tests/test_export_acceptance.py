"""Export-target acceptance: markdown + bibliography.bib (V2 spec section 5)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.knowledge import compose_project_draft as _compose_project_draft
from memoria_vault.runtime.knowledge import resolve_evidence_review as _resolve_evidence_review
from memoria_vault.runtime.knowledge import verify_project_draft as _verify_project_draft
from memoria_vault.runtime.knowledge import write_project_export as _write_project_export
from tests.helpers import call_with_context, write_checked_concept


def compose_project_draft(vault: Path, *args, **kwargs):
    return call_with_context(_compose_project_draft, vault, *args, **kwargs)


def verify_project_draft(vault: Path, *args, **kwargs):
    return call_with_context(_verify_project_draft, vault, *args, **kwargs)


def write_project_export(vault: Path, *args, **kwargs):
    return call_with_context(_write_project_export, vault, *args, **kwargs)


def resolve_evidence_review(vault: Path, *args, **kwargs):
    kwargs.setdefault("actor", "pi")
    kwargs.setdefault("machine", "test-machine")
    return _resolve_evidence_review(vault, *args, **kwargs)


def _project(vault: Path) -> None:
    write_checked_concept(
        vault,
        "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n",
        "project",
    )


def _outline(vault: Path, content: str) -> None:
    path = vault / "projects/project-alpha/outline.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _source_span(vault: Path, work_id: str) -> None:
    path = vault / f".memoria/blobs/source-content/{work_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{work_id} source span. ^p0001\n", encoding="utf-8")


def _catalog_source(vault: Path, work_id: str, **kwargs) -> None:
    state.upsert_catalog_record(
        vault,
        work_id=work_id,
        title=kwargs.pop("title", f"{work_id} source"),
        check_status="checked",
        content_path=f".memoria/blobs/source-content/{work_id}.md",
        **kwargs,
    )
    _source_span(vault, work_id)


def _source_backed_draft(vault: Path) -> None:
    _project(vault)
    write_checked_concept(
        vault,
        "notes/support.md",
        "type: note\ncheck_status: checked\ntitle: Support\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FA2\nwork_id: catalog/sources/source-alpha\n",
        "note",
        body="This source-backed claim can be exported.",
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA2 — Support\n")
    compose_project_draft(vault, "project-alpha")


def _fence(content: str) -> str:
    match = re.search(r"```bibtex\n(?P<bib>.*?)\n```", content, re.S)
    assert match is not None, "exported artifact carries no inlined bibtex fence"
    return match.group("bib")


def test_markdown_draft_export_citations_resolve_against_inlined_fence(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    _catalog_source(vault, "source-alpha", citekey="smith2020")
    _source_backed_draft(vault)
    verify_project_draft(vault, "project-alpha")

    exported = write_project_export(vault, "project-alpha", draft=True)

    content = exported["content"]
    body, _, references = content.partition("## References")
    assert references, "draft export must inline the References fence"
    used = set(re.findall(r"\[@([^;\]\s]+)", body))
    fence_keys = {
        match.group(1).strip() for match in re.finditer(r"(?m)^@\w+\{([^,]+),", _fence(content))
    }
    assert used == {"smith2020"}
    assert used <= fence_keys


def test_draft_export_refuses_unresolved_citation_naming_the_finding(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    # DOI-bearing, citekey-less: in the catalog but absent from the
    # bibliography projection — shipped behavior silently drops its citation.
    _catalog_source(vault, "source-alpha", doi="10.1000/alpha")
    _source_backed_draft(vault)
    verify_project_draft(vault, "project-alpha")

    with pytest.raises(ValueError, match="unresolved-citation:source-alpha"):
        write_project_export(vault, "project-alpha", draft=True)
