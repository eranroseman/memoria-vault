"""Typed-consequence propagation over the grounding closure and derivation DAG.

The walk is the union EDGES section 5 asks for: `integrity._downstream_events`
inverts the derivation DAG and keeps walking only that, while a claim can also
lose its grounds through a `supports` edge or a cited source's standing. Both
halves live here, and `consequence_closure` is pure so the decision table
(C.2), the mark writer (C.4) and the trigger seams (C.5) can each test their
own rule against literal dicts.

Node space is **path space** — the one `edges.concept_edge_path_pairs`
publishes. `concept_edges` keys its endpoints in identity space, where a file
Concept is a ULID and a catalog work is a bare `work_id`, and `normalize_path`
accepts a bare `work_id` unchanged: normalizing an identity here would mint a
plausible node no consumer's path space contains. Nothing in this module reads
an identity column, and each raw producer is normalized exactly once, at its
own boundary — stored endpoints by the projection, journal references by
`_journal_ref`, caller-supplied starts and seeds by the walk itself.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Collection, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.evidence import evidence_ref_kind, parse_source_span_ref
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.subsystems.lib.edges import concept_edge_path_pairs
from memoria_vault.runtime.trusted_writer import (
    EVENT_DERIVED,
    EVENT_OBSERVED_EXTERNAL_EDIT,
)

CONSEQUENCE_TYPES = (
    "grounds-lost",
    "warrant-lost",
    "qualifier-regression",
    "rebuttal-strengthened",
)
TRIGGERS = (
    "claim-changed",
    "claim-retracted",
    "edge-added",
    "edge-removed",
    "standing-changed",
    "decided-wrong",
)
HOP_EVIDENCE = "evidence"
HOP_DERIVED = "derived"

# EDGES section 5's decision table, split into the answer every hop gives once the
# walk is past the trigger's own neighbourhood and the few cells where being the
# changed node's own hop overrides that. Falling triggers (`claim-retracted`,
# `standing-changed`, `decided-wrong`) need no overrides at all: what they do to a
# seed's dependents is what any hop further out already means.
_TRANSITIVE_CONSEQUENCE: dict[str, str | None] = {
    "supports": "grounds-lost",
    "extends": "grounds-lost",
    "warrant": "warrant-lost",
    "qualifier": "qualifier-regression",
    "rebuttal": None,
    "contradicts": None,
    "tension": None,
    HOP_EVIDENCE: "grounds-lost",
    HOP_DERIVED: "grounds-lost",
}
_SEED_OVERRIDES: dict[str, dict[str, str | None]] = {
    "claim-changed": {"rebuttal": "rebuttal-strengthened"},
    "edge-added": {
        "supports": None,
        "extends": None,
        "warrant": None,
        "qualifier": None,
        "rebuttal": "rebuttal-strengthened",
        HOP_EVIDENCE: None,
        HOP_DERIVED: None,
    },
    "edge-removed": {HOP_EVIDENCE: None, HOP_DERIVED: None},
}
# Derived, not a second literal: the published roster and the table that answers
# for it are the same set by construction, so a hop kind can never be in one
# without the other. `tests/test_propagation.py` pins the members against
# `EDGE_RELATIONS`, which is what an eighth relation verb has to fail against.
HOP_KINDS: tuple[str, ...] = tuple(_TRANSITIVE_CONSEQUENCE)


def hop_consequence(trigger: str, hop: str, *, seed: bool) -> str | None:
    """EDGES section 5 decision table: which trigger+hop yields which consequence.

    The standard `typer` for `consequence_closure`; `None` means no mark and no
    traversal through that hop. `seed` is the walk's own distinction between a
    hop out of the node the trigger named and a hop further downstream.
    """
    if trigger not in TRIGGERS:
        raise ValueError(f"unknown propagation trigger: {trigger!r}")
    if hop not in _TRANSITIVE_CONSEQUENCE:
        raise ValueError(f"unknown hop kind: {hop!r}")
    overrides = _SEED_OVERRIDES.get(trigger, {}) if seed else {}
    return overrides[hop] if hop in overrides else _TRANSITIVE_CONSEQUENCE[hop]


@dataclass(frozen=True)
class ClosureInputs:
    """The three dependency maps the walk unions, all keyed in path space."""

    grounding_edges: tuple[dict[str, str], ...]
    evidence_dependents: dict[str, tuple[str, ...]]
    derivation_children: dict[str, tuple[str, ...]]


def consequence_closure(
    start_ids: Collection[str],
    *,
    trigger: str,
    grounding_edges: Iterable[Mapping[str, Any]],
    evidence_dependents: Mapping[str, Collection[str]],
    derivation_children: Mapping[str, Collection[str]],
    typer: Callable[..., str | None],
    initial_marks: Mapping[str, str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Walk the grounding closure and derivation DAG from fallen nodes to their dependents.

    ``extends`` dependency runs source→target (the extender depends on its
    base), every other relation target→source; ``typer(trigger, hop, seed=...)``
    returning None means no mark and no traversal through that hop.

    Breadth-first from every start, so a dependent records the shortest depth it
    was reached at. One guard makes that safe on a cyclic graph and is the same
    guard that keeps the depth stable: a node already marked, or a start, is
    never marked again, so nothing re-enters the queue and a cycle runs out of
    unmarked nodes instead of running forever. `evidence_item_closure` is the
    same posture one layer down, and both stay total on a graph naming a node no
    input map holds — by reaching nothing through it.
    """
    if trigger not in TRIGGERS:
        raise ValueError(f"unknown propagation trigger: {trigger!r}")
    forward: dict[str, list[tuple[str, str]]] = {}
    for row in grounding_edges:
        source = str(row["source_path"])
        relation = str(row["relation_type"])
        target = str(row["target_path"])
        if relation == "extends":
            forward.setdefault(target, []).append((relation, source))
        else:
            forward.setdefault(source, []).append((relation, target))

    starts = {normalize_path(str(node)) for node in start_ids}
    marked: dict[str, dict[str, Any]] = {}
    queue: deque[tuple[str, int]] = deque((node, 0) for node in sorted(starts))
    for node, consequence in sorted((initial_marks or {}).items()):
        rel = normalize_path(str(node))
        marked[rel] = {"consequence": consequence, "via": "seed", "depth": 0}
        queue.append((rel, 0))
    while queue:
        current, depth = queue.popleft()
        hops = list(forward.get(current, ()))
        hops.extend((HOP_EVIDENCE, str(dep)) for dep in evidence_dependents.get(current, ()))
        hops.extend((HOP_DERIVED, str(dep)) for dep in derivation_children.get(current, ()))
        # Everything reached by a hop is marked before it is queued, so a node
        # still unmarked when it comes off the queue is one the caller named.
        seed = current not in marked
        for hop, dependent in sorted(hops, key=lambda pair: (pair[1], pair[0])):
            if dependent in marked or dependent in starts:
                continue
            consequence = typer(trigger, hop, seed=seed)
            if consequence is None:
                continue
            marked[dependent] = {"consequence": consequence, "via": hop, "depth": depth + 1}
            queue.append((dependent, depth + 1))
    return marked


