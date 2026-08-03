"""Typed-consequence propagation over the grounding closure and derivation DAG.

The walk is the union EDGES section 5 asks for: `grounding._downstream_events`
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

from collections import Counter, deque
from collections.abc import Callable, Collection, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.attention.inbox import write_finding
from memoria_vault.runtime.evidence import evidence_ref_kind, parse_source_span_ref
from memoria_vault.runtime.policy.audit import EMPTY_SHA256, sha256_file
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.trusted_writer import (
    EVENT_CHECK_FIRED,
    EVENT_DERIVED,
    EVENT_OBSERVED_EXTERNAL_EDIT,
    OperationContext,
    append_explicit_journal_event,
    append_journal_event,
    commit_explicit_writer_changes,
    commit_writer_changes,
    validate_operation_context,
)
from memoria_vault.runtime.vaultio import (
    iter_markdown,
    read_frontmatter,
    split_frontmatter,
    write_frontmatter_doc,
)
from memoria_vault.runtime.vocabulary.edges import concept_edge_path_pairs, thesis_rel

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
        # it, exactly as `grounding._latest_derived` folds the same two types.
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


def _target_aliases(vault: Path, target: str) -> set[str]:
    """Return every path space rendering of one fallen target.

    A copy of `grounding._trace_aliases`, and it stays a copy: C.5 wires
    integrity to call this module, so the import back is the one direction that
    is now closed. Twelve duplicated lines is the price of that edge running one
    way.
    """
    aliases = {target}
    row = state.catalog_source(vault, target)
    if row is None:
        return aliases
    work_id = str(row.get("work_id") or "").strip()
    concept_path = str(row.get("concept_path") or "").strip()
    if work_id:
        aliases.add(f"catalog/sources/{work_id}")
    if concept_path:
        aliases.add(normalize_path(concept_path))
    return aliases


def mark_consequence(
    vault: Path,
    concept_id: str,
    *,
    consequence: str,
    trigger_id: str,
    reason: str,
    append_event: Callable[[dict[str, Any]], Any],
) -> dict[str, Any]:
    """Apply one typed-consequence mark: label, verdict mirror, compat flag.

    A file Concept is labelled in its own frontmatter and mirrored; a Concept the
    vault holds only in the database — a catalog work — is mirrored alone. A
    Concept the mirror has never seen is neither: the walk reaches a pending
    edge's target legally, and every write below is FK-backed onto ``concepts``,
    so one dangling forward link would otherwise abort a whole propagation run.

    Re-marking with the consequence already recorded is a full no-op: no write,
    no event, ``changed=False``. Clearing a label is deliberately absent — re-
    verification is lazy (EDGES section 5), ``set_concept_verdict`` clears the DB
    mirror, and the PI removing the two fields is an observed PI edit.
    """
    if consequence not in CONSEQUENCE_TYPES:
        raise ValueError(f"unknown consequence type: {consequence!r}")
    vault = Path(vault)
    target = normalize_path(concept_id)
    trigger = normalize_path(trigger_id)
    path = vault / target
    unchanged = {
        "concept_id": target,
        "consequence": consequence,
        "changed": False,
        "path": "",
    }
    if not state.concept_exists(vault, target):
        return unchanged
    is_markdown = target.endswith(".md") and path.is_file()
    if is_markdown:
        frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
        if frontmatter.get("stale") is True and frontmatter.get("consequence") == consequence:
            return unchanged
        frontmatter["stale"] = True
        frontmatter["consequence"] = consequence
        write_frontmatter_doc(path, frontmatter, body)
    elif state.concept_consequence(vault, target) == consequence and "stale" in state.concept_flags(
        vault, target
    ):
        return unchanged
    state.set_concept_consequence(vault, target, consequence)
    state.set_concept_flag(vault, target, "stale", reason=reason, trigger_id=trigger)
    target_sha = sha256_file(path) if path.is_file() else EMPTY_SHA256
    # The event shape mirrors `grounding._flag_descendant` so `rebuild_trace_state`
    # keeps `_known_current_hashes` current: without `output_sha256` the next scan
    # reads this mark as a foreign edit on a file the writer itself just wrote.
    append_event(
        {
            "event": EVENT_CHECK_FIRED,
            "check": "typed-consequence",
            "status": "failed",
            "reason": reason,
            "consequence": consequence,
            "target_id": target,
            "target_sha256": target_sha,
            "output_sha256": target_sha,
            "trigger_id": trigger,
            "shadow": False,
            "route": "log",
        }
    )
    if is_markdown:
        # Three readers hold a hash for this file and all three have to move with
        # it, or the writer's own write reads back as somebody else's edit: the
        # journal event above keeps `rebuild_trace_state`'s known hashes current
        # (the scan), the output row keeps the file consumable as checked (the
        # read barrier), and the PI baseline keeps the reconcile quiet.
        state.refresh_output_sha256(vault, target, target_sha)
        baseline = state.file_baseline(vault, target)
        if baseline is not None:
            state.upsert_file_baseline(
                vault,
                target,
                human_sha256=target_sha,
                restriction_keys=list(baseline["restriction_keys"]),
            )
    return {
        "concept_id": target,
        "consequence": consequence,
        "changed": True,
        "path": target if is_markdown else "",
    }


def compute_consequences(vault: Path, target_id: str, *, trigger: str) -> dict[str, dict[str, Any]]:
    """Return the typed closure one fallen target implies, writing nothing.

    The blast radius on its own, which is what ERP-D.1's `decided-wrong` report
    card counts before any label exists. Starts are alias-expanded because a
    catalog work is named three ways — bare ``work_id``, ``catalog/sources/<id>``,
    and its read-scope ``concept_path`` — and only the rendered forms are nodes
    the path-space graph contains.
    """
    vault = Path(vault)
    inputs = closure_inputs(vault)
    return consequence_closure(
        sorted(_target_aliases(vault, normalize_path(target_id))),
        trigger=trigger,
        grounding_edges=inputs.grounding_edges,
        evidence_dependents=inputs.evidence_dependents,
        derivation_children=inputs.derivation_children,
        typer=hop_consequence,
    )


def active_project_slices(vault: Path, *, checked_only: bool = False) -> dict[str, set[str]]:
    """Per active (non-archived) project: its undirected thesis neighbourhood.

    Path space, like the rest of this module and like the ``marked`` map the
    router intersects against. `concept_edge_path_pairs` is the projection that
    answers there; `concept_edges` answers in identity space, where a file
    Concept is a ULID and an unresolved target is NULL, so an adjacency built
    from its endpoint columns would miss every Concept that authored an id and
    would give every pending edge in the vault one shared blank node to join
    through — one slice absorbing another's members. `thesis_rel` is the same
    boundary for the seed: `thesis:` is path space, and it owns the completion
    rules (bare stem under ``notes/``, `.md` tail, roster check).

    Active is the schema-declared ``archived: bool`` on the project document
    (`schemas/types/project.yaml`); ``lifecycle`` is retired and no checked
    Concept can carry it.

    ``checked_only`` selects which topology the closure walks, and the default
    is this module's own need: a cascade's reach must be known *before* the
    graph is settled, so an unchecked edge still says which Concepts the blast
    would land on. A retrieval caller whose surface promises a vetted answer —
    `explore._vetted_project_slice_ids` — passes ``True`` instead and gets the
    closure over confirmed topology only. The returned member set always
    contains the project document itself; a caller that wants members-not-self
    subtracts it, because the container is a real node of the closure and
    dropping it here would hide a project reached through another project.
    """
    vault = Path(vault)
    adjacency: dict[str, set[str]] = {}
    for row in concept_edge_path_pairs(vault, checked_only=checked_only):
        source = row["source_path"]
        target = row["target_path"]
        adjacency.setdefault(source, set()).add(target)
        adjacency.setdefault(target, set()).add(source)
    slices: dict[str, set[str]] = {}
    for path in iter_markdown(vault):
        frontmatter = read_frontmatter(path)
        if frontmatter.get("type") != "project" or frontmatter.get("archived") is True:
            continue
        rel = path.relative_to(vault).as_posix()
        members = {rel}
        if thesis := thesis_rel(frontmatter):
            members.add(thesis)
        queue = deque(members)
        while queue:
            for neighbour in adjacency.get(queue.popleft(), ()):
                if neighbour not in members:
                    members.add(neighbour)
                    queue.append(neighbour)
        slices[rel] = members
    return slices


def route_consequence_cards(
    vault: Path,
    marked: Mapping[str, str],
    *,
    trigger_id: str,
    reason: str,
) -> list[str]:
    """Raise one alert card per active project whose slice this run's marks touched.

    The loudness rule (EDGES section 9): a cascade the researcher's own project
    depends on is worth interrupting for, and one that lands nowhere near it is
    not. Marks outside every active slice route nothing at all — the quiet tier
    is labels and journal, which the caller has already written. A flood is
    bounded by the projects it reached, never by the number of marks: one card
    per (trigger, project), deduped by slug so a re-run of a settled sweep adds
    none. ``block`` is never emitted here; flood mechanics past this routing rule
    are out of scope.

    Returns the vault-relative card paths, for the caller's own commit.
    """
    vault = Path(vault)
    cards: list[str] = []
    for project_rel, members in sorted(active_project_slices(vault).items()):
        hits = {rel: consequence for rel, consequence in marked.items() if rel in members}
        if not hits:
            continue
        summary = ", ".join(
            f"{name}: {count}" for name, count in sorted(Counter(hits.values()).items())
        )
        card = write_finding(
            vault,
            "flag",
            f"Consequence cascade touches {Path(project_rel).stem}",
            (
                f"{len(hits)} concept(s) in this project's slice were marked stale "
                f"({summary}) after: {reason}"
            ),
            "consequence-propagation",
            target=project_rel,
            loudness="alert",
            evidence="\n".join(
                f"- `{rel}` — {consequence}" for rel, consequence in sorted(hits.items())
            ),
            dedupe_slug=f"consequence-{trigger_id}-{project_rel}",
        )
        if card is not None:
            cards.append(card.relative_to(vault).as_posix())
    return cards


def _propagate(
    vault: Path,
    target_id: str,
    *,
    trigger: str,
    reason: str,
    append_event: Callable[[dict[str, Any]], Any],
    commit: Callable[[str, list[str]], str],
    initial_marks: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Compute, mark, and commit one propagation run.

    ``marked`` is what the closure decided, which is not the same as what was
    written: a dependent the mirror has never seen is in the answer and has
    nowhere to carry a label, and a dependent already carrying this consequence
    is a no-op. Only the rels `mark_consequence` actually rewrote reach the
    commit, so a re-run of a settled sweep commits nothing at all.
    """
    vault = Path(vault)
    target = normalize_path(target_id)
    if initial_marks is None:
        marked = compute_consequences(vault, target, trigger=trigger)
    else:
        inputs = closure_inputs(vault)
        marked = consequence_closure(
            (),
            trigger=trigger,
            grounding_edges=inputs.grounding_edges,
            evidence_dependents=inputs.evidence_dependents,
            derivation_children=inputs.derivation_children,
            typer=hop_consequence,
            initial_marks=initial_marks,
        )
    consequences: dict[str, str] = {}
    changed_paths: list[str] = []
    for concept_id in sorted(marked):
        consequence = str(marked[concept_id]["consequence"])
        result = mark_consequence(
            vault,
            concept_id,
            consequence=consequence,
            trigger_id=target,
            reason=reason,
            append_event=append_event,
        )
        consequences[concept_id] = consequence
        if result["path"]:
            changed_paths.append(str(result["path"]))
    # Routing reads closure membership, not the write receipts: a dependent the
    # mirror has never seen is still inside the project's slice and still part of
    # what fell. It is the labels that are conditional, never the loudness.
    cards = route_consequence_cards(vault, consequences, trigger_id=target, reason=reason)
    commit_paths = [*changed_paths, *cards]
    commit_hash = (
        commit(f"propagate typed consequences from {target}", commit_paths) if commit_paths else ""
    )
    return {
        "target_id": target,
        "trigger": trigger,
        "marked": consequences,
        "cards": cards,
        "commit": commit_hash,
    }


