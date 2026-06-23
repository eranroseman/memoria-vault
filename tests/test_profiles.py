"""The five shipped agents (ADR-48): structure, wiring, and ceiling consistency."""

import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
PROFILES = SRC / ".memoria" / "profiles"
LANES = SRC / ".memoria" / "lane-overrides"

EXPECTED = {
    "memoria-copi",
    "memoria-librarian",
    "memoria-writer",
    "memoria-peer-reviewer",
    "memoria-engineer",
}
RETIRED = {
    "memoria-mapper",
    "memoria-socratic",
    "memoria-verifier",
    "memoria-coder",
    "memoria-linter",
}
PROD_MODELS = {
    "memoria-copi": "~anthropic/claude-opus-latest",
    "memoria-peer-reviewer": "~anthropic/claude-opus-latest",
    "memoria-writer": "~anthropic/claude-sonnet-latest",
    "memoria-librarian": "~anthropic/claude-haiku-latest",
    "memoria-engineer": "~anthropic/claude-haiku-latest",
}
PLATFORM_KEYS = {
    "cli",
    "cron",
    "api_server",
    "telegram",
    "discord",
    "slack",
    "whatsapp",
    "whatsapp_cloud",
    "signal",
    "bluebubbles",
    "email",
    "homeassistant",
    "mattermost",
    "matrix",
    "dingtalk",
    "feishu",
    "wecom",
    "wecom_callback",
    "qqbot",
    "yuanbao",
    "teams",
    "google_chat",
}
DIRECT_WORLD_TOOLSETS = {"file", "terminal", "code_execution", "browser", "web", "computer_use"}


def test_exactly_the_five_agents_ship():
    names = {p.name for p in PROFILES.iterdir() if p.is_dir()}
    assert names == EXPECTED
    assert not (names & RETIRED)


def test_profile_structure_complete():
    for name in EXPECTED:
        d = PROFILES / name
        for f in ("SOUL.md", "config.yaml", "distribution.yaml"):
            assert (d / f).is_file(), f"{name} missing {f}"
        assert (d / ".no-bundled-skills").is_file(), f"{name} allows bundled skill seeding"
        dist = yaml.safe_load((d / "distribution.yaml").read_text(encoding="utf-8"))
        assert dist["name"] == name
        assert dist["version"] == "0.1.0-alpha.10"
        assert dist["hermes_requires"] == ">=0.17.0"


def test_configs_parse_and_reference_real_servers():
    for name in EXPECTED:
        cfg = yaml.safe_load((PROFILES / name / "config.yaml").read_text(encoding="utf-8"))
        for server, spec in (cfg.get("mcp_servers") or {}).items():
            args = spec.get("args") or []
            for a in args:
                if a.endswith(".py"):
                    rel = a.replace("{{VAULT_PATH}}/", "")
                    assert (SRC / rel).is_file(), f"{name}: {server} references missing {rel}"


def test_obsidian_mcp_uses_verified_https():
    """ADR-31/#527: vault MCP bearer traffic stays on verified loopback HTTPS."""
    for name in EXPECTED:
        cfg = yaml.safe_load((PROFILES / name / "config.yaml").read_text(encoding="utf-8"))
        obsidian = cfg["mcp_servers"]["obsidian"]
        assert obsidian["url"] == "https://127.0.0.1:${OBSIDIAN_MCP_PORT}/mcp"
        assert obsidian["ssl_verify"] == "${OBSIDIAN_MCP_SSL_VERIFY}"

        dist = yaml.safe_load((PROFILES / name / "distribution.yaml").read_text(encoding="utf-8"))
        env_names = {item["name"] for item in dist["env_requires"]}
        assert "OBSIDIAN_MCP_SSL_VERIFY" in env_names


