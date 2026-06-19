---
title: Agent-client pane
parent: Using Obsidian
nav_order: 3
---

# Agent-client pane

Talk to the Co-PI from inside Obsidian without switching to a terminal. This guide covers opening the pane, attaching context, reading responses, and ending a session cleanly.

## Prerequisites

- Obsidian open with the vault
- `agent-client` plugin installed and the Hermes gateway reachable ([Set up Hermes](../setup/set-up-hermes.md))

## One agent in the picker — by design

The picker offers exactly one agent: the **Co-PI** (`memoria-copi`) — the only profile you converse with; it delegates every write-task to the background lanes as board cards, and why it's the sole agent is explained in [The agent-client pane](../../explanation/obsidian/agent-client-picker.md). The Co-PI's lane can write nothing, so a pane conversation can never damage the vault — ask freely.

## Opening the pane

The saved **Memoria** reset workspace keeps the pane in the right sidebar, so restoring
the shell brings the Co-PI back beside the active space ([Workspaces](use-workspaces.md)).
Space switching does not reset the chat session because spaces are notes, not workspace
layout swaps. To open it manually: `Cmd/Ctrl+P` -> **Agent Client: Open chat view** or
the Hermes icon in the left ribbon.

## Attaching a note as context

**Auto-mention (default).** With `autoMentionActiveNote` on, the note open in your editor is attached automatically when you open the pane or send a message — it arrives as a context card with no extra step. Open the note you want to discuss first, then open the pane (or just type, if the pane is already open).

**Via the pane directly:**
Click the paperclip icon at the top of the ACP pane → select a file from the picker. Use this when the note you want to discuss isn't the one currently open in the editor.

The attached note appears as a named context card at the top of the conversation. The Co-PI reads its full title and body. It does not follow wikilinks to other notes — attach additional files explicitly if you need them in context.

## Reading responses

Two kinds of turn come back:

- **Conversation** — questions, observations, gentle pushback on the attached note. You are expected to reply. The Co-PI will not produce a finished note: when you've arrived at a durable claim, write the claim note yourself (`Memoria: write claim note`).
- **Delegation receipts** — when you ask for work ("verify this draft", "bring in this paper"), the Co-PI raises a card on the right lane and tells you so. Track it on the board (`hermes kanban list`, or the Board State dashboard); the result lands in your Inbox, not in the pane.

## Ending a session

Leave the pane open during a reading session — sustained questioning across the notes of one topic is its purpose. Press **Clear** at the top of the pane when you finish a paper or topic cluster, before switching to unrelated work. Long histories degrade response quality.

## Exporting a session

Sessions are captured automatically: with the shipped config, opening and closing a chat exports the conversation as a markdown file to `system/exports/` (filenames start with `chat_`). You can also export mid-session via `Cmd/Ctrl+P` → **Agent Client: Export chat**.

Exports are visible raw material for PI review. They are not canonical notes and they do not enter Inbox or fleeting triage automatically. When a conversation contains something durable, promote the insight yourself: create a fleeting note, claim note, source note annotation, or project scratch entry in the right visible folder.

Three folders to **never** point `exportSettings.defaultFolder` at:

- `.memoria/` — hidden runtime internals, not a PI-facing review surface.
- `inbox/` — reserved for agent-raised honesty cards (candidates, gaps, flags, alerts), not chat transcripts.
- `projects/` — active project work belongs here, not chat transcripts.

Auto-export is enabled for both new-chat and close-chat events (`autoExportOnNewChat: true`, `autoExportOnCloseChat: true`) so a pane session has a visible transcript even if Obsidian closes unexpectedly.

## If the pane won't connect

On production Windows, Obsidian and Hermes both run natively. The shipped Agent
Client config should use:

- **WSL mode off.** `windowsWslMode: false`.
- **Command = `hermes`** when the native Hermes installer has placed Hermes on
  your User PATH. If Obsidian was already open during install, fully restart it
  so it sees the updated PATH.

For the Linux/WSL test path where Obsidian runs on Windows and Hermes runs
inside WSL, turn `windowsWslMode` on and point the command at the WSL absolute
Hermes path, for example `/home/<you>/.local/bin/hermes`. That is a test-path
exception, not the production Windows default.

## Verify

- The picker shows one agent — **Co-PI** — and the pane connects
- Opening the pane with a note active attaches it as a context card (auto-mention)
- Asking for lane work ("verify this draft") produces a card on the board, not prose-only
- Pressing **Clear** empties the pane and resets the session

## Related

- Discussing a paper end-to-end: [Discuss a paper](../library/discuss-a-paper.md)
- Gate/reset layout: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- Plugin settings and `customAgents` keys: [Obsidian plugins](../../reference/obsidian-plugins.md)
- Why one agent, not a picker of specialists: [The agent-client pane](../../explanation/obsidian/agent-client-picker.md)
