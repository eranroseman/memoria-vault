---
topic: architecture
---

# Memory tiers

"Memory" in Memoria is not one thing — it operates across several scopes with different lifespans, backing stores, and owners. Confusing the scopes is the source of most "the agent forgot" and "the agent remembered something it shouldn't have" bugs.

Two of these scopes are **provided by [Hermes Agent](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) natively**; two are **substrates Memoria adds on top** (the Kanban board and the vault). Naming which substrate a piece of state lives in is the whole point of this document — it answers "where does X belong?" with a single right answer.

## The substrates

| Tier | Substrate | Scope | Lifespan | Backing store | What it holds |
| --- | --- | --- | --- | --- | --- |
| **Working context** | Hermes-native | One profile session | Session-bound; cleared on `/clear` | In-context (the live conversation) | Current goal, recent tool results, in-flight reasoning. |
| **Profile memory** (`MEMORY.md` + `USER.md`) | Hermes-native | One Hermes profile | Durable; frozen-snapshot at session start | `~/.hermes/profiles/memoria-<name>/memories/` | `MEMORY.md` (~800 tokens): environment facts, conventions, things the profile learned. `USER.md` (~500 tokens): human preferences and working style. Injected into the system prompt as a frozen snapshot when the session starts. (Approximate caps as of current Hermes runtime — verify in upstream docs.) |
| **Session search** | Hermes-native | One profile, all past sessions | Indefinite; unlimited capacity | SQLite at `~/.hermes/state.db` (full-text) | Searchable history of prior conversations. Retrieved on demand, not injected — so it costs no system-prompt tokens until queried. |
| **Board memory** (handoff payload) | Memoria — Kanban | One card (travels across profiles) | Card-bound; lives with the active card | The card's `metadata` field | The handoff: goal, context, allowed paths, expected outputs, recent handoff summary, the working set of paper notes. |
| **Vault project memory** | Memoria — vault files | One project, across lanes | Project-bound | `40-workbench/<project>/` | `research-directions`, open questions, decisions log. Shared across every profile that touches the project. |
| **Vault audit memory** | Memoria — vault files | The whole vault | Indefinite; append-only, never overwritten | `00-meta/02-logs/` (+ `00-meta/08-metrics/`) | Audit trail, snapshots, weekly summaries, fleet metrics. The long-term operational record. (Renamed from "episodic archive" — it is operational logging, not autobiographical event memory.) |

`SOUL.md` is adjacent but is *not* memory: it is the profile's identity prompt (slot #1), stable across sessions by design. See [profiles/README.md](../profiles/README.md#per-profile-contracts).

## Rules

- **Working context is not shared and does not persist.** The Librarian's in-session reasoning does not bleed into the Writer's session, and `/clear` discards it. Anything worth keeping must be written to one of the durable substrates below.
- **Profile memory is per-profile, frozen at session start.** Because `MEMORY.md` / `USER.md` are injected as a snapshot, a mid-session write isn't seen until the next session. Keep them small (the token caps are load-bearing — approximate values in the table above; verify current limits in upstream Hermes docs) and reserve them for *stable* facts — not in-flight task state, which belongs in board memory. Per-machine by default; under multi-machine deployment it can follow the human between devices via the [`memories/` junction](../../project/roadmap/sync-and-coordination.md#syncing-profile-memory-across-machines-the-memories-junction).
- **Session search is the cross-session recall channel, not a planning store.** Use it to answer "did we discuss X before?" cheaply. It is read-only history; it never gates promotion and is never authoritative over the vault.
- **Board memory is per-card, not per-profile.** When a card moves from the Librarian lane to the Writer lane, the handoff payload travels with it (see [kanban-board/card-schema.md](../../reference/card-schema.md#structured-payload)). The Writer does not inherit the Librarian's working context — only the payload.
- **Vault project memory is the cross-lane channel.** Anything that must survive across lanes within a project belongs here — not in profile memory (too local, capped) and not in vault audit memory (too distant). `research-directions.md` is the definitive example.
- **Vault audit memory is append-only.** Profiles read it; only the Linter writes to it. `00-meta/02-logs/audit.jsonl` is part of it today; `00-meta/08-metrics/` joins when [fleet observability](../../project/roadmap/future-directions.md#fleet-observability) ships (Post-MVS).
- **The audit event records outcomes, not just diffs.** Beyond *what changed* (path, `before_hash` / `after_hash`), each run's event carries **disposition** (the `review_status` outcome), **cost** (tokens / $), **tool-call outcome**, and **verify result**. This one substrate is what the observability metrics aggregate from (see [roadmap/success-metrics.md](../../project/roadmap/success-metrics.md) and [roadmap/evaluation.md](../../project/roadmap/evaluation.md)); capture it from day one, because human-loop and cost trends cannot be reconstructed retroactively.

## Why the substrate split matters

This is the **thin control over thick state** principle (see [architecture/README.md](README.md#thin-control-over-thick-state)) applied to memory. The Hermes-native layers are deliberately *thin* — bounded working context, capped profile notes, on-demand session search — so a profile carries minimal persistent state. The durable, compounding knowledge lives in *thick* files: the board's handoff payloads while work is in flight, and the vault while it's settled. Workers re-ground on those files between steps rather than relying on conversational memory.

Without the split, every cross-session question collapses into "store it in memory and hope," and profiles either share too much (leaking context between lanes) or too little (re-deriving the project goal every session). The tiers make "where does X live?" answerable by lifespan and scope.

## Related

- Hermes Agent's native memory model: [hermes-agent.nousresearch.com/docs/user-guide/features/memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory)
- Task packet (how board memory travels between profiles): [kanban-board/card-schema.md](../../reference/card-schema.md#structured-payload)
- Vault project-memory pattern: [workflows/README.md](../../how-to/workflows/README.md)
- Audit log location: `00-meta/02-logs/audit.jsonl` (see [architecture/policy-mcp.md](../../reference/architecture/policy-mcp.md))
- Thin control over thick state: [architecture/README.md](README.md#thin-control-over-thick-state)
