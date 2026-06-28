"""Every shipped .base view stays in sync with the schemas (ADR-49 risk control).

Bases have no schema enforcement by design; this test is our side of the contract —
every frontmatter property a .base references must exist in the schema of a type
homed in the folder(s) the base draws from.
"""

import re
from pathlib import Path

import yaml
from operations.lib import schema

SRC = Path(__file__).resolve().parent.parent / "vault-template"

# properties Obsidian provides on every note
_BUILTIN_PREFIXES = ("file.", "formula.", "this.")
_BUILTIN = {"type", "lifecycle"}


def _bases() -> list[Path]:
    return sorted(SRC.rglob("*.base"))


def _base_path_for_embed(target: str) -> Path:
    direct = SRC / target
    if direct.is_file():
        return direct
    matches = [path for path in _bases() if path.name == Path(target).name]
    assert len(matches) == 1, f"{target}: expected one matching .base, found {matches}"
    return matches[0]


def _base_view_names(path: Path) -> set[str]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {view.get("name") for view in data.get("views", [])}


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
    "file",
    "inFolder",
    "ext",
    "md",
    "and",
    "or",
    "not",
    "hasTag",
    "hasLink",
    "now",
    "today",
    "date",
    "if",
    "true",
    "false",
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


def test_base_views_start_with_clickable_note_links():
    """Every Base row should expose the underlying note as the first visible field."""
    for b in _bases():
        data = yaml.safe_load(b.read_text(encoding="utf-8"))
        formulas = data.get("formulas") or {}
        properties = data.get("properties") or {}
        assert "note" in formulas, f"{b}: missing clickable note formula"
        assert str(formulas["note"]).startswith("link(file.path,"), (
            f"{b}: note formula must link to file.path"
        )
        assert properties["formula.note"]["displayName"] == "Note", (
            f"{b}: note formula should display as Note"
        )
        for view in data.get("views", []):
            order = view.get("order", [])
            assert order and order[0] == "formula.note", (
                f"{b}::{view.get('name')} should start with formula.note"
            )
            assert not {"title", "name", "file.name"} & set(order), (
                f"{b}::{view.get('name')} uses a non-clickable identity column"
            )


def test_markdown_base_embeds_reference_existing_views():
    for note in sorted(SRC.rglob("*.md")):
        text = note.read_text(encoding="utf-8")
        for target, view_name in re.findall(r"!\[\[([^#\]]+\.base)#([^\]]+)\]\]", text):
            base = _base_path_for_embed(target)
            assert view_name in _base_view_names(base), (
                f"{note}: embeds {target}#{view_name}, missing in {base}"
            )


def test_inbox_base_has_needs_me_view():
    inbox = SRC / "inbox" / "inbox.base"
    data = yaml.safe_load(inbox.read_text(encoding="utf-8"))
    views = {v.get("name"): v for v in data.get("views", [])}
    names = set(views)
    assert "Needs me" in names  # the Inbox queue embeds this view by name
    assert data["formulas"]["note"] == (
        'link(file.path, if(action.isEmpty() || action == title, title, title + " - " + action))'
    )
    assert data["properties"]["formula.note"]["displayName"] == "Note"
    needs_me_order = views["Needs me"]["order"]
    assert needs_me_order[0] == "formula.note"
    assert "title" not in needs_me_order
    assert "action" not in needs_me_order
    assert needs_me_order == ["formula.note", "formula.age_days"]
    assert views["Needs me"]["columnSize"] == {"formula.note": 760, "formula.age_days": 72}
    needs_me_filter = " ".join(views["Needs me"]["filters"]["and"])
    assert 'lifecycle == "proposed"' in needs_me_filter
    assert all(card_type in needs_me_filter for card_type in ("candidate", "gap", "work-prompt"))
    assert "flag" not in needs_me_filter
    assert "alert" not in needs_me_filter


def test_inbox_space_embeds_activity_from_worker_cards():
    text = (SRC / "spaces" / "inbox.md").read_text(encoding="utf-8")
    assert "![[inbox.base#Needs me]]" in text
    assert "![[board.base#Inbox activity]]" in text
    assert text.index("## Activity") < text.index("## Needs me") < text.index("## Fleeting notes")

    board = yaml.safe_load((SRC / "system" / "board" / "board.base").read_text(encoding="utf-8"))
    views = {v.get("name"): v for v in board.get("views", [])}
    assert "Inbox activity" in views
    assert 'file.inFolder("system/board")' in (SRC / "system" / "board" / "board.base").read_text(
        encoding="utf-8"
    )
    assert 'type == "worker-card"' in (SRC / "system" / "board" / "board.base").read_text(
        encoding="utf-8"
    )
    assert views["Inbox activity"]["order"] == [
        "formula.note",
        "expected_outputs",
        "formula.age_min",
    ]
    activity_filter = " ".join(views["Inbox activity"]["filters"]["and"])
    assert all(status in activity_filter for status in ("triage", "todo", "ready", "running"))
    assert "blocked" not in activity_filter
    assert "done" not in activity_filter


