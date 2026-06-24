#!/usr/bin/env python3
"""Hermes pre_tool_call hook -- route vault writes through the policy gate.

The policy MCP (policy_mcp.py) can *decide* whether a write is allowed, but the
write tools don't call it. This hook closes that gap: it runs *before* every
matched tool, maps the tool to a policy action, asks the same tested decision
core, and BLOCKS denied / review-gated writes by printing
``{"decision": "block", "reason": ...}``. Allowed actions print ``{}`` (proceed).

The sandbox model is policy-via-MCP, MCP-only (D40/ADR-46): agents reach the
vault, operations, and external APIs ONLY through MCP servers. Accordingly:
  - the `obsidian` MCP write tools (every profile's one vault-write path) are
    PATH-GATED -- mapped to a policy action and decided by the lane policy; and
  - every direct-capability tool (`file`, `terminal`, code-exec families plus
    unaudited egress / messaging / browser / computer-use / media families --
    DENY_DIRECT_TOOLS) is HARD-DENIED for every lane. No Memoria profile ships
    those toolsets in `platform_toolsets` (and `agent.disabled_toolsets` strips
    known direct-world fallbacks); a call reaching us anyway means config drift
    or prompt injection, so the gate fails closed rather than trusting the
    capability layer.
The capability layer is the first wall; this hook is the second, in-process one.

This one script handles BOTH the gate and the audit completion, branching on
`hook_event_name`:
  - pre_tool_call  -> decide; block deny/dry_run; on allow, stash before_hash.
  - post_tool_call -> read the stash, compute after_hash, append the paired
                      reversibility record (before+after) to audit.jsonl, clean up.

Registered PER PROFILE (the stdin payload carries no profile name) in each
profile's config.yaml -- {{VAULT_PATH}} is substituted by install.ps1, same
command for both events:

    hooks:
      pre_tool_call:
        - matcher: "obsidian.*"        # Hermes matches via re.fullmatch -> need .* to catch obsidian_* writes
          command: "python {{VAULT_PATH}}/.memoria/mcp/policy_hook.py --profile memoria-<name>"
          timeout: 10
      post_tool_call:
        - matcher: "obsidian.*"
          command: "python {{VAULT_PATH}}/.memoria/mcp/policy_hook.py --profile memoria-<name>"
          timeout: 10

Wire protocol: hermes-agent.nousresearch.com/docs/user-guide/features/hooks
  stdin  : {"tool_name","tool_input","session_id","cwd","extra":{"task_id",...}}
  stdout : {} to allow; {"decision":"block","reason":"..."} to block.

LIMITATION (documented): Hermes fails *open* on hook errors (non-zero exit /
malformed JSON are logged but never abort the loop), so this policy gate cannot be
truly fail-closed at the Hermes layer. It fails closed on its own decisions --
an unresolvable write (missing profile/path/task_id, or policy import failure)
is blocked -- which is the strongest guarantee a hook can give. For hard
enforcement, front the writes with a custom obsidian bridge that calls policy
internally.

    python policy_hook.py --profile memoria-writer    # reads one JSON event on stdin
"""

from __future__ import annotations

import argparse
import json
import os
import site
import sys
import time
from pathlib import Path


def _vault_site_packages() -> list[Path]:
    memoria_dir = Path(__file__).resolve().parents[1]
    venv = memoria_dir / ".venv"
    return [venv / "Lib" / "site-packages", *sorted((venv / "lib").glob("python*/site-packages"))]


def _bootstrap_vault_runtime_package() -> None:
    # The policy plugin runs in Hermes's Python, not the vault venv.
    for path in _vault_site_packages():
        if not path.is_dir():
            continue
        site.addsitedir(str(path))
        path_text = str(path)
        if path_text in sys.path:
            sys.path.remove(path_text)
        sys.path.insert(0, path_text)


_bootstrap_vault_runtime_package()

from _shared import load_json, safe_filename

from memoria.runtime.diagnostics import record_event

