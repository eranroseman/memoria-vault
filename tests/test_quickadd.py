"""The shipped QuickAdd surface matches the alpha.11 reset."""

import json
import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "vault-template"
QUICKADD = SRC / ".obsidian" / "plugins" / "quickadd" / "data.json"
CMDR = SRC / ".obsidian" / "plugins" / "cmdr" / "data.json"
MODALFORMS = SRC / ".obsidian" / "plugins" / "modalforms" / "data.json"
SCRIPTS = SRC / "system" / "scripts"

EXPECTED_SCRIPTS = {
    "capture-note.js",
    "open-inbox.js",
    "quickadd-utils.js",
    "record-exploration-trace.js",
    "resolve-inbox-card.js",
    "restore-memoria-shell.js",
}
EXPECTED_COMMANDS = {
    "Memoria: capture note",
    "Memoria: dismiss inbox card",
    "Memoria: open Inbox",
    "Memoria: record exploration trace",
    "Memoria: resolve inbox card",
}
RETIRED_TYPE_LITERALS = {
    "type: alert",
    "type: candidate",
    "type: claim",
    "type: dataset",
    "type: eval-task",
    "type: fleeting",
    "type: gap",
    "type: maintenance",
    "type: paper",
    "type: pattern",
    "type: queue",
    "type: repository",
    "type: space",
    "type: thesis",
    "type: worker-card",
    "type: worklist-item",
    "type: work-prompt",
}


def _quickadd_choices():
    return json.loads(QUICKADD.read_text(encoding="utf-8"))["choices"]


def _script_paths():
    return {
        cmd["path"]
        for choice in _quickadd_choices()
        if choice["type"] == "Macro"
        for cmd in choice["macro"]["commands"]
        if cmd["type"] == "UserScript"
    }


def test_command_labels_are_the_alpha11_surface():
    commands = {choice["name"] for choice in _quickadd_choices() if choice.get("command")}
    assert commands == EXPECTED_COMMANDS

    startup = {choice["name"] for choice in _quickadd_choices() if choice.get("runOnStartup")}
    assert startup == {"Memoria: restore shell on startup"}


def test_macro_choices_reference_existing_scripts_and_unique_ids():
    seen = set()
    for choice in _quickadd_choices():
        ids = [choice["id"]]
        if choice["type"] != "Macro":
            continue
        assert choice["macro"]["name"] == choice["name"]
        assert choice["macro"].get("id"), f"{choice['name']}: macro has no id"
        ids.append(choice["macro"]["id"])
        for cmd in choice["macro"]["commands"]:
            ids.append(cmd["id"])
            if cmd["type"] == "UserScript":
                script = SRC / cmd["path"]
                assert script.is_file(), f"{choice['name']}: missing {cmd['path']}"
                assert cmd["path"].startswith("system/scripts/")
        for id_ in ids:
            assert id_ not in seen, f"duplicate QuickAdd id {id_}"
            seen.add(id_)


def test_only_alpha11_quickadd_scripts_ship():
    scripts = {path.name for path in SCRIPTS.glob("*.js")}
    assert scripts == EXPECTED_SCRIPTS
    assert _script_paths() == {
        "system/scripts/capture-note.js",
        "system/scripts/open-inbox.js",
        "system/scripts/record-exploration-trace.js",
        "system/scripts/resolve-inbox-card.js",
        "system/scripts/restore-memoria-shell.js",
    }


def test_quickadd_scripts_do_not_emit_retired_types_or_hermes_cards():
    for script in SCRIPTS.glob("*.js"):
        text = script.read_text(encoding="utf-8")
        assert "queueHermesCard" not in text, script.name
        assert "hermes kanban create" not in text, script.name
        for literal in RETIRED_TYPE_LITERALS:
            assert literal not in text, f"{script.name}: {literal}"


def test_cmdr_buttons_reference_live_quickadd_commands():
    live_ids = {choice["id"]: choice["name"] for choice in _quickadd_choices()}
    config = json.loads(CMDR.read_text(encoding="utf-8"))
    for zone in ("leftRibbon", "pageHeader"):
        for button in config[zone]:
            id_ = button["id"].removeprefix("quickadd:choice:")
            assert id_ in live_ids, button
            assert button["name"] == live_ids[id_]


def test_modalforms_only_ships_note_capture_after_schema_reset():
    forms = json.loads(MODALFORMS.read_text(encoding="utf-8"))["formDefinitions"]
    assert [form["name"] for form in forms] == ["memoria-note-capture"]
    field_names = [field["name"] for field in forms[0]["fields"]]
    assert field_names == ["title", "description", "body"]


