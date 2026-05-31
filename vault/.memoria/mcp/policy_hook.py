#!/usr/bin/env python3
"""Hermes pre_tool_call hook -- route obsidian-MCP vault writes through the policy gate.

The policy MCP (policy_mcp.py) can *decide* whether a write is allowed, but a
vanilla `mcp-obsidian` write tool doesn't call it. This hook closes that gap: it
runs *before* every matched obsidian tool, maps the tool to a policy action, asks
the same tested decision core, and BLOCKS denied / review-gated writes by printing
``{"decision": "block", "reason": ...}``. Allowed actions print ``{}`` (proceed).

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
        - matcher: "obsidian"          # regex on the tool name; catches obsidian_* writes
          command: "python {{VAULT_PATH}}/.memoria/mcp/policy_hook.py --profile memoria-<name>"
          timeout: 10
      post_tool_call:
        - matcher: "obsidian"
          command: "python {{VAULT_PATH}}/.memoria/mcp/policy_hook.py --profile memoria-<name>"
          timeout: 10

Wire protocol: hermes-agent.nousresearch.com/docs/user-guide/features/hooks
  stdin  : {"tool_name","tool_input","session_id","cwd","extra":{"task_id",...}}
  stdout : {} to allow; {"decision":"block","reason":"..."} to block.

LIMITATION (documented): Hermes fails *open* on hook errors (non-zero exit /
malformed JSON are logged but never abort the loop), so this gate cannot be
truly fail-closed at the Hermes layer. It fails closed on its own decisions --
an unresolvable write (missing profile/path/task_id, or policy import failure)
is blocked -- which is the strongest guarantee a hook can give. For hard
enforcement, front the writes with a custom obsidian bridge that calls policy
internally (see docs/project/implementation-status.md).

    python policy_hook.py --profile memoria-writer    # reads one JSON event on stdin
    python policy_hook.py --self-test                 # synthetic-event unit tests
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

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
PATH_KEYS = ("filepath", "path", "file", "target", "filename", "dest", "destination")


def classify(tool_name: str) -> str | None:
    """Policy action for an obsidian *write* tool, or None for reads / non-obsidian."""
    t = (tool_name or "").lower()
    if "obsidian" not in t:
        return None
    for kw, action in WRITE_KEYWORDS.items():
        if kw in t:
            return action
    return None


def extract_path(tool_input: dict) -> str:
    for k in PATH_KEYS:
        v = (tool_input or {}).get(k)
        if isinstance(v, str) and v.strip():
            return v
    return ""


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
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in key)
    return vault / "00-meta" / "02-logs" / ".pending" / f"{safe}.json"


def evaluate_pre(payload: dict, profile: str, vault: Path) -> dict:
    """pre_tool_call: gate the write. Returns {} (allow) or a block dict.

    Side effect on allow: stashes before_hash so the post_tool_call pass can
    complete the reversibility record. Pure enough to unit-test otherwise."""
    action = classify(payload.get("tool_name", ""))
    if action is None:
        return {}                                  # not an obsidian write -> not our concern

    path = extract_path(payload.get("tool_input") or {})
    extra = payload.get("extra") or {}
    task_id = extra.get("task_id") or payload.get("session_id") or ""

    # Fail closed on our own decision: a write we can't identify is blocked.
    if not profile or not path or not task_id:
        return {"decision": "block",
                "reason": f"policy gate: cannot evaluate '{payload.get('tool_name')}' "
                          f"(missing {'profile' if not profile else 'path' if not path else 'task_id'}) "
                          f"-- blocked fail-closed."}

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import policy_mcp                            # reuse the tested decision core
    except Exception as exc:                         # import failure -> block the write
        return {"decision": "block",
                "reason": f"policy gate unavailable ({exc}) -- write blocked fail-closed."}

    resp = policy_mcp.PolicyEngine(vault).check(
        profile, action, path, task_id, reason=f"obsidian:{payload.get('tool_name')}")
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
        return {"decision": "block",
                "reason": f"review-gated ({rule}): write to '{path}' must be human-approved "
                          f"-- surface as a board comment; do not write directly."}
    return {"decision": "block",                     # deny / anything unexpected
            "reason": f"policy {decision} ({rule}): "
                      f"{resp.get('message') or f'write to {path!r} not permitted for {profile}'}"}


def evaluate_post(payload: dict, profile: str, vault: Path) -> dict:
    """post_tool_call: complete the audit record with after_hash, then clean up.

    Post hooks never block (they can only allow/inject), so this always returns
    {}. It only acts when a matching pre-stash exists (i.e. an allowed write);
    reads and blocked writes leave no stash and are no-ops."""
    pend = _pending_file(vault, _stash_key(payload))
    if not pend.is_file():
        return {}                                   # read, denied write, or unmatched -> nothing to complete
    try:
        stashed = json.loads(pend.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    action = classify(payload.get("tool_name", "")) or "write"
    path = extract_path(payload.get("tool_input") or {}) or stashed.get("path", "")
    extra = payload.get("extra") or {}
    task_id = extra.get("task_id") or payload.get("session_id") or ""

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import policy_mcp
        policy_mcp.PolicyEngine(vault).complete_write(
            profile, action, path, task_id, stashed.get("before_hash", policy_mcp.EMPTY_SHA256))
    except Exception:
        pass                                        # never break the loop on the audit-completion path
    finally:
        try:
            pend.unlink()
        except OSError:
            pass
    return {}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", default=os.environ.get("HERMES_PROFILE", ""),
                    help="profile whose lane to enforce (e.g. memoria-writer)")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(1 if self_test() else 0)

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        print("{}")                                  # malformed event: let Hermes proceed
        return
    event = payload.get("hook_event_name", "pre_tool_call")
    handler = evaluate_post if event == "post_tool_call" else evaluate_pre
    print(json.dumps(handler(payload, args.profile, vault_root())))


# --------------------------------------------------------------------------- #
def self_test() -> int:
    import tempfile

    failures = 0

    def check(name: str, cond: bool) -> None:
        nonlocal failures
        failures += not cond
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")

    # classify / extract_path -------------------------------------------------
    check("classify: patch -> write", classify("obsidian_patch_content") == "write")
    check("classify: append -> append", classify("obsidian_append_content") == "append")
    check("classify: delete -> delete", classify("obsidian_delete_file") == "delete")
    check("classify: prefixed write matched", classify("mcp__obsidian__put_content") == "write")
    check("classify: read tool -> None", classify("obsidian_get_file_contents") is None)
    check("classify: search -> None", classify("obsidian_simple_search") is None)
    check("classify: non-obsidian -> None", classify("terminal") is None)
    check("extract_path: filepath", extract_path({"filepath": "20-sources/x.md"}) == "20-sources/x.md")

    # evaluate against a temp vault + real lane files -------------------------
    with tempfile.TemporaryDirectory() as td:
        # Build <vault>/.memoria/{lane-overrides,mcp}/ and copy policy_mcp.py in so
        # the hook's import + parents[2] vault resolution both work.
        vault = Path(td)
        lanes = vault / ".memoria" / "lane-overrides"
        lanes.mkdir(parents=True)
        (vault / ".memoria" / "mcp").mkdir(parents=True)
        import shutil
        shutil.copy(Path(__file__).resolve().parent / "policy_mcp.py",
                    vault / ".memoria" / "mcp" / "policy_mcp.py")
        (lanes / "writer.yaml").write_text(
            "profile: memoria-writer\npolicy:\n  allow:\n    write:\n"
            "      - \"10-inbox/02-answers/**\"\n      - \"30-synthesis/02-reference/**\"\n"
            "  deny:\n    write:\n      - \"30-synthesis/01-claims/**\"\n"
            "  require:\n    - audit_log\nrouting:\n  write_scope:\n    - \"10-inbox/02-answers/\"\n",
            encoding="utf-8")

        ev = lambda tool, path: evaluate_pre(
            {"tool_name": tool, "tool_input": {"filepath": path},
             "extra": {"task_id": "T1"}}, "memoria-writer", vault)

        check("read tool not gated -> {}", ev("obsidian_get_file_contents", "x.md") == {})
        check("allowed write -> {}", ev("obsidian_patch_content", "10-inbox/02-answers/a.md") == {})
        r_dry = ev("obsidian_patch_content", "30-synthesis/02-reference/r.md")
        check("review-gated write -> block", r_dry.get("decision") == "block" and "review-gated" in r_dry["reason"])
        r_deny = ev("obsidian_delete_file", "30-synthesis/01-claims/c.md")
        check("denied write -> block", r_deny.get("decision") == "block")
        # missing task_id -> fail-closed block
        r_fc = evaluate_pre({"tool_name": "obsidian_patch_content",
                             "tool_input": {"filepath": "10-inbox/02-answers/a.md"}},
                            "memoria-writer", vault)
        check("missing task_id -> fail-closed block", r_fc.get("decision") == "block")

        # pre -> post reversibility roundtrip (paired before/after hash) ------
        (vault / "10-inbox" / "02-answers").mkdir(parents=True, exist_ok=True)
        ev_payload = {"tool_name": "obsidian_put_content",
                      "tool_input": {"filepath": "10-inbox/02-answers/round.md"},
                      "extra": {"task_id": "T9", "tool_call_id": "call-xyz"}}
        pre = evaluate_pre(ev_payload, "memoria-writer", vault)
        stash = _pending_file(vault, _stash_key(ev_payload))
        check("pre allow stashes before_hash", pre == {} and stash.is_file())
        # the tool "runs": the file now exists with content
        (vault / "10-inbox" / "02-answers" / "round.md").write_text("answer body", encoding="utf-8")
        post = evaluate_post(ev_payload, "memoria-writer", vault)
        audit_lines = (vault / "00-meta" / "02-logs" / "audit.jsonl").read_text(encoding="utf-8").splitlines()
        completes = [json.loads(l) for l in audit_lines if json.loads(l).get("decision") == "write_complete"]
        check("post returns {} (never blocks)", post == {})
        check("post appended a write_complete record", len(completes) == 1)
        check("write_complete pairs before+after", bool(completes and completes[0]["before_hash"] and completes[0]["after_hash"] and completes[0]["before_hash"] != completes[0]["after_hash"]))
        check("post cleaned up the stash", not stash.is_file())

    print(f"\n{'OK' if not failures else 'FAILED'}: {failures} failing check(s).")
    return failures


if __name__ == "__main__":
    main()
