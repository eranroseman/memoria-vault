---
id: 29
title: Admin/forensic GUI surface (hermes-workspace) — deferred, tool too immature to adopt
status: proposed
date_proposed: 2026-05-30
date_resolved:
supersedes: []
superseded_by: []
---

# ADR-29: admin/forensic GUI surface (`hermes-workspace`) — deferred

## Context

Memoria's operator surfaces are: **Obsidian** (content workflow), **dashboards inside Obsidian**
(state visibility), the **CLI** (forensic/admin), **Telegram** (mobile/urgent push), and the
**API** (programmatic). There is a recurring gap among them: no GUI for *administration and
forensics* — "what skills are loaded right now," "what's in this profile's memory," "show me the
audit log filtered to deny events this week." Those are CLI-only today, which is fine for
command-line natives but slow for browsing.

`hermes-workspace` (a Nous Research hackathon project; web UI on the Hermes API at `:8642`; chat
with SSE streaming, file browser, terminal, memory editor, skills browser, session inspector;
PWA, Tailscale-accessible, MIT) addresses exactly that gap. Status as evaluated: v0.1.0, ~9
stars, single contributor — a hackathon project, not a mature product.

## Decision

**Defer; watch maturity.** The admin/forensic gap is real, but `hermes-workspace` at v0.1.0
(single contributor, ~9 stars) is **too immature to adopt or to document as a recommended
surface** — pinning canonical docs to it would create a stale-doc liability for near-zero
benefit while the CLI fills the gap today. Memoria does not adopt it, bundle it, or recommend
it now. Re-evaluate if the tool matures (stable releases, more than one maintainer, sustained
activity). Whatever fills this gap later, it stays a **forensic/admin browse surface only** —
never a place where content work, triage, or approvals happen, because those must stay in
Obsidian + dashboards where the review gate and the policy MCP apply.

## Consequences

- No new dependency and no second control plane; nothing in Memoria breaks if the tool stalls
  or disappears.
- The CLI remains the documented admin/forensic surface in the interim — slow for browsing
  "what's loaded / in memory / in the audit log," but authoritative and dependency-free.
- The gap is recorded rather than papered over, with an explicit re-entry trigger (the tool
  maturing), so it is not silently forgotten.
- If a forensic browse surface is ever adopted, the review-gate and policy-MCP invariants are
  pre-committed: approvals never move to a surface that bypasses `metadata.review_status` and
  the audit trail.

## Alternatives considered

**Adopt `hermes-workspace` now as an optional documented surface.** Rejected: documenting a
v0.1.0 single-contributor tool in canonical docs is a maintenance liability that outweighs the
convenience, and the CLI already covers the need.

**Adopt it as a primary surface.** Rejected outright: it overlaps Obsidian (file browser, chat)
and would create a second, un-gated place to act on content — directly against the "Obsidian is
the content surface; the board holds state; the policy MCP gates writes" architecture.

**Build a Memoria-native admin GUI.** Rejected as scope creep: the forensic need is real but
narrow, and the CLI + dashboards already cover the daily path. Not worth a bespoke UI.

## Related

- **Existing surfaces:** the CLI (forensic), dashboards (state visibility), Telegram (push) — see [human-channels.md](../../explanation/architecture/human-channels.md)
- **Invariant protected:** the human review gate (`review_status`) and the [policy MCP](../../reference/architecture/policy-mcp.md)
- **Adjacent future idea:** the read-only [Memoria Inspector Obsidian plugin](../roadmap/future-directions.md#memoria-inspector-obsidian-plugin) covers part of the same forensic need from inside Obsidian
