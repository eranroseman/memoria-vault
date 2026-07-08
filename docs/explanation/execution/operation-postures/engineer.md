---
title: The Engineer
parent: Operation postures
grand_parent: Execution
nav_order: 5
---

# The Engineer

The Engineer is not an installed profile or direct code runner. It is the
handoff posture for external coding work: Memoria can prepare and record a
handoff, but the external coding agent does the coding
([standalone engine with operations as product code, no agent tools](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)).

## What it does

- Scaffolds a code handoff when the PI chooses to use an external coding agent.
- Records provenance and the commit/revert checkpoint.
- Keeps Memoria's workspace writes inside the CLI/engine and trusted-writer
  boundary.

## Boundary

- The Engineer posture does **not** grant Memoria terminal, file, or code
  execution authority ([standalone engine with operations as product code, no agent tools](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)).
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

- Where the handoff lives: [The vault](../../architecture/vault.md)
- How far each posture may delegate: [Operation postures](README.md#delegation-posture)
- Why the posture boundaries are strict: [Why operation postures](../../rationale/boundaries/why-operation-postures.md)
- The autonomy boundary it tests: [Why Memoria doesn't pursue full autonomy](../../rationale/boundaries/why-not-autonomous.md)
