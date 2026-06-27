---
title: Why the architecture is layered
parent: Design rationale
nav_order: 1
---

# Why the architecture is layered

Memoria separates orchestration, execution, and settled knowledge into distinct layers. This is not a layering convention; it is the mechanism that makes retries safe, handoffs lossless, and review enforceable. The argument was first made for three layers ([ADR-01](../../adr/01-three-layer-architecture.md): board, workers, vault) and survives intact in the seven-layer stack that superseded it ([ADR-46](../../adr/46-seven-layer-architecture.md)) — the refinement added layers; it never weakened the separation.

For the current shared vocabulary, start with [The model](../../the-model.md).

---

## The three concerns

Any knowledge production system that uses AI agents must manage three kinds of state:

1. **Active work state** — what tasks are in flight, what's their status, who owns them, what happened when they failed.
2. **Execution context** — which agent is running, what permissions it has, what tools it can use.
3. **Settled knowledge** — what has been established, synthesized, and approved as canonical.

The failure mode of most single-agent or single-document systems is that these three concerns share the same substrate. They collapse together in chat history, in the agent's working memory, or in a flat document store.

---

## What happens when they collapse

**Orchestration + execution collapsed (no separate board):**
Work state lives in agent memory or chat context. When a session ends, the state is gone. The next session starts fresh: it doesn't know what was already done, what failed and why, or where the previous worker left off. Retries duplicate work. Handoffs lose context. Long-horizon tasks that span multiple sessions become unreliable.

**Execution + knowledge collapsed (agents write canon directly):**
There is no gate between "the agent finished" and "this is now trusted information." A confidently-wrong agent writes claims that downstream work cites — and those errors compound.

**Orchestration + knowledge collapsed (tasks and knowledge share a store):**
Task history pollutes the knowledge graph. In-flight notes get confused with settled notes, and there is no structural way to tell them apart. Queries against the vault return noise.

---

## Thin control over thick state

The layered design follows a principle that several independent research systems identified from different starting points:

**[Chen et al. 2026](../../reference/bibliography.md#chen2026autonomous)** (*Toward Autonomous Long-Horizon Engineering for ML Research*) describes this as "thin control over thick state": the orchestrator and workers carry as little persistent context as possible; durable knowledge lives in files. Their ablation removes the persistent knowledge layer and measures a drop of 6.41 points on PaperBench and 31.82 points on MLE-Bench Lite. The persistent layer isn't overhead — it's the mechanism that enables long-horizon work.

**AgentRxiv** ([Schmidgall and Moor 2025](../../reference/bibliography.md#schmidgall2025agentrxiv)) shows that agents reading prior agent-generated reports gain ~11% over isolated agents on MATH-500. Cross-session knowledge persistence is the mechanism; agents that can't read prior work start from scratch every time.

**PARNESS** ([Wang and Luan 2026](../../reference/bibliography.md#wang2026parness)) names "no existing tool persists cross-run knowledge in a form that can be retrieved into a finite LLM context" as one of five structural problems in the field — and addresses it with a persistent knowledge layer. The defining difference is that PARNESS is fully autonomous where Memoria has a blocking human gate.

Unrelated systems, different architectures, one finding: long-horizon agent work fails when state lives in chat and succeeds when state lives in files. (A further corroboration at the claim grain is catalogued in [Pattern provenance: borrow, adapt, ignore](why-pattern-provenance.md).)

---

## From three layers to seven

ADR-01's three layers framed the original infrastructure, but conflated two distinctions: *where* things live (structure) and *who* acts (actor-kind). [ADR-46](../../adr/46-seven-layer-architecture.md) pulled them apart and superseded ADR-01 with the seven-layer stack: **PI · Interface · Co-PI · Tasks · MCP · Operations · Vault.**

Each refinement carries the same argument further:

- The **board and workers** became the **Tasks** layer, with the **Co-PI** lifted out as its own layer — the one agent that converses and remembers, separated from the stateless lanes that execute.
- The **policy boundary** became an explicit layer (**MCP**) rather than an implementation detail of the worker layer — naming where allow-listing, write-scoping, and audit actually live.
- Deterministic work was pulled out of the worker set into **operations** — reproducible mechanism that needs no posture and no lane.
- The **Interface** and the **PI** were named as layers because the strict layering claim had to be scoped honestly: it binds the *agent write-path* (Co-PI → Tasks → MCP → Operations/Vault); the PI and cron/CI are direct edges.

The file-as-bus, durable-state core — thick files, thin everything else — is unchanged from ADR-01 to ADR-46.

---

## The load-bearing rules

The separation is maintained by rules that cannot be violated without breaking the design:

**The board never holds knowledge.** It tracks work. Cards die at `archived`; knowledge lives in the vault. A card can reference a vault note by path; it never *is* a note.

**The agents never hold permanent state.** Lanes claim cards, act, and release; the Co-PI's memory holds working style and conventions, never canon. Continuity comes from the board (in-flight) or the vault (settled).

**The vault never schedules work.** It is the destination, not the orchestrator. A vault note does not trigger agent action; a board card does.

**The boundary is enforced, not promised.** The policy MCP intercepts every agent write; the gated zones degrade to proposals for every lane. The boundary isn't "an agent should not write here" — it's "an agent cannot write here."

---

## Related

**Explanation**

- The seven layers described: [Architecture](../architecture/README.md)
- How the agent layer is structured: [Why specialist profiles, not a generalist agent](why-specialist-profiles.md)
- Why the vault's review gate is structural: [Why the review gate is structural](why-human-gate.md)

**Reference**

- The guard layer in detail: [Policy MCP](../../reference/policy-mcp.md)
- The thick-state substrate: [Memory substrates](../../reference/memory.md)
