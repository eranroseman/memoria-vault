---
title: Navigate Memoria surfaces
parent: Using Obsidian
grand_parent: How-to guides
nav_order: 5
---

# Navigate Memoria surfaces

Use Obsidian as a Markdown reader/editor if you like; use `memoria` for actions.

## Steps

**1. Open the right Markdown area for the question.**

- Need attention: open `inbox/`
- Reading sources: open `digests/` and `fulltexts/`
- Checked claims: open `notes/` and `hubs/`
- Project work: open `projects/<slug>/project.md`
- Workspace health: open `system/dashboards/`

**2. Run the matching CLI action.**

Use `memoria request list`, `memoria work add` or `memoria work import`,
`memoria ask`, `memoria project gaps`, and `memoria workspace check` from the
same workspace folder.

`_nav.md` links the same Markdown pages. It is a convenience file, not a runtime
control surface.

## Verify

- The editor is showing the same folder passed to `--workspace`.
- Direct edits are followed by `memoria workspace scan --workspace .`.

## Related

- CLI reference: [Memoria CLI](../../reference/cli.md)
- On-disk layout: [On-disk layout](../../reference/on-disk-layout.md)
