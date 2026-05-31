# Policy MCP

The runtime write-gate that intercepts every vault action, checks lane-override rules, and returns a decision. Enforces lane permissions at the tool layer — not just as documentation. For why a runtime gate exists see [explanation/architecture/](../../explanation/architecture/).

## Decision protocol

Every vault action passes through `check_permission(profile, action, path, task_id, flags?)`. The `task_id` is required — the MCP cannot ask the worker which task it's running mid-decision.

| Decision | Meaning | Logged? |
| --- | --- | --- |
| `allow` | Action proceeds. | Only if lane's `policy.require` includes `audit_log`. |
| `allow_with_log` | Action proceeds. Audit entry mandatory. | Always. |
| `deny` | Action blocked. Worker must escalate or choose a different path. | Always. |
| `dry_run` | Action logged and reported but not performed. Worker escalates via board comment. | Always. |

**Two rules override lane configuration entirely:**

1. **Review-gated zones are never auto-written.** Writes to `30-synthesis/01-claims/`, `30-synthesis/02-reference/`, `30-synthesis/03-moc/`, and `50-deliverables/` degrade to `dry_run` regardless of the lane's `policy.allow` rules.
2. **Linter auto-fix is class-gated.** When `profile = memoria-linter` and `action = auto_fix`, the MCP requires `flags.class ∈ {safe-and-unambiguous, authorized-targeted}`. All other classes are `deny`.

## Action vocabulary

| Action | Default disposition |
| --- | --- |
| `read` | `allow` within `policy.allow.read`; `allow_with_log` for review-gated zones and cross-zone reads. |
| `write` | Governed by `policy.allow.write`. `dry_run` in review-gated zones. |
| `append` | `allow` for audit logs and session logs within the lane's own paths. |
| `move` | `allow_with_log` same-zone; `dry_run` cross-zone unless `flags.explicit_authorization`. |
| `delete` | `deny` by default for all profiles. Requires `flags.explicit_authorization` + `allow_with_log`. |
| `mkdir` | `allow` within `routing.write_scope`. |
| `auto_fix` | Class-gated via `flags.class` (Linter only). |
| `report` | Always `allow` within the worker's lane. |

## Skill-conditional policy

Skills can declare additive `policy.deny` rules in their `SKILL.md` frontmatter. Composition rules:

- **Deny is additive.** Lane denies + skill denies both apply. The narrower set wins.
- **Allow is a ceiling.** Skills cannot raise the lane's `policy.allow`. They can only carve from it.
- **Require is union.** Any `require` invariant from either the lane or the skill must hold.
- **Narrowing is one-way.** No tool call or nested skill load can override a deny rule the loaded skill brought in. Unloading the skill mid-session returns to lane-only policy, but does not retroactively change earlier decisions.

The one shipped restrictive skill is `counter-outline` (Writer-loaded), which narrows Writer's write scope to `40-workbench/*/02-framing/` only for the framing stage.

## Audit log entry shape

Each MCP decision appends one JSON object to `00-meta/02-logs/audit.jsonl`:

| Field | Notes |
| --- | --- |
| `ts` | ISO datetime of the decision. |
| `profile` | `memoria-<name>` |
| `action` | One of the eight actions above. |
| `path` | Vault path the action targeted. |
| `decision` | `allow`, `allow_with_log`, `deny`, or `dry_run`. |
| `policy_rule` | Which lane-override rule matched (for audit trail reconstruction). |
| `before_hash` | SHA-256 of the file before the write. |
| `after_hash` | SHA-256 after. |
| `task_id` | The Kanban card that triggered the action. |

The `before_hash` / `after_hash` chain must remain unbroken. `vault-hash-drift` fires if any link fails.

**SHA-256 rules:**

- The MCP computes hashes — workers never supply them.
- Always SHA-256, stored as `"sha256:<64-hex-chars>"` (algorithm is self-describing).
- Newly created files: `before_hash` = SHA-256 of empty byte string (`sha256:e3b0c4...`), not `null`.
- If the MCP cannot read the file to hash it (permissions error, race condition), the decision is `deny` — no hash, no allow.
- For `read` actions: `before_hash` only. For `deny` and `dry_run`: neither hash (no write occurred).

## Request/response JSON

**Request:**

```json
{
  "profile": "memoria-coder",
  "action": "write",
  "path": "40-workbench/project-x/06-code/main.py",
  "reason": "implement parser fix",
  "task_id": "TASK-2026-05-25-014",
  "flags": { "explicit_authorization": false, "proposed_only": false, "class": null }
}
```

`path` — vault-root-relative, forward slashes, no leading `./`. `reason` — short prose for the audit log.

**allow / allow_with_log response:**

```json
{ "decision": "allow", "policy_rule": "Coder.write.40-workbench-code", "log_required": false }
```

**deny response:**

```json
{ "decision": "deny", "policy_rule": "Writer.deny.30-synthesis-claims", "message": "..." }
```

**dry_run response:**

```json
{ "decision": "dry_run", "policy_rule": "review_gated.dry_run", "message": "..." }
```

## Relationship to Hermes Tirith

Two coexisting policy layers:

| Layer | Scope | Owner |
| --- | --- | --- |
| **Hermes Tirith** | Which *tools* a profile may call | Hermes-side, per-profile, runtime-internal |
| **Memoria policy MCP** | What each call may *write to disk* | Memoria-side, per-lane via lane-override YAML |

An unexpected `deny` is a Memoria-side question: check the lane-override YAML, then the audit log. A Tirith rejection (tool call blocked entirely) is a Hermes-side question. The two failure modes are distinct.

Because the policy MCP contract is self-contained, Memoria works against any MCP-capable agent runtime — not only Hermes.

## Related

- Lane-override YAML: [explanation/profiles/README.md](../../explanation/profiles/README.md)
- Linter auto-fix classes: [explanation/profiles/linter.md](../../explanation/profiles/linter.md)
- Audit-log dashboard: [explanation/dashboards/](../../explanation/dashboards/)
