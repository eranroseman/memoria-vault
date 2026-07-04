"""L1 component tests for policy_hook (ADR-44)."""

import os
import time as _time

from memoria_vault.runtime.policy import hook as _m

Path = _m.Path
_pending_file = _m._pending_file
_stash_key = _m._stash_key
classify = _m.classify
evaluate_post = _m.evaluate_post
evaluate_pre = _m.evaluate_pre
extract_path = _m.extract_path
json = _m.json
to_workspace_relative = _m.to_workspace_relative
POLICY_CONFIG = """
version: 1
actors:
  adapter:
    allow:
      tools:
        - obsidian.get_file_contents
        - obsidian.patch_content
        - obsidian.append_content
        - obsidian.delete_file
        - obsidian.put_content
        - obsidian.vault_write
        - qmd.search
        - skills
        - kanban
      write:
        - "inbox/**"
        - "knowledge/hubs/**"
    deny:
      write:
        - "knowledge/notes/**"
    require:
      - audit_log
    write_scope:
      - "inbox/"
  readonly:
    allow:
      tools:
        - obsidian.get_file_contents
        - qmd.search
"""


def test_classify_maps_write_tools_and_ignores_read_or_direct_tools():
    assert classify("obsidian_patch_content") == "write"
    assert classify("obsidian_append_content") == "append"
    assert classify("obsidian_delete_file") == "delete"
    assert classify("mcp__obsidian__put_content") == "write"
    assert classify("obsidian_get_file_contents") is None
    assert classify("obsidian_simple_search") is None
    assert classify("process") is None
    for direct in (
        "terminal",
        "run_command",
        "write_file",
        "patch",
        "file__write_file",
        "read_file",
        "search_files",
        "web_search",
        "browser_navigate",
        "send_message",
        "delegate_task",
    ):
        assert classify(direct) is None


def test_direct_capability_tools_are_hard_denied():
    for direct in (
        "terminal",
        "run_command",
        "write_file",
        "patch",
        "file__write_file",
        "read_file",
        "search_files",
        "web_search",
        "browser_navigate",
        "send_message",
        "delegate_task",
    ):
        blocked = evaluate_pre(
            {
                "tool_name": direct,
                "tool_input": {},
                "session_id": "t_x",
                "extra": {"request_id": "req_x"},
            },
            "adapter",
            Path("/nonexistent"),
        )
        assert blocked.get("decision") == "block"
        assert "direct or unaudited external access" in blocked.get("reason", "")


def test_extract_path_accepts_both_filepath_spellings():
    assert (
        extract_path({"filepath": "catalog/sources/x/source.md"}) == "catalog/sources/x/source.md"
    )
    assert extract_path({"file_path": "knowledge/notes/y.md"}) == "knowledge/notes/y.md"


def _vault_with_policy(tmp_path):
    vault = tmp_path
    config = vault / ".memoria" / "config" / "policy.yaml"
    config.parent.mkdir(parents=True)
    config.write_text(POLICY_CONFIG, encoding="utf-8")
    return vault


def _ev(vault, tool, path, *, key="filepath"):
    return evaluate_pre(
        {"tool_name": tool, "tool_input": {key: path}, "extra": {"request_id": "REQ-1"}},
        "adapter",
        vault,
    )


def test_evaluate_pre_allows_reads_and_gates_adapter_writes(tmp_path):
    vault = _vault_with_policy(tmp_path)

    assert _ev(vault, "obsidian_get_file_contents", "x.md") == {}
    direct = _ev(vault, "obsidian_patch_content", "inbox/a.md")
    review = _ev(vault, "obsidian_patch_content", "knowledge/hubs/r.md")
    denied = _ev(vault, "obsidian_delete_file", "knowledge/notes/c.md")
    missing_request = evaluate_pre(
        {"tool_name": "obsidian_patch_content", "tool_input": {"filepath": "inbox/a.md"}},
        "adapter",
        vault,
    )
    session_only = evaluate_pre(
        {
            "tool_name": "obsidian_patch_content",
            "tool_input": {"filepath": "inbox/a.md"},
            "session_id": "session-only",
        },
        "adapter",
        vault,
    )

    assert direct == {}
    assert review.get("decision") == "block"
    assert "attention item" in review["reason"]
    assert denied.get("decision") == "block"
    assert missing_request.get("decision") == "block"
    assert session_only.get("decision") == "block"
    assert "missing request_id" in session_only.get("reason", "")


def test_evaluate_pre_blocks_tools_outside_actor_policy(tmp_path):
    vault = _vault_with_policy(tmp_path)

    blocked = evaluate_pre(
        {
            "tool_name": "mcp_paper_search_search_arxiv",
            "tool_input": {},
            "extra": {"request_id": "REQ-2"},
        },
        "adapter",
        vault,
    )
    allowed = evaluate_pre(
        {"tool_name": "mcp_qmd_search", "tool_input": {}, "extra": {"request_id": "REQ-3"}},
        "adapter",
        vault,
    )

    assert blocked.get("decision") == "block"
    assert "tool allowlist" in blocked["reason"]
    assert allowed == {}


def test_evaluate_pre_maps_builtin_tool_names_to_allowed_toolsets(tmp_path):
    vault = _vault_with_policy(tmp_path)
    payload = {"tool_input": {}, "extra": {"request_id": "REQ-4"}}

    assert evaluate_pre({**payload, "tool_name": "skill_view"}, "adapter", vault) == {}
    assert evaluate_pre({**payload, "tool_name": "mcp_x__skill_manage"}, "adapter", vault) == {}


