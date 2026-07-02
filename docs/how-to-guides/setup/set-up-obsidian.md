---
title: Set up Obsidian
parent: Setup
grand_parent: How-to guides
nav_order: 3
---

# Set up Obsidian

Alpha.14 does not require Obsidian. Use this page only if you want Obsidian as a
plain Markdown editor for the workspace keep-set.

## Prerequisites

- Memoria installed with the standalone CLI runtime.
- Obsidian installed, if you choose to use it as an editor.

## Steps

1. Open the workspace folder in Obsidian.
2. Do not install or enable Memoria-specific plugins for alpha.14.
3. Use the terminal for Memoria actions:

```bash
memoria work capture --workspace . --doi <doi>
memoria work import --workspace . --format bibtex --file references.bib
memoria ask --workspace . --question "<question>"
memoria workspace check --workspace .
```

4. If you edit Markdown directly, run:

```bash
memoria workspace scan --workspace .
```

Direct edits are observed, checked, and promoted by the engine. Obsidian is not a
write-policy boundary, scheduler, model runner, or operation API.

## Verify

- `memoria doctor --workspace .` passes from the terminal.
- `memoria workspace check --workspace .` reports the same workspace you opened
  in Obsidian.
- No Memoria plugin setup is required.

## Related

- CLI command reference: [Memoria CLI](../../reference/cli.md)
- Obsidian plugin boundary: [Obsidian plugins](../../reference/obsidian-plugins.md)
- On-disk layout: [On-disk layout](../../reference/on-disk-layout.md)
