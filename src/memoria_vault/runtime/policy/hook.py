"""Adapter hook helpers that route workspace writes through the policy gate.

The standalone runtime does not require MCP or chat runtimes. Optional adapters
can still call these helpers before and after tool invocations so adapter writes
reuse the same fail-closed policy and audit behavior as the runtime package.

This one script handles BOTH the gate and the audit completion, branching on
`hook_event_name`:
  - pre_tool_call  -> decide; block deny/dry_run; on allow, stash before_hash.
  - post_tool_call -> read the stash, compute after_hash, append the paired
                      reversibility record (before+after) to audit.jsonl, clean up.

External adapter wire protocol:
  stdin  : {"tool_name","tool_input","session_id","cwd","extra":{"request_id",...}}
  stdout : {} to allow; {"decision":"block","reason":"..."} to block.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from memoria_vault.runtime.diagnostics import record_event
from memoria_vault.runtime.paths import load_json, safe_filename

# Obsidian adapter tool-name keyword -> policy action. Matched by substring so it
# survives server prefixing (e.g. mcp__obsidian__patch_content). Read tools
# (get / list / search) contain none of these keywords -> not gated (return {}).
WRITE_KEYWORDS = {
    "append": "append",
    "patch": "write",
    "put": "write",
    "create": "write",
    "write": "write",
    "delete": "delete",
    "rename": "move",
    "move": "move",
}
# Direct-capability and unaudited-egress tools hard-denied for EVERY adapter actor.
# The standalone runtime owns writes through requests and trusted_writer; any
# adapter call reaching these tools is config drift or prompt-injection bypassing
# schema-hiding, so fail closed.
# Bare tool names matched exactly so an unrelated tool merely containing "patch"
# is never caught. This list covers the known file/terminal/code_execution plus
# egress/side-effect toolsets exposed by historical adapters.
DENY_DIRECT_TOOLS = frozenset(
    {
        "write_file",
        "patch",
        "read_file",
        "search_files",  # file toolset
        "terminal",
        "process",  # terminal toolset — sibling of `terminal`, runs/inspects processes
        "run_command",  # common alias name; harmless when absent
        "code_execution",  # legacy/alias name (the real tool is `execute_code`)
        "execute_code",  # code_execution toolset
        "session_search",
        "web_extract",
        "web_search",
        "browser_back",
        "browser_cdp",
        "browser_click",
        "browser_console",
        "browser_dialog",
        "browser_get_images",
        "browser_navigate",
        "browser_press",
        "browser_scroll",
        "browser_snapshot",
        "browser_type",
        "browser_vision",
        "send_message",
        "x_search",
        "computer_use",
        "delegate_task",
        "image_generate",
        "vision_analyze",
        "video_analyze",
        "video_generate",
        "text_to_speech",
        "ha_call_service",
        "ha_get_state",
        "ha_list_entities",
        "ha_list_services",
        "spotify_albums",
        "spotify_devices",
        "spotify_library",
        "spotify_playback",
        "spotify_playlists",
        "spotify_queue",
        "spotify_search",
        "cronjob",
    }
)
PATH_KEYS = ("filepath", "file_path", "path", "file", "target", "filename", "dest", "destination")

# Obsidian native-MCP tools hard-denied for EVERY actor. `command_execute` runs an
# arbitrary Obsidian command and has no single path to gate (so the path matcher
# can't bound it); `vault_delete`/`vault_move` are destructive ops the workflows
# don't need (least privilege -- the prior uvx mcp-obsidian exposed only
# read/write/append/patch). Matched as a substring after the `obsidian` prefix.
DENY_OBSIDIAN = ("command_execute", "vault_delete", "vault_move")
BUILTIN_TOOLSET_BY_TOOL = {
    "kanban_show": "kanban",
    "kanban_list": "kanban",
    "kanban_complete": "kanban",
    "kanban_block": "kanban",
    "kanban_heartbeat": "kanban",
    "kanban_comment": "kanban",
    "kanban_create": "kanban",
    "kanban_link": "kanban",
    "kanban_unblock": "kanban",
    "skills_list": "skills",
    "skill_view": "skills",
    "skill_manage": "skills",
}


def _actor_tool_policy(workspace: Path, actor: str) -> tuple[set[str], set[str]]:
    from memoria_vault.runtime.policy.workspace import load_actor_policy

    policy = load_actor_policy(workspace, actor)
    return (
        {str(tool).lower() for tool in policy.allow_tools},
        {str(tool).lower() for tool in policy.deny_tools},
    )


def _tool_candidates(tool_name: str, allowed: set[str]) -> set[str]:
    t = (tool_name or "").lower()
    candidates = {t}
    base = t.rsplit("__", 1)[-1].rsplit(".", 1)[-1]
    if base in BUILTIN_TOOLSET_BY_TOOL:
        candidates.add(BUILTIN_TOOLSET_BY_TOOL[base])
    if not t.startswith("mcp_"):
        candidates.add(base)
        if "__" in t:
            candidates.add(t.split("__", 1)[0])
        if t.startswith("obsidian_"):
            candidates.add("obsidian." + t.removeprefix("obsidian_"))

    servers = sorted(
        {tool.split(".", 1)[0] for tool in allowed if "." in tool}, key=len, reverse=True
    )
    if t.startswith("mcp__"):
        parts = t.split("__", 2)
        if len(parts) == 3:
            server, tool = parts[1], parts[2]
            candidates.add(f"{server}.{tool}")
            if tool.startswith(f"{server}_"):
                candidates.add(f"{server}.{tool.removeprefix(f'{server}_')}")
    elif t.startswith("mcp_"):
        rest = t.removeprefix("mcp_")
        for server in servers:
            if rest == server:
                candidates.add(server)
            elif rest.startswith(f"{server}_"):
                tool = rest.removeprefix(f"{server}_")
                candidates.add(f"{server}.{tool}")
                if tool.startswith(f"{server}_"):
                    candidates.add(f"{server}.{tool.removeprefix(f'{server}_')}")
    return candidates


def _tool_policy_block(tool_name: str, actor: str, workspace: Path) -> dict | None:
    try:
        allowed, denied = _actor_tool_policy(workspace, actor)
    except Exception as exc:  # noqa: BLE001 -- missing/invalid policy must fail closed
        return {
            "decision": "block",
            "reason": f"policy gate: workspace policy unavailable for {actor} ({exc}) -- blocked fail-closed.",
        }
    candidates = _tool_candidates(tool_name, allowed | denied)
    if not candidates.isdisjoint(denied):
        return {
            "decision": "block",
            "reason": f"policy gate: '{tool_name}' is denied for actor {actor}.",
        }
    if candidates.isdisjoint(allowed):
        return {
            "decision": "block",
            "reason": f"policy gate: '{tool_name}' is outside actor {actor}'s tool allowlist.",
        }
    return None


def classify(tool_name: str) -> str | None:
    """Policy action for a gated *write* tool, or None for reads / ungated tools."""
    t = (tool_name or "").lower()
    if "obsidian" in t:
        for kw, action in WRITE_KEYWORDS.items():
            if kw in t:
                return action
        return None
    return None


def extract_path(tool_input: dict) -> str:
    for k in PATH_KEYS:
        v = (tool_input or {}).get(k)
        if isinstance(v, str) and v.strip():
            return v
    return ""


def to_workspace_relative(path: str, workspace: Path):
    """Normalize a tool-supplied path to workspace-root-relative.

    Obsidian tools already emit vault-relative paths (pass-through). Some
    adapter tools can emit ABSOLUTE paths; the policy globs are workspace-relative, so:
      - relative path        -> returned as-is (sans leading ``./``)
      - absolute under workspace -> relativized to the workspace root
      - absolute OUTSIDE workspace -> ``None``: the gate governs workspace zones only, so
        an external write (for example, a separate code repository) is
        not this hook's concern and is left to proceed."""
    if not path:
        return path
    p = path.replace("\\", "/")
    pp = Path(p)
    if not pp.is_absolute():
        return p[2:] if p.startswith("./") else p
    try:
        return str(pp.resolve().relative_to(workspace.resolve())).replace("\\", "/")
    except (ValueError, OSError):
        return None


