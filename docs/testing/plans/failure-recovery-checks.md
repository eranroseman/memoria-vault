---
topic: tests
title: Failure Recovery Checks
status: draft
parent: Test plans
grand_parent: Testing
nav_order: 60
---

# Failure Recovery Checks

These checks prove Memoria fails closed and can recover from common interrupted
states. Run them for releases that touch policy, ingest, MCP, installer, cron, or
workflow replay.

## Checks

| Failure mode | Pass criteria |
| --- | --- |
| Forbidden write | No target file is created; audit records `deny`. |
| Gate error | The write fails closed, with no un-audited file mutation. |
| Obsidian MCP down | Agent reports the bridge failure; no raw filesystem fallback write occurs. |
| Duplicate ingest | Re-running the same citekey does not create a duplicate canonical note. |
| Tier-0 interruption | A note stuck at `ingest_status: tier0` is found by retry/reconcile and re-driven. |
| Dry-run path | Peer-reviewer and deterministic dry-run checks leave target files byte-identical. |
| Installer re-run | Re-running install against the throwaway vault is idempotent. |
| Cron recovery | A safe cron can be run manually after missed schedule time and emits expected logs. |

## Evidence Home

Record only failures, release-blocking recovery evidence, or release-candidate
manual runs. Routine unit evidence stays in Source Gate results.
