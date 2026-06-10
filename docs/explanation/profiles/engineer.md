---
title: The Engineer
parent: Profiles
nav_order: 5
---

# The Engineer

The Engineer runs the **code** lane as a documentary front for an external coding agent. Its posture is **delegating** — the defining trait is the **two-agent boundary**: Memoria treats the external coding agent as an opaque peer with shared filesystem access. The Engineer scaffolds the `code` handoff in `projects/<project>/code/`, records provenance, runs per-task git commits, and owns the commit/revert gate. The substantive coding — generating, debugging, restructuring — happens in the external agent ([ADR-07](../../adr/07-delegate-coding-to-external-agents.md)). It ships with the Project workspace (v0.1.2).

---

## Why it's designed this way

**Memoria doesn't compete with coding agents — it connects to them.** Capable coding agents already exist; reimplementing them inside Memoria would produce a worse copy. The Engineer owns the connective tissue between Memoria's audit and review discipline and the external agent's capability: the vault is the external agent's read-only context, the project's `code/` folder is its write zone, the handoff note is the contract.

**The sanctioned autonomy exception.** The external coding loop is the one place Memoria's autonomy ceiling is deliberately exceeded — and it is contained by construction ([ADR-21](../../adr/21-l3-autonomy-ceiling.md)): the loop runs outside Memoria's runtime, writes only the code zone, and re-enters through the Engineer's per-task commits and the PI's review.

**Per-task commits, not mega-commits.** One logical change per call keeps the audit trail granular — one card, one commit, one diff to review — and keeps revert scope small.

## What the Engineer is not

**Not the agent that writes code.** The external agent does. The Engineer scaffolds, records, commits.

**Not orchestration infrastructure.** It does not spawn the external agent as a subprocess, parse its output, or drive it through an API. The two agents coordinate through a markdown handoff and a shared filesystem — an explicit design choice, not a limitation.

**Not a documenter of research.** A `code` handoff records what was built and why. Writing *about* the methodology or results is the Writer's domain.

---

## Related

- Where the handoff lives: [The vault](../architecture/vault.md)
- How far each agent may delegate: [Delegation posture](delegation-posture.md)
- The autonomy boundary it tests: [Why Memoria doesn't pursue full autonomy](../rationale/why-not-autonomous.md)