def test_note_capture_is_guided_and_writes_unchecked_note_concept():
    choices = {choice["name"]: choice for choice in _quickadd_choices()}
    choice = choices["Memoria: capture note"]
    assert choice["type"] == "Macro"
    [cmd] = choice["macro"]["commands"]
    assert cmd["path"] == "system/scripts/capture-note.js"
    assert "openFile" not in choice

    script = (SCRIPTS / "capture-note.js").read_text(encoding="utf-8")
    for marker in (
        "openForm(FORM_NAME)",
        'FORM_NAME = "memoria-note-capture"',
        'NOTE_FOLDER = "knowledge/notes/"',
        'TEMPLATE_PATH = "system/templates/note.md"',
        "renderNoteTemplate(template, title, data.description, data.body)",
        "Note text is required.",
    ):
        assert marker in script
    template = (SRC / "system" / "templates" / "note.md").read_text(encoding="utf-8")
    for marker in ("type: note", "check_status: unchecked", "description:"):
        assert marker in template
    assert "openFile" not in script


def test_resolve_inbox_card_resolves_attention_projection():
    script = (SCRIPTS / "resolve-inbox-card.js").read_text(encoding="utf-8")
    for marker in (
        '"Dismiss": "resolved"',
        'ATTENTION_LOG = "system/logs/attention.jsonl"',
        'TRIAGE_LOG = "system/logs/triage.jsonl"',
        'event: "attention_resolved"',
        'fm.projection !== "attention"',
        "fm.attention_status = attentionStatus",
        "fm.resolved_at = resolvedAt",
        "appendJsonl(app, ATTENTION_LOG, attentionRow)",
        "appendJsonl(app, TRIAGE_LOG, triageRow)",
        'getAbstractFileByPath("spaces/inbox.md")',
    ):
        assert marker in script
    assert "fm.lifecycle" not in script
    assert "card_type" not in script

    choices = {choice["name"]: choice for choice in _quickadd_choices()}
    dismiss = choices["Memoria: dismiss inbox card"]["macro"]["commands"][0]
    assert dismiss["path"] == "system/scripts/resolve-inbox-card.js"
    assert dismiss["settings"] == {"Outcome": "Dismiss"}


def test_startup_macro_restores_saved_memoria_shell():
    choices = {choice["name"]: choice for choice in _quickadd_choices()}
    choice = choices["Memoria: restore shell on startup"]
    assert choice["type"] == "Macro"
    assert choice["command"] is False
    assert choice["runOnStartup"] is True

    [cmd] = choice["macro"]["commands"]
    assert cmd["path"] == "system/scripts/restore-memoria-shell.js"

    script = (SCRIPTS / "restore-memoria-shell.js").read_text(encoding="utf-8")
    assert 'WORKSPACE_NAME = "Memoria"' in script
    assert 'NAV_FILE = "_nav.md"' in script
    assert "RAIL_SETTLE_MS = 500" in script
    assert "internalPlugins?.plugins?.workspaces?.instance" in script
    assert "if (await revealNavRail(app)) return;" in script
    assert "loadWorkspace(WORKSPACE_NAME)" in script
    assert "getLeavesOfType" in script
    assert "setTimeout(resolve, RAIL_SETTLE_MS)" in script
    assert "revealLeaf(navLeaf)" in script


def test_exploration_trace_capture_is_project_local_and_not_canonical():
    choices = {choice["name"]: choice for choice in _quickadd_choices()}
    choice = choices["Memoria: record exploration trace"]
    [cmd] = choice["macro"]["commands"]
    assert cmd["path"] == "system/scripts/record-exploration-trace.js"

    script = (SCRIPTS / "record-exploration-trace.js").read_text(encoding="utf-8")
    for marker in (
        'MAPS_DIR = "knowledge/notes/maps/"',
        '"type: note"',
        '"check_status: unchecked"',
        '"# Exploration trace"',
        '"## Rejected direction"',
        '"## Why rejected"',
        '"## Evidence checked"',
        '"## Retry only if"',
        "never adopted automatically into curated knowledge",
        "isMapReport(reportPath)",
    ):
        assert marker in script
    for forbidden in (
        "knowledge/hubs/",
        "knowledge/projects/",
        "type: hub",
    ):
        assert forbidden not in script


def test_quickadd_scripts_resolve_shared_helpers_from_vault_root():
    for script in SCRIPTS.glob("*.js"):
        text = script.read_text(encoding="utf-8")
        assert 'require("./quickadd-utils")' not in text, script.name
        assert 'require("./quickadd-similarity")' not in text, script.name
    helper_users = ["capture-note.js", "record-exploration-trace.js"]
    for name in helper_users:
        text = (SCRIPTS / name).read_text(encoding="utf-8")
        assert "system/scripts/quickadd-utils.js" in text
        assert "getBasePath" in text


def test_command_labels_do_not_reintroduce_articles():
    banned = re.compile(r"^Memoria: (?:delegate a task|run a pattern|workspace )")
    commands = {choice["name"] for choice in _quickadd_choices() if choice.get("command")}
    assert not any(banned.match(name) for name in commands)
