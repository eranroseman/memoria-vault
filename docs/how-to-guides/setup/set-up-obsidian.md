---
title: Set up Obsidian
parent: Setup
grand_parent: How-to guides
nav_order: 3
---

# Set up Obsidian

Obsidian is optional. Use this page if you want Obsidian as a
plain Markdown editor for the workspace keep-set.

## Prerequisites

- Memoria installed with the standalone CLI runtime.
- Obsidian installed, if you choose to use it as an editor.

## Steps

1. Open the workspace folder in Obsidian.
2. Do not install a plugin for ordinary Markdown editing. The optional
   `packages/memoria-obsidian/` proof adapter exists for local HTTP control and
   empirical-event capture, but it is not installed by bootstrap.
3. Use the terminal for Memoria actions:

```bash
memoria work add --workspace . --doi <doi>
memoria work import --workspace . --format bibtex --file bibliography.bib
memoria ask --workspace . --question "<question>"
memoria workspace check --workspace .
```

4. If you edit Markdown directly, run:

```bash
memoria workspace scan --workspace .
```

Direct edits are observed, checked, and promoted by the engine. Obsidian is not a
write-policy boundary, scheduler, or model runner.

## Verify

- `memoria doctor --workspace .` passes from the terminal.
- `memoria workspace check --workspace .` reports the same workspace you opened
  in Obsidian.
- No Memoria plugin setup is required for this plain-editor path.

## Related

- CLI command reference: [Memoria CLI](../../reference/commands-and-transports/cli.md)
- Optional proof adapter contract: [External integrations](../../reference/evidence-and-integrations/integrations.md#obsidian-proof-adapter)
- On-disk layout: [On-disk layout](../../reference/system/on-disk-layout.md)
