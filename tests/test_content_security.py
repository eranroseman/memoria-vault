"""Content-security regression tests."""

from pathlib import Path

from memoria_vault.runtime.capture import capture_source as _capture_source
from memoria_vault.runtime.content_security import neutralize_untrusted_markdown
from memoria_vault.runtime.knowledge import (
    compose_project_draft as _compose_project_draft,
)
from memoria_vault.runtime.knowledge import curate_note_candidate as _curate_note_candidate
from memoria_vault.runtime.knowledge import emit_note_candidates as _emit_note_candidates
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


def test_existing_code_spans_and_fences_are_untouched() -> None:
    source = (
        "`http://inline.example` and ``![literal](http://code.example)``\n"
        "```markdown\n![literal](http://fenced.example)\n```\n"
        '~~~html\n<img src="http://tilde.example">\n~~~\n'
    )

    assert neutralize_untrusted_markdown(source) == source


def test_neutralization_is_idempotent() -> None:
    source = "![x](http://evil.example/x) <script>bad()</script>"
    once = neutralize_untrusted_markdown(source)

    assert neutralize_untrusted_markdown(once) == once


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
