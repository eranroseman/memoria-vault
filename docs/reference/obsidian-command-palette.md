---
title: Obsidian command palette
parent: Agents and control
grand_parent: Reference
---

# Obsidian command palette

Alpha.14 has no required Obsidian command-palette surface. The product surface is
the `memoria` CLI, and optional editor adapters must call the CLI/engine instead
of owning workflow state or write policy.

## CLI replacements

| Former editor action | Alpha.14 command |
| --- | --- |
| Capture a source | `memoria work capture --workspace . --doi <doi>` |
| Import bibliography rows | `memoria work import --workspace . --format bibtex --file <file>` |
| Ask a grounded question | `memoria ask --workspace . --question "<question>"` |
| Resolve or retry queued work | `memoria request answer`, `memoria request retry`, `memoria request resume` |
| Check workspace integrity | `memoria workspace check --workspace .` |

## Adapter rule

An optional editor palette may expose shortcuts later, but each shortcut is only
a thin caller of the same CLI/engine command. It must not introduce a second
operation manifest, direct write path, policy gate, or unchecked state store.

## Related

- CLI command reference: [Memoria CLI](cli.md)
- Current Concept types: [Document types](document-types.md)