def closure_inputs(vault: Path) -> ClosureInputs:
    """Assemble the union walk's three inputs from the substrate."""
    vault = Path(vault)

    rows_by_id = {str(row["id"]): row for row in state.evidence_sets(vault)}
    evidence_dependents: dict[str, set[str]] = {}
    for evidence_id, row in rows_by_id.items():
        claim_rel = str(row["block_ref"]).split("#", 1)[0]
        if not claim_rel:
            continue
        for item, _path in state.evidence_item_closure(rows_by_id, evidence_id):
            # Every leaf the closure returns already parsed as one of the three
            # ref kinds; only a span names the catalog work whose standing moves.
            if evidence_ref_kind(item) != "source-span":
                continue
            work_ref = f"catalog/sources/{parse_source_span_ref(item).work_id}"
            evidence_dependents.setdefault(work_ref, set()).add(claim_rel)

    latest: dict[str, dict[str, Any]] = {}
    for event in state.read_event_log(
        vault, event_types=(EVENT_DERIVED, EVENT_OBSERVED_EXTERNAL_EDIT)
    ):
        # Last event wins: re-deriving an output replaces the inputs that feed
        # it, exactly as `integrity._latest_derived` folds the same two types.
        # The two folds stay separate only because C.5 wires integrity to call
        # this module, which a module-scope import back would close into a cycle.
        if output_id := _journal_ref(event.get("output_id")):
            latest[output_id] = event
    derivation_children: dict[str, set[str]] = {}
    for output_id, event in latest.items():
        for row in event.get("inputs") or []:
            input_id = _journal_ref(row.get("id")) if isinstance(row, dict) else ""
            if input_id:
                derivation_children.setdefault(input_id, set()).add(output_id)

    return ClosureInputs(
        grounding_edges=tuple(concept_edge_path_pairs(vault)),
        evidence_dependents=_frozen_dependents(evidence_dependents),
        derivation_children=_frozen_dependents(derivation_children),
    )


def _journal_ref(value: object) -> str:
    """Return one raw journal reference in path space, or ``''`` if it has none.

    Journal payloads are free-form JSON — ``output_id`` and ``inputs[].id`` are
    whatever the writing operation put there — so this is where they enter the
    walk's node space or stop. `edges.projected_edge_endpoints` is the same rule
    on the stored-edge side: a reference that renders nowhere is dropped, never
    published as the blank node every walk would join through.
    """
    if not isinstance(value, str):
        return ""
    try:
        return normalize_path(value)
    except ValueError:
        return ""


def _frozen_dependents(dependents: dict[str, set[str]]) -> dict[str, tuple[str, ...]]:
    """Freeze each dependent set into the one order a set cannot promise.

    Key order is left as built: both producers here iterate a deterministic
    query (`evidence_sets` orders by block ref, the event log by event id), so
    the sets are the only part of this shape that needs an order imposed.
    """
    return {key: tuple(sorted(values)) for key, values in dependents.items()}
