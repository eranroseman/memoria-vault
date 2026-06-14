"""The five shipped agents (ADR-48): structure, wiring, and ceiling consistency."""

from pathlib import Path

import yaml

SRC = Path(__file__).resolve().parent.parent / "src"
PROFILES = SRC / ".memoria" / "profiles"
LANES = SRC / ".memoria" / "lane-overrides"

EXPECTED = {"memoria-copi", "memoria-librarian", "memoria-writer",
            "memoria-peer-reviewer", "memoria-engineer"}
RETIRED = {"memoria-mapper", "memoria-socratic", "memoria-verifier",
           "memoria-coder", "memoria-linter"}


def test_exactly_the_five_agents_ship():
    names = {p.name for p in PROFILES.iterdir() if p.is_dir()}
    assert names == EXPECTED
    assert not (names & RETIRED)


def test_profile_structure_complete():
    for name in EXPECTED:
        d = PROFILES / name
        for f in ("SOUL.md", "config.yaml", "distribution.yaml"):
            assert (d / f).is_file(), f"{name} missing {f}"
        dist = yaml.safe_load((d / "distribution.yaml").read_text(encoding="utf-8"))
        assert dist["name"] == name
        assert dist["version"] == "0.1.0-alpha.2"


def test_configs_parse_and_reference_real_servers():
    for name in EXPECTED:
        cfg = yaml.safe_load((PROFILES / name / "config.yaml").read_text(encoding="utf-8"))
        for server, spec in (cfg.get("mcp_servers") or {}).items():
            args = spec.get("args") or []
            for a in args:
                if a.endswith(".py"):
                    rel = a.replace("{{VAULT_PATH}}/", "")
                    assert (SRC / rel).is_file(), f"{name}: {server} references missing {rel}"


def test_every_agent_has_a_lane_override():
    for name in EXPECTED:
        short = name.removeprefix("memoria-")
        assert (LANES / f"{short}.yaml").is_file(), f"no lane-override for {name}"
    lane_files = {p.stem for p in LANES.glob("*.yaml")}
    assert lane_files == {n.removeprefix("memoria-") for n in EXPECTED}


def test_copi_is_hard_read_only():
    """ADR-48: the Co-PI delegates every write — empty write scope, denied everywhere."""
    lane = yaml.safe_load((LANES / "copi.yaml").read_text(encoding="utf-8"))
    assert lane["policy"]["allow"]["write"] == []
    assert lane["routing"]["write_scope"] == []
    assert lane["routing"]["invocation"] == "interactive_only"
    cfg = yaml.safe_load((PROFILES / "memoria-copi" / "config.yaml").read_text(encoding="utf-8"))
    # the Co-PI alone keeps the memory toolset (D46)
    assert "memory" not in cfg["agent"]["disabled_toolsets"]
    assert "tasks" in cfg["mcp_servers"], "the Co-PI needs the delegation path"


def test_specialists_keep_memory_disabled():
    """D46: specialist postures are fixed; the learning loop is Co-PI-only."""
    for name in EXPECTED - {"memoria-copi"}:
        cfg = yaml.safe_load((PROFILES / name / "config.yaml").read_text(encoding="utf-8"))
        assert "memory" in cfg["agent"]["disabled_toolsets"], f"{name} must not carry memory"


def test_lane_scopes_avoid_gated_zones():
    """No lane's write_scope may sit inside a review-gated prefix (ADR-03/47)."""
    import schema

    gated = tuple(schema.gated_prefixes(schema.load_folders()))
    for f in LANES.glob("*.yaml"):
        lane = yaml.safe_load(f.read_text(encoding="utf-8"))
        for scope in (lane.get("routing") or {}).get("write_scope") or []:
            assert not scope.startswith(gated), f"{f.name}: scope {scope} is review-gated"


def test_peer_reviewer_writes_only_inbox():
    lane = yaml.safe_load((LANES / "peer-reviewer.yaml").read_text(encoding="utf-8"))
    assert lane["routing"]["write_scope"] == ["inbox/"]


def _skill_frontmatter(profile: str, skill: str) -> dict:
    text = (PROFILES / profile / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    return yaml.safe_load(text.split("---", 2)[1])


def test_catalog_enrich_record_creates_proposed_source_notes():
    fm = _skill_frontmatter("memoria-librarian", "catalog-enrich-record")
    memoria = fm["metadata"]["memoria"]
    assert "notes/source/" in memoria["write_scope"]
    assert "source" in memoria["outputs"]


def test_acp_pane_is_copi_only():
    import json

    data = json.loads((SRC / ".obsidian/plugins/agent-client/data.json.example")
                      .read_text(encoding="utf-8"))
    agents = data["customAgents"]
    assert [a["id"] for a in agents] == ["memoria-copi"]
    assert agents[0]["displayName"] == "Memoria Co-PI"
    assert data["defaultAgentId"] == "memoria-copi"
    exports = data["exportSettings"]
    assert exports["defaultFolder"] == "system/exports"
    assert exports["autoExportOnNewChat"] is True
    assert exports["autoExportOnCloseChat"] is True
    assert exports["openFileAfterExport"] is False
    assert exports["imageCustomFolder"] == "system/exports/assets"


def test_no_profile_has_direct_world_access():
    """D40/ADR-46: agents reach the vault, engines, and APIs ONLY through MCP.
    Every profile must disable the direct-capability toolsets — no exceptions."""
    import yaml
    forbidden = {"file", "terminal", "code_execution", "browser", "web", "computer_use"}
    for cfg in sorted(PROFILES.glob("*/config.yaml")):
        data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        disabled = set((data.get("agent") or {}).get("disabled_toolsets") or [])
        missing = forbidden - disabled
        assert not missing, f"{cfg.parent.name}: direct-access toolsets not disabled: {sorted(missing)}"
