---
title: Inspect session logs
parent: Operate
grand_parent: How-to guides
nav_order: 9
---

# Inspect session logs

Read the audit trail and the per-session summaries from the terminal — filter by lane, date, decision, or card — when you need to answer "what did the system actually do?" without waiting for a dashboard. This is the ad-hoc path beneath the audit-log and fleet-health dashboards ([Dashboards](../../reference/dashboards.md)); they render the same data — this is for one-off questions and scripting.

Both logs are append-only JSONL and **read-only** — never edit them; an out-of-band edit is exactly what the Linter's tamper detectors exist to catch.

## The two logs

| Log | Path | One row / file |
| --- | --- | --- |
| Policy audit log | `system/logs/audit.jsonl` | One gated decision (`allow` / `allow_with_log` / `deny` / `dry_run`), plus a paired `write_complete` record per write. |
| Per-session summaries | `system/logs/sessions/YYYY-MM-DD-HHMM.jsonl` | One deterministic digest per session — a header plus one record per touched path. |

The audit log is forensic and grows forever; the per-session summaries are digests the Linter writes once a session has been quiet for 24 h. The design is in [Session logging](../../explanation/architecture/session-logging.md); the audit field schema is owned by [Policy MCP](../../reference/policy-mcp.md).

## Prerequisites

- `jq` installed (`sudo apt install jq`) — every recipe below uses it
- Run from the vault root so the relative paths resolve

## Recipes

The audit fields you'll filter on: `timestamp` (UTC, `…Z`), `profile` (`memoria-<name>`), `action` (`read` / `write` / `append` / `move` / `delete` / `mkdir` / `auto_fix` / `report`), `path`, `task_id`, `decision`, and `policy_rule`.

**Recent denials across all lanes** — the first thing to check when a write didn't land:

```bash
jq -c 'select(.decision == "deny")' system/logs/audit.jsonl | tail -20
```

**One lane's activity on a given day:**

```bash
jq -c 'select(.profile == "memoria-writer" and (.timestamp >= "2026-06-18"))' system/logs/audit.jsonl
```

**Everything a single card touched** — the full footprint of one task, in order:

```bash
jq -c 'select(.task_id == "TASK-2026-06-18-003") | {timestamp, action, path, decision}' system/logs/audit.jsonl
```

**Pending schema migrations** — `dry_run` decisions are writes the gate refused to apply automatically (a field rename or enum change awaiting `lint:migrate-schema`):

```bash
jq -c 'select(.decision == "dry_run") | {path, policy_rule}' system/logs/audit.jsonl
```

**Decision tally for a lane** — a quick health read without the dashboard:

```bash
jq -r 'select(.profile == "memoria-librarian") | .decision' system/logs/audit.jsonl | sort | uniq -c
```

**Trace a write's reversibility pair** — the decision entry carries `before_hash`; the separate `write_complete` record carries the paired `after_hash`, matched by `task_id` + `path`:

```bash
jq -c 'select(.path == "catalog/papers/smith-2024.md")' system/logs/audit.jsonl
```

**Read the latest session summary** — what a session accomplished, digested:

```bash
ls -t system/logs/sessions/ | head -1
jq . "system/logs/sessions/$(ls -t system/logs/sessions/ | head -1)"
```

The digest's header carries the task, profiles, start/end, and counts by action and decision; each subsequent record is one touched path with its actions, final decision, and final `after_hash`.

## Verify

- Your filter returns rows (an empty result usually means the field value or date didn't match — check `profile` is the full `memoria-<name>` and the date is `YYYY-MM-DD`)
- Counts you compute by hand match what the audit-log / fleet-health dashboards show for the same window

## Notes and limits

- **No note content** ever enters either log — only paths, IDs, actions, decisions, and hashes. You can't reconstruct *what* was written, only *that* it was and whether it was authorized.
- **`write_complete` is a record kind, not a decision** — don't filter for it under `.decision`; match the before/after pair by `task_id` + `path`.
- **Audit growth is expected** — the log is never rotated; the Linter raises an advisory only past 50 MB.
- Only sessions quiet for 24 h are summarized, so a digest for today's in-flight work won't exist yet.

## Related

- The two-log design and why they stay separate: [Session logging](../../explanation/architecture/session-logging.md)
- The audit field schema and hash pairing: [Policy MCP](../../reference/policy-mcp.md)
- The full log inventory and JSONL conventions: [Telemetry & logs](../../reference/telemetry.md)
- The dashboards over this data: [Dashboards](../../reference/dashboards.md)
- Diagnosing a write that was denied: [Diagnose a denied or blocked write](../troubleshooting/diagnose-a-denied-write.md)
