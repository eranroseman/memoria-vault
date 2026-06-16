#!/usr/bin/env python3
"""schema — loader + validator for the canonical type schemas (ADR-49/ADR-50).

`.memoria/schemas/` is the single source for the vault's type vocabulary
(ADR-47): per-type frontmatter schemas (`types/<type>.yaml`), the type→folder
map (`folders.yaml`), and the calibrated thresholds (`calibration.yaml`).
This module is the one reader every consumer shares — the Linter, the
pre-commit hook, the installer-skeleton test, and the template/Bases tests —
so a schema change is a one-file edit, never a hunt across hardcoded lists.

Field kinds: str | int | bool | date | list | map | literal:<value> | enum:<name>.
`required_any` lists field names of which at least one must be present.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import yaml

SCHEMAS_DIR = Path(__file__).resolve().parent.parent.parent / "schemas"

UNIVERSAL_LIFECYCLE = ["proposed", "provisional", "current", "retracted", "archived"]


def _schemas_dir(schemas_dir: Path | None = None) -> Path:
    return Path(schemas_dir) if schemas_dir else SCHEMAS_DIR


def load_types(schemas_dir: Path | None = None) -> dict[str, dict]:
    """Return {type name: schema dict} for every types/<type>.yaml."""
    out: dict[str, dict] = {}
    for f in sorted((_schemas_dir(schemas_dir) / "types").glob("*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        out[data["type"]] = data
    return out


def load_folders(schemas_dir: Path | None = None) -> dict:
    """Return the parsed folders.yaml (homes, gated/transient prefixes, skeleton)."""
    f = _schemas_dir(schemas_dir) / "folders.yaml"
    return yaml.safe_load(f.read_text(encoding="utf-8"))


def load_calibration(schemas_dir: Path | None = None) -> dict:
    f = _schemas_dir(schemas_dir) / "calibration.yaml"
    return yaml.safe_load(f.read_text(encoding="utf-8"))


def home_for(type_name: str, folders: dict) -> str | None:
    return folders.get("homes", {}).get(type_name)


def gated_prefixes(folders: dict) -> list[str]:
    return list(folders.get("gated_prefixes", []))


# The dependency-free fallback for the review-gated zones. policy_mcp and
# patterns_mcp carry the same tuple hardcoded (they run standalone, without
# this module or even PyYAML on the path); tests/test_schemas.py asserts all
# three stay in sync with folders.yaml.
FALLBACK_GATED_PREFIXES = ("notes/claims/", "notes/hubs/")


def load_gated_prefixes(schemas_dir: Path | None = None) -> tuple[str, ...]:
    """The review-gated prefixes from folders.yaml, with the hardcoded fallback
    when the schema home is unreadable — the one loader every in-repo consumer
    of `gated_prefixes` should share."""
    try:
        return tuple(load_folders(schemas_dir)["gated_prefixes"]) or FALLBACK_GATED_PREFIXES
    except Exception:
        return FALLBACK_GATED_PREFIXES


def lifecycle_for(schema: dict) -> list[str]:
    return list(schema.get("enums", {}).get("lifecycle", []))


def _check_kind(value, kind: str, enums: dict) -> str | None:
    """Return an error string if value does not match kind, else None."""
    if kind.startswith("literal:"):
        want = kind.split(":", 1)[1]
        return None if value == want else f"expected literal {want!r}, got {value!r}"
    if kind.startswith("enum:"):
        name = kind.split(":", 1)[1]
        allowed = enums.get(name, [])
        return None if value in allowed else f"value {value!r} not in enum {name} {allowed}"
    if kind == "str":
        return None if isinstance(value, str) else f"expected str, got {type(value).__name__}"
    if kind == "int":
        return None if isinstance(value, int) and not isinstance(value, bool) else "expected int"
    if kind == "bool":
        return None if isinstance(value, bool) else "expected bool"
    if kind == "date":
        if isinstance(value, datetime.date):
            return None
        if isinstance(value, str):
            try:
                datetime.date.fromisoformat(value[:10])
                return None
            except ValueError:
                return f"expected ISO date, got {value!r}"
        return f"expected date, got {type(value).__name__}"
    if kind == "list":
        return None if isinstance(value, list) else f"expected list, got {type(value).__name__}"
    if kind == "map":
        return None if isinstance(value, dict) else f"expected map, got {type(value).__name__}"
    return f"unknown kind {kind!r}"


def validate_frontmatter(fm: dict, schema: dict) -> list[str]:
    """Validate one note's frontmatter against its type schema.

    Returns a list of human-readable error strings (empty = valid).
    Unknown extra fields are allowed — the schema constrains, it does not enumerate.
    """
    errors: list[str] = []
    enums = schema.get("enums", {})
    for field, kind in (schema.get("required") or {}).items():
        if field not in fm or fm[field] in (None, ""):
            errors.append(f"missing required field: {field}")
            continue
        err = _check_kind(fm[field], kind, enums)
        if err:
            errors.append(f"{field}: {err}")
    for field, kind in (schema.get("optional") or {}).items():
        if field in fm and fm[field] not in (None, ""):
            err = _check_kind(fm[field], kind, enums)
            if err:
                errors.append(f"{field}: {err}")
    any_of = schema.get("required_any") or []
    if any_of and not any(fm.get(f) not in (None, "") for f in any_of):
        errors.append(f"at least one of {any_of} is required")
    gate = schema.get("promotion_gate")
    if gate and fm.get("lifecycle") == gate and fm.get("promoted_at") in (None, ""):
        errors.append(f"lifecycle {gate!r} requires promoted_at promotion provenance")
    return errors


if __name__ == "__main__":
    print(__doc__)
