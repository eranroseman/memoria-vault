---
title: Vault launch screen
parent: Using Obsidian
grand_parent: How-to guides
nav_order: 1
---

# Vault launch screen

`home.md` is the plain Markdown welcome note in a Memoria workspace. It is useful
in Obsidian, VS Code, terminal editors, or any file browser.

## Steps

1. Open `home.md`.
2. Open `_nav.md` for links to Inbox, Library, Knowledge, Project, and
   Maintenance.
3. Run actions from the terminal, for example:

```bash
memoria work capture --workspace . --doi <doi>
memoria ask --workspace . --question "<question>"
memoria workspace check --workspace .
```

4. Keep `steering.md` current when project direction changes.

## Verify

- The Markdown files open in your editor.
- CLI commands run against the same workspace path.
- No Obsidian startup macro or plugin action is required.

## Related

- Workspace layout: [On-disk layout](../../reference/on-disk-layout.md)
- CLI reference: [Memoria CLI](../../reference/cli.md)
