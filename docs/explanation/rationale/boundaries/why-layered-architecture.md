---
title: Why the architecture is layered
parent: Boundaries
grand_parent: Design rationale
nav_order: 2
---

# Why the architecture is layered

Memoria separates orchestration, execution, and settled knowledge because those
states fail differently. The separation makes retries safe, handoffs lossless,
and review enforceable. The
[alpha.15 standalone engine checkpoint](https://github.com/eranroseman/memoria-vault/blob/main/design-history/15-alpha.15.md)
records the older layered version of this rule; the current standalone baseline
implements the same separation through the CLI, SQLite request table, worker
operations, and checked workspace.

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

The rule is: keep control thin and state thick. Orchestrators and workers should
carry as little persistent context as possible; durable knowledge should live in
retrievable files.

Three independent systems point to the same shape:

- **[Chen et al. 2026](../../../reference/evidence-and-integrations/bibliography.md#chen2026autonomous)**
  names "thin control over thick state." Removing the persistent knowledge layer
  drops PaperBench by 6.41 points and MLE-Bench Lite by 31.82 points.
- **AgentRxiv** ([Schmidgall and Moor 2025](../../../reference/evidence-and-integrations/bibliography.md#schmidgall2025agentrxiv))
  shows an ~11% MATH-500 gain when agents can read prior agent-generated
  reports instead of starting from scratch.
- **PARNESS** ([Wang and Luan 2026](../../../reference/evidence-and-integrations/bibliography.md#wang2026parness))
  treats retrievable cross-run knowledge as a structural requirement. It differs
  from Memoria by pursuing full autonomy; Memoria keeps the blocking human gate.

Different systems, same finding: long-horizon agent work fails when state lives
in chat and succeeds when durable knowledge lives in files. The
[Pattern provenance table](../../../reference/evidence-and-integrations/pattern-provenance.md) tracks the
claim-level corroboration.

---

## From three layers to seven

The original three-layer framing separated board, workers, and vault, but
conflated two distinctions: *where* things live (structure) and *who* acts
(actor-kind). [The alpha.15 standalone engine checkpoint](https://github.com/eranroseman/memoria-vault/blob/main/design-history/15-alpha.15.md) pulled them apart
into the seven-layer stack. The current standalone baseline keeps that boundary
but replaces the board, MCP, and installed-profile mechanics with CLI/API
requests, runtime policy, and operation manifests.

Each refinement carries the same argument further:

- The **request table and workers** are the control layer, with the **Co-PI**
  posture kept read-only and separated from deterministic operations.
- The **policy boundary** is explicit runtime code rather than an adapter
  convention — naming where allow-listing, write-scoping, and audit actually
  live.
- Deterministic work lives in **operations** — reproducible mechanism that needs
  no installed profile or background lane.
- The **Interface** and the **PI** are named layers so the boundary is scoped
  honestly: it binds the machine write path. PI edits and operator-managed
  scheduled jobs are direct edges the engine observes or executes through
  explicit requests.

The file-as-bus, durable-state core — thick files, thin everything else — is unchanged in [the alpha.15 standalone engine checkpoint](https://github.com/eranroseman/memoria-vault/blob/main/design-history/15-alpha.15.md).

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

- The seven layers described: [Architecture](../../architecture/README.md)
- How the agent layer is structured: [Why operation postures](why-operation-postures.md)
- Why the vault's review gate is structural: [Why the review gate is structural](why-review-gate-is-structural.md)

**Reference**

- The guard layer in detail: [Policy gate](../../../reference/control-and-policy/policy-mcp.md)
- The thick-state substrate: [Memory substrates](../../../reference/pipelines-and-io/memory-substrates.md)
