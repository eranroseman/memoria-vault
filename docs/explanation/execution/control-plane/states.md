---
title: Request states and the review gate
parent: Execution
grand_parent: Explanation
nav_order: 31
---

# Request states and the review gate

This page explains why the control-plane state machine is shaped the way it is:
why execution state stays separate from PI attention, and why rejected work
creates a new request instead of rewriting the old one. For the current command
lookup, see the
[Control plane reference](../../../reference/control-plane.md).

---

## What a request carries

A request is not just a task title. It carries execution state, input refs,
output intents, precondition hashes, optional machine recommendations, journal
events, and retry/blocking history. Those fields make work persistent,
queryable, recoverable, and safe to resume without sharing profile memory.

The key invariant: **request execution and PI attention are separate states**.
The worker can finish a request as `done`; the human still decides whether any
attention item raised by that work has been handled.

## The execution chain is the hidden mechanic

The runtime moves each request through machine-facing states owned by the control
plane reference and worker code. Recovery marks interrupted running work as
failed so it can be retried explicitly, and pending materialization payloads
replay through `workspace recover`. This chain is load-bearing for the worker and
recovery code, but the **PI does not treat it as approval**. It is plumbing, and
its design serves execution:

**Pending work exists so dispatch never starts before scope is explicit.** A
request carries input refs, output intents, and checks before execution. A file
change observed by `workspace scan` is first recorded and checked; it is not
machine-consumable merely because it appeared on disk.

**Retries are explicit request operations.** A recoverable run failure can be
retried against the same durable request payload. Failures that need human
judgment become attention, with a reason, for the PI to clear or amend.

## The PI sees only action state

The human-facing state is an attention projection over request/journal state,
not a durable Concept lifecycle. Concept read state is the DB/read API
`check_status` verdict; Concept frontmatter stays meaning-only. For an action
prompt the PI records an explicit outcome: apply, reject, or defer.

An action prompt awaiting you appears in the Inbox projection. You act on it, then it
leaves the active queue when no action remains. There is no separate `review-request`
card type and no second durable Concept family to learn: "what needs me?" is an
attention query, not a checked-knowledge query.

---

## Three orthogonal dimensions

A request or attention prompt carries three independent signals, and keeping
them separate is what prevents a machine verdict from rubber-stamping a human
decision:

- **execution status** — did the worker run, finish, or get stuck? Exact values
  belong to the reference and request table.
- **attention state** — the PI's decision: has the human acted on this?
- **machine recommendation** — a soft verdict such as inconclusive, issues-found,
  or clean; never a gate.

A worker finishing implies nothing about acceptance; a clean recommendation
never substitutes for the PI acting. The read barrier is enforced, not advisory:
checked materialization means checks passed and warrants resolve, while PI action
is recorded separately.

**Rejection creates a new request, not a revision of the old one.** A rejected
attempt is closed; rework begins on a fresh request or amended request that
records what it supersedes. Each attempt has one stated outcome, so the history
of attempts stays traceable. A system where rejected work is silently reopened is
a system where the audit trail lies.

## Requests and notes are different things

A request is **work**: transient, pending in the engine, and closed when the
attempt is over. A note is **knowledge**: durable, linkable, and preserved in the
workspace. A request can reference or produce a note, but it never *is* a note.
Mixing request fields (`status`, `request_id`, output intents) with note fields
(`type`, `links`, `tags`) confuses what has been done with what has been
established.

That split is why the engine can retry and block work without polluting the
knowledge graph, and why the workspace can preserve provenance without becoming
a task tracker.

## Related

**Explanation**

- Conceptual overview: [Request control plane](README.md)
- The prompt the PI reads: [The honesty prompt](honesty-card.md)
- Why WIP limits exist: [WIP limits and back-pressure](wip-limits.md)
- Why the Co-PI is not a lane: [Operation postures](../operation-postures/README.md)
- Why operations are not lanes: [Operations](../operations.md)
- Why review is human-only: [Why the review gate is structural](../../../design/boundaries/why-review-gate-is-structural.md)
- The decision-kind model the gate implements: [Decision points](decision-points.md)

**How-to**

- Troubleshooting for stuck work: [Fix a stuck card](../../../how-to-guides/troubleshooting/fix-stuck-card.md)

**Reference**

- Board-states lookup table: [Control plane reference](../../../reference/control-plane.md)
