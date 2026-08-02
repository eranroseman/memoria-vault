import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.subsystems.lib.edges import (
    concept_edge_path_records,
    normalize_link_target,
    thesis_rel,
)
from memoria_vault.runtime.subsystems.processing.project import structural_impact as impact
from memoria_vault.runtime.subsystems.processing.project import (
    structural_impact_graph as impact_graph,
)
from memoria_vault.runtime.vaultio import iter_markdown, parse_frontmatter, safe_read
from tests.helpers import copy_memoria_dirs, init_git, operation_context

pytestmark = pytest.mark.contract


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# --- v16 substrate fixtures ---------------------------------------------------
#
# Two namespaces meet in these fixtures and neither may stand in for the other.
# `concept_edges.source_concept_id` and `concepts.concept_id` are **identity
# space** — a ULID that shares nothing with the file's location — while
# `concepts.path`, `concept_edges.target_path` and every value the structural
# graph works in are **path space**. A fixture whose ids were path-shaped would
# pass with the projection removed entirely, so no id below is path-shaped.


def concept_ulid(rel: str) -> str:
    """A fixed, valid ULID per note path — deterministic, and never path-shaped."""
    return f"01KBN6V6KX{hashlib.sha256(rel.encode()).hexdigest()[:16].upper()}"


def rebuild_mirror(vault: Path):
    """Rebuild the v16 identity mirror over every note now on disk."""
    rows = []
    for path in iter_markdown(vault):
        rel = path.relative_to(vault).as_posix()
        frontmatter = parse_frontmatter(safe_read(path))
        rows.append(
            {
                "concept_id": concept_ulid(rel),
                "concept_type": str(frontmatter.get("type") or "note"),
                "path": rel,
            }
        )
    state.rebuild_file_concept_mirror(vault, rows)


def edge_row(
    source_path: str,
    relation: str,
    target_path: str,
    *,
    addressed: object = None,
    check_status: str = "checked",
):
    """One substrate row: identity-keyed source, durable path target.

    ``addressed=None`` writes no attribute at all, which is what the mirror pass
    stores for an ordinary authored link — so the projection's default is the
    arm most of this file rides on rather than an unfixtured branch.
    """
    return {
        "source_concept_id": concept_ulid(source_path),
        "relation_type": relation,
        "target_path": target_path,
        "check_status": check_status,
        "source_path": source_path,
        "attributes_json": json.dumps({} if addressed is None else {"addressed": addressed}),
    }


def link_row(vault: Path, source: str, relation: str, target: str, **overrides):
    """Seed the one substrate row ``notes/<source>.md`` authors, scoped to that source."""
    rebuild_mirror(vault)
    source_path = f"notes/{source}.md"
    state.replace_concept_edges(
        vault,
        [edge_row(source_path, relation, f"notes/{target}.md", **overrides)],
        paths=[source_path],
    )


def project(vault: Path, *, scope="alpha", active="thesis", output_mode="thesis", refutation=True):
    refutation_line = "refutation_sufficiency: true\n" if refutation else ""
    write(
        vault / "projects/demo/project.md",
        "---\n"
        "type: project\n"
        "check_status: checked\n"
        "title: Demo project\n"
        "description: Demo project\n"
        "slug: demo\n"
        f"scope_topics: [{scope}]\n"
        "inquiry: {}\n"
        "finer: {}\n"
        f"output_mode: {output_mode}\n"
        "question_version: 1\n"
        "question_log: []\n"
        f"thesis: '[[notes/{active}]]'\n"
        f"{refutation_line}"
        "---\n",
    )
    write(
        vault / "notes/thesis.md",
        "---\n"
        "type: note\n"
        "check_status: checked\n"
        "title: Demo thesis\n"
        "description: Demo thesis\n"
        "status: accepted\n"
        "role: thesis\n"
        "project: '[[projects/demo/project]]'\n"
        "evidence_set: []\n"
        "---\n",
    )


def claim(vault: Path, name: str, relation: str, target: str, *, topics="alpha"):
    write(
        vault / f"notes/{name}.md",
        "---\n"
        "type: note\n"
        "check_status: checked\n"
        f"title: {name}\n"
        f"claim_text: {name}\n"
        "status: accepted\n"
        f"topics: [{topics}]\n"
        "links:\n"
        f"  {relation}: ['[[notes/{target}]]']\n"
        "---\n",
    )
    link_row(vault, name, relation, target)


