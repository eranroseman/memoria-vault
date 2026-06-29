---
title: The Engineer
parent: Profiles
grand_parent: Explanation
nav_order: 5
---

# The Engineer

The Engineer/code lane is deferred in alpha.11. Its planned posture is
**delegating**: Memoria prepares and records a handoff, but the external coding
agent does the coding ([ADR-07](../../adr/07-delegate-coding-to-external-agents.md)).

## What it does

- Scaffolds the `code` handoff when the deferred code lane is reintroduced.
- Records provenance and the commit/revert checkpoint.
- Routes all writes through the gated Obsidian MCP.

## Boundary

- The Engineer is **MCP-only**: no terminal, file access, or code execution ([ADR-46](../../adr/46-seven-layer-architecture.md)).
- The external coding agent is an opaque peer, not a subprocess Memoria drives.
- The autonomous code-experiment loop remains deferred.

---

## What the Engineer is not

**Not the agent that writes code.** The external agent does. The Engineer scaffolds, records, commits.

**Not orchestration infrastructure.** It does not spawn the external agent as a
subprocess, parse its output, or drive it through an API. Coordination is
through documented handoff artifacts, not an agent-control plane.

**Not a documenter of research.** A `code` handoff records what was built and why. Writing *about* the methodology or results is the Writer's domain.

---

## Related

- Where the handoff lives: [The vault](../architecture/vault.md)
- How far each agent may delegate: [Profiles](README.md#delegation-posture)
- Why the profile boundaries are strict: [Why specialist profiles, not a generalist agent](../../design/why-specialist-profiles.md)
- The autonomy boundary it tests: [Why Memoria doesn't pursue full autonomy](../../design/why-not-autonomous.md)
