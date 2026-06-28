---
title: Diagnose a denied or blocked write
parent: Troubleshooting
grand_parent: How-to guides
nav_order: 4
---


# Diagnose a denied or blocked write

**Symptom:** an agent reports a write, but it never shows up in the vault.

**Diagnosis:** there are two very different causes, and they need opposite fixes:

1. The policy MCP **denied** it — a deliberate decision, recorded in the audit log.
2. The write **never reached the gate** — a wiring or plugin failure. Because Hermes fails *open* on hook errors, these can be silent.

**Fix:** use the audit log to tell the two apart, then act on the cause — read the policy `reason`, or repair the wiring.

## Prerequisites

- The policy MCP wired and running — it writes `system/logs/audit.jsonl`. Until the gate runs live, that log does not exist; a missing *file* is a wiring problem, not a denial.
- The [audit-log dashboard](../../explanation/dashboards/operational-health.md#audit-log) available in Obsidian

## Steps

**1. Open the audit-log dashboard.**

From `home.md` → the audit-log dashboard. Its primary view is recent **denies and dry-runs**, newest first. Find an entry whose `path` and `profile` match the missing write, around the time it happened.

**2. Found a matching `deny` or `dry_run`? It was a policy decision.**

Read the `decision`, `policy_rule`, and `reason` fields on the entry (full field schema: [Policy audit log](../../reference/policy-audit-log.md); lane-override decision protocol: [Policy MCP](../../reference/policy-mcp.md)):

- **`deny`** — the lane forbids that action on that path (e.g., Librarian writing to `notes/claims/`). The fix is either the wrong lane for the task, or an intended permission you must change in the lane-override.
- **`dry_run`** — the path is a review-gated zone; the write is *held*, not refused. Approve it through the queue: [Work the action queue](../inbox/work-the-action-queue.md).

**3. No matching entry at all? The write never reached the gate.**

Hermes fails open on hook errors, so a broken hook or unregistered MCP can let an attempt pass without ever logging a decision. Check, in order:

- Is the policy server registered in the profile's `config.yaml` (`mcp_servers`)?
- Smoke-test the gate live:

  ```bash
  python3 .memoria/mcp/policy_mcp.py --vault . --decide '{"profile":"memoria-librarian","action":"write","path":"notes/claims/x.md","task_id":"T1"}'
  ```

  Expected result: `"decision": "deny"` because `notes/claims/` is review-gated. If the command errors or allows the write, the gate logic is broken. The full component test suite is `scripts/test.sh l1` from the repo clone.
- Did the Obsidian Local REST API native MCP or a plugin error? The agent may report success while the write silently failed upstream of the gate. Check the plugin's HTTPS server is on, its port matches `OBSIDIAN_MCP_PORT`, and `OBSIDIAN_MCP_SSL_VERIFY` points at the exported PEM certificate/CA bundle ([Set up Obsidian](../setup/set-up-obsidian.md)).

A missing log entry for a write that *should* have been attempted points at wiring, not policy.

**4. Distinguish a policy denial from a plugin failure.**

If the agent reported success, nothing changed on disk, and there's **no** audit entry, suspect the vault-access path (obsidian-local-rest-api) rather than policy. The audit log only records what reached the gate — silence there means the write didn't get that far.

**5. Watch for a spike — it can be a security signal.**

A sudden rise in denies, especially right after ingesting a PDF, can indicate an indirect prompt-injection attempt nudging an agent toward unauthorized writes — not just operator error. The audit log is where this surfaces first; escalate and inspect the source rather than reflexively widening permissions.

## Verify

- You can name the cause: a logged `deny`/`dry_run` (policy) vs no entry (wiring/plugin).
- For a policy denial, you've read `policy_rule` and `reason`.
- Each write's `before_hash` / `after_hash` pairing is intact (the Linter's `audit-unpaired-writes` isn't firing) — confirming the write completed and wasn't tampered with.

## Related

- Approving a held (`dry_run`) write: [Work the action queue](../inbox/work-the-action-queue.md)
- Other troubleshooting procedures: [Troubleshooting](README.md)
- The audit event schema: [Policy audit log](../../reference/policy-audit-log.md)
- The decision protocol and action vocabulary: [Policy MCP](../../reference/policy-mcp.md)
- The dashboard: [audit-log dashboard](../../explanation/dashboards/operational-health.md#audit-log)