def test_installer_generated_profile_configs_keep_verified_https():
    """WS-1/#620: placeholder substitution must not degrade Obsidian MCP TLS."""
    replacements = {
        "{{PYTHON}}": "/tmp/Memoria-test/.memoria/.venv/bin/python",
        "{{VAULT_PATH}}": "/tmp/Memoria-test",
        "{{QMD}}": "qmd",
        "{{PROFILE}}": "memoria-test",
        "{{MODEL_PROVIDER}}": "kilocode",
        "{{MODEL_BASE_URL}}": "https://api.kilo.ai/api/gateway",
        "{{MODEL_DEFAULT}}": "~anthropic/claude-haiku-latest",
    }
    for name in EXPECTED:
        text = (PROFILES / name / "config.yaml").read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = text.replace("  # {{MODEL_LOCAL_CONTEXT}}\n", "")
        cfg = yaml.safe_load(text)
        obsidian = cfg["mcp_servers"]["obsidian"]
        assert obsidian["url"] == "https://127.0.0.1:${OBSIDIAN_MCP_PORT}/mcp"
        assert obsidian["ssl_verify"] == "${OBSIDIAN_MCP_SSL_VERIFY}"


def _render_profile_config(name: str, *, env: str) -> dict:
    text = (PROFILES / name / "config.yaml").read_text(encoding="utf-8")
    common = {
        "{{PYTHON}}": "/tmp/Memoria-test/.memoria/.venv/bin/python",
        "{{VAULT_PATH}}": "/tmp/Memoria-test",
        "{{QMD}}": "qmd",
        "{{PROFILE}}": name,
    }
    if env == "prod":
        model = {
            "{{MODEL_PROVIDER}}": "kilocode",
            "{{MODEL_BASE_URL}}": "https://api.kilo.ai/api/gateway",
            "{{MODEL_DEFAULT}}": PROD_MODELS[name],
        }
        context = ""
    elif env == "test":
        model = {
            "{{MODEL_PROVIDER}}": "custom",
            "{{MODEL_BASE_URL}}": "http://127.0.0.1:11434/v1",
            "{{MODEL_DEFAULT}}": "qwen2.5:7b",
        }
        context = "  context_length: 65536\n  ollama_num_ctx: 65536\n"
    else:
        raise AssertionError(env)

    for old, new in (common | model).items():
        text = text.replace(old, new)
    text = text.replace("  # {{MODEL_LOCAL_CONTEXT}}\n", context)
    return yaml.safe_load(text)


def test_prod_model_overlay_preserves_shipped_profile_tiers():
    for name in EXPECTED:
        model = _render_profile_config(name, env="prod")["model"]
        assert model == {
            "provider": "kilocode",
            "base_url": "https://api.kilo.ai/api/gateway",
            "default": PROD_MODELS[name],
        }


def test_test_model_overlay_wires_profiles_to_local_ollama():
    for name in EXPECTED:
        model = _render_profile_config(name, env="test")["model"]
        assert model == {
            "provider": "custom",
            "base_url": "http://127.0.0.1:11434/v1",
            "default": "qwen2.5:7b",
            "context_length": 65536,
            "ollama_num_ctx": 65536,
        }


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
    assert "memory" in set(cfg["platform_toolsets"]["cli"])
    assert cfg["memory"]["memory_enabled"] is True
    assert cfg["memory"]["user_profile_enabled"] is True
    assert cfg["memory"]["write_approval"] is True
    assert "tasks" in cfg["mcp_servers"], "the Co-PI needs the delegation path"
    assert "paper_search" not in cfg["mcp_servers"], "the Co-PI delegates discovery"


def test_specialists_keep_memory_disabled():
    """D46: specialist postures are fixed; the learning loop is Co-PI-only."""
    for name in EXPECTED - {"memoria-copi"}:
        cfg = yaml.safe_load((PROFILES / name / "config.yaml").read_text(encoding="utf-8"))
        assert "memory" in cfg["agent"]["disabled_toolsets"], f"{name} must not carry memory"
        assert "memory" not in set(cfg["platform_toolsets"]["cli"])
        assert cfg["memory"]["memory_enabled"] is False
        assert cfg["memory"]["user_profile_enabled"] is False


def _registry() -> dict:
    return yaml.safe_load((SRC / ".memoria/tool-registry.yaml").read_text(encoding="utf-8"))


