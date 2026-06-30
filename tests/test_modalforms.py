"""Modal Forms config for the remaining alpha.11 PI form."""

import json
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "vault-template"
MODALFORMS = SRC / ".obsidian" / "plugins" / "modalforms" / "data.json"


def _forms_by_name() -> dict:
    data = json.loads(MODALFORMS.read_text(encoding="utf-8"))
    return {form["name"]: form for form in data["formDefinitions"]}


def test_modal_forms_plugin_is_bundled():
    plugin_dir = SRC / ".obsidian" / "plugins" / "modalforms"
    for filename in ("main.js", "manifest.json", "styles.css", "data.json"):
        assert (plugin_dir / filename).is_file(), f"Modal Forms missing {filename}"
    assert (
        json.loads((plugin_dir / "manifest.json").read_text(encoding="utf-8"))["id"] == "modalforms"
    )
    roster = json.loads((SRC / ".obsidian" / "community-plugins.json").read_text(encoding="utf-8"))
    assert "modalforms" in roster


def test_modal_forms_have_alpha11_roster():
    assert set(_forms_by_name()) == {"memoria-note-capture"}


def test_note_capture_form_carries_prompt_instructions():
    form = _forms_by_name()["memoria-note-capture"]
    assert form["version"] == "1"
    fields = {field["name"]: field for field in form["fields"]}
    assert list(fields) == ["title", "description", "body"]
    assert fields["title"]["label"] == "Title"
    assert fields["description"]["label"] == "Description"
    assert fields["body"]["label"] == "Note body"
    assert fields["body"]["isRequired"] is True
    assert fields["body"]["input"] == {"type": "textarea"}
    assert "worker/check loop owns promotion" in fields["body"]["description"]
