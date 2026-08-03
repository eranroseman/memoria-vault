#!/usr/bin/env python3
"""Loader and validator for the canonical type schemas.

`.memoria/schemas/` is the single source for the vault's document-type vocabulary
with per-type frontmatter schemas (`types/<type>.yaml`), the Concept-type roster
(`concept-types.yaml`), the type→folder map (`folders.yaml`), and the controlled
vocabulary (`system/vocabulary.md`).
This module is the reader shared by the Linter, the pre-commit hook,
`memoria init`, package-spine tests, and no-Bases seed tests, so a schema change is a
one-file edit, never a hunt across hardcoded lists.

Field kinds: str | int | bool | date | list | map | link | links | ulid | literal:<value>
| enum:<name>. `link` is one path-space Concept reference (a project's `thesis:`);
`links` is the relation→targets map.
`required_when` maps a field to {field, equals}; `forbidden` lists retired fields.
"""

from __future__ import annotations

import datetime
import re
from pathlib import Path

import yaml

# Re-exports live one release for external importers, then die by the sweep
# discipline (EDGES design, section 1). New code imports lib.edges directly;
# `_normalized_link_target` is not a re-export but this module's own use of the
# owner's target normalizer, which `_check_links` needs for its reason codes.
from memoria_vault.runtime.subsystems.lib.edges import (  # noqa: F401
    LINK_RELATIONS,
    _normalized_link_target,
    normalize_link_target,
    parse_links,
)
from memoria_vault.runtime.vaultio import (
    DEFAULT_SKIP_DIRS,
    is_ulid,
    universal_concept_frontmatter_errors,
)


def _default_schemas_dir() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "product/workspace_seed/.memoria/schemas"
        if candidate.is_dir():
            return candidate
    return Path(__file__).resolve().parents[3] / "product/workspace_seed/.memoria/schemas"


SCHEMAS_DIR = _default_schemas_dir()

VOCABULARY_FIELDS = {"note": {"topics": "topics"}}

# The version the root index.md declares, and the one the conformance check
# holds every bundle index to.
OKF_VERSION = "0.2"
_NESTED_BUNDLE_INDEX = re.compile(r"projects/[^/]+/index\.md")


def _present(value) -> bool:
    return value not in (None, "", [])


def _schemas_dir(schemas_dir: Path | None = None) -> Path:
    return Path(schemas_dir) if schemas_dir else SCHEMAS_DIR


def load_concept_types(schemas_dir: Path | None = None) -> dict[str, str]:
    """Return {concept type: one-line role} from the seeded registry.

    concept-types.yaml is the single source of the DB Concept-type roster;
    the schema.sql CHECK is held to it by the registry parity test.
    """
    registry_file = _schemas_dir(schemas_dir) / "concept-types.yaml"
    if not registry_file.is_file():
        raise ValueError(f"missing required concept-types.yaml: {registry_file}")
    data = yaml.safe_load(registry_file.read_text(encoding="utf-8"))
    return {str(name): str(role) for name, role in data["concept_types"].items()}


