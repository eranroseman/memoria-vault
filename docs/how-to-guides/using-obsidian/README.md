---
title: Using Obsidian
parent: How-to guides
nav_order: 2
permalink: /how-to-guides/using-obsidian/
---

# Using Obsidian

Use Obsidian as a Markdown reader/editor if you like. Actions still run through
the `memoria` CLI; Obsidian is not the required UI, scheduler, model runner,
operation API, or write-policy boundary.

## Open the launch files

1. Open `home.md`.
2. Open `_nav.md` for links to Inbox, Library, Knowledge, Project, and
   Maintenance.
3. Keep `steering.md` current when project direction changes.

## Pick the right surface

| Need | Open | Run |
| --- | --- | --- |
| Attention | `inbox/` | `memoria request list` or `memoria attention resolve` |
| Reading sources | `digests/` and `fulltexts/` | `memoria work add`, `memoria work import`, or `memoria work digest` |
| Checked claims | `notes/` and `hubs/` | `memoria ask` or `memoria link` |
| Project work | `projects/<slug>/project.md` | `memoria project gaps`, `memoria project compose`, or `memoria project verify` |
| Workspace health | `system/dashboards/` | `memoria workspace check` |

`_nav.md` links the same Markdown areas. It is a convenience file, not a
runtime control surface.

## Run actions from the same workspace

Use terminal commands from the folder Obsidian has open:

```bash
memoria work add --workspace . --doi <doi>
memoria ask --workspace . --question "<question>"
memoria workspace check --workspace .
```

## Verify

- The editor shows the same folder passed to `--workspace`.
- Direct edits are followed by `memoria workspace scan --workspace .`.
- No Obsidian startup macro or plugin action is required.

## Related

- Workspace layout: [On-disk layout](../../reference/system/on-disk-layout.md)
- CLI reference: [Memoria CLI](../../reference/commands-and-transports/cli.md)
