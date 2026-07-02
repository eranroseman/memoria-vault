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
to_vault_relative = _m.to_vault_relative
TOOL_REGISTRY = """
version: 1
groups:
  vault_read: [obsidian.get_file_contents]
  qmd_read: [qmd.search]
profiles:
  memoria-copi:
    allow: [skills]
  memoria-librarian:
    allow: [vault_read, skills, kanban, qmd_read]
  memoria-writer:
    allow: [vault_read, skills, kanban, qmd_read]
  memoria-peer-reviewer:
    allow: [vault_read, skills, kanban, qmd_read]
  memoria-engineer:
    allow: [vault_read, skills, kanban]
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
                "extra": {"task_id": "t_x"},
            },
            "memoria-engineer",
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
    lanes = vault / ".memoria" / "lane-overrides"
    lanes.mkdir(parents=True)
    (vault / ".memoria" / "tool-registry.yaml").write_text(TOOL_REGISTRY, encoding="utf-8")
    (lanes / "writer.yaml").write_text(
        "profile: memoria-writer\npolicy:\n  allow:\n    write:\n"
        '      - "inbox/**"\n      - "knowledge/hubs/**"\n'
        '  deny:\n    write:\n      - "knowledge/notes/**"\n'
        '  require:\n    - audit_log\nrouting:\n  write_scope:\n    - "inbox/"\n',
        encoding="utf-8",
    )
    return vault


def _ev(vault, tool, path, *, key="filepath"):
    return evaluate_pre(
        {"tool_name": tool, "tool_input": {key: path}, "extra": {"task_id": "T1"}},
        "memoria-writer",
        vault,
    )


def test_evaluate_pre_allows_reads_but_blocks_direct_profile_writes(tmp_path):
    vault = _vault_with_policy(tmp_path)

    assert _ev(vault, "obsidian_get_file_contents", "x.md") == {}
    direct = _ev(vault, "obsidian_patch_content", "inbox/a.md")
    review = _ev(vault, "obsidian_patch_content", "knowledge/hubs/r.md")
    denied = _ev(vault, "obsidian_delete_file", "knowledge/notes/c.md")
    missing_task = evaluate_pre(
        {"tool_name": "obsidian_patch_content", "tool_input": {"filepath": "inbox/a.md"}},
        "memoria-writer",
        vault,
    )

    assert direct.get("decision") == "block"
    assert "tool-registry allowlist" in direct["reason"]
    assert review.get("decision") == "block"
    assert "tool-registry allowlist" in review["reason"]
    assert denied.get("decision") == "block"
    assert missing_task.get("decision") == "block"


def test_evaluate_pre_blocks_tools_outside_profile_registry(tmp_path):
    vault = _vault_with_policy(tmp_path)

    blocked = evaluate_pre(
        {
            "tool_name": "mcp_paper_search_search_arxiv",
            "tool_input": {},
            "extra": {"task_id": "T2"},
        },
        "memoria-writer",
        vault,
    )
    allowed = evaluate_pre(
        {"tool_name": "mcp_qmd_search", "tool_input": {}, "extra": {"task_id": "T3"}},
        "memoria-writer",
        vault,
    )

    assert blocked.get("decision") == "block"
    assert "tool-registry allowlist" in blocked["reason"]
    assert allowed == {}


def test_evaluate_pre_maps_builtin_tool_names_to_allowed_toolsets(tmp_path):
    vault = _vault_with_policy(tmp_path)
    payload = {"tool_input": {}, "extra": {"task_id": "T4"}}

    assert evaluate_pre({**payload, "tool_name": "skill_view"}, "memoria-writer", vault) == {}
    assert (
        evaluate_pre({**payload, "tool_name": "mcp_x__skill_manage"}, "memoria-copi", vault) == {}
    )


def test_evaluate_pre_allows_kanban_worker_tools_for_dispatched_profiles(tmp_path):
    vault = _vault_with_policy(tmp_path)
    payload = {"tool_input": {}, "extra": {"task_id": "T4"}}

    for profile in (
        "memoria-librarian",
        "memoria-writer",
        "memoria-peer-reviewer",
        "memoria-engineer",
    ):
        assert evaluate_pre({**payload, "tool_name": "kanban_show"}, profile, vault) == {}
        assert (
            evaluate_pre({**payload, "tool_name": "mcp_x__kanban_complete"}, profile, vault) == {}
        )

    blocked = evaluate_pre({**payload, "tool_name": "kanban_show"}, "memoria-copi", vault)
    assert blocked.get("decision") == "block"
    assert "tool-registry allowlist" in blocked["reason"]


def test_evaluate_pre_fails_closed_when_registry_is_missing(tmp_path):
    vault = _vault_with_policy(tmp_path)
    (vault / ".memoria" / "tool-registry.yaml").unlink()

    blocked = _ev(vault, "obsidian_get_file_contents", "x.md")

    assert blocked.get("decision") == "block"
    assert "tool registry unavailable" in blocked["reason"]


def test_native_obsidian_mcp_writes_are_gated_and_dangerous_tools_hard_block(tmp_path):
    vault = _vault_with_policy(tmp_path)

    assert _ev(vault, "mcp_obsidian_vault_write", "inbox/n.md").get("decision") == "block"
    assert _ev(vault, "mcp_obsidian_vault_write", "knowledge/notes/c.md").get("decision") == "block"
    assert _ev(vault, "mcp_obsidian_command_execute", "").get("decision") == "block"
    assert _ev(vault, "mcp_obsidian_vault_delete", "inbox/a.md").get("decision") == "block"
    assert _ev(vault, "mcp_obsidian_vault_move", "inbox/a.md").get("decision") == "block"


def test_file_toolset_writes_are_blocked_even_for_allowed_vault_zones(tmp_path):
    vault = _vault_with_policy(tmp_path)
    abs_claim = str(vault / "knowledge" / "notes" / "c.md")

    assert _ev(vault, "write_file", "inbox/f.md", key="file_path").get("decision") == "block"
    assert (
        _ev(vault, "write_file", "knowledge/notes/c.md", key="file_path").get("decision") == "block"
    )
    assert to_vault_relative(abs_claim, vault) == "knowledge/notes/c.md"
    assert _ev(vault, "write_file", abs_claim, key="file_path").get("decision") == "block"
    assert to_vault_relative("/etc/passwd", vault) is None
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
        "extra": {"task_id": "T9", "tool_call_id": "call-xyz"},
    }

    stash = _pending_file(vault, _stash_key(payload))
    stash.parent.mkdir(parents=True, exist_ok=True)
    stash.write_text(
        json.dumps({"before_hash": EMPTY_SHA256, "path": "inbox/round.md"}),
        encoding="utf-8",
    )
    (vault / "inbox" / "round.md").write_text("answer body", encoding="utf-8")
    post = evaluate_post(payload, "memoria-writer", vault)
    audit_lines = (
        (vault / "system" / "logs" / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    )
    completes = [
        json.loads(ln) for ln in audit_lines if json.loads(ln).get("decision") == "write_complete"
    ]

    assert stash.exists() is False
    assert post == {}
    assert len(completes) == 1
    assert completes[0]["before_hash"]
    assert completes[0]["after_hash"]
    assert completes[0]["before_hash"] != completes[0]["after_hash"]


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