def gap(vault: Path, name: str, relation: str, target: str, *, topics="alpha"):
    write(
        vault / f"notes/{name}.md",
        "---\n"
        "type: note\n"
        "check_status: checked\n"
        f"title: {name}\n"
        "description: close the gap\n"
        "status: needs_review\n"
        "gap_type: additive\n"
        f"topics: [{topics}]\n"
        "links:\n"
        f"  {relation}: ['[[notes/{target}]]']\n"
        "---\n",
    )
    link_row(vault, name, relation, target)


def seed_mature_graph(vault: Path):
    project(vault)
    claim(vault, "a", "supports", "thesis")
    claim(vault, "b", "supports", "a")
    claim(vault, "c", "contradicts", "thesis")
    claim(vault, "d", "supports", "a")
    claim(vault, "e", "contradicts", "a")


def node(payload, path):
    return next(row for row in payload["nodes"] if row["path"] == path)


def resolver_for(vault: Path) -> dict[str, str]:
    return impact_graph.build_resolver(impact_graph.read_notes(vault))


def test_normalize_link_extracts_a_dict_target_and_strips_wikilink_syntax():
    """The dict form a note's undeclared `project:` key may carry, and its junk arms."""
    assert impact_graph.normalize_link({"target": "[[notes/a.md#section|Claim A]]"}) == "notes/a"
    assert impact_graph.normalize_link({"note": "Toulmin: the warrant"}) == "Toulmin: the warrant"
    assert impact_graph.normalize_link("[[/notes/a/]]") == "notes/a"
    assert impact_graph.normalize_link({"unrelated": "notes/a"}) == ""
    assert impact_graph.normalize_link("   ") == ""
    assert impact_graph.normalize_link(17) == ""


def test_normalize_link_stays_in_alias_space_where_a_path_validator_refuses():
    """The namespace boundary this module straddles, asserted from both sides.

    `normalize_link` feeds `build_resolver`'s alias table, which keys on title,
    slug and stem as well as path, so its domain is strictly wider than path
    space. ERP-A.3's Critical was handing exactly these values to the path-space
    validator: every colon-bearing and dotted-tail title normalized to `''` and a
    live project read as brand-new with zero validation errors. The pairs below
    are the two verdicts, side by side, so a future delegation cannot be silent.
    """
    for value in ("Toulmin: the warrant", "Study 1.2", "Method: pilot v1.2"):
        assert impact_graph.normalize_link(value) == value
        assert impact_graph.normalize_link(f"[[{value}|display]]") == value
        assert normalize_link_target(value) == ""

    # A bare stem and an unsuffixed path are the shapes both namespaces accept —
    # the overlap is real, which is why the intersection alone proves nothing.
    assert impact_graph.normalize_link("thesis") == "thesis"
    assert impact_graph.normalize_link("notes/thesis.md") == "notes/thesis"
    assert normalize_link_target("thesis") == "thesis"


def test_find_project_and_find_thesis_resolve_references_written_as_titles(tmp_path):
    """Alias space at its two surviving live call sites.

    `links:` is path space and now reaches the graph only through the substrate,
    so `normalize_link` no longer parses it. What still reads
    an alias is the project selector and the `project:` back-reference on a
    thesis note, and both carry research titles: a colon or a dotted tail is
    ordinary there and fatal to a path validator.
    """
    write(
        tmp_path / "projects/demo/project.md",
        "---\ntype: project\ntitle: 'Method: pilot v1.2'\nslug: demo-1.2\n---\n",
    )
    write(
        tmp_path / "notes/thesis.md",
        "---\ntype: note\ntitle: Demo thesis\nstatus: accepted\nrole: thesis\n"
        "project: '[[Method: pilot v1.2]]'\n---\n",
    )
    notes = impact_graph.read_notes(tmp_path)

    by_title = impact_graph.find_project(notes, "Method: pilot v1.2")
    by_slug = impact_graph.find_project(notes, "demo-1.2")
    thesis = impact_graph.find_thesis(notes, by_title, impact_graph.build_resolver(notes))

    assert by_title.path == by_slug.path == "projects/demo/project.md"
    assert thesis is not None
    assert thesis.path == "notes/thesis.md"
    # The same two references a path-space validator empties on sight.
    assert normalize_link_target("Method: pilot v1.2") == ""
    assert normalize_link_target("demo-1.2") == ""


def test_structural_impact_materializes_mature_argument_graph(tmp_path):
    seed_mature_graph(tmp_path)

    result = impact.run(
        tmp_path,
        "projects/demo/project",
        now=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
    )
    payload = result["payload"]

    assert result["changed"] is True
    assert result["path"] == "projects/demo/project-gate-index.md"
    assert payload["argument_stage"] == "mature"
    assert payload["evidence_saturation"] == "saturated"
    assert payload["saturation_conditions"] == {
        "mature_graph": True,
        "no_high_impact_open_gaps": True,
        "refutation_sufficiency": True,
    }
    assert payload["displayed_confidence"] == "load-bearing"
    assert payload["relation_count"] == 5
    assert payload["supports_count"] == 3
    assert payload["contradicts_count"] == 2
    assert node(payload, "notes/thesis.md")["on_path"] is True
    assert node(payload, "notes/a.md")["articulation"] is True
    assert node(payload, "notes/a.md")["impact"] >= 2
    assert {row["kind"] for row in payload["gap_findings"]} == {"conflict", "fragility"}
    assert {row["kind"] for row in payload["advisories"]} == {"structural"}

    rendered = (tmp_path / result["path"]).read_text(encoding="utf-8")
    assert "<!-- memoria-structural-impact:json -->" in rendered
    assert 'computed_at: "2026-06-16T12:00:00Z"' in rendered


def test_structural_impact_preserves_index_when_values_do_not_change(tmp_path):
    seed_mature_graph(tmp_path)
    first = impact.run(
        tmp_path,
        "projects/demo/project",
        now=datetime(2026, 6, 16, 12, 0, tzinfo=UTC),
    )
    index = tmp_path / first["path"]
    original = index.read_text(encoding="utf-8")

    second = impact.run(
        tmp_path,
        "projects/demo/project",
        now=datetime(2026, 6, 16, 13, 0, tzinfo=UTC),
    )

    assert second["changed"] is False
    assert index.read_text(encoding="utf-8") == original
    assert second["payload"]["computed_at"] == "2026-06-16T12:00:00Z"


def test_structural_impact_ranks_on_path_gaps_and_prunes_off_path(tmp_path):
    seed_mature_graph(tmp_path)
    gap(tmp_path, "on-path-gap", "supports", "a")
    claim(tmp_path, "f", "supports", "on-path-gap")
    claim(tmp_path, "g", "supports", "on-path-gap")
    gap(tmp_path, "off-path-gap", "supports", "ghost")

    result = impact.run(tmp_path, "projects/demo/project")
    payload = result["payload"]

    assert payload["argument_stage"] == "mature"
    assert payload["evidence_saturation"] == "unsaturated"
    assert payload["open_high_impact_gaps"] == 1
    assert node(payload, "notes/on-path-gap.md")["on_path"] is True
    assert node(payload, "notes/on-path-gap.md")["impact"] >= 2
    assert node(payload, "notes/off-path-gap.md")["on_path"] is False
    assert node(payload, "notes/off-path-gap.md")["impact"] == 0
    assert any(
        row["kind"] == "additive" and row["path"] == "notes/on-path-gap.md"
        for row in payload["gap_findings"]
    )


def test_structural_impact_requires_refutation_sufficiency_stamp(tmp_path):
    project(tmp_path, refutation=False)
    claim(tmp_path, "a", "supports", "thesis")
    claim(tmp_path, "b", "supports", "a")
    claim(tmp_path, "c", "contradicts", "thesis")
    claim(tmp_path, "d", "supports", "a")
    claim(tmp_path, "e", "contradicts", "a")

    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert payload["argument_stage"] == "mature"
    assert payload["refutation_floor_met"] is True
    assert payload["refutation_sufficiency"] is False
    assert payload["evidence_saturation"] == "unsaturated"
    assert payload["saturation_conditions"]["refutation_sufficiency"] is False


