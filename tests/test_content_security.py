"""Content-security regression tests."""

import shutil
import subprocess
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.capture import capture_source as _capture_source
from memoria_vault.runtime.content_security import neutralize_untrusted_markdown
from memoria_vault.runtime.knowledge import (
    _outline_text,
)
from memoria_vault.runtime.knowledge import (
    compose_project_draft as _compose_project_draft,
)
from memoria_vault.runtime.knowledge import curate_note_candidate as _curate_note_candidate
from memoria_vault.runtime.knowledge import emit_note_candidates as _emit_note_candidates
from memoria_vault.runtime.knowledge import (
    render_project_draft_export_markdown as _render_project_draft_export_markdown,
)
from memoria_vault.runtime.knowledge import (
    render_project_export_markdown as _render_project_export_markdown,
)
from memoria_vault.runtime.knowledge import write_project_export as _write_project_export
from memoria_vault.runtime.operations import (
    compile_source_digest as _compile_source_digest,
)
from memoria_vault.runtime.vaultio import read_frontmatter
from tests.helpers import (
    call_with_context,
    copy_memoria_dirs,
    init_git,
    operation_context,
    write_checked_concept,
)


def test_image_embeds_cannot_render() -> None:
    markdown_image = neutralize_untrusted_markdown("![beacon](http://evil.example/x.png)")
    obsidian_embed = neutralize_untrusted_markdown("![[remote.png]]")

    assert "![" not in markdown_image
    assert "![" not in obsidian_embed
    assert "`http://evil.example/x.png`" in markdown_image


def test_raw_html_is_inert() -> None:
    rendered = neutralize_untrusted_markdown(
        '<img src="http://evil.example/x">hi<script>go()</script>'
    )

    assert "<img" not in rendered
    assert "<script" not in rendered
    assert "&lt;img" in rendered
    assert "&lt;script" in rendered
    assert "`http://evil.example/x`" in rendered
    assert "hi" in rendered


def test_multiline_raw_html_is_inert() -> None:
    source = '<img\nsrc="&#x68;ttps://evil.example/beacon.png">\n'

    rendered = neutralize_untrusted_markdown(source)

    assert "<img" not in rendered
    assert "&lt;img\nsrc=" in rendered


def test_links_and_external_urls_are_noninteractive_code_spans() -> None:
    rendered = neutralize_untrusted_markdown(
        "see [here](https://evil.example/x) or //evil.example/y"
    )

    assert "](https://evil.example/x)" not in rendered
    assert "`https://evil.example/x`" in rendered
    assert "`//evil.example/y`" in rendered
    assert "here" in rendered


def test_only_vault_wikilinks_remain_live() -> None:
    rendered = neutralize_untrusted_markdown(
        "See [[notes/claim-1]] and [relative](notes/claim-2.md)."
    )

    assert "[[notes/claim-1]]" in rendered
    assert "](notes/claim-2.md)" not in rendered
    assert "`notes/claim-2.md`" in rendered


def test_entity_obfuscated_shortcut_reference_link_is_inert() -> None:
    source = "[beacon]\n\n[beacon]: &#x68;ttps://evil.example/click\n"

    rendered = neutralize_untrusted_markdown(source)

    assert "\\[beacon]: &#x68;ttps://evil.example/click" in rendered


def test_entity_obfuscated_blockquote_reference_definition_is_inert() -> None:
    source = "> [beacon]\n>\n> [beacon]: &#x68;ttps://evil.example/click\n"

    rendered = neutralize_untrusted_markdown(source)

    assert "> \\[beacon]: &#x68;ttps://evil.example/click" in rendered


def test_entity_obfuscated_multiline_reference_definition_is_inert() -> None:
    source = "[foo bar]\n\n[foo\nbar]: &#x68;ttps://evil.example/click\n"

    rendered = neutralize_untrusted_markdown(source)

    assert "\\[foo\nbar]: &#x68;ttps://evil.example/click" in rendered


