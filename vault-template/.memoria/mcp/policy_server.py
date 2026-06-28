"""MCP server wrapper for the Memoria policy engine."""

from __future__ import annotations

from pathlib import Path

from memoria_vault.runtime.paths import resolve_vault as _resolve_vault
from memoria_vault.runtime.policy.decision import set_gated_prefixes
from memoria_vault.runtime.policy.engine import PolicyEngine
from memoria_vault.runtime.policy.lanes import load_gated_prefixes


def build_server(vault: Path):
    """Wrap the policy engine as an MCP server."""
    set_gated_prefixes(load_gated_prefixes(vault))

    from mcp.server.fastmcp import FastMCP  # type: ignore

    engine = PolicyEngine(vault)
    server = FastMCP("memoria-policy")

    @server.tool()
    def check_permission(
        profile: str,
        action: str,
        path: str,
        task_id: str,
        reason: str = "",
        flags: dict | None = None,
    ) -> dict:
        """Authorize a vault action."""
        return engine.check(profile, action, path, task_id, reason, flags)

    @server.tool()
    def complete_write(
        profile: str, action: str, path: str, task_id: str, before_hash: str
    ) -> dict:
        """Record after_hash once a write completes."""
        return engine.complete_write(profile, action, path, task_id, before_hash)

    @server.tool()
    def set_session_skill(task_id: str, skill_policy: dict | None = None) -> dict:
        """Register a loaded skill's policy block for one-way session narrowing."""
        engine.set_session_skill(task_id, skill_policy)
        return {"ok": True}

    @server.tool()
    def clear_session_skill(task_id: str) -> dict:
        """Drop a session's skill narrowing."""
        engine.clear_session_skill(task_id)
        return {"ok": True}

    return server


def resolve_vault(arg: str | None) -> Path:
    """Resolve the policy server vault argument."""
    return _resolve_vault(arg, "MEMORIA_VAULT_PATH")
