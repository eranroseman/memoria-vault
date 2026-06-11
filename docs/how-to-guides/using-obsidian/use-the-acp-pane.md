---
title: Agent-client pane
parent: Using Obsidian
nav_order: 3
---

# Agent-client pane

Talk to the co-PI from inside Obsidian without switching to a terminal. This guide covers opening the pane, attaching context, reading responses, and ending a session cleanly.

## Prerequisites

- Obsidian open with the vault
- `agent-client` plugin installed and the Hermes gateway reachable ([Set up Hermes](../setup/set-up-hermes.md))

## One agent in the picker — by design

The picker offers exactly one agent: the **co-PI** (`memoria-copi`, ADR-48). It is the only profile you converse with — it questions your reading Socratically, explains how the system works, and **delegates** every write-task to the background lanes (Librarian, Writer, Peer-reviewer, Engineer) as ceiling-validated board cards via `delegate_route_task`. The lanes run on Kanban dispatch and never appear in this pane; their results resurface as cards in your Inbox. For the design rationale, see [The agent-client pane](../../explanation/obsidian/agent-client-picker.md).

The co-PI's lane can write nothing, so a pane conversation can never damage the vault — ask freely.

## Opening the pane

`Cmd/Ctrl+P` → **Agent Client: Open chat view**, or click the Hermes icon in the left ribbon. The pane keeps its session across workspace switches ([Workspaces](use-workspaces.md)).

## Attaching a note as context

**Auto-mention (default).** With `autoMentionActiveNote` on, the note open in your editor is attached automatically when you open the pane or send a message — it arrives as a context card with no extra step. Open the note you want to discuss first, then open the pane (or just type, if the pane is already open).

**Via the pane directly:**
Click the paperclip icon at the top of the ACP pane → select a file from the picker. Use this when the note you want to discuss isn't the one currently open in the editor.

The attached note appears as a named context card at the top of the conversation. The co-PI reads its full title and body. It does not follow wikilinks to other notes — attach additional files explicitly if you need them in context.

## Reading responses

Two kinds of turn come back:

- **Conversation** — questions, observations, gentle pushback on the attached note. You are expected to reply. The co-PI will not produce a finished note: when you've arrived at a durable claim, write the claim note yourself (`Memoria: write claim note`).
- **Delegation receipts** — when you ask for work ("verify this draft", "bring in this paper"), the co-PI raises a card on the right lane and tells you so. Track it on the board (`hermes kanban list`, or the Board State dashboard); the result lands in your Inbox, not in the pane.

## Ending a session

Leave the pane open during a reading session — sustained questioning across the notes of one topic is its purpose. Press **Clear** at the top of the pane when you finish a paper or topic cluster, before switching to unrelated work. Long histories degrade response quality.

## Exporting a session

Sessions are captured automatically: with the shipped config, closing a chat exports the conversation as a markdown file to `notes/fleeting/chats/` (filenames start with `chat_`). You can also export mid-session via `Cmd/Ctrl+P` → **Agent Client: Export chat**.

Exports are fleeting-grade raw material, and the system processes them instead of letting them rot:

1. The plugin writes the transcript to `notes/fleeting/chats/` with no Memoria frontmatter.
2. Within 15 minutes the sweeps cron stamps it with valid fleeting frontmatter (`type: fleeting`, `lifecycle: proposed`, `origin: chat`). Already-stamped files are never touched.
3. The stamped export then appears in the fleeting dashboard (`system/dashboards/fleeting.base`) and is flagged by the stale-fleeting detector after a week — triage it like any other fleeting note: [Triage fleeting notes](../compile/triage-fleeting-notes.md).

Two folders to **never** point `exportSettings.defaultFolder` at:

- `inbox/` — reserved for agent-raised honesty cards (candidates, gaps, flags, alerts), not chat transcripts.
- `projects/` — reserved and empty until v0.1.2.

Auto-export fires on chat **close**, not on new chat (`autoExportOnCloseChat: true`, `autoExportOnNewChat: false`) — you get one transcript per finished session, no empty stubs.

## If the pane won't connect (Windows + WSL)

On Windows, Obsidian runs natively while hermes lives in WSL, so the ACP commands must resolve **through `wsl.exe`**. Two settings make that work (Settings → **Agent Client**):

- **WSL mode on.** `windowsWslMode: true` — the plugin then runs each agent as `wsl.exe … sh -c "<command> …"`. Without it, Obsidian tries to launch the WSL binary as a Windows process and can't find it.
- **Command = the WSL absolute path** to hermes, e.g. `/home/<you>/.local/bin/hermes` — **not** a Windows path and **not** the `{{HOME}}` placeholder. The quickest way to fill it is the **Auto-detect** button next to each agent (it runs `which hermes` inside WSL).

The installer (`scripts/install.sh`, run under WSL) seeds these automatically — it substitutes `{{HOME}}` with your WSL home and sets `windowsWslMode: true`. If you instead see a **"Command Not Found: `{{HOME}}/.local/bin/hermes`"** error, the substitution didn't run (an older installer, or a hand-copied `data.json.example`): set the path via **Auto-detect**, confirm WSL mode is on, then **fully restart Obsidian** so the plugin re-reads the config.

On native Linux (Obsidian and hermes on one filesystem) leave WSL mode **off** and point the command at the plain hermes path.

## Verify

- The picker shows one agent — **co-PI** — and the pane connects
- Opening the pane with a note active attaches it as a context card (auto-mention)
- Asking for lane work ("verify this draft") produces a card on the board, not prose-only
- Pressing **Clear** empties the pane and resets the session

## Related

- Discussing a paper end-to-end: [Discuss a paper](../compile/discuss-a-paper.md)
- Workspace layouts: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- Plugin settings and `customAgents` keys: [Obsidian plugins](../../reference/obsidian-plugins.md)
- Why one agent, not a picker of specialists: [The agent-client pane](../../explanation/obsidian/agent-client-picker.md)