def test_reference_definition_with_inline_code_label_is_inert() -> None:
    source = "[foo `bar`]\n\n[foo `bar`]: &#x68;ttps://evil.example/click\n"

    rendered = neutralize_untrusted_markdown(source)

    assert "\\[foo `bar`]: &#x68;ttps://evil.example/click" in rendered


def test_existing_code_spans_and_fences_are_untouched() -> None:
    source = (
        "`http://inline.example` and ``![literal](http://code.example)``\n"
        "```markdown\n![literal](http://fenced.example)\n```\n"
        '~~~html\n<img src="http://tilde.example">\n~~~\n'
    )

    assert neutralize_untrusted_markdown(source) == source


def test_multiline_code_span_is_untouched() -> None:
    source = "`![literal](http://code.example/image.png)\nhttps://code.example/inside`"

    assert neutralize_untrusted_markdown(source) == source


def test_neutralization_is_idempotent() -> None:
    source = "![x](http://evil.example/x) <script>bad()</script>"
    once = neutralize_untrusted_markdown(source)

    assert neutralize_untrusted_markdown(once) == once


def test_escaped_backtick_delimiters_are_inert_through_export_boundaries(
    tmp_path: Path,
) -> None:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("Pandoc is optional")
    payload = r'\` <img src="https://evil.example/x"> \`'
    helper = neutralize_untrusted_markdown(payload)

    write_checked_concept(
        tmp_path,
        "projects/argument/project.md",
        "type: project\ncheck_status: checked\ntitle: Argument project\n",
        "project",
        body=payload,
    )
    argument_rendered = _render_project_export_markdown(tmp_path, "argument")
    argument_written = call_with_context(
        _write_project_export,
        tmp_path,
        "argument",
        machine="argument-export-machine",
    )

    state.upsert_catalog_record(
        tmp_path,
        work_id="source-escaped",
        title="Escaped Source",
        check_status="checked",
        content_path=".memoria/blobs/source-content/source-escaped.md",
    )
    source = tmp_path / ".memoria/blobs/source-content/source-escaped.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("Escaped source span. ^p0001\n", encoding="utf-8")
    write_checked_concept(
        tmp_path,
        "projects/draft/project.md",
        "type: project\ncheck_status: checked\ntitle: Draft project\n",
        "project",
    )
    write_checked_concept(
        tmp_path,
        "notes/escaped.md",
        "type: note\ncheck_status: checked\ntitle: Escaped note\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FA3\n"
        "work_id: catalog/sources/source-escaped\n",
        "note",
        body=payload,
    )
    outline = tmp_path / "projects/draft/outline.md"
    outline.parent.mkdir(parents=True, exist_ok=True)
    outline.write_text("- 01ARZ3NDEKTSV4RRFFQ69G5FA3 — Escaped note\n", encoding="utf-8")
    call_with_context(_compose_project_draft, tmp_path, "draft", machine="draft-machine")
    draft_rendered = call_with_context(
        _render_project_draft_export_markdown,
        tmp_path,
        "draft",
        machine="draft-render-machine",
    )
    draft_written = call_with_context(
        _write_project_export,
        tmp_path,
        "draft",
        draft=True,
        machine="draft-export-machine",
    )

    assert neutralize_untrusted_markdown(helper) == helper
    for markdown in (
        helper,
        argument_rendered["content"],
        argument_written["content"],
        draft_rendered["content"],
        draft_written["content"],
    ):
        rendered = subprocess.run(
            [pandoc, "-f", "commonmark", "-t", "html"],
            input=markdown,
            text=True,
            capture_output=True,
            check=True,
        ).stdout
        assert "<img" not in rendered
        assert 'href="https://evil.example/x"' not in rendered


