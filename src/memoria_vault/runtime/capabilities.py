"""Generated alpha.12 capability catalog projection."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.trusted_writer import append_journal_event, commit_writer_changes
from memoria_vault.runtime.vaultio import parse_frontmatter, read_frontmatter, safe_read

CAPABILITY_TYPES = {"operation", "skill", "mcp", "workflow"}


def render_ai_catalog(vault: Path) -> str:
    """Render capability Concepts as the generated ai-catalog projection."""
    vault = Path(vault)
    payload = {
        "schema_version": 1,
        "generated_by": "memoria_vault.runtime.capabilities.render_ai_catalog",
        "capabilities": [_catalog_row(vault, path) for path in _capability_paths(vault)],
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def write_ai_catalog(
    vault: Path,
    *,
    output_path: str = "capabilities/ai-catalog.json",
    commit: bool = False,
    machine: str | None = None,
) -> dict[str, Any]:
    """Write the generated ai-catalog projection."""
    vault = Path(vault)
    output = vault / normalize_path(output_path)
    text = render_ai_catalog(vault)
    old = output.read_text(encoding="utf-8") if output.exists() else None
    changed = old != text
    if changed:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    event = None
    commit_id = ""
    if commit:
        event = append_journal_event(
            vault,
            {
                "event": "run",
                "run_id": "projection:ai-catalog.json",
                "workflow": "generate_ai_catalog",
                "status": "done",
                "outputs": [normalize_path(output_path)],
            },
            machine=machine,
        )
        commit_id = commit_writer_changes(
            vault,
            "regenerate ai-catalog.json",
            [output_path],
            machine=machine,
        )
    return {
        "path": normalize_path(output_path),
        "changed": changed,
        "event": event,
        "commit": commit_id,
    }


def check_ai_catalog(vault: Path, *, output_path: str = "capabilities/ai-catalog.json") -> bool:
    path = Path(vault) / normalize_path(output_path)
    return path.is_file() and path.read_text(encoding="utf-8") == render_ai_catalog(vault)


def import_capability(
    vault: Path,
    source_path: Path | str,
    *,
    machine: str | None = None,
    commit: bool = False,
) -> dict[str, Any]:
    """Import a capability only when its trust metadata allows it."""
    vault = Path(vault)
    source = Path(source_path)
    frontmatter = parse_frontmatter(safe_read(source))
    capability_type = str(frontmatter.get("type") or "")
    if capability_type not in CAPABILITY_TYPES:
        raise ValueError(f"unsupported capability type: {capability_type or '<missing>'}")
    trust = frontmatter.get("trust") if isinstance(frontmatter.get("trust"), dict) else {}
    if trust.get("signed") is True:
        raise NotImplementedError("signed capability promotion is not implemented")

    quarantine_path = _unique_path(vault / ".memoria/quarantine/capabilities/imports" / source.name)
    quarantine_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, quarantine_path)
    event = append_journal_event(
        vault,
        {
            "event": "check-fired",
            "check": "capability-import-trust",
            "status": "failed",
            "reason": "unsigned capability import",
            "capability_type": capability_type,
            "target_id": f"capability-import:{source.name}",
            "target_sha256": sha256_file(source),
            "quarantined_id": quarantine_path.relative_to(vault).as_posix(),
        },
        machine=machine,
    )
    commit_id = ""
    if commit:
        commit_id = commit_writer_changes(
            vault, "quarantine unsigned capability import", [], machine=machine
        )
    return {
        "status": "quarantined",
        "quarantine_path": quarantine_path.relative_to(vault).as_posix(),
        "event": event,
        "commit": commit_id,
    }


def _capability_paths(vault: Path) -> list[Path]:
    root = vault / "capabilities"
    if not root.is_dir():
        return []
    return sorted(
        path
        for path in root.glob("*/*.md")
        if read_frontmatter(path).get("type") in CAPABILITY_TYPES
    )


def _catalog_row(vault: Path, path: Path) -> dict[str, Any]:
    frontmatter = read_frontmatter(path)
    rel = path.relative_to(vault).as_posix()
    row = {
        "id": _capability_id(path, frontmatter),
        "type": frontmatter["type"],
        "path": rel,
        "title": frontmatter.get("title", ""),
        "description": frontmatter.get("description", ""),
        "check_status": frontmatter.get("check_status", ""),
        "trust": {
            "source": "local",
            "sha256": sha256_file(path),
        },
    }
    for key in (
        "operation_id",
        "allowed_tools",
        "allowed_paths",
        "allowed_network",
        "runner",
        "model",
        "prompt_version",
        "risk_class",
        "required_checks",
        "resource",
        "tags",
    ):
        if key in frontmatter:
            row[key] = frontmatter[key]
    return row


def _capability_id(path: Path, frontmatter: dict[str, Any]) -> str:
    if frontmatter.get("operation_id"):
        return str(frontmatter["operation_id"])
    return path.stem


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    base = path.with_suffix("")
    suffix = path.suffix
    index = 1
    while True:
        candidate = base.with_name(f"{base.name}-{index}{suffix}")
        if not candidate.exists():
            return candidate
        index += 1
