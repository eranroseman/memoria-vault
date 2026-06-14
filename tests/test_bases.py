"""Every shipped .base view stays in sync with the schemas (ADR-49 risk control).

Bases have no schema enforcement by design; this test is our side of the contract —
every frontmatter property a .base references must exist in the schema of a type
homed in the folder(s) the base draws from.
"""

import re
from pathlib import Path

import yaml

import schema

SRC = Path(__file__).resolve().parent.parent / "src"

# properties Obsidian provides on every note
_BUILTIN_PREFIXES = ("file.", "formula.", "this.")
_BUILTIN = {"type", "lifecycle"}


def _bases() -> list[Path]:
    return sorted(SRC.rglob("*.base"))


def _folder_types(folder: str, types: dict, folders: dict) -> set[str]:
    """Type names homed at or under `folder`."""
    out = set()
    for name in types:
        home = schema.home_for(name, folders)
        if home == folder or home.startswith(folder.rstrip("/") + "/"):
            out.add(name)
    return out


def _known_fields(type_names: set[str], types: dict) -> set[str]:
    fields = set(_BUILTIN)
    for n in type_names:
        sc = types[n]
        fields |= set(sc.get("required") or {})
        fields |= set(sc.get("optional") or {})
    return fields


def _referenced_properties(base: dict) -> set[str]:
    """Frontmatter properties referenced in order/groupBy/filters."""
    props: set[str] = set()

    def from_filter(node) -> None:
        if isinstance(node, str):
            for ident in re.findall(r"[A-Za-z_][\w-]*", node):
                props.add(ident)
        elif isinstance(node, dict):
            for v in node.values():
                from_filter(v)
        elif isinstance(node, list):
            for v in node:
                from_filter(v)

    for view in base.get("views", []):
        for col in view.get("order", []):
            if not col.startswith(_BUILTIN_PREFIXES):
                props.add(col)
        gb = view.get("groupBy")
        if isinstance(gb, dict) and not str(gb.get("property", "")).startswith(_BUILTIN_PREFIXES):
            props.add(gb["property"])
    return props


# identifiers in filter strings that are functions/keywords, not properties
_FILTER_NOISE = {
    "file", "inFolder", "ext", "md", "and", "or", "not", "hasTag", "hasLink",
    "now", "today", "date", "if", "true", "false",
}


def test_every_base_parses_as_yaml():
    assert _bases(), "no .base files shipped"
    for b in _bases():
        yaml.safe_load(b.read_text(encoding="utf-8"))


def test_base_properties_exist_in_schemas():
    types = schema.load_types()
    folders = schema.load_folders()
    for b in _bases():
        data = yaml.safe_load(b.read_text(encoding="utf-8"))
        # the folders this base draws from (inFolder calls anywhere in the file)
        targets = set(re.findall(r'file\.inFolder\("([^"]+)"\)', b.read_text(encoding="utf-8")))
        if not targets:
            continue
        type_names: set[str] = set()
        for folder in targets:
            type_names |= _folder_types(folder, types, folders)
        assert type_names, f"{b}: draws from {targets} where no type is homed"
        known = _known_fields(type_names, types)
        unknown = _referenced_properties(data) - known
        assert not unknown, f"{b}: references properties not in any schema: {sorted(unknown)}"


def test_inbox_base_has_needs_me_view():
    inbox = SRC / "inbox" / "inbox.base"
    data = yaml.safe_load(inbox.read_text(encoding="utf-8"))
    views = {v.get("name"): v for v in data.get("views", [])}
    names = set(views)
    assert "Needs me" in names  # home.md embeds this view by name
    needs_me_order = views["Needs me"]["order"]
    assert "action" in needs_me_order
    assert "finding" in needs_me_order


def test_reading_pipeline_embeds_source_and_claim_bases():
    text = (SRC / "system" / "dashboards" / "reading-pipeline.md").read_text(encoding="utf-8")
    assert "![[sources.base#To read & distill]]" in text
    assert "![[claims.base#By maturity]]" in text
    assert "```dataview" not in text


def test_fleeting_base_matches_capture_template_home():
    quickadd = yaml.safe_load((SRC / "system" / "dashboards" / "fleeting.base").read_text(encoding="utf-8"))
    text = (SRC / "system" / "dashboards" / "fleeting.base").read_text(encoding="utf-8")
    assert 'file.inFolder("notes/fleeting")' in text
    assert 'file.ext == "md"' in text
    assert 'type == "fleeting"' in text
    names = {v.get("name") for v in quickadd.get("views", [])}
    assert "To process" in names
