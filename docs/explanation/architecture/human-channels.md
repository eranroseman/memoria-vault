---
title: Interaction channels
parent: Architecture
nav_order: 4
---

# Interaction channels

Memoria's primary UI is Obsidian. Beyond it are two secondary channels for reaching the system when Obsidian isn't the right place — the CLI (precise, occasional, forensic) and Telegram (mobile, async) — plus one non-human integration path, the API server, which programs use and humans never touch directly.

The organizing principle: **each channel owns one mode.** Using one for another's job produces slow erosion — daily operations done via CLI compound into friction that eventually stops the behavior; push notifications wired for the wrong events train the human to ignore them all.

| Channel | Mode | Purpose |
| --- | --- | --- |
| **Obsidian** | Desktop, focused, deliberate | Daily triage, reading, authoring, agent conversations on the active note |
| **CLI** (`hermes …`) | Desktop, occasional, precise | Forensic queries, profile administration, manual dispatch, backup |
| **Telegram** | Mobile, async, lightweight | Fleeting capture, source-URL queuing, urgent push notifications |
| **API server** (port 8642) | Programmatic, integration | File-system watchers, Zotero hooks, git post-commit hooks, cross-machine dispatch |

---

## Why the CLI is for rare, precise operations

A UI exists for frequent operations. A CLI is invisible until needed, and then exactly the right shape — it surfaces complete state (retry count, blocker reason, audit slices) without the constraints of a dashboard layout.

The CLI's role is forensic and administrative: card inspection, lane health checks, audit trail queries, manual dispatch outside the normal trigger flow, profile administration, and backup operations. These are all low-frequency and high-precision — exactly the profile where a CLI excels over a UI.

The diagnostic the CLI is uniquely suited for is "why did this happen" rather than "what should I do next." The dashboards answer the second question; the CLI is for the first.

The signal that a CLI operation is being used too often is that the operation belongs somewhere else. Daily approvals done at the terminal mean the dashboard approval path is missing or broken. Frequent manual dispatch means a trigger should be automated. CLI frequency is a smell, not a workflow.

For command syntax and available operations, see [Hermes CLI](../../reference/hermes-cli.md).

---

## Why Telegram has two distinct modes

Telegram serves two purposes that are easy to conflate but that need to remain separate: push notification for urgent signals, and lightweight mobile capture.

The push notification mode is for things that cannot wait for the morning Daily Health glance — hard blockers, time-sensitive completions, high-severity drift alarms, cron failures. The critical distinction is whether the notification changes what the human would do in the next 30 minutes. If it doesn't, it should surface in a dashboard, not Telegram. Wiring Telegram for per-card events or routine approvals teaches the human to ignore Telegram notifications — including the ones that actually matter.

The mobile capture mode takes advantage of the phone's always-accessible nature: capture fleeting thoughts, queue URLs for ingest, quick corpus lookups, or Socratic processing while in motion. The key constraint is that the Telegram toolset is intentionally narrower than the CLI or desktop — mobile is for thinking and capture, not for code execution, web search, or programmatic operations that have desktop footguns.

Confining Telegram to one messaging channel is also intentional. Each additional channel — Discord, Slack, WhatsApp — competes for attention and demands its own notification discipline. Until there is a concrete need that Telegram cannot serve, additional channels add noise without value.

For Telegram configuration and the recommended per-profile toolset, see [How to set up the messaging gateway](../../how-to-guides/setup/set-up-messaging.md).

---

## Why the API server is for programs only

The API server (port 8642) is where programs connect to Memoria — file-system watchers, Zotero hooks, mail filters, git post-commit hooks, calendar integrations, and cross-machine dispatch. Humans never touch it directly because the same operations available through the API are exposed through the command palette and CLI with better affordances for human use.

The API server exists because programmatic integration needs a different interface than human operation. A file-system watcher that fires on PDF drops cannot use the command palette. A Better BibTeX script that fires on Zotero save needs a network endpoint. The API is the integration surface for automation; the channels above are the interaction surfaces for humans.

Security-wise, the API passes every write through the policy MCP — it does not grant elevated permissions. A program that calls the API has exactly the permissions of the profile it is acting as. See [Policy MCP](../../reference/policy-mcp.md) for the enforcement details.

---

## Related

- Messaging gateway setup: [How to set up the messaging gateway](../../how-to-guides/setup/set-up-messaging.md)
- Obsidian UI components: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- CLI commands: [Hermes CLI](../../reference/hermes-cli.md)
- Policy MCP (what API calls go through): [Policy MCP](../../reference/policy-mcp.md)