def _audit_tool_policy_block(
    workspace: Path, actor: str, tool_name: str, payload: dict, reason: str
):
    action = classify(tool_name)
    if action is None:
        return
    path = to_workspace_relative(extract_path(payload.get("tool_input") or {}), workspace)
    extra = payload.get("extra") or {}
    request_id = extra.get("request_id") or ""
    if path is None or not path or not request_id:
        return
    try:
        from memoria_vault.runtime.policy.audit import append_audit
        from memoria_vault.runtime.time import now_iso

        append_audit(
            workspace,
            {
                "timestamp": now_iso(),
                "actor": actor,
                "action": action,
                "path": path,
                "request_id": request_id,
                "decision": "deny",
                "policy_rule": "tool-policy.allowlist",
                "message": reason,
            },
        )
    except Exception:  # noqa: BLE001 -- policy block itself already fails closed
        return


# --- pending-write stash (correlates the pre/post pair by tool_call_id) ------ #
def _stash_key(payload: dict) -> str:
    extra = payload.get("extra") or {}
    tcid = extra.get("tool_call_id")
    if tcid:
        return str(tcid)
    # Fallback when the runtime omits tool_call_id: request_id + path slug.
    request_id = extra.get("request_id") or "norequest"
    slug = extract_path(payload.get("tool_input") or {}).replace("/", "_") or "nopath"
    return f"{request_id}__{slug}"


