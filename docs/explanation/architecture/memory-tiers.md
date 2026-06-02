---
title: Memory tiers
parent: Architecture
---

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

## Why each substrate has its scope

The scoping of each substrate is not arbitrary — it follows from what each substrate is responsible for holding, and the cost of getting it wrong.

**Working context** is correctly session-scoped because it is the agent's active reasoning state. Sharing it across profiles would mean the Librarian's in-flight reasoning bleeds into the Writer's session — a cross-contamination with no coherent owner. The cost of discarding it on `/clear` is zero, because anything worth keeping from a session must be written to one of the durable substrates.

**Profile memory** is per-profile and frozen at session start because it is injected as a snapshot into the system prompt. The token caps on `MEMORY.md` (~800 tokens) and `USER.md` (~500 tokens) are load-bearing: profile memory that exceeds these caps gets truncated or degraded. This makes profile memory unsuitable for in-flight task state, which belongs in board memory instead, and appropriate only for stable facts that change infrequently.

**Session search** is the cross-session recall channel but carries no authority. It is searchable history — useful for answering "did we discuss X before?" — but it never gates promotion and is never treated as authoritative over the vault. A session search result that contradicts a vault note loses; the vault is the ground truth.

**Board memory** is per-card rather than per-profile because the handoff is the unit of cross-profile communication. When a card moves from the Librarian lane to the Writer lane, the payload travels with it. The Writer does not inherit the Librarian's conversational context — only the structured handoff payload. This is what makes cross-profile handoffs reliable without requiring profiles to share session state.

**Vault project memory** is the appropriate location for anything that must survive across lanes within a project. Profile memory is too local (scoped to one profile, capped in size) and vault audit memory is too far downstream (aggregate history, not project state). `research-directions.md` is the canonical example: it must be readable by every profile that touches the project, but it is not an audit artifact.

**Vault audit memory** is append-only because its value is the complete, unmodified chain. Profiles read it; only the Linter writes to it. The append-only constraint is not just a policy choice — the Linter's `vault-hash-drift` detector catches files modified outside this trail. Starting audit capture from day one matters because the cost and human-loop trends it tracks cannot be reconstructed retroactively.

---

## Why the substrate split matters

This is the thin-control-over-thick-state principle applied to memory. The Hermes-native layers are deliberately thin — bounded working context, capped profile notes, on-demand session search — so a profile carries minimal persistent state. The durable, compounding knowledge lives in thick files: the board's handoff payloads while work is in flight, and the vault while it's settled.

Without the split, every cross-session question collapses into "store it in memory and hope," and profiles either share too much (leaking context between lanes) or too little (re-deriving the project goal every session). The tiers make "where does X live?" answerable by lifespan and scope.

---

## Configuration is not memory

A frequent miscategorization is trying to store a *fact* in a *config* file, or a *rule* in a memory tier. The six substrates above hold state the system produces and reads back as **recall**; configuration is input you author that the agent reads as **rules**. They're edited at different times by different owners, so keep them distinct:

| If the thing is… | It belongs in… | Not in… |
| --- | --- | --- |
| A durable fact or convention the agent should recall | Profile `MEMORY.md` | `project-hints.yaml` (that's config, not recall) |
| Your working style or preferences | Profile `USER.md` | `MEMORY.md` (keep identity vs. preference separate) |
| Which topics map to which project | `.memoria/project-hints.yaml` (config) | Profile memory or a vault note |
| A synthesized claim or finding | Vault notes (`30-synthesis/`) | Any memory tier |
| Cross-lane project state (open questions, directions) | Vault project memory (`40-workbench/<project>/`) | Profile memory |

The test: **memory is read back as recall; configuration is read as rules.** "Topics `jitai`, `mhealth` belong to the scoping-review project" is a rule (config → [project-hints.yaml](../../how-to-guides/setup/configure-project-hints.md)); "the user prefers British spelling" is recall (profile memory).

---

## Related

**Explanation**

- Board handoff payload (board memory travels here): [Why the card schema is split](../kanban-board/card-schema.md)
- Architecture overview: [Architecture](README.md)

**How-to**

- Configuring project hints (the config example above): [How to configure project hints](../../how-to-guides/setup/configure-project-hints.md)

**Reference**

- Audit log format: [Policy MCP](../../reference/policy-mcp.md)
- The substrate table as reference: [Memory substrates](../../reference/memory.md)

**Background**

- Hermes native memory: [hermes-agent.nousresearch.com/docs/user-guide/features/memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory)
