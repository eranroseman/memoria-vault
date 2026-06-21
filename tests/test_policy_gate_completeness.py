"""L1 completeness sweep for the policy gate's direct-capability hard-deny.

A boundary test must prove the boundary is *complete*, not that one known case is
denied (AGENTS.md "Enforcement is a mechanism, not a label"). This sweep asserts the
gate actually blocks **every** name in `DENY_DIRECT_TOOLS` — including through the
`mcp_<server>_` / `<toolset>__` prefixes Hermes adds — and pins the `process`
regression (a real terminal-toolset tool that the denylist missed, so the gate
allowed it). `hermes_contract_doctor.py` is the companion that keeps the list itself
in sync with the installed Hermes; this test proves whatever is in the list is enforced.
"""

import hermes_contract_doctor as doctor
import policy_hook as _m

evaluate_pre = _m.evaluate_pre
Path = _m.Path


def _decide(tool_name: str, profile: str = "memoria-copi") -> dict:
    return evaluate_pre(
        {
            "tool_name": tool_name,
            "tool_input": {},
            "session_id": "t_sweep",
            "extra": {"task_id": "t_sweep"},
        },
        profile,
        Path("/nonexistent"),
    )


def test_every_denylisted_tool_is_blocked_bare_and_prefixed():
    """Each DENY_DIRECT_TOOLS entry blocks by its bare name AND through the
    `mcp_<server>_` and `<toolset>__` prefixes the runtime actually emits."""
    assert _m.DENY_DIRECT_TOOLS, "denylist must not be empty"
    for tool in sorted(_m.DENY_DIRECT_TOOLS):
        for name in (tool, f"mcp_x__{tool}", f"file__{tool}"):
            decision = _decide(name)
            assert decision.get("decision") == "block", f"gate did not block {name!r}: {decision}"
            assert "MCP" in decision.get("reason", "")


def test_process_is_blocked_regression():
    """`process` is a real tool in Hermes's terminal toolset; the denylist once
    missed it, so the gate returned {} (allow). Regression guard."""
    assert "process" in _m.DENY_DIRECT_TOOLS
    assert _decide("process").get("decision") == "block"
    assert _decide("mcp_x__process").get("decision") == "block"


def test_egress_tools_are_blocked_regression():
    """alpha.9: disabled toolsets are schema-hiding, so direct invocation by name
    must hit the gate for egress/messaging/browser families."""
    for tool in ("web_search", "browser_navigate", "send_message", "delegate_task"):
        assert tool in _m.DENY_DIRECT_TOOLS
        assert _decide(tool).get("decision") == "block"
        assert _decide(f"mcp_x__{tool}").get("decision") == "block"


def test_contract_doctor_fails_when_installed_egress_tool_is_not_denied(tmp_path, monkeypatch):
    hermes = tmp_path / "hermes-agent"
    hermes.mkdir()
    (hermes / "toolsets.py").write_text(
        "TOOLSETS = {'web': {'tools': ['web_search', 'new_web_tool']}}\n",
        encoding="utf-8",
    )

    report = doctor.run_contract_doctor(hermes)

    assert not report["ok"]
    assert any("new_web_tool" in err for err in report["errors"])


def test_contract_doctor_checks_deployed_policy_hook_freshness(tmp_path, monkeypatch):
    hermes = tmp_path / "hermes-agent"
    hermes.mkdir()
    (hermes / "toolsets.py").write_text("TOOLSETS = {}\n", encoding="utf-8")
    vault = tmp_path / "vault"
    deployed = vault / ".memoria/mcp/policy_hook.py"
    deployed.parent.mkdir(parents=True)
    deployed.write_text("# stale\n", encoding="utf-8")

    report = doctor.run_contract_doctor(hermes, vault)

    assert not report["ok"]
    assert any("stale" in err for err in report["errors"])


if __name__ == "__main__":  # pragma: no cover — manual smoke
    test_every_denylisted_tool_is_blocked_bare_and_prefixed()
    test_process_is_blocked_regression()
    print("policy-gate completeness sweep: OK")
