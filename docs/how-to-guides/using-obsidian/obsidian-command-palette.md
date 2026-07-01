---
title: Command palette
parent: Using Obsidian
grand_parent: How-to guides
nav_order: 4
---

# Command palette

The command palette is Obsidian's keyboard launcher. In alpha.11, Memoria keeps
the `Memoria:` palette deliberately small: PI conveniences stay in QuickAdd,
and worker actions run from the `memoria` CLI.

Open it with `Cmd-P` (`Ctrl-P` on Windows), then type `Memoria:`.

## Steps

**1. Confirm the alpha.11 commands are present.**

The visible commands are:

| Command | Use it for |
| --- | --- |
| `Memoria: capture note` | Write one unchecked PI-owned note into `knowledge/notes/`. |
| `Memoria: open Inbox` | Open `spaces/inbox.md`. |
| `Memoria: record exploration trace` | Record a rejected direction beside a map/gap report. |
| `Memoria: resolve inbox card` | Mark the active attention projection resolved. |
| `Memoria: dismiss inbox card` | Dismiss the active attention projection. |

The startup macro `Memoria: restore shell on startup` is hidden from the
palette.

**2. Use the CLI for worker jobs.**

Source processing, integrity checks, rollback, and attention acknowledgement
are worker jobs. Use `memoria work`, `memoria operation`, `memoria workspace`,
and `memoria attention` instead of looking for palette commands.

**3. Use the rail for navigation.**

Switch spaces from the left navigation rail. The palette is for actions, not
the primary way to move between Library, Knowledge, Project, Inbox, and
Maintenance.

## Verify

- `Cmd-P` -> `Memoria:` shows the five visible commands above.
- The left ribbon exposes capture/open-inbox/resolve controls.
- Source and integrity jobs are available from the `memoria` CLI, not QuickAdd.

## Related

- Exact command catalog: [Obsidian command palette](../../reference/obsidian-command-palette.md)
- Operational Inspector: [Obsidian plugin settings](../../reference/obsidian-plugin-settings.md)
- Conversational route: [Agent Client pane](use-the-agent-client-pane.md)
