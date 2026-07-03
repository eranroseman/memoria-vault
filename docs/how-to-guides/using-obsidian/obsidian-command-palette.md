---
title: Command palette
parent: Using Obsidian
grand_parent: How-to guides
nav_order: 4
---

# Command palette

Alpha.15 does not ship Obsidian command-palette shortcuts. Use the `memoria` CLI
for workspace actions.

## Common replacements

```bash
memoria work add --workspace . --doi <doi>
memoria work import --workspace . --format bibtex --file <file>
memoria request list --workspace .
memoria ask --workspace . --question "<question>"
memoria workspace check --workspace .
```

If you configure your own editor shortcut, make it call the same CLI command.
The shortcut must not write workspace files directly or maintain separate
operation state.

## Related

- Command boundary: [Obsidian command palette](../../reference/obsidian-command-palette.md)
- CLI reference: [Memoria CLI](../../reference/cli.md)
