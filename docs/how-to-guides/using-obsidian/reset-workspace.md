---
title: Reset workspace
parent: Using Obsidian
grand_parent: How-to guides
nav_order: 2
---

# Reset workspace

Alpha.14 ships no saved Obsidian workspace. If you use Obsidian, open the
workspace folder and navigate with ordinary Markdown links.

## Steps

1. Open `home.md` for the welcome note.
2. Open `_nav.md` for the space links.
3. Open the relevant space:
   - `spaces/inbox.md`
   - `spaces/library.md`
   - `spaces/knowledge.md`
   - `spaces/project.md`
   - `spaces/maintenance.md`
4. Run Memoria actions from the terminal.

## Verify

- `memoria doctor --workspace . bundle` passes.
- Direct Markdown edits are followed by `memoria workspace scan --workspace .`.

## Related

- Workspace reference: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- Opening surfaces: [Navigate Memoria surfaces](navigate-memoria-surfaces.md)
