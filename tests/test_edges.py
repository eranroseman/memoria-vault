"""Single owner of the concept-relation rosters and links parsing (EDGES spec section 1)."""

from __future__ import annotations

import re

from memoria_vault.runtime.subsystems.lib import edges, schema
from tests.helpers import ROOT


def test_edge_relations_is_the_full_seven() -> None:
    assert edges.EDGE_RELATIONS == frozenset(
        {"supports", "contradicts", "extends", "tension", "warrant", "qualifier", "rebuttal"}
    )


def test_link_relations_is_everything_except_tension() -> None:
    assert edges.LINK_RELATIONS == edges.EDGE_RELATIONS - {"tension"}


def test_schema_reexports_the_moved_names() -> None:
    assert schema.LINK_RELATIONS is edges.LINK_RELATIONS
    assert schema.parse_links is edges.parse_links
    assert schema.normalize_link_target is edges.normalize_link_target


def test_normalize_link_target_strips_wikilink_alias_and_anchor() -> None:
    assert edges.normalize_link_target("[[notes/a|Alias]]") == "notes/a"
    assert edges.normalize_link_target("[[notes/a#section]]") == "notes/a"
    assert edges.normalize_link_target(" notes/a ") == "notes/a"
    assert edges.normalize_link_target("[[ ]]") == ""


def test_normalize_link_target_is_total_over_non_strings() -> None:
    # The one isinstance guard left in the parser family: `parse_links` hands its
    # raw YAML list entries straight here, so a non-str target is junk, not a crash.
    assert edges.normalize_link_target(17) == ""
    assert edges.normalize_link_target(None) == ""


def test_parse_links_accepts_the_six_and_skips_tension_and_junk() -> None:
    pairs = edges.parse_links(
        {
            "supports": ["[[notes/a]]"],
            "warrant": ["notes/w.md"],
            "qualifier": ["[[notes/q|Q]]"],
            "rebuttal": ["[[notes/r]]"],
            "tension": ["notes/t.md"],
            "related": ["notes/x.md"],
            "extends": "not-a-list",
            # YAML admits non-str mapping keys; the roster test is the only skip
            # they need, so `parse_links` carries no isinstance guard for them.
            1: ["notes/n.md"],
            None: ["notes/none.md"],
        }
    )
    # Equality, not membership: it is also the proof that `tension`, an unknown
    # relation, a non-list value, and the two non-str keys all left nothing behind.
    assert pairs == [
        ("supports", "notes/a"),
        ("warrant", "notes/w.md"),
        ("qualifier", "notes/q"),
        ("rebuttal", "notes/r"),
    ]


def test_parse_links_keeps_every_target_of_every_relation_in_authored_order() -> None:
    # N>1 on both axes: three relations, and two targets under each of two of them.
    pairs = edges.parse_links(
        {
            "supports": ["[[notes/a]]", "notes/b.md"],
            "qualifier": ["notes/q1.md", "[[notes/q2|Q2]]"],
            "rebuttal": ["notes/r.md"],
        }
    )

    assert pairs == [
        ("supports", "notes/a"),
        ("supports", "notes/b.md"),
        ("qualifier", "notes/q1.md"),
        ("qualifier", "notes/q2"),
        ("rebuttal", "notes/r.md"),
    ]


def test_parse_links_drops_one_unusable_target_without_dropping_its_siblings() -> None:
    # The per-target skip, not the per-relation skip: the relation stays legal
    # and its usable siblings survive alongside the dropped entries.
    assert edges.parse_links(
        {"supports": ["notes/a.md", 17, "notes/../escape.md", "", "notes/b.md"]}
    ) == [
        ("supports", "notes/a.md"),
        ("supports", "notes/b.md"),
    ]


def test_parse_links_ignores_a_non_map_links_value() -> None:
    assert edges.parse_links(["supports", "notes/a.md"]) == []
    assert edges.parse_links(None) == []


def test_parse_typed_wikilinks_filters_to_frontmatter_legal_relations() -> None:
    body = (
        "Typed [[supports::notes/a.md]] then [[rebuttal::notes/r.md|R]] then "
        "[[tension::notes/t.md]] then [[frob::notes/x.md]] and bare [[notes/b.md]]."
    )
    assert edges.parse_typed_wikilinks(body) == [
        ("supports", "notes/a.md"),
        ("rebuttal", "notes/r.md"),
    ]


def test_parse_typed_wikilinks_skips_a_whitespace_only_target() -> None:
    # The `and target` arm: the regex matches (one or more chars between `::`
    # and `]]`), and only the post-strip blank check drops this pair.
    assert edges.parse_typed_wikilinks("[[supports::   ]] and [[supports::notes/a.md]]") == [
        ("supports", "notes/a.md")
    ]


def test_parse_typed_wikilinks_reads_every_typed_link_in_one_body() -> None:
    body = (
        "[[supports::notes/a.md]] and [[supports::notes/b.md]] and "
        "[[qualifier::notes/q.md]] and [[warrant::notes/w.md|W]]."
    )
    assert edges.parse_typed_wikilinks(body) == [
        ("supports", "notes/a.md"),
        ("supports", "notes/b.md"),
        ("qualifier", "notes/q.md"),
        ("warrant", "notes/w.md"),
    ]


def test_single_roster_definition_repo_wide() -> None:
    """EDGES section 10's acceptance: grepping the repo finds one roster definition."""
    roster_literal = re.compile(r"['\"]supports['\"]\s*,\s*['\"]contradicts['\"]")
    offenders = [
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "src/memoria_vault").rglob("*.py")
        if path.name != "edges.py" and roster_literal.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []
