"""The consequence closure walk over grounding closure and derivation DAG (EDGES section 5)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.propagation import (
    CONSEQUENCE_TYPES,
    HOP_DERIVED,
    HOP_EVIDENCE,
    HOP_KINDS,
    TRIGGERS,
    closure_inputs,
    consequence_closure,
    hop_consequence,
)
from memoria_vault.runtime.trusted_writer import append_explicit_journal_event
from memoria_vault.runtime.vocabulary.edges import EDGE_RELATIONS

pytestmark = pytest.mark.runtime

CLAIM_ULID = "01JXCCCCCCCCCCCCCCCCCCCCCC"
THESIS_ULID = "01JXTTTTTTTTTTTTTTTTTTTTTT"
SPAN_SHA = "sha256:" + "a" * 64


def _all_grounds_lost(trigger: str, hop: str, *, seed: bool) -> str | None:
    return "grounds-lost"


def _edge(source: str, relation: str, target: str) -> dict[str, str]:
    """One row in the shape `edges.concept_edge_path_pairs` publishes."""
    return {"source_path": source, "relation_type": relation, "target_path": target}


class _RecordingTyper:
    """A typer that records the walk's trajectory, not only its fixed point."""

    def __init__(self, answer: str | None = "grounds-lost") -> None:
        self.answer = answer
        self.calls: list[tuple[str, str, bool]] = []

    def __call__(self, trigger: str, hop: str, *, seed: bool) -> str | None:
        self.calls.append((trigger, hop, seed))
        return self.answer


# Every relation in the live roster and the endpoint the walk treats as the
# dependent. `extends` is the one that runs source->target — the extender depends
# on the base it extends — and the other six run target->source. Asserting these
# keys against EDGE_RELATIONS is what makes an eighth verb fail loudly here
# instead of silently inheriting the target->source default.
_DEPENDENT_BY_RELATION = {
    "supports": "notes/target.md",
    "contradicts": "notes/target.md",
    "extends": "notes/source.md",
    "tension": "notes/target.md",
    "warrant": "notes/target.md",
    "qualifier": "notes/target.md",
    "rebuttal": "notes/target.md",
}


def test_the_consequence_roster_is_the_four_spec_types() -> None:
    assert CONSEQUENCE_TYPES == (
        "grounds-lost",
        "warrant-lost",
        "qualifier-regression",
        "rebuttal-strengthened",
    )


def test_the_trigger_roster_is_the_six_named_seams() -> None:
    assert TRIGGERS == (
        "claim-changed",
        "claim-retracted",
        "edge-added",
        "edge-removed",
        "standing-changed",
        "decided-wrong",
    )


def test_the_non_edge_hop_kinds_never_collide_with_a_relation_verb() -> None:
    """`via` is one namespace: hop kinds, the seed label, and the seven verbs share it.

    C.2's decision table keys on the hop, so a hop kind that equalled a relation
    would make one table row answer for two different kinds of dependency.
    """
    assert (HOP_EVIDENCE, HOP_DERIVED) == ("evidence", "derived")
    assert not {HOP_EVIDENCE, HOP_DERIVED, "seed"} & EDGE_RELATIONS


def test_every_edge_relation_has_a_declared_traversal_direction() -> None:
    assert set(_DEPENDENT_BY_RELATION) == set(EDGE_RELATIONS)
    assert [
        relation
        for relation, dependent in sorted(_DEPENDENT_BY_RELATION.items())
        if dependent == "notes/source.md"
    ] == ["extends"]

    for relation, dependent in sorted(_DEPENDENT_BY_RELATION.items()):
        rows = [_edge("notes/source.md", relation, "notes/target.md")]
        fallen = "notes/source.md" if dependent == "notes/target.md" else "notes/target.md"

        assert consequence_closure(
            [fallen],
            trigger="claim-retracted",
            grounding_edges=rows,
            evidence_dependents={},
            derivation_children={},
            typer=_all_grounds_lost,
        ) == {dependent: {"consequence": "grounds-lost", "via": relation, "depth": 1}}

        # The other way down the same edge reaches nothing: a direction that
        # traversed both ways would satisfy the assertion above too.
        assert (
            consequence_closure(
                [dependent],
                trigger="claim-retracted",
                grounding_edges=rows,
                evidence_dependents={},
                derivation_children={},
                typer=_all_grounds_lost,
            )
            == {}
        )


def test_closure_walks_supports_forward_and_extends_reverse() -> None:
    marked = consequence_closure(
        ["notes/a.md"],
        trigger="claim-retracted",
        grounding_edges=[
            _edge("notes/a.md", "supports", "notes/b.md"),
            _edge("notes/c.md", "extends", "notes/a.md"),
            _edge("notes/z.md", "supports", "notes/a.md"),
        ],
        evidence_dependents={},
        derivation_children={},
        typer=_all_grounds_lost,
    )
    assert marked == {
        "notes/b.md": {"consequence": "grounds-lost", "via": "supports", "depth": 1},
        "notes/c.md": {"consequence": "grounds-lost", "via": "extends", "depth": 1},
    }


def test_closure_unions_evidence_and_derivation_hops_transitively() -> None:
    marked = consequence_closure(
        ["catalog/sources/w1"],
        trigger="standing-changed",
        grounding_edges=[_edge("notes/claim.md", "supports", "notes/downstream.md")],
        evidence_dependents={"catalog/sources/w1": ["notes/claim.md"]},
        derivation_children={"catalog/sources/w1": ["digests/w1.md"]},
        typer=_all_grounds_lost,
    )
    assert marked == {
        "notes/claim.md": {"consequence": "grounds-lost", "via": HOP_EVIDENCE, "depth": 1},
        "digests/w1.md": {"consequence": "grounds-lost", "via": HOP_DERIVED, "depth": 1},
        "notes/downstream.md": {"consequence": "grounds-lost", "via": "supports", "depth": 2},
    }


def test_closure_is_cycle_safe_and_never_marks_start_nodes() -> None:
    marked = consequence_closure(
        ["notes/a.md"],
        trigger="claim-retracted",
        grounding_edges=[
            _edge("notes/a.md", "supports", "notes/b.md"),
            _edge("notes/b.md", "supports", "notes/a.md"),
            _edge("notes/b.md", "supports", "notes/b.md"),
        ],
        evidence_dependents={},
        derivation_children={},
        typer=_all_grounds_lost,
    )
    assert marked == {"notes/b.md": {"consequence": "grounds-lost", "via": "supports", "depth": 1}}


def test_closure_terminates_on_a_cycle_that_holds_no_start_node() -> None:
    """The interior cycle, which the start-node guard cannot absorb.

    In `a -> b <-> c` the two-node cycle is entirely downstream of the start, so
    only the visited-set guard can stop it — and the marks it leaves are the
    first (shortest) depth each node was reached at, not the last.
    """
    marked = consequence_closure(
        ["notes/a.md"],
        trigger="claim-changed",
        grounding_edges=[
            _edge("notes/a.md", "supports", "notes/b.md"),
            _edge("notes/b.md", "supports", "notes/c.md"),
            _edge("notes/c.md", "supports", "notes/b.md"),
        ],
        evidence_dependents={},
        derivation_children={},
        typer=_all_grounds_lost,
    )
    assert marked == {
        "notes/b.md": {"consequence": "grounds-lost", "via": "supports", "depth": 1},
        "notes/c.md": {"consequence": "grounds-lost", "via": "supports", "depth": 2},
    }


def test_closure_none_consequence_stops_marking_and_traversal() -> None:
    def contradicts_is_silent(trigger: str, hop: str, *, seed: bool) -> str | None:
        return None if hop == "contradicts" else "grounds-lost"

    marked = consequence_closure(
        ["notes/a.md"],
        trigger="claim-retracted",
        grounding_edges=[
            _edge("notes/a.md", "contradicts", "notes/b.md"),
            _edge("notes/b.md", "supports", "notes/c.md"),
        ],
        evidence_dependents={},
        derivation_children={},
        typer=contradicts_is_silent,
    )
    assert marked == {}


def test_closure_initial_marks_seed_transitive_expansion() -> None:
    marked = consequence_closure(
        (),
        trigger="edge-removed",
        grounding_edges=[_edge("notes/b.md", "supports", "notes/c.md")],
        evidence_dependents={},
        derivation_children={},
        typer=_all_grounds_lost,
        initial_marks={"notes/b.md": "warrant-lost"},
    )
    assert marked == {
        "notes/b.md": {"consequence": "warrant-lost", "via": "seed", "depth": 0},
        "notes/c.md": {"consequence": "grounds-lost", "via": "supports", "depth": 1},
    }


def test_initial_marks_expand_as_already_marked_nodes_not_as_seeds() -> None:
    typer = _RecordingTyper()

    consequence_closure(
        ["notes/a.md"],
        trigger="edge-removed",
        grounding_edges=[
            _edge("notes/a.md", "supports", "notes/c.md"),
            _edge("notes/b.md", "supports", "notes/d.md"),
        ],
        evidence_dependents={},
        derivation_children={},
        typer=typer,
        initial_marks={"notes/b.md": "warrant-lost"},
    )

    # Hops out of the start node carry seed=True; hops out of a node the caller
    # had already marked are second-order and carry seed=False.
    assert typer.calls == [
        ("edge-removed", "supports", True),
        ("edge-removed", "supports", False),
    ]


def test_the_walk_types_every_hop_once_in_breadth_first_order() -> None:
    """Sample the trajectory, not the absorbing state.

    A depth-first walk and a walk that re-typed an already-marked node both
    converge on the same `marked` dict as this one; only the call log tells
    them apart.
    """
    typer = _RecordingTyper()

    marked = consequence_closure(
        ["notes/a.md"],
        trigger="claim-changed",
        grounding_edges=[_edge("notes/c.md", "supports", "notes/e.md")],
        evidence_dependents={"notes/a.md": ["notes/b.md"]},
        derivation_children={"notes/a.md": ["notes/c.md"], "notes/b.md": ["notes/d.md"]},
        typer=typer,
    )

    assert typer.calls == [
        ("claim-changed", HOP_EVIDENCE, True),
        ("claim-changed", HOP_DERIVED, True),
        ("claim-changed", HOP_DERIVED, False),
        ("claim-changed", "supports", False),
    ]
    assert marked == {
        "notes/b.md": {"consequence": "grounds-lost", "via": HOP_EVIDENCE, "depth": 1},
        "notes/c.md": {"consequence": "grounds-lost", "via": HOP_DERIVED, "depth": 1},
        "notes/d.md": {"consequence": "grounds-lost", "via": HOP_DERIVED, "depth": 2},
        "notes/e.md": {"consequence": "grounds-lost", "via": "supports", "depth": 2},
    }


def test_a_dependent_reached_twice_keeps_its_shortest_depth() -> None:
    marked = consequence_closure(
        ["notes/a.md"],
        trigger="claim-changed",
        grounding_edges=[
            _edge("notes/a.md", "supports", "notes/d.md"),
            _edge("notes/a.md", "supports", "notes/b.md"),
            _edge("notes/b.md", "supports", "notes/c.md"),
            _edge("notes/c.md", "supports", "notes/d.md"),
        ],
        evidence_dependents={},
        derivation_children={},
        typer=_all_grounds_lost,
    )
    assert marked["notes/d.md"]["depth"] == 1
    assert marked["notes/c.md"]["depth"] == 2


def test_a_dependent_reachable_by_two_hop_kinds_records_one_deterministic_via() -> None:
    typer = _RecordingTyper()

    marked = consequence_closure(
        ["notes/a.md"],
        trigger="claim-changed",
        grounding_edges=[_edge("notes/a.md", "supports", "notes/b.md")],
        evidence_dependents={"notes/a.md": ["notes/b.md"]},
        derivation_children={},
        typer=typer,
    )

    assert marked == {
        "notes/b.md": {"consequence": "grounds-lost", "via": HOP_EVIDENCE, "depth": 1}
    }
    assert typer.calls == [("claim-changed", HOP_EVIDENCE, True)]


def test_caller_supplied_starts_and_seeds_are_normalized_into_path_space() -> None:
    """Starts and seeds come from callers, so they are the walk's raw boundary.

    The three input maps arrive from `closure_inputs`, already in the one path
    space; a trigger seam hands this function whatever the operation payload
    called the changed note.
    """
    marked = consequence_closure(
        ["./notes/a.md"],
        trigger="edge-removed",
        grounding_edges=[
            _edge("notes/a.md", "supports", "notes/b.md"),
            _edge("notes/x.md", "supports", "notes/y.md"),
        ],
        evidence_dependents={},
        derivation_children={},
        typer=_all_grounds_lost,
        initial_marks={"/notes/x.md": "warrant-lost"},
    )
    assert marked == {
        "notes/b.md": {"consequence": "grounds-lost", "via": "supports", "depth": 1},
        "notes/x.md": {"consequence": "warrant-lost", "via": "seed", "depth": 0},
        "notes/y.md": {"consequence": "grounds-lost", "via": "supports", "depth": 1},
    }


def test_an_identity_start_reaches_nothing_while_its_rendered_path_marks() -> None:
    """The bare `work_id`, not the ULID, is the identity that fails quietly.

    `normalize_path("settles-2016")` returns it unchanged, so a caller that
    handed this walk a catalog identity instead of its `catalog/sources/…`
    rendering would get a plausible node no input map contains. Yielding
    nothing is the fail-closed half; the second assertion is what proves the
    fixture could have marked something.
    """
    rows = [_edge("catalog/sources/settles-2016", "supports", "notes/claim.md")]
    arguments = {
        "trigger": "standing-changed",
        "grounding_edges": rows,
        "evidence_dependents": {},
        "derivation_children": {},
        "typer": _all_grounds_lost,
    }

    assert consequence_closure(["settles-2016"], **arguments) == {}
    assert consequence_closure(["catalog/sources/settles-2016"], **arguments) == {
        "notes/claim.md": {"consequence": "grounds-lost", "via": "supports", "depth": 1}
    }


def test_closure_refuses_an_unknown_trigger() -> None:
    try:
        consequence_closure(
            ["notes/a.md"],
            trigger="claim-improved",
            grounding_edges=[],
            evidence_dependents={},
            derivation_children={},
            typer=_all_grounds_lost,
        )
    except ValueError as exc:
        assert "claim-improved" in str(exc)
    else:
        raise AssertionError("an unrostered trigger should fail")


def _seed_graph(vault: Path, *, with_unchecked: bool = False, with_pending: bool = False) -> None:
    """Seed the v16 mirror the way ERP-A.6's projection reads it: ULID ids, path renderings."""
    state.rebuild_file_concept_mirror(
        vault,
        [
            {"concept_id": CLAIM_ULID, "concept_type": "note", "path": "notes/claim.md"},
            {"concept_id": THESIS_ULID, "concept_type": "note", "path": "notes/thesis.md"},
        ],
    )
    rows = [
        {
            "source_concept_id": CLAIM_ULID,
            "relation_type": "supports",
            "target_path": "notes/thesis.md",
            "check_status": "checked",
            "source_path": "notes/claim.md",
        }
    ]
    if with_unchecked:
        rows.append(
            {
                "source_concept_id": CLAIM_ULID,
                "relation_type": "extends",
                "target_path": "notes/pending.md",
                "check_status": "unchecked",
                "source_path": "notes/claim.md",
            }
        )
    if with_pending:
        rows.append(
            {
                "source_concept_id": CLAIM_ULID,
                "relation_type": "supports",
                "target_path": "notes/unwritten.md",
                "check_status": "checked",
                "source_path": "notes/claim.md",
            }
        )
    state.replace_concept_edges(vault, rows)


def _evidence_set(evidence_id: str, block_ref: str, items: list[str]) -> dict[str, object]:
    return {
        "id": evidence_id,
        "block_ref": block_ref,
        "items": items,
        "type": "single-span",
        "completeness_status": "complete",
        "review_required": False,
        "bind": False,
    }


def _derived(vault: Path, output_id: str, inputs: list[object]) -> None:
    append_explicit_journal_event(
        vault,
        {"event": "derived", "output_id": output_id, "inputs": inputs},
        actor="operation",
        machine="test-machine",
    )


def test_closure_inputs_builds_all_three_union_sources(tmp_path: Path) -> None:
    _seed_graph(tmp_path)
    state.replace_evidence_sets(
        tmp_path,
        [_evidence_set("ev-11111111", "notes/claim.md#^blk-11111111", ["w1#^p0001"])],
    )
    _derived(tmp_path, "digests/w1.md", [{"id": "catalog/sources/w1"}])

    inputs = closure_inputs(tmp_path)

    # Whole-row equality against the projection's three fields: an implementation
    # reading `state.concept_edges` instead would carry `edge_id`, `check_status`
    # and — the failure this pins — the stored ULID in place of the source path.
    assert inputs.grounding_edges == (
        {
            "source_path": "notes/claim.md",
            "target_path": "notes/thesis.md",
            "relation_type": "supports",
        },
    )
    assert CLAIM_ULID not in json.dumps(inputs.grounding_edges)
    assert inputs.evidence_dependents == {"catalog/sources/w1": ("notes/claim.md",)}
    assert inputs.derivation_children == {"catalog/sources/w1": ("digests/w1.md",)}


def test_the_walk_reaches_a_pending_target_that_owns_no_concept_row(tmp_path: Path) -> None:
    """The v16 pending edge: a checked link to a note nobody has written yet.

    Its `target_concept_id` is NULL, so only the durable `target_path` renders
    it and only through the projection. A forward link to an unwritten note is
    legal practice (NODES section 1.6), so the mark writer downstream will meet
    a marked node with no file — better proven here than discovered there.
    """
    _seed_graph(tmp_path, with_pending=True)
    with state.connect(tmp_path) as conn:
        parked = conn.execute(
            "SELECT target_concept_id FROM concept_edges WHERE target_path = 'notes/unwritten.md'"
        ).fetchone()

    # Not degenerate: the row really is parked, unresolved, in the mirror.
    assert parked["target_concept_id"] is None

    inputs = closure_inputs(tmp_path)

    assert consequence_closure(
        ["notes/claim.md"],
        trigger="claim-retracted",
        grounding_edges=inputs.grounding_edges,
        evidence_dependents=inputs.evidence_dependents,
        derivation_children=inputs.derivation_children,
        typer=_all_grounds_lost,
    ) == {
        "notes/thesis.md": {"consequence": "grounds-lost", "via": "supports", "depth": 1},
        "notes/unwritten.md": {"consequence": "grounds-lost", "via": "supports", "depth": 1},
    }


def test_closure_inputs_leaves_unchecked_topology_out_of_the_walk(tmp_path: Path) -> None:
    """The `checked_only=True` default, with the row that makes it visible."""
    _seed_graph(tmp_path, with_unchecked=True)

    assert [edge["relation_type"] for edge in closure_inputs(tmp_path).grounding_edges] == [
        "supports"
    ]


def test_closure_inputs_reads_only_source_span_leaves_of_the_evidence_closure(
    tmp_path: Path,
) -> None:
    _seed_graph(tmp_path)
    state.replace_evidence_sets(
        tmp_path,
        [
            _evidence_set(
                "ev-11111111",
                "notes/claim.md#^blk-11111111",
                ["w1#^p0001", f"code-grounds:run-1:artifact-1:{SPAN_SHA}"],
            )
        ],
    )

    # The code-grounds leaf is a real dependency of the same claim, but it names
    # no catalog work, so only the span leaf can key a standing hop.
    assert closure_inputs(tmp_path).evidence_dependents == {
        "catalog/sources/w1": ("notes/claim.md",)
    }


def test_closure_inputs_follows_nested_evidence_sets_to_their_span_leaves(
    tmp_path: Path,
) -> None:
    _seed_graph(tmp_path)
    state.replace_evidence_sets(
        tmp_path,
        [
            _evidence_set("ev-11111111", "notes/claim.md#^blk-11111111", ["w1#^p0001"]),
            _evidence_set("ev-22222222", "notes/outer.md#^blk-22222222", ["ev-11111111"]),
        ],
    )

    # The outer set cites the inner one and nothing else: a reader that stopped
    # at direct items would leave `notes/outer.md` off the work's dependents.
    assert closure_inputs(tmp_path).evidence_dependents == {
        "catalog/sources/w1": ("notes/claim.md", "notes/outer.md")
    }


def test_closure_inputs_drops_an_evidence_set_that_names_no_block_path(tmp_path: Path) -> None:
    _seed_graph(tmp_path)
    state.replace_evidence_sets(
        tmp_path,
        [
            _evidence_set("ev-11111111", "", ["w1#^p0001"]),
            _evidence_set("ev-22222222", "notes/claim.md#^blk-22222222", ["w1#^p0001"]),
        ],
    )

    # A blank block_ref would otherwise enter the walk as a `''` dependent that
    # every later pass would try to mark.
    assert closure_inputs(tmp_path).evidence_dependents == {
        "catalog/sources/w1": ("notes/claim.md",)
    }


def test_closure_inputs_keeps_only_the_latest_derivation_of_an_output(tmp_path: Path) -> None:
    _seed_graph(tmp_path)
    _derived(tmp_path, "digests/w1.md", [{"id": "catalog/sources/w1"}])
    _derived(tmp_path, "digests/w1.md", [{"id": "catalog/sources/w2"}])

    # Re-deriving an output replaces its inputs; the superseded parent must stop
    # reaching it, or a retracted work marks digests it no longer feeds.
    assert closure_inputs(tmp_path).derivation_children == {
        "catalog/sources/w2": ("digests/w1.md",)
    }


