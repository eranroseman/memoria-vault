---
title: Interaction channels
parent: Architecture
grand_parent: Explanation
nav_order: 4
---

# Interaction channels

Memoria has one daily human surface and two secondary human channels:

| Channel | Mode | Purpose |
| --- | --- | --- |
| **Obsidian** | Focused desktop work | Inbox triage, reading, writing, dashboards, and Co-PI conversation. |
| **CLI** (`hermes ...`) | Precise occasional work | Forensic queries, profile administration, manual dispatch, backup. |
| **Telegram** | Mobile async signal | Urgent push notifications today; mobile capture remains planned work. |

The API server is not a human channel. Programs use it for filesystem watchers,
Zotero hooks, git hooks, or dispatch integrations, and policy still gates writes
at the calling profile's permissions.

## Signal routing

Every finding has a loudness. Quiet and notice-level events wait in dashboards or
Maintenance. Alert and block-level events may push to Telegram because they can
change what the PI does soon.

Daily approvals should not require the CLI. Routine events should not push to the
phone. If either happens often, the surface is wrong.

## Related

- Obsidian layout contract: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- CLI commands: [Hermes CLI](../../reference/hermes-cli.md)
- Policy boundary: [Policy MCP](../../reference/policy-mcp.md)
