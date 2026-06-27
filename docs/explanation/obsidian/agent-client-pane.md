---
title: The Agent Client pane
parent: Obsidian
grand_parent: Explanation
nav_order: 4
---

# The Agent Client pane

The agent-client plugin implements ACP (Agent Client Protocol) inside Obsidian: a chat pane where the human talks to a Hermes profile. The pane hosts **one agent — the Co-PI** (Memoria's single conversational agent — see [Glossary](../../reference/glossary.md)) ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)). The specialists (Librarian, Writer, Peer-reviewer, Engineer) are **board lanes** (background workers on the kanban board — see [Glossary](../../reference/glossary.md)), not conversation partners, and the Co-PI delegates cards (units of delegated work) to them.

For *how to operate* the pane — opening it, attaching a note as context, reading responses, ending a session — see the how-to guide [Agent Client pane](../../how-to-guides/using-obsidian/use-the-agent-client-pane.md). For the `data.json` keys, load-bearing settings, hotkeys, and per-device install discipline, see [Obsidian plugin settings](../../reference/obsidian-plugin-settings.md) and [Obsidian plugin data files](../../reference/obsidian-plugin-data-files.md).

---

## Exploratory vs. durable work

The practical discipline the pane asks of the human:

- **Stay in the pane** while the work is exploratory — questioning a source, branching framings, asking what exists. The output is your sharpened thinking; nothing needs to be filed.
- **Leave the pane** the moment the work should produce an artifact. Either write it yourself through the gated path (a claim note, a draft edit), use the matching direct command, or ask the Co-PI to delegate it — "draft this section" becomes a card on the draft lane, with a reviewable output and an audit trail.

A pane session that keeps producing things you wish were files is the signal to switch modes: conversations are for converging on what to make, cards are for making it.

---

## Related

- The one agent in the pane: [The Co-PI](../profiles/co-pi.md)
- Why the pane exists: [Why the Agent Client pane exists](../../design/why-agent-client-pane.md)
- Operating the pane: [Agent Client pane](../../how-to-guides/using-obsidian/use-the-agent-client-pane.md)
- Where delegated work goes: [The control plane](../architecture/control-plane.md)
- Plugin settings: [Obsidian plugin settings](../../reference/obsidian-plugin-settings.md)
- Plugin data-file conventions: [Obsidian plugin data files](../../reference/obsidian-plugin-data-files.md)
