---
topic: plugins
---

# The Obsidian plugin model — why these plugins

Memoria depends on a small set of Obsidian community plugins. This document explains *why* that set — the reasoning behind the priority order, what install order to follow, and what the required/recommended/reference distinction means as a set of concepts. For the actual lookup of which plugin does what and how each plugin's `data.json` should be configured, see [the configuration reference](../../reference/plugins/README.md).

## Priority, not alphabetical: the install-order reasoning

The filesystem sorts the plugins alphabetically, but **the priority order is what matters when setting up the vault**. Install plugins in priority order; skip the lower-priority ones until their absence is felt. The point of the ordering is that a fresh vault should be brought up incrementally — the human installs what Memoria *breaks* without first, gets a working system, and only then adds the quality-of-life layers as the friction of not having them becomes concrete. Installing everything up front means configuring plugins whose value the human can't yet feel, which is how `data.json` files drift away from reviewed defaults.

## The three tiers as concepts

The on-disk folders are three — `required/`, `recommended/`, `reference/` — and the split is a deliberate statement about each plugin's relationship to the system, not just a sorting convenience:

- **`required/`** — Memoria *breaks* without these. The control plane, the dashboards, the command palette, the callouts, and the git-driven workflows each assume a specific plugin is present and configured. A required plugin is part of the architecture, not an add-on; disabling one is not a degraded experience but a broken one. This is why the operational rule is "downgrade, don't disable" when a required plugin's update misbehaves.
- **`recommended/`** — quality-of-life installs the human adds *when the friction is felt*. Memoria works without them; they remove specific pains (semantic search, link coloring, hover previews, physical buttons). The finer labels used in the reference tables — the core eight that most humans want early, and the narrower three installed only when a specific use case lands — are editorial groupings *within* this one folder, not separate directories. The recommended tier is where the "install when felt" discipline lives: each plugin earns its place by solving a problem the human has actually hit.
- **`reference/`** — plugins documented for the record but **not** part of the install set. These are evaluated alternatives and future-migration targets, kept on record so the *reasoning* — why Memoria chose its current tool over this one, or under what conditions it would switch — isn't lost. A reference-tier plugin is held knowledge, not a recommendation; treating it as something to install misreads the tier.

The distinction matters because it tells the human how to *react* to each plugin: required plugins are non-negotiable infrastructure, recommended plugins are invitations to install on demand, and reference plugins are decisions already made and parked.

## Related

- [Plugin configuration reference](../../reference/plugins/README.md) — the Required / Recommended / Reference tables and the `data.json` conventions.
- [plugin-configs-lifecycle.md](plugin-configs-lifecycle.md) — what each `data.json` suffix means, what ships, and how drift is audited.
- [obsidian-ui/ui-discipline.md](../obsidian-ui/ui-discipline.md) — visual-style discipline, independent of any specific plugin.
