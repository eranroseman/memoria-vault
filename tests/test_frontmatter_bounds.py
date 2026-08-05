"""The one frontmatter-bounds implementation: vaultio.frontmatter_bounds."""

from __future__ import annotations

import pytest

from memoria_vault.runtime.state.markdown import _yaml_frontmatter_bounds
from memoria_vault.runtime.vaultio import (
    frontmatter_bounds,
    parse_frontmatter,
    split_frontmatter,
)
from memoria_vault.runtime.vocabulary import schema

pytestmark = pytest.mark.unit

PLAIN = "---\ntype: note\n---\nbody\n"
BOM = "\ufeff---\ntype: note\n---\nbody\n"
BLANK_LEAD = "\n---\ntype: note\n---\nbody\n"
DOTS = "---\ntype: note\n...\nbody\n"
CRLF = "---\r\ntype: note\r\n---\r\nbody\r\n"
NO_FRONTMATTER = "just body\n"


def test_plain_document() -> None:
    assert parse_frontmatter(PLAIN) == {"type": "note"}
    assert split_frontmatter(PLAIN) == ({"type": "note"}, "body\n")


def test_bom_document_has_frontmatter() -> None:
    assert parse_frontmatter(BOM) == {"type": "note"}
    assert split_frontmatter(BOM)[1] == "body\n"


def test_leading_blank_line_has_frontmatter() -> None:
    assert parse_frontmatter(BLANK_LEAD) == {"type": "note"}


def test_dots_terminator_closes_frontmatter() -> None:
    assert parse_frontmatter(DOTS) == {"type": "note"}
    assert split_frontmatter(DOTS)[1] == "body\n"


def test_crlf_document_has_frontmatter() -> None:
    assert parse_frontmatter(CRLF) == {"type": "note"}


def test_unclosed_frontmatter_is_absent() -> None:
    assert frontmatter_bounds("---\ntype: note\n") is None
    assert parse_frontmatter("---\ntype: note\n") == {}


def test_plain_body_is_absent() -> None:
    assert frontmatter_bounds("just body\n") is None
    assert split_frontmatter("just body\n") == ({}, "just body\n")


def test_horizontal_rule_mid_body_does_not_close_frontmatter_early() -> None:
    text = "---\ntype: note\n---\nbody\n---\nmore\n"
    assert split_frontmatter(text)[1] == "body\n---\nmore\n"


def test_four_dash_rule_does_not_close_frontmatter() -> None:
    """Deliberate tightening vs. the old strict implementation: the old
    ``text.find("\\n---", 3)`` matched a ``----`` line as a prefix of ``---``,
    so a four-dash rule inside frontmatter closed it early. The new anchored
    closing regex requires the line to be exactly ``---`` or ``...`` (plus
    only trailing whitespace), so a lone ``----`` line no longer closes it."""
    # No real closer exists, only a four-dash line -- frontmatter is correctly
    # reported as unterminated rather than closing early against it.
    unterminated = "---\ntype: note\n----\nbody\n"
    assert frontmatter_bounds(unterminated) is None

    # With a real closer further down, that is where frontmatter ends, not at
    # the four-dash line.
    text = "---\ntype: note\n----\nbody\n---\nreal body\n"
    assert frontmatter_bounds(text) is not None
    assert split_frontmatter(text)[1] == "real body\n"


def test_trailing_text_on_opening_line_does_not_open_frontmatter() -> None:
    """Deliberate tightening vs. the old strict implementation: the old
    ``text.startswith("---")`` accepted ``--- trailing text`` as an opener.
    The new opening regex requires the line to end right after ``---`` (plus
    only trailing whitespace before the newline), so trailing text on the
    opening line means no frontmatter at all."""
    text = "--- trailing text\ntype: note\n---\nbody\n"
    assert frontmatter_bounds(text) is None
    assert parse_frontmatter(text) == {}
    assert split_frontmatter(text) == ({}, text)


@pytest.mark.parametrize(
    ("label", "text"),
    [
        ("plain", PLAIN),
        ("bom", BOM),
        ("leading_blank_line", BLANK_LEAD),
        ("dots_terminated", DOTS),
        ("crlf", CRLF),
        ("no_frontmatter", NO_FRONTMATTER),
    ],
)
def test_consumers_agree_on_frontmatter_classification(tmp_path, label, text) -> None:
    """The branch's actual invariant: `vaultio.split_frontmatter`, the
    `state/markdown` alias import, and `vocabulary.schema._markdown_frontmatter`
    must classify the same bytes identically. These three were the divergent
    forks this branch unified; a regression here means one of them started
    reimplementing its own answer to "where does frontmatter end" again.
    """
    # Route every consumer through one identical read: `_markdown_frontmatter`
    # only accepts a Path and reads it via `path.read_text`, which universal-
    # newline-translates CRLF -- comparing against the raw in-memory `text`
    # would fail on a translation artifact unrelated to frontmatter
    # classification. Reading `file_text` back once keeps all three consumers
    # looking at the exact same string.
    path = tmp_path / f"{label}.md"
    path.write_text(text, encoding="utf-8")
    file_text = path.read_text(encoding="utf-8")

    vaultio_bounds = frontmatter_bounds(file_text)
    assert _yaml_frontmatter_bounds(file_text) == vaultio_bounds

    vaultio_fm, vaultio_body = split_frontmatter(file_text)

    schema_fm, schema_body, schema_errors = schema._markdown_frontmatter(path)

    if vaultio_bounds is None:
        assert vaultio_fm == {}
        assert schema_errors[:1] in (
            ["missing YAML frontmatter"],
            ["unterminated YAML frontmatter"],
        )
    else:
        assert schema_errors == []
        assert schema_fm == vaultio_fm
        assert schema_body == vaultio_body
