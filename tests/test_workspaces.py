"""Alpha.7 space dashboards replace per-space workspace swapping."""

import json
import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
WORKSPACES = SRC / ".obsidian" / "workspaces.json"
QUICKADD = SRC / ".obsidian" / "plugins" / "quickadd" / "data.json"
HOMEPAGE = SRC / ".obsidian" / "plugins" / "homepage" / "data.json"
COMMANDER = SRC / ".obsidian" / "plugins" / "cmdr" / "data.json"
APP = SRC / ".obsidian" / "app.json"
CORE = SRC / ".obsidian" / "core-plugins.json"
COMMUNITY_PLUGINS = SRC / ".obsidian" / "community-plugins.json"
PORTALS = SRC / ".obsidian" / "plugins" / "portals" / "data.json"
OBSIDIAN_GIT = SRC / ".obsidian" / "plugins" / "obsidian-git" / "data.json"

SPACES = {
    "inbox": "spaces/inbox.md",
    "library": "spaces/library.md",
    "knowledge": "spaces/knowledge.md",
    "project": "spaces/project.md",
}
FIRST_ACTION_COMMANDS = {
    "inbox": [
        "Memoria: capture source from URL",
        "Memoria: capture fleeting",
        "Agent Client pane",
    ],
    "library": [
        "Memoria: capture source from URL",
        "Memoria: capture from Zotero selection",
        "Memoria: structured source capture",
    ],
    "knowledge": [
        "Memoria: write claim note",
        "Memoria: create linked claim note",
        "Memoria: link claim",
    ],
    "project": [
        "Memoria: start project",
        "Memoria: refresh project gate",
        "Memoria: draft section",
    ],
}
COPI_VIEW = "agent-client-chat-view"


def _workspace_data():
    return json.loads(WORKSPACES.read_text(encoding="utf-8"))


def _leaves(node):
    if node.get("type") == "leaf":
        yield node["state"]
        return
    for child in node.get("children", []):
        yield from _leaves(child)


def _choices():
    return json.loads(QUICKADD.read_text(encoding="utf-8"))["choices"]


def _quickadd_command_ids_by_name():
    return {
        choice["name"]: f"quickadd:choice:{choice['id']}"
        for choice in _choices()
        if choice.get("command")
    }


def test_single_reset_workspace_ships_and_opens_inbox():
    data = _workspace_data()
    assert sorted(data["workspaces"]) == ["Memoria"]
    assert data["active"] == "Memoria"

    ws = data["workspaces"]["Memoria"]
    main_files = [
        leaf.get("state", {}).get("file")
        for leaf in _leaves(ws["main"])
        if leaf.get("state", {}).get("file")
    ]
    assert main_files == ["spaces/inbox.md"]
    assert COPI_VIEW in [leaf["type"] for leaf in _leaves(ws["right"])]
    # Left pane is the navigation rail (ADR-114): the pinned nav note ahead of
    # the file-explorer escape hatch.
    left = list(_leaves(ws["left"]))
    assert [leaf["type"] for leaf in left] == ["markdown", "file-explorer"]
    assert left[0]["state"]["file"] == "spaces/_nav.md"


def test_homepage_opens_inbox_space_on_startup():
    homepage = json.loads(HOMEPAGE.read_text(encoding="utf-8"))
    main = homepage["homepages"]["Main Homepage"]
    assert main["kind"] == "File"
    assert main["value"] == "spaces/inbox"
    assert main["openOnStartup"] is True
    assert main["openMode"] == "Replace last note"
    assert main["view"] == "Reading view"
    assert main["pin"] is False


def test_space_dashboards_exist_and_link_to_each_other():
    for space, relpath in SPACES.items():
        path = SRC / relpath
        assert path.is_file(), f"{relpath} missing"
        text = path.read_text(encoding="utf-8")
        assert f"space: {space}" in text
        assert "cssclasses: memoria-space" in text
        assert "![[" in text, f"{relpath} does not embed any Bases views"
        for other, other_relpath in SPACES.items():
            if other == space:
                continue
            link = other_relpath.removesuffix(".md")
            assert f"[[{link}|" in text, f"{relpath} missing nav link to {link}"


