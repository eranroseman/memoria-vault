---
topic: decisions
id: 40
title: Admin/forensic GUI surface (hermes-workspace)
status: rejected
assumes: []
date_proposed: 2026-05-30
date_resolved: 2026-06-16
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 40
nav_exclude: true
---

# ADR-40: Admin/forensic GUI surface (`hermes-workspace`)

> **Rejected 2026-06-16.** The forensic need is covered by the CLI and
> dashboards now, with a possible read-only Obsidian Inspector recorded in
> [ADR-58](58-adjacent-tool-integrations.md). An external admin GUI would add a
> second, immature surface with too much write capability for too little benefit.

## What

A web GUI for *administration and forensics* — "what skills are loaded," "what's in this profile's memory," "show the audit log filtered to deny events this week" — to fill the one gap among Memoria's operator surfaces (Obsidian, in-vault dashboards, CLI, Telegram, API). `hermes-workspace` (a Nous Research project; web UI on the Hermes API at `:8642`; chat with SSE, file browser, terminal, memory editor, skills browser, session inspector; PWA, Tailscale-accessible, MIT) addresses exactly that gap.

## Why

The admin/forensic views above are CLI-only today — fine for command-line natives, slow for browsing. There is no GUI for the "what's loaded / in memory / in the audit log" questions.

## Trade-offs

- `hermes-workspace` is v0.1.0, ~9 stars, single contributor — a hackathon project, not a mature product. Documenting it in canonical docs is a stale-doc liability for near-zero benefit while the CLI fills the gap.
- Any such surface risks becoming a second, un-gated place to act on content if scoped wrong.

## Rejection rationale

Memoria will not adopt `hermes-workspace`. It is a broad administrative GUI over
profile memory, files, terminal access, and sessions; even local-only, it expands
the action surface outside the vault's existing policy-gated flows. The durable
need is forensic visibility, not another write-capable workspace.


## Alternatives considered

**Adopt `hermes-workspace` now as an optional documented surface.** Rejected: documenting a v0.1.0 single-contributor tool is a maintenance liability that outweighs the convenience; the CLI already covers the need.

**Adopt it as a primary surface.** Rejected outright: it overlaps Obsidian (file browser, chat) and would create a second, un-gated place to act on content — against the "Obsidian is the content surface; the board holds state; the policy MCP gates writes" architecture.

**Build a Memoria-native admin GUI.** Rejected as scope creep: the forensic need is real but narrow; the CLI + dashboards cover the daily path.

## Related

- **Tracking issue:** [#373](https://github.com/eranroseman/memoria-vault/issues/373) — revisit each release cadence.
- **Existing surfaces:** CLI (forensic), dashboards (state), Telegram (push) — see [Interaction channels](../explanation/architecture/human-channels.md)
- **Invariant protected:** the human review gate (`review_status`) and the [policy MCP](../reference/policy-mcp.md)
- **Adjacent future idea:** the read-only Memoria Inspector Obsidian plugin from
  [Adjacent tool integrations](58-adjacent-tool-integrations.md) covers part of
  the same forensic need from inside Obsidian.
