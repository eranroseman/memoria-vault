---
topic: decisions
id: 23
title: Memory is six scoped substrates, not one store
status: accepted
date_proposed: 2026-06-01
date_resolved: 2026-06-01
supersedes: []
superseded_by: []
---

# ADR-23: Memory is six scoped substrates, not one store

## Context

"Memory" in Memoria is not one thing, and treating it as one is the source of most "the agent forgot" and "the agent remembered something it shouldn't" failures. Every profile's read/write boundary depends on which substrate holds a given fact, yet the split was only described in [memory-tiers.md](../../docs/explanation/architecture/memory-tiers.md) and never recorded as a decision. Because the substrate boundaries are what keep one lane's in-flight reasoning from leaking into another's — and what keep durable knowledge out of size-capped, session-frozen stores — the split deserves a fixed anchor rather than living only in mutable prose.

## Decision

Memoria's memory is **six distinct substrates**, each with its own scope, lifespan, backing store, and owner — two provided by Hermes natively, four added by Memoria:

1. **Working context** (Hermes) — one profile session, cleared on `/clear`; active reasoning state.
2. **Profile memory** `MEMORY.md` + `USER.md` (Hermes) — one profile, durable, injected as a *frozen snapshot* into the system prompt under hard token caps (~800 / ~500); stable facts only.
3. **Session search** (Hermes) — one profile across all past sessions; searchable recall that carries **no authority** and never gates promotion.
4. **Board memory / handoff payload** (Memoria — Kanban) — one card, travels across profiles; the structured unit of cross-profile communication.
5. **Vault project memory** (Memoria — vault files) — one project across lanes; `research-focus`, open questions, decisions.
6. **Vault audit memory** (Memoria — vault files) — whole vault, append-only; audit trail, snapshots, metrics.

The governing test: **memory is read back as recall; configuration is read as rules** — config (e.g. `project-hints.yaml`) is not a seventh tier. `SOUL.md` is identity, not memory.

## Consequences

- "Where does X live?" becomes answerable by lifespan and scope, which is what makes cross-profile handoffs reliable: the Writer inherits the Librarian's *handoff payload* (board memory), never its session context.
- Profile memory's token caps are load-bearing, not advisory — anything that needs to hold in-flight task state must use board memory instead, and anything durable and project-scoped must use vault project memory, not profile memory.
- The vault is ground truth: a session-search result that contradicts a vault note loses. This keeps recall convenience from quietly overriding canonical knowledge.
- Vault audit memory's append-only constraint is enforced, not merely intended — the Linter's `vault-hash-drift` detector flags files modified outside the trail ([ADR-25](25-session-logging-two-logs.md)), and audit capture must start from day one because cost and human-loop trends cannot be reconstructed retroactively.
- Adding any new place to "remember" something must map onto one of these six (or be reclassified as configuration); a seventh substrate is a schema change that would supersede this ADR.

## Alternatives considered

**One unified memory store.** Rejected: it collapses every cross-session question into "store it and hope," and forces profiles to either share too much (one lane's reasoning leaks into another) or too little (re-deriving the project goal every session). The scoped split is the thin-control-over-thick-state principle applied to memory.

**Store durable facts in profile memory.** Rejected as a general approach: profile memory is per-profile, size-capped, and frozen at session start, so it cannot hold cross-lane project state or in-flight task state without truncation or staleness — those belong in vault project memory and board memory respectively.

## Related

- **Supporting rationale:** [memory-tiers.md](../../docs/explanation/architecture/memory-tiers.md) (the substrate table, per-scope reasoning, and the memory-vs-configuration test).
- **Related decisions:** [ADR-01 three-layer architecture](01-three-layer-architecture.md) and [ADR-22 build on Hermes](22-build-on-hermes-runtime.md) (substrates 1–3 are Hermes-native); [ADR-25 session logging](25-session-logging-two-logs.md) (the append-only audit substrate's enforcement).
- **Reference:** [reference/memory.md](../../docs/reference/memory.md) (the substrate table as lookup).
- **Source discussion:** retroactively records the substrate split already embedded in `memory-tiers.md`. The per-substrate detail evolves there; the six-way split and the recall-vs-rules boundary are what this ADR fixes.
