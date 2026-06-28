import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import l2_obsidian_mcp_shim as shim
import l2_openai_smoke_server as smoke_server
import l2_smoke


def test_test_l2_help_documents_prereqs_and_non_pr_status():
    result = subprocess.run(
        ["bash", "scripts/test-l2.sh", "--help"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    assert "manual/nightly" in result.stdout
    assert "not a required PR CI gate" in result.stdout
    assert "hermes on PATH" in result.stdout
    assert "MEMORIA_L2_USE_SMOKE_MODEL=1" in result.stdout
    assert "MEMORIA_L2_MODEL_BASE_URL" in result.stdout


def test_obsidian_shim_rejects_paths_outside_vault(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()

    with pytest.raises(ValueError, match="inside the vault"):
        shim.put_content(vault, "../outside.md", "bad")
    with pytest.raises(ValueError, match="inside the vault"):
        shim.put_content(vault, str(tmp_path / "outside.md"), "bad")


def test_obsidian_shim_writes_and_reads_vault_relative_file(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()

    result = shim.put_content(vault, "projects/l2-smoke/live.md", "hello")

    assert result == {"path": "projects/l2-smoke/live.md", "status": "written"}
    assert shim.get_content(vault, "projects/l2-smoke/live.md") == "hello"


def test_l2_smoke_profile_uses_filesystem_obsidian_shim(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    profile_stage = tmp_path / "profile"

    l2_smoke.write_profile(
        ROOT / "vault-template/.memoria/profiles/memoria-writer",
        profile_stage,
        repo_root=ROOT,
        vault=vault,
        python=sys.executable,
        provider="custom",
        model="qwen2.5:7b",
        base_url="http://127.0.0.1:11434/v1",
        context_length=4096,
    )

    config = yaml.safe_load((profile_stage / "config.yaml").read_text(encoding="utf-8"))
    assert config["mcp_servers"]["obsidian"]["command"] == sys.executable
    assert config["mcp_servers"]["obsidian"]["args"] == [
        str(ROOT / "scripts/l2_obsidian_mcp_shim.py"),
        "--vault",
        str(vault),
    ]
    assert config["plugins"]["enabled"] == ["memoria-policy-gate"]
    assert set(config["platform_toolsets"]["cli"]) == {"skills", "obsidian"}
    assert config["agent"]["tool_use_enforcement"] is True
    assert "file" in config["agent"]["disabled_toolsets"]
    assert (profile_stage / "SOUL.md").is_file()


def test_l2_smoke_deploys_policy_plugin_with_repo_import_path(tmp_path):
    profile_dir = tmp_path / "profile"
    vault = tmp_path / "vault"
    vault.mkdir()

    l2_smoke.deploy_policy_plugin(ROOT, profile_dir, "memoria-writer", vault)

    plugin = (profile_dir / "plugins/memoria-policy-gate/__init__.py").read_text(encoding="utf-8")
    assert 'PROFILE = "memoria-writer"' in plugin
    assert f"sys.path.insert(0, {str(ROOT / 'src')!r})" in plugin


def test_l2_smoke_asserts_artifact_and_audit_row(tmp_path, capsys):
    vault = tmp_path / "vault"
    artifact = vault / "projects/l2-smoke/live-dispatch.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("---\ntype: project\nl2_live_smoke: true\n---\n", encoding="utf-8")
    audit = vault / "system/logs/audit.jsonl"
    audit.parent.mkdir(parents=True)
    audit.write_text(
        json.dumps({"path": "elsewhere.md", "decision": "allow_with_log"})
        + "\n"
        + json.dumps(
            {
                "path": "projects/l2-smoke/live-dispatch.md",
                "decision": "allow_with_log",
                "before_hash": "0" * 64,
                "task_id": "task-1",
            }
        )
        + "\n"
        + json.dumps(
            {
                "path": "projects/l2-smoke/live-dispatch.md",
                "decision": "write_complete",
                "before_hash": "0" * 64,
                "after_hash": "1" * 64,
                "task_id": "task-1",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    l2_smoke.assert_smoke(vault, "projects/l2-smoke/live-dispatch.md", audit_before=1)

    out = capsys.readouterr().out
    assert "live dispatch artifact asserted" in out
    assert "task_id=task-1" in out


def test_openai_smoke_server_selects_obsidian_put_tool():
    request = {
        "tools": [
            {"function": {"name": "mcp_obsidian_obsidian_get_content"}},
            {"function": {"name": "mcp_obsidian_obsidian_put_content"}},
        ]
    }

    assert smoke_server._select_put_tool(request) == "mcp_obsidian_obsidian_put_content"
