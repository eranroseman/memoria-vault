"""Survey-mode structural impact analysis."""

from __future__ import annotations

from typing import Any

from operations.processing.project.structural_impact_graph import (
    Note,
    adjacency,
    build_descriptive_edges,
    scope_terms,
    values_as_set,
)
from operations.processing.project.structural_impact_payload import (
    CONFIDENT_GAP_KINDS,
    MATURITY_RELATION_THRESHOLD,
    base_payload,
)


def analyze_survey(notes: dict[str, Note], resolver: dict[str, str], project: Note) -> dict[str, Any]:
    edges = [edge for edge in build_descriptive_edges(notes, resolver) if edge.addressed]
    graph = adjacency(edges)
    project_scope = values_as_set(project.frontmatter.get("scope_topics"))
    scoped = {
        key for key, note in notes.items()
        if key != project.key and (not project_scope or scope_terms(note) & project_scope)
    }
    high_degree = {key for key in scoped if len(graph.get(key, set()) & scoped) >= 2}
    open_scope_gaps = [
        note for key, note in notes.items()
        if key in scoped and note.note_type == "gap" and note.lifecycle != "archived"
    ]
    maturity = "cold-start"
    if len(scoped) >= MATURITY_RELATION_THRESHOLD and high_degree:
        maturity = "mature"
    elif scoped:
        maturity = "developing"
    saturation = "unknown"
    if maturity == "mature":
        saturation = "saturated" if not open_scope_gaps else "unsaturated"
    elif maturity == "developing":
        saturation = "unsaturated"
    rows = []
    for key in sorted(scoped):
        note = notes[key]
        degree = len(graph.get(key, set()) & scoped)
        rows.append(
            {
                "path": note.path,
                "type": note.note_type,
                "title": note.title,
                "lifecycle": note.lifecycle,
                "on_path": False,
                "impact": degree,
                "degree": degree,
                "articulation": False,
                "scope_overlap": bool(project_scope and (scope_terms(note) & project_scope)),
                "open_gap": note.note_type == "gap" and note.lifecycle != "archived",
            }
        )
    payload = base_payload(project, None)
    payload.update(
        {
            "mode": "survey",
            "argument_stage": maturity,
            "evidence_saturation": saturation,
            "displayed_confidence": "load-bearing" if maturity == "mature" else "below-threshold",
            "relation_count": len(edges),
            "scope_overlap_count": len(scoped),
            "open_high_impact_gaps": len(open_scope_gaps),
            "survey_high_degree_count": len(high_degree),
            "saturation_conditions": {
                "mature_graph": maturity == "mature",
                "no_open_scope_gaps": not open_scope_gaps,
            },
            "gap_findings": [] if maturity != "mature" else [
                {
                    "kind": str(note.frontmatter.get("gap_type") or "additive"),
                    "visibility": "shown",
                    "path": note.path,
                    "title": note.title,
                    "impact": len(graph.get(note.key, set()) & scoped),
                }
                for note in open_scope_gaps
                if str(note.frontmatter.get("gap_type") or "additive") in CONFIDENT_GAP_KINDS
            ],
            "advisories": [],
            "nodes": rows,
        }
    )
    return payload
