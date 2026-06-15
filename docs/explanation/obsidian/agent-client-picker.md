---
title: The agent-client pane
parent: Obsidian
nav_order: 4
---

# The agent-client pane

The agent-client plugin implements ACP (Agent Client Protocol) inside Obsidian: a chat pane where the human talks to a Hermes profile. In v0.1.0-alpha.2 the pane hosts **one agent — the Co-PI** ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)). There is no profile picker to manage: the specialists (Librarian, Writer, Peer-reviewer, Engineer) are **board lanes**, not conversation partners, and the Co-PI delegates cards to them. This document explains the pane's *design*: why a conversational surface exists at all alongside the board, and why exactly one agent lives in it.

For *how to operate* the pane — opening it, attaching a note as context, reading responses, ending a session — see the how-to guide [Agent-client pane](../../how-to-guides/using-obsidian/use-the-acp-pane.md). For the `data.json` keys, load-bearing settings, hotkeys, and per-device install discipline, see [Obsidian plugins](../../reference/obsidian-plugins.md).

---

## Why a conversational pane at all

Most of Memoria's work flows through the board: a card is created, dispatched, completed, reviewed. The pane is the deliberate exception — the one surface for work that is *synchronous and exploratory* rather than queued and auditable. Thinking a paper through, asking what the corpus already holds, sketching a counter-outline: these are conversations, not tasks with a fixed output. Forcing them onto the board would produce cards that never cleanly close, because the "output" lives in the human's understanding, not in a file.

So the pane and the board divide cleanly: **the board is for work that produces a reviewable artifact; the pane is for thinking that produces a clearer human.** Anything from a pane session that *should* become durable (a claim note, a draft) is written through the normal gated path afterward — by the PI directly, or as a card the Co-PI delegates. The pane itself writes nothing canonical: the Co-PI is structurally read-only ([The Co-PI](../profiles/co-pi.md)).

## Why one agent, not a picker

An earlier design put four ACP-suitable profiles behind a picker (Socratic, Mapper, Writer, Verifier) and cleared the conversation on every switch, so that one specialist's context couldn't bleed into another's permission contract. ADR-48 retired that design by consolidating the conversational roles into the Co-PI: questioning is its own verb (the old Socratic role, folded in), and the Mapper/Writer/Verifier jobs became delegations to the map, draft, and verify lanes.

The consolidation dissolves the problem the picker existed to manage. With one agent in the pane there is no contract boundary to police mid-conversation — the Co-PI holds a single, hard contract (read-only; every write leaves as a card), so no exchange can talk it into a write it isn't allowed. And because there is no switch, **the conversation persists** — and a persisting conversation is exactly what the Co-PI's memory loop needs to compound into a genuine Co-PI rather than a stateless assistant ([The Co-PI](../profiles/co-pi.md)).

What the picker's separation protected now lives where it belongs — on the board. Each lane runs under its own scoped write ceiling, each delegation is ceiling-validated, and each result comes back through the review gate ([The control plane](../architecture/control-plane.md)). The boundary between specialists is physical (separate dispatched processes with separate permissions), not a UI affordance the human must operate correctly.

The assist surface keeps that split visible instead of hiding it behind the old picker. Find/Search/Patterns/Ask/Draft/Explore exist as direct palette commands and can carry the active editor selection into a staged card or proposal artifact; the same verbs can also start in the pane as conversation. The rule is the same in both places: exploratory Ask/Explore can stay read-only in the pane, while anything durable leaves through a gated card or PI-authored note ([Obsidian command palette](../../reference/obsidian-command-palette.md)).

## Exploratory vs. durable work

The practical discipline the pane asks of the human survives from the original design unchanged:

- **Stay in the pane** while the work is exploratory — questioning a source, branching framings, asking what exists. The output is your sharpened thinking; nothing needs to be filed.
- **Leave the pane** the moment the work should produce an artifact. Either write it yourself through the gated path (a claim note, a draft edit) or ask the Co-PI to delegate it — "draft this section" becomes a card on the draft lane, with a reviewable output and an audit trail.

A pane session that keeps producing things you wish were files is the signal to switch modes: conversations are for converging on what to make, cards are for making it.

---

## Related

- The one agent in the pane: [The Co-PI](../profiles/co-pi.md)
- Operating the pane: [Agent-client pane](../../how-to-guides/using-obsidian/use-the-acp-pane.md)
- Where delegated work goes: [The control plane](../architecture/control-plane.md)
- Plugin settings: [Obsidian plugins](../../reference/obsidian-plugins.md)
