---
title: Operate
parent: How-to guides
nav_order: 7
has_children: true
permalink: /how-to-guides/operate/
---

# Operate

Terminal-side system upkeep — operational checks and maintenance tasks run from
the command line or an operator-managed scheduler.

| Guide | What it covers |
| --- | --- |
| [Run the Linter](run-the-linter.md) | On-demand or scheduled structural health check |
| [Run a retraction sweep](run-a-retraction-sweep.md) | Check ingested papers against retraction registries; update affected claims |
| [Rebuild the search index](rebuild-the-search-index.md) | Refresh the checked-only search input tree and BM25 index |
| [Run the vault eval](run-the-vault-eval.md) | Dispatch and score workspace-authored eval fixtures on demand |
| [Inspect session logs](inspect-session-logs.md) | Read the audit and per-request logs ad hoc — filter by request, actor, date, or decision |
| [Back up and restore the workspace](back-up-and-restore-the-workspace.md) | Back up the SQLite catalog, blobs, and journal Git doesn't track, and restore or recover them |

Several of these guides call the Linter's Python module directly rather than
through `memoria`. That entry point takes **`--vault`**, unlike the `memoria`
CLI's own **`--workspace`** flag — both name the same directory; the flag name
just differs by entry point.
