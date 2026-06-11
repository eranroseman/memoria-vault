---
topic: decisions
id: 60
title: Cross-vault and cross-project knowledge sharing
status: deferred
nav_exclude: true
date_proposed: 2026-06-11
date_resolved:
assumes: [23, 24]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 60
---

# ADR-60: Cross-vault and cross-project knowledge sharing

## Context

The v0.1 scope is one researcher working one vault on one machine ([ADR-24](24-single-researcher-scope.md)). But a researcher accumulates more than one vault (a collaborator's, a separate domain vault) and more than one project inside a vault, and recall does not currently cross either boundary: a claim settled in vault A is invisible from vault B, and work approved on one project never primes another. Each gap is a felt friction only once the second vault or third project is real — so the shapes are settled here while the scheduling waits on the trigger.

## Decision

Memoria defines four additive cross-boundary capabilities, each scoped to a memory substrate ([ADR-23](23-scoped-memory-substrates.md)) and each gated behind its own trust guard:

1. **Cross-vault read-only retrieval.** MCP-mediated read access to a second Memoria vault, strictly read-only — no writes, no card creation — with the policy MCP enforcing the boundary. The foreign vault's canon is someone else's: its claim notes are treated as *sources*, not as your own synthesis. Requires both vaults reachable by the same Hermes instance.
2. **Cross-project reading as personal AgentRxiv.** Profiles scan approved outputs from other projects in the same vault at session start — the within-vault analogue of AgentRxiv's ~11% gain from agents reading prior agent reports — implemented as a step in the Librarian's session-start routine.
3. **Scripted session-history sync.** `hermes profile export` / `import` snapshots carry `state.db` chat history between machines for session continuity without a shared server, extending the `memories/` junction sync pattern. Manual or cron-triggered; snapshots must exclude credentials.
4. **Hermes shared-memory server.** A remote shared memory provider giving real-time, concurrency-capable cross-machine recall — the live-service replacement for scripted snapshots — adopted only for the specific failure mode where the scripted approach breaks.

## Consequences

- Cross-vault retrieval introduces a trust boundary: foreign claim notes must never be promoted to local canon without re-synthesis.
- Cross-project reading earns its keep only on a vault with real overlap; on a sparse vault it adds noise and latency.
- The Hermes memory server adds standing infrastructure cost and a hosting dependency — scripted sync covers ~90% of the need at zero infrastructure, which is why it is sequenced first.

## When this matters

Per capability, a concrete signal — not "might be useful" — as context for the cadence review:

- **Cross-vault retrieval:** two active research vaults are in use and you regularly switch between them to check whether a claim from vault A is addressed in vault B.
- **Cross-project reading:** the vault has ≥ 3 active projects with ≥ 50 approved claim notes each, *and* cross-project insights are being missed until manual review.
- **Scripted session-history sync:** you regularly start a session on a second machine and want prior session context from the primary.
- **Hermes memory server:** the scripted snapshot approach is *already* failing because you switch devices frequently *within* a single work session, not just between sessions. **Guard: do not adopt the memory server before scripted sync has been tried** — it is the right fix for one specific failure mode, and adopting it pre-emptively buys infrastructure cost without clear benefit.

## Related

- **Related decisions / Depends on:** [ADR-23](23-scoped-memory-substrates.md) (the scoped memory substrates each capability rides on); [ADR-24](24-single-researcher-scope.md) (single-researcher scope) — this ADR extends ADR-24's bounds outward to the multi-vault, multi-project case while keeping the single-operator invariant.
- **Deployment substrate:** [ADR-63 multi-machine deployment](63-multi-machine-deployment.md) — the sync topologies these cross-machine capabilities run on; the two are designed to move together.
