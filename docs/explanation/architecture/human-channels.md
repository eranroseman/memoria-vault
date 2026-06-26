---
title: Interaction channels
parent: Architecture
nav_order: 4
---

# Interaction channels

Memoria's primary UI is Obsidian — and within it, `inbox/` is the one place agents leave PI-facing cards: candidate, gap, flag, alert, and work-prompt ([ADR-51](../../adr/51-inbox-category-and-honesty-card.md)). The daily Inbox queue shows only action cards in "Needs me"; Maintenance reads the flag/alert drift slices ([ADR-81](../../adr/81-persistent-gate-dashboards.md)). Beyond Obsidian are two secondary channels for reaching the system when it isn't the right place — the CLI (precise, occasional, forensic) and Telegram (mobile, async) — plus one non-human integration path, the API server, which programs use and humans never touch directly.

The organizing principle: **each channel owns one mode.** Using one for another's job produces slow erosion — daily operations done via CLI compound into friction that eventually stops the behavior; push notifications wired for the wrong events train the human to ignore them all.

| Channel | Mode | Purpose |
| --- | --- | --- |
| **Obsidian** | Desktop, focused, deliberate | Daily triage (the Inbox), reading, authoring, the Co-PI conversation in the Agent Client pane |
| **CLI** (`hermes …`) | Desktop, occasional, precise | Forensic queries, profile administration, manual dispatch, backup |
| **Telegram** | Mobile, async, lightweight | Urgent push notifications today; mobile capture is planned work |

The three rows above are the human channels. The API server (port 8642) is listed separately below because it is *not* a human-operated channel — it is a programmatic integration surface that programs use and humans never operate directly:

| Integration surface | Mode | Purpose |
| --- | --- | --- |
| **API server** (port 8642) | Programmatic, integration (not human-operated) | File-system watchers, Zotero hooks, git post-commit hooks, cross-machine dispatch |

---

## Why the CLI is for rare, precise operations

A UI exists for frequent operations. A CLI is invisible until needed, and then exactly the right shape — it surfaces complete state (retry count, blocker reason, audit slices) without the constraints of a dashboard layout.

The CLI's role is forensic and administrative: card inspection, lane health checks, audit trail queries, manual dispatch outside the normal trigger flow, profile administration, and backup operations. These are all low-frequency and high-precision — exactly the profile where a CLI excels over a UI.

The diagnostic the CLI is uniquely suited for is "why did this happen" rather than "what should I do next." The dashboards answer the second question; the CLI is for the first.

The signal that a CLI operation is being used too often is that the operation belongs somewhere else. Daily approvals done at the terminal mean the dashboard approval path is missing or broken. Frequent manual dispatch means a trigger should be automated. CLI frequency is a smell, not a workflow.

For command syntax and available operations, see [Hermes CLI](../../reference/hermes-cli.md).

---

## Graded loudness — how a signal picks its surface

Every agent and operation finding carries one of four loudness levels, and the level decides where it surfaces:

| Level | Outcome |
| --- | --- |
| **Quiet** | logged only; no push |
| **Notice** | appears in the relevant dashboard + weekly review; no push |
| **Alert** | appears in Maintenance's health surfaces and sends Telegram push when configured |
| **Block** | appears in Maintenance or an Inbox work prompt, sends Telegram push when configured, and pauses new delegation plus review-gated promotion until acknowledged |

The test for push vs dashboard routing: *does it change what the PI does in the next 30 minutes?* Only Alert and Block should ever reach a push channel; everything else waits in the Inbox, Maintenance, or the relevant dashboard. This is what keeps the push channel trustworthy — when Telegram buzzes, it matters.

---

## Why Telegram stays narrow

Telegram has two tempting jobs that are easy to conflate: push notification for
urgent signals, and lightweight mobile capture. Only urgent push is shipped
today; inbound mobile capture remains planned work ([#382](https://github.com/eranroseman/memoria-vault/issues/382)).

The push notification mode carries the **Alert** and **Block** levels only — hard blockers, time-sensitive completions, high-severity drift alarms, cron failures. Wiring Telegram for per-card events or routine approvals teaches the human to ignore Telegram notifications — including the ones that actually matter.

The planned mobile capture mode takes advantage of the phone's always-accessible nature: capture fleeting thoughts, queue URLs for ingest, or quick corpus lookups while in motion. The key constraint is that the Telegram toolset stays narrower than the CLI or desktop — mobile is for thinking and capture, not for code execution, web search, or programmatic operations that have desktop footguns.

Confining Telegram to one messaging channel is also intentional. Each additional channel — Discord, Slack, WhatsApp — competes for attention and demands its own notification discipline. Until there is a concrete need that Telegram cannot serve, additional channels add noise without value.

---

## Why the API server is for programs only

The API server (port 8642) is the one-row integration surface in the table above: programs connect through it (file-system watchers, Zotero hooks, git post-commit hooks, cross-machine dispatch) while humans use the command palette and CLI instead. It is a different door, not a different key — every API write still passes through the policy MCP at the calling profile's permissions. The full rationale is in [Why Hermes](../rationale/why-hermes.md).

---

## Related

- Obsidian UI components: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- CLI commands: [Hermes CLI](../../reference/hermes-cli.md)
- Policy MCP (what API calls go through): [Policy MCP](../../reference/policy-mcp.md)
