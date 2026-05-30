---
topic: obsidian-ui
---

# Visual style discipline

Plugin choice is only half the UX. The other half is restraint about how the vault *looks*. Discipline here matters more than people admit — a vault that becomes a cockpit of indicators is a vault that gets abandoned. The defaults below are deliberate; deviating from them is fine as long as the deviation is also deliberate.

## Typography and structure

- **One accent color for callouts.** Pick a single accent (Memoria's default is a muted blue) and use it for all three callout types: `[!brief]`, `[!suggestions]`, `[!verification]`. Differentiate by icon, not by color. Rainbow callouts train the eye to ignore them all.
- **Monospace for code blocks and identifiers; system font for prose.** Don't get clever with custom font picks — Obsidian's defaults are already legible. Configure once in Settings → Appearance, then leave it.
- **Heading hierarchy enforced.** The Memoria Linter (the structural one, not the Obsidian Linter) flags notes with no H1, H4 used without H3, or jumps of more than one heading level (planned M-detector; not yet implemented). This isn't pedantry — Dataview queries that filter on heading content break when the hierarchy is inconsistent.
- **No emoji in note titles.** They break filename portability across operating systems and look like noise after a year. Emoji in note *bodies* is fine; titles are filenames.

## UI chrome

- **Hide chrome by default.** Settings → Appearance → Hide tab bar, Hide sidebar until invoked. The vault should feel like writing, not like piloting a cockpit. The human reaches for chrome explicitly when needed (Cmd-\ for sidebar, Cmd-P for palette); the rest of the time the screen is the note.
- **Light theme for day, dark for night.** Set up the auto-switching by sunset/sunrise. The eye strain over hours of reading is real, and the cost of configuring this once is paid back the first week.
- **One Obsidian window per vault.** Don't run multiple Memoria vault windows side by side; the agent layer assumes a single active vault, and inline-callout interactions get confused when two windows try to update the same card.

## Workspace layout discipline

Workspace design rules (one mode per workspace, three is the working set, no topic-binding) are defined in [workspaces.md](../../reference/obsidian-ui/workspaces.md#design-rules-for-workspaces). The visual-style angle: those rules *are* visual restraint — a fourth workspace is visual proliferation by another name, and a topic-bound workspace conflates cognitive mode with project context. Trust the workspace rules; don't reintroduce the proliferation they prevent.

## The deeper rule

The architecture is invisible during normal use, legible when something goes wrong (see [the cross-component rules](README.md#cross-component-rules)). Visual-style discipline supports this: the vault looks like a writing environment most of the time, and indicators light up only when something specific demands attention. Three months in, the human's mouse hand barely moves and they've stopped consciously tracking which workspace they're in. That's the success condition.
