"""Memoria policy gate — Hermes Python plugin (the vault write gate).

This is the PRIMARY enforcement point for the structural review gate (ADR-03):
every vault write the agent attempts is routed through the lane policy BEFORE it
executes, and blocked on `deny`/`dry_run`.

Why a plugin and not the `hooks:` shell hook it replaces (ADR-28):
  * Hermes registers MCP tools as `mcp_<server>_<tool>` — the obsidian write is
    `mcp_obsidian_obsidian_append_content`. The shell-hook matcher uses
    `re.fullmatch`, so `obsidian.*` never matched it and the gate never fired.
  * Shell hooks are consent-gated (skipped on non-TTY runs unless allowlisted)
    AND fail-OPEN (errors/timeouts proceed). Neither is acceptable for a gate.
  * A Python plugin runs in-process in EVERY mode (-z / gateway / cron / ACP),
    needs no consent, does its own matching (so the real `mcp_obsidian_*` name is
    caught), receives the `task_id`, and can be made fail-CLOSED.

It reuses the tested decision core verbatim — `policy_hook.evaluate_pre` /
`evaluate_post` and `policy_mcp.PolicyEngine` — so no policy logic lives here.

The installer substitutes {{PROFILE}} and {{VAULT_PATH}} per lane at deploy time.
"""

import sys
import traceback
from pathlib import Path

PROFILE = "{{PROFILE}}"
VAULT = Path("{{VAULT_PATH}}")

_MCP_DIR = VAULT / ".memoria" / "mcp"
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))


def _payload(tool_name, args, task_id):
    tid = task_id or ""
    return {
        "tool_name": tool_name,
        "tool_input": args or {},
        "session_id": tid,
        "extra": {"task_id": tid},
    }


def _gate(tool_name, args, task_id, **kwargs):
    """pre_tool_call: block deny/dry_run vault writes. Fail-closed."""
    try:
        import policy_hook

        result = policy_hook.evaluate_pre(_payload(tool_name, args, task_id), PROFILE, VAULT)
        if result.get("decision") == "block":
            return {"action": "block", "message": result.get("reason", "policy gate: blocked")}
        return None
    except Exception as exc:  # noqa: BLE001 -- policy gate fails closed; any error blocks the write
        return {"action": "block", "message": f"policy gate failed-closed (plugin error): {exc}"}


def _complete(tool_name, args, task_id, **kwargs):
    """post_tool_call: finish the audit record (after_hash). Never blocks."""
    try:
        import policy_hook

        policy_hook.evaluate_post(_payload(tool_name, args, task_id), PROFILE, VAULT)
    except Exception:  # noqa: BLE001 -- never block the agent on audit-completion failures
        # Never block the agent on audit-completion failures, but log so the
        # operator can diagnose missing audit records.
        traceback.print_exc(file=sys.stderr)
    return


def register(ctx):
    ctx.register_hook("pre_tool_call", _gate)
    ctx.register_hook("post_tool_call", _complete)
