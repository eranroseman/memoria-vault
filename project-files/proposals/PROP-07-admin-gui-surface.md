---
topic: proposals
id: PROP-07
title: Admin/forensic GUI surface (hermes-workspace) — deferred, tool too immature to adopt
status: deferred
created: 2026-05-30
---

# PROP-07: Admin/forensic GUI surface (`hermes-workspace`)

## What

A web GUI for *administration and forensics* — "what skills are loaded," "what's in this profile's memory," "show the audit log filtered to deny events this week" — to fill the one gap among Memoria's operator surfaces (Obsidian, in-vault dashboards, CLI, Telegram, API). `hermes-workspace` (a Nous Research project; web UI on the Hermes API at `:8642`; chat with SSE, file browser, terminal, memory editor, skills browser, session inspector; PWA, Tailscale-accessible, MIT) addresses exactly that gap.

## Why

The admin/forensic views above are CLI-only today — fine for command-line natives, slow for browsing. There is no GUI for the "what's loaded / in memory / in the audit log" questions.

## Trade-offs

- `hermes-workspace` is v0.1.0, ~9 stars, single contributor — a hackathon project, not a mature product. Documenting it in canonical docs is a stale-doc liability for near-zero benefit while the CLI fills the gap.
- Any such surface risks becoming a second, un-gated place to act on content if scoped wrong.

## Adoption trigger

The tool matures: stable releases, more than one maintainer, sustained activity.

## Guard

Whatever fills this gap stays a **forensic/admin browse surface only** — never a place where content work, triage, or approvals happen. Those must stay in Obsidian + dashboards where the review gate and the policy MCP apply; approvals never move to a surface that bypasses `metadata.review_status` and the audit trail.

## Alternatives considered

**Adopt `hermes-workspace` now as an optional documented surface.** Rejected: documenting a v0.1.0 single-contributor tool is a maintenance liability that outweighs the convenience; the CLI already covers the need.

**Adopt it as a primary surface.** Rejected outright: it overlaps Obsidian (file browser, chat) and would create a second, un-gated place to act on content — against the "Obsidian is the content surface; the board holds state; the policy MCP gates writes" architecture.

**Build a Memoria-native admin GUI.** Rejected as scope creep: the forensic need is real but narrow; the CLI + dashboards cover the daily path.

## Related

- **Existing surfaces:** CLI (forensic), dashboards (state), Telegram (push) — see [human-channels.md](../../docs/explanation/architecture/human-channels.md)
- **Invariant protected:** the human review gate (`review_status`) and the [policy MCP](../../docs/reference/policy-mcp.md)
- **Adjacent future idea:** the read-only [Memoria Inspector Obsidian plugin](surveys/integrations.md) covers part of the same forensic need from inside Obsidian
