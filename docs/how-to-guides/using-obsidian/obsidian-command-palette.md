---
title: Command palette
parent: Using Obsidian
nav_order: 4
---

# Command palette

Drive Memoria's capture and delegation entry points from `Cmd-P` (`Ctrl-P` on Windows) without leaving Obsidian. This guide covers the pre-wired commands and how to make them fast.

## Prerequisites

- Obsidian open with the vault
- QuickAdd and Commander ship bundled and enabled with the starter vault — no install needed (see [Set up Obsidian](../setup/set-up-obsidian.md))
- The Memoria command catalog open for reference: [Obsidian command palette](../../reference/obsidian-command-palette.md)

## Steps

**1. Open the palette and confirm the pre-wired commands are present.**

`Cmd-P` (or `Ctrl-P`) → type `Mem`. The commands ship pre-wired in the starter vault, in two groups ([Obsidian command palette](../../reference/obsidian-command-palette.md) has the full catalog):

**Capture and note creation** — the entry points that must fire from inside the editor:

- `Memoria: capture fleeting` — fleeting note in `notes/fleeting/` from `system/templates/fleeting.md`
- `Memoria: write claim note` — claim note in `notes/claims/` from `system/templates/claim.md` (review-gated home: only you create here)
- `Memoria: capture source from URL` — a capture card on the Librarian lane from a pasted URL
- `Memoria: structured source capture` — a guided Modal Forms capture that writes a proposed source note plus Inbox candidate
- `Memoria: capture from Zotero selection` — the same capture card, citekey pre-filled from the current Zotero selection
- `Memoria: resolve inbox card` — flips the active Inbox note's `lifecycle` to a schema-valid outcome in place

**Per-task lane commands** ([#203](https://github.com/eranroseman/memoria-vault/issues/203)) — one command per lane task, each prompting only for what the task needs and creating a correctly-addressed board card:

- `Memoria: catalog source` · `Memoria: extract claims` · `Memoria: link claim` · `Memoria: map corpus` — the Librarian's four tasks
- `Memoria: draft section` — the Writer's `draft` lane
- `Memoria: verify draft` — the Peer-reviewer's `verify` lane
- `Memoria: run pattern` — pick a runnable pattern from `system/patterns/`; the active note rides along
- `Memoria: delegate task` — the generic fallback: pick any lane (including `code`) and type a free-form goal

**Assist commands** — verb-shaped starts from the palette, a pane conversation, or selected text:

- `Memoria: assist find` · `Memoria: assist search` · `Memoria: assist patterns`
- `Memoria: assist ask` · `Memoria: assist draft` · `Memoria: assist explore`

Palette/selection assist commands create cards or proposal artifacts in staging. They never write directly to canonical notes.

The task commands default sensibly off the **active note** — `extract claims` on an open paper or source note, `link a claim` on an open claim, `verify a draft` on an open project file. Assist commands also carry the active note and selected text as context when present.

**2. Use the visible toolbar buttons for the main loop.**

Commander places the high-frequency commands directly in Obsidian chrome: the left ribbon has capture fleeting, capture from Zotero selection, capture source from URL, delegate task, resolve inbox card, and the Desk/Library/Studio workspace switchers. The note page header has create linked claim note, write claim note, extract claims, and link claim, so active-note defaults are visible when you invoke them.

**3. Or skip the palette and ask the Co-PI.**

The conversational route does the same thing: open the Agent Client pane, say what you want, and the Co-PI raises a ceiling-validated card on the right lane when work should become durable ([Agent-client pane](use-the-acp-pane.md)). Use the palette when you already know the lane, task, or assist verb; use the Co-PI when you don't, when the work spans several tasks, or when Ask/Explore should stay conversational. Two things have no command at all by design: linting needs no invocation — the Linter is an operation on a daily cron plus the pre-commit gate ([Run the Linter](../operate/run-the-linter.md)) — and project scaffolding returns with the deferred Project workflow after alpha.3.

**4. Use the palette by type, not by scroll.**

`Cmd-P` → type `M` → the palette filters to `Memoria:` commands only. Type 1–3 more letters to narrow further. The filter is fast enough that you do not need physical hotkeys for most commands.

**5. Assign a physical hotkey to any command you invoke more than ten times a day** (optional).

Settings → Hotkeys → search for the command name → assign a key combination. Reserve physical hotkeys for the genuinely highest-frequency commands only — `Memoria: capture fleeting` is the usual candidate.

## Verify

- `Cmd-P` → `M` returns the `Memoria:` commands in the capture, task, assist, and workspace groups
- The left ribbon exposes capture, delegate, resolve, and Desk/Library/Studio workspace buttons
- `Memoria: capture fleeting` creates a new note in `notes/fleeting/` with `lifecycle: proposed` and `origin: human`
- `Memoria: structured source capture` creates a proposed `notes/sources/` note and an Inbox `candidate` card
- `Memoria: write claim note` creates a titled claim note in `notes/claims/` from the template — Properties populated, clean body, no template scaffolding
- A task command (e.g. `Memoria: map corpus`) lands a card on the board: `hermes kanban list` shows it addressed to the right lane

## Related

- Full command catalog, including the removed and retired commands: [Obsidian command palette](../../reference/obsidian-command-palette.md)
- The conversational route: [Agent-client pane](use-the-acp-pane.md)
- QuickAdd and the rest of the plugin set: [Obsidian plugins](../../reference/obsidian-plugins.md)
