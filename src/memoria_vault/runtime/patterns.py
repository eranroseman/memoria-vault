"""Prompt-operation composition helpers for the standalone runtime."""

from __future__ import annotations

import datetime
import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any

import yaml

from memoria_vault.runtime.policy import REVIEW_GATED_PREFIXES

PATTERNS_RELDIR = "capabilities/operations"
PREAMBLE_RELPATH = "system/patterns/_preamble.md"
PROVENANCE_RELPATH = "system/logs/patterns.jsonl"
_FM_RE = re.compile(r"^---\n(.*?)\n---\n?", re.S)


def _gated_prefixes(vault: Path) -> tuple[str, ...]:
    try:
        folders = yaml.safe_load(
            (vault / ".memoria" / "schemas" / "folders.yaml").read_text(encoding="utf-8")
        )
        return tuple(folders["gated_prefixes"])
    except Exception:  # noqa: BLE001 -- missing workspace schema falls back to policy default.
        return REVIEW_GATED_PREFIXES


def _parse(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    match = _FM_RE.match(text)
    if not match:
        return {}, text
    return (yaml.safe_load(match.group(1)) or {}), text[match.end() :]


def _is_prompt_operation(body: str) -> bool:
    return "{{input}}" in body


def list_patterns(vault: Path, mode: str = "") -> list[dict[str, Any]]:
    """Return checked prompt operations, optionally filtered by mode."""
    out = []
    directory = vault / PATTERNS_RELDIR
    for path in sorted(directory.glob("*.md")) if directory.is_dir() else []:
        if path.name.startswith("_"):
            continue
        frontmatter, body = _parse(path)
        if frontmatter.get("type") != "operation" or frontmatter.get("check_status") != "checked":
            continue
        if not _is_prompt_operation(body):
            continue
        if mode and frontmatter.get("mode") not in (mode, "both"):
            continue
        out.append(
            {
                "id": path.stem,
                "title": frontmatter.get("title", path.stem),
                "mode": frontmatter.get("mode"),
                "action": frontmatter.get("action"),
                "posture": frontmatter.get("posture"),
                "output_target": frontmatter.get("output_target"),
            }
        )
    return out


def run_pattern(
    vault: Path, pattern_id: str, input_text: str, input_ref: str = ""
) -> dict[str, Any]:
    """Compose preamble plus operation body, enforce gated targets, and log provenance."""
    path = vault / PATTERNS_RELDIR / f"{pattern_id}.md"
    if not path.is_file():
        return {
            "error": "unknown-pattern",
            "pattern": pattern_id,
            "available": [item["id"] for item in list_patterns(vault)],
        }
    frontmatter, body = _parse(path)
    if frontmatter.get("check_status") != "checked":
        return {
            "error": "operation-not-checked",
            "pattern": pattern_id,
            "check_status": frontmatter.get("check_status"),
        }
    if not _is_prompt_operation(body):
        return {
            "error": "unknown-pattern",
            "pattern": pattern_id,
            "available": [item["id"] for item in list_patterns(vault)],
        }

    target = (frontmatter.get("output_target") or "").lstrip("/")
    dry_run = (not target) or target.startswith(_gated_prefixes(vault))
    preamble_file = vault / PREAMBLE_RELPATH
    preamble = preamble_file.read_text(encoding="utf-8") if preamble_file.is_file() else ""
    prompt = body.replace("{{input}}", input_text or f"[see {input_ref}]")
    run_id = str(uuid.uuid4())[:8]
    record = {
        "timestamp": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run_id": run_id,
        "pattern": pattern_id,
        "version": str(frontmatter.get("version", "")),
        "input_ref": input_ref,
        "input_chars": len(input_text or ""),
        "output_target": target,
        "dry_run": dry_run,
    }
    provenance_logged = True
    try:
        log = vault / PROVENANCE_RELPATH
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
    except Exception as exc:  # noqa: BLE001 -- prompt still returns but provenance loss is loud.
        provenance_logged = False
        print(
            f"[patterns] WARNING: provenance write to {PROVENANCE_RELPATH} "
            f"failed for run {run_id} ({pattern_id}): {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )

    result: dict[str, Any] = {
        "run_id": run_id,
        "pattern": pattern_id,
        "prompt": f"{preamble}\n\n---\n\n{prompt}".strip(),
        "output_target": target,
        "dry_run": dry_run,
        "posture": frontmatter.get("posture"),
        "model_hint": frontmatter.get("model_hint") or None,
    }
    if not provenance_logged:
        result["provenance_logged"] = False
    if dry_run:
        result["note"] = (
            "output_target is missing or review-gated - the run is dry-run only; "
            "fix the operation file before promotion"
        )
    return result