def test_evaluate_pre_allows_declared_adapter_tools(tmp_path):
    vault = _vault_with_policy(tmp_path)
    payload = {"tool_input": {}, "extra": {"request_id": "REQ-4"}}

    assert evaluate_pre({**payload, "tool_name": "kanban_show"}, "adapter", vault) == {}
    assert evaluate_pre({**payload, "tool_name": "mcp_x__kanban_complete"}, "adapter", vault) == {}

    blocked = evaluate_pre({**payload, "tool_name": "kanban_show"}, "readonly", vault)
    assert blocked.get("decision") == "block"
    assert "tool allowlist" in blocked["reason"]


def test_evaluate_pre_fails_closed_when_actor_policy_is_missing(tmp_path):
    vault = _vault_with_policy(tmp_path)
    (vault / ".memoria" / "config" / "policy.yaml").unlink()

    blocked = _ev(vault, "obsidian_get_file_contents", "x.md")

    assert blocked.get("decision") == "block"
    assert "workspace policy unavailable" in blocked["reason"]


def test_native_obsidian_mcp_writes_are_gated_and_dangerous_tools_hard_block(tmp_path):
    vault = _vault_with_policy(tmp_path)

    assert _ev(vault, "mcp_obsidian_vault_write", "inbox/n.md") == {}
    assert _ev(vault, "mcp_obsidian_vault_write", "knowledge/notes/c.md").get("decision") == "block"
    assert _ev(vault, "mcp_obsidian_command_execute", "").get("decision") == "block"
    assert _ev(vault, "mcp_obsidian_vault_delete", "inbox/a.md").get("decision") == "block"
    assert _ev(vault, "mcp_obsidian_vault_move", "inbox/a.md").get("decision") == "block"


def test_file_toolset_writes_are_blocked_even_for_allowed_workspace_zones(tmp_path):
    vault = _vault_with_policy(tmp_path)
    abs_claim = str(vault / "knowledge" / "notes" / "c.md")

    assert _ev(vault, "write_file", "inbox/f.md", key="file_path").get("decision") == "block"
    assert (
        _ev(vault, "write_file", "knowledge/notes/c.md", key="file_path").get("decision") == "block"
    )
    assert to_workspace_relative(abs_claim, vault) == "knowledge/notes/c.md"
    assert _ev(vault, "write_file", abs_claim, key="file_path").get("decision") == "block"
    assert to_workspace_relative("/etc/passwd", vault) is None
    assert (
        _ev(vault, "write_file", "/tmp/external-repo/main.py", key="file_path").get("decision")
        == "block"
    )


def test_evaluate_post_pairs_write_hashes_and_cleans_pending_stash(tmp_path):
    vault = _vault_with_policy(tmp_path)
    (vault / "inbox").mkdir(parents=True, exist_ok=True)
    from memoria_vault.runtime.policy import EMPTY_SHA256

    payload = {
        "tool_name": "obsidian_put_content",
        "tool_input": {"filepath": "inbox/round.md"},
        "extra": {"request_id": "REQ-9", "tool_call_id": "call-xyz"},
    }

    stash = _pending_file(vault, _stash_key(payload))
    stash.parent.mkdir(parents=True, exist_ok=True)
    stash.write_text(
        json.dumps({"before_hash": EMPTY_SHA256, "path": "inbox/round.md"}),
        encoding="utf-8",
    )
    (vault / "inbox" / "round.md").write_text("answer body", encoding="utf-8")
    post = evaluate_post(payload, "adapter", vault)
    audit_lines = (
        (vault / "system" / "logs" / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    )
    completes = [
        json.loads(ln) for ln in audit_lines if json.loads(ln).get("decision") == "write_complete"
    ]

    assert stash.exists() is False
    assert post == {}
    assert len(completes) == 1
    assert completes[0]["actor"] == "adapter"
    assert completes[0]["request_id"] == "REQ-9"
    assert completes[0]["before_hash"]
    assert completes[0]["after_hash"]
    assert completes[0]["before_hash"] != completes[0]["after_hash"]


def test_evaluate_post_requires_explicit_request_id_for_completion_audit(tmp_path):
    vault = _vault_with_policy(tmp_path)
    (vault / "inbox").mkdir(parents=True, exist_ok=True)
    from memoria_vault.runtime.policy import EMPTY_SHA256

    payload = {
        "tool_name": "obsidian_put_content",
        "tool_input": {"filepath": "inbox/round.md"},
        "session_id": "session-only",
        "extra": {"tool_call_id": "call-without-request"},
    }
    stash = _pending_file(vault, _stash_key(payload))
    stash.parent.mkdir(parents=True, exist_ok=True)
    stash.write_text(
        json.dumps({"before_hash": EMPTY_SHA256, "path": "inbox/round.md"}),
        encoding="utf-8",
    )
    (vault / "inbox" / "round.md").write_text("answer body", encoding="utf-8")

    post = evaluate_post(payload, "adapter", vault)
    audit_log = vault / "system" / "logs" / "audit.jsonl"

    assert post == {}
    assert stash.exists() is False
    assert not audit_log.exists()


def test_evaluate_pre_prunes_stale_pending_stashes_but_keeps_fresh_stashes(tmp_path):
    vault = _vault_with_policy(tmp_path)
    pend_dir = vault / "system" / "logs" / ".pending"
    pend_dir.mkdir(parents=True, exist_ok=True)
    stale = pend_dir / "stale-call.json"
    fresh = pend_dir / "fresh-call.json"
    stale.write_text("{}", encoding="utf-8")
    fresh.write_text("{}", encoding="utf-8")
    old_ts = _time.time() - 25 * 3600
    os.utime(stale, (old_ts, old_ts))

    _ev(vault, "obsidian_get_file_contents", "x.md")

    assert not stale.is_file()
    assert fresh.is_file()
