#!/usr/bin/env python3
# ruff: noqa: E402
"""Project-gate structural impact cache.

Reads the thesis-rooted argument graph (`links.supports` / `links.contradicts`)
and writes one generated Project gate index note when the derived values change.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_RUNTIME_ROOT = Path(__file__).resolve().parents[3]
if str(_RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(_RUNTIME_ROOT))

from operations.processing.project.structural_impact_analysis import analyze
from operations.processing.project.structural_impact_gap import gap_taxonomy
from operations.processing.project.structural_impact_graph import (
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
    iter_markdown,
    lost_reachability,
    normalize_link,
    normalize_target,
    read_notes,
    relation_values,
    scope_terms,
    truthy,
    values_as_set,
)
from operations.processing.project.structural_impact_payload import (
    ADVISORY_GAP_KINDS,
    CONFIDENT_GAP_KINDS,
    HIGH_IMPACT_THRESHOLD,
    MATURITY_RELATION_THRESHOLD,
    base_payload,
)
from operations.processing.project.structural_impact_render import (
    JSON_END,
    JSON_START,
    generated_path,
    previous_payload,
    render,
    run,
    stable_payload,
)
from operations.processing.project.structural_impact_survey import analyze_survey

__all__ = [
    "ADVISORY_GAP_KINDS",
    "CONFIDENT_GAP_KINDS",
    "HIGH_IMPACT_THRESHOLD",
    "JSON_END",
    "JSON_START",
    "MATURITY_RELATION_THRESHOLD",
    "Edge",
    "Note",
    "adjacency",
    "analyze",
    "analyze_survey",
    "articulation_points",
    "base_payload",
    "build_descriptive_edges",
    "build_edges",
    "build_resolver",
    "component",
    "find_project",
    "find_thesis",
    "gap_taxonomy",
    "generated_path",
    "iter_markdown",
    "lost_reachability",
    "normalize_link",
    "normalize_target",
    "previous_payload",
    "read_notes",
    "relation_values",
    "render",
    "run",
    "scope_terms",
    "stable_payload",
    "truthy",
    "values_as_set",
]


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
