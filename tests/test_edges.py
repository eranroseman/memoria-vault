"""Single owner of the concept-relation rosters and links parsing (EDGES spec section 1)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from memoria_vault.runtime import state
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


def test_strip_wikilink_is_syntax_only_and_normalize_link_target_is_not() -> None:
    """The namespace boundary, asserted from both sides.

    Titles and slugs — the alias space `structural_impact_graph` resolves in —
    routinely carry a colon or a dotted tail, which the path-space validator
    rejects as a URI scheme and a foreign suffix. The stripper must not judge,
    and the validator must keep judging.
    """
    assert edges.strip_wikilink("[[Toulmin: the warrant]]") == "Toulmin: the warrant"
    assert edges.strip_wikilink("[[Study 1.2|the pilot]]") == "Study 1.2"
    assert edges.strip_wikilink("[[notes/a#section]]") == "notes/a"
    assert edges.strip_wikilink(" notes/a ") == "notes/a"

    assert edges.normalize_link_target("[[Toulmin: the warrant]]") == ""
    assert edges.normalize_link_target("[[Study 1.2]]") == ""

    # Braces come off only in matched pairs: a half-typed wikilink is returned
    # whole, never truncated into a target the author never wrote.
    assert edges.strip_wikilink("[[notes/foo") == "[[notes/foo"
    assert edges.strip_wikilink("notes/foo]]") == "notes/foo]]"


def test_the_two_target_functions_share_one_totality_contract() -> None:
    # Two public functions in the roster owner: a non-`str` is junk to both, so
    # neither manufactures `"None"` or a stringified dict as a target.
    for junk in (None, 17, {"target": "notes/a.md"}, ["notes/a.md"]):
        assert edges.strip_wikilink(junk) == ""
        assert edges.normalize_link_target(junk) == ""


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


# --- Identity-safe path projections (ERP-A.6) --------------------------------
#
# Two namespaces meet here, and every fixture below keeps them distinguishable:
# `concept_edges.source_concept_id`/`target_concept_id` and `concepts.concept_id`
# are **identity space** (a ULID for a file Concept that authored one, a bare
# `work_id` for a catalog work, a provisional path for an id-less file), while
# `concepts.path`, `concept_edges.target_path` and everything these projections
# return are **path space**. `concepts.path` relates the two; it is not equal to
# either. A fixture whose ids happen to equal its paths proves nothing here, so
# no identity below is path-shaped except where that case is the subject.

SOURCE_ULID = "01JXSSSSSSSSSSSSSSSSSSSSSS"
RESOLVED_ULID = "01JXRRRRRRRRRRRRRRRRRRRRRR"


def _mirror_rows(*, resolved_path: str = "notes/resolved.md") -> list[dict[str, str]]:
    return [
        {"concept_id": SOURCE_ULID, "concept_type": "note", "path": "notes/source.md"},
        {"concept_id": RESOLVED_ULID, "concept_type": "note", "path": resolved_path},
    ]


def _edge(relation: str, target: str, **overrides: str) -> dict[str, str]:
    row = {
        "source_concept_id": SOURCE_ULID,
        "relation_type": relation,
        "target_path": target,
        "check_status": "checked",
        "source_path": "notes/source.md",
    }
    row.update(overrides)
    return row


def _seed_projection_vault(vault: Path, *, with_unchecked: bool = False) -> None:
    """Seed the v16 mirror through the NID-B trusted seam: ULID ids, path renderings."""
    state.rebuild_file_concept_mirror(vault, _mirror_rows())
    rows = [
        _edge("supports", "notes/resolved.md", attributes_json='{"warrant": "licensed"}'),
        _edge("extends", "notes/pending.md", attributes_json='{"addressed": false}'),
    ]
    if with_unchecked:
        rows.append(_edge("contradicts", "notes/resolved.md", check_status="unchecked"))
    state.replace_concept_edges(vault, rows)


def _stored_edge_identities(vault: Path) -> set[str]:
    with state.connect(vault) as conn:
        return {
            str(row["source_concept_id"])
            for row in conn.execute("SELECT source_concept_id FROM concept_edges")
        }


def test_concept_edge_path_pairs_project_stored_identities_to_durable_paths(
    tmp_path: Path,
) -> None:
    _seed_projection_vault(tmp_path)

    # The fixture is not degenerate: what is stored is the ULID, not the path.
    assert _stored_edge_identities(tmp_path) == {SOURCE_ULID}

    pairs = edges.concept_edge_path_pairs(tmp_path)

    assert pairs == [
        {
            "source_path": "notes/source.md",
            "target_path": "notes/pending.md",
            "relation_type": "extends",
        },
        {
            "source_path": "notes/source.md",
            "target_path": "notes/resolved.md",
            "relation_type": "supports",
        },
    ]
    serialized = json.dumps(pairs)
    assert SOURCE_ULID not in serialized
    assert RESOLVED_ULID not in serialized


def test_concept_edge_path_records_add_parsed_attributes_and_nothing_else(
    tmp_path: Path,
) -> None:
    _seed_projection_vault(tmp_path)

    records = edges.concept_edge_path_records(tmp_path)

    # Whole-row equality: the only field the record API adds is `attributes`, so
    # no `edge_id`, `source_concept_id` or `target_concept_id` can ride along.
    assert records == [
        {
            "source_path": "notes/source.md",
            "target_path": "notes/pending.md",
            "relation_type": "extends",
            "attributes": {"addressed": False},
        },
        {
            "source_path": "notes/source.md",
            "target_path": "notes/resolved.md",
            "relation_type": "supports",
            "attributes": {"warrant": "licensed"},
        },
    ]
    assert SOURCE_ULID not in json.dumps(records)


def test_unchecked_topology_is_absent_by_default_from_both_projections(tmp_path: Path) -> None:
    _seed_projection_vault(tmp_path, with_unchecked=True)

    assert [pair["relation_type"] for pair in edges.concept_edge_path_pairs(tmp_path)] == [
        "extends",
        "supports",
    ]
    assert [record["relation_type"] for record in edges.concept_edge_path_records(tmp_path)] == [
        "extends",
        "supports",
    ]

    assert [
        pair["relation_type"]
        for pair in edges.concept_edge_path_pairs(tmp_path, checked_only=False)
    ] == ["contradicts", "extends", "supports"]
    assert [
        record["relation_type"]
        for record in edges.concept_edge_path_records(tmp_path, checked_only=False)
    ] == ["contradicts", "extends", "supports"]


def test_a_bare_work_id_endpoint_renders_at_its_catalog_path(tmp_path: Path) -> None:
    """The second non-path identity shape, and the one that fails quietly.

    A catalog work keys by its bare ``work_id``, which `normalize_path` accepts
    unchanged — so an implementation that normalized the identity instead of
    joining `concepts.path` would emit a plausible `settles-2016` node that no
    consumer's path space contains. Only the rendered `catalog/sources/…` form
    satisfies this assertion.
    """
    state.upsert_catalog_record(tmp_path, work_id="settles-2016", title="A spaced repetition model")
    state.rebuild_file_concept_mirror(tmp_path, _mirror_rows())
    state.replace_concept_edges(
        tmp_path,
        [
            _edge("supports", "catalog/sources/settles-2016"),
            _edge(
                "extends",
                "notes/resolved.md",
                source_concept_id="settles-2016",
                source_path="",
            ),
        ],
    )

    assert _stored_edge_identities(tmp_path) == {SOURCE_ULID, "settles-2016"}
    assert edges.concept_edge_path_pairs(tmp_path) == [
        {
            "source_path": "catalog/sources/settles-2016",
            "target_path": "notes/resolved.md",
            "relation_type": "extends",
        },
        {
            "source_path": "notes/source.md",
            "target_path": "catalog/sources/settles-2016",
            "relation_type": "supports",
        },
    ]


def test_a_resolved_target_projects_its_current_path_not_the_stored_one(tmp_path: Path) -> None:
    """The resolved arm has to come from the mirror, or a rename serves a dead path.

    NID-B.4's reconcile-by-id moves `concepts.path` for a file renamed out of
    band and leaves `concept_edges.target_path` at the vacated path, which is the
    one state where the two disagree — and the only one that tells a projection
    reading `target concepts.path` apart from one reading the durable column.
    """
    _seed_projection_vault(tmp_path)
    state.rebuild_file_concept_mirror(tmp_path, _mirror_rows(resolved_path="notes/renamed.md"))

    with state.connect(tmp_path) as conn:
        stored = conn.execute(
            "SELECT target_path FROM concept_edges WHERE relation_type = 'supports'"
        ).fetchone()
    assert str(stored["target_path"]) == "notes/resolved.md"

    assert [pair["target_path"] for pair in edges.concept_edge_path_pairs(tmp_path)] == [
        "notes/pending.md",
        "notes/renamed.md",
    ]


def test_a_pathless_endpoint_is_skipped_while_its_durable_target_path_survives(
    tmp_path: Path,
) -> None:
    """`concepts.path` is not total: a db-store Concept may render nowhere.

    The schema defaults `path` to `''` and no writer mints such a row today, but
    a projection that emitted it would hand every path-space walk a `''` node
    that joins every blank-source edge to every other. The resolved-but-pathless
    *target* is the opposite case: its durable `target_path` is still the honest
    answer, so it survives.
    """
    state.rebuild_file_concept_mirror(tmp_path, _mirror_rows())
    with state.connect(tmp_path) as conn:
        state.ensure_concept_parent_conn(
            conn, "cap-mv", concept_type="capability", store="db", path=""
        )
    state.replace_concept_edges(
        tmp_path,
        [
            _edge("supports", "notes/resolved.md"),
            _edge("rebuttal", ""),
            _edge("qualifier", "cap-mv"),
            _edge("warrant", "notes/resolved.md", source_concept_id="cap-mv", source_path=""),
        ],
    )

    assert edges.concept_edge_path_pairs(tmp_path) == [
        {
            "source_path": "notes/source.md",
            "target_path": "cap-mv",
            "relation_type": "qualifier",
        },
        {
            "source_path": "notes/source.md",
            "target_path": "notes/resolved.md",
            "relation_type": "supports",
        },
    ]


def test_unusable_edge_attributes_project_as_an_empty_dict(tmp_path: Path) -> None:
    # `replace_concept_edges` stores `attributes_json` verbatim, so both shapes
    # are reachable through the trusted seam: JSON that is not an object, and
    # text that is not JSON.
    state.rebuild_file_concept_mirror(tmp_path, _mirror_rows())
    state.replace_concept_edges(
        tmp_path,
        [
            _edge("supports", "notes/resolved.md", attributes_json="[1, 2]"),
            _edge("extends", "notes/resolved.md", attributes_json="{oops"),
        ],
    )

    assert [record["attributes"] for record in edges.concept_edge_path_records(tmp_path)] == [
        {},
        {},
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
