---
title: Why specialist profiles, not a generalist agent
parent: Design rationale
nav_order: 2
---

# Why specialist profiles, not a generalist agent

Memoria uses **one conversational Co-PI and four posture-defined background agents** instead of one generalist — and instead of the seven specialists it used to run ([ADR-48](../../adr/48-copi-and-agent-consolidation.md), superseding ADR-02). The dividing line is **posture and write-permission, not capability or tool**: faithful vs skeptical, read-only vs scratch-write vs review-gated. This page makes both arguments — why specialists at all, and why five postures beat seven roles.

---

## The problem with a generalist agent

A generalist agent that does everything — discovers sources, synthesizes claims, verifies citations, writes deliverables — has several structural problems:

**Unclear responsibility.** When quality fails, it's not possible to say "this was a discovery error" vs "this was a verification failure." The same agent made every decision in sequence.

**Ambiguous permissions.** The most permissive access required by any task becomes the baseline for all tasks. The policy MCP can't distinguish "this agent is discovering" from "this agent is synthesizing."

**No separation of stances.** Discovery should be generous; verification should be skeptical. An agent that does both must switch stances internally, with no structural guarantee that it does.

---

## Why posture is the unit, not the role

The original cut produced seven role-named profiles (Librarian, Mapper, Socratic, Writer, Verifier, Coder, Linter). Under the rule **a profile is a posture; skills attach per lane**, that set turned out to be over-divided — several profiles shared one stance:

- The old Librarian and Mapper were both *faithful* — intake and corpus mapping are one research-librarian stance pointed in two directions. They merged into the **Librarian** (catalog · extract · link · map).
- The old Socratic was the conversational stance with the write-wall — exactly the **Co-PI**, so it folded in.
- The old Verifier mixed two method classes: its *judgment* checks became the **Peer-reviewer**; its deterministic sweeps became **engines**.
- The old Linter was never an agent at all — zero-LLM, reproducible, cron-run: an **engine** by definition.
- The old Coder kept its boundary and became the **Engineer**.

One posture per agent, one agent per posture. The fragmentation cost of going finer is real: more lanes to route between, more permission matrices, and — decisively — a fragmented learning loop.

## Why one Co-PI fronts everything

Seven specialists created a real UX failure: *who do I talk to?* Every profile was a possible conversation, so no conversation compounded. Concentrating all dialogue in **one Co-PI** fixes both halves:

- **The learning loop needs one home.** Hermes' self-improving loop — memory · /goals · skills — only compounds in an agent that has every conversation. Split across seven, each got a sliver of context and none grew.
- **Delegation keeps the wall.** The Co-PI is read-only; every write leaves as a routed card under a background lane's ceiling. You get one warm, remembering front *and* stateless, scoped executors — not a generalist with the union of everyone's permissions.

The background lanes stay out of conversation by design: a lane is a propose-then-dispose executor, and keeping it stateless is what keeps its failures scoped and its permissions legible.

## The independence argument

One consolidation was refused on principle: the **Peer-reviewer was never merged into the Librarian**, however much retrieval tooling they share. The agent that gathers and synthesizes must not also grade the result — separation of duties is the anti-rubber-stamp principle. A checker that inherits the proposer's faithful stance waves through exactly what the gate exists to catch. The two postures are in deliberate tension: the Librarian includes generously; the Peer-reviewer doubts independently. The asymmetry is the design — you need both, and they must be separate to work.

## No Orchestrator, no Reviewer

Memoria still deliberately omits two roles that comparable multi-agent systems include:

**No Orchestrator profile.** Routing lives in the Co-PI's `delegate:route-task` and the board's dispatch rules — auditable mechanism, not a reasoning agent whose routing mistakes are hard to trace. If the rules can't decide, the card waits for a human.

**No Reviewer profile.** An LLM reviewer that decides whether work is good enough converts a structural gate into a probabilistic one. The Peer-reviewer and the engines produce *recommendations* that inform the PI's judgment; the gate itself is always human ([Why the review gate is structural](why-human-gate.md)).

---

## The cost: capability duplication

Dividing by posture still has its price: the same *technique* can live in several agents. Embedding similarity drives the Librarian's mapping, the Peer-reviewer's duplicate adjudication, and the intake brief. Memoria takes the duplication on purpose — a shared capability-agent would need the union of every caller's access, dissolving the per-lane write boundaries the split exists to make legible. The reconciliation is layering: capability lives in **engines and shared MCP servers** every lane reaches through the policy gate; the **agents stay posture-pure** — identity, write zone, and stance, not tools.

---

## Related

- The five agents described: [Profiles](../profiles/README.md)
- The deterministic actors that left the set: [Engines](../engines/README.md)
- Why the layers separate concerns: [Why the architecture is layered](why-three-layers.md)
- Why the review gate is human-owned: [Why the review gate is structural](why-human-gate.md)
