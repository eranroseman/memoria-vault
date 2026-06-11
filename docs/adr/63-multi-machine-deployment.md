---
topic: decisions
id: 63
title: Multi-machine deployment topologies and secondary-device patterns
status: deferred
nav_exclude: true
date_proposed: 2026-06-11
date_resolved:
assumes: [24, 26, 55]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 63
---

# ADR-63: Multi-machine deployment topologies and secondary-device patterns

## Context

The v0.1 default is `local-only` — one workstation, Git for history, Zotero on localhost ([deployment options](../explanation/deployment/deployment-options.md)). That default requires the workstation to be on and offers neither auto-sync nor unattended automation. Two felt needs push past it: working the vault from a second device (laptop, phone, tablet), and running discovery/ingest overnight without a human kickoff. Both require a sync topology *and* a safe answer to "what may a non-primary device do against a vault the primary is also dispatching against?" — without one, two machines race on card writes and corrupt the audit log. The topologies are additive and cost nothing to defer, so they are settled here and scheduled later. `deployment-options.md` currently defers the past-`local-only` substrate *to* this decision, which is its authoritative target.

## Decision

Memoria defines three sync topologies beyond `local-only`, a set of secondary-device operating patterns, and the invariants that keep them safe:

- **Three topologies:** `local-mesh` (Syncthing P2P, no VPS, $0 infra — desktop + laptop); `obsidian-sync` (Obsidian cloud sync, ~$10/mo, `.bib`-only Zotero on the VPS — when iOS access is needed); `always-on` (Syncthing + VPS, ~$12–25/mo — multi-device with an always-on agent, recommended for the discovery loop). Migration is monotonic: start `local-only`, move to `local-mesh` when a second device enters the workflow, graduate to `always-on` when unattended automation is wanted. `local-mesh` is structurally `always-on` minus the VPS.
- **Secondary-device patterns**, ordered by setup complexity: *vault-only* (Obsidian + Git, read/write notes, ~80% of daily work, no Hermes); *Telegram dispatch* (dispatch via the primary's bot, nothing installed locally); *HTTP API client* (POST to the primary's loopback/Tailscale API); *Hermes ACP-only* (local Hermes binary, the only pattern enabling the `agent-client` plugin); and *SSH-spawned ACP* (no local Hermes — spawn the primary's Hermes over SSH). Pattern selection follows topology: under `local-mesh` the desktop primary sleeps, so a local ACP install is preferred; under `always-on` the VPS is always reachable, so SSH-spawn is the default and removes install drift.
- **Structural-over-behavioral install policy.** A secondary device compiles only profiles architecturally safe on it, not the primary's full set. `memoria-copi` is the always-safe baseline — `policy.allow.write: []` and `routing.invocation: interactive_only` mean it *cannot* write or be queue-dispatched regardless of human behavior. The background lanes — Librarian, Writer, Peer-reviewer, and Engineer — are add-as-needed/dispatched, each carrying obligations the human must remember (API cost, queue conflicts, or background-only) before being installed on a secondary. Structural enforcement ("profile not found") beats the behavioral convention "don't enable cron, don't claim cards."
- **One dispatcher per vault, enforced by isolation.** Exactly one Hermes dispatcher touches a given vault. A developer's full install may coexist with the primary *only* by pointing at a different vault: under `always-on`, `HERMES_HOME` isolation **and** a *test vault* (clone, fixture, Docker volume) are mandatory, never optional — a dev Hermes on the production vault while the VPS also dispatches is the failure mode this rule exists to prevent.

## Consequences

- **Write coordination is the core risk** the whole secondary-device design exists to make structurally impossible, not merely discouraged.
- `always-on` adds standing cost and ops surface — a rented VPS, a Syncthing mesh to keep healthy, and a cron whose silent failure is the dominant operational risk.
- `obsidian-sync` degrades Zotero to `.bib`-only on the VPS, constraining Librarian discovery on that node.
- SSH-spawned ACP removes local install drift but adds a reachability dependency (primary awake, ~100–500ms/message latency).
- Install drift across devices is a standing maintenance cost once more than one machine compiles profiles — the co-PI-only baseline is what keeps it bounded.

## When this matters

Per topology, a concrete signal — context for the cadence review, not a gate:

- **`local-mesh`:** a *second device* genuinely enters daily use and manual Git pull/push between machines is the felt friction.
- **`always-on`:** unattended overnight work is wanted — most concretely the discovery loop — and a sleep-prone workstation keeps missing the cron.
- **`obsidian-sync`:** iOS/mobile vault access is required and Syncthing-on-mobile isn't viable.

**Guard: do not stand up a VPS or Syncthing mesh as a preparatory measure.** `local-only` is the correct posture until a second device or unattended automation is real; Syncthing is additive later and restructures nothing, so there is no first-mover cost to pay early. The invariant that must never relax on adoption: **exactly one Hermes dispatcher per vault**.

## Related

- **Authoritative target / adopted baseline:** [deployment options](../explanation/deployment/deployment-options.md) — defers the past-`local-only` substrate to this decision; documents the `local-only` default and the common conventions (Git history, `memoria.bib` in-vault, one dispatcher per vault, `.env` per-machine) these patterns presuppose.
- **Related decisions / Depends on:** [ADR-24](24-single-researcher-scope.md) (single-researcher scope); [ADR-26](26-repo-as-install-unit.md) (repo as install unit); [ADR-55](55-src-scaffold-populate-golden-copy.md) (src scaffold).
- **Cross-machine capabilities:** [ADR-60 cross-vault knowledge sharing](60-cross-vault-knowledge-sharing.md) — the capabilities that ride this substrate; the two are designed to move together.
- **Tracking issue:** [#413](https://github.com/eranroseman/memoria-vault/issues/413) — revisit at each release cadence.
