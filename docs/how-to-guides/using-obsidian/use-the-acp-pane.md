---
title: Agent-client pane
parent: Using Obsidian
nav_order: 3
---

# Agent-client pane

Drive Memoria's conversational profiles from inside Obsidian without switching to a terminal. This guide covers opening the pane, selecting a profile, attaching context, reading responses, and ending a session cleanly.

## Prerequisites

- Obsidian open with the vault
- `agent-client` plugin installed and the Hermes gateway reachable ([Set up Hermes](../setup/set-up-hermes.md))
- The three workspace layouts configured ([Obsidian workspaces](../../reference/obsidian-workspaces.md))

## Which profile to open

Four profiles appear in the ACP picker. Choose based on what you're about to do:

| Profile      | Use it for                                            | Pattern                            |
| ------------ | ----------------------------------------------------- | ---------------------------------- |
| **Socratic** | Thinking through a paper or claim in conversation     | Sustained — keep open across notes |
| **Mapper**   | Asking what's ready, thin, or missing in your corpus  | One-shot — clear after each task   |
| **Writer**   | Drafting a claim note or outline section              | One-shot — clear after each task   |
| **Verifier** | Checking if a draft claim duplicates an existing note | One-shot — clear after each task   |

Start with Socratic by default. Switch to the others only when you have a specific one-shot task.

For the design rationale behind the picker — why three profiles are absent and why the labels name identities rather than actions — see [The agent-client pane](../../explanation/obsidian/agent-client-picker.md).

## Opening the pane

**From the Reading & Processing workspace** (`Ctrl+2` on Windows, `Cmd+2` on Mac):
The ACP pane appears in the right column. If it's not visible, click the Hermes icon in the left ribbon, or `Cmd/Ctrl+P` → **Agent Client: Open chat view**.

**From any other workspace:**
`Cmd/Ctrl+P` → **Agent Client: Open chat view**, or click the Hermes ribbon icon.

## Switching profiles

Click the profile name at the top of the ACP pane to open the dropdown, then select a different profile.

> The pane has no profile-switch keyboard shortcut. Obsidian doesn't ship one, and the plugin exposes no per-profile command to bind in Settings → Hotkeys — switch from the picker.

Switch profiles between tasks, not mid-conversation. The conversation history clears on switch — this is intentional. A Mapper session's context should not bleed into a Socratic session.

## Attaching a note as context

**Auto-mention (default).** With `autoMentionActiveNote` on, the note open in your editor is attached automatically when you open the pane or send a message — it arrives as a context card with no extra step. Open the note you want to discuss first, then open the pane (or just type, if the pane is already open).

**Via the pane directly:**
Click the paperclip icon at the top of the ACP pane → select a file from the picker. Use this when the note you want to discuss isn't the one currently open in the editor.

The attached note appears as a named context card at the top of the conversation. The profile reads its full title and body. It does not follow wikilinks to other notes — attach additional files explicitly if you need them in context.

## Reading responses

**Socratic** responses are conversational: questions, observations, gentle pushback. You are expected to reply. Socratic will not produce a finished note — when you've arrived at a durable claim, close the pane and write the claim note yourself.

The transient profiles return structured outputs:

| Profile  | Output format                                                        | What to do with it                                         |
| -------- | -------------------------------------------------------------------- | ---------------------------------------------------------- |
| Mapper   | `[!corpus-map]` callout — dense clusters, thin topics, gaps          | Read the gap list before framing a writing project         |
| Writer   | Draft prose or outline, written directly in the response             | Copy the sections you want into your draft file            |
| Verifier | `[!similarity-report]` — ranked similar notes with similarity scores | Check any note with score ≥ 0.8 before writing a new claim |

A similarity score ≥ 0.8 from Verifier means the claim likely already exists in your vault in different wording. Open the similar note and decide: are these the same claim? If yes, write into the existing note rather than creating a new one.

## Ending a session

**Transient profiles (Mapper, Writer, Verifier):** after reading the response, press **Clear** at the top of the pane to close the conversation. This frees the context window for the next task. Do not let transient sessions accumulate across multiple tasks.

**Socratic:** leave the pane open during a reading session — it's designed for sustained conversation across multiple notes on the same topic. Clear explicitly at the end of the session: when you're done with a paper or topic cluster, press **Clear** before switching to unrelated work.

Do not let Socratic accumulate more than one session's worth of conversation. Long histories degrade response quality. Clear when done.

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

- Selecting **Socratic** from the picker switches the pane without reloading Obsidian
- Opening the pane with a note active attaches it as a context card (auto-mention)
- After a Mapper query, the `[!corpus-map]` callout appears in the response area
- Pressing **Clear** empties the pane and resets the session

## Related

- Discussing a paper end-to-end: [Discuss a paper](../compile/discuss-a-paper.md)
- Workspace layouts and hotkeys: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- Plugin settings and `customAgents` keys: [Obsidian plugins](../../reference/obsidian-plugins.md)
- Profile picker design: [The agent-client pane](../../explanation/obsidian/agent-client-picker.md)
