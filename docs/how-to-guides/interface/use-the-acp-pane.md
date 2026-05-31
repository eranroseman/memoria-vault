
# How to use the agent-client pane

Drive Memoria's conversational profiles from inside Obsidian without switching to a terminal. This guide covers opening the pane, selecting a profile, attaching context, reading responses, and ending a session cleanly.

## Prerequisites

- Obsidian open with the vault
- `agent-client` plugin installed and the Hermes gateway reachable ([set-up-hermes.md](../setup/set-up-hermes.md))
- The three workspace layouts configured ([reference/obsidian-workspaces.md](../../reference/obsidian-workspaces.md))

## Which profile to open

Four profiles appear in the ACP picker. Choose based on what you're about to do:

| Profile | Use it for | Session type |
| --- | --- | --- |
| **Socratic** | Thinking through a paper or claim in conversation | Persistent — stays open across notes |
| **Mapper** | Asking what's ready, thin, or missing in your corpus | Transient — one question, then done |
| **Writer** | Drafting a claim note or outline section | Transient — one task, then done |
| **Verifier** | Checking if a draft claim duplicates an existing note | Transient — one check, then done |

Start with Socratic by default. Switch to the others only when you have a specific one-shot task.

For the design rationale behind the picker — why three profiles are absent and why the labels name identities rather than actions — see [explanation/obsidian/agent-client-picker.md](../../explanation/obsidian/agent-client-picker.md).

## Opening the pane

**From the Reading & Processing workspace** (`Ctrl+2` on Windows, `Cmd+2` on Mac):
The ACP pane appears in the right column. If it's not visible, click the Hermes icon in the left ribbon, or `Cmd/Ctrl+P` → **Agent Client: Open pane**.

**From any other workspace:**
`Cmd/Ctrl+P` → **Agent Client: Open pane**.

## Switching profiles

**Keyboard bindings** (fastest):

| Binding | Profile |
| --- | --- |
| `Ctrl+Shift+1` | Socratic |
| `Ctrl+Shift+2` | Mapper |
| `Ctrl+Shift+3` | Writer |
| `Ctrl+Shift+4` | Verifier |

**From the picker:** click the profile name at the top of the ACP pane to open the dropdown and select a different profile.

Switch profiles between tasks, not mid-conversation. The conversation history clears on switch — this is intentional. A Mapper session's context should not bleed into a Socratic session.

## Attaching a note as context

**Via the command palette (standard path):**
Open the note you want to discuss. `Cmd/Ctrl+P` → **Memoria: ask about this note**. This opens the ACP pane, activates Socratic, and attaches the current note automatically.

**Via the pane directly:**
Click the paperclip icon at the top of the ACP pane → select a file from the picker. Use this when the note you want to discuss isn't the one currently open in the editor.

The attached note appears as a named context card at the top of the conversation. The profile reads its full title and body. It does not follow wikilinks to other notes — attach additional files explicitly if you need them in context.

## Reading responses

**Socratic** responses are conversational: questions, observations, gentle pushback. You are expected to reply. Socratic will not produce a finished note — when you've arrived at a durable claim, close the pane and write the claim note yourself.

The transient profiles return structured outputs:

| Profile | Output format | What to do with it |
| --- | --- | --- |
| Mapper | `[!corpus-map]` callout — dense clusters, thin topics, gaps | Read the gap list before framing a writing project |
| Writer | Draft prose or outline, written directly in the response | Copy the sections you want into your draft file |
| Verifier | `[!similarity-report]` — ranked similar notes with similarity scores | Check any note with score ≥ 0.85 before writing a new claim |

A similarity score ≥ 0.85 from Verifier means the claim likely already exists in your vault in different wording. Open the similar note and decide: are these the same claim? If yes, write into the existing note rather than creating a new one.

## Ending a session

**Transient profiles (Mapper, Writer, Verifier):** after reading the response, press **Clear** at the top of the pane to close the conversation. This frees the context window for the next task. Do not let transient sessions accumulate across multiple tasks.

**Socratic:** leave the pane open during a reading session — it's designed for sustained conversation across multiple notes on the same topic. Clear explicitly at the end of the session: when you're done with a paper or topic cluster, press **Clear** before switching to unrelated work.

Do not let Socratic accumulate more than one session's worth of conversation. Long histories degrade response quality. Clear when done.

## Verify

- `Ctrl+Shift+1` switches the pane to Socratic without reloading Obsidian
- **Memoria: ask about this note** opens the pane with the current note in the context card
- After a Mapper query, the `[!corpus-map]` callout appears in the response area
- Pressing **Clear** empties the pane and resets the session

## Related

- Profile picker design: [explanation/obsidian/agent-client-picker.md](../../explanation/obsidian/agent-client-picker.md)
- Workspace layouts and hotkeys: [reference/obsidian-workspaces.md](../../reference/obsidian-workspaces.md)
- Plugin settings and `customAgents` keys: [reference/plugins.md](../../reference/plugins.md)
- Discussing a paper end-to-end: [sources/discuss-a-paper.md](../sources/discuss-a-paper.md)
