#!/usr/bin/env python3
"""Emit batch screening projection surfaces.

A high-cardinality report becomes many worklist projection notes under
`system/worklists/<worklist>/`, plus exactly one aggregate Inbox attention prompt.
The PI works the batch in Obsidian Bases by toggling each row's `decision` field.

Usage:
  python3 worklists.py emit --vault VAULT --report report.json --title "Batch title"
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any

from operations.lib import inbox

DECISIONS = ("proposed", "include", "exclude", "maybe", "archived")


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:60] or "worklist"


def _yaml_str(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _item_ref(item: dict[str, Any], index: int) -> str:
    for key in ("item_ref", "target", "path", "citekey", "url", "id"):
        value = str(item.get(key, "")).strip()
        if value:
            return value
    return f"item-{index}"


def _item_title(item: dict[str, Any], ref: str) -> str:
    return str(item.get("title") or item.get("name") or ref).strip()


def _report_items(report: dict[str, Any]) -> list[dict[str, Any]]:
    raw = report.get("items", report.get("rows", []))
    if not isinstance(raw, list):
        raise ValueError("report items/rows must be a list")
    items: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict):
            items.append(item)
        else:
            items.append({"title": str(item), "item_ref": str(item)})
    return items


def emit_worklist(
    vault: Path,
    title: str,
    rows: list[dict[str, Any]],
    source_report: str = "",
    workflow: str = "screen",
    worklist_id: str = "",
) -> dict[str, Any]:
    """Write a file-backed worklist and one aggregate work-prompt.

    Returns the worklist slug, item paths, and the prompt path (or None when the
    deduped prompt already existed). Rows may contain title/name, item_ref/target,
    group, decision, rank, and reason.
    """
    if not rows:
        raise ValueError("a worklist needs at least one row")
    vault = Path(vault)
    slug = _slug(worklist_id or title)
    worklist_dir = vault / "system" / "worklists" / slug
    worklist_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    item_paths: list[Path] = []

    for index, row in enumerate(rows, start=1):
        ref = _item_ref(row, index)
        item_title = _item_title(row, ref)
        decision = str(row.get("decision") or "proposed").strip()
        if decision not in DECISIONS:
            raise ValueError(f"decision must be one of {DECISIONS}")
        rank = int(row.get("rank") or index)
        group = str(row.get("group") or row.get("category") or workflow).strip()
        reason = str(row.get("reason") or row.get("evidence") or "").strip()
        item_source = str(row.get("source_report") or source_report).strip()
        item_slug = _slug(f"{rank:03d}-{item_title}")
        path = worklist_dir / f"{item_slug}.md"
        lines = [
            "---",
            f"title: {_yaml_str(item_title)}",
            "projection: worklist-item",
            "attention_status: open",
            f"decision: {decision}",
            f"worklist: {_yaml_str(slug)}",
            f"item_ref: {_yaml_str(ref)}",
        ]
        if item_source:
            lines.append(f"source_report: {_yaml_str(item_source)}")
        if group:
            lines.append(f"group: {_yaml_str(group)}")
        lines += [f"rank: {rank}", f"created: {today}", "---", ""]
        body = [f"# {item_title}", "", f"Reference: `{ref}`", ""]
        if reason:
            body += ["# Reason", "", reason, ""]
        path.write_text("\n".join(lines + body), encoding="utf-8")
        item_paths.append(path)

    target = f"system/worklists/worklists.base#By worklist · system/worklists/{slug}/"
    prompt = inbox.write_work_prompt(
        vault,
        title=f"Review worklist: {title}",
        action=(
            "Open the worklist Base, review the grouped rows, and set each "
            "item's decision to include, exclude, maybe, or archived."
        ),
        what_happened=(
            f"{len(item_paths)} items were emitted into the {slug} "
            f"batch from {source_report or 'a report'}."
        ),
        raised_by="worklists",
        target=target,
        lane="copi",
        loudness="notice",
        dedupe_slug=f"worklist-{slug}",
    )
    return {"worklist": slug, "items": item_paths, "prompt": prompt}


def emit_report(
    vault: Path, report_path: Path, title: str = "", workflow: str = "screen"
) -> dict[str, Any]:
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    rows = _report_items(report)
    report_title = title or str(report.get("title") or Path(report_path).stem)
    source_report = str(report.get("source_report") or report_path)
    worklist_id = str(report.get("worklist") or report.get("worklist_id") or "")
    return emit_worklist(
        vault,
        report_title,
        rows,
        source_report=source_report,
        workflow=workflow,
        worklist_id=worklist_id,
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Emit ADR-54 batch worklists")
    sub = parser.add_subparsers(dest="cmd")
    emit = sub.add_parser("emit")
    emit.add_argument("--vault", required=True)
    emit.add_argument("--report", required=True)
    emit.add_argument("--title", default="")
    emit.add_argument("--workflow", default="screen")
    args = parser.parse_args(argv)
    if args.cmd == "emit":
        result = emit_report(Path(args.vault), Path(args.report), args.title, args.workflow)
        print(
            json.dumps(
                {
                    "worklist": result["worklist"],
                    "items": [str(p) for p in result["items"]],
                    "prompt": str(result["prompt"]) if result["prompt"] else None,
                },
                indent=2,
            )
        )
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
