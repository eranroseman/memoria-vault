---
title: The Engineer
parent: Profiles
grand_parent: Explanation
nav_order: 5
---

# The Engineer

The Engineer runs the **code** lane as a documentary front for an external coding agent. Its posture is **delegating** — the defining trait is the **two-agent boundary**: Memoria treats the external coding agent as an opaque peer it hands off to, never executes itself. Like every Memoria agent, the Engineer is **MCP-only** — no terminal, no file access, no code execution ([ADR-46](../../adr/46-seven-layer-architecture.md)); it scaffolds the `code` handoff into `projects/<project>/code/` through the gated obsidian MCP, records provenance, and owns the commit/revert checkpoint. The substantive coding — generating, debugging, restructuring — happens in the external agent, which executes nothing inside Memoria's runtime ([ADR-07](../../adr/07-delegate-coding-to-external-agents.md)). Project folders now exist through the Project gate; the autonomous code-experiment loop remains deferred.

---

## What the Engineer is not

**Not the agent that writes code.** The external agent does. The Engineer scaffolds, records, commits.

**Not orchestration infrastructure.** It does not spawn the external agent as a subprocess, parse its output, or drive it through an API. The two agents coordinate through a markdown handoff and the artifacts that land in `projects/<project>/code/` — an explicit design choice, not a limitation.

**Not a documenter of research.** A `code` handoff records what was built and why. Writing *about* the methodology or results is the Writer's domain.

---

## Related

- Where the handoff lives: [The vault](../architecture/vault.md)
- How far each agent may delegate: [Delegation posture](delegation-posture.md)
- Why the profile boundaries are strict: [Why profile boundaries exist](../../design/why-profile-boundaries.md)
- The autonomy boundary it tests: [Why Memoria doesn't pursue full autonomy](../../design/why-not-autonomous.md)
