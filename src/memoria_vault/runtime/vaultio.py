"""Vault file helpers that stay importable without MCP dependencies."""

from __future__ import annotations

import os
import secrets
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

DEFAULT_SKIP_DIRS = frozenset({".git", ".memoria", ".obsidian", "node_modules"})
UNIVERSAL_CONCEPT_BUNDLES = frozenset({"knowledge"})
UNIVERSAL_CONCEPT_TYPES = frozenset({"note", "work", "hub", "project"})
ULID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
RETIRED_FRONTMATTER_FIELDS = frozenset(
    {
        "check_status",
        "standing",
        "lifecycle",
        "metadata_status",
        "text_status",
        "confidence",
        "contested",
        "created",
        "updated",
    }
)


def safe_read(path: Path) -> str:
    """Read UTF-8 text, returning ``""`` for missing/unreadable/binary files."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse leading YAML frontmatter, returning ``{}`` when absent or invalid."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    raw = text[3:end]
    try:
        import yaml
    except ImportError:  # pragma: no cover - exercised in runtime deployments without PyYAML
        return _parse_frontmatter_minimal(raw)
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def read_frontmatter(path: Path) -> dict[str, Any]:
    return parse_frontmatter(safe_read(path))


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    body_start = end + len("\n---")
    if body_start < len(text) and text[body_start] == "\n":
        body_start += 1
    return parse_frontmatter(text), text[body_start:]


def dump_frontmatter(frontmatter: dict[str, Any]) -> str:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - packaged deployments install PyYAML.
        raise RuntimeError("PyYAML is required to write frontmatter") from exc

    return yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()


def frontmatter_doc(frontmatter: dict[str, Any], body: str) -> str:
    if not body.startswith("\n"):
        body = "\n" + body
    if not body.endswith("\n"):
        body += "\n"
    return f"---\n{dump_frontmatter(frontmatter)}\n---{body}"


def apply_universal_concept_frontmatter(
    frontmatter: dict[str, Any], rel_path: str
) -> dict[str, Any]:
    """Add alpha.15 universal meaning fields for knowledge Concepts."""
    normalized = rel_path.replace("\\", "/")
    if not normalized.endswith(".md"):
        return frontmatter
    parts = normalized.split("/", 1)
    if len(parts) != 2 or parts[0] not in UNIVERSAL_CONCEPT_BUNDLES:
        return frontmatter
    if frontmatter.get("type") in UNIVERSAL_CONCEPT_TYPES:
        frontmatter.setdefault("id", new_ulid())
        frontmatter.setdefault("tags", [])
        frontmatter.setdefault("links", {})
    return frontmatter


def universal_concept_frontmatter_errors(frontmatter: dict[str, Any], rel_path: str) -> list[str]:
    normalized = rel_path.replace("\\", "/")
    if not normalized.endswith(".md"):
        return []
    parts = normalized.split("/", 1)
    if len(parts) != 2 or parts[0] not in UNIVERSAL_CONCEPT_BUNDLES:
        return []
    errors: list[str] = []
    if frontmatter.get("type") in UNIVERSAL_CONCEPT_TYPES:
        if not is_ulid(str(frontmatter.get("id") or "")):
            errors.append("id must be a ULID")
        if not isinstance(frontmatter.get("links"), dict):
            errors.append("links must be a map")
    return errors


def retired_frontmatter_field_errors(frontmatter: dict[str, Any]) -> list[str]:
    return [
        f"retired frontmatter field is ignored: {field}"
        for field in sorted(RETIRED_FRONTMATTER_FIELDS & set(frontmatter))
    ]


def is_ulid(value: str) -> bool:
    return len(value) == 26 and all(ch in ULID_ALPHABET for ch in value)


def new_ulid() -> str:
    value = ((int(time.time() * 1000) & ((1 << 48) - 1)) << 80) | secrets.randbits(80)
    chars = []
    for shift in range(125, -1, -5):
        chars.append(ULID_ALPHABET[(value >> shift) & 31])
    return "".join(chars)


def concept_text(frontmatter: dict[str, Any], title: str, body: str) -> str:
    return frontmatter_doc(frontmatter, f"# {title}\n\n{body.rstrip()}\n")


def write_frontmatter_doc(
    path: Path,
    frontmatter: dict[str, Any],
    body: str,
    *,
    create_parent: bool = False,
) -> None:
    if create_parent:
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter_doc(frontmatter, body), encoding="utf-8")


def iter_markdown(
    vault: Path, skip_dirs: set[str] | frozenset[str] | None = None
) -> Iterator[Path]:
    """Yield markdown files below ``vault``, pruning skipped directories while walking."""
    skipped = set(DEFAULT_SKIP_DIRS if skip_dirs is None else skip_dirs)
    for dirpath, dirnames, filenames in os.walk(vault):
        dirnames[:] = sorted(name for name in dirnames if name not in skipped)
        for name in sorted(filenames):
            if name.endswith(".md"):
                yield Path(dirpath) / name


def _parse_frontmatter_minimal(raw: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        if line.startswith((" ", "\t")):
            continue
        key, _, value = line.partition(":")
        value = value.strip().strip("\"'")
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key.strip()] = [
                item.strip().strip("\"'") for item in inner.split(",") if item.strip()
            ]
        else:
            data[key.strip()] = value
    return data
