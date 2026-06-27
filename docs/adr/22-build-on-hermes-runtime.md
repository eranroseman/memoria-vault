---
topic: decisions
id: 22
title: Build on the Hermes Agent runtime rather than a bespoke one
nav_exclude: true
status: accepted
date_proposed: 2026-06-01
date_resolved: 2026-06-01
assumes: []
supersedes: []
superseded_by: []
---

# ADR-22: Build on the Hermes Agent runtime rather than a bespoke one

## Context

> *Note (v0.1.0-alpha.2): the "seven specialist `SOUL.md`s" below predates [ADR-48](48-copi-and-agent-consolidation.md), which consolidated the fleet to **five** profiles; likewise the ADR-01 three-layer framing in Related was superseded by the seven-layer model ([ADR-46](46-seven-layer-architecture.md)). The build-on-Hermes decision itself is unchanged.*

Memoria's entire execution layer — the Kanban board, the worker profiles, the dispatcher, the programmatic API — is supplied by an external runtime, [Hermes Agent](https://hermes-agent.nousresearch.com/) (Nous Research). This is a foundational, hard-to-reverse dependency: it determines what the board *is*, how profiles claim work, and where integrations connect. The choice was explained at length in [Why Hermes](../explanation/rationale/why-hermes.md) but never recorded as a decision, so the alternatives that were weighed — and the precise Memoria/Hermes boundary — had no fixed anchor. An ADR matters here specifically to preserve *what was rejected and why*, which is the part most likely to be re-litigated when a shinier runtime appears.

## Decision

Memoria builds **on** Hermes rather than implementing its own runtime. Hermes owns the execution substrate: the persistent Kanban board (`kanban.db`) as a durable cross-session state machine, the profile mechanism (`SOUL.md` identity, `config.yaml` model routing, lane permissions), the dispatcher that claims `ready` cards and advances state with retries, and the native memory tiers, MCP host, and API server (port 8642). Memoria supplies only the *conventions on top* — the review-gate overlay in card `metadata`, the policy MCP that gates writes, the seven specialist `SOUL.md`s, and the vault schema — all riding Hermes's extension points without modifying it. The governing rule of thumb: **Hermes moves work; Memoria decides what work means and what may become canonical.**

## Consequences

- Memoria's design effort goes entirely into the knowledge layer, which is where its actual contribution lies; the hardest runtime problems (durable state across crashes, atomic card claiming, retry semantics, MCP hosting) are not Memoria's to solve.
- Memoria stays compatible with a stock Hermes install: the overlay lives in card `metadata` that Hermes treats as opaque, so the board works with standard Hermes tooling.
- The cost is a standing dependency on an external runtime's release cadence and conventions. This is accepted deliberately, and it is why [Hermes conventions are reused verbatim](../explanation/rationale/why-hermes.md) rather than renamed.
- The boundary is load-bearing: anything that would require *modifying* Hermes internals (rather than riding its MCP/metadata/lane extension points) is a signal the design has drifted and should be reconsidered against this ADR.
- The same "thin front over a mature external engine" logic recurs in [ADR-07](07-delegate-coding-to-external-agents.md) (Coder delegates to external coding agents); the two decisions share a rationale and should move together if that rationale is ever revisited.

## Alternatives considered

**Build a bespoke runtime.** Rejected: its hardest parts are exactly what Hermes already solves, so a reimplementation would be a worse copy plus a permanent maintenance burden, for no gain in the knowledge layer.

**AutoGen-style chat-as-substrate.** Rejected: routing durable work state through a conversation transcript puts state in the wrong layer. Memoria's state must survive `/clear` and cross-profile handoffs in thick stores (board, vault), not in chat history ([the memory model](../explanation/architecture/memory-model.md)).

**OpenHands-style sandbox-vs-host permission model.** Rejected: it routes permissions through a sandbox boundary, whereas Memoria needs permissions enforced per-profile at the write layer (the policy MCP), independent of where execution runs.

**Render the board with the Obsidian Kanban plugin.** Rejected: the authoritative board is Hermes's `kanban.db`, surfaced via the Dataview-backed [`board-state`](../explanation/dashboards/daily-glance/board-state.md) dashboard. The plugin reads only its own single-file Kanban-format markdown (`kanban-plugin: board` frontmatter), of which there is none. Bridging them — the `hermes-kanban` translation layer — works but couples two state machines for no gain; the Hermes Workspace board view and the `board-state` dashboard already cover visualization. (Obsidian Kanban remains fine for standalone personal boards unrelated to the Hermes board.)

## Related

- **Supporting rationale:** [Why Hermes](../explanation/rationale/why-hermes.md) (what Hermes provides, the boundary table, the API surface), [Why the architecture is layered](../explanation/rationale/why-three-layers.md) (thin-control-over-thick-state), [Pattern provenance: borrow, adapt, ignore](../explanation/rationale/why-pattern-provenance.md) (this as a deliberate "borrow").
- **Related decisions:** [ADR-01 three-layer architecture](01-three-layer-architecture.md) (the layers Hermes coordinates); [ADR-02 seven specialist profiles](02-seven-specialist-profiles.md) (the profiles *are* Hermes profiles, and there is no Orchestrator); [ADR-07 external coding agent boundary](07-delegate-coding-to-external-agents.md) (same thin-front rationale).
- **Source discussion:** retroactively records the runtime choice already embedded in `why-hermes.md`. The evolving detail of the boundary lives in that doc; the decision to build on Hermes rather than reimplement it is what this ADR fixes.