def test_structural_impact_cold_start_when_scope_does_not_overlap(tmp_path):
    project(tmp_path, scope="beta")
    claim(tmp_path, "a", "supports", "thesis", topics="alpha")
    claim(tmp_path, "b", "supports", "a", topics="alpha")
    claim(tmp_path, "c", "contradicts", "thesis", topics="alpha")
    claim(tmp_path, "d", "supports", "a", topics="alpha")
    claim(tmp_path, "e", "contradicts", "a", topics="alpha")

    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert payload["relation_count"] == 5
    assert payload["scope_overlap_count"] == 0
    assert payload["argument_stage"] == "cold-start"
    assert payload["evidence_saturation"] == "unknown"
    assert payload["displayed_confidence"] == "below-threshold"
    assert payload["gap_findings"] == []
    assert payload["advisories"] == []


def test_structural_impact_refutation_advisory_only_above_readiness(tmp_path):
    project(tmp_path)
    claim(tmp_path, "a", "supports", "thesis")
    claim(tmp_path, "b", "supports", "a")
    claim(tmp_path, "c", "contradicts", "a")
    claim(tmp_path, "d", "supports", "a")

    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert payload["argument_stage"] == "developing"
    assert payload["advisories"] == []

    claim(tmp_path, "e", "supports", "c")
    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert payload["argument_stage"] == "mature"
    assert any(row["kind"] == "refutation" for row in payload["advisories"])


def test_survey_mode_uses_coverage_saturation(tmp_path):
    project(tmp_path, active="", output_mode="survey")
    for name, target in (
        ("a", "b"),
        ("b", "c"),
        ("c", "a"),
        ("d", "a"),
        ("e", "b"),
    ):
        claim(tmp_path, name, "supports", target)

    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert payload["mode"] == "survey"
    assert payload["argument_stage"] == "mature"
    assert payload["evidence_saturation"] == "saturated"
    assert payload["relation_count"] == 5
    assert payload["saturation_conditions"] == {
        "mature_graph": True,
        "no_open_scope_gaps": True,
    }

    gap(tmp_path, "survey-gap", "supports", "a")
    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert payload["evidence_saturation"] == "unsaturated"
    assert any(row["path"] == "notes/survey-gap.md" for row in payload["gap_findings"])


# --- ERP-D.4: the substrate is the edge source -------------------------------


def test_structural_impact_reads_substrate_not_file_text(tmp_path):
    """The rewire's whole claim: `links:` text is no longer an edge source."""
    seed_mature_graph(tmp_path)
    # Corrupt one frontmatter links block after the substrate rows exist: the
    # substrate, not file text, must be the edge source.
    path = tmp_path / "notes/a.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "  supports: ['[[notes/thesis]]']", "  supports: []"
        ),
        encoding="utf-8",
    )

    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert payload["relation_count"] == 5
    assert payload["supports_count"] == 3


def test_substrate_edges_traverse_every_relation_the_substrate_may_hold(tmp_path):
    """Written out, not iterated from the roster: a shrinking roster must fail here."""
    write(tmp_path / "notes/a.md", "---\ntype: note\ntitle: A\n---\nBody.\n")
    write(tmp_path / "notes/b.md", "---\ntype: note\ntitle: B\n---\nBody.\n")
    rebuild_mirror(tmp_path)
    relations = ("contradicts", "extends", "qualifier", "rebuttal", "supports", "warrant")
    state.replace_concept_edges(
        tmp_path,
        [edge_row("notes/a.md", relation, "notes/b.md") for relation in relations],
        paths=["notes/a.md"],
    )

    built = impact_graph.substrate_edges(tmp_path, resolver_for(tmp_path))

    assert [(edge.source, edge.relation, edge.target) for edge in built] == [
        ("notes/a", relation, "notes/b") for relation in relations
    ]


def test_the_substrate_is_identity_keyed_and_the_graph_never_sees_an_id(tmp_path):
    """Anti-degeneracy: the stored endpoints are ULIDs, the graph's are paths."""
    seed_mature_graph(tmp_path)

    with state.connect(tmp_path) as conn:
        stored = {
            str(row["source_concept_id"])
            for row in conn.execute("SELECT source_concept_id FROM concept_edges")
        }

    assert stored == {concept_ulid(f"notes/{name}.md") for name in ("a", "b", "c", "d", "e")}
    assert all("/" not in value for value in stored)

    rendered = repr(impact_graph.substrate_edges(tmp_path, resolver_for(tmp_path)))
    assert all(value not in rendered for value in stored)


