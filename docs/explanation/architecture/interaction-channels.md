---
title: Interaction channels
parent: Architecture
grand_parent: Explanation
nav_order: 3
---

# Interaction channels

Memoria has one required PI surface: the CLI over a local workspace. Editor
files are the durable working surface, and optional notification channels can
draw attention to urgent items. They do not become the source of authority.

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
