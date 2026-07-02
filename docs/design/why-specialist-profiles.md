---
title: Why operation postures, not a generalist agent
parent: Design Book
grand_parent: Developers
nav_order: 11
---

# Why operation postures, not a generalist agent

Memoria uses **one read-only conversational posture plus capability-backed
operation postures** instead of one generalist ([ADR-48](../adr/48-copi-and-agent-consolidation.md)).
The dividing line is **posture and write-permission, not capability or tool**:
faithful vs skeptical, read-only vs checked-write vs proposal-only. This page
makes the argument - why specialists at all, and why posture is the axis that
divides them.

---

## The problem with a generalist agent

A generalist agent that does everything — discovers sources, synthesizes claims, verifies citations, writes deliverables — has several structural problems:

**Unclear responsibility.** When quality fails, it's not possible to say "this was a discovery error" vs "this was a verification failure." The same agent made every decision in sequence.

**Ambiguous permissions.** The most permissive access required by any task becomes the baseline for all tasks. The policy gate can't distinguish "this agent is discovering" from "this agent is synthesizing."

**No separation of stances.** Discovery should be generous; verification should be skeptical. An agent that does both must switch stances internally, with no structural guarantee that it does.

---

## Why posture is the unit, not the role

A posture is a stance bound to a write-permission, not a task list. Capability
manifests and operations define what can run; posture defines *how work acts on
the workspace*. Organizing by posture rather than by role keeps the set small:
tasks that share a stance collapse into one operation family.

- Intake and corpus mapping are one *faithful* research-librarian stance pointed
  in two directions, so they are a single **Librarian** operation posture, not
  several installed agents.
- Judgment-checking is a distinct *skeptical, independent* stance, so it is the
  **Peer-reviewer** posture.
- Conversational questioning is the read-only front stance: the **Co-PI** query
  and interview flow.
- Scaffolding a code handoff is a *delegating* stance: the **Engineer** handoff
  posture.
- Deterministic, zero-LLM work has no judgment posture at all. It is simply an
  **operation**: the Linter, sweeps, projections, and rebuilds.

One posture per operation family. The fragmentation cost of going finer is real:
more routing, more permission matrices, and - decisively - a fragmented learning
loop.

The boundary matters because each posture carries different authority. The Co-PI
is read-only; operation manifests and trusted-writer checks scope machine
writes; the PI is the only actor that disposes. That split prevents conversation
from becoming writing, production from grading itself, and deterministic
operations from masquerading as judgment-bearing synthesis.

## Why one Co-PI fronts everything

Splitting conversation across many agents creates a real UX failure: *who do I
talk to?* Every profile would become a possible conversation, so no conversation
compounds. Concentrating read-only dialogue in **one Co-PI posture** fixes both
halves:

- **The learning loop needs one home.** Durable learning belongs in checked
  workspace state; optional chat memory is useful only when it routes durable
  outcomes back into that state.
- **Delegation keeps the wall.** The Co-PI is read-only; every write leaves as a
  request under an operation manifest's ceiling. You get one conversational
  front and scoped executors - not a generalist with the union of everyone's
  permissions.

Machine execution stays out of conversation by design: an operation is a
propose-then-dispose executor, and keeping it request-scoped is what keeps its
failures scoped and its permissions legible.

## The independence argument

The **Peer-reviewer is kept separate from the Librarian** on principle, however
much retrieval tooling they share. The posture that gathers and synthesizes must
not also grade the result - separation of duties is the anti-rubber-stamp
principle. A checker that inherits the proposer's faithful stance waves through
exactly what the review gate exists to catch. The two postures are in deliberate
tension: the Librarian includes generously; the Peer-reviewer doubts
independently. The asymmetry is the design - you need both, and they must be
separate to work.

## No Orchestrator, no Reviewer

Memoria omits two roles that comparable multi-agent systems include:

**No Orchestrator profile.** Routing lives in explicit CLI commands, request
rows, operation manifests, and scheduler/scan inputs - auditable mechanism, not
a reasoning agent whose routing mistakes are hard to trace. If the rules cannot
decide, attention waits for a human.

**No Reviewer profile.** An LLM reviewer that decides whether work is good enough converts a structural gate into a probabilistic one. The Peer-reviewer and the operations produce *recommendations* that inform the PI's judgment; the review gate itself is always human ([Why the review gate is structural](why-review-gate-is-structural.md)).

---

## The cost: capability duplication

Dividing by posture still has its price: the same *technique* can live in several
operation families. Embedding similarity drives mapping, duplicate adjudication,
and intake briefs. Memoria takes the duplication on purpose - a shared
capability-agent would need the union of every caller's access, dissolving the
write boundaries the split exists to make legible. The reconciliation is
layering: capability lives in **operations and shared optional adapters**; the
postures stay pure - write zone and stance, not tools.

---

## Related

- The operation postures described: [Operation postures](../explanation/profiles/README.md)
- The deterministic actors that are not agents: [Operations](../explanation/operations.md)
- Why the layers separate concerns: [Why the architecture is layered](why-layered-architecture.md)
- Why the review gate is human-owned: [Why the review gate is structural](why-review-gate-is-structural.md)
