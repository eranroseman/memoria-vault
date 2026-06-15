"""Every shipped template conforms to its type schema (ADR-49/50/51).

Templates carry QuickAdd placeholders ({{VALUE:...}}, {{DATE:...}}), so the check
is structural: the type literal is right, every required schema field is present
as a key, and enum-kind fields default to a *valid* enum value — a note created
from a template starts schema-valid.
"""

import re
from pathlib import Path

import schema
import yaml

TEMPLATES = Path(__file__).resolve().parent.parent / "src" / "system" / "templates"

_PLACEHOLDER = re.compile(r'"?\{\{[^}]*\}\}"?')


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path.name}: no frontmatter block"
    return yaml.safe_load(_PLACEHOLDER.sub("PLACEHOLDER", m.group(1)))


def _frontmatter_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path.name}: no frontmatter block"
    return m.group(1)


def test_one_template_per_type():
    types = schema.load_types()
    names = {p.stem for p in TEMPLATES.glob("*.md")}
    # patterns (ADR-53) and eval gold tasks (ADR-11) are not template-created —
    # the files in system/patterns/ and system/eval/ ARE the instances
    expected = set(types) - {"pattern", "eval-task"}
    assert names == expected, (
        f"templates {names ^ expected} out of sync with schemas")


def test_templates_conform_to_schemas():
    types = schema.load_types()
    for tpl in sorted(TEMPLATES.glob("*.md")):
        sc = types[tpl.stem]
        fm = _frontmatter(tpl)
        enums = sc.get("enums", {})
        # the type literal is exact
        assert fm.get("type") == tpl.stem, f"{tpl.name}: wrong type literal"
        for field, kind in (sc.get("required") or {}).items():
            assert field in fm, f"{tpl.name}: missing required key {field}"
            if kind.startswith("enum:"):
                allowed = enums[kind.split(":", 1)[1]]
                assert fm[field] in allowed, (
                    f"{tpl.name}: {field}={fm[field]!r} not a valid default {allowed}")


def test_fleeting_template_keeps_origin_comment_out_of_yaml():
    """Obsidian Bases failed to index later keys when this carried an inline comment."""
    fm = _frontmatter_text(TEMPLATES / "fleeting.md")
    assert "origin: human\n" in f"{fm}\n"
    assert "origin: human #" not in fm


def test_proposal_cards_carry_honesty_body():
    """Candidate/gap templates render the D49 honesty sections (ADR-51)."""
    for name in ("candidate", "gap"):
        body = (TEMPLATES / f"{name}.md").read_text(encoding="utf-8")
        for heading in ("# Action", "# For", "# Against", "# What tipped it"):
            assert heading in body, f"{name}.md missing section {heading}"


def test_verification_cards_lead_with_finding():
    for name in ("flag", "alert"):
        body = (TEMPLATES / f"{name}.md").read_text(encoding="utf-8")
        assert "# Finding" in body, f"{name}.md missing # Finding"


def test_source_template_exposes_linked_claim_button():
    body = (TEMPLATES / "source.md").read_text(encoding="utf-8")
    assert "action QuickAdd: Memoria: create linked claim note" in body
    assert body.index("```button") > body.index("# Worth distilling")
