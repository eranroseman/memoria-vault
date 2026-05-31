---
topic: plugins
---

# obsidian-kanban — evaluated, does not integrate with the Hermes board

Obsidian Kanban renders a **single markdown file** (carrying `kanban-plugin: board` frontmatter) as a drag-and-drop Kanban view. It was evaluated for visualizing Memoria's board and **not adopted**, for a structural reason: the authoritative board is the **Hermes Kanban (`kanban.db`)**, and the [`board-state` dashboard](../../explanation/dashboards/board-state.md) renders it via **Dataview**, not this plugin. There is no Obsidian-Kanban-format markdown file for it to read.

Bridging the two would mean translating Hermes worker semantics into the plugin's data model — the `hermes-kanban` bridge listed among the [alternatives considered and rejected](../../explanation/kanban-board/README.md#alternatives-considered-not-adopted) (it works, but adds a translation layer between two state machines).

- **Use it only** for standalone markdown Kanban boards of your own, unrelated to the Hermes board.
- **For the Hermes board**, the right surfaces are the Hermes Workspace board view or the Dataview-backed [`board-state`](../../explanation/dashboards/board-state.md) dashboard.
