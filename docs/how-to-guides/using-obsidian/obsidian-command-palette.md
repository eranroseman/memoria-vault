---
title: Command palette
parent: Using Obsidian
nav_order: 4
---

# Command palette

Drive Memoria's capture and delegation entry points from `Cmd-P` (`Ctrl-P` on Windows) without leaving Obsidian. This guide covers the pre-wired commands and how to make them fast.

## Prerequisites

- Obsidian open with the vault
- QuickAdd ships bundled and enabled with the starter vault — no install needed (see [Set up Obsidian](../setup/set-up-obsidian.md))
- The Memoria command catalog open for reference: [Obsidian command palette](../../reference/obsidian-command-palette.md)

## Steps

**1. Open the palette and confirm the pre-wired commands are present.**

`Cmd-P` (or `Ctrl-P`) → type `Mem`. The commands ship pre-wired in the starter vault, in two groups ([Obsidian command palette](../../reference/obsidian-command-palette.md) has the full catalog):

**Capture and note creation** — the entry points that must fire from inside the editor:

- `Memoria: capture fleeting` — fleeting note in `notes/fleeting/` from `system/templates/fleeting.md`
- `Memoria: write claim note` — claim note in `notes/claims/` from `system/templates/claim.md` (review-gated home: only you create here)
- `Memoria: capture source from URL` — a capture card on the Librarian lane from a pasted URL
- `Memoria: capture from Zotero selection` — the same capture card, citekey pre-filled from the current Zotero selection
- `Memoria: resolve inbox card` — flips the active Inbox note's `lifecycle` to your verdict in place

**Per-task lane commands** ([#203](https://github.com/eranroseman/memoria-vault/issues/203)) — one command per lane task, each prompting only for what the task needs and creating a correctly-addressed board card:

- `Memoria: catalog a source` · `Memoria: extract claims` · `Memoria: link a claim` · `Memoria: map the corpus` — the Librarian's four tasks
- `Memoria: draft a section` — the Writer's `draft` lane
- `Memoria: verify a draft` — the Peer-reviewer's `verify` lane
- `Memoria: run a pattern` — pick a runnable pattern from `system/patterns/`; the active note rides along
- `Memoria: delegate a task` — the generic fallback: pick any lane (including `code`) and type a free-form goal

The task commands default sensibly off the **active note** — `extract claims` on an open paper or source note, `link a claim` on an open claim, `verify a draft` on an open project file.

**2. Or skip the palette and ask the co-PI.**

The conversational route does the same thing: open the Agent Client pane, say what you want, and the co-PI raises a ceiling-validated card on the right lane ([Agent-client pane](use-the-acp-pane.md)). Use the palette when you already know the lane and task; use the co-PI when you don't, or when the work spans several tasks. Two things have no command at all by design: linting needs no invocation — the Linter is an engine on a daily cron plus the pre-commit gate ([Run the Linter](../operate/run-the-linter.md)) — and project scaffolding returns with the v0.1.2 Project release. The assist surface (find/search/ask from the palette) is tracked in [#380](https://github.com/eranroseman/memoria-vault/issues/380).

**3. Use the palette by type, not by scroll.**

`Cmd-P` → type `M` → the palette filters to `Memoria:` commands only. Type 1–3 more letters to narrow further. The filter is fast enough that you do not need physical hotkeys for most commands.

**4. Assign a physical hotkey to any command you invoke more than ten times a day** (optional).

Settings → Hotkeys → search for the command name → assign a key combination. Reserve physical hotkeys for the genuinely highest-frequency commands only — `Memoria: capture fleeting` is the usual candidate.

## Verify

- `Cmd-P` → `M` returns the `Memoria:` commands in both groups
- `Memoria: capture fleeting` creates a new note in `notes/fleeting/` with `lifecycle: proposed` and `origin: human`
- `Memoria: write claim note` creates a titled claim note in `notes/claims/` from the template — Properties populated, clean body, no template scaffolding
- A task command (e.g. `Memoria: map the corpus`) lands a card on the board: `hermes kanban list` shows it addressed to the right lane

## Related

- Full command catalog, including the removed and retired commands: [Obsidian command palette](../../reference/obsidian-command-palette.md)
- The conversational route: [Agent-client pane](use-the-acp-pane.md)
- QuickAdd and the rest of the plugin set: [Obsidian plugins](../../reference/obsidian-plugins.md)
