---
title: Policy MCP
parent: Reference
---

# Policy MCP

The runtime write-gate that intercepts every vault action, checks lane-override rules, and returns a decision before any content reaches disk. For the design rationale see [explanation/architecture/why-human-gate.md](../explanation/rationale/why-human-gate.md).

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

Every request carries complete identity and task metadata. `task_id` is required — the MCP cannot ask the worker mid-decision which task it is running.

---

## Action vocabulary

| Action | Default disposition |
|---|---|
| `read` | `allow` within `policy.allow.read`; `allow_with_log` for review-gated zones and cross-zone reads. |
| `write` | Governed by `policy.allow.write`. `dry_run` in review-gated zones. |
| `append` | `allow` for audit and session logs within the lane's own paths. |
| `move` | `allow_with_log` same-zone; `dry_run` cross-zone unless `flags.explicit_authorization`. |
| `delete` | `deny` by default for all profiles. Requires `flags.explicit_authorization` + `allow_with_log`. |
| `mkdir` | `allow` within `routing.write_scope`. |
| `auto_fix` | Class-gated via `flags.class` (Linter only — see [Auto-fix policy](#auto-fix-policy)). |
| `report` | Always `allow` within the worker's lane. |

---

## Decision values

| Decision | Meaning | Logged? |
|---|---|---|
| `allow` | Action proceeds. | Only if lane's `policy.require` includes `audit_log`. |
| `allow_with_log` | Action proceeds; audit entry mandatory. | Always. |
| `deny` | Action blocked; worker must escalate or choose a different path. | Always. |
| `dry_run` | Action logged and reported but not performed; worker escalates via board comment. | Always. |

**Two rules override lane configuration entirely:**

1. **Review-gated zones are never auto-written.** Writes to `30-synthesis/01-claims/`, `30-synthesis/02-reference/`, `30-synthesis/03-moc/`, and `50-deliverables/` degrade to `dry_run` regardless of the lane's `policy.allow` rules. No profile can bypass this. Any command or skill that writes to a review-gated zone or runs `schema-migrate` must default to dry-run.

2. **Linter auto-fix is class-gated.** When `profile = memoria-linter` and `action = auto_fix`, the MCP requires `flags.class ∈ {safe-and-unambiguous, authorized-targeted}`. All other classes are `deny`.

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
    "draft_only": false,
    "class": null
  }
}
```

| Field | Required | Notes |
|---|---|---|
| `profile` | yes | Must match a known lane-override file. |
| `action` | yes | One of the action vocabulary values above. |
| `path` | yes | Vault-root-relative, forward slashes, no leading `./`. Normalized before evaluation. |
| `reason` | no | Short prose for the audit log. |
| `task_id` | yes | Board card that triggered the action. Required on every request. |
| `flags.explicit_authorization` | no | Overrides default `dry_run` for specific paths when the card carries `review_status: approved`. |
| `flags.draft_only` | no | Signals the write is a proposal landing in a working zone, not a canonical write. |
| `flags.class` | no | Required for `auto_fix` actions (Linter only). |

---

## Response contract

Allow:
```json
{ "decision": "allow_with_log", "policy_rule": "writer.write.workbench", "log_required": true }
```

Deny:
```json
{ "decision": "deny", "policy_rule": "writer.deny.30-synthesis-claims", "message": "memoria-writer cannot write to 30-synthesis/01-claims/ — review gate required" }
```

Dry-run:
```json
{ "decision": "dry_run", "policy_rule": "review_gated.dry_run", "diff": "--- /dev/null\n+++ 30-synthesis/01-claims/claim-xyz.md\n..." }
```

---

## Audit log format

Every `allow_with_log` and `deny` decision appends one JSONL entry to `00-meta/02-logs/audit.jsonl`:

```json
{
  "ts": "2026-05-31T14:23:01Z",
  "profile": "memoria-librarian",
  "action": "write",
  "path": "20-sources/01-papers/smith-2024.md",
  "task_id": "TASK-2026-05-31-003",
  "decision": "allow_with_log",
  "policy_rule": "librarian.write.sources",
  "sha256_before": "sha256:e3b0c44298fc1c149afbf4c8996fb924...",
  "sha256_after": "sha256:a87ff679a2f3e71d9181a67b7542122c..."
}
```

**SHA-256 rules:**

- The MCP computes hashes — workers never supply them.
- Format: `"sha256:<64-hex-chars>"` (algorithm is self-describing).
- Newly created files: `before_hash` = SHA-256 of empty byte string (`sha256:e3b0c4...`), not `null`.
- If the MCP cannot read the file to hash it (permissions error, race), the decision is `deny` — no hash, no allow.
- `read` actions: `before_hash` only. `deny` and `dry_run`: neither hash (no write occurred).
- The `before_hash` / `after_hash` chain must remain unbroken across the entire log. `vault-hash-drift` fires if any link fails.

Full field definitions and log rotation spec: [memory.md — Audit log event fields](memory.md#audit-log-event-fields).

---

## Auto-fix policy

`auto_fix` is class-gated. The MCP enforces the class gate at the tool layer — the Linter cannot bypass it.

| Class | Auto-fix allowed | Requires `task_id` | Examples |
|---|---|---|---|
| `safe-and-unambiguous` | Yes | No | Trailing whitespace, missing `created` timestamp, missing required template field with one obvious value |
| `authorized-targeted` | Yes | Yes | Audit-log rotation, lint-findings file truncation, dashboard `last_updated` refresh |
| `schema-content` | No — `dry_run` always | — | Frontmatter field rename, value-set change, deprecated field removal |
| `review-gated-edit` | No — `deny` always | — | Any write to a review-gated zone |

---

## Skill-conditional policy

Skills can declare additive `policy.deny` rules in their `SKILL.md` frontmatter. Composition rules:

- **Deny is additive.** Lane denies + skill denies both apply. The narrower set wins.
- **Allow is a ceiling.** Skills cannot raise the lane's `policy.allow`. They can only carve from it.
- **Require is union.** Any `require` invariant from either the lane or the skill must hold.
- **Narrowing is one-way.** No tool call or nested skill load can override a deny rule the loaded skill brought in.

The one shipped restrictive skill is `counter-outline` (Writer-loaded), which narrows Writer's write scope to `40-workbench/*/02-framing/` only during the framing stage.

---

## Lane-override file shape

The policy manifest for each profile lives in `.memoria/lane-overrides/<lane>.yaml`. The MCP reads these at startup.

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

`policy.deny` wins over `policy.allow`. Review-gated zones are enforced independently of the lane-override — even an explicit `allow` on a review-gated path degrades to `dry_run`.

---

## Enforcement: the pre/post_tool_call hook

`check_permission` only decides — by itself it does not stop a write. Vault writes go through the `obsidian` MCP server, which has no knowledge of the policy MCP. The bridge is a Hermes shell hook, `.memoria/mcp/policy_hook.py`, registered per profile in `config.yaml`:

```yaml
hooks:
  pre_tool_call:
    - matcher: "obsidian.*"
      command: "python {{VAULT_PATH}}/.memoria/mcp/policy_hook.py --profile memoria-<name>"
      timeout: 10
  post_tool_call:
    - matcher: "obsidian.*"
      command: "python {{VAULT_PATH}}/.memoria/mcp/policy_hook.py --profile memoria-<name>"
      timeout: 10
```

- **`pre_tool_call`** maps the obsidian tool to a policy action, calls `check_permission`, and blocks `deny`/`dry_run`. On an allowed write it stashes the `before_hash`.
- **`post_tool_call`** reads the stash, computes `after_hash`, and appends the paired `write_complete` audit record.

**Matcher must be a `re.fullmatch` pattern (Tier-4).** Hermes matches the hook `matcher` against the tool name with `re.fullmatch` (`agent/shell_hooks.py`), so a bare `matcher: "obsidian"` matches *only* a tool literally named `obsidian` and never fires on `obsidian_append_content`/`obsidian_patch_content`. Use `"obsidian.*"` (and `"write_file|patch"` for the Coder/Linter `file` toolset). A wrong matcher silently disables the gate — verify with `hermes -p <profile> hooks test pre_tool_call --for-tool obsidian_patch_content`.

**Caveat 1 — best-effort, not fail-closed.** Hermes fails open on hook errors (a crashing hook is logged but does not abort the loop). Hard enforcement that survives a broken hook would need a custom obsidian bridge that calls `check_permission` internally.

**Caveat 2 — shell hooks do not fire during real tool execution (Tier-4, [#58](https://github.com/eranroseman/memoria-vault/issues/58)).** Confirmed live on Hermes v0.14.0: a `pre_tool_call` shell hook does **not** fire on the agent's tool calls in **either** `hermes -z`/oneshot **or** the gateway (`api_server`, which shares `run_agent.AIAgent` with every chat platform) — tested with a `.*` global matcher, `HERMES_ACCEPT_HOOKS=1`, and a confirmed tool call. The hook fires only under `hermes hooks test`. So `policy_hook.py` **cannot be the primary enforcement** for automated lanes — "run via the gateway" does not help. **The primary guarantee must be a custom obsidian bridge** (a thin MCP server wrapping `mcp-obsidian` that calls `check_permission` internally before writing — mode-independent, fully fail-closed). The shell hook stays as defense-in-depth for the interactive modes where it does fire; the capability layer (`agent.disabled_toolsets`) still removes terminal/file from non-Coder/Linter lanes. **Release blocker.**

---

## Relationship to Hermes Tirith

Two coexisting policy layers:

| Layer | Scope | Owner |
|---|---|---|
| **Hermes Tirith** | Which *tools* a profile may call | Hermes-side, per-profile, runtime-internal |
| **Memoria policy MCP** | What each call may *write to disk* | Memoria-side, per-lane via lane-override YAML |

An unexpected `deny` is a Memoria-side question: check the lane-override YAML, then the audit log. A Tirith rejection (tool call blocked entirely) is a Hermes-side question. The two failure modes are distinct.

---

## Related

- Profile permission tables: [profiles.md](profiles.md)
- Audit log substrate and rotation: [memory.md](memory.md)
- Why the gate is structural: [explanation/architecture/why-human-gate.md](../explanation/rationale/why-human-gate.md)
- The guard layer in the three-layer model: [why-three-layers.md](../explanation/rationale/why-three-layers.md)