# obsidian (mcp-obsidian) tool-name keyword -> policy action. Matched by substring
# so it survives server prefixing (e.g. mcp__obsidian__patch_content). Read tools
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
# Direct-capability and unaudited-egress tools hard-denied for EVERY lane
# (D40/ADR-46: agents reach the vault, operations, and APIs ONLY through MCP —
# no exceptions). No Memoria profile ships these toolsets, so any such call is
# config drift or prompt-injection bypassing schema-hiding — fail closed.
# Bare tool names matched exactly so an unrelated tool merely containing "patch"
# is never caught. This list MUST cover every tool in Hermes's file/terminal/
# code_execution plus egress/side-effect toolsets; `hermes_contract_doctor.py`
# fails the build if the installed Hermes ships a covered tool this set is
# missing (drift), which is how `process` (terminal toolset) was caught.
DENY_DIRECT_TOOLS = frozenset(
    {
        "write_file",
        "patch",
        "read_file",
        "search_files",  # file toolset
        "terminal",
        "process",  # terminal toolset — sibling of `terminal`, runs/inspects processes
        "run_command",  # legacy/alias name (not in installed Hermes; harmless)
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

# Obsidian native-MCP tools hard-denied for EVERY lane. `command_execute` runs an
# arbitrary Obsidian command and has no single path to gate (so the path matcher
# can't bound it); `vault_delete`/`vault_move` are destructive ops the workflows
# don't need (least privilege -- the prior uvx mcp-obsidian exposed only
# read/write/append/patch). Matched as a substring after the `obsidian` prefix.
DENY_OBSIDIAN = ("command_execute", "vault_delete", "vault_move")


def _allowed_registry_tools(vault: Path, profile: str) -> set[str]:
    import yaml

    path = vault / ".memoria" / "tool-registry.yaml"
    registry = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    groups = registry["groups"]
    allow = registry["profiles"][profile]["allow"]
    out: set[str] = set()
    for entry in allow:
        out.update(str(tool).lower() for tool in groups.get(entry, [entry]))
    return out


def _tool_candidates(tool_name: str, allowed: set[str]) -> set[str]:
    t = (tool_name or "").lower()
    candidates = {t}
    if not t.startswith("mcp_"):
        candidates.add(t.rsplit("__", 1)[-1].rsplit(".", 1)[-1])
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


def _registry_block(tool_name: str, profile: str, vault: Path) -> dict | None:
    try:
        allowed = _allowed_registry_tools(vault, profile)
    except Exception as exc:  # noqa: BLE001 -- missing/invalid registry must fail closed
        return {
            "decision": "block",
            "reason": f"policy gate: tool registry unavailable for {profile} ({exc}) -- blocked fail-closed.",
        }
    if _tool_candidates(tool_name, allowed).isdisjoint(allowed):
        return {
            "decision": "block",
            "reason": f"policy gate: '{tool_name}' is outside {profile}'s tool-registry allowlist.",
        }
    return None


def classify(tool_name: str) -> str | None:
    """Policy action for a gated *write* tool, or None for reads / ungated tools.

    Two families: obsidian MCP writes (substring match, survives prefixing) and
    Hermes `file` toolset writes (exact base-name match). Everything else --
    reads, and crucially the `terminal` toolset -- returns None (not gated here)."""
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


def to_vault_relative(path: str, vault: Path):
    """Normalize a tool-supplied path to vault-root-relative (forward slashes).

    Obsidian tools already emit vault-relative paths (pass-through). The `file`
    toolset can emit ABSOLUTE paths; the policy lane globs are vault-relative, so:
      - relative path        -> returned as-is (sans leading ``./``)
      - absolute under vault -> relativized to the vault root
      - absolute OUTSIDE vault -> ``None``: the gate governs vault zones only, so
        an external write (e.g. the Engineer committing to a repo outside the vault) is
        not this hook's concern and is left to proceed."""
    if not path:
        return path
    p = path.replace("\\", "/")
    pp = Path(p)
    if not pp.is_absolute():
        return p[2:] if p.startswith("./") else p
    try:
        return str(pp.resolve().relative_to(vault.resolve())).replace("\\", "/")
    except (ValueError, OSError):
        return None


def vault_root() -> Path:
    # <vault>/.memoria/mcp/policy_hook.py -> parents[2] == <vault>
    return Path(__file__).resolve().parents[2]


# --- pending-write stash (correlates the pre/post pair by tool_call_id) ------ #
def _stash_key(payload: dict) -> str:
    extra = payload.get("extra") or {}
    tcid = extra.get("tool_call_id")
    if tcid:
        return str(tcid)
    # Fallback when the runtime omits tool_call_id: task_id + path slug.
    task_id = extra.get("task_id") or payload.get("session_id") or "notask"
    slug = extract_path(payload.get("tool_input") or {}).replace("/", "_") or "nopath"
    return f"{task_id}__{slug}"


def _pending_file(vault: Path, key: str) -> Path:
    return vault / "system" / "logs" / ".pending" / f"{safe_filename(key)}.json"


def _prune_stale_pending(vault: Path, max_age_s: float = 24 * 3600) -> None:
    """Opportunistically drop .pending/ stash files older than 24h.

    A stash with no matching post_tool_call (a crashed tool, a lost pair key)
    would otherwise accumulate forever. Cheap (one glob) and best-effort: this
    runs on the pre_tool_call hot path and must NEVER raise or block a write."""
    try:
        cutoff = time.time() - max_age_s
        for f in (vault / "system" / "logs" / ".pending").glob("*.json"):
            try:
                if f.stat().st_mtime < cutoff:
                    f.unlink()
            except OSError:
                continue
    except Exception:  # noqa: S110, BLE001
        pass


def evaluate_pre(payload: dict, profile: str, vault: Path) -> dict:
    """pre_tool_call: gate the write. Returns {} (allow) or a block dict.

    Side effect on allow: stashes before_hash so the post_tool_call pass can
    complete the reversibility record. Pure enough to unit-test otherwise."""
    _prune_stale_pending(vault)  # opportunistic; never raises
    tool_name = payload.get("tool_name", "")
    t = (tool_name or "").lower()
    if "obsidian" in t and any(d in t for d in DENY_OBSIDIAN):
        return {
            "decision": "block",  # hard deny -> never reaches a lane check
            "reason": f"policy gate: '{tool_name}' is not permitted for any lane "
            f"(arbitrary command execution / destructive op has no path to gate).",
        }
    base = t.rsplit("__", 1)[-1].rsplit(".", 1)[-1]  # strip server/toolset prefix
    if base in DENY_DIRECT_TOOLS:
        return {
            "decision": "block",  # MCP-only sandbox (D40) -> fail closed
            "reason": f"policy gate: '{tool_name}' is direct or unaudited external access -- "
            f"agents reach the vault only through MCP (D40/ADR-46); no lane "
            f"is permitted this toolset.",
        }
    registry_block = _registry_block(tool_name, profile, vault)
    if registry_block is not None:
        return registry_block
    action = classify(tool_name)
    if action is None:
        return {}  # read / terminal / ungated tool -> not our concern

    path = to_vault_relative(extract_path(payload.get("tool_input") or {}), vault)
    if path is None:
        return {}  # file write outside the vault -> gate governs vault zones only
    extra = payload.get("extra") or {}
    task_id = extra.get("task_id") or payload.get("session_id") or ""

    # Fail closed on our own decision: a write we can't identify is blocked.
    if not profile or not path or not task_id:
        return {
            "decision": "block",
            "reason": f"policy gate: cannot evaluate '{payload.get('tool_name')}' "
            f"(missing {'profile' if not profile else 'path' if not path else 'task_id'}) "
            f"-- blocked fail-closed.",
        }

    try:
        from memoria.runtime.policy import PolicyEngine
    except Exception as exc:  # noqa: BLE001
        return {
            "decision": "block",
            "reason": f"policy gate unavailable ({exc}) -- write blocked fail-closed.",
        }

    resp = PolicyEngine(vault).check(
        profile, action, path, task_id, reason=f"obsidian:{payload.get('tool_name')}"
    )
    decision = resp.get("decision")
    rule = resp.get("policy_rule", "")
    if decision in ("allow", "allow_with_log"):
        # Stash before_hash for the post pass to pair with after_hash.
        before = resp.get("before_hash")
        if before is not None:
            pend = _pending_file(vault, _stash_key(payload))
            pend.parent.mkdir(parents=True, exist_ok=True)
            pend.write_text(json.dumps({"before_hash": before, "path": path}), encoding="utf-8")
        return {}
    if decision == "dry_run":
        return {
            "decision": "block",
            "reason": f"review-gated ({rule}): write to '{path}' must be human-approved "
            f"-- surface as a board comment; do not write directly.",
        }
    return {
        "decision": "block",  # deny / anything unexpected
        "reason": f"policy {decision} ({rule}): "
        f"{resp.get('message') or f'write to {path!r} not permitted for {profile}'}",
    }


def evaluate_post(payload: dict, profile: str, vault: Path) -> dict:
    """post_tool_call: complete the audit record with after_hash, then clean up.

    Post hooks never block (they can only allow/inject), so this always returns
    {}. It only acts when a matching pre-stash exists (i.e. an allowed write);
    reads and blocked writes leave no stash and are no-ops."""
    pend = _pending_file(vault, _stash_key(payload))
    if not pend.is_file():
        return {}  # read, denied write, or unmatched -> nothing to complete
    try:
        stashed = load_json(pend)
    except (json.JSONDecodeError, OSError):
        return {}

    action = classify(payload.get("tool_name", "")) or "write"
    path = to_vault_relative(extract_path(payload.get("tool_input") or {}), vault) or stashed.get(
        "path", ""
    )
    extra = payload.get("extra") or {}
    task_id = extra.get("task_id") or payload.get("session_id") or ""

    try:
        from memoria.runtime.policy import EMPTY_SHA256, PolicyEngine

        PolicyEngine(vault).complete_write(
            profile, action, path, task_id, stashed.get("before_hash", EMPTY_SHA256)
        )
    except Exception as exc:  # noqa: BLE001
        # Never break the agent loop on the audit-completion path, but always
        # log the failure to stderr so it is diagnosable in Hermes logs.
        print(
            f"[policy_hook] audit completion failed for {profile}/{path}: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        try:
            record_event(
                component="mcp.policy_hook",
                level="error",
                code="audit_completion_failed",
                details={
                    "profile": profile,
                    "path": path,
                    "exception_type": type(exc).__name__,
                },
                vault_path=vault,
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
        "--profile",
        default=os.environ.get("HERMES_PROFILE", ""),
        help="profile whose lane to enforce (e.g. memoria-writer)",
    )
    args = ap.parse_args()

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"[policy_hook] malformed stdin payload: {exc}", file=sys.stderr)
        print("{}")  # let Hermes proceed
        return
    event = payload.get("hook_event_name", "pre_tool_call")
    handler = evaluate_post if event == "post_tool_call" else evaluate_pre
    print(json.dumps(handler(payload, args.profile, vault_root())))


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    main()
