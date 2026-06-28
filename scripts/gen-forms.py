#!/usr/bin/env python3
"""Generate Modal Forms config from Memoria schemas and vocabulary."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "vault-template"
SCHEMA_DIR = SRC / ".memoria" / "schemas" / "types"
VOCABULARY = SRC / "system" / "vocabulary.md"
FORM_TYPES = ("fleeting", "source", "claim", "project")


def _schema(name: str) -> dict:
    return yaml.safe_load((SCHEMA_DIR / f"{name}.yaml").read_text(encoding="utf-8"))


def _terms(section: str) -> list[str]:
    text = VOCABULARY.read_text(encoding="utf-8")
    match = re.search(rf"^## {re.escape(section)}\n(?P<body>.*?)(?=^## |\Z)", text, re.S | re.M)
    if not match:
        raise SystemExit(f"{section} section missing from {VOCABULARY}")
    return re.findall(r"^- ([a-z0-9-]+) — ", match.group("body"), re.M)


def _fixed_select(values: list[str]) -> dict:
    return {
        "type": "select",
        "source": "fixed",
        "options": [{"label": value.replace("-", " ").title(), "value": value} for value in values],
    }


def _fixed_multi(values: list[str]) -> dict:
    return {"type": "multiselect", "source": "fixed", "multi_select_options": values}


def _notes(folder: str) -> dict:
    return {"type": "note", "folder": folder}


def _note_multi(folder: str, *, folders: list[str] | None = None) -> dict:
    data = {"type": "multiselect", "source": "notes", "folder": folder}
    if folders:
        data["folders"] = folders
    return data


def _field(
    name: str,
    label: str,
    input_def: dict,
    *,
    description: str = "",
    required: bool = False,
) -> dict:
    data = {"name": name, "label": label}
    if description:
        data["description"] = description
    if required:
        data["isRequired"] = True
    data["input"] = input_def
    return data


def _form(title: str, name: str, fields: list[dict]) -> dict:
    return {"title": title, "name": name, "version": "1", "fields": fields}


def _vocabulary_terms(input_def: dict) -> list[str]:
    values = _terms(input_def["vocabulary"])
    if values:
        return values
    fallback = input_def.get("fallback_vocabulary")
    return _terms(fallback) if fallback else values


def _input_from_spec(input_def: dict, schema: dict) -> dict:
    kind = input_def["type"]
    if kind in {"text", "textarea"}:
        return {"type": kind}
    if kind == "select":
        if "enum" in input_def:
            return _fixed_select(schema["enums"][input_def["enum"]])
        return _fixed_select(input_def["values"])
    if kind == "multiselect":
        return _fixed_multi(_vocabulary_terms(input_def))
    if kind == "note":
        return _notes(input_def["folder"])
    if kind == "note-multiselect":
        return _note_multi(input_def["folder"])
    raise SystemExit(f"{schema['type']}: unsupported creation input type {kind!r}")


def _field_from_spec(field: dict, schema: dict) -> dict:
    generated = _field(
        field["name"],
        field["label"],
        _input_from_spec(field["input"], schema),
        description=field.get("description", ""),
        required=bool(field.get("required", False)),
    )
    if "condition" in field:
        generated["condition"] = field["condition"]
    return generated


def _form_from_schema(schema: dict) -> dict:
    form = schema["creation"]["form"]
    return _form(
        form["title"],
        form["name"],
        [_field_from_spec(field, schema) for field in form["fields"]],
    )


def generate() -> dict:
    return {
        "editorPosition": "right",
        "attachShortcutToGlobalWindow": False,
        "globalNamespace": "MF",
        "formDefinitions": [_form_from_schema(_schema(type_name)) for type_name in FORM_TYPES],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="exit non-zero if data.json drifts")
    parser.add_argument("--write", action="store_true", help="write generated data.json")
    parser.add_argument(
        "--output",
        type=Path,
        default=SRC / ".obsidian" / "plugins" / "modalforms" / "data.json",
    )
    args = parser.parse_args()

    rendered = json.dumps(generate(), indent=2) + "\n"
    if args.check:
        current = args.output.read_text(encoding="utf-8")
        if current != rendered:
            raise SystemExit(f"{args.output} is out of date; run scripts/gen-forms.py --write")
        return 0
    if args.write:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
