# Why Hermes

Memoria's entire execution layer is [Hermes Agent](https://hermes-agent.nousresearch.com/) (Nous Research). The board is Hermes's Kanban, the workers are Hermes profiles, the dispatcher is Hermes's, and the integration endpoint is Hermes's API server. This page explains why Memoria builds *on* a runtime rather than building its own, what Hermes provides, and where the Memoria/Hermes boundary falls.

If Memoria is *what you keep* — the vault, the knowledge, the schema — Hermes is *who moves things*: it carries work between states, between profiles, and between the human and the vault.

---

## What Hermes provides

Memoria needs an execution substrate with four properties, and Hermes ships all four:

- **A persistent Kanban board** (`kanban.db`) — a durable state machine across sessions and retries. When a session closes, work state survives; the next worker picks the card up from its last known state. This is the [thin-control-over-thick-state](why-three-layers.md) requirement made concrete.
- **Profiles with lanes** — each agent is a named profile (`SOUL.md` identity, `config.yaml` model routing, lane-override permissions) that claims cards on its lane. Memoria's seven specialists *are* Hermes profiles.
- **A dispatcher** — claims `ready` cards for matching profiles, runs them, advances state, retries on recoverable failure. Memoria adds routing *rules*, not a routing *agent* (there is no Orchestrator — see [why-specialist-profiles.md](why-specialist-profiles.md)).
- **Native memory, MCP, and an API** — profile memory (`MEMORY.md`/`USER.md`), an MCP server interface (which Memoria's policy gate plugs into), and a network endpoint for programmatic triggers.

Memoria supplies the *conventions on top*: the review-gate overlay in card `metadata`, the policy MCP that gates writes, the seven specialist `SOUL.md`s, and the vault schema. None of those require modifying Hermes — they ride its extension points.

---

## Why not build our own runtime

A bespoke agent runtime would be a large, ongoing engineering commitment whose hardest parts — durable state across crashes, atomic card claiming, retry semantics, memory tiers, an MCP host — are exactly what Hermes already solves. Reimplementing them would produce a worse copy and a maintenance burden, the same reasoning that makes [Coder a thin front for external coding agents](../profiles/coder.md) rather than a reimplementation of them.

Building on Hermes also keeps Memoria compatible with stock `hermes` tooling: the board works with any standard Hermes install, and Memoria's overlay lives in `metadata` that Hermes treats as opaque (see [the card schema](../kanban-board/card-schema.md)). The cost of this choice is a dependency on an external runtime's release cadence and conventions; the benefit is that Memoria's design effort goes entirely into the *knowledge* layer, which is where its actual contribution lies.

This is a deliberate **borrow** in the [pattern-provenance](why-pattern-provenance.md) sense: Hermes's persistent-Kanban-plus-worker-lanes pattern is adopted wholesale; what Memoria declines from other runtimes is, e.g., chat-as-substrate (AutoGen) and sandbox-vs-host permission models (OpenHands), because those route durable state or permissions through the wrong layer.

---

## The programmatic surface (the API server)

Hermes exposes an **API server** (port 8642) — the surface where *programs*, not humans, connect to Memoria. File-system watchers, Zotero/Better BibTeX hooks, git `post-commit` hooks, calendar integrations, and cross-machine dispatch all enter here.

**Why a separate surface at all.** Programmatic integration needs a different interface than human operation. A file-system watcher that fires on a PDF drop cannot use the command palette; a Better BibTeX script that fires on Zotero save needs a network endpoint. The API is the integration surface for automation; Obsidian, the CLI, and Telegram (see [human-channels.md](human-channels.md)) are the interaction surfaces for humans. The same operations available through the API are exposed to humans through the palette and CLI with better affordances — so humans never need to touch the API directly.

**It grants no extra power.** Every write through the API still passes through the policy MCP. A program calling the API has exactly the permissions of the profile it acts as — no elevation. The API is a different *door*, not a different *key*. See [reference/policy-mcp.md](../../reference/policy-mcp.md) for enforcement details.

This is why the API server lives here, with Hermes, rather than in [human-channels.md](human-channels.md): it is a Hermes integration surface that humans never operate, not a human channel.

---

## The Memoria / Hermes boundary

| Concern | Owned by |
| --- | --- |
| Board state machine, dispatcher, retries | Hermes |
| Profile mechanism (identity, model routing, lanes) | Hermes |
| Native memory tiers, MCP host, API server | Hermes |
| Review-gate overlay (`review_status`, `agent_recommendation`) | Memoria (card `metadata`) |
| Write-gating policy MCP | Memoria (plugs into Hermes's MCP interface) |
| The seven specialist `SOUL.md`s and lane-overrides | Memoria |
| The vault, schema, and note types | Memoria |

The rule of thumb: **Hermes moves work; Memoria decides what work means and what may become canonical.**

---

## Related

**Explanation**

- What Hermes coordinates — the three layers: [why-three-layers.md](why-three-layers.md)
- The board as a state machine: [../workflows/board-as-state-machine.md](../workflows/board-as-state-machine.md)
- The card-schema overlay Memoria adds on top of Hermes: [../kanban-board/card-schema.md](../kanban-board/card-schema.md)
- The human interaction surfaces (Obsidian, CLI, Telegram): [human-channels.md](human-channels.md)

**Reference**

- What the API's writes pass through: [reference/policy-mcp.md](../../reference/policy-mcp.md)
- Hermes admin commands (reference): [reference/hermes-cli.md](../../reference/hermes-cli.md)
