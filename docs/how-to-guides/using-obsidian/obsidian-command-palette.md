---
title: Command palette
parent: Using Obsidian
nav_order: 4
---

# Command palette

Drive Memoria's daily operations from `Cmd-P` (`Ctrl-P` on Windows) without leaving Obsidian. This guide covers the pre-wired commands and how to add the rest.

## Prerequisites

- Obsidian open with the vault
- QuickAdd ships bundled and enabled with the starter vault — no install needed (see [Set up Obsidian](../setup/set-up-obsidian.md))
- The Memoria command catalog open for reference: [Obsidian command palette](../../reference/obsidian-command-palette.md)

## Steps

**1. Open the palette and confirm the pre-wired commands are present.**

`Cmd-P` (or `Ctrl-P`) → type `Mem`. **Seven note-creation commands ship pre-wired** in the starter vault — each a QuickAdd _Template_ choice that instantiates one of the raw-note templates in `99-system/templates/`:

- `Memoria: capture fleeting` — fleeting note in `10-inbox/01-fleeting/`
- `Memoria: write claim note` — claim note in `30-synthesis/01-claims/`
- `Memoria: write MOC` — Map of Content in `30-synthesis/03-moc/`
- `Memoria: write draft` · `Memoria: scaffold canvas` · `Memoria: scaffold code note` · `Memoria: write project note` — workbench notes (you pick the `40-workbench/<project>/` subfolder)

Each stamps `created`/`updated` automatically and takes its title from a prompt (`capture fleeting` uses a timestamp instead). The **card-producing** agent commands are also wired as QuickAdd Macros → user scripts that `hermes kanban create` a card on the matching lane: `lint this note`, `new project`, `scope this project`, `frame this section`, and `verify this draft`. The remaining **conversational** commands (`ask about this note`, `find related notes`, …) run through the ACP pane today and are tracked as a build gap ([#203](https://github.com/eranroseman/memoria-vault/issues/203)). Add the ones you need per step 2.

**2. Add a QuickAdd entry for each agent command you use.**

Settings → QuickAdd → Add choice → name it exactly as it appears in the catalog (e.g., `Memoria: ask about this note`). Set the type and implementation per the catalog's Implementation column (Macro → user script → Hermes API).

Start with the agent commands you'll reach for most:

- `Memoria: ask about this note` — open the Socratic ACP pane on the current note
- `Memoria: lint this note` — run the Linter on the current note
- `Memoria: find related notes`
- `Memoria: new project` — scaffold a full project folder under `40-workbench/`

**3. Use the palette by type, not by scroll.**

`Cmd-P` → type `M` → the palette filters to `Memoria:` commands only. Type 1–3 more letters to narrow further. The filter is fast enough that you do not need physical hotkeys for most commands.

**4. Pin the highest-frequency commands to the Commander toolbar** (optional).

If you have the Commander plugin installed: Commander settings → toolbar → add your most-used commands as toolbar buttons. These give one-click access without opening the palette.

**5. Assign a physical hotkey to any command you invoke more than ten times a day** (optional).

Settings → Hotkeys → search for the command name → assign a key combination. Reserve physical hotkeys for the genuinely highest-frequency commands only. More than five hotkeys and the bindings become difficult to remember.

## Verify

- `Cmd-P` → `M` returns a filtered list of `Memoria:` commands
- `Memoria: capture fleeting` creates a new note in `10-inbox/01-fleeting/`
- `Memoria: write claim note` creates a titled claim note in `30-synthesis/01-claims/` from the template — Properties populated, clean body, no template scaffolding

## Related

- Full command catalog: [Obsidian command palette](../../reference/obsidian-command-palette.md)
- ACP pane and profile switching: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- QuickAdd plugin reference: [Obsidian plugins](../../reference/obsidian-plugins.md)
