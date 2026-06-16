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
COMMANDER = SRC / ".obsidian" / "plugins" / "cmdr" / "data.json"
HOME = SRC / "home.md"
DESK_DASHBOARD = SRC / "system" / "dashboards" / "desk.md"
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

def test_workspace_main_panes_open_gate_dashboards():
    expected = {
        "Desk": "system/dashboards/desk.md",
        "Library": "system/dashboards/library.md",
        "Studio": "system/dashboards/studio.md",
    }
    for name, ws in _data()["workspaces"].items():
        files = [
            leaf.get("state", {}).get("file")
            for leaf in _leaves(ws["main"])
            if leaf.get("state", {}).get("file")
        ]
        assert files == [expected[name]], f"{name}: unexpected main pane files {files}"

def test_file_explorer_is_the_last_left_tab():
    for name, ws in _data()["workspaces"].items():
        types = [leaf["type"] for leaf in _leaves(ws["left"])]
        assert types[-1] == "file-explorer", (
            f"{name}: file explorer must be the last left tab, got {types}")


def _choices():
    return json.loads(QUICKADD.read_text(encoding="utf-8"))["choices"]


def _quickadd_command_ids_by_name():
    return {
        choice["name"]: f"quickadd:choice:{choice['id']}"
        for choice in _choices()
        if choice.get("command")
    }


def _assert_buttons_dispatch_registered_commands(path):
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(r"```button\n(.*?)```", text, re.S)
    assert blocks, f"no button blocks in {path.relative_to(SRC)}"
    choice_commands = {f"QuickAdd: {c['name']}" for c in _choices() if c.get("command")}
    for block in blocks:
        assert re.search(r"^type command$", block, re.M), (
            f"non-command button in {path.relative_to(SRC)} (ADR-68 bans them):\n{block}")
        action = re.search(r"^action (.+)$", block, re.M).group(1)
        assert action == COPI_COMMAND or action in choice_commands, (
            f"{path.relative_to(SRC)} button action {action!r} matches no registered command")

def test_home_status_line_reads_linter_verdict_and_board_queue_depths():
    text = HOME.read_text(encoding="utf-8")

    assert "> [!brief] Status line" in text
    assert "dv.pages(" in text
    assert "system/metrics" in text
    assert 'page.type === "lint-verdict"' in text
    assert 'system/logs/lint-findings.jsonl' in text
    assert 'system/logs/board-state.jsonl' in text
    for field in ("running", "blocked", "review_queue", "retrying"):
        assert f"totals.{field}" in text
    assert "Active:" in text and "Waiting:" in text
    assert "Review:" in text and "Retries:" in text

def test_home_buttons_dispatch_registered_commands():
    _assert_buttons_dispatch_registered_commands(HOME)

def test_desk_dashboard_buttons_dispatch_registered_commands():
    _assert_buttons_dispatch_registered_commands(DESK_DASHBOARD)

def test_workspace_choices_reference_the_loader_script():
    by_name = {c["name"]: c for c in _choices()}
    for ws in WORKSPACE_NAMES:
        command = f"Memoria: open {ws} workspace"
        choice = by_name.get(command)
        assert choice, f"QuickAdd choice {command!r} missing"
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

def test_commander_plugin_is_bundled():
    plugin_dir = SRC / ".obsidian" / "plugins" / "cmdr"
    for filename in ("main.js", "manifest.json", "styles.css", "data.json"):
        assert (plugin_dir / filename).is_file(), f"Commander missing {filename}"
    assert json.loads((plugin_dir / "manifest.json").read_text(encoding="utf-8"))["id"] == "cmdr"
    roster = json.loads(
        (SRC / ".obsidian" / "community-plugins.json").read_text(encoding="utf-8"))
    assert "cmdr" in roster

def test_commander_toolbar_commands_reference_quickadd_choices():
    data = json.loads(COMMANDER.read_text(encoding="utf-8"))
    quickadd_ids = _quickadd_command_ids_by_name()

    expected_left_ribbon = [
        "Memoria: capture fleeting",
        "Memoria: capture from Zotero selection",
        "Memoria: capture source from URL",
        "Memoria: delegate task",
        "Memoria: resolve inbox card",
        "Memoria: open Desk workspace",
        "Memoria: open Library workspace",
        "Memoria: open Studio workspace",
    ]
    expected_page_header = [
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
        assert [entry["id"] for entry in configured] == [
            quickadd_ids[name] for name in names
        ]
        assert all(entry["mode"] == "any" for entry in configured)

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
    appearance = json.loads(
        (SRC / ".obsidian" / "appearance.json").read_text(encoding="utf-8")
    )
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
        '--memoria-link-proposed-color',
    ):
        assert marker in css
