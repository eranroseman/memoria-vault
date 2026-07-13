"""Content-security regression tests."""

from memoria_vault.runtime.content_security import neutralize_untrusted_markdown


def test_image_embeds_cannot_render() -> None:
    markdown_image = neutralize_untrusted_markdown(
        "![beacon](http://evil.example/x.png)"
    )
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
        "~~~html\n<img src=\"http://tilde.example\">\n~~~\n"
    )

    assert neutralize_untrusted_markdown(source) == source


def test_neutralization_is_idempotent() -> None:
    source = "![x](http://evil.example/x) <script>bad()</script>"
    once = neutralize_untrusted_markdown(source)

    assert neutralize_untrusted_markdown(once) == once
