"""Packaged alpha.15 capability catalog helpers."""

from __future__ import annotations

import hashlib
import json
import shutil
from importlib import resources
from pathlib import Path
from typing import Any

from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.trusted_writer import append_journal_event, commit_writer_changes
from memoria_vault.runtime.vaultio import parse_frontmatter, safe_read

CAPABILITY_TYPES = {"operation"}
CAPABILITY_HOMES = {"operation": "operations"}
CAPABILITY_PACKAGES = {
    kind: f"memoria_vault.product.capabilities.{home}" for kind, home in CAPABILITY_HOMES.items()
}
CAPABILITY_INDEX_PATH = ".memoria/index/capability-index.json"
PRODUCT_CAPABILITY_PREFIX = "product/capabilities"


def render_capability_index(vault: Path | None = None) -> str:
    """Render packaged capability manifests as a product catalog."""
    payload = {
        "schema_version": 1,
        "generated_by": "memoria_vault.runtime.capabilities.render_capability_index",
        "capabilities": [_catalog_row(item) for item in _capability_resources()],
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def write_capability_index(
    vault: Path,
    *,
    output_path: str = CAPABILITY_INDEX_PATH,
    commit: bool = False,
    machine: str | None = None,
) -> dict[str, Any]:
    """Write an ignored local cache of the product capability catalog."""
    vault = Path(vault)
    output = vault / normalize_path(output_path)
    text = render_capability_index(vault)
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
                "run_id": "projection:capability-index.json",
                "workflow": "generate_capability_index",
                "status": "done",
                "outputs": [normalize_path(output_path)],
            },
            machine=machine,
        )
        commit_id = commit_writer_changes(
            vault,
            "regenerate capability-index.json",
            [],
            machine=machine,
        )
    return {
        "path": normalize_path(output_path),
        "changed": changed,
        "event": event,
        "commit": commit_id,
    }


def check_capability_index(vault: Path, *, output_path: str = CAPABILITY_INDEX_PATH) -> bool:
    path = Path(vault) / normalize_path(output_path)
    return path.is_file() and path.read_text(encoding="utf-8") == render_capability_index(vault)


def read_capability_manifest(capability_type: str, capability_id: str) -> dict[str, Any]:
    """Return one packaged capability manifest with text, frontmatter, and display path."""
    item = _capability_resource(capability_type, capability_id)
    return {
        "path": item["path"],
        "text": item["text"],
        "frontmatter": item["frontmatter"],
        "sha256": _sha256_text(item["text"]),
    }


def iter_capability_manifests(capability_type: str) -> list[dict[str, Any]]:
    """Return packaged manifests for one capability type."""
    if capability_type not in CAPABILITY_HOMES:
        raise ValueError(f"unsupported capability type: {capability_type or '<missing>'}")
    return [
        item
        for item in _capability_resources()
        if item["frontmatter"].get("type") == capability_type
    ]


def _capability_resource(capability_type: str, capability_id: str) -> dict[str, Any]:
    home = CAPABILITY_HOMES.get(capability_type)
    if home is None:
        raise ValueError(f"unsupported capability type: {capability_type or '<missing>'}")
    root = resources.files(CAPABILITY_PACKAGES[capability_type])
    stem = safe_filename(capability_id)
    resource = root / f"{stem}.md"
    display = f"{PRODUCT_CAPABILITY_PREFIX}/{home}/{stem}.md"
    asset_dir = root / stem
    if not resource.is_file() and asset_dir.is_dir():
        _raise_directory_only(f"{PRODUCT_CAPABILITY_PREFIX}/{home}/{stem}", display)
    if not resource.is_file():
        raise FileNotFoundError(display)
    text = resource.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(text)
    return {"path": display, "text": text, "frontmatter": frontmatter}


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


def _capability_resources() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for capability_type, home in CAPABILITY_HOMES.items():
        root = resources.files(CAPABILITY_PACKAGES[capability_type])
        for child in sorted(root.iterdir(), key=lambda item: item.name):
            if child.is_dir():
                sibling = root / f"{child.name}.md"
                if not sibling.is_file() and child.name != "__pycache__":
                    _raise_directory_only(
                        f"{PRODUCT_CAPABILITY_PREFIX}/{home}/{child.name}",
                        f"{PRODUCT_CAPABILITY_PREFIX}/{home}/{child.name}.md",
                    )
                continue
            if not child.name.endswith(".md"):
                continue
            text = child.read_text(encoding="utf-8")
            frontmatter = parse_frontmatter(text)
            if frontmatter.get("type") in CAPABILITY_TYPES:
                items.append(
                    {
                        "path": f"{PRODUCT_CAPABILITY_PREFIX}/{home}/{child.name}",
                        "text": text,
                        "frontmatter": frontmatter,
                    }
                )
    return items


def _raise_directory_only(asset_display: str, sibling_display: str) -> None:
    raise ValueError(
        "directory-only capability manifest is invalid: "
        f"{asset_display}; expected sibling {sibling_display}"
    )


def _catalog_row(item: dict[str, Any]) -> dict[str, Any]:
    frontmatter = item["frontmatter"]
    row = {
        "id": _capability_id(item["path"], frontmatter),
        "type": frontmatter["type"],
        "path": item["path"],
        "title": frontmatter.get("title", ""),
        "description": frontmatter.get("description", ""),
        "check_status": frontmatter.get("check_status", ""),
        "trust": {
            "source": "product",
            "sha256": _sha256_text(item["text"]),
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


def _capability_id(path: str, frontmatter: dict[str, Any]) -> str:
    if frontmatter.get("operation_id"):
        return str(frontmatter["operation_id"])
    return Path(path).stem


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


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