def _expected_toolsets(profile: str) -> set[str]:
    registry = _registry()
    groups = registry["groups"]
    allow = registry["profiles"][profile]["allow"]
    out = set()
    for entry in allow:
        for tool in groups.get(entry, [entry]):
            out.add(tool.split(".", 1)[0] if "." in tool else tool)
    return out


def _expected_mcp_tools(profile: str) -> dict[str, set[str]]:
    registry = _registry()
    groups = registry["groups"]
    allow = registry["profiles"][profile]["allow"]
    out: dict[str, set[str]] = {}
    for entry in allow:
        for tool in groups.get(entry, [entry]):
            if "." not in tool:
                continue
            server, name = tool.split(".", 1)
            out.setdefault(server, set()).add(name)
    return out


def test_platform_toolsets_match_registry_allowlist():
    for name in EXPECTED:
        cfg = yaml.safe_load((PROFILES / name / "config.yaml").read_text(encoding="utf-8"))
        expected = _expected_toolsets(name)
        assert set(cfg["platform_toolsets"]) == PLATFORM_KEYS
        for platform, toolsets in cfg["platform_toolsets"].items():
            assert set(toolsets) == expected, f"{name}/{platform}"
        assert DIRECT_WORLD_TOOLSETS.isdisjoint(expected)
        assert cfg["tools"]["tool_search"]["enabled"] == "auto"
        assert cfg["agent"]["tool_use_enforcement"] is True


def test_mcp_tool_filters_match_registry_allowlist():
    for name in EXPECTED:
        cfg = yaml.safe_load((PROFILES / name / "config.yaml").read_text(encoding="utf-8"))
        expected = _expected_mcp_tools(name)
        for server, tools in expected.items():
            if server == "obsidian":
                continue
            actual = set(cfg["mcp_servers"][server]["tools"]["include"])
            assert actual == tools, f"{name}/{server}"


def test_profile_configs_are_materialized_from_registry():
    subprocess.run(["python", "scripts/render_profile_configs.py", "--check"], cwd=ROOT, check=True)


def test_worker_skills_and_curator_are_locked_down():
    for name in EXPECTED:
        cfg = yaml.safe_load((PROFILES / name / "config.yaml").read_text(encoding="utf-8"))
        assert cfg["skills"]["write_approval"] is True
        assert cfg["skills"]["guard_agent_created"] is True
        assert cfg["curator"]["enabled"] is False


def test_lane_scopes_avoid_gated_zones():
    """No lane's write_scope may sit inside a review-gated prefix (ADR-03/47)."""
    from operations.lib import schema

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
    assert "notes/sources/" in memoria["write_scope"]
    assert "source" in memoria["outputs"]


def test_acp_pane_is_copi_only():
    import json

    data = json.loads(
        (SRC / ".obsidian/plugins/agent-client/data.json.example").read_text(encoding="utf-8")
    )
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
    for cfg in sorted(PROFILES.glob("*/config.yaml")):
        data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        disabled = set((data.get("agent") or {}).get("disabled_toolsets") or [])
        missing = DIRECT_WORLD_TOOLSETS - disabled
        assert not missing, (
            f"{cfg.parent.name}: direct-access toolsets not disabled: {sorted(missing)}"
        )
        for platform, toolsets in data["platform_toolsets"].items():
            leaked = DIRECT_WORLD_TOOLSETS & set(toolsets)
            assert not leaked, f"{cfg.parent.name}/{platform}: direct toolsets enabled: {leaked}"


def test_profiles_do_not_ship_inert_checkpoints():
    """Hermes checkpoints do not snapshot MCP writes; dead safety config must stay absent."""
    for cfg in sorted(PROFILES.glob("*/config.yaml")):
        data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        assert "checkpoints" not in data, f"{cfg.parent.name}: inert checkpoints config shipped"


def test_every_profile_enables_policy_gate_plugin():
    for cfg in sorted(PROFILES.glob("*/config.yaml")):
        data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        enabled = (data.get("plugins") or {}).get("enabled") or []
        assert enabled == ["memoria-policy-gate"], f"{cfg.parent.name}: policy gate not enabled"
