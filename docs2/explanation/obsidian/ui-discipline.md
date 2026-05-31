# Visual style discipline

Plugin choice is only half the UX. The other half is restraint about how the vault *looks*. A vault that becomes a cockpit of indicators is a vault that gets abandoned. The defaults below are deliberate; deviating from them is fine as long as the deviation is also deliberate.

## Typography

- **One accent color for callouts.** Use a single accent for all three callout types (`[!brief]`, `[!suggestions]`, `[!verification]`). Differentiate by icon, not by color. Rainbow callouts train the eye to ignore them all.
- **Monospace for code blocks and identifiers; system font for prose.** Obsidian's defaults are already legible — configure once in Settings → Appearance and leave it.
- **Heading hierarchy enforced.** The Linter flags notes with no H1, with H4 used without H3, or with jumps of more than one level. This matters because Dataview queries that filter on heading content break when the hierarchy is inconsistent.
- **No emoji in note titles.** They break filename portability across operating systems. Emoji in note *bodies* is fine; titles are filenames.

## Chrome

- **Hide chrome by default.** Settings → Appearance → hide the tab bar and sidebar until explicitly invoked. The vault should feel like writing, not like piloting a cockpit. The sidebar opens with `Cmd+\`; the command palette with `Cmd+P`.
- **One Obsidian window per vault.** The agent layer assumes a single active vault; multiple windows trying to update the same card produce race conditions.

## Workspaces

Three workspaces — Human, Reading, Drafting — map to cognitive modes, not to projects. The workspace discipline is defined in detail in [reference/obsidian/workspaces.md](../../reference/obsidian/workspaces.md). The visual-style angle: a fourth workspace is visual proliferation by another name. Trust the workspace rules.

## The underlying principle

The architecture is invisible during normal use, legible when something goes wrong. Visual-style discipline supports this: the vault looks like a writing environment most of the time, and indicators surface only when something specific demands attention. Three months in, the mouse hand barely moves and there's no conscious tracking of which workspace is active. That's the success condition.
