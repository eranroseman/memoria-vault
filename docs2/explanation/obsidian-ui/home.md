# Home — the vault front door

`Home.md` at the vault root is the note Memoria opens on launch via the obsidian-homepage plugin. It is a **launchpad**, not a dashboard: it surfaces the dashboards rather than computing anything itself.

## What Home is and isn't

Home is the starting point for every session. It links to Daily Health, the board-state dashboard, quick-capture commands, and your research directions. It does not contain Dataview queries of its own — any query it shows is defined in a dashboard and embedded here. This distinction matters: if Home computed its own health queries, those queries would drift from the authoritative versions in the dedicated dashboards, creating two places that need to be kept in sync.

Home is a consumer, never a producer. If a question belongs in a dashboard, it lives in that dashboard. Home links it.

## Why a note, not a plugin

Home is a Markdown note rendered by Dataview — git-tracked, lintable, embeddable. A plugin-rendered start page would be opaque to git, outside the Linter's reach, and unembeddable by other notes. The Obsidian-homepage plugin simply opens this note on launch; it is a convenience, not a dependency. If the plugin isn't installed, `Home.md` is still an ordinary note the human can pin in the sidebar.

## Graceful degradation

When the vault is freshly cloned and the dashboards have no data yet, Home shows mostly empty states and navigation links. That's intentional — the dashboards degrade gracefully too. Home never breaks because it never does its own computation.

## Related

- [how-to-guides/obsidian/command-palette.md](../../how-to-guides/obsidian/command-palette.md) — invoking commands from Home
- [explanation/dashboards/daily-health.md](../dashboards/daily-health.md) — the primary dashboard Home surfaces