def test_closure_inputs_reads_an_observed_external_edit_as_a_derivation(tmp_path: Path) -> None:
    """The second DAG-writing event, and the one that is self-referential.

    `trusted_writer` records an out-of-band edit with the edited file as its own
    `prior-head` input, so the derivation DAG really does contain self-loops —
    reached from the substrate, not synthesized by a fixture. Dropping this
    event type from the read would leave every externally edited note's
    dependents unreachable.
    """
    _seed_graph(tmp_path)
    append_explicit_journal_event(
        tmp_path,
        {
            "event": "observed_external_edit",
            "output_id": "notes/claim.md",
            "inputs": [
                {"id": "catalog/sources/w1"},
                {"id": "notes/claim.md", "role": "prior-head"},
            ],
        },
        actor="pi",
        machine="test-machine",
    )
    inputs = closure_inputs(tmp_path)

    assert inputs.derivation_children == {
        "catalog/sources/w1": ("notes/claim.md",),
        "notes/claim.md": ("notes/claim.md",),
    }

    # The self-loop is inert: the claim is the start, so the walk passes through
    # its own derivation edge to the thesis instead of marking itself.
    assert consequence_closure(
        ["notes/claim.md"],
        trigger="claim-changed",
        grounding_edges=inputs.grounding_edges,
        evidence_dependents=inputs.evidence_dependents,
        derivation_children=inputs.derivation_children,
        typer=_all_grounds_lost,
    ) == {"notes/thesis.md": {"consequence": "grounds-lost", "via": "supports", "depth": 1}}


def test_closure_inputs_normalizes_the_raw_journal_references(tmp_path: Path) -> None:
    """`output_id` and `inputs[].id` are free-form payload, normalized nowhere else."""
    _seed_graph(tmp_path)
    _derived(tmp_path, "./digests/w1.md", [{"id": "/catalog/sources/w1"}])

    assert closure_inputs(tmp_path).derivation_children == {
        "catalog/sources/w1": ("digests/w1.md",)
    }


def test_closure_inputs_drops_derivation_references_that_name_no_path(tmp_path: Path) -> None:
    _seed_graph(tmp_path)
    _derived(
        tmp_path,
        "digests/w1.md",
        [
            "catalog/sources/bare",
            {"path": "catalog/sources/keyless"},
            {"id": ""},
            {"id": "../up"},
            {"id": 7},
        ],
    )
    _derived(tmp_path, "digests/w2.md", [{"id": "catalog/sources/w2"}])

    # The second event is the other direction: the same reader that drops four
    # unusable references still resolves an ordinary one.
    assert closure_inputs(tmp_path).derivation_children == {
        "catalog/sources/w2": ("digests/w2.md",)
    }


def test_the_walk_over_vault_inputs_marks_path_members_not_identities(tmp_path: Path) -> None:
    """The two halves joined, on the fixture where identity and path disagree.

    `concept_edges` stores the claim as a ULID and the work as a bare `work_id`;
    every node this walk marks has to be the rendered path instead.
    """
    _seed_graph(tmp_path)
    state.replace_evidence_sets(
        tmp_path,
        [_evidence_set("ev-11111111", "notes/claim.md#^blk-11111111", ["w1#^p0001"])],
    )
    _derived(tmp_path, "digests/w1.md", [{"id": "catalog/sources/w1"}])
    inputs = closure_inputs(tmp_path)

    marked = consequence_closure(
        ["catalog/sources/w1"],
        trigger="standing-changed",
        grounding_edges=inputs.grounding_edges,
        evidence_dependents=inputs.evidence_dependents,
        derivation_children=inputs.derivation_children,
        typer=_all_grounds_lost,
    )

    assert marked == {
        "notes/claim.md": {"consequence": "grounds-lost", "via": HOP_EVIDENCE, "depth": 1},
        "digests/w1.md": {"consequence": "grounds-lost", "via": HOP_DERIVED, "depth": 1},
        "notes/thesis.md": {"consequence": "grounds-lost", "via": "supports", "depth": 2},
    }
    assert CLAIM_ULID not in json.dumps(marked)


# --- C.2: the trigger x hop decision table -------------------------------------

_FALLING_TRIGGERS = ("claim-retracted", "standing-changed", "decided-wrong")


