---
topic: decisions
id: 57
title: Engines write, agents judge — no LLM agent as a mechanical writer
status: accepted
date_proposed: 2026-06-11
date_resolved: 2026-06-11
assumes: [30, 32, 46]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 57
---

# ADR-57: Engines write, agents judge — no LLM agent as a mechanical writer

## Context

Memoria's split between deterministic **engines** and judgment-bearing **agents**
(ADR-46, ADR-48; the [task classification](../explanation/rationale/why-computational-methods.md))
has always carried an implicit corollary: an LLM agent is **never used as the
mechanical writer** of an artifact whose content is derivable by rule — catalog
records, logs, file moves, schema-shaped transformations, exports. ADR-30 applies it
to ingest ("scriptable-before-LLM"), ADR-32 applies it to external access, and
ADRs 9/10 invoke it when rejecting LLM-judged dashboards and supersession — but the
general decision and its reasons were never recorded in one place. This ADR records it.

(*Naming note:* this is unrelated to the **Writer** agent, whose drafting is a
*generative* task — open-ended composition the PI reviews behind the gate. The rule
governs **mechanical** writes: outputs with a single right answer.)

## Decision

**Any write whose correct content is derivable by rule is performed by an engine
(deterministic code), never by an LLM agent following an instruction.** Agents
contribute only the judgment holes (a brief, a classification proposal, prose) and
every agent write is a gated proposal. If a task's output can be specified — same
input, same bytes — it is engine work by definition.

## Why

Two properties a knowledge substrate cannot do without, and an LLM-as-scribe provides
neither:

1. **Consistency.** The same action must yield the same result. LLM output varies
   run-to-run even at `temperature 0`: production inference is not batch-invariant —
   floating-point non-associativity under varying server batch sizes makes identical
   prompts diverge (an experiment sampling one prompt 1,000 times at temperature 0
   produced **80 distinct outputs**; bitwise-identical completions required replacing
   the inference kernels themselves). Empirically, multi-step tool-calling agents show
   the same pattern at the behavioral level: stable tool *choice*, varying *arguments* —
   exactly the part that becomes file content. A mechanical writer that paraphrases a
   field name, reorders keys, or "helpfully" reformats once per hundred runs corrupts a
   substrate that schemas, links, and diffs depend on.

2. **Traceability.** When an engine writes, the *why* of every byte is reconstructable:
   a code path, inputs, a log line, a diff, a test that pins the behavior. When an
   agent writes from an instruction, the derivation lives in opaque sampling — the same
   action can yield a different result **without leaving a trace that lets you find out
   what happened**. The audit chain records *that* a write occurred and its hashes, but
   only deterministic code lets you replay and explain it. Observability research on
   agents reaches the same conclusion from the other side: making agent behavior
   auditable requires pinning and logging every model/prompt/tool version precisely
   *because* the step itself is irreproducible — machinery Memoria does not need to
   build for writes an engine can simply perform.

The cost asymmetry seals it: an engine write is cheap, testable, and idempotent; an
LLM write costs tokens and latency and can fail in ways no test can enumerate.

## How the rule lands in v0.1.0-alpha.2

- The ingest engine assembles records, builds relationships, appends the intake
  anchor; the Librarian fills only the two judgment holes (ADR-30, ADR-56).
- `board_export`, `metrics_aggregate`, `golden`, the sweeps, and the Linter write
  their artifacts directly as trusted engine code — never via an agent.
- The reconcile sweep stamps chat exports mechanically; no agent rewrites files.
- Agent writes that remain are judgment products (briefs, proposals, drafts, cards)
  and go through the policy gate as proposals (ADR-03, ADR-28).

## Trade-offs

- Every new mechanical write needs engine code (and a test) instead of a sentence in
  a SKILL.md — slower to add, which is the point: the sentence version is the failure.
- Some tasks sit on the boundary (e.g. summarize-then-file); the
  [task classification](../explanation/rationale/why-computational-methods.md) default
  test applies — if a rule would produce the right answer most of the time, the write
  is engine work and the LLM contributes at most a bounded judgment hole.

## Alternatives weighed

- **Let agents perform mechanical writes under tight prompts.** Rejected: prompt
  discipline degrades (ADR-03's argument), and no prompt restores batch-invariance or
  a derivation trace.
- **Accept variance and lint it away afterwards.** Rejected: the Linter is a monitor
  and commit gate, not a substitute for writes being right; silent near-misses inside
  schema-valid values are exactly what detectors cannot see.
- **Pin providers/kernels for deterministic inference.** Rejected as the general
  answer: batch-invariant inference exists but trades throughput, binds Memoria to
  specific serving stacks, and still leaves the derivation opaque — determinism
  without explainability.

## Evidence

- Thinking Machines Lab, *Defeating Nondeterminism in LLM Inference* (2025) — batch
  non-invariance as the root cause; 1,000 temp-0 samples → 80 distinct outputs;
  bitwise reproducibility only via batch-invariant kernels.
  <https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/>
- LMSYS, *Towards Deterministic Inference in SGLang* (2025) — what it takes to make
  serving deterministic, and the cost. <https://www.lmsys.org/blog/2025-09-22-sglang-deterministic/>
- *How Consistent Are LLM Agents? Measuring Behavioral Reproducibility in Multi-Step
  Tool-Calling Pipelines* (2026) — "structural consistency, parametric variance"
  across 1,140 agent traces. <https://arxiv.org/abs/2605.28840>
- *AgentTrace: A Structured Logging Framework for Agent System Observability* (2026) —
  the logging burden required to make nondeterministic agent steps auditable.
  <https://arxiv.org/pdf/2602.10133>
- *Beyond Reproducibility: Token Probabilities Expose Large Language Model
  Nondeterminism* (2026). <https://arxiv.org/pdf/2601.06118>

## Related

- **Reinforces:** [ADR-30](30-deterministic-ingest-pipeline.md) (scriptable-before-LLM),
  [ADR-32](32-external-access-over-mcp.md), [ADR-46](46-seven-layer-architecture.md)
  (engines as an actor-kind), [ADR-03](03-structural-review-gate.md) (structure over
  prompt discipline).
- **Rationale page:** [Why Memoria uses deterministic methods alongside LLMs](../explanation/rationale/why-computational-methods.md).
