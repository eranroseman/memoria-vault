---
title: Load and remove the sample vault
parent: Setup
grand_parent: How-to guides
nav_order: 5
---

# Load and remove the sample vault

Load the sample vault to follow the [tutorials](../../tutorials/README.md), which are built around a small worked corpus instead of an empty vault. It is removable — archive it when you're done (below). To work straight from your own material instead, skip the tutorial arc and use the other how-to guides.

## Prerequisites

- Memoria is installed and open in Obsidian.
- QuickAdd is enabled, so `Memoria:` commands appear in `Cmd/Ctrl-P`.

## Load it

1. Open Obsidian in your Memoria vault.
2. Press `Cmd/Ctrl-P`.
3. Run **Memoria: load sample vault**.
4. Open the Library or Knowledge space.

The command copies the bundled `.memoria/samples/mediterranean-diet/` notes into live `catalog/` and `notes/` folders. It skips existing files, so it will not overwrite your notes.

## Remove it from active views

1. Press `Cmd/Ctrl-P`.
2. Run **Memoria: remove sample vault**.

The command archives live sample notes labeled `sample: true`. They stay on disk so wikilinks keep resolving, but active dashboards stop showing them.

## Related

- Sample vault contents: [The sample vault](../../reference/sample-vault.md)
- Command details: [Obsidian command palette](../../reference/obsidian-command-palette.md)
