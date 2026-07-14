"""Graph loading and resolution helpers for structural impact."""

from __future__ import annotations

import re
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from memoria_vault.runtime.vaultio import iter_markdown as iter_vault_markdown
from memoria_vault.runtime.vaultio import parse_frontmatter, safe_read

RELATIONS = ("supports", "contradicts")


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


def read_notes(vault: Path) -> dict[str, Note]:
    notes: dict[str, Note] = {}
    for path in iter_vault_markdown(vault):
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


def build_edges(notes: dict[str, Note], resolver: dict[str, str]) -> list[Edge]:
    return [
        edge for edge in build_descriptive_edges(notes, resolver) if edge.relation in RELATIONS
    ]


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
                    edges.append(
                        Edge(
                            source=source,
                            target=target,
                            relation=str(relation),
                            addressed=addressed,
                        )
                    )
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
    active = normalize_link(
        project.frontmatter.get("thesis") or project.frontmatter.get("active_thesis")
    )
    if active:
        key = resolver.get(active, active)
        note = notes.get(key)
        if note and note.note_type == "note":
            return note
    project_aliases = {
        project.key,
        project.path,
        project.stem,
        str(project.frontmatter.get("slug") or ""),
    }
    candidates: list[Note] = []
    for note in notes.values():
        if note.note_type != "note" or note.frontmatter.get("status") == "rejected":
            continue
        if note.frontmatter.get("role") != "thesis":
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
    return (
        len(nodes)
        - 1
        - len(component(root, {n: graph.get(n, set()) & remaining for n in remaining}))
    )


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
