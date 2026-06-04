---
topic: decisions
id: 23
title: Memory is seven scoped substrates, not one store
status: accepted
date_proposed: 2026-06-01
date_resolved: 2026-06-02
supersedes: []
superseded_by: []
---

# ADR-23: Memory is seven scoped substrates, not one store

> **Revised 2026-06-02.** Originally six substrates. Substrate 5 ("vault project memory") was split into **project memory** and **program memory**, and the set was renamed for self-explanatory, scope-faithful names. Updated in place rather than superseded — this extends the same decision a day after it was recorded, it does not reverse it. (The filename retains `six` for link stability; the title, body, and count are authoritative at **seven**.)

## Context

"Memory" in Memoria is not one thing, and treating it as one is the source of most "the agent forgot" and "the agent remembered something it shouldn't" failures. Every profile's read/write boundary depends on which substrate holds a given fact, yet the split was only described in [the memory model](../../docs/explanation/architecture/memory-model.md) and never recorded as a decision. Because the substrate boundaries are what keep one lane's in-flight reasoning from leaking into another's — and what keep durable knowledge out of size-capped, session-frozen stores — the split deserves a fixed anchor rather than living only in mutable prose.

## Decision

Memoria's memory is **seven distinct substrates**, each with its own scope, lifespan, backing store, and owner — **three** provided by Hermes natively (Working memory, Agent memory, Session history), **four** added by Memoria:

1. **Working memory** (Hermes) — one session, cleared on `/clear`; active reasoning state.
2. **Agent memory** `MEMORY.md` + `USER.md` (Hermes) — one agent (profile), durable, injected as a *frozen snapshot* into the system prompt under hard token caps (~800 / ~500); stable facts only.
3. **Session history** (Hermes) — one agent across all past sessions; searchable recall that carries **no authority** and never gates promotion.
4. **Handoff memory** (Memoria — Kanban) — one card, travels across profiles; the structured unit of cross-profile communication.
5. **Project memory** (Memoria — vault files) — one sub-project across lanes; open questions, decisions, framing; archives with the project.
6. **Program memory** (Memoria — vault files) — the whole research program; the human's standing steering (`research-focus`, `screening-protocol`); persistent.
7. **Audit memory** (Memoria — vault files) — whole vault, append-only; audit trail, snapshots, metrics.

A **substrate** is one of these seven categories; its **backing** is the store behind it (Hermes / Kanban / vault files). The governing test: **memory is read back as recall; configuration is read as rules** — config (e.g. `project-hints.yaml`) is not an eighth substrate. `SOUL.md` is identity, not memory.

## Why

- Substrate boundaries exist to keep each profile's read/write/retention rules clean; lumping facts of different scope or lifespan into one store is what produces the "forgot / shouldn't-have-remembered" failures.
- Program steering (persistent, program-wide — `research-focus`) and project working state (bounded, per-project) differ on scope, lifespan, and cardinality, so they are separate substrates, not one "project memory."
- Each name states its scope/role, so "where does X live?" is answerable from the name alone.

## Consequences

- "Where does X live?" becomes answerable by lifespan and scope, which is what makes cross-profile handoffs reliable: the Writer inherits the Librarian's *handoff payload* (handoff memory), never its session context.
- Agent memory's token caps are load-bearing, not advisory — in-flight task state must use handoff memory; cross-project standing steering uses program memory; one project's working state uses project memory.
- The vault is ground truth: a session-history result that contradicts a vault note loses.
- Audit memory's append-only constraint is enforced — the Linter's `vault-hash-drift` detector flags files modified outside the trail ([ADR-25](25-session-logging-two-logs.md)); audit capture must start from day one because cost and human-loop trends cannot be reconstructed retroactively.
- Adding an eighth place to "remember" something must map onto one of these seven (or be reclassified as configuration); an eighth substrate is a schema change that would supersede this ADR.

## Alternatives considered

**One unified memory store.** Rejected: it collapses every cross-session question into "store it and hope," and forces profiles to share too much (one lane's reasoning leaks into another) or too little (re-deriving the project goal every session). The scoped split is thin-control-over-thick-state applied to memory.

**Keep program and project as one "vault project memory" substrate.** Rejected (2026-06-02): a program-wide, persistent steering file and per-project, bounded scratch are different memory on every axis but "human-owned vault file" — merging them mislabels the substrate and buries `research-focus` as one example among others.

**Store durable facts in agent memory.** Rejected as a general approach: agent memory is per-profile, size-capped, and frozen at session start, so it cannot hold cross-lane or in-flight state without truncation or staleness — those belong in program/project memory and handoff memory respectively.

## Related

- **Supporting rationale:** [the memory model](../../docs/explanation/architecture/memory-model.md) (the substrate table, per-scope reasoning, and the memory-vs-configuration test).
- **Related decisions:** [ADR-01 three-layer architecture](01-three-layer-architecture.md) and [ADR-22 build on Hermes](22-build-on-hermes-runtime.md) (substrates 1–3 are Hermes-native); [ADR-25 session logging](25-session-logging-two-logs.md) (the append-only audit substrate's enforcement).
- **Reference:** [Memory substrates](../../docs/reference/memory.md) (the substrate table as lookup).