def load_types(schemas_dir: Path | None = None) -> dict[str, dict]:
    """Return {document type: schema dict} for every types/<type>.yaml.

    Raises ValueError when a doc-type yaml names no concept-type registry
    member in its concept_type key (the NODES §2 load-time check).
    """
    schema_dir = _schemas_dir(schemas_dir)
    registry = load_concept_types(schemas_dir)
    out: dict[str, dict] = {}
    for f in sorted((schema_dir / "types").glob("*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        member = data.get("concept_type")
        if member not in registry:
            raise ValueError(
                f"{f.name}: concept_type {member!r} is not in concept-types.yaml {sorted(registry)}"
            )
        out[data["type"]] = data
    return out


def concept_type_for(type_name: str, schemas_dir: Path | None = None) -> str:
    """Return the validated registry member for one document type."""
    type_schema = load_types(schemas_dir).get(type_name)
    if type_schema is None:
        raise ValueError(f"unknown document type: {type_name}")
    return str(type_schema["concept_type"])


def load_folders(schemas_dir: Path | None = None) -> dict:
    """Return the parsed folders.yaml (homes, transient prefixes, skeleton)."""
    f = _schemas_dir(schemas_dir) / "folders.yaml"
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


def bundle_roots(folders: dict) -> tuple[str, ...]:
    return tuple(folders.get("bundle_roots") or folders.get("categories") or ())


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
    if kind == "link":
        return _check_link(value)
    if kind == "links":
        return _check_links(value)
    if kind == "ulid":
        return None if isinstance(value, str) and is_ulid(value) else "expected ULID"
    return f"unknown kind {kind!r}"


def _check_link(value) -> str | None:
    """Validate one path-space Concept reference, in `_check_links`' wording.

    The schema layer is where issue #1623 decided that `thesis:` is path space:
    a title, slug, or prose sentence fails here, visibly, instead of resolving
    to nothing in five readers that each missed it differently.
    """
    if not isinstance(value, str) or not value.strip():
        return f"expected non-empty target string, got {type(value).__name__}"
    raw, reason = _normalized_link_target(value)
    if raw:
        return None
    if reason == "traversal":
        return "target must not escape the workspace"
    if reason == "empty":
        return "expected non-empty target string"
    return "expected local Concept target"


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
            raw, reason = _normalized_link_target(target)
            if not raw:
                if reason == "traversal":
                    return f"links.{relation}[{index}]: target must not escape the workspace"
                if reason == "empty":
                    return f"links.{relation}[{index}]: expected non-empty target string"
                return f"links.{relation}[{index}]: expected local Concept target"
    return None


def validate_frontmatter(
    fm: dict, schema: dict, vocabulary_terms: dict[str, set[str]] | None = None
) -> list[str]:
    """Validate one document's frontmatter against its type schema.

    Returns a list of human-readable error strings (empty = valid).
    Validation is closed: fields not declared by the type schema are rejected
    (nest extension data under the declared `x:` map instead).
    """
    errors: list[str] = []
    enums = schema.get("enums", {})
    for field in schema.get("forbidden") or []:
        if field in fm:
            errors.append(f"{field}: field is retired")
    known_fields = (
        set(schema.get("required") or {})
        | set(schema.get("optional") or {})
        | set(schema.get("forbidden") or [])
    )
    for field in sorted(set(fm) - known_fields):
        errors.append(f"{field}: unknown field; declare it in the type schema or nest under x:")
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
    for field, rule in (schema.get("required_when") or {}).items():
        if not isinstance(rule, dict):
            errors.append(f"required_when.{field}: expected map")
            continue
        controller = str(rule.get("field") or "")
        if fm.get(controller) == rule.get("equals") and not _present(fm.get(field)):
            errors.append(f"{field}: required when {controller} is {rule.get('equals')!r}")
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
    """OKF v0.2 core conformance (spec §11) over the whole bundle tree.

    Every non-reserved `.md` file in the tree needs parseable frontmatter with
    a non-empty `type` -- not just files under the bundle roots -- because the
    exported bundle is the whole vault minus `.memoria/`, so a root-level file
    like `Start here.md` is a concept document to an OKF consumer too.
    """
    root = Path(root)
    folders = load_folders(schemas_dir)
    errors: list[str] = []
    for bundle in bundle_roots(folders):
        if not (root / bundle).is_dir():
            errors.append(f"missing bundle root: {bundle}")
    reserved = {"index.md", "log.md"}
    for path in sorted(root.rglob("*.md")):
        # Relative parts only: a vault that happens to live under a directory
        # named like a skip target is still a vault.
        if any(part in DEFAULT_SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        rel = path.relative_to(root).as_posix()
        if path.name in reserved:
            errors.extend(_reserved_file_errors(path, rel, is_bundle_root=(rel == path.name)))
            continue
        if path.name == "SCHEMA.md":
            continue
        fm, _body, fm_errors = _markdown_frontmatter(path)
        errors.extend(f"{rel}: {err}" for err in fm_errors)
        if fm_errors:
            continue
        if fm.get("type") in (None, ""):
            errors.append(f"{rel}: missing required field: type")
        errors.extend(f"{rel}: {error}" for error in universal_concept_frontmatter_errors(fm, rel))
    return errors


def _reserved_file_errors(path: Path, rel: str, *, is_bundle_root: bool) -> list[str]:
    """Spec §8/§9: index.md declares okf_version at a bundle root; log.md carries none.

    A nested bundle may declare its own version (§12), so `projects/<slug>/index.md`
    is allowed the same one-key frontmatter as the root. Every other index.md
    carries none, and the root's declaration is required, not optional: the claim
    that this tree is an OKF bundle is made in exactly that one line.
    """
    root_index = is_bundle_root and path.name == "index.md"
    declares_version = root_index or _NESTED_BUNDLE_INDEX.fullmatch(rel) is not None
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        if root_index:
            return [f'{rel}: the bundle root index.md must declare okf_version "{OKF_VERSION}"']
        return []
    fm, _body, fm_errors = _markdown_frontmatter(path)
    if fm_errors:
        return [f"{rel}: {err}" for err in fm_errors]
    if path.name == "log.md":
        return [f"{rel}: reserved log.md must carry no frontmatter"]
    if not declares_version or set(fm) != {"okf_version"}:
        return [f"{rel}: reserved index.md frontmatter is limited to okf_version at a bundle root"]
    if str(fm["okf_version"]) != OKF_VERSION:
        return [f"{rel}: index.md must declare okf_version {OKF_VERSION!r}, not {fm!r}"]
    return []


def validate_memoria_workspace(root: Path, schemas_dir: Path | None = None) -> list[str]:
    """Strict Memoria Concept check before promotion into bundle roots.

    Its own per-type checks stay bundle-root-scoped (via `_concept_files`) by
    design: root-level files like `Start here.md` carry `type: system`, which
    is not in the type-schema roster, and must not fail this strict validator.
    """
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
