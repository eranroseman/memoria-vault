---
title: Why operation postures
parent: Boundaries
grand_parent: Design rationale
nav_order: 4
---

# Why operation postures

Memoria uses **one read-only conversational posture plus capability-backed
operation postures** instead of one generalist ([alpha.15 standalone engine checkpoint](https://github.com/eranroseman/memoria-vault/blob/main/design-history/15-alpha.15.md)).
The dividing line is **posture and write permission, not capability or tool**:
faithful vs. skeptical, read-only vs. checked-write vs. proposal-only.

---

## The problem with a generalist agent

A generalist agent that does everything — discovers sources, synthesizes claims, verifies citations, writes deliverables — has several structural problems:

**Unclear responsibility.** When quality fails, it's not possible to say "this was a discovery error" vs "this was a verification failure." The same agent made every decision in sequence.

**Ambiguous permissions.** The most permissive access required by any task becomes the baseline for all tasks. The policy gate can't distinguish "this agent is discovering" from "this agent is synthesizing."

**No separation of stances.** Discovery should be generous; verification should be skeptical. An agent that does both must switch stances internally, with no structural guarantee that it does.

---

## Why posture is the unit, not the role

A posture is a stance bound to a write permission, not a task list. Capability
manifests define what can run; posture defines how work may affect the
workspace. Grouping by posture keeps the set small because tasks with the same
stance collapse into one operation family.

- Intake and corpus mapping are one *faithful* research-librarian stance pointed
  in two directions, so they are a single **Librarian** operation posture, not
  several installed agents.
- Judgment-checking is a distinct *skeptical, independent* stance, so it is the
  **Peer-reviewer** posture.
- Conversational questioning is the read-only front stance: the **Co-PI** query
  and interview flow.
- Scaffolding a code handoff is a *delegating* stance: the **Engineer** handoff
  posture.
- Composing project prose from checked claims is a *generative, draft-scoped*
  stance, so it is the **Writer** posture — bounded to traceable files,
  verification, and refusal gates rather than open-ended authorship.
- Deterministic, zero-LLM work has no judgment posture at all. It is simply an
  **operation**: the Linter, sweeps, projections, and rebuilds.

One posture per operation family. Going finer adds routing, permission matrices,
and a fragmented learning loop.

Each posture carries different authority. The Co-PI is read-only. Operation
manifests and trusted-writer checks scope machine writes. The PI is the only
actor that disposes. That split keeps conversation from becoming writing,
production from grading itself, and deterministic operations from masquerading as
judgment.

## Why one Co-PI fronts everything

Splitting conversation across many agents creates a UX failure: *who do I talk
to?* Every profile would become a possible conversation, so no conversation
compounds. One read-only **Co-PI posture** fixes both halves:

- **The learning loop needs one home.** Durable learning belongs in checked
  workspace state; optional chat memory is useful only when it routes durable
  outcomes back into that state.
- **Delegation keeps the wall.** The Co-PI is read-only; every write leaves as a
  request under an operation manifest's ceiling. You get one conversational
  front and scoped executors - not a generalist with the union of everyone's
  permissions.

Machine execution stays out of conversation by design. An operation is
request-scoped, which keeps failures local and permissions legible.

## The independence argument

The **Peer-reviewer stays separate from the Librarian** even when they share
retrieval tooling. The posture that gathers and synthesizes must not also grade
the result. A checker that inherits the proposer's faithful stance can wave
through what the review gate exists to catch. The Librarian includes generously;
the Peer-reviewer doubts independently. The tension is the design.

## No Orchestrator, no Reviewer

Memoria omits two roles that comparable multi-agent systems include:

**No Orchestrator profile.** Routing lives in explicit CLI commands, request
rows, operation manifests, and scheduler/scan inputs - auditable mechanism, not
a reasoning agent whose routing mistakes are hard to trace. If the rules cannot
decide, attention waits for a human.

**No Reviewer profile.** An LLM reviewer that decides whether work is good enough converts a structural gate into a probabilistic one. The Peer-reviewer and the operations produce *recommendations* that inform the PI's judgment; the review gate itself is always human ([Why the review gate is structural](why-review-gate-is-structural.md)).

---

## The cost: capability duplication

Dividing by posture has a cost: the same technique can appear in several
operation families. Embedding similarity can drive mapping, duplicate
adjudication, and intake briefs. Memoria accepts that duplication because a
shared capability-agent would need the union of every caller's access,
dissolving the write boundaries the split exists to preserve.

Layering reconciles the duplication. Capability lives in **package-owned
operations**; optional adapters present or transport over the CLI/engine.
Postures remain write zone plus stance, not tool bundles.

---

## Related

- The operation postures described: [Operation postures](../../execution/operation-postures/README.md)
- The deterministic actors that are not agents: [Operations](../../execution/operations.md)
- Why the layers separate concerns: [Why the architecture is layered](why-layered-architecture.md)
- Why the review gate is human-owned: [Why the review gate is structural](why-review-gate-is-structural.md)
