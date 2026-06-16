#!/usr/bin/env python3
"""Delegate ADR-19 hub-threshold findings to the Librarian map lane.

Tier 1 stays report-only in detectors.py. This Tier 2 operation reads those
findings and creates a review-gated Mapper handoff: the agent may draft a hub
proposal in staging, but the canonical hub home (notes/hubs/) remains PI-owned.

    python hub_handoff.py --vault <path> [--threshold 15] [--json]
    python hub_handoff.py --self-test
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
for _path in (_HERE, _RUNTIME_ROOT / "mcp", _RUNTIME_ROOT / "operations" / "lib"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import detectors  # noqa: E402
import tasks_mcp  # noqa: E402

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
    return "\n".join([
        f"- Draft one staged hub proposal at notes/fleeting/maps/hub-proposal-{proposal}.md.",
        "- The proposal should include schema-shaped hub frontmatter as a quoted template: title, type: hub, lifecycle: current, topic, members: [].",
        "- Include only candidate member links and the threshold evidence; do not write curation prose or annotations as if approved.",
        "- Raise or update one Inbox candidate card pointing the PI at the staged proposal.",
        "- Do not write, move, or create files under notes/hubs/; the PI creates or promotes the final hub.",
    ])


def _context(finding: detectors.Finding, topic: str, count: int, threshold: int) -> str:
    return "\n".join([
        "ADR-19 Tier 2 handoff from the Linter hub-threshold detector.",
        f"Finding: {finding.message}",
        f"Topic: {topic}",
        f"Count: {count}; threshold: {threshold}",
        "The Linter is report-only. The map lane may stage a proposal, but notes/hubs/ is review-gated and PI-owned.",
    ])


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
            out.append({"created": False, "error": "unparseable-finding", "finding": finding.__dict__})
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
        out.append({
            "topic": topic,
            "count": count,
            "finding": finding.__dict__,
            "allowed_paths": list(_ALLOWED_PATHS),
            "idempotency_key": key,
            "delegation": delegation,
        })
    return out


def _self_test() -> int:
    import tempfile

    failures = 0

    def ck(label: str, ok: bool) -> None:
        nonlocal failures
        print(("  ok " if ok else "  FAIL ") + label)
        if not ok:
            failures += 1

    with tempfile.TemporaryDirectory() as td:
        v = Path(td)
        lo = v / ".memoria" / "lane-overrides"
        lo.mkdir(parents=True)
        (lo / "librarian.yaml").write_text(
            'profile: memoria-librarian\nrouting:\n  write_scope:\n'
            '    - "inbox/"\n    - "notes/fleeting/"\n', encoding="utf-8")
        (v / "notes/claims").mkdir(parents=True)
        for i in range(2):
            (v / f"notes/claims/t-{i}.md").write_text(
                "---\ntype: claim\nlifecycle: current\nmaturity: seedling\n"
                f"title: T {i}\nsources: ['@x2024']\ntopics: [sleep]\n---\n", encoding="utf-8")
        seen: dict[str, list[str] | str] = {}

        class Result:
            stdout = '{"id":"card-1"}'

        def fake_runner(cmd, **kwargs):
            seen["cmd"] = cmd
            seen["body"] = cmd[cmd.index("--body") + 1]
            return Result()

        rows = handoff_hub_thresholds(v, threshold=2, card_runner=fake_runner)
        body = str(seen.get("body", ""))
        allowed_section = body.split("## Allowed paths", 1)[1].split("## Expected outputs", 1)[0]
        ck("one handoff created", len(rows) == 1 and rows[0]["delegation"].get("created") is True)
        ck("routes to map lane assignee", "memoria-librarian" in seen.get("cmd", []))
        ck("staging paths only", "notes/fleeting/maps/" in allowed_section and "inbox/" in allowed_section and "notes/hubs/" not in allowed_section)
        ck("idempotency key includes topic", "hub-threshold-sleep" in seen.get("cmd", []))
    print("self-test:", "PASS" if failures == 0 else f"{failures} FAILURE(S)")
    return 1 if failures else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", type=Path, help="vault root to scan")
    ap.add_argument("--threshold", type=int, default=15, help="hub-threshold note count")
    ap.add_argument("--json", action="store_true", help="emit handoff results as JSON")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(_self_test())
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
            status = "created" if delegation.get("created") else delegation.get("error", "not-created")
            print(f"{row['topic']}: {status} ({row['idempotency_key']})")
    else:
        print("no hub-threshold handoffs")


if __name__ == "__main__":
    main()
