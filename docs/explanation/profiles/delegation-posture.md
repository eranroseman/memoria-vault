---
title: Delegation posture
parent: Profiles
nav_order: 8
---

# Delegation posture

Profiles differ in how much they may hand a narrow, temporary subtask to a child or external agent — never the role's *defining* judgment, only support work around it. Strongest delegators at the top:

```text
  more ┌─────────────────────────────────────────────────────────────────┐
   ▲   │ Coder      Moderate    helper/lookup + substantive coding to the  │
   │   │                        external agent; commits stay per-task      │
   │   │ Writer     Supportive  facts / cleanup; synthesis stays local     │
   │   │ Librarian  Targeted    narrow enrichment / source lookups;        │
   │   │                        keeps discovery ownership                   │
   │   │ Mapper     Low         mechanical retrieval (qmd); keeps the map   │
   │   │ Verifier   Very low    delegation weakens independence; traces     │
   │   │ Linter     Lowest      does not spawn work; may request context   │
   ▼   │ Socratic   None        can't write; questions are the whole product│
  less └─────────────────────────────────────────────────────────────────┘
```

**Rule:** delegate narrow, temporary, low-risk subtasks; never the defining judgment. The Coder's delegation is widest because the substantive coding *is* an external-agent handoff by design ([ADR-07](../../adr/07-delegate-coding-to-external-agents.md)); the Socratic profile delegates nothing because it cannot write and its questions are the entire deliverable.

---

## Related

- The profiles ranked above: [Profiles](README.md)
- Why tasks go to specialists at all: [Why specialist profiles, not a generalist agent](../rationale/why-specialist-profiles.md)
- The widest delegator and its external-agent handoff: [Coder](coder.md)
