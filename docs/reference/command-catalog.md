---
topic: obsidian-ui
---

# Command catalog — the standard `Memoria:` commands

This is the authoritative catalog of Memoria commands: what each invokes and where it's implemented. It's the reference the human consults when configuring [QuickAdd](plugins/quickadd.md) (which registers the commands) and [Commander](../explanation/obsidian-plugins/cmdr.md) (which puts the top five on physical buttons).

For how to invoke the palette, the `Cmd-P → Memoria:` pattern, the naming convention, session-persistent vs. transient modes, hotkey discipline, and Commander bindings, see [the command palette how-to](../how-to/obsidian-ui/command-palette.md).

## The standard commands

### Capture (3 commands)

| Command | What it does | Implementation |
| --- | --- | --- |
| `Memoria: capture fleeting` | Instant note to `10-inbox/01-fleeting/` with timestamp. No friction; the human presses the hotkey, types one sentence, presses enter, and the thought is captured. | QuickAdd → Templater (fleeting-note template) |
| `Memoria: capture source from URL` | Prompts for a URL, creates `intake:source` card in the Librarian lane's queue. Librarian picks it up within 60 seconds and starts the ingest pipeline. | QuickAdd → POST to Hermes API (`hermes kanban create`) |
| `Memoria: capture from Zotero selection` | Reads the current Zotero selection (via the Zotero local API), creates an `intake:source` card with the citekey pre-populated. Useful when the human is mid-reading in Zotero and wants the paper in the vault. | QuickAdd → reads Zotero API → POST to Hermes API |

### Processing (3 commands)

