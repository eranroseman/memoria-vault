"""Tests for the repository's agent-guidance drift guard."""

from scripts.checks import agents_doctor


def test_agent_guidance_is_valid_and_generated_files_are_current():
    assert agents_doctor.check() == []


def test_change_impact_registry_has_paths_and_checks():
    data = agents_doctor.yaml.safe_load(agents_doctor.IMPACT_SOURCE.read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert all(row["paths"] and row["checks"] for row in data["areas"])


def test_change_impact_registry_rejects_duplicate_items():
    data = {
        "version": 1,
        "areas": [
            {
                "area": "Testing",
                "paths": ["scripts/verify", "scripts/verify"],
                "inspect": ["Checks"],
                "checks": ["python3 scripts/verify"],
            }
        ],
    }

    assert (
        "change-impact.yaml: Testing paths contains duplicate scripts/verify"
        in agents_doctor._impact_errors(data)
    )


def test_change_impact_registry_rejects_malformed_shape():
    errors = agents_doctor._impact_errors({"version": 1, "areas": []})

    assert "change-impact.yaml: must contain a non-empty areas list" in errors


def test_required_ci_checks_are_parsed_from_agents_table():
    text = """## Required CI checks

| Check | Validates |
|---|---|
| `lint` | Fast checks |
| `python-selftest` | Tests |

---
"""
    assert agents_doctor._required_ci_checks_from_agents(text) == ["lint", "python-selftest"]


def test_agents_required_ci_table_matches_ruleset_contract():
    assert agents_doctor._required_ci_errors() == []


def test_agent_guidance_consistency_literals_are_current():
    assert agents_doctor._guidance_consistency_errors() == []


def test_toolkit_parity_table_is_current():
    assert agents_doctor._toolkit_parity_errors() == []


def test_toolkit_parity_table_requires_fallback_and_check():
    text = """## Tooling Parity

| Task | Claude path | Codex path | Shared fallback | Required check |
|---|---|---|---|---|
| Skill routing | Claude | Codex | n/a | `python3 scripts/checks/agents_doctor.py` |
"""

    errors = agents_doctor._toolkit_parity_errors(text)

    assert ".agents/toolkit.md: Skill routing missing Shared fallback" in errors
    assert ".agents/toolkit.md: tooling parity table missing PR review" in errors


def test_optional_agent_client_docs_are_link_checked(tmp_path, monkeypatch):
    root = tmp_path
    (root / ".agents" / "system").mkdir(parents=True)
    (root / ".agents" / "skills").mkdir(parents=True)
    (root / ".claude").mkdir()
    (root / ".claude" / "guide.md").write_text("[missing](missing.md)\n", encoding="utf-8")

    monkeypatch.setattr(agents_doctor, "ROOT", root)
    monkeypatch.setattr(agents_doctor, "AGENTS", root / ".agents")
    errs = agents_doctor._local_link_errors()
    assert any(".claude/guide.md: broken link missing.md" in e for e in errs)
