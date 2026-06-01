---
title: How to use the Memoria command palette
parent: Using Obsidian
---


# How to use the Memoria command palette

Drive Memoria's daily operations from `Cmd-P` (`Ctrl-P` on Windows) without leaving Obsidian. This guide covers setting up the bindings and using the palette efficiently.

## Prerequisites

- Obsidian open with the vault
- QuickAdd ships bundled and enabled with the starter vault — no install needed (see [set-up-obsidian.md](../setup/set-up-obsidian.md))
- The Memoria command catalog open for reference: [reference/obsidian-command-palette.md](../../reference/obsidian-command-palette.md)

## Steps

**1. Open the palette and confirm the Memoria commands are present.**

`Cmd-P` (or `Ctrl-P`) → type `Mem`. Two commands ship pre-wired in the starter vault: `Memoria: capture fleeting` and `Memoria: write claim note` (both backed by Templater templates). The remaining commands in the catalog are not yet wired — they require QuickAdd Macros and user scripts that POST to the Hermes API, which are tracked as a build gap (see [implementation-status.md](../../../project-files/operations/implementation-status.md)). Add the ones you need per step 2.

**2. Create a QuickAdd entry for each command you use.**

Settings → QuickAdd → Add choice → name it exactly as it appears in the catalog (e.g., `Memoria: capture fleeting`). Set the type and implementation per the catalog's Implementation column.

Repeat for each command you want. Start with the five most-used:

- `Memoria: capture fleeting`
- `Memoria: ask about this note`
- `Memoria: new project`
- `Memoria: lint this note`
- `Memoria: approve all link suggestions`

**3. Use the palette by type, not by scroll.**

`Cmd-P` → type `M` → the palette filters to `Memoria:` commands only. Type 1–3 more letters to narrow further. The filter is fast enough that you do not need physical hotkeys for most commands.

**4. Pin the five highest-frequency commands to the Commander toolbar** (optional).

If you have the Commander plugin installed: Commander settings → toolbar → add the five commands from step 2 as toolbar buttons. These give one-click access without opening the palette.

**5. Assign a physical hotkey to any command you invoke more than ten times a day** (optional).

Settings → Hotkeys → search for the command name → assign a key combination. Reserve physical hotkeys for the genuinely highest-frequency commands only. More than five hotkeys and the bindings become difficult to remember.

## Verify

- `Cmd-P` → `M` returns a filtered list of `Memoria:` commands
- `Memoria: capture fleeting` creates a new note in `10-inbox/01-fleeting/`
- `Memoria: ask about this note` opens the Socratic ACP pane with the current note in context

## Related

- Full command catalog: [reference/obsidian-command-palette.md](../../reference/obsidian-command-palette.md)
- ACP pane and profile switching: [obsidian-workspaces.md](../../reference/obsidian-workspaces.md)
- QuickAdd plugin reference: [obsidian-plugins.md](../../reference/obsidian-plugins.md)
