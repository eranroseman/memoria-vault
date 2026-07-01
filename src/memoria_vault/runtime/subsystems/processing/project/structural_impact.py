#!/usr/bin/env python3
"""Project-gate structural impact cache."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from memoria_vault.runtime.subsystems.processing.project.structural_impact_graph import (
    Edge,
    Note,
    adjacency,
    articulation_points,
    build_descriptive_edges,
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
from memoria_vault.runtime.time import utc_z

CONFIDENT_GAP_KINDS = {"additive", "conflict", "fragility"}
ADVISORY_GAP_KINDS = {"structural", "refutation"}
READINESS_RELATION_THRESHOLD = 5
HIGH_IMPACT_THRESHOLD = 2
JSON_START = "<!-- memoria-structural-impact:json -->"
JSON_END = "<!-- /memoria-structural-impact:json -->"


def _is_open_gap(note: Note) -> bool:
    return note.note_type == "note" and (
        note.frontmatter.get("status") == "needs_review" or bool(note.frontmatter.get("gap_type"))
    )


def _is_claim_note(note: Note) -> bool:
    return note.note_type == "note" and bool(note.frontmatter.get("claim_text"))


def base_payload(project: Note, thesis: Note | None) -> dict[str, Any]:
    return {
        "mode": str(project.frontmatter.get("output_mode") or "thesis"),
        "project": project.path,
        "project_slug": str(project.frontmatter.get("slug") or project.stem),
        "active_thesis": thesis.path if thesis else "",
        "thesis_lifecycle": thesis.lifecycle if thesis else "",
        "argument_stage": "cold-start",
        "evidence_saturation": "unknown",
        "displayed_confidence": "below-threshold",
        "stale": False,
        "relation_count": 0,
        "supports_count": 0,
        "contradicts_count": 0,
        "scope_overlap_count": 0,
        "open_high_impact_gaps": 0,
        "impact_threshold": HIGH_IMPACT_THRESHOLD,
        "refutation_floor_met": False,
        "refutation_sufficiency": False,
        "saturation_conditions": {},
        "gap_findings": [],
        "advisories": [],
        "nodes": [],
    }


def analyze_survey(
    notes: dict[str, Note], resolver: dict[str, str], project: Note
) -> dict[str, Any]:
    edges = [edge for edge in build_descriptive_edges(notes, resolver) if edge.addressed]
    graph = adjacency(edges)
    project_scope = values_as_set(project.frontmatter.get("scope_topics"))
    scoped = {
        key
        for key, note in notes.items()
        if key != project.key and (not project_scope or scope_terms(note) & project_scope)
    }
    high_degree = {key for key in scoped if len(graph.get(key, set()) & scoped) >= 2}
    open_scope_gaps = [note for key, note in notes.items() if key in scoped and _is_open_gap(note)]
    readiness = "cold-start"
    if len(scoped) >= READINESS_RELATION_THRESHOLD and high_degree:
        readiness = "mature"
    elif scoped:
        readiness = "developing"
    saturation = "unknown"
    if readiness == "mature":
        saturation = "saturated" if not open_scope_gaps else "unsaturated"
    elif readiness == "developing":
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
                "open_gap": _is_open_gap(note),
            }
        )
    payload = base_payload(project, None)
    payload |= {
        "mode": "survey",
        "argument_stage": readiness,
        "evidence_saturation": saturation,
        "displayed_confidence": "load-bearing" if readiness == "mature" else "below-threshold",
        "relation_count": len(edges),
        "scope_overlap_count": len(scoped),
        "open_high_impact_gaps": len(open_scope_gaps),
        "survey_high_degree_count": len(high_degree),
        "saturation_conditions": {
            "mature_graph": readiness == "mature",
            "no_open_scope_gaps": not open_scope_gaps,
        },
        "gap_findings": []
        if readiness != "mature"
        else [
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
    return payload


def gap_taxonomy(
    *,
    notes: dict[str, Note],
    component_edges: list[Edge],
    on_path_nodes: set[str],
    articulation: set[str],
    rows_by_key: dict[str, dict[str, Any]],
    thesis: Note,
    readiness: str,
    refutation_floor_met: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if readiness != "mature":
        return [], []
    findings: list[dict[str, Any]] = []
    advisories: list[dict[str, Any]] = []

    for key in sorted(on_path_nodes):
        note = notes[key]
        row = rows_by_key.get(key, {})
        if _is_open_gap(note):
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
        if _is_claim_note(note):
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

    def ordered(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(rows, key=lambda r: (-int(r.get("impact", 0)), r["kind"], r["path"]))

    return ordered(findings), ordered(advisories)


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
        readiness = "cold-start"
    elif (
        len(component_edges) >= READINESS_RELATION_THRESHOLD
        and support_count >= 1
        and contradict_count >= 1
    ):
        readiness = "mature"
    else:
        readiness = "developing"

    points = articulation_points(on_path_nodes, graph)
    rows = []
    rows_by_key: dict[str, dict[str, Any]] = {}
    high_open_gaps = 0
    for note in sorted(notes.values(), key=lambda n: n.path):
        if note.note_type not in {"note", "source", "hub"}:
            continue
        on_path = note.key in on_path_nodes
        degree = len(graph.get(note.key, set()) & on_path_nodes) if on_path else 0
        if on_path:
            impact = lost_reachability(thesis.key, note.key, on_path_nodes, graph)
            if note.key not in points and note.key != thesis.key:
                impact = degree
        else:
            impact = 0
        open_gap = _is_open_gap(note)
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
    condition_1 = readiness == "mature"
    condition_2 = high_open_gaps == 0
    condition_3 = refutation_floor_met and refutation_sufficiency
    saturation = "saturated" if condition_1 and condition_2 and condition_3 else "unsaturated"
    if readiness == "cold-start":
        saturation = "unknown"

    gap_findings, advisories = gap_taxonomy(
        notes=notes,
        component_edges=component_edges,
        on_path_nodes=on_path_nodes,
        articulation=points,
        rows_by_key=rows_by_key,
        thesis=thesis,
        readiness=readiness,
        refutation_floor_met=refutation_floor_met,
    )

    payload = base_payload(project, thesis)
    payload |= {
        "argument_stage": readiness,
        "evidence_saturation": saturation,
        "displayed_confidence": "load-bearing" if readiness == "mature" else "below-threshold",
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
    return payload


def generated_path(vault: Path, project: str) -> Path:
    project_note = find_project(read_notes(vault), project)
    return vault / str(Path(project_note.path).with_name("project-gate-index.md"))


def previous_payload(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    start = text.find(JSON_START)
    end = text.find(JSON_END)
    if start == -1 or end == -1 or end <= start:
        return None
    raw = text[start + len(JSON_START) : end].strip()
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def stable_payload(payload: dict[str, Any]) -> dict[str, Any]:
    stable = json.loads(json.dumps(payload, sort_keys=True))
    stable.pop("computed_at", None)
    return stable


def render(payload: dict[str, Any]) -> str:
    fm = {
        "title": f"Project gate index: {payload['project_slug']}",
        "generated_by": "memoria-structural-impact",
        "project": payload["project"],
        "active_thesis": payload["active_thesis"],
        "computed_at": payload["computed_at"],
        "stale": payload["stale"],
        "argument_stage": payload["argument_stage"],
        "evidence_saturation": payload["evidence_saturation"],
        "displayed_confidence": payload["displayed_confidence"],
        "relation_count": payload["relation_count"],
        "open_high_impact_gaps": payload["open_high_impact_gaps"],
        "gap_findings": len(payload["gap_findings"]),
        "advisories": len(payload["advisories"]),
    }
    body = [
        "---",
        *[f"{key}: {json.dumps(value)}" for key, value in fm.items()],
        "---",
        "",
        f"# Project gate index: {payload['project_slug']}",
        "",
        "| Path | Type | On path | Impact | Degree | Articulation | Open gap |",
        "| --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in payload["nodes"]:
        body.append(
            f"| `{row['path']}` | {row['type']} | {str(row['on_path']).lower()} | "
            f"{row['impact']} | {row['degree']} | {str(row['articulation']).lower()} | "
            f"{str(row['open_gap']).lower()} |"
        )
    body.extend(
        [
            "",
            "## Gap Findings",
            "",
            "| Kind | Visibility | Path | Impact |",
            "| --- | --- | --- | ---: |",
            *[
                f"| {row['kind']} | {row['visibility']} | `{row['path']}` | {row['impact']} |"
                for row in payload["gap_findings"]
            ],
            "",
            "## Advisories",
            "",
            "| Kind | Path | Impact |",
            "| --- | --- | ---: |",
            *[
                f"| {row['kind']} | `{row['path']}` | {row['impact']} |"
                for row in payload["advisories"]
            ],
            "",
            JSON_START,
            json.dumps(payload, indent=2, sort_keys=True),
            JSON_END,
            "",
        ]
    )
    return "\n".join(body)


def run(
    vault: Path,
    project: str = "",
    *,
    now: datetime | None = None,
    apply: bool = True,
) -> dict[str, Any]:
    payload = analyze(vault, project)
    out = generated_path(vault, project or payload["project"])
    previous = previous_payload(out)
    if previous and stable_payload(previous) == stable_payload(payload):
        payload["computed_at"] = previous.get("computed_at", "")
        return {"changed": False, "path": out.relative_to(vault).as_posix(), "payload": payload}
    payload["computed_at"] = utc_z(now)
    if apply:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(payload), encoding="utf-8")
    return {"changed": apply, "path": out.relative_to(vault).as_posix(), "payload": payload}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, default=Path("."))
    parser.add_argument("--project", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = run(args.vault, args.project, apply=not args.dry_run)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
    else:
        status = "updated" if result["changed"] else "unchanged"
        print(f"{status}: {result['path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
