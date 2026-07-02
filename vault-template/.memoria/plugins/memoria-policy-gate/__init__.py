"""Memoria policy gate plugin for optional external adapters.

The standalone CLI/runtime is the baseline write path. If an operator wires an
external adapter, its vault writes should pass through this plugin before the
tool executes and through audit completion after it returns. The plugin reuses
the tested runtime policy core; no policy decision logic lives here.
"""

import site
import sys
import traceback
from pathlib import Path

PROFILE = "{{PROFILE}}"
VAULT = Path("{{VAULT_PATH}}")


def _vault_site_packages() -> list[Path]:
    venv = VAULT / ".memoria" / ".venv"
    return [venv / "Lib" / "site-packages", *sorted((venv / "lib").glob("python*/site-packages"))]


def _bootstrap_vault_runtime_package() -> None:
    for path in _vault_site_packages():
        if not path.is_dir():
            continue
        site.addsitedir(str(path))
        path_text = str(path)
        if path_text in sys.path:
            sys.path.remove(path_text)
        sys.path.insert(0, path_text)


_bootstrap_vault_runtime_package()


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
        from memoria_vault.runtime.policy import hook as policy_hook

        result = policy_hook.evaluate_pre(_payload(tool_name, args, task_id), PROFILE, VAULT)
        if result.get("decision") == "block":
            return {"action": "block", "message": result.get("reason", "policy gate: blocked")}
        return None
    except Exception as exc:  # noqa: BLE001 -- policy gate fails closed; any error blocks the write
        return {"action": "block", "message": f"policy gate failed-closed (plugin error): {exc}"}


def _complete(tool_name, args, task_id, **kwargs):
    """post_tool_call: finish the audit record (after_hash). Never blocks."""
    try:
        from memoria_vault.runtime.policy import hook as policy_hook

        policy_hook.evaluate_post(_payload(tool_name, args, task_id), PROFILE, VAULT)
    except Exception:  # noqa: BLE001 -- never block the agent on audit-completion failures
        # Never block the agent on audit-completion failures, but log so the
        # operator can diagnose missing audit records.
        traceback.print_exc(file=sys.stderr)
    return


def register(ctx):
    ctx.register_hook("pre_tool_call", _gate)
    ctx.register_hook("post_tool_call", _complete)
