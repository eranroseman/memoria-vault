"""The QuickAdd palette config is internally consistent.

Every Macro choice in the shipped quickadd data.json points at a user script
that actually exists under system/scripts/, and every macro a choice embeds
carries an id (Obsidian resolves commands by these ids — a dangling reference
makes the palette entry a silent no-op).
"""

import json
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
DATA = SRC / ".obsidian" / "plugins" / "quickadd" / "data.json"


def _choices():
    return json.loads(DATA.read_text(encoding="utf-8"))["choices"]


def test_macro_choices_reference_existing_scripts():
    macros = [c for c in _choices() if c["type"] == "Macro"]
    assert macros, "no Macro choices found in quickadd data.json"
    for choice in macros:
        for cmd in choice["macro"]["commands"]:
            if cmd["type"] != "UserScript":
                continue
            script = SRC / cmd["path"]
            assert script.is_file(), (
                f"{choice['name']}: script {cmd['path']} missing under src/")
            assert cmd["path"].startswith("system/scripts/"), (
                f"{choice['name']}: script {cmd['path']} outside system/scripts/")


def test_macro_ids_exist_and_are_unique():
    seen = set()
    for choice in _choices():
        ids = [choice["id"]]
        if choice["type"] == "Macro":
            assert choice["macro"].get("id"), f"{choice['name']}: macro has no id"
            ids.append(choice["macro"]["id"])
            ids += [cmd["id"] for cmd in choice["macro"]["commands"]]
        for i in ids:
            assert i not in seen, f"duplicate QuickAdd id {i}"
            seen.add(i)
