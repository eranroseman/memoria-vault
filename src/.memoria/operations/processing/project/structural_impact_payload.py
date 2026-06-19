"""Shared payload constants and skeletons for structural impact."""

from __future__ import annotations

from typing import Any

from structural_impact_graph import Note

CONFIDENT_GAP_KINDS = {"additive", "conflict", "fragility"}
ADVISORY_GAP_KINDS = {"structural", "refutation"}
MATURITY_RELATION_THRESHOLD = 5
HIGH_IMPACT_THRESHOLD = 2


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
