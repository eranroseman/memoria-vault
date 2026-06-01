# Architecture

Memoria has three layers — a Kanban board that orchestrates work, seven Hermes profiles that execute it, and an Obsidian vault that stores durable knowledge. The layers are connected through explicit handoffs but never collapsed into one.

```text
┌──────────────────────────────────────────────────────────────────┐
│  Board layer (Kanban) — orchestration and memory of active work  │
│  triage → todo → ready → running → done → archived               │
│  review overlay on done: requested → approved                    │
└──────────────────────────┬───────────────────────────────────────┘
                           │ assigns lane / advances state
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  Worker layer (Hermes) — seven profiles execute in their lanes   │
│  Librarian · Mapper · Socratic · Writer · Verifier · Coder       |
|  · Linter                                                        │
└──────────────────────────┬───────────────────────────────────────┘
                           │ every write checked by the policy MCP
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  Vault layer (Obsidian) — durable knowledge by lifecycle stage   │
│  00-meta · 10-inbox · 20-sources · 30-synthesis                  │
│  40-workbench · 50-deliverables · 90-assets · 95-archive         │
└──────────────────────────────────────────────────────────────────┘
```

---

## The three layers and their roles

**The board is the control plane.** It persists every task as a card with status, assignee, and history, and keeps the card alive until a human review gate is passed. The board never holds knowledge — it tracks work. Cards are transient; they die at `archived`. Knowledge lives in the vault.

**The worker layer is seven specialist profiles.** Each profile has narrow permissions, a focused command surface, and a clear exit condition. Profiles execute against the board's cards; they don't decide what work to do or what to keep. There is no Orchestrator profile and no Reviewer profile.

**The vault is the durable memory.** It stores knowledge organized by lifecycle stage. Nothing enters the canonical zones (`30-synthesis/`, `50-deliverables/`) without a human review approval. The vault is the destination, not the orchestrator.

---

## What this architecture prevents

**The most common failure mode of agent-assisted knowledge work** is state living in chat. When a session ends, the context is gone. The next agent starts fresh and produces redundant work, misses prior decisions, or contradicts earlier synthesis.

Memoria addresses this by design: the board persists in-flight state across sessions; the vault persists settled knowledge. Workers re-ground on those files between steps rather than relying on conversational continuity. This is "thin control over thick state" — the agents carry as little context as possible; the durable artifacts carry the memory.

Three independent research systems (Chen 2026, AgentRxiv 2025, PARNESS 2026) reach the same conclusion from different starting points: long-horizon agent work fails when state lives in chat and succeeds when state lives in files. The three-layer split is the structural form of that finding. See [why-three-layers.md](why-three-layers.md) for the full reasoning.

---

## Why these three specifically

The three layers correspond to three concerns that must be kept separate for the system to be reliable:

- *What work is in progress* — the board's concern.
- *Who is executing it and under what permissions* — the worker layer's concern.
- *What stable knowledge has accumulated* — the vault's concern.

Collapsing any two creates problems. Board + workers collapsed means work state lives in agent memory (lost between sessions). Workers + vault collapsed means agents write canonical knowledge without review. Board + vault collapsed means task history pollutes the knowledge graph. See [why-three-layers.md](why-three-layers.md) for each failure mode in detail.

---

## Documents in this section

- **[why-three-layers.md](why-three-layers.md)** — the thin-control-thick-state principle and what breaks without separation.
- **[why-specialist-profiles.md](why-specialist-profiles.md)** — why seven specialists instead of one generalist, and why there is no Orchestrator.
- **[why-human-gate.md](why-human-gate.md)** — why the review gate is structural, not advisory.
- **[why-not-autonomous.md](why-not-autonomous.md)** — the autonomy ceiling: why Memoria doesn't pursue L4/L5 autonomy for synthesis.

Structural topics in this section also include **[control-plane.md](control-plane.md)**, **[memory-tiers.md](memory-tiers.md)**, **[human-channels.md](human-channels.md)**, **[distribution-model.md](distribution-model.md)**, **[why-pattern-provenance.md](why-pattern-provenance.md)**, **[why-computational-methods.md](why-computational-methods.md)**, **[vault.md](vault.md)** (the vault as a knowledge structure), and **[session-logging.md](session-logging.md)** (what each session records).

## `why-*` explanations vs. ADRs

The `why-*` files here and the ADRs in [project-files/decisions/](../../../project-files/decisions/) are deliberately different artifacts, and the boundary matters:

- A **`why-*` explanation** is the *durable conceptual argument* — why the design is shaped this way, written to be read and re-read. It carries no date and no status; it is maintained as the canonical reasoning.
- An **ADR** is the *dated decision record* — what was decided, when, the alternatives weighed, and the status. It is immutable once accepted.

When the two cover the same ground (e.g. [why-human-gate.md](why-human-gate.md) and the structural-review-gate ADR), the explanation holds the argument and the ADR holds the decision; each should link to the other rather than restate it. If you change the reasoning, update the `why-*` file; if you reverse the decision, supersede the ADR.

For operational reference (permission matrices, command lists, config formats), see [reference/](../../reference/).