def test_space_dashboards_have_day1_empty_state_actions():
    for space, relpath in SPACES.items():
        text = (SRC / relpath).read_text(encoding="utf-8")
        assert "[!suggestions] First actions" in text
        for command in FIRST_ACTION_COMMANDS[space]:
            assert command in text, f"{relpath} missing first action {command!r}"


def test_inbox_space_owns_fleeting_triage_queue():
    text = (SRC / "spaces" / "inbox.md").read_text(encoding="utf-8")
    assert "## Fleeting notes" in text
    assert "![[fleeting.base#To process]]" in text
    assert "distill, attach, or archive" in text


def test_space_guide_links_use_canonical_pages_routes():
    for relpath in SPACES.values():
        text = (SRC / relpath).read_text(encoding="utf-8")
        guide_links = re.findall(
            r"\]\((https://eranroseman\.github\.io/memoria-vault/how-to-guides/[^)]+)\)",
            text,
        )
        assert guide_links, f"{relpath} has no guide links"
        assert all(link.endswith(".html") for link in guide_links), relpath
        assert not any(link.endswith("/") for link in guide_links), relpath
        assert not any(link.endswith(".md") for link in guide_links), relpath


def test_space_dashboards_use_non_hidden_location():
    for relpath in SPACES.values():
        assert not relpath.startswith("system/"), f"{relpath} would be hidden by Portals"


def test_space_dashboards_hide_obsidian_properties_panel():
    snippet = (SRC / ".obsidian" / "snippets" / "memoria-property-badges.css").read_text(
        encoding="utf-8"
    )
    assert ".markdown-preview-view.memoria-space .metadata-container" in snippet
    assert ".markdown-source-view.memoria-space .metadata-container" in snippet
    assert "display: none;" in snippet


def test_every_pinned_file_exists_under_src():
    for name, ws in _workspace_data()["workspaces"].items():
        for pane in ("main", "left", "right"):
            for leaf in _leaves(ws[pane]):
                file = leaf.get("state", {}).get("file")
                if file is not None:
                    assert (SRC / file).is_file(), (
                        f"{name}/{pane}: pinned file {file} missing under src/"
                    )


def test_workspace_loader_choices_are_retired():
    names = {choice["name"] for choice in _choices()}
    assert "Memoria: open Desk workspace" not in names
    assert "Memoria: open Library workspace" not in names
    assert "Memoria: open Studio workspace" not in names
    assert "Memoria: open Project gate" not in names
    assert not (SRC / "system/scripts/load-workspace.js").exists()
    assert not (SRC / "system/scripts/open-project-gate.js").exists()


def test_commander_ribbon_keeps_global_actions_only():
    data = json.loads(COMMANDER.read_text(encoding="utf-8"))
    quickadd_ids = _quickadd_command_ids_by_name()

    expected_left_ribbon = [
        "Memoria: capture fleeting",
        "Memoria: capture from Zotero selection",
        "Memoria: capture source from URL",
        "Memoria: delegate task",
        "Memoria: resolve inbox card",
    ]
    expected_page_header = [
        "Memoria: capture fleeting",
        "Memoria: create linked claim note",
        "Memoria: write claim note",
        "Memoria: extract claims",
        "Memoria: link claim",
    ]

    assert data["showAddCommand"] is False
    for surface, names in (
        ("leftRibbon", expected_left_ribbon),
        ("pageHeader", expected_page_header),
    ):
        configured = data[surface]
        assert [entry["name"] for entry in configured] == names
        assert [entry["id"] for entry in configured] == [quickadd_ids[name] for name in names]
        assert all(entry["mode"] == "any" for entry in configured)


