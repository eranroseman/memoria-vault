"""Modal Forms capture config stays sourced from type schemas and vocabulary."""

import json
import re
from pathlib import Path

import yaml

SRC = Path(__file__).resolve().parent.parent / "src"
SCHEMA_DIR = SRC / ".memoria" / "schemas" / "types"
VOCABULARY = SRC / "system" / "vocabulary.md"
MODALFORMS = SRC / ".obsidian" / "plugins" / "modalforms" / "data.json"
FORM_TYPES = ("fleeting", "source", "claim", "project")


def _schema(type_name: str) -> dict:
    return yaml.safe_load((SCHEMA_DIR / f"{type_name}.yaml").read_text(encoding="utf-8"))


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


def test_modal_forms_match_type_schema_creation_metadata():
    forms = _forms_by_name()
    assert set(forms) == {
        _schema(type_name)["creation"]["form"]["name"] for type_name in FORM_TYPES
    }

    for type_name in FORM_TYPES:
        schema = _schema(type_name)
        spec = schema["creation"]["form"]
        form = forms[spec["name"]]
        assert form["title"] == spec["title"]
        assert form["version"] == "1"
        assert [field["name"] for field in form["fields"]] == [
            field["name"] for field in spec["fields"]
        ]

        generated_fields = {field["name"]: field for field in form["fields"]}
        for field in spec["fields"]:
            generated = generated_fields[field["name"]]
            assert generated["label"] == field["label"]
            assert generated.get("description", "") == field.get("description", "")
            assert generated.get("isRequired", False) is bool(field.get("required", False))
            assert generated.get("condition") == field.get("condition")
            enum_name = field["input"].get("enum")
            if enum_name:
                assert [option["value"] for option in generated["input"]["options"]] == schema[
                    "enums"
                ][enum_name]


def test_structured_capture_forms_cover_source_and_project_setup():
    forms = _forms_by_name()
    assert {
        "memoria-fleeting-capture",
        "memoria-source-capture",
        "memoria-claim-capture",
        "memoria-project-start",
    } == set(forms)


def test_fleeting_capture_form_carries_prompt_instructions():
    form = _forms_by_name()["memoria-fleeting-capture"]
    fields = {field["name"]: field for field in form["fields"]}
    assert fields["body"]["label"] == "Thought, quote, or idea"
    assert fields["body"]["isRequired"] is True
    assert (
        "Capture first; distill or archive from the Inbox later." in fields["body"]["description"]
    )


def test_claim_capture_form_carries_prompt_instructions():
    form = _forms_by_name()["memoria-claim-capture"]
    fields = {field["name"]: field for field in form["fields"]}
    assert fields["title"]["description"] == "Short label for the note and Base row."
    assert (
        fields["maturity"]["description"]
        == "Start at seedling unless the claim is already well supported."
    )
    assert (
        fields["sources"]["description"]
        == "Pick the catalog paper(s) whose citekeys support this claim."
    )
    assert (
        fields["claim"]["description"]
        == "One durable, source-grounded assertion in your own words."
    )
    for required in ("title", "maturity", "sources", "claim"):
        assert fields[required]["isRequired"] is True


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
    for required in ("title", "output_mode"):
        assert fields[required]["isRequired"] is True
    assert fields["scope_topics"].get("isRequired", False) is False
    assert fields["scope_topics"]["input"]["multi_select_options"] == _terms("research_area")
    assert [o["value"] for o in fields["output_mode"]["input"]["options"]] == ["thesis", "survey"]
    assert fields["provisional_thesis"]["condition"] == {
        "dependencyName": "output_mode",
        "type": "isExactly",
        "value": "thesis",
    }
    assert fields["provisional_thesis"].get("isRequired", False) is False


def test_source_capture_uses_catalog_note_picker():
    fields = {
        field["name"]: field for field in _forms_by_name()["memoria-source-capture"]["fields"]
    }
    assert fields["entity"]["input"] == {"type": "note", "folder": "catalog"}


def test_claim_sources_use_catalog_paper_picker():
    fields = {field["name"]: field for field in _forms_by_name()["memoria-claim-capture"]["fields"]}
    assert fields["sources"]["input"] == {
        "type": "multiselect",
        "source": "notes",
        "folder": "catalog/papers",
    }


def test_project_start_form_uses_adr119_phase5_fields():
    fields = {field["name"] for field in _forms_by_name()["memoria-project-start"]["fields"]}
    assert fields == {"title", "scope_topics", "output_mode", "provisional_thesis"}