def test_the_structural_graph_walks_unchecked_topology(tmp_path):
    """`checked_only=False`: the PI is shown gaps in the graph they actually have."""
    seed_mature_graph(tmp_path)
    state.replace_concept_edges(
        tmp_path,
        [
            edge_row("notes/b.md", "supports", "notes/a.md"),
            edge_row("notes/b.md", "extends", "notes/c.md", check_status="unchecked"),
        ],
        paths=["notes/b.md"],
    )

    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert payload["relation_count"] == 6


def test_addressed_attribute_gates_each_edge_and_defaults_to_true_when_absent(tmp_path):
    """Four shapes, because three of them are otherwise unfixtured branches."""
    seed_mature_graph(tmp_path)
    state.replace_concept_edges(
        tmp_path,
        [
            edge_row("notes/a.md", "supports", "notes/thesis.md"),
            edge_row("notes/a.md", "extends", "notes/b.md", addressed=True),
            edge_row("notes/a.md", "qualifier", "notes/d.md", addressed=False),
            edge_row("notes/a.md", "warrant", "notes/c.md", addressed="yes"),
        ],
        paths=["notes/a.md"],
    )

    addressed = {
        (edge.source, edge.relation, edge.target): edge.addressed
        for edge in impact_graph.substrate_edges(tmp_path, resolver_for(tmp_path))
    }
    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    # Absent, explicitly true, and a non-bool truthy value all land on the
    # dataclass's declared type — `is True`, never a string that merely reads true.
    assert addressed[("notes/a", "supports", "notes/thesis")] is True
    assert addressed[("notes/a", "extends", "notes/b")] is True
    assert addressed[("notes/a", "warrant", "notes/c")] is True
    assert addressed[("notes/a", "qualifier", "notes/d")] is False
    # 4 baseline edges from b/c/d/e plus a's three addressed ones; the qualifier
    # edge is built but filtered out of the analysis.
    assert payload["relation_count"] == 7


def test_a_self_referential_row_is_not_a_relation(tmp_path):
    seed_mature_graph(tmp_path)
    state.replace_concept_edges(
        tmp_path,
        [
            edge_row("notes/a.md", "supports", "notes/thesis.md"),
            edge_row("notes/a.md", "extends", "notes/a.md"),
        ],
        paths=["notes/a.md"],
    )

    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert payload["relation_count"] == 5


def test_a_target_that_renders_nowhere_is_dropped_from_the_graph(tmp_path):
    """A pending row is retained by the projection and skipped by this consumer.

    Never rendered as a node the vault has no note for, and never a crash in the
    resolver — exactly the old resolver's behavior for a dangling link.
    """
    seed_mature_graph(tmp_path)
    state.replace_concept_edges(
        tmp_path,
        [
            edge_row("notes/a.md", "supports", "notes/thesis.md"),
            edge_row("notes/a.md", "supports", "notes/ghost.md"),
        ],
        paths=["notes/a.md"],
    )

    # The projection keeps the pending row; the structural graph does not.
    projected = concept_edge_path_records(tmp_path, checked_only=False)
    assert {"notes/ghost.md"} == {
        record["target_path"] for record in projected if record["target_path"].endswith("ghost.md")
    }

    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert payload["relation_count"] == 5
    assert [row for row in payload["nodes"] if "ghost" in row["path"]] == []


def test_an_edge_whose_source_renders_in_no_note_is_dropped(tmp_path):
    """The mirror keeps a Concept the vault no longer shows; the graph does not.

    Left in, the source resolves to `None` and enters the undirected walk as a
    node with no path — the blank-endpoint shape that already escaped one review
    one module over.
    """
    seed_mature_graph(tmp_path)
    claim(tmp_path, "gone", "supports", "thesis")
    (tmp_path / "notes/gone.md").unlink()

    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert payload["relation_count"] == 5
    assert [row["path"] for row in payload["nodes"] if "gone" in row["path"]] == []