| Command | What it does | Implementation |
| --- | --- | --- |
| `Memoria: ask about this note` | Opens the [ACP pane](plugins/agent-client.md) in **Ask** mode (Socratic profile), passing the active note path as context. The conversation never modifies the note (Socratic's lane policy is `policy.allow.write: []`). **Session-resident pane** — the conversation has its own lifecycle and can be resumed via `savedSessions[]`. | QuickAdd → `open-chat-view` (uses `defaultAgentId: memoria-socratic`; active note auto-attached via `autoMentionActiveNote: true`) |
| `Memoria: discuss this fleeting note` | Moves the current fleeting note to the discuss queue: creates a `discuss` card targeting the human, and opens the Socratic ACP pane. Combines the previous two commands for the fleeting → claim transition. | QuickAdd composing two prior commands |
| `Memoria: write claim note` | Opens a new note with the claim-note template, prompts for the source citekey, and pre-populates the frontmatter. Lands in `30-synthesis/01-claims/` with `maturity: seedling`. | QuickAdd → Templater (claim-note template) |

### Interactive retrieval (3 commands — transient ACP)

These commands invoke a profile via a *transient* ACP session: the agent-client plugin opens a fresh chat session, the agent returns results, the session closes. No session-persistent pane, no `savedSessions[]` entry. They're for "ask one specific question and get an answer" — distinct from the session-persistent Socratic processing chat above (*persistent* here means the chat session outlives one exchange — unrelated to the persistent dashboards component), and distinct from the substantive card-based work in the Project section below (which produces durable artifacts via the Kanban).

One transient command per ACP-suitable profile in the picker (Mapper / Writer / Verifier), each pointed at the kind of question the profile is shaped to answer.

| Command | What it does | Implementation |
| --- | --- | --- |
| `Memoria: find related notes` | Invokes Mapper in transient ACP mode with the current note's content as the query. Returns a ranked list of related notes (top 5–10 by embedding similarity + shared citations + topic overlap) directly in the ACP chat. No file artifact written; no card created. The human copies citekeys they want or dismisses the session. | QuickAdd Macro → `open-new-chat-view` → `switch-agent-to-memoria-mapper` (active note auto-attached). The "transient" close-after-response behavior is a Memoria discipline — the human dismisses the view manually. |
| `Memoria: counter-outline this section` | Invokes Writer with the `counter-outline` skill loaded in transient ACP mode. Returns 2–3 competing outlines for the current section directly in chat — no file artifact, no project-scratch write. Useful for quick brainstorming before committing to a framing direction. For the substantive *committed* counter-outline (which writes to `40-workbench/<project>/02-framing/`), use `Memoria: frame this section` in the Project section below. | QuickAdd Macro → `open-new-chat-view` → `switch-agent-to-memoria-writer` (active selection auto-attached). The first message — pre-filled by the macro template — invokes the `counter-outline` skill via Hermes slash command. Human closes the view after the response. |
| `Memoria: similarity-check this claim` | Invokes Verifier in transient ACP mode with the current selection (or active note's body if no selection) as the query. Returns the top 3 most-similar existing claim-notes by cosine similarity over the embedding index, with the similarity score per result. No card created; no `near-duplicate-candidate` flag written. Useful before filing a new claim note to check for duplicates; if the human decides to file anyway, the card-time `similarity-check` runs separately and produces the audit-trail entry. See [profiles/verifier.md `similarity-check`](profile-commands.md) for the substantive card-based version. | QuickAdd Macro → `open-new-chat-view` → `switch-agent-to-memoria-verifier` (active selection or note auto-attached). The first message — pre-filled by the macro template — requests top-N similars via Hermes slash command. Human closes the view after the response. |

See [`agent-client.md`](plugins/agent-client.md) for the per-profile rationale behind which profiles get session-resident versus transient ACP sessions. **agent-client.md is the authoritative source for the ACP command IDs** (`open-chat-view`, `open-new-chat-view`, `switch-agent-to-*`) and the session-policy semantics; the Implementation columns here only reference them.

**The transient commands don't replace their card-based counterparts.** Each profile has both entry points:

| Profile | Transient ACP (this section) | Substantive card-based |
| --- | --- | --- |
| Mapper | `Memoria: find related notes` — quick query, no artifact | `Memoria: scope this project` — produces `corpus-map.md`, Kanban-tracked |
| Writer | `Memoria: counter-outline this section` — quick brainstorm, no artifact | `Memoria: frame this section` — produces outlines in `40-workbench/<project>/02-framing/`, Kanban-tracked |
| Verifier | `Memoria: similarity-check this claim` — quick lookup, no audit entry | (filing-time `similarity-check` fires automatically when a new claim-note is filed; produces the audit-trail entry and the `near-duplicate-candidate` flag if applicable) |

The distinction is *output discipline*: transient commands produce chat output the human can copy or dismiss; substantive commands produce file artifacts tracked through the Kanban with audit trail.

### Project (4 commands)

| Command | What it does | Implementation |
| --- | --- | --- |
| `Memoria: new project` | Creates `40-workbench/<name>/` with `brief.md` from the project template, then opens a `scope` card on the Mapper lane queue. The human fills the brief; Mapper picks up the card and produces the corpus map. | QuickAdd → Templater (project-brief template) → POST to Hermes API |
| `Memoria: scope this project` | Manually triggers Mapper's `scope-project` skill on the current project folder. Produces `corpus-map.md` as a *file artifact* tracked as a card on the Kanban. For quick "what does my corpus say about X" queries without file commitment, use `Memoria: find related notes` (transient ACP) in the Interactive retrieval section above. | QuickAdd → POST to Hermes API (lane: mapping, task: scope-project, payload: project path) |
| `Memoria: frame this section` | Invokes Writer with the `counter-outline` skill loaded on the current project. Produces 2–3 competing outlines as *file artifacts* in `40-workbench/<project>/02-framing/`, tracked as a card on the Kanban. For quick brainstorming without file commitment, use `Memoria: counter-outline this section` (transient ACP) in the Interactive retrieval section above. | QuickAdd → POST to Hermes API (lane: writer, skill: counter-outline) |
| `Memoria: verify this draft` | Manually triggers Verifier's `cite-check` on the current draft. Normally Verifier fires automatically on git commit; this command is for the case where the human wants verification on uncommitted work. | QuickAdd → POST to Hermes API (lane: verify, task: cite-check, payload: draft path) |

### Maintenance (3 commands)

| Command | What it does | Implementation |
| --- | --- | --- |
| `Memoria: approve all link suggestions` | Bulk-approves every link-suggestion card awaiting review (`review_status: requested`). The human should glance through the [`weekly-review`](../explanation/dashboards/weekly-review.md) first; this is the "if they all look right" shortcut. | QuickAdd → POST to Hermes API (bulk approve filtered cards) |
| `Memoria: lint this note` | Runs the Linter (dry-run) on the current note, displays the report inline. The Linter is otherwise scheduled (see [`roadmap/README.md` Standard cron tasks](../project/roadmap/standard-cron-tasks.md)); this is the manual on-demand check. | QuickAdd → POST to Hermes API (lane: linter, task: lint, payload: note path) |
| `Memoria: show lane status` | Opens [Daily Health](../explanation/dashboards/daily-health.md) in the right sidebar. Useful when the human wants to glance at lane health mid-task without leaving their current note. | QuickAdd → Workspace pane manipulation |

### Lens-based reading (parameterized; 4 examples)

Each lens is its own command. The commands invoke Socratic with the named `lens-reading` parameter. Adding a new lens means adding one more command — the parameter is the lens skill's slug.

| Command | Lens |
| --- | --- |
| `Memoria: read through Mamykina lens` | `mamykina-sensemaking` |
| `Memoria: read through Veinot equity lens` | `veinot-informational-justice` |
| `Memoria: read through Design Justice lens` | `design-justice-costanza-chock` |
| `Memoria: read through JITAI lens` | `jitai-receptivity-timing` |

Implementation pattern (same for all): QuickAdd → `open-chat-view` (defaultAgentId is already `memoria-socratic`). The first message — pre-filled by the macro template — invokes the lens-reading skill with the lens's slug via Hermes slash command (e.g., `/lens mamykina-sensemaking`).

**Why each lens is its own command rather than one parameterized command.** Memoria's discipline says lens-based reading is *deliberately constrained* — the human picks a specific lens at the start of the session and stays in it, rather than switching mid-conversation. One command per lens makes the choice explicit before the conversation begins. A single parameterized command would invite mid-conversation lens-switching, which muddies whose questions are being asked.

## What's deliberately NOT in this catalog

- **Card state management.** Approving, denying, rejecting individual cards happens through inline callout buttons (see [`obsidian-ui/callouts.md`](../explanation/obsidian-ui/callouts.md)) or through the Kanban directly. There's no `Memoria: approve this card` command because card state changes need card context the palette doesn't provide. (Card buttons live in the [`obsidian-ui/callouts.md`](../explanation/obsidian-ui/callouts.md) callouts.)
- **Profile administration.** Reloading a profile, editing a lane-override, editing a profile source in `.memoria/profiles/memoria-<name>/` and redeploying with `install.ps1` — these are CLI operations, not palette operations. The palette is for *daily ops*; profile config is a *deployment concern*.
- **Search and retrieval (search-engine-style).** The vault's native search, Dataview queries, and `qmd` search are richer than any palette command could be. Memoria doesn't try to substitute its own search. The Interactive retrieval commands above are a different category — *conversational* retrieval where the human asks a profile a question and gets a curated response, not full-text / vector / property search that returns ranked results from an index.
- **Composing custom workflows.** Humans add their own commands for their own workflows; this catalog is the *standard Memoria set*, not an exhaustive catalog of human additions.

## Related

- [`command-palette.md`](../how-to/obsidian-ui/command-palette.md) — how to invoke the palette, the naming convention, modes, and Commander bindings.
- [`quickadd.md`](plugins/quickadd.md) — QuickAdd and Templater plugin details.
- [`cmdr.md`](../explanation/obsidian-plugins/cmdr.md) — Commander plugin for putting top commands on buttons.
- [`obsidian-ui/README.md`](../explanation/obsidian-ui/README.md) — the Obsidian UI components (dashboards, workspaces, callouts, status line, Agent Client pane) that this command palette sits alongside. The palette is itself one of those components — Obsidian's keyboard component; see the [glossary](glossary.md#the-obsidian-ui-and-channels) for components vs. the CLI / Telegram channels.
- [`workflows/README.md`](../how-to/workflows/README.md) — workflows the commands trigger (workflow Discuss, Assess, Frame, Verify).
