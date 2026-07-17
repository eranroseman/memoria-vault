"""Export-target acceptance: markdown + bibliography.bib (V2 spec section 5)."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.capture import bibliography_citekeys, render_references_bib
from memoria_vault.runtime.knowledge import compose_project_draft as _compose_project_draft
from memoria_vault.runtime.knowledge import resolve_evidence_review as _resolve_evidence_review
from memoria_vault.runtime.knowledge import verify_project_draft as _verify_project_draft
from memoria_vault.runtime.knowledge import write_project_export as _write_project_export
from tests.helpers import call_with_context, write_checked_concept

_URL_TRIGGER_CITEKEYS = (
    "http://example.test/key",
    "HTTPS://example.test/key",
    "ftp://example.test/key",
    "www.example.test/key",
    "mailto:person",
    "prefix-http://example.test/key",
    "prefix.https://example.test/key",
    "prefix+ftp://example.test/key",
    "prefix-www.example.test/key",
    "prefix.mailto:person",
    "prefix-//example.test/key",
)


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


def _pandoc_citation_ids(markdown: str) -> list[str]:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("Pandoc is optional")
    parsed = subprocess.run(
        [pandoc, "--from=markdown", "--to=json"],
        input=markdown,
        text=True,
        capture_output=True,
        check=False,
    )
    assert parsed.returncode == 0, parsed.stderr
    citation_ids: list[str] = []

    def visit(value: object) -> None:
        if isinstance(value, dict):
            if value.get("t") == "Cite":
                citation_ids.extend(str(citation["citationId"]) for citation in value["c"][0])
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(json.loads(parsed.stdout))
    return citation_ids


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


@pytest.mark.parametrize(
    ("opening", "closing"),
    [("```text", "```"), ("~~~text", "~~~")],
)
def test_draft_export_ignores_recognized_fenced_marker_outside_direct_claims(
    tmp_path: Path, opening: str, closing: str
) -> None:
    vault = tmp_path
    _catalog_source(vault, "source-alpha", citekey="safe2026")
    _catalog_source(vault, "source-literal", doi="10.1000/literal")
    _source_backed_draft(vault)
    draft_path = vault / "projects/project-alpha/draft.md"
    draft_path.write_text(
        draft_path.read_text(encoding="utf-8").rstrip()
        + f"\n\n{opening}\nliteral %%ev: ev-12345678 items=source-literal#^p0001%%\n{closing}\n",
        encoding="utf-8",
    )

    verification = verify_project_draft(vault, "project-alpha")
    assert verification["ready"] is True
    exported = write_project_export(vault, "project-alpha", draft=True)

    assert "[@safe2026]" in exported["content"]
    assert "literal %%ev: ev-12345678 items=source-literal#^p0001%%" in exported["content"]


@pytest.mark.parametrize("invalid_fence", ["~~~bogus header ???", "```bad`info"])
def test_draft_export_refuses_direct_marker_after_invalid_code_fence(
    tmp_path: Path, invalid_fence: str
) -> None:
    vault = tmp_path
    _catalog_source(vault, "source-alpha", citekey="safe2026")
    _catalog_source(vault, "source-hidden", doi="10.1000/hidden")
    _source_backed_draft(vault)
    draft_path = vault / "projects/project-alpha/draft.md"
    draft_path.write_text(
        draft_path.read_text(encoding="utf-8").rstrip()
        + "\n\nPrior prose\n"
        + f"{invalid_fence}\n"
        + "Claim %%ev: ev-87654321 items=source-hidden#^p0001%%\n",
        encoding="utf-8",
    )

    verification = verify_project_draft(vault, "project-alpha")
    assert verification["ready"] is False
    assert verification["missing"] == ["evidence-text-unbound:ev-87654321"]
    with pytest.raises(ValueError, match="evidence-text-unbound:ev-87654321"):
        write_project_export(vault, "project-alpha", draft=True)


@pytest.mark.parametrize(
    "hidden_control",
    [
        "<!-- %%ev: ev-87654321 items=source-hidden#^p0001%% -->",
        "`%%ev: ev-87654321 items=source-hidden#^p0001%%`",
    ],
)
def test_draft_export_only_cites_direct_evidence_markers(
    tmp_path: Path, hidden_control: str
) -> None:
    vault = tmp_path
    hidden_marker = "%%ev: ev-87654321 items=source-hidden#^p0001%%"
    _catalog_source(vault, "source-alpha", citekey="safe2026")
    _catalog_source(vault, "source-hidden", citekey="hidden2026")
    _source_backed_draft(vault)
    draft_path = vault / "projects/project-alpha/draft.md"
    draft_path.write_text(
        draft_path.read_text(encoding="utf-8").rstrip() + f"\n\n{hidden_control}\n",
        encoding="utf-8",
    )

    assert verify_project_draft(vault, "project-alpha")["ready"] is True
    exported = write_project_export(vault, "project-alpha", draft=True)

    assert hidden_marker in exported["content"]
    assert "[@safe2026]" in exported["content"]
    assert "[@hidden2026]" not in exported["content"]
    assert _pandoc_citation_ids(exported["content"]) == ["safe2026"]


@pytest.mark.parametrize(
    "citekey",
    ["foo,bar", "foo;bar", "foo]bar", "unsafe\n```bibtex", "unsafe`key"],
)
def test_draft_export_refuses_referenced_unsafe_citekey(tmp_path: Path, citekey: str) -> None:
    vault = tmp_path
    _catalog_source(vault, "source-alpha", citekey=citekey)
    _source_backed_draft(vault)
    verify_project_draft(vault, "project-alpha")

    with pytest.raises(ValueError, match="unresolved-citation:source-alpha"):
        write_project_export(vault, "project-alpha", draft=True)


@pytest.mark.parametrize("citekey", _URL_TRIGGER_CITEKEYS)
def test_draft_export_refuses_referenced_url_trigger_citekey(tmp_path: Path, citekey: str) -> None:
    vault = tmp_path
    _catalog_source(vault, "source-alpha", citekey=citekey)
    _source_backed_draft(vault)
    verify_project_draft(vault, "project-alpha")

    assert render_references_bib(vault) == ""
    assert bibliography_citekeys(vault) == {}
    with pytest.raises(ValueError, match="unresolved-citation:source-alpha"):
        write_project_export(vault, "project-alpha", draft=True)


@pytest.mark.parametrize("citekey", ["alpha-", "alpha.", "alpha/", "alpha+", "alpha:"])
def test_draft_export_refuses_referenced_terminal_punctuation_citekey(
    tmp_path: Path, citekey: str
) -> None:
    vault = tmp_path
    _catalog_source(vault, "source-alpha", citekey=citekey)
    _source_backed_draft(vault)
    verify_project_draft(vault, "project-alpha")

    assert render_references_bib(vault) == ""
    with pytest.raises(ValueError, match="unresolved-citation:source-alpha"):
        write_project_export(vault, "project-alpha", draft=True)


@pytest.mark.parametrize(
    "citekey",
    [
        "foo::bar",
        "a::b",
        "a:+b",
        "a:-b",
        "a:.b",
        "a./b",
        "a/+b",
        "a-:b",
        "a.:b",
        "a++b",
        "a--b",
        "a..b",
    ],
)
def test_draft_export_refuses_referenced_citekey_with_pandoc_punctuation_continuation(
    tmp_path: Path, citekey: str
) -> None:
    vault = tmp_path
    _catalog_source(vault, "source-alpha", citekey=citekey)
    _source_backed_draft(vault)
    verify_project_draft(vault, "project-alpha")

    assert render_references_bib(vault) == ""
    assert bibliography_citekeys(vault) == {}
    with pytest.raises(ValueError, match="unresolved-citation:source-alpha"):
        write_project_export(vault, "project-alpha", draft=True)


def test_draft_export_uses_csl_id_when_explicit_citekey_is_whitespace(tmp_path: Path) -> None:
    vault = tmp_path
    _catalog_source(vault, "source-alpha", citekey=" \t ", csl_json={"id": "fallback2026"})
    _source_backed_draft(vault)
    verify_project_draft(vault, "project-alpha")

    exported = write_project_export(vault, "project-alpha", draft=True)

    assert "[@fallback2026]" in exported["content"]
    assert "@article{fallback2026," in _fence(exported["content"])


@pytest.mark.parametrize(
    "citekey",
    ["alpha_", "a:b:c", "a.b_c-d:e+f/g", "doi:10.1000/key", "smith:2026"],
)
def test_draft_export_preserves_pandoc_safe_citekey(tmp_path: Path, citekey: str) -> None:
    vault = tmp_path
    _catalog_source(vault, "source-alpha", citekey=citekey)
    _source_backed_draft(vault)
    verify_project_draft(vault, "project-alpha")

    exported = write_project_export(vault, "project-alpha", draft=True)

    assert f"[@{citekey}]" in exported["content"]
    assert f"@article{{{citekey}," in _fence(exported["content"])
    assert _pandoc_citation_ids(exported["content"]) == [citekey]


def test_draft_export_refuses_referenced_duplicate_citekey(tmp_path: Path) -> None:
    vault = tmp_path
    _catalog_source(vault, "source-alpha", citekey="shared2026")
    _catalog_source(vault, "source-beta", citekey="shared2026")
    _source_backed_draft(vault)
    verify_project_draft(vault, "project-alpha")

    with pytest.raises(ValueError, match="unresolved-citation:source-alpha"):
        write_project_export(vault, "project-alpha", draft=True)


def test_draft_export_omits_unrelated_url_trigger_citekey_from_inlined_fence(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    _catalog_source(vault, "source-alpha", citekey="safe2026")
    _catalog_source(vault, "source-url", citekey="prefix-http://example.test/key")
    _source_backed_draft(vault)
    verify_project_draft(vault, "project-alpha")

    exported = write_project_export(vault, "project-alpha", draft=True)

    assert "[@safe2026]" in exported["content"]
    assert "@article{safe2026," in _fence(exported["content"])
    assert "prefix-http://example.test/key" not in exported["content"]
    assert len(re.findall(r"(?m)^```", exported["content"])) == 2


@pytest.mark.parametrize("fence", ["```", "~~~", "````"])
def test_draft_export_refuses_unterminated_body_code_fence(tmp_path: Path, fence: str) -> None:
    vault = tmp_path
    _catalog_source(vault, "source-alpha", citekey="safe2026")
    _source_backed_draft(vault)
    draft_path = vault / "projects/project-alpha/draft.md"
    draft_path.write_text(draft_path.read_text(encoding="utf-8").rstrip() + f"\n\n{fence}\n")

    with pytest.raises(ValueError, match="unterminated-code-fence"):
        write_project_export(vault, "project-alpha", draft=True)


def test_draft_export_refuses_fence_created_by_rendered_body_trimming(tmp_path: Path) -> None:
    vault = tmp_path
    _catalog_source(vault, "source-alpha", citekey="safe2026")
    _source_backed_draft(vault)
    draft_path = vault / "projects/project-alpha/draft.md"
    draft_path.write_text(
        draft_path.read_text(encoding="utf-8").replace("\n---\n\n", "\n---\n\n    ```\n", 1),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unterminated-code-fence"):
        write_project_export(vault, "project-alpha", draft=True)


def test_draft_export_refuses_fence_exposed_by_anchor_removal_and_unicode_trim(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    _catalog_source(vault, "source-alpha", citekey="safe2026")
    _source_backed_draft(vault)
    draft_path = vault / "projects/project-alpha/draft.md"
    draft_path.write_text(
        draft_path.read_text(encoding="utf-8").replace(
            "\n---\n\n", "\n---\n\n\N{NO-BREAK SPACE} ^blk-rendered-away\n    ```\n", 1
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unterminated-code-fence"):
        write_project_export(vault, "project-alpha", draft=True)


def test_draft_export_inlined_bibtex_escapes_backslashes_for_pandoc(tmp_path: Path) -> None:
    vault = tmp_path
    title = r"C:\temp #1 is 100% of $5; literal \% and \$; trailing " + "\\"
    _catalog_source(
        vault,
        "source-alpha",
        citekey="slash2026",
        title=title,
    )
    _source_backed_draft(vault)
    verify_project_draft(vault, "project-alpha")

    bibtex = _fence(write_project_export(vault, "project-alpha", draft=True)["content"])

    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("Pandoc is optional")
    parsed = subprocess.run(
        [pandoc, "--from=bibtex", "--to=csljson"],
        input=bibtex,
        text=True,
        capture_output=True,
        check=False,
    )
    assert parsed.returncode == 0, parsed.stderr
    assert json.loads(parsed.stdout)[0]["title"] == title


def test_draft_export_inlined_bibtex_preserves_percent_and_dollar_metadata(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    title = "100% success costs $5"
    _catalog_source(vault, "source-alpha", citekey="percent2026", title=title)
    _source_backed_draft(vault)
    verify_project_draft(vault, "project-alpha")

    bibtex = _fence(write_project_export(vault, "project-alpha", draft=True)["content"])

    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("Pandoc is optional")
    parsed = subprocess.run(
        [pandoc, "--from=bibtex", "--to=csljson"],
        input=bibtex,
        text=True,
        capture_output=True,
        check=False,
    )
    assert parsed.returncode == 0, parsed.stderr
    assert json.loads(parsed.stdout)[0]["title"] == title
