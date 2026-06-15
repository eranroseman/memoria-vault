"""Modal Forms capture config stays sourced from system/vocabulary.md."""

import json
import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
VOCABULARY = SRC / "system" / "vocabulary.md"
MODALFORMS = SRC / ".obsidian" / "plugins" / "modalforms" / "data.json"


def _terms(section: str) -> list[str]:
    text = VOCABULARY.read_text(encoding="utf-8")
    match = re.search(rf"^## {re.escape(section)}\n(?P<body>.*?)(?=^## |\Z)", text, re.S | re.M)
    assert match, f"{section} section missing from system/vocabulary.md"
    return re.findall(r"^- ([a-z0-9-]+) — ", match.group("body"), re.M)


def _forms_by_name() -> dict:
    data = json.loads(MODALFORMS.read_text(encoding="utf-8"))
    return {form["name"]: form for form in data["formDefinitions"]}


def _source_capture_form() -> dict:
    return _forms_by_name()["memoria-source-capture"]


def test_modal_forms_plugin_is_bundled():
    plugin_dir = SRC / ".obsidian" / "plugins" / "modalforms"
    for filename in ("main.js", "manifest.json", "styles.css", "data.json"):
        assert (plugin_dir / filename).is_file(), f"Modal Forms missing {filename}"
    assert json.loads((plugin_dir / "manifest.json").read_text(encoding="utf-8"))["id"] == "modalforms"
    roster = json.loads((SRC / ".obsidian" / "community-plugins.json").read_text(encoding="utf-8"))
    assert "modalforms" in roster


def test_source_capture_form_uses_vocabulary_options():
    form = _source_capture_form()
    assert form["version"] == "1"
    fields = {field["name"]: field for field in form["fields"]}

    assert fields["research_area"]["input"]["type"] == "multiselect"
    assert fields["research_area"]["input"]["source"] == "fixed"
    assert fields["research_area"]["input"]["options"] == _terms("research_area")

    assert fields["methodology"]["input"]["type"] == "multiselect"
    assert fields["methodology"]["input"]["source"] == "fixed"
    assert fields["methodology"]["input"]["options"] == _terms("methodology")



def test_structured_capture_forms_cover_source_and_project_setup():
    forms = _forms_by_name()
    assert {"memoria-source-capture", "memoria-project-start"} <= set(forms)


def test_project_start_form_is_available_for_later_automation():
    form = _forms_by_name()["memoria-project-start"]
    assert form["version"] == "1"
    fields = {field["name"]: field for field in form["fields"]}
    for required in ("title", "slug", "goal"):
        assert fields[required]["isRequired"] is True
    assert fields["research_area"]["input"]["options"] == _terms("research_area")
    assert fields["methodology"]["input"]["options"] == _terms("methodology")
