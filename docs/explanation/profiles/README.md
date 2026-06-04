---
title: Profiles
parent: Explanation
nav_order: 5
has_children: true
permalink: /explanation/profiles/
---

# Profiles

Memoria runs **seven specialist profiles** instead of one generalist agent. Each is a Hermes profile with a fixed identity, a narrow permission contract enforced by the policy MCP, and a clear exit condition. The specialization is the design: a profile that does one thing has permissions you can reason about, failures you can scope, and a quality posture you can name.

The profiles aren't seven equals — they group by which flow of the [knowledge cycle](../workflows/compile-and-compose.md) they serve, and each owns specific phases of it. Each profile page follows the same shape: its mission, *why it's designed this way*, and *what it is not* (the contrasts that keep its boundary sharp).

## Compile — bringing knowledge in

| Profile | Posture | Phase(s) | What it covers |
| --- | --- | --- | --- |
| **[Librarian](librarian.md)** | optimistic | find · capture · enrich | Discovery and ingest. The system's entry point for new sources; proposes generously, lets review gate. |
| **[Socratic](socratic.md)** | write-denied | discuss | Questions a source or claim in conversation. Architecturally write-denied — its product is your sharpened thinking, not a file. |

## Compose — turning knowledge into output

| Profile | Posture | Phase(s) | What it covers |
| --- | --- | --- | --- |
| **[Mapper](mapper.md)** | read-only | assess | Surveys the existing corpus (scope, gaps, clusters) to open a writing project. Never writes canonical content. |
| **[Writer](writer.md)** | draft-only | frame · draft | Composes prose and outlines. Drafts and proposes, but cannot canonize — the human owns synthesis. |
| **[Verifier](verifier.md)** | flag, don't fix | verify | Traces claims to sources, checks citations, surfaces near-duplicates. Flags; never edits. |
| **[Coder](coder.md)** | delegating | code (parallel branch) | Scaffolds the handoff to an external coding agent and records provenance; the substantive coding happens outside Memoria. |

## Cross-cutting — keeping the vault sound

| Profile | Posture | Phase(s) | What it covers |
| --- | --- | --- | --- |
| **[Linter](linter.md)** | zero-LLM, dry-run | — (any phase) | Deterministic structural validation; reports by default, auto-fixes only cosmetics and log maintenance. |

The phases no profile owns are the **human's**: `classify`, `distill`, and `connect` on the Compile side, `sketch` and the `review` gate on the Compose side. Agents find, capture, propose, draft, and check; the human canonizes. (`export` is a mechanical Pandoc render the human triggers.)

## Where to go next

- Why seven specialists, not one generalist: [Why specialist profiles, not a generalist agent](../rationale/why-specialist-profiles.md)
- How much each profile may delegate, and the rule that bounds it: [Delegation posture](delegation-posture.md)
- The phases each profile owns, in flow context: [The Compile and Compose flows](../workflows/compile-and-compose.md)
- How profiles pick up and hand off work: [The board as a state machine (the control plane)](../workflows/board-as-state-machine.md)
- Permission matrices — who can write where (lookup tables): [Profile capabilities](../../reference/profiles.md)
