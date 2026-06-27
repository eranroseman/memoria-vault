---
title: Command palette
parent: Using Obsidian
grand_parent: How-to guides
nav_order: 4
---

# Command palette

The command palette is Obsidian's keyboard launcher for actions. In Memoria it's how you capture notes and hand work to agents without leaving the editor — no buttons to hunt for, no terminal.

Open it with `Cmd-P` (`Ctrl-P` on Windows), then type `Memoria:` to filter to Memoria's commands. Every Memoria action reads `Memoria: <action>`.

The palette is for **actions**, not navigation. To switch between spaces — the rooms you work in, like Library or Knowledge — use the navigator rail (the **Now** / **Places** strip in the left pane), not the palette.

This guide covers how to use the palette quickly. The full command inventory
lives in [Obsidian command palette](../../reference/obsidian-command-palette.md).

## Prerequisites

- Obsidian open with the vault
- QuickAdd and Commander ship bundled and enabled with the starter vault — no install needed (see [Set up Obsidian](../setup/set-up-obsidian.md))
- The command reference if you need exact names: [Obsidian command palette](../../reference/obsidian-command-palette.md)

## Steps

**1. Open the palette and confirm the pre-wired commands are present.**

`Cmd-P` (or `Ctrl-P`) → type `Memoria:`. The starter vault ships pre-wired
capture, task, assist, inbox, and project commands. Confirm they appear; use the
reference page only when you need an exact command name or implementation source.

Task commands default to the **active note**. Assist commands also carry the
active note and any selected text as context. Navigation commands are the
exception: prefer the left-pane rail for spaces and Inbox.

**2. Use the visible buttons for the main loop.**

You don't have to type every command. The most frequent ones also appear as
buttons in the left ribbon, note header, and left-pane rail.

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

- `Cmd-P` → type `Memoria:` returns Memoria commands
- The left ribbon exposes capture, delegate, and resolve controls; the navigator rail (**Now** / **Places**) handles space switching
- `Memoria: capture fleeting` creates a new note in `notes/fleeting/` with `lifecycle: proposed` and `origin: human`, then surfaces it in the Inbox **Fleeting notes** queue
- `Memoria: structured source capture` creates a proposed `notes/sources/` note and an Inbox `candidate` card
- `Memoria: write claim note` opens the guided claim form and creates a titled claim note in `notes/claims/` — Properties populated, clean body, no template scaffolding
- A task command (e.g. `Memoria: map corpus`) lands a card on the board: `hermes kanban list` shows it addressed to the right lane

## Related

- Full command catalog: [Obsidian command palette](../../reference/obsidian-command-palette.md)
- The conversational route: [Agent Client pane](use-the-agent-client-pane.md)
- QuickAdd and the rest of the plugin set: [Obsidian plugins](../../reference/obsidian-plugins.md)
