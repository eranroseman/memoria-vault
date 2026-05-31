# Memory tiers

"Memory" in Memoria is not one thing. It operates across six substrates with different lifespans, backing stores, and owners. Confusing the scopes is the source of most "the agent forgot" and "the agent remembered something it shouldn't" problems.

Two of these scopes are provided by Hermes natively; four are substrates Memoria adds on top.

---

## The six substrates

| Tier | Substrate | Scope | Lifespan | What it holds |
| --- | --- | --- | --- | --- |
| **Working context** | Hermes-native | One profile session | Session-bound; cleared on `/clear` | Current goal, recent tool results, in-flight reasoning |
| **Profile memory** (`MEMORY.md` + `USER.md`) | Hermes-native | One Hermes profile | Durable; frozen-snapshot at session start | `MEMORY.md` (~800 tokens): environment facts, conventions, learned preferences. `USER.md` (~500 tokens): human working style. Injected into the system prompt as a frozen snapshot. |
| **Session search** | Hermes-native | One profile, all past sessions | Indefinite, unlimited | Searchable history of prior conversations. Retrieved on demand — costs no system-prompt tokens until queried. |
| **Board memory** (handoff payload) | Memoria — Kanban | One card, travels across profiles | Card-bound | The handoff: goal, context, allowed paths, expected outputs, the working set of notes |
| **Vault project memory** | Memoria — vault files | One project, across lanes | Project-bound | `research-directions`, open questions, decisions log. Shared across every profile that touches the project. |
| **Vault audit memory** | Memoria — vault files | The whole vault | Indefinite, append-only | Audit trail, snapshots, weekly summaries, fleet metrics |

`SOUL.md` is adjacent but is *not* memory — it is the profile's identity prompt, stable across sessions by design.

---

## Rules

**Working context is not shared and does not persist.** The Librarian's in-session reasoning does not bleed into the Writer's session, and `/clear` discards it. Anything worth keeping must be written to one of the durable substrates.

**Profile memory is per-profile and frozen at session start.** Because `MEMORY.md` and `USER.md` are injected as a snapshot, a mid-session write isn't visible until the next session. Keep them small — the token caps are load-bearing — and reserve them for stable facts, not in-flight task state (which belongs in board memory).

**Session search is the cross-session recall channel, not a planning store.** Use it to answer "did we discuss X before?" cheaply. It is read-only history; it never gates promotion and is never authoritative over the vault.

**Board memory is per-card, not per-profile.** When a card moves from the Librarian lane to the Writer lane, the handoff payload travels with it. The Writer does not inherit the Librarian's working context — only the structured payload.

**Vault project memory is the cross-lane channel.** Anything that must survive across lanes within a project belongs here — not in profile memory (too local, capped) and not in vault audit memory (too distant). `research-directions.md` is the defining example.

**Vault audit memory is append-only.** Profiles read it; only the Linter writes to it. Capture it from day one — human-loop and cost trends cannot be reconstructed retroactively.

---

## Why the substrate split matters

This is the thin-control-over-thick-state principle applied to memory. The Hermes-native layers are deliberately thin — bounded working context, capped profile notes, on-demand session search — so a profile carries minimal persistent state. The durable, compounding knowledge lives in thick files: the board's handoff payloads while work is in flight, and the vault while it's settled.

Without the split, every cross-session question collapses into "store it in memory and hope," and profiles either share too much (leaking context between lanes) or too little (re-deriving the project goal every session). The tiers make "where does X live?" answerable by lifespan and scope.

---

## Related

- Hermes native memory: [hermes-agent.nousresearch.com/docs/user-guide/features/memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory)
- Board handoff payload (board memory travels here): [explanation/kanban-board/card-schema.md](../kanban-board/card-schema.md)
- Audit log format: [reference/architecture/policy-mcp.md](../../reference/architecture/policy-mcp.md)
- Architecture overview: [explanation/architecture/README.md](README.md)
