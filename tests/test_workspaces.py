"""The shipped workspace layouts and the home.md control panel are internally consistent.

ADR-68: three workspaces (Desk / Library / Studio) share one layout contract —
every file a layout pins exists under src/, the Co-PI chat view is pinned in
every right sidebar, and home.md's command buttons dispatch only commands that
actually exist (a QuickAdd choice registered as `QuickAdd: <choice name>`, or
the agent-client chat command). The three workspace-switch choices must point
at the shipped loader script, which must know all three names.
"""

import json
import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
WORKSPACES = SRC / ".obsidian" / "workspaces.json"
QUICKADD = SRC / ".obsidian" / "plugins" / "quickadd" / "data.json"
HOMEPAGE = SRC / ".obsidian" / "plugins" / "homepage" / "data.json"
HOME = SRC / "home.md"
LOADER = SRC / "system" / "scripts" / "load-workspace.js"

WORKSPACE_NAMES = ["Desk", "Library", "Studio"]
COPI_VIEW = "agent-client-chat-view"
COPI_COMMAND = "Agent Client: Open chat view"


def _data():
    return json.loads(WORKSPACES.read_text(encoding="utf-8"))


def _leaves(node):
    """Flatten a workspace split tree into its leaf states."""
    if node.get("type") == "leaf":
        yield node["state"]
        return
    for child in node.get("children", []):
        yield from _leaves(child)


def test_three_workspaces_ship_and_desk_is_active():
    data = _data()
    assert sorted(data["workspaces"]) == sorted(WORKSPACE_NAMES)
    assert data["active"] == "Desk"


def test_homepage_replaces_saved_layout_on_startup():
    homepage = json.loads(HOMEPAGE.read_text(encoding="utf-8"))
    main = homepage["homepages"]["Main Homepage"]
    assert main["kind"] == "File"
    assert main["value"] == "home"
    assert main["openOnStartup"] is True
    assert main["openMode"] == "Replace all open notes"
    assert main["view"] == "Reading view"


def test_every_pinned_file_exists_under_src():
    for name, ws in _data()["workspaces"].items():
        for pane in ("main", "left", "right"):
            for leaf in _leaves(ws[pane]):
                file = leaf.get("state", {}).get("file")
                if file is not None:
                    assert (SRC / file).is_file(), (
                        f"{name}/{pane}: pinned file {file} missing under src/")


def test_base_files_use_the_bases_view_type():
    for name, ws in _data()["workspaces"].items():
        for pane in ("main", "left", "right"):
            for leaf in _leaves(ws[pane]):
                file = leaf.get("state", {}).get("file", "")
                if file.endswith(".base"):
                    assert leaf["type"] == "bases", (
                        f"{name}/{pane}: {file} must be a 'bases' leaf, got {leaf['type']}")


def test_copi_pinned_in_every_right_sidebar():
    for name, ws in _data()["workspaces"].items():
        types = [leaf["type"] for leaf in _leaves(ws["right"])]
        assert COPI_VIEW in types, f"{name}: no {COPI_VIEW} leaf in the right sidebar"


def test_main_pane_is_a_real_work_surface():
    for name, ws in _data()["workspaces"].items():
        leaves = list(_leaves(ws["main"]))
        assert leaves, f"{name}: empty main pane"
        for leaf in leaves:
            assert leaf["type"] != "empty", f"{name}: main pane has an empty leaf"
            assert leaf.get("state", {}).get("file") != "home.md", (
                f"{name}: home.md must not be pinned in a workspace (ADR-68)")


def test_file_explorer_is_the_last_left_tab():
    for name, ws in _data()["workspaces"].items():
        types = [leaf["type"] for leaf in _leaves(ws["left"])]
        assert types[-1] == "file-explorer", (
            f"{name}: file explorer must be the last left tab, got {types}")


def _choices():
    return json.loads(QUICKADD.read_text(encoding="utf-8"))["choices"]


def test_home_buttons_dispatch_registered_commands():
    text = HOME.read_text(encoding="utf-8")
    blocks = re.findall(r"```button\n(.*?)```", text, re.S)
    assert blocks, "no button blocks in home.md"
    choice_commands = {f"QuickAdd: {c['name']}" for c in _choices() if c.get("command")}
    for block in blocks:
        assert re.search(r"^type command$", block, re.M), (
            f"non-command button in home.md (ADR-68 bans them):\n{block}")
        action = re.search(r"^action (.+)$", block, re.M).group(1)
        assert action == COPI_COMMAND or action in choice_commands, (
            f"home.md button action {action!r} matches no registered command")


def test_workspace_choices_reference_the_loader_script():
    by_name = {c["name"]: c for c in _choices()}
    for ws in WORKSPACE_NAMES:
        choice = by_name.get(f"Memoria: workspace {ws}")
        assert choice, f"QuickAdd choice 'Memoria: workspace {ws}' missing"
        assert choice["command"], f"workspace {ws}: choice not exposed as a command"
        cmds = choice["macro"]["commands"]
        assert len(cmds) == 1 and cmds[0]["path"] == "system/scripts/load-workspace.js"
        assert cmds[0]["settings"] == {"Workspace": ws}


def test_loader_script_ships_and_names_all_three():
    assert LOADER.is_file()
    text = LOADER.read_text(encoding="utf-8")
    for ws in WORKSPACE_NAMES:
        assert f'"{ws}"' in text, f"load-workspace.js does not mention {ws}"


def test_buttons_plugin_is_bundled():
    manifest = SRC / ".obsidian" / "plugins" / "buttons" / "manifest.json"
    assert manifest.is_file()
    assert json.loads(manifest.read_text(encoding="utf-8"))["id"] == "buttons"
    roster = json.loads(
        (SRC / ".obsidian" / "community-plugins.json").read_text(encoding="utf-8"))
    assert "buttons" in roster
