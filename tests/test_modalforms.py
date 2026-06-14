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


def _source_capture_form() -> dict:
    data = json.loads(MODALFORMS.read_text(encoding="utf-8"))
    forms = {form["name"]: form for form in data["formDefinitions"]}
    return forms["memoria-source-capture"]


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
