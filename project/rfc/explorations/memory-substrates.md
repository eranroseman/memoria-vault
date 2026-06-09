---
topic: proposals
title: Memory substrates — seven scoped stores, not one
status: as-built
created: 2026-06-09
---

# Memory substrates — seven scoped stores, not one

A design capture of where Memoria's state actually lives. "Memory" is not one store
but seven, each with a distinct scope, lifespan, and owner — three provided by the
Hermes runtime, four by Memoria in the vault. Reconstructed from
[ADR-23](../../adr/23-six-memory-substrates.md) and the real on-disk locations.

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
| 2 | **Agent memory** | Hermes | one profile, all sessions | durable; frozen snapshot at session start | `~/.hermes/profiles/memoria-<name>/memories/` (`MEMORY.md`, `USER.md`) |
| 3 | **Session history** | Hermes | one profile, all past sessions | indefinite; searchable | `~/.hermes/state.db` (SQLite) |
| 4 | **Handoff memory** | Memoria | one card, across profiles | card-bound | Kanban card `metadata` field (`~/.hermes/kanban.db`) |
| 5 | **Project memory** | Memoria | one sub-project, across lanes | bounded; archives with project | `40-workbench/<project>/` |
| 6 | **Program memory** | Memoria | whole research program | persistent | `research-focus.md`, `screening-protocol.md` |
| 7 | **Audit memory** | Memoria | whole vault | indefinite; append-only | `99-system/logs/audit.jsonl` + `sessions/` |

## How it works

**The Hermes substrates (1–3)** are runtime-internal — no vault path. Working memory
is the live context, gone on `/clear`. Agent memory is a per-profile `MEMORY.md` /
`USER.md` pair, frozen as a snapshot when a session starts so mid-session writes don't
shift the agent's footing. Session history is a searchable SQLite log of past
sessions, the substrate behind cross-session recall.

**The Memoria substrates (4–7)** are the ones a human can see and steer:

- **Handoff memory** travels *with the work*. When a card moves between lanes
  (Librarian → Verifier → Writer), the context rides in the card's `metadata`, not in
  any agent's head — this is what makes the board a state machine rather than a queue.
- **Project memory** is the workbench. Everything scoped to one project — map, framing,
  drafts, verification, code — lives under `40-workbench/<project>/` and archives as a
  unit when the project closes.
- **Program memory** is the steering layer. [`research-focus.md`](../../../vault/research-focus.md)
  carries current priorities, open questions, and synthesis gaps; the Librarian reads
  it at session start to weight discovery. It is human-maintained, refreshed in the
  weekly (Friday) ritual. `screening-protocol.md` holds per-program inclusion criteria.
- **Audit memory** is the permanent trail — the hash-chained `audit.jsonl` plus the
  never-rotated `sessions/` summaries (see
  [session-logging-and-audit.md](session-logging-and-audit.md)).

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

## Related

- [ADR-23](../../adr/23-six-memory-substrates.md)
- [memory-systems-and-benchmarks.md](memory-systems-and-benchmarks.md) — the (pending) evidence behind durable state
- [session-logging-and-audit.md](session-logging-and-audit.md) — audit memory in detail
- [profiles-and-soul-model.md](profiles-and-soul-model.md) — agent memory is per-profile
- Explanation: [`docs/explanation/architecture/memory-model.md`](../../../docs/explanation/architecture/memory-model.md); Reference: [`docs/reference/memory.md`](../../../docs/reference/memory.md)