def test_survey_mode_drops_an_unaddressed_relation(tmp_path):
    """Survey mode reads the descriptive graph, and `addressed` still gates it."""
    project(tmp_path, active="", output_mode="survey")
    for name, target in (("a", "b"), ("b", "c"), ("c", "a"), ("d", "a"), ("e", "b")):
        claim(tmp_path, name, "supports", target)
    link_row(tmp_path, "e", "contradicts", "c", addressed=False)

    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert payload["mode"] == "survey"
    assert payload["relation_count"] == 4


def test_an_unsuffixed_target_path_still_reaches_its_note(tmp_path):
    """A `links:` value written without `.md` parks unresolved and resolves here.

    `parse_links` accepts it, `_concept_edge_target_path` cannot key it to a
    Concept, so the projection hands back the durable `notes/b` it was parked at.
    The alias table keys every note by both spellings, which is the whole reason
    projected paths need no second normalization on this side.
    """
    write(tmp_path / "notes/a.md", "---\ntype: note\ntitle: A\n---\nBody.\n")
    write(tmp_path / "notes/b.md", "---\ntype: note\ntitle: B\n---\nBody.\n")
    rebuild_mirror(tmp_path)
    state.replace_concept_edges(
        tmp_path,
        [
            edge_row("notes/a.md", "supports", "notes/b"),
            edge_row("notes/a.md", "extends", "b"),
        ],
        paths=["notes/a.md"],
    )

    built = impact_graph.substrate_edges(tmp_path, resolver_for(tmp_path))

    assert [(edge.source, edge.relation, edge.target) for edge in built] == [
        ("notes/a", "extends", "notes/b"),
        ("notes/a", "supports", "notes/b"),
    ]


def test_a_catalog_work_target_joins_the_graph_without_becoming_a_note(tmp_path):
    """ERP-B's claim→work bridge: connectivity yes, note-keyed rendering no.

    The work id carries a dotted tail on purpose. A bridge target is the one
    projected value a path-space validator does not return unchanged — it reads
    `.v2` as a foreign file suffix and empties the whole reference — so this is
    where the safe direction of the namespace boundary is observable rather than
    merely asserted.
    """
    seed_mature_graph(tmp_path)
    state.upsert_catalog_record(tmp_path, work_id="smith-2020.v2", title="Active learning")
    assert normalize_link_target("catalog/sources/smith-2020.v2") == ""
    state.replace_concept_edges(
        tmp_path,
        [
            edge_row("notes/a.md", "supports", "notes/thesis.md"),
            edge_row("notes/a.md", "supports", "catalog/sources/smith-2020.v2"),
        ],
        paths=["notes/a.md"],
    )

    built = impact_graph.substrate_edges(tmp_path, resolver_for(tmp_path))
    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert ("notes/a", "supports", "catalog/sources/smith-2020.v2") in [
        (edge.source, edge.relation, edge.target) for edge in built
    ]
    assert payload["relation_count"] == 6
    assert payload["supports_count"] == 4
    # It carries connectivity, and it is not a note: no row, no scope overlap,
    # no gap-taxonomy pass over a Note that does not exist.
    assert [row for row in payload["nodes"] if "catalog" in row["path"]] == []
    # The five scoped claim notes; the work is on the path and is not one of them.
    assert payload["scope_overlap_count"] == 5


def test_a_contradicts_edge_to_a_catalog_work_is_not_rendered_as_a_conflict(tmp_path):
    """The conflict finding names two Notes; a work has none, so the edge is skipped."""
    seed_mature_graph(tmp_path)
    state.upsert_catalog_record(tmp_path, work_id="smith-2020.v2", title="Active learning")
    state.replace_concept_edges(
        tmp_path,
        [
            edge_row("notes/a.md", "supports", "notes/thesis.md"),
            edge_row("notes/a.md", "contradicts", "catalog/sources/smith-2020.v2"),
        ],
        paths=["notes/a.md"],
    )

    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert payload["contradicts_count"] == 3
    assert [row["path"] for row in payload["gap_findings"] if row["kind"] == "conflict"] == [
        "notes/c.md",
        "notes/e.md",
    ]
    assert all("catalog" not in json.dumps(row) for row in payload["gap_findings"])


