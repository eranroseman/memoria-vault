"""Thesis-mode structural impact analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from operations.processing.project.structural_impact_gap import gap_taxonomy
from operations.processing.project.structural_impact_graph import (
    adjacency,
    articulation_points,
    build_edges,
    build_resolver,
    component,
    find_project,
    find_thesis,
    lost_reachability,
    read_notes,
    scope_terms,
    truthy,
    values_as_set,
)
from operations.processing.project.structural_impact_payload import (
    HIGH_IMPACT_THRESHOLD,
    MATURITY_RELATION_THRESHOLD,
    base_payload,
)
from operations.processing.project.structural_impact_survey import analyze_survey


def analyze(vault: Path, project_arg: str = "") -> dict[str, Any]:
    notes = read_notes(vault)
    resolver = build_resolver(notes)
    project = find_project(notes, project_arg)
    if str(project.frontmatter.get("output_mode") or "") == "survey":
        return analyze_survey(notes, resolver, project)
    thesis = find_thesis(notes, project, resolver)
    if thesis is None:
        payload = base_payload(project, None)
        payload["argument_stage"] = "cold-start"
        payload["evidence_saturation"] = "unknown"
        payload["displayed_confidence"] = "below-threshold"
        return payload

    edges = [edge for edge in build_edges(notes, resolver) if edge.addressed]
    graph = adjacency(edges)
    on_path_nodes = component(thesis.key, graph)
    component_edges = [
        edge for edge in edges if edge.source in on_path_nodes and edge.target in on_path_nodes
    ]
    support_count = sum(1 for edge in component_edges if edge.relation == "supports")
    contradict_count = sum(1 for edge in component_edges if edge.relation == "contradicts")

    project_scope = values_as_set(project.frontmatter.get("scope_topics"))
    scope_overlap = 0
    if project_scope:
        scope_overlap = sum(1 for key in on_path_nodes if scope_terms(notes[key]) & project_scope)

    if not component_edges or (project_scope and scope_overlap == 0):
        maturity = "cold-start"
    elif (
        len(component_edges) >= MATURITY_RELATION_THRESHOLD
        and support_count >= 1
        and contradict_count >= 1
    ):
        maturity = "mature"
    else:
        maturity = "developing"

    points = articulation_points(on_path_nodes, graph)
    rows = []
    rows_by_key: dict[str, dict[str, Any]] = {}
    high_open_gaps = 0
    for note in sorted(notes.values(), key=lambda n: n.path):
        if note.note_type not in {"claim", "gap", "thesis", "source", "hub"}:
            continue
        on_path = note.key in on_path_nodes
        degree = len(graph.get(note.key, set()) & on_path_nodes) if on_path else 0
        if on_path:
            impact = lost_reachability(thesis.key, note.key, on_path_nodes, graph)
            if note.key not in points and note.key != thesis.key:
                impact = degree
        else:
            impact = 0
        open_gap = note.note_type == "gap" and note.lifecycle != "archived"
        if open_gap and on_path and impact >= HIGH_IMPACT_THRESHOLD:
            high_open_gaps += 1
        row = {
            "path": note.path,
            "type": note.note_type,
            "title": note.title,
            "lifecycle": note.lifecycle,
            "on_path": on_path,
            "impact": impact,
            "degree": degree,
            "articulation": note.key in points,
            "scope_overlap": bool(project_scope and (scope_terms(note) & project_scope)),
            "open_gap": open_gap,
        }
        rows.append(row)
        rows_by_key[note.key] = row

    refutation_floor_met = any(
        edge.relation == "contradicts" and thesis.key in {edge.source, edge.target}
        for edge in component_edges
    )
    refutation_sufficiency = truthy(
        project.frontmatter.get("refutation_sufficiency")
        or thesis.frontmatter.get("refutation_sufficiency")
    )
    condition_1 = maturity == "mature"
    condition_2 = high_open_gaps == 0
    condition_3 = refutation_floor_met and refutation_sufficiency
    saturation = "saturated" if condition_1 and condition_2 and condition_3 else "unsaturated"
    if maturity == "cold-start":
        saturation = "unknown"

    gap_findings, advisories = gap_taxonomy(
        notes=notes,
        component_edges=component_edges,
        on_path_nodes=on_path_nodes,
        articulation=points,
        rows_by_key=rows_by_key,
        thesis=thesis,
        maturity=maturity,
        refutation_floor_met=refutation_floor_met,
    )

    payload = base_payload(project, thesis)
    payload.update(
        {
            "argument_stage": maturity,
            "evidence_saturation": saturation,
            "displayed_confidence": "load-bearing" if maturity == "mature" else "below-threshold",
            "relation_count": len(component_edges),
            "supports_count": support_count,
            "contradicts_count": contradict_count,
            "scope_overlap_count": scope_overlap,
            "open_high_impact_gaps": high_open_gaps,
            "impact_threshold": HIGH_IMPACT_THRESHOLD,
            "refutation_floor_met": refutation_floor_met,
            "refutation_sufficiency": refutation_sufficiency,
            "saturation_conditions": {
                "mature_graph": condition_1,
                "no_high_impact_open_gaps": condition_2,
                "refutation_sufficiency": condition_3,
            },
            "gap_findings": gap_findings,
            "advisories": advisories,
            "nodes": rows,
        }
    )
    return payload
