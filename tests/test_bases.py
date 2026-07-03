"""Schema-backed .base views stay in sync with the alpha.15 schemas."""

import re
from pathlib import Path

import yaml

from memoria_vault.runtime.subsystems.lib import schema

SRC = Path(__file__).resolve().parent.parent / "vault-template"

_BUILTIN_PREFIXES = ("file.", "formula.", "this.")
_BUILTIN = {"type", "check_status"}


def _bases() -> list[Path]:
    return sorted(SRC.rglob("*.base"))


def _folder_types(folder: str, types: dict, folders: dict) -> set[str]:
    out = set()
    for name in types:
        home = schema.home_for(name, folders)
        if home == folder or home.startswith(folder.rstrip("/") + "/"):
            out.add(name)
    return out


def _known_fields(type_names: set[str], types: dict) -> set[str]:
    fields = set(_BUILTIN)
    for name in type_names:
        sc = types[name]
        fields |= set(sc.get("required") or {})
        fields |= set(sc.get("optional") or {})
    return fields


def _referenced_properties(base: dict) -> set[str]:
    props: set[str] = set()
    for view in base.get("views", []):
        for col in view.get("order", []):
            if not col.startswith(_BUILTIN_PREFIXES):
                props.add(col)
        group_by = view.get("groupBy")
        if isinstance(group_by, dict):
            prop = str(group_by.get("property", ""))
            if prop and not prop.startswith(_BUILTIN_PREFIXES):
                props.add(prop)
    return props


def test_every_base_parses_as_yaml():
    assert _bases(), "no .base files shipped"
    for base in _bases():
        yaml.safe_load(base.read_text(encoding="utf-8"))


def test_base_properties_exist_in_schemas():
    types = schema.load_types()
    folders = schema.load_folders()
    for base in _bases():
        data = yaml.safe_load(base.read_text(encoding="utf-8"))
        targets = set(re.findall(r'file\.inFolder\("([^"]+)"\)', base.read_text()))
        assert targets, f"{base}: no file.inFolder target"
        type_names: set[str] = set()
        for folder in targets:
            type_names |= _folder_types(folder, types, folders)
        if not type_names:
            continue
        unknown = _referenced_properties(data) - _known_fields(type_names, types)
        assert not unknown, f"{base}: references properties not in any schema: {sorted(unknown)}"


def test_base_views_start_with_clickable_note_links():
    for base in _bases():
        data = yaml.safe_load(base.read_text(encoding="utf-8"))
        formulas = data.get("formulas") or {}
        properties = data.get("properties") or {}
        assert str(formulas.get("note", "")).startswith("link(file.path,")
        assert properties["formula.note"]["displayName"] == "Note"
        for view in data.get("views", []):
            order = view.get("order", [])
            assert order and order[0] == "formula.note", f"{base}::{view.get('name')}"
            assert not {"title", "name", "file.name"} & set(order)
