"""Rendering and persistence for structural impact."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from memoria.runtime.time import utc_z
from operations.processing.project.structural_impact_analysis import analyze
from operations.processing.project.structural_impact_graph import (
    find_project,
    read_notes,
)

JSON_START = "<!-- memoria-structural-impact:json -->"
JSON_END = "<!-- /memoria-structural-impact:json -->"


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
