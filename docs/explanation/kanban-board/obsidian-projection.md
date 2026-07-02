---
title: How the board surfaces
parent: Kanban board
grand_parent: Explanation
nav_order: 4
---

# How the board surfaces

Alpha.14 does not ship an Obsidian board projection. Operational state lives in
SQLite request tables, the journal, and generated attention/worklist views.

## What the PI sees

| Need | Surface |
| --- | --- |
| Current queued/running work | `memoria request list --workspace .` |
| Work that needs PI attention | `spaces/inbox.md` and attention commands |
| Integrity or drift findings | `memoria workspace check --workspace .` and `spaces/maintenance.md` |
| Durable project work | `knowledge/projects/` plus `memoria project ...` commands |

## Authority

The request database and journal are authoritative. Markdown space pages are
readable projections or navigation aids; editing a generated projection does not
change request state and is quarantined by scan/check behavior.

## Related

- System actions: [System actions](../../reference/system-actions.md)
- On-disk layout: [On-disk layout](../../reference/on-disk-layout.md)
