---
title: Hermes boundary
parent: Design Book
grand_parent: Developers
nav_order: 14
---

# Hermes boundary

Memoria's alpha.15 design does not use Hermes. The product runtime is the
standalone CLI/engine, local workspace database, checked knowledge files, qmd
search, and optional machine transports owned by the engine.

Hermes remains useful historical context because earlier Memoria designs used
profiles, lanes, board state, and dispatcher concepts. Those mechanisms are not
part of the alpha.15 baseline.

---

## Baseline

| Question | Alpha.15 answer |
| --- | --- |
| Does setup install Hermes? | No. |
| Does runtime require Hermes profiles, lanes, Kanban, cron, or API server surfaces? | No. |
| Does Memoria ship a Hermes adapter? | No. |
| Can a user experiment with Hermes outside Memoria? | Yes, but it must call the same CLI/engine and cannot own state or policy. |

## Boundary

If someone builds an external Hermes experiment later, it is a client of
Memoria, not a Memoria runtime layer. It must not own:

- source authority
- operation manifests
- request lifecycle
- write policy
- provider configuration
- qmd indexing
- checks, recovery, or git/journal history

---

## Why keep this page

The page exists to prevent old profile/lane/board assumptions from leaking back
into current docs or implementation. The durable design decision is negative:
Memoria must operate completely without Hermes.

---

## Related

**Explanation**

- Why requests, workers, and workspace knowledge are separate: [Why the architecture is layered](why-layered-architecture.md)
- The current request state machine: [Request states and the review gate](../explanation/kanban-board/states.md)

**Reference**

- Current command surface: [CLI](../reference/cli.md)
- No Hermes command surface: [Hermes CLI](../reference/hermes-cli.md)
