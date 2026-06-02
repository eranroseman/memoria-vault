---
title: How to diagnose a denied or blocked write
parent: Recovery
---


# How to diagnose a denied or blocked write

When an agent's write doesn't show up, there are two very different causes, and they need opposite fixes:

1. The policy MCP **denied** it — a deliberate decision, recorded in the audit log.
2. The write **never reached the gate** — a wiring or plugin failure. Because Hermes fails *open* on hook errors, these can be silent.

This guide uses the audit log to tell them apart and find the reason.

## Prerequisites

- The policy MCP wired and running — it writes `99-system/logs/audit.jsonl`. Until the gate runs live, that log does not exist (see [Implementation status](../../../project-files/plans/implementation-status.md)); a missing *file* is a wiring problem, not a denial.
- The [audit-log dashboard](../../explanation/dashboards/operational-health/audit-log.md) available in Obsidian

## Steps

**1. Open the audit-log dashboard.**

From `home.md` → the audit-log dashboard. Its primary view is recent **denies and dry-runs**, newest first. Find an entry whose `path` and `profile` match the missing write, around the time it happened.

**2. Found a matching `deny` or `dry_run`? It was a policy decision.**

Read the fields ([full schema](../../reference/memory.md#audit-log-event-fields)):

| Field | What it tells you |
| --- | --- |
| `decision` | `deny` (forbidden) vs `dry_run` (held for review) |
| `action` | which of the eight actions was attempted (`write`/`move`/`delete`/…) |
| `path` | the target the action was refused on |
| `policy_rule` | exactly which lane-override rule fired |
| `reason` | the human-readable cause |

- **`deny`** — the lane forbids that action on that path (e.g., Librarian writing to `30-synthesis/01-claims/`). The fix is either the wrong lane for the task, or an intended permission you must change in the lane-override.
- **`dry_run`** — the path is a review-gated zone; the write is *held*, not refused. Approve it through the queue: [Work the review queue](../writing/work-the-review-queue.md).

**3. No matching entry at all? The write never reached the gate.**

Hermes fails open on hook errors, so a broken hook or unregistered MCP can let an attempt pass without ever logging a decision. Check, in order:

- Is the policy server registered in the profile's `mcp.json`?
- Run the self-tests: `python .memoria/mcp/policy_mcp.py --self-test` and `python .memoria/mcp/policy_hook.py --self-test`. A failure here means the gate isn't enforcing.
- Did the Obsidian Local REST API (port 27124) or a plugin error? The agent may report success while the write silently failed upstream of the gate.

A missing log entry for a write that *should* have been attempted points at wiring, not policy.

**4. Distinguish a policy denial from a plugin failure.**

If the agent reported success, nothing changed on disk, and there's **no** audit entry, suspect the vault-access path (obsidian-local-rest-api) rather than policy. The audit log only records what reached the gate — silence there means the write didn't get that far.

**5. Watch for a spike — it can be a security signal.**

A sudden rise in denies, especially right after ingesting a PDF, can indicate an indirect prompt-injection attempt nudging an agent toward unauthorized writes — not just operator error. The audit log is where this surfaces first; escalate and inspect the source rather than reflexively widening permissions.

## Verify

- You can name the cause: a logged `deny`/`dry_run` (policy) vs no entry (wiring/plugin).
- For a policy denial, you've read `policy_rule` and `reason`.
- The `before_hash` / `after_hash` chain is intact (the Linter's `vault-hash-drift` isn't firing) — confirming the log itself wasn't tampered with.

## Related

- Approving a held (`dry_run`) write: [Work the review queue](../writing/work-the-review-queue.md)
- Other recovery procedures: [recovery guides](README.md)
- The event schema: [memory.md — Audit log event fields](../../reference/memory.md#audit-log-event-fields)
- The decision protocol and action vocabulary: [Policy MCP](../../reference/policy-mcp.md)
- The dashboard: [audit-log dashboard](../../explanation/dashboards/operational-health/audit-log.md)
