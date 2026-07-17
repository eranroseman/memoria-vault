"""Export-target acceptance: markdown + bibliography.bib (V2 spec section 5)."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.capture import (
    bibliography_citekeys,
    parse_bibtex_entry,
    render_references_bib,
    write_references_bib_explicit,
)
from memoria_vault.runtime.content_security import neutralize_untrusted_markdown
from memoria_vault.runtime.knowledge import _draft_unresolved_raw_citations
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


def _pandoc_code_block_texts(markdown: str) -> list[str]:
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
    return [
        str(block["c"][1])
        for block in json.loads(parsed.stdout)["blocks"]
        if block["t"] == "CodeBlock"
    ]


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


def test_draft_export_keeps_tilde_fenced_marker_after_heading_non_direct(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    hidden_marker = "%%ev: ev-87654321 items=source-hidden#^p0001%%"
    _catalog_source(vault, "source-alpha", citekey="safe2026")
    _catalog_source(vault, "source-hidden", doi="10.1000/hidden")
    _source_backed_draft(vault)
    draft_path = vault / "projects/project-alpha/draft.md"
    draft_path.write_text(
        draft_path.read_text(encoding="utf-8").rstrip()
        + "\n\n# Context\n~~~text\n"
        + f"Hidden evidence marker. {hidden_marker}\n~~~\n",
        encoding="utf-8",
    )

    assert "ev-87654321" not in {
        marker.evidence_id
        for marker in state.evidence_markers_from_markdown(draft_path.read_text(encoding="utf-8"))
    }
    assert verify_project_draft(vault, "project-alpha")["ready"] is True
    exported = write_project_export(vault, "project-alpha", draft=True)

    assert hidden_marker in exported["content"]
    assert "[@safe2026]" in exported["content"]
    assert any(hidden_marker in block for block in _pandoc_code_block_texts(exported["content"]))
    assert _pandoc_citation_ids(exported["content"]) == ["safe2026"]


def test_draft_export_refuses_tilde_marker_after_paragraph_prose(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    hidden_marker = "%%ev: ev-87654321 items=source-hidden#^p0001%%"
    _catalog_source(vault, "source-alpha", citekey="safe2026")
    _catalog_source(vault, "source-hidden", doi="10.1000/hidden")
    _source_backed_draft(vault)
    draft_path = vault / "projects/project-alpha/draft.md"
    fragment = f"Prior prose\n~~~text\nClaim {hidden_marker}\n~~~\n"
    draft_path.write_text(
        draft_path.read_text(encoding="utf-8").rstrip() + "\n\n" + fragment,
        encoding="utf-8",
    )

    assert _pandoc_code_block_texts(fragment) == []
    assert "ev-87654321" in {
        marker.evidence_id
        for marker in state.evidence_markers_from_markdown(draft_path.read_text(encoding="utf-8"))
    }
    verification = verify_project_draft(vault, "project-alpha")
    assert verification["ready"] is False
    assert verification["missing"] == ["evidence-text-unbound:ev-87654321"]
    with pytest.raises(ValueError, match="evidence-text-unbound:ev-87654321"):
        write_project_export(vault, "project-alpha", draft=True)


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
    "prefix",
    [
        "~~~foo ^blk-opener\n",
        "Heading\n--- ^blk-opener\n~~~text\n",
    ],
)
def test_draft_export_preserves_non_direct_anchors_that_prevent_fence_synthesis(
    tmp_path: Path, prefix: str
) -> None:
    vault = tmp_path
    marker = "%%ev: ev-87654321 items=source-alpha#^p0001%%"
    _catalog_source(vault, "source-alpha", citekey="safe2026")
    _source_backed_draft(vault)
    draft_path = vault / "projects/project-alpha/draft.md"
    draft_path.write_text(
        draft_path.read_text(encoding="utf-8").rstrip()
        + f"\n\n{prefix}Claim ^blk-87654321 {marker}\n~~~\n",
        encoding="utf-8",
    )

    assert verify_project_draft(vault, "project-alpha")["ready"] is True
    exported = write_project_export(vault, "project-alpha", draft=True)["content"]

    assert "^blk-opener" in exported
    assert "^blk-87654321" not in exported
    assert _pandoc_citation_ids(exported).count("safe2026") == 2
    assert not any("[@safe2026]" in block for block in _pandoc_code_block_texts(exported))


@pytest.mark.parametrize(
    ("raw_citation", "missing_ids"),
    [
        ("Author supplied [@not-in-fence].", ["not-in-fence"]),
        ("<!-- [@not-in-fence] -->", ["not-in-fence"]),
        (
            "Author supplied [see @not-in-fence; -@also-missing, p. 3] and @bare-missing.",
            ["also-missing", "bare-missing", "not-in-fence"],
        ),
        (
            "> - ```text\n> - [@not-in-fence]\n> ```",
            ["not-in-fence"],
        ),
        (
            "> - ```text\nplain [@not-in-fence]\n> - ```",
            ["not-in-fence"],
        ),
    ],
)
def test_draft_export_refuses_raw_citations_outside_the_bibliography_projection(
    tmp_path: Path, raw_citation: str, missing_ids: list[str]
) -> None:
    vault = tmp_path
    _catalog_source(vault, "source-alpha", citekey="safe2026")
    _source_backed_draft(vault)
    draft_path = vault / "projects/project-alpha/draft.md"
    draft_path.write_text(
        draft_path.read_text(encoding="utf-8").rstrip() + f"\n\n{raw_citation}\n",
        encoding="utf-8",
    )

    assert verify_project_draft(vault, "project-alpha")["ready"] is True
    with pytest.raises(ValueError) as error:
        write_project_export(vault, "project-alpha", draft=True)

    assert str(error.value) == "project draft is not export-ready: " + ", ".join(
        f"unresolved-citation:{citekey}" for citekey in missing_ids
    )


def test_raw_citation_membership_scan_keeps_normalized_inline_html_visible() -> None:
    content = neutralize_untrusted_markdown("<span>[@not-in-fence]</span>\n")

    assert _pandoc_citation_ids(content) == ["not-in-fence"]
    assert _draft_unresolved_raw_citations(content, {"safe2026"}) == ["not-in-fence"]


def test_raw_citation_membership_refuses_ambiguous_pandoc_table_citations() -> None:
    content = "a b\n-- --\n```\n[@evil]\n```\n"

    assert _pandoc_citation_ids(content) == ["e"]
    assert _draft_unresolved_raw_citations(content, {"evil"}) == ["ambiguous-markdown-table"]


@pytest.mark.parametrize(
    "content",
    [
        "> a b\n> -- --\n> ~~~text\n> [@evil]\n> ~~~\n",
        ">> a b\n>> -- --\n>> ~~~text\n>> [@evil]\n>> ~~~\n",
        "- a b\n  -- --\n  ~~~text\n  [@evil]\n  ~~~\n",
        "- > a b\n  > -- --\n  > ~~~text\n  > [@evil]\n  > ~~~\n",
        "> - a b\n>   -- --\n>   ~~~text\n>   [@evil]\n>   ~~~\n",
    ],
)
def test_raw_citation_membership_refuses_ambiguous_container_table_citations(
    content: str,
) -> None:
    assert _pandoc_citation_ids(content) == ["e"]
    assert _draft_unresolved_raw_citations(content, {"evil"}) == ["ambiguous-markdown-table"]


@pytest.mark.parametrize(
    ("suffix", "expected_id"),
    [
        ("//", "safe2026/"),
        ("//not", "safe2026//not"),
        (":/", "safe2026:"),
        ("://", "safe2026:/"),
        ("~not", "safe2026~not"),
        ("?not", "safe2026?not"),
        ("#not", "safe2026#not"),
        ("$not", "safe2026$not"),
        ("%not", "safe2026%not"),
        ("&not", "safe2026&not"),
        ("<not>", "safe2026&lt"),
        (".not", "safe2026.not"),
        (":not", "safe2026:not"),
        ("+not", "safe2026+not"),
        ("-not", "safe2026-not"),
    ],
)
def test_raw_citation_membership_does_not_prefix_match_pandoc_ids(
    suffix: str, expected_id: str
) -> None:
    content = neutralize_untrusted_markdown(f"[@safe2026{suffix}]\n")

    assert _pandoc_citation_ids(content) == [expected_id]
    assert _draft_unresolved_raw_citations(content, {"safe2026"}) == [expected_id]


def test_raw_citation_membership_splits_adjacent_pandoc_citations() -> None:
    content = neutralize_untrusted_markdown("[@safe2026@not-in-fence]\n")

    assert _pandoc_citation_ids(content) == ["safe2026", "not-in-fence"]
    assert _draft_unresolved_raw_citations(content, {"safe2026"}) == ["not-in-fence"]
    assert _draft_unresolved_raw_citations(content, {"safe2026", "not-in-fence"}) == []


def test_raw_citation_membership_accepts_pandoc_star_prefixed_ids() -> None:
    content = neutralize_untrusted_markdown("[@*not-in-fence]\n")

    assert _pandoc_citation_ids(content) == ["*not-in-fence"]
    assert _draft_unresolved_raw_citations(content, set()) == ["*not-in-fence"]


def test_raw_citation_membership_respects_unicode_word_boundaries() -> None:
    content = neutralize_untrusted_markdown("\N{LATIN SMALL LETTER E WITH ACUTE}@safe2026\n")

    assert _pandoc_citation_ids(content) == []
    assert _draft_unresolved_raw_citations(content, set()) == []


@pytest.mark.parametrize(
    ("content", "citation_ids"),
    [
        ("/@not-in-fence\n", ["not-in-fence"]),
        ("foo/@not-in-fence\n", ["not-in-fence"]),
        ("foo:@not-in-fence\n", ["not-in-fence"]),
        ("_@not-in-fence\n", ["not-in-fence"]),
        ("!@not-in-fence\n", ["not-in-fence"]),
        ("-@not-in-fence\n", ["not-in-fence"]),
        ("@@not-in-fence\n", ["not-in-fence"]),
        ("\\@not-in-fence\n", []),
        ("\\\\@not-in-fence\n", ["not-in-fence"]),
        (".@not-in-fence\n", []),
        ("\N{LATIN SMALL LETTER E WITH ACUTE}@not-in-fence\n", []),
    ],
)
def test_raw_citation_membership_matches_pandoc_left_boundaries(
    content: str, citation_ids: list[str]
) -> None:
    assert _pandoc_citation_ids(content) == citation_ids
    expected = ["not-in-fence"] if citation_ids else []
    assert _draft_unresolved_raw_citations(content, set()) == expected


@pytest.mark.parametrize(
    "suffix",
    [
        ".",
        ",",
        ";",
        ":",
        "!",
        "?",
        "#",
        "%",
        "&",
        "+",
        "-",
        "~",
        "<",
        ">",
        "$",
        "/",
        "*",
        "./",
        "/.",
        "!?/",
        "/!?",
        ".//",
        "~//",
        "-//",
        "&//",
        "/./",
    ],
)
def test_raw_citation_membership_keeps_pandoc_terminal_punctuation_valid(suffix: str) -> None:
    content = neutralize_untrusted_markdown(f"[@safe2026{suffix}]\n")

    assert _pandoc_citation_ids(content) == ["safe2026"]
    assert _draft_unresolved_raw_citations(content, {"safe2026"}) == []


@pytest.mark.parametrize(
    ("content", "unresolved"),
    [
        ("`x\n\n[@evil]\ny`\n", ["evil"]),
        ("`\n---\n[@evil]\n`\n", ["evil"]),
        ("`x\n---\n[@evil]\ny`\n", ["evil"]),
        ("`x\n-\n[@evil]\ny`\n", ["evil"]),
        ("`x\n--\n[@evil]\ny`\n", ["evil"]),
        ("`x\n-----  -----\n[@evil]\ny`\n", ["ambiguous-markdown-table"]),
        ("`x\n: definition\n[@evil]\ny`\n", ["evil"]),
        ("`x\n~ definition\n[@evil]\ny`\n", ["evil"]),
        ("``\n[@evil]\n\n``\n", ["evil"]),
        ("> - ```text\n> - [@evil]\n```\n", ["evil"]),
        ("- ```text\n- [@evil]\n```\n", ["evil"]),
        ("> - ```text\n> - [@evil]\n> ```\n", ["evil"]),
        ("> - ```foo}bar\n> - [@evil]\n> ```\n", ["evil"]),
        ("- > ```text\n  - > [@evil]\n  > ```\n", ["evil"]),
        ("- > ```foo}bar\n  - > [@evil]\n  > ```\n", ["evil"]),
        ("> - ```text\n[@evil]\n> - ```\n", ["evil"]),
        ("> - ```text\nplain [@evil]\n> - ```\n", ["evil"]),
        ("- > ```text\n[@evil]\n- > ```\n", ["evil"]),
        ("- > ```text\nplain [@evil]\n- > ```\n", ["evil"]),
    ],
)
def test_raw_citation_membership_does_not_mask_ambiguous_multiline_code_spans(
    content: str,
    unresolved: list[str],
) -> None:
    normalized = neutralize_untrusted_markdown(content)

    assert _pandoc_citation_ids(normalized) == ["evil"]
    assert _draft_unresolved_raw_citations(normalized, {"safe2026"}) == unresolved


def test_raw_citation_membership_masks_definite_multiline_code_span() -> None:
    normalized = neutralize_untrusted_markdown("`x\n[@evil]\ny`\n")

    assert _pandoc_citation_ids(normalized) == []
    assert _draft_unresolved_raw_citations(normalized, {"safe2026"}) == []


def test_raw_citation_membership_masks_multiline_code_span_after_opening_line_break() -> None:
    normalized = neutralize_untrusted_markdown("`\n[@evil]\n`\n")

    assert _pandoc_citation_ids(normalized) == []
    assert _draft_unresolved_raw_citations(normalized, {"safe2026"}) == []


@pytest.mark.parametrize("raw", ["@?", "@.", "@#", "@/", "@%", "@:", "@-", "@<>"])
def test_raw_citation_membership_ignores_non_citation_token_starters(raw: str) -> None:
    content = neutralize_untrusted_markdown(f"{raw}\n")

    assert _pandoc_citation_ids(content) == []
    assert _draft_unresolved_raw_citations(content, set()) == []


@pytest.mark.parametrize(
    "content",
    [
        "> ~~~text\n> code\n~~~\n[@not-in-fence]\n",
        "- ~~~text\n  code\n~~~\n[@not-in-fence]\n",
        "> ~~~text\n> code\n\n~~~\n[@not-in-fence]\n",
        "- ~~~text\n  code\n\n~~~\n[@not-in-fence]\n",
        "> ~~~text\n> code\n\nvisible [@not-in-fence]\n~~~\n",
        "- ~~~text\n  code\n\nvisible [@not-in-fence]\n~~~\n",
        "~~~\n> ~~~text\n> code\n~~~\n[@not-in-fence]\n",
        "> ~~~foo=bar\n> [@not-in-fence]\n>> ~~~\n",
        "> prose\n> ~~~foo=bar\n> [@not-in-fence]\n> ~~~\n",
        "> ---\n>> prose\n> ~~~text\n> [@not-in-fence]\n> ~~~\n",
        "> prose\n> # heading\n> ~~~foo=bar\n> [@not-in-fence]\n> ~~~\n",
        "> prose\n>> # heading\n>> ~~~foo=bar\n>> [@not-in-fence]\n>> ~~~\n",
        "> prose\n>>\n>> ~~~foo=bar\n>> [@not-in-fence]\n>> ~~~\n",
        "plain prose\n> # heading\n> ~~~foo=bar\n> [@not-in-fence]\n> ~~~\n",
        "plain prose\n# heading\n> ~~~foo=bar\n> [@not-in-fence]\n> ~~~\n",
        "plain prose\n# heading\n    [@not-in-fence]\n",
        "# heading\n```foo}bar\n[@not-in-fence]\n````\n",
        "plain prose\n# heading\n~~~text\n[@not-in-fence]\n~~~~\n",
        "> # heading\noutside prose\n> ~~~foo=bar\n> [@not-in-fence]\n> ~~~\n",
        "- item\n> ~~~foo=bar\n> [@not-in-fence]\n> ~~~\n",
        "- item\n> # heading\n> ~~~foo=bar\n> [@not-in-fence]\n> ~~~\n",
        "1. item\n# heading\n    [@not-in-fence]\n",
        "- item\n\n    [@not-in-fence]\n",
        "Term\n: definition\n\n    [@not-in-fence]\n",
        "-\t ~~~text\n    [@not-in-fence]\n    ~~~\n",
        "- ~~~text\n\t\t[@not-in-fence]\n\t\t~~~\n",
        "outer prose\n- ~~~foo=bar\n  [@not-in-fence]\n  ~~~\n",
        "outer prose\n- prose\n- ~~~foo=bar\n  [@not-in-fence]\n  ~~~\n",
        "outer prose\n# Heading\n- prose\n- ~~~foo=bar\n  [@not-in-fence]\n  ~~~\n",
        "* * *\n  continuation\n- ~~~foo=bar\n  [@not-in-fence]\n  ~~~\n",
        "> ~~~bogus header ???\n> [@not-in-fence]\n> ~~~\n",
        "- ~~~bogus header ???\n  [@not-in-fence]\n  ~~~\n",
        "> ~~~foo}bar\n> [@not-in-fence]\n> ~~~\n",
        "- ~~~foo}bar\n  [@not-in-fence]\n  ~~~\n",
        "outer prose\n> - ~~~foo=bar\n>   [@not-in-fence]\n>   ~~~\n",
        "> prose\n> - ~~~foo=bar\n>   [@not-in-fence]\n>   ~~~\n",
        "> - ~~~foo=bar\n>   [@not-in-fence]\n>> ~~~\n",
        "> - ~~~bogus header ???\n>   [@not-in-fence]\n>   ~~~\n",
        "outer prose\n- > ~~~foo=bar\n  > [@not-in-fence]\n  > ~~~\n",
        "- > ~~~bogus header ???\n  > [@not-in-fence]\n  > ~~~\n",
        "- > ~~~foo=bar\n  > [@not-in-fence]\n  >> ~~~\n",
    ],
)
def test_raw_citation_membership_unmasks_after_container_fence_bare_closer(
    content: str,
) -> None:
    assert _pandoc_citation_ids(content) == ["not-in-fence"]
    assert _draft_unresolved_raw_citations(content, {"safe2026"}) == ["not-in-fence"]


@pytest.mark.parametrize(
    "content",
    [
        "Prose\n    [@not-in-fence]\n",
        "- Prose\n    [@not-in-fence]\n",
    ],
)
def test_raw_citation_membership_does_not_mask_indented_paragraph_continuations(
    content: str,
) -> None:
    assert _pandoc_citation_ids(content) == ["not-in-fence"]
    assert _draft_unresolved_raw_citations(content, {"safe2026"}) == ["not-in-fence"]


def test_draft_export_allows_raw_projection_citations_with_multiple_ids(tmp_path: Path) -> None:
    vault = tmp_path
    _catalog_source(vault, "source-alpha", citekey="safe2026")
    _catalog_source(vault, "source-beta", citekey="beta2026")
    _source_backed_draft(vault)
    draft_path = vault / "projects/project-alpha/draft.md"
    draft_path.write_text(
        draft_path.read_text(encoding="utf-8").rstrip()
        + "\n\nAuthor supplied [see @safe2026; -@beta2026, p. 3].\n",
        encoding="utf-8",
    )

    assert verify_project_draft(vault, "project-alpha")["ready"] is True
    exported = write_project_export(vault, "project-alpha", draft=True)["content"]

    assert _pandoc_citation_ids(exported) == ["safe2026", "safe2026", "beta2026"]


def test_raw_citation_table_guard_excludes_generated_bibliography() -> None:
    body = neutralize_untrusted_markdown("a b\n-- --\nx y\n\n")
    content = body + "## References\n\n```bibtex\n@article{safe2026,\n}\n```\n"

    assert (
        _draft_unresolved_raw_citations(
            content,
            {"safe2026"},
            table_ambiguity_content=body,
        )
        == []
    )


@pytest.mark.parametrize(
    "literal",
    [
        "`[@not-in-fence]`",
        "```text\n[@not-in-fence]\n```",
        "# Heading\n```text\n[@not-in-fence]\n```",
        "> ~~~text\n> [@not-in-fence]\n> ~~~",
        "- ~~~text\n  [@not-in-fence]\n  ~~~",
        '> ~~~foo="bar"\n> [@not-in-fence]\n> ~~~',
        '- ~~~foo="bar"\n  [@not-in-fence]\n  ~~~',
        "> # Heading\n> ~~~foo=bar\n> [@not-in-fence]\n> ~~~",
        "> prose\n> ---\n> ~~~foo=bar\n> [@not-in-fence]\n> ~~~",
        "> # Outer heading\n>> # Inner heading\n>> ~~~foo=bar\n>> [@not-in-fence]\n>> ~~~",
        "- item\n\n> # Heading\n> ~~~foo=bar\n> [@not-in-fence]\n> ~~~",
        "> - ~~~foo=bar\n>   [@not-in-fence]\n>   ~~~",
        "> - ~~~foo=bar\n>   [@not-in-fence]\n~~~",
        "- > ~~~foo=bar\n  > [@not-in-fence]\n  > ~~~",
        "- > ~~~foo=bar\n  > [@not-in-fence]\n~~~",
        "- prose\n- ~~~foo=bar\n  [@not-in-fence]\n  ~~~",
        "# Heading\n- prose\n- ~~~foo=bar\n  [@not-in-fence]\n  ~~~",
    ],
)
def test_draft_export_does_not_treat_code_literals_as_raw_citations(
    tmp_path: Path, literal: str
) -> None:
    vault = tmp_path
    _catalog_source(vault, "source-alpha", citekey="safe2026")
    _source_backed_draft(vault)
    draft_path = vault / "projects/project-alpha/draft.md"
    draft_path.write_text(
        draft_path.read_text(encoding="utf-8").rstrip() + f"\n\n{literal}\n",
        encoding="utf-8",
    )

    assert verify_project_draft(vault, "project-alpha")["ready"] is True
    exported = write_project_export(vault, "project-alpha", draft=True)["content"]

    assert _pandoc_citation_ids(exported) == ["safe2026"]


def test_draft_export_refuses_fence_created_after_direct_unicode_anchor_removal(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    _catalog_source(vault, "source-alpha", citekey="safe2026")
    _source_backed_draft(vault)
    draft_path = vault / "projects/project-alpha/draft.md"
    content = draft_path.read_text(encoding="utf-8")
    implicit_marker = "%%ev: ev-deadbeef items=%%"
    draft_path.write_text(
        content.replace(
            "# Alpha project",
            "\N{NO-BREAK SPACE}^blk-deadbeef " + implicit_marker + "~~~\n# Alpha project",
            1,
        ),
        encoding="utf-8",
    )

    verification = verify_project_draft(vault, "project-alpha")
    assert verification["missing"] == [
        "evidence-incomplete:ev-deadbeef",
        "review-required:ev-deadbeef",
    ]
    resolve_evidence_review(vault, "ev-deadbeef", decision="accept", reason="PI accepted")
    assert verify_project_draft(vault, "project-alpha")["ready"] is True

    with pytest.raises(ValueError, match="unterminated-code-fence"):
        write_project_export(vault, "project-alpha", draft=True)


def test_draft_export_removes_direct_anchor_after_unicode_line_separator(tmp_path: Path) -> None:
    vault = tmp_path
    marker = "%%ev: ev-87654321 items=source-alpha#^p0001%%"
    _catalog_source(vault, "source-alpha", citekey="safe2026")
    _source_backed_draft(vault)
    draft_path = vault / "projects/project-alpha/draft.md"
    draft_path.write_text(
        draft_path.read_text(encoding="utf-8").rstrip()
        + "\n\nx\u2028\n\n~~~foo ^blk-opener\n"
        + f"Claim ^blk-87654321 {marker}\n~~~\n",
        encoding="utf-8",
    )

    assert verify_project_draft(vault, "project-alpha")["ready"] is True
    exported = write_project_export(vault, "project-alpha", draft=True)["content"]

    assert "^blk-opener" in exported
    assert "^blk-87654321" not in exported
    assert _pandoc_citation_ids(exported).count("safe2026") == 2
    assert not any("[@safe2026]" in block for block in _pandoc_code_block_texts(exported))


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


def test_draft_export_preserves_non_direct_anchor_that_prevents_unicode_trimmed_fence(
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

    exported = write_project_export(vault, "project-alpha", draft=True)["content"]

    assert "^blk-rendered-away" in exported
    assert "## References" in exported


def test_draft_export_inlined_bibtex_preserves_text_and_identifier_metadata(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    title = r"C:\temp #1 is 100% of $5; literal \% and \$; trailing " + "\\"
    doi = r"10.1000/a\b#c%25$x"
    url = r"https://example.test/a\b#frag%25$z\q"
    _catalog_source(
        vault,
        "source-alpha",
        citekey="slash2026",
        title=title,
        identifiers={"doi": doi},
        csl_json={"URL": url},
        resource=url,
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
    item = json.loads(parsed.stdout)[0]
    assert item["title"] == title
    assert item["DOI"] == doi
    assert item["URL"] == url


def test_draft_export_omits_identifier_metadata_with_trailing_backslash(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    doi = "10.1000/trailing" + "\\"
    url = "https://example.test/trailing" + "\\"
    _catalog_source(
        vault,
        "source-alpha",
        citekey="trailing2026",
        title="Trailing identifier source",
        identifiers={"doi": doi},
        csl_json={"URL": url},
        resource=url,
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
    item = json.loads(parsed.stdout)[0]
    assert item["title"] == "Trailing identifier source"
    assert "DOI" not in item
    assert "URL" not in item


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


def test_draft_export_inlined_bibtex_preserves_display_metadata(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    title = "NASA Study: A_B ~ API"
    journal = "JOURNAL of A_B ~ APIs"
    abstract = "NASA Abstract: A_B ~ API"
    authors = [
        {"family": "Smith", "given": "Ada"},
        {"family": "Jones", "given": "Bob"},
    ]
    _catalog_source(
        vault,
        "source-alpha",
        citekey="display2026",
        csl_json={
            "title": title,
            "container-title": journal,
            "abstract": abstract,
            "author": authors,
            "issued": {"date-parts": [[2026]]},
        },
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
    item = json.loads(parsed.stdout)[0]
    assert item["title"] == title
    assert item["container-title"] == journal
    assert item["abstract"] == abstract
    assert item["author"] == authors


def test_draft_export_inlined_bibtex_round_trips_literal_braces_and_authors(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    title = r"Title \\ {braces} # 100% costs $5 ~"
    journal = r"Journal \\ {braces} # 100% costs $5 ~"
    abstract = r"Abstract \\ {braces} # 100% costs $5 ~"
    authors = [
        {"literal": "OpenAI and Co."},
        {"family": "Smith", "given": "Ada"},
    ]
    _catalog_source(
        vault,
        "source-alpha",
        citekey="literal2026",
        csl_json={
            "title": title,
            "container-title": journal,
            "abstract": abstract,
            "author": authors,
            "issued": {"date-parts": [[2026]]},
        },
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
    item = json.loads(parsed.stdout)[0]
    assert item["title"] == title
    assert item["container-title"] == journal
    assert item["abstract"] == abstract
    assert item["author"] == authors


def test_generated_bibtex_parser_preserves_escaped_literal_braces(tmp_path: Path) -> None:
    vault = tmp_path
    title = "Open { only"
    journal = "Close } only"
    abstract = "Both { and }"
    _catalog_source(
        vault,
        "source-alpha",
        citekey="braces2026",
        csl_json={
            "title": title,
            "container-title": journal,
            "abstract": abstract,
        },
    )

    parsed = parse_bibtex_entry(render_references_bib(vault))

    assert parsed["fields"] == {
        "title": title,
        "journal": journal,
        "abstract": abstract,
    }


def _implicit_draft(vault: Path) -> str:
    _project(vault)
    write_checked_concept(
        vault,
        "notes/thesis.md",
        "type: note\ncheck_status: checked\ntitle: Thesis\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
        "note",
        body="This implicit claim needs review.",
    )
    _outline(vault, "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — Thesis\n")
    composed = compose_project_draft(vault, "project-alpha")
    return composed["evidence_markers"][0]["id"]


def test_blocked_export_names_its_findings(tmp_path: Path) -> None:
    vault = tmp_path
    evidence_id = _implicit_draft(vault)
    verification = verify_project_draft(vault, "project-alpha")

    assert verification["ready"] is False
    with pytest.raises(ValueError) as refusal:
        write_project_export(vault, "project-alpha", draft=True)

    message = str(refusal.value)
    assert "project draft is not export-ready" in message
    assert f"evidence-incomplete:{evidence_id}" in message
    assert f"review-required:{evidence_id}" in message


def test_rejected_disposition_leaves_export_blocked(tmp_path: Path) -> None:
    """Only accept clears holds; rejecting an evidence set keeps export refused."""
    vault = tmp_path
    evidence_id = _implicit_draft(vault)
    verify_project_draft(vault, "project-alpha")

    resolve_evidence_review(vault, evidence_id, decision="reject", reason="unsupported")
    reverified = verify_project_draft(vault, "project-alpha")

    assert reverified["ready"] is False
    with pytest.raises(ValueError, match="project draft is not export-ready"):
        write_project_export(vault, "project-alpha", draft=True)


def test_bibliography_projection_round_trips_through_structural_bibtex_parse(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    state.upsert_catalog_record(
        vault,
        work_id="work-alpha",
        title="Alpha & the {Braced} Title",
        check_status="checked",
        citekey="alpha2020",
        identifiers={"doi": "10.1000/alpha"},
        csl_json={
            "author": [{"family": "Müller", "given": "A."}],
            "issued": {"date-parts": [[2020]]},
            "container-title": "Journal of Tests",
        },
    )
    state.upsert_catalog_record(
        vault,
        work_id="work-beta",
        title="Beta",
        check_status="checked",
        citekey="beta2021",
    )

    write_references_bib_explicit(vault, actor="pi", machine="test-machine")

    text = (vault / "bibliography.bib").read_text(encoding="utf-8")
    chunks = [f"@{chunk}" for chunk in re.split(r"(?m)^@", text) if chunk.strip()]
    entries = [parse_bibtex_entry(chunk) for chunk in chunks]

    citekeys = [entry["citekey"] for entry in entries]
    assert citekeys == ["alpha2020", "beta2021"]
    assert len(set(citekeys)) == len(citekeys), "duplicate citekeys break Zotero import"
    for entry in entries:
        assert entry["entry_type"], "typeless entries break Zotero import"
        assert entry["fields"].get("title"), "titleless entries import as blanks"
    alpha = entries[0]["fields"]
    assert alpha.get("doi") == "10.1000/alpha"
    assert "Müller" in alpha.get("author", "")
    assert alpha.get("year") == "2020"
