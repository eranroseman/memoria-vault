# Obsidian — the human surface

Obsidian is where the human meets Memoria. The agents run in Hermes and the board lives in `kanban.db`, but everything the human reads, writes, and decides happens here. This section explains *how that surface is designed* — not how to operate it (that's the [interface how-to guides](../../how-to-guides/interface/)) and not the exact settings (that's [reference/obsidian-plugins.md](../../reference/obsidian-plugins.md) and the `obsidian-*` reference pages).

One principle runs through every page below: **the architecture is invisible during normal use and legible when something goes wrong.** The vault should feel like a writing environment; the machinery surfaces only when it needs a decision.

## The surfaces

| Page | What it explains |
|---|---|
| [home.md](home.md) | The front door — why launch opens a plain note that *consumes* dashboards and computes nothing itself. |
| [the-status-line.md](the-status-line.md) | The one always-visible ambient indicator — why a glance-readable count, not a dashboard, answers "is everything fine?" |
| [callouts.md](callouts.md) | The inline callout types (`[!brief]`, `[!suggestions]`, `[!verification]`) agents write into notes, and what each means. |
| [agent-client-picker.md](agent-client-picker.md) | The ACP chat pane and its profile picker — why a conversational surface exists alongside the board, and why it clears on switch. |

## The discipline behind them

| Page | What it explains |
|---|---|
| [visual-discipline.md](visual-discipline.md) | The restraint that makes the above work — single-accent callouts, hidden chrome, three cognitive-mode workspaces, and why each default is deliberate. |

The **dashboards** are also an Obsidian surface, but they have their own section: [explanation/dashboards/](../dashboards/README.md).

---

## Related

- How to *use* these surfaces (operate the pane, navigate dashboards, drive the palette): [how-to-guides/interface/](../../how-to-guides/interface/)
- Plugin inventory and load-bearing settings: [reference/obsidian-plugins.md](../../reference/obsidian-plugins.md)
- Workspace, callout, and status-line reference pages: [reference/](../../reference/)
