---
title: Delegation posture
parent: Profiles
nav_order: 8
---

# Delegation posture

Agents differ in how much they may hand a narrow, temporary subtask to a child or external agent — never the role's *defining* judgment, only support work around it. Strongest delegators at the top:

```text
  more ┌────────────────────────────────────────────────────────────────────┐
   ▲   │ Engineer       Widest      substantive coding goes to the external  │
   │   │                            agent by design; commits stay per-task   │
   │   │ Writer         Supportive  facts / cleanup; synthesis stays local   │
   │   │ Librarian      Targeted    narrow enrichment / source lookups;      │
   │   │                            keeps discovery ownership                │
   │   │ Peer-reviewer  Very low    delegation weakens independence; runs    │
   │   │                            its own traces                           │
   ▼   │ Co-PI          None        read-only; every write leaves as a       │
  less │                            routed card, not a spawned helper        │
       └────────────────────────────────────────────────────────────────────┘
```

**Rule:** delegate narrow, temporary, low-risk subtasks; never the defining judgment. The Engineer's delegation is widest because the substantive coding *is* an external-agent handoff by design ([ADR-07](../../adr/07-delegate-coding-to-external-agents.md)). The Co-PI sits at the bottom despite delegating *everything*: routing a write to a board lane is the system's front door, not a subtask spawn — the card lands under another lane's ceiling and the PI's gate, never under the Co-PI's own authority.

However far an agent delegates, the **propose-not-dispose** rule holds for all five: whatever a helper or external agent produces re-enters as a proposal under the originating lane's write ceiling, and the PI disposes. Delegation can move work around; it can never move a decision past the gate.

---

## Related

- The agents ranked above: [Profiles](README.md)
- Why tasks go to specialists at all: [Why specialist profiles, not a generalist agent](../rationale/why-specialist-profiles.md)
- The widest delegator and its external-agent handoff: [The Engineer](engineer.md)