def propagate_consequences(
    vault: Path,
    target_id: str,
    *,
    trigger: str,
    reason: str,
    context: OperationContext,
) -> dict[str, Any]:
    """Propagate typed consequences inside an operation envelope."""
    validate_operation_context(vault, context)
    return _propagate(
        vault,
        target_id,
        trigger=trigger,
        reason=reason,
        append_event=lambda event: append_journal_event(vault, event, context=context),
        commit=lambda message, paths: commit_writer_changes(vault, message, paths, context=context),
    )


def propagate_consequences_explicit(
    vault: Path,
    target_id: str,
    *,
    trigger: str,
    reason: str,
    actor: str,
    machine: str,
) -> dict[str, Any]:
    """Propagate typed consequences outside an operation envelope."""
    return _propagate(
        vault,
        target_id,
        trigger=trigger,
        reason=reason,
        append_event=lambda event: append_explicit_journal_event(
            vault, event, actor=actor, machine=machine
        ),
        commit=lambda message, paths: commit_explicit_writer_changes(
            vault, message, paths, actor=actor, machine=machine
        ),
    )


def propagate_edge_change(
    vault: Path,
    *,
    source: str,
    relation_type: str,
    target: str,
    added: bool,
    reason: str,
    context: OperationContext,
) -> dict[str, Any]:
    """Edge add/remove trigger seam for the curate and insert write paths.

    The changed edge names its own dependent — the source for ``extends`` (the
    extender depends on the base it extends), the target for every other
    relation — and that endpoint is seeded with the decision table's *seed*
    answer for this relation before the walk expands from it transitively. A
    seed row that types nothing is the whole event: an added ``supports`` is a
    grounds gain, and gaining grounds marks nobody.
    """
    validate_operation_context(vault, context)
    trigger = "edge-added" if added else "edge-removed"
    source_rel = normalize_path(source)
    target_rel = normalize_path(target)
    dependent = source_rel if relation_type == "extends" else target_rel
    seed = hop_consequence(trigger, relation_type, seed=True)
    if seed is None:
        return {
            "target_id": dependent,
            "trigger": trigger,
            "marked": {},
            "cards": [],
            "commit": "",
        }
    return _propagate(
        vault,
        dependent,
        trigger=trigger,
        reason=reason,
        append_event=lambda event: append_journal_event(vault, event, context=context),
        commit=lambda message, paths: commit_writer_changes(vault, message, paths, context=context),
        initial_marks={dependent: seed},
    )
