"""L1 tests for the fail-closed memoria-policy-gate plugin."""

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "src" / ".memoria" / "plugins" / "memoria-policy-gate" / "__init__.py"


def _load_plugin():
    spec = importlib.util.spec_from_file_location("memoria_policy_gate_test", PLUGIN)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _vault_with_writer_policy(tmp_path):
    lane_dir = tmp_path / ".memoria" / "lane-overrides"
    lane_dir.mkdir(parents=True)
    (lane_dir / "writer.yaml").write_text(
        "profile: memoria-writer\n"
        "policy:\n"
        "  allow:\n"
        "    write:\n"
        '      - "inbox/**"\n'
        "  deny:\n"
        "    write:\n"
        '      - "notes/claims/**"\n'
        "  require:\n"
        "    - audit_log\n"
        "routing:\n"
        "  write_scope:\n"
        '    - "inbox/"\n',
        encoding="utf-8",
    )
    return tmp_path


def test_plugin_blocks_known_deny_mcp_obsidian_write_and_audits(tmp_path):
    gate = _load_plugin()
    gate.PROFILE = "memoria-writer"
    gate.VAULT = _vault_with_writer_policy(tmp_path)

    result = gate._gate(
        "mcp_obsidian_vault_write",
        {"filepath": "notes/claims/blocked.md", "content": "must not land"},
        "TASK-DENY",
    )
    audit = [
        json.loads(line)
        for line in (tmp_path / "system" / "logs" / "audit.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]

    assert result["action"] == "block"
    assert "deny" in result["message"]
    assert audit[-1]["decision"] == "deny"
    assert audit[-1]["path"] == "notes/claims/blocked.md"
    assert audit[-1]["task_id"] == "TASK-DENY"


def test_plugin_blocks_disabled_tool_invocation_by_name(tmp_path):
    gate = _load_plugin()
    gate.PROFILE = "memoria-writer"
    gate.VAULT = _vault_with_writer_policy(tmp_path)

    result = gate._gate("mcp_x__web_search", {"query": "exfiltrate"}, "TASK-EGRESS")

    assert result["action"] == "block"
    assert "MCP" in result["message"]


def test_plugin_blocks_when_policy_hook_import_is_broken(tmp_path, monkeypatch):
    gate = _load_plugin()
    gate.PROFILE = "memoria-writer"
    gate.VAULT = _vault_with_writer_policy(tmp_path)
    monkeypatch.setitem(sys.modules, "policy_hook", None)

    result = gate._gate("mcp_obsidian_vault_write", {"filepath": "inbox/a.md"}, "TASK-IMPORT")

    assert result["action"] == "block"
    assert "failed-closed" in result["message"]
