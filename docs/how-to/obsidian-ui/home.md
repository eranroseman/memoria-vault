---
topic: obsidian-ui
---

> [!warning] Status: Accepted-Pending (ADR-25)
> `Home.md` does not yet exist at the vault root. Create it manually or wait for the post-clone setup step to be documented.

# Home — what it contains and how to set it up

`Home.md` (vault root) is the note Memoria opens on launch via [obsidian-homepage](../../reference/plugins/obsidian-homepage.md) ([ADR-25](../../project/decisions/25-homepage-front-door.md)). It is a **launchpad**, not a dashboard: it *surfaces* the dashboards rather than being one of the eleven shipped dashboards. Role split — [Daily Health](../../explanation/dashboards/daily-health.md) is the health glance; Home leads with it and adds navigation plus quick actions, so a session starts at one deliberate place.

For *why* Home is a thin, note-based consumer rather than a plugin UI — the design rules behind it — see [the Home design rationale](../../explanation/obsidian-ui/home.md).

## What Home contains

- **Lead glance:** the Daily Health red signals, linked (or a block-embedded) so opening Home *is* the morning health check.
- **Navigate:** links to the board and the knowledge dashboards ([open-questions](../../explanation/dashboards/open-questions.md), [contradictions](../../explanation/dashboards/contradictions.md), [reading-pipeline](../../explanation/dashboards/reading-pipeline.md)).
- **Quick actions:** command-palette entries (`Memoria: …`) for the common moves (new paper, find, discuss) — see [command-catalog.md](../../reference/command-catalog.md).
- **Recent activity:** a short Dataview list of recently-touched notes.

## Runtime scaffold

A thin starting point for the starter vault's `Home.md` (Dataview; trim or extend to taste). Adjust links to the vault's actual dashboard filenames:

````markdown
---
type: dashboard
---
# 🏠 Memoria — Home

**Health:** [[index|Daily Health]]  ·  **Board:** [[board-state]]

## Knowledge

[[open-questions]] · [[contradictions]] · [[reading-pipeline]]

## Quick actions

`Memoria: New paper note` · `Memoria: Find` · `Memoria: Discuss current note`

## Recently touched

```dataview
TABLE file.mtime AS "Updated"
FROM "30-synthesis" OR "20-sources"
SORT file.mtime DESC
LIMIT 8
```
````

The Daily Health dashboard ships at `00-meta/01-dashboards/index.md`; link it as `[[index|Daily Health]]` or block-embed a red-signals section if Daily Health exposes one.

## Related

- [Home design rationale](../../explanation/obsidian-ui/home.md) — why Home is thin, a pure consumer, a note not a plugin UI, and degrades gracefully.
- [obsidian-homepage](../../reference/plugins/obsidian-homepage.md) — the plugin that opens Home on launch.
