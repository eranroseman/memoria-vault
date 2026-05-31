---
topic: obsidian-ui
---

# Command palette — Memoria's keyboard component

The single biggest UX move in Memoria is binding every common operation to an Obsidian command, then driving the system from `Cmd-P` (`Ctrl-P` on Windows/Linux) instead of clicking through menus. Within a few weeks of consistent use, muscle memory replaces every UI click.

This document covers how to invoke the palette, the naming convention, the session-persistent vs. transient modes, hotkey discipline, and the Commander bindings. For the full catalog of `Memoria:` commands — what each invokes and where it's implemented — see [the command catalog](../../reference/command-catalog.md).

## Naming convention

Every command begins with the prefix **`Memoria:`** so the human can type `Cmd-P → "M"` and filter the palette to Memoria-only commands. After three months of use, this becomes the primary input mode for the system — the human types Cmd-P, then 1–3 letters of the command name, then enter.

Two-tier discipline:

- The **core commands** (cataloged in [command-catalog.md](../../reference/command-catalog.md)) are the operational set. They cover capture, processing, interactive retrieval, projects, maintenance, and lens-based reading.
- Anything beyond these is a *human addition*, not part of the standard Memoria UX. Humans add their own custom commands freely — but the standard set is what every Memoria install ships with, what cross-machine portability assumes, and what the [Commander](../../explanation/obsidian-plugins/cmdr.md) recommendation set is drawn from.

## Session-persistent vs. transient modes

Two of the command categories differ in how long the ACP session they open lives — a distinction the human needs to hold in mind when using the palette:

- **Session-resident.** The Processing command `Memoria: ask about this note` opens an ACP pane whose conversation has its own lifecycle and can be resumed via `savedSessions[]`. The pane stays around; the human returns to it across exchanges.
- **Transient.** The Interactive retrieval commands (`Memoria: find related notes`, `Memoria: counter-outline this section`, `Memoria: similarity-check this claim`) open a fresh chat session, get one answer, and the session is meant to be dismissed. No session-persistent pane, no `savedSessions[]` entry. The "transient" close-after-response behavior is a Memoria discipline — the human dismisses the view manually.

The distinction is *output discipline*: transient commands produce chat output the human can copy or dismiss; the substantive card-based commands produce file artifacts tracked through the Kanban. See [command-catalog.md](../../reference/command-catalog.md) for which command falls in which category, and [`agent-client.md`](../../reference/plugins/agent-client.md) for the per-profile rationale behind session-resident versus transient ACP sessions.

## Setting up the bindings

The bindings are human-side configuration, not part of Memoria's shipped vault. The convention:

1. **Install [QuickAdd](../../reference/plugins/quickadd.md)**.
2. **For each command in the [catalog](../../reference/command-catalog.md), create a QuickAdd entry** with the same name (preserving the `Memoria:` prefix).
3. **Configure the underlying mechanism** per the Implementation column of the catalog — Templater templates for capture commands, Hermes API calls for Kanban interactions, agent-client commands for ACP invocations.
4. **Optionally pin the top 5 to Commander** for physical-button access. The recommended Commander set (see [`cmdr.md`](../../explanation/obsidian-plugins/cmdr.md)):
   - `Memoria: capture fleeting`
   - `Memoria: ask about this note`
   - `Memoria: new project`
   - `Memoria: lint this note`
   - `Memoria: approve all link suggestions`

The `Cmd-P → "M"` filter convention works from the moment the first three commands exist. The human builds the muscle memory as they go.

## Hotkey discipline

Reserve physical hotkeys (and Commander buttons) for the highest-frequency commands only — the recommended top five above. Everything else stays palette-driven: typed via `Cmd-P → "M"` plus 1–3 letters. Binding too many commands to hotkeys defeats the muscle-memory payoff, because the human can no longer predict which key does what. The palette filter is fast enough that the marginal command does not need a key of its own.

## Related

- [`command-catalog.md`](../../reference/command-catalog.md) — the full catalog of `Memoria:` commands and their implementations.
- [`quickadd.md`](../../reference/plugins/quickadd.md) — QuickAdd and Templater plugin details.
- [`cmdr.md`](../../explanation/obsidian-plugins/cmdr.md) — Commander plugin for putting top commands on buttons.
- [`obsidian-ui/README.md`](../../explanation/obsidian-ui/README.md) — the Obsidian UI components (dashboards, workspaces, callouts, status line, Agent Client pane) that this command palette sits alongside. The palette is itself one of those components — Obsidian's keyboard component; see the [glossary](../../reference/glossary.md#the-obsidian-ui-and-channels) for components vs. the CLI / Telegram channels.
- [`workflows/README.md`](../workflows/README.md) — workflows the commands trigger (workflow Discuss, Assess, Frame, Verify).
