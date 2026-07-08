#!/usr/bin/env python3
"""Check reference docs against the live frontmatter schemas."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_KEYS = {
    "category",
    "gated",
    "required",
    "optional",
    "enums",
    "required_any",
    "required_when",
    "forbidden",
}


def load_types(schemas_dir: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for path in sorted((schemas_dir / "types").glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if isinstance(data, dict) and isinstance(data.get("type"), str):
            out[data["type"]] = data
    return out


def check_schema_docs(schemas_dir: Path, docs_dir: Path) -> list[str]:
    schemas = load_types(schemas_dir)
    errors: list[str] = []
    document_types = _find_doc(docs_dir, "document-types.md")
    frontmatter = _find_doc(docs_dir, "frontmatter.md")
    errors.extend(_check_type_roster(document_types, schemas))
    for path in (frontmatter, document_types):
        errors.extend(_check_schema_examples(path, schemas))
    return errors


def _find_doc(docs_dir: Path, filename: str) -> Path:
    matches = sorted(docs_dir.rglob(filename))
    return matches[0] if len(matches) == 1 else docs_dir / filename


def _check_type_roster(path: Path, schemas: dict[str, dict[str, Any]]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"current schema defines\s+(\d+)\s+document types?:\s+(.+?)\.",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return [f"{path}: missing current-schema document type roster"]
    documented_count = int(match.group(1))
    documented_types = set(re.findall(r"`([^`]+)`", match.group(2)))
    live_types = set(schemas)
    errors = []
    if documented_count != len(live_types):
        errors.append(
            f"{path}: document type count {documented_count} != live count {len(live_types)}"
        )
    if documented_types != live_types:
        errors.append(
            f"{path}: document types {sorted(documented_types)} != live {sorted(live_types)}"
        )
    return errors


def _check_schema_examples(path: Path, schemas: dict[str, dict[str, Any]]) -> list[str]:
    if not path.is_file():
        return [f"{path}: missing"]
    errors: list[str] = []
    for index, block in enumerate(_yaml_blocks(path.read_text(encoding="utf-8")), start=1):
        data = yaml.safe_load(block) or {}
        if not _is_schema_claim(data):
            continue
        type_name = str(data.get("type") or "")
        live = schemas.get(type_name)
        if live is None:
            errors.append(f"{path}: yaml block {index}: unknown schema type {type_name!r}")
            continue
        errors.extend(
            f"{path}: yaml block {index}: {error}"
            for error in _schema_claim_errors(data, live, type_name)
        )
    return errors


def _yaml_blocks(text: str) -> list[str]:
    return re.findall(r"```ya?ml\n(.*?)\n```", text, flags=re.DOTALL)


def _is_schema_claim(value: object) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("type"), str)
        and bool(SCHEMA_KEYS.intersection(value))
    )


def _schema_claim_errors(claim: dict[str, Any], live: dict[str, Any], type_name: str) -> list[str]:
    errors: list[str] = []
    for scalar in ("category", "gated"):
        if scalar in claim and claim.get(scalar) != live.get(scalar):
            errors.append(
                f"{type_name}.{scalar}: documented {claim.get(scalar)!r} != live {live.get(scalar)!r}"
            )
    errors.extend(_field_map_errors(claim, live, type_name, "required"))
    errors.extend(_field_map_errors(claim, live, type_name, "optional"))
    errors.extend(_enum_errors(claim, live, type_name))
    errors.extend(_required_when_errors(claim, live, type_name))
    errors.extend(_list_subset_errors(claim, live, type_name, "required_any"))
    errors.extend(_list_subset_errors(claim, live, type_name, "forbidden"))
    return errors


def _field_map_errors(
    claim: dict[str, Any], live: dict[str, Any], type_name: str, section: str
) -> list[str]:
    documented = claim.get(section) or {}
    live_fields = live.get(section) or {}
    errors = []
    if not isinstance(documented, dict):
        return [f"{type_name}.{section}: documented value is not a map"]
    if not isinstance(live_fields, dict):
        live_fields = {}
    for field, kind in documented.items():
        if field not in live_fields:
            errors.append(f"{type_name}.{section}.{field}: documented field is not live")
        elif live_fields[field] != kind:
            errors.append(
                f"{type_name}.{section}.{field}: documented {kind!r} != live {live_fields[field]!r}"
            )
    return errors


def _enum_errors(claim: dict[str, Any], live: dict[str, Any], type_name: str) -> list[str]:
    documented = claim.get("enums") or {}
    live_enums = live.get("enums") or {}
    errors = []
    if not isinstance(documented, dict):
        return [f"{type_name}.enums: documented value is not a map"]
    if not isinstance(live_enums, dict):
        live_enums = {}
    for enum, values in documented.items():
        if enum not in live_enums:
            errors.append(f"{type_name}.enums.{enum}: documented enum is not live")
        elif list(live_enums[enum]) != list(values):
            errors.append(
                f"{type_name}.enums.{enum}: documented {values!r} != live {live_enums[enum]!r}"
            )
    return errors


def _required_when_errors(claim: dict[str, Any], live: dict[str, Any], type_name: str) -> list[str]:
    documented = claim.get("required_when") or {}
    live_rules = live.get("required_when") or {}
    errors = []
    if not isinstance(documented, dict):
        return [f"{type_name}.required_when: documented value is not a map"]
    if not isinstance(live_rules, dict):
        live_rules = {}
    for field, rule in documented.items():
        if field not in live_rules:
            errors.append(f"{type_name}.required_when.{field}: documented rule is not live")
        elif live_rules[field] != rule:
            errors.append(
                f"{type_name}.required_when.{field}: documented {rule!r} != live {live_rules[field]!r}"
            )
    return errors


def _list_subset_errors(
    claim: dict[str, Any], live: dict[str, Any], type_name: str, section: str
) -> list[str]:
    if section not in claim:
        return []
    documented = claim.get(section) or []
    live_values = live.get(section) or []
    if not isinstance(documented, list):
        return [f"{type_name}.{section}: documented value is not a list"]
    missing = [value for value in documented if value not in live_values]
    if missing:
        return [f"{type_name}.{section}: documented {missing!r} not in live {live_values!r}"]
    return []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schemas", type=Path, default=ROOT / "vault-template/.memoria/schemas")
    parser.add_argument("--docs", type=Path, default=ROOT / "docs/reference")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors = check_schema_docs(args.schemas, args.docs)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("schema-doc-drift: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
