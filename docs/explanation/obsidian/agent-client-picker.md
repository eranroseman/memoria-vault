---
title: The agent-client pane
parent: Obsidian
nav_order: 6
---

# The agent-client pane

The agent-client plugin implements ACP (Agent Client Protocol) inside Obsidian: a chat pane where the human talks to a Hermes profile, and a picker — driven by its `customAgents` array — for switching which profile is active. This document explains the pane's *design*: why a conversational surface exists at all alongside the board, why switching profiles clears the conversation, and why Memoria labels its profiles by identity rather than by action.

For *how to operate* the pane — opening it, attaching a note as context, reading responses, ending a session — see the how-to guide [How to use the agent-client pane](../../how-to-guides/using-obsidian/use-the-acp-pane.md). For the `data.json` keys, load-bearing settings, hotkeys, and per-device install discipline, see [Obsidian plugins](../../reference/obsidian-plugins.md).

---

## Why a conversational pane at all

Most of Memoria's work flows through the board: a card is created, dispatched, completed, reviewed. The pane is the deliberate exception — the one surface for work that is *synchronous and exploratory* rather than queued and auditable. Thinking a paper through, asking what the corpus already holds, sketching a counter-outline: these are conversations, not tasks with a fixed output. Forcing them onto the board would produce cards that never cleanly close, because the "output" lives in the human's understanding, not in a file.

So the pane and the board divide cleanly: **the board is for work that produces a reviewable artifact; the pane is for thinking that produces a clearer human.** Anything from a pane session that *should* become durable (a claim note, a draft) is written through the normal gated path afterward — the pane itself writes nothing canonical (Socratic writes nothing at all).

## Why the conversation clears on profile switch

Switching the picker to a different profile discards the current conversation, by design. Each profile is a distinct specialist with its own permission contract and its own frame; carrying a Mapper exchange into a Socratic session would blur whose questions are being asked and invite the human to run, say, a drafting operation inside what they think is a read-only corpus query. A cleared pane on switch makes the boundary between specialists physical rather than a matter of discipline — the same separation the three-dimension card schema enforces on the board, applied to the interactive surface. (The persistent exception is Socratic, which stays open across notes *within* a reading session precisely because sustained questioning is its whole purpose.)

## Profiles, not modes

The picker is a **profile switcher**, not a mode selector. Each entry is a distinct specialist with a fixed permission contract. Memoria labels its profiles by identity — Socratic, Mapper, Writer, Verifier — because they are different agents, not different modes of one agent.

An earlier design borrowed verb-label conventions (Ask / Map / Draft / Check) that name actions inside one assistant. Memoria's entries are separate agents — closer to role-named specialists like Architect and Orchestrator. The label names the contract-holder; the description carries the "what happens next."

---

## The four ACP-suitable profiles

| Picker label | Profile | Invocation pattern | Why |
| --- | --- | --- | --- |
| **Socratic** — Think a source through in conversation before distilling it | `memoria-socratic` | Persistent pane (default) | Long conversations during processing. Architecturally write-denied — safe on any device. The standard ACP use case: open the pane in the Reading & Processing workspace, talk through a paper note via questioning. |
| **Mapper** — Map a project's corpus: what's ready, thin, missing | `memoria-mapper` | Transient session | Quick corpus-retrieval queries via command palette. Session opens, returns results, closes. Not for persistent chat. |
| **Writer** — Distill sources into claim notes; turn framings into drafts | `memoria-writer` | Transient session | Quick drafting assistance via command palette ("counter-outline this section"). Useful with discipline — interactive `chat` mode only. Session closes after response. |
| **Verifier** — Trace a draft's claims back to their sources; flag the gaps | `memoria-verifier` | Transient session | Pre-filing similarity check ("show top-3 similar notes to this claim"). Returns ranked list, session closes. |

Socratic is the **persistent** default because reading sessions demand sustained conversation. The other three are transient — they answer one question and close, which keeps context discipline and prevents the human from accidentally running drafting operations in a persistent Mapper session.

---

## Why three profiles are absent from the picker

**Librarian** — network-active; every `find`-style chat costs external API calls. Better dispatched via cards (queued, audited, retryable). Add only if the human specifically wants interactive discovery and accepts the cost.

**Coder** — delegates substantive coding to an external coding agent. The Hermes-side Coder profile doesn't fit ACP chat — its work happens in the external agent's session, not in a conversational pane.

**Linter** — background-only by design. No interactive use case.

---

## Related

- Socratic profile: [The Socratic](../profiles/socratic.md)
- Reading & Processing workspace (where the persistent ACP pane lives): [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- Plugin settings: [Obsidian plugins](../../reference/obsidian-plugins.md)
