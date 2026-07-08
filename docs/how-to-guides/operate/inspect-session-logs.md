---
title: Inspect session logs
parent: Operate
grand_parent: How-to guides
nav_order: 9
---

# Inspect session logs

Use the terminal to answer one question: "what did the system actually do?"
The logs are read-only. Inspect them; do not edit them.

## Prerequisites

- `jq` installed (`sudo apt install jq`) — every recipe below uses it
- Run from the vault root so the relative paths resolve

## Steps

**1. Check recent denials.**

```bash
jq -c 'select(.decision == "deny")' system/logs/audit.jsonl | tail -20
```

**2. Filter one actor or day when the window is known.**

```bash
jq -c 'select(.actor == "adapter" and (.timestamp >= "2026-06-18"))' system/logs/audit.jsonl
```

**3. Trace everything a single request touched.**

```bash
jq -c 'select(.request_id == "REQ-2026-06-18-003") | {timestamp, action, path, decision}' system/logs/audit.jsonl
```

**4. Find dry-run write decisions.**

```bash
jq -c 'select(.decision == "dry_run") | {path, policy_rule}' system/logs/audit.jsonl
```

**5. Count decisions for one actor.**

```bash
jq -r 'select(.actor == "adapter") | .decision' system/logs/audit.jsonl | sort | uniq -c
```

**6. Inspect one path's write trace.**

```bash
jq -c 'select(.path == "bibliography.bib")' system/logs/audit.jsonl
```

**7. Read the latest request summary.**

```bash
ls -t system/logs/sessions/ | head -1
jq . "system/logs/sessions/$(ls -t system/logs/sessions/ | head -1)"
```

## Verify

- Your filter returns rows (an empty result usually means the field value or date
  did not match -- check `actor` and the date is `YYYY-MM-DD`)
- Counts you compute by hand match what the audit-log dashboard shows for the same window

## Related

- The two-log design and why they stay separate: [Session logging](../../explanation/architecture/session-logging.md)
- The audit field schema and hash pairing: [Policy audit log](../../reference/policy-audit-log.md)
- The full log inventory and JSONL conventions: [Telemetry & logs](../../reference/telemetry.md)
- The dashboards over this data: [Dashboards](../../reference/dashboards.md)
- Diagnosing a write that was denied: [Diagnose a denied or blocked write](../troubleshooting/diagnose-a-denied-write.md)