def _pending_file(workspace: Path, key: str) -> Path:
    return workspace / "system" / "logs" / ".pending" / f"{safe_filename(key)}.json"


def _prune_stale_pending(workspace: Path, max_age_s: float = 24 * 3600) -> None:
    """Opportunistically drop .pending/ stash files older than 24h.

    A stash with no matching post_tool_call (a crashed tool, a lost pair key)
    would otherwise accumulate forever. Cheap (one glob) and best-effort: this
    runs on the pre_tool_call hot path and must NEVER raise or block a write."""
    try:
        cutoff = time.time() - max_age_s
        for f in (workspace / "system" / "logs" / ".pending").glob("*.json"):
            try:
                if f.stat().st_mtime < cutoff:
                    f.unlink()
            except OSError:
                continue
    except Exception:  # noqa: S110, BLE001
        pass


def evaluate_pre(payload: dict, actor: str, workspace: Path) -> dict:
    """pre_tool_call: gate the write. Returns {} (allow) or a block dict.

    Side effect on allow: stashes before_hash so the post_tool_call pass can
    complete the reversibility record. Pure enough to unit-test otherwise."""
    _prune_stale_pending(workspace)  # opportunistic; never raises
    tool_name = payload.get("tool_name", "")
    t = (tool_name or "").lower()
    if "obsidian" in t and any(d in t for d in DENY_OBSIDIAN):
        return {
            "decision": "block",  # hard deny -> never reaches actor policy
            "reason": f"policy gate: '{tool_name}' is not permitted for any actor "
            f"(arbitrary command execution / destructive op has no path to gate).",
        }
    base = t.rsplit("__", 1)[-1].rsplit(".", 1)[-1]  # strip server/toolset prefix
    if base in DENY_DIRECT_TOOLS:
        return {
            "decision": "block",  # direct tool escape -> fail closed
            "reason": f"policy gate: '{tool_name}' is direct or unaudited external access -- "
            f"adapter agents must use approved workspace tools; no actor is "
            f"permitted this toolset.",
        }
    tool_policy_block = _tool_policy_block(tool_name, actor, workspace)
    if tool_policy_block is not None:
        _audit_tool_policy_block(workspace, actor, tool_name, payload, tool_policy_block["reason"])
        return tool_policy_block
    action = classify(tool_name)
    if action is None:
        return {}  # read / terminal / ungated tool -> not our concern

    path = to_workspace_relative(extract_path(payload.get("tool_input") or {}), workspace)
    if path is None:
        return {}  # file write outside the workspace -> gate governs workspace zones only
    extra = payload.get("extra") or {}
    request_id = extra.get("request_id") or ""

    # Fail closed on our own decision: a write we can't identify is blocked.
    if not actor or not path or not request_id:
        return {
            "decision": "block",
            "reason": f"policy gate: cannot evaluate '{payload.get('tool_name')}' "
            f"(missing {'actor' if not actor else 'path' if not path else 'request_id'}) "
            f"-- blocked fail-closed.",
        }

    try:
        from memoria_vault.runtime.policy import PolicyEngine
    except Exception as exc:  # noqa: BLE001
        return {
            "decision": "block",
            "reason": f"policy gate unavailable ({exc}) -- write blocked fail-closed.",
        }

    resp = PolicyEngine(workspace).check(
        actor, action, path, request_id, reason=f"adapter:{payload.get('tool_name')}"
    )
    decision = resp.get("decision")
    rule = resp.get("policy_rule", "")
    if decision in ("allow", "allow_with_log"):
        # Stash before_hash for the post pass to pair with after_hash.
        before = resp.get("before_hash")
        if before is not None:
            pend = _pending_file(workspace, _stash_key(payload))
            pend.parent.mkdir(parents=True, exist_ok=True)
            pend.write_text(json.dumps({"before_hash": before, "path": path}), encoding="utf-8")
        return {}
    if decision == "dry_run":
        return {
            "decision": "block",
            "reason": f"review-gated ({rule}): write to '{path}' must be human-approved "
            f"-- surface as an attention item; do not write directly.",
        }
    return {
        "decision": "block",  # deny / anything unexpected
        "reason": f"policy {decision} ({rule}): "
        f"{resp.get('message') or f'write to {path!r} not permitted for {actor}'}",
    }


