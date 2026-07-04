#!/usr/bin/env python3
"""Turn ADR-126 hub-threshold findings into map-proposal requests.

Tier 1 stays report-only in detectors.py. This Tier 2 operation reads those
findings and creates a review-gated proposal handoff: an operation may draft a
hub proposal in staging, but the canonical hub home (knowledge/hubs/) remains
PI-owned.

    python hub_handoff.py --vault <path> [--threshold 15] [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from memoria_vault.runtime.subsystems.integrity.linter import detectors

_ALLOWED_PATHS = ["knowledge/notes/maps/"]
_FINDING_RE = re.compile(r"topic '(.+)' has (\d+) notes")


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:64].strip("-") or "topic"


def _parse_hub_threshold(finding: detectors.Finding) -> dict | None:
    m = _FINDING_RE.search(finding.message)
    if not m:
        return None
    return {"topic": m.group(1), "count": int(m.group(2))}


def _expected_outputs(topic: str) -> str:
    proposal = _slug(topic)
    return "\n".join(
        [
            f"- Draft one unchecked note proposal at knowledge/notes/maps/hub-proposal-{proposal}.md.",
            "- The proposal should include schema-shaped hub frontmatter as a quoted template: title, type: hub, id, tags: [], links: {}, tag.",
            "- Include only candidate member links and the threshold evidence; do not write curation prose or annotations as if approved.",
            "- Do not write, move, or create files under knowledge/hubs/; the PI curates the final hub.",
        ]
    )


def _context(finding: detectors.Finding, topic: str, count: int, threshold: int) -> str:
    return "\n".join(
        [
            "ADR-126 Tier 2 handoff from the Linter hub-threshold detector.",
            f"Finding: {finding.message}",
            f"Topic: {topic}",
            f"Count: {count}; threshold: {threshold}",
            "The Linter is report-only. A map-proposal operation may stage a "
            "proposal, but knowledge/hubs/ is PI-curated.",
        ]
    )


def handoff_hub_thresholds(
    vault: Path,
    threshold: int = 15,
) -> list[dict]:
    """Return one map-proposal handoff payload per current hub-threshold finding."""
    out: list[dict] = []
    for finding in detectors.hub_threshold(vault, threshold=threshold):
        parsed = _parse_hub_threshold(finding)
        if parsed is None:
            out.append(
                {"created": False, "error": "unparseable-finding", "finding": finding.__dict__}
            )
            continue
        topic = parsed["topic"]
        count = parsed["count"]
        key = f"hub-threshold-{_slug(topic)}"
        out.append(
            {
                "topic": topic,
                "count": count,
                "finding": finding.__dict__,
                "operation_id": "suggest-hubs",
                "posture": "mapping",
                "goal": f"Draft hub proposal: {topic}",
                "context": _context(finding, topic, count, threshold),
                "allowed_paths": list(_ALLOWED_PATHS),
                "expected_outputs": _expected_outputs(topic),
                "review_checks": "Confirm the proposal is only a suggestion; PI curation is "
                "required before anything enters knowledge/hubs/.",
                "idempotency_key": key,
            }
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--vault", type=Path, help="vault root to scan")
    ap.add_argument("--threshold", type=int, default=15, help="hub-threshold note count")
    ap.add_argument("--json", action="store_true", help="emit handoff results as JSON")
    args = ap.parse_args()
    if not args.vault:
        ap.error("provide --vault <path>")
    if not args.vault.is_dir():
        sys.exit(f"not a directory: {args.vault}")
    rows = handoff_hub_thresholds(args.vault, threshold=args.threshold)
    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    elif rows:
        for row in rows:
            print(f"{row['topic']}: handoff ({row['idempotency_key']})")
    else:
        print("no hub-threshold handoffs")


if __name__ == "__main__":
    main()
