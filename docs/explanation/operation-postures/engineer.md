---
title: The Engineer
parent: Operation postures
grand_parent: Explanation
nav_order: 5
---

# The Engineer

The Engineer is not an installed alpha.15 profile or code runner. It is the
handoff posture for external coding work: Memoria can prepare and record a
handoff, but the external coding agent does the coding
([ADR-125](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)).

## What it does

- Scaffolds a code handoff when the PI chooses to use an external coding agent.
- Records provenance and the commit/revert checkpoint.
- Keeps Memoria's workspace writes inside the CLI/engine and trusted-writer
  boundary.

## Boundary

- The Engineer posture does **not** grant Memoria terminal, file, or code
  execution authority ([ADR-125](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)).
- The external coding agent is an opaque peer, not a subprocess Memoria drives.
- The autonomous code-experiment loop remains deferred.

---

## What the Engineer is not

**Not the agent that writes code.** The external agent does. The Engineer
posture scaffolds and records the handoff.

**Not orchestration infrastructure.** It does not spawn the external agent as a
subprocess, parse its output, or drive it through an API. Coordination is
through documented handoff artifacts, not an agent-control plane.

**Not a documenter of research.** A `code` handoff records what was built and why. Writing *about* the methodology or results is the Writer's domain.

---

## Related

- Where the handoff lives: [The vault](../architecture/vault.md)
- How far each posture may delegate: [Operation postures](README.md#delegation-posture)
- Why the posture boundaries are strict: [Why operation postures, not a generalist agent](../../design/why-specialist-postures.md)
- The autonomy boundary it tests: [Why Memoria doesn't pursue full autonomy](../../design/why-not-autonomous.md)
