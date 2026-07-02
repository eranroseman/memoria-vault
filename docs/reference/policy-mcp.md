---
title: Policy MCP
parent: Agents and control
grand_parent: Reference
---

# Policy MCP

The alpha.14 write boundary is the standalone CLI/engine: operation manifests,
request rows, staging, checks, promotion, and journal entries control machine
mutations. `vault-template/.memoria/mcp/policy_mcp.py` remains as an optional
adapter shim for tools that still need a pre-write decision API.

The template does **not** ship lane overrides. If an adapter calls the Policy MCP
without an operator-supplied `.memoria/lane-overrides/<lane>.yaml`, the decision
fails closed with `policy_rule: lane.load-error`.

## Request Flow

```text
optional adapter tool call
  -> Policy MCP
     -> load operator-supplied lane policy, if present
     -> normalize path and action
     -> allow | allow_with_log | deny | dry_run
     -> adapter executes or blocks
```

Every request carries complete identity and task metadata. `task_id` is required.
A missing `task_id` or a path-traversal attempt (`..` escaping the vault root) is
denied and audited.

## Action Vocabulary

| Action | Default disposition |
| --- | --- |
| `read` | Default-allow unless explicitly denied. |
| `write` / `append` | `deny.write` wins; else `allow.write` -> allow; else default-deny. |
| `move` | As write, and always `allow_with_log` when allowed. |
| `delete` | Deny unless `flags.explicit_authorization` and the path is inside scope. |
| `mkdir` | Allow within `routing.write_scope`, else deny. |
| `auto_fix` | Class-gated by `flags.class`. |
| `report` | Non-mutating report action. |

A loaded skill policy can only narrow the lane by adding deny globs for the
session.

## Request Contract

```json
{
  "profile": "memoria-writer",
  "action": "write",
  "path": "knowledge/projects/project-x/drafts/chapter-1.md",
  "reason": "draft synthesis from checked notes",
  "task_id": "TASK-2026-05-31-007",
  "flags": {
    "explicit_authorization": false,
    "class": null
  }
}
```

| Field | Required | Notes |
| --- | --- | --- |
| `profile` | yes | Adapter profile/lane id. It must resolve to an operator-supplied lane policy when the shim is used. |
| `action` | yes | One of the actions above. |
| `path` | yes | Vault-root-relative, forward slashes; normalized before evaluation. |
| `reason` | no | Short prose for the audit log. |
| `task_id` | yes | The request/card/session that triggered the action. |
| `flags.explicit_authorization` | no | Required for privileged deletes. |
| `flags.class` | no | Required for `auto_fix`. |

Debug a decision with:

```bash
python3 .memoria/mcp/policy_mcp.py --vault <workspace> \
  --decide '{"profile":"memoria-writer","action":"write","path":"knowledge/projects/x/draft.md","task_id":"T1"}'
```

## Response Contract

Allow:

```json
{ "decision": "allow", "policy_rule": "Writer.write.projects", "log_required": true }
```

Deny:

```json
{ "decision": "deny", "policy_rule": "lane.load-error", "message": "no lane-override for profile 'memoria-writer'" }
```

Dry-run:

```json
{ "decision": "dry_run", "policy_rule": "review_gated.dry_run", "message": "review-gated Concept write requires worker promotion" }
```

On an allowed mutating action, the response also carries `before_hash`. The
adapter calls `complete_write` after the write so the paired `after_hash` lands
in the audit trail as a separate `write_complete` record.

## Tools

| Tool | Does |
| --- | --- |
| `check_permission(profile, action, path, task_id, reason, flags)` | Decision entry point. |
| `complete_write(profile, action, path, task_id, before_hash)` | Records the post-write `after_hash`. |
| `set_session_skill(task_id, skill_policy)` / `clear_session_skill(task_id)` | Register or clear one-way session narrowing. |

## Audit Log

The full audit-log schema, JSON example, decision enum, and per-write SHA-256
hash-pairing rules live in [Policy audit log](policy-audit-log.md).

## Related

- Current CLI/engine command surface: [CLI](cli.md)
- Operation allowlists: [Operations](operations.md)
- No installed profile packages: [Installed profiles](profile-capabilities.md)
