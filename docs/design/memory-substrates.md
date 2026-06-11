---
topic: explorations
title: Memory substrates — seven scoped stores, not one
status: as-built
created: 2026-06-09
parent: Design notes
grand_parent: Explanation
nav_order: 14
---

# Memory substrates — seven scoped stores, not one

A design capture of where Memoria's state actually lives in v0.1.1. "Memory" is not
one store but seven, each with a distinct scope, lifespan, and owner — three provided
by the Hermes runtime, four by Memoria in the vault. Reconstructed from
[ADR-23](../adr/23-scoped-memory-substrates.md) and the real on-disk locations.

> **Why capture this.** ADR-23 names the substrates; this grounds each to its real
> path (or marks it runtime-internal), which matters because three of the four
> Memoria substrates are ordinary vault files a human reads and edits directly.
> Note: the ADR filename still says `six` for link stability, but the set is **seven**
> (substrate 5 was split into project + program memory on 2026-06-02).

## What it is

Seven substrates, ordered from most transient to most durable:

| # | Substrate | Owner | Scope | Lifespan | Where it lives |
|---|---|---|---|---|---|
| 1 | **Working memory** | Hermes | one session | cleared on `/clear` | in-context reasoning state |
| 2 | **Agent memory** | Hermes | **the co-PI only**, all sessions | durable; frozen snapshot at session start | `~/.hermes/profiles/memoria-copi/memories/` (`MEMORY.md`, `USER.md`) |
| 3 | **Session history** | Hermes | one profile, all past sessions | indefinite; searchable | `~/.hermes/state.db` (SQLite) |
| 4 | **Handoff memory** | Memoria | one card, across lanes | card-bound | Kanban card `metadata` field (`~/.hermes/kanban.db`) |
| 5 | **Project memory** | Memoria | one project, across lanes | bounded; archives with project | `projects/<project>/` |
| 6 | **Program memory** | Memoria | whole research program | persistent | `research-focus.md` (vault root) |
| 7 | **Audit memory** | Memoria | whole vault | indefinite; append-only | `system/logs/` + `system/metrics/` |

## How it works

**The Hermes substrates (1–3)** are runtime-internal — no vault path. Working memory
is the live context, gone on `/clear`. Agent memory is a `MEMORY.md` / `USER.md`
pair, frozen as a snapshot when a session starts so mid-session writes don't shift
the agent's footing. In v0.1.1 it belongs to the **co-PI alone** — the four
specialist lanes ship with `memory` in `agent.disabled_toolsets`, because a
dispatched worker gets everything it needs from the handoff payload and the vault
([ADR-48](../adr/48-copi-and-agent-consolidation.md), D46). Session history is a
searchable SQLite log of past sessions, the substrate behind cross-session recall;
it carries no authority — a history result that contradicts a vault note loses.

**The Memoria substrates (4–7)** are the ones a human can see and steer:

- **Handoff memory** travels *with the work*. When the co-PI delegates (the tasks
  MCP's `delegate_route_task`) or a card moves between lanes, the context — goal,
  allowed paths, expected outputs, review checks — rides in the card's `metadata`,
  not in any agent's head. This is what makes the board a state machine rather than
  a queue.
- **Project memory** is the project folder. Everything scoped to one project — open
  questions, decisions, framing, drafts, code — lives under `projects/<project>/`
  and archives as a unit when the project closes. (The full Project workspace that
  exercises this substrate is v0.1.2 scope, D39/D52; the folder and its lane scopes
  ship now.)
- **Program memory** is the steering layer. [`research-focus.md`](../../src/research-focus.md)
  carries current priorities, open questions, and synthesis gaps; the Librarian reads
  it at session start to weight discovery, and the co-PI brings it into conversation.
  It is human-maintained, refreshed in the weekly (Friday) ritual. A per-program
  `screening-protocol.md` is part of the same substrate but ships only when the
  systematic-review mode is adopted ([ADR-16](../adr/16-systematic-review-adopt-on-demand.md)
  — adopt-on-demand, not installed by default).
- **Audit memory** is the permanent trail — `system/logs/audit.jsonl` plus the
  operational logs (`capture-intake.jsonl`, `classify.jsonl`, `patterns.jsonl`, the
  board projections) and the derived `system/metrics/` notes (see
  [Session logging and audit — two logs, tamper-evidence, fleet trust](session-logging-and-audit.md)).

## Design rationale

- **One store would collapse scopes that must stay separate.** Session-scoped scratch,
  card-bound handoff context, program-wide steering, and a permanent audit trail have
  different lifespans and owners; one store forces one lifespan and loses the
  distinctions that make permission and cleanup tractable.
- **State travels with work, not with agents.** Putting handoff context on the card
  (not in agent memory) is what lets a stateless worker pick up a card mid-pipeline and
  continue — the durable-state-over-chat thesis of the three-layer architecture.
- **The steering layer is a plain file on purpose.** Program memory is `research-focus.md`
  precisely so the human edits it directly; the agent reads it, never owns it.
- **Frozen agent snapshots.** Freezing `MEMORY.md` at session start prevents an agent
  from rewriting its own footing mid-task — memory is stable within a session.
- **One agent compounds; the lanes stay stateless.** Concentrating agent memory in
  the co-PI is the ADR-48 consolidation applied to memory: one conversational
  context that grows into a genuine co-PI, instead of seven part-memories that
  reset and drift.

## Related

- [ADR-23](../adr/23-scoped-memory-substrates.md)
- [Memory systems and benchmarks — the evidence behind durable state](memory-systems-and-benchmarks.md) — the (pending) evidence behind durable state
- [Session logging and audit — two logs, tamper-evidence, fleet trust](session-logging-and-audit.md) — audit memory in detail
- [Profiles and the SOUL model — one co-PI, four lanes, no orchestrator](profiles-and-soul-model.md) — why agent memory is the co-PI's alone
- Explanation: [`docs/explanation/architecture/memory-model.md`](../explanation/architecture/memory-model.md); Reference: [`docs/reference/memory.md`](../reference/memory.md)
