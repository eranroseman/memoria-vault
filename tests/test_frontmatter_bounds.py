"""The one frontmatter-bounds implementation: vaultio.frontmatter_bounds."""

from __future__ import annotations

from memoria_vault.runtime.vaultio import (
    frontmatter_bounds,
    parse_frontmatter,
    split_frontmatter,
)

PLAIN = "---\ntype: note\n---\nbody\n"
BOM = "\ufeff---\ntype: note\n---\nbody\n"
BLANK_LEAD = "\n---\ntype: note\n---\nbody\n"
DOTS = "---\ntype: note\n...\nbody\n"
CRLF = "---\r\ntype: note\r\n---\r\nbody\r\n"


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
