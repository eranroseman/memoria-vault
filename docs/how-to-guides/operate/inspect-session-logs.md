---
title: Inspect session logs
parent: Operate
grand_parent: How-to guides
nav_order: 9
---

# Inspect session logs

Read the audit trail and the per-session summaries from the terminal — filter by
adapter/profile, date, decision, or task — when you need to answer "what did the
system actually do?" without waiting for a dashboard. This is the ad-hoc path
beneath the audit-log dashboard ([Dashboards](../../reference/dashboards.md));
it renders the same data — this is for one-off questions and scripting.

Both logs are append-only JSONL and **read-only** — never edit them; an
out-of-band edit is exactly what the Linter's tamper detectors exist to catch.
The two-log design is in [Session
logging](../../explanation/architecture/session-logging.md); the audit field
schema is owned by [Policy gate](../../reference/policy-mcp.md).

## Prerequisites

- `jq` installed (`sudo apt install jq`) — every recipe below uses it
- Run from the vault root so the relative paths resolve

## Recipes

The audit fields you'll filter on: `timestamp` (UTC, `…Z`), `profile` (`memoria-<name>`), `action` (`read` / `write` / `append` / `move` / `delete` / `mkdir` / `auto_fix` / `report`), `path`, `task_id`, `decision`, and `policy_rule`.

**Recent denials** — the first thing to check when a write didn't land:

```bash
jq -c 'select(.decision == "deny")' system/logs/audit.jsonl | tail -20
```

**One adapter/profile's activity on a given day:**

```bash
jq -c 'select(.profile == "memoria-writer" and (.timestamp >= "2026-06-18"))' system/logs/audit.jsonl
```

**Everything a single card touched** — the full footprint of one task, in order:

```bash
jq -c 'select(.task_id == "TASK-2026-06-18-003") | {timestamp, action, path, decision}' system/logs/audit.jsonl
```

**Dry-run write decisions** — writes the gate refused to apply automatically:

```bash
jq -c 'select(.decision == "dry_run") | {path, policy_rule}' system/logs/audit.jsonl
```

**Decision tally for one adapter/profile** — a quick policy read without the dashboard:

```bash
jq -r 'select(.profile == "memoria-librarian") | .decision' system/logs/audit.jsonl | sort | uniq -c
```

**Trace a write's reversibility pair** — the decision entry carries `before_hash`; the separate `write_complete` record carries the paired `after_hash`, matched by `task_id` + `path`:

```bash
jq -c 'select(.path == "catalog/sources/smith-2024/source.md")' system/logs/audit.jsonl
```

**Read the latest session summary** — what a session accomplished, digested:

```bash
ls -t system/logs/sessions/ | head -1
jq . "system/logs/sessions/$(ls -t system/logs/sessions/ | head -1)"
```

The digest's header carries the task, profiles, start/end, and counts by action and decision; each subsequent record is one touched path with its actions, final decision, and final `after_hash`.

## Verify

- Your filter returns rows (an empty result usually means the field value or date didn't match — check `profile` is the full `memoria-<name>` and the date is `YYYY-MM-DD`)
- Counts you compute by hand match what the audit-log dashboard shows for the same window

## Notes and limits

- **No note content** ever enters either log — only paths, IDs, actions, decisions, and hashes. You can't reconstruct *what* was written, only *that* it was and whether it was authorized.
- **`write_complete` is a record kind, not a decision** — don't filter for it under `.decision`; match the before/after pair by `task_id` + `path`.
- **Audit growth is expected** — the log is never rotated; the Linter raises an advisory only past 50 MB.
- Only sessions quiet for 24 h are summarized, so a digest for today's in-flight work won't exist yet.

## Related

- The two-log design and why they stay separate: [Session logging](../../explanation/architecture/session-logging.md)
- The audit field schema and hash pairing: [Policy gate](../../reference/policy-mcp.md)
- The full log inventory and JSONL conventions: [Telemetry & logs](../../reference/telemetry.md)
- The dashboards over this data: [Dashboards](../../reference/dashboards.md)
- Diagnosing a write that was denied: [Diagnose a denied or blocked write](../troubleshooting/diagnose-a-denied-write.md)
