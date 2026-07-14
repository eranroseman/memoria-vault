"""L1 completeness sweep for the policy gate's direct-capability hard-deny.

A boundary test must prove the boundary is *complete*, not that one known case is
denied (AGENTS.md "Enforcement is a mechanism, not a label"). This sweep asserts the
gate actually blocks **every** name in `DENY_DIRECT_TOOLS` — including through
adapter-style prefixes — and pins the `process` regression (a terminal-toolset
tool that the denylist missed, so the gate allowed it).
"""

from memoria_vault.runtime.policy import hook as _m

evaluate_pre = _m.evaluate_pre
Path = _m.Path
ROOT = Path(__file__).resolve().parents[1]
POLICY_CONFIG = """
version: 1
actors:
  memory-reader:
    allow:
      tools: [memory]
  adapter:
    allow:
      tools: [skills, kanban, search.query]
    deny:
      tools: [memory]
"""


def _payload(tool_name: str) -> dict:
    return {
        "tool_name": tool_name,
        "tool_input": {},
        "session_id": "t_sweep",
        "extra": {"request_id": "req_sweep"},
    }


def _decide(tool_name: str, actor: str = "adapter") -> dict:
    return evaluate_pre(_payload(tool_name), actor, Path("/nonexistent"))


def _workspace_with_policy(tmp_path: Path) -> Path:
    config = tmp_path / ".memoria" / "config" / "policy.yaml"
    config.parent.mkdir(parents=True)
    config.write_text(POLICY_CONFIG, encoding="utf-8")
    return tmp_path


def test_every_denylisted_tool_is_blocked_bare_and_prefixed():
    """Each DENY_DIRECT_TOOLS entry blocks by its bare name AND through the
    `mcp_<server>_` and `<toolset>__` prefixes the runtime actually emits."""
    assert _m.DENY_DIRECT_TOOLS, "denylist must not be empty"
    for tool in sorted(_m.DENY_DIRECT_TOOLS):
        for name in (tool, f"mcp_x__{tool}", f"file__{tool}"):
            decision = _decide(name)
            assert decision.get("decision") == "block", f"gate did not block {name!r}: {decision}"
            assert "direct or unaudited external access" in decision.get("reason", "")


def test_process_is_blocked_regression():
    """`process` is a real tool in terminal toolsets; the denylist once
    missed it, so the gate returned {} (allow). Regression guard."""
    assert "process" in _m.DENY_DIRECT_TOOLS
    assert _decide("process").get("decision") == "block"
    assert _decide("mcp_x__process").get("decision") == "block"


def test_egress_tools_are_blocked_regression():
    """Disabled toolsets are schema-hiding, so direct invocation by name
    must hit the gate for egress/messaging/browser families."""
    for tool in ("web_search", "browser_navigate", "send_message", "delegate_task"):
        assert tool in _m.DENY_DIRECT_TOOLS
        assert _decide(tool).get("decision") == "block"
        assert _decide(f"mcp_x__{tool}").get("decision") == "block"


def test_acp_exposed_local_history_tools_are_blocked_or_actor_scoped(tmp_path):
    vault = _workspace_with_policy(tmp_path)
    assert "session_search" in _m.DENY_DIRECT_TOOLS
    assert _decide("session_search").get("decision") == "block"
    assert _decide("mcp_x__session_search").get("decision") == "block"

    assert evaluate_pre(_payload("memory"), "memory-reader", vault) == {}
    assert (
        evaluate_pre(_payload("mcp_x__memory"), "memory-reader", vault).get("decision") == "block"
    )
    decision = evaluate_pre(_payload("memory"), "adapter", vault)
    assert decision.get("decision") == "block", f"gate did not block memory: {decision}"
    assert "denied for actor adapter" in decision.get("reason", "")
    assert evaluate_pre(_payload("mcp_x__memory"), "adapter", vault).get("decision") == "block"
