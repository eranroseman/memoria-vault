---
title: Command palette
parent: Using Obsidian
nav_order: 4
---

# Command palette

The command palette is Obsidian's keyboard launcher for actions. In Memoria it's how you capture notes and hand work to agents without leaving the editor — no buttons to hunt for, no terminal.

Open it with `Cmd-P` (`Ctrl-P` on Windows), then type `Memoria:` to filter to Memoria's commands. Every Memoria action reads `Memoria: <action>`.

The palette is for **actions**, not navigation. To switch between spaces — the rooms you work in, like Library or Knowledge — use the navigator rail (the **Now** / **Places** strip in the left pane), not the palette.

This guide covers the commands that ship pre-wired and how to make them fast.

## Prerequisites

- Obsidian open with the vault
- QuickAdd and Commander ship bundled and enabled with the starter vault — no install needed (see [Set up Obsidian](../setup/set-up-obsidian.md))
- The Memoria command catalog open for reference: [Obsidian command palette](../../reference/obsidian-command-palette.md)

## Steps

**1. Open the palette and confirm the pre-wired commands are present.**

`Cmd-P` (or `Ctrl-P`) → type `Memoria:`. The commands ship pre-wired in the starter vault, in four groups. The full catalog is in [Obsidian command palette](../../reference/obsidian-command-palette.md).

First, a few terms used below:

- **Lane** — a kind of background work an agent does (catalog, extract, draft, verify). Lanes run on the **kanban board**, a column-per-lane task tracker.
- **Card** — a tracked work item: a board card is a task on a lane; an **Inbox** card is something waiting for your attention. The Inbox is a **queue** — a list you work down to empty.
- **Citekey** — a paper's short citation id, e.g. `smith2024`.

**Capture and note creation** — entry points that must fire from inside the editor:

- `Memoria: capture fleeting` — a quick-note form; writes one raw item to `notes/fleeting/`
- `Memoria: write claim note` — a guided form; writes a claim note in `notes/claims/` (only you create these)
- `Memoria: capture source from URL` — turns a pasted URL into a capture card on the Librarian lane
- `Memoria: structured source capture` — a guided form; writes a proposed source note plus an Inbox candidate card
- `Memoria: capture from Zotero selection` — the same capture card, citekey pre-filled from the current Zotero selection
- `Memoria: resolve inbox card` — marks the active Inbox card resolved, in place

**Per-task lane commands** ([#203](https://github.com/eranroseman/memoria-vault/issues/203)) — one command per lane task. Each prompts only for what that task needs, then raises a board card on the right lane:

- `Memoria: catalog source` · `Memoria: extract claims` · `Memoria: link claim` · `Memoria: map corpus` — the Librarian's four tasks
- `Memoria: draft section` — the Writer's `draft` lane
- `Memoria: verify draft` — the Peer-reviewer's `verify` lane
- `Memoria: run pattern` — pick a runnable pattern from `system/patterns/`; the active note rides along
- `Memoria: delegate task` — the generic fallback: pick any lane (including `code`) and type a free-form goal

**Assist commands** — verb-shaped starts, from the palette, a pane conversation, or selected text:

- `Memoria: assist find` · `Memoria: assist search` · `Memoria: assist patterns`
- `Memoria: assist ask` · `Memoria: assist draft` · `Memoria: assist explore`

From the palette or a selection, assist commands stage a card or draft for review. They never write directly to your canonical notes.

**Project commands** — maintenance for a writing project:

- `Memoria: start project` — scaffold `projects/<slug>/` with the project note, first thesis, and gate surface (a **gate** is the human approval step before work advances)
- `Memoria: refresh project gate` — recalculate `project-gate-index.md` from the active project's state
- `Memoria: supersede thesis` — create a replacement thesis, mark the old one superseded, and raise a re-confirmation alert

Task commands default to the **active note** — the file open in your editor. `extract claims` runs on an open paper or source note, `link claim` on an open claim, `verify draft` on an open project file. Assist commands also carry the active note and any selected text as context.

**2. Use the visible buttons for the main loop.**

You don't have to type every command. The most frequent ones also appear as buttons.

The left ribbon holds: capture fleeting, capture from Zotero selection, capture source from URL, delegate task, and resolve inbox card.

The note page header holds: capture fleeting, create linked claim note, write claim note, extract claims, and link claim — so capture stays close while the active-note defaults stay visible.

Navigation lives elsewhere: switch spaces and open the Inbox queue from the navigator rail (**Now** / **Places**) in the left pane, not from the palette.

**3. Reach for the Co-PI when the command isn't obvious.**

The **Co-PI** is the one agent you can chat with, in the Agent Client pane ([Agent Client pane](use-the-agent-client-pane.md)). It complements the palette; it doesn't replace it.

- **Know the lane, task, or assist verb?** Use the palette — it's faster.
- **Not sure which command, or the work spans several tasks?** Ask the Co-PI.
- **Want Ask or Explore to stay a conversation?** Stay in the pane.

When a conversation should produce real work, the Co-PI raises a card on the right lane for you. (It checks the request against that lane's write limits first, so it can't overstep.)

Two things to know:

- **Linting has no command.** The Linter runs on a daily schedule and on each commit, not from the palette ([Run the Linter](../operate/run-the-linter.md)).
- **Starting a project does** — use `Memoria: start project`.

**4. Filter by typing, don't scroll.**

`Cmd-P` → type `Memoria:` → the palette shows Memoria's commands only. Type a few more letters to narrow (e.g. `Memoria: ext` for `extract claims`). Filtering is fast enough that most commands never need a hotkey.

**5. Assign a physical hotkey to any command you invoke more than ten times a day** (optional).

Settings → Hotkeys → search for the command name → assign a key combination. Reserve physical hotkeys for the genuinely highest-frequency commands only — `Memoria: capture fleeting` is the usual candidate.

## Verify

- `Cmd-P` → type `Memoria:` returns the commands in the capture, task, assist, and project groups
- The left ribbon exposes capture, delegate, and resolve controls; the navigator rail (**Now** / **Places**) handles space switching
- `Memoria: capture fleeting` creates a new note in `notes/fleeting/` with `lifecycle: proposed` and `origin: human`, then surfaces it in the Inbox **Fleeting notes** queue
- `Memoria: structured source capture` creates a proposed `notes/sources/` note and an Inbox `candidate` card
- `Memoria: write claim note` opens the guided claim form and creates a titled claim note in `notes/claims/` — Properties populated, clean body, no template scaffolding
- A task command (e.g. `Memoria: map corpus`) lands a card on the board: `hermes kanban list` shows it addressed to the right lane

## Related

- Full command catalog: [Obsidian command palette](../../reference/obsidian-command-palette.md)
- The conversational route: [Agent Client pane](use-the-agent-client-pane.md)
- QuickAdd and the rest of the plugin set: [Obsidian plugins](../../reference/obsidian-plugins.md)
