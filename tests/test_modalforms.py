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
    assert (
        json.loads((plugin_dir / "manifest.json").read_text(encoding="utf-8"))["id"] == "modalforms"
    )
    roster = json.loads((SRC / ".obsidian" / "community-plugins.json").read_text(encoding="utf-8"))
    assert "modalforms" in roster


def test_source_capture_form_uses_vocabulary_options():
    form = _source_capture_form()
    assert form["version"] == "1"
    fields = {field["name"]: field for field in form["fields"]}

    assert fields["research_area"]["input"]["type"] == "multiselect"
    assert fields["research_area"]["input"]["source"] == "fixed"
    assert fields["research_area"]["input"]["multi_select_options"] == _terms("research_area")

    assert fields["methodology"]["input"]["type"] == "multiselect"
    assert fields["methodology"]["input"]["source"] == "fixed"
    assert fields["methodology"]["input"]["multi_select_options"] == _terms("methodology")


def test_structured_capture_forms_cover_source_and_project_setup():
    forms = _forms_by_name()
    assert {
        "memoria-fleeting-capture",
        "memoria-source-capture",
        "memoria-claim-capture",
        "memoria-hub-capture",
        "memoria-project-start",
        "memoria-thesis-capture",
    } <= set(forms)


def test_fleeting_capture_form_carries_prompt_instructions():
    form = _forms_by_name()["memoria-fleeting-capture"]
    fields = {field["name"]: field for field in form["fields"]}
    assert fields["body"]["label"] == "Thought, quote, or idea"
    assert fields["body"]["isRequired"] is True
    assert (
        "Capture first; distill or archive from the Inbox later." in fields["body"]["description"]
    )


def test_modal_forms_data_is_generated_from_schema():
    import subprocess

    subprocess.run(
        ["python", "scripts/gen-forms.py", "--check"],
        cwd=SRC.parent,
        check=True,
    )


def test_project_start_form_is_available_for_later_automation():
    form = _forms_by_name()["memoria-project-start"]
    assert form["version"] == "1"
    fields = {field["name"]: field for field in form["fields"]}
    for required in (
        "title",
        "slug",
        "scope_topics",
        "inquiry_population",
        "inquiry_outcome",
        "output_mode",
    ):
        assert fields[required]["isRequired"] is True
    assert fields["scope_topics"]["input"]["multi_select_options"] == _terms("research_area")
    assert [o["value"] for o in fields["output_mode"]["input"]["options"]] == ["thesis", "survey"]


def test_source_capture_uses_catalog_note_picker():
    fields = {
        field["name"]: field for field in _forms_by_name()["memoria-source-capture"]["fields"]
    }
    assert fields["entity"]["input"] == {"type": "note", "folder": "catalog"}


def test_claim_and_thesis_sources_use_catalog_paper_picker():
    for form_name in ("memoria-claim-capture", "memoria-thesis-capture"):
        fields = {field["name"]: field for field in _forms_by_name()[form_name]["fields"]}
        assert fields["sources"]["input"] == {
            "type": "multiselect",
            "source": "notes",
            "folder": "catalog/papers",
        }


def test_project_start_form_covers_project_schema_fields():
    fields = {field["name"] for field in _forms_by_name()["memoria-project-start"]["fields"]}
    assert {
        "title",
        "slug",
        "scope_topics",
        "inquiry_population",
        "inquiry_intervention",
        "inquiry_comparison",
        "inquiry_outcome",
        "finer_feasible",
        "finer_novel",
        "finer_relevant",
        "output_mode",
    } <= fields
