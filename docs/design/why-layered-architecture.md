---
title: Why the architecture is layered
parent: Design Book
grand_parent: Developers
nav_order: 10
---

# Why the architecture is layered

Memoria separates orchestration, execution, and settled knowledge into distinct
layers. This is not a layering convention; it is the mechanism that makes
retries safe, handoffs lossless, and review enforceable. [ADR-46](../adr/46-seven-layer-architecture.md)
records the older layered decision; alpha.15 implements the same separation
through the standalone CLI, SQLite request table, worker operations, and checked
workspace.

For the current shared vocabulary, start with [Home](../README.md).

---

## The three concerns

Any knowledge production system that uses AI agents must manage three kinds of state:

1. **Active work state** — what tasks are in flight, what's their status, who owns them, what happened when they failed.
2. **Execution context** — which agent is running, what permissions it has, what tools it can use.
3. **Settled knowledge** — what has been established, synthesized, and made available as checked knowledge.

The failure mode of most single-agent or single-document systems is that these three concerns share the same substrate. They collapse together in chat history, in the agent's working memory, or in a flat document store.

---

## What happens when they collapse

| Collapse | Failure | Layered fix |
| --- | --- | --- |
| Orchestration + execution | Work state lives in chat or agent memory; retries duplicate work and handoffs lose context. | A request row records status, operation, input refs, output intents, handoff payload, and failure history. |
| Execution + knowledge | Agents write knowledge directly; confident errors become cited knowledge. | The review gate separates "finished" from "checked." |
| Orchestration + knowledge | Task history pollutes the knowledge graph. | Requests stay in SQLite and the journal; settled knowledge stays in checked workspace Concepts. |

---

## Thin control over thick state

The layered design follows a principle that several independent research systems identified from different starting points:

**[Chen et al. 2026](../reference/bibliography.md#chen2026autonomous)** (*Toward Autonomous Long-Horizon Engineering for ML Research*) describes this as "thin control over thick state": the orchestrator and workers carry as little persistent context as possible; durable knowledge lives in files. Their ablation removes the persistent knowledge layer and measures a drop of 6.41 points on PaperBench and 31.82 points on MLE-Bench Lite. The persistent layer isn't overhead — it's the mechanism that enables long-horizon work.

**AgentRxiv** ([Schmidgall and Moor 2025](../reference/bibliography.md#schmidgall2025agentrxiv)) shows that agents reading prior agent-generated reports gain ~11% over isolated agents on MATH-500. Cross-session knowledge persistence is the mechanism; agents that can't read prior work start from scratch every time.

**PARNESS** ([Wang and Luan 2026](../reference/bibliography.md#wang2026parness)) names "no existing tool persists cross-run knowledge in a form that can be retrieved into a finite LLM context" as one of five structural problems in the field — and addresses it with a persistent knowledge layer. The defining difference is that PARNESS is fully autonomous where Memoria has a blocking human gate.

Unrelated systems, different architectures, one finding: long-horizon agent work fails when state lives in chat and succeeds when state lives in files. (A further corroboration at the claim grain is catalogued in the [Pattern provenance table](../reference/pattern-provenance.md).)

---

## From three layers to seven

The original three-layer framing separated board, workers, and vault, but
conflated two distinctions: *where* things live (structure) and *who* acts
(actor-kind). [ADR-46](../adr/46-seven-layer-architecture.md) pulled them apart
into the seven-layer stack. Alpha.15 keeps the boundary but replaces the board,
MCP, and installed-profile mechanics with CLI/API requests, runtime policy, and
operation manifests.

Each refinement carries the same argument further:

- The **request table and workers** are the control layer, with the **Co-PI**
  posture kept read-only and separated from deterministic operations.
- The **policy boundary** is explicit runtime code rather than an adapter
  convention — naming where allow-listing, write-scoping, and audit actually
  live.
- Deterministic work lives in **operations** — reproducible mechanism that needs
  no installed profile or background lane.
- The **Interface** and the **PI** were named as layers because the strict
  layering claim had to be scoped honestly: in alpha.15 it binds the machine
  write path from CLI/API request envelope through engine, runtime policy,
  operations, storage, and vault materialization. PI edits and operator-managed
  scheduled jobs are direct edges that the engine observes or executes through
  explicit requests.

The file-as-bus, durable-state core — thick files, thin everything else — is unchanged in ADR-46.

---

## The load-bearing rules

The separation is maintained by rules that cannot be violated without breaking the design:

**Requests never hold knowledge.** They track work. Requests close; knowledge
lives in checked workspace Concepts. A request can reference a note or Work by
path or ID; it never *is* that knowledge.

**The agent posture never holds permanent state.** Operations claim requests,
act, and finish; read-only conversation can shape a follow-up request but never
becomes canon. Continuity comes from request/journal state while work is in
flight and checked workspace Concepts once settled.

**The workspace never silently schedules work.** It is the destination, not the
orchestrator. CLI commands, observed file changes, and operator-managed
scheduled jobs create explicit requests.

**The boundary is enforced, not promised.** Runtime policy and the worker
lifecycle intercept machine writes; gated zones degrade to proposals or
quarantine. The boundary isn't "an agent should not write here" — it's "machine
work cannot bypass the checked request/write lifecycle."

---

## Related

**Explanation**

- The seven layers described: [Architecture](../explanation/architecture/README.md)
- How the agent layer is structured: [Why operation postures, not a generalist agent](why-specialist-postures.md)
- Why the vault's review gate is structural: [Why the review gate is structural](why-review-gate-is-structural.md)

**Reference**

- The guard layer in detail: [Policy gate](../reference/policy-mcp.md)
- The thick-state substrate: [Memory substrates](../reference/memory-substrates.md)
