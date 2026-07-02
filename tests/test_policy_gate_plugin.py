"""L1 tests for the fail-closed memoria-policy-gate plugin."""

import builtins
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "vault-template" / ".memoria" / "plugins" / "memoria-policy-gate" / "__init__.py"
POLICY_CONFIG = """
version: 1
actors:
  adapter:
    allow:
      tools:
        - obsidian.vault_write
      write:
        - "inbox/**"
    deny:
      write:
        - "knowledge/notes/**"
    require:
      - audit_log
    write_scope:
      - "inbox/"
"""


def _load_plugin():
    spec = importlib.util.spec_from_file_location("memoria_policy_gate_test", PLUGIN)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _workspace_with_actor_policy(tmp_path):
    config = tmp_path / ".memoria" / "config" / "policy.yaml"
    config.parent.mkdir(parents=True)
    config.write_text(POLICY_CONFIG, encoding="utf-8")
    return tmp_path


def test_plugin_blocks_known_deny_mcp_obsidian_write_and_audits(tmp_path):
    gate = _load_plugin()
    gate.ACTOR = "adapter"
    gate.WORKSPACE = _workspace_with_actor_policy(tmp_path)

    result = gate._gate(
        "mcp_obsidian_vault_write",
        {"filepath": "knowledge/notes/blocked.md", "content": "must not land"},
        "REQ-DENY",
    )
    audit = [
        json.loads(line)
        for line in (tmp_path / "system" / "logs" / "audit.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]

    assert result["action"] == "block"
    assert "policy deny" in result["message"]
    assert audit[-1]["decision"] == "deny"
    assert audit[-1]["policy_rule"] == "Adapter.deny.write"
    assert audit[-1]["actor"] == "adapter"
    assert audit[-1]["path"] == "knowledge/notes/blocked.md"
    assert audit[-1]["request_id"] == "REQ-DENY"


def test_plugin_blocks_disabled_tool_invocation_by_name(tmp_path):
    gate = _load_plugin()
    gate.ACTOR = "adapter"
    gate.WORKSPACE = _workspace_with_actor_policy(tmp_path)

    result = gate._gate("mcp_x__web_search", {"query": "exfiltrate"}, "REQ-EGRESS")

    assert result["action"] == "block"
    assert "direct or unaudited external access" in result["message"]


def test_plugin_blocks_when_runtime_policy_hook_import_is_broken(tmp_path, monkeypatch):
    gate = _load_plugin()
    gate.ACTOR = "adapter"
    gate.WORKSPACE = _workspace_with_actor_policy(tmp_path)
    real_import = builtins.__import__

    def broken_import(name, globals_=None, locals_=None, fromlist=(), level=0):
        if name == "memoria_vault.runtime.policy" and "hook" in fromlist:
            raise ImportError("hook unavailable")
        return real_import(name, globals_, locals_, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", broken_import)

    result = gate._gate("mcp_obsidian_vault_write", {"filepath": "inbox/a.md"}, "REQ-IMPORT")

    assert result["action"] == "block"
    assert "failed-closed" in result["message"]
