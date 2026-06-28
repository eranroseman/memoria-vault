"""Every shipped template conforms to its type schema (ADR-49/50/51).

Templates carry QuickAdd placeholders ({{VALUE:...}}, {{DATE:...}}), so the check
is structural: the type literal is right, every required schema field is present
as a key, and enum-kind fields default to a *valid* enum value — a note created
from a template starts schema-valid.
"""

import re
from pathlib import Path

import yaml
from operations.lib import schema

TEMPLATES = Path(__file__).resolve().parent.parent / "vault-template" / "system" / "templates"

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
    # patterns (ADR-53), eval gold tasks (ADR-11), space dashboards, the inbox
    # queue and maintenance dashboards, and worker-card projections are not template-created;
    # their writers create the instances directly.
    expected = set(types) - {
        "pattern",
        "eval-task",
        "space",
        "queue",
        "maintenance",
        "worker-card",
    }
    assert names == expected, f"templates {names ^ expected} out of sync with schemas"


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
                    f"{tpl.name}: {field}={fm[field]!r} not a valid default {allowed}"
                )


def test_fleeting_template_keeps_origin_comment_out_of_yaml():
    """Obsidian Bases failed to index later keys when this carried an inline comment."""
    fm = _frontmatter_text(TEMPLATES / "fleeting.md")
    assert "origin: human\n" in f"{fm}\n"
    assert "origin: human #" not in fm


def test_fleeting_template_carries_triage_options_callout():
    body = (TEMPLATES / "fleeting.md").read_text(encoding="utf-8")
    assert "> [!suggestions] Triage options" in body
    assert "Promote to a claim" in body
    assert "Attach to an existing source, claim, hub, or project" in body
    assert "Capture or delegate a source chase" in body
    assert "Archive or delete it once the action is done" in body
    for command in (
        "QuickAdd: Memoria: write claim note",
        "QuickAdd: Memoria: capture source from URL",
        "QuickAdd: Memoria: delegate task",
        "QuickAdd: Memoria: archive fleeting note",
    ):
        assert f"action {command}" in body
    assert body.count("type command") == 4
    assert "type template" not in body
    assert "type text" not in body
    assert "type calculate" not in body


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


def test_claim_template_carries_action_buttons():
    body = (TEMPLATES / "claim.md").read_text(encoding="utf-8")
    assert "> [!suggestions] Claim actions" in body
    assert "Link this claim to nearby claims and sources" in body
    assert "Capture another source" in body
    assert "Delegate follow-up work" in body
    assert "Archive the claim" in body
    for command in (
        "QuickAdd: Memoria: link claim",
        "QuickAdd: Memoria: capture source from URL",
        "QuickAdd: Memoria: delegate task",
        "QuickAdd: Memoria: archive claim note",
    ):
        assert f"action {command}" in body
    assert body.count("type command") == 4
    assert "type template" not in body
    assert "type text" not in body
    assert "type calculate" not in body


def test_templates_surface_identity_type_lifecycle_first():
    """Properties pane scan order: identity first, then type/lifecycle (#145)."""
    for tpl in sorted(TEMPLATES.glob("*.md")):
        keys = [
            line.split(":", 1)[0]
            for line in _frontmatter_text(tpl).splitlines()
            if line and not line.startswith(" ")
        ]
        assert "type" in keys and "lifecycle" in keys, tpl.name
        identity = "title" if "title" in keys else "name"
        assert keys[:3] == [identity, "type", "lifecycle"], tpl.name
        if tpl.name == "claim.md":
            assert keys[:4] == ["title", "type", "lifecycle", "maturity"]
        if tpl.name == "fleeting.md":
            assert keys[:4] == ["title", "type", "lifecycle", "origin"]


def test_project_templates_start_in_schema_valid_states():
    project = _frontmatter(TEMPLATES / "project.md")
    thesis = _frontmatter(TEMPLATES / "thesis.md")
    project_body = (TEMPLATES / "project.md").read_text(encoding="utf-8")

    assert project["lifecycle"] == "current"
    assert project["output_mode"] == "thesis"
    assert project["question_version"] == 1
    assert set(project["finer"]) == {"feasible", "interesting", "novel", "ethical", "relevant"}
    assert "# {{VALUE:project question}}" in project_body
    assert "Project · thesis mode" in project_body
    assert "[[project-gate-index|Readiness details]]" in project_body
    assert "name Map corpus" in project_body
    assert "QuickAdd: Memoria: map corpus" in project_body
    assert "name Refresh gate" in project_body
    assert "![[project-gate-index]]" not in project_body
    assert thesis["lifecycle"] == "proposed"
    assert thesis["project"] == "[[PLACEHOLDER]]"


def test_code_note_template_scaffolds_external_agent_handoff():
    fm = _frontmatter(TEMPLATES / "code-note.md")
    body = (TEMPLATES / "code-note.md").read_text(encoding="utf-8")

    assert fm["type"] == "code-note"
    assert fm["lifecycle"] == "proposed"
    assert fm["agent"] == "codex"
    assert fm["acceptance"] == []
    for heading in ("# Purpose", "# Handoff", "# Acceptance", "# Runbook"):
        assert heading in body
