"""Packaged capability catalog helpers."""

from __future__ import annotations

import hashlib
import json
from importlib import resources
from pathlib import Path
from typing import Any

from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.trusted_writer import (
    OperationContext,
    append_journal_event,
    commit_writer_changes,
    validate_operation_context,
)
from memoria_vault.runtime.vaultio import parse_frontmatter

CAPABILITY_TYPE = "operation"
CAPABILITY_HOME = "operations"
CAPABILITY_PACKAGE = "memoria_vault.product.capabilities.operations"
CAPABILITY_INDEX_PATH = ".memoria/index/capability-index.json"
PRODUCT_CAPABILITY_PREFIX = "product/capabilities"
DEFAULT_RUNNER_POLICY = {
    "test": {"provider": "local", "model": "deterministic-fixture", "temperature": 0},
    "live": {"provider": "gateway", "model": "deterministic-fixture", "temperature": 0},
}


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
    context: OperationContext,
    output_path: str = CAPABILITY_INDEX_PATH,
    commit: bool = False,
) -> dict[str, Any]:
    """Write an ignored local cache of the product capability catalog."""
    validate_operation_context(vault, context)
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
                "workflow": "generate_capability_index",
                "status": "done",
                "outputs": [normalize_path(output_path)],
            },
            context=context,
        )
        commit_id = commit_writer_changes(
            vault,
            "regenerate capability-index.json",
            [],
            context=context,
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
    if capability_type != CAPABILITY_TYPE:
        raise ValueError(f"unsupported capability type: {capability_type or '<missing>'}")
    item = _capability_resource(capability_id)
    return {
        "path": item["path"],
        "text": item["text"],
        "frontmatter": item["frontmatter"],
        "sha256": _sha256_text(item["text"]),
    }


def iter_capability_manifests(capability_type: str) -> list[dict[str, Any]]:
    """Return packaged manifests for one capability type."""
    if capability_type != CAPABILITY_TYPE:
        raise ValueError(f"unsupported capability type: {capability_type or '<missing>'}")
    return list(_capability_resources())


def _capability_resource(capability_id: str) -> dict[str, Any]:
    root = resources.files(CAPABILITY_PACKAGE)
    stem = safe_filename(capability_id)
    resource = root / f"{stem}.md"
    display = f"{PRODUCT_CAPABILITY_PREFIX}/{CAPABILITY_HOME}/{stem}.md"
    asset_dir = root / stem
    if not resource.is_file() and asset_dir.is_dir():
        _raise_directory_only(f"{PRODUCT_CAPABILITY_PREFIX}/{CAPABILITY_HOME}/{stem}", display)
    if not resource.is_file():
        raise FileNotFoundError(display)
    text = resource.read_text(encoding="utf-8")
    frontmatter = _manifest_frontmatter(text)
    return {"path": display, "text": text, "frontmatter": frontmatter}


def _capability_resources() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    root = resources.files(CAPABILITY_PACKAGE)
    for child in sorted(root.iterdir(), key=lambda item: item.name):
        if child.is_dir():
            sibling = root / f"{child.name}.md"
            if not sibling.is_file() and child.name != "__pycache__":
                _raise_directory_only(
                    f"{PRODUCT_CAPABILITY_PREFIX}/{CAPABILITY_HOME}/{child.name}",
                    f"{PRODUCT_CAPABILITY_PREFIX}/{CAPABILITY_HOME}/{child.name}.md",
                )
            continue
        if not child.name.endswith(".md"):
            continue
        text = child.read_text(encoding="utf-8")
        frontmatter = _manifest_frontmatter(text)
        if frontmatter.get("type") != CAPABILITY_TYPE:
            continue
        items.append(
            {
                "path": f"{PRODUCT_CAPABILITY_PREFIX}/{CAPABILITY_HOME}/{child.name}",
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


def _manifest_frontmatter(text: str) -> dict[str, Any]:
    frontmatter = parse_frontmatter(text)
    if frontmatter.get("type") == CAPABILITY_TYPE and "runner" not in frontmatter:
        frontmatter["runner"] = {
            mode: dict(branch) for mode, branch in DEFAULT_RUNNER_POLICY.items()
        }
    return frontmatter


def _catalog_row(item: dict[str, Any]) -> dict[str, Any]:
    frontmatter = item["frontmatter"]
    row = {
        "id": _capability_id(item["path"], frontmatter),
        "type": frontmatter["type"],
        "path": item["path"],
        "title": frontmatter.get("title", ""),
        "description": frontmatter.get("description", ""),
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
