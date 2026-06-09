---
topic: explorations
title: Memory systems and benchmarks — the evidence behind durable state
status: stub
created: 2026-06-09
parent: Design notes
grand_parent: Explanation
nav_order: 15
nav_exclude: true
---

# Memory systems and benchmarks — the evidence behind durable state

> **STUB — research not yet done.** This document is a placeholder for the background
> research that several accepted ADRs already cite as load-bearing but which has no
> working write-up in the repo. The numbers below are quoted *as they currently appear
> in ADRs* and are **unverified against their sources**. Do not treat any figure here
> as confirmed until this stub is filled in with checked citations.
>
> **How to fill this in:** run the [`deep-research`](../..) harness over each cited
> claim, fetch the primary source, verify the figure (or correct it), and replace each
> "⚠️ unverified" marker with a citation. Folds in what would otherwise be a separate
> `persistent-state-evidence.md` — it is the same literature.

## Why this is needed

[docs/explanation/](../explanation) and the ADRs argue that **durable,
persistent state is the load-bearing mechanism** for long-horizon agent research —
the thesis behind the three-layer architecture and the seven memory substrates. That
argument rests on external empirical results that are currently only *asserted*, with
no in-repo document tracing each figure to its source. If any number is misremembered,
the ADRs that lean on it weaken.

## Claims to verify (quoted from ADRs; ⚠️ unverified)

| Claim (as cited) | Cited in | Source | Status |
|---|---|---|---|
| Removing the durable-artifact layer costs **6.41 pts on PaperBench** and **31.82 pts on MLE-Bench Lite** | [ADR-01](../adr/01-three-layer-architecture.md) | Chen et al. 2026 | ⚠️ unverified |
| Agents reading prior agent-generated reports gain **~11% on MATH-500** | [ADR-01](../adr/01-three-layer-architecture.md) | AgentRxiv (Schmidgall & Moor 2025) | ⚠️ unverified |
| "No existing tool persists cross-run knowledge in finite context" — one of five structural problems | [ADR-01](../adr/01-three-layer-architecture.md) | PARNESS (Wang & Luan 2026) | ⚠️ unverified |
| **FAMA** metric penalizes reuse of obsolete/invalidated memory; "revise, don't accumulate" | [ADR-10](../adr/10-claim-supersession.md) | Memora; ClawArena | ⚠️ unverified |
| LLM memory judgments are unreliable (memory-benchmark evidence) | [ADR-10](../adr/10-claim-supersession.md) | Memora, MemoryAgentBench | ⚠️ unverified |
| Persistent knowledge accumulation is the **primary barrier to L5 autonomy** | [ADR-21](../adr/21-l3-autonomy-ceiling.md) | Chen 2026 (~95-paper survey) | ⚠️ unverified |

## Structure to fill in

1. **The durable-state thesis** — what each of Chen 2026 / AgentRxiv / PARNESS
   measured, and how three different starting points converge on "state in files beats
   state in chat." Verify the ablation deltas.
2. **The memory-failure literature** — FAMA, MemoryAgentBench, ClawArena: what failure
   mode each isolates, and why it justifies human-set claim supersession ([ADR-10](../adr/10-claim-supersession.md))
   over agent-judged memory.
3. **The substrate mapping** — how the verified findings map onto Memoria's seven
   substrates (see [Memory substrates — seven scoped stores, not one](memory-substrates.md)).

## Related

- [ADR-01](../adr/01-three-layer-architecture.md), [ADR-10](../adr/10-claim-supersession.md), [ADR-21](../adr/21-l3-autonomy-ceiling.md), [ADR-23](../adr/23-six-memory-substrates.md)
- [Memory substrates — seven scoped stores, not one](memory-substrates.md) — the as-built substrate set this evidence underpins
- [AI-research systems survey — the evidence behind the provenance table](ai-research-systems-survey.md) — the sibling survey stub (overlapping sources)
- Explanation: [`why-three-layers.md`](../explanation/rationale/why-three-layers.md), [`architecture/memory-model.md`](../explanation/architecture/memory-model.md)
- Reference: [`docs/reference/bibliography.md`](../reference/bibliography.md)