def evaluate_post(payload: dict, actor: str, workspace: Path) -> dict:
    """post_tool_call: complete the audit record with after_hash, then clean up.

    Post hooks never block (they can only allow/inject), so this always returns
    {}. It only acts when a matching pre-stash exists (i.e. an allowed write);
    reads and blocked writes leave no stash and are no-ops."""
    pend = _pending_file(workspace, _stash_key(payload))
    if not pend.is_file():
        return {}  # read, denied write, or unmatched -> nothing to complete
    try:
        stashed = load_json(pend)
    except (json.JSONDecodeError, OSError):
        return {}

    action = classify(payload.get("tool_name", "")) or "write"
    path = to_workspace_relative(
        extract_path(payload.get("tool_input") or {}), workspace
    ) or stashed.get("path", "")
    extra = payload.get("extra") or {}
    request_id = extra.get("request_id") or ""
    if not request_id:
        try:
            pend.unlink()
        except OSError:
            pass
        return {}

    try:
        from memoria_vault.runtime.policy import EMPTY_SHA256, PolicyEngine

        PolicyEngine(workspace).complete_write(
            actor, action, path, request_id, stashed.get("before_hash", EMPTY_SHA256)
        )
    except Exception as exc:  # noqa: BLE001
        # Never break the adapter loop on the audit-completion path, but always
        # log the failure to stderr so it is diagnosable.
        print(
            f"[policy_hook] audit completion failed for {actor}/{path}: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        try:
            record_event(
                component="adapter.policy_hook",
                level="error",
                code="audit_completion_failed",
                details={
                    "actor": actor,
                    "path": path,
                    "exception_type": type(exc).__name__,
                },
                vault_path=workspace,
            )
        except Exception:  # noqa: S110, BLE001
            pass
    finally:
        try:
            pend.unlink()
        except OSError:
            pass
    return {}


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--actor",
        default=os.environ.get("MEMORIA_POLICY_ACTOR", ""),
        help="workspace actor to enforce, for example adapter",
    )
    ap.add_argument(
        "--workspace",
        default=os.environ.get("MEMORIA_WORKSPACE", ""),
        help="workspace root; required unless MEMORIA_WORKSPACE is set",
    )
    args = ap.parse_args()
    if not args.workspace:
        print("[policy_hook] --workspace or MEMORIA_WORKSPACE is required", file=sys.stderr)
        print(json.dumps({"decision": "block", "reason": "policy gate: missing workspace"}))
        return

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"[policy_hook] malformed stdin payload: {exc}", file=sys.stderr)
        print(json.dumps({"decision": "block", "reason": "policy gate: malformed payload"}))
        return
    event = payload.get("hook_event_name", "pre_tool_call")
    handler = evaluate_post if event == "post_tool_call" else evaluate_pre
    print(json.dumps(handler(payload, args.actor, Path(args.workspace))))


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    main()
