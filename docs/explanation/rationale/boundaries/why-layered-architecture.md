---
title: Why the architecture is layered
parent: Boundaries
grand_parent: Design rationale
nav_order: 2
---

# Why the architecture is layered

Memoria separates orchestration, execution, and settled knowledge because those
states fail differently. The separation makes retries safe, handoffs lossless,
and review enforceable. The standalone runtime implements those boundaries
through the CLI, SQLite request table, worker operations, runtime policy, and
checked workspace.

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

## Current boundaries

The standalone runtime has five components with distinct jobs:

- The **CLI** accepts PI commands and creates explicit requests.
- **SQLite state** records requests, catalog rows, journals, and read verdicts.
- The **worker** executes requests and records their outcomes.
- **Operation manifests and runtime policy** constrain allowed execution and
  machine writes.
- The **workspace** holds checked Concepts and generated projections.

Optional adapters use the same request and read surfaces. They do not own
runtime state. PI edits and operator-managed scheduled jobs enter through
explicit requests or are observed by the integrity path.

The system keeps control thin and durable knowledge thick: requests and journal
state coordinate work, while checked workspace files carry settled knowledge.

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

- The current standalone structure: [Architecture](../../architecture/README.md)
- How the agent layer is structured: [Why operation postures](why-operation-postures.md)
- Why the vault's review gate is structural: [Why the review gate is structural](why-review-gate-is-structural.md)

**Reference**

- The guard layer in detail: [Policy gate](../../../reference/control-and-policy/policy-mcp.md)
- The thick-state substrate: [Memory substrates](../../../reference/pipelines-and-io/memory-substrates.md)
