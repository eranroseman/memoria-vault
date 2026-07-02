---
title: Navigate Memoria surfaces
parent: Using Obsidian
grand_parent: How-to guides
nav_order: 5
---

# Navigate Memoria surfaces

Use Obsidian as a Markdown reader/editor if you like; use `memoria` for actions.

| Situation | Open | Run |
| --- | --- | --- |
| What needs attention? | `spaces/inbox.md` | `memoria request list --workspace .` |
| What should I read next? | `spaces/library.md` | `memoria work capture` or `memoria work import` |
| What does the checked corpus say? | `spaces/knowledge.md` | `memoria ask --workspace . --question "<question>"` |
| What gaps remain? | `spaces/project.md` | `memoria project gaps project-alpha --workspace .` |
| Is the workspace healthy? | `spaces/maintenance.md` | `memoria workspace check --workspace .` |

`_nav.md` links the same Markdown pages. It is a convenience file, not a runtime
control surface.

## Verify

- The editor is showing the same folder passed to `--workspace`.
- Direct edits are followed by `memoria workspace scan --workspace .`.

## Related

- CLI reference: [Memoria CLI](../../reference/cli.md)
- On-disk layout: [On-disk layout](../../reference/on-disk-layout.md)
