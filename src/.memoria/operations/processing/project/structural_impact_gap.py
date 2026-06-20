"""Gap finding and advisory taxonomy for structural impact."""

from __future__ import annotations

from typing import Any

from operations.processing.project.structural_impact_graph import Edge, Note
from operations.processing.project.structural_impact_payload import (
    ADVISORY_GAP_KINDS,
    CONFIDENT_GAP_KINDS,
)


def gap_taxonomy(
    *,
    notes: dict[str, Note],
    component_edges: list[Edge],
    on_path_nodes: set[str],
    articulation: set[str],
    rows_by_key: dict[str, dict[str, Any]],
    thesis: Note,
    maturity: str,
    refutation_floor_met: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if maturity != "mature":
        return [], []
    findings: list[dict[str, Any]] = []
    advisories: list[dict[str, Any]] = []

    for key in sorted(on_path_nodes):
        note = notes[key]
        row = rows_by_key.get(key, {})
        if note.note_type == "gap" and note.lifecycle != "archived":
            kind = str(note.frontmatter.get("gap_type") or "additive")
            target = advisories if kind in ADVISORY_GAP_KINDS else findings
            if kind in CONFIDENT_GAP_KINDS or kind in ADVISORY_GAP_KINDS:
                target.append(
                    {
                        "kind": kind,
                        "visibility": "advisory" if target is advisories else "shown",
                        "path": note.path,
                        "title": note.title,
                        "impact": row.get("impact", 0),
                    }
                )
        if note.note_type == "claim":
            sources = note.frontmatter.get("sources") or []
            source_count = len(sources) if isinstance(sources, list) else 1 if sources else 0
            support_degree = sum(
                1
                for edge in component_edges
                if edge.relation == "supports" and key in {edge.source, edge.target}
            )
            if source_count == 1 or (source_count == 0 and support_degree <= 1):
                findings.append(
                    {
                        "kind": "fragility",
                        "visibility": "shown",
                        "path": note.path,
                        "title": note.title,
                        "impact": row.get("impact", 0),
                        "reason": "single-source or single-support on the thesis path",
                    }
                )
        if key in articulation and key != thesis.key:
            advisories.append(
                {
                    "kind": "structural",
                    "visibility": "advisory",
                    "path": note.path,
                    "title": note.title,
                    "impact": row.get("impact", 0),
                    "reason": "articulation point in the thesis-rooted argument graph",
                }
            )

    for edge in component_edges:
        if edge.relation == "contradicts":
            source = notes[edge.source]
            target = notes[edge.target]
            findings.append(
                {
                    "kind": "conflict",
                    "visibility": "shown",
                    "path": source.path,
                    "target": target.path,
                    "title": f"{source.title} contradicts {target.title}",
                    "impact": max(
                        rows_by_key.get(edge.source, {}).get("impact", 0),
                        rows_by_key.get(edge.target, {}).get("impact", 0),
                    ),
                }
            )

    if not refutation_floor_met:
        advisories.append(
            {
                "kind": "refutation",
                "visibility": "advisory",
                "path": thesis.path,
                "title": "No addressed contradicts edge touches the active thesis",
                "impact": rows_by_key.get(thesis.key, {}).get("impact", 0),
            }
        )

    ordered = lambda rows: sorted(
        rows, key=lambda r: (-int(r.get("impact", 0)), r["kind"], r["path"])
    )
    return ordered(findings), ordered(advisories)
