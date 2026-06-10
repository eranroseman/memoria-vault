---
title: Design rationale
parent: Explanation
nav_order: 10
has_children: true
permalink: /explanation/rationale/
---

# Design rationale

The `why-*` pages: the durable conceptual arguments behind Memoria's core design choices. Each answers "why is it shaped this way?" and is written to be read and re-read. These carry no date and no status — they are the canonical reasoning, maintained over time.

> **`why-*` explanations vs. ADRs.** A `why-*` page holds the _argument_; an [ADR](../../adr) holds the _dated decision_. When both cover the same ground, the explanation carries the reasoning and the ADR carries the record — each links to the other rather than restating it. Change the reasoning → update the `why-*` page; reverse the decision → supersede the ADR.

## The arguments

| Page                                                              | The question it answers                                                                                             |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| [Why the architecture is layered](why-three-layers.md)                  | Why board, workers, and vault are kept separate — the thin-control-thick-state principle and what breaks without it |
| [Why specialist profiles](why-specialist-profiles.md)             | Why seven narrow specialists instead of one generalist, and why there is no Orchestrator                            |
| [Why the review gate is structural](why-human-gate.md)            | Why the human approval gate is enforced by architecture, not advised by convention                                  |
| [Why Memoria doesn't pursue full autonomy](why-not-autonomous.md) | The autonomy ceiling — why synthesis stays human-owned                                                              |
| [Why Hermes](why-hermes.md)                                       | Why the execution layer is the Hermes runtime, and where the programmatic surface fits                              |
| [Why deterministic methods](why-computational-methods.md)         | Why deterministic methods are preferred over LLM calls wherever correctness matters                                 |

## The evidence base

| Page                                                                   | What it provides                                                                                                                           |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| [Pattern provenance: borrow, adapt, ignore](why-pattern-provenance.md) | The borrow / adapt / reference / ignore judgment table against ~47 surveyed AI-research systems — the evidence the arguments above lean on |

---

## Related

- The structures these arguments shape: [Architecture](../architecture/README.md)
- The dated decisions they pair with: [ADRs](../../adr)
- The cross-cutting principles they share: [Design principles](../overview/design-principles.md)
