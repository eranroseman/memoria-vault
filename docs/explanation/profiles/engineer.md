---
title: The Engineer
parent: Profiles
nav_order: 5
---

# The Engineer

The Engineer runs the **code** lane as a documentary front for an external coding agent. Its posture is **delegating** — the defining trait is the **two-agent boundary**: Memoria treats the external coding agent as an opaque peer it hands off to, never executes itself. Like every Memoria agent, the Engineer is **MCP-only** — no terminal, no file access, no code execution ([ADR-46](../../adr/46-seven-layer-architecture.md)); it scaffolds the `code` handoff into `projects/<project>/code/` through the gated obsidian MCP, records provenance, and owns the commit/revert gate. The substantive coding — generating, debugging, restructuring — happens in the external agent, which executes nothing inside Memoria's runtime ([ADR-07](../../adr/07-delegate-coding-to-external-agents.md)). Project folders now exist through the Project gate; the autonomous code-experiment loop remains deferred.

---

## Why it's designed this way

**Memoria doesn't compete with coding agents — it connects to them.** Capable coding agents already exist; reimplementing them inside Memoria would produce a worse copy. The Engineer owns the connective tissue between Memoria's audit and review discipline and the external agent's capability: the handoff package (goal, specs, constraints, acceptance checks) is the contract, and what comes back re-enters through the gated `code/` zone.

**Execution stays outside Memoria.** [ADR-21](../../adr/21-l3-autonomy-ceiling.md) retired the old Coder-lane execution exception: no Memoria agent — the Engineer included — gets terminal, file, or code-execution capability. The external coding agent is third-party code that runs in its own runtime, never inside Memoria's; its work re-enters only as artifacts under `projects/<project>/code/`, through the Engineer's per-task commits and the PI's review.

**Per-task commits, not mega-commits.** One logical change per call keeps the audit trail granular — one card, one commit, one diff to review — and keeps revert scope small.

## What the Engineer is not

**Not the agent that writes code.** The external agent does. The Engineer scaffolds, records, commits.

**Not orchestration infrastructure.** It does not spawn the external agent as a subprocess, parse its output, or drive it through an API. The two agents coordinate through a markdown handoff and the artifacts that land in `projects/<project>/code/` — an explicit design choice, not a limitation.

**Not a documenter of research.** A `code` handoff records what was built and why. Writing *about* the methodology or results is the Writer's domain.

---

## Related

- Where the handoff lives: [The vault](../architecture/vault.md)
- How far each agent may delegate: [Delegation posture](delegation-posture.md)
- The autonomy boundary it tests: [Why Memoria doesn't pursue full autonomy](../rationale/why-not-autonomous.md)