def test_app_json_ships_memoria_editor_settings():
    app = json.loads(APP.read_text(encoding="utf-8"))
    assert app == {
        "showInlineTitle": False,
        "readableLineLength": True,
        "newLinkFormat": "absolute",
        "alwaysUpdateLinks": True,
        "newFileLocation": "folder",
        "newFileFolderPath": "notes/fleeting",
        "attachmentFolderPath": "attachments",
        "trashOption": "local",
        "propertiesInDocument": "hidden",
    }


def test_core_plugin_toggles_match_alpha7_shell():
    core = json.loads(CORE.read_text(encoding="utf-8"))
    assert core["workspaces"] is True
    assert core["file-explorer"] is True
    assert core["templates"] is False
    assert core["daily-notes"] is False
    assert core["tag-pane"] is False


def test_portals_ships_curated_folder_navigation_with_core_fallback():
    portals = json.loads(PORTALS.read_text(encoding="utf-8"))
    spaces = portals["spaces"]
    assert [space["folderPath"] for space in spaces] == [
        "inbox",
        "catalog",
        "notes/sources",
        "notes/claims",
        "notes/hubs",
        "projects",
    ]
    assert {space["portalType"] for space in spaces} == {"folder"}
    assert portals["replaceFileExplorer"] is True
    assert portals["hiddenItems"] == {"system": True, ".memoria": True}
    assert portals["tagNotesFolderPath"] == "system/_tag-notes"
    assert portals["splitViewTabs"] == ["recent", "bookmarks", "context-notes", "trash"]

    roster = json.loads(COMMUNITY_PLUGINS.read_text(encoding="utf-8"))
    assert "portals" in roster
    assert "workspaces-plus" not in roster
    assert json.loads(CORE.read_text(encoding="utf-8"))["file-explorer"] is True


def test_obsidian_git_does_not_pull_on_boot_without_upstream():
    data = json.loads(OBSIDIAN_GIT.read_text(encoding="utf-8"))
    assert data["autoPullOnBoot"] is False
    assert data["pullBeforePush"] is True
    assert data["autoPushInterval"] == 0


def test_buttons_plugin_is_still_bundled_but_home_has_no_buttons():
    manifest = SRC / ".obsidian" / "plugins" / "buttons" / "manifest.json"
    assert manifest.is_file()
    assert json.loads(manifest.read_text(encoding="utf-8"))["id"] == "buttons"
    roster = json.loads(COMMUNITY_PLUGINS.read_text(encoding="utf-8"))
    assert "buttons" in roster
    assert "```button" not in (SRC / "home.md").read_text(encoding="utf-8")


def test_property_badge_snippet_ships_state_accents():
    snippet = SRC / ".obsidian" / "snippets" / "memoria-property-badges.css"
    css = snippet.read_text(encoding="utf-8")
    for marker in (
        'data-property-key="lifecycle"',
        'data-property-key="ingest_status"',
        'data-property-key="loudness"',
        '[value="complete"]',
        '[value="block"]',
    ):
        assert marker in css


def test_starter_vault_enables_memoria_snippets():
    appearance = json.loads((SRC / ".obsidian" / "appearance.json").read_text(encoding="utf-8"))
    assert set(appearance["enabledCssSnippets"]) >= {
        "memoria-link-colors",
        "memoria-property-badges",
    }


def test_link_color_snippet_ships_lifecycle_accents():
    snippet = SRC / ".obsidian" / "snippets" / "memoria-link-colors.css"
    css = snippet.read_text(encoding="utf-8")
    for marker in (
        'data-link-lifecycle="proposed"',
        'data-link-lifecycle="provisional"',
        'data-link-lifecycle="current"',
        'data-link-lifecycle="retracted"',
        'data-link-lifecycle="archived"',
        "--memoria-link-proposed-color",
    ):
        assert marker in css


def test_space_dashboard_embeds_reference_existing_base_names():
    base_names = {path.name for path in SRC.rglob("*.base")}
    for relpath in SPACES.values():
        text = (SRC / relpath).read_text(encoding="utf-8")
        for base in re.findall(r"!\[\[([^#\]]+\.base)", text):
            assert base in base_names, f"{relpath} embeds missing base {base}"
