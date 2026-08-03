"""Graph loading and resolution helpers for structural impact."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from memoria_vault.runtime.vaultio import iter_markdown as iter_vault_markdown
from memoria_vault.runtime.vaultio import parse_frontmatter, safe_read
from memoria_vault.runtime.vocabulary.edges import LINK_RELATIONS, strip_wikilink

RELATIONS = tuple(sorted(LINK_RELATIONS))


@dataclass(frozen=True)
class Note:
    path: str
    key: str
    stem: str
    title: str
    note_type: str
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
            frontmatter=fm,
        )
    return notes


def normalize_link(raw: Any) -> str:
    """Return one **alias-space** reference from a `thesis:` or `project:` value.

    `build_resolver` keys on title, slug and stem as well as path, so the result
    is not required to look like a vault-relative path — and must never be
    produced by `edges.normalize_link_target`, the path-space validator, which
    refuses the colons and dotted tails real research titles carry. That exact
    delegation shipped a Critical: every such reference normalized to `''` and a
    live project read as brand-new with the validator raising nothing.

    The dict form is reachable through a note's undeclared `project:` key.
    `thesis:` cannot take it — `project.yaml` types that field `link`, which
    accepts a string only — and its resolution belongs to `edges.thesis_rel`
    (issue #1623); this reader is the one place still holding an alias.
    """
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
    # `strip_wikilink` is total over non-strings and strips whitespace, which is
    # this function's whole junk guard: an absent dict key, a blank string and a
    # YAML integer all arrive here and all leave as `""`. A separate pre-check
    # was a second copy of that rule, and mutation-testing found it unkillable.
    value = strip_wikilink(value)
    if value.endswith(".md"):
        value = value[:-3]
    return value.strip("/")


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


def substrate_edges(vault: Path, resolver: dict[str, str]) -> list[Edge]:
    """Return the structural graph's edges from the `concept_edges` substrate.

    The only edge source for structural impact: no frontmatter `links:` text is
    parsed here. This is the namespace boundary the rewire crosses, and it
    crosses it in the safe direction. `edges.concept_edge_path_records` answers
    in **path space** — both endpoints already rendered through `concepts.path`
    and normalized — while `resolver` is an **alias table** whose key domain is
    a strict superset of path space: `build_resolver` keys every note by its
    `.md` path, by that path without the suffix, and by its stem, title and
    slug. So a projected path lands without a second normalization on this side,
    and a durable target parked at a bare stem still finds its note.

    The reverse direction is the one that shipped a Critical: handing an alias —
    a title carrying a colon, a stem with a dotted tail — to the path-space
    validator `edges.normalize_link_target` empties it, and a live project reads
    as brand-new with no error raised. `normalize_link` above is alias space
    and stays out of this function for exactly that reason.

    `checked_only=False` is deliberate: this graph shows the PI the topology
    they have, including the unchecked and pending parts.

    A target that renders in no note but sits under `catalog/sources/` is ERP-B's
    claim→work bridge. It stays in the graph as a virtual node carrying
    connectivity; every note-keyed read in `structural_impact` skips it, and it
    is never published as a node row. Any other unrenderable endpoint — a
    dangling link's pending row — is dropped, as the frontmatter resolver
    dropped it before.
    """
    from memoria_vault.runtime.vocabulary.edges import concept_edge_path_records

    edges: list[Edge] = []
    for record in concept_edge_path_records(vault, checked_only=False):
        source = resolver.get(record["source_path"])
        target_path = record["target_path"]
        target = resolver.get(target_path)
        if target is None and target_path.startswith("catalog/sources/"):
            target = target_path
        if not source or not target or source == target:
            continue
        edges.append(
            Edge(
                source=source,
                target=target,
                relation=record["relation_type"],
                addressed=bool(record["attributes"].get("addressed", True)),
            )
        )
    return edges


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
