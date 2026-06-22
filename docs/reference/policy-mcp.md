---
title: Policy MCP
parent: Reference
---

# Policy MCP

The runtime write-gate (`src/.memoria/mcp/policy_mcp.py`): it intercepts every vault action, checks the lane-override rules, and returns a decision before any content reaches disk. The stable deployed entrypoint is `policy_mcp.py`; the behavior-preserving core is split under `memoria.runtime.policy` (`model`, `paths`, `lanes`, `decision`, `audit`, and `engine`), with the MCP tools wrapped by `src/.memoria/mcp/policy_server.py`. Every rule lives in a versioned lane-override file — the gate is not a substitute for the review gate, not a content checker, and not a hidden controller.

---

## Request flow

```text
Hermes profile
  → tool call (write / move / delete / auto_fix)
    → Policy MCP
      → profile lookup in lane-override file
      → path + action evaluation
      → allow | allow_with_log | deny | dry_run
      → filesystem execution or diff report
```

Every request carries complete identity and task metadata. `task_id` is required — the MCP cannot ask the worker mid-decision which task it is running. A missing `task_id` or a path-traversal attempt (`..` escaping the vault root) is denied and audited.

---

## Action vocabulary

Eight guarded actions; `read` and `report` are non-mutating, the rest are subject to the review-gated `dry_run` rule.