def test_hop_kinds_is_the_edge_roster_plus_the_two_non_edge_hops() -> None:
    """The roster literal first, then the partition that makes an eighth verb fail here.

    Set equality, not containment: a hop kind the decision table answers for but
    no relation produces would be a table row nothing can reach, and a relation
    with no table row would raise `unknown hop kind` mid-walk.
    """
    assert HOP_KINDS == (
        "supports",
        "extends",
        "warrant",
        "qualifier",
        "rebuttal",
        "contradicts",
        "tension",
        "evidence",
        "derived",
    )
    assert len(set(HOP_KINDS)) == len(HOP_KINDS)
    assert set(HOP_KINDS) == set(EDGE_RELATIONS) | {HOP_EVIDENCE, HOP_DERIVED}


def test_hop_consequence_encodes_spec_parentheticals() -> None:
    for trigger in _FALLING_TRIGGERS:
        assert hop_consequence(trigger, "supports", seed=True) == "grounds-lost"
        assert hop_consequence(trigger, "extends", seed=True) == "grounds-lost"
        assert hop_consequence(trigger, "warrant", seed=True) == "warrant-lost"
        assert hop_consequence(trigger, "qualifier", seed=True) == "qualifier-regression"
        assert hop_consequence(trigger, "rebuttal", seed=True) is None
        assert hop_consequence(trigger, "contradicts", seed=True) is None
        assert hop_consequence(trigger, "tension", seed=True) is None
        assert hop_consequence(trigger, HOP_EVIDENCE, seed=True) == "grounds-lost"
        assert hop_consequence(trigger, HOP_DERIVED, seed=True) == "grounds-lost"

    # `claim-changed` differs from a falling trigger on exactly one hop: an
    # exception note that changed strengthens the rebuttal rather than falling.
    assert hop_consequence("claim-changed", "rebuttal", seed=True) == "rebuttal-strengthened"
    assert hop_consequence("claim-changed", "supports", seed=True) == "grounds-lost"
    assert hop_consequence("claim-changed", "qualifier", seed=True) == "qualifier-regression"
    assert hop_consequence("claim-changed", HOP_EVIDENCE, seed=True) == "grounds-lost"

    assert hop_consequence("edge-added", "rebuttal", seed=True) == "rebuttal-strengthened"
    assert hop_consequence("edge-added", "supports", seed=True) is None
    assert hop_consequence("edge-added", "extends", seed=True) is None
    assert hop_consequence("edge-added", "warrant", seed=True) is None
    assert hop_consequence("edge-added", "qualifier", seed=True) is None

    assert hop_consequence("edge-removed", "supports", seed=True) == "grounds-lost"
    assert hop_consequence("edge-removed", "extends", seed=True) == "grounds-lost"
    assert hop_consequence("edge-removed", "warrant", seed=True) == "warrant-lost"
    assert hop_consequence("edge-removed", "qualifier", seed=True) == "qualifier-regression"
    assert hop_consequence("edge-removed", "rebuttal", seed=True) is None

    # `evidence` and `derived` are never an edge trigger's own hop — no concept
    # edge is added to or removed from an evidence set or a derivation — so both
    # edge triggers answer None there instead of inheriting falling semantics.
    for hop in (HOP_EVIDENCE, HOP_DERIVED):
        assert hop_consequence("edge-added", hop, seed=True) is None
        assert hop_consequence("edge-removed", hop, seed=True) is None

    # Transitive hops are uniform falling semantics for every trigger: the seed
    # overrides describe what the trigger did to the seed's own neighbours only.
    for trigger in ("claim-changed", "edge-added", "edge-removed", *_FALLING_TRIGGERS):
        assert hop_consequence(trigger, "supports", seed=False) == "grounds-lost"
        assert hop_consequence(trigger, "extends", seed=False) == "grounds-lost"
        assert hop_consequence(trigger, "warrant", seed=False) == "warrant-lost"
        assert hop_consequence(trigger, "qualifier", seed=False) == "qualifier-regression"
        assert hop_consequence(trigger, "rebuttal", seed=False) is None
        assert hop_consequence(trigger, "contradicts", seed=False) is None
        assert hop_consequence(trigger, "tension", seed=False) is None
        assert hop_consequence(trigger, HOP_EVIDENCE, seed=False) == "grounds-lost"
        assert hop_consequence(trigger, HOP_DERIVED, seed=False) == "grounds-lost"


