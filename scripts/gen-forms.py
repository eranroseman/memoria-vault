#!/usr/bin/env python3
"""Generate the shipped Modal Forms config."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "vault-template"


def _field(
    name: str,
    label: str,
    input_def: dict,
    *,
    description: str = "",
    required: bool = False,
    condition: dict | None = None,
) -> dict:
    data = {"name": name, "label": label}
    if description:
        data["description"] = description
    if required:
        data["isRequired"] = True
    data["input"] = input_def
    if condition:
        data["condition"] = condition
    return data


def _form(title: str, name: str, fields: list[dict]) -> dict:
    return {"title": title, "name": name, "version": "1", "fields": fields}


def _note_capture_form() -> dict:
    return _form(
        "Memoria note capture",
        "memoria-note-capture",
        [
            _field("title", "Title", {"type": "text"}, description="Optional short title."),
            _field(
                "description",
                "Description",
                {"type": "text"},
                description="Optional short preview; defaults to the title.",
            ),
            _field(
                "body",
                "Note body",
                {"type": "textarea"},
                description="One unchecked note Concept. The worker/check loop owns promotion.",
                required=True,
            ),
        ],
    )


def generate() -> dict:
    return {
        "editorPosition": "right",
        "attachShortcutToGlobalWindow": False,
        "globalNamespace": "MF",
        "formDefinitions": [_note_capture_form()],
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
