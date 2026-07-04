"""Prompt-operation composition helpers for the standalone runtime."""

from __future__ import annotations

import datetime
import re
import sys
import uuid
from pathlib import Path
from typing import Any

import yaml

from memoria_vault.runtime.capabilities import iter_capability_manifests, read_capability_manifest
from memoria_vault.runtime.jsonl import append_jsonl
from memoria_vault.runtime.policy import REVIEW_GATED_PREFIXES

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
    for item in iter_capability_manifests("operation"):
        frontmatter, body = item["frontmatter"], split_manifest_body(item["text"])
        if frontmatter.get("type") != "operation" or frontmatter.get("check_status") != "checked":
            continue
        if not _is_prompt_operation(body):
            continue
        if mode and frontmatter.get("mode") not in (mode, "both"):
            continue
        out.append(
            {
                "id": frontmatter.get("operation_id") or Path(item["path"]).stem,
                "title": frontmatter.get("title", Path(item["path"]).stem),
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
    try:
        item = read_capability_manifest("operation", pattern_id)
    except FileNotFoundError:
        return {
            "error": "unknown-pattern",
            "pattern": pattern_id,
            "available": [item["id"] for item in list_patterns(vault)],
        }
    frontmatter, body = item["frontmatter"], split_manifest_body(item["text"])
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
        append_jsonl(vault / PROVENANCE_RELPATH, [record])
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


def split_manifest_body(text: str) -> str:
    match = _FM_RE.match(text)
    return text[match.end() :] if match else text
