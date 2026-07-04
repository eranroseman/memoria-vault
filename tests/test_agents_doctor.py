"""Tests for the repository's agent-guidance drift guard."""

import agents_doctor


def test_agent_guidance_is_valid_and_generated_files_are_current():
    assert agents_doctor.check() == []


def test_generated_agent_references_are_limited_to_guidance_mirrors():
    generated = {
        path.relative_to(agents_doctor.ROOT).as_posix() for path in agents_doctor.generated_files()
    }

    assert generated == {
        ".agents/system/change-impact-map.md",
    }


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


def test_agents_md_is_link_checked(tmp_path, monkeypatch):
    root = tmp_path
    root.joinpath("AGENTS.md").write_text("[missing](missing.md)\n", encoding="utf-8")

    monkeypatch.setattr(agents_doctor, "ROOT", root)
    errs = agents_doctor._local_link_errors()

    assert "AGENTS.md: broken link missing.md" in errs


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


def test_source_of_truth_map_backticked_paths_are_valid():
    assert agents_doctor._source_map_path_errors() == []


def test_source_of_truth_map_missing_backticked_path_fails():
    errs = agents_doctor._source_map_path_errors("Owner is `scripts/no-such-file.py`.\n")

    assert errs == [".agents/system/source-of-truth-map.md: missing path `scripts/no-such-file.py`"]


def test_agents_pr_policy_mirror_matches_policy_constants():
    assert agents_doctor._pr_policy_errors() == []


def test_agents_pr_policy_trusted_author_drift_fails():
    text = (agents_doctor.ROOT / "AGENTS.md").read_text(encoding="utf-8")
    bad = text.replace("`dependabot[bot]`", "`not-a-bot[bot]`")

    assert any("trusted authors drift" in err for err in agents_doctor._pr_policy_errors(bad))


def test_verify_change_gate_roster_matches_verify_script():
    assert agents_doctor._verify_change_errors() == []


def test_verify_change_gate_roster_drift_fails():
    text = (agents_doctor.AGENTS / "playbooks/verify-change.md").read_text(encoding="utf-8")
    bad = text.replace("| Live |", "| Live runtime |")

    assert any("gate rows drift" in err for err in agents_doctor._verify_change_errors(bad))


def test_verify_change_mode_roster_drift_fails():
    text = (agents_doctor.AGENTS / "playbooks/verify-change.md").read_text(encoding="utf-8")
    bad = text.replace("`scripts/verify live`", "`scripts/verify live-missing`")

    assert any("mode: live" in err for err in agents_doctor._verify_change_errors(bad))


def test_agents_enforcement_tags_name_existing_mechanisms():
    assert agents_doctor._agent_tag_errors() == []


def test_agents_enforcement_tag_missing_mechanism_fails():
    text = "Bad rule. *(enforced: no-such-hook)*\n"

    assert agents_doctor._agent_tag_errors(text) == [
        "AGENTS.md enforcement tag names missing mechanism: no-such-hook"
    ]
