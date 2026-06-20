#!/usr/bin/env python3
"""Delegate ADR-19 hub-threshold findings to the Librarian map lane.

Tier 1 stays report-only in detectors.py. This Tier 2 operation reads those
findings and creates a review-gated map-lane handoff: the agent may draft a hub
proposal in staging, but the canonical hub home (notes/hubs/) remains PI-owned.

    python hub_handoff.py --vault <path> [--threshold 15] [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_RUNTIME_ROOT = _HERE.parents[2]
for _path in (_RUNTIME_ROOT, _RUNTIME_ROOT / "mcp"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import tasks_mcp

from operations.integrity.linter import detectors

_ALLOWED_PATHS = ["notes/fleeting/maps/", "inbox/"]
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
            f"- Draft one staged hub proposal at notes/fleeting/maps/hub-proposal-{proposal}.md.",
            "- The proposal should include schema-shaped hub frontmatter as a quoted template: title, type: hub, lifecycle: current, topic, members: [].",
            "- Include only candidate member links and the threshold evidence; do not write curation prose or annotations as if approved.",
            "- Raise or update one Inbox candidate card pointing the PI at the staged proposal.",
            "- Do not write, move, or create files under notes/hubs/; the PI creates or promotes the final hub.",
        ]
    )


def _context(finding: detectors.Finding, topic: str, count: int, threshold: int) -> str:
    return "\n".join(
        [
            "ADR-19 Tier 2 handoff from the Linter hub-threshold detector.",
            f"Finding: {finding.message}",
            f"Topic: {topic}",
            f"Count: {count}; threshold: {threshold}",
            "The Linter is report-only. The map lane may stage a proposal, but notes/hubs/ is review-gated and PI-owned.",
        ]
    )


def handoff_hub_thresholds(
    vault: Path,
    threshold: int = 15,
    card_runner=subprocess.run,
) -> list[dict]:
    """Create one map-lane delegation per current hub-threshold finding."""
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
        goal = f"Draft hub proposal: {topic}"
        delegation = tasks_mcp.delegate(
            vault,
            "map",
            goal,
            context=_context(finding, topic, count, threshold),
            allowed_paths=list(_ALLOWED_PATHS),
            expected_outputs=_expected_outputs(topic),
            review_checks="Confirm the staged proposal is only a candidate; PI approval is required before anything enters notes/hubs/.",
            idempotency_key=key,
            card_runner=card_runner,
        )
        out.append(
            {
                "topic": topic,
                "count": count,
                "finding": finding.__dict__,
                "allowed_paths": list(_ALLOWED_PATHS),
                "idempotency_key": key,
                "delegation": delegation,
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
            delegation = row.get("delegation", {})
            status = (
                "created" if delegation.get("created") else delegation.get("error", "not-created")
            )
            print(f"{row['topic']}: {status} ({row['idempotency_key']})")
    else:
        print("no hub-threshold handoffs")


if __name__ == "__main__":
    main()
