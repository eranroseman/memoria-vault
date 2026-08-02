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
slug, or stem. `thesis_rel` is the third boundary this module names: a
project's `thesis:` is path space too, and it is the only reference whose
resolution five separate readers used to own. Retrieval no longer parses
`links:` for itself: `graph_sql.project_slice` and `explore` both read
`propagation.active_project_slices`, whose closure walks the `concept_edges`
mirror this module projects, so the roster question is settled once at the
mirror writer rather than re-answered by each reader.

No first-party imports at module scope, by design, so state.py, cli.py, and
structural_impact_graph.py can import it without a cycle. The path projections
at the bottom read the database, and import `state` inside the function for
exactly that reason.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

EDGE_RELATIONS = frozenset(
    {"supports", "contradicts", "extends", "tension", "warrant", "qualifier", "rebuttal"}
)
LINK_RELATIONS = EDGE_RELATIONS - {"tension"}

# Graph-R11: which side of the argument each verb speaks for. The three
# partition EDGE_RELATIONS exactly — tests/test_edges.py holds that, so a
# seventh verb without a role fails there instead of defaulting to structure.
# `qualifier` is structure, not challenge: EDGES spec section 4 defines it as
# bounding a claim's scope or strength, which is also what ERP-C's
# qualifier-regression semantics read it as.
SUPPORT_RELATIONS = frozenset({"supports"})
CHALLENGE_RELATIONS = frozenset({"contradicts", "rebuttal", "tension"})
STRUCTURE_RELATIONS = frozenset({"warrant", "qualifier", "extends"})

TYPED_WIKILINK_RE = re.compile(r"\[\[([a-z][a-z0-9-]*)::([^\]\|]+)(?:\|[^\]]*)?\]\]")

_LINK_TARGET_URI_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")

CONCEPT_ROOTS = ("catalog/sources/", "notes/", "hubs/", "digests/", "fulltexts/")

EDGES_CONFIG = ".memoria/config/edges.yaml"


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


def thesis_rel(frontmatter: object) -> str:
    """Return a project's `thesis:` as one vault-relative Concept path, or `""`.

    The third namespace boundary this module names, after `strip_wikilink`
    (alias space) and `normalize_link_target` (path space). `thesis:` is **path
    space**, exactly like `links:`: the canonical value is a vault-relative
    Concept path, optionally `[[…]]`-wrapped, and a bare stem completes under
    `notes/`. A title, slug, or prose sentence is refused here and reported by
    the `link` kind in `project.yaml` — a visible validation error rather than
    the silent miss five readers each used to produce differently. `graph_sql`,
    `explore`, `search_index` and both `knowledge` argument readers call this and
    nothing else (issue #1623).

    Returns `""` rather than raising for every rejected value: an unresolvable
    thesis is a reader's miss to report, not its crash. `active_thesis:` is not
    consulted — `project.yaml` retires it.

    `normalize_path` is imported inside the function because this module takes
    no first-party import at module scope, the same reason
    `projected_edge_endpoints` below does it. It cannot raise here:
    `_normalized_link_target` has already rejected every `..` segment that
    `normalize_path` refuses.
    """
    from memoria_vault.runtime.policy.paths import normalize_path

    value = frontmatter.get("thesis") if isinstance(frontmatter, dict) else None
    if isinstance(value, dict):
        value = value.get("target") or value.get("path") or value.get("id") or value.get("note")
    raw = normalize_link_target(value) if isinstance(value, str) else ""
    if not raw:
        return ""
    rel = normalize_path(raw)
    if not rel:
        # `normalize_path('.')` is empty and would complete to `notes/.md`, a
        # file `iter_markdown` really can yield: one absorbing sink for junk.
        return ""
    if "/" not in rel:
        rel = f"notes/{rel}"
    if rel.startswith("catalog/sources/"):
        if rel.count("/") != 2:
            return ""
    elif not rel.endswith(".md"):
        rel += ".md"
    return rel if rel.startswith(CONCEPT_ROOTS) else ""


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


def warrant_absence_threshold(vault: Path) -> int | None:
    """Return the pre-registered warrant-absence threshold, or None when disabled.

    Absence-honesty guard (EDGES spec section 4): warrant absence is never an
    ambient finding until per-type usage crosses a threshold the researcher
    registered, so silence reads as non-use rather than as "this claim has no
    warrant". Disabled is the default and the fallback: an absent, unreadable,
    malformed, or key-missing config all return None, and so does any value that
    is not a positive integer. `True` is refused explicitly — `isinstance(True,
    int)` holds, so a config that meant "on" would otherwise register the
    loudest possible threshold in the guard that exists to stay quiet.
    """
    path = Path(vault) / EDGES_CONFIG
    if not path.is_file():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(data, dict):
        return None
    value = data.get("warrant_absence_threshold")
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None
    return value


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
        endpoints = projected_edge_endpoints(row["source_path"], row["target_path"])
        if endpoints is None:
            continue
        source_path, target_path = endpoints
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


def projected_edge_endpoints(source_path: object, target_path: object) -> tuple[str, str] | None:
    """Return one edge's two endpoints in path space, or ``None`` if it has no rendering.

    The single home for the endpoint rule, and it is public for one reason:
    `graph_sql.neighborhood` reimplements this projection's SQL because its
    eligibility predicate needs columns the public API withholds, so it would
    otherwise carry a second copy of the rule. Two copies is how one Concept ends
    up with two ids in a single path-space answer — a blank endpoint entering an
    undirected walk as a hub, or a stored ``./notes/x.md`` sitting beside the
    ``notes/x.md`` every consumer holds. Both escaped a review here.

    Normalization is not decoration. ``state.replace_concept_edges`` keys every
    row it writes through ``_concept_edge_target_path`` and contract 4 binds
    ``insert_concept_edge`` to the same function, but a PI-owned ``tension`` row
    is written outside that pass by design, so an unnormalized durable
    ``target_path`` is reachable and must project to the one path space.
    """
    from memoria_vault.runtime.policy.paths import normalize_path

    source = normalize_path(str(source_path or ""))
    target = normalize_path(str(target_path or ""))
    return None if not source or not target else (source, target)


def _edge_attributes(raw: object) -> dict[str, Any]:
    """Return one edge's attribute map; anything that is not a JSON object is `{}`."""
    try:
        parsed = json.loads(str(raw))
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}
