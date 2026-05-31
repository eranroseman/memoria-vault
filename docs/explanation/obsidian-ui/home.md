---
topic: obsidian-ui
---

> [!note] Status: Shipped (ADR-25)
> `Home.md` ships at the vault root. The obsidian-homepage auto-open wiring is a post-clone setup step — see [the Home how-to](../../how-to/obsidian-ui/home.md).

# Home — why a thin, note-based front door

`Home.md` (vault root) is the note Memoria opens on launch via [obsidian-homepage](../../reference/plugins/obsidian-homepage.md) ([ADR-25](../../project/decisions/25-homepage-front-door.md)). It is a **launchpad**, not a dashboard: it *surfaces* the dashboards rather than being one of the eleven shipped dashboards. Role split — [Daily Health](../dashboards/daily-health.md) is the health glance; Home leads with it and adds navigation plus quick actions, so a session starts at one deliberate place.

This document is the rationale for Home's shape. For what Home actually contains and the runtime scaffold / setup steps, see [the Home how-to](../../how-to/obsidian-ui/home.md).

## Design rules

- **Thin, and a pure consumer.** Home embeds/links existing surfaces; it never becomes a second place that *computes* health or questions. If a query belongs to a dashboard, it lives in that dashboard and Home links it. The danger Home guards against is becoming a parallel dashboard that drifts from the real ones — keeping it a consumer means there is exactly one place each query is defined.
- **A note, not a plugin UI.** Home is Dataview-in-a-note — git-tracked, lintable, embeddable. This is exactly why a plugin-rendered start page was rejected ([ADR-25](../../project/decisions/25-homepage-front-door.md)): a plugin UI would be opaque to git, outside the linter, and unembeddable, breaking the properties the rest of the vault relies on.
- **Graceful degradation.** With the homepage plugin absent, `Home.md` is still an ordinary note the human can pin — nothing depends on auto-open. Home being a plain note means the recommended-tier homepage plugin is a convenience, never a dependency; the vault stays usable on a device that hasn't installed it.

## Related

- [Home how-to](../../how-to/obsidian-ui/home.md) — what Home contains and the runtime scaffold / setup steps.
- [obsidian-homepage](../../reference/plugins/obsidian-homepage.md) — the plugin that opens Home on launch.
- [ADR-25](../../project/decisions/25-homepage-front-door.md) — the homepage-front-door decision.
