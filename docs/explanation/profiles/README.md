---
title: Profiles
parent: Explanation
nav_order: 5
has_children: true
permalink: /explanation/profiles/
---

# Profiles

Memoria runs **seven specialist profiles** instead of one generalist agent. Each is a Hermes profile with a fixed identity, a narrow permission contract enforced by the policy MCP, and a clear exit condition. The specialization is the design: a profile that does one thing has permissions you can reason about, failures you can scope, and a quality posture you can name. (For *why* seven specialists beat one generalist, see [Why specialist profiles, not a generalist agent](../rationale/why-specialist-profiles.md).)

The profiles aren't seven equals — they group by where they sit in the knowledge cycle:

## Upstream — bringing knowledge in

| Profile | Posture | One-line |
| --- | --- | --- |
| **[Librarian](librarian.md)** | optimistic | Discovery and ingest. The system's entry point for new sources; proposes generously, lets review gate. |
| **[Mapper](mapper.md)** | read-only | Surveys the existing corpus (scope, gaps, clusters). Never writes canonical content. |
| **[Socratic](socratic.md)** | write-denied | Questions a source or claim in conversation. Architecturally write-denied — its product is your sharpened thinking, not a file. |

## Synthesis — turning knowledge into output

| Profile | Posture | One-line |
| --- | --- | --- |
| **[Writer](writer.md)** | draft-only | Composes prose and outlines. Drafts and proposes, but cannot canonize — the human owns synthesis. |
| **[Verifier](verifier.md)** | flag, don't fix | Traces claims to sources, checks citations, surfaces near-duplicates. Flags; never edits. |
| **[Coder](coder.md)** | delegating | Scaffolds the handoff to an external coding agent and records provenance; the substantive coding happens outside Memoria. |

## Cross-cutting — keeping the vault sound

| Profile | Posture | One-line |
| --- | --- | --- |
| **[Linter](linter.md)** | zero-LLM, dry-run | Deterministic structural validation; reports by default, auto-fixes only cosmetics and log maintenance. |

Each profile page follows the same shape: its mission, *why it's designed this way*, and *what it is not* (the contrasts that keep its boundary sharp).

---

## Delegation posture

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

**Rule:** delegate narrow, temporary, low-risk subtasks; never the defining judgment. The Coder's delegation is widest because the substantive coding *is* an external-agent handoff by design ([ADR-07](../../../project-files/decisions/07-code-agent-attachment.md)); the Socratic profile delegates nothing because it cannot write and its questions are the entire deliverable.

---

## Related

- Why seven specialists, not one generalist: [Why specialist profiles, not a generalist agent](../rationale/why-specialist-profiles.md)
- How profiles pick up and hand off work: [The board as a state machine (the control plane)](../workflows/board-as-state-machine.md)
- Permission matrices — who can write where (lookup tables): [Profile capabilities](../../reference/profiles.md)
