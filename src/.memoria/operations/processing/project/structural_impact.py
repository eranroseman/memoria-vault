#!/usr/bin/env python3
"""Project-gate structural impact cache.

Reads the thesis-rooted argument graph (`links.supports` / `links.contradicts`)
and writes one generated Project gate index note when the derived values change.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from memoria.runtime.time import utc_z
from memoria.runtime.vaultio import iter_markdown as iter_vault_markdown
from memoria.runtime.vaultio import parse_frontmatter, safe_read

SKIP_DIRS = {".git", ".memoria", ".obsidian", "node_modules"}
RELATIONS = ("supports", "contradicts")
CONFIDENT_GAP_KINDS = {"additive", "conflict", "fragility"}
ADVISORY_GAP_KINDS = {"structural", "refutation"}
MATURITY_RELATION_THRESHOLD = 5
HIGH_IMPACT_THRESHOLD = 2
JSON_START = "<!-- memoria-structural-impact:json -->"
JSON_END = "<!-- /memoria-structural-impact:json -->"


@dataclass(frozen=True)
class Note:
    path: str
    key: str
    stem: str
    title: str
    note_type: str
    lifecycle: str
    frontmatter: dict[str, Any]


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    relation: str
    addressed: bool


def iter_markdown(vault: Path):
    yield from iter_vault_markdown(vault, SKIP_DIRS)


def read_notes(vault: Path) -> dict[str, Note]:
    notes: dict[str, Note] = {}
    for path in iter_markdown(vault):
        rel = path.relative_to(vault).as_posix()
        text = safe_read(path)
        fm = parse_frontmatter(text)
        if fm.get("generated_by") == "memoria-structural-impact":
            continue
        key = rel[:-3] if rel.endswith(".md") else rel
        notes[key] = Note(
            path=rel,
            key=key,
            stem=path.stem,
            title=str(fm.get("title") or path.stem),
            note_type=str(fm.get("type") or ""),
            lifecycle=str(fm.get("lifecycle") or ""),
            frontmatter=fm,
        )
    return notes


_WIKI = re.compile(r"^\[\[(?P<target>[^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]$")


def normalize_target(raw: Any) -> tuple[str, bool] | None:
    addressed = True
    value: Any = raw
    if isinstance(raw, dict):
        value = (
            raw.get("target")
            or raw.get("to")
            or raw.get("note")
            or raw.get("path")
            or raw.get("link")
            or raw.get("id")
        )
        if "addressed" in raw:
            addressed = bool(raw["addressed"])
        elif "status" in raw:
            addressed = str(raw["status"]).lower() in {"addressed", "closed", "current", "done"}
    if not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    match = _WIKI.match(value)
    if match:
        value = match.group("target")
    value = value.split("|", 1)[0].split("#", 1)[0].strip()
    if value.endswith(".md"):
        value = value[:-3]
    return value.strip("/"), addressed


def build_resolver(notes: dict[str, Note]) -> dict[str, str]:
    resolver: dict[str, str] = {}
    for key, note in notes.items():
        aliases = {
            key,
            note.path,
            note.path[:-3] if note.path.endswith(".md") else note.path,
            note.stem,
            note.title,
            note.frontmatter.get("slug"),
        }
        for alias in aliases:
            if isinstance(alias, str) and alias:
                resolver.setdefault(alias.strip("/"), key)
    return resolver


def relation_values(fm: dict[str, Any], relation: str) -> list[Any]:
    links = fm.get("links")
    if isinstance(links, dict):
        value = links.get(relation, [])
        return value if isinstance(value, list) else [value]
    return []


def build_edges(notes: dict[str, Note], resolver: dict[str, str]) -> list[Edge]:
    edges: list[Edge] = []
    for source, note in notes.items():
        for relation in RELATIONS:
            for raw in relation_values(note.frontmatter, relation):
                normalized = normalize_target(raw)
                if normalized is None:
                    continue
                target_raw, addressed = normalized
                target = resolver.get(target_raw)
                if target and target != source:
                    edges.append(Edge(source=source, target=target, relation=relation, addressed=addressed))
    return edges


def build_descriptive_edges(notes: dict[str, Note], resolver: dict[str, str]) -> list[Edge]:
    edges: list[Edge] = []
    for source, note in notes.items():
        links = note.frontmatter.get("links")
        if not isinstance(links, dict):
            continue
        for relation, values in links.items():
            if not isinstance(values, list):
                values = [values]
            for raw in values:
                normalized = normalize_target(raw)
                if normalized is None:
                    continue
                target_raw, addressed = normalized
                target = resolver.get(target_raw)
                if target and target != source:
                    edges.append(Edge(source=source, target=target, relation=str(relation), addressed=addressed))
    return edges


def normalize_link(raw: Any) -> str:
    normalized = normalize_target(raw)
    return normalized[0] if normalized else ""


def find_project(notes: dict[str, Note], project_arg: str) -> Note:
    resolver = build_resolver(notes)
    needle = project_arg.strip()
    if needle.endswith(".md"):
        needle = needle[:-3]
    key = resolver.get(needle.strip("/"), needle.strip("/"))
    note = notes.get(key)
    if note and note.note_type == "project":
        return note
    matches = [n for n in notes.values() if n.note_type == "project"]
    if len(matches) == 1 and not project_arg:
        return matches[0]
    raise ValueError(f"project note not found: {project_arg}")


def find_thesis(notes: dict[str, Note], project: Note, resolver: dict[str, str]) -> Note | None:
    active = normalize_link(project.frontmatter.get("active_thesis"))
    if active:
        key = resolver.get(active, active)
        note = notes.get(key)
        if note and note.note_type == "thesis":
            return note
    project_aliases = {project.key, project.path, project.stem, str(project.frontmatter.get("slug") or "")}
    candidates: list[Note] = []
    for note in notes.values():
        if note.note_type != "thesis" or note.lifecycle in {"archived", "retracted"}:
            continue
        linked_project = normalize_link(note.frontmatter.get("project"))
        if linked_project in project_aliases or resolver.get(linked_project) == project.key:
            candidates.append(note)
    return sorted(candidates, key=lambda n: n.path)[0] if candidates else None


def adjacency(edges: list[Edge]) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        graph[edge.source].add(edge.target)
        graph[edge.target].add(edge.source)
    return graph


def component(root: str, graph: dict[str, set[str]]) -> set[str]:
    seen = {root}
    queue = deque([root])
    while queue:
        node = queue.popleft()
        for neighbor in graph.get(node, set()):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen


def articulation_points(nodes: set[str], graph: dict[str, set[str]]) -> set[str]:
    index = 0
    indexes: dict[str, int] = {}
    low: dict[str, int] = {}
    parent: dict[str, str | None] = {}
    points: set[str] = set()

    def dfs(node: str):
        nonlocal index
        indexes[node] = low[node] = index
        index += 1
        children = 0
        for neighbor in sorted(graph.get(node, set()) & nodes):
            if neighbor not in indexes:
                parent[neighbor] = node
                children += 1
                dfs(neighbor)
                low[node] = min(low[node], low[neighbor])
                if parent.get(node) is None and children > 1:
                    points.add(node)
                if parent.get(node) is not None and low[neighbor] >= indexes[node]:
                    points.add(node)
            elif neighbor != parent.get(node):
                low[node] = min(low[node], indexes[neighbor])

    for node in sorted(nodes):
        if node not in indexes:
            parent[node] = None
            dfs(node)
    return points


def lost_reachability(root: str, removed: str, nodes: set[str], graph: dict[str, set[str]]) -> int:
    if removed == root:
        return max(0, len(nodes) - 1)
    remaining = nodes - {removed}
    if root not in remaining:
        return len(remaining)
    return len(nodes) - 1 - len(component(root, {n: graph.get(n, set()) & remaining for n in remaining}))


def values_as_set(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, list):
        return {str(v).strip().lower() for v in value if str(v).strip()}
    return {str(value).strip().lower()} if str(value).strip() else set()


def scope_terms(note: Note) -> set[str]:
    fields = ("scope_topics", "topics", "tags", "keywords", "research_area", "methodology")
    terms: set[str] = set()
    for field in fields:
        terms |= values_as_set(note.frontmatter.get(field))
    return terms


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "yes", "true", "y", "done", "sufficient"}


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
                1 for edge in component_edges
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

    ordered = lambda rows: sorted(rows, key=lambda r: (-int(r.get("impact", 0)), r["kind"], r["path"]))
    return ordered(findings), ordered(advisories)


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
    raw = text[start + len(JSON_START):end].strip()
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