def test_a_durable_target_carrying_wikilink_syntax_is_dropped_not_repaired(tmp_path):
    """The safe direction of the boundary, made observable.

    `insert_concept_edge` keys its durable `target_path` through
    `normalize_path`, which is not a syntax stripper — so an anchored reference
    reaches the projection intact. This consumer treats what the projection hands
    it as path space and nothing else: it does not run the alias-space stripper
    over it and guess that `notes/thesis.md#claim` meant `notes/thesis`. A
    malformed durable target is the writer's defect to fix, not a node this graph
    invents.
    """
    copy_memoria_dirs(tmp_path, "schemas")
    init_git(tmp_path, "impact@example.invalid", "Impact Tests")
    seed_mature_graph(tmp_path)
    state.insert_concept_edge(
        tmp_path,
        source="notes/b.md",
        relation_type="extends",
        target="notes/thesis.md#claim",
        context=operation_context(tmp_path),
    )

    projected = {
        (record["source_path"], record["relation_type"], record["target_path"])
        for record in concept_edge_path_records(tmp_path, checked_only=False)
    }
    built = impact_graph.substrate_edges(tmp_path, resolver_for(tmp_path))
    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert ("notes/b.md", "extends", "notes/thesis.md#claim") in projected
    assert ("notes/b", "extends", "notes/thesis") not in [
        (edge.source, edge.relation, edge.target) for edge in built
    ]
    assert payload["relation_count"] == 5


def test_a_confirmed_tension_row_is_outside_the_structural_roster(tmp_path):
    """`tension` is substrate-legal and roster-illegal, and this reader keeps the roster.

    `replace_concept_edges` skips tension by design, so the only writer is
    `insert_concept_edge` — which is exactly why the filter survives the rewire:
    the substrate can hold a relation the structural graph must not count.
    """
    copy_memoria_dirs(tmp_path, "schemas")
    init_git(tmp_path, "impact@example.invalid", "Impact Tests")
    seed_mature_graph(tmp_path)
    state.insert_concept_edge(
        tmp_path,
        source="notes/a.md",
        relation_type="tension",
        target="notes/c.md",
        context=operation_context(tmp_path),
    )

    built = impact_graph.substrate_edges(tmp_path, resolver_for(tmp_path))
    payload = impact.run(tmp_path, "projects/demo/project")["payload"]

    assert ("notes/a", "tension", "notes/c") in [
        (edge.source, edge.relation, edge.target) for edge in built
    ]
    assert payload["relation_count"] == 5


@pytest.mark.parametrize(
    ("name", "value"),
    [("path", "notes/thesis.md"), ("wikilink", "'[[notes/thesis]]'"), ("stem", "thesis")],
)
def test_structural_impact_lands_on_the_same_note_as_the_one_thesis_normalizer(
    tmp_path, name, value
):
    """`thesis:` is a path-space reference (issue #1623), so these are its shapes.

    This family used to fixture the field as an alias — a note title carrying a
    colon — which `project.yaml`'s `link` kind now refuses outright; alias-space
    resolution keeps its own cover in
    `test_find_project_and_find_thesis_resolve_references_written_as_titles`.
    What has to hold here is that this reader lands on the note
    `edges.thesis_rel` names, the one normalizer the five path-space readers
    share.
    """
    vault = tmp_path / name
    project(vault, active="thesis")
    # No `role: thesis` / `project:` pair, so `thesis:` is the only route to this
    # note: the fallback scan must not rescue the lookup.
    write(
        vault / "notes/thesis.md",
        "---\ntype: note\ncheck_status: checked\ntitle: Demo thesis\n"
        "description: Demo thesis\nstatus: accepted\nevidence_set: []\n---\n",
    )
    write(
        vault / "projects/demo/project.md",
        (vault / "projects/demo/project.md")
        .read_text(encoding="utf-8")
        .replace("thesis: '[[notes/thesis]]'", f"thesis: {value}"),
    )
    claim(vault, "a", "supports", "thesis")

    payload = impact.run(vault, "projects/demo/project")["payload"]

    assert thesis_rel({"thesis": value.strip("'")}) == "notes/thesis.md"
    assert payload["active_thesis"] == "notes/thesis.md"
    assert payload["argument_stage"] == "developing"
    assert payload["relation_count"] == 1