def test_the_decision_table_is_total_and_answers_only_rostered_consequences() -> None:
    """Every cell of TRIGGERS x HOP_KINDS x seed, exhaustively — no cell may escape.

    Exact set equality both ways: `<=` would still pass if a whole consequence
    type had dropped out of the table, and totality is what proves no pair
    raises where the walk would meet it.
    """
    answers = {
        (trigger, hop, seed): hop_consequence(trigger, hop, seed=seed)
        for trigger in TRIGGERS
        for hop in HOP_KINDS
        for seed in (True, False)
    }

    assert len(answers) == len(TRIGGERS) * len(HOP_KINDS) * 2
    assert set(answers.values()) == {None, *CONSEQUENCE_TYPES}


def test_adding_an_edge_can_only_ever_strengthen_a_rebuttal() -> None:
    """The `edge-added` row read across the whole roster, not hop by hop.

    A relation added to the roster but forgotten in the seed-override table
    would inherit falling semantics and report grounds-lost for an edge that was
    *gained*; only a roster-wide assertion catches that.
    """
    assert {hop: hop_consequence("edge-added", hop, seed=True) for hop in HOP_KINDS} == {
        **dict.fromkeys(HOP_KINDS),
        "rebuttal": "rebuttal-strengthened",
    }


def test_rebuttal_strengthened_is_reachable_only_as_a_seed() -> None:
    """The one consequence type no transitive hop may ever produce.

    `rebuttal-strengthened` is a statement about the edge the trigger touched;
    propagating it onwards would relabel unrelated dependents.
    """
    assert {
        hop_consequence(trigger, hop, seed=False) for trigger in TRIGGERS for hop in HOP_KINDS
    } == {None, "grounds-lost", "warrant-lost", "qualifier-regression"}


def test_hop_consequence_rejects_unknown_trigger_and_hop() -> None:
    with pytest.raises(ValueError, match="unknown propagation trigger"):
        hop_consequence("made-up", "supports", seed=True)
    with pytest.raises(ValueError, match="unknown hop kind"):
        hop_consequence("claim-changed", "made-up", seed=True)
    # `seed` is the walk's own label for a start node's own hops, not a hop kind:
    # feeding it in as one has to be rejected rather than answered.
    with pytest.raises(ValueError, match="unknown hop kind"):
        hop_consequence("claim-changed", "seed", seed=True)


def test_hop_consequence_is_the_closure_typer_for_a_real_vault_walk(tmp_path: Path) -> None:
    """The table wired into the walk, on the substrate fixture, at both seed depths.

    `notes/thesis.md` is reached transitively through the claim's `supports`
    edge, so a table that answered only for seeds would leave it unmarked; the
    `rebuttal` edge is the reverse, marked at depth 1 and dead at depth 2.
    """
    _seed_graph(tmp_path)
    state.replace_concept_edges(
        tmp_path,
        [
            {
                "source_concept_id": CLAIM_ULID,
                "relation_type": "supports",
                "target_path": "notes/thesis.md",
                "check_status": "checked",
                "source_path": "notes/claim.md",
            },
            {
                "source_concept_id": THESIS_ULID,
                "relation_type": "rebuttal",
                "target_path": "notes/rebutted.md",
                "check_status": "checked",
                "source_path": "notes/thesis.md",
            },
        ],
    )
    inputs = closure_inputs(tmp_path)
    arguments = {
        "grounding_edges": inputs.grounding_edges,
        "evidence_dependents": inputs.evidence_dependents,
        "derivation_children": inputs.derivation_children,
        "typer": hop_consequence,
    }

    # A retraction falls through `supports` and stops at the rebuttal.
    assert consequence_closure(["notes/claim.md"], trigger="claim-retracted", **arguments) == {
        "notes/thesis.md": {"consequence": "grounds-lost", "via": "supports", "depth": 1}
    }
    # An edge added to the thesis strengthens its own rebuttal and nothing else.
    assert consequence_closure(["notes/thesis.md"], trigger="edge-added", **arguments) == {
        "notes/rebutted.md": {
            "consequence": "rebuttal-strengthened",
            "via": "rebuttal",
            "depth": 1,
        }
    }
    # From the claim, the same `edge-added` reaches the thesis through `supports`
    # — a gained ground, no mark — so the rebuttal one hop further stays dark.
    assert consequence_closure(["notes/claim.md"], trigger="edge-added", **arguments) == {}
