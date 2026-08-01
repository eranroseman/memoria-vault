#!/usr/bin/env python3
"""Single owner of the concept-relation rosters and links parsing.

EDGE_RELATIONS governs concept_edges.relation_type: the DB CHECK mirrors it
and tests/test_query_substrate.py holds the parity test. LINK_RELATIONS is
the frontmatter-legal subset — everything except 'tension', which is
machine-surfaced and PI-confirmed, never authored in links: frontmatter
(docs/superpowers/specs/2026-07-15-graph-edges-roles-propagation-design.md,
sections 1, 3, 4). Every relation roster in the repo imports from here; a
relation change is a one-file edit, never a hunt across hardcoded sets.

Two target namespaces, two functions — mixing them is a silent bug:
`normalize_link_target` validates *path space* (a vault-relative Concept
target, the only thing `links:` frontmatter may hold), while `strip_wikilink`
strips `[[…]]` syntax in *alias space*, where the value may equally be a title,
slug, or stem. Retrieval closures (`graph_sql`/`explore`) normalize each target
through the path-space function but walk the raw `links:` map without a roster
filter, deliberately: `neighborhood` admits every relation the live CHECK holds
so that tensions stay first-class retrievable, and a fallback closure narrower
than the substrate traversal it stands in for would be a worse reader, not a
stricter one. If one were ever wanted it would be EDGE_RELATIONS, never
LINK_RELATIONS.

Stdlib-only at module scope by design so state.py, cli.py, and
structural_impact_graph.py can import it without a cycle. The path projections
at the bottom read the database, and import `state` inside the function for
exactly that reason.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

EDGE_RELATIONS = frozenset(
    {"supports", "contradicts", "extends", "tension", "warrant", "qualifier", "rebuttal"}
)
LINK_RELATIONS = EDGE_RELATIONS - {"tension"}

TYPED_WIKILINK_RE = re.compile(r"\[\[([a-z][a-z0-9-]*)::([^\]\|]+)(?:\|[^\]]*)?\]\]")

_LINK_TARGET_URI_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def _normalized_link_target(target: str) -> tuple[str, str | None]:
    """Return one local Concept target and an invalidity reason, if any."""
    raw = target.strip()
    wrapped = raw.startswith("[[") or raw.endswith("]]")
    if wrapped:
        if not (raw.startswith("[[") and raw.endswith("]]")):
            return "", "invalid"
        raw = raw[2:-2]
        if "[" in raw or "]" in raw:
            return "", "invalid"
        raw = raw.split("|", 1)[0].split("#", 1)[0].strip()
    elif "[" in raw or "]" in raw:
        return "", "invalid"

    if not raw:
        return "", "empty"

    path = raw.replace("\\", "/")
    if path.startswith(("/", "#")) or path.endswith("/") or _LINK_TARGET_URI_RE.match(raw):
        return "", "invalid"
    if ".." in [part for part in path.split("/") if part and part != "."]:
        return "", "traversal"

    suffix = Path(path.rsplit("/", 1)[-1]).suffix
    if suffix and suffix != ".md":
        return "", "invalid"
    return raw, None


def strip_wikilink(value: str) -> str:
    """Strip ``[[…]]`` braces, alias, and anchor from one reference — syntax only.

    Namespace-free: the result may be a vault-relative path, a title, a slug, or
    a stem, so this applies no path-space rule. Callers that resolve a reference
    through an alias table (structural impact, whose resolver keys on title and
    slug as well as path) need exactly this and must not call
    `normalize_link_target`, which would reject the colons and dotted tails that
    real titles carry. Total over non-strings on the same terms as that function:
    a non-`str` is junk, never `str()`-coerced into a target that never existed.
    """
    if not isinstance(value, str):
        return ""
    raw = value.strip()
    if raw.startswith("[[") and raw.endswith("]]"):
        raw = raw[2:-2]
    return raw.split("|", 1)[0].split("#", 1)[0].strip()


def normalize_link_target(target: str) -> str:
    """Normalize one valid local Concept target, or return an empty string for junk.

    Path space: use `strip_wikilink` instead when the value may be a title or slug.
    """
    if not isinstance(target, str):
        return ""
    return _normalized_link_target(target)[0]


def parse_links(links: object) -> list[tuple[str, str]]:
    """Return ``(relation, normalized target)`` pairs from a links frontmatter map.

    Single owner of links parsing: validation and edge derivation share the
    same six-relation roster and normalization.
    """
    pairs: list[tuple[str, str]] = []
    if not isinstance(links, dict):
        return pairs
    for relation, targets in links.items():
        # A non-str key (YAML `links: {1: [...]}`) needs no isinstance guard of its
        # own: it is not in the roster, so it takes the same skip.
        if relation not in LINK_RELATIONS or not isinstance(targets, list):
            continue
        for target in targets:
            normalized = normalize_link_target(target)
            if normalized:
                pairs.append((relation, normalized))
    return pairs


def parse_typed_wikilinks(body: str) -> list[tuple[str, str]]:
    """Return ``(relation, target)`` pairs from explicit ``[[relation::target]]`` body links.

    Propose-only input: callers mint edge-candidate prompts, never edge rows.
    Non-roster relations and blank targets are skipped.
    """
    pairs: list[tuple[str, str]] = []
    for match in TYPED_WIKILINK_RE.finditer(body):
        # The relation capture is `[a-z][a-z0-9-]*`: already lowercase, never padded.
        relation = match.group(1)
        target = match.group(2).strip()
        if relation in LINK_RELATIONS and target:
            pairs.append((relation, target))
    return pairs


def concept_edge_path_pairs(vault: Path, *, checked_only: bool = True) -> list[dict[str, str]]:
    """Return graph edges projected to durable vault paths — the strict endpoint API.

    Every row is exactly ``source_path``, ``target_path`` and ``relation_type``.
    This is the second namespace boundary this module names — the first being
    `strip_wikilink` (alias space) vs `normalize_link_target` (path space) —
    and it is the one v16 created: `concept_edges` keys its
    endpoints in **identity space**, where a file Concept is a ULID and a catalog
    work is a bare ``work_id``, while every path-facing consumer — retrieval
    walks, propagation closures, the structural graph — works in **path space**.
    `concepts.path` is the map between them, and it is neither the identity nor
    total, so no consumer may substitute one column for the other.
    """
    return [
        {
            "source_path": record["source_path"],
            "target_path": record["target_path"],
            "relation_type": record["relation_type"],
        }
        for record in concept_edge_path_records(vault, checked_only=checked_only)
    ]


def concept_edge_path_records(vault: Path, *, checked_only: bool = True) -> list[dict[str, Any]]:
    """Return the projected paths plus parsed edge attributes, for graph-internal readers.

    The shared query behind both projections. A source is rendered by its own
    mirror row; a target that resolved is rendered by the target mirror row's
    current path, so a rename reconciled by id serves the new path, and a target
    that never resolved keeps the durable ``concept_edges.target_path`` it was
    parked at. An endpoint that renders nowhere is dropped rather than published
    as a blank node. Neither projection emits a concept id or ``edge_id``:
    `attributes` is the only field this one adds, for the `warrant`/`addressed`
    readers that need it.

    ``checked_only`` filters on the edge row's own status; ``False`` is for the
    graph-internal consumers that deliberately walk unchecked/pending topology.
    """
    from memoria_vault.runtime import state
    from memoria_vault.runtime.policy.paths import normalize_path

    if not state.db_path(vault).is_file():
        return []
    with state.connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT source.path AS source_path,
                   COALESCE(NULLIF(target.path, ''), edge.target_path) AS target_path,
                   edge.relation_type AS relation_type,
                   edge.attributes_json AS attributes_json
            FROM concept_edges AS edge
            JOIN concepts AS source ON source.concept_id = edge.source_concept_id
            LEFT JOIN concepts AS target ON target.concept_id = edge.target_concept_id
            WHERE ? = 0 OR edge.check_status = 'checked'
            """,
            (1 if checked_only else 0,),
        ).fetchall()
    records: list[dict[str, Any]] = []
    for row in rows:
        source_path = normalize_path(str(row["source_path"] or ""))
        target_path = normalize_path(str(row["target_path"] or ""))
        if not source_path or not target_path:
            continue
        records.append(
            {
                "source_path": source_path,
                "target_path": target_path,
                "relation_type": str(row["relation_type"]),
                "attributes": _edge_attributes(row["attributes_json"]),
            }
        )
    records.sort(
        key=lambda record: (record["source_path"], record["relation_type"], record["target_path"])
    )
    return records


def _edge_attributes(raw: object) -> dict[str, Any]:
    """Return one edge's attribute map; anything that is not a JSON object is `{}`."""
    try:
        parsed = json.loads(str(raw))
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}
