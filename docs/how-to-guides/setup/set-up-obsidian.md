---
title: Set up Obsidian
parent: Setup
grand_parent: How-to guides
nav_order: 3
---

# Set up Obsidian

Obsidian is optional. New Memoria workspaces already include Memoria's Obsidian
plugin files and core Obsidian settings; use this page when you want to open the
workspace in Obsidian and enable the local adapter.

## Prerequisites

- Memoria installed with the standalone CLI runtime.
- Obsidian installed, if you choose to use it as an editor.

## Steps

1. Install Obsidian if it is not already installed.
2. Open the workspace folder in Obsidian.
3. Enable community plugins for this vault if Obsidian prompts for confirmation.
4. Open the Memoria plugin settings and enter the local HTTP server URL/token
   only when you want adapter actions or empirical event recording.
5. Use the terminal for Memoria actions:

```bash
memoria work add --workspace . --doi <doi>
memoria work import --workspace . --format bibtex --file bibliography.bib
memoria ask --workspace . --question "<question>"
memoria workspace check --workspace .
```

6. If you edit Markdown directly, run:

```bash
memoria workspace scan --workspace .
```

Direct edits are observed, checked, and promoted by the engine. Obsidian is not a
write-policy boundary, scheduler, or model runner.

If you created a workspace directly with `memoria init --no-obsidian`, rerun
`memoria doctor --repair --workspace .` to restore the default Obsidian profile
before following this page.

## Verify

- `memoria doctor --workspace .` passes from the terminal.
- `memoria workspace check --workspace .` reports the same workspace you opened
  in Obsidian.
- `.obsidian/plugins/memoria-obsidian/manifest.json` exists in the workspace.
- No extra community plugin is required.

## Related

- CLI command reference: [Memoria CLI](../../reference/commands-and-transports/cli.md)
- Optional proof adapter contract: [External integrations](../../reference/evidence-and-integrations/integrations.md#obsidian-proof-adapter)
- On-disk layout: [On-disk layout](../../reference/system/on-disk-layout.md)
