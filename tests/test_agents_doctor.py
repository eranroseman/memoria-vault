"""Tests for the repository's agent-guidance drift guard."""

import agents_doctor


def test_agent_guidance_is_valid_and_generated_files_are_current():
    assert agents_doctor.check() == []


def test_docs_manifest_routes_model_and_runtime_surfaces():
    manifest = agents_doctor.yaml.safe_load(agents_doctor._render_docs_manifest())
    entries = {entry["path"]: entry for entry in manifest["entries"]}

    assert entries["AGENTS.md"]["book"] == "Reference"
    assert entries["docs/developers.md"]["book"] == "Developers"
    assert entries["docs/adr/README.md"]["book"] == "Developers"
    assert entries["docs/design/README.md"]["book"] == "Developers"
    assert entries["docs/explanation/README.md"]["book"] == "Explanation"
    assert entries["docs/reference/README.md"]["book"] == "Reference"
    assert entries["docs/README.md"]["book"] == "Model spine"
    assert entries["docs/README.md"]["canonical_owner"] is True


def test_change_impact_registry_has_paths_and_checks():
    data = agents_doctor.yaml.safe_load(agents_doctor.IMPACT_SOURCE.read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert all(row["paths"] and row["checks"] for row in data["areas"])


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