def test_project_space_embeds_project_gate_views():
    text = (SRC / "spaces" / "project.md").read_text(encoding="utf-8")
    assert "![[projects.base#Active projects]]" in text
    assert "![[projects.base#Needs refutation stamp]]" in text
    base_path = SRC / "projects" / "projects.base"
    base_text = base_path.read_text(encoding="utf-8")
    base = yaml.safe_load(base_text)
    views = {v.get("name"): v for v in base.get("views", [])}
    assert {"Active projects", "Needs refutation stamp"} <= set(views)
    assert views["Active projects"]["groupBy"]["property"] == "output_mode"
    assert "refutation_sufficiency" in views["Active projects"]["order"]
    assert "refutation_sufficiency != true" in base_text


def test_consolidated_dashboard_alias_pages_are_retired():
    retired = {
        "contradictions.md",
        "discuss-queue.md",
        "drift-watch.md",
        "loose-ends.md",
        "open-questions.md",
        "project-gate.md",
        "project-gate.base",
        "reading-pipeline.md",
        "weekly-review.md",
    }
    dashboard_dir = SRC / "system" / "dashboards"
    for name in retired:
        assert not (dashboard_dir / name).exists()
    assert {path.name for path in dashboard_dir.glob("*.md")} == {
        "audit-log.md",
        "board-state.md",
        "eval-trend.md",
        "fleet-health.md",
        "skill-state.md",
    }


def test_fleeting_base_matches_capture_template_home():
    quickadd = yaml.safe_load(
        (SRC / "system" / "dashboards" / "fleeting.base").read_text(encoding="utf-8")
    )
    text = (SRC / "system" / "dashboards" / "fleeting.base").read_text(encoding="utf-8")
    assert 'file.inFolder("notes/fleeting")' in text
    assert 'file.ext == "md"' in text
    assert 'type == "fleeting"' in text
    names = {v.get("name") for v in quickadd.get("views", [])}
    assert "To process" in names
    views = {v.get("name"): v for v in quickadd.get("views", [])}
    assert quickadd["formulas"]["note"] == "link(file.path, title)"
    assert quickadd["properties"]["formula.note"]["displayName"] == "Note"
    assert views["To process"]["order"][0] == "formula.note"
    assert "title" not in views["To process"]["order"]


def test_maintenance_has_weekly_digest_without_queue_duplication():
    text = (SRC / "spaces" / "maintenance.md").read_text(encoding="utf-8")
    assert 'FROM "catalog"' in text
    assert 'FROM "notes"' in text
    assert 'AND type != "fleeting"' in text
    assert "![[fleeting.base#To process]]" not in text


def test_key_bases_surface_lifecycle_near_left_edge():
    """The PI-facing state should be visible without horizontal scanning (#145)."""
    bases = [
        SRC / "system" / "dashboards" / "sources.base",
        SRC / "catalog" / "catalog.base",
        SRC / "inbox" / "inbox.base",
        SRC / "system" / "dashboards" / "claims.base",
    ]
    for path in bases:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for view in data.get("views", []):
            order = view.get("order", [])
            if "lifecycle" in order:
                assert order.index("lifecycle") <= 1, (
                    f"{path.name}::{view.get('name')} buries lifecycle"
                )


def test_worklists_base_groups_by_worklist_decision_and_group():
    data = yaml.safe_load(
        (SRC / "system" / "worklists" / "worklists.base").read_text(encoding="utf-8")
    )
    text = (SRC / "system" / "worklists" / "worklists.base").read_text(encoding="utf-8")
    assert 'file.inFolder("system/worklists")' in text
    assert 'type == "worklist-item"' in text
    views = {v.get("name"): v for v in data.get("views", [])}
    assert {"By worklist", "By decision", "By group"} <= set(views)
    assert views["By worklist"]["groupBy"]["property"] == "worklist"
    assert views["By decision"]["groupBy"]["property"] == "decision"
    assert views["By group"]["groupBy"]["property"] == "group"
    for view in views.values():
        order = view.get("order", [])
        assert "lifecycle" in order and order.index("lifecycle") <= 1
        assert "decision" in order and order.index("decision") <= 2
