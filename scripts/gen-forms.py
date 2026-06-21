#!/usr/bin/env python3
"""Generate Modal Forms config from Memoria schemas and vocabulary."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCHEMA_DIR = SRC / ".memoria" / "schemas" / "types"
VOCABULARY = SRC / "system" / "vocabulary.md"


def _schema(name: str) -> dict:
    return yaml.safe_load((SCHEMA_DIR / f"{name}.yaml").read_text(encoding="utf-8"))


def _terms(section: str) -> list[str]:
    text = VOCABULARY.read_text(encoding="utf-8")
    match = re.search(rf"^## {re.escape(section)}\n(?P<body>.*?)(?=^## |\Z)", text, re.S | re.M)
    if not match:
        raise SystemExit(f"{section} section missing from {VOCABULARY}")
    return re.findall(r"^- ([a-z0-9-]+) — ", match.group("body"), re.M)


def _fixed_select(values: list[str]) -> dict:
    return {
        "type": "select",
        "source": "fixed",
        "options": [{"label": value.replace("-", " ").title(), "value": value} for value in values],
    }


def _radio(values: list[str]) -> dict:
    return {
        "type": "select",
        "source": "fixed",
        "options": [{"label": value.replace("-", " ").title(), "value": value} for value in values],
    }


def _fixed_multi(values: list[str]) -> dict:
    return {"type": "multiselect", "source": "fixed", "multi_select_options": values}


def _notes(folder: str) -> dict:
    return {"type": "note", "folder": folder}


def _note_multi(folder: str, *, folders: list[str] | None = None) -> dict:
    data = {"type": "multiselect", "source": "notes", "folder": folder}
    if folders:
        data["folders"] = folders
    return data


def _field(
    name: str,
    label: str,
    input_def: dict,
    *,
    description: str = "",
    required: bool = False,
) -> dict:
    data = {"name": name, "label": label}
    if description:
        data["description"] = description
    if required:
        data["isRequired"] = True
    data["input"] = input_def
    return data


def _form(title: str, name: str, fields: list[dict]) -> dict:
    return {"title": title, "name": name, "version": "1", "fields": fields}


def generate() -> dict:
    source = _schema("source")
    claim = _schema("claim")
    project = _schema("project")

    research_area = _terms("research_area")
    methodology = _terms("methodology")
    topics = _terms("topics") or research_area

    return {
        "editorPosition": "right",
        "attachShortcutToGlobalWindow": False,
        "globalNamespace": "MF",
        "formDefinitions": [
            _form(
                "Memoria fleeting capture",
                "memoria-fleeting-capture",
                [
                    _field("title", "Title", {"type": "text"}, description="Optional short title."),
                    _field(
                        "body",
                        "Thought, quote, or idea",
                        {"type": "textarea"},
                        description=(
                            "One raw item per note. Capture first; distill or archive from "
                            "the Inbox later."
                        ),
                        required=True,
                    ),
                ],
            ),
            _form(
                "Memoria source capture",
                "memoria-source-capture",
                [
                    _field("title", "Source title", {"type": "text"}, required=True),
                    _field("entity", "Catalog entity", _notes("catalog"), required=True),
                    _field(
                        "source_type",
                        "Source type",
                        _fixed_select(["paper", "dataset", "repository", "web-page", "report"]),
                        required=True,
                    ),
                    _field(
                        "evidence_level",
                        "Evidence level",
                        _fixed_select(source["enums"]["evidence_level"]),
                    ),
                    _field("research_area", "Research area", _fixed_multi(research_area)),
                    _field("methodology", "Methodology", _fixed_multi(methodology)),
                    _field("summary", "In my words", {"type": "textarea"}),
                ],
            ),
            _form(
                "Memoria claim capture",
                "memoria-claim-capture",
                [
                    _field(
                        "title",
                        "Claim title",
                        {"type": "text"},
                        description="Short label for the note and Base row.",
                        required=True,
                    ),
                    _field(
                        "maturity",
                        "Maturity",
                        _radio(claim["enums"]["maturity"]),
                        description="Start at seedling unless the claim is already well supported.",
                        required=True,
                    ),
                    _field(
                        "sources",
                        "Sources",
                        _note_multi("catalog/papers"),
                        description="Pick the catalog paper(s) whose citekeys support this claim.",
                        required=True,
                    ),
                    _field(
                        "topics",
                        "Topics",
                        _fixed_multi(topics),
                        description="Optional vocabulary tags for retrieval and hub thresholds.",
                    ),
                    _field(
                        "claim",
                        "Claim statement",
                        {"type": "textarea"},
                        description="One durable, source-grounded assertion in your own words.",
                        required=True,
                    ),
                ],
            ),
            _form(
                "Memoria hub capture",
                "memoria-hub-capture",
                [
                    _field("title", "Hub title", {"type": "text"}, required=True),
                    _field("topic", "Topic", _fixed_select(topics), required=True),
                    _field("members", "Member claims", _note_multi("notes/claims")),
                    _field("body", "Shape of the topic", {"type": "textarea"}),
                ],
            ),
            _form(
                "Memoria project start",
                "memoria-project-start",
                [
                    _field("title", "Project title", {"type": "text"}, required=True),
                    _field("slug", "Project slug", {"type": "text"}, required=True),
                    _field(
                        "scope_topics", "Scope topics", _fixed_multi(research_area), required=True
                    ),
                    _field("inquiry_population", "Population", {"type": "text"}, required=True),
                    _field("inquiry_intervention", "Intervention", {"type": "text"}),
                    _field("inquiry_comparison", "Comparison", {"type": "text"}),
                    _field("inquiry_outcome", "Outcome", {"type": "text"}, required=True),
                    _field("finer_feasible", "Feasible", {"type": "textarea"}),
                    _field("finer_novel", "Novel", {"type": "textarea"}),
                    _field("finer_relevant", "Relevant", {"type": "textarea"}),
                    _field(
                        "output_mode",
                        "Output mode",
                        _radio(project["enums"]["output_mode"]),
                        required=True,
                    ),
                ],
            ),
            _form(
                "Memoria thesis capture",
                "memoria-thesis-capture",
                [
                    _field("title", "Thesis", {"type": "textarea"}, required=True),
                    _field("project", "Project", _notes("projects"), required=True),
                    _field("sources", "Sources", _note_multi("catalog/papers"), required=True),
                ],
            ),
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="exit non-zero if data.json drifts")
    parser.add_argument("--write", action="store_true", help="write generated data.json")
    parser.add_argument(
        "--output",
        type=Path,
        default=SRC / ".obsidian" / "plugins" / "modalforms" / "data.json",
    )
    args = parser.parse_args()

    rendered = json.dumps(generate(), indent=2) + "\n"
    if args.check:
        current = args.output.read_text(encoding="utf-8")
        if current != rendered:
            raise SystemExit(f"{args.output} is out of date; run scripts/gen-forms.py --write")
        return 0
    if args.write:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
