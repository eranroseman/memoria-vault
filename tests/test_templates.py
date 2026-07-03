"""Alpha.15 templates begin schema-valid for PI-created Concept types."""

import re
from pathlib import Path

import yaml

from memoria_vault.runtime.subsystems.lib import schema

TEMPLATES = Path(__file__).resolve().parent.parent / "vault-template" / "system" / "templates"

_PLACEHOLDER = re.compile(r"\{\{[^}]*\}\}")
PI_CREATED_TYPES = {"note", "hub", "project"}
VALID_ULID = "01KBN6V6KX0000000000000001"


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path.name}: no frontmatter block"
    text = _PLACEHOLDER.sub("PLACEHOLDER", m.group(1))
    text = text.replace('id: "PLACEHOLDER"', f"id: {VALID_ULID}")
    text = text.replace("id: PLACEHOLDER", f"id: {VALID_ULID}")
    return yaml.safe_load(text)


def _frontmatter_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path.name}: no frontmatter block"
    return m.group(1)


def test_alpha15_templates_are_only_pi_created_types():
    names = {p.stem for p in TEMPLATES.glob("*.md")}
    assert names == PI_CREATED_TYPES


def test_templates_conform_to_schemas():
    types = schema.load_types()
    for tpl in sorted(TEMPLATES.glob("*.md")):
        sc = types[tpl.stem]
        fm = _frontmatter(tpl)
        assert schema.validate_frontmatter(fm, sc) == []


def test_templates_surface_meaning_fields_first():
    for tpl in sorted(TEMPLATES.glob("*.md")):
        keys = [
            line.split(":", 1)[0]
            for line in _frontmatter_text(tpl).splitlines()
            if line and not line.startswith(" ")
        ]
        assert "check_status" not in keys, tpl.name
        assert "standing" not in keys, tpl.name
        assert keys[:3] == ["title", "type", "id"], tpl.name


def test_templates_have_a_body_heading():
    for tpl in sorted(TEMPLATES.glob("*.md")):
        body = tpl.read_text(encoding="utf-8").split("---\n", 2)[2]
        assert body.startswith("# {{VALUE:"), tpl.name
