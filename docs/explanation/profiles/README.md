---
title: Profiles
parent: Explanation
has_children: true
permalink: /explanation/profiles/
---

# Profiles

Memoria runs **seven specialist profiles** instead of one generalist agent. Each is a Hermes profile with a fixed identity, a narrow permission contract enforced by the policy MCP, and a clear exit condition. The specialization is the design: a profile that does one thing has permissions you can reason about, failures you can scope, and a quality posture you can name. (For *why* seven specialists beat one generalist, see [why-specialist-profiles.md](../architecture/why-specialist-profiles.md).)

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

## Related

- Why seven specialists, not one generalist: [why-specialist-profiles.md](../architecture/why-specialist-profiles.md)
- How profiles pick up and hand off work: [../workflows/board-as-state-machine.md](../workflows/board-as-state-machine.md)
- Permission matrices — who can write where (lookup tables): [reference/profiles.md](../../reference/profiles.md)
