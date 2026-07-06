#!/usr/bin/env python3
"""schema — loader + validator for the canonical type schemas (ADR-122/ADR-50).

`.memoria/schemas/` is the single source for the vault's document-type vocabulary
(ADR-47): per-type frontmatter schemas (`types/<type>.yaml`), the type→folder
map (`folders.yaml`), and the calibrated thresholds (`calibration.yaml`).
This module is the one reader every consumer shares — the Linter, the
pre-commit hook, the installer-skeleton test, and the template/Bases tests —
so a schema change is a one-file edit, never a hunt across hardcoded lists.

Field kinds: str | int | bool | date | list | map | links | ulid | literal:<value> | enum:<name>.
`required_any` lists field names of which at least one must be present.
"""

from __future__ import annotations

import datetime
import re
from pathlib import Path

import yaml

from memoria_vault.runtime.vaultio import is_ulid, universal_concept_frontmatter_errors


def _default_schemas_dir() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "vault-template/.memoria/schemas"
        if candidate.is_dir():
            return candidate
    return Path(__file__).resolve().parent.parent.parent / "schemas"


SCHEMAS_DIR = _default_schemas_dir()

UNIVERSAL_LIFECYCLE = ["proposed", "provisional", "current", "retracted", "archived"]
VOCABULARY_FIELDS = {
    "source": {"research_area": "research_area", "methodology": "methodology"},
    "note": {"topics": "topics"},
}
LINK_RELATIONS = frozenset({"supports", "contradicts", "extends"})


def _schemas_dir(schemas_dir: Path | None = None) -> Path:
    return Path(schemas_dir) if schemas_dir else SCHEMAS_DIR


