---
topic: reference
---

# Policy MCP

The policy MCP sits between Hermes profiles and the vault. It intercepts every vault write, evaluates it against the requesting profile's declared permissions, and returns one of four decisions before any content reaches disk. For the design rationale see [explanation/architecture/why-human-gate.md](../explanation/architecture/why-human-gate.md).

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

---

## Action vocabulary

| Action | What it covers |
|---|---|
| `read` | Any vault file read |
| `write` | Create or overwrite a file |
| `append` | Append to an existing file |
| `move` | Relocate a file within the vault |
| `delete` | Remove a file |
| `mkdir` | Create a directory |
| `auto_fix` | Structural repair (separate class — see auto-fix policy below) |
| `report` | Emit a dry-run diff without touching the filesystem |

---

## Decision values

| Decision | Meaning |
|---|---|
| `allow` | Action proceeds; no log entry required unless `log_required` is set. |
| `allow_with_log` | Action proceeds; a structured audit entry is written to `00-meta/02-logs/audit.jsonl`. |
| `deny` | Action blocked; a `deny` entry is written; the agent receives an error response. |
| `dry_run` | Action is converted to a `report` — the diff is computed and returned, but no file is written. Used for review-gated zones and Linter structural checks. |

**Review-gated zones always degrade to `dry_run`** regardless of which profile requests the write and regardless of the profile's declared permissions:

- `30-synthesis/01-claims/`
- `30-synthesis/02-reference/`
- `30-synthesis/03-moc/`
- `50-deliverables/`

No profile can bypass this. The Linter's `dry_run` default for all non-trivial fixes uses the same mechanism. Any command or skill that writes to a review-gated zone or runs `schema-migrate` must default to dry-run; `schema-migrate` must never be run without reviewing the diff first.

---

## Request contract

```json
{
  "profile": "memoria-writer",
  "action": "write",
  "path": "40-workbench/project-x/04-drafts/chapter-1.md",
  "reason": "draft synthesis from claim notes",
  "task_id": "TASK-2026-05-31-007",
  "flags": {
    "explicit_authorization": false,
    "draft_only": true
  }
}
```

| Field | Required | Notes |
|---|---|---|
| `profile` | yes | Must match a known lane-override file. |
| `action` | yes | One of the action vocabulary values above. |
| `path` | yes | Relative to vault root. Normalized before evaluation. |
| `reason` | no | Human-readable intent; written to audit log when present. |
| `task_id` | no | Board card ID; required for `authorized-targeted` auto-fix class. |
| `flags.explicit_authorization` | no | Overrides default `dry_run` for specific paths when the card carries `review_status: approved`. |
| `flags.draft_only` | no | Signals the write is a proposal landing in a working zone, not a canonical write. |

---

## Response contract

Allow:
```json
{
  "decision": "allow_with_log",
  "policy_rule": "writer.write.workbench",
  "log_required": true
}
```

Deny:
```json
{
  "decision": "deny",
  "policy_rule": "writer.no-canonical-write",
  "message": "memoria-writer cannot write to 30-synthesis/01-claims/ — review gate required"
}
```

Dry-run:
```json
{
  "decision": "dry_run",
  "policy_rule": "review-gated-zone",
  "diff": "--- /dev/null\n+++ 30-synthesis/01-claims/claim-xyz.md\n@@ -0,0 +1,12 @@\n..."
}
```

---

## Audit log format

Every `allow_with_log` and `deny` decision writes a JSONL entry to `00-meta/02-logs/audit.jsonl`:

```json
{
  "ts": "2026-05-31T14:23:01Z",
  "profile": "memoria-librarian",
  "action": "write",
  "path": "20-sources/01-papers/smith-2024.md",
  "task_id": "TASK-2026-05-31-003",
  "decision": "allow_with_log",
  "policy_rule": "librarian.write.sources",
  "sha256_before": "e3b0c44298fc1c149afbf4c8996fb924...",
  "sha256_after": "a87ff679a2f3e71d9181a67b7542122c..."
}
```

The full field definitions (types, notes, hash-chain rules) and log rotation spec are in [memory.md — Audit log event fields](memory.md#audit-log-event-fields).

---

## Auto-fix policy

`auto_fix` is a separate action class because the Linter allows only narrowly scoped structural repairs while denying schema and canonical-content changes. The MCP enforces the class gate at the tool layer — the Linter cannot bypass it.

| Class | Auto-fix allowed | Requires `task_id` | Examples |
|---|---|---|---|
| `safe-and-unambiguous` | Yes | No | Trailing whitespace, missing `created` timestamp on a new note, missing required template field with one obvious value |
| `authorized-targeted` | Yes | Yes | Audit-log rotation, lint-findings file truncation, dashboard `last_updated` refresh |
| `schema-content` | No — dry_run always | — | Frontmatter field rename, value-set change, deprecated field removal |
| `review-gated-edit` | No — deny always | — | Any write to a review-gated zone |

---

## Lane-override file shape

The policy manifest for each profile lives in `.memoria/lane-overrides/<lane>.yaml`. The MCP reads these at startup. Example for the Writer lane:

```yaml
profile: memoria-writer

policy:
  allow:
    write:
      - "10-inbox/**"
      - "40-workbench/**"
  deny:
    write:
      - "30-synthesis/**"
      - "50-deliverables/**"
  require:
    - audit_log
    - timeout_required

routing:
  invocation: dispatched
  write_scope:
    - "10-inbox/02-answers/"
    - "40-workbench/"
```

`policy.deny` wins over `policy.allow`. Review-gated zones are enforced by the MCP independently of what the lane-override declares — even an explicit `allow` on a review-gated path degrades to `dry_run`.

---

## Related

- Why the gate is structural: [explanation/architecture/why-human-gate.md](../explanation/architecture/why-human-gate.md)
- Profile permission tables: [profiles.md](profiles.md)
- Audit log substrate and rotation: [memory.md](memory.md)
