"""Published-docs link-target tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.checks.doc_link_targets import (
    anchor_definitions,
    check_doc_links,
    published_pages,
)

pytestmark = pytest.mark.static


def _corpus(tmp_path: Path) -> Path:
    """A miniature published site: docs/ plus the unpublished neighbors.

    Layout mirrors the real repo -- `docs/reference/` holds a section index and
    a page with anchors, `docs/superpowers/` is present but unpublished, and
    `src/` sits outside `docs/` entirely.
    """
    docs = tmp_path / "docs"
    (docs / "reference").mkdir(parents=True)
    (docs / "superpowers").mkdir()
    (tmp_path / "src").mkdir()

    # The site config drives what counts as published; the gate reads it rather
    # than restating the exclude list, so the fixture carries one too.
    (docs / "_config.yml").write_text(
        'exclude:\n  - "**/tmp/"\n  - "superpowers/"\n', encoding="utf-8"
    )
    (tmp_path / "src" / "engine.py").write_text("x = 1\n", encoding="utf-8")
    (docs / "logo.png").write_bytes(b"\x89PNG")
    (docs / "reference" / "README.md").write_text("# Reference\n", encoding="utf-8")
    (docs / "reference" / "frontmatter.md").write_text(
        "# Frontmatter\n\n## The `id` field\n\n## Links & catalog resources\n",
        encoding="utf-8",
    )
    (docs / "superpowers" / "plan.md").write_text("# Plan\n", encoding="utf-8")
    return docs


def _write(docs: Path, name: str, body: str) -> None:
    (docs / name).write_text(body, encoding="utf-8")


def test_unpublished_dirs_come_from_the_site_config(tmp_path: Path) -> None:
    """`docs/_config.yml` decides what the site serves; the gate must not guess.

    The exclude list has grown before (`agents/` arrived after this gate was
    written). A hardcoded copy would keep passing links into pages that 404.
    """
    docs = _corpus(tmp_path)
    (docs / "_config.yml").write_text(
        'exclude:\n  - "**/tmp/"\n  - "superpowers/"\n  - "agents/"\n', encoding="utf-8"
    )
    (docs / "agents").mkdir()
    (docs / "agents" / "domain.md").write_text("# Domain\n", encoding="utf-8")
    _write(docs, "guide.md", "# Guide\n\nSee [domain](agents/domain.md).\n")

    failures = check_doc_links(docs)

    assert failures == [
        "docs/guide.md:3: link target is not published: 'agents/domain.md'",
    ]
    assert all("agents" not in page.as_posix() for page in published_pages(docs))


def test_clean_page_with_every_allowed_form_passes(tmp_path: Path) -> None:
    docs = _corpus(tmp_path)
    _write(
        docs,
        "guide.md",
        "# Guide\n"
        "\n"
        "## A section\n"
        "\n"
        "See [the site](https://example.com/x) and [mail](mailto:a@example.com).\n"
        "Read [frontmatter](reference/frontmatter.md) and\n"
        "[the id field](reference/frontmatter.md#the-id-field).\n"
        "Jump to [a section](#a-section). The [index](reference/) lists more.\n"
        "Here is the ![logo](logo.png).\n"
        "\n"
        "```markdown\n"
        "[broken](nowhere.md) and [escape](../src/engine.py)\n"
        "```\n",
    )

    assert check_doc_links(docs) == []


def test_dead_relative_link_fails(tmp_path: Path) -> None:
    docs = _corpus(tmp_path)
    _write(docs, "guide.md", "# Guide\n\nSee [gone](reference/gone.md).\n")

    errors = check_doc_links(docs)

    assert errors == ["docs/guide.md:3: link target does not exist: 'reference/gone.md'"]


def test_absolute_filesystem_path_fails(tmp_path: Path) -> None:
    docs = _corpus(tmp_path)
    _write(docs, "guide.md", "# Guide\n\nSee [abs](/docs/reference/frontmatter.md).\n")

    errors = check_doc_links(docs)

    assert errors == [
        "docs/guide.md:3: absolute filesystem path: '/docs/reference/frontmatter.md' "
        "-- use a relative link or a full URL"
    ]


def test_link_escaping_into_src_fails(tmp_path: Path) -> None:
    docs = _corpus(tmp_path)
    _write(docs, "guide.md", "# Guide\n\nSee [engine](../src/engine.py).\n")

    errors = check_doc_links(docs)

    assert errors == ["docs/guide.md:3: link target leaves docs/: '../src/engine.py'"]


def test_link_into_unpublished_superpowers_fails(tmp_path: Path) -> None:
    docs = _corpus(tmp_path)
    _write(docs, "guide.md", "# Guide\n\nSee [plan](superpowers/plan.md).\n")

    errors = check_doc_links(docs)

    assert errors == [
        "docs/guide.md:3: link target is not published: 'superpowers/plan.md'",
    ]


def test_dead_anchor_fails(tmp_path: Path) -> None:
    docs = _corpus(tmp_path)
    _write(docs, "guide.md", "# Guide\n\nSee [x](reference/frontmatter.md#no-such-heading).\n")

    errors = check_doc_links(docs)

    assert errors == [
        "docs/guide.md:3: no heading or anchor 'no-such-heading' in docs/reference/frontmatter.md"
    ]


def test_dead_same_page_anchor_fails(tmp_path: Path) -> None:
    docs = _corpus(tmp_path)
    _write(docs, "guide.md", "# Guide\n\nJump to [nowhere](#nowhere).\n")

    errors = check_doc_links(docs)

    assert errors == ["docs/guide.md:3: no heading or anchor 'nowhere' in docs/guide.md"]


def test_unpublished_pages_are_not_scanned(tmp_path: Path) -> None:
    docs = _corpus(tmp_path)
    _write(docs / "superpowers", "plan.md", "# Plan\n\n[gone](nowhere.md)\n")

    assert check_doc_links(docs) == []
    assert all("superpowers" not in page.as_posix() for page in published_pages(docs))


def test_directory_target_resolves_through_its_readme(tmp_path: Path) -> None:
    """Section indexes are linked as `reference/` -- a real Pages route."""
    docs = _corpus(tmp_path)
    _write(
        docs,
        "guide.md",
        "# Guide\n\n[slash](reference/) and [bare](reference) and [heading](reference/#reference)\n",
    )

    assert check_doc_links(docs) == []


def test_directory_target_without_a_readme_fails(tmp_path: Path) -> None:
    docs = _corpus(tmp_path)
    (docs / "empty").mkdir()
    _write(docs, "guide.md", "# Guide\n\n[nothing](empty/)\n")

    errors = check_doc_links(docs)

    assert errors == ["docs/guide.md:3: link target does not exist: 'empty/'"]


def test_html_anchor_definition_satisfies_an_anchor_link(tmp_path: Path) -> None:
    """The bibliography convention: `<a id="bush1945">` is a real target."""
    docs = _corpus(tmp_path)
    _write(docs, "bibliography.md", '# Bibliography\n\n<a id="bush1945"></a> Bush, V. 1945.\n')
    _write(docs, "guide.md", "# Guide\n\nSee [Bush](bibliography.md#bush1945).\n")

    assert check_doc_links(docs) == []


def test_heading_inside_a_code_fence_is_not_an_anchor(tmp_path: Path) -> None:
    docs = _corpus(tmp_path)
    _write(docs, "target.md", "# Target\n\n```bash\n# Not a heading\n```\n")
    _write(docs, "guide.md", "# Guide\n\nSee [x](target.md#not-a-heading).\n")

    errors = check_doc_links(docs)

    assert errors == ["docs/guide.md:3: no heading or anchor 'not-a-heading' in docs/target.md"]


def test_anchor_matches_either_slug_dialect(tmp_path: Path) -> None:
    """Punctuation-heavy headings: pass if kramdown OR GitHub slugging matches."""
    docs = _corpus(tmp_path)
    _write(
        docs,
        "target.md",
        "# Target\n\n## Part 1 — The as-built map (alpha.16)\n\n## Links & catalog `resources`\n",
    )
    _write(
        docs,
        "guide.md",
        "# Guide\n"
        "\n"
        "[github style](target.md#part-1--the-as-built-map-alpha16)\n"
        "[collapsed](target.md#part-1-the-as-built-map-alpha16)\n"
        "[backticks stripped](target.md#links--catalog-resources)\n",
    )

    assert check_doc_links(docs) == []


def test_kramdown_explicit_header_id_is_an_anchor(tmp_path: Path) -> None:
    """`### Name {#custom-id}` sets the id kramdown renders -- honor it."""
    docs = _corpus(tmp_path)
    _write(
        docs,
        "target.md",
        "# Target\n\n### Open Knowledge Format (OKF) {#open-knowledge-format-okf}\n"
        "\n### event_log {: #event_log}\n",
    )
    _write(
        docs,
        "guide.md",
        "# Guide\n\n[okf](target.md#open-knowledge-format-okf)\n[log](target.md#event_log)\n",
    )

    assert check_doc_links(docs) == []


def test_explicit_header_id_does_not_pollute_the_computed_slug(tmp_path: Path) -> None:
    docs = _corpus(tmp_path)
    _write(docs, "target.md", "# Target\n\n## Task/request {#task-request}\n")

    anchors = anchor_definitions((docs / "target.md").read_text(encoding="utf-8"))

    assert "task-request" in anchors
    assert "taskrequest" in anchors  # the heading's own slug, id suffix removed
    assert not any("task-request-task" in anchor for anchor in anchors)


def test_anchor_definitions_collects_headings_and_html_ids(tmp_path: Path) -> None:
    text = '# A Title\n\n<a id="explicit"></a>\n\n```\n## Fenced\n```\n\n## Second Heading\n'

    anchors = anchor_definitions(text)

    assert "a-title" in anchors
    assert "second-heading" in anchors
    assert "explicit" in anchors
    assert "fenced" not in anchors


def test_link_target_on_its_own_line_is_still_checked(tmp_path: Path) -> None:
    """The corpus wraps long links, leaving `](target)` alone on a line."""
    docs = _corpus(tmp_path)
    _write(docs, "guide.md", "# Guide\n\nSee [a very long link text\n](reference/gone.md).\n")

    errors = check_doc_links(docs)

    assert errors == ["docs/guide.md:4: link target does not exist: 'reference/gone.md'"]


def test_link_title_is_stripped_before_resolving(tmp_path: Path) -> None:
    docs = _corpus(tmp_path)
    _write(docs, "guide.md", '# Guide\n\nSee [fm](reference/frontmatter.md "Frontmatter").\n')

    assert check_doc_links(docs) == []


def test_non_md_target_ignores_its_fragment(tmp_path: Path) -> None:
    docs = _corpus(tmp_path)
    _write(docs, "guide.md", "# Guide\n\n![logo](logo.png#x)\n")

    assert check_doc_links(docs) == []


def test_empty_link_target_fails(tmp_path: Path) -> None:
    docs = _corpus(tmp_path)
    _write(docs, "guide.md", "# Guide\n\nSee [nothing]().\n")

    errors = check_doc_links(docs)

    assert errors == ["docs/guide.md:3: empty link target: ''"]


def test_errors_are_reported_in_page_then_line_order(tmp_path: Path) -> None:
    docs = _corpus(tmp_path)
    _write(docs, "a-guide.md", "# A\n\n[one](gone.md)\n\n[two](/abs.md)\n")
    _write(docs, "b-guide.md", "# B\n\n[three](gone.md)\n")

    errors = check_doc_links(docs)

    assert [error.split(": ", 1)[0] for error in errors] == [
        "docs/a-guide.md:3",
        "docs/a-guide.md:5",
        "docs/b-guide.md:3",
    ]
