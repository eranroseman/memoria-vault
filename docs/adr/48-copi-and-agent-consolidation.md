---
topic: decisions
id: 48
title: One Co-PI fronts everything; specialists consolidate to posture-defined agents
status: accepted
date_proposed: 2026-06-10
date_resolved: 2026-06-10
assumes: [22, 46]
supersedes: [2, 37, 42]
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 48
---

# ADR-48: One Co-PI fronts everything; specialists consolidate to posture-defined agents

## Context

ADR-02's seven specialist profiles created a real UX failure — "who do I talk to?" —
and fragmented the learning loop across agents that never conversed. Under
"profile = posture, skills attach per lane" several profiles shared one stance. The
design update (D26/D27/D34/D38/D46) consolidated by posture and concentrated
conversation in a single front.

## Decision

The PI converses with **one agent — the Co-PI** — and **delegates** everything else.
The Co-PI is the permanent agent in the ACP pane: reflective thinking-partner posture
(it subsumes the old Socratic role), **read-only** (it runs read-only skills directly;
every write goes out as a delegated task card), and the sole carrier of Hermes'
self-improving loop (**memory · /goals · skills**); **`/personality` is a Co-PI-only
affordance** — specialist postures are fixed by design.

The background agents are role-named, posture-defined lanes: **Librarian** (*faithful*;
the four processing lanes catalog · extract · link · map — the old Librarian + Analyst),
**Writer** (*generative, draft-only*), **Peer-reviewer** (*skeptical, deliberately
independent* — never merged with the Librarian; separation of duties), **Engineer**
(*delegating*). Deterministic work is **engines, not agents**
([ADR-46](46-seven-layer-architecture.md)): the Linter and the verification sweeps left
the profile set. Each agent = a shared layer (the vault `AGENTS.md`) + a unique layer
(`SOUL.md`, `skills/`, `config.yaml`, MCP wiring).

**v0.1.0-alpha.2 ships all five profiles** (the original plan shipped only Co-PI + Librarian,
with the rest deferred to v0.1.0-alpha.3; the PI expanded the scope mid-build — 2026-06-09 — so
Writer, Peer-reviewer, and Engineer landed in v0.1.0-alpha.2 as well; their *Project-workspace
workflows* still arrive with v0.1.0-alpha.3).

## Consequences

- One conversational context compounds (memory/goals/skills) instead of seven that
  reset; background lanes stay stateless propose-then-dispose executors.
- The board's lanes shrink to the background agents; there is no Co-PI lane and no
  engine lane.
- Drafting and verification interrogation are conversational but currently routed
  through one-shot cards — the open "conversational specialist work" question
  (red-team theme C) is deliberately unresolved; a routing agent is rejected.
- The old profile names (Mapper, Socratic, Verifier, Coder) disappear from the
  installed set; their useful skills migrate into the consolidated lanes.

## Alternatives considered

**Keep seven specialists.** Artificial handoffs between profiles sharing one posture,
and the "who do I talk to?" confusion. **Co-PI plus directly-conversable specialists.**
Reintroduces the confusion and splits the learning loop; revisit only if a specialist
conversation proves necessary. **Merging verification into the Librarian.** Breaks
separation of duties — the agent that synthesizes must not grade its own work.

## Related

- **Resolves / supersedes:** [ADR-02](02-seven-specialist-profiles.md)
- **Related decisions / Depends on:** [ADR-46](46-seven-layer-architecture.md),
  [ADR-21](21-l3-autonomy-ceiling.md), [ADR-23](23-scoped-memory-substrates.md)