def load_types(schemas_dir: Path | None = None) -> dict[str, dict]:
    """Return {document type: schema dict} for every types/<type>.yaml."""
    out: dict[str, dict] = {}
    for f in sorted((_schemas_dir(schemas_dir) / "types").glob("*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        out[data["type"]] = data
    return out


def load_folders(schemas_dir: Path | None = None) -> dict:
    """Return the parsed folders.yaml (homes, transient prefixes, skeleton)."""
    f = _schemas_dir(schemas_dir) / "folders.yaml"
    return yaml.safe_load(f.read_text(encoding="utf-8"))


def load_calibration(schemas_dir: Path | None = None) -> dict:
    f = _schemas_dir(schemas_dir) / "calibration.yaml"
    return yaml.safe_load(f.read_text(encoding="utf-8"))


def load_vocabulary(
    vocabulary_path: Path | None = None, schemas_dir: Path | None = None
) -> dict[str, set[str]]:
    path = vocabulary_path or _schemas_dir(schemas_dir).parent.parent / "system" / "vocabulary.md"
    out: dict[str, set[str]] = {"research_area": set(), "methodology": set(), "topics": set()}
    if not path.is_file():
        return out
    current = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## research_area"):
            current = "research_area"
            continue
        if line.startswith("## methodology"):
            current = "methodology"
            continue
        if line.startswith("## topics"):
            current = ""
            continue
        if current:
            match = re.match(r"- ([a-z0-9-]+) —", line)
            if match:
                out[current].add(match.group(1))
    out["topics"] = set(out["research_area"])
    return out


def home_for(type_name: str, folders: dict) -> str | None:
    return folders.get("homes", {}).get(type_name)


def gated_prefixes(folders: dict) -> list[str]:
    return list(folders.get("gated_prefixes", []))


# Dependency-free fallback for the structural review gate. The schema no longer
# declares gated prefixes; machine writes route through worker staging,
# promotion, and quarantine instead.
FALLBACK_GATED_PREFIXES = ("notes/", "hubs/")


def load_gated_prefixes(schemas_dir: Path | None = None) -> tuple[str, ...]:
    """Return structural review-gated prefixes."""
    try:
        return (
            tuple(load_folders(schemas_dir).get("gated_prefixes") or ()) or FALLBACK_GATED_PREFIXES
        )
    except (OSError, yaml.YAMLError, KeyError):
        return FALLBACK_GATED_PREFIXES


def bundle_roots(folders: dict) -> tuple[str, ...]:
    return tuple(folders.get("bundle_roots") or folders.get("categories") or ())


def lifecycle_for(schema: dict) -> list[str]:
    return list(schema.get("enums", {}).get("lifecycle", []))


def check_status_for(schema: dict) -> list[str]:
    return list(schema.get("enums", {}).get("check_status", []))


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
    if kind == "links":
        return _check_links(value)
    if kind == "ulid":
        return None if isinstance(value, str) and is_ulid(value) else "expected ULID"
    return f"unknown kind {kind!r}"


def _check_links(value) -> str | None:
    if not isinstance(value, dict):
        return f"expected links map, got {type(value).__name__}"
    for relation, targets in value.items():
        if not isinstance(relation, str) or not relation.strip():
            return "links relation keys must be non-empty strings"
        if relation not in LINK_RELATIONS:
            return f"links.{relation}: unknown relation; expected {sorted(LINK_RELATIONS)}"
        if not isinstance(targets, list):
            return f"links.{relation}: expected list, got {type(targets).__name__}"
        for index, target in enumerate(targets):
            if not isinstance(target, str) or not target.strip():
                return f"links.{relation}[{index}]: expected non-empty target string"
            raw = target.strip()
            if raw.startswith("[[") and raw.endswith("]]"):
                raw = raw[2:-2].split("|", 1)[0].split("#", 1)[0].strip()
            if not raw:
                return f"links.{relation}[{index}]: expected non-empty target string"
            if "://" in raw or raw.startswith(("mailto:", "/")):
                return f"links.{relation}[{index}]: expected local Concept target"
            parts = [part for part in raw.replace("\\", "/").split("/") if part and part != "."]
            if ".." in parts:
                return f"links.{relation}[{index}]: target must not escape the workspace"
    return None


def validate_frontmatter(
    fm: dict, schema: dict, vocabulary_terms: dict[str, set[str]] | None = None
) -> list[str]:
    """Validate one document's frontmatter against its type schema.

    Returns a list of human-readable error strings (empty = valid).
    Unknown extra fields are accepted. The schema enforces required meaning fields
    without making hand-authored markdown brittle during alpha migrations.
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
    if vocabulary_terms:
        for field, vocabulary in VOCABULARY_FIELDS.get(str(schema.get("type")), {}).items():
            values = fm.get(field)
            allowed = vocabulary_terms.get(vocabulary) or set()
            if not allowed or values in (None, "") or not isinstance(values, list):
                continue
            bad = [str(value) for value in values if str(value) not in allowed]
            if bad:
                errors.append(f"{field}: off-vocabulary value(s) {bad}; expected {vocabulary} term")
    return errors


def _markdown_frontmatter(path: Path) -> tuple[dict, str, list[str]]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text, ["missing YAML frontmatter"]
    try:
        _, fm_text, body = text.split("---\n", 2)
    except ValueError:
        return {}, text, ["unterminated YAML frontmatter"]
    try:
        data = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as exc:
        return {}, body, [f"invalid YAML frontmatter: {exc}"]
    if not isinstance(data, dict):
        return {}, body, ["YAML frontmatter must be a map"]
    return data, body, []


def _concept_files(root: Path, folders: dict) -> list[Path]:
    bundle_dirs = [root / bundle for bundle in bundle_roots(folders)]
    ignored = {"index.md", "log.md", "SCHEMA.md"}
    out: list[Path] = []
    for bundle_dir in bundle_dirs:
        if not bundle_dir.is_dir():
            continue
        out.extend(
            path
            for path in bundle_dir.rglob("*.md")
            if path.name not in ignored and ".memoria" not in path.parts
        )
    return sorted(out)


def _under_home(path: Path, root: Path, home: str) -> bool:
    rel = path.relative_to(root).as_posix()
    home = home.rstrip("/")
    return rel == home or rel.startswith(f"{home}/")


def validate_okf_core_workspace(root: Path, schemas_dir: Path | None = None) -> list[str]:
    """Permissive OKF-core shape check for bundle roots."""
    root = Path(root)
    folders = load_folders(schemas_dir)
    errors: list[str] = []
    for bundle in bundle_roots(folders):
        if not (root / bundle).is_dir():
            errors.append(f"missing bundle root: {bundle}")
    for path in _concept_files(root, folders):
        fm, _body, fm_errors = _markdown_frontmatter(path)
        rel = path.relative_to(root).as_posix()
        errors.extend(f"{rel}: {err}" for err in fm_errors)
        if fm_errors:
            continue
        if fm.get("type") in (None, ""):
            errors.append(f"{rel}: missing required field: type")
        errors.extend(f"{rel}: {error}" for error in universal_concept_frontmatter_errors(fm, rel))
    return errors


def validate_memoria_workspace(root: Path, schemas_dir: Path | None = None) -> list[str]:
    """Strict Memoria Concept check before promotion into bundle roots."""
    root = Path(root)
    types = load_types(schemas_dir)
    folders = load_folders(schemas_dir)
    errors = validate_okf_core_workspace(root, schemas_dir)
    for path in _concept_files(root, folders):
        rel = path.relative_to(root).as_posix()
        fm, _body, fm_errors = _markdown_frontmatter(path)
        if fm_errors:
            continue
        type_name = str(fm.get("type") or "")
        sc = types.get(type_name)
        if sc is None:
            errors.append(f"{rel}: unknown type: {type_name}")
            continue
        home = home_for(type_name, folders)
        if home and not _under_home(path, root, home):
            errors.append(f"{rel}: type {type_name!r} must live under {home}/")
        errors.extend(f"{rel}: {err}" for err in validate_frontmatter(fm, sc))
    return errors


if __name__ == "__main__":
    print(__doc__)
