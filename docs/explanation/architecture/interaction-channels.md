---
title: Interaction channels
parent: Architecture
grand_parent: Explanation
nav_order: 3
---

# Interaction channels

Memoria has one required PI surface and optional secondary channels:

| Channel | Mode | Purpose |
| --- | --- | --- |
| **CLI** (`memoria ...`) | Required daily and operator work | Capture, enrich, digest, ask, request recovery, audit queries, rebuilds, and checks. |
| **Editor files** | Focused desktop work | Reading, writing, dashboards, and review decisions over the workspace files. |
| **Telegram** | Optional mobile async signal | Urgent push notifications when configured; mobile capture remains planned work. |

An optional adapter is not the source of authority. Programs may wrap the CLI or
watch files, but the request queue, operation manifests, policy gate, and journal
remain the write boundary.

## Signal routing

Every finding has a loudness. Quiet and notice-level events wait in dashboards or
Maintenance. Alert and block-level events may push to Telegram because they can
change what the PI does soon.

Routine events should not push to the phone. If they do, the loudness policy is
wrong.

## Related

- CLI commands: [CLI](../../reference/cli.md)
- Policy boundary: [Policy gate](../../reference/policy-mcp.md)
