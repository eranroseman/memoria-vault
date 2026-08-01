#!/usr/bin/env python3
"""Single owner of the concept-relation rosters and links parsing.

EDGE_RELATIONS governs concept_edges.relation_type: the DB CHECK mirrors it
and tests/test_query_substrate.py holds the parity test. LINK_RELATIONS is
the frontmatter-legal subset — everything except 'tension', which is
machine-surfaced and PI-confirmed, never authored in links: frontmatter
(docs/superpowers/specs/2026-07-15-graph-edges-roles-propagation-design.md,
sections 1, 3, 4). Every roster and links-parser in the repo imports from
here; a relation change is a one-file edit, never a hunt across hardcoded
sets.

Stdlib-only by design so state.py, cli.py, and structural_impact_graph.py can
import it without a cycle.
"""

from __future__ import annotations

import re
from pathlib import Path

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


def normalize_link_target(target: str) -> str:
    """Normalize one valid local Concept target, or return an empty string for junk."""
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