| Action | Default disposition |
| --- | --- |
| `read` | Default-allow; `allow_with_log` in review-gated zones; an explicit `deny.read` wins. |
| `write` / `append` | `deny.write` wins; else `allow.write` → allow; else **default-deny**. `dry_run` in review-gated zones. |
| `move` | As write, and always `allow_with_log` when allowed. |
| `delete` | `deny` unless `flags.explicit_authorization` (then `allow_with_log`, within the lane's write globs); review-gated → `dry_run`. |
| `mkdir` | `allow` within `routing.write_scope`, else `deny`. |
| `auto_fix` | Class-gated via `flags.class` (see [Auto-fix policy](#auto-fix-policy)). |
| `report` | Always `allow` within the worker's lane. |

A skill loaded for the session can only **narrow**: its `policy.deny.write` patterns are composed additively onto the lane (one-way for the session; checked before everything but action validity).

---

## Decision values

| Decision | Meaning | Logged? |
| --- | --- | --- |
| `allow` | Action proceeds. | Only if the lane's `policy.require` includes `audit_log` (every shipped lane does). |
| `allow_with_log` | Action proceeds; audit entry mandatory. | Always. |
| `deny` | Action blocked; worker must escalate or choose a different path. | Always. |
| `dry_run` | Action logged and reported but not performed; the worker surfaces it as a board comment. | Always. |

**Two rules override lane configuration entirely:**

1. **Review-gated zones are never auto-written.** The gated prefixes are loaded from `src/.memoria/schemas/folders.yaml` (`gated_prefixes`) — currently `notes/claims/` and `notes/hubs/`. The dependency-free fallback tuple in `memoria.runtime.policy.paths` mirrors them (test-enforced to stay in sync). An otherwise-allowed mutating action there degrades to `dry_run` regardless of the lane's `policy.allow`. No profile can bypass this.
2. **Auto-fix is class-gated.** Only `flags.class ∈ {safe-and-unambiguous, authorized-targeted}` may proceed; `schema-content` is pinned to `dry_run` and `review-gated-edit` to `deny`, regardless of who asks.

---

## Request contract

```json
{
  "profile": "memoria-writer",
  "action": "write",
  "path": "projects/project-x/drafts/chapter-1.md",
  "reason": "draft synthesis from claim notes",
  "task_id": "TASK-2026-05-31-007",
  "flags": {
    "explicit_authorization": false,
    "class": null
  }
}
```

| Field | Required | Notes |
| --- | --- | --- |
| `profile` | yes | Must match a lane-override file (`memoria-writer` → `writer.yaml`). |
| `action` | yes | One of the eight actions above. |
| `path` | yes | Vault-root-relative, forward slashes; normalized (no `./`, no `..`) before evaluation. |
| `reason` | no | Short prose for the audit log. |
| `task_id` | yes | The board card that triggered the action. Required on every request. |
| `flags.explicit_authorization` | no | Required for `delete`; forces `allow_with_log` on writes. |
| `flags.class` | no | Required for `auto_fix`. |

Debugging an unexpected deny is a one-shot CLI away (the lane-override says what the rule is; the audit log says what was decided):

```bash
python3 .memoria/mcp/policy_mcp.py --vault <vault> \
  --decide '{"profile":"memoria-librarian","action":"write","path":"catalog/papers/x.md","task_id":"T1"}'
```

---

## Response contract

Allow:

```json
{ "decision": "allow", "policy_rule": "Librarian.write.catalog", "log_required": true }
```

Deny:

```json
{ "decision": "deny", "policy_rule": "Librarian.deny.write", "message": "memoria-librarian is denied write to 'notes/claims/x.md'" }
```

Dry-run:

```json
{ "decision": "dry_run", "policy_rule": "review_gated.dry_run", "message": "review-gated zone write requires approval — surface as board comment" }
```

On an allowed mutating action the response also carries `before_hash`; the worker calls `complete_write` after the write so the paired `after_hash` lands in the audit trail as a separate `write_complete` record (see [Audit log format](#audit-log-format)).

### Tools

| Tool | Does |
| --- | --- |
| `check_permission(profile, action, path, task_id, reason, flags)` | The decision entry point. |
| `complete_write(profile, action, path, task_id, before_hash)` | Records the post-write `after_hash` (reversibility / tamper trail). |
| `set_session_skill(task_id, skill_policy)` / `clear_session_skill(task_id)` | Register / drop a loaded skill's one-way deny narrowing. |

---

## Audit log format

The full audit-log schema, JSON example, decision enum, and per-write SHA-256 hash-pairing rules live in [Policy audit log](policy-audit-log.md).

## Auto-fix policy

The auto-fix classes and their dispositions live in [Policy auto-fix](policy-auto-fix.md).

## The five lane-overrides

The policy manifest for each profile lives in `src/.memoria/lane-overrides` — `copi.yaml`, `librarian.yaml`, `writer.yaml`, `peer-reviewer.yaml`, `engineer.yaml`. Shape:

```yaml
profile: memoria-librarian

policy:
  allow:
    skills: [obsidian, qmd]
    write:
      - "inbox/**"
      - "catalog/**"
      - "notes/fleeting/**"
      - "notes/sources/**"
  deny:
    skills: [review_gated_publish, destructive_shell]
    write:
      - "notes/claims/**"
      - "notes/hubs/**"
  require:
    - audit_log
    - timeout_required
    - source_tracking

routing:
  invocation: dispatched
  external_api_policy: explicit_only
  write_scope:
    - "inbox/"
    - "catalog/"
    - "notes/fleeting/"
    - "notes/sources/"
```

`policy.deny` wins over `policy.allow`; an unmatched path is default-denied. The Co-PI's override is the limiting case: `allow.write: []` plus `deny.write: "**"` — the structural guarantee behind "read directly, delegate writes". The full scope table is in [Profile capabilities](profiles.md).

One consequence worth naming: every shipped lane denies writes under `system/**` (the Co-PI under `**`), and no lane's `allow.write`, `routing.write_scope`, or auto-fix scope reaches into `system/` — so no profile can mutate `system/templates/` (or any other system file) through the gate, for any action: write, append, move, delete (even with `explicit_authorization`, the scope check denies), mkdir, auto_fix. Accidental *human* overwrites of system files are the golden copy's job — drift detection plus `lint:restore`, see [Linter: detectors and auto-fix](linter.md#the-golden-copy).

Globs use doublestar semantics: `**` crosses path segments, `*` stays within one, `?` matches one non-`/` character.

---

## Enforcement: the policy-gate plugin

`check_permission` only decides — the bridge that actually stops a write is the **`memoria-policy-gate` Hermes plugin** (deployed per profile by the installer; it reuses `src/.memoria/mcp/policy_hook.py`'s decision core):

- **`pre_tool_call`** maps the obsidian tool to a policy action, calls the decision core, and blocks on `deny`/`dry_run`; on an allowed write it stashes the `before_hash`. **Fail-closed:** any error inside the gate blocks.
- **`post_tool_call`** computes `after_hash` and appends the paired `write_complete` audit record.

It is a Python plugin, not a shell hook ([ADR-28](../adr/28-write-gate-as-plugin.md)): Hermes registers MCP tools as `mcp_<server>_<tool>`, shell hooks are consent-gated and fail-open — the plugin runs in-process in every mode, matches in Python, receives the `task_id`, and is fail-closed. The hook also hard-denies the native `vault_delete`/`vault_move` and `command_execute` (no path to gate). The per-profile positive `platform_toolsets` allowlist ([ADR-27](../adr/27-hermes-native-config-and-gate-enforcement.md)) makes the gated obsidian MCP the only write path on the non-Engineer lanes. ACP can still expose direct Hermes fallback tools, so the plugin also hard-denies direct-world/history tools, allows Hermes `memory` only for the Co-PI, and denies `session_search` everywhere. The broader tool capability registry is documented in [Profile capabilities](profiles.md#capability-allowlist): today it is a checked source-of-truth contract, while runtime enforcement is the rendered profile toolset configuration plus the fail-closed Obsidian write gate.

---

## Related

- The lane ceilings in table form: [Profile capabilities](profiles.md)
- Audit-log substrate and retention: [Memory substrates](memory.md)
- The ceiling check on delegation payloads: [Kanban board reference](kanban-board.md)
- The gated folder map's single source: [Note types](note-types.md)