def test_work_title_canary_is_inert_at_apply_and_export(tmp_path: Path) -> None:
    vault = tmp_path
    copy_memoria_dirs(vault, "schemas", "config")
    init_git(vault, "content-security@example.invalid", "Content Security")
    payload = (
        "![work](http://beacon.example/work.png) "
        "<script>signal()</script> http://beacon.example/bare"
    )
    call_with_context(
        _capture_source,
        vault,
        "work-canary",
        payload,
        "Canary source description.",
        "Canary source content about framing, methods, outcomes, gaps, and impact. ^p0001",
        machine="capture-machine",
    )
    digest = call_with_context(
        _compile_source_digest,
        vault,
        "work-canary",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="digest-machine",
    )
    note_context = operation_context(
        vault,
        operation_id="propose-note-candidates",
        machine="note-machine",
        run_id="note-canary",
    )
    notes = _emit_note_candidates(
        vault,
        "work-canary",
        [{"title": payload, "body": f"Canary analysis: {payload}"}],
        context=note_context,
    )
    [note_rel] = notes["note_paths"]
    call_with_context(
        _curate_note_candidate,
        vault,
        note_rel,
        "accepted",
        actor="pi",
        machine="curator-machine",
    )
    note_id = str(read_frontmatter(vault / note_rel)["id"])
    write_checked_concept(
        vault,
        "projects/canary/project.md",
        "type: project\ncheck_status: checked\ntitle: Canary project\n",
        "project",
    )
    outline = vault / "projects/canary/outline.md"
    outline.write_text(f"- {note_id} — Canary note\n", encoding="utf-8")
    call_with_context(_compose_project_draft, vault, "canary", machine="draft-machine")
    exported = call_with_context(
        _write_project_export,
        vault,
        "canary",
        draft=True,
        machine="export-machine",
    )

    applied = [
        (vault / digest["digest_path"]).read_text(encoding="utf-8"),
        (vault / note_rel).read_text(encoding="utf-8"),
        (vault / "projects/canary/draft.md").read_text(encoding="utf-8"),
    ]
    for content in [*applied, exported["content"]]:
        assert "![work]" not in content
        assert "<script>" not in content
        assert "](http://beacon.example" not in content
        assert "`http://beacon.example/work.png`" in content
        assert "`http://beacon.example/bare`" in content


def test_composed_draft_headings_and_outline_reasoning_render_fenced_fragments_inert(
    tmp_path: Path,
) -> None:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("Pandoc is optional")
    vault = tmp_path
    copy_memoria_dirs(vault, "schemas", "config")
    init_git(vault, "content-security@example.invalid", "Content Security")
    outline_reasoning = '```\n<img src="https://evil.example/outline-reasoning">\n```'
    write_checked_concept(
        vault,
        "projects/fenced/project.md",
        "type: project\ncheck_status: checked\ntitle: |\n"
        "  ```\n"
        '  <img src="https://evil.example/project-title">\n'
        "  ```\n",
        "project",
    )
    write_checked_concept(
        vault,
        "notes/fenced.md",
        "type: note\ncheck_status: checked\n"
        "title: |\n"
        "  ```\n"
        '  <img src="https://evil.example/member-title">\n'
        "  ```\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n",
        "note",
        body="A checked note body.",
    )
    outline = vault / "projects/fenced/outline.md"
    outline.parent.mkdir(parents=True, exist_ok=True)
    outline.write_text("- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — selected\n", encoding="utf-8")
    call_with_context(_compose_project_draft, vault, "fenced", machine="draft-machine")

    draft = (vault / "projects/fenced/draft.md").read_text(encoding="utf-8")
    outline_text = _outline_text(
        [{"id": "01ARZ3NDEKTSV4RRFFQ69G5FA1", "reasoning": outline_reasoning}]
    )
    for markdown in (draft, outline_text):
        rendered = subprocess.run(
            [pandoc, "-f", "commonmark", "-t", "html"],
            input=markdown,
            text=True,
            capture_output=True,
            check=True,
        ).stdout
        assert "<img" not in rendered
