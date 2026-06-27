---
title: Why profile boundaries exist
parent: Design Book
grand_parent: Developers
nav_order: 25
---

# Why profile boundaries exist

Memoria uses one conversational Co-PI plus four background lanes because each
role has a different authority boundary. The Co-PI is memory-carrying and
read-only; the lanes are scoped, stateless executors; the PI is the only actor
that disposes.

The hard split prevents three collapses:

- **Conversation into writing.** A chat can drift and persuade; a board card has
  scoped permissions, a payload, and review state. The Co-PI can route work, but
  it cannot write canonical files.
- **Production into verification.** The Writer produces drafts; the Peer-reviewer
  checks them. An author grading its own output is the rubber-stamp failure the
  role split exists to prevent.
- **Operations into agents.** Deterministic work such as ingest, sweeps, and
  linting is an operation, not a posture-bearing agent. Agents spend judgment
  only where judgment is needed.

Delegation follows the same rule: delegate narrow support work, never the
profile's defining judgment. The Engineer delegates most widely because coding
itself is an external-agent handoff; the Co-PI delegates only by creating cards
under another lane's ceiling. In all cases, outputs re-enter as proposals and
the PI decides.

## Related

- Profile roster and lane map: [Profiles](../explanation/profiles/README.md)
- Why specialist profiles: [Why specialist profiles, not a generalist agent](why-specialist-profiles.md)
- The structural gate: [Why the review gate is structural](why-human-gate.md)
