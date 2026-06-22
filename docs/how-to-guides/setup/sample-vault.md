---
title: Load and remove the sample vault
parent: Setup
nav_order: 4
---

# Load and remove the sample vault

Use the sample vault when you want the tutorials to start from a small worked corpus instead of an empty vault. It is optional; skip it if you want to start with your own source.

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

- Tutorial sample contents: [The sample vault](../../tutorials/sample-vault/)
- Command details: [Obsidian command palette](../../reference/obsidian-command-palette.md)
